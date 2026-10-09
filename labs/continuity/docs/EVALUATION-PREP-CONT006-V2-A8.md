# EVALUATION-PREP-CONT006-V2-A8 — the v3n amendment (DRAFT)

Status: **DRAFT for the next review pass + owner acceptance.** Amends
docs/EVALUATION-PREP-CONT006-V2.md (amendments A.1–A.7, owner-accepted
2026-10-09) with exactly ONE change: the behavioral suite. Everything else
in A.1–A.7 stays binding as accepted. Basis: the v3m calibration
STOP-OUT-OF-BAND record
(results/CONT-006-CAL/cont006-cal-20261010-000940/calibration-verdict.json),
the diagnostic docs/DIAGNOSTIC-CONT006-V2-CR.md, and the owner decision
"ок по дефолтах" (ROADMAP, recorded 2026-10-10: v3n authoring authorized;
cr diagnostic first; the arc continues). Behavioral inference on v3n
remains NEVER-AUTONOMOUS until the owner accepts this amendment.

## A.8 — Suite: fixtures/v3n (replaces v3m for every behavioral phase)

1. `fixtures/v3n` (builder `build_v3n.py`, deterministic; validator
   `--suite v3n` PASS 20/20 incl. V18 world-freshness vs ALL prior suites
   including v3m, verified BOTH ways; regressions v3..v3m PASS ×7;
   fixture-validation-v3n.json committed; suite sha256 9201d710…).
   Composition identical to v3m (15 TR + 4 VAL cr-8005/cu-8105/rt-8204/
   dx-8403 + GC×3; ids x-8xxx; seeds {8001..8007} pre-declared).
2. Difficulty re-aim (design-time, from the CALIBRATION evidence — the
   mechanical family bands, not post-hoc tuning of v3m texts):
   cr EASIER (probe reports carry the exact head-noun phrase of one card
   line — lexically transparent mapping; target band mid-scale at R0);
   dx HARDER (the lure is re-confirmed in s2 while the expected code is
   stated once — salience competition; transposition-confusable code
   pairs); dr HARDER (two other entities' codes of the same kind logged in
   s2 — interference binding; lure_value = the first interference code);
   cu/rt/gc mechanics unchanged (cu 0.5 and rt 0.33 were in-band).
   Out of band at the v3n calibration -> a NEW suite again (never a v3n
   edit); the A.3 bands and the 0.525 anchor are unchanged.
   Reading note (K-4 of the 2026-10-10 diff-pass review, carried): 3/35
   rendered cr probe reports carry modifier-position stems from other card
   lines (e.g. "before the pour" ~ trap 'pouring' in cr-8001 seed 8007);
   the head-noun mapping claim holds as worded (the exact head noun of
   exactly one card line is always present) — these modifiers are minor
   noise, reported here so the cr family numbers read honestly.
3. Store reuse (declared): the R2 store (W2 worker-v2 output, committed)
   and the R3 store (r3-store-v2.json recap artifact) are SUITE-INDEPENDENT
   — the worker pass ran over the frozen CONT-005-C2 corpus (v3i/v3j
   traces), never over v3m/v3n. The rerun chain REUSES both stores
   byte-identically; NO new worker inference. The contamination gate
   re-runs against every rendered v3n turn text (pre-checked: counterfactual
   lessons 0 shared 4-grams; the W2/R3 store scan re-runs at execution).
4. Execution chain (A.6 order unchanged, v3m→v3n): re-freeze (SUITE_DIR →
   fixtures/v3n; ALL_SEEDS/PILOT_SEEDS → {8001..8007}/{8001,8002}; TR/VAL/
   GC ids per v3n; CF_SUBSET → positional equivalents [cr-8001, cr-8003,
   rt-8201, rt-8202, cu-8101, dx-8401, dr-8301, gc-8501]; freeze manifest
   re-emit with the v3n digests + this amendment) → contamination gate
   (stores vs v3n) → calibration pilot (A.3 unchanged: R0+R2 × {8001,8002}
   over the full v3n set, memory ON; the v3m CAL cells are NOT part of the
   v3n dataset — v3m is the stopped chain's record) → Phase V → P → C per
   A.6/A.7. MME 0.20 absolute and the power artifact are unchanged (the
   K15×7 design and the b0 0.525 anchor do not depend on suite texts).
5. Run-record additions: the header carries the v3m calibration STOP note
   (family bands dx/dr ceiling, cr floor; verdict artifact path) and the
   corpus-coverage caveat from DIAGNOSTIC-CONT006-V2-CR (worker lessons
   are corpus-shaped "answer what the instruction states" prescriptions;
   cr clusters must be baseline-solvable at R0 so the lessons' pull is
   measurable rather than floor-masked — the R2−R0 contrast on cr reads
   as transfer-vs-suppression of memory-based inference).
6. Review routing: Fable diff-pass is sufficient (its closing note on the
   V2 review; a full re-review is not required for a suite swap with
   unchanged machinery); the owner gate follows. The V2 freeze manifest
   (frozen-config-cont006-v2.json) stays untouched as the stopped chain's
   record; the re-freeze emits a new manifest.

## What A.8 does NOT change

Arms R0/R1/R2/R3 and definitions; the primary endpoint Δ = S(R2) − S(R0)
over 15 TR clusters; the four-branch decision rule; §7.1 evidence
validation; the FP-6 cap; the activation rule (+0.05, fail-closed); the
counterfactual lesson texts; MME 0.20 (band caveat-only); the A.2 memory
discipline and live-telemetry gating; the A.3 band/anchor numbers; Stage B
deferral; never-autonomous.
