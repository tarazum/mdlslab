# Owner Brief — CONT-005 confirmatory run (2026-10-05)

Per `docs/OWNER-BRIEF-TEMPLATE.md`. Run of record:
`results/CONT-005-CONFIRMATORY/cont005-confirmatory-20261005-123917/` (commit 859e6fc).
This file is the durable copy of the chat brief (bridge reliability practice).

## VERDICT

**No confirmatory difference established** (frozen protocol, exact wording):
T0−T2 = **−0.100**, 95% CI [−0.283, 0.000], MME 0.25 — the CI includes 0.
Caveat: the primary effect does not clear the guessing band (max band 0.333).

## DECISIONS FOR YOU

1. **Accept the confirmatory result?** — default: **yes**
2. **Accept the analysis-script hotfix** (secondary-block crash BEFORE any results were read; primary logic untouched; recorded in `frozen-config-v2.json` post_freeze_hotfixes, M7 c679547 pattern)? — default: **yes**
3. **Next lab step** — default: **a small focused "anchoring-by-flagging" study** (see the strongest new signal below) or CONT-005 closure

## WHAT RAN

25/25 arm-seeds completed cleanly (T0, T2, A, T1, T3 x seeds 1001–1005 over the
held-out suite v3h, fresh worlds, ~150 min GPU, zero retries). Gate-V2 (Fable,
non-executor) GO before launch; frozen analysis after completion.

## NUMBERS (the six that matter)

- Primary: **T0−T2 = −0.100**, CI [−0.283, 0.000] — not established; direction
  REVERSED vs the pilot (+0.36): the pilot effect did not replicate
- **T2/T3 repeat the scripted/superseded trap 5/60 each; A/T0/T1: 0** — the
  cleanest new signal in the lab ("anchoring-by-flagging" hypothesis: trust
  annotations may raise trap salience)
- Overall: A 0.208 (guessing level, equals pilot) · T0 0.417 · T1 0.450 · T2 0.350 · T3 0.450
- Memory itself is real: CU pass 0.00 (A) → ~1.0 (T0) on 3 of 4 clusters
- The DR fix from the pilot worked: delayed_recall 0.0 → 0.60–0.67 across memory arms
- T2 failed cu-2004 in all 5 seeds (T0 perfect) — that single cluster carries
  most of the delta

## NEGATIVES & DEVIATIONS

- Post-freeze hotfix of the analysis script (crash in the SECONDARY
  t1_t3_exploratory block before any output was written; flattening fix; digests
  recorded; flagged for your acceptance)
- The pilot's T2 advantage was a design-loop artifact — Fable named this exact
  risk (CU ceiling, regression to the mean) in PR-REVIEW-v2 before the run
- Guess-band caveat fired (primary |delta| < 2 × max band)

## NOT CLAIMED

- This is NOT "trust hierarchies don't work": it is "not confirmed on THIS
  endpoint, with one outlier cluster (cu-2004) carrying the reversal; without it
  the delta is ≈ 0"
- T1 ≈ T3 > T2 overall is exploratory (annotations may help, resolution/policy
  may hurt) — a next-cycle design input, not a claim
- No external-validity claims beyond granite-code:8b @ temp 0.0 on synthetic v3h

## CORRECTION ADDENDUM (2026-10-05, after the Fable audit — supersedes parts of NUMBERS above)

The Fable post-result audit (`docs/REVIEW-FABLE-RESULTS.md`, owner-requested
second look) verified the primary verdict independently (exact recount from
traces) and CORRECTED one claim of this brief:

- ~~"T2/T3 trap-repeats 5/60 vs 0 elsewhere — the cleanest new signal"~~ —
  **retracted as stated**: all five repeats are one cluster (cu-2004), and the
  "zero elsewhere" was a strict-normalization artifact (arm A repeated the
  same trap in quotes; T0 repeated trap words inside sentences). The
  label-level re-analysis (same traces, zero GPU): A 25/90 > T0 15/90 >
  T2 = T3 10/90 > **T1 0/90** — annotations-only is the only zero-repeat arm.
- The verdict is STRONGER than it sounds: the CI upper bound (0.000) excludes
  the pre-registered effect >= MME 0.25. Not "we failed to confirm" but "the
  data rule out the claimed effect at this scale."
- Added caveats: temp-0 seeds are degenerate (identical prompts -> identical
  answers; effective n ~ 12 binary observations); one cluster (cu-2004)
  carries 83% of the delta; T2/T3 answers sometimes echo render markup
  (invalid-format errors), and supersession has no typed sources to act on in
  numeric CU conflicts.

Updated decision-3 default: accept + accept the hotfix; next cycle = fix the
T2/T3 render leakage and numeric-conflict supersession, vary content across
seeds, and test the T1-annotations finding properly.

## DIG DEEPER

`results/CONT-005-CONFIRMATORY/cont005-confirmatory-20261005-123917/results-summary.json` ·
`docs/GATE-V2.md` · `docs/PR-REVIEW-v2.md` · `docs/EVALUATION-PREP-v2.md` · `LOG.md` (2026-10-05 tail)

**Recommendation (defaults):** accept all; next cycle = the small focused
trap-salience study — it is cheap, zero new infrastructure, and tests the
sharpest unexplained observation the lab has produced.
