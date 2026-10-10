# RESULTS — CONT-006 CAPACITY-×-CONTENT (step 3, post-review): a strong model-vs-8B contrast in probe-time block response; per-condition interference outcomes; one content-specific cluster; the rt-8204 gain is filler-associated

Diagnostic per docs/PREREG-CONT006-CAPACITY-CONTENT.md (pre-registered +
frozen BEFORE consumer inference: faithful bundles 1b69ff2, prereg+freeze
0d49be2, 129 digests; run root results/CONT-006-CAPACITY/
cont006-cap-20261010-204517: 696 new + 168 reused = 864/864 records, 0
headroom violations; G8B granite-code:8b 36c3c3b9683b, Q35
qwen36-35b-a3b:mdlslab 8a0fd5da454e, identical pins; noise floors: G8B
carries step-1's 1/24, Q35 duplicates agree 24/24 in score AND text).
Independent review (docs/REVIEW-ASTRA-CONT006-CAPACITY-CONTENT.md):
every number independently reproduced (pools, per-cluster, error modes,
bootstrap, freeze/chronology, W3 regeneration, all 168 reuse hashes); the
CONCLUSIONS were narrowed accordingly — this is the post-fold version.

## Headline: harm-cluster pools (56 cells per condition-model)

| condition | G8B | Q35 |
|---|---|---|
| NONE | 47/56 | 56/56 |
| NEUTRAL (registered filler control) | 36/56 (−11) | 56/56 (0) |
| OLDW (old worker store) | 39/56 (−8) | 56/56 (0) |
| OLDG (old gold store) | 40/56 (−7) | 56/56 (0) |
| NEWF (faithful-evidence W3 store) | 35/56 (−12) | 56/56 (0) |

Q35 scores 56/56 in EVERY condition — it solves the harm clusters cold
and is unaffected by any of the tested blocks. G8B loses 7–12 probes to
every block, filler included.

## Pre-registered endpoints vs outcomes (as registered, then decomposed)

- **E1**: I_OLDW +8, I_OLDG +7, I_NEWF +12 — all ≥ the +4 band. READING
  (bounded, per review): the interaction is mechanically the NEGATIVE
  G8B block effect at a Q35 ceiling (Q35 lesson-minus-NONE is exactly 0
  everywhere); it is an observed CONTRAST between these two models'
  responses to the tested blocks — not identification of
  conditional-application capacity, model size, or stronger-model lesson
  benefit. The exploratory I_OLDG bootstrap is +0.125, CI [0.0, 0.375]
  (interval includes 0 at the boundary). Family/tokenizer/instruction-
  tuning confounds are bundled with the model choice (declared).
- **E2 (per the registered per-condition rule, gap ≤ 3 = reproduced)**:
  OLDW reproduced (|−11−(−8)| = 3); NEWF reproduced (|−11−(−12)| = 1);
  OLDG mixed/indeterminate (|−11−(−7)| = 4). The registered rule FIRED
  PER-CONDITION — there is no single "the deficit is generic" outcome.
  Cell-level decomposition (exploratory): ALL seven of OLDG's net losses
  sit at cr-8003 (content-concentrated), while NEUTRAL's eleven losses
  sit mostly elsewhere — only 2 of OLDG's 9 baseline-pass→fail cells
  overlap NEUTRAL's losses. The error-mode shifts also DIFFER (vs NONE:
  NEUTRAL adds +10 wrong-label / +1 format-miss; OLDG adds +1 wrong-label
  / +6 format-miss) — similar aggregate sizes, distinct mechanisms.
- **E3**: G8B NEWF −12 vs OLDW −8 — this W3 store did not benefit G8B.
  Q35 vacuous at ceiling (0 vs 0). See the addenda: E3 compares two
  STORE PIPELINES, not evidence fidelity alone.
- **E4 (non-primary)**: Q35 NONE 56/56 vs G8B NONE 47/56; Q35 solves
  rt-8203 at 12/14 (G8B floor 1/14 in every condition) — Q35's only
  rt-8203 failures are seed-8006 × every condition (a systematic
  'collection' answer for that seed's different-family item: the
  underspecification defect, model-independent).

## Per-cluster table (G8B; Q35 is 14/14 everywhere except rt-8203 12/14, rt-8204 12/14 — all conditions)

| cluster | NONE | NEUTRAL | OLDW | OLDG | NEWF | reading |
|---|---|---|---|---|---|---|
| cr-8003 | 11/14 | 10/14 (−1) | 7/14 (−4) | 4/14 (−7) | 3/14 (−8) | LESSON-ASSOCIATED harm: filler costs −1, lesson texts cost −4…−8 (failure mode: card-echo / 'Acknowledge.' / 'moulding') — the content-specific cluster |
| cr-8004 | 8/14 | 5/14 (−3) | 8/14 (0) | 8/14 (0) | 4/14 (−4) | mixed: filler −3, NEWF −4, old lessons 0 |
| dx-8401 | 14/14 | 11/14 | 12/14 | 14/14 | 14/14 | filler-associated losses; OLDG 0 |
| dx-8402 | 14/14 | 10/14 | 12/14 | 14/14 | 14/14 | same |
| rt-8203 | 1/14 | 1/14 | 1/14 | 1/14 | 1/14 | G8B floor in every condition (underspecified probe) |
| rt-8204 | 3/14 | 12/14 | 13/14 | 7/14 | 3/14 | FILLER-ASSOCIATED gain: NEUTRAL 12 ≈ OLDW 13 ≫ NONE 3 — lesson-specific information is unnecessary for the large gain; content still modulates it (OLDG only 7). The step-1 "lesson-block-associated gain" decomposes to "block-present effect + content modulation" |

