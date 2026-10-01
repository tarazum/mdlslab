"""CONT-000 mini-pilot, arm E: full fixture suite x predeclared seeds, one warm
process, per-seed persistent memory + self-model + reflection + world model +
bounded policy (M5).

Usage (from anywhere; take the shared GPU lock around this, see
shared/tooling/agent-resource-coordination/PROTOCOL.md):

    python labs/continuity/experiments/CONT-000/run_pilot_arm_e.py

Mirrors run_pilot_arm_d.py (M4) with the arm-E additions:
- arm="E" passed to run_scenario (arm D semantics + ex-ante world-model
  predictions on probe turns + the bounded deterministic policy
  {answer_direct, retrieve_then_answer});
- world-model calibration summaries (per seed, from the per-seed WorldModel
  counters, PLUS a pooled re-derivation from the traces) and the policy
  action distribution (per seed and pooled, with rules and no-op reasons)
  are aggregated into aggregate.json;
- after the runs, an arm A vs B vs C vs D vs E per-family comparison
  artifact is written next to the aggregate (A/B/C/D numbers are read from
  the M1/M2/M3/M4 pilot aggregates, never re-run).

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
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))  # reuse M2/M4 pilot helpers

from continuity import PROTOCOL_VERSION  # noqa: E402
from continuity.events import EventJournal, validate_trace  # noqa: E402
from continuity.fixtures import load_suite  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.policy import ACTION_SET  # noqa: E402
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

# --- Predeclared run configuration (fixed BEFORE any pilot run) ---
SEEDS: tuple[int, ...] = (11, 22, 33)
MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned by the P0a smoke (CN-001)
TEMPERATURE = 0.0
NUM_CTX = 4096
KEEP_ALIVE = "30m"
PILOT_WALL_CLOCK_S = 30 * 60.0  # leaves margin inside the 40 min GPU budget
SCENARIO_BUDGET = {"max_turns": 40, "max_total_tokens": 100_000, "wall_clock_s": 600.0}
DEFAULT_SELFMODEL = LAB_ROOT / "state" / "selfmodel.json"

WORLDMODEL_CONFIG = {
    "prediction": (
        "before each probe turn is answered: predicted pass/fail + confidence "
        "= the self-model's CURRENT per-family pass-rate estimate (0.5 default "
        "prior), capped at 0.25 when the store holds no episodes for the scenario"
    ),
    "decision_threshold": 0.5,
    "buckets": {"high": ">= 0.75", "medium": "[0.5, 0.75)", "low": "< 0.5"},
    "non_behavioral": (
        "predictions are trace events only; they never alter the prompt or the "
        "answer path (the M5 policy acts on environment/memory signals, not "
        "predictions)"
    ),
    "cn009_caveat": (
        "prediction confidence derives from self-model family rates estimated "
        "on the same fixture suite (CN-009) — exploratory calibration, not "
        "clean calibration"
    ),
}

POLICY_CONFIG = {
    "action_set": sorted(ACTION_SET),
    "rules": (
        "R1 retrieve_then_answer when the environment turn carries a fixed "
        "absence-of-records marker ('not at hand', 'no logbook', 'no paperwork', "
        "'no papers', 'no timetable', 'from your own records', 'from your "
        "records'); R2 retrieve_then_answer when the turn is a probe and the "
        "scenario's stored environment episodes contain a corrective marker "
        "(reflection.CORRECTIVE_MARKERS); otherwise answer_direct"
    ),
    "actuation": (
        "per-turn memory refresh/extension ONLY: same renderer, same keyword "
        "retrieval rule and top_k as the arm-B baseline injection, query = the "
        "CURRENT turn; dedup no-op recorded when the retrieved ids are already "
        "covered by this session's injections; no new tools, no prompt changes, "
        "no new memory semantics (CONT-005 trust hierarchy NOT implemented — "
        "owner-gated)"
    ),
    "consumes_predictions": False,
}

REFLECTION_CONFIG = {
    "engine": "deterministic MVP (no LLM call; bounded: one pass per non-stopped session)",
    "proposal_types": [
        "episode_summary",
        "selfmodel_capability_update",
        "selfmodel_failure_pattern",
    ],
    "validator": "schema + evidence re-derivation (episode ids / probe outcomes); no evidence -> reject",
    "commits": (
        "summaries as new episodes (role reflection.summary, immutable events "
        "never rewritten); self-model via fail-closed selfmodel.commit into a "
        "per-run copy (state/selfmodel.json untouched)"
    ),
}


def parse_policy_events(trace_path: Path) -> dict[str, Any]:
    """Policy evidence from the trace: action/rule distribution + actuation."""
    by_action = {a: 0 for a in sorted(ACTION_SET)}
    by_rule: dict[str, int] = {}
    injections = 0
    noop_reasons: dict[str, int] = {}
    by_scenario: dict[str, dict[str, int]] = {}
    with open(trace_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") != "policy.action":
                continue
            payload = record["payload"]
            by_action[payload["action"]] += 1
            by_rule[payload["rule"]] = by_rule.get(payload["rule"], 0) + 1
            slot = by_scenario.setdefault(record.get("scenario") or "?", dict(by_action))
            slot[payload["action"]] += 1
            retrieval = payload.get("retrieval")
            if payload["action"] == "retrieve_then_answer":
                if retrieval and retrieval.get("injected"):
                    injections += 1
                else:
                    reason = (retrieval or {}).get("reason", "unknown")
                    noop_reasons[reason] = noop_reasons.get(reason, 0) + 1
    return {
        "actions": by_action,
        "rules": by_rule,
        "retrieve_injections": injections,
        "retrieve_noop_reasons": noop_reasons,
        "by_scenario": by_scenario,
    }


def parse_worldmodel_events(trace_path: Path) -> list[dict[str, Any]]:
    """Per-probe prediction+outcome pairs from the trace (pooled re-derivation)."""
    pairs: dict[str, dict[str, Any]] = {}
    with open(trace_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == "worldmodel.prediction":
                payload = record["payload"]
                pairs[payload["prediction_id"]] = {
                    "scenario": record.get("scenario"),
                    "family": payload["family"],
                    "turn_ref": payload["turn_ref"],
                    "predicted": payload["predicted"],
                    "confidence": payload["confidence"],
                    "bucket": payload["bucket"],
                }
            elif record.get("type") == "worldmodel.outcome":
                payload = record["payload"]
                slot = pairs.get(payload["prediction_id"])
                if slot is not None:
                    slot["actual_passed"] = payload["actual_passed"]
                    slot["prediction_correct"] = payload["prediction_correct"]
    return list(pairs.values())


def pooled_calibration(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Bucketed calibration over pooled prediction/outcome rows."""

    def rate(num: int, den: int) -> float | None:
        return round(num / den, 3) if den else None

    n = len(rows)
    out: dict[str, Any] = {
        "predictions": n,
        "outcomes": sum(1 for r in rows if "actual_passed" in r),
        "overall": {
            "predicted_pass_rate": rate(sum(1 for r in rows if r.get("predicted") == "pass"), n),
            "actual_pass_rate": rate(sum(1 for r in rows if r.get("actual_passed")), n),
            "accuracy": rate(sum(1 for r in rows if r.get("prediction_correct")), n),
            "mean_confidence": rate(sum(r["confidence"] for r in rows), n),
        },
        "by_bucket": {},
        "by_family": {},
    }
    for bucket in ("high", "medium", "low"):
        slot = [r for r in rows if r["bucket"] == bucket]
        out["by_bucket"][bucket] = {
            "n": len(slot),
            "predicted_pass_rate": rate(
                sum(1 for r in slot if r.get("predicted") == "pass"), len(slot)
            ),
            "actual_pass_rate": rate(sum(1 for r in slot if r.get("actual_passed")), len(slot)),
            "mean_confidence": rate(sum(r["confidence"] for r in slot), len(slot)),
        }
    for family in sorted({r["family"] for r in rows}):
        slot = [r for r in rows if r["family"] == family]
        out["by_family"][family] = {
            "n": len(slot),
            "mean_confidence": rate(sum(r["confidence"] for r in slot), len(slot)),
            "predicted_pass_rate": rate(
                sum(1 for r in slot if r.get("predicted") == "pass"), len(slot)
            ),
            "actual_pass_rate": rate(sum(1 for r in slot if r.get("actual_passed")), len(slot)),
        }
    return out


