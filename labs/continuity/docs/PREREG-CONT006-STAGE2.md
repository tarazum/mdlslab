# PREREG — CONT-006 STAGE 2 (end-to-end lesson transfer on v3o: delivery position × content × model)

Written and frozen BEFORE any v3o consumer inference (2026-10-11; owner
authorization: stage-2 brief kickoff, then «Тут, зараз — задача 4» for the
prereg half). Prerequisites complete and frozen (stage2-freeze.json, 26
digests): validator V2 audit (task 1), suite v3o (task 2), balanced W4 +
NEWF-v2 store (task 3). This is the FIRST end-to-end (not replay)
lesson-transfer design of the arc. Registered verdicts and all committed
run artifacts stay READ-ONLY.

## 1. Question

Steps 1+3 left: corrected probe-time delivery still nets a residual on the
8B with competing explanations (content / capacity / interference); the
strong model's lesson response is unmeasured (v3n ceiling); session-start
delivery is untested as a position; the old gold content is untested under
corrected mechanics. This experiment separates, END-TO-END (memory on,
full sessions, real delivery):

- CONTENT: does the faithful balanced NEWF-v2 store move pass rates
  relative to (a) nothing and (b) a per-cluster-matched neutral block?
- POSITION: does the same block behave differently at session-start vs
  immediately before the probe (the 8B's open hypothesis)?
- MODEL: do the 8B and the 35B respond differently (interaction), on a
  surface where BOTH have headroom (in-run verified)?
- GENERATION: does the old gold content (OLDG) behave differently from
  NEWF-v2 under identical corrected mechanics?

## 2. Design

- **Suite**: v3o (frozen, sha in stage2-freeze.json). 15 primary clusters
  (CR4 + CU4 + RT3 + DX2 + DR2) × 7 seeds {9001..9007}; 4 VAL clusters;
  3 GC scenarios.
- **Models** (digest-pinned at preflight; NO downloads): G8B =
  granite-code:8b (36c3c3b9683b); Q35 = qwen36-35b-a3b:mdlslab
  (8a0fd5da454e). Sampling pins IDENTICAL across models: temperature 0.0,
  seed = run seed, num_ctx 8192 (headroom-gated: no call may come within
  512 tokens of the window), num_predict 256, think:false (frozen
  provider), keep_alive 30m, timeout 600 s. Determinism caveat PB-071/
  CN-003 applies; there is NO replay noise-floor arm in an end-to-end
  design — every CI below inherits that limitation (declared).
- **Cells** per model (NONE is position-invariant BY CONSTRUCTION —
  nothing is delivered at either position; one run set serves both
  positions):
  1. NONE (all 22 scenarios incl. VAL+GC) — R0-equivalent baseline
     (persistent memory, no lessons); mechanical parity with the frozen
     runner enforced by the --smoke gate.
  2. NEWF2 @ probe_time (15 primary + 4 VAL)
  3. NEWF2 @ session_start (15 primary)
  4. NEUTRAL @ probe_time (15 primary)
  5. NEUTRAL @ session_start (15 primary)
  6. OLDG @ probe_time (15 primary)
  7. OLDG @ session_start (15 primary)
- **Mechanics** (stage2_endtoend.py, NEW versioned code; frozen
  runner imported read-only): persistent memory ON in every cell (the
  CN-012-fixed R0 path: per-exchange appends, session-start injection at
  session ≥ 2, flat renderer, top-8, fail-closed memory guard marking
  runs INVALID on zero appends or zero non-empty injections). Delivery =
  the step-1 corrected mechanism (annotated routing, full-field rendering
  "Title. When …: Rule: … Behavior: …", no budget):
  - probe_time: ONE system message immediately before the probe turn.
  - session_start: ONE system message at the start of EVERY session, in
    the frozen R2/R3 lesson slot (after the memory block) — the ORIGINAL
    delivery position with corrected content mechanics.
- **GC handling**: GC scenarios run ONLY in the NONE cells; NEWF2@pt
  skips them because no lesson applies to GC (identical prompts by
  construction — the analyzer reports GC from NONE; zero duplicate
  calls). VAL clusters run in NONE and NEWF2@pt only (activation
  monitoring).
- **Budget**: 812 scenario-runs per model (1624 total), ≈4.7 agent calls
  per run ≈ 7,600 calls. G8B ≈ 2.3 s/call (CN-002) ≈ 5 h. Q35 consumer
  latency is UNMEASURED — measured at preflight (2 timed calls); if
  10–20 s/call the Q35 half is 21–42 h wall, executed PHASED (one cell
  per --run-phase invocation), wall-guarded (4 h/phase, no new cell-seed
  starts past the guard), resumable (completed cell-seed dirs skipped),
  across sessions if needed. Budget per cell-seed: 130 turns / 400k
  tokens / 5400 s (V2A convention).

## 3. Endpoints (fixed BEFORE any v3o inference)

- **Co-primary (per model)**: d_m = pass(NEWF2@pt) − pass(NONE), pooled
  over 15 clusters × 7 seeds; two-sided 95% CLUSTER percentile bootstrap
  (10k, RNG 20261011) over cluster deltas. **MME 0.20** (power 0.86 at
  K15×7 conservative; power-results-cont006-stage2.json rows W2/W9;
  seed cuts to 4/3 drop power to 0.63/0.55 — full 7 seeds REQUIRED).
  Branches: established (CI>0 AND d≥MME) / directional-below-MME (CI>0,
  d<MME) / harm (CI<0) / no-difference (includes 0). Sub-MME effects are
  NOT claimable at this design's power.
- **Secondary** (same bootstrap; no MME branch machinery beyond CIs):
  - Interaction I = d_G8B − d_Q35: powered ONLY at |I| ≥ 0.25 (row I8:
    0.800); at the step-3-observed scale (~0.13–0.21) it is DIRECTIONAL
    ONLY — declared.
  - Neutral contrast (NEWF2@pt − NEUTRAL@pt) per model.
  - Session-start (OPEN hypothesis, no presumption):
    (NEWF2@ss − NONE) and (NEWF2@ss − NEWF2@pt) per model.
  - OLDG: (OLDG@pt − NONE), (OLDG@ss − NONE) per model.
- **Exploratory**: per-family decomposition; error modes (wrong-label vs
  format-miss); lesson-echo (verbatim 6-gram block↔reply, expected 0);
  the OLDG 'sorting' collision count on rt (declared confound, below);
  GC guess-rate/position monitoring (NONE cells); VAL activation.
- **Baseline difficulty gate (P0, pre-registered STOP branch)**: after
  each NONE phase, pooled PRIMARY pass must lie in G8B [0.15, 0.85], Q35
  [0.35, 0.85]. Outside → STOP-OUT-OF-BAND: the v3o difficulty levers
  failed (ceiling or floor); the stage halts; a NEW suite is authored,
  never a v3o edit (v3m precedent, branch A.3).

## 4. Predictions (fixed directions, registered before inference)

- **P1 (G8B content)**: d_G8B ≤ 0 — probe-time block presence continues
  to hurt or stay flat on the 8B end-to-end (step-1 residual, step-3
  block effects). A CI>0 established branch would be the arc's FIRST
  positive lesson result and falsifies this prediction.
- **P2 (Q35 content)**: d_Q35 ≥ 0 — the strong model with headroom
  extracts benefit or stays unharmed (step-3 injection-robustness at
  ceiling). Two-sided CI; established-up would demonstrate faithful
  lesson VALUE for a stronger model.
- **P3 (interference isolation)**: if NEWF2 ≈ NEUTRAL < NONE on the 8B,
  generic prompt interference reproduces end-to-end (step-3 pattern);
  if NEWF2 > NEUTRAL, content-specific value exists beyond block
  presence.
- **P4 (position, open)**: (NEWF2@ss − NEWF2@pt) ≠ 0 in either direction
  is informative; NO presumption that session-start is safe for the 8B.
- **P5 (generation)**: OLDG ≤ NEWF2 per model under identical mechanics
  (the corpus-shaped old generation underperforms the faithful balanced
  one) — directional.
- **P6 (interaction)**: expected at the step-3 scale (~0.13–0.21) IF P1
  and P2 hold — directional-only at this K (declared power limit).

## 5. Delivery annotations and control texts (single source:
experiments/cont006/stage2_design.py — digested by the EXEC FREEZE; the
tables below are informative copies)

