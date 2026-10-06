"""CONT-005 CYCLE-2 PILOT run (frozen at FREEZE-A): 5 arms x 5 seeds over suite v3i.

Predeclared (frozen-config-v3a.json): arms order (T0, T1, A, T2, T3 — primary
arms FIRST so a budget overrun can only trim secondary arms per the
droppable-secondary clause), seeds {2001..2005} (each seed renders its OWN
predeclared content variant via load_suite_for_seed — the cycle-1 lesson:
temp-0 seeds on byte-identical prompts are one run, not five), model
granite-code:8b pinned by digest prefix 36c3c3b9683b (CN-001), temperature
0.0, options in every request (PB-071), one warm process per arm-seed
(PB-070), wall clock the GPU metric (CN-002).

The pilot's job is HEADROOM + SPREAD + ECHO (EVALUATION-PREP-v3 §2 clauses
1-4, computed by the frozen analyze_pilot_v3.py), NOT confirmation: no
bootstrap verdict is produced at this stage. Expectations ex ante:
  X1  per-family headroom evaluable: CR and CU family means inside
      (0.15, 0.85) in T0 and T1 (else that family is rebalanced in v3j);
  X2  between-seed spread measurable and reported with df=4 CI (routing:
      sd > 0.25 -> P4 stress row + owner sign-off);
  X3  live clusters >= 8/12 (else P5 row + owner sign-off);
  X4  no '[RESOLVED' bracket echo in any T2/T3 answer (else pre-authorized
      NOTE: prose fix at FREEZE-B);
  X5  guess probes: valid-label fraction ~1.0, max position share <= 0.5
      (the variant rotation should compress the cycle-1 position
      concentration; T0 0.5 is the named risk being addressed).

Artifacts under results/CONT-005-C2-PILOT/pilot-c2-<ts>/<arm>/seed-<n>/:
trace.jsonl (primary), summary.json, env.json, memory.sqlite3 (memory arms).
aggregate.json is derived. Fail-closed preflight (Ollama reachable, model
present, digest pinned, warmup). Wall guard: no NEW arm-seed starts after
170 min (PROCESS.md rule 6; 25 arm-seeds x ~5.5-6.5 min ~= 140-160 min per
EVALUATION-PREP-v3 §13). Transient-infra hardening: one hung request kills at
most one attempt; the WHOLE arm-seed retried fresh once (attempt-scoped dirs,
partials kept as evidence).

Usage:
    python labs/continuity/experiments/suite-v3/run_pilot_v3.py \
        [--base-url http://localhost:11434] [--resume <previous run root>]
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import statistics
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity import PROTOCOL_VERSION  # noqa: E402
from continuity.events import EventJournal, validate_trace  # noqa: E402
from continuity.fixtures import load_suite_for_seed  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider, ProviderError  # noqa: E402
from continuity.runner import Budget, run_scenario  # noqa: E402

TRANSIENT = (TimeoutError, ProviderError, OSError)

# --- Predeclared run configuration (frozen at FREEZE-A) ---
SEEDS: tuple[int, ...] = (2001, 2002, 2003, 2004, 2005)
ARMS: tuple[str, ...] = ("T0", "T1", "A", "T2", "T3")  # primary-first
MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned since P0a (CN-001)
TEMPERATURE = 0.0
NUM_CTX = 4096
NUM_PREDICT = 256  # CN-011
KEEP_ALIVE = "30m"
PILOT_WALL_CLOCK_S = 170 * 60.0
SCENARIO_BUDGET = {"max_turns": 40, "max_total_tokens": 100_000, "wall_clock_s": 600.0}
DETERMINISM_CAVEAT = "greedy+seed does not guarantee identical outputs (PB-071, CN-003); per-seed content variants make seeds true replicates regardless"

EXPECTATIONS_EX_ANTE = [
    "X1 per-family headroom: CR and CU family mean error inside (0.15, 0.85) in T0 and T1 (else rebalance that family in v3j at FREEZE-B)",
    "X2 between-seed spread: reported per arm with df=4 CI; sd > 0.25 -> P4 stress row + owner sign-off",
    "X3 live clusters (both primary arms inside (0.10, 0.90)) >= 8/12; else P5 row + owner sign-off",
    "X4 residual echo: zero '[RESOLVED' substrings in T2/T3 replies; else NOTE: prose fix at FREEZE-B (pre-authorized)",
    "X5 guess probes: valid-label fraction ~1.0, max position share <= 0.5 (variant rotation compresses position concentration)",
]


def git_rev() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(LAB_ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def preflight(base_url: str) -> dict[str, Any]:
    probe = OllamaProvider(base_url=base_url, model=MODEL)
    try:
        version = probe.version()
    except Exception as exc:
        print(f"FAIL-CLOSED: Ollama unreachable at {base_url}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    with urllib.request.urlopen(base_url + "/api/tags", timeout=30) as response:
        tags = [m.get("name", "") for m in json.loads(response.read().decode())["models"]]
    if MODEL not in tags:
        print(f"FAIL-CLOSED: model {MODEL!r} missing (tags: {tags})", file=sys.stderr)
        raise SystemExit(2)
    warm = OllamaProvider(base_url=base_url, model=MODEL, temperature=TEMPERATURE,
                          seed=0, num_ctx=NUM_CTX, keep_alive=KEEP_ALIVE)
    t0 = time.monotonic()
    warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
    warmup_s = round(time.monotonic() - t0, 1)
    pinned = probe.model_info()
    if not pinned.get("digest", "").startswith(EXPECTED_DIGEST_PREFIX):
        print(f"FAIL-CLOSED: digest {pinned.get('digest')!r} != pinned {EXPECTED_DIGEST_PREFIX!r}",
              file=sys.stderr)
        raise SystemExit(2)
    return {"ollama_version": version, "digest": pinned["digest"], "warmup_s": warmup_s}


def run_one(arm: str, seed: int, out_root: Path, run_id: str,
            base_url: str, env_common: dict[str, Any], attempt: int = 1) -> dict[str, Any]:
    stem = f"seed-{seed}" if attempt == 1 else f"seed-{seed}-a{attempt}"
    out_dir = out_root / arm / stem
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = OllamaProvider(base_url=base_url, model=MODEL, temperature=TEMPERATURE,
                              seed=seed, num_ctx=NUM_CTX, num_predict=NUM_PREDICT,
                              keep_alive=KEEP_ALIVE)
    memory = None
    if arm != "A":
        memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    journal = EventJournal(str(out_dir / "trace.jsonl"), f"{run_id}-{arm}-seed{seed}")
    try:
        # Per-seed variant rendering: the scenario list is seed-specific.
        _, scenarios = load_suite_for_seed(str(LAB_ROOT / "fixtures" / "v3i"), seed)
        return _run_one_body(arm, seed, scenarios, out_dir, out_root, run_id, provider,
                             journal, memory, env_common)
    finally:
        journal.close()  # release Windows handles before any dir moves (run-5 lesson)
        if memory is not None:
            memory.close()


def _run_one_body(arm: str, seed: int, scenarios: list[dict], out_dir: Path,
                  out_root: Path, run_id: str, provider: OllamaProvider,
                  journal: EventJournal, memory, env_common: dict[str, Any]) -> dict[str, Any]:
    journal.emit("run.start", {
        "protocol_version": PROTOCOL_VERSION, "kind": "cont005-c2-pilot",
        "pilot_run_id": run_id, "arm": arm, "model": MODEL, "seed": seed,
        "seeds_predeclared": list(SEEDS), "arms_predeclared": list(ARMS),
        "temperature": TEMPERATURE, "num_ctx": NUM_CTX, "keep_alive": KEEP_ALIVE,
        "scenario_order": [s["id"] for s in scenarios], "git_rev": env_common["git_rev"],
        "suite": "fixtures/v3i (per-seed rendered variants)", "expectations_ex_ante": EXPECTATIONS_EX_ANTE,
    })
    env_snapshot = {
        "python": platform.python_version(), "platform": platform.platform(),
        "ollama_version": env_common["ollama_version"], "model": MODEL,
        "model_digest": env_common["digest"], "arm": arm, "seed": seed,
        "determinism_caveat": DETERMINISM_CAVEAT,
    }
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(json.dumps(env_snapshot, indent=2), encoding="utf-8")

    started = time.monotonic()
    scenario_summaries: list[dict[str, Any]] = []
    budget_stops = 0
    for scenario in scenarios:
        budget = Budget(**SCENARIO_BUDGET)
        scenario_summaries.append(
            run_scenario(scenario, provider, journal, budget, arm=arm, memory=memory)
        )
        if scenario_summaries[-1]["stopped"]:
            budget_stops += 1
    wall_s = round(time.monotonic() - started, 1)
    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))

    scored = [p for s in scenario_summaries for p in s["probes"] if p["passed"] is not None]
    summary = {
        "run_id": f"{run_id}-{arm}-seed{seed}", "arm": arm, "seed": seed,
        "model": MODEL, "model_digest": pinned["digest"],
        "scenario_summaries": scenario_summaries,
        "probes_passed": sum(1 for p in scored if p["passed"]),
        "probes_total": len(scored),
        "guess_probes": sum(1 for s in scenario_summaries for p in s["probes"] if p["passed"] is None),
        "turns": sum(s["turns"] for s in scenario_summaries),
        "tokens_total": sum(s["tokens_total"] for s in scenario_summaries),
        "budget_stops": budget_stops, "wall_s": wall_s,
    }
    if memory is not None:
        summary["memory_episodes"] = memory.count()
    trace_ok, trace_errors = validate_trace(str(out_dir / "trace.jsonl"))
    summary["trace_schema_valid"] = trace_ok
    summary["trace_validation_errors"] = trace_errors
    summary["completed"] = (not budget_stops) and trace_ok and summary["probes_total"] > 0
    summary["dir"] = f"{arm}/{out_dir.name}"
    journal.emit("run.end", {
        "completed": summary["completed"], "trace_schema_valid": trace_ok,
        "probes_passed": summary["probes_passed"], "probes_total": summary["probes_total"],
        "wall_s": wall_s,
    })
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True),
                                          encoding="utf-8")
    return summary


def build_aggregate(run_id: str, out_root: Path, summaries: dict[tuple[str, int], dict],
                    env_common: dict) -> dict:
    per_arm: dict[str, Any] = {}
    for arm in ARMS:
        fam_pass: dict[str, list[int]] = {}
        guess = {"probes": 0, "valid_label": 0, "positions": {}}
        for seed in SEEDS:
            s_sum = summaries.get((arm, seed))
            if not s_sum:
                continue
            for sc in s_sum["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is None:
                        guess["probes"] += 1
                        pos = p.get("observed_position")
                        if p.get("observed_label") is not None:
                            guess["valid_label"] += 1
                        if pos is not None:
                            guess["positions"][str(pos)] = guess["positions"].get(str(pos), 0) + 1
                        continue
                    fam_pass.setdefault(sc["family"], []).append(1 if p["passed"] else 0)
        per_arm[arm] = {
            "per_family_pass": {
                f: {"mean": round(statistics.fmean(v), 3), "n": len(v)}
                for f, v in fam_pass.items()
            },
            "guess": {
                **guess,
                "valid_fraction": round(guess["valid_label"] / guess["probes"], 3)
                if guess["probes"] else None,
                "max_position_share": round(
                    max(guess["positions"].values()) / guess["probes"], 3
                ) if guess["positions"] else None,
            },
        }

    runs = [
        {
            "arm": s["arm"], "seed": s["seed"], "dir": s.get("dir", f"{s['arm']}/seed-{s['seed']}"),
            "completed": s["completed"], "trace_schema_valid": s["trace_schema_valid"],
            "budget_stops": s["budget_stops"], "probes_passed": s["probes_passed"],
            "probes_total": s["probes_total"], "guess_probes": s["guess_probes"],
            "turns": s["turns"], "tokens_total": s["tokens_total"],
            "wall_s": s["wall_s"], **({"memory_episodes": s["memory_episodes"]} if "memory_episodes" in s else {}),
        }
        for s in summaries.values()
    ]
    total_wall = round(sum(s["wall_s"] for s in summaries.values()), 1)
    return {
        "pilot": {
            "run_id": run_id, "kind": "cont005-c2-pilot",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_rev": env_common["git_rev"], "model": MODEL,
            "model_digest": env_common["digest"], "ollama_version": env_common["ollama_version"],
            "arms_predeclared": list(ARMS), "seeds_predeclared": list(SEEDS),
            "suite": "fixtures/v3i (27 scenarios, per-seed rendered variants)",
            "expectations_ex_ante": EXPECTATIONS_EX_ANTE,
            "determinism_caveat": DETERMINISM_CAVEAT,
            "gpu_note": "run held the shared gpu lock; wall clock is the GPU metric (CN-002)",
            "total_wall_s": total_wall, "total_tokens": sum(s["tokens_total"] for s in summaries.values()),
            "requests_estimated": sum(s["turns"] for s in summaries.values()),
        },
        "runs": runs,
        "per_arm": per_arm,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument(
        "--resume", default=None,
        help="previous pilot run root: completed arm-seeds are copied (zero repeated inference)",
    )
    args = parser.parse_args()

    _, scenarios_first = load_suite_for_seed(str(LAB_ROOT / "fixtures" / "v3i"), SEEDS[0])
    total_turns = sum(len(sess["turns"]) for s in scenarios_first for sess in s["sessions"])
    print(f"suite v3i: {len(scenarios_first)} scenarios, {total_turns} turns/seed (per-seed variants)")
    print(f"plan: {len(ARMS)} arms x {len(SEEDS)} seeds = {len(ARMS) * len(SEEDS)} arm-seeds "
          f"({len(ARMS) * len(SEEDS) * total_turns} requests)")

    env_common = preflight(args.base_url)
    env_common["git_rev"] = git_rev()
    print(f"preflight ok: ollama {env_common['ollama_version']}, digest "
          f"{env_common['digest'][:12]}..., warmup {env_common['warmup_s']}s")

    run_id = time.strftime("pilot-c2-%Y%m%d-%H%M%S")
    out_root = LAB_ROOT / "results" / "CONT-005-C2-PILOT" / run_id
    out_root.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    summaries: dict[tuple[str, int], dict] = {}
    skipped: list[str] = []
    resumed: list[str] = []
    if args.resume:
        resume_root = Path(args.resume)
        for arm in ARMS:
            for seed in SEEDS:
                prev = None
                for stem in (f"seed-{seed}", f"seed-{seed}-a2"):
                    candidate = resume_root / arm / stem / "summary.json"
                    if candidate.exists():
                        prev = candidate
                        break
                if prev is None:
                    continue
                prev_summary = json.loads(prev.read_text(encoding="utf-8"))
                if not prev_summary.get("completed"):
                    continue
                dest = out_root / arm / prev.parent.name
                shutil.copytree(prev.parent, dest)
                summaries[(arm, seed)] = prev_summary
                resumed.append(f"{arm}/seed-{seed}")
                print(f"resumed {arm}/seed-{seed} (completed, zero repeated inference)")
    for arm in ARMS:
        for seed in SEEDS:
            if (arm, seed) in summaries:
                continue
            elapsed = time.monotonic() - started
            if elapsed > PILOT_WALL_CLOCK_S:
                skipped.append(f"{arm}/seed-{seed}")
                print(f"wall guard hit ({elapsed:.0f}s): skipping {arm}/seed-{seed}",
                      file=sys.stderr)
                continue
            print(f"--- {arm} seed {seed} ({time.strftime('%H:%M:%S')})")
            placed = False
            for attempt in (1, 2):
                try:
                    summaries[(arm, seed)] = run_one(arm, seed, out_root, run_id,
                                                     args.base_url, env_common, attempt=attempt)
                    placed = True
                    break
                except TRANSIENT as exc:
                    msg = f"{arm}/seed-{seed} attempt {attempt} failed: {type(exc).__name__}: {str(exc)[:100]}"
                    if attempt == 1:
                        print(msg + " -> retrying the arm-seed fresh in 15s", file=sys.stderr)
                        time.sleep(15)
                    else:
                        print(msg + " -> giving up on this arm-seed", file=sys.stderr)
            if not placed:
                skipped.append(f"{arm}/seed-{seed} (transient x2)")
                continue
            s = summaries[(arm, seed)]
            print(f"{arm} seed {seed}: scored {s['probes_passed']}/{s['probes_total']} "
                  f"(+{s['guess_probes']} guess), tokens {s['tokens_total']}, "
                  f"wall {s['wall_s']}s, completed={s['completed']}")

    aggregate = build_aggregate(run_id, out_root, summaries, env_common)
    aggregate["pilot"]["skipped"] = skipped
    if resumed:
        aggregate["pilot"]["resumed_from"] = str(Path(args.resume).name)
        aggregate["pilot"]["resumed_arm_seeds"] = resumed
    (out_root / "aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=True),
                                             encoding="utf-8")
    print(f"\naggregate: {out_root / 'aggregate.json'}")
    for arm in ARMS:
        pa = aggregate["per_arm"].get(arm, {})
        fams = ", ".join(f"{f}={v['mean']}" for f, v in sorted(pa.get("per_family_pass", {}).items()))
        g = pa.get("guess", {})
        print(f"  {arm}: {fams}; guess valid {g.get('valid_fraction')}, maxpos {g.get('max_position_share')}")
    ok = all(s["completed"] for s in summaries.values()) and not skipped and len(summaries) == len(ARMS) * len(SEEDS)
    print(f"pilot completed={ok}")
    print(f"NEXT: python labs/continuity/experiments/suite-v3/analyze_pilot_v3.py --run-root {out_root}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
