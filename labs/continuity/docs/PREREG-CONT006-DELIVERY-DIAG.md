# PREREG — CONT-006 DELIVERY-DIAG: corrected-lesson-delivery probe-level diagnostic (step 1)

Written BEFORE any new inference (2026-10-10; house discipline per
SESSION-BRIEF-CONT006-DELIVERY.md and PREREG-REQUIREMENTS-V2 §1 spirit —
this is a DIAGNOSTIC, not a confirmatory run: no MME/verdict machinery,
no promotion of its numbers into the registered V2A record). Authorization:
the owner's kickoff line (verbatim match of the brief's §Kickoff).

Frozen-code rule: everything under src/continuity/ and the committed run
roots is READ-ONLY here. All new code lives in
experiments/cont006/delivery_v2_diagnostic.py; its digest + this doc's
digest + the digests of every input artifact enter
experiments/cont006/delivery-v2-freeze.json BEFORE the GPU part (§8).

## 1. Question and hypothesis

The V2A registered negative (Δ = −0.0667; R3−R0 = −0.1048, CI excludes 0
down) was produced by a delivery pipeline with five documented defects
(AUDIT-CONT006-V2A-POSTVERDICT §B2). This diagnostic isolates the
DELIVERY defects: does the same 8B model, on the SAME recorded session
histories, answer the same probes better when lessons are delivered by a
corrected mechanism (probe-time routing, strictly-annotated applicability,
full-rule rendering, no budget drops)?

H (delivery-defect): the registered harm is substantially an artifact of
WHAT was delivered WHERE; corrected delivery recovers harm without losing
the rt-8204-style gains.
Anti-H (content/capacity): the lesson CONTENT (or the 8B's ability to apply
it conditionally) is the problem; corrected delivery does not help, or
still hurts vs no lessons.

## 2. Probe set (fixed; 84 cells)

All probes of the harm + driver clusters across seeds, lesson arms only:

| cluster | class | probes at | seeds 8001–8002 trace source | seeds 8003–8007 | arms |
|---|---|---|---|---|---|
| cr-8003 | FP-3b | s3t2 | P root (byte-copy of CAL2 R2; P R3) | C root | R2, R3 |
| cr-8004 | FP-3b | s3t2 | P / C as above | C root | R2, R3 |
| dx-8401 | FP-4 | s3t2 | P / C as above | C root | R2, R3 |
| dx-8402 | FP-4 | s3t2 | P / C as above | C root | R2, R3 |
| rt-8203 | FP-2 | s3t2 | P / C as above | C root | R2, R3 |
| rt-8204 | FP-2 (VAL) | s3t2 | V root (all 7 seeds) | V root | R2, R3 |

6 clusters × 7 seeds × 2 arms = 84 probe contexts. Recorded reference
scores (variant a) and R0 references come from the same cells' committed
probe.result events / summaries. P = results/CONT-006-PILOT/
cont006-p-20261010-132230, C = results/CONT-006-CONFIRMATORY/
cont006-c-20261010-144817, V = results/CONT-006-VAL/
cont006-v-20261010-130154. Store pins (asserted per cell from
lessons.injected events; lesson CONTENT identical across pins — only the
status field differs): C root (active stores) R2 = f99be96f…59302,
R3 = b2500b6b…12cb; V root (kind "w2") R2 = f82efc3f…320b2,
R3 = 48064a02…6fafa; P root: R3 cells ran fresh with the ACTIVE store
(b2500b6b…12cb) while the R2 cells are the REUSED CAL2 copies pinning the
w2 store (f82efc3f…320b2).

## 3. Context reconstruction (exact, from committed artifacts)

For each cell, the as-executed probe context is rebuilt byte-exactly:

1. system = ARM_A_SYSTEM_PROMPT (frozen runner.py; no self-model in R0/R2/R3);
2. memory block = frozen format_memory_block over the episodes listed by
   the probe session's memory.injected event (ids in recorded order),
   contents read from the cell's committed memory.sqlite3 (asserted equal
   to the trace's env.turn / agent.response texts);
3. lesson block (as-executed variant only) = frozen lessons.retrieve +
   render_block over the pinned store, keyed on the probe session's first
   environment turn — asserted to reproduce the recorded rendered
   lesson_ids AND the recorded block length in chars;
4. session turns before the probe: user(env.turn text) / assistant(recorded
   reply content) pairs, in order;
5. final message: user(probe turn text).

Sampling pins are read from the recorded agent.response options of each
cell and reused verbatim (temperature 0.0, seed = cell seed, num_ctx 4096,
num_predict 256, think false, keep_alive 30m, model granite-code:8b,
digest-pinned 36c3c3b9683b via /api/ps before the first call).

## 4. Variants

