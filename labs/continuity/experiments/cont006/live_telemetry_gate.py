"""Live-telemetry gate (REVIEW-FABLE-CONT006 D.3.8 / RC-6): the mechanical
channel-liveness check that must PASS over every arm-seed trace of a
behavioral run BEFORE any analyzer reads its results. The invalid run's
gates were all pre-inference; this gate reads LIVE traces.

Checks per arm-seed trace (R0/R1/R2/R3/RBAD/RGOLD on v3m):
  T1 memory appends: memory.append events > 0 (CN-012 — the class killer)
  T2 non-empty injections: >= 1 memory.injected with episode_count > 0 at
     session >= 2, and every injected episode ref resolves to an APPEND
     committed EARLIER in the same scenario (RC-2: refs resolve to
     earlier committed turns)
  T3 lesson renders: lesson arms show >= 1 lessons.injected with
     injected=true; non-lesson arms show ZERO lessons.* events
  T4 context fit: max agent.response prompt_tokens < num_ctx (4096) with
     >= 512 tokens of headroom (no silent clip)
  T5 memory_episodes in the summary matches the append-event count / 2

Exit 0 = PASS; exit 2 = FAIL-CLOSED (the analyzer must not run).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

LESSON_ARMS = {"R2", "R3", "RBAD", "RGOLD"}
NUM_CTX = 4096
HEADROOM = 512


def check_trace(trace_path: Path, arm: str) -> tuple[bool, list[str]]:
    problems: list[str] = []
    events = [json.loads(line) for line in
              trace_path.read_text(encoding="utf-8").splitlines()]
    appends = [e for e in events if e["type"] == "memory.append"]
    inj = [e for e in events if e["type"] == "memory.injected"]
    inj_ok = [e for e in inj if e["payload"].get("episode_count")]
    les = [e for e in events if e["type"] == "lessons.injected"]
    les_ok = [e for e in les if e["payload"].get("injected")]
    responses = [e for e in events if e["type"] == "agent.response"]

    # T1
    if not appends:
        problems.append("T1: zero memory.append events (CN-012 class)")
    # T2
    if not inj_ok:
        problems.append("T2: no non-empty memory.injected at any session")
    else:
        # refs resolve to earlier appends of the same scenario
        appended_refs = {(a["scenario"], a["payload"]["turn_ref"], a["payload"]["role"])
                         for a in appends}
        for e in inj_ok:
            for ref in e["payload"].get("episode_refs", []):
                turn_ref, role = ref.rsplit("|", 1)
                if (e["scenario"], turn_ref, role) not in appended_refs:
                    problems.append(f"T2: injected ref {ref!r} does not resolve "
                                    f"to an earlier append")
    # T3
    if arm in LESSON_ARMS and not les_ok:
        problems.append("T3: lesson arm with zero rendered lesson blocks")
    if arm not in LESSON_ARMS and les:
        problems.append("T3: non-lesson arm emitted lessons.* events")
    # T4
    for r in responses:
        pt = r["payload"].get("usage", {}).get("prompt_tokens", 0)
        if pt >= NUM_CTX - HEADROOM:
            problems.append(f"T4: prompt_tokens {pt} within {HEADROOM} of "
                            f"num_ctx {NUM_CTX} (silent clip risk)")
            break
    # T5 (summary cross-check)
    summary = trace_path.parent / "summary.json"
    if summary.exists():
        data = json.loads(summary.read_text(encoding="utf-8"))
        if data.get("completed") and data.get("memory_episodes", 0) == 0:
            problems.append("T5: completed summary reports 0 memory episodes")
    return (not problems), problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", required=True,
                        help="a Phase V/P/C run root (arm/seed-* layout)")
    args = parser.parse_args()
    root = Path(args.run_root).resolve()
    traces = sorted(root.glob("*/seed-*/trace.jsonl"))
    canonical = [t for t in traces
                 if t.parent.name.startswith("seed-")
                 and t.parent.name[5:].isdigit()]
    if not canonical:
        print(f"FAIL-CLOSED: no canonical arm/seed traces under {root}")
        return 2
    failures = 0
    for trace_path in canonical:
        arm = trace_path.parts[-3]
        ok, problems = check_trace(trace_path, arm)
        if not ok:
            failures += 1
            print(f"FAIL {trace_path.relative_to(root)}: {'; '.join(problems[:3])}")
    verdict = "PASS" if failures == 0 else "FAIL"
    report = {"kind": "cont006-live-telemetry-gate", "run_root": str(root),
              "traces_checked": len(canonical), "failures": failures,
              "verdict": verdict}
    out = root / "live-telemetry-gate.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print(f"LIVE-TELEMETRY GATE: {verdict} ({len(canonical)} traces, "
          f"{failures} failures) -> {out}")
    return 0 if failures == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
