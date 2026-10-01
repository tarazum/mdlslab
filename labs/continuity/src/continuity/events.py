"""Append-only event journal with trace validation.

The journal is the durable evidence layer: every state transition of a run
emits one JSON line. A trace is *replayable* when it re-validates from disk,
independent of the process that produced it (artifact over exit code).
"""

from __future__ import annotations

import json
import os
import time
from typing import Any

REQUIRED_FIELDS = ("seq", "ts", "run_id", "type", "payload")

EVENT_TYPES = frozenset(
    {
        "run.start",
        "env.snapshot",
        "env.model_pinned",
        "scenario.start",
        "session.start",
        "session.context_reset",
        "memory.append",
        "memory.injected",
        "env.turn",
        "agent.response",
        "probe.result",
        "budget.stop",
        "scenario.end",
        "run.end",
    }
)


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


class EventJournal:
    """Append-only JSONL journal for one run."""

    def __init__(self, path: str, run_id: str) -> None:
        self.path = path
        self.run_id = run_id
        self.seq = 0
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self._fh = open(path, "a", encoding="utf-8")

    def emit(
        self,
        type_: str,
        payload: dict[str, Any],
        scenario: str | None = None,
        session: int | None = None,
    ) -> dict[str, Any]:
        if type_ not in EVENT_TYPES:
            raise ValueError(f"unknown event type: {type_}")
        self.seq += 1
        record = {
            "seq": self.seq,
            "ts": _utc_now(),
            "run_id": self.run_id,
            "scenario": scenario,
            "session": session,
            "type": type_,
            "payload": payload,
        }
        self._fh.write(json.dumps(record, ensure_ascii=True, sort_keys=True) + "\n")
        self._fh.flush()
        return record

    def close(self) -> None:
        self._fh.close()


def validate_trace(path: str) -> tuple[bool, list[str]]:
    """Re-read a trace from disk and check structural invariants."""
    errors: list[str] = []
    expected_seq = 0
    records = 0
    with open(path, "r", encoding="utf-8") as fh:
        for line_no, line in enumerate(fh, start=1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError as exc:
                errors.append(f"line {line_no}: invalid JSON ({exc})")
                continue
            records += 1
            expected_seq += 1
            for field in REQUIRED_FIELDS:
                if field not in record or record[field] in (None, ""):
                    errors.append(f"line {line_no}: missing/empty field '{field}'")
            if record.get("seq") != expected_seq:
                errors.append(
                    f"line {line_no}: seq is {record.get('seq')}, expected {expected_seq}"
                )
            if record.get("type") not in EVENT_TYPES:
                errors.append(f"line {line_no}: unknown type {record.get('type')!r}")
            if not isinstance(record.get("payload"), dict):
                errors.append(f"line {line_no}: payload is not an object")
    if records == 0:
        errors.append("trace is empty")
    return (not errors), errors
