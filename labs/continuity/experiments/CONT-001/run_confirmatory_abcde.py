"""CONT-001 CONFIRMATORY multi-arm run (M7): arms A-E x fixture v2 x predeclared
seeds {101, 202, 303, 404, 505}, one warm process (agent-pre-registered per
docs/EVALUATION-PREP.md, frozen at commit a845fc5).

EVERY artifact this script produces is labeled:
"agent-pre-registered, pending owner acceptance".

Relationship to the M6 runner (run_exploratory_abcde.py): the run semantics
are carried over UNCHANGED (same run_one_seed logic, budgets, memory/self-
model/reflection/policy wiring, one warm process, sampling options in every
request, per-seed fresh stores). The ONLY deltas, each labeled [D1]-[D7]:
  [D1] seeds {101,202,303,404,505} (EVALUATION-PREP.md 6.1; disjoint from all
       M1-M6 seeds and from the calibration seeds);
  [D2] fixture suite = fixtures/v2 (held-out, mechanically validated before
       any inference by validate_fixtures_v2.py);
  [D3] self-model = revision 1' estimated ONLY on the designated calibration
       suite (run_calibration_v2.py; CN-009 fix);
  [D4] run.start/aggregate/cross-arm labels are confirmatory + pending owner
       acceptance (no "exploratory" wording anywhere);
  [D5] freeze verification at start (6.9): frozen-config.json must exist in
       the run root and its recorded digests (fixtures, EVALUATION-PREP.md,
       self-model) and git rev must match the working tree, else exit 2
       (contamination halt, section 8);
  [D6] no pilot-consistency artifact (there is no pilot of v2 by design);
       the fixture-validation verdict and freeze verification take its place;
  [D7] wall-clock guard 120 min (M7 budget 150 min wall / 180 min GPU; on
       guard hit seeds are skipped and RECORDED - never silently reduced).

Usage (take the shared GPU lock around this):
    python labs/continuity/experiments/CONT-001/run_confirmatory_abcde.py \
        --run-root labs/continuity/results/CONT-001-confirmatory/<run_id>

Layout (under the run root):
    fixture-validation.json frozen-config.json calibration/ selfmodel-v2-calibration.json
    arm-<X>/seed-<n>/{trace.jsonl, summary.json, env.json
                      [, memory.sqlite3, memory-export.json, selfmodel-run.json]}
    arm-<X>/aggregate-arm-<X>.json
    cross-arm-table.json / cross-arm-table.md
"""

from __future__ import annotations

import argparse
import hashlib
import json
import platform
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))
sys.path.insert(0, str(LAB_ROOT / "experiments" / "CONT-000"))

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
from run_pilot_arm_d import gpu_snapshot, parse_reflection_events  # noqa: E402
from run_pilot_arm_e import parse_policy_events, parse_worldmodel_events, pooled_calibration  # noqa: E402

# --- Predeclared run configuration (fixed BEFORE any run; EVALUATION-PREP.md 6.1) ---
SEEDS: tuple[int, ...] = (101, 202, 303, 404, 505)  # [D1]
ARMS: tuple[str, ...] = ("A", "B", "C", "D", "E")
MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned by the P0a smoke (CN-001)
TEMPERATURE = 0.0
NUM_CTX = 4096
KEEP_ALIVE = "30m"
RUN_WALL_CLOCK_S = 120 * 60.0  # [D7] seed-skip guard; M7 budget is 150 min wall
SCENARIO_BUDGET = {"max_turns": 40, "max_total_tokens": 100_000, "wall_clock_s": 600.0}
FIXTURE_DIR = LAB_ROOT / "fixtures" / "v2"  # [D2]
PREP_DOC = LAB_ROOT / "docs" / "EVALUATION-PREP.md"
PREP_FREEZE_COMMIT = "a845fc5"
LABEL = "agent-pre-registered, pending owner acceptance"

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

