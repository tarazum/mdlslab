# Session brief addendum — CONT-006 STAGE 2, execution half (tasks 4-6)

For the NEXT working session (fresh context). Parent brief:
docs/SESSION-BRIEF-CONT006-STAGE2.md (binding order §1-§6). This addendum
records that tasks (1)-(3) are COMPLETE and frozen (checkpoint rule of the
parent brief: do not carry a tired chain into GPU execution), and pins what
the execution half must decide FIRST. Context docs to read, in order:
SESSION-BRIEF-CONT006-STAGE2.md → this addendum → docs/PREREG-CONT006-
VALIDATOR-V2.md → experiments/cont006/stage2-freeze.json →
experiments/suite-v3/power-results-cont006-stage2.json → LOG.md
2026-10-10 stage-2 entries.

## Completed in the previous session (do not redo; frozen)

- Task 1 (validator audit): prereg docs/PREREG-CONT006-VALIDATOR-V2.md;
  NEW module experiments/cont006/lessons_v2.py (frozen lessons.py
  untouched; lockstep assertion v2-walk == BLOCKED_VOCAB PASS). Enumerated:
  C1 = digits 2-9 (of which 6/7/8/9 are ALSO expected answers of
  answerable cu probes — declared residual risk, mitigated by the
  consumption gate); C2 = 50 expected-null GC option words. Re-run of the
  W3 dispositions: ALL 5 rejected candidates would pass under V2
  (would-be store 9 lessons, 6/6 FP classes) — NEWF's cr-only coverage is
  quantified as validator-selected. Artifact:
  results/CONT-006-VALIDATOR-AUDIT/20261010-222935/audit.json.
- Task 2 (suite v3o): experiments/suite-v3/build_v3o.py; 22 scenarios,
  ids x-9xxx, seeds {9001..9007}, fresh worlds; rt LINEN_CARD defect FIXED
  BY CONSTRUCTION (FULL six-category card in s1 of every rt cluster,
  builder-asserted); cr harder (within-line phrase generalization +
  inherited retraction sub-type); cu chained superseded; dx two lures both
  re-confirmed; GC pools disjoint from the C2 words. v3o PASS V1-V18;
  regressions v3..v3n 9/9 PASS (fixture-validation-regressions-post-v3o.
  json). Power artifact: power_calc_stage2.py / power-results-cont006-
  stage2.json.
- Task 3 (balanced corpus + W4): worker_v4_bundles.py (faithful v3
  rendering + BALANCED selection: per-arm cap 3, total 12, rank order as
  v2/v3; arm A 27% vs ~90% executed; gates green) → worker_v4_bundles.json;
  _w4_driver.py ran the frozen machinery with validator V2 substituted
  (declared, recorded; num_ctx 16384 deviation as W3) + the v3o
  CONSUMPTION GATE. Run root: results/CONT-006-WORKER/
  cont006-worker-v4-20261010-224921 (9/9 calls, 0 parse errors,
  0 truncated; 10 candidates, 9 accepted, 1 rejected for 1-trace support).
  NEWF-v2 store = newf2-store-postgate.json: 8 lessons (FP-1 x3, FP-3a x2,
  FP-3b x2, FP-4 x1), store sha 145cc88cca587459…; the FP-2 lesson
  excluded fail-closed by the consumption gate ('sorting' in applicability
  = a v3o PARCEL answer tag — the gate demonstrably closes the v1 gap).
  FREEZE: experiments/cont006/stage2-freeze.json (26 digests) committed
  BEFORE any consumer inference.

## Next session order (binding)

