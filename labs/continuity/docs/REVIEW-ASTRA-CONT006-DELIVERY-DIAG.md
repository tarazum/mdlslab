# REVIEW — CONT-006 DELIVERY-DIAG independent review (GPT-6 Astra, 2026-10-10)

Provenance: step-1 diagnostic close-out review per the session brief's
routing (Fable still limit-blocked from this morning; reset 2:30am Kyiv;
codex CLI 0.162.1 already configured). Reviewer: gpt-6-astra, reasoning
effort high, read-only sandbox, cwd = repo root. Prompt:
docs/_dd_review_prompt.md (design + annotation + reconstruction + results
+ interpretation). Raw output kept verbatim below and in
docs/_dd_review_raw.txt.

Reviewer's own verification (from its report): it re-executed the frozen
runner offline over recorded replies, matched every memory/lesson
injection event and probe context across all 84 cells, matched all 192
logged context hashes and corrected blocks, rescored all 192 replies +
84 recorded baselines with ZERO discrepancies, reproduced both bootstrap
intervals, and audited the freeze (117/118 byte-match; the sole mismatch
= the declared post-freeze analysis-path module edit, whose diff it
confirmed analysis-only).

## Implementer curation appendix (mandatory house check)

Verified by direct computation AFTER the review:
- R2/R3 harm decomposition (review finding 3): R2 a 19/28 → b 19/28,
  c 25/28; R3 a 17/28 → b 21/28, c 22/28 — CONFIRMED from
  calls.jsonl + per-arm cluster counts (all net recovery is R3; the
  pooled b<c residual is predominantly R2). This is the sharpest
  post-review refinement and is folded into the results doc.
- Replay agreement (finding 4): byte-exact 20/24, whitespace-trimmed
  23/24, score agreement 23/24 — CONFIRMED (my analyzer had reported
  only the trimmed count under an ambiguous "exact-content" label; the
  results doc now reports all three).
- dx R3 delivery = G006 AND G007, not the binding lesson alone
  (finding 1, sub-point) — CONFIRMED (prereg table says so; my first
  draft's "ONLY thing delivered" wording was wrong for R3; fixed).
- Freeze 117/118 with the module as sole mismatch — CONFIRMED by
  recompute.
- Annotation disagreements (finding 2): G003/W005 at rt-8203/8204 would
  be WITHHELD under the reviewer's literal reading (the linen card never
  defines the queried folding/collection family — the applicability
  condition "a verified standing rule defines how items of that family
  sort" is not satisfied for the probed family); W006 at dx = "plausible
  but not literal" (its own text says "current environment prompt /
  immediate context"; the binding lives in an earlier session recalled
  via memory). ACCEPTED as recorded disagreements; the pre-registered
  annotation stands as the executed treatment (reviewer's own
  instruction), and the results doc now carries the sensitivity note —
  including its sharpest corollary: under the stricter reading, the
  rt-8204 (b) gain came from lessons a strict annotator would withhold.
- MAJOR-1's core (b is a PACKAGE change: selection+position+wording+
  length+combinations; no neutral-block control) — ACCEPTED; the
  results/owner docs now word the residual as having COMPETING
  explanations (content / conditional-application capacity / generic
  prompt interference) and the step-3 recommendation adds the
  matched neutral-block control.
- No findings rejected. NOTE: the review's finding-5 statement "at
  review time uncommitted" was accurate when made; the fix now rides
  the close-out commit, and the post-freeze note in the results doc was
  corrected accordingly (including the R0-reference fields addition it
  flagged as omitted).

## Verbatim review (as returned)

1. **MAJOR — The residual does not establish a content defect or eliminate delivery explanations.**  
   [Results, lines 43–65](C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-DELIVERY-DIAG.md:43) moves from an observed **b<c** contrast to “CONTENT-level … not a delivery artifact.” That inference is too strong. Variant b jointly changes selection, position, wording, length, and lesson combinations. There is no matched neutral block, placement control, or individual-lesson ablation.

   In particular, G003’s instruction to derive a fresh classification from the standing card **supports** cr-8003’s task; its text does not contradict the inference demand. Card-echoing establishes unsuccessful application, not that the prescription itself is wrong. Also, R3’s dx treatment includes **G006 and G007**, contradicting the claim that the binding lesson was “the ONLY thing delivered.” See [routing table](C:/projects/mdlslab/labs/continuity/experiments/cont006/delivery_v2_diagnostic.py:99) and diagnostic `calls.jsonl:129`.

   The [owner brief, lines 21–34](C:/projects/mdlslab/labs/continuity/docs/OWNER-BRIEF-CONT006-DELIVERY-DIAG.md:21) strengthens these claims further: “ideally delivered,” a residual unexplained by delivery, and benefit “not randomness.” It also omits the English report’s crucial rt-8204 underspecification caveat. Required wording: **this delivery package leaves a pooled deficit; lesson content, conditional application, and prompt interference remain competing explanations.**

