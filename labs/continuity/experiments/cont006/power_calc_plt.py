"""Power calculation for the CONT-006 PLT primary endpoint (BEFORE the
prereg freeze — DESIGN-CONT006-PLT.md rev 2 §6 / review R-1).

Primary: recurrence rate of the target failure class, L − A, on
cluster = (class, instance): 5 classes × 5 instances = 25 clusters × 7
seeds (binary episode outcomes; an episode counts only if its trigger
opportunity occurred — R-2; modeled here as the per-seed Bernoulli).

Simulation model (stage-2 power_calc_stage2.py lineage, extended per
review R-1 to make the class structure explicit — instances within a
class share the latent rule):

    kappa[class]               ~ N(0, sig_kappa)    # class baseline shift,
                                                    # shared by BOTH arms ->
                                                    # cancels in paired d_c
    delta_class[class]         ~ N(d_true, sig_dclass)
                                                    # EFFECT heterogeneity
                                                    # across classes — the
                                                    # honesty term: does NOT
                                                    # cancel
    eps[cluster]               ~ N(0, sig_inst)     # instance baseline
                                                    # spread (paired, cancels)
    eta[cluster, arm, seed]    ~ N(0, sig_cell)
    p(arm)[cluster, seed] = clip(b0 + kappa + eps + d_arm + eta),
        d_A = 0, d_L = delta_class[class]
    d_c = mean_seeds(L) − mean_seeds(A)   per cluster

Analysis replicated as pre-registered: cluster percentile bootstrap over
the 25 d_c (BOOT resamples, RNG frozen). MANDATORY sensitivity variants:
(a) leave-one-class-out (drop one class = 5 clusters; worst case over
which class is dropped is approximated by re-running at K=20 with the
same generative process); (b) two-level bootstrap (resample classes,
then instances within class). MME = the smallest 0.05-step effect with
power >= 0.80 on the conservative row at the planned K=25×7.

Planning base: arm-A recurrence b0 = 0.60 (mid-band for the pilot gate
[0.3, 0.9]; the pilot verifies). Sensitivity rows 0.45 / 0.75.
Conservative row: sig_kappa 0.15, sig_inst 0.10, sig_cell 0.10,
sig_dclass 0.10.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

OUT = Path(__file__).parent / "power-results-plt.json"
rng = np.random.default_rng(20261011)
REPS = 3000
BOOT = 4000
CLIP = (0.02, 0.98)
B0 = 0.60
N_CLASSES = 5
N_INST = 5
N_SEEDS = 7
K = N_CLASSES * N_INST        # 25 planned clusters
CONSERVATIVE = dict(sig_kappa=0.15, sig_inst=0.10, sig_cell=0.10,
                    sig_dclass=0.10)
SIG_DINST = 0.05           # instance-level effect heterogeneity (V-12)


def _boot_means(d_c: np.ndarray) -> np.ndarray:
    idx = rng.integers(0, len(d_c), size=(BOOT, len(d_c)))
    return d_c[idx].mean(axis=1)


def _boot(d_c: np.ndarray, two_level: bool = False) -> tuple:
    d = float(d_c.mean())
    if not two_level:
        means = _boot_means(d_c)
    else:
        # resample classes (5), then instances within each resampled class
        cls_idx = np.arange(len(d_c)).reshape(N_CLASSES, N_INST)
        pick_c = rng.integers(0, N_CLASSES, (BOOT, N_CLASSES))
        inst = rng.integers(0, N_INST, (BOOT, N_CLASSES, N_INST))
        sel = cls_idx[pick_c[:, :, None], inst]
        means = d_c[sel].mean(axis=(1, 2))
    lo, hi = np.percentile(means, [2.5, 97.5])
    return d, lo, hi, lo > 0.0, hi < 0.0


def simulate_conjunctive(b0: float, d_true: float, sig_kappa: float,
                         sig_inst: float, sig_cell: float,
                         sig_dclass: float, sig_dinst: float,
                         mme: float, k_classes: int = N_CLASSES,
                         n_inst: int = N_INST, n_seeds: int = N_SEEDS
                         ) -> dict:
    """The DECISION rule as pre-registered (review V-1): established =
    (CI95 entirely below 0) AND (point |d| >= mme) AND (every leave-one-
    class-out drop keeps CI entirely below 0) AND (two-level class->
    instance bootstrap CI entirely below 0). All four computed INSIDE one
    replication (not separate runs)."""
    hits = ci_only = 0
    widths = []
    for _ in range(REPS):
        kappa = np.repeat(rng.normal(0.0, sig_kappa, k_classes), n_inst)
        d_class = np.repeat(rng.normal(d_true, sig_dclass, k_classes), n_inst)
        d_inst = rng.normal(0.0, sig_dinst, k_classes * n_inst)
        eps = rng.normal(0.0, sig_inst, k_classes * n_inst)
        base = (b0 + kappa + eps)[:, None]
        p_a = np.clip(base + rng.normal(0.0, sig_cell,
                                        (k_classes * n_inst, n_seeds)), *CLIP)
        p_l = np.clip(base - (d_class + d_inst)[:, None]
                      + rng.normal(0.0, sig_cell,
                                   (k_classes * n_inst, n_seeds)), *CLIP)
        d_c = rng.binomial(1, p_l).mean(axis=1) \
            - rng.binomial(1, p_a).mean(axis=1)
        d_hat, lo, hi, _, dn = _boot(d_c)
        widths.append(hi - lo)
        ci_only += dn
        if not (dn and abs(d_hat) >= mme):
            continue
        loo_ok = True
        for g in range(k_classes):
            sub = np.delete(d_c, np.s_[g * n_inst:(g + 1) * n_inst])
            if not _boot(sub)[4]:
                loo_ok = False
                break
        if loo_ok and _boot(d_c, two_level=True)[4]:
            hits += 1
    return {"ci_only": round(ci_only / REPS, 3),
            "conjunctive_established": round(hits / REPS, 3),
            "width": round(float(np.median(widths)), 3)}


def simulate(b0: float, d_true: float, sig_kappa: float, sig_inst: float,
             sig_cell: float, sig_dclass: float, sig_dinst: float = 0.05,
             k_classes: int = N_CLASSES,
             n_inst: int = N_INST, n_seeds: int = N_SEEDS,
             two_level: bool = False) -> dict:
    """Two arms (A, L); d = lesson effect on recurrence (negative = good);
    rows below use POSITIVE d = recurrence REDUCTION magnitude for
    readability (detect = CI entirely below 0 on the raw scale)."""
    k = k_classes * n_inst
    ci_low = ci_high = 0
    widths = []
    for _ in range(REPS):
        kappa = np.repeat(rng.normal(0.0, sig_kappa, k_classes), n_inst)
        d_class = np.repeat(rng.normal(d_true, sig_dclass, k_classes), n_inst)
        d_inst = rng.normal(0.0, sig_dinst, k)
        eps = rng.normal(0.0, sig_inst, k)
        base = (b0 + kappa + eps)[:, None]
        p_a = np.clip(base
                      + rng.normal(0.0, sig_cell, (k, n_seeds)), *CLIP)
        p_l = np.clip(base - (d_class + d_inst)[:, None]
                      + rng.normal(0.0, sig_cell, (k, n_seeds)), *CLIP)
        d_c = rng.binomial(1, p_l).mean(axis=1) \
            - rng.binomial(1, p_a).mean(axis=1)
        _, lo, hi, up, dn = _boot(d_c, two_level=two_level)
        widths.append(hi - lo)
        ci_low += dn          # benefit direction (L lower than A)
        ci_high += up         # interference direction
    return {"detect_benefit": round(ci_low / REPS, 3),
            "detect_harm": round(ci_high / REPS, 3),
            "width": round(float(np.median(widths)), 3)}


def main() -> None:
    rows: list[dict] = []

    def add(label: str, family: str, **kw) -> None:
        rows.append({"label": label, "family": family, **simulate(**kw)})

    # --- planned geometry K=25x7, conservative row, MDE ladder ---
    add("P1 binomial sanity (no noise), d .20", "primary",
        b0=B0, d_true=0.20, sig_kappa=0, sig_inst=0, sig_cell=0, sig_dclass=0,
        sig_dinst=0)
    add("P2 CI-ONLY conservative, d .20, K25x7", "ci_only", b0=B0, d_true=0.20,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P3 CI-ONLY conservative, d .15, K25x7", "ci_only", b0=B0, d_true=0.15,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P4 CI-ONLY conservative, d .10, K25x7", "ci_only", b0=B0, d_true=0.10,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P5 CI-ONLY conservative, d .25, K25x7", "ci_only", b0=B0, d_true=0.25,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    # --- false positive / harm ---
    add("P6 d 0.0 false-positive (CI-only), K25x7", "ci_only", b0=B0, d_true=0.0,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P7 interference d -0.15 (recurrence UP), K25x7", "primary", b0=B0,
        d_true=-0.15, **CONSERVATIVE, sig_dinst=SIG_DINST)
    # --- base sensitivity, including the pilot-band edges (V-12) ---
    add("P8 base .45, d .15", "ci_only", b0=0.45, d_true=0.15,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P9 base .75, d .15", "ci_only", b0=0.75, d_true=0.15,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P8b band edge base .30, d .15", "ci_only", b0=0.30, d_true=0.15,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P9b band edge base .90, d .15", "ci_only", b0=0.90, d_true=0.15,
        **CONSERVATIVE, sig_dinst=SIG_DINST)
    # --- effect-heterogeneity sensitivity (the R-1 honesty term) ---
    add("P10 no effect heterogeneity (sig_dclass 0), d .15", "ci_only",
        b0=B0, d_true=0.15, sig_kappa=0.15, sig_inst=0.10, sig_cell=0.10,
        sig_dclass=0.0, sig_dinst=0.0)
    add("P11 strong effect heterogeneity (sig_dclass .15), d .15", "ci_only",
        b0=B0, d_true=0.15, sig_kappa=0.15, sig_inst=0.10, sig_cell=0.10,
        sig_dclass=0.15, sig_dinst=SIG_DINST)
    add("P11b strong heterogeneity, d .20 (V-12)", "ci_only",
        b0=B0, d_true=0.20, sig_kappa=0.15, sig_inst=0.10, sig_cell=0.10,
        sig_dclass=0.15, sig_dinst=SIG_DINST)
    # --- LOO approximation: 4 classes x 5 instances = 20 clusters ---
    add("P12 leave-one-class-out approx (K20x7), d .15", "sensitivity", b0=B0,
        d_true=0.15, k_classes=4, **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P13 LOO approx (K20x7), d .20", "sensitivity", b0=B0, d_true=0.20,
        k_classes=4, **CONSERVATIVE, sig_dinst=SIG_DINST)
    # --- two-level bootstrap analysis variant at d .15 / .20 ---
    add("P14 two-level bootstrap, d .15, K25x7", "sensitivity", b0=B0,
        d_true=0.15, **CONSERVATIVE, sig_dinst=SIG_DINST, two_level=True)
    add("P15 two-level bootstrap, d .20, K25x7", "sensitivity", b0=B0,
        d_true=0.20, **CONSERVATIVE, sig_dinst=SIG_DINST, two_level=True)
    # --- THE DECISION RULE (conjunctive, review V-1) ---------------
    # Claim threshold m (the |d-hat| >= m leg) is FIXED; the ladder
    # varies the TRUE effect. MME = the smallest d_true where the
    # conjunctive power >= 0.80 (a threshold equal to d_true would be
    # a median event by construction -> structural ceiling ~0.5).
    for d_true in (0.20, 0.25, 0.30, 0.35):
        rows.append({
            "label": f"C1 conjunctive (claim m .20), d_true {d_true:.2f}",
            "family": "decision_rule",
            **simulate_conjunctive(b0=B0, d_true=d_true, mme=0.20,
                                   **CONSERVATIVE, sig_dinst=SIG_DINST)})
    rows.append({
        "label": "C1e conjunctive (claim m .25), d_true .30 [sensitivity]",
        "family": "decision_rule",
        **simulate_conjunctive(b0=B0, d_true=0.30, mme=0.25,
                               **CONSERVATIVE, sig_dinst=SIG_DINST)})
    rows.append({
        "label": "C2 conjunctive rule, d 0.0 false-positive, K25x7",
        "family": "decision_rule",
        **simulate_conjunctive(b0=B0, d_true=0.0, mme=0.20,
                               **CONSERVATIVE, sig_dinst=SIG_DINST)})
    rows.append({
        "label": "C3 conjunctive (claim m .20), d .25, no effect het.",
        "family": "decision_rule",
        **simulate_conjunctive(b0=B0, d_true=0.25, mme=0.20,
                               sig_kappa=0.15, sig_inst=0.10, sig_cell=0.10,
                               sig_dclass=0.0, sig_dinst=0.0)})

    # --- rejected geometries, for the record ---
    add("P16 rev-1 geometry (5 classes x 3 inst = K15x7), d .20", "rejected",
        b0=B0, d_true=0.20, n_inst=3, **CONSERVATIVE, sig_dinst=SIG_DINST)
    add("P17 seed cut n=4, K25x4, d .20 [record]", "rejected", b0=B0,
        d_true=0.20, n_seeds=4, **CONSERVATIVE, sig_dinst=SIG_DINST)

    out = {
        "kind": "cont006-plt-power-calc",
        "endpoint": "recurrence of target failure class, L - A; cluster = "
                    "(class, instance); K = 5 classes x 5 instances = 25 x 7 "
                    "seeds; binary episode outcomes with trigger-predicate "
                    "eligibility (R-2); paired cluster percentile bootstrap "
                    "(BOOT 4000; the frozen analyzer will use 10k — power "
                    "approximation declared); MANDATORY pre-registered "
                    "sensitivity: leave-one-class-out (all 5 drops, computed "
                    "inside each replication of the decision rule) + "
                    "two-level class->instance bootstrap; class-level "
                    "generalization NOT inferred; scope = the 5 tested "
                    "classes",
        "model": "kappa[class] baseline (paired, cancels); delta_class ~ "
                 "N(d_true, sig_dclass) EFFECT heterogeneity across classes "
                 "(does NOT cancel); d_inst ~ N(0, sig_dinst) instance-level "
                 "effect heterogeneity (V-12); eps[instance] baseline "
                 "(paired, cancels); eta[cluster,arm,seed]; clip [0.02,0.98]; "
                 "planning base A-recurrence 0.60 (pilot verifies band "
                 "[0.3,0.9] per class); conservative row sig_kappa .15 / "
                 "sig_inst .10 / sig_cell .10 / sig_dclass .10 / sig_dinst "
                 ".05",
        "mme_rule": "DECISION RULE (conjunctive, review V-1): established = "
                    "CI95 entirely below 0 AND point |d| >= MME AND every "
                    "leave-one-class-out drop keeps CI below 0 AND the "
                    "two-level bootstrap CI below 0 — all inside one "
                    "replication. MME = the smallest 0.05-step effect where "
                    "the CONJUNCTIVE power (C-rows) >= 0.80 on the "
                    "conservative row at K25x7. CI-only rows (P-family) are "
                    "reported for reference and must NOT be quoted as the "
                    "power of the decision. Effects below MME are NOT "
                    "claimable; the sensitivity terms exist to price the "
                    "class structure honestly",
        "seeds": {"sim_rng": 20261011, "REPS": REPS, "BOOT": BOOT},
        "results": rows,
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote", OUT)
    for r in rows:
        if "conjunctive_established" in r:
            print(f"{r['label']:58s} conj={r['conjunctive_established']:.3f} "
                  f"ci_only={r['ci_only']:.3f} width={r['width']:.3f}")
        else:
            print(f"{r['label']:58s} benefit={r['detect_benefit']:.3f} "
                  f"harm={r['detect_harm']:.3f} width={r['width']:.3f}")


if __name__ == "__main__":
    main()
