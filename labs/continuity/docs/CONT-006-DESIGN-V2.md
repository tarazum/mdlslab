# CONT-006 DESIGN V2 — the rethink addendum (owner-directed 2026-10-09)

Status: DESIGN AMENDMENT for the V2 pre-registration. Basis: the CN-012
invalidation audit + TWO independent reviews (docs/REVIEW-FABLE-CONT006.md
F-1..F-3, C.1–C.6, D.3; docs/REVIEW-CONT006-CN012-RERUN.md RC-1..RC-6,
Stage A/B) and the owner decisions of 2026-10-09 (rethink = yes; fresh
suite v3m; hosted-model replication deferred to the end). This addendum
AMENDS docs/CONT-006-DESIGN.md and docs/EVALUATION-PREP-CONT006.md; the
V1 documents stay as the historical record of the invalidated chain.

## What the invalid run actually was

An accidental lessons-WITHOUT-episodic-memory ablation (≈ the prereg's
critical test 1): every R-arm ran memoryless (CN-012 — the runner's append
tuple omitted the R-arms; 0 memory.append events across all v3l traces).
Its verdict "no confirmatory difference" (Δ = 0.019) is INVALID as a test
of the registered arms and is preserved as an unregistered exploratory
datapoint. What it DID establish (channel properties, memory-independent):
the lesson channel is live and strong (format-miss 0.162 → 0.0095/0.029,
replicated twice); lessons alone teach reply DISCIPLINE, not semantic
correctness; an active poisoned lesson is quoted verbatim and followed
(RBAD parroting — the arc's safety headline).

## V2 changes (each traced to its review)

1. **Fresh suite v3m** (owner decision; Fable C.6): ids x-7xxx, seeds
   {7001..7007}, fresh worlds, composition identical to v3l (15 TR + 4 VAL
   + GC×3, every taxonomy class ≥ 2 primary clusters), mechanics inherited
   from the frozen suites only. Validator extended (`--suite v3m`): PASS
   19/19 + regressions v3..v3l PASS ×6. v3l stays committed as the
   invalidated chain's surface (and as the calibration reference for what
   NOT to reuse).
2. **Memory discipline** (CN-012/F-1/F-2/RC-1/RC-2 — all folded): a single
   module-level MEMORY_ARMS source of truth; the memory guard derives from
   it; `experiments/cont006/combined_channel_smoke.py` is a permanent
   regression test (every memory arm on a REAL multi-session scenario;
   asserts appends, non-empty injections, lesson renders, R0/R2/R3
   IDENTICAL episodic refs, context fit — PASS ×5); **a live-telemetry
   gate reads every trace BEFORE any analyzer** (`live_telemetry_gate.py`
   — T1 appends, T2 refs-resolve-to-earlier-appends, T3 lesson renders,
   T4 context clip, T5 summary cross-check; verified FAIL-CLOSED on the
   invalid run: 20/20 traces flagged).
3. **Multi-trace worker bundles** (Fable C.3 — FIX-A/B become design): 8
   bundles grouped by family/sub-type across the whole corpus (12
   scenario-runs each, fails-first, deterministic order), ONE 5-part ref
   format pinned by a worked example, cross-trace citation natural (3–12
   distinct traces per bundle); the prompt explicitly prefers SUBSTANCE
   lessons over formatting. Pre-computed artifact:
   experiments/cont006/worker_v2_bundles.json. The worker pass re-runs on
   the same corpus (its input) under this design after the review chain.
4. **FP-6 store cap** (Fable C.4): the lesson pipeline accepts at most ONE
   format-discipline lesson per store (FP-6 is cross-cutting by taxonomy;
   three near-copies crowded retrieval in the invalid run — 265/265/228
   injections vs 37 for the supersession lesson). Class-coverage telemetry
   is a declared store report. No forced quotas on other classes (an
   honest worker negative stays honest).
5. **MME back to 0.20, band = caveat-only** (Fable C.2): the 0.333
   re-derivation was a small-n artifact of the invalid pilot (12 gc
   probes). V2 power artifact: power_calc_cont006_v2.py (seed 20261009) —
   conservative row 0.871 at MME 0.20; the empirical band is REPORTED next
   to family numbers and never moves the MME (paired-Δ arm-symmetric
   reading).
6. **Per-family headroom gates** (Fable C.1 — cycle-2 discipline
   restored): the calibration pilot requires EVERY TR family mean in
   (0.15, 0.85) for BOTH R0 and R2; out of band → halt & author a NEW
   suite (never a v3m edit).
7. **Anchor-divergence halt** (Fable F-3 — the cheapest CN-012-class
   detector): |measured R0 base − 0.525 anchor| > 0.15 at the calibration
   pilot or Phase V → HALT & INVESTIGATE (never a parameter move; the
   invalid run printed this signal — 0.267 vs 0.525 — with no criterion
   attached).
8. **Arm-equivalence audit** (co-owner RC-3):
   experiments/cont006/arm_equivalence_audit.py emits the mechanical
   artifact (single-source membership, provider contract, retrieval/
   renderer constants, runner source checks, rendering identity); PASS.
9. **Calibration pilot** (Fable D.4): R0+R2 × seeds {7001, 7002} on v3m
   WITH memory, BEFORE freeze-sign-off: verifies family bands, anchor,
   live invariants; in-band → the seeds are part of the final dataset
   (single freeze; CONT-002 pattern). Out-of-band → fresh suite, owner
   consulted.
10. **Arms**: R0/R1/R2/R3 unchanged in definition (R1 STAYS — Fable C.5:
    with memory alive, the parroting-replication expectation R1 ≤ R0 is
    finally testable). Counterfactual BAD/GOLD-TRIV texts reused with a
    mandatory 4-gram re-check against rendered v3m. R3 gold lessons
    reused (blind protocol intact — the author never saw v3l or v3m);
    the FP-6 cap applies uniformly (8 → 7 lessons).
11. **Stage B (hosted models)** deferred to the end (owner) — a separate
    external-validity experiment after Stage A concludes, per the
    co-owner's review.

## Chain (V2)

RC-6 review chain → owner accept → freeze V2 → worker v2 pass (multi-trace
bundles; FP-6 cap + class telemetry) → R3 store recapped (classes + cap,
uniform with R2) → contamination gate → calibration pilot (R0+R2 × 2 seeds
on v3m with memory, live gates; needs the worker v2 store — hence AFTER the
worker pass; before the store freeze and any transfer phase) → Phase V
(activation; anchor-checked) → store freeze → Phase P pilot (incl.
BAD/GOLD-TRIV on v3m; live gate before analysis) → pilot-gate checkpoint →
Phase C → live gate → frozen analyzer → verdict.
Every phase's traces pass the live-telemetry gate before anything reads
them. (RC-6 self-review fold: this chain previously placed the calibration
pilot BEFORE the worker pass — impossible, R2 needs the worker store; the
order above is canonical and matches prereg A.3/A.6.)
