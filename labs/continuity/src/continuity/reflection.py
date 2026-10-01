"""Bounded post-session reflection pass (arm D MVP, deterministic, stdlib only).

M4 contract (docs/ROADMAP.md): after each session ends, ONE bounded pass
reviews the session's episodes and produces PROPOSALS only. A deterministic
validator (schema + every proposal must cite evidence: episode ids / probe
outcomes; no evidence -> reject) commits accepted proposals via the existing
fail-closed stores or rejects them. Immutable events are NEVER rewritten —
summaries are NEW records. Accept/reject counts are telemetry.

Design decisions (recorded in LOG.md 2026-10-01 23:21 start-note):
- DETERMINISTIC MVP, no LLM call: reproducible, zero GPU cost, and an LLM
  reflecting on its own wrong answers is itself exposed to the CN-007
  anchoring mechanism it is meant to cure. All inference requests keep their
  per-request sampling options (PB-071); reflection adds no inference.
- Proposal types:
  (a) episode_summary — one compact summary episode of the session's episodes
      (environment records verbatim, own answers capped, plus a fixed-rule
      conflict review). The conflict review is the deterministic CN-007/CN-008
      mitigation attempt: when an assistant answer is followed by a LATER
      same-session environment record containing one of the fixed corrective
      markers ("do not use", "instead of", "is now", "correction", ...), the
      summary juxtaposes the two and marks the later corrective record
      authoritative (supersession semantics as prompt content derived from
      evidence — no policy/tool changes).
  (b) selfmodel_capability_update — cumulative probe-count increment for a
      family, accepted only when the family's per-seed probe count is
      complete, so the selfmodel arithmetic invariant (total == probes_per_seed
      x seeds) holds and `selfmodel.validate()` still recomputes cleanly.
  (c) selfmodel_failure_pattern — in-run failure entry citing the failed
      probe. The rendered text shows the observed answer, never the expected
      one (CN-009 exposure control); the full outcome stays in stored
      evidence for audit.
- Self-model revisions commit through `selfmodel.commit()` (fail-closed,
  revision +1) into a per-run COPY of the canonical store — pilots never
  mutate `state/selfmodel.json`. If the store refuses, every self-model
  proposal of that pass flips to rejected with the store's reason.
- CN-009 exposure (explicit, not silent): these revisions are estimated from
  in-run probe outcomes and render into later sessions of the same run. Every
  reflection-derived estimate carries provenance.method starting with
  "reflection" and in-run trace refs, so the exposure is auditable.
"""

from __future__ import annotations

import copy
import json
import time
from pathlib import Path
from typing import Any

from .memory import MemoryStore
from .selfmodel import SelfModelError
from .selfmodel import binomial_sd, commit as selfmodel_commit
from .selfmodel import load as load_selfmodel
from .selfmodel import selfmodel_sha256, wilson_interval

# Fixed corrective-marker list (deterministic conflict detection). Lowercase
# substrings matched against later environment records of the same session.
CORRECTIVE_MARKERS: tuple[str, ...] = (
    "do not use",
    "do not",
    "instead of",
    "rather than",
    "no longer",
    "not anymore",
    "is now",
    "corrected",
    "correction",
    "actually",
    "revised",
    "superseded",
    "supersedes",
    "updated to",
    "changed to",
)

SUMMARY_ROLE = "reflection.summary"
MAX_SUMMARY_CHARS = 1200
PROPOSAL_TYPES = frozenset(
    {"episode_summary", "selfmodel_capability_update", "selfmodel_failure_pattern"}
)


class ReflectionError(RuntimeError):
    """Engine misuse (bad store, unknown proposal type) — not a proposal rejection."""


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _snippet(text: str, cap: int = 160) -> str:
    text = " ".join(text.split())
    return text if len(text) <= cap else text[: cap - 1] + "…"


def _marker_sentence(content: str, marker: str) -> str:
    """The sentence of `content` containing `marker` (deterministic, capped)."""
    lowered = content.lower()
    for sentence in content.split(". "):
        if marker in sentence.lower() or (
            sentence.lower() in lowered and marker in lowered
        ):
            return _snippet(sentence, 200)
    return _snippet(content, 200)


