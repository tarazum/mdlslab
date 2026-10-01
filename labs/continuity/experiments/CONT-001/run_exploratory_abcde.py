"""CONT-001 exploratory multi-arm run: arms A-E x full fixture suite x
predeclared seeds {11, 22, 33, 44, 55} (seed count per docs/SIZING.md),
one warm process for the whole batch (M6).

Usage (from anywhere; take the shared GPU lock around this, see
shared/tooling/agent-resource-coordination/PROTOCOL.md):

    python labs/continuity/experiments/CONT-001/run_exploratory_abcde.py

What this is (and is NOT):

- EXPLORATORY. The M1-M5 mini-pilots used seeds {11,22,33} for arms B-E and
  5 seeds for arm A; this run re-runs ALL arms at the SIZING.md seed count
  so the cross-arm table has a uniform basis. Fixtures and arm semantics
  are untouched (M1-M5 comparability is the point).
- NOT the confirmatory CONT-001 run (M7) and NOT a calibration input for
  the held-out fixture v2. Numbers here feed the pre-registration
  (docs/EVALUATION-PREP.md) as EXPLORATORY evidence only.

Layout (under results/CONT-001-exploratory/<run_id>/):

    arm-<X>/seed-<n>/{trace.jsonl, summary.json, env.json
                      [, memory.sqlite3, memory-export.json, selfmodel-run.json]}
    arm-<X>/aggregate-arm-<X>.json
    cross-arm-table.json / cross-arm-table.md   (normalized comparison)
    pilot-consistency.json                       (re-run vs M1-M5 outcomes)

Fail-closed: if Ollama is unreachable, the model is missing, the resident
digest does not match EXPECTED_DIGEST_PREFIX, or the self-model store does
not validate, nothing runs and the script exits 2.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import statistics
import sys
import time
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))
sys.path.insert(0, str(LAB_ROOT / "experiments" / "CONT-000"))  # pilot helpers

from continuity import PROTOCOL_VERSION  # noqa: E402
from continuity.events import EventJournal, validate_trace  # noqa: E402
from continuity.fixtures import load_suite  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.reflection import ReflectionEngine  # noqa: E402
from continuity.runner import MEMORY_TOP_K, Budget, run_scenario  # noqa: E402
from continuity.selfmodel import load as load_selfmodel  # noqa: E402
from continuity.selfmodel import selfmodel_sha256  # noqa: E402
from continuity.worldmodel import WorldModel  # noqa: E402

from run_pilot_arm_b import (  # noqa: E402
    DETERMINISM_CAVEAT,
    git_rev,
    parse_memory_events,
    parse_request_stats,
    percentile,
    preflight,
)
from run_pilot_arm_d import (  # noqa: E402
    find_aggregate,
    gpu_snapshot,
    parse_reflection_events,
)
from run_pilot_arm_e import (  # noqa: E402
    parse_policy_events,
    parse_worldmodel_events,
    pooled_calibration,
)

# --- Predeclared run configuration (fixed BEFORE any run; SIZING.md: 5 seeds) ---
SEEDS: tuple[int, ...] = (11, 22, 33, 44, 55)
ARMS: tuple[str, ...] = ("A", "B", "C", "D", "E")
MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned by the P0a smoke (CN-001)
TEMPERATURE = 0.0
NUM_CTX = 4096
KEEP_ALIVE = "30m"
RUN_WALL_CLOCK_S = 100 * 60.0  # seed-skip guard; M6 budget is 150 min wall
SCENARIO_BUDGET = {"max_turns": 40, "max_total_tokens": 100_000, "wall_clock_s": 600.0}
DEFAULT_SELFMODEL = LAB_ROOT / "state" / "selfmodel.json"

RUN_ID_PREFIX = "cont001-exploratory"

MEMORY_RUN_CONFIG = {
    "backend": "sqlite (stdlib)",
    "scope": "one store per seed run; retrieval scoped to current scenario",
    "retrieval": "keyword/substring scoring (word=1.0, extra substring=0.5)",
    "top_k": MEMORY_TOP_K,
    "injection_rule": (
        "at session start with index >= 2, one system message after the base "
        "prompt; query = the session's first environment turn"
    ),
    "export_format": "continuity-memory-export v1 (model-neutral JSON)",
}

SELFMODEL_RUN_CONFIG = {
    "source": "state/selfmodel.json (revision 1; per-run copies per seed)",
    "injection_rule": (
        "one system message immediately after the base system prompt in EVERY "
        "session; content = selfmodel.render_summary of the revision current "
        "at session start"
    ),
    "cn009_caveat": (
        "revision-1 capability estimates derive from the arm-B mini-pilot on "
        "THIS SAME fixture suite (seeds 11/22/33) — exploratory-only leakage, "
        "documented as CN-009; the confirmatory run must use disjoint "
        "calibration scenarios per EVALUATION-PREP.md"
    ),
}

ARM_DESCRIPTIONS = {
    "A": "no persistent memory (session-local context only)",
    "B": "A + SQLite persistent memory (keyword retrieval, session-start injection)",
    "C": "B + validated self-model summary in every session prompt",
    "D": "C + bounded deterministic post-session reflection (proposals, evidence-gated commits)",
    "E": "D + ex-ante world-model predictions (non-behavioral) + bounded policy "
    "{answer_direct, retrieve_then_answer}",
}


def run_one_seed(
    arm: str,
    seed: int,
    scenarios: list[dict],
    run_root: Path,
    run_id: str,
    base_url: str,
    env_common: dict[str, Any],
    base_selfmodel: dict[str, Any],
    base_sha: str,
    selfmodel_source: str,
    selfmodel_source_path: str,
) -> dict[str, Any]:
    seed_run_id = f"{run_id}-arm{arm}-seed{seed}"
    out_dir = run_root / f"arm-{arm}" / f"seed-{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)

    provider = OllamaProvider(
        base_url=base_url,
        model=MODEL,
        temperature=TEMPERATURE,
        seed=seed,
        num_ctx=NUM_CTX,
        keep_alive=KEEP_ALIVE,
    )
    memory = (
        MemoryStore(str(out_dir / "memory.sqlite3")) if arm in ("B", "C", "D", "E") else None
    )
    journal = EventJournal(str(out_dir / "trace.jsonl"), seed_run_id)

    run_start_payload: dict[str, Any] = {
        "protocol_version": PROTOCOL_VERSION,
        "kind": "cont001-exploratory",
        "run_id": run_id,
        "arm": arm,
        "arm_description": ARM_DESCRIPTIONS[arm],
        "model": MODEL,
        "seed": seed,
        "seeds_predeclared": list(SEEDS),
        "arms_predeclared": list(ARMS),
        "temperature": TEMPERATURE,
        "num_ctx": NUM_CTX,
        "keep_alive": KEEP_ALIVE,
        "scenario_order": [s["id"] for s in scenarios],
        "git_rev": env_common["git_rev"],
        "exploratory_note": (
            "exploratory CONT-001 pass (M6); NOT the confirmatory run; feeds "
            "docs/EVALUATION-PREP.md as exploratory evidence only"
        ),
    }
    if memory is not None:
        run_start_payload["memory"] = dict(MEMORY_RUN_CONFIG)
    if arm in ("C", "D", "E"):
        run_start_payload["selfmodel"] = {
            **SELFMODEL_RUN_CONFIG,
            "agent_id": base_selfmodel["agentId"],
            "revision": base_selfmodel["revision"],
            "sha256": base_sha,
        }
    journal.emit("run.start", run_start_payload)

    env_snapshot = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ollama_version": env_common["ollama_version"],
        "model": MODEL,
        "model_digest": env_common["digest"],
        "seed": seed,
        "arm": arm,
        "run_id": run_id,
        "determinism_caveat": DETERMINISM_CAVEAT,
    }
    if arm in ("C", "D", "E"):
        env_snapshot["selfmodel_revision_initial"] = base_selfmodel["revision"]
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(
        json.dumps(env_snapshot, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    engine: ReflectionEngine | None = None
    worldmodel: WorldModel | None = None
    if arm in ("C", "D", "E"):
        shutil.copyfile(selfmodel_source_path, out_dir / "selfmodel-run.json")
    if arm in ("D", "E"):
        engine = ReflectionEngine(
            selfmodel_path=str(out_dir / "selfmodel-run.json"),
            memory=memory,
            journal=journal,
            run_seed=seed,
            source_artifact=f"{seed_run_id}/summary.json",
        )
    if arm == "E":
        worldmodel = WorldModel(journal)

    started = time.monotonic()
    scenario_summaries: list[dict[str, Any]] = []
    budget_stops = 0
    for scenario in scenarios:
        budget = Budget(**SCENARIO_BUDGET)
        kwargs: dict[str, Any] = {"arm": arm}
        if memory is not None:
            kwargs["memory"] = memory
        if arm == "C":
            kwargs["selfmodel"] = base_selfmodel
        elif arm in ("D", "E"):
            kwargs["selfmodel"] = engine.model
            kwargs["reflection"] = engine
        if arm == "E":
            kwargs["worldmodel"] = worldmodel
        scenario_summaries.append(
            run_scenario(scenario, provider, journal, budget, **kwargs)
        )
        if scenario_summaries[-1]["stopped"]:
            budget_stops += 1
    wall_s = round(time.monotonic() - started, 1)

    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))

    memory_export = None
    if memory is not None:
        memory_export = memory.export_json(str(out_dir / "memory-export.json"))
        memory.close()

    summary: dict[str, Any] = {
        "run_id": seed_run_id,
        "seed": seed,
        "arm": arm,
        "model": MODEL,
        "model_digest": pinned["digest"],
        "scenario_summaries": scenario_summaries,
        "probes_passed": sum(s["probes_passed"] for s in scenario_summaries),
        "probes_total": sum(s["probes_total"] for s in scenario_summaries),
        "turns": sum(s["turns"] for s in scenario_summaries),
        "tokens_total": sum(s["tokens_total"] for s in scenario_summaries),
        "budget_stops": budget_stops,
        "wall_s": wall_s,
    }
    if memory_export is not None:
        summary["memory_episodes_total"] = memory_export["episode_count"]
        summary["memory_export"] = "memory-export.json"
    if arm in ("C", "D", "E"):
        summary["selfmodel_revision_initial"] = base_selfmodel["revision"]
        summary["selfmodel_sha256_initial"] = base_sha
    if engine is not None:
        summary["reflection_telemetry"] = engine.telemetry
        summary["selfmodel_revision_final"] = engine.model["revision"]
        summary["selfmodel_sha256_final"] = selfmodel_sha256(engine.model)
    if worldmodel is not None:
        summary["worldmodel_calibration"] = worldmodel.calibration()
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


def outcome_vector(aggregate: dict[str, Any]) -> dict[str, dict[str, list[bool]]]:
    """{scenario: {seed: [probe passed flags in turn order]}} from an aggregate."""
    out: dict[str, dict[str, list[bool]]] = {}
    for sid, entry in aggregate.get("per_scenario", {}).items():
        for seed_str, obs in entry.get("observations_by_seed", {}).items():
            out.setdefault(sid, {})[int(seed_str)] = [bool(o["passed"]) for o in obs]
    return out


def build_arm_aggregate(
    arm: str,
    run_id: str,
    arm_dir: Path,
    seeds_run: list[int],
    seeds_skipped: list[int],
    scenario_defs: list[dict],
    run_summaries: list[dict[str, Any]],
    env_common: dict[str, Any],
    base_selfmodel: dict[str, Any],
    base_sha: str,
    selfmodel_source: str,
) -> dict[str, Any]:
    request_stats: list[dict[str, Any]] = []
    memory_stats: list[dict[str, Any]] = []
    reflection_trace_stats: list[dict[str, Any]] = []
    policy_by_seed: list[dict[str, Any]] = []
    worldmodel_rows: list[dict[str, Any]] = []
    for r in run_summaries:
        seed_dir = arm_dir / f"seed-{r['seed']}"
        request_stats.extend(parse_request_stats(seed_dir / "trace.jsonl"))
        if arm in ("B", "C", "D", "E"):
            memory_stats.append(
                {"seed": r["seed"], **parse_memory_events(seed_dir / "trace.jsonl")}
            )
        if arm in ("D", "E"):
            reflection_trace_stats.append(
                {"seed": r["seed"], **parse_reflection_events(seed_dir / "trace.jsonl")}
            )
        if arm == "E":
            policy_by_seed.append(
                {"seed": r["seed"], **parse_policy_events(seed_dir / "trace.jsonl")}
            )
            worldmodel_rows.extend(parse_worldmodel_events(seed_dir / "trace.jsonl"))

    per_family: dict[str, Any] = {}
    per_scenario: dict[str, Any] = {}
    overall_by_seed: dict[str, float] = {}
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
        overall_by_seed[r["seed"]] = round(r["probes_passed"] / r["probes_total"], 3)
    for family, entry in per_family.items():
        rates = list(entry["pass_rate_by_seed"].values())
        entry["spread"] = {
            "min": min(rates),
            "max": max(rates),
            "range": round(max(rates) - min(rates), 3),
            "mean": round(statistics.fmean(rates), 3),
        }
    overall_rates = list(overall_by_seed.values())

    latencies = sorted(st["total_duration_ms"] for st in request_stats)
    prompt_tokens = [st["prompt_tokens"] for st in request_stats]
    eval_tokens = [st["eval_tokens"] for st in request_stats]

    aggregate: dict[str, Any] = {
        "run": {
            "run_id": run_id,
            "kind": "cont001-exploratory",
            "arm": arm,
            "arm_description": ARM_DESCRIPTIONS[arm],
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_rev": env_common["git_rev"],
            "model": MODEL,
            "model_digest": env_common["digest"],
            "ollama_version": env_common["ollama_version"],
            "python": platform.python_version(),
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "keep_alive": KEEP_ALIVE,
            "seeds_predeclared": list(SEEDS),
            "seeds_run": seeds_run,
            "seeds_skipped": seeds_skipped,
            "scenario_order": [s["id"] for s in scenario_defs],
            "scenario_budget": dict(SCENARIO_BUDGET),
            "run_wall_clock_guard_s": RUN_WALL_CLOCK_S,
            "arm_wall_s": round(sum(r["wall_s"] for r in run_summaries), 1),
            "determinism_caveat": DETERMINISM_CAVEAT,
            "gpu_lock_note": (
                "run held the shared gpu lock; wall clock (CN-002 rule) is the "
                "budget metric; total_duration is relative-only"
            ),
        },
        "runs": [
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
                **({"memory_episodes_total": r["memory_episodes_total"]} if "memory_episodes_total" in r else {}),
                **({"selfmodel_revision_final": r["selfmodel_revision_final"]} if "selfmodel_revision_final" in r else {}),
            }
            for r in run_summaries
        ],
        "overall": {
            "pass_rate_by_seed": overall_by_seed,
            "probes_per_seed": run_summaries[0]["probes_total"] if run_summaries else 0,
            "spread": {
                "min": min(overall_rates),
                "max": max(overall_rates),
                "range": round(max(overall_rates) - min(overall_rates), 3),
                "mean": round(statistics.fmean(overall_rates), 3),
            },
        },
        "per_family": per_family,
        "per_scenario": per_scenario,
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
    if memory_stats:
        aggregate["memory_stats"] = memory_stats
    if arm in ("C", "D", "E"):
        aggregate["run"]["selfmodel"] = {
            **SELFMODEL_RUN_CONFIG,
            "agent_id": base_selfmodel["agentId"],
            "revision_initial": base_selfmodel["revision"],
            "sha256_initial": base_sha,
            "estimate_provenance": base_selfmodel["provenance"]["derived_from"],
        }
    if reflection_trace_stats:
        aggregate["reflection_trace_stats"] = reflection_trace_stats
    if arm == "E":
        aggregate["policy_by_seed"] = policy_by_seed
        aggregate["worldmodel_prediction_rows"] = worldmodel_rows
        aggregate["run"]["worldmodel_calibration_pooled"] = pooled_calibration(worldmodel_rows)
    return aggregate


def build_cross_arm_table(
    run_id: str,
    arm_aggregates: dict[str, dict[str, Any]],
    scenario_defs: list[dict],
    env_common: dict[str, Any],
    total_gpu_wall_s: float,
    script_wall_s: float,
    warmup_s: float,
    gpu_at_start: dict[str, Any] | None,
) -> dict[str, Any]:
    families = sorted({s["family"] for s in scenario_defs})
    arms_view: dict[str, Any] = {}
    for arm, agg in arm_aggregates.items():
        tokens = agg["request_stats"]["tokens"]
        passed_total = sum(r["probes_passed"] for r in agg["runs"])
        probes_total = sum(r["probes_total"] for r in agg["runs"])
        arms_view[arm] = {
            "seeds_predeclared": agg["run"]["seeds_predeclared"],
            "seeds_run": agg["run"]["seeds_run"],
            "seeds_skipped": agg["run"]["seeds_skipped"],
            "requests": agg["request_stats"]["count"],
            "overall": {
                "mean_pass_rate": agg["overall"]["spread"]["mean"],
                "spread_range": agg["overall"]["spread"]["range"],
                "pass_rate_by_seed": agg["overall"]["pass_rate_by_seed"],
                "probes_passed_total": f"{passed_total}/{probes_total}",
            },
            "families": {
                family: {
                    "probes_per_seed": entry["probes_per_seed"],
                    "mean_pass_rate": entry["spread"]["mean"],
                    "spread_range": entry["spread"]["range"],
                    "pass_rate_by_seed": entry["pass_rate_by_seed"],
                }
                for family, entry in agg["per_family"].items()
            },
            "per_scenario_pass_count": {
                sid: entry["pass_count"] for sid, entry in agg["per_scenario"].items()
            },
            "tokens": {
                "prompt_sum": tokens["prompt_sum"],
                "eval_sum": tokens["eval_sum"],
                "total_sum": tokens["total_sum"],
                "per_seed_mean": round(tokens["total_sum"] / len(agg["run"]["seeds_run"]), 1)
                if agg["run"]["seeds_run"]
                else 0,
                "prompt_mean_per_request": tokens["prompt_mean"],
                "eval_mean_per_request": tokens["eval_mean"],
            },
            "wall_s_by_seed": {str(r["seed"]): r["wall_s"] for r in agg["runs"]},
            "arm_wall_s": agg["run"]["arm_wall_s"],
            "latency_ms_mean_p95": [
                agg["request_stats"]["latency_ms"]["mean"],
                agg["request_stats"]["latency_ms"]["p95"],
            ],
        }

    return {
        "kind": "cont001-exploratory-cross-arm-table",
        "exploratory": True,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": run_id,
        "config": {
            "model": MODEL,
            "model_digest": env_common["digest"],
            "ollama_version": env_common["ollama_version"],
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "seeds_predeclared": list(SEEDS),
            "seed_count_rationale": "docs/SIZING.md recommendation: 5 seeds",
            "arms": list(ARMS),
            "scenario_order": [s["id"] for s in scenario_defs],
            "families": families,
            "scenarios": len(scenario_defs),
            "turns_per_seed": sum(
                len(s["turns"]) for s in scenario_defs for s in s["sessions"]
            ),
            "probes_per_seed": sum(
                1 for s in scenario_defs for s in s["sessions"] for t in s["turns"]
                if t.get("probe") is not None
            ),
            "one_warm_process": True,
            "sampling_options_in_every_request": True,
        },
        "time_budget": {
            "total_gpu_wall_s": round(total_gpu_wall_s, 1),
            "script_wall_s": round(script_wall_s, 1),
            "warmup_s": warmup_s,
            "budget_gpu_cap_min": 180,
            "budget_wall_cap_min": 150,
            "gpu_metric_note": (
                "CN-002 rule: wall clock under the shared GPU lock is the GPU "
                "occupancy metric; Ollama total_duration is relative-only"
            ),
        },
        "gpu_at_start": gpu_at_start,
        "arms": arms_view,
        "notes": [
            "EXPLORATORY only — input to docs/EVALUATION-PREP.md, not a confirmatory result.",
            "CN-004: rt-0003 option leakage inflates arm A (and any arm answering 'perf' without memory of its own 'bug').",
            "CN-007: repeated_task flat at 0.333 for arms B-E in the M2-M5 pilots (own-answer anchoring).",
            "CN-009: arm C-E self-model revision 1 was estimated on this same fixture suite (arm-B mini-pilot) — leakage documented, exploratory only.",
            "CN-010: arm-E policy actuation surface empty on this suite (all probes are session-first turns).",
            "CN-003: temperature 0.0 does not fully determinize outputs across seeds; spread columns carry the observed seed variation.",
        ],
    }


def render_cross_arm_markdown(table: dict[str, Any]) -> str:
    cfg = table["config"]
    arms = list(table["arms"].keys())
    fam_probe_counts: dict[str, int] = {}
    for a in arms:
        for fam, view in table["arms"][a]["families"].items():
            fam_probe_counts.setdefault(fam, view["probes_per_seed"])
    lines = [
        "# CONT-001 exploratory — cross-arm table (M6)",
        "",
        f"- run `{table['run_id']}` (exploratory; NOT confirmatory)",
        f"- model `{cfg['model']}`, digest `{cfg['model_digest'][:12]}…`, "
        f"temp {cfg['temperature']}, num_ctx {cfg['num_ctx']}",
        f"- seeds {cfg['seeds_predeclared']} (SIZING.md), arms {cfg['arms']}, "
        f"{cfg['scenarios']} scenarios / {cfg['turns_per_seed']} turns / "
        f"{cfg['probes_per_seed']} probes per seed, one warm process",
        f"- GPU wall {table['time_budget']['total_gpu_wall_s']} s under the shared "
        f"lock (cap {table['time_budget']['budget_gpu_cap_min']} min); "
        f"script wall {table['time_budget']['script_wall_s']} s "
        f"(cap {table['time_budget']['budget_wall_cap_min']} min)",
        "",
        "Pass rates are mean over seeds; brackets show the cross-seed range "
        "(min-max). 'overall' = all probes of the suite per seed.",
        "",
        "| family (probes/seed) | " + " | ".join(f"arm {a}" for a in arms) + " |",
        "| --- | " + " | ".join("---" for _ in arms) + " |",
    ]
    for family in sorted(fam_probe_counts):
        cells = []
        for a in arms:
            fam = table["arms"][a]["families"].get(family)
            cells.append(
                "n/a" if fam is None else
                f"{fam['mean_pass_rate']:.3f} [{fam['spread_range']:.3f}]"
            )
        lines.append(
            f"| {family} ({fam_probe_counts[family]}) | " + " | ".join(cells) + " |"
        )
    overall_cells = [
        f"{table['arms'][a]['overall']['mean_pass_rate']:.3f} "
        f"[{table['arms'][a]['overall']['spread_range']:.3f}]"
        for a in arms
    ]
    lines.append("| **overall (10)** | " + " | ".join(f"**{c}**" for c in overall_cells) + " |")

    lines += [
        "",
        "Per-scenario pass counts (passed probes / seeds run x 1 probe):",
        "",
        "| scenario | " + " | ".join(f"arm {a}" for a in arms) + " |",
        "| --- | " + " | ".join("---" for _ in arms) + " |",
    ]
    for sid in cfg["scenario_order"]:
        cells = []
        for a in arms:
            count = table["arms"][a]["per_scenario_pass_count"].get(sid)
            n_seeds = len(table["arms"][a]["seeds_run"])
            cells.append("n/a" if count is None else f"{count}/{n_seeds}")
        lines.append(f"| {sid} | " + " | ".join(cells) + " |")

    lines += [
        "",
        "Cost (tokens are per-request sums over the whole arm; wall per CN-002 rule):",
        "",
        "| arm | seeds run | requests | prompt tok | eval tok | total tok | "
        "wall/seed s (min-max) | arm wall s |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for a in arms:
        v = table["arms"][a]
        walls = [w for w in v["wall_s_by_seed"].values()]
        wall_str = f"{min(walls):.0f}-{max(walls):.0f}" if walls else "n/a"
        lines.append(
            f"| {a} | {len(v['seeds_run'])} | {v['requests']} | "
            f"{v['tokens']['prompt_sum']:,} | {v['tokens']['eval_sum']:,} | "
            f"{v['tokens']['total_sum']:,} | {wall_str} | {v['arm_wall_s']} |"
        )

    lines += [
        "",
        "Notes: " + " ".join(f"[{n.split(':')[0]}]" for n in table["notes"]),
    ]
    lines += [
        "",
        "Caveats (see docs/FINDINGS.md): CN-003 (temp-0 seed drift), CN-004 "
        "(rt-0003 option leakage), CN-007 (own-answer anchoring), CN-009 "
        "(self-model estimated on this suite), CN-010 (empty policy actuation "
        "surface). Exploratory numbers only — the confirmatory contrast is "
        "defined in docs/EVALUATION-PREP.md.",
    ]
    return "\n".join(lines) + "\n"


def build_pilot_consistency(
    run_id: str,
    arm_aggregates: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Compare per-seed probe outcome vectors with the M1-M5 pilot artifacts."""
    report: dict[str, Any] = {
        "kind": "cont001-exploratory-pilot-consistency",
        "run_id": run_id,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "comparison": "per-scenario, per-seed probe outcome vectors (fixtures and arm code unchanged)",
        "arms": {},
    }
    pilot_patterns = {
        "A": "pilot-armA-*/aggregate.json",
        "B": "pilot-armB-*/aggregate.json",
        "C": "pilot-armC-*/aggregate.json",
        "D": "pilot-armD-*/aggregate.json",
        "E": "pilot-armE-*/aggregate.json",
    }
    for arm, pattern in pilot_patterns.items():
        if arm not in arm_aggregates:
            continue
        try:
            pilot_path = find_aggregate(pattern, None)
        except SystemExit:
            report["arms"][arm] = {"pilot": None, "error": "pilot aggregate not found"}
            continue
        pilot = json.loads(pilot_path.read_text(encoding="utf-8"))
        mine = outcome_vector(arm_aggregates[arm])
        theirs = outcome_vector(pilot)
        # overlapping seeds = seeds present in both runs for any scenario
        my_seeds = {s for per in mine.values() for s in per}
        their_seeds = {s for per in theirs.values() for s in per}
        overlapping = sorted(my_seeds & their_seeds)
        compared = 0
        identical = 0
        mismatches: list[dict[str, Any]] = []
        for sid in sorted(set(mine) & set(theirs)):
            for seed in overlapping:
                if seed in mine[sid] and seed in theirs[sid]:
                    compared += 1
                    if mine[sid][seed] == theirs[sid][seed]:
                        identical += 1
                    else:
                        mismatches.append(
                            {
                                "scenario": sid,
                                "seed": seed,
                                "exploratory": mine[sid][seed],
                                "pilot": theirs[sid][seed],
                            }
                        )
        report["arms"][arm] = {
            "pilot": str(pilot_path.relative_to(LAB_ROOT)).replace("\\", "/"),
            "pilot_seeds": sorted(their_seeds),
            "overlapping_seeds": overlapping,
            "scenario_seed_outcomes_compared": compared,
            "identical": identical,
            "mismatches": mismatches,
        }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--selfmodel", default=str(DEFAULT_SELFMODEL))
    args = parser.parse_args()

    fixture_dir = LAB_ROOT / "fixtures" / "v1"
    manifest, scenarios = load_suite(str(fixture_dir))
    total_turns = sum(len(s["turns"]) for s in scenarios for s in s["sessions"])
    print(f"suite: {len(scenarios)} scenarios, families={manifest['families']}")
    print(
        f"plan: arms {list(ARMS)} x {len(SEEDS)} seeds x {total_turns} turns = "
        f"{len(ARMS) * len(SEEDS) * total_turns} requests "
        f"(predeclared seeds {list(SEEDS)})"
    )

    try:
        base_selfmodel = load_selfmodel(args.selfmodel)
    except Exception as exc:
        print(f"FAIL-CLOSED: self-model store invalid: {exc}", file=sys.stderr)
        raise SystemExit(2)
    base_sha = selfmodel_sha256(base_selfmodel)
    selfmodel_source = str(Path(args.selfmodel).relative_to(LAB_ROOT)).replace("\\", "/")
    print(
        f"self-model ok: agent {base_selfmodel['agentId']}, revision "
        f"{base_selfmodel['revision']}, sha {base_sha[:12]}... (per-run copies)"
    )

    env_common = preflight(args.base_url, MODEL)
    env_common["git_rev"] = git_rev()
    print(
        f"preflight ok: ollama {env_common['ollama_version']}, digest "
        f"{env_common['digest'][:12]}..., warmup {env_common['warmup_s']}s"
    )
    gpu_at_start = gpu_snapshot(args.base_url)
    print(f"gpu snapshot (CN-005): {gpu_at_start}")

    run_id = time.strftime(f"{RUN_ID_PREFIX}-%Y%m%d-%H%M%S")
    run_root = LAB_ROOT / "results" / "CONT-001-exploratory" / run_id
    run_root.mkdir(parents=True, exist_ok=True)

    script_started = time.monotonic()
    gpu_started = time.monotonic()
    arm_aggregates: dict[str, dict[str, Any]] = {}
    all_ok = True
    for arm in ARMS:
        arm_dir = run_root / f"arm-{arm}"
        arm_dir.mkdir(parents=True, exist_ok=True)
        run_summaries: list[dict[str, Any]] = []
        seeds_run: list[int] = []
        seeds_skipped: list[int] = []
        print(f"=== arm {arm} starting ({time.strftime('%H:%M:%S')})")
        for seed in SEEDS:
            elapsed = time.monotonic() - script_started
            if elapsed > RUN_WALL_CLOCK_S:
                seeds_skipped.append(seed)
                print(
                    f"run wall-clock guard hit ({elapsed:.0f}s): skipping "
                    f"arm {arm} seed {seed}",
                    file=sys.stderr,
                )
                continue
            print(f"--- arm {arm} seed {seed} starting ({time.strftime('%H:%M:%S')})")
            seeds_run.append(seed)
            run_summaries.append(
                run_one_seed(
                    arm, seed, scenarios, run_root, run_id, args.base_url, env_common,
                    base_selfmodel, base_sha, selfmodel_source, args.selfmodel,
                )
            )
            r = run_summaries[-1]
            print(
                f"arm {arm} seed {seed}: probes {r['probes_passed']}/{r['probes_total']}, "
                f"turns {r['turns']}, tokens {r['tokens_total']}, "
                f"wall {r['wall_s']}s, completed={r['completed']}"
            )
        if not run_summaries:
            print(f"FAIL-CLOSED: no seeds completed for arm {arm}", file=sys.stderr)
            return 2
        aggregate = build_arm_aggregate(
            arm, run_id, arm_dir, seeds_run, seeds_skipped, scenarios,
            run_summaries, env_common, base_selfmodel, base_sha, selfmodel_source,
        )
        arm_aggregates[arm] = aggregate
        (arm_dir / f"aggregate-arm-{arm}.json").write_text(
            json.dumps(aggregate, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        all_ok = all_ok and all(r["completed"] for r in run_summaries) and not seeds_skipped
        print(
            f"=== arm {arm} done: overall {aggregate['overall']['spread']['mean']} "
            f"(spread {aggregate['overall']['spread']['range']}), "
            f"arm wall {aggregate['run']['arm_wall_s']}s"
        )
    total_gpu_wall_s = time.monotonic() - gpu_started

    consistency = build_pilot_consistency(run_id, arm_aggregates)
    (run_root / "pilot-consistency.json").write_text(
        json.dumps(consistency, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    table = build_cross_arm_table(
        run_id, arm_aggregates, scenarios, env_common, total_gpu_wall_s,
        time.monotonic() - script_started, env_common["warmup_s"], gpu_at_start,
    )
    table["pilot_consistency_summary"] = {
        arm: {
            "identical": slot.get("identical"),
            "compared": slot.get("scenario_seed_outcomes_compared"),
            "mismatches": len(slot.get("mismatches", [])),
        }
        for arm, slot in consistency["arms"].items()
    }
    (run_root / "cross-arm-table.json").write_text(
        json.dumps(table, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    (run_root / "cross-arm-table.md").write_text(
        render_cross_arm_markdown(table), encoding="utf-8"
    )

    print(f"\ncross-arm table: {run_root / 'cross-arm-table.md'}")
    for arm in ARMS:
        agg = arm_aggregates[arm]
        print(
            f"  arm {arm}: overall mean {agg['overall']['spread']['mean']} "
            f"spread {agg['overall']['spread']['range']} "
            f"families={ {f: e['spread']['mean'] for f, e in agg['per_family'].items()} }"
        )
    print(f"pilot consistency: {run_root / 'pilot-consistency.json'}")
    print(f"total GPU wall: {total_gpu_wall_s:.0f}s")
    print(f"all completed={all_ok}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
