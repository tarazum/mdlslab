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

## STATUS UPDATE 2026-10-11 (task 4 COMPLETE — prereg half done in-session)

Task 4 is DONE and frozen; the next session is EXECUTION-ONLY. Completed
after the checkpoint with owner approval («Тут, зараз — задача 4;
GPU-виконання — у свіжій сесії»):

- **PREREG-CONT006-STAGE2.md** — full prereg: cells (7/model; NONE
  position-invariant), co-primary per model d_m = NEWF2@pt − NONE at MME
  0.20 (power 0.86; 7 seeds REQUIRED), interaction directional-only below
  I=0.25 (declared), predictions P1–P6, in-run baseline difficulty gate
  (G8B [0.15,0.85], Q35 [0.35,0.85], STOP-OUT-OF-BAND), phases 1–14,
  wall guards, budget (≈7,600 calls; Q35 latency measured at preflight).
- **stage2_design.py** — annotations (NEWF2 19 clusters, OLDG 15; flagged
  calls F1–F4), neutral pool + mechanical composer (all 15 clusters in
  ±25% band), vocab checks (NEWF2/NEUTRAL fail-closed clean; the OLDG
  'sorting' collision DECLARED as the old-generation confound, measured
  by the analyzer, never edited).
- **stage2_endtoend.py** — the end-to-end wrapper (NEW versioned code;
  frozen runner imported read-only): R0-equivalent mechanics + positional
  delivery, CN-012 fail-closed guard, 14 phases, resumable, wall-guarded,
  per-cell calls telemetry. **--smoke PASS incl. NONE-parity vs the
  frozen runner (byte-equal message sequences)**.
- **analyze_stage2.py** — frozen analyzer (self-test PASS); refuses to
  run before --gate PASS.
- **stage2-exec-freeze.json** — 12 digests, committed BEFORE any v3o
  consumer inference.

## Next session order (binding, EXECUTION ONLY)

1. `python experiments/cont006/stage2_endtoend.py --smoke` — MUST PASS
   (zero GPU precondition re-verification).
2. `--preflight` — freeze digests (stage2-freeze + stage2-exec-freeze),
   model pins, ollama version, Q35 latency (2 timed calls) + budget
   re-estimate BEFORE phase 8.
3. `--run-phase N --run-root <path>` in order 1..14 (G8B block first);
   after phases 1 and 8 evaluate `--baseline-gate G8B|Q35` — violation =
   STOP-OUT-OF-BAND (halt + owner brief). Phases resumable; wall guard
   4 h/phase; Q35 phases may span sessions.
4. `--gate --run-root <path>` — live telemetry + completeness; MUST PASS;
   writes gate-PASS.json (the analyzer refuses to run without it).
5. `python experiments/cont006/analyze_stage2.py --run-root <path>` —
   frozen analysis → stage2-results.json.
6. Review + close-out (unchanged): Fable if reset (check on the spot;
   2:30am Kyiv window) else codex gpt-6-astra (working invocation in the
   parent brief §6); diff-pass on prereg + results; fold; owner gate;
   RESULTS doc + plain-language owner brief («підтвердилось/ні» first);
   LOG; safety scan; push (GitHub links to the owner).

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
