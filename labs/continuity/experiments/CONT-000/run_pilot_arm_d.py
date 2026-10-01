"""CONT-000 mini-pilot, arm D: full fixture suite x predeclared seeds, one warm
process, per-seed persistent memory + self-model + the bounded post-session
reflection pass (M4).

Usage (from anywhere; take the shared GPU lock around this, see
shared/tooling/agent-resource-coordination/PROTOCOL.md):

    python labs/continuity/experiments/CONT-000/run_pilot_arm_d.py

Mirrors run_pilot_arm_c.py (M3) with the arm-D additions:
- arm="D" passed to run_scenario (arm C semantics + ONE deterministic
  reflection pass after each non-stopped session);
- each seed gets a per-run COPY `selfmodel-run.json` of `state/selfmodel.json`
  (revision 1) that evolves only through accepted, evidence-gated proposals
  via the fail-closed `selfmodel.commit()`; the canonical store is untouched;
- accepted episode summaries land as NEW episodes (role `reflection.summary`)
  in the same SQLite store and surface through the unchanged memory injection
  rule; accepted self-model revisions render in later sessions;
- accept/reject telemetry is aggregated (per type) into aggregate.json;
- after the runs, an arm A vs arm B vs arm C vs arm D per-family comparison
  artifact is written next to the aggregate (A/B/C numbers are read from the
  M1/M2/M3 pilot aggregates, never re-run).

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
sys.path.insert(0, str(Path(__file__).resolve().parent))  # reuse M2 pilot helpers

from continuity import PROTOCOL_VERSION  # noqa: E402
from continuity.events import EventJournal, validate_trace  # noqa: E402
from continuity.fixtures import load_suite  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.reflection import ReflectionEngine  # noqa: E402
from continuity.runner import MEMORY_TOP_K, Budget, run_scenario  # noqa: E402
from continuity.selfmodel import load as load_selfmodel  # noqa: E402
from continuity.selfmodel import selfmodel_sha256  # noqa: E402

from run_pilot_arm_b import (  # noqa: E402
    DETERMINISM_CAVEAT,
    git_rev,
    parse_memory_events,
    parse_request_stats,
    percentile,
    preflight,
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
    "cn009_exposure": (
        "reflection-derived estimates come from in-run probe outcomes and render "
        "into later sessions of the same run (CN-009 amplified; auditable via "
        "provenance.method starting with 'reflection' and trace refs; rendered "
        "failure-pattern text shows observed answers, never expected answers)"
    ),
}


def parse_reflection_events(trace_path: Path) -> dict[str, Any]:
    """Reflection evidence from the trace (proposal/accept/reject counts)."""
    by_type: dict[str, dict[str, int]] = {}
    passes = 0
    with open(trace_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            if record.get("type") == "reflection.start":
                passes += 1
            elif record.get("type") == "reflection.proposal":
                ptype = record["payload"]["type"]
                slot = by_type.setdefault(ptype, {"proposals": 0, "accepted": 0, "rejected": 0})
                slot["proposals"] += 1
                slot["accepted" if record["payload"]["accepted"] else "rejected"] += 1
    return {"passes": passes, "by_type": by_type}


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
            "kind": "pilot-armD",
            "pilot_run_id": pilot_run_id,
            "arm": "D",
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
        "arm": "D",
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
    started = time.monotonic()
    scenario_summaries: list[dict[str, Any]] = []
    budget_stops = 0
    for scenario in scenarios:
        budget = Budget(**SCENARIO_BUDGET)
        scenario_summaries.append(
            run_scenario(
                scenario, provider, journal, budget, arm="D",
                memory=memory, selfmodel=engine.model, reflection=engine,
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
        "arm": "D",
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
            "kind": "pilot-armD",
            "arm": "D",
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
                    "revision current at session start (arm D: may have been "
                    "updated by earlier accepted reflection proposals)"
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
    }


def find_aggregate(pattern: str, explicit: str | None) -> Path:
    if explicit:
        path = Path(explicit)
        if not path.exists():
            raise SystemExit(f"FAIL-CLOSED: aggregate not found: {path}")
        return path
    candidates = sorted((LAB_ROOT / "results" / "CONT-000").glob(pattern))
    if not candidates:
        raise SystemExit(f"FAIL-CLOSED: no aggregate matching {pattern} under results/CONT-000")
    return candidates[-1]


def gpu_snapshot(base_url: str) -> dict[str, Any]:
    """CN-005 attribution snapshot: nvidia-smi total + ollama residents."""
    snap: dict[str, Any] = {"nvidia_smi_used_mib": None, "ollama_ps": []}
    try:
        out = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader"],
            stderr=subprocess.DEVNULL, timeout=10,
        ).decode().strip()
        snap["nvidia_smi_used_mib"] = int(out.split()[0])
    except Exception:
        pass
    try:
        with urllib.request.urlopen(base_url + "/api/ps", timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
        snap["ollama_ps"] = [
            {
                "name": m.get("name"),
                "digest": m.get("digest", "")[:12],
                "size_vram_mib": round(m.get("size_vram", 0) / (1024 * 1024), 1),
            }
            for m in data.get("models", [])
        ]
    except Exception:
        pass
    return snap


def build_comparison_abcd(
    arm_d_aggregate: dict[str, Any],
    arm_a_path: Path,
    arm_b_path: Path,
    arm_c_path: Path,
    out_dir: Path,
) -> dict[str, Any]:
    """Per-family arm A vs B vs C vs D table (numbers only, exploratory)."""
    arm_a = json.loads(arm_a_path.read_text(encoding="utf-8"))
    arm_b = json.loads(arm_b_path.read_text(encoding="utf-8"))
    arm_c = json.loads(arm_c_path.read_text(encoding="utf-8"))

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

    a, b, c, d = (
        arm_view(arm_a), arm_view(arm_b), arm_view(arm_c), arm_view(arm_d_aggregate)
    )
    families = sorted(
        set(a["per_family"]) | set(b["per_family"]) | set(c["per_family"]) | set(d["per_family"])
    )

    per_family_table = {}
    for family in families:
        per_family_table[family] = {
            "arm_A_mean": a["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_B_mean": b["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_C_mean": c["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_D_mean": d["per_family"].get(family, {}).get("mean_pass_rate"),
            "arm_D_minus_arm_C": None
            if not d["per_family"].get(family) or not c["per_family"].get(family)
            else round(
                d["per_family"][family]["mean_pass_rate"]
                - c["per_family"][family]["mean_pass_rate"],
                3,
            ),
            "arm_D_pass_rate_by_seed": d["per_family"].get(family, {}).get(
                "pass_rate_by_seed"
            ),
        }

    comparison = {
        "kind": "armA-vs-armB-vs-armC-vs-armD-per-family",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "arm_a_source": str(arm_a_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_b_source": str(arm_b_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_c_source": str(arm_c_path.relative_to(LAB_ROOT)).replace("\\", "/"),
        "arm_d_source": "aggregate.json (this directory)",
        "shared_config": {
            "model": arm_b["pilot"]["model"],
            "model_digest": arm_b["pilot"]["model_digest"],
            "temperature": arm_b["pilot"]["temperature"],
            "num_ctx": arm_b["pilot"]["num_ctx"],
            "scenario_order": arm_b["pilot"]["scenario_order"],
            "note": (
                "seeds differ by design (arm A: 5 predeclared M1 seeds; arms B/C/D: "
                "first 3 of the same predeclared list, per the M2/M3/M4 briefs)"
            ),
        },
        "arms": {
            "A": {"seeds": a["seeds"]},
            "B": {"seeds": b["seeds"]},
            "C": {"seeds": c["seeds"]},
            "D": {"seeds": d["seeds"]},
        },
        "per_family": per_family_table,
        "per_scenario_pass_counts": {
            sid: {
                "arm_A": a["per_scenario_pass_count"].get(sid),
                "arm_B": b["per_scenario_pass_count"].get(sid),
                "arm_C": c["per_scenario_pass_count"].get(sid),
                "arm_D": d["per_scenario_pass_count"].get(sid),
            }
            for sid in arm_b["pilot"]["scenario_order"]
        },
        "notes": [
            (
                "CN-007 watch (repeated_task, the own-answer-anchoring family): "
                "arm B 0.333 / arm C 0.333 — see per_scenario rows rt-0001/2/3 for "
                "whether arm D's reflection (conflict-review summaries) moved it."
            ),
            (
                "CN-009 amplification: arm D's self-model evolves in-run from probe "
                "outcomes and renders into later sessions; every reflection-derived "
                "estimate carries provenance.method starting with 'reflection'."
            ),
        ],
    }

    (out_dir / "armA-vs-armB-vs-armC-vs-armD.json").write_text(
        json.dumps(comparison, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    lines = [
        "# Arm A vs arm B vs arm C vs arm D — per family (M4 mini-pilot)",
        "",
        f"- arm A source: `{comparison['arm_a_source']}` (seeds {a['seeds']})",
        f"- arm B source: `{comparison['arm_b_source']}` (seeds {b['seeds']})",
        f"- arm C source: `{comparison['arm_c_source']}` (seeds {c['seeds']})",
        f"- arm D source: `{comparison['arm_d_source']}` (seeds {d['seeds']})",
        f"- model {comparison['shared_config']['model']}, digest "
        f"`{comparison['shared_config']['model_digest'][:12]}…`, temp "
        f"{comparison['shared_config']['temperature']}, num_ctx "
        f"{comparison['shared_config']['num_ctx']}",
        "- arm D = arm C + one deterministic post-session reflection pass "
        "(episode summaries with conflict review; evidence-gated self-model "
        "revisions through the fail-closed store)",
        "",
        "| family | A mean | B mean | C mean | D mean | D - C |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for family in families:
        row = per_family_table[family]
        delta = row["arm_D_minus_arm_C"]
        delta_str = "n/a" if delta is None else f"{delta:+.3f}"
        lines.append(
            f"| {family} | {row['arm_A_mean']} | {row['arm_B_mean']} | "
            f"{row['arm_C_mean']} | {row['arm_D_mean']} | {delta_str} |"
        )
    lines += [
        "",
        "Per-scenario pass counts (passed probes / seeds x 1 probe):",
        "",
        "| scenario | arm A | arm B | arm C | arm D |",
        "| --- | --- | --- | --- | --- |",
    ]
    for sid, counts in comparison["per_scenario_pass_counts"].items():
        lines.append(
            f"| {sid} | {counts['arm_A']}/{len(a['seeds'])} "
            f"| {counts['arm_B']}/{len(b['seeds'])} | {counts['arm_C']}/{len(c['seeds'])} "
            f"| {counts['arm_D']}/{len(d['seeds'])} |"
        )
    lines += [
        "",
        "Exploratory mini-pilot numbers only. Caveats: CN-009 (the arm-C/D "
        "self-model was estimated on this same fixture suite from the arm-B "
        "pilot, and under arm D additionally evolves in-run from probe "
        "outcomes that render into later sessions); CN-004 (rt-0003 option "
        "leakage inflates arm A there). Not the confirmatory CONT-001 contrast.",
    ]
    (out_dir / "armA-vs-armB-vs-armC-vs-armD.md").write_text(
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

    pilot_run_id = time.strftime("pilot-armD-%Y%m%d-%H%M%S")
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
    comparison = build_comparison_abcd(aggregate, arm_a_path, arm_b_path, arm_c_path, out_root)

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
        f"revisions by seed {aggregate['pilot']['reflection']['selfmodel_revisions_final_by_seed']}"
    )
    print(
        f"comparison: {out_root / 'armA-vs-armB-vs-armC-vs-armD.json'} "
        f"(sources: {arm_a_path.name}, {arm_b_path.name}, {arm_c_path.name})"
    )
    for family in sorted(comparison["per_family"]):
        row = comparison["per_family"][family]
        print(
            f"  {family:22s} A={row['arm_A_mean']} B={row['arm_B_mean']} "
            f"C={row['arm_C_mean']} D={row['arm_D_mean']} D-C={row['arm_D_minus_arm_C']}"
        )
    ok = all(r["completed"] for r in run_summaries) and not seeds_skipped
    print(f"pilot completed={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