- **NEWF2 annotation** (19 clusters incl. VAL): cr-9001 [W-002];
  cr-9002 [W-005]; cr-9003 [W-004]; cr-9004 [W-001, W-007]; cr-9005/VAL
  [W-005]; cu-9101/9102/9105 [W-003]; cu-9103/9104 [W-007];
  rt-9201..9204 [W-002, W-003]; dx-9401..9403 [W-009];
  dr-9301/9302 [W-009].
- **OLDG annotation** (15 primary): every cluster [mechanism-fit G-lesson
  + LL-G-007] — cr-9001 [G-004, G-007]; cr-9002/9003 [G-005, G-007];
  cr-9004 [G-002, G-007]; cu-9101/9102 [G-001, G-007]; cu-9103/9104
  [G-002, G-007]; rt-9201..9203 [G-003, G-007]; dx/dr [G-006, G-007].
- **NEUTRAL control**: numbered-line shape matched (line count == the
  NEWF2 set size for that cluster); content = fixed descriptive pool
  (kettle/cat/clock/rain/shelf/geese — no instructions, no surface
  vocabulary, no format/workflow content; Addendum-C lesson); word total
  inside ±25% of the NEWF2 block per cluster (mechanical composer +
  checker — all 15 clusters verified in band at authoring).
- **Flagged judgment calls** (annotation was implementer-judged BEFORE
  inference; review may disagree — disagreements are recorded, the table
  is the executed treatment): F1 rt gets W-002+W-003 because the
  mechanism-fit FP-2 lesson was consumption-gate-excluded ('sorting');
  F2 dr gets the FP-4 lesson because the FP-5 lesson failed mining
  validation (1-trace support); F3 cu-superseded gets W-003 over W-006
  (W-006's withdrawal clause inert); F4 OLDG sets carry G-007 everywhere
  (step-1 G-annotation pattern).
- **Declared confound**: LL-G-003's text contains 'sorting', a v3o answer
  tag (rt options). The OLDG arm delivers the old store AS AUTHORED (its
  generation predates the v3o vocabulary discipline — that IS the old-
  content treatment); the analyzer MEASURES the collision
  (rt observed-label == 'sorting' counts per OLDG cell) and every OLDG-rt
  number carries this caveat. NEWF2 and NEUTRAL are fail-closed clean
  (verified at authoring: zero answer-vocabulary collisions).

## 6. Gates, freeze, run, analysis (binding order)

1. EXEC FREEZE (stage2-exec-freeze.json): digests of this prereg,
   stage2_design.py, stage2_endtoend.py, analyze_stage2.py, the parent
   brief + addendum, and the task-3 stage2-freeze.json — committed BEFORE
   the first --run-phase. All freeze digests are CRLF-NORMALIZED (CR-LF
   stripped before hashing): the first stage2-freeze emit hashed
   pre-normalization bytes and git's autocrlf checkout invalidated 5/26
   raw digests (all content-equal after CR-strip — caught by this
   preflight BEFORE any consumer inference; both manifests re-emitted
   once with the declared normalization; recorded as CN-013).
2. --smoke (zero GPU) PASS — mandatory before preflight: design checks,
   NONE parity vs the frozen R0 runner (byte-equal provider message
   sequences), injection-position asserts (probe-time exactly-once
   immediately before the probe; session-start every-session after
   memory), CN-012 guard self-test.
3. --preflight: all freeze digests verify; both model pins match; ollama
   0.34.x; Q35 latency measured (2 timed calls) and the wall budget
   re-estimated BEFORE phase 8 starts.
4. Phases 1–14 in declared order (G8B block, then Q35; NONE first per
   model). After phases 1 and 8 the baseline gate (P0) is evaluated;
   violation halts the chain (STOP-OUT-OF-BAND, owner brief).
5. --gate (live telemetry + completeness) MUST PASS before the analyzer;
   the analyzer refuses to run otherwise (fail-closed).
6. analyze_stage2.py (frozen) → stage2-results.json; verdict branches as
   §3; no post-hoc endpoint changes — exploratory tables are labeled.
7. Review + close-out per the addendum (Fable → codex routing); owner
   gate; results + plain-language owner brief; LOG; push.

## 7. Non-goals (binding)

No frontier/hosted models; no changes to any registered verdict, frozen
file, or committed run artifact; no v3o retrofit (difficulty out of band →
a NEW suite); lesson TEXT stays as authored by the frozen worker prompt
(the consumption gate EXCLUDES rather than edits); the OLDG store is
delivered as authored (measured confound, never edited); no new UI/tools;
no pilot/confirmatory split — this is one pre-registered run with an
in-run difficulty gate.
