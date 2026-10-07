"""CONT-002 pilot analysis (frozen): GO/NO-GO + pilot-gate checkpoint outputs.

Implements EVALUATION-PREP-CONT002 section 2 (all four predeclared pilot
criteria) and section 5's pilot-gate checkpoint outputs (the RC-1 fold: every
pilot-dependent adjustment executes HERE — after the frozen pilot analysis,
before any confirmatory inference, owner-visible — never "at freeze").

Input: the pilot run root (results/CONT-002-PILOT/cont002-pilot-<ts>/) —
reads cells.json (derived; audit path = per-cell summaries + traces).

Criterion 1 (B label-form compliance, RC-5 definition): invalid-format share
= probes whose observed_label is None (zero or >1 distinct standalone label
under extract_label) over the 15 clusters x 2 pilot seeds = 30 probes per B
cell. GO iff < 0.30 on BOTH B cells.
Criterion 2 (wall-time): extrapolated 7-seed total vs the 5.5 h cap; the
declared trim (GC-B to seeds {5001..5004}) and its saving are computed; the
pathological worst case is stated plainly (N-3): if the extrapolation
exceeds the cap even after the trim, NO-GO.
Criterion 3 (ΔA ladder): pilot ΔA point over the 30 paired primary probes;
>= 0.45 GO; < 0.30 non-estimable-risk declaration; MME re-derivation fires
iff ΔA < 0.60 with the frozen upward-only formula
R_MME' = max(0.25, max(0.15, 2*band_max)/ΔA_measured) where band_max is the
larger core's |guess_rate - 1/6| from that core's GC probes.
Criterion 4 (spread): per-cell between-seed sd reported (n=2 gates nothing);
any cell sd > 0.25 -> stress governance flag (owner sign-off line, cycle-2
clause-2 pattern).

Output: pilot-gate.json in the run root + printed verdict GO / NO-GO with
the owner-action lines. --self-test runs on synthetic cells with known
answers (RC-4b dry-run; the v2-hotfix lesson).
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]

MME_R = 0.25
DA_PILOT_GO = 0.45
DA_NONESTIM_RISK = 0.30
DA_REDERIVE_TRIGGER = 0.60
SD_STRESS = 0.25
GPU_CAP_S = 330 * 60
WALL_GUARD_S = 300 * 60
K_PRIMARY = 15
GUESS_K = 6
TRIM_GC_B_SAVING_SEEDS = 3  # GC-B trimmed to 4 seeds -> 3 seeds dropped


def load_probes(run_root: Path, cell: str) -> list[dict]:
    cells = json.loads((run_root / "cells.json").read_text(encoding="utf-8"))
    seeds = sorted(
        int(key.split("seed-")[1].split("-")[0])
        for key in cells["cells"]
        if key.startswith(f"{cell}/seed-") and cells["cells"][key].get("completed") is not False
    )
    probes: list[dict] = []
    for seed in seeds:
        summary_path = run_root / cell / f"seed-{seed}" / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        probes.extend(p for p in summary["probes"] if p.get("family") != "guess_calibration")
    return probes


def load_gc(run_root: Path, cell: str) -> list[dict]:
    probes: list[dict] = []
    for seed_dir in sorted((run_root / cell).glob("seed-*")):
        summary_path = seed_dir / "summary.json"
        if not summary_path.exists():
            continue
        summary = json.loads(summary_path.read_text(encoding="utf-8"))
        probes.extend(p for p in summary["probes"] if p.get("family") == "guess_calibration")
    return probes


def invalid_share(probes: list[dict]) -> float:
    if not probes:
        return 1.0
    return sum(1 for p in probes if p.get("observed_label") is None) / len(probes)


def pass_rate(probes: list[dict]) -> float:
    return sum(1 for p in probes if p.get("passed") is True) / len(probes) if probes else 0.0


def guess_band(gc_probes: list[dict]) -> tuple[float, int]:
    """|guess_rate - 1/k| over the word-probe subset (positions from labels)."""
    word = [p for p in gc_probes if p.get("observed_position") is not None]
    if not word:
        return 1.0, 0
    rate = sum(1 for p in word if p["observed_position"] == 0) / len(word)
    return abs(rate - 1.0 / GUESS_K), len(word)


def sd(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    mean = sum(values) / len(values)
    return math.sqrt(sum((v - mean) ** 2 for v in values) / (len(values) - 1))


def analyze(run_root: Path) -> dict[str, Any]:
    b_restored = load_probes(run_root, "B-restored")
    b_clean = load_probes(run_root, "B-clean")
    a_restored = load_probes(run_root, "A-restored")
    a_clean = load_probes(run_root, "A-clean")
    gc_a, gc_b = load_gc(run_root, "GC-A"), load_gc(run_root, "GC-B")

    completeness = {
        "primary_probes_per_cell": K_PRIMARY * 2,
        "observed": {c: len(ps) for c, ps in
                     (("A-restored", a_restored), ("A-clean", a_clean),
                      ("B-restored", b_restored), ("B-clean", b_clean))},
    }
    complete = all(len(ps) == K_PRIMARY * 2 for ps in (a_restored, a_clean, b_restored, b_clean))

    # Criterion 1: B compliance (RC-5 definition).
    inv_b_restored, inv_b_clean = invalid_share(b_restored), invalid_share(b_clean)
    crit1 = complete and inv_b_restored < 0.30 and inv_b_clean < 0.30

    # Criterion 2: wall-time.
    cells = json.loads((run_root / "cells.json").read_text(encoding="utf-8"))
    per_cell_wall = {}
    for key, rec in cells["cells"].items():
        cell, seed = key.split("/seed-")[0], key.split("seed-")[1]
        per_cell_wall.setdefault(cell, []).append(rec.get("wall_s", 0.0))
    pilot_wall = sum(sum(v) for v in per_cell_wall.values())
    mean_gc_b = (sum(per_cell_wall.get("GC-B", [0.0])) / 2) if per_cell_wall.get("GC-B") else 0.0
    extrapolated = pilot_wall / 2 * 7  # linear over seeds (7-seed total)
    trim_saving = mean_gc_b * TRIM_GC_B_SAVING_SEEDS
    crit2 = extrapolated <= GPU_CAP_S or (extrapolated - trim_saving) <= GPU_CAP_S
    trim_applies = GPU_CAP_S < extrapolated <= GPU_CAP_S + trim_saving

    # Criterion 3: ΔA ladder + MME re-derivation (pilot-gate checkpoint).
    da = pass_rate(a_restored) - pass_rate(a_clean)
    band_a, n_a = guess_band(gc_a)
    band_b, n_b = guess_band(gc_b)
    band_max = max(band_a, band_b)
    mme_derived = MME_R
    rederivation = None
    if da < DA_REDERIVE_TRIGGER:
        mme_derived = max(MME_R, max(0.15, 2 * band_max) / da if da > 0 else float("inf"))
        rederivation = {
            "formula": "R_MME' = max(0.25, max(0.15, 2*band_max)/dA_measured)",
            "band_max": round(band_max, 4),
            "dA_measured": round(da, 4),
            "R_MME_before": MME_R,
            "R_MME_after": round(mme_derived, 4),
            "upward_only_ok": mme_derived >= MME_R,
        }
    crit3 = da >= DA_PILOT_GO

    # Criterion 4: spread (reported; flag only).
    per_seed = {}
    for cell in ("A-restored", "A-clean", "B-restored", "B-clean"):
        for seed_dir in sorted((run_root / cell).glob("seed-*")):
            sp = seed_dir / "summary.json"
            if not sp.exists():
                continue
            s = json.loads(sp.read_text(encoding="utf-8"))
            per_seed.setdefault(cell, {}).setdefault(seed_dir.name, pass_rate(s["probes"]))
    spread = {c: {"per_seed": v, "sd": round(sd(list(v.values())), 4)}
              for c, v in per_seed.items()}
    stress_flag = any(v["sd"] > SD_STRESS for v in spread.values())

    verdict = "GO" if (crit1 and crit2 and crit3 and complete) else "NO-GO"
    out = {
        "kind": "cont002-pilot-gate",
        "run_root": str(run_root),
        "completeness": completeness,
        "criterion1_b_compliance": {
            "invalid_share_B_restored": round(inv_b_restored, 4),
            "invalid_share_B_clean": round(inv_b_clean, 4),
            "threshold": 0.30,
            "definition": "observed_label is None (zero or >1 distinct standalone label)",
            "pass": crit1,
        },
        "criterion2_walltime": {
            "pilot_wall_s": round(pilot_wall, 1),
            "extrapolated_7seed_s": round(extrapolated, 1),
            "gpu_cap_s": GPU_CAP_S,
            "gc_b_trim_saving_s": round(trim_saving, 1),
            "trim_applies": trim_applies,
            "worst_case_note": "if the extrapolation exceeds the cap even after the trim, "
                               "NO-GO (N-3: the backstop is NO-GO, the trim covers only a "
                               "moderate overrun)",
            "pass": crit2,
        },
        "criterion3_dA_ladder": {
            "dA_pilot": round(da, 4),
            "ladder": {"estimability_gate_floor": DA_NONESTIM_RISK,
                       "pilot_go_floor": DA_PILOT_GO,
                       "rederivation_trigger": DA_REDERIVE_TRIGGER},
            "nonestim_risk_declared": da < DA_NONESTIM_RISK,
            "mme_rederivation": rederivation,
            "R_MME_effective": round(mme_derived, 4),
            "pass": crit3,
        },
        "criterion4_spread": {
            "per_cell": spread,
            "stress_flag_sd_gt_0_25": stress_flag,
            "owner_signoff_required_if_stress": stress_flag,
            "note": "n=2 gates nothing; reported for the pilot-gate checkpoint",
        },
        "guess_bands": {"GC-A": {"band": round(band_a, 4), "n_word_probes": n_a},
                        "GC-B": {"band": round(band_b, 4), "n_word_probes": n_b}},
        "verdict": verdict,
        "owner_actions": [
            "review this pilot-gate.json",
            *(["MME re-derived upward — acknowledge the new MME before the confirmatory"]
              if rederivation else []),
            *(["stress flag fired (sd > 0.25) — sign off the stress-row governance before "
               "the confirmatory"] if stress_flag else []),
        ],
        "carried_notes": {
            "N_1": "power-model caveats (ceiling compression; shared-eps-across-cores) "
                   "travel with every power number",
            "N_2": "pilot GO condition induces a small upward selection bias on dA",
        },
    }
    (run_root / "pilot-gate.json").write_text(
        json.dumps(out, indent=1, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return out


# ----------------------------------------------------------------------------
# self-test (RC-4b): synthetic pilot with known answers
# ----------------------------------------------------------------------------

def self_test() -> None:
    tmp = Path(LAB_ROOT / "results" / "CONT-002-PILOT" / "selftest-cont002-pilot")
    if tmp.exists():
        import shutil
        shutil.rmtree(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    (tmp / "cells.json").write_text(json.dumps(
        {"kind": "cont002-cells", "cells": {}}, indent=1), encoding="utf-8")

    def synth_cell(cell: str, seeds: dict[int, float], gc: bool = False, invalid: float = 0.0):
        for seed, rate in seeds.items():
            d = tmp / cell / f"seed-{seed}"
            d.mkdir(parents=True, exist_ok=True)
            probes = []
            n = 4 if gc else K_PRIMARY
            for i in range(n):
                if gc:
                    probes.append({"family": "guess_calibration", "passed": None,
                                   "observed_position": 0 if i % 6 == 0 else (i % 6)})
                else:
                    probes.append({
                        "family": "delayed_recall" if i % 2 else "distractor_recall",
                        "passed": (i / n) < rate,
                        "observed_label": None if (i / n) < invalid else "A12",
                        "expected": "A12",
                    })
            (d / "summary.json").write_text(json.dumps({
                "kind": "cont002-cell-summary", "cell": cell, "seed": seed,
                "probes": probes, "duration_s": 60.0, "completed": True,
            }, indent=1), encoding="utf-8")
            cells = json.loads((tmp / "cells.json").read_text(encoding="utf-8"))
            cells["cells"][f"{cell}/seed-{seed}"] = {"wall_s": 60.0, "attempts": 1,
                                                     "completed": True}
            (tmp / "cells.json").write_text(json.dumps(cells, indent=1), encoding="utf-8")

    # GO case: dA = 0.8 - 0.2 = 0.6 >= 0.45; B invalid 10% < 30%; wall tiny;
    # guess band position-0 share 1/6 -> band 0.
    synth_cell("learn-A", {5001: 0, 5002: 0})
    synth_cell("A-restored", {5001: 0.8, 5002: 0.8})
    synth_cell("A-clean", {5001: 0.2, 5002: 0.2})
    synth_cell("B-restored", {5001: 0.5, 5002: 0.5}, invalid=0.1)
    synth_cell("B-clean", {5001: 0.2, 5002: 0.2}, invalid=0.1)
    synth_cell("GC-A", {5001: 0, 5002: 0}, gc=True)
    synth_cell("GC-B", {5001: 0, 5002: 0}, gc=True)
    out = analyze(tmp)
    assert out["verdict"] == "GO", f"self-test GO case failed: {out['verdict']}"
    assert abs(out["criterion3_dA_ladder"]["dA_pilot"] - 0.6) < 1e-9
    assert out["criterion3_dA_ladder"]["mme_rederivation"] is None  # 0.6 not < 0.6
    print("SELF-TEST PASS: GO case (dA 0.6, B invalid 0.1, no re-derivation)")

    # NO-GO + re-derivation case: rates quantize to 8/15 and 3/15 ->
    # dA = 5/15 = 0.3333 -> < 0.45 fails crit3; < 0.60 fires re-derivation.
    # GC positions [0,1,2,3]x2 -> rate0 = 0.25, band = |0.25 - 1/6| = 1/12 ->
    # 2*band = 1/6 -> R' = max(0.25, (1/6)/(1/3)) = 0.5 (UPWARD from 0.25).
    synth_cell("A-restored", {5001: 0.5, 5002: 0.5})
    out = analyze(tmp)
    assert out["verdict"] == "NO-GO"
    red = out["criterion3_dA_ladder"]["mme_rederivation"]
    assert red is not None and abs(red["dA_measured"] - 1 / 3) < 1e-4
    assert abs(red["R_MME_after"] - 0.5) < 1e-9
    print("SELF-TEST PASS: NO-GO case (dA 1/3 -> crit3 fail + upward re-derivation to 0.5)")


def main() -> int:
    parser = argparse.ArgumentParser(description="CONT-002 pilot analysis (frozen)")
    parser.add_argument("--run-root", default=None, help="pilot run root to analyze")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0
    if not args.run_root:
        raise SystemExit("--run-root required (or --self-test)")
    out = analyze(Path(args.run_root))
    print(json.dumps({k: out[k] for k in ("verdict", "criterion1_b_compliance",
                                          "criterion2_walltime", "criterion3_dA_ladder")},
                     indent=1, ensure_ascii=True))
    print(f"verdict: {out['verdict']} — pilot-gate.json written to {args.run_root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