Lesson-echo (prereg §7 promise): 0/84 verbatim 6-gram overlaps in EVERY
condition × BOTH models — no parroting anywhere; the interference is
behavioral. Q35 rt-8204 secondary prediction (lesson gain on the strong
model) FAILED: every condition including NONE is 12/14 — no lesson gain
exists to measure at this difficulty.

## Addendum A — the W3 store's narrow coverage is substantially
validator-induced (corrects the prereg §6 wording)

The prereg said the five rejected W3 candidates "quoted numeric label
tokens from the evidence". WRONG (reviewer finding 3, verified by direct
read): the rejections were lexical accidents of the frozen anti-salience
vocabulary — 'forward' inside "carry forward" (an English verb; also a
corpus label), and the standalone digits 2/3/4/5 coming from the
FP-taxonomy numbers in TITLES ("FP-4 Distractor…") and from numbered
behavioral steps ("step 2"). Removing those purely lexical triggers
in-memory eliminates every violation (reviewer-verified). Consequence:
NEWF's cr-only coverage is substantially an artifact of the validator's
blocked-vocabulary collisions, NOT evidence that faithful mining found
no grounded dx/rt lessons. The store itself is valid (4 accepted lessons
are real and mechanism-level); its COVERAGE is selected by the validator
as much as by the evidence. A validator audit (blocked-vocab collision
report) is a stage-2 prerequisite.

## Addendum B — "same selection, isolates fidelity ONLY" overstated

The faithful bundles' declared char-budget trim dropped 1–2 lowest-ranked
runs in 4 of 9 bundles (12→11 cr-FP1-retraction, 12→11 cr-FP3a-vce,
12→10 cr-FP3a-vct, 12→10 cr-FP3b-sc; six runs total), plus the declared
worker num_ctx 8192→16384. E3 therefore compares two STORE PIPELINES
(fidelity + trim + context + validator-selected coverage), not evidence
fidelity alone. The frozen artifacts stand; the isolation claim is
corrected here.

## Addendum C — the NEUTRAL control's own limits

The filler block was word-matched to OLDG only (cr-8003 word totals:
NEUTRAL 349 vs OLDG 290 vs OLDW 102 vs NEWF 109), and despite the spec
it contains mild format/workflow instructions ("same order", "few short
lines", labeling boxes, using initials). It therefore supports "THESE
filler instructions reproduce a large part of the deficit and the
rt-8204 gain" — not "any block does", and not content-independent
causation.

## Interpretation (post-fold, bounded)

1. **A large, clean model contrast**: on identical prompts, the tested
   stronger model solves all harm probes cold and is measurably
   unaffected by every tested block, while the 8B loses 7–12/56 probes
   to each — filler included. This is the strongest evidence in the arc
   for a capacity-related component of the owner's hypothesis, in the
   refined form "robustness to probe-time context injection", with the
   model-family confound declared and no claim about stronger-model
   lesson BENEFIT (unmeasurable at ceiling).
2. **The 8B's deficit decomposes by condition, not by one mechanism**:
   filler reproduces the OLDW and NEWF deficits (registered rule), the
   OLDG deficit is cr-8003-concentrated and lesson-associated with a
   different error signature. "Generic interference dominates" is NOT
   established as a single mechanism — the honest statement is
   "block-associated losses are the rule for the 8B; their content-
   specificity varies by cluster and store".
3. **The rt-8204 gain is filler-associated** — lesson-specific
   information is unnecessary for it (12/14 filler vs 3/14 none), with
   content modulation on top (OLDG 7).
4. **No tested lesson text has yet helped either model on this surface**
   (Q35 ceiling; G8B: every lesson condition ≤ NONE pooled, and the one
   faithful targeted delivery (cr-8003) hurt most there).
5. **Lesson benefit remains unmeasured for the strong model** — any next
   claim needs a surface with headroom for that model.

## Limitations (declared)

Probe-level replay on recorded 8B histories (the NONE baseline is "no
block given a lesson-shaped history"); one stronger model (family/
tokenizer/tuning bundled); NEWF pipeline confounds (Addenda A/B); the
NEUTRAL control's scope (Addendum C); Q35 ceiling caps E1's reading and
vacates E3; rt-8203 is an underspecification witness only.

## Next-step implication (owner gate)

Stage 2 (separate brief): end-to-end new suite (v3o) — repaired rt
mappings (rule actually supplied), balanced memory-condition sampling
for any future mining, difficulty calibrated so the STRONG model has
headroom (independently calibrated), corrected delivery fixed,
neutral-block controls matched per delivery position, and — as an OPEN
HYPOTHESIS with matched controls, not a settled recommendation — a
session-start (non-probe-time) delivery arm for the 8B. Prerequisite:
the validator blocked-vocab audit (Addendum A).