2. **MAJOR — Four rt applicability calls lack their required evidence; W006’s two dx calls require a broader temporal interpretation than its wording.**  
   My independent annotation follows. `Y` means defensible; `N` means withhold; `J` means the registered interpretation is plausible but I would withhold under a literal reading. Grouped rows have identical judgments for every listed lesson.

   | Lesson | cr-8003 | cr-8004 | dx-8401 | dx-8402 | rt-8203 | rt-8204 |
   |---|---|---|---|---|---|---|
   | G001, G002, G004 | N | N | N | N | N | N |
   | G003 | Y | Y | N | N | **N** | **N** |
   | G005 | Y | Y | N | N | N | N |
   | G006 | N | N | Y | Y | N | N |
   | G007 | Y | Y | Y | Y | Y | Y |
   | W002, W003, W004 | N | N | N | N | N | N |
   | W005 | Y | Y | N | N | **N** | **N** |
   | W006 | N | N | **J** | **J** | N | N |

   G003 requires a standing rule defining the relevant family; W005 instructs extracting the answer from the verification source. Neither [rt-8203:24](C:/projects/mdlslab/labs/continuity/fixtures/v3n/repeated_task/rt-8203.json:24) nor [rt-8204:24](C:/projects/mdlslab/labs/continuity/fixtures/v3n/repeated_task/rt-8204.json:24) supplies the folding/collection mapping. Both supply only mending/pressing. The [preregistered G003 rationale](C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-DELIVERY-DIAG.md:115) therefore overstates what was shown. A card’s existence is insufficient to satisfy these prescriptions for the queried family.

   For W006, the rule repeatedly says **“current environment prompt,” “immediate context,”** and **“current environment description”** ([store:118](C:/projects/mdlslab/labs/continuity/results/CONT-006-VAL/cont006-v-20261010-130154/active-store-r2.json:118)). The dx binding is supplied in an earlier session, then recalled through memory. The scenario-wide interpretation is transparently preregistered, but it is not an unambiguous strict match.

   I agree with the flagged G001/G004 exclusions: cr-8004 reaffirms the standing routing; it does not amend it. The remaining exclusions and positive calls are defensible. Preserve the original annotation as the executed treatment; append these disagreements rather than retrospectively changing it.

3. **MAJOR — “Confirmed,” “material,” and “approximately half” exceed the evidence for recovery.**  
   The registered directional rule passes, but the meaningful band fails: **40/56 < 42/56**. The reproduced exploratory b−a interval is **[−0.125, +0.1964]**. One score flip among 24 replays supplies an empirical disagreement rate, not a statistical boundary beyond which chance has been excluded. Thus [Results:43](C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-DELIVERY-DIAG.md:43) should describe evidence *consistent with partial recovery*, rather than confirmed material attribution.

   Pooling also conceals an important distinction, independently recomputed from the traces and calls:

   | Harm clusters | Recorded a | Corrected b | Memory-only c |
   |---|---:|---:|---:|
   | R2 | 19/28 | 19/28 | 25/28 |
   | R3 | 17/28 | 21/28 | 22/28 |

   **All net recovery is R3; six of the seven residual failures relative to c are R2.** R3’s b−c difference, 1/28, is below the registered pooled replay-rate threshold. This materially narrows claims about residual harm from gold lessons.

   The [owner brief’s “delivery ~half the problem”](C:/projects/mdlslab/labs/continuity/docs/OWNER-BRIEF-CONT006-DELIVERY-DIAG.md:56) is not an estimated decomposition. Even descriptively, recovery is 4 of the 11 failures separating a from c, or 4 of 14 relative to the duplicated historical R0 reference. Neither supports that quantitative attribution.

4. **MINOR — “23/24 exact-content replays” actually means whitespace-trimmed agreement.**  
   [Analyzer:514](C:/projects/mdlslab/labs/continuity/experiments/cont006/delivery_v2_diagnostic.py:514) compares `.strip()` results. Independent counts are:

   | Replay agreement | Count |
   |---|---:|
   | Byte-exact content | **20/24** |
   | Content after trimming boundary whitespace | **23/24** |
   | Pass/fail score | **23/24** |

   Diagnostic `calls.jsonl:35,51,60` differ only in trailing newlines; line 147 changes `Acknowledge.` to `M17.` and flips the score. These distinctions do not undermine the reconstruction. However, [prereg P4](C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-DELIVERY-DIAG.md:175) ambiguously connects “exact-content” differences to “flips,” while the frozen implementation uses **score disagreement** for the noise rate. Report all three explicitly; do not silently reinterpret the threshold after seeing results.

