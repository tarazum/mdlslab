"""Deterministic scenario runner with budgets and the arm-A no-memory agent.

Arm A semantics: the agent sees only the current session's exchanges; the
context is reset between sessions. This is exactly the "no persistent memory"
ablation baseline of CONT-001.
"""

from __future__ import annotations

import re
import time
from typing import Any

from .events import EventJournal
from .provider import OllamaProvider

ARM_A_SYSTEM_PROMPT = (
    "You are a focused assistant in a controlled evaluation. "
    "Answer the environment's messages directly and briefly."
)


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
) -> dict[str, Any]:
    sid = scenario["id"]
    journal.emit("scenario.start", {"scenario": sid, "family": scenario["family"]}, scenario=sid)
    probes: list[dict] = []
    stopped = False

    for session in scenario["sessions"]:
        journal.emit(
            "session.start", {"index": session["index"]}, scenario=sid, session=session["index"]
        )
        # Arm A: session-local context only. The reset between sessions is the
        # absence of persistent memory.
        context: list[dict] = [{"role": "system", "content": ARM_A_SYSTEM_PROMPT}]
        journal.emit(
            "session.context_reset",
            {"reason": "arm-A no persistent memory"},
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
        "sessions_planned": len(scenario["sessions"]),
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