def run_one_seed(
    seed: int,
    scenarios: list[dict],
    out_root: Path,
    pilot_run_id: str,
    base_url: str,
    env_common: dict[str, Any],
    base_selfmodel: dict[str, Any],
    base_sha: str,
    selfmodel_source: str,
    selfmodel_source_path: str,
) -> dict[str, Any]:
    run_id = f"{pilot_run_id}-seed{seed}"
    out_dir = out_root / f"seed-{seed}"
    out_dir.mkdir(parents=True, exist_ok=True)
    selfmodel_run_path = out_dir / "selfmodel-run.json"
    shutil.copyfile(selfmodel_source_path, selfmodel_run_path)

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
            "kind": "pilot-armE",
            "pilot_run_id": pilot_run_id,
            "arm": "E",
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
            "selfmodel": {
                "store": "selfmodel-run.json (per-run copy in this seed dir)",
                "source": selfmodel_source,
                "agent_id": base_selfmodel["agentId"],
                "revision": base_selfmodel["revision"],
                "sha256": base_sha,
                "injection": "one system message after the base prompt in every session",
            },
            "reflection": dict(REFLECTION_CONFIG),
            "worldmodel": dict(WORLDMODEL_CONFIG),
            "policy": dict(POLICY_CONFIG),
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
        "arm": "E",
        "selfmodel_revision_initial": base_selfmodel["revision"],
        "determinism_caveat": DETERMINISM_CAVEAT,
    }
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(
        json.dumps(env_snapshot, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    engine = ReflectionEngine(
        selfmodel_path=str(selfmodel_run_path),
        memory=memory,
        journal=journal,
        run_seed=seed,
        source_artifact=f"{run_id}/summary.json",
    )
    worldmodel = WorldModel(journal)
    started = time.monotonic()
    scenario_summaries: list[dict[str, Any]] = []
    budget_stops = 0
    for scenario in scenarios:
        budget = Budget(**SCENARIO_BUDGET)
        scenario_summaries.append(
            run_scenario(
                scenario, provider, journal, budget, arm="E",
                memory=memory, selfmodel=engine.model, reflection=engine,
                worldmodel=worldmodel,
            )
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
        "arm": "E",
        "model": MODEL,
        "model_digest": pinned["digest"],
        "selfmodel_revision_initial": base_selfmodel["revision"],
        "selfmodel_sha256_initial": base_sha,
        "selfmodel_revision_final": engine.model["revision"],
        "selfmodel_sha256_final": selfmodel_sha256(engine.model),
        "scenario_summaries": scenario_summaries,
        "probes_passed": sum(s["probes_passed"] for s in scenario_summaries),
        "probes_total": sum(s["probes_total"] for s in scenario_summaries),
        "turns": sum(s["turns"] for s in scenario_summaries),
        "tokens_total": sum(s["tokens_total"] for s in scenario_summaries),
        "budget_stops": budget_stops,
        "wall_s": wall_s,
        "memory_episodes_total": memory_export["episode_count"],
        "memory_export": "memory-export.json",
        "selfmodel_run_copy": "selfmodel-run.json",
    }
    summary["reflection_telemetry"] = engine.telemetry
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
    base_selfmodel: dict[str, Any],
    base_sha: str,
    selfmodel_source: str,
    gpu_at_start: dict[str, Any] | None,
) -> dict[str, Any]:
    scenario_order = [s["id"] for s in scenario_defs]

    runs = []
    reflection_totals = {"proposals": 0, "accepted": 0, "rejected": 0}
    by_type_totals: dict[str, dict[str, int]] = {}
    policy_totals = {
        "actions": {a: 0 for a in sorted(ACTION_SET)},
        "rules": {},
        "retrieve_injections": 0,
        "retrieve_noop_reasons": {},
    }
    worldmodel_rows: list[dict[str, Any]] = []
    for r in run_summaries:
        runs.append(
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
                "reflection": {
                    "passes": r["reflection_telemetry"]["passes"],
                    "summaries_appended": r["reflection_telemetry"]["summaries_appended"],
                    "selfmodel_revision_final": r["selfmodel_revision_final"],
                    "selfmodel_sha256_final": r["selfmodel_sha256_final"],
                },
                "worldmodel_calibration": r["worldmodel_calibration"],
            }
        )
        rt = r["reflection_telemetry"]
        for ptype in rt["proposals_by_type"]:
            agg = by_type_totals.setdefault(
                ptype, {"proposals": 0, "accepted": 0, "rejected": 0}
            )
            agg["proposals"] += rt["proposals_by_type"][ptype]
            agg["accepted"] += rt["accepted_by_type"][ptype]
            agg["rejected"] += rt["rejected_by_type"][ptype]
            reflection_totals["proposals"] += rt["proposals_by_type"][ptype]
            reflection_totals["accepted"] += rt["accepted_by_type"][ptype]
            reflection_totals["rejected"] += rt["rejected_by_type"][ptype]

    # World-model + policy evidence re-derived from the traces (primary source).
    policy_by_seed: list[dict[str, Any]] = []
    for r in run_summaries:
        seed_dir = out_root / f"seed-{r['seed']}"
        policy_by_seed.append(
            {"seed": r["seed"], **parse_policy_events(seed_dir / "trace.jsonl")}
        )
        worldmodel_rows.extend(parse_worldmodel_events(seed_dir / "trace.jsonl"))
    for entry in policy_by_seed:
        for action, count in entry["actions"].items():
            policy_totals["actions"][action] += count
        for rule, count in entry["rules"].items():
            policy_totals["rules"][rule] = policy_totals["rules"].get(rule, 0) + count
        policy_totals["retrieve_injections"] += entry["retrieve_injections"]
        for reason, count in entry["retrieve_noop_reasons"].items():
            policy_totals["retrieve_noop_reasons"][reason] = (
                policy_totals["retrieve_noop_reasons"].get(reason, 0) + count
            )

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
            "kind": "pilot-armE",
            "arm": "E",
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
                    "base prompt; query = the session's first environment turn; "
                    "accepted reflection summaries surface through this same rule"
                ),
                "export_format": "continuity-memory-export v1 (model-neutral JSON)",
            },
            "selfmodel": {
                "store": "selfmodel-run.json (per-run copy per seed)",
                "source": selfmodel_source,
                "agent_id": base_selfmodel["agentId"],
                "revision_initial": base_selfmodel["revision"],
                "sha256_initial": base_sha,
                "injection_rule": (
                    "one system message immediately after the base system prompt in "
                    "EVERY session; content = selfmodel.render_summary of the "
                    "revision current at session start"
                ),
                "estimate_provenance": base_selfmodel["provenance"]["derived_from"],
            },
            "reflection": {
                **REFLECTION_CONFIG,
                "telemetry_totals": reflection_totals,
                "telemetry_by_type": by_type_totals,
                "selfmodel_revisions_final_by_seed": {
                    str(r["seed"]): r["selfmodel_revision_final"] for r in run_summaries
                },
            },
            "worldmodel": {
                **WORLDMODEL_CONFIG,
                "calibration_pooled": pooled_calibration(worldmodel_rows),
            },
            "policy": {
                **POLICY_CONFIG,
                "distribution_totals": policy_totals,
                "distribution_by_seed": policy_by_seed,
            },
            "determinism_caveat": DETERMINISM_CAVEAT,
            "gpu_lock_note": (
                "run held the shared gpu lock; any nvidia-smi 'busy' at start was "
                "attributed via ollama /api/ps (CN-005 monitoring rule)"
            ),
            "gpu_at_start": gpu_at_start,
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
        "worldmodel_prediction_rows": worldmodel_rows,
    }


