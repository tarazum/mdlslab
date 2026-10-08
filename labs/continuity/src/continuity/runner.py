"""Deterministic scenario runner with budgets and the arm-A/arm-B/arm-C/arm-D agents.

Arm A semantics (unchanged since P0a): the agent sees only the current
session's exchanges; the context is reset between sessions. This is exactly
the "no persistent memory" ablation baseline of CONT-001.

Arm B (M2): arm A + a SQLite persistent memory store. The base system prompt
is byte-identical; the only addition is one extra system message injected at
session start (sessions with index >= 2) carrying the keyword-retrieved
episodes of the SAME scenario, plus append of both sides of every exchange to
the store after the exchange completes. The injection rule is fixed and
documented here so runs are reproducible.

Arm C (M3): arm B + the current self-model summary rendered into the system
prompt. One extra system message, immediately after the base system prompt,
in EVERY session (the self-model is session-independent). The block is
`selfmodel.render_summary` output — measured capability estimates and
recorded failure patterns, deterministic for a given self-model revision.
Everything else (base prompt, memory rule, budgets) is identical to arm B.

Arm D (M4): arm C + a bounded post-session reflection pass. After each
non-stopped session, `reflection.reflect_session(...)` (deterministic MVP,
see reflection.py) reviews the session's episodes and probe outcomes,
produces PROPOSALS (episode summaries / self-model revisions), and a
deterministic evidence-gated validator commits or rejects them. Accepted
summaries are NEW episodes in the same store (they surface through the
unchanged memory injection rule); accepted self-model revisions commit
through the fail-closed store (revision +1) and later sessions render the
updated revision. Immutable events are never rewritten. Arms A/B/C code
paths are unchanged by the arm D addition.

Arm E (M5): arm D + an ex-ante world model and a bounded deterministic
policy. Before each PROBE turn is answered, `worldmodel.WorldModel` records
a pass/fail prediction with a confidence derived from the self-model's
current family-rate estimate and record presence (events
`worldmodel.prediction` / `worldmodel.outcome`; bucketed calibration
counters) — predictions NEVER alter the prompt or the answer path. Each
turn, `policy.decide` chooses over the FIXED action set
{answer_direct, retrieve_then_answer} from explicit signals (absence-of-
records marker in the turn text; probe following a stored corrective
record) — event `policy.action`. The ONLY actuation is a per-turn memory
refresh/extension using the SAME renderer, retrieval rule and top-k as the
arm-B baseline injection (query = the CURRENT turn), skipped and recorded
as a no-op when the retrieved ids are already covered by this session's
injections. Arms A/B/C/D code paths are unchanged by the arm E addition
(a world model is rejected for any arm != "E").
"""

from __future__ import annotations

import re
import time
from typing import Any

from .events import EventJournal
from .claims import format_trust_block
from .lessons import LessonChannel
from .memory import MemoryStore
from .policy import ACTION_SET
from .policy import decide as policy_decide
from .provider import OllamaProvider
from .reflection import ReflectionEngine
from .selfmodel import render_summary, selfmodel_sha256
from .worldmodel import WorldModel, family_rate

ARM_A_SYSTEM_PROMPT = (
    "You are a focused assistant in a controlled evaluation. "
    "Answer the environment's messages directly and briefly."
)

# --- Arm B fixed memory-injection rule (M2) -------------------------------
# At the start of every session with index >= 2: query = the session's first
# environment turn; retrieve the top MEMORY_TOP_K episodes of the SAME
# scenario (keyword scoring, see memory.py); inject them as ONE system
# message appended after the base system prompt, most relevant first.
MEMORY_TOP_K = 8
MEMORY_BLOCK_HEADER = (
    "Your persistent memory: relevant records from your earlier sessions "
    "(most relevant first). Use them when the current session does not "
    "provide the information."
)


def format_memory_block(episodes: list[dict[str, Any]]) -> str:
    lines = [MEMORY_BLOCK_HEADER]
    for ep in episodes:
        lines.append(f"[{ep['turn_ref']}|{ep['role']}] {ep['content']}")
    return "\n".join(lines)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def extract_label(reply: str, labels: list[str]) -> str | None:
    """Suite v3 label-form scoring rule (declared before run 4, SUITE-V3-DESIGN 3).

    Find every option label that appears in the normalized reply as a standalone
    token (word boundaries, case-insensitive; surrounding quotes/punctuation do
    not count as part of the label). Return the label iff EXACTLY ONE distinct
    label is present; None when the reply contains none or several (ambiguous
    or prose without a label - a miss, never a pass).
    """
    observed = normalize(reply)
    found: list[str] = []
    for label in labels:
        if re.search(rf"(?<![a-z0-9]){re.escape(normalize(label))}(?![a-z0-9])", observed):
            found.append(label)
    distinct = sorted(set(found))
    return distinct[0] if len(distinct) == 1 else None


