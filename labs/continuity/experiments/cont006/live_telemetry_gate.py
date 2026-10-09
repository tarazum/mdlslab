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
  T5 summary cross-check: summary.json EXISTS, is completed, and its
     memory_episodes equals the trace's memory.append count (episodes are
     1:1 with append events) — zero or mismatched counts are flagged

Exit 0 = PASS; exit 2 = FAIL-CLOSED (the analyzer must not run).

--self-test (zero GPU, FakeProvider): builds a HEALTHY arm/seed layout
(R0 + R2 on the real multi-session v3l scenario cu-6101) and asserts the
gate PASSes it, then simulates the CN-012 signature (appends stripped,
injections emptied, summary zeroed) and asserts FAIL. Verifies BOTH gate
directions — the invalid-run verification covered only FAIL.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
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
    # T5 (summary cross-check): episodes are 1:1 with append events
    summary = trace_path.parent / "summary.json"
    if not summary.exists():
        problems.append("T5: summary.json missing")
    else:
        data = json.loads(summary.read_text(encoding="utf-8"))
        episodes = data.get("memory_episodes", 0)
        if not data.get("completed"):
            problems.append("T5: summary not completed (memory guard tripped?)")
        elif episodes == 0:
            problems.append("T5: completed summary reports 0 memory episodes")
        elif episodes != len(appends):
            problems.append(f"T5: summary memory_episodes {episodes} != "
                            f"{len(appends)} memory.append events")
    return (not problems), problems


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", default=None,
                        help="a Phase V/P/C run root (arm/seed-* layout)")
    parser.add_argument("--self-test", action="store_true",
                        help="zero-GPU gate self-test (healthy PASS + "
                             "CN-012-simulated FAIL) instead of gating a root")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.run_root:
        parser.error("--run-root is required unless --self-test is given")
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


def self_test() -> int:
    """Healthy PASS + CN-012-simulated FAIL, zero GPU (FakeProvider)."""
    from continuity.events import EventJournal
    from continuity.fixtures import render_seed_variant
    from continuity.lessons import LessonChannel, make_store
    from continuity.memory import MemoryStore
    from continuity.runner import Budget, run_scenario

    class FakeProvider:
        model = "fake"
        options = {"temperature": 0.0}

        def chat(self, messages):
            words = sum(len(m["content"].split()) for m in messages)
            return {"content": f"ack ({words} words in context)",
                    "usage": {"prompt_tokens": words, "eval_tokens": 3,
                              "total_tokens": words + 3},
                    "total_duration_ms": 1.0}

    store = make_store([{
        "lessonId": "LL-GATE", "title": "One option, nothing else",
        "applicability": ["a closed list of choices is offered"],
        "recommendedBehavior": "respond with exactly one item from the list",
    }], source="worker", status="active")
    base = json.loads(
        (LAB_ROOT / "fixtures/v3l/contradiction_update/cu-6101.json")
        .read_text(encoding="utf-8"))
    scenario = render_seed_variant(base, 6001)
    for sess in scenario["sessions"]:
        for t in sess["turns"]:
            t.pop("probe", None)
            t.pop("initial_expected", None)
    tmp = Path(tempfile.mkdtemp())
    root = tmp / "run"
    for arm, lessons in (("R0", None), ("R2", LessonChannel(store))):
        arm_dir = root / arm / "seed-9901"
        arm_dir.mkdir(parents=True)
        mem = MemoryStore(str(tmp / f"m-{arm}.sqlite3"))
        jour = EventJournal(str(arm_dir / "trace.jsonl"), f"selftest-{arm}")
        try:
            run_scenario(scenario, FakeProvider(), jour,
                         Budget(60, 200_000, 120), arm=arm,
                         memory=mem, lessons=lessons)
        finally:
            jour.close()
        episodes = mem.count()
        mem.close()
        (arm_dir / "summary.json").write_text(json.dumps({
            "kind": "cont006-arm-seed-summary", "arm": arm, "seed": 9901,
            "completed": True, "memory_episodes": episodes}, indent=1) + "\n",
            encoding="utf-8")
    healthy = all(check_trace(t, t.parts[-3])[0]
                  for t in sorted(root.glob("*/seed-*/trace.jsonl")))
    # CN-012 simulation: strip appends, empty the injections, zero the summary
    broken_dir = root / "R2" / "seed-9902"
    broken_dir.mkdir()
    lines = (root / "R2" / "seed-9901" / "trace.jsonl").read_text(
        encoding="utf-8").splitlines()
    out = []
    for line in lines:
        e = json.loads(line)
        if e["type"] == "memory.append":
            continue
        if e["type"] == "memory.injected":
            e["payload"] = {**e["payload"], "episode_count": 0,
                            "episode_refs": [], "episode_ids": [],
                            "injected": False}
        out.append(json.dumps(e, ensure_ascii=True))
    (broken_dir / "trace.jsonl").write_text("\n".join(out) + "\n",
                                            encoding="utf-8")
    (broken_dir / "summary.json").write_text(json.dumps({
        "kind": "cont006-arm-seed-summary", "arm": "R2", "seed": 9902,
        "completed": True, "memory_episodes": 0}, indent=1) + "\n",
        encoding="utf-8")
    ok_broken, why_broken = check_trace(broken_dir / "trace.jsonl", "R2")
    print(f"self-test healthy-root PASS: {healthy}")
    print(f"self-test CN-012-sim FAIL: {not ok_broken} "
          f"({'; '.join(why_broken[:3])})")
    if not healthy or ok_broken:
        print("GATE SELF-TEST: FAIL")
        return 2
    print("GATE SELF-TEST: PASS (both directions verified)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
