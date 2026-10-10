# PREREG — CONT-006 CAPACITY-×-CONTENT (step 3, step-2 folds as prerequisites)

Written BEFORE any consumer inference (2026-10-10; owner authorization:
«йдемо далі за рекомендацією» after RESULTS-CONT006-DELIVERY-DIAG.md).
Diagnostic (not confirmatory): no MME/verdict machinery; never promotable
into the registered records. The step-1 artifacts, frozen sources and all
committed run roots are READ-ONLY.

## 1. Question

Step 1 left a residual: correctly-delivered lessons still net-hurt the
harm clusters vs memory-only on the 8B (−0.125), with COMPETING
explanations — lesson content, conditional-application capacity, generic
prompt interference. This diagnostic separates them:

- CAPACITY: does a stronger instruction-follower extract more from the
  SAME conditional lessons at the SAME probes (interaction, not level)?
- INTERFERENCE: does a length/position-matched NEUTRAL block reproduce
  the 8B deficit?
- EVIDENCE FIDELITY: do lessons mined from FAITHFUL evidence behave
  better than the fragment-mined originals?

## 2. Design

- **Cells**: the step-1 84-cell set (cr-8003/8004, dx-8401/8402,
  rt-8203/8204 × seeds 8001..8007 × R2/R3 recorded histories), same
  reconstruction machinery and gates (delivery_v2_diagnostic.py, imported
  read-only; its G-A..G-E gate definitions apply verbatim).
- **Models** (both local, digest-pinned at preflight; NO downloads):
  G8B = granite-code:8b (36c3c3b9683b); Q35 = qwen36-35b-a3b:mdlslab
  (8a0fd5da454e — the frozen worker reflector, validated as a consumer in
  CONT-002). Sampling pins IDENTICAL across models: temperature 0.0,
  seed = cell seed, num_ctx 4096, num_predict 256, think:false,
  keep_alive 30m. Prompts are byte-identical per condition across models
  (the model is the only difference).
- **Conditions** (one system message right before the probe turn for 2-5;
  NONE has none):
  1. NONE — no lesson block (= step-1 variant c).
  2. NEUTRAL — matched control block: same header, same numbered
     skeleton ("K. Title. When …: Rule: … Behavior: …"), housekeeping
     content unrelated to labels/corrections/cards/identifiers/format;
     line count = the OLDG delivery set size for that cluster; word total
     within ±25% of the OLDG block for that cluster (fixed texts in §5).
  3. OLDW — the executed worker store (5 lessons, W2), delivery-v2 with
     the step-1 W-annotation (PREREG-CONT006-DELIVERY-DIAG §5, unchanged).
  4. OLDG — the executed gold store (7 lessons), delivery-v2 with the
     step-1 G-annotation (unchanged).
  5. NEWF — the FAITHFUL-evidence worker store (W3 pass over
     worker_v3_bundles.json: same selection/grouping/cap as W2, evidence
     restored — full env turns, source_type/actor, every agent reply;
     same frozen worker prompt/validator/FP-6 cap; DECLARED DEVIATION:
     worker num_ctx 8192→16384 via custom provider — the faithful digests
     are ~10.1k prompt tokens and the frozen ctx rejects them
     (exceed_context_size_error n_prompt_tokens=10146, first call;
     everything else identical: temp 0.0, seed 42, num_predict 768)),
     delivery-v2 with the NEW annotation in §6 (filled from the W3 store
     BEFORE the freeze — the freeze digests this file, so the annotation
     is pre-registered by construction).
- Every condition runs on EVERY cell for Q35 (5 × 84 = 420) and for G8B
  minus the step-1 reuse: G8B×NONE (step-1 c, 84) and arm-matched
  G8B×OLDW-on-R2 / OLDG-on-R3 (step-1 b, 84) are REUSED — context sha256
  equality between the rebuilt and step-1 contexts is a REQUIRED gate.
  New G8B calls: NEUTRAL/NEWF (2 × 84) + cross-arm OLDW-on-R3 /
  OLDG-on-R2 (2 × 42) = 252. Q35 determinism subset: NONE called twice on
  seeds {8001, 8005} (24 duplicate calls). Total new inference = 696.

## 3. Endpoints (fixed BEFORE any consumer inference)

Pools: HARM = cr-8003/8004 + dx-8401/8402 (56 cells per condition-model);
report rt-8203/8204 separately (driver + floor clusters).