def score_probe(probe: dict, answer: str) -> dict:
    observed = normalize(answer)
    if probe["kind"] == "guess_calibration":
        # Suite v3: never-stated fact. Not scored; the reply is aggregated to
        # measure the empirical guess rate and position bias (design E14).
        labels = probe.get("labels", [])
        hit = extract_label(answer, labels)
        return {
            "kind": probe["kind"],
            "expected": None,
            "observed_normalized": observed,
            "observed_label": hit,
            "observed_position": labels.index(hit) if hit is not None else None,
            "labels": labels,
            "passed": None,
        }
    expected = normalize(probe["expected"])
    if probe["kind"] == "exact_match":
        if probe.get("labels"):
            # Label-form probe: extract the single standalone label (v3 rule).
            hit = extract_label(answer, probe["labels"])
            passed = hit is not None and normalize(hit) == expected
            return {
                "kind": probe["kind"],
                "expected": probe["expected"],
                "observed_normalized": observed,
                "observed_label": hit,
                "passed": passed,
            }
        passed = observed == expected
    elif probe["kind"] == "contains":
        passed = expected in observed
    else:  # guarded by fixture validation; keep the runner defensive anyway
        raise ValueError(f"unknown probe kind: {probe['kind']}")
    return {
        "kind": probe["kind"],
        "expected": probe["expected"],
        "observed_normalized": observed,
        "passed": passed,
    }


class Budget:
    def __init__(
        self,
        max_turns: int = 60,
        max_total_tokens: int = 200_000,
        wall_clock_s: float = 900.0,
    ) -> None:
        self.max_turns = max_turns
        self.max_total_tokens = max_total_tokens
        self.wall_clock_s = wall_clock_s
        self.turns = 0
        self.tokens = 0
        self.started = time.monotonic()
        self.violation: str | None = None

    def check(self) -> str | None:
        if self.violation:
            return self.violation
        if self.turns > self.max_turns:
            self.violation = f"turns={self.turns} > max_turns={self.max_turns}"
        elif self.tokens > self.max_total_tokens:
            self.violation = f"tokens={self.tokens} > max_total_tokens={self.max_total_tokens}"
        elif (time.monotonic() - self.started) > self.wall_clock_s:
            self.violation = (
                f"wall_clock={time.monotonic() - self.started:.1f}s > {self.wall_clock_s}s"
            )
        return self.violation


