"""CONT-001 confirmatory: self-model calibration run (M7, EVALUATION-PREP.md 6.8).

Runs arm B (the M2 pilot code path, imported and reused unchanged) over the
designated calibration suite `fixtures/v2-calibration/` on the pinned core,
then derives self-model revision 1' ONLY from that calibration aggregate.

Provenance rules (frozen plan section 6.8 / section 8):
- revision 1' capabilities are recomputed from the calibration aggregate's
  per-family counts (same arithmetic as selfmodel.build_from_arm_b_aggregate,
  mirrored here with the CN-007/CN-008 failure-pattern evidence scenarios
  PARAMETERIZED to calibration scenarios — the M3 builder hard-codes the v1
  ids rt-0003/cu-0001, which must NOT appear in a calibration-derived store);
- provenance.derived_from points at the calibration aggregate artifact (the
  analysis halts if it points anywhere else);
- calibration seeds are the v1 calibration seeds {11, 22, 33}; the
  confirmatory seeds {101, 202, 303, 404, 505} are NEVER used for calibration
  (section 6.1);
- in-run capability updates remain disabled during the confirmatory run by
  the calibration suite's guard sizing (validator check C4).

Usage (take the shared GPU lock around this):
    python labs/continuity/experiments/CONT-001/run_calibration_v2.py \
        --run-root labs/continuity/results/CONT-001-confirmatory/<run_id>

Writes calibration/ (seed dirs + aggregate.json) and selfmodel-v2-calibration.json
into the run root. Fail-closed exit 2 on any preflight/store/verification error.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))
sys.path.insert(0, str(LAB_ROOT / "experiments" / "CONT-000"))
sys.path.insert(0, str(LAB_ROOT / "experiments" / "CONT-001"))

from continuity.fixtures import load_suite  # noqa: E402
from continuity.selfmodel import (  # noqa: E402
    SelfModelError,
    binomial_sd,
    commit as selfmodel_commit,
    load as load_selfmodel,
    selfmodel_sha256,
    validate as selfmodel_validate,
    wilson_interval,
)
from run_pilot_arm_b import (  # noqa: E402
    MODEL,
    build_aggregate as build_arm_b_aggregate,
    git_rev,
    parse_memory_events,
    parse_request_stats,
    preflight,
    run_one_seed,
)

CALIBRATION_SEEDS = (11, 22, 33)  # v1 calibration seeds; confirmatory seeds never used here (6.1)
CAL_DIR = LAB_ROOT / "fixtures" / "v2-calibration"
CN007_EVIDENCE_SCENARIO = "cal-RT1"  # calibration analogues of the v1 evidence scenarios
CN008_EVIDENCE_SCENARIO = "cal-CU1"
LABEL = "agent-pre-registered, pending owner acceptance"


def build_revision_1p_from_calibration(
    aggregate: dict[str, Any], *, source_artifact: str
) -> dict[str, Any]:
    """Revision 1' from the calibration aggregate only.

    Mirrors selfmodel.build_from_arm_b_aggregate (same arithmetic, same
    validation) with two deltas required by EVALUATION-PREP.md 6.8:
    (a) the CN-007/CN-008 failure-pattern evidence scenarios are the
    calibration analogues (cal-RT1 / cal-CU1), not the v1 evaluation ids;
    (b) provenance records the calibration-only estimation and the guard
    sizing that keeps in-run capability updates disabled.
    """
    pilot = aggregate.get("pilot", {})
    if pilot.get("arm") != "B":
        raise SelfModelError(f"aggregate is arm {pilot.get('arm')!r}, expected 'B'")
    per_family = aggregate.get("per_family")
    per_scenario = aggregate.get("per_scenario", {})
    if not isinstance(per_family, dict) or not per_family:
        raise SelfModelError("aggregate has no per_family data")
    seeds_run = pilot.get("seeds_run")
    if not seeds_run:
        raise SelfModelError("aggregate has no seeds_run")
    if sorted(seeds_run) != sorted(CALIBRATION_SEEDS):
        raise SelfModelError(f"calibration seeds must be {list(CALIBRATION_SEEDS)}, got {seeds_run}")

    capabilities: list[dict[str, Any]] = []
    for family in sorted(per_family):
        entry = per_family[family]
        passed_by_seed = entry.get("passed_by_seed", {})
        probes_per_seed = entry.get("probes_per_seed")
        if not passed_by_seed or not probes_per_seed:
            raise SelfModelError(f"{family}: missing passed_by_seed/probes_per_seed")
        missing = [s for s in seeds_run if str(s) not in passed_by_seed]
        if missing:
            raise SelfModelError(f"{family}: no counts for seeds {missing}")
        passed = sum(int(passed_by_seed[str(s)]) for s in seeds_run)
        total = int(probes_per_seed) * len(seeds_run)
        capabilities.append(
            {
                "family": family,
                "unit": "probe pass rate",
                "passed": passed,
                "total": total,
                "seeds": list(seeds_run),
                "probes_per_seed": int(probes_per_seed),
                "rate": round(passed / total, 3),
                "wilson95": wilson_interval(passed, total),
                "binomial_sd": binomial_sd(passed, total),
                "provenance": {
                    "source_artifact": source_artifact,
                    "method": (
                        "sum of per-family probe pass counts across the calibration "
                        "aggregate's seeds_run (calibration suite only)"
                    ),
                    "numbers": {
                        "passed_by_seed": {str(k): v for k, v in sorted(passed_by_seed.items())},
                        "probes_per_seed": probes_per_seed,
                        "model": pilot.get("model"),
                        "model_digest": pilot.get("model_digest"),
                        "temperature": pilot.get("temperature"),
                        "run_id": pilot.get("run_id"),
                    },
                },
            }
        )

    def scenario_evidence(sid: str, what: str) -> dict[str, Any]:
        slot = per_scenario.get(sid)
        if not slot:
            raise SelfModelError(f"cannot seed failure-pattern evidence: {sid} missing ({what})")
        observations: dict[str, list[dict[str, Any]]] = slot.get("observations_by_seed", {})
        observed = sorted(
            {o.get("observed_normalized", "") for obs in observations.values() for o in obs}
        )
        return {
            "scenario": sid,
            "family": slot.get("family"),
            "pass_count": slot.get("pass_count"),
            "seeds": len(observations),
            "observed_normalized": observed,
        }

    rt_cal = scenario_evidence(CN007_EVIDENCE_SCENARIO, "CN-007")
    cu_cal = scenario_evidence(CN008_EVIDENCE_SCENARIO, "CN-008")
    known_failure_patterns = [
        {
            "id": "CN-007",
            "title": "own-answer anchoring",
            "pattern": (
                "The agent's own early answers, once stored in persistent memory, "
                "anchor later answers even when a later session supplies the "
                "correcting rubric; an early misclassification can repeat across "
                "sessions instead of being revised."
            ),
            "evidence": {
                "refs": [
                    "labs/continuity/docs/FINDINGS.md#CN-007",
                    f"calibration scenario {CN007_EVIDENCE_SCENARIO} (v2-calibration suite)",
                ],
                "numbers": rt_cal,
            },
        },
        {
            "id": "CN-008",
            "title": "no supersession of corrected facts",
            "pattern": (
                "When a later session corrects an earlier fact, keyword memory "
                "recalls both versions and the superseded value may be repeated "
                "even though the correction was retrieved first; conflict "
                "resolution is the gap."
            ),
            "evidence": {
                "refs": [
                    "labs/continuity/docs/FINDINGS.md#CN-008",
                    f"calibration scenario {CN008_EVIDENCE_SCENARIO} (v2-calibration suite)",
                ],
                "numbers": cu_cal,
            },
        },
    ]

    now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    return {
        "format": "continuity-selfmodel",
        "schemaVersion": 1,
        "agentId": f"continuity/{pilot.get('model', 'unknown')}@{str(pilot.get('model_digest', ''))[:12]}",
        "revision": 1,
        "createdUtc": now,
        "updatedUtc": now,
        "lastConsolidation": None,
        "capabilities": capabilities,
        "knownFailurePatterns": known_failure_patterns,
        "provenance": {
            "derived_from": source_artifact,
            "method": (
                "capabilities recomputed from per-family probe counts of the "
                "designated calibration run; failure patterns seeded from "
                "CN-007/CN-008 evidence in the same calibration aggregate"
            ),
            "note": (
                "calibration-only estimation per docs/EVALUATION-PREP.md 6.8 "
                "(CN-009 fix): calibration scenarios are disjoint from the "
                "evaluation suite and from fixtures/v1; no M1-M6 or pilot "
                "aggregate feeds this store; calibration probes_per_seed per "
                "family exceeds the evaluation suite's, so the reflection "
                "double-count guard keeps in-run capability updates disabled "
                "during the confirmatory run"
            ),
            "agent_id_basis": {
                "model": pilot.get("model"),
                "model_digest": pilot.get("model_digest"),
            },
        },
    }


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
        run_root = LAB_ROOT / run_root
    if run_root.exists() and (run_root / "frozen-config.json").exists():
        print(
            "FAIL-CLOSED: frozen-config.json already exists in the run root - "
            "calibration must precede the freeze (6.9)",
            file=sys.stderr,
        )
        return 2
    cal_root = run_root / "calibration"
    cal_root.mkdir(parents=True, exist_ok=True)

    manifest, scenarios = load_suite(str(CAL_DIR))
    total_turns = sum(len(s["turns"]) for s in scenarios for s in s["sessions"])
    print(
        f"calibration suite: {len(scenarios)} scenarios, families={manifest['families']}, "
        f"{total_turns} turns x {len(CALIBRATION_SEEDS)} seeds = "
        f"{total_turns * len(CALIBRATION_SEEDS)} requests (seeds {list(CALIBRATION_SEEDS)})"
    )

    env_common = preflight(args.base_url, MODEL)
    env_common["git_rev"] = git_rev()
    print(
        f"preflight ok: ollama {env_common['ollama_version']}, digest "
        f"{env_common['digest'][:12]}..., warmup {env_common['warmup_s']}s"
    )

    cal_run_id = time.strftime("cont001-calibration-%Y%m%d-%H%M%S")
    started = time.monotonic()
    run_summaries: list[dict[str, Any]] = []
    seeds_run: list[int] = []
    for seed in CALIBRATION_SEEDS:
        print(f"--- calibration arm B seed {seed} ({time.strftime('%H:%M:%S')})")
        seeds_run.append(seed)
        run_summaries.append(
            run_one_seed(seed, scenarios, cal_root, cal_run_id, args.base_url, env_common)
        )
        r = run_summaries[-1]
        print(
            f"seed {seed}: probes {r['probes_passed']}/{r['probes_total']}, "
            f"tokens {r['tokens_total']}, wall {r['wall_s']}s, completed={r['completed']}"
        )
    if not all(r["completed"] for r in run_summaries):
        print("FAIL-CLOSED: a calibration seed-run did not complete", file=sys.stderr)
        return 2

    request_stats: list[dict[str, Any]] = []
    memory_stats: list[dict[str, Any]] = []
    for r in run_summaries:
        seed_dir = cal_root / f"seed-{r['seed']}"
        request_stats.extend(parse_request_stats(seed_dir / "trace.jsonl"))
        memory_stats.append({"seed": r["seed"], **parse_memory_events(seed_dir / "trace.jsonl")})

    aggregate = build_arm_b_aggregate(
        cal_run_id, cal_root, seeds_run, [], scenarios, run_summaries,
        request_stats, memory_stats, env_common,
    )
    aggregate["kind"] = "cont001-confirmatory-calibration"
    aggregate["label"] = LABEL
    aggregate["calibration_note"] = (
        "self-model calibration run for the confirmatory CONT-001 pass "
        "(EVALUATION-PREP.md 6.8): designated calibration scenarios only, "
        "disjoint from the evaluation suite and from fixtures/v1; this "
        "aggregate is the ONLY input to the confirmatory self-model revision 1'"
    )
    aggregate_rel = str((cal_root / "aggregate.json").relative_to(LAB_ROOT)).replace("\\", "/")
    (cal_root / "aggregate.json").write_text(
        json.dumps(aggregate, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    candidate = build_revision_1p_from_calibration(
        json.loads(json.dumps(aggregate)), source_artifact=aggregate_rel
    )
    errors = selfmodel_validate(candidate)
    if errors:
        print(f"FAIL-CLOSED: revision-1' candidate invalid: {errors}", file=sys.stderr)
        return 2
    out_path = run_root / "selfmodel-v2-calibration.json"
    committed = selfmodel_commit(str(out_path), candidate)  # new store -> revision 1
    reloaded = load_selfmodel(str(out_path))
    sha = selfmodel_sha256(reloaded)
    print(
        f"self-model revision 1' committed: {out_path.name}, agent "
        f"{committed['agentId']}, {len(committed['capabilities'])} capability "
        f"estimates, sha256 {sha[:12]}..."
    )
    for cap in committed["capabilities"]:
        print(f"  {cap['family']}: {cap['passed']}/{cap['total']} rate {cap['rate']} (probes_per_seed {cap['probes_per_seed']})")

    print(f"calibration wall: {time.monotonic() - started:.0f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
