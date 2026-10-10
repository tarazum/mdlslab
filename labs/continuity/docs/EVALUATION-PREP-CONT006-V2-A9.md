# EVALUATION-PREP-CONT006-V2-A9 — the dx/dr band-exemption amendment

Status: **OWNER-ACCEPTED 2026-10-10** (ROADMAP "Owner decisions — recorded
2026-10-10 (CONT-006 A.9 ACCEPTED…)"; owner chat: "1. ок, дефолт").
Amends EVALUATION-PREP-CONT006-V2.md A.3 (the calibration checks) with
exactly ONE change; everything else in A.1–A.8 stays binding as accepted.

## A.9 — Calibration family bands: cr/cu/rt gated; dx/dr exempt + caveat

1. The per-family headroom criterion (A.3.1) applies to the families
   cr, cu, rt ONLY: every one of them must have mean pass strictly inside
   (0.15, 0.85) for BOTH R0 and R2.
2. dx and dr are EXEMPT from the band. Their family means are REPORTED
   in the verdict record with the standing ceiling caveat: at a 1.0
   baseline, IMPROVEMENT is unmeasurable in those families (no headroom
   above), while HARM remains fully measurable (any drop from ceiling
   registers). The exemption is declared, not silent: the verdict JSON
   carries the caveat and the family means either way.
3. Basis (recorded, not a post-hoc rationalization): two independent
   suites (v3m, v3n) with different difficulty mechanics (lure salience,
   same-kind interference) both placed R0 dx/dr at a structural ceiling
   for the granite+memory pair at the registered task scale (n = 4
   probes/family at calibration); the v3n levers demonstrably moved the
   LESSON arm (R2 dx 0.75) but not the R0 baseline.
4. Consequences for the primary endpoint (declared reading): the Δ =
   S(R2) − S(R0) improvement detection leans on the 11/15 in-band
   clusters (cr/cu/rt + dx-R2 headroom); power at K11×7 is ~0.79–0.80 on
   the conservative row (power-results-cont006-v2.json R4 K12×7 = 0.79
   brackets it) — retained. A "no confirmatory difference" verdict on
   this surface therefore does NOT exclude a recall-type-specific lesson
   benefit (ceiling-masked in dx/dr); it answers the registered mixed-
   surface question. Harm (negative Δ) is measurable everywhere.
5. Everything else in A.3 is unchanged: the anchor |R0 pooled TR pass −
   0.525| ≤ 0.15, the live-telemetry gate BEFORE the analyzer, the
   invalid-share < 0.30 per arm, and the consequence rule (out of band
   on the GATED families → STOP; a NEW suite only after the owner).
6. Implementation discipline: analyze_calibration.py is amended BEFORE
   any further behavioral inference; the v3n calibration verdict is
   RECOMPUTED under A.9 from the SAME committed run root (zero repeated
   inference; the A.3 STOP verdict is preserved as
   calibration-verdict-a3-stop.json in the run root and in git history);
   the execution freeze is re-emitted (frozen-config-cont006-v3a.json)
   with this document and the amended analyzer digested, preflight PASS
   required before Phase V. The calibration cells (R0/R2 × 8001/8002)
   are PART OF THE FINAL DATASET (single freeze; unchanged).

## What A.9 does NOT change

The pilot-gate criteria (including R0 pooled-TR headroom ≤ 0.75); the
confirmatory analysis and the four-branch decision rule; MME 0.20
absolute (band caveat-only); the arms, stores, activation rule,
counterfactual texts; A.2 memory discipline and gating; never-autonomous
(the standing autonomous-completion authorization and its binding stop
branches govern the continuation).