def run_scenario(
    scenario: dict,
    provider: OllamaProvider,
    journal: EventJournal,
    budget: Budget,
    arm: str = "A",
    memory: MemoryStore | None = None,
    selfmodel: dict | None = None,
    reflection: ReflectionEngine | None = None,
    worldmodel: WorldModel | None = None,
    lessons: LessonChannel | None = None,
) -> dict[str, Any]:
    # CONT-006 arms (additive; existing arms byte-comparable in behavior —
    # lessons default None and the R-branches never touch them):
    #   R0 = persistent memory (flat renderer), no lessons (T0-equivalent)
    #   R1 = deterministic MVP reflection in-run (D-equivalent: selfmodel +
    #        reflection.py, byte-stable baseline)
    #   R2/R3 = flat memory + the lesson channel (worker store / gold store)
    #   RBAD/RGOLD = flat memory + a one-lesson counterfactual channel
    #        (pilot-only safety/manipulation arms, never in the primary)
    valid_arms = ("A", "B", "C", "D", "E", "T0", "T1", "T2", "T3",
                  "R0", "R1", "R2", "R3", "RBAD", "RGOLD")
    memory_arms = ("B", "C", "D", "E", "T0", "T1", "T2", "T3",
                   "R0", "R1", "R2", "R3", "RBAD", "RGOLD")
    lesson_arms = ("R2", "R3", "RBAD", "RGOLD")
    if arm not in valid_arms:
        raise ValueError(f"unknown arm: {arm!r}")
    if arm in memory_arms and memory is None:
        raise ValueError(f"arm {arm} requires a memory store")
    if arm in ("C", "D", "E", "R1") and selfmodel is None:
        raise ValueError(f"arm {arm} requires a self-model")
    if arm in ("D", "E", "R1") and reflection is None:
        raise ValueError(f"arm {arm} requires a reflection engine")
    if arm == "E" and worldmodel is None:
        raise ValueError("arm E requires a world model")
    if arm != "E" and worldmodel is not None:
        raise ValueError("worldmodel is arm-E only (A/B/C/D behavior-identity guard)")
    if arm in ("T1", "T2", "T3") and selfmodel is not None:
        raise ValueError("selfmodel is not part of the T-arms (CONT-005 memory-side ablation)")
    if arm in lesson_arms and lessons is None:
        raise ValueError(f"arm {arm} requires a lesson channel")
    if arm not in lesson_arms and lessons is not None:
        raise ValueError("the lesson channel is R2/R3/RBAD/RGOLD only (CONT-006)")
    sid = scenario["id"]
    # Arm-A trace payloads stay byte-identical to the M1 pilot (comparability);
    # arms B/C/D/E add their marker.
    start_payload = {"scenario": sid, "family": scenario["family"]}
    if arm != "A":
        start_payload["arm"] = arm
    journal.emit("scenario.start", start_payload, scenario=sid)
    probes: list[dict] = []
    stopped = False
    reflection_reports: list[dict] = []
    policy_action_counts = {a: 0 for a in sorted(ACTION_SET)} if arm == "E" else None
    policy_injections = 0
    wm_counts_before = (
        (worldmodel.counters["predictions"], worldmodel.counters["outcomes"])
        if worldmodel is not None
        else (0, 0)
    )

    for session in scenario["sessions"]:
        session_probes: list[dict] = []
        journal.emit(
            "session.start", {"index": session["index"]}, scenario=sid, session=session["index"]
        )
        # Arm-E policy actuation bookkeeping: ids already injected into this
        # session's context (baseline session-start injection + any policy
        # injections earlier in the session) — the dedup surface.
        session_injected_ids: set[int] = set()
        # All arms reset the session-local context; arm A has nothing else
        # (that reset IS the ablation), arms B/C/D/E re-attach persistent memory.
        context: list[dict] = [{"role": "system", "content": ARM_A_SYSTEM_PROMPT}]
        if arm == "A":
            journal.emit(
                "session.context_reset",
                {"reason": "arm-A no persistent memory"},
                scenario=sid,
                session=session["index"],
            )
        else:
            journal.emit(
                "session.context_reset",
                {"reason": f"arm-{arm} session-local reset; persistent memory store retained"},
                scenario=sid,
                session=session["index"],
            )
            if arm in ("C", "D", "E", "R1"):
                # Fixed injection rule: the self-model summary goes into EVERY
                # session (session-independent), as one system message right
                # after the base prompt, rendered from the current revision.
                # Arm D renders the revision current at session start (the
                # reflection pass may have committed a newer one earlier).
                selfmodel_block = render_summary(selfmodel)
                context.append({"role": "system", "content": selfmodel_block})
                journal.emit(
                    "selfmodel.injected",
                    {
                        "agent_id": selfmodel["agentId"],
                        "revision": selfmodel["revision"],
                        "sha256": selfmodel_sha256(selfmodel),
                        "chars": len(selfmodel_block),
                        "capability_families": [
                            cap["family"] for cap in selfmodel["capabilities"]
                        ],
                        "failure_pattern_ids": [
                            pat["id"] for pat in selfmodel["knownFailurePatterns"]
                        ],
                    },
                    scenario=sid,
                    session=session["index"],
                )
            # Fixed injection rule: retrieve once per session (index >= 2),
            # query = the session's first environment turn, same-scenario scope.
            if session["index"] >= 2:
                query_text = session["turns"][0]["text"]
                episodes = memory.retrieve(query_text, scenario=sid, limit=MEMORY_TOP_K)
                if episodes:
                    if arm == "T0":
                        # Flat baseline: byte-identical renderer to arm B.
                        block = format_memory_block(episodes)
                    elif arm in ("T1", "T2", "T3"):
                        # CONT-005 trust arms: annotations / resolution / policy
                        # header rendered from the scenario's own source turns.
                        turn_by_ref = {
                            f"s{sess['index']}t{k}": t
                            for sess in scenario["sessions"]
                            for k, t in enumerate(sess["turns"], start=1)
                        }
                        block = format_trust_block(episodes, turn_by_ref, arm)
                    else:
                        block = format_memory_block(episodes)
                    context.append({"role": "system", "content": block})
                    if arm == "E":
                        session_injected_ids = {ep["id"] for ep in episodes}
                journal.emit(
                    "memory.injected",
                    {
                        "query_turn_ref": f"s{session['index']}t1",
                        "episode_count": len(episodes),
                        "episode_ids": [ep["id"] for ep in episodes],
                        "episode_refs": [f"{ep['turn_ref']}|{ep['role']}" for ep in episodes],
                        "top_k": MEMORY_TOP_K,
                        "injected": bool(episodes),
                        "renderer": (
                            "trust" if arm in ("T1", "T2", "T3") else "flat"
                        ),
                    },
                    scenario=sid,
                    session=session["index"],
                )
            if lessons is not None:
                # CONT-006 lesson channel (design §7, R2/R3/RBAD/RGOLD only):
                # retrieve once per session (EVERY session), query = the
                # session's first environment turn, render as ONE plain-prose
                # system message; retrieval telemetry per session (the M2b
                # "was the block actually rendered" check, at scale).
                selected = lessons.retrieve(session["turns"][0]["text"])
                block = None
                rendered_ids: list[str] = []
                if selected:
                    block, rendered = lessons.render(selected)
                    # FIX-R condition 2 (GATE-CONT006-VFIX): telemetry
                    # reports the RENDERED lessons (post-budget-fit), not
                    # the retrieved set — the M2b rendered-check reads this.
                    rendered_ids = [les["lessonId"] for les in rendered]
                    context.append({"role": "system", "content": block})
                journal.emit(
                    "lessons.injected",
                    {
                        "query_turn_ref": f"s{session['index']}t1",
                        "retrieved_ids": [les["lessonId"] for les in selected],
                        "lesson_ids": rendered_ids,
                        "injected": bool(rendered_ids),
                        "budget_dropped": len(selected) - len(rendered_ids),
                        "chars": len(block) if block else 0,
                        "renderer": "prose",
                        "store_sha256": lessons.digest,
                        "store_status": lessons.status,
                    },
                    scenario=sid,
                    session=session["index"],
                )
        for turn_no, turn in enumerate(session["turns"], start=1):
            turn_ref = f"s{session['index']}t{turn_no}"
            journal.emit(
                "env.turn",
                {"turn_ref": turn_ref, "text": turn["text"]},
                scenario=sid,
                session=session["index"],
            )
            if arm == "E":
                # M5 policy: decide + actuate BEFORE answering. The only
                # actuation is a per-turn memory refresh/extension with the
                # SAME renderer / retrieval rule / top-k as the baseline
                # injection (query = the CURRENT turn); no-op recorded when
                # the retrieved ids are already covered this session.
                decision = policy_decide(
                    turn_text=turn["text"],
                    is_probe=turn.get("probe") is not None,
                    env_episodes=memory.episodes_for_scenario(sid),
                )
                retrieval: dict[str, Any] | None = None
                if decision["action"] == "retrieve_then_answer":
                    episodes = memory.retrieve(turn["text"], scenario=sid, limit=MEMORY_TOP_K)
                    new_episodes = [e for e in episodes if e["id"] not in session_injected_ids]
                    if new_episodes:
                        context.append(
                            {"role": "system", "content": format_memory_block(new_episodes)}
                        )
                        session_injected_ids |= {e["id"] for e in new_episodes}
                        policy_injections += 1
                        retrieval = {
                            "injected": True,
                            "query_turn_ref": turn_ref,
                            "episode_ids": [e["id"] for e in new_episodes],
                            "episode_refs": [f"{e['turn_ref']}|{e['role']}" for e in new_episodes],
                            "dedup": "new-episode-ids-only",
                        }
                    else:
                        retrieval = {
                            "injected": False,
                            "query_turn_ref": turn_ref,
                            "episode_ids": [],
                            "reason": (
                                "no-op: no relevant episodes retrieved"
                                if not episodes
                                else "no-op: retrieved episodes already covered by this "
                                "session's injections"
                            ),
                        }
                policy_action_counts[decision["action"]] += 1
                journal.emit(
                    "policy.action",
                    {"turn_ref": turn_ref, **decision, "retrieval": retrieval},
                    scenario=sid,
                    session=session["index"],
                )
                if turn.get("probe") is not None:
                    # M5 world model: ex-ante prediction BEFORE the probe is
                    # answered — observational only, never alters the prompt
                    # or the answer path.
                    worldmodel.predict_probe(
                        scenario=sid,
                        family=scenario["family"],
                        turn_ref=turn_ref,
                        family_rate_value=family_rate(selfmodel, scenario["family"]),
                        episodes_for_scenario=memory.count(scenario=sid),
                        session=session["index"],
                    )
            context.append({"role": "user", "content": turn["text"]})
            reply = provider.chat(context)
            budget.turns += 1
            budget.tokens += reply["usage"]["total_tokens"]
            context.append({"role": "assistant", "content": reply["content"]})
            journal.emit(
                "agent.response",
                {
                    "turn_ref": turn_ref,
                    "content": reply["content"],
                    "usage": reply["usage"],
                    "total_duration_ms": reply["total_duration_ms"],
                    "options": dict(provider.options),
                    "model": provider.model,
                },
                scenario=sid,
                session=session["index"],
            )
            if arm in ("B", "C", "D", "E", "T0", "T1", "T2", "T3"):
                # Remember both sides of the exchange, immediately after it.
                for role, content in (
                    ("environment", turn["text"]),
                    ("assistant", reply["content"]),
                ):
                    episode_id = memory.append_episode(
                        run_id=journal.run_id,
                        scenario=sid,
                        session=session["index"],
                        turn_ref=turn_ref,
                        role=role,
                        content=content,
                    )
                    journal.emit(
                        "memory.append",
                        {"episode_id": episode_id, "turn_ref": turn_ref, "role": role},
                        scenario=sid,
                        session=session["index"],
                    )
            probe = turn.get("probe")
            if probe is not None:
                result = score_probe(probe, reply["content"])
                result["turn_ref"] = turn_ref
                probes.append(result)
                session_probes.append(dict(result))
                journal.emit(
                    "probe.result",
                    dict(result),
                    scenario=sid,
                    session=session["index"],
                )
                if arm == "E":
                    # M5 world model: attach the observed outcome to its
                    # prediction and update the calibration counters.
                    worldmodel.attach_outcome(
                        scenario=sid,
                        turn_ref=turn_ref,
                        passed=result["passed"],
                        session=session["index"],
                    )
            violation = budget.check()
            if violation is not None:
                journal.emit("budget.stop", {"violation": violation}, scenario=sid)
                stopped = True
                break
        if not stopped and arm in ("D", "E", "R1"):
            # M4: ONE bounded reflection pass after each non-stopped session.
            # Accepted summaries feed later sessions through the unchanged
            # memory injection rule; accepted self-model revisions render in
            # every later session (the local `selfmodel` rebinds to the
            # engine's current revision).
            reflection_reports.append(
                reflection.reflect_session(
                    scenario_id=sid,
                    family=scenario["family"],
                    session_index=session["index"],
                    session_probes=session_probes,
                )
            )
            selfmodel = reflection.model
        if stopped:
            break

    summary = {
        "scenario": sid,
        "family": scenario["family"],
        "arm": arm,
        "sessions_planned": len(scenario["sessions"]),
        "memory_episodes": memory.count(scenario=sid) if memory is not None else 0,
        "turns": budget.turns,
        "tokens_total": budget.tokens,
        "probes": probes,
        "probes_passed": sum(1 for p in probes if p["passed"]),
        "probes_total": len(probes),
        "stopped": stopped,
        "budget_violation": budget.violation,
        "duration_s": round(time.monotonic() - budget.started, 1),
    }
    if arm in ("D", "E", "R1") and reflection is not None:
        decisions = [d for r in reflection_reports for d in r["decisions"]]
        summary["reflection"] = {
            "passes": len(reflection_reports),
            "proposals": len(decisions),
            "accepted": sum(1 for d in decisions if d["accepted"]),
            "rejected": sum(1 for d in decisions if not d["accepted"]),
            "summaries_appended": sum(
                1 for d in decisions if d["type"] == "episode_summary" and d["accepted"]
            ),
            "selfmodel_revision_final": reflection.model["revision"],
        }
    if arm == "E" and worldmodel is not None:
        preds_before, outcomes_before = wm_counts_before
        summary["worldmodel"] = {
            "predictions_this_scenario": worldmodel.counters["predictions"] - preds_before,
            "outcomes_this_scenario": worldmodel.counters["outcomes"] - outcomes_before,
            "calibration_cumulative": worldmodel.calibration(),
        }
        summary["policy"] = {
            "actions": policy_action_counts,
            "injections": policy_injections,
            "action_set": sorted(ACTION_SET),
        }
    journal.emit("scenario.end", dict(summary), scenario=sid)
    return summary
