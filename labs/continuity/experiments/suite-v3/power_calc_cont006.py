"""Power calculation for the CONT-006 primary endpoint: R2 - R0 transfer delta.

Design (docs/CONT-006-DESIGN.md, docs/EVALUATION-PREP-CONT006.md): paired
two-arm comparison {R0 = persistent memory, no lessons; R2 = same + ACTIVE
worker lessons through the lesson channel} on the v3l PRIMARY transfer
clusters (15 = CR x4 + CU x4 + RT x3 + DX x2 + DR x2), 7 seed-variant
observations per cluster per arm (seeds 6001..6007), one held-out label-form
probe per observation (scoring SUITE-V3-DESIGN section 3).

Simulated data-generating model per cluster c, seed s (paired-variant model
in the power_calc_cont002.py lineage, two cells instead of four):

    eps[c,s]  ~ N(0, sig_shared)   # cluster-seed content difficulty, SHARED
                                   # by both arms (same rendered content)
                                   # -> cancels inside the delta
    p(R0)     = clip(b0 + eps + eta0)          # eta ~ N(0, sig_arm) per arm
    p(R2)     = clip(b0 + d_true + eps + eta2) # the lesson treatment

Bases: b0 = 0.525 (the C2-confirmatory T-arm pooled pass rate on PRIMARY
family probes: passes 65/67/62/58 of 120 non-gc probes per arm = 252/480;
PR-REVIEW-CONT006 RC-1 corrected the denominator — the pilot run's 0.42 had
wrongly divided the same numerators by 150, which includes the 30 gc probes
the selector never counts as fails; R0 is the closest committed analogue of
the lesson-free memory-on configuration); d_true at the MME row = MME. The
lesson injection is an arm-level treatment; eta does NOT cancel — the power
killer (as in CONT-002). Clip [0.02, 0.98]. Sensitivity rows keep b0 0.30 /
0.55 / 0.75, which bracket the former 0.42 reading.

Analysis replicated EXACTLY as pre-registered: per cluster, seed means ->
d_c = mean_R2 - mean_R0; d = mean over clusters; two-sided 95% cluster
percentile bootstrap (10,000-equivalent BOOT resamples, RNG seed frozen).
Verdict branches: CI excludes 0 upward AND d >= MME -> "lesson transfer
established"; CI>0 and d < MME -> directional below MME; CI<0 -> harm;
includes 0 -> no difference. Reported per row: detection power
(P(CI excludes 0 upward)), established-branch rate, harm rate, median CI
width. House precedent: the "established" branch additionally requires the
point estimate >= MME, bounding it near 0.5 AT exactly the MME — reported
openly, never hidden (cycle-2 / CONT-002 precedent).
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20261008)
REPS = 3000
BOOT = 4000
K = 15                 # v3l primary transfer clusters (CR4+CU4+RT3+DX2+DR2)
N_OBS = 7              # seed-variant observations per cluster (6001..6007)
MME_D = 0.20           # pre-registered MME on the absolute pass-rate delta
CLIP = (0.02, 0.98)
B0 = 0.525             # R0 base (C2 T-arm pooled pass on primary families, 252/480)


def simulate(b0: float, d_true: float, sig_shared: float, sig_arm: float,
             k: int = K, n_obs: int = N_OBS) -> dict:
    ci_up = ci_any = established = harm = 0
    widths = []
    for _ in range(REPS):
        eps = rng.normal(0.0, sig_shared, (k, n_obs))
        p0 = np.clip(b0 + eps + rng.normal(0.0, sig_arm, (k, n_obs)), *CLIP)
        p2 = np.clip(b0 + d_true + eps + rng.normal(0.0, sig_arm, (k, n_obs)), *CLIP)
        d_c = rng.binomial(1, p2).mean(axis=1) - rng.binomial(1, p0).mean(axis=1)
        d = d_c.mean()
        idx = rng.integers(0, k, size=(BOOT, k))
        d_star = d_c[idx].mean(axis=1)
        lo, hi = np.percentile(d_star, [2.5, 97.5])
        widths.append(hi - lo)
        if lo > 0.0:
            ci_up += 1
            if d >= MME_D:
                established += 1
        elif hi < 0.0:
            harm += 1
    return {
        "detection_power_ci_up": round(ci_up / REPS, 3),
        "established_branch": round(established / REPS, 3),
        "harm_branch": round(harm / REPS, 3),
        "median_ci_width": round(float(np.median(widths)), 3),
    }


def main() -> None:
    base = dict(b0=B0, sig_shared=0.20, sig_arm=0.10)
    rows = [
        ("R1 binomial (0,0), d 0.20, K15x7 [sanity]",
         simulate(**base | dict(d_true=0.20, sig_shared=0.0, sig_arm=0.0))),
        ("R2 conservative (sh .20, sa .10), d 0.20 = MME, K15x7 [grounds MME]",
         simulate(**base | dict(d_true=0.20))),
        ("R3 conservative, d 0.20, K15x5 [seeds-only reduction - record]",
         simulate(**base | dict(d_true=0.20, n_obs=5))),
        ("R4 conservative, d 0.20, K12x7 [clusters-only reduction - record]",
         simulate(**base | dict(d_true=0.20, k=12))),
        ("R5 conservative, d 0.15 (sub-MME), K15x7",
         simulate(**base | dict(d_true=0.15))),
        ("R6 conservative, d 0.175 (ladder mid), K15x7",
         simulate(**base | dict(d_true=0.175))),
        ("R7 stress (sa .15), d 0.20, K15x7",
         simulate(**base | dict(d_true=0.20, sig_arm=0.15))),
        ("R8 conservative, d 0.30 (R3-gold-channel scale), K15x7",
         simulate(**base | dict(d_true=0.30))),
        ("R9 conservative, d 0.00 (false positive), K15x7",
         simulate(**base | dict(d_true=0.0))),
        ("R10 conservative, d -0.15 (harm), K15x7",
         simulate(**base | dict(d_true=-0.15))),
        ("R11 conservative, d 0.20, weaker base (b0 0.30), K15x7",
         simulate(**base | dict(d_true=0.20, b0=0.30))),
        ("R12 conservative, d 0.20, stronger base (b0 0.55), K15x7",
         simulate(**base | dict(d_true=0.20, b0=0.55))),
        ("R13 conservative, d 0.20, headroom edge (b0 0.75), K15x7",
         simulate(**base | dict(d_true=0.20, b0=0.75))),
    ]
    results = [{"label": label, **res} for label, res in rows]
    for r in results:
        print(f"{r['label']:64s} detect={r['detection_power_ci_up']:.3f} "
              f"estab={r['established_branch']:.3f} harm={r['harm_branch']:.3f} "
              f"width={r['median_ci_width']}")
    out = Path(__file__).parent / "power-results-cont006.json"
    out.write_text(json.dumps({
        "kind": "cont006-power-calc",
        "endpoint": "d = S(R2) - S(R0) label-form pass-rate delta on the v3l "
                    "primary transfer clusters (CR4+CU4+RT3+DX2+DR2 = 15); "
                    "two-sided 95% cluster percentile bootstrap; 7 seed-variant "
                    "obs/cluster/arm (seeds 6001..6007)",
        "model": "per cluster c, seed s: eps~N(0,sig_shared) shared by both arms "
                 "(cancels inside d); eta~N(0,sig_arm) per arm (power killer); "
                 "b0 0.525 (C2-confirmatory T-arm pooled pass on PRIMARY-family probes, 252/480; PR-REVIEW-CONT006 RC-1 corrected denominator); clip [0.02,0.98]",
        "mme": {"d": MME_D,
                "rationale": "MME ladder 0.15/0.175/0.20 was sized at design time "
                             "(zero GPU): per-observation binomial noise with n=1 "
                             "probes per cluster-seed-arm binds detection below "
                             "0.80 at d 0.15 (row R5) and 0.175 (row R6); 0.20 is "
                             "the smallest 0.05-step effect detectable at >= 0.80 "
                             "on the conservative row (R2) — effects below 0.20 "
                             "are NOT claimable at this design's power (declared "
                             "limitation, cycle-2 / CONT-002 sizing precedent); "
                             "0.20 also clears the template section 9 guessing-"
                             "band floor (>= 0.15). MME moved during design-time "
                             "sizing BEFORE any inference, never after."},
        "seeds": {"sim_rng": 20261008, "REPS": REPS, "BOOT": BOOT},
        "results": results,
    }, indent=1), encoding="utf-8")
    print("written:", out)


if __name__ == "__main__":
    main()