1. **Task 4 — PREREG FIRST (zero GPU).** Author docs/PREREG-CONT006-
   STAGE2.md (capacity prereg structure; house template PREREG-
   REQUIREMENTS-V2 incl. §6 power) and commit it BEFORE any v3o consumer
   inference. Design points already pinned by the parent brief + this
   session's power artifact — adjust only with recorded justification:
   - Cells per model: NONE (position-invariant BY CONSTRUCTION — nothing
     delivered at either position; declared, one run set reused for both
     positions) + {session-start, probe-time} x {NEUTRAL, NEWF-v2, OLDG} =
     7 distinct cells per model, K = 15 primary clusters x 7 seeds = 105
     runs/cell.
   - Co-primary (per model): d_m = pass(NEWF-v2, probe-time) −
     pass(NONE), pooled; MME 0.20 (power 0.86 at K15x7; seed cuts K15x4/3
     drop to 0.63/0.55 — full 7 seeds REQUIRED). Interaction
     I = d_G8B − d_Q35 is SECONDARY: powered only at I ≥ 0.25 (0.80);
     at the step-3-observed scale (~0.13-0.21) it is directional-only —
     declared. Neutral contrast and session-start contrasts secondary.
   - Session-start arm for the 8B = OPEN HYPOTHESIS (no presumption).
   - NEUTRAL controls matched PER POSITION to the NEWF-v2 block actually
     delivered (word total ±25%, same header/numbered skeleton, NO
     format/workflow instructions, no surface vocabulary — Addendum C
     lesson). Author the two texts at prereg from the frozen store's
     rendered blocks and pin them in the prereg.
   - In-run baseline difficulty gate (replaces a separate calibration
     phase): after the NONE cells, Q35 pooled pass must lie in [0.35,
     0.85] and G8B in [0.15, 0.85]; outside → STOP-OUT-OF-BAND (new suite,
     never a v3o edit) — v3m precedent branch A.3.
   - End-to-end runner wiring = NEW versioned code (wrapper/module pattern
     like delivery_v2/capacity_content_diag; runner.py frozen). Contract:
     persistent memory ON for every cell (CN-012-fixed semantics — the
     fail-closed memory guard is a prerequisite gate), corrected delivery
     mechanics (applicability-annotated routing, full-rule rendering incl.
     the lesson field, no budget drops) at BOTH positions; OLDG uses the
     step-1 G-annotation unchanged; NEWF-v2 gets a fresh annotation filled
     from the frozen store BEFORE the execution freeze.
   - Budget at prereg: G8B ≈ 2.3 s/call (CN-002); Q35 consumer latency
     UNMEASURED — measure at preflight (one warm call) and re-estimate;
     phased execution cell-by-cell with wall guards + checkpoint/resume;
     the run may span sessions (declare the phase order deterministic).
   - Sampling pins: temperature 0.0, seed = run seed, num_predict 256,
     think:false, keep_alive 30m; num_ctx declared in the prereg (the
     corrected full-rule blocks make prompts larger than the replay
     calls; 8192 recommended, headroom-checked at preflight).
   - GC battery + VAL clusters: measured in NONE and NEWF-v2 probe-time
     cells (both models) as declared secondary monitoring (capacity
     degradation + activation); no verdict machinery on them.
2. **Task 5 — execution** (GPU, owner kickoff per phase batch or one
   kickoff with wall guards — record the choice): preflight (digests vs
   stage2-freeze.json, model pins, GPU lock) → NONE cells first (baseline
   gate) → the rest in declared phase order → live telemetry gate before
   analyzers → completeness.
3. **Task 6 — review + close-out**: Fable first if its limit has reset
   (check on the spot; last known reset window 2:30am Kyiv) else codex
   gpt-6-astra (`codex exec -m gpt-6-astra -c model_reasoning_effort=
   '"high"' --sandbox read-only - < prompt.md`); diff-pass on prereg +
   results; fold; owner gate; RESULTS doc + plain-language owner brief
   («підтвердилось/ні» first); LOG; safety scan; push (GitHub links to the
   owner, not local paths).

## Entry conditions (verify before any work)

- git clean on main at the stage-2 freeze commit (see LOG for the sha;
  the freeze manifest references 26 digests — all must verify).
- Ollama 0.34.x up; granite-code:8b (36c3c3b9683b) AND
  qwen36-35b-a3b:mdlslab (8a0fd5da454e) present.
- experiments/cont006/stage2-freeze.json present; every digest verifies.
- The owner's kickoff word for THIS execution half (never-autonomous).

## Out of scope (unchanged from the parent brief)

No frontier/hosted models; no changes to any registered verdict, frozen
file, or committed run artifact; no v3o retrofit; lesson TEXT stays as
authored by the frozen worker prompt; no new UI/tools.

## Kickoff (paste into the fresh session)

"Прочитай labs/continuity/docs/SESSION-BRIEF-CONT006-STAGE2-ADDENDUM.md і
виконай execution half згідно адендуму. Перевір entry-умови до будь-яких
дій."
