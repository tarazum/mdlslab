"""Power calculation for the CONT-002 primary endpoint R = dB/dA.

Design (docs/CONT-002-DESIGN.md, docs/EVALUATION-PREP-CONT002.md): 2x2 over
{core A = granite-code:8b, core B = Qwen3.6-35B-A3B} x {restored state, clean}
on the v3k primary set (DR+DX recall clusters), 5 seed-variant observations
per cluster per cell, one held-out label-form probe per observation
(6 options; scoring SUITE-V3-DESIGN section 3).

Simulated data-generating model per cluster c, seed s (extends the
power_calc_v3 paired-variant model to FOUR cells):

    eps[c,s]  ~ N(0, sig_shared)   # cluster-seed content difficulty, SHARED
                                   # by all four cells (same rendered content)
                                   # -> cancels inside dA and dB, and
                                   # correlates dA with dB (stabilizes R)
    p(A+state)  = clip(bAs + eps + R_true*(0) ... )   # see below
    p(A+clean)  = clip(bAc + eps + eta)
    p(B+state)  = clip(bBc + eps + R_true*dA_latent + eta)
    p(B+clean)  = clip(bBc + eps + eta)
    eta ~ N(0, sig_int) per CELL  # cell-specific response; does NOT cancel -
                                  # the power killer (as in cycle 2)
    dA_latent = bAs - bAc         # eps cancels pre-clipping; R_true scales it

Bases: bAs = 0.90 (cycles 1-2 DR/DX pass with memory ~ 1.0), bAc = 0.15
(clean pass ~ guess band), bBc = 0.17 (guess-level B+clean; M2b B+clean
missed; sensitivity 0.30). dA_latent = 0.75 at defaults.

Analysis replicated EXACTLY as pre-registered: cluster means over seeds ->
dA_c, dB_c -> dA, dB = cluster means -> R = dB/dA; estimability gate
(dA point >= 0.30 AND two-sided 95% cluster percentile bootstrap CI of dA
excludes 0); R CI = percentile bootstrap over clusters, 10,000-equivalent
method (BOOT resamples, same indices reused for the dA CI and the R CI,
RNG seed recorded). Verdict branches as frozen in the prereg.

Reported per row: P(CI of R excludes 0) = detection power at that R_true;
P(full "retention established" branch = CI>0 AND point R >= MME 0.25);
P(harm branch = CI<0); P(non-estimable via the gate); median CI width;
share of degenerate bootstrap draws (dA* <= 0.05) exceeding 10%.
House precedent (cycle 2, EVALUATION-PREP-v3 section 5-6): the headline
"power at MME" is the CI-exclusion power; the established branch
additionally requires the point estimate >= MME, which bounds its rate near
0.50 AT exactly the MME by construction (reported separately, never hidden).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20261007)
REPS = 3000
BOOT = 4000
K = 15                 # v3k primary clusters (DR 7 + DX 8; amendment-c ceiling)
N_OBS = 7              # seed-variant observations per cluster (seeds 5001..5007)
MME_R = 0.25           # pre-registered MME on R
DA_MIN = 0.30          # pre-registered minimum meaningful dA (estimability gate)
CLIP = (0.02, 0.98)


def simulate(b_as: float, b_ac: float, b_bc: float, r_true: float,
             sig_shared: float, sig_int_a: float, sig_int_b: float,
             k: int = K, n_obs: int = N_OBS) -> dict:
    """One configuration: returns the branch-rate table over REPS sims."""
    da_latent = b_as - b_ac
    ci_excl0 = established = harm = nonestim = unstable = 0
    widths = []
    for _ in range(REPS):
        eps = rng.normal(0.0, sig_shared, (k, n_obs))
        p_as = np.clip(b_as + eps + rng.normal(0.0, sig_int_a, (k, n_obs)), *CLIP)
        p_ac = np.clip(b_ac + eps + rng.normal(0.0, sig_int_a, (k, n_obs)), *CLIP)
        p_bs = np.clip(b_bc + eps + r_true * da_latent
                       + rng.normal(0.0, sig_int_b, (k, n_obs)), *CLIP)
        p_bc = np.clip(b_bc + eps + rng.normal(0.0, sig_int_b, (k, n_obs)), *CLIP)
        da_c = rng.binomial(1, p_as).mean(axis=1) - rng.binomial(1, p_ac).mean(axis=1)
        db_c = rng.binomial(1, p_bs).mean(axis=1) - rng.binomial(1, p_bc).mean(axis=1)
        da, db = da_c.mean(), db_c.mean()
        idx = rng.integers(0, k, size=(BOOT, k))
        da_star = da_c[idx].mean(axis=1)
        db_star = db_c[idx].mean(axis=1)
        da_lo, da_hi = np.percentile(da_star, [2.5, 97.5])
        if da < DA_MIN or not (da_lo > 0.0 or da_hi < 0.0):
            nonestim += 1
            continue
        degenerate = (da_star <= 0.05).mean()
        if degenerate > 0.10:
            unstable += 1
            continue
        with np.errstate(divide="ignore", invalid="ignore"):
            r_star = db_star / da_star
        r_lo, r_hi = np.percentile(r_star, [2.5, 97.5])
        widths.append(r_hi - r_lo)
        r_hat = db / da
        if r_lo > 0.0:
            ci_excl0 += 1
            if r_hat >= MME_R:
                established += 1
        elif r_hi < 0.0:
            harm += 1
    return {
        "detection_power_ci_excl_0": round(ci_excl0 / REPS, 3),
        "retention_established_branch": round(established / REPS, 3),
        "harm_branch": round(harm / REPS, 3),
        "non_estimable_gate": round(nonestim / REPS, 3),
        "unstable_denominator_flag": round(unstable / REPS, 3),
        "median_r_ci_width": round(float(np.median(widths)), 3) if widths else None,
    }


def main() -> None:
    base = dict(b_as=0.90, b_ac=0.15, b_bc=0.17, sig_shared=0.20,
                sig_int_a=0.10, sig_int_b=0.10)
    rows = [
        ("R1 binomial (0,0), R 0.25, K15x7 [sanity]",
         simulate(**base | dict(r_true=0.25, sig_shared=0.0, sig_int_a=0.0, sig_int_b=0.0))),
        ("R2 conservative (sh .20, siA/B .10), R 0.25, K15x7 [grounds MME]",
         simulate(**base | dict(r_true=0.25))),
        ("R3 conservative, R 0.25, K12x5 [undersized - kept for the record]",
         simulate(**base | dict(r_true=0.25, k=12, n_obs=5))),
        ("R4 conservative, R 0.25, K15x5 [clusters-only upgrade]",
         simulate(**base | dict(r_true=0.25, n_obs=5))),
        ("R5 conservative, R 0.25, K12x7 [seeds-only upgrade]",
         simulate(**base | dict(r_true=0.25, k=12))),
        ("R6 stress (siA/B .15), R 0.25, K15x7",
         simulate(**base | dict(r_true=0.25, sig_int_a=0.15, sig_int_b=0.15))),
        ("R7 B-stress (siB .20, siA .10), R 0.25, K15x7",
         simulate(**base | dict(r_true=0.25, sig_int_b=0.20))),
        ("R8 conservative, R 0.15 (sub-MME), K15x7",
         simulate(**base | dict(r_true=0.15))),
        ("R9 conservative, R 0.50, K15x7",
         simulate(**base | dict(r_true=0.50))),
        ("R10 conservative, R 1.00 (full portability), K15x7",
         simulate(**base | dict(r_true=1.00))),
        ("R11 conservative, R 0.00 (false positive), K15x7",
         simulate(**base | dict(r_true=0.0))),
        ("R12 conservative, R -0.25 (harm), K15x7",
         simulate(**base | dict(r_true=-0.25))),
        ("R13 conservative, R 0.25, stronger B base (bBc 0.30), K15x7",
         simulate(**base | dict(r_true=0.25, b_bc=0.30))),
        ("R14 conservative, R 0.25, weaker A benefit (dA 0.60), K15x7",
         simulate(**base | dict(r_true=0.25, b_as=0.75))),
        ("R15 conservative, R 0.25, gate-edge dA 0.35, K15x7",
         simulate(**base | dict(r_true=0.25, b_as=0.50))),
    ]
    results = [{"label": label, **res} for label, res in rows]
    for r in results:
        print(f"{r['label']:58s} detect={r['detection_power_ci_excl_0']:.3f} "
              f"estab={r['retention_established_branch']:.3f} harm={r['harm_branch']:.3f} "
              f"nonest={r['non_estimable_gate']:.3f} unstable={r['unstable_denominator_flag']:.3f} "
              f"width={r['median_r_ci_width']}")
    out = Path(__file__).parent / "power-results-cont002.json"
    out.write_text(json.dumps({
        "kind": "cont002-power-calc",
        "endpoint": "R = dB/dA retained-benefit ratio; cluster percentile bootstrap (two-sided 95%) over v3k primary clusters (DR 7 + DX 8 = 15); 7 seed-variant obs/cluster/cell (seeds 5001..5007)",
        "model": "per cluster c, seed s: eps~N(0,sig_shared) shared by all four cells (cancels inside dA/dB, correlates them); eta~N(0,sig_int) per cell (power killer); bases bAs 0.90 / bAc 0.15 / bBc 0.17 (dA latent 0.75); clip [0.02,0.98]",
        "gate": "dA point >= 0.30 AND dA cluster-bootstrap CI excludes 0, else non-estimable (inspirer clause); R bootstrap draws with dA* <= 0.05 -> unstable flag if > 10% of draws",
        "mme": {"R": MME_R, "dA_min": DA_MIN},
        "seeds": {"sim_rng": 20261007, "REPS": REPS, "BOOT": BOOT},
        "results": results,
    }, indent=1), encoding="utf-8")
    print("written:", out)


if __name__ == "__main__":
    main()
