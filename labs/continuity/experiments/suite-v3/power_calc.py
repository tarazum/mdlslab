"""Suite v3 design-phase power calculation (zero GPU).

Simulates the pre-registered cluster percentile bootstrap (the CONT-001 frozen
method: resample scenario-clusters with replacement, two-sided 95% percentile CI)
to answer, BEFORE any v3 data exists:

  R1 (retrospective): with K=7 clusters and arm A pinned at 0 (v2 free-form
     probes), how much power did the frozen test actually have?
  R2 (prospective): with K in {10, 12, 14, 16} clusters and label-form probes
     (guessing baseline 1/k instead of a degenerate 0), what effect sizes are
     detectable at ~80% power?
  R3: how much does the concentration of the effect across clusters matter
     (effect in all clusters vs only m of K)?

Method: per configuration, Monte-Carlo reps of a full experiment
(Bernoulli outcomes per seed x probe per cluster per arm -> cluster rates ->
delta -> bootstrap resample of clusters -> percentile CI), power = fraction of
reps where the two-sided 95% CI excludes 0. Stdlib-compatible output JSON next
to this script; numbers quoted in docs/SUITE-V3-DESIGN.md come from that file.
"""

from __future__ import annotations

import json
import math
import random
from itertools import product
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20261004)

REPS = 3000        # Monte-Carlo experiment repetitions per configuration
BOOT = 4000        # bootstrap resamples per experiment (frozen analysis uses 10k;
                   # 4k keeps the Monte-Carlo tractable and moves power by <1pt)
SEEDS = 5          # per arm, matches SIZING.md recommendation
PROBES = 2         # eligible probes per RM-cluster (v2 had 1-2; v3 plans 2)
ALPHA = 0.05

# (K, p_t0, p_t1, label) — cluster-level RM rates for the two arms compared.
CONFIGS = [
    # R1 retrospective: v2 confirmatory shape. A pinned at 0, E repeats in
    # 2/7 clusters at ~1.0 within them (D/E strict pattern), 0 elsewhere.
    (7, 0.0, "2of7@1.0", "R1: v2 retrospective, A pinned at 0, effect in 2/7 clusters"),
    # R2 prospective: label-form un-pins the no-memory arm to the guessing
    # baseline (1/k, k=6 -> 0.167). Uniform effect across clusters.
    (10, 0.60, 0.20, "R2: K=10, uniform RM 0.60 vs 0.20"),
    (12, 0.60, 0.20, "R2: K=12, uniform RM 0.60 vs 0.20"),
    (14, 0.60, 0.20, "R2: K=14, uniform RM 0.60 vs 0.20"),
    (16, 0.60, 0.20, "R2: K=16, uniform RM 0.60 vs 0.20"),
    # R2 smaller effects at K=14 (the planned cluster count).
    (14, 0.55, 0.25, "R2: K=14, uniform RM 0.55 vs 0.25 (delta 0.30)"),
    (14, 0.50, 0.30, "R2: K=14, uniform RM 0.50 vs 0.30 (delta 0.20)"),
    (14, 0.45, 0.35, "R2: K=14, uniform RM 0.45 vs 0.35 (delta 0.10)"),
    # R3 concentration at K=14, average delta 0.24: all clusters vs 8/14 vs 5/14.
    (14, 0.60, 0.20, "R3: K=14, effect in ALL 14 clusters"),
    (14, 0.48, 0.24, "R3: K=14, effect concentrated in 8/14 clusters (0.60v0.20 there, 0.36v0.28 elsewhere)"),
    (14, 0.42, 0.30, "R3: K=14, effect concentrated in 5/14 clusters (0.60v0.20 there, 0.35v0.33 elsewhere)"),
]


