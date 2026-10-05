"""Power calculation v3 for the CONT-005 cycle-2 primary endpoint (T1 vs T0).

Endpoint: LABEL-FORM ERROR RATE on the CR+CU primary set (12 clusters), suite
v3i protocol. Cycle-2 changes vs power_calc_v2:
  - primary contrast T0 - T1 (annotations-only; the only 0/90 label-trap-repeat
    arm in cycle 1), T2/T3 demoted to secondaries;
  - NEW between-seed spread model. Cycle 1 (Fable audit) showed temp-0 seeds on
    byte-identical prompts are ONE observation, not five; suite v3i renders a
    predeclared per-seed content variant, so the 5 observations per cluster are
    genuine replicates whose error rates carry a seed-level difficulty
    component. Model (per arm a, cluster c, seed s):
        p[a,c,s] = clip(base_a + eps_s + eta[a,s], 0.02, 0.98)
        eps_s    ~ N(0, sig_shared)  # variant difficulty, SHARED by both arms
                                      # (same rendered content) -> cancels in
                                      # the paired per-seed delta
        eta[a,s] ~ N(0, sig_int)     # arm-specific variant response (does the
                                      # arm react differently to this variant?)
                                      # -> does NOT cancel; the power killer
  The design-phase spread is UNMEASURED (zero v3i inference so far), so rows
  scan (sig_shared, sig_int) explicitly and the MME is grounded on the
  conservative row; the pilot measures the actual spread and the freeze-time
  power re-check must clear the same row (pre-declared in EVALUATION-PREP-v3).

Method: same simulation harness as power_calc_v2 (cluster percentile bootstrap,
two-sided 95%, REPS x BOOT Monte-Carlo; 5 seeds x 1 probe per cluster).

Configurations (T0 error rate fixed at the design target 0.50 — the v3i
authoring aim is mid-scale headroom in BOTH arms; sensitivity rows 0.40/0.64):
  P1  binomial-equivalent (0, 0): MME scan 0.15 / 0.20 / 0.25 / 0.30
  P2  shared difficulty only (0.20, 0): delta 0.25 (expect ~P1: cancels)
  P3  conservative (0.20, 0.10): delta 0.20 / 0.25 / 0.30
  P4  stress (0.20, 0.15): delta 0.25 / 0.30
  P5  concentration under P3: effect in 8/12 and 6/12 clusters
  P6  T0 base sensitivity under P3: T0 0.64 (cycle-1 CR scale) / 0.40
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

rng = np.random.default_rng(20261006)
REPS = 3000
BOOT = 4000
K = 12
N_OBS = 5
T0_RATE = 0.50
CLIP = (0.02, 0.98)


def simulate(t0_rate: float, delta: float, sig_shared: float, sig_int: float,
             effect_clusters: int | None = None) -> float:
    """Power of the two-sided 95% cluster bootstrap for T0 - T1 = delta.

    effect_clusters: None = uniform delta; else the delta lands in the first
    `effect_clusters` clusters only (concentration scenarios), with the
    average delta preserved over the K clusters.
    """
    if effect_clusters is None:
        base0 = np.full(K, t0_rate)
        base1 = np.full(K, t0_rate - delta)
    else:
        # keep the average delta equal: effected clusters shift by
        # delta * K / m, non-effected stay at the T0 rate
        d_eff = delta * K / effect_clusters
        base0 = np.full(K, t0_rate)
        base1 = np.concatenate([
            np.full(effect_clusters, t0_rate - d_eff),
            np.full(K - effect_clusters, t0_rate),
        ])
    hits = 0
    for _ in range(REPS):
        eps = rng.normal(0.0, sig_shared, N_OBS)              # shared per seed
        p0 = np.clip(base0[:, None] + eps[None, :] + rng.normal(0.0, sig_int, (K, N_OBS)), *CLIP)
        p1 = np.clip(base1[:, None] + eps[None, :] + rng.normal(0.0, sig_int, (K, N_OBS)), *CLIP)
        y0 = rng.binomial(1, p0).mean(axis=1)                 # cluster means
        y1 = rng.binomial(1, p1).mean(axis=1)
        d = y0 - y1
        idx = rng.integers(0, K, size=(BOOT, K))
        means = d[idx].mean(axis=1)
        lo, hi = np.percentile(means, [2.5, 97.5])
        hits += (lo > 0.0) or (hi < 0.0)
    return hits / REPS


def main() -> None:
    rows = [
        ("P1: binomial-equivalent (0,0), delta 0.15", simulate(T0_RATE, 0.15, 0.0, 0.0)),
        ("P1: binomial-equivalent (0,0), delta 0.20", simulate(T0_RATE, 0.20, 0.0, 0.0)),
        ("P1: binomial-equivalent (0,0), delta 0.25", simulate(T0_RATE, 0.25, 0.0, 0.0)),
        ("P1: binomial-equivalent (0,0), delta 0.30", simulate(T0_RATE, 0.30, 0.0, 0.0)),
        ("P2: shared difficulty only (0.20,0), delta 0.25", simulate(T0_RATE, 0.25, 0.20, 0.0)),
        ("P3: conservative (0.20,0.10), delta 0.20", simulate(T0_RATE, 0.20, 0.20, 0.10)),
        ("P3: conservative (0.20,0.10), delta 0.25", simulate(T0_RATE, 0.25, 0.20, 0.10)),
        ("P3: conservative (0.20,0.10), delta 0.30", simulate(T0_RATE, 0.30, 0.20, 0.10)),
        ("P4: stress (0.20,0.15), delta 0.25", simulate(T0_RATE, 0.25, 0.20, 0.15)),
        ("P4: stress (0.20,0.15), delta 0.30", simulate(T0_RATE, 0.30, 0.20, 0.15)),
        ("P5: P3 + effect in 8/12 clusters, avg delta 0.25", simulate(T0_RATE, 0.25, 0.20, 0.10, effect_clusters=8)),
        ("P5: P3 + effect in 6/12 clusters, avg delta 0.25", simulate(T0_RATE, 0.25, 0.20, 0.10, effect_clusters=6)),
        ("P6: P3, T0 0.64 (cycle-1 CR scale), delta 0.25", simulate(0.64, 0.25, 0.20, 0.10)),
        ("P6: P3, T0 0.40, delta 0.25", simulate(0.40, 0.25, 0.20, 0.10)),
    ]
    results = [{"label": label, "power": round(p, 3)} for label, p in rows]
    for r in results:
        print(f"{r['label']:58s} power={r['power']:.3f}")
    out = Path(__file__).parent / "power-results-v3.json"
    out.write_text(json.dumps({
        "kind": "suite-v3-power-calc-v3",
        "endpoint": "label-form error rate, CR+CU primary set, K=12 clusters, 5 seed-variant obs/cluster, T0=0.50 (design target; sensitivity 0.40/0.64)",
        "method": "cluster percentile bootstrap, two-sided 95%; REPS=3000, BOOT=4000; paired per-seed variant model: p=clip(base+eps_shared+eta_arm), eps shared across arms (cancels in delta), eta arm-specific (power killer)",
        "seed": 20261006,
        "results": results,
    }, indent=1), encoding="utf-8")
    print("written:", out)


if __name__ == "__main__":
    main()