class ReflectionEngine:
    """One engine per run (per seed); ONE pass per non-stopped session."""

    def __init__(
        self,
        *,
        selfmodel_path: str,
        memory: MemoryStore,
        journal: Any,
        run_seed: int,
        source_artifact: str,
    ) -> None:
        # Fail-closed: the per-run copy must validate before anything runs.
        self.model = load_selfmodel(selfmodel_path)
        self.selfmodel_path = selfmodel_path
        self.memory = memory
        self.journal = journal
        self.run_seed = run_seed
        self.source_artifact = source_artifact
        self.pass_no = 0
        self._proposal_counter = 0
        self._family_observed: dict[str, dict[str, int]] = {}
        self.telemetry: dict[str, Any] = {
            "passes": 0,
            "selfmodel_sha256_initial": selfmodel_sha256(self.model),
            "selfmodel_revision_initial": self.model["revision"],
            "proposals_by_type": {t: 0 for t in sorted(PROPOSAL_TYPES)},
            "accepted_by_type": {t: 0 for t in sorted(PROPOSAL_TYPES)},
            "rejected_by_type": {t: 0 for t in sorted(PROPOSAL_TYPES)},
            "rejection_reasons": [],
            "selfmodel_revision_final": self.model["revision"],
            "summaries_appended": 0,
        }

    # ------------------------------------------------------------------ pass

    def reflect_session(
        self,
        *,
        scenario_id: str,
        family: str,
        session_index: int,
        session_probes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """ONE bounded pass over the just-ended session. Returns the pass report."""
        self.pass_no += 1
        episodes = self.memory.episodes_for(scenario_id, session_index)
        self.journal.emit(
            "reflection.start",
            {
                "pass": self.pass_no,
                "scenario": scenario_id,
                "family": family,
                "session": session_index,
                "evidence_episode_ids": [e["id"] for e in episodes],
                "probe_turn_refs": [p["turn_ref"] for p in session_probes],
            },
            scenario=scenario_id,
            session=session_index,
        )

        # Accumulate in-run family observations (evidence for capability updates).
        for probe in session_probes:
            slot = self._family_observed.setdefault(
                family, {"passed": 0, "total": 0, "turn_refs": []}
            )
            slot["passed"] += 1 if probe["passed"] else 0
            slot["total"] += 1
            slot["turn_refs"].append(probe["turn_ref"])

        proposals: list[dict[str, Any]] = []
        if episodes:
            proposals.append(
                self._build_summary_proposal(
                    scenario_id=scenario_id, session_index=session_index,
                    episodes=episodes,
                )
            )
        if self._family_observed.get(family, {}).get("total", 0) > 0:
            proposals.append(
                self._build_capability_proposal(
                    scenario_id=scenario_id, family=family,
                    session_probes=session_probes,
                )
            )
        for probe in session_probes:
            if not probe["passed"]:
                proposals.append(
                    self._build_failure_pattern_proposal(
                        scenario_id=scenario_id, family=family, probe=probe
                    )
                )

        # Deterministic validation — evidence is re-derived, never trusted.
        verdicts: list[tuple[dict[str, Any], bool, str]] = [
            (p, *self._validate(p, scenario_id, session_index, session_probes))
            for p in proposals
        ]

        # Commit phase. Summaries are new records in the episode store; all
        # validator-accepted self-model proposals share ONE revision bump.
        accepted_sm = [p for p, ok, _ in verdicts if ok and p["type"] != "episode_summary"]
        revision_before = self.model["revision"]
        sm_error: str | None = None
        if accepted_sm:
            try:
                candidate = self._selfmodel_candidate(accepted_sm)
                self.model = selfmodel_commit(self.selfmodel_path, candidate)
            except SelfModelError as exc:
                sm_error = str(exc)
                verdicts = [
                    (p, False, f"selfmodel commit refused: {exc}")
                    if p["type"] != "episode_summary"
                    else (p, ok, reason)
                    for p, ok, reason in verdicts
                ]

        decisions: list[dict[str, Any]] = []
        summary_episode_id: int | None = None
        for proposal, accepted, reason in verdicts:
            committed: dict[str, Any] = {}
            if accepted and proposal["type"] == "episode_summary":
                summary_episode_id = self.memory.append_episode(
                    run_id=self.journal.run_id,
                    scenario=scenario_id,
                    session=session_index,
                    turn_ref=f"s{session_index}-summary",
                    role=SUMMARY_ROLE,
                    content=proposal["payload"]["content"],
                    importance=0.5,
                    meta={
                        "kind": SUMMARY_ROLE,
                        "proposal_id": proposal["proposal_id"],
                        "reflection_pass": self.pass_no,
                        "evidence_episode_ids": proposal["evidence"]["episode_ids"],
                        "conflict_review": proposal["payload"]["conflict_review"],
                    },
                )
                self.telemetry["summaries_appended"] += 1
                committed["summary_episode_id"] = summary_episode_id
            if accepted and proposal["type"] != "episode_summary":
                committed["selfmodel_revision"] = self.model["revision"]
            ptype = proposal["type"]
            self.telemetry["proposals_by_type"][ptype] += 1
            if accepted:
                self.telemetry["accepted_by_type"][ptype] += 1
            else:
                self.telemetry["rejected_by_type"][ptype] += 1
                self.telemetry["rejection_reasons"].append(
                    {"proposal_id": proposal["proposal_id"], "reason": reason}
                )
            decision = {
                "proposal_id": proposal["proposal_id"],
                "type": ptype,
                "accepted": accepted,
                "reason": reason,
                "evidence": proposal["evidence"],
                **committed,
            }
            decisions.append(decision)
            self.journal.emit(
                "reflection.proposal", decision, scenario=scenario_id, session=session_index
            )

        self.telemetry["passes"] += 1
        self.telemetry["selfmodel_revision_final"] = self.model["revision"]
        commit_payload = {
            "pass": self.pass_no,
            "scenario": scenario_id,
            "session": session_index,
            "proposals": len(decisions),
            "accepted": sum(1 for d in decisions if d["accepted"]),
            "rejected": sum(1 for d in decisions if not d["accepted"]),
            "summaries_appended_total": self.telemetry["summaries_appended"],
            "selfmodel_revision_before": revision_before,
            "selfmodel_revision_after": self.model["revision"],
            "selfmodel_sha256_after": selfmodel_sha256(self.model),
        }
        if sm_error:
            commit_payload["selfmodel_commit_error"] = sm_error
        self.journal.emit(
            "reflection.commit", commit_payload, scenario=scenario_id, session=session_index
        )
        return {
            "pass": self.pass_no,
            "scenario": scenario_id,
            "session": session_index,
            "decisions": decisions,
            "summary_episode_id": summary_episode_id,
            "selfmodel_revision_after": self.model["revision"],
        }

    # ------------------------------------------------------------- builders

    def _next_proposal_id(self) -> str:
        self._proposal_counter += 1
        return f"P-{self._proposal_counter:04d}"

    def _build_summary_proposal(
        self, *, scenario_id: str, session_index: int, episodes: list[dict[str, Any]]
    ) -> dict[str, Any]:
        env = [e for e in episodes if e["role"] == "environment"]
        own = [e for e in episodes if e["role"] == "assistant"]
        conflicts = self._conflict_review(episodes)
        lines = [
            f"SESSION SUMMARY (deterministic reflection, pass {self.pass_no}) of "
            f"{scenario_id} session {session_index}; compacted from "
            f"{len(episodes)} records.",
            "Environment records (verbatim, in order):",
        ]
        lines += [f"- [{e['turn_ref']}] {_snippet(e['content'], 400)}" for e in env]
        lines.append("Your recorded answers:")
        answer_lines = [f"- [{e['turn_ref']}] {_snippet(e['content'], 120)}" for e in own]
        lines += answer_lines if answer_lines else ["- (none)"]
        lines.append("Conflict review:")
        if conflicts:
            lines += [f"- {c}" for c in conflicts]
        else:
            lines.append(
                "- none detected (no own answer is followed by a corrective "
                "environment record in this session)."
            )
        content = "\n".join(lines)
        if len(content) > MAX_SUMMARY_CHARS:
            content = content[: MAX_SUMMARY_CHARS - 15] + "…(truncated)"
        return {
            "proposal_id": self._next_proposal_id(),
            "type": "episode_summary",
            "scenario": scenario_id,
            "session": session_index,
            "evidence": {"episode_ids": [e["id"] for e in episodes]},
            "payload": {"content": content, "conflict_review": conflicts},
        }

    def _conflict_review(self, episodes: list[dict[str, Any]]) -> list[str]:
        """Fixed-rule supersession detection (CN-007/CN-008 mitigation attempt).

        For each own answer, if a LATER environment record of the same session
        contains a corrective marker, juxtapose the two and mark the later
        corrective record authoritative. One corrective record per answer.
        """
        conflicts: list[str] = []
        env_eps = [e for e in episodes if e["role"] == "environment"]
        for own_ep in (e for e in episodes if e["role"] == "assistant"):
            for env_ep in (e for e in env_eps if e["id"] > own_ep["id"]):
                lowered = env_ep["content"].lower()
                marker = next((m for m in CORRECTIVE_MARKERS if m in lowered), None)
                if marker is None:
                    continue
                conflicts.append(
                    f"your answer at {own_ep['turn_ref']} "
                    f"({_snippet(own_ep['content'], 80)!r}) is followed by the "
                    f"corrective record at {env_ep['turn_ref']} "
                    f"({_marker_sentence(env_ep['content'], marker)!r}); when they "
                    f"disagree, the later corrective record is authoritative."
                )
                break
        return conflicts

    def _build_capability_proposal(
        self, *, scenario_id: str, family: str, session_probes: list[dict[str, Any]]
    ) -> dict[str, Any]:
        obs = self._family_observed[family]
        return {
            "proposal_id": self._next_proposal_id(),
            "type": "selfmodel_capability_update",
            "scenario": scenario_id,
            "session": None,
            "family": family,
            "evidence": {
                "probe_outcomes": [
                    {
                        "turn_ref": p["turn_ref"],
                        "passed": bool(p["passed"]),
                        "scenario": scenario_id,
                    }
                    for p in session_probes
                ],
                "cumulative_turn_refs": list(obs["turn_refs"]),
            },
            "payload": {"family": family},
        }

    def _build_failure_pattern_proposal(
        self, *, scenario_id: str, family: str, probe: dict[str, Any]
    ) -> dict[str, Any]:
        proposal_id = self._next_proposal_id()
        return {
            "proposal_id": proposal_id,
            "type": "selfmodel_failure_pattern",
            "scenario": scenario_id,
            "session": None,
            "family": family,
            "evidence": {
                "probe_outcomes": [
                    {"turn_ref": probe["turn_ref"], "passed": False, "scenario": scenario_id}
                ],
            },
            "payload": {
                "pattern_id": "REF-" + proposal_id[2:],
                "family": family,
                "scenario": scenario_id,
                "probe": dict(probe),
            },
        }

    # -------------------------------------------------------------- validator

    def _validate(
        self,
        proposal: dict[str, Any],
        scenario_id: str,
        session_index: int,
        session_probes: list[dict[str, Any]],
    ) -> tuple[bool, str]:
        """Deterministic schema + evidence re-derivation. No evidence -> reject."""
        ptype = proposal.get("type")
        if ptype not in PROPOSAL_TYPES:
            return False, f"unknown proposal type: {ptype!r}"

        if ptype == "episode_summary":
            ids = proposal.get("evidence", {}).get("episode_ids") or []
            if not ids:
                return False, "no evidence episode ids"
            actual = {
                e["id"] for e in self.memory.episodes_for(scenario_id, session_index)
            }
            missing = [i for i in ids if i not in actual]
            if missing:
                return False, f"evidence episodes not found in store: {missing}"
            content = proposal.get("payload", {}).get("content", "")
            if not content.strip():
                return False, "summary content empty"
            if len(content) > MAX_SUMMARY_CHARS + 1:
                return False, "summary exceeds length bound"
            return True, "evidence verified: all cited episodes exist in the session store"

        if ptype == "selfmodel_capability_update":
            family = proposal.get("family")
            obs = self._family_observed.get(family)
            if not obs or obs["total"] <= 0:
                return False, f"no observed probe outcomes for family {family!r}"
            cap = next(
                (c for c in self.model["capabilities"] if c["family"] == family), None
            )
            if cap is None:
                return False, f"self-model has no capability entry for family {family!r}"
            if self.run_seed in cap["seeds"]:
                return False, f"seed {self.run_seed} already counted for family {family!r}"
            if obs["total"] != cap["probes_per_seed"]:
                return False, (
                    f"family incomplete: observed {obs['total']} of "
                    f"{cap['probes_per_seed']} probes for family {family!r}"
                )
            # Arithmetic pre-check mirroring selfmodel.validate().
            new_passed = cap["passed"] + obs["passed"]
            new_total = cap["total"] + obs["total"]
            if new_total != cap["probes_per_seed"] * (len(cap["seeds"]) + 1):
                return False, "arithmetic mismatch: total != probes_per_seed x seeds"
            cited = {o["turn_ref"] for o in proposal["evidence"]["probe_outcomes"]}
            real = {p["turn_ref"] for p in session_probes}
            if not cited or not cited <= real:
                return False, "cited probe outcomes not found in session outcomes"
            return True, (
                "evidence verified: family complete, counts recomputed from probe "
                "outcomes, seed new"
            )

        if ptype == "selfmodel_failure_pattern":
            payload = proposal.get("payload", {})
            pattern_id = payload.get("pattern_id", "")
            if not pattern_id.strip():
                return False, "empty failure-pattern id"
            if pattern_id in {p["id"] for p in self.model["knownFailurePatterns"]}:
                return False, f"duplicate failure-pattern id {pattern_id!r}"
            cited = proposal["evidence"]["probe_outcomes"]
            real = {p["turn_ref"]: p for p in session_probes}
            for outcome in cited:
                probe = real.get(outcome["turn_ref"])
                if probe is None:
                    return False, f"cited probe {outcome['turn_ref']!r} not in session outcomes"
                if probe["passed"] or outcome["passed"]:
                    return False, f"cited probe {outcome['turn_ref']!r} did not fail"
            return True, "evidence verified: cited probe exists and failed"

        return False, f"unhandled proposal type: {ptype!r}"

    # ---------------------------------------------------------------- commits

    def _selfmodel_candidate(self, proposals: list[dict[str, Any]]) -> dict[str, Any]:
        """One revision bump carrying every validator-accepted self-model proposal."""
        candidate = copy.deepcopy(self.model)
        candidate["revision"] = self.model["revision"] + 1
        candidate["updatedUtc"] = _utc_now()
        candidate["lastConsolidation"] = _utc_now()
        for proposal in proposals:
            if proposal["type"] == "selfmodel_capability_update":
                family = proposal["family"]
                obs = self._family_observed[family]
                prev_cap = next(c for c in self.model["capabilities"] if c["family"] == family)
                cap = next(c for c in candidate["capabilities"] if c["family"] == family)
                cap["passed"] += obs["passed"]
                cap["total"] += obs["total"]
                cap["seeds"] = list(cap["seeds"]) + [self.run_seed]
                cap["rate"] = round(cap["passed"] / cap["total"], 3)
                cap["wilson95"] = wilson_interval(cap["passed"], cap["total"])
                cap["binomial_sd"] = binomial_sd(cap["passed"], cap["total"])
                cap["provenance"] = {
                    "source_artifact": self.source_artifact,
                    "method": (
                        "reflection (M4, deterministic): cumulative in-run probe "
                        "counts after family completion; CN-009 exposure — renders "
                        "into later sessions of the same run"
                    ),
                    "numbers": {
                        "previous": {
                            "passed": prev_cap["passed"],
                            "total": prev_cap["total"],
                        },
                        "observed_passed": obs["passed"],
                        "observed_total": obs["total"],
                        "observed_turn_refs": obs["turn_refs"],
                        "seed": self.run_seed,
                    },
                }
            elif proposal["type"] == "selfmodel_failure_pattern":
                payload = proposal["payload"]
                probe = payload["probe"]
                candidate["knownFailurePatterns"].append(
                    {
                        "id": payload["pattern_id"],
                        "title": f"in-run failure: {payload['family']} / {payload['scenario']}",
                        "pattern": (
                            "In-run recorded failure (deterministic reflection): the "
                            f"probe at {probe['turn_ref']} in scenario "
                            f"{payload['scenario']} (family {payload['family']}) was "
                            f"answered {probe['observed_normalized']!r} and failed. "
                            "Background self-knowledge only; it does not override "
                            "what the current session or the records say."
                        ),
                        "evidence": {
                            "refs": [
                                f"{self.source_artifact} (reflection pass "
                                f"{self.pass_no}, proposal {proposal['proposal_id']})"
                            ],
                            "numbers": {
                                "scenario": payload["scenario"],
                                "family": payload["family"],
                                "turn_ref": probe["turn_ref"],
                                "observed_normalized": [probe["observed_normalized"]],
                                "expected": probe["expected"],  # stored, never rendered
                                "pass_count": 0,
                                "seeds": 1,
                                "seed": self.run_seed,
                            },
                        },
                    }
                )
        return candidate


# --- offline selftest -------------------------------------------------------

def _selftest() -> int:
    """Offline: proposals -> validator -> commits -> trace events -> tamper paths."""
    import tempfile

    from .events import EventJournal, validate_trace
    from .selfmodel import build_from_arm_b_aggregate

    aggregate = {
        "pilot": {
            "arm": "B", "run_id": "selftest", "model": "granite-code:8b",
            "model_digest": "36c3c3b9683b", "temperature": 0.0,
            "seeds_run": [11, 22],
        },
        "per_family": {
            "delayed_recall": {"passed_by_seed": {"11": 3, "22": 3}, "probes_per_seed": 3},
            "repeated_task": {"passed_by_seed": {"11": 1, "22": 0}, "probes_per_seed": 3},
        },
        "per_scenario": {
            "rt-0003": {
                "family": "repeated_task", "pass_count": 0,
                "observations_by_seed": {
                    "11": [{"observed_normalized": "bug", "passed": False}],
                    "22": [{"observed_normalized": "bug", "passed": False}],
                },
            },
            "cu-0001": {
                "family": "contradiction_update", "pass_count": 0,
                "observations_by_seed": {
                    "11": [{"observed_normalized": "12", "passed": False}],
                    "22": [{"observed_normalized": "12", "passed": False}],
                },
            },
        },
    }

    with tempfile.TemporaryDirectory() as tmp:
        store_path = str(Path(tmp) / "selfmodel.json")
        base = build_from_arm_b_aggregate(
            aggregate, agent_id="continuity/selftest",
            source_artifact="results/CONT-000/selftest/aggregate.json",
        )
        selfmodel_commit(store_path, base)

        memory = MemoryStore(str(Path(tmp) / "memory.sqlite3"))
        journal = EventJournal(str(Path(tmp) / "trace.jsonl"), "selftest-run")
        try:
            # Session 1 of an rt-like scenario: episodes incl. a corrective record.
            memory.append_episode(
                run_id="selftest-run", scenario="rt-x", session=1, turn_ref="s1t1",
                role="environment",
                content="Classify this support ticket: billing | bug | account. "
                "Ticket: 'The app takes two minutes to open settings.'",
            )
            memory.append_episode(
                run_id="selftest-run", scenario="rt-x", session=1, turn_ref="s1t1",
                role="assistant", content="bug",
            )
            memory.append_episode(
                run_id="selftest-run", scenario="rt-x", session=1, turn_ref="s1t2",
                role="environment",
                content="For your records, the rubric: slowness without a crash gets "
                "the label perf — do not use bug for slow-but-working behavior.",
            )
            engine = ReflectionEngine(
                selfmodel_path=store_path, memory=memory, journal=journal,
                run_seed=33, source_artifact="results/CONT-000/selftest/summary.json",
            )
            report1 = engine.reflect_session(
                scenario_id="rt-x", family="repeated_task", session_index=1,
                session_probes=[],
            )
            d1 = {d["type"]: d for d in report1["decisions"]}
            assert d1["episode_summary"]["accepted"], d1
            summary_ep = memory.episodes_for("rt-x", 1)[-1]
            assert summary_ep["role"] == SUMMARY_ROLE
            assert "do not use" in summary_ep["content"], summary_ep["content"]
            assert "authoritative" in summary_ep["content"]
            assert json.loads(summary_ep["meta"])["kind"] == SUMMARY_ROLE

            # Session 2: probe outcome evidence paths.
            memory.append_episode(
                run_id="selftest-run", scenario="rt-x", session=2, turn_ref="s2t1",
                role="environment", content="Classify: 'PDF export works but is slow.'",
            )
            failed_probe = {
                "kind": "exact_match", "expected": "perf", "observed_normalized": "bug",
                "passed": False, "turn_ref": "s2t1",
            }
            report2 = engine.reflect_session(
                scenario_id="rt-x", family="repeated_task", session_index=2,
                session_probes=[failed_probe],
            )
            d2 = {d["type"]: d for d in report2["decisions"]}
            # repeated_task observed 1 of 3 probes -> capability update REJECTED
            assert not d2["selfmodel_capability_update"]["accepted"]
            assert "family incomplete" in d2["selfmodel_capability_update"]["reason"]
            # failed probe -> failure pattern accepted, revision bumped
            assert d2["selfmodel_failure_pattern"]["accepted"]
            assert engine.model["revision"] == 2
            assert engine.model["knownFailurePatterns"][-1]["id"] == "REF-" + d2[
                "selfmodel_failure_pattern"
            ]["proposal_id"][2:]
            # expected answer stored for audit, but not rendered
            stored = json.dumps(engine.model["knownFailurePatterns"][-1])
            assert '"expected": "perf"' in stored
            assert "perf" not in engine.model["knownFailurePatterns"][-1]["pattern"]

            # Family completion: two more probes complete repeated_task (pps=3).
            for i, (passed, turn) in enumerate([(True, "s3t1"), (True, "s4t1")], start=3):
                memory.append_episode(
                    run_id="selftest-run", scenario=f"rt-y{i}", session=1,
                    turn_ref=turn, role="environment", content="classify",
                )
                engine.reflect_session(
                    scenario_id=f"rt-y{i}", family="repeated_task", session_index=1,
                    session_probes=[{
                        "kind": "exact_match", "expected": "x",
                        "observed_normalized": "x" if passed else "bug",
                        "passed": passed, "turn_ref": turn,
                    }],
                )
            assert engine.model["revision"] == 3
            cap = next(
                c for c in engine.model["capabilities"] if c["family"] == "repeated_task"
            )
            # prev 1/6 over seeds [11,22] + observed 2/3 for seed 33 -> 3/9, seeds [11,22,33]
            assert cap["seeds"] == [11, 22, 33] and cap["total"] == 9, cap
            assert cap["passed"] == 3 and cap["rate"] == 0.333
            assert cap["provenance"]["method"].startswith("reflection")

            # Validator tamper paths (direct calls, no commits).
            bogus = {
                "proposal_id": "P-9999", "type": "episode_summary", "scenario": "rt-x",
                "session": 9, "evidence": {"episode_ids": [99999]},
                "payload": {"content": "x"},
            }
            ok, reason = engine._validate(bogus, "rt-x", 9, [])
            assert not ok and "not found" in reason
            dup = {
                "proposal_id": "P-9998", "type": "selfmodel_failure_pattern",
                "scenario": "rt-x", "session": None, "family": "repeated_task",
                "evidence": {"probe_outcomes": [{"turn_ref": "s2t1", "passed": False}]},
                "payload": {
                    "pattern_id": engine.model["knownFailurePatterns"][-1]["id"],
                    "family": "repeated_task", "scenario": "rt-x",
                    "probe": dict(failed_probe),
                },
            }
            ok, reason = engine._validate(dup, "rt-x", 2, [failed_probe])
            assert not ok and "duplicate" in reason

            # Trace re-validates and reflection events are visible.
            trace_path = str(Path(tmp) / "trace.jsonl")
            journal.close()
            ok, errors = validate_trace(trace_path)
            assert ok, errors
            text = Path(trace_path).read_text(encoding="utf-8")
            for etype in ("reflection.start", "reflection.proposal", "reflection.commit"):
                assert f'"type": "{etype}"' in text, etype
            t = engine.telemetry
            assert t["accepted_by_type"]["episode_summary"] == 4
            assert t["rejected_by_type"]["selfmodel_capability_update"] >= 1
        finally:
            # Windows: close handles before TemporaryDirectory cleanup.
            journal.close()
            memory.close()
    print(
        "reflection selftest ok: deterministic proposals, evidence-gated "
        "validator (rejections + tamper paths), fail-closed selfmodel commits, "
        "trace events"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
