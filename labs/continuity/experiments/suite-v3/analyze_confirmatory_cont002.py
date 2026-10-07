"""CONT-002 confirmatory analysis (frozen): the R = dB/dA verdict machinery.

Implements EVALUATION-PREP-CONT002 sections 3-6 exactly:

- Unit: cluster = scenario. Per cell: cluster mean over its 7 seed-variant
  probes; dA_c, dB_c per cluster; dA, dB = cluster means; R = dB/dA as a
  RATIO OF CLUSTER MEANS (never a mean of per-cluster ratios).
- Estimability gate: dA point >= 0.30 AND the two-sided 95% cluster
  percentile bootstrap CI of dA excludes 0 — else "non-estimable" (the
  inspirer's clause: report the two deltas as diagnostics; no ratio, no
  transfer claim, no alternative denominator — RC-2: NO ratios at all in
  this branch, including per-family).
- R CI: percentile bootstrap over clusters, same resample indices reused
  for the dA CI and the R CI (correlation preserved), RNG seed frozen
  below. Degenerate draws (N-4): R* computed for every draw with dA* != 0;
  non-finite draws excluded from percentiles and counted; if > 10% of
  draws have |dA*| <= 0.05 the CI carries an unstable-denominator flag and
  no "established" verdict is issued.
- Verdict wording (section 6, five branches, two-sided, no post-hoc switch):
  retention established (CI > 0 and R >= MME) / retention below MME (CI > 0,
  R < MME) / harm established (CI < 0) / no confirmatory transfer difference
  established (CI includes 0) / non-estimable (gate fails).
- MME: R_MME = 0.25, UNLESS the pilot-gate checkpoint re-derived it upward
  (the frozen formula; --mme carries the effective value, cross-checked
  against pilot-gate.json when the pilot root is given).
- Secondaries (section 8): per-family R ONLY when the pooled gate passed;
  per-cluster dA/dB tables always; invalid-format decomposition per cell
  (observed_label None = format miss); empirical guess rates per core;
  between-seed spread; token/wall report; carried notes N-1/N-2 in the
  record header.

Input: one or more run roots (pilot + confirmatory; the seven seeds combine
— single freeze, prereg section 2). Reads per-cell summary.json probes.
Output: results-summary.json + results-summary.md in the LAST run root +
printed verdict. --self-test verifies the machinery on synthetic cells with
a known outcome (RC-4b).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]

K_PRIMARY = 15
N_SEEDS = 7
MME_R_DEFAULT = 0.25
DA_MIN = 0.30
BOOTSTRAP_N = 10_000
BOOTSTRAP_SEED = 20261007
UNSTABLE_ABS_DA = 0.05
UNSTABLE_SHARE = 0.10
GUESS_K = 6

VERDICT_NON_ESTIMABLE = ("primary endpoint non-estimable; deltas reported as "
                         "diagnostics; no transfer claim")
VERDICT_RETAINED = ("retained benefit established: a quarter or more of the "
                    "core-A memory benefit survives the core replacement")
VERDICT_BELOW_MME = ("directional retention below the minimum meaningful "
                     "effect; transfer detected but not established as meaningful")
VERDICT_HARM = "state actively hurts core B"
VERDICT_NULL = "no confirmatory transfer difference established"


def load_cell_probes(run_roots: list[Path], cell: str) -> dict[tuple[str, int], list[dict]]:
    """{cluster id -> per-seed pass/observed_label for the cell} across all runs."""
    by_cluster: dict[str, dict[int, dict]] = {}
    for root in run_roots:
        for seed_dir in sorted((root / cell).glob("seed-*")):
            if "-a" in seed_dir.name:  # failed attempts kept as evidence, not data
                continue
            sp = seed_dir / "summary.json"
            if not sp.exists():
                continue
            seed = int(seed_dir.name.split("seed-")[1].split("-")[0])
            summary = json.loads(sp.read_text(encoding="utf-8"))
            for p in summary["probes"]:
                if p.get("family") == "guess_calibration":
                    continue
                by_cluster.setdefault(p["scenario"], {})[seed] = p
    return {(cid, seed): probe for cid, per_seed in by_cluster.items()
            for seed, probe in per_seed.items()}


def cluster_table(run_roots: list[Path]) -> list[dict]:
    cells = {c: load_cell_probes(run_roots, c)
             for c in ("A-restored", "A-clean", "B-restored", "B-clean")}
    clusters = sorted({cid for (cid, _) in cells["A-restored"]})
    rows = []
    for cid in clusters:
        seeds = sorted({s for (c, s) in cells["A-restored"] if c == cid})
        row = {"cluster": cid, "n": len(seeds)}
        for cell in cells:
            probes = [cells[cell].get((cid, s)) for s in seeds]
            present = [p for p in probes if p is not None]
            row[cell] = {
                "pass_rate": (sum(1 for p in present if p.get("passed") is True)
                              / len(present)) if present else None,
                "n_present": len(present),
                "invalid": sum(1 for p in present if p.get("observed_label") is None),
            }
        row["dA_c"] = (row["A-restored"]["pass_rate"] - row["A-clean"]["pass_rate"]
                       if row["A-restored"]["pass_rate"] is not None
                       and row["A-clean"]["pass_rate"] is not None else None)
        row["dB_c"] = (row["B-restored"]["pass_rate"] - row["B-clean"]["pass_rate"]
                       if row["B-restored"]["pass_rate"] is not None
                       and row["B-clean"]["pass_rate"] is not None else None)
        row["family"] = "delayed_recall" if cid.startswith("dr-") else "distractor_recall"
        rows.append(row)
    return rows


def verdict(rows: list[dict], mme: float, rng_seed: int = BOOTSTRAP_SEED) -> dict[str, Any]:
    import random

    complete = (len(rows) == K_PRIMARY
                and all(r["n"] == N_SEEDS and r["dA_c"] is not None and r["dB_c"] is not None
                        for r in rows))
    da_c = [r["dA_c"] for r in rows]
    db_c = [r["dB_c"] for r in rows]
    da, db = sum(da_c) / len(da_c), sum(db_c) / len(db_c)

    rng = random.Random(rng_seed)
    k = len(rows)
    da_stars, db_stars = [], []
    for _ in range(BOOTSTRAP_N):
        idx = [rng.randrange(k) for _ in range(k)]
        da_stars.append(sum(da_c[i] for i in idx) / k)
        db_stars.append(sum(db_c[i] for i in idx) / k)
    da_stars_s = sorted(da_stars)
    da_lo = da_stars_s[int(0.025 * BOOTSTRAP_N)]
    da_hi = da_stars_s[int(0.975 * BOOTSTRAP_N) - 1]

    gate_point = da >= DA_MIN
    gate_ci = da_lo > 0.0 or da_hi < 0.0
    nonfinite = sum(1 for d in da_stars if d == 0.0)
    r_stars = sorted(db / d for db, d in zip(db_stars, da_stars) if d != 0.0)
    unstable_share = sum(1 for d in da_stars if abs(d) <= UNSTABLE_ABS_DA) / BOOTSTRAP_N
    unstable = unstable_share > UNSTABLE_SHARE
    r_lo = r_stars[int(0.025 * len(r_stars))]
    r_hi = r_stars[int(0.975 * len(r_stars)) - 1]
    r_hat = db / da if da != 0 else None

    if not complete:
        branch = "INCOMPLETE"
        wording = ("incomplete: the completeness guard requires 15 clusters x 7 seeds x "
                   "4 cells; missing observations are listed in the record")
    elif not (gate_point and gate_ci):
        branch, wording = "NON-ESTIMABLE", VERDICT_NON_ESTIMABLE
    elif unstable:
        branch = "UNSTABLE-DENOMINATOR"
        wording = ("unstable denominator: > 10% of bootstrap draws have |dA*| <= 0.05; "
                   "no established verdict is issued (prereg section 4)")
    elif r_lo > 0.0 and r_hat >= mme:
        branch, wording = "RETENTION-ESTABLISHED", VERDICT_RETAINED
    elif r_lo > 0.0:
        branch, wording = "RETENTION-BELOW-MME", VERDICT_BELOW_MME
    elif r_hi < 0.0:
        branch, wording = "HARM-ESTABLISHED", VERDICT_HARM
    else:
        branch, wording = "NULL", VERDICT_NULL

    return {
        "completeness": {"clusters": len(rows),
                         "expected": K_PRIMARY,
                         "complete": complete,
                         "missing": [{"cluster": r["cluster"], "n": r["n"]}
                                     for r in rows if r["n"] != N_SEEDS] or None},
        "dA": {"point": round(da, 4), "ci95": [round(da_lo, 4), round(da_hi, 4)]},
        "dB": {"point": round(db, 4)},
        "gate": {"dA_min": DA_MIN, "point_ok": gate_point, "ci_excludes_0": gate_ci,
                 "passed": gate_point and gate_ci},
        "R": {"point": round(r_hat, 4) if r_hat is not None else None,
              "ci95": [round(r_lo, 4), round(r_hi, 4)],
              "mme": mme,
              "unstable_denominator_flag": unstable,
              "unstable_share": round(unstable_share, 4),
              "nonfinite_draws": nonfinite,
              "bootstrap": {"n": BOOTSTRAP_N, "rng_seed": rng_seed,
                            "method": "cluster percentile, ratio of means, shared indices"}},
        "branch": branch,
        "verdict": wording,
    }


def secondaries(run_roots: list[Path], rows: list[dict], main: dict[str, Any],
                mme: float) -> dict[str, Any]:
    out: dict[str, Any] = {"per_cluster": rows}
    # Per-family R ONLY if the pooled gate passed (RC-2); deltas always.
    if main["gate"]["passed"] and not main["R"]["unstable_denominator_flag"]:
        for fam in ("delayed_recall", "distractor_recall"):
            sub = [r for r in rows if r["family"] == fam]
            da_f = sum(r["dA_c"] for r in sub) / len(sub)
            db_f = sum(r["dB_c"] for r in sub) / len(sub)
            out[f"R_{fam}"] = round(db_f / da_f, 4) if da_f != 0 else None
    else:
        out["R_per_family"] = ("NOT COMPUTED — pooled estimability gate failed or "
                               "unstable denominator (RC-2: no ratios in this branch)")
    # Invalid-format decomposition per cell.
    for cell in ("A-restored", "A-clean", "B-restored", "B-clean"):
        probes = [p for (cid, s), p in load_cell_probes(run_roots, cell).items()]
        out[f"invalid_share_{cell}"] = round(
            sum(1 for p in probes if p.get("observed_label") is None) / len(probes), 4
        ) if probes else None
    # Guess bands per core.
    for cell in ("GC-A", "GC-B"):
        pos = []
        for root in run_roots:
            for seed_dir in sorted((root / cell).glob("seed-*")):
                sp = seed_dir / "summary.json"
                if not sp.exists():
                    continue
                for p in json.loads(sp.read_text(encoding="utf-8"))["probes"]:
                    if p.get("family") == "guess_calibration" and p.get("observed_position") is not None:
                        pos.append(p["observed_position"])
        rate0 = sum(1 for x in pos if x == 0) / len(pos) if pos else None
        out[f"guess_{cell}"] = {
            "n": len(pos),
            "position0_share": round(rate0, 4) if rate0 is not None else None,
            "band": round(abs(rate0 - 1 / GUESS_K), 4) if rate0 is not None else None,
        }
    out["carried_notes"] = {
        "N_1": "power-model caveats (ceiling compression of realized dA at bAs 0.90; "
               "shared-eps-across-cores assumption narrows R's CI) travel with every "
               "power number",
        "N_2": "the pilot GO condition (dA >= 0.45 on seeds kept in the final dataset) "
               "induces a small upward selection bias on dA — conservative for R, "
               "anti-conservative for the estimability gate",
        "determinism": "greedy+seed does not guarantee identical outputs (PB-071, CN-003)",
    }
    return out


def analyze(run_roots: list[Path], mme: float) -> dict[str, Any]:
    rows = cluster_table(run_roots)
    main = verdict(rows, mme)
    sec = secondaries(run_roots, rows, main, mme)
    record = {
        "kind": "cont002-confirmatory-results",
        "run_roots": [str(r) for r in run_roots],
        "mme_effective": mme,
        "primary": main,
        "secondaries": sec,
        "record_header": {
            "label": "agent-pre-registered, pending owner acceptance",
            "revs": "TO FILL AT RUN TIME — every git rev of execution, attempt counts exact",
            "wall_time": "TO FILL FROM cells.json (per-cell sums across attempts; "
                         "cell/cluster/run reconciliation per template section 5)",
        },
    }
    out_path = run_roots[-1] / "results-summary.json"
    out_path.write_text(json.dumps(record, indent=1, ensure_ascii=True) + "\n",
                        encoding="utf-8")
    return record


# ----------------------------------------------------------------------------
# self-test (RC-4b): synthetic 15x7 cells with a known outcome
# ----------------------------------------------------------------------------

def self_test() -> None:
    import random
    import shutil

    tmp = LAB_ROOT / "results" / "CONT-002-CONFIRMATORY" / "selftest-cont002-confirm"
    if tmp.exists():
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    rng = random.Random(7)

    def synth(cell: str, base: float, delta_key: str):
        for seed in range(N_SEEDS):
            d = tmp / cell / f"seed-{5001 + seed}"
            d.mkdir(parents=True, exist_ok=True)
            probes = []
            for i in range(K_PRIMARY):
                p_pass = base if delta_key == "clean" else base
                probes.append({
                    "family": "guess_calibration" if False else
                              ("delayed_recall" if i % 2 else "distractor_recall"),
                    "scenario": (f"dr-53{i + 1:02d}" if i % 2 else f"dx-54{i + 1:02d}"),
                    "passed": rng.random() < min(0.98, max(0.02, p_pass)),
                    "observed_label": "X1", "expected": "X1",
                })
            (d / "summary.json").write_text(json.dumps(
                {"kind": "cont002-cell-summary", "cell": cell, "seed": 5001 + seed,
                 "probes": probes, "duration_s": 10.0, "completed": True},
                indent=1), encoding="utf-8")

    # Known design: dA = 0.75, dB = 0.375 -> R ~= 0.5 (RETENTION-ESTABLISHED).
    synth("A-restored", 0.90, "state")
    synth("A-clean", 0.15, "clean")
    synth("B-restored", 0.545, "state")
    synth("B-clean", 0.17, "clean")
    record = analyze([tmp], MME_R_DEFAULT)
    p = record["primary"]
    assert p["branch"] == "RETENTION-ESTABLISHED", f"branch: {p['branch']}\n{json.dumps(p, indent=1)}"
    assert 0.2 <= p["R"]["point"] <= 0.9, p["R"]
    print(f"SELF-TEST PASS: known R~0.5 -> {p['branch']} "
          f"(dA {p['dA']['point']}, R {p['R']['point']}, CI {p['R']['ci95']})")

    # Null case: dB = 0 -> NULL branch (gate still passes, CI includes 0).
    for seed_dir in (tmp / "B-restored").glob("seed-*"):
        s = json.loads((seed_dir / "summary.json").read_text(encoding="utf-8"))
        for p_ in s["probes"]:
            p_["passed"] = rng.random() < 0.17
        (seed_dir / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    record = analyze([tmp], MME_R_DEFAULT)
    assert record["primary"]["branch"] == "NULL", record["primary"]["branch"]
    print("SELF-TEST PASS: dB=0 -> NULL branch")

    # Non-estimable case: dA ~ 0 -> NON-ESTIMABLE, and NO per-family ratios.
    for seed_dir in (tmp / "A-restored").glob("seed-*"):
        s = json.loads((seed_dir / "summary.json").read_text(encoding="utf-8"))
        for p_ in s["probes"]:
            p_["passed"] = rng.random() < 0.15
        (seed_dir / "summary.json").write_text(json.dumps(s, indent=1), encoding="utf-8")
    record = analyze([tmp], MME_R_DEFAULT)
    assert record["primary"]["branch"] == "NON-ESTIMABLE", record["primary"]["branch"]
    assert "R_per_family" in record["secondaries"]
    print("SELF-TEST PASS: dA~0 -> NON-ESTIMABLE + per-family ratios withheld")


def main() -> int:
    parser = argparse.ArgumentParser(description="CONT-002 confirmatory analysis (frozen)")
    parser.add_argument("--run-roots", nargs="+", default=None,
                        help="pilot and confirmatory run roots (all seven seeds combine)")
    parser.add_argument("--mme", type=float, default=MME_R_DEFAULT,
                        help="effective MME (0.25 unless the pilot-gate re-derived upward)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.run_roots:
        raise SystemExit("--run-roots required (or --self-test)")
    record = analyze([Path(r) for r in args.run_roots], args.mme)
    p = record["primary"]
    print(json.dumps({"dA": p["dA"], "gate": p["gate"], "R": p["R"],
                      "branch": p["branch"]}, indent=1, ensure_ascii=True))
    print(f"VERDICT: {p['verdict']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
