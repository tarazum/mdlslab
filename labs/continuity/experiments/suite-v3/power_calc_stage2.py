"""Power calculation for the CONT-006 STAGE 2 primary endpoints (v3o suite).

Stage-2 design (SESSION-BRIEF-CONT006-STAGE2.md §4 minimum, fixed at prereg):
models {G8B, Q35} x delivery positions {session-start, probe-time} x content
{NONE (position-invariant by construction: nothing is delivered at either
position), NEUTRAL-matched-per-position, NEWF-v2, OLDG}; corrected delivery
fixed. Primary per the brief: the lesson-minus-baseline INTERACTION per
model pair —

    I_NEWF = (NEWF_v2 - NONE)_G8B - (NEWF_v2 - NONE)_Q35     (E1 analogue,
                                                             end-to-end)

with the within-model lesson effect d_m = (NEWF_v2 - NONE)_m at the
corrected (probe-time) delivery as the per-model co-primary, and the
neutral contrast (NEWF_v2 - NEUTRAL)_m as secondary.

Simulation model (the power_calc_cont006_v2.py lineage, extended to four
cells): per cluster c, seed s,

    eps[c,s]   ~ N(0, sig_shared)   # cluster-seed content difficulty,
                                    # SHARED by every cell (same rendered
                                    # v3o content) -> cancels inside every
                                    # (content - NONE) difference and inside
                                    # the interaction
    eta[c,s,m,cell] ~ N(0, sig_cell)  # per observation, independent
    p(m,cell)[c,s] = clip(b0_m + d_m(cell) + eps + eta)

Analysis replicated as pre-registered: per cluster, seed means ->
cluster-level d_c -> mean over clusters -> two-sided 95% cluster percentile
bootstrap (BOOT resamples, RNG frozen). The interaction analysis
double-differences per cluster (G8B lesson-delta minus Q35 lesson-delta)
and bootstraps the same way.

MME (template PREREG-REQUIREMENTS-V2 §6/§9): the v3o primary probes are
closed 6-option label probes (guess = 1/6; measured-deviation term 0), so
the guessing-band floor is 0.15; MME = the smallest 0.05-step effect
detectable at >= 0.80 power on the conservative row (sig_shared .20,
sig_cell .10) at the planned K = 15 clusters x 7 seeds, laddered below
(0.10 / 0.15 / 0.20). Declared sizing limitation (CONT-002 / V2 sizing
precedent): effects below the MME are NOT claimable at this design's
power.

Bases: v3o difficulty is re-aimed so BOTH models have headroom (design
bands; verified by the pre-registered in-run baseline gate): G8B b0 0.35,
Q35 b0 0.65 as the planning point; sensitivity rows 0.30/0.50/0.70.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20261010)
REPS = 3000
BOOT = 4000
K = 15                 # v3o primary transfer clusters (CR4+CU4+RT3+DX2+DR2)
N_OBS = 7              # seed-variant observations per cluster (9001..9007)
CLIP = (0.02, 0.98)
B0_G8B = 0.35          # planning-point bases (v3o design bands; see docstring)
B0_Q35 = 0.65


def _cluster_deltas(means: dict[str, np.ndarray], a: str, b: str) -> np.ndarray:
    """per-cluster mean of cell a minus cell b (arrays are (k, n_obs))."""
    return means[a].mean(axis=1) - means[b].mean(axis=1)


def _boot_ci(d_c: np.ndarray) -> tuple[float, float, float, bool, bool]:
    d = float(d_c.mean())
    idx = rng.integers(0, len(d_c), size=(BOOT, len(d_c)))
    lo, hi = np.percentile(d_c[idx].mean(axis=1), [2.5, 97.5])
    return d, lo, hi, lo > 0.0, hi < 0.0


def simulate_within_model(b0: float, d_true: float, sig_shared: float,
                          sig_cell: float, k: int = K,
                          n_obs: int = N_OBS) -> dict:
    """One model, two cells (NONE vs NEWF_v2); d = lesson effect."""
    ci_up = estab = harm = 0
    widths = []
    for _ in range(REPS):
        eps = rng.normal(0.0, sig_shared, (k, n_obs))
        p0 = np.clip(b0 + eps + rng.normal(0.0, sig_cell, (k, n_obs)), *CLIP)
        p1 = np.clip(b0 + d_true + eps + rng.normal(0.0, sig_cell, (k, n_obs)), *CLIP)
        d_c = rng.binomial(1, p1).mean(axis=1) - rng.binomial(1, p0).mean(axis=1)
        _, lo, hi, up, dn = _boot_ci(d_c)
        widths.append(hi - lo)
        ci_up += up
        estab += up and d_true >= 0.15  # established-branch reference at MME floor
        harm += dn
    return {"detect": round(ci_up / REPS, 3), "estab": round(estab / REPS, 3),
            "harm": round(harm / REPS, 3),
            "width": round(float(np.median(widths)), 3)}


def simulate_interaction(b0_g8b: float, b0_q35: float, d_g8b: float,
                         d_q35: float, sig_shared: float, sig_cell: float,
                         k: int = K, n_obs: int = N_OBS) -> dict:
    """Four cells (2 models x {NONE, NEWF_v2}); I = the model x lesson
    interaction = (d_G8B - d_Q35) with d_true_I = d_g8b - d_q35."""
    d_true_i = d_g8b - d_q35
    ci_up = ci_dn = 0
    widths = []
    for _ in range(REPS):
        eps = rng.normal(0.0, sig_shared, (k, n_obs))
        cells = {}
        for m, b0, d in (("g8b", b0_g8b, d_g8b), ("q35", b0_q35, d_q35)):
            p_none = np.clip(b0 + eps + rng.normal(0.0, sig_cell, (k, n_obs)), *CLIP)
            p_newf = np.clip(b0 + d + eps + rng.normal(0.0, sig_cell, (k, n_obs)), *CLIP)
            cells[f"{m}_none"] = rng.binomial(1, p_none).mean(axis=1)
            cells[f"{m}_newf"] = rng.binomial(1, p_newf).mean(axis=1)
        i_c = (cells["g8b_newf"] - cells["g8b_none"]) \
            - (cells["q35_newf"] - cells["q35_none"])
        _, lo, hi, up, dn = _boot_ci(i_c)
        widths.append(hi - lo)
        ci_up += up
        ci_dn += dn
    return {"detect_up": round(ci_up / REPS, 3), "detect_down": round(ci_dn / REPS, 3),
            "width": round(float(np.median(widths)), 3),
            "d_true_I": round(d_true_i, 3)}


def main() -> None:
    cons = dict(sig_shared=0.20, sig_cell=0.10)
    rows: list[dict] = []

    # --- within-model lesson effect (co-primary), G8B base ---
    for label, kw in [
        ("W1 G8B binomial sanity, d .20", dict(b0=B0_G8B, d_true=0.20, sig_shared=0.0, sig_cell=0.0)),
        ("W2 G8B conservative, d .20, K15x7", dict(b0=B0_G8B, d_true=0.20, **cons)),
        ("W3 G8B conservative, d .15, K15x7", dict(b0=B0_G8B, d_true=0.15, **cons)),
        ("W4 G8B conservative, d .10, K15x7", dict(b0=B0_G8B, d_true=0.10, **cons)),
        ("W5 G8B conservative, d .20, K15x4 [seed cut - record]", dict(b0=B0_G8B, d_true=0.20, n_obs=4, **cons)),
        ("W6 G8B conservative, d .20, K15x3 [seed cut - record]", dict(b0=B0_G8B, d_true=0.20, n_obs=3, **cons)),
        ("W7 G8B conservative, d .15, K15x4 [seed cut]", dict(b0=B0_G8B, d_true=0.15, n_obs=4, **cons)),
        ("W8 G8B weaker base .30, d .15", dict(b0=0.30, d_true=0.15, **cons)),
        ("W9 Q35 base .65, d .15", dict(b0=B0_Q35, d_true=0.15, **cons)),
        ("W10 Q35 base .65, d .10", dict(b0=B0_Q35, d_true=0.10, **cons)),
        ("W11 G8B d 0.0 false-positive", dict(b0=B0_G8B, d_true=0.0, **cons)),
        ("W12 G8B d -0.15 harm", dict(b0=B0_G8B, d_true=-0.15, **cons)),
    ]:
        rows.append({"label": label, "family": "within_model",
                     **simulate_within_model(**kw)})

    # --- primary interaction (E1 analogue, end-to-end) ---
    for label, kw in [
        ("I1 interaction d_G8B .15 d_Q35 .0 (I=.15), K15x7", dict(d_g8b=0.15, d_q35=0.0, **cons)),
        ("I2 interaction d_G8B .20 d_Q35 .0 (I=.20), K15x7", dict(d_g8b=0.20, d_q35=0.0, **cons)),
        ("I3 interaction d_G8B .0 d_Q35 .0 (I=0, false positive), K15x7", dict(d_g8b=0.0, d_q35=0.0, **cons)),
        ("I4 interaction d_G8B -.15 d_Q35 .0 (I=-.15, harm side), K15x7", dict(d_g8b=-0.15, d_q35=0.0, **cons)),
        ("I5 interaction d_G8B .15 d_Q35 .05 (I=.10), K15x7", dict(d_g8b=0.15, d_q35=0.05, **cons)),
        ("I8 interaction d_G8B .25 d_Q35 .0 (I=.25), K15x7", dict(d_g8b=0.25, d_q35=0.0, **cons)),
        ("I9 interaction d_G8B .30 d_Q35 .0 (I=.30), K15x7 [0.80 pin]", dict(d_g8b=0.30, d_q35=0.0, **cons)),
        ("I6 interaction I=.15, K15x4 [seed cut - record]", dict(d_g8b=0.15, d_q35=0.0, n_obs=4, **cons)),
        ("I7 interaction I=.15, K15x3 [seed cut - record]", dict(d_g8b=0.15, d_q35=0.0, n_obs=3, **cons)),
    ]:
        rows.append({"label": label, "family": "interaction",
                     **simulate_interaction(b0_g8b=B0_G8B, b0_q35=B0_Q35, **kw)})

    out = Path(__file__).parent / "power-results-cont006-stage2.json"
    out.write_text(json.dumps({
        "kind": "cont006-stage2-power-calc",
        "endpoint": "within-model d_m = (NEWF_v2 - NONE)_m pass-rate delta on the "
                    "v3o primary clusters (15 = CR4+CU4+RT3+DX2+DR2) and the "
                    "primary interaction I = d_G8B - d_Q35; two-sided 95% cluster "
                    "percentile bootstrap; planned K = 15 x 7 seeds (v3o 9001..9007)",
        "model": "per cluster c, seed s: eps~N(0,sig_shared) shared by EVERY cell "
                 "(same rendered v3o content; cancels in every difference); "
                 "eta~N(0,sig_cell) per observation-cell; clip [0.02,0.98]; "
                 "planning bases G8B 0.35 / Q35 0.65 (v3o design bands, verified "
                 "by the pre-registered in-run baseline gate)",
        "mme": {"d": None,
                "rationale": "laddered below: the smallest 0.05-step effect with "
                             "detection power >= 0.80 on the conservative row "
                             "(sig_shared .20, sig_cell .10) at the planned K; "
                             "the template guessing-band floor is 0.15 (closed "
                             "6-option probes, guess 1/6); effects below the MME "
                             "are NOT claimable at this design's power (declared "
                             "limitation; CONT-002 / V2 sizing precedent). The MME "
                             "is pinned by the rows in this artifact at prereg."},
        "seeds": {"sim_rng": 20261010, "REPS": REPS, "BOOT": BOOT},
        "results": rows,
    }, indent=1), encoding="utf-8")
    for r in rows:
        if r["family"] == "within_model":
            print(f"{r['label']:52s} detect={r['detect']:.3f} estab={r['estab']:.3f} "
                  f"harm={r['harm']:.3f} width={r['width']}")
        else:
            print(f"{r['label']:52s} I={r['d_true_I']:+.2f} up={r['detect_up']:.3f} "
                  f"down={r['detect_down']:.3f} width={r['width']}")
    print("written:", out)


if __name__ == "__main__":
    main()
