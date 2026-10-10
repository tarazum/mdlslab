# RESULTS — CONT-006 DELIVERY-DIAG (step 1): corrected delivery is CONSISTENT WITH partial recovery, concentrated entirely in the gold arm; the worker arm shows none; a residual vs memory-only remains with competing explanations

Diagnostic per docs/PREREG-CONT006-DELIVERY-DIAG.md (pre-registered
BEFORE inference; freeze 118 digests committed at 2a24ce6; run root
results/CONT-006-DELIVERY-DIAG/cont006-dd-20261010-183404; 192/192 calls,
0 headroom violations, model granite-code:8b 36c3c3b9683b, temp 0.0,
seed=cell seed, num_ctx 4096, num_predict 256). The registered V2A
verdict and all committed run artifacts are untouched (non-goals held).
Independent review (GPT-6 Astra, docs/REVIEW-ASTRA-CONT006-DELIVERY-DIAG.md):
all 192 replies + 84 recorded baselines rescored with ZERO discrepancies;
reconstruction independently re-executed via the frozen runner; the
conclusions below are the post-fold (narrower) reading — the review
rejected the stronger causal wording of the first draft.

## Headline (pre-registered predictions vs outcomes)

| prediction | outcome | verdict |
|---|---|---|
| P1 corrected ≥ as-executed on harm clusters | b 40/56 vs a 36/56 (Δ +0.071; replay score-disagreement rate 1/24 = 0.042) | DIRECTIONAL + above the empirical disagreement rate; meaningful band ≥42/56 NOT met → CONSISTENT WITH PARTIAL RECOVERY (b−a exploratory CI [−0.125, +0.196] still straddles 0) |
| P1a R3 harm recovery ≥ 21/28 | b(R3) 21/28 vs a(R3) 17/28 | MET (+4) |
| P2 rt-8204 gains retained (≥ 7/14) | b 10/14 | MET (and b ≫ c 3/14: the gain is associated with the lesson block on identical histories — see caveats) |
| P3 b < c would implicate content/capacity | b 40/56 < c 47/56 (Δ −0.125; exploratory cluster bootstrap CI [−0.232, −0.071], excludes 0 down) | FIRED — but see §Interpretation: content, conditional-application capacity, and GENERIC PROMPT INTERFERENCE remain competing explanations |
| P4 replay noise floor | byte-exact 20/24; whitespace-trimmed 23/24; pass/fail score agreement 23/24 (1 flip: R3/seed-8001/dx-8402 'Acknowledge.'→'M17.') | reconstruction validated; the frozen noise implementation reads SCORE disagreement (1/24) |

Both pre-registered decision branches fired simultaneously; "MIXED" is
the reasonable synthesis of that overlap (the prereg did not fix a
precedence between the P1+P2 and P3 branches — review note 5).

## The decomposition that matters (per arm, harm clusters, /28)

| arm | a (executed) | b (corrected) | c (no lessons) | reading |
|---|---|---|---|---|
| R2 (worker store) | 19 | 19 | 25 | NO recovery under corrected delivery; a 6-probe deficit vs memory-only remains |
| R3 (gold store) | 17 | 21 | 22 | recovery +4 (band met); corrected delivery reaches memory-only PARITY (deficit 1, below the disagreement rate) |
| pooled | 36 | 40 | 47 | all net recovery is R3; the pooled b<c residual is predominantly R2 |

Per cluster (14 = 7 seeds × R2+R3):

| cluster | R0 ref | a | b | c | reading |
|---|---|---|---|---|---|
| cr-8003 | 7/7 | 10/14 | 7/14 | 11/14 | corrected delivery does NOT recover here — replies degenerate into card-echoing, list-echo, 'Acknowledge.' deflection. NOTE (review): G003's text SUPPORTS this task (derive from the card); card-echoing is UNSUCCESSFUL APPLICATION, not evidence the prescription is wrong |
| cr-8004 | 4/7 | 5/14 | 7/14 | 8/14 | partial recovery, residual −1 vs c |
| dx-8401 | 7/7 | 10/14 | 13/14 | 14/14 | targeted delivery recovers most of the executed harm (R3: 4/7 → 7/7); R3 dx delivered G006 AND G007 (not the binding lesson alone); residual −1 |
| dx-8402 | 7/7 | 11/14 | 13/14 | 14/14 | same as dx-8401 |
| rt-8203 | 0/7 | 1/14 | 1/14 | 1/14 | floor in every variant — the underspecified probe (defect 5, LINEN_CARD never supplied) is uninformative for delivery |
| rt-8204 | 1/7 | 12/14 | 10/14 | 3/14 | lesson-block-ASSOCIATED improvement on fixed histories; NOT validated rule transfer (the probe remains partly underspecified — defect 5) |

