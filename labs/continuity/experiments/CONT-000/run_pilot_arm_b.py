"""CONT-000 mini-pilot, arm B: full fixture suite x predeclared seeds, one warm
process, per-seed persistent memory (M2).

Usage (from anywhere; take the shared GPU lock around this, see
shared/tooling/agent-resource-coordination/PROTOCOL.md):

    python labs/continuity/experiments/CONT-000/run_pilot_arm_b.py

Mirrors run_pilot_arm_a.py (M1) with the arm-B additions:
- arm="B" passed to run_scenario; one SQLite memory store per seed run
  (retrieval scoped to the current scenario), exported to a portable
  memory-export.json per seed (the future CONT-002 state carrier);
- the run.start event and aggregate carry the memory configuration;
- after the runs, an arm A vs arm B comparison artifact for the
  delayed_recall family is written next to the aggregate (arm A numbers are
  read from the M1 pilot aggregate, never re-run).

Fail-closed: if Ollama is unreachable, the model is missing, or the resident
digest does not match EXPECTED_DIGEST_PREFIX, nothing runs and the script
exits 2.
"""

from __future__ import annotations

import argparse
import json
import platform
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
from continuity.fixtures import load_suite  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import MEMORY_TOP_K, Budget, run_scenario  # noqa: E402

# --- Predeclared run configuration (fixed BEFORE any pilot run) ---
SEEDS: tuple[int, ...] = (11, 22, 33)
MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned by the P0a smoke (CN-001)
TEMPERATURE = 0.0
NUM_CTX = 4096
KEEP_ALIVE = "30m"
PILOT_WALL_CLOCK_S = 25 * 60.0  # leaves margin inside the 30 min GPU budget
SCENARIO_BUDGET = {"max_turns": 40, "max_total_tokens": 100_000, "wall_clock_s": 600.0}

DETERMINISM_CAVEAT = (
    "greedy+seed does not guarantee identical outputs across batch sizes or "
    "backends (PB-071)"
)


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