5. **MINOR — The post-freeze correction is substantively legitimate, but its provenance statement is inaccurate and the decision branches were not exhaustive.**  
   The freeze contains 118 entries; **117 match the current checkout**, and the sole mismatch is the declared diagnostic-module edit. The committed module at `2a24ce6` matches its frozen digest exactly. Its diff changes analysis/reporting only: the erroneous c−c bootstrap, the P3 explanation, and previously empty R0-reference fields. I reproduced both corrected intervals. I found no inference-path change or threshold tuning.

   Nevertheless, [Results:97–102](C:/projects/mdlslab/labs/continuity/docs/RESULTS-CONT006-DELIVERY-DIAG.md:97) says the correction was committed separately with a LOG entry. At review time it is **uncommitted**, and LOG ends with the start entry. The note also omits the R0-reference addition. Correct that account when closing out.

   Predictions and numerical thresholds were fixed and falsifiable. But [decision directions:181–190](C:/projects/mdlslab/labs/continuity/docs/PREREG-CONT006-DELIVERY-DIAG.md:181) simultaneously prescribe step 2 for P1+P2 and step 3 for P3, without explicit precedence. “MIXED” is a reasonable synthesis of this overlap, not a uniquely preregistered compound verdict. No evidence here requires treating the analysis fix as outcome fishing.

6. **MINOR — The assurance gates are weaker than their documentation, although this dataset passes the missing checks independently.**  
   [Freeze construction:357–361](C:/projects/mdlslab/labs/continuity/experiments/cont006/delivery_v2_diagnostic.py:357) hashes only the rendered **seed-8001** suite, leaving other seed-specific fixture definitions outside that witness. [G-C:252–263](C:/projects/mdlslab/labs/continuity/experiments/cont006/delivery_v2_diagnostic.py:252) checks expected answer and turn reference, not the claimed label-list equality or complete rendered prompt. G-D reads the first session response’s options. [Analysis:489–501](C:/projects/mdlslab/labs/continuity/experiments/cont006/delivery_v2_diagnostic.py:489) does not independently enforce option pins or reject duplicate/unexpected keys.

   I found no resulting corruption: all 192 keys are unique and expected, all recorded options agree, and fixture/trace replay agrees. These are future fail-closed deficiencies, not grounds to discard this run.

7. **NOTE — Reconstruction, scoring, and headline arithmetic survived independent verification.**  
   Beyond rerunning reconstruction, I executed the **frozen runner offline**, supplying recorded replies and retaining episodes only in RAM. Across all 84 cells, every memory/lesson injection event and final probe context matched the original trace and reconstructed context. All 192 logged context hashes and corrected blocks matched; no inference was invoked.

   I independently rescored all 192 replies and all 84 recorded baselines with zero discrepancies. The verified headline numbers are **40/56 versus 36/56 versus 47/56**, R3 **21/28 versus 17/28**, and rt-8204 **10/14 versus 3/14**. R0 references also match their raw traces. All calls succeeded on their first recorded attempt; maximum prompt usage was 972 tokens.

   Manual examples from [calls.jsonl](C:/projects/mdlslab/labs/continuity/results/CONT-006-DELIVERY-DIAG/cont006-dd-20261010-183404/calls.jsonl:1), applying [the frozen rule](C:/projects/mdlslab/labs/continuity/src/continuity/runner.py:102): line 10’s prose containing only `dispatch` passes; line 97’s whole-card reply contains six distinct labels and fails; line 108 contains only the allowed label `fettling`, so it is a **wrong-label** failure despite its length; line 147’s `M17.` passes.

**Verdict:** I would retain the diagnostic and its numerical results, but **not approve the conclusions as written**. A qualified MIXED reading is warranted: recovery is concentrated in R3, the remaining pooled deficit is predominantly R2, and rt-8204 shows a lesson-block-associated improvement on fixed histories—not validated rule transfer. Correct the applicability qualifications, causal certainty, replay terminology, and provenance account in both documents. Folding step 2 into step 3 is sensible provided repaired fixtures and faithful evidence are common prerequisites, old/new content is explicitly crossed with model, and within-model lesson-minus-baseline effects are measured. Include a matched neutral-block control if the next study intends to distinguish content failure from generic prompt interference. No rerun is necessary merely to preserve this diagnostic under those narrower conclusions.