Error modes on the harm clusters: b = 6 wrong-label + 10 format-miss;
c = 5 + 4 — the format-degeneration signature persists under corrected
delivery. Verbatim lesson echo under (b): 0/84 (no parroting; the
interference is behavioral, not quoting). Max prompt tokens 972
(headroom safe); one generation hit the 256 cap (an a-replay card-echo).

## Interpretation (warranted, post-review — the narrower reading)

1. **The executed delivery was defective and part of the harm recovers
   when it is fixed — consistent with partial recovery, not a confirmed
   material decomposition.** The pooled improvement (+4) is entirely
   carried by the gold arm (17→21), which reaches memory-only parity;
   the meaningful band (≥42/56) was not met and the exploratory CI
   straddles 0. The registered directional reading stands; quantitative
   attribution ("delivery = half the problem") is NOT supported.
2. **The worker store (R2) shows no delivery-side recovery at all**
   (19→19 vs c 25): with these worker-authored texts, correcting
   WHERE/WHEN/HOW lessons arrive did not help the harm clusters. The
   pooled b<c residual (−0.125) is predominantly R2.
3. **The residual vs memory-only has COMPETING explanations this design
   cannot separate** (review MAJOR-1): variant b jointly changes
   selection, position, wording, length, and lesson combinations; there
   is no matched neutral-block control, placement control, or
   per-lesson ablation. Lesson content, conditional-application
   capacity, and generic prompt interference all remain live. The
   R2-vs-R3 asymmetry (R2 delivers fewer, shorter lessons and does
   WORSE) weakens a pure length/interference story but does not close
   it.
4. **The rt-8204 gain is associated with the lesson block on identical
   histories** (b 10/14 vs c 3/14) and survives corrected delivery — a
   behavioral lesson effect, not validated transfer of the intended
   supplied rule (underspecification caveat, defect 5).
5. **Annotation sensitivity (review MAJOR-2, disagreements recorded,
   original annotation preserved as the executed treatment)**: under
   the reviewer's stricter literal readings, G003/W005 would be
   WITHHELD at rt-8203/8204 (the linen card never defines the queried
   folding/collection family) and W006 at dx is defensible-but-literal-
   borderline. Notably, under those readings the rt-8204 gain under (b)
   came from lessons a strict annotator would not deliver — the
   gain's provenance is the lesson block, its specific correctness
   less certain.

## Limitations (declared)

- Probe-level replay design: variants (b)/(c) hold the RECORDED lesson-run
  histories fixed; (c) is therefore "no lesson block given a lesson-shaped
  history", not a full memory-only re-run (that is R0's recorded role,
  25/28). History contamination is inherent and small here (c 47/56 vs
  R0 25/28) but nonzero.
- One annotator (the implementer) produced the applicability table
  pre-inference; judgment calls were flagged and the independent review
  disagreed on 6 of 84 cell-level calls (recorded in the review doc).
- 56-cell pooled harm contrasts sit at the edge of resolution; the
  pre-registered directional + empirical-disagreement reading is the
  registered interpretation, the bootstrap is context.
- rt-8203 contributes nothing (floor) — the underspecification defect
  re-confirms that any future transfer claim needs the rt mappings
  actually supplied (step 2's new-suite requirement).
- P4's "exact-content" wording was ambiguous in the prereg; the frozen
  implementation reads SCORE disagreement (declared here, not silently
  reinterpreted — review MINOR-4).

## Next-step implication (owner gate decides)

The open question is now a CONTENT question with an unresolved
interference confound — exactly what step 3 (capacity × content,
corrected delivery held fixed, lesson-minus-baseline INTERACTION per
model) isolates, PROVIDED it adds: a matched neutral-block control
(same length/position, non-lesson text) to separate content failure
from generic prompt interference, an explicit old-content × new-content
× model crossing, and the repaired rt fixtures + faithful worker
evidence from step 2 as common prerequisites (folding step 2 in).
Recommended unchanged from the first draft, now with the control.

## Post-freeze note (PREREG-REQUIREMENTS-V2 §2 declaration — corrected
per review MINOR-5)

One analysis-path fix AFTER the run, BEFORE trusting the results file:
the exploratory bootstrap compared variant c against itself (always 0),
the P3 reading string could mislead for compound outcomes, and the
per-cluster R0-reference fields were empty. All three fixed in
delivery_v2_diagnostic.py; calls.jsonl, gates and pins untouched; the
fix rides THIS close-out commit (at review time it was still uncommitted
— accurately flagged by the reviewer; the frozen manifest at 2a24ce6
preserves the pre-inference module bytes, and 117/118 frozen entries
byte-match the post-fix checkout with the module as the sole declared
mismatch).
