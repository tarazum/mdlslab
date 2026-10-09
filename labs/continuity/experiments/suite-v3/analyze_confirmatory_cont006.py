"""Frozen CONT-006 V2 confirmatory analysis (EVALUATION-PREP-CONT006 §3–§4
as kept by EVALUATION-PREP-CONT006-V2 A.7; v3m surface per A.1).

V2 port written BEFORE any V2 inference (template §1; freeze manifest
frozen-config-cont006-v2.json digests this file). Reads the Phase P (pilot)
+ Phase C (confirmatory) run roots — the pilot seeds {7001,7002} are part
of the final dataset (single freeze; the R0/R2 pilot cells reuse the
calibration arm-seeds) — and computes:

PRIMARY: Δ = S(R2) − S(R0) over the 15 TR clusters x 7 seeds (cluster mean
per arm; Δ_c per cluster; Δ = cluster mean). Two-sided 95% cluster
percentile bootstrap, EXACTLY 10,000 draws, RNG seed 20261008 (frozen), the
same resample indices reused for every CI computed in this record.

Decision rule (frozen wording, §4): CI excludes 0 upward AND Δ >= MME ->
"lesson transfer established"; CI > 0 and Δ < MME -> "directional
improvement below the minimum meaningful effect"; CI excludes 0 downward ->
"lessons actively hurt"; else "no confirmatory difference established".
MME = 0.20 ABSOLUTE (A.5): the empirical guessing band is reported next to
family numbers and NEVER moves the MME (caveat-only; no re-derivation
formula — the V1 band-rule supersession is repealed).

Completeness guard: 15 x 7 x 4 primary cell-probes present, else INCOMPLETE
(no substitution). Secondaries (never promotable): R3−R0, R1−R0 with CIs;
invalid-format decomposition per arm; per-taxonomy-class Δ table (carries
the FP-3a/FP-2 co-signature note N-3); guess band + position per arm;
carried notes CN-A/B/C in the run-record header alongside revs + wall
reconciliation (template §5/§8). The run-record header MUST also carry the
CN-012 invalidation note, the accidental-ablation label of the V1 chain,
the PW-OVERRIDE history and the V2 amendment list A.1–A.7 (CARRIED below).

--self-test: synthetic matrices for the established / null / harm /
incomplete branches — no GPU, no real run roots.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

LAB_ROOT = Path(__file__).resolve().parents[2]

TR_IDS = ["cr-7001", "cr-7002", "cr-7003", "cr-7004", "cu-7101", "cu-7102",
          "cu-7103", "cu-7104", "rt-7201", "rt-7202", "rt-7203", "dx-7401",
          "dx-7402", "dr-7301", "dr-7302"]
# v3m sub_types (verified from fixtures/v3m): cr-7001 valid_correction_
# environment + cr-7002 valid_correction_tool -> FP-3a; cr-7003 erroneous_
# user_correction + cr-7004 source_conflict -> FP-3b
CLASS_OF = {"cr-7001": "FP-3a", "cr-7002": "FP-3a", "cr-7003": "FP-3b",
            "cr-7004": "FP-3b", "cu-7101": "FP-1", "cu-7102": "FP-1",
            "cu-7103": "FP-1", "cu-7104": "FP-1", "rt-7201": "FP-2",
            "rt-7202": "FP-2", "rt-7203": "FP-2", "dx-7401": "FP-4",
            "dx-7402": "FP-4", "dr-7301": "FP-5", "dr-7302": "FP-5"}
ARMS = ["R0", "R1", "R2", "R3"]
SEEDS = [7001, 7002, 7003, 7004, 7005, 7006, 7007]
BOOT = 10_000
RNG_SEED = 20261008
MME_D = 0.20
DETERMINISM_CAVEAT = ("greedy+seed does not guarantee identical outputs "
                      "(PB-071, CN-003); per-seed content variants make seeds "
                      "true replicates regardless")
CARRIED = {
    "CN-012-INVALIDATION": "the V1 chain (v3l, frozen-config-cont006.json) "
                           "ran every R-arm MEMORYLESS — the runner's append "
                           "tuple omitted the R-arms (CN-012); its verdict "
                           "'no confirmatory difference' (Δ = 0.019) is "
                           "INVALID as a test of the registered arms and is "
                           "preserved as an unregistered exploratory "
                           "datapoint (an accidental lessons-WITHOUT-memory "
                           "ablation ≈ prereg critical test 1)",
    "V2-AMENDMENTS": "A.1 suite v3m (fresh worlds; V3+V18 disjointness); "
                     "A.2 memory discipline (MEMORY_ARMS single source + "
                     "live-telemetry gate before every analyzer); A.3 "
                     "calibration pilot (family bands + anchor 0.525±0.15); "
                     "A.4 worker v2 multi-trace bundles + FP-6 store cap + "
                     "class schema; A.5 MME 0.20 absolute, band caveat-only; "
                     "A.6 chain/gates order; A.7 arms/endpoint/decision-rule "
                     "unchanged (R1 stays; parroting-replication R1<=R0 "
                     "finally testable with memory alive)",
    "V2-STORES": "R2 store = the W2 worker-v2 pass output (multi-trace "
                 "bundles, FP-6 cap, class-coverage telemetry); R3 store = "
                 "the blind-authored gold recap with declared classes + the "
                 "same FP-6 cap (LL-G-008 dropped, 8->7; recap artifact "
                 "r3-store-v2.json); both activated per the +0.05 "
                 "store-level rule at Phase V",
    "CN-A": "power-model caveats: paired-eps assumption narrows Δ's CI; b0 "
            "anchored to C2 T-arms (corrected 0.525, PR-REVIEW-CONT006 RC-1) — "
            "if R0 behaves differently the realized power shifts; the "
            "pilot-gate re-check governs",
    "CN-B": "pilot GO criteria 1–2 condition the LAUNCH, not the estimate — "
            "no endpoint-value condition selects the dataset; the headroom "
            "criterion reads R0 only",
    "CN-C": "pilot criterion 1(ii) runs on ~14 probes (binomial sd ~0.12); a "
            "violation routes to the owner gate, never an automatic stop",
    "N-3": "FP-3a clusters (cr-7001/7002) seed the agent's own wrong first "
           "answer by construction — per-class Δ partially co-measures FP-2 "
           "susceptibility; class attribution reads weaker than it looks",
    "PW-6": "worker sampling config frozen since FREEZE is num_ctx 8192 / "
            "num_predict 768 (reflection_v2.WORKER_OPTIONS) while prereg §1 "
            "quotes the WORKING-CORE config 4096/256 — different roles, "
            "declared per GATE-CONT006-POSTW condition 10 (low materiality)",
    "PW-OVERRIDE": "OWNER OVERRIDE 2026-10-09 (V1 chain history): the V1 "
                   "pilot NO-GO (criterion 1(i) BAD-lesson parroting — an "
                   "agent quoted the injected bad lesson verbatim and acted "
                   "on it; criterion 2 0.071 < 0.10) was explicitly "
                   "OVERRIDDEN by the owner ('(b) Дозволити фінальний забіг "
                   "попри NO-GO', ROADMAP Owner decisions 2026-10-09). That "
                   "V1 confirmatory is the invalidated memoryless run; the "
                   "harm-containment finding rides THIS run record as a "
                   "headline secondary, and the primary R2-R0 endpoint is "
                   "unaffected (counterfactual arms never enter it)",
}


def load_arm_seeds(root: Path) -> dict[str, dict[int, list[dict]]]:
    out: dict[str, dict[int, list[dict]]] = {}
    if not root.exists():
        return out
    for arm_dir in sorted(root.iterdir()):
        if not arm_dir.is_dir():
            continue
        for seed_dir in sorted(arm_dir.iterdir()):
            # canonical cells only: ^seed-\d{4}$ — invalidated attempt dirs
            # are evidence, never data (c679547 telemetry-aggregation class;
            # same fix as the pilot analyzer's loader).
            if not seed_dir.is_dir() or not re.fullmatch(r"seed-\d{4}", seed_dir.name):
                continue
            summary = seed_dir / "summary.json"
            if summary.exists():
                data = json.loads(summary.read_text(encoding="utf-8"))
                out.setdefault(arm_dir.name, {})[int(seed_dir.name[5:])] = \
                    data.get("probes", [])
    return out


def arm_cluster_pass(data: dict[str, dict[int, list[dict]]], arm: str,
                     seeds: list[int]) -> dict[str, float | None]:
    """cluster -> pass rate over the arm's seed probes (None if absent)."""
    per: dict[str, list[int]] = {sid: [] for sid in TR_IDS}
    for sd in seeds:
        for p in data.get(arm, {}).get(sd, []):
            sid = p.get("scenario")
            if sid in per and p.get("kind") != "guess_calibration":
                per[sid].append(1 if p.get("passed") is True else 0)
    return {sid: (sum(v) / len(v) if v else None) for sid, v in per.items()}