def build_comparison_abcde(
    arm_e_aggregate: dict[str, Any],
    arm_a_path: Path,
    arm_b_path: Path,
    arm_c_path: Path,
    arm_d_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Per-family arm A vs B vs C vs D vs E table (numbers only, exploratory)."""
    arm_a = json.loads(arm_a_path.read_text(encoding="utf-8"))
    arm_b = json.loads(arm_b_path.read_text(encoding="utf-8"))
    arm_c = json.loads(arm_c_path.read_text(encoding="utf-8"))
    arm_d = json.loads(arm_d_path.read_text(encoding="utf-8"))

    def arm_view(aggregate: dict[str, Any]) -> dict[str, Any]:
        return {
            "seeds": aggregate["pilot"]["seeds_run"],
            "per_family": {
                family: {
                    "pass_rate_by_seed": entry["pass_rate_by_seed"],
                    "mean_pass_rate": entry["spread"]["mean"],
                }
                for family, entry in aggregate["per_family"].items()
            },
            "per_scenario_pass_count": {
                sid: entry["pass_count"] for sid, entry in aggregate["per_scenario"].items()
            },
        }

    a, b, c, d, e = (
        arm_view(arm_a), arm_view(arm_b), arm_view(arm_c), arm_view(arm_d),
        arm_view(arm_e_aggregate),
    )
    families = sorted(
        set(a["per_family"]) | set(b["per_family"]) | set(c["per_family"])
        | set(d["per_family"]) | set(e["per_family"])
    )

    per_family_table = {}
    for family in families:
        per_family_table[family] = {
            "arm_A_mean": a["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_B_mean": b["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_C_mean": c["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_D_mean": d["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_E_mean": e["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_E_minus_arm_D": None
            if not e["per_family"].get(family) or not d["per_family"].get(family)
            else round(
                e["per_family"][family]["mean_pass_rate"]
                - d["per_family"][family]["mean_pass_rate"],
                3,
            ),
            "arm_E_pass_rate_by_seed": e["per_family"].get(family, {}).get(
                "pass_rate_by_seed"
            ),
        }

    calibration = arm_e_aggregate["pilot"]["worldmodel"]["calibration_pooled"]
    policy_totals = arm_e_aggregate["pilot"]["policy"]["distribution_totals"]

    comparison = {
        "kind": "armA-vs-armB-vs-armC-vs-armD-vs-armE-per-family",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "arm_a_source": str(arm_a_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_b_source": str(arm_b_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_c_source": str(arm_c_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_d_source": str(arm_d_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_e_source": "aggregate.json (this directory)",
        "shared_config": {
            "model": arm_b["pilot"]["model"],
            "model_digest": arm_b["pilot"]["model_digest"],
            "temperature": arm_b["pilot"]["temperature"],
            "num_ctx": arm_b["pilot"]["num_ctx"],
            "scenario_order": arm_b["pilot"]["scenario_order"],
            "note": (
                "seeds differ by design (arm A: 5 predeclared M1 seeds; arms B/C/D/E: "
                "first 3 of the same predeclared list, per the M2-M5 briefs)"
            ),
        },
        "arms": {
            "A": {"seeds": a["seeds"]},
            "B": {"seeds": b["seeds"]},
            "C": {"seeds": c["seeds"]},
            "D": {"seeds": d["seeds"]},
            "E": {"seeds": e["seeds"]},
        },
        "per_family": per_family_table,
        "per_scenario_pass_counts": {
            sid: {
                "arm_A": a["per_scenario_pass_count"].get(sid),
                "arm_B": b["per_scenario_pass_count"].get(sid),
                "arm_C": c["per_scenario_pass_count"].get(sid),
                "arm_D": d["per_scenario_pass_count"].get(sid),
                "arm_E": e["per_scenario_pass_count"].get(sid),
            }
            for sid in arm_b["pilot"]["scenario_order"]
        },
        "arm_e_worldmodel_calibration_pooled": calibration,
        "arm_e_policy_distribution": policy_totals,
        "notes": [
            (
                "CN-007 watch (repeated_task, the own-answer-anchoring family): "
                "arms B/C/D all 0.333 — see per_scenario rows rt-0001/2/3 for whether "
                "arm E's bounded policy (retrieve_then_answer re-surfacings) moved it. "
                "Retrieval weighting/filtering is NOT in the M5 action set (that is "
                "the owner-gated CONT-005 trust-hierarchy proposal)."
            ),
            (
                "CN-009 caveat: arm E's prediction confidence derives from self-model "
                "family rates estimated on this same fixture suite — the calibration "
                "numbers are exploratory and partly circular, not clean calibration."
            ),
            (
                "Policy actuation is bounded to memory refresh/extension (same "
                "renderer/rule/top-k as the arm-B baseline injection, query = current "
                "turn); no new tools, no prompt-template changes, no new memory "
                "semantics."
            ),
        ],
    }

    (out_dir / "armA-vs-armB-vs-armC-vs-armD-vs-armE.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    def fmt(x):
        return "n/a" if x is None else f"{x:.3f}" if isinstance(x, float) else str(x)

    lines = [
        "# Arm A vs arm B vs arm C vs arm D vs arm E — per family (M5 mini-pilot)",
        "",
        f"- arm A source: `{comparison['arm_a_source']}` (seeds {a['seeds']})",
        f"- arm B source: `{comparison['arm_b_source']}` (seeds {b['seeds']})",
        f"- arm C source: `{comparison['arm_c_source']}` (seeds {c['seeds']})",
        f"- arm D source: `{comparison['arm_d_source']}` (seeds {d['seeds']})",
        f"- arm E source: `{comparison['arm_e_source']}` (seeds {e['seeds']})",
        f"- model {comparison['shared_config']['model']}, digest "
        f"`{comparison['shared_config']['model_digest'][:12]}…`, temp "
        f"{comparison['shared_config']['temperature']}, num_ctx "
        f"{comparison['shared_config']['num_ctx']}",
        "- arm E = arm D + ex-ante world-model predictions on probe turns "
        "(non-behavioral, trace events) + bounded policy {answer_direct, "
        "retrieve_then_answer} (actuation: per-turn memory refresh/extension only)",
        "",
        "| family | A mean | B mean | C mean | D mean | E mean | E - D |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for family in families:
        row = per_family_table[family]
        delta = row["arm_E_minus_arm_D"]
        delta_str = "n/a" if delta is None else f"{delta:+.3f}"
        lines.append(
            f"| {family} | {row['arm_A_mean']} | {row['arm_B_mean']} | "
            f"{row['arm_C_mean']} | {row['arm_D_mean']} | {row['arm_E_mean']} "
            f"| {delta_str} |"
        )
    lines += [
        "",
        "Per-scenario pass counts (passed probes / seeds x 1 probe):",
        "",
        "| scenario | arm A | arm B | arm C | arm D | arm E |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for sid, counts in comparison["per_scenario_pass_counts"].items():
        lines.append(
            f"| {sid} | {counts['arm_A']}/{len(a['seeds'])} "
            f"| {counts['arm_B']}/{len(b['seeds'])} | {counts['arm_C']}/{len(c['seeds'])} "
            f"| {counts['arm_D']}/{len(d['seeds'])} | {counts['arm_E']}/{len(e['seeds'])} |"
        )

    ov = calibration["overall"]
    lines += [
        "",
        "## Arm E world-model calibration (pooled over "
        f"{calibration['predictions']} predictions / {calibration['outcomes']} outcomes)",
        "",
        f"- overall: predicted-pass rate {fmt(ov['predicted_pass_rate'])} vs actual "
        f"{fmt(ov['actual_pass_rate'])}; pass/fail accuracy {fmt(ov['accuracy'])}; "
        f"mean confidence {fmt(ov['mean_confidence'])}",
        "",
        "| bucket | n | predicted-pass rate | actual pass rate | mean confidence |",
        "| --- | --- | --- | --- | --- |",
    ]
    for bucket in ("high", "medium", "low"):
        slot = calibration["by_bucket"][bucket]
        lines.append(
            f"| {bucket} | {slot['n']} | {fmt(slot['predicted_pass_rate'])} | "
            f"{fmt(slot['actual_pass_rate'])} | {fmt(slot['mean_confidence'])} |"
        )
    lines += [
        "",
        "CN-009 caveat: confidence derives from self-model family rates estimated "
        "on this same fixture suite — exploratory calibration, partly circular.",
        "",
        "## Arm E policy action distribution (pooled over "
        f"{sum(policy_totals['actions'].values())} turn decisions)",
        "",
        "| action / rule | count |",
        "| --- | --- |",
    ]
    for action, count in policy_totals["actions"].items():
        lines.append(f"| action: {action} | {count} |")
    for rule, count in sorted(policy_totals["rules"].items()):
        lines.append(f"| rule fired: {rule} | {count} |")
    lines.append(
        f"| retrieve_then_answer -> physical injection | "
        f"{policy_totals['retrieve_injections']} |"
    )
    for reason, count in sorted(policy_totals["retrieve_noop_reasons"].items()):
        lines.append(f"| retrieve_then_answer -> no-op ({reason}) | {count} |")
    lines += [
        "",
        "Exploratory mini-pilot numbers only. Caveats: CN-009 (self-model "
        "estimated on this same fixture suite; predictions partly circular); "
        "CN-004 (rt-0003 option leakage inflates arm A there). Not the "
        "confirmatory CONT-001 contrast.",
    ]
    (out_dir / "armA-vs-armB-vs-armC-vs-armD-vs-armE.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return comparison


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument(
        "--arm-a-aggregate", default=None,
        help="path to the arm-A pilot aggregate.json (default: newest pilot-armA-*)",
    )
    parser.add_argument(
        "--arm-b-aggregate", default=None,
        help="path to the arm-B pilot aggregate.json (default: newest pilot-armB-*)",
    )
    parser.add_argument(
        "--arm-c-aggregate", default=None,
        help="path to the arm-C pilot aggregate.json (default: newest pilot-armC-*)",
    )
    parser.add_argument(
        "--arm-d-aggregate", default=None,
        help="path to the arm-D pilot aggregate.json (default: newest pilot-armD-*)",
    )
    parser.add_argument("--selfmodel", default=str(DEFAULT_SELFMODEL))
    args = parser.parse_args()

    fixture_dir = LAB_ROOT / "fixtures" / "v1"
    manifest, scenarios = load_suite(str(fixture_dir))
    total_turns = sum(len(s["turns"]) for s in scenarios for s in s["sessions"])
    print(f"suite: {len(scenarios)} scenarios, families={manifest['families']}")
    print(
        f"plan: {len(SEEDS)} seeds x {total_turns} turns = "
        f"{len(SEEDS) * total_turns} requests (predeclared seeds {list(SEEDS)})"
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

    pilot_run_id = time.strftime("pilot-armE-%Y%m%d-%H%M%S")
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
            run_one_seed(
                seed, scenarios, out_root, pilot_run_id, args.base_url, env_common,
                base_selfmodel, base_sha, selfmodel_source, args.selfmodel,
            )
        )
        r = run_summaries[-1]
        print(
            f"seed {seed}: probes {r['probes_passed']}/{r['probes_total']}, "
            f"turns {r['turns']}, tokens {r['tokens_total']}, "
            f"episodes {r['memory_episodes_total']}, wall {r['wall_s']}s, "
            f"selfmodel rev {r['selfmodel_revision_initial']}->"
            f"{r['selfmodel_revision_final']}, completed={r['completed']}"
        )

    request_stats: list[dict[str, Any]] = []
    memory_stats: list[dict[str, Any]] = []
    reflection_trace_stats: list[dict[str, Any]] = []
    for r in run_summaries:
        seed_dir = out_root / f"seed-{r['seed']}"
        request_stats.extend(parse_request_stats(seed_dir / "trace.jsonl"))
        memory_stats.append({"seed": r["seed"], **parse_memory_events(seed_dir / "trace.jsonl")})
        reflection_trace_stats.append(
            {"seed": r["seed"], **parse_reflection_events(seed_dir / "trace.jsonl")}
        )

    aggregate = build_aggregate(
        pilot_run_id, out_root, seeds_run, seeds_skipped, scenarios, run_summaries,
        request_stats, memory_stats, env_common, base_selfmodel, base_sha,
        selfmodel_source, gpu_at_start,
    )
    aggregate["pilot"]["wall_clock_s"] = round(time.monotonic() - pilot_started, 1)
    aggregate["reflection_trace_stats"] = reflection_trace_stats
    (out_root / "aggregate.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    arm_a_path = find_aggregate("pilot-armA-*/aggregate.json", args.arm_a_aggregate)
    arm_b_path = find_aggregate("pilot-armB-*/aggregate.json", args.arm_b_aggregate)
    arm_c_path = find_aggregate("pilot-armC-*/aggregate.json", args.arm_c_aggregate)
    arm_d_path = find_aggregate("pilot-armD-*/aggregate.json", args.arm_d_aggregate)
    comparison = build_comparison_abcde(
        aggregate, arm_a_path, arm_b_path, arm_c_path, arm_d_path, out_root
    )

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
    rt = aggregate["pilot"]["reflection"]["telemetry_totals"]
    print(
        f"  reflection: {rt['proposals']} proposals "
        f"({rt['accepted']} accepted / {rt['rejected']} rejected); "
        f"revisions by seed "
        f"{aggregate['pilot']['reflection']['selfmodel_revisions_final_by_seed']}"
    )
    cal = aggregate["pilot"]["worldmodel"]["calibration_pooled"]
    print(
        f"  worldmodel calibration (pooled): predictions={cal['predictions']} "
        f"overall={json.dumps(cal['overall'])}"
    )
    pol = aggregate["pilot"]["policy"]["distribution_totals"]
    print(
        f"  policy: actions={pol['actions']} injections={pol['retrieve_injections']} "
        f"noops={pol['retrieve_noop_reasons']}"
    )
    print(
        f"comparison: {out_root / 'armA-vs-armB-vs-armC-vs-armD-vs-armE.json'} "
        f"(sources: {arm_a_path.name}, {arm_b_path.name}, {arm_c_path.name}, "
        f"{arm_d_path.name})"
    )
    for family in sorted(comparison["per_family"]):
        row = comparison["per_family"][family]
        print(
            f"  {family:22s} A={row['arm_A_mean']} B={row['arm_B_mean']} "
            f"C={row['arm_C_mean']} D={row['arm_D_mean']} E={row['arm_E_mean']} "
            f"E-D={row['arm_E_minus_arm_D']}"
        )
    ok = all(r["completed"] for r in run_summaries) and not seeds_skipped
    print(f"pilot completed={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