SELFMODEL_RUN_CONFIG = {  # [D3]
    "source": (
        "selfmodel-v2-calibration.json in the run root (revision 1', estimated "
        "ONLY on the designated calibration suite fixtures/v2-calibration; "
        "per-run copies per seed)"
    ),
    "injection_rule": (
        "one system message immediately after the base system prompt in EVERY "
        "session; content = selfmodel.render_summary of the revision current "
        "at session start"
    ),
    "cn009_fix": (
        "revision 1' provenance.derived_from points at the calibration "
        "aggregate only (EVALUATION-PREP.md 6.8); in-run capability updates "
        "stay disabled (double-count guard active; calibration probes_per_seed "
        "exceeds the evaluation suite's per family)"
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


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_digest(fixture_dir: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in fixture_dir.rglob("*") if p.is_file()):
        h.update(path.relative_to(fixture_dir).as_posix().encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def git_changes_since(rev: str, paths: list[str]) -> list[str]:
    """Paths changed between `rev` and HEAD, limited to `paths`."""
    try:
        out = subprocess.check_output(
            ["git", "diff", "--name-only", rev, "HEAD", "--", *paths],
            cwd=str(LAB_ROOT), stderr=subprocess.DEVNULL,
        ).decode()
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return ["<git-diff-failed>"]


def git_status_dirty(paths: list[str]) -> list[str]:
    """Uncommitted changes under the given paths (forward-slash, repo-relative)."""
    try:
        out = subprocess.check_output(
            ["git", "status", "--porcelain", "--", *paths],
            cwd=str(LAB_ROOT), stderr=subprocess.DEVNULL,
        ).decode()
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return ["<git-status-failed>"]


def verify_freeze(run_root: Path) -> dict[str, Any]:
    """[D5] Contamination halt per section 8 / freeze discipline 6.9.

    Section 6.9 freezes: fixture v2, seeds, the self-model calibration
    artifact, and docs/EVALUATION-PREP.md. The rev-drift and dirty checks are
    scoped to exactly those paths (the run scripts themselves are not frozen
    content; they are committed before the run but may receive pre-run
    mechanical fixes - each recorded in LOG.md).
    """
    frozen_path = run_root / "frozen-config.json"
    if not frozen_path.exists():
        print(
            "FAIL-CLOSED: frozen-config.json missing from the run root - the freeze "
            "(6.9) must precede the first confirmatory inference request",
            file=sys.stderr,
        )
        raise SystemExit(2)
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))
    problems: list[str] = []

    frozen_paths = [
        "labs/continuity/fixtures",
        "labs/continuity/docs/EVALUATION-PREP.md",
        "labs/continuity/state",
        f"labs/continuity/{str(run_root.relative_to(LAB_ROOT)).replace(chr(92), '/')}/calibration",
        f"labs/continuity/{str(run_root.relative_to(LAB_ROOT)).replace(chr(92), '/')}/selfmodel-v2-calibration.json",
        f"labs/continuity/{str(run_root.relative_to(LAB_ROOT)).replace(chr(92), '/')}/fixture-validation.json",
    ]

    prep_sha = sha256_file(PREP_DOC)
    if prep_sha != frozen["protocol"]["evaluation_prep_sha256"]:
        problems.append(f"EVALUATION-PREP.md sha256 {prep_sha} != frozen {frozen['protocol']['evaluation_prep_sha256']}")
    if frozen["protocol"].get("evaluation_prep_frozen_commit", frozen["protocol"].get("frozen_commit")) != PREP_FREEZE_COMMIT:
        problems.append("frozen-config records a different protocol freeze commit than the runner constant")

    eval_sha = suite_digest(FIXTURE_DIR)
    if eval_sha != frozen["fixtures"]["evaluation_suite_sha256"]:
        problems.append("fixtures/v2 digest changed after freeze")
    cal_sha = suite_digest(LAB_ROOT / "fixtures" / "v2-calibration")
    if cal_sha != frozen["fixtures"]["calibration_suite_sha256"]:
        problems.append("fixtures/v2-calibration digest changed after freeze")

    sm_path = run_root / "selfmodel-v2-calibration.json"
    if not sm_path.exists():
        problems.append("selfmodel-v2-calibration.json missing")
    else:
        try:
            sm = load_selfmodel(str(sm_path))
        except Exception as exc:
            problems.append(f"self-model store invalid: {exc}")
            sm = None
        if sm is not None:
            sha = selfmodel_sha256(sm)
            if sha != frozen["selfmodel"]["sha256"]:
                problems.append("self-model sha256 changed after freeze")
            derived = sm.get("provenance", {}).get("derived_from", "")
            cal_rel = frozen["selfmodel"]["calibration_aggregate_rel"]
            if derived != cal_rel:
                problems.append(
                    f"self-model provenance points at {derived!r}, not the calibration artifact {cal_rel!r}"
                )
            if sorted(sm.get("capabilities", [{}])[0].get("seeds", [])) != sorted(
                frozen["selfmodel"]["calibration_seeds"]
            ):
                problems.append("self-model capability seeds do not match the calibration seeds")

    rev = git_rev()
    changed_frozen = git_changes_since(frozen["freeze"]["git_rev"], frozen_paths)
    if changed_frozen:
        problems.append(
            f"frozen paths changed since the freeze commit "
            f"{frozen['freeze']['git_rev'][:12]}: {changed_frozen}"
        )
    dirty = git_status_dirty(frozen_paths)
    if dirty:
        problems.append(f"uncommitted changes on frozen paths (post-freeze edit?): {dirty}")

    verification = {
        "kind": "freeze-verification",
        "label": LABEL,
        "checked_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "git_rev": rev,
        "evaluation_prep_sha256": prep_sha,
        "evaluation_suite_sha256": eval_sha,
        "calibration_suite_sha256": cal_sha,
        "problems": problems,
        "passed": not problems,
    }
    (run_root / "freeze-verification.json").write_text(
        json.dumps(verification, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    if problems:
        for p in problems:
            print(f"FAIL-CLOSED (contamination halt, section 8): {p}", file=sys.stderr)
        raise SystemExit(2)
    print(f"freeze verification PASSED (git rev {rev[:12]}...)")
    return frozen


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
        "kind": "cont001-confirmatory",  # [D4]
        "label": LABEL,
        "pre_registration": {
            "doc": "labs/continuity/docs/EVALUATION-PREP.md",
            "frozen_commit": PREP_FREEZE_COMMIT,
            "review": "labs/continuity/docs/PR-REVIEW.md (M6b verdict GO)",
        },
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
        "confirmatory_note": (
            "confirmatory CONT-001 pass (M7) executing the frozen "
            "pre-registration; held-out fixture v2; agent-pre-registered, "
            "pending owner acceptance"
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
        "label": LABEL,
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
        "label": LABEL,
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
        capability_updates_accepted = sum(
            engine.telemetry["accepted_by_type"].get("selfmodel_capability_update", 0)
        )
        summary["inrun_capability_updates_accepted"] = capability_updates_accepted
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
            "kind": "cont001-confirmatory",
            "label": LABEL,
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
                **({"inrun_capability_updates_accepted": r["inrun_capability_updates_accepted"]} if "inrun_capability_updates_accepted" in r else {}),
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
    fixture_validation: dict[str, Any],
    freeze_verification: dict[str, Any],
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
        "kind": "cont001-confirmatory-cross-arm-table",
        "confirmatory": True,
        "label": LABEL,
        "pre_registration": {
            "doc": "labs/continuity/docs/EVALUATION-PREP.md",
            "frozen_commit": PREP_FREEZE_COMMIT,
        },
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_id": run_id,
        "config": {
            "model": MODEL,
            "model_digest": env_common["digest"],
            "ollama_version": env_common["ollama_version"],
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "seeds_predeclared": list(SEEDS),
            "seed_count_rationale": "docs/SIZING.md recommendation: 5 seeds (fresh confirmatory seeds per EVALUATION-PREP.md 6.1)",
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
        "fixture_validation_verdict": fixture_validation.get("verdict"),
        "freeze_verification_passed": freeze_verification.get("passed"),
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
            "CONFIRMATORY (agent-pre-registered, pending owner acceptance) - executes docs/EVALUATION-PREP.md exactly; no post-hoc metric switching.",
            "Fixture v2 is held-out: new scenario ids/content, no option lists on probe turns (CN-004 fix), RM probes on non-first session turns with expected arm-E actuation >= 1 physical injection per seed (CN-010 fix).",
            "Arm C-E self-model revision 1' was estimated ONLY on the designated calibration suite (CN-009 fix); in-run capability updates stayed disabled (double-count guard).",
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
        "# CONT-001 confirmatory — cross-arm table (M7)",
        "",
        f"**{table['label']}**",
        "",
        f"- run `{table['run_id']}` (confirmatory; pre-registration frozen at "
        f"`{table['pre_registration']['frozen_commit']}`)",
        f"- model `{cfg['model']}`, digest `{cfg['model_digest'][:12]}…`, "
        f"temp {cfg['temperature']}, num_ctx {cfg['num_ctx']}",
        f"- seeds {cfg['seeds_predeclared']} (fresh, EVALUATION-PREP.md 6.1), arms {cfg['arms']}, "
        f"{cfg['scenarios']} scenarios / {cfg['turns_per_seed']} turns / "
        f"{cfg['probes_per_seed']} probes per seed, one warm process",
        f"- fixture validation verdict: {table['fixture_validation_verdict']}; "
        f"freeze verification passed: {table['freeze_verification_passed']}",
        f"- GPU wall {table['time_budget']['total_gpu_wall_s']} s under the shared "
        f"lock (cap {table['time_budget']['budget_gpu_cap_min']} min); "
        f"script wall {table['time_budget']['script_wall_s']} s "
        f"(cap {table['time_budget']['budget_wall_cap_min']} min)",
        "",
        "Pass rates are mean over seeds; brackets show the cross-seed range (min-max).",
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
    lines.append(
        f"| **overall ({cfg['probes_per_seed']})** | "
        + " | ".join(f"**{c}**" for c in overall_cells) + " |"
    )

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
        "The confirmatory claim is decided ONLY by the pre-registered primary "
        "analysis (`repeated-mistake-analysis.md`): RM(E) - RM(A), two-sided 95% "
        "paired cluster bootstrap over scenarios, MME 0.15. This table is "
        "descriptive. " + table["label"] + ".",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument(
        "--run-root", required=True,
        help="confirmatory run root (results/CONT-001-confirmatory/<run_id>)",
    )
    args = parser.parse_args()
    run_root = Path(args.run_root)
    if not run_root.is_absolute():
        # accept CWD-relative, lab-relative, and repo-root-relative forms
        if run_root.exists():
            run_root = run_root.resolve()
        elif (LAB_ROOT / run_root).exists():
            run_root = (LAB_ROOT / run_root).resolve()
        else:
            run_root = (LAB_ROOT.parents[1] / run_root).resolve()
    if not run_root.is_dir():
        print(f"FAIL-CLOSED: run root not found: {run_root}", file=sys.stderr)
        return 2
    run_id = run_root.name

    fixture_validation_path = run_root / "fixture-validation.json"
    if not fixture_validation_path.exists():
        print(
            "FAIL-CLOSED: fixture-validation.json missing - the pre-inference "
            "validator must pass before any confirmatory inference",
            file=sys.stderr,
        )
        return 2
    fixture_validation = json.loads(fixture_validation_path.read_text(encoding="utf-8"))
    if fixture_validation.get("verdict") != "PASS":
        print(f"FAIL-CLOSED: fixture validation verdict is {fixture_validation.get('verdict')}", file=sys.stderr)
        return 2

    frozen = verify_freeze(run_root)

    manifest, scenarios = load_suite(str(FIXTURE_DIR))
    total_turns = sum(len(s["turns"]) for s in scenarios for s in s["sessions"])
    print(f"suite: {len(scenarios)} scenarios, families={manifest['families']}")
    print(
        f"plan: arms {list(ARMS)} x {len(SEEDS)} seeds x {total_turns} turns = "
        f"{len(ARMS) * len(SEEDS) * total_turns} requests "
        f"(predeclared seeds {list(SEEDS)})"
    )

    selfmodel_path = run_root / "selfmodel-v2-calibration.json"
    try:
        base_selfmodel = load_selfmodel(str(selfmodel_path))
    except Exception as exc:
        print(f"FAIL-CLOSED: calibration self-model invalid: {exc}", file=sys.stderr)
        raise SystemExit(2)
    base_sha = selfmodel_sha256(base_selfmodel)
    selfmodel_source = str(selfmodel_path.relative_to(LAB_ROOT)).replace("\\", "/")
    print(
        f"self-model ok: agent {base_selfmodel['agentId']}, revision "
        f"{base_selfmodel['revision']}, sha {base_sha[:12]}... "
        f"(calibration-derived, per-run copies)"
    )

    env_common = preflight(args.base_url, MODEL)
    env_common["git_rev"] = git_rev()
    frozen_paths = [
        "labs/continuity/fixtures",
        "labs/continuity/docs/EVALUATION-PREP.md",
        "labs/continuity/state",
        f"labs/continuity/{str(run_root.relative_to(LAB_ROOT)).replace(chr(92), '/')}/calibration",
        f"labs/continuity/{str(run_root.relative_to(LAB_ROOT)).replace(chr(92), '/')}/selfmodel-v2-calibration.json",
        f"labs/continuity/{str(run_root.relative_to(LAB_ROOT)).replace(chr(92), '/')}/fixture-validation.json",
    ]
    changed_frozen = git_changes_since(frozen["freeze"]["git_rev"], frozen_paths)
    if changed_frozen:
        print(
            f"FAIL-CLOSED: frozen paths changed since freeze "
            f"({changed_frozen})",
            file=sys.stderr,
        )
        return 2
    print(
        f"preflight ok: ollama {env_common['ollama_version']}, digest "
        f"{env_common['digest'][:12]}..., warmup {env_common['warmup_s']}s"
    )
    gpu_at_start = gpu_snapshot(args.base_url)
    print(f"gpu snapshot (CN-005): {gpu_at_start}")

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
                    f"arm {arm} seed {seed} (recorded, not silent)",
                    file=sys.stderr,
                )
                continue
            print(f"--- arm {arm} seed {seed} starting ({time.strftime('%H:%M:%S')})")
            seeds_run.append(seed)
            run_summaries.append(
                run_one_seed(
                    arm, seed, scenarios, run_root, run_id, args.base_url, env_common,
                    base_selfmodel, base_sha, selfmodel_source, str(selfmodel_path),
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

    table = build_cross_arm_table(
        run_id, arm_aggregates, scenarios, env_common, total_gpu_wall_s,
        time.monotonic() - script_started, env_common["warmup_s"], gpu_at_start,
        fixture_validation, json.loads((run_root / "freeze-verification.json").read_text(encoding="utf-8")),
    )
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
    print(f"total GPU wall: {total_gpu_wall_s:.0f}s (cap {180 * 60}s)")
    print(f"all completed={all_ok}")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