def cluster_rates(p0: float, p1: float | str, K: int, n_obs: int) -> tuple[np.ndarray, np.ndarray]:
    """One simulated experiment: per-cluster mean RM rate for each arm.

    p1 may be a scalar or a concentration spec 'mofK@rate' meaning m of K
    clusters carry the effect at `rate` and the rest sit at the guessing
    baseline for both arms.
    """
    if isinstance(p1, str) and "of" in p1:
        m, rate = p1.split("@")
        m = int(m.split("of")[0])
        rate = float(rate)
        eff0 = np.full(m, 0.0)                      # A pinned at 0 (v2 shape)
        eff1 = np.full(m, rate)
        rest = K - m
        base = 1.0 / 6.0                            # label-form guess floor
        r0 = np.concatenate([eff0, np.full(rest, base)])
        r1 = np.concatenate([eff1, np.full(rest, base)])
    elif isinstance(p1, str):
        # '0.60v0.20 there, 0.36v0.28 elsewhere' concentration specs handled below
        raise ValueError(p1)
    else:
        r0 = np.full(K, p0)
        r1 = np.full(K, p1)
    o0 = rng.binomial(n_obs, r0) / n_obs
    o1 = rng.binomial(n_obs, r1) / n_obs
    return o0, o1


def conc_rates(spec: str, K: int, n_obs: int, m_eff: int) -> tuple[np.ndarray, np.ndarray]:
    """Concentration configs: m_eff clusters carry (hi0, hi1), the rest (lo0, lo1)."""
    hi0, hi1, lo0, lo1 = spec
    r0 = np.concatenate([np.full(m_eff, hi0), np.full(K - m_eff, lo0)])
    r1 = np.concatenate([np.full(m_eff, hi1), np.full(K - m_eff, lo1)])
    o0 = rng.binomial(n_obs, r0) / n_obs
    o1 = rng.binomial(n_obs, r1) / n_obs
    return o0, o1


def boot_ci_excludes0(deltas: np.ndarray) -> bool:
    """Frozen method: resample clusters with replacement, two-sided 95% percentile CI."""
    idx = rng.integers(0, len(deltas), size=(BOOT, len(deltas)))
    means = deltas[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    return lo > 0.0 or hi < 0.0


def power(p0, p1, K: int, n_obs: int) -> float:
    hits = 0
    for _ in range(REPS):
        o0, o1 = cluster_rates(p0, p1, K, n_obs)
        hits += boot_ci_excludes0(o1 - o0)
    return hits / REPS


def run_conc(spec, K, n_obs, m_eff):
    hits = 0
    for _ in range(REPS):
        o0, o1 = conc_rates(spec, K, n_obs, m_eff)
        hits += boot_ci_excludes0(o1 - o0)
    return hits / REPS


def main() -> None:
    n_obs = SEEDS * PROBES
    results = []
    for K, p0, p1, label in CONFIGS:
        # concentration rows carry (hi0,hi1,lo0,lo1) via p1 tuple encoded in label
        if "8/14" in label:
            rates0, rates1 = None, None
            spec = (0.60, 0.20, 0.36, 0.28); m_eff = 8
            pw = run_conc(spec, K, n_obs, m_eff)
        elif "5/14" in label:
            spec = (0.60, 0.20, 0.35, 0.33); m_eff = 5
            pw = run_conc(spec, K, n_obs, m_eff)
        else:
            pw = power(p0, p1, K, n_obs)
        results.append({"label": label, "K": K, "n_obs_per_cluster": n_obs,
                        "reps": REPS, "bootstrap": BOOT, "power": round(pw, 3)})
        print(f"{label:70s} power={pw:.3f}")

    out = Path(__file__).parent / "power-results.json"
    out.write_text(json.dumps({
        "kind": "suite-v3-power-calc",
        "method": "cluster percentile bootstrap, two-sided 95%; Bernoulli outcomes, "
                  "5 seeds x 2 probes per cluster; BOOT=4000 resamples per rep, "
                  "REPS=3000 Monte-Carlo experiments per configuration",
        "seed": 20261004,
        "results": results,
    }, indent=1), encoding="utf-8")
    print("written:", out)


if __name__ == "__main__":
    main()