def completeness(data: dict[str, dict[int, list[dict]]], seeds: list[int]) -> list[str]:
    """Prereg §10: ALL 15 x 7 x 4 primary CELL-probes present (every
    cluster-seed-arm cell needs its probe — a cluster covered by only some
    seeds is still incomplete; no substitution)."""
    missing = []
    for arm in ARMS:
        for sid in TR_IDS:
            for sd in seeds:
                cell = [p for p in data.get(arm, {}).get(sd, [])
                        if p.get("scenario") == sid
                        and p.get("kind") != "guess_calibration"]
                if not cell:
                    missing.append(f"{arm}/{sid}/seed-{sd}")
    return missing


def delta_ci(d_c: np.ndarray, idx: np.ndarray) -> dict:
    """Percentile bootstrap CI over cluster deltas. GATE-CONT006 D-1 fix: the
    resample index array is generated ONCE per run record and REUSED for
    every CI in that record (prereg section 4: "the same resample indices
    used for any secondary CI computed in the same run record")."""
    d = float(d_c.mean())
    stars = d_c[idx].mean(axis=1)
    lo, hi = (float(x) for x in np.percentile(stars, [2.5, 97.5]))
    return {"delta": round(d, 4), "ci_lo": round(lo, 4), "ci_hi": round(hi, 4),
            "ci_excludes_0_up": lo > 0.0, "ci_excludes_0_down": hi < 0.0}