- (a) AS-EXECUTED: recorded scores (no new inference by default). A fixed
  REPLAY SUBSET — every cluster × both arms × seeds {8001, 8005} = 24
  cells — is re-inferred from the reconstructed exact context to (i)
  validate the reconstruction end-to-end and (ii) measure the greedy+seed
  replay noise floor (CN-003/PB-071 caveat; env.json of every run carries
  it).
- (b) CORRECTED DELIVERY (delivery-v2): NO session-start lesson block;
  instead ONE system message immediately BEFORE the probe user turn,
  containing ONLY the lessons whose pre-registered applicability (§5)
  matches the cluster, rendered in FULL (title + when/applicability +
  RULE/lesson + behavior), store order, no budget. If no lesson applies,
  NO lesson message is sent.
- (c) MEMORY-ONLY: no lesson message anywhere (the R0-equivalent prompt
  on the same recorded history).

Scoring: the frozen score_probe over the rendered v3n fixture probe dict
for that seed (labels/expected asserted equal to the recorded
probe.result). New inference total: 84 (b) + 84 (c) + 24 (a-replay) = 192
calls (brief budget ~100–200 × 1 call — 168 primary + 24 noise-floor
replays, declared).

## 5. Applicability annotation (THE pre-registered routing table)

Annotated INDEPENDENTLY of any model output, from lesson text + fixture
template semantics only (cluster-level, seed-independent). Judgment calls
are marked [JC] and go to the external review.

R3 (gold store, delivery order = store order G001…G007):

