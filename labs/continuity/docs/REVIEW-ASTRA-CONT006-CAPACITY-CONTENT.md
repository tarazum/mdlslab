# REVIEW — CONT-006 CAPACITY-×-CONTENT independent review (GPT-6 Astra, 2026-10-10)

Provenance: step-3 close-out review per the session brief's routing
(Fable limit resets 2:30am Kyiv; not reset). Reviewer: gpt-6-astra,
reasoning high, read-only sandbox, cwd = repo root. Prompt:
docs/_cap_review_prompt.md. Raw verbatim below + docs/_cap_review_raw.txt.
Reviewer's own verification: all 129 freeze digests; chronology of
commits 1b69ff2 -> 0d49be2 vs the consumer run; 864 unique records, all
scores/context hashes/options; all 168 reused step-1 records; G8B harm
pools 47/36/39/40/35 and Q35 56/56; per-cluster + error-mode counts; the
bootstrap 0.125 [0.0, 0.375]; Q35 duplicates 24/24 in score AND text; W3
regeneration (520 env turns match rendered fixtures, 124 source-marked
turns provenance-checked, 520 agent responses represented, all nine
worker prompt/response hashes).

## Implementer curation appendix (mandatory house check)

Verified by direct computation AFTER the review:
- E2 per-condition gaps: OLDW |−11−(−8)|=3 (reproduced), OLDG 4
  (mixed), NEWF 1 (reproduced) — CONFIRMED; my draft's pooled
  "interference-dominated" override of the registered per-condition
  outcome was wrong and is corrected in the results doc.
- OLDG pass->fail cells: 9 (8 at cr-8003 + 1 cr-8004); overlap with
  NEUTRAL losses = 2 — CONFIRMED (reviewer's "seven net losses all at
  cr-8003" reads on net deltas; both decompositions support the
  cr-8003 concentration).
- W3 rejection causes: 'forward' in "carry forward"; standalone digits
  2/3/4/5 from FP-taxonomy titles and numbered behavioral steps —
  CONFIRMED by direct read of candidates-v2.json; my prereg §6
  explanation ("quoted numeric label tokens from the evidence") was
  WRONG and is corrected in Addendum A.
- Bundle trim counts (12->11/11/10/10, six runs) — CONFIRMED from
  worker_v3_bundles.json (my own gate output had shown trimmed=1..2);
  the "isolates fidelity ONLY" claim corrected in Addendum B.
- Lesson-echo (prereg §7 promise, missing from my first report) —
  computed post-review: 0/84 in every condition x both models; added to
  the results doc.
- cr-8003 exact losses −4/−7/−8 (not "−7…−8") and the differing
  error-mode shifts (NEUTRAL +10WL/+1FM vs OLDG +1WL/+6FM vs NONE) —
  CONFIRMED from calls.jsonl; results doc updated.
- Q35 rt-8204 secondary prediction FAILED (all conditions incl NONE
  12/14) — CONFIRMED; stated explicitly in the results doc.
- No findings rejected. Harness-hardening notes (MINOR-7: reuse-hash
  skip-on-missing, duplicate-key overwrite, E2 implemented only for
  OLDG) accepted as future fail-closed requirements for this harness.

## Verbatim review (as returned)

1. **MAJOR — “Generic-interference-dominated” is not established by the pooled totals.** The registered E2 rule gives OLDW **reproduced** (gap 3), OLDG **mixed/indeterminate** (gap 4), and NEWF **reproduced** (gap 1). The draft acknowledges OLDG’s failure, then overrides it with a stronger pooled conclusion. More seriously, **all seven net OLDG losses occur at cr-8003**, where NEUTRAL loses only one; NEUTRAL’s other ten net losses occur elsewhere. Only **2 of OLDG’s 9 baseline-pass→failure cells** overlap NEUTRAL’s losses. Similar aggregate deficits do not establish a common mechanism or its dominance. Preserve the condition-specific E2 outcomes and describe the decomposition as exploratory. [Registered rule](/C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-CAPACITY-CONTENT.md:75), [overridden reading](/C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-CAPACITY-CONTENT.md:35), [cluster table](/C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-CAPACITY-CONTENT.md:53).

2. **MAJOR — “Capacity hypothesis confirmed” exceeds what E1 identifies.** The interactions **+8/+7/+12** are correct, but Q35 contributes zero lesson-minus-NONE improvement throughout HARM. At this ceiling, the interaction mechanically equals the negative G8B treatment effect. It demonstrates an observed difference between these two models’ responses to the tested blocks; it does not identify conditional-application capacity, model size, or stronger-model lesson benefit. Family, tokenizer, instruction tuning, and model-specific prompt serialization remain bundled together—subtracting baselines does not remove their treatment interactions. The exploratory OLDG interval also includes zero. Replace “CONFIRMED,” “REAL,” and “fully injection-robust” with bounded descriptive language in **both** documents. [Results interpretation](/C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-CAPACITY-CONTENT.md:69), [owner headline](/C:/projects/mdlslab/labs/continuity/docs/OWNER-BRIEF-CONT006-CAPACITY-CONTENT.md:6).

3. **MAJOR — W3’s narrow coverage is substantially validator-induced, and the rejection explanation is wrong.** I reproduced all nine validator dispositions. The five rejected candidates were blocked by:
   
   - W-001: **“forward”** in “Do not carry forward.”
   - W-006: **2/3/4** in numbered behavioral instructions.
   - W-007/W-008/W-009: **5/4/2** in their **FP taxonomy titles**.

   These are not the claimed quotations of numeric answer labels from evidence. In-memory removal of those purely lexical triggers eliminated every anti-salience violation. This does **not** establish that the candidates should otherwise be accepted; it establishes that the absence of dx/rt lessons cannot be interpreted simply as faithful mining finding no grounded lesson there. Report this selection mechanism explicitly and audit it before future mining. [Incorrect explanation](/C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-CAPACITY-CONTENT.md:154), [candidate evidence](/C:/projects/mdlslab/labs/continuity/results/CONT-006-WORKER/cont006-worker-v3-20261010-203420/candidates-v2.json:169), [validator](/C:/projects/mdlslab/labs/continuity/src/continuity/lessons.py:109).