def verdict_of(prim: dict, mme: float) -> str:
    if prim["ci_excludes_0_up"] and prim["delta"] >= mme:
        return (f"lesson transfer established (Δ = {prim['delta']}, 95% CI "
                f"[{prim['ci_lo']}, {prim['ci_hi']}]): evidence-validated worker "
                f"lessons improve held-out transfer by at least the minimum "
                f"meaningful effect")
    if prim["ci_excludes_0_up"]:
        return ("directional improvement below the minimum meaningful effect "
                f"(Δ = {prim['delta']}, 95% CI [{prim['ci_lo']}, {prim['ci_hi']}])")
    if prim["ci_excludes_0_down"]:
        return (f"lessons actively hurt transfer (Δ = {prim['delta']}, 95% CI "
                f"[{prim['ci_lo']}, {prim['ci_hi']}])")
    return "no confirmatory difference established"


def analyze(pilot_root: Path | None, conf_root: Path | None) -> dict:
    data: dict[str, dict[int, list[dict]]] = {}
    for root in (pilot_root, conf_root):
        if root is not None:
            for arm, seeds in load_arm_seeds(root).items():
                data.setdefault(arm, {}).update(seeds)
    rng = np.random.default_rng(RNG_SEED)
    missing = completeness(data, SEEDS)
    header = {
        "revs": "recorded from env.json files at run-record assembly",
        "wall_reconciliation": "per-arm totals = sum over arm-seed summaries "
                               "across BOTH roots (template §5)",
        "carried_notes": CARRIED,
        "determinism_caveat": DETERMINISM_CAVEAT,
    }
    if missing:
        return {"kind": "cont006-confirmatory", "verdict": "INCOMPLETE",
                "missing_cell_probes": missing, "header": header}
    r0 = arm_cluster_pass(data, "R0", SEEDS)
    r2 = arm_cluster_pass(data, "R2", SEEDS)
    r1 = arm_cluster_pass(data, "R1", SEEDS)
    r3 = arm_cluster_pass(data, "R3", SEEDS)
    d_primary = np.array([r2[s] - r0[s] for s in TR_IDS], dtype=float)
    d_r3 = np.array([r3[s] - r0[s] for s in TR_IDS], dtype=float)
    d_r1 = np.array([r1[s] - r0[s] for s in TR_IDS], dtype=float)
    idx = rng.integers(0, len(TR_IDS), size=(BOOT, len(TR_IDS)))  # ONE draw, shared
    # MME 0.20 ABSOLUTE (A.5): the empirical guessing band is reported in
    # secondaries.guess_band_and_position as a caveat and NEVER moves the
    # MME — the V1 band-rule upward re-derivation is repealed.
    mme = MME_D
    band_note = ("MME 0.20 absolute; band caveat-only (A.5) — see "
                 "secondaries.guess_band_and_position")
    prim = delta_ci(d_primary, idx)
    sec_r3 = delta_ci(d_r3, idx)
    sec_r1 = delta_ci(d_r1, idx)
    # invalid-format decomposition per arm (TR probes)
    fmt = {}
    for arm in ARMS:
        probes = [p for sd in SEEDS for p in data.get(arm, {}).get(sd, [])
                  if p.get("scenario") in TR_IDS]
        wrong = sum(1 for p in probes if p.get("passed") is False
                    and p.get("observed_label") is not None)
        miss = sum(1 for p in probes if p.get("observed_label") is None)
        fmt[arm] = {"probes": len(probes), "wrong_label": wrong, "format_miss": miss,
                    "format_miss_share": round(miss / len(probes), 4) if probes else None}
    # per-class Δ table (deltas only; co-signature note carried)
    per_class = {}
    for cls in sorted(set(CLASS_OF.values())):
        ids = [s for s in TR_IDS if CLASS_OF[s] == cls]
        per_class[cls] = {
            "clusters": ids,
            "delta_mean_r2_minus_r0": round(float(np.mean([r2[s] - r0[s] for s in ids])), 4),
            "delta_mean_r3_minus_r0": round(float(np.mean([r3[s] - r0[s] for s in ids])), 4),
        }
    # guess band + position per arm (GC probes)
    guess = {}
    for arm in ARMS:
        gc = [p for sd in SEEDS for p in data.get(arm, {}).get(sd, [])
              if p.get("kind") == "guess_calibration"]
        valid = [p for p in gc if p.get("observed_label") is not None]
        pos0 = (sum(1 for p in valid if p.get("observed_position") == 0) / len(valid)
                if valid else None)
        guess[arm] = {"n": len(gc), "valid_share": round(len(valid) / len(gc), 4) if gc else None,
                      "position0_share": round(pos0, 4) if pos0 is not None else None,
                      "band_dev": round(abs(pos0 - 1 / 6), 4) if pos0 is not None else None}
    return {
        "kind": "cont006-confirmatory",
        "primary": {"endpoint": "delta = S(R2) - S(R0), 15 TR clusters x 7 seeds",
                    "mme": mme, "band_note": band_note,
                    "bootstrap": {"draws": BOOT, "rng_seed": RNG_SEED,
                                  "method": "cluster percentile, same indices "
                                            "reused for every CI in this record"},
                    **prim},
        "verdict": verdict_of(prim, mme),
        "secondaries": {
            "note": "exploratory, never promotable (prereg §14)",
            "r3_minus_r0_channel_viability": sec_r3,
            "r1_minus_r0_parroting_replication": sec_r1,
            "invalid_format_decomposition": fmt,
            "per_taxonomy_class_delta": per_class,
            "guess_band_and_position": guess,
        },
        "header": header,
    }