- **E1 CAPACITY (primary)**: for each lesson condition L ∈ {OLDW, OLDG,
  NEWF}: I_L = (S_L − S_NONE)_Q35 − (S_L − S_NONE)_G8B over HARM.
  Primary decision: I_OLDG > 0 beyond noise. Band: I_OLDG ≥ +4/56.
- **E2 INTERFERENCE**: D_N = (S_NEUTRAL − S_NONE) per model over HARM.
  Reading rule (fixed): if D_N(G8B) ≤ −3/56 AND |D_N(G8B) − D_L(G8B)|
  ≤ 3/56 for a lesson condition L, the neutral text reproduces that
  lesson deficit → generic interference; if |D_N| ≤ 3/56 (either model)
  while D_L ≤ −3/56, that lesson deficit is content-specific.
- **E3 EVIDENCE FIDELITY**: (S_NEWF − S_NONE) vs (S_OLDW − S_NONE) per
  model over HARM; directional prediction NEWF ≥ OLDW on both models.
- **E4 LEVEL (declared non-primary)**: S_NONE(Q35) vs S_NONE(G8B) —
  expected Q35 ≥ G8B; NEVER read as the claim (family/tokenizer changes
  ride along; the interaction is the estimand).

Noise floors: G8B carries step-1's replay floor (1/24 score
disagreement); Q35's floor measured by the 24 duplicate NONE calls. A
contrast whose |size| is within the applicable floor is read as "no
difference" in conclusions.

## 4. Predictions (fixed) and decision directions

- P-E1: I_OLDG > 0 (band ≥ +4/56). If MET + E2 says content-specific →
  conditional-application CAPACITY is the 8B's limiter on this surface
  (the owner's small-model hypothesis, refined); next = stage-2
  end-to-end suite (v3o: repaired rt mappings, balanced sampling) with
  both models.
- If I_OLDG ≤ noise (or ≤ 0) → lesson CONTENT fails across capacity on
  this surface → lesson generation/curation is the lever regardless of
  model; step-2-full (faithful evidence at scale + curation) leads.
- P-E2: pre-registered both ways (see §3 rule); if neutral reproduces the
  deficit → delivery FORMAT/length/position is the lever, not content.
- P-E3: NEWF ≥ OLDW directionally on both models; if MET on Q35 with
  I_NEWF > I_OLDW → faithful evidence improves lessons where capacity
  allows applying them.
- rt-8204 (secondary): the lesson-driven gain should replicate on Q35
  (S_L − S_NONE > 0 for the lesson conditions); if it does not, the
  activation gain is model-specific, weakening its transfer reading.

## 5. NEUTRAL block texts (fixed before freeze; ~95-105 words each so that
N-line totals sit within ±25% of every cluster's OLDG block: cr 3 lines vs
~290 words, dx/rt 2 lines vs ~191-200 words)