| lesson | cr-8003 | cr-8004 | dx-8401 | dx-8402 | rt-8203 | rt-8204 | basis |
|---|---|---|---|---|---|---|---|
| G001 amended value governs | – | – | – | – | – | – | no amendment of any queried value exists in these scenarios (cr-8004's verified notice explicitly RE-AFFIRMS "remains as the card has it") [JC] |
| G002 withdrawn correction reverts | – | – | – | – | – | – | no withdrawal/retraction event in any of the six |
| G003 re-derive from standing card | YES | YES | – | – | YES | YES | the probe classifies a NEW item of a family whose verified standing rule card was shown ("card not at hand / cards locked away") |
| G004 verified correction to routing | – | – | – | – | – | – | no routing correction arrives on the verified channel in these scenarios (cr-8004 re-affirms; cr-8003's press is unverified) [JC] |
| G005 unverified claims never override | YES | YES | – | – | – | – | an unverified re-file/re-route insistence is present (shed hand / yard chalkboard) and must not govern |
| G006 re-bind look-alike identifiers | – | – | YES | YES | – | – | two look-alike codes logged together; probe asks for the code of ONE entity; options contain the other's code |
| G007 closed-list single option | YES | YES | YES | YES | YES | YES | every probe offers a closed list and demands the option alone |

R2 (worker store, store order W002…W006):

| lesson | cr-8003 | cr-8004 | dx-8401 | dx-8402 | rt-8203 | rt-8204 | basis |
|---|---|---|---|---|---|---|---|
| W002 explicit correction priority | – | – | – | – | – | – | no verified correction of the QUERIED item exists at these probes; the rule has no valid referent (its application is the documented suppression mechanism) |
| W003 verified-correction override | – | – | – | – | – | – | same as W002 (near-duplicate) |
| W004 explicit instruction over distractors | – | – | – | – | – | – | its own condition fails: the probe instruction never names the target category/action (the answer must be derived) |
| W005 verification-source ground truth | YES | YES | – | – | YES | YES | the probe references the verification artifact (card "not at hand"/"not in reach"); correct behavior = extract the label from that (remembered) source, output only the label |
| W006 explicit value for queried entity | – | – | YES | YES | – | – | the scenario environment stated the queried entity's value; the probe asks exactly that entity's value among look-alike options. "Environment prompt" read at scenario scope, not probe-turn scope [JC] |

Resulting delivery sets:
R2: cr-8003 [W005]; cr-8004 [W005]; dx-8401 [W006]; dx-8402 [W006];
rt-8203 [W005]; rt-8204 [W005].
R3: cr-8003 [G003, G005, G007]; cr-8004 [G003, G005, G007];
dx-8401 [G006, G007]; dx-8402 [G006, G007]; rt-8203 [G003, G007];
rt-8204 [G003, G007].

Note the embedded tests this creates: (i) G005 — retrieved-then-dropped at
the harm clusters by the defective renderer — is restored exactly there;
(ii) at dx clusters the R2 corrected delivery sends ONE targeted lesson
where the executed channel dumped the entity-binding-harming mix;
(iii) G007 rides at every probe (honest annotation of its own condition)
despite the RGOLD list-echo precedent — the diagnostic therefore also
measures whether FULL-rule rendering avoids the trivial-format-lesson
degradation.

## 6. Recorded baselines (variant a; recomputed from committed summaries,
verified against REVIEW-ASTRA table)

| cluster | R0 | R2(a) | R3(a) |
|---|---|---|---|
| cr-8003 | 7/7 | 6/7 | 4/7 |
| cr-8004 | 4/7 | 2/7 | 3/7 |
| dx-8401 | 7/7 | 6/7 | 4/7 |
| dx-8402 | 7/7 | 5/7 | 6/7 |
| harm pooled (4 clusters, /28) | 25 | 19 | 17 |
| rt-8203 | 0/7 | 1/7 | 0/7 |
| rt-8204 (VAL, /7) | 1 | 6 | 6 |

Harm-cluster error modes (recorded): R0 3 wrong-label / 0 format-miss;
R2 4/5; R3 7/4.

## 7. Predictions (fixed BEFORE inference) and decision directions

- P1 (primary, delivery-defect): S_b(harm pooled over 56 cells) >
  S_a(harm pooled) = 36/56. Meaningful-band: S_b ≥ 42/56 (+6 net probes).
- P1a (R3 recovery): S_b(R3 harm, /28) > 17/28; band ≥ 21/28.
- P2 (rt-8204 gains retained): S_b(rt-8204 pooled over 14) ≥ 7/14
  (= recorded R0 level 2/14 + half the recorded margin (12−2)/14).
- P3 (discriminating): if S_b(harm) ≤ S_a(harm) → delivery defects alone
  do NOT explain the registered harm (content/capacity gain; step 3 of
  the ranking becomes next). If S_b(harm) < S_c(harm) → corrected lessons
  still actively hurt vs no lessons on identical histories → the
  content/capacity hypotheses strengthen decisively.
- P4 (noise floor): the 24 a-replays report exact-content match vs
  recorded replies; flip count / 24 = replay noise. Any (b)/(c) delta
  whose absolute size is within (flips/24 scaled to the compared pool)
  is read as "no difference" in the conclusions, not as an effect.

Decision directions (pre-registered):
- P1 (beyond noise) AND P2 → "corrected delivery recovers the harm
  without losing the gains": the delivery defects explain the registered
  negative on this surface; next = step 2 (faithful evidence + fixed
  fixtures in a new suite).
- P1 (beyond noise) but P2 fails → partial recovery at the cost of the
  activation gain: mixed reading; owner gate decides step order.
- P1 fails (≤ noise or negative) → delivery fix insufficient; capacity ×
  content comparison (step 3) becomes next regardless of P3.
- P3 fires → content/capacity strongly implicated; step 3 next; the
  "faithful worker evidence" step 2 re-scoped accordingly.

Exploratory (never promotable): per-cluster (b)/(c)/(a) table; format-miss
and wrong-label decomposition per variant; lesson-text echo rate (≥6-word
overlap with an injected lesson line); prompt-token telemetry; cluster
percentile bootstrap over the 4 harm clusters (10,000 draws, RNG seed
20261010) for (b)−(a) and (b)−(c), labeled exploratory.

## 8. Gates and freeze (binding order)

1. Zero-GPU reconstruction gates (ALL must pass before ANY inference):
   G-A lesson-block reproduction (ids + chars) on all 84 cells; G-B
   memory-episode content equality sqlite-vs-trace for every referenced
   episode; G-C rendered-fixture probe (labels/expected) equals recorded
   probe.result expected, probe at s3t2; G-D recorded per-cell options ==
   pins of §3; G-E store digests per cell match §2 pins; completeness 84.
2. Freeze manifest (experiments/cont006/delivery-v2-freeze.json):
   digests of this doc, delivery_v2_diagnostic.py, the session brief,
   src/continuity/{runner,provider,memory,lessons,events,fixtures}.py,
   both active stores, and every trace.jsonl + memory.sqlite3 +
   summary.json the reconstruction reads. Emitted AFTER gates, COMMITTED
   before the GPU part; preflight re-verifies fail-closed.
3. GPU part writes results/CONT-006-DELIVERY-DIAG/cont006-dd-<ts>/:
   env.json (model digest pin, options, caveat), calls.jsonl (one record
   per inference: cell, variant, context sha256, messages hash, usage,
   content, scoring), delivery-diag-results.json (analysis vs §7).
4. Pre-analysis completeness check (live-gate analogue): 192/192 calls
   present with pinned options and prompt_tokens < 4096, else the record
   carries the misses and the affected prediction is read conservatively.

## 9. Non-goals (binding)

No re-running of the confirmatory; no worker re-mining; no fixture
repair or new suite; no capacity comparison; no Stage B; NO change to the
registered V2A verdict, the frozen source files, or any committed run
artifact (all reads read-only). The registered numbers and their
interpretation are untouched by this diagnostic's outcome.