# ----------------------------------------------------------------------------
# self-test (RC-4b): synthetic matrices with known branch outcomes
# ----------------------------------------------------------------------------

def _synthetic(delta_r2: float | None, delta_r3: float = 0.0) -> dict:
    rng = np.random.default_rng(7)
    data: dict[str, dict[int, list[dict]]] = {a: {} for a in ARMS}
    for arm in ARMS:
        for sd in SEEDS:
            probes = []
            for sid in TR_IDS:
                base = 0.5 + (0.1 if sid in TR_IDS[:7] else -0.05)
                extra = {"R2": delta_r2, "R3": delta_r3}.get(arm) or 0.0
                p_pass = min(0.95, max(0.05, base + extra + rng.normal(0, 0.1)))
                passed = rng.random() < p_pass
                probes.append({"kind": "exact_match", "scenario": sid,
                               "passed": bool(passed),
                               "observed_label": "x" if passed else None})
            data[arm][sd] = probes
    if delta_r2 is None:  # incompleteness: drop one cluster-seed-arm cell
        data["R2"][7004] = [p for p in data["R2"][7004] if p["scenario"] != "dr-7302"]
    return data


def _analyze_data(data: dict) -> dict:
    """The primary machinery over in-memory data (self-test path)."""
    rng = np.random.default_rng(RNG_SEED)
    missing = completeness(data, SEEDS)
    if missing:
        return {"verdict": "INCOMPLETE", "missing_cell_probes": missing[:3]}
    r0 = arm_cluster_pass(data, "R0", SEEDS)
    r2 = arm_cluster_pass(data, "R2", SEEDS)
    d = np.array([r2[s] - r0[s] for s in TR_IDS], dtype=float)
    idx = rng.integers(0, len(TR_IDS), size=(BOOT, len(TR_IDS)))
    prim = delta_ci(d, idx)
    return {"verdict": verdict_of(prim, MME_D), "primary": prim}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pilot-root", default=None)
    parser.add_argument("--conf-root", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        # three branch checks with known synthetic effects + incompleteness
        for name, eff, expect in (("established", 0.35, "established"),
                                  ("null", 0.0, "no confirmatory"),
                                  ("harm", -0.35, "hurt")):
            r = _analyze_data(_synthetic(eff))
            assert expect in r["verdict"], (name, r["verdict"])
            print(f"SELF-TEST PASS: {name} branch -> {r['verdict'][:60]}")
        r = _analyze_data(_synthetic(None))
        assert r["verdict"] == "INCOMPLETE", r
        print("SELF-TEST PASS: incomplete branch")
        return 0
    if not args.conf_root:
        raise SystemExit("--conf-root required (or --self-test)")
    report = analyze(Path(args.pilot_root) if args.pilot_root else None,
                     Path(args.conf_root))
    out = Path(args.conf_root) / "results-summary-cont006.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print(f"VERDICT: {report['verdict']}")
    if "primary" in report:
        p = report["primary"]
        print(f"  Δ = {p['delta']} 95% CI [{p['ci_lo']}, {p['ci_hi']}] (MME {p['mme']})")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
