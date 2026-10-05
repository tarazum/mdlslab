"""Power calculation v2 for the CONT-005 confirmatory primary endpoint.

Endpoint changed after the headroom pilot (LOG 2026-10-05): the primary is the
LABEL-FORM ERROR RATE on the policy-targeted family set CR+CU (12 clusters:
correction_reuse x8 + contradiction_update x4), primary contrast T2 - T0
(benefit = negative). The strict scripted-trap RM endpoint has no headroom on
suite v3 (0/42 in T0/T2 at pilot scale) and is demoted to secondary.

Method: same simulation harness as power_calc.py (cluster percentile bootstrap,
two-sided 95%, REPS x BOOT Monte-Carlo; Bernoulli outcomes, 5 seeds x 1 probe
per cluster = 5 observations per cluster).

Configurations (T0 error rate fixed at the pilot estimate 0.64):
  R1  pilot-scale effect: T2 0.28 (delta 0.36)
  R2  MME scan: T2 0.49 / 0.44 / 0.39 (delta 0.15 / 0.20 / 0.25)
  R3  concentration: effect in 8/12 and 6/12 clusters (avg delta preserved ~0.24)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20261005)
REPS = 3000
BOOT = 4000
K = 12
N_OBS = 5
T0_RATE = 0.64


def power_uniform(p1: float) -> float:
    hits = 0
    for _ in range(REPS):
        d0 = rng.binomial(N_OBS, T0_RATE, K) / N_OBS
        d1 = rng.binomial(N_OBS, p1, K) / N_OBS
        delta = d1 - d0
        idx = rng.integers(0, K, size=(BOOT, K))
        means = delta[idx].mean(axis=1)
        lo, hi = np.percentile(means, [2.5, 97.5])
        hits += (lo > 0.0) or (hi < 0.0)
    return hits / REPS


def power_concentrated(m_eff: int, hi1: float, lo1: float) -> float:
    """Effect in m_eff of K clusters: T2 error hi1 there, lo1 elsewhere."""
    r1 = np.concatenate([np.full(m_eff, hi1), np.full(K - m_eff, lo1)])
    hits = 0
    for _ in range(REPS):
        d0 = rng.binomial(N_OBS, T0_RATE, K) / N_OBS
        d1 = rng.binomial(N_OBS, r1, K) / N_OBS
        delta = d1 - d0
        idx = rng.integers(0, K, size=(BOOT, K))
        means = delta[idx].mean(axis=1)
        lo, hi = np.percentile(means, [2.5, 97.5])
        hits += (lo > 0.0) or (hi < 0.0)
    return hits / REPS


def main() -> None:
    results = [
        {"label": "R1: pilot-scale, T2 err 0.28 (delta 0.36)", "power": round(power_uniform(0.28), 3)},
        {"label": "R2: MME scan, delta 0.15 (T2 0.49)", "power": round(power_uniform(0.49), 3)},
        {"label": "R2: MME scan, delta 0.20 (T2 0.44)", "power": round(power_uniform(0.44), 3)},
        {"label": "R2: MME scan, delta 0.25 (T2 0.39)", "power": round(power_uniform(0.39), 3)},
        {"label": "R3: effect in 8/12 clusters (0.28 there, 0.49 elsewhere)", "power": round(power_concentrated(8, 0.28, 0.49), 3)},
        {"label": "R3: effect in 6/12 clusters (0.28 there, 0.57 elsewhere)", "power": round(power_concentrated(6, 0.28, 0.57), 3)},
    ]
    for r in results:
        print(f"{r['label']:58s} power={r['power']:.3f}")
    out = Path(__file__).parent / "power-results-v2.json"
    out.write_text(json.dumps({
        "kind": "suite-v3-power-calc-v2",
        "endpoint": "label-form error rate, CR+CU primary set, K=12 clusters, 5 obs/cluster, T0=0.64",
        "method": "cluster percentile bootstrap, two-sided 95%; REPS=3000, BOOT=4000",
        "seed": 20261005,
        "results": results,
    }, indent=1), encoding="utf-8")
    print("written:", out)


if __name__ == "__main__":
    main()