Header: identical to the lesson header ("Lessons learned in earlier work
(apply where relevant):"). Line skeleton identical to the lesson renderer
("K. Title. When …: Rule: … Behavior: …"). The three texts (first N per
cluster, N = |OLDG set| = 3 for cr-8003/8004, 2 for dx/rt):

1. "Shift handover hygiene. When a shift ends and a handover note is
   written for the incoming desk worker: Rule: record only the start and
   end times of the shift, the desk location, and whether the keys were
   returned; nothing about ongoing tasks belongs in the note, because the
   task board is updated separately by the rota lead each morning and
   duplicate notes cause confusion. Behavior: write the note in the same
   order every time, keep it to a few short lines, date it at the top,
   and leave it in the tray under the desk lamp rather than pinning it to
   the wall where previous notes have gone missing during busy hours."
2. "Supply shelf order. When the supply shelf is restocked during a quiet
   period before the weekly count: Rule: arrange items by size with the
   tallest containers at the back and the smallest in front, keep one
   clear aisle between the glassware and the paper stock, and never stack
   loose pens or brushes on top of the ledgers that live on the lower
   level of the same shelf. Behavior: wipe the shelf before restocking,
   label any box that has lost its mark, fold the step stool against the
   wall afterwards, and note the count date on the clipboard so the next
   shift knows the shelf was already checked and can trust the
   arrangement they inherit."
3. "Visitor greeting practice. When a visitor arrives at the desk during
   daytime hours while the sign-in book is open: Rule: greet the visitor
   first, then ask the purpose of the visit, then point to the floor plan
   only if the purpose actually needs one; courier deliveries go to the
   side hatch, never the front desk, and contractors must show a badge
   before being waved through. Behavior: keep the floor-plan reference
   brief, offer the chair by the window to anyone who has to wait, return
   the visitor badge tray to its drawer after use, and log the visit with
   initials rather than full names so the sign-in line keeps moving at
   busy times."

Word totals per cluster are recorded in the run log and gate-checked
within ±25% of the OLDG block.

## 6. NEWF applicability annotation (filled from the W3 store BEFORE freeze)

W3 pass complete (results/CONT-006-WORKER/cont006-worker-v3-20261010-203420:
9/9 calls, 0 parse errors, 0 truncations; 9 candidates → 4 accepted
(2×FP-3a, 2×FP-3b), 5 rejected by the frozen anti-salience validator —
they quoted numeric label tokens from the evidence; store digest
a670b941…34c4; declared deviation num_ctx 8192→16384 recorded in
telemetry). The faithful store covers ONLY correction-family situations —
annotation from lesson text + fixture template semantics, [JC] flags:

| lesson | cr-8003 | cr-8004 | dx-8401/02 | rt-8203/04 | basis |
|---|---|---|---|---|---|
| W-002 verified-correction-to-card (FP-3a) | – | – | – | – | needs a VERIFIED correction amending an entry; cr-8003's press is unverified (the hauler book rejects it), cr-8004's notice re-affirms without amending |
| W-003 verified-tool 'out of date' (FP-3a) | – | – | – | – | no tool-marked invalidation event in any of the six |
| W-004 verified ledger over user insistence (FP-3b) | YES | – | – | – | cr-8003: shed hand insists on re-filing; the hauler book (verified record) keeps the entry — exactly this lesson's conditions |
| W-005 verified notice over unreviewed feed (FP-3b) | – [JC] | YES | – | – | cr-8004: verified re-affirming notice + unreviewed chalkboard claim. At cr-8003 the rejection comes from a record, not a verified notice re-affirming a rule — read as W-004's case, not W-005's [JC] |

Resulting delivery sets: cr-8003 [W-004]; cr-8004 [W-005]; dx-8401 [],
dx-8402 [], rt-8203 [], rt-8204 [] — the faithful store is CONDITION-
SCOPED: it withholds everywhere it has no grounded lesson (dx/rt),
unlike the fragment-mined OLDW whose prescriptions covered everything.
At dx/rt clusters NEWF ≡ NONE by construction (declared; E3 reads on the
cr clusters there, pools reported per cluster).

## 7. Gates, freeze, run, analysis

1. Zero-GPU gates BEFORE any consumer inference: step-1 gates G-A..G-E
   re-run clean over all 84 cells; NEWF store digest pinned; NEWF
   annotation covers every W3 lesson × every cluster (YES/NO + basis);
   neutral word-totals within ±25%; context-sha256 equality for the 168
   reused step-1 calls.
2. Freeze (experiments/cont006/capacity-freeze.json): digests of this
   doc, capacity_content_diag.py, worker_v3_bundles.py/.json, the W3
   output dir artifacts, the step-1 module + run root calls.jsonl, all
   step-1-frozen sources/stores/traces, and the rendered-suite witness.
   Committed BEFORE the consumer calls; preflight re-verifies fail-closed
   + pins BOTH model digests (warm-then-pin).
3. Run → results/CONT-006-CAPACITY/cont006-cap-<ts>/ (env.json,
   calls.jsonl with per-call condition/model/context-sha256/usage/scoring,
   capacity-results.json). Pre-analysis completeness: 696 new + 168
   reused = 864 records, 0 headroom violations (prompt_tokens < 4096),
   else the affected endpoint reads conservative.
4. Analysis: frozen scoring; exact counts everywhere; exploratory
   cluster bootstrap for I_OLDG (10k draws, RNG seed 20261011, labeled
   exploratory); error modes; lesson-echo; token telemetry; per-model ×
   per-condition × per-cluster table.

## 8. Non-goals (binding)

No new suite authoring (v3o end-to-end is stage 2, separate brief); no
balanced corpus re-sampling (declared open, stage 2); no end-to-end
session re-runs; no changes to any frozen file, registered verdict, or
committed artifact; the W3 worker pass itself reuses the frozen worker
machinery unchanged (only the bundle content differs, and the bundles
are a NEW artifact).
