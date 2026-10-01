"""Deterministic scenario runner with budgets and the arm-A/arm-B agents.

Arm A semantics (unchanged since P0a): the agent sees only the current
session's exchanges; the context is reset between sessions. This is exactly
the "no persistent memory" ablation baseline of CONT-001.

Arm B (M2): arm A + a SQLite persistent memory store. The base system prompt
is byte-identical; the only addition is one extra system message injected at
session start (sessions with index >= 2) carrying the keyword-retrieved
episodes of the same scenario, plus append of both sides of every exchange to
the store after the exchange completes. The injection rule is fixed and
documented here so runs are reproducible.
"""

from __future__ import annotations

import re
import time
from typing import Any

from .events import EventJournal
from .memory import MemoryStore
from .provider import OllamaProvider

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


def score_probe(probe: dict, answer: str) -> dict:
    observed = normalize(answer)
    expected = normalize(probe["expected"])
    if probe["kind"] == "exact_match":
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
) -> dict[str, Any]:
    if arm not in ("A", "B"):
        raise ValueError(f"unknown arm: {arm!r}")
    if arm == "B" and memory is None:
        raise ValueError("arm B requires a memory store")
    sid = scenario["id"]
    # Arm-A trace payloads stay byte-identical to the M1 pilot (comparability);
    # arm B adds its marker.
    start_payload = {"scenario": sid, "family": scenario["family"]}
    if arm != "A":
        start_payload["arm"] = arm
    journal.emit("scenario.start", start_payload, scenario=sid)
    probes: list[dict] = []
    stopped = False

    for session in scenario["sessions"]:
        journal.emit(
            "session.start", {"index": session["index"]}, scenario=sid, session=session["index"]
        )
        # Both arms reset the session-local context; arm A has nothing else
        # (that reset IS the ablation), arm B re-attaches persistent memory.
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
                {"reason": "arm-B session-local reset; persistent memory store retained"},
                scenario=sid,
                session=session["index"],
            )
            # Fixed injection rule: retrieve once per session (index >= 2),
            # query = the session's first environment turn, same-scenario scope.
            if session["index"] >= 2:
                query_text = session["turns"][0]["text"]
                episodes = memory.retrieve(query_text, scenario=sid, limit=MEMORY_TOP_K)
                if episodes:
                    context.append(
                        {"role": "system", "content": format_memory_block(episodes)}
                    )
                journal.emit(
                    "memory.injected",
                    {
                        "query_turn_ref": f"s{session['index']}t1",
                        "episode_count": len(episodes),
                        "episode_ids": [ep["id"] for ep in episodes],
                        "episode_refs": [f"{ep['turn_ref']}|{ep['role']}" for ep in episodes],
                        "top_k": MEMORY_TOP_K,
                        "injected": bool(episodes),
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
            if arm == "B":
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
                journal.emit(
                    "probe.result",
                    dict(result),
                    scenario=sid,
                    session=session["index"],
                )
            violation = budget.check()
            if violation is not None:
                journal.emit("budget.stop", {"violation": violation}, scenario=sid)
                stopped = True
                break
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
    journal.emit("scenario.end", dict(summary), scenario=sid)
    return summary
