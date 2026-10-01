"""CONT-000 smoke: one scenario, arm A, replayable trace.

Usage (from anywhere):
    python labs/continuity/experiments/CONT-000/run_smoke.py \
        [--model granite-code:8b] [--scenario dr-0001] [--seed 42]

The run directory under results/CONT-000/<run_id>/ is the evidence:
trace.jsonl, summary.json, env.json. A run "passes" the CONT-000 feasibility
endpoint when it completes without a budget stop and the trace re-validates
from disk (PB-067: the artifact is the proof, not the exit code).
"""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity import PROTOCOL_VERSION  # noqa: E402
from continuity.events import EventJournal, validate_trace  # noqa: E402
from continuity.fixtures import load_scenario  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import Budget, run_scenario  # noqa: E402


def git_rev() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(LAB_ROOT), stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="granite-code:8b")
    parser.add_argument("--scenario", default="dr-0001")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--num-ctx", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.0)
    args = parser.parse_args()

    run_id = time.strftime(f"cont000-smoke-{args.scenario}-%Y%m%d-%H%M%S")
    out_dir = LAB_ROOT / "results" / "CONT-000" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    fixture_path = LAB_ROOT / "fixtures" / "v1" / "delayed_recall" / f"{args.scenario}.json"
    family = "delayed_recall"
    if not fixture_path.exists():
        fixture_path = LAB_ROOT / "fixtures" / "v1" / "repeated_task" / f"{args.scenario}.json"
        family = "repeated_task"
    scenario = load_scenario(str(fixture_path))

    provider = OllamaProvider(
        model=args.model, temperature=args.temperature, seed=args.seed, num_ctx=args.num_ctx
    )
    journal = EventJournal(str(out_dir / "trace.jsonl"), run_id)
    journal.emit(
        "run.start",
        {
            "protocol_version": PROTOCOL_VERSION,
            "kind": "smoke",
            "scenario": scenario["id"],
            "model": args.model,
            "seed": args.seed,
            "temperature": args.temperature,
            "num_ctx": args.num_ctx,
            "git_rev": git_rev(),
        },
    )

    env_snapshot = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ollama_version": provider.version(),
        "model": args.model,
        "determinism_caveat": (
            "greedy+seed does not guarantee identical outputs across batch "
            "sizes or backends (PB-071)"
        ),
    }
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(json.dumps(env_snapshot, indent=2), encoding="utf-8")

    budget = Budget(max_turns=40, max_total_tokens=100_000, wall_clock_s=600)
    summary = run_scenario(scenario, provider, journal, budget)

    # Model identity is pinned after the run: the model is guaranteed loaded
    # (keep_alive) and /api/ps can attribute the digest (CN-001).
    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))
    summary["model_digest"] = pinned["digest"]

    trace_ok, trace_errors = validate_trace(str(out_dir / "trace.jsonl"))
    summary["run_id"] = run_id
    summary["trace_schema_valid"] = trace_ok
    summary["trace_validation_errors"] = trace_errors
    summary["completed"] = (not summary["stopped"]) and trace_ok

    journal.emit(
        "run.end",
        {"completed": summary["completed"], "trace_schema_valid": trace_ok},
    )
    journal.close()
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    print(f"run_id: {run_id}")
    print(f"completed: {summary['completed']} stopped: {summary['stopped']}")
    print(
        f"probes: {summary['probes_passed']}/{summary['probes_total']} passed; "
        f"turns: {summary['turns']}; tokens: {summary['tokens_total']}; "
        f"duration_s: {summary['duration_s']}"
    )
    for probe in summary["probes"]:
        print(
            f"  {probe['turn_ref']} {probe['kind']} expected={probe['expected']!r} "
            f"passed={probe['passed']} observed={probe['observed_normalized'][:80]!r}"
        )
    print(f"artifacts: {out_dir}")
    return 0 if summary["completed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