def ollama_tags(base_url: str) -> list[str]:
    with urllib.request.urlopen(base_url + "/api/tags", timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return [m.get("name", "") for m in data.get("models", [])]


def preflight(base_url: str, model: str) -> dict[str, Any]:
    """Fail-closed checks + warmup. Returns the pinned model info."""
    probe = OllamaProvider(base_url=base_url, model=model)
    try:
        version = probe.version()
    except Exception as exc:
        print(f"FAIL-CLOSED: Ollama unreachable at {base_url}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    try:
        tags = ollama_tags(base_url)
    except Exception as exc:
        print(f"FAIL-CLOSED: /api/tags failed: {exc}", file=sys.stderr)
        raise SystemExit(2)
    if model not in tags:
        print(
            f"FAIL-CLOSED: model {model!r} missing from Ollama (tags: {tags})",
            file=sys.stderr,
        )
        raise SystemExit(2)
    warm = OllamaProvider(
        base_url=base_url, model=model, temperature=TEMPERATURE, seed=0, num_ctx=NUM_CTX,
        keep_alive=KEEP_ALIVE,
    )
    warmup_started = time.monotonic()
    warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
    warmup_s = round(time.monotonic() - warmup_started, 1)
    pinned = probe.model_info()
    digest = pinned.get("digest", "")
    if not digest.startswith(EXPECTED_DIGEST_PREFIX):
        print(
            f"FAIL-CLOSED: resident digest {digest!r} does not match pinned prefix "
            f"{EXPECTED_DIGEST_PREFIX!r}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return {"ollama_version": version, "digest": digest, "warmup_s": warmup_s, **pinned}


def run_one_seed(
    seed: int,
    scenarios: list[dict],
    out_root: Path,
    pilot_run_id: str,
    base_url: str,
    env_common: dict[str, Any],
) -> dict[str, Any]:
    run_id = f"{pilot_run_id}-seed{seed}"
    out_dir = out_root / f"seed-{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    provider = OllamaProvider(
        base_url=base_url,
        model=MODEL,
        temperature=TEMPERATURE,
        seed=seed,
        num_ctx=NUM_CTX,
        keep_alive=KEEP_ALIVE,
    )
    memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    journal = EventJournal(str(out_dir / "trace.jsonl"), run_id)
    journal.emit(
        "run.start",
        {
            "protocol_version": PROTOCOL_VERSION,
            "kind": "pilot-armB",
            "pilot_run_id": pilot_run_id,
            "arm": "B",
            "model": MODEL,
            "seed": seed,
            "seeds_predeclared": list(SEEDS),
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "keep_alive": KEEP_ALIVE,
            "memory": {
                "backend": "sqlite",
                "db": "memory.sqlite3",
                "retrieval": "keyword/substring, same-scenario scope",
                "top_k": MEMORY_TOP_K,
                "injection": "one system message at session start (index >= 2)",
                "export": "memory-export.json (portable, model-neutral)",
            },
            "scenario_order": [s["id"] for s in scenarios],
            "git_rev": env_common["git_rev"],
        },
    )
    env_snapshot = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ollama_version": env_common["ollama_version"],
        "model": MODEL,
        "model_digest": env_common["digest"],
        "seed": seed,
        "arm": "B",
        "determinism_caveat": DETERMINISM_CAVEAT,
    }
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(
        json.dumps(env_snapshot, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    started = time.monotonic()
    scenario_summaries: list[dict[str, Any]] = []
    budget_stops = 0
    for scenario in scenarios:
        budget = Budget(**SCENARIO_BUDGET)
        scenario_summaries.append(
            run_scenario(scenario, provider, journal, budget, arm="B", memory=memory)
        )
        if scenario_summaries[-1]["stopped"]:
            budget_stops += 1
    wall_s = round(time.monotonic() - started, 1)

    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))

    memory_export = memory.export_json(str(out_dir / "memory-export.json"))
    memory.close()

    summary: dict[str, Any] = {
        "run_id": run_id,
        "seed": seed,
        "arm": "B",
        "model": MODEL,
        "model_digest": pinned["digest"],
        "scenario_summaries": scenario_summaries,
        "probes_passed": sum(s["probes_passed"] for s in scenario_summaries),
        "probes_total": sum(s["probes_total"] for s in scenario_summaries),
        "turns": sum(s["turns"] for s in scenario_summaries),
        "tokens_total": sum(s["tokens_total"] for s in scenario_summaries),
        "budget_stops": budget_stops,
        "wall_s": wall_s,
        "memory_episodes_total": memory_export["episode_count"],
        "memory_export": "memory-export.json",
    }
    trace_ok, trace_errors = validate_trace(str(out_dir / "trace.jsonl"))
    summary["trace_schema_valid"] = trace_ok
    summary["trace_validation_errors"] = trace_errors
    summary["completed"] = (
        (not summary["budget_stops"]) and trace_ok and summary["probes_total"] > 0
    )
    journal.emit(
        "run.end",
        {
            "completed": summary["completed"],
            "trace_schema_valid": trace_ok,
            "probes_passed": summary["probes_passed"],
            "probes_total": summary["probes_total"],
            "wall_s": wall_s,
        },
    )
    journal.close()
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    return summary


def parse_request_stats(trace_path: Path) -> list[dict[str, Any]]:
    """Per-request stats from agent.response events (the trace is primary)."""
    stats: list[dict[str, Any]] = []
    with open(trace_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") != "agent.response":
                continue
            payload = record["payload"]
            stats.append(
                {
                    "scenario": record.get("scenario"),
                    "turn_ref": payload.get("turn_ref"),
                    "prompt_tokens": payload["usage"]["prompt_tokens"],
                    "eval_tokens": payload["usage"]["eval_tokens"],
                    "total_duration_ms": payload["total_duration_ms"],
                }
            )
    return stats


def parse_memory_events(trace_path: Path) -> dict[str, Any]:
    """Memory-injection evidence from the trace (episode counts per scenario)."""
    injected: dict[str, int] = {}
    appended = 0
    with open(trace_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == "memory.injected":
                scenario = record.get("scenario") or "?"
                injected[scenario] = injected.get(scenario, 0) + record["payload"][
                    "episode_count"
                ]
            elif record.get("type") == "memory.append":
                appended += 1
    return {"appended_events": appended, "injected_episodes_by_scenario": injected}


def percentile(sorted_values: list[float], q: float) -> float:
    if not sorted_values:
        return 0.0
    idx = min(len(sorted_values) - 1, max(0, round(q * (len(sorted_values) - 1))))
    return sorted_values[idx]


def build_aggregate(
    pilot_run_id: str,
    out_root: Path,
    seeds_run: list[int],
    seeds_skipped: list[int],
    scenario_defs: list[dict],
    run_summaries: list[dict[str, Any]],
    request_stats: list[dict[str, Any]],
    memory_stats: list[dict[str, Any]],
    env_common: dict[str, Any],
) -> dict[str, Any]:
    scenario_order = [s["id"] for s in scenario_defs]

    runs = [
        {
            "seed": r["seed"],
            "run_id": r["run_id"],
            "dir": f"seed-{r['seed']}",
            "completed": r["completed"],
            "trace_schema_valid": r["trace_schema_valid"],
            "budget_stops": r["budget_stops"],
            "probes_passed": r["probes_passed"],
            "probes_total": r["probes_total"],
            "turns": r["turns"],
            "tokens_total": r["tokens_total"],
            "wall_s": r["wall_s"],
            "memory_episodes_total": r["memory_episodes_total"],
        }
        for r in run_summaries
    ]

    per_family: dict[str, Any] = {}
    per_scenario: dict[str, Any] = {}
    for r in run_summaries:
        by_seed_family: dict[str, list[int]] = {}
        for s in r["scenario_summaries"]:
            by_seed_family.setdefault(s["family"], []).extend(
                1 if p["passed"] else 0 for p in s["probes"]
            )
            for p in s["probes"]:
                slot = per_scenario.setdefault(
                    s["scenario"],
                    {
                        "family": s["family"],
                        "probe_results": {},
                        "pass_count": 0,
                        "observations_by_seed": {},
                    },
                )
                slot["probe_results"].setdefault(
                    p["turn_ref"], {"kind": p["kind"], "expected": p["expected"]}
                )
                slot["observations_by_seed"].setdefault(r["seed"], []).append(
                    {
                        "turn_ref": p["turn_ref"],
                        "passed": p["passed"],
                        "observed_normalized": p["observed_normalized"],
                    }
                )
                slot["pass_count"] += 1 if p["passed"] else 0
        for family, results in by_seed_family.items():
            entry = per_family.setdefault(
                family, {"pass_rate_by_seed": {}, "passed_by_seed": {}, "probes_per_seed": 0}
            )
            entry["passed_by_seed"][r["seed"]] = sum(results)
            entry["pass_rate_by_seed"][r["seed"]] = round(sum(results) / len(results), 3)
            entry["probes_per_seed"] = len(results)

    for family, entry in per_family.items():
        rates = list(entry["pass_rate_by_seed"].values())
        entry["spread"] = {
            "min": min(rates),
            "max": max(rates),
            "range": round(max(rates) - min(rates), 3),
            "mean": round(statistics.fmean(rates), 3) if len(rates) > 1 else rates[0],
        }

    latencies = sorted(st["total_duration_ms"] for st in request_stats)
    prompt_tokens = [st["prompt_tokens"] for st in request_stats]
    eval_tokens = [st["eval_tokens"] for st in request_stats]

    return {
        "pilot": {
            "run_id": pilot_run_id,
            "kind": "pilot-armB",
            "arm": "B",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_rev": env_common["git_rev"],
            "model": MODEL,
            "model_digest": env_common["digest"],
            "ollama_version": env_common["ollama_version"],
            "python": platform.python_version(),
            "warmup_s": env_common["warmup_s"],
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "keep_alive": KEEP_ALIVE,
            "seeds_predeclared": list(SEEDS),
            "seeds_run": seeds_run,
            "seeds_skipped": seeds_skipped,
            "scenario_order": scenario_order,
            "fixture_families": sorted({s["family"] for s in scenario_defs}),
            "scenarios": len(scenario_defs),
            "probes_per_seed_per_scenario": 1,
            "memory": {
                "backend": "sqlite (stdlib)",
                "scope": "one store per seed; retrieval scoped to current scenario",
                "retrieval": "keyword/substring scoring (word=1.0, extra substring=0.5)",
                "top_k": MEMORY_TOP_K,
                "injection_rule": (
                    "at session start with index >= 2, one system message after the "
                    "base prompt; query = the session's first environment turn"
                ),
                "export_format": "continuity-memory-export v1 (model-neutral JSON)",
            },
            "determinism_caveat": DETERMINISM_CAVEAT,
            "gpu_lock_note": (
                "run held the shared gpu lock; any nvidia-smi 'busy' at start was "
                "attributed via ollama /api/ps (CN-005 monitoring rule)"
            ),
        },
        "runs": runs,
        "per_family": per_family,
        "per_scenario": per_scenario,
        "memory_stats": memory_stats,
        "request_stats": {
            "count": len(request_stats),
            "latency_ms": {
                "mean": round(statistics.fmean(latencies), 1) if latencies else 0,
                "median": round(statistics.median(latencies), 1) if latencies else 0,
                "p90": percentile(latencies, 0.90),
                "p95": percentile(latencies, 0.95),
                "min": latencies[0] if latencies else 0,
                "max": latencies[-1] if latencies else 0,
            },
            "tokens": {
                "prompt_sum": sum(prompt_tokens),
                "eval_sum": sum(eval_tokens),
                "total_sum": sum(prompt_tokens) + sum(eval_tokens),
                "prompt_mean": round(statistics.fmean(prompt_tokens), 1)
                if prompt_tokens
                else 0,
                "eval_mean": round(statistics.fmean(eval_tokens), 1) if eval_tokens else 0,
            },
        },
    }


def find_arm_a_aggregate(explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise SystemExit(f"FAIL-CLOSED: arm-A aggregate not found: {path}")
        return path
    candidates = sorted(
        (LAB_ROOT / "results" / "CONT-000").glob("pilot-armA-*/aggregate.json")
    )
    if not candidates:
        raise SystemExit("FAIL-CLOSED: no arm-A pilot aggregate found under results/CONT-000")
    return candidates[-1]


def build_comparison(
    arm_b_aggregate: dict[str, Any], arm_a_path: Path, out_dir: Path
) -> dict[str, Any]:
    """Small A-vs-B artifact for the delayed_recall family (numbers only)."""
    arm_a = json.loads(arm_a_path.read_text(encoding="utf-8"))
    family = "delayed_recall"
    comparison = {
        "kind": "armA-vs-armB-delayed_recall",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "family": family,
        "arm_a_source": str(arm_a_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_b_source": "aggregate.json (this directory)",
        "shared_config": {
            "model": arm_a["pilot"]["model"],
            "model_digest": arm_a["pilot"]["model_digest"],
            "temperature": arm_a["pilot"]["temperature"],
            "num_ctx": arm_a["pilot"]["num_ctx"],
            "scenario_order": arm_a["pilot"]["scenario_order"],
            "note": (
                "seeds differ by design (arm A: 5 predeclared M1 seeds; arm B: first "
                "3 of the same predeclared list, per the M2 brief)"
            ),
        },
        "arm_a": {
            "seeds": arm_a["pilot"]["seeds_run"],
            "pass_rate_by_seed": arm_a["per_family"][family]["pass_rate_by_seed"],
            "passed_by_seed": arm_a["per_family"][family]["passed_by_seed"],
            "probes_per_seed": arm_a["per_family"][family]["probes_per_seed"],
            "mean_pass_rate": arm_a["per_family"][family]["spread"]["mean"],
            "per_scenario_pass_count": {
                sid: entry["pass_count"] if entry["family"] == family else None
                for sid, entry in arm_a["per_scenario"].items()
                if entry["family"] == family
            },
        },
        "arm_b": {
            "seeds": arm_b_aggregate["pilot"]["seeds_run"],
            "pass_rate_by_seed": arm_b_aggregate["per_family"][family][
                "pass_rate_by_seed"
            ],
            "passed_by_seed": arm_b_aggregate["per_family"][family]["passed_by_seed"],
            "probes_per_seed": arm_b_aggregate["per_family"][family]["probes_per_seed"],
            "mean_pass_rate": arm_b_aggregate["per_family"][family]["spread"]["mean"],
            "per_scenario_pass_count": {
                sid: entry["pass_count"]
                for sid, entry in arm_b_aggregate["per_scenario"].items()
                if entry["family"] == family
            },
        },
    }
    comparison["delta_mean_pass_rate"] = round(
        comparison["arm_b"]["mean_pass_rate"] - comparison["arm_a"]["mean_pass_rate"], 3
    )

    (out_dir / "armA-vs-armB-delayed_recall.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    a = comparison["arm_a"]
    b = comparison["arm_b"]
    lines = [
        "# Arm A vs arm B — delayed_recall family (M2 mini-pilot)",
        "",
        f"- arm A source: `{comparison['arm_a_source']}` (seeds {a['seeds']})",
        f"- arm B source: `{comparison['arm_b_source']}` (seeds {b['seeds']})",
        f"- model {comparison['shared_config']['model']}, digest "
        f"`{comparison['shared_config']['model_digest'][:12]}…`, temp "
        f"{comparison['shared_config']['temperature']}, num_ctx "
        f"{comparison['shared_config']['num_ctx']}",
        "",
        "| arm | pass rate by seed | mean |",
        "| --- | --- | --- |",
        f"| A (no persistent memory) | {a['pass_rate_by_seed']} | {a['mean_pass_rate']} |",
        f"| B (SQLite persistent memory) | {b['pass_rate_by_seed']} | {b['mean_pass_rate']} |",
        "",
        f"Delta (B - A) mean pass rate: **{comparison['delta_mean_pass_rate']:+.3f}**",
        "",
        "Per-scenario pass counts (passed probes / seeds x 1 probe):",
        "",
        "| scenario | arm A | arm B |",
        "| --- | --- | --- |",
    ]
    for sid in comparison["shared_config"]["scenario_order"]:
        if sid in a["per_scenario_pass_count"] or sid in b["per_scenario_pass_count"]:
            lines.append(
                f"| {sid} | {a['per_scenario_pass_count'].get(sid, 0)}/{len(a['seeds'])} "
                f"| {b['per_scenario_pass_count'].get(sid, 0)}/{len(b['seeds'])} |"
            )
    lines += [
        "",
        "Exploratory mini-pilot numbers only; not the confirmatory CONT-001 contrast.",
    ]
    (out_dir / "armA-vs-armB-delayed_recall.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument(
        "--arm-a-aggregate",
        default=None,
        help="path to the arm-A pilot aggregate.json (default: newest pilot-armA-*)",
    )
    args = parser.parse_args()

    fixture_dir = LAB_ROOT / "fixtures" / "v1"
    manifest, scenarios = load_suite(str(fixture_dir))
    total_turns = sum(len(s["turns"]) for s in scenarios for s in s["sessions"])
    print(f"suite: {len(scenarios)} scenarios, families={manifest['families']}")
    print(
        f"plan: {len(SEEDS)} seeds x {total_turns} turns = "
        f"{len(SEEDS) * total_turns} requests (predeclared seeds {list(SEEDS)})"
    )

    env_common = preflight(args.base_url, MODEL)
    env_common["git_rev"] = git_rev()
    print(
        f"preflight ok: ollama {env_common['ollama_version']}, digest "
        f"{env_common['digest'][:12]}..., warmup {env_common['warmup_s']}s"
    )

    pilot_run_id = time.strftime("pilot-armB-%Y%m%d-%H%M%S")
    out_root = LAB_ROOT / "results" / "CONT-000" / pilot_run_id
    out_root.mkdir(parents=True, exist_ok=True)

    pilot_started = time.monotonic()
    run_summaries: list[dict[str, Any]] = []
    seeds_run: list[int] = []
    seeds_skipped: list[int] = []
    for seed in SEEDS:
        elapsed = time.monotonic() - pilot_started
        if elapsed > PILOT_WALL_CLOCK_S:
            seeds_skipped.append(seed)
            print(
                f"pilot wall-clock guard hit ({elapsed:.0f}s): skipping seed {seed}",
                file=sys.stderr,
            )
            continue
        print(f"--- seed {seed} starting ({time.strftime('%H:%M:%S')})")
        seeds_run.append(seed)
        run_summaries.append(
            run_one_seed(seed, scenarios, out_root, pilot_run_id, args.base_url, env_common)
        )
        r = run_summaries[-1]
        print(
            f"seed {seed}: probes {r['probes_passed']}/{r['probes_total']}, "
            f"turns {r['turns']}, tokens {r['tokens_total']}, "
            f"episodes {r['memory_episodes_total']}, wall {r['wall_s']}s, "
            f"completed={r['completed']}"
        )

    request_stats: list[dict[str, Any]] = []
    memory_stats: list[dict[str, Any]] = []
    for r in run_summaries:
        seed_dir = out_root / f"seed-{r['seed']}"
        request_stats.extend(parse_request_stats(seed_dir / "trace.jsonl"))
        memory_stats.append({"seed": r["seed"], **parse_memory_events(seed_dir / "trace.jsonl")})

    aggregate = build_aggregate(
        pilot_run_id, out_root, seeds_run, seeds_skipped, scenarios, run_summaries,
        request_stats, memory_stats, env_common,
    )
    aggregate["pilot"]["wall_clock_s"] = round(time.monotonic() - pilot_started, 1)
    (out_root / "aggregate.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    arm_a_path = find_arm_a_aggregate(args.arm_a_aggregate)
    comparison = build_comparison(aggregate, arm_a_path, out_root)

    print(f"\naggregate: {out_root / 'aggregate.json'}")
    for family, entry in aggregate["per_family"].items():
        print(
            f"  {family:22s} pass_rate_by_seed={entry['pass_rate_by_seed']} "
            f"spread={entry['spread']}"
        )
    lat = aggregate["request_stats"]["latency_ms"]
    tok = aggregate["request_stats"]["tokens"]
    print(
        f"  requests={aggregate['request_stats']['count']} "
        f"latency_ms(mean/p95/max)={lat['mean']}/{lat['p95']}/{lat['max']} "
        f"tokens(prompt/eval sums)={tok['prompt_sum']}/{tok['eval_sum']}"
    )
    print(
        f"comparison: {out_root / 'armA-vs-armB-delayed_recall.json'} "
        f"(delta mean pass rate {comparison['delta_mean_pass_rate']:+.3f}; "
        f"arm-A source {arm_a_path.name})"
    )
    ok = all(r["completed"] for r in run_summaries) and not seeds_skipped
    print(f"pilot completed={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