4. **MAJOR — “Same selection” and “isolates evidence fidelity ONLY” are false.** Grouping, ranking, and the nominal 12-run cap match v2, but the additional character-budget trim changes the actual selected evidence:
   
   | Bundle | v2 runs | v3 runs |
   |---|---:|---:|
   | cr-FP1-retraction | 12 | 11 |
   | cr-FP3a-vce | 12 | 11 |
   | cr-FP3a-vct | 12 | 10 |
   | cr-FP3b-sc | 12 | 10 |

   Six runs disappear. The trim was present before consumer inference, so this is not post-outcome manipulation; it is an inaccurately described design difference. Alongside the declared worker context increase and changed delivery coverage, E3 compares two resulting store pipelines rather than isolating fidelity alone. “This W3 store did not benefit G8B” stands; a causal conclusion about fidelity does not. Correct this through an explicit addendum, preserving the frozen artifacts. [Isolation claim](/C:/projects/mdlslab/labs/continuity/experiments/cont006/worker_v3_bundles.py:18), [trim implementation](/C:/projects/mdlslab/labs/continuity/experiments/cont006/worker_v3_bundles.py:144), [recorded bundle sizes](/C:/projects/mdlslab/labs/continuity/experiments/cont006/worker_v3_bundles.json:6).

5. **MAJOR — The control supports “these filler instructions can reproduce an effect,” not “any block” or content-independent causation.** NEUTRAL satisfies the registered OLDG word tolerance, but is not matched to OLDW or NEWF: at cr-8003 the word counts are **349 / 290 / 102 / 109** for NEUTRAL/OLDG/OLDW/NEWF. It also contains formatting and workflow instructions—“same order,” “few short lines,” labeling boxes, using initials—despite the specification requiring content unrelated to format and identifiers. This is a limitation of the registered control itself.

   At rt-8204, **12/14 NEUTRAL versus 13/14 OLDW versus 3/14 NONE** convincingly shows that lesson-specific information is unnecessary for a large gain. It does not prove that *any* system block works or that content has no influence; OLDG reaches only **7/14**. Q35’s registered positive-gain prediction also fails: every condition, including NONE, scores **12/14**. State that result explicitly. [Control specification](/C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-CAPACITY-CONTENT.md:39), [rt claim](/C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-CAPACITY-CONTENT.md:60), [secondary prediction](/C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-CAPACITY-CONTENT.md:106).

6. **MINOR — Two descriptive claims misstate the verified results.** At cr-8003, lesson losses are **−4 OLDW, −7 OLDG, −8 NEWF**, not uniformly −7…−8. Also, the error modes weaken the claimed common “format-degeneration signature”: relative to NONE, NEUTRAL adds **10 wrong-label errors and only 1 format miss**, whereas OLDG adds **1 wrong-label error and 6 format misses**. Report these different distributions rather than attributing them to the same mechanism. The preregistered lesson-echo analysis is also absent from the generated report. [Cluster/error prose](/C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-CAPACITY-CONTENT.md:55), [planned analysis](/C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-CAPACITY-CONTENT.md:194).

7. **MINOR — The harness’s completeness checks are weaker than advertised, although this run passes independent checking.** Missing reuse hashes are skipped by `if want`; the reuse report assumes 84 NONE records. Analysis silently skips missing cells, overwrites duplicate keys, and reports completeness/headroom counts without enforcing conservative endpoint handling. E2 is implemented only for OLDG despite the registered per-lesson rule. These did not corrupt this complete dataset, but should be corrected before reusing the harness. [Reuse gate](/C:/projects/mdlslab/labs/continuity/experiments/cont006/capacity_content_diag.py:244), [analysis](/C:/projects/mdlslab/labs/continuity/experiments/cont006/capacity_content_diag.py:441).

8. **NOTE — The underlying execution evidence is reproducible; I found no integrity blocker.** Read-only verification established:
   
   - All **129 freeze entries** match; the preregistration and freeze match commit `0d49be2`. Recorded chronology places that commit before the consumer run.
   - **864 unique expected records**, with no missing or extra cells; all scores, context hashes, and sampling options check out. All **168 reused records** match step 1.
   - G8B HARM totals reproduce as **47/36/39/40/35**, with Q35 **56/56 throughout**. Every cluster-table entry and error-mode count matches.
   - Q35 duplicates agree **24/24 in both score and text**. The bootstrap reproduces **0.125 [0, 0.375]**. Maximum prompt length is **1,030 tokens**; one G8B OLDG response reaches the 256-token output cap.
   - W3 regenerates exactly. All **520 retained environment turns** match rendered fixtures, all **124 source-marked turns** have matching fixture provenance, and all **520 agent responses** are represented. All nine worker prompt/response hashes match.

**Verdict:** The numerical results stand; the conclusions do **not stand as written**. Retain the observed model contrast, Q35 ceiling, cr-8003 lesson-associated harm, rt-8204 filler-associated gain, and this W3 store’s lack of G8B benefit. Remove claims that capacity is confirmed or generic interference dominates the lesson deficit. Stage 2 is sensible with repaired mappings, balanced sampling, independently calibrated headroom, and neutral controls—but session-start delivery should be tested as an open hypothesis, with matched controls at each position. Add the validator audit and explicit E3 confounds before proceeding. No files were modified.
