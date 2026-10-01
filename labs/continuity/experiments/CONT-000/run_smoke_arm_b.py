"""CONT-000 smoke, arm B: one scenario (dr-0001) with persistent memory.

Usage (from anywhere; take the shared GPU lock around this, see
shared/tooling/agent-resource-coordination/PROTOCOL.md):

    python labs/continuity/experiments/CONT-000/run_smoke_arm_b.py

Arm B = arm A + the SQLite memory store (M2). The M2 gate: the delayed-recall
probe (dr-0001 s2t1, expected "7") must now PASS — that is the whole point of
persistent memory — and the trace must re-validate from disk. Exit 0 only when
both hold (plus completion and no budget stop).

Fail-closed: if Ollama is unreachable, the model is missing, or the resident
digest does not match EXPECTED_DIGEST_PREFIX, nothing runs and the script
exits 2.
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
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import MEMORY_TOP_K, Budget, run_scenario  # noqa: E402

MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned since the P0a smoke (CN-001)
SEED = 42  # same seed as the arm-A smoke for direct comparison
TEMPERATURE = 0.0
NUM_CTX = 4096


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


def preflight(base_url: str) -> dict:
    probe = OllamaProvider(base_url=base_url, model=MODEL)
    try:
        version = probe.version()
    except Exception as exc:
        print(f"FAIL-CLOSED: Ollama unreachable at {base_url}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    warm = OllamaProvider(
        base_url=base_url, model=MODEL, temperature=TEMPERATURE, seed=0, num_ctx=NUM_CTX
    )
    warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
    pinned = probe.model_info()
    digest = pinned.get("digest", "")
    if not digest.startswith(EXPECTED_DIGEST_PREFIX):
        print(
            f"FAIL-CLOSED: resident digest {digest!r} does not match pinned prefix "
            f"{EXPECTED_DIGEST_PREFIX!r}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return {"ollama_version": version, "digest": digest, "size_vram": pinned.get("size_vram", 0)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--scenario", default="dr-0001")
    parser.add_argument("--seed", type=int, default=SEED)
    args = parser.parse_args()

    env = preflight(args.base_url)
    scenario = load_scenario(
        str(LAB_ROOT / "fixtures" / "v1" / "delayed_recall" / f"{args.scenario}.json")
    )

    run_id = time.strftime(f"cont000-smoke-armB-{args.scenario}-%Y%m%d-%H%M%S")
    out_dir = LAB_ROOT / "results" / "CONT-000" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)

    provider = OllamaProvider(
        base_url=args.base_url,
        model=MODEL,
        temperature=TEMPERATURE,
        seed=args.seed,
        num_ctx=NUM_CTX,
    )
    memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    journal = EventJournal(str(out_dir / "trace.jsonl"), run_id)
    journal.emit(
        "run.start",
        {
            "protocol_version": PROTOCOL_VERSION,
            "kind": "smoke-armB",
            "arm": "B",
            "scenario": scenario["id"],
            "model": MODEL,
            "seed": args.seed,
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "memory": {
                "backend": "sqlite",
                "db": "memory.sqlite3",
                "retrieval": "keyword/substring, same-scenario scope",
                "top_k": MEMORY_TOP_K,
                "injection": "one system message at session start (index >= 2)",
            },
            "git_rev": git_rev(),
        },
    )
    env_snapshot = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ollama_version": env["ollama_version"],
        "model": MODEL,
        "model_digest": env["digest"],
        "seed": args.seed,
        "arm": "B",
        "determinism_caveat": (
            "greedy+seed does not guarantee identical outputs across batch "
            "sizes or backends (PB-071)"
        ),
    }
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(
        json.dumps(env_snapshot, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    budget = Budget(max_turns=40, max_total_tokens=100_000, wall_clock_s=600)
    summary = run_scenario(
        scenario, provider, journal, budget, arm="B", memory=memory
    )

    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))
    summary["model_digest"] = pinned["digest"]

    memory_export = memory.export_json(str(out_dir / "memory-export.json"))
    summary["memory_episodes_total"] = memory_export["episode_count"]
    memory.close()

    trace_ok, trace_errors = validate_trace(str(out_dir / "trace.jsonl"))
    summary["run_id"] = run_id
    summary["trace_schema_valid"] = trace_ok
    summary["trace_validation_errors"] = trace_errors
    summary["completed"] = (not summary["stopped"]) and trace_ok
    probes_passed = summary["probes_passed"] == summary["probes_total"] and summary["probes_total"] > 0
    summary["all_probes_passed"] = probes_passed

    journal.emit(
        "run.end",
        {
            "completed": summary["completed"],
            "trace_schema_valid": trace_ok,
            "probes_passed": summary["probes_passed"],
            "probes_total": summary["probes_total"],
            "all_probes_passed": probes_passed,
        },
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
        f"memory episodes: {summary['memory_episodes_total']}"
    )
    for probe in summary["probes"]:
        print(
            f"  {probe['turn_ref']} {probe['kind']} expected={probe['expected']!r} "
            f"passed={probe['passed']} observed={probe['observed_normalized'][:80]!r}"
        )
    print(f"artifacts: {out_dir}")
    ok = summary["completed"] and probes_passed
    print(f"M2 smoke gate (arm B probe passes + trace valid): {ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
