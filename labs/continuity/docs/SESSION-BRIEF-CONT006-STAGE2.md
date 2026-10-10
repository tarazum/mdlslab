# Session brief — CONT-006 STAGE 2: v3o end-to-end suite (validator audit + repaired rt + balanced faithful mining + two-model delivery-position comparison)

For the NEXT working session (fresh context). This brief + the repo are
the complete state carrier. House process: labs/continuity/PROCESS.md.
Context docs (read in this order): docs/RESULTS-CONT006-CAPACITY-CONTENT.md
(post-fold, incl. Addenda A–C) → docs/REVIEW-ASTRA-CONT006-CAPACITY-CONTENT.md
(curation appendix) → docs/RESULTS-CONT006-DELIVERY-DIAG.md → LOG.md
2026-10-10 (step-1 and step-3 entries).

## Where things stand (do not re-litigate)

- Step 1 (corrected delivery, probe-level): gold-arm harm recovers to
  memory-only parity; worker-arm harm does not recover; residual has
  competing explanations.
- Step 3 (capacity × content, probe-level): Q35 (qwen36-35b) 56/56 in
  EVERY condition (ceiling — injection-robust, lesson benefit
  unmeasurable at this difficulty); 8B loses 7–12/56 to every block
  (filler reproduced OLDW/NEWF deficits; the OLDG deficit is
  cr-8003-concentrated and lesson-associated with a distinct error
  signature); the rt-8204 gain is filler-associated (block-present
  effect, not lesson content); no tested lesson text has helped either
  model; lesson-echo 0/84 everywhere.
- Owner decision (chat 2026-10-10): «йдемо за рекомендацією» — stage 2
  authorized. If the kickoff says to run this brief, that is the
  authorization.

## Scope (ONE stage, likely two working sessions — checkpoint inside)

Goal: the first end-to-end (not replay) lesson-transfer test on a surface
where the STRONG model has headroom, with delivery position varied and
every lesson claim controlled by matched neutral blocks. Binding order:

1. **Validator audit (zero GPU, FIRST — prerequisite)**: enumerate the
   anti-salience blocked-vocabulary collisions that rejected 5/9 W3
   candidates ('forward' in "carry forward"; standalone digits 2–5 from
   FP-taxonomy class titles and numbered behavioral steps — see RESULTS
   Addendum A + REVIEW finding 3). Fix as NEW versioned code (e.g. an
   allowlist/collision-report module next to the worker, or a v2 check
   function) — NEVER edit frozen src/continuity/lessons.py. Pre-register
   the fix rule; re-run the W3 disposition audit against it (report
   which rejected candidates would pass).
2. **Suite v3o authoring + validation (zero GPU)**: new fixtures per the
   house pattern (fresh worlds; ids x-9xxx; build_v3o.py + validator
   run): (a) rt clusters with the FULL rule card supplied IN-SESSION
   (the LINEN_CARD defect fixed by construction — no probe may expect a
   category whose rule was never stated); (b) difficulty calibrated so
   the strong model (Q35) has headroom — use harder cr/dx variants
   (v3n's dx lure-salience pattern is the proven lever) and a small
   zero-GPU smoke calibration if needed; (c) GC battery unchanged in
   kind; (d) regression checks v3..v3n PASS. Power calc artifact for the
   new design (MME + power at the planned K; template §6).
3. **Balanced faithful corpus + W4 worker pass (small GPU)**: re-select
   the experience corpus BALANCED across memory conditions (the CONT-005
   C2 corpus has A/T0/T1 traces — defect 2 of the audit), rebuild
   bundles as worker_v4 (faithful v3 rendering + balanced selection),
   run the W-worker (same frozen machinery, custom-provider ctx pin as
   in W3) with the AUDITED validator; store = NEWF-v2. Store freeze
   BEFORE any consumer inference (house rule).
4. **Pre-registration (template discipline)**: arms/conditions fixed
   BEFORE any v3o inference. Minimum design (adjust at prereg, keep the
   logic): models {G8B, Q35} × delivery positions {session-start,
   probe-time} × content {NONE, NEUTRAL-matched-per-position, NEWF-v2,
   OLDG} with corrected delivery fixed; primary = lesson-minus-baseline
   INTERACTION per model; neutral controls matched PER POSITION; the
   session-start arm for the 8B is an OPEN HYPOTHESIS (step-3 suggests
   probe-time injection is the 8B's problem — do not presume session-
   start is safe). End-to-end runs need runner wiring for the corrected
   delivery positions as NEW versioned code (runner.py is frozen —
   wrapper/module pattern like delivery_v2/capacity_content_diag).
5. **Execution (GPU)**: phased with the house gates (freeze →
   preflight → live telemetry gate before analyzers → completeness).
   Budget estimate at prereg; wall guards; both model digests pinned.
6. **Review + close-out**: Fable if its limit has reset (check first —
   last known reset window 2:30am Kyiv; the step-1/3 rounds fell back
   to codex) — else GPT-6 Astra via codex (working invocation:
   `codex exec -m gpt-6-astra -c model_reasoning_effort='"high"'
   --sandbox read-only - < prompt.md`). Diff-pass on prereg + results;
   fold; owner gate; results doc + plain-language owner brief
   («підтвердилось/ні» first); LOG; safety scan; push.

CHECKPOINT: if (1)–(3) complete and the session is deep, STOP after
committing the freeze; the execution runs in the NEXT session via a
short addendum brief. Do not carry a tired chain into GPU execution.

## Out of scope (non-goals)

No frontier/hosted models (owner-gated external access); no changes to
any registered verdict, frozen file, or committed run artifact; no
retrofit of v3n/v3l/v3m; no new UI/tools; lesson TEXT stays as authored
by the frozen worker prompt (content improvements are a later owner
decision, not this stage's lever).

## Entry conditions (verify before any work)

- git clean on main at HEAD ≥ 7ceddc6; LOG step-3 close entry intact.
- Ollama 0.34.x up; granite-code:8b (36c3c3b9683b) AND
  qwen36-35b-a3b:mdlslab (8a0fd5da454e) present.
- The step-1/step-3 artifacts exist: results/CONT-006-DELIVERY-DIAG/,
  results/CONT-006-CAPACITY/, results/CONT-006-WORKER/
  cont006-worker-v3-20261010-203420/, experiments/cont006/
  capacity-freeze.json.
- The owner's kickoff word for THIS stage (never-autonomous).

## Kickoff (paste into the fresh session)

"Прочитай labs/continuity/docs/SESSION-BRIEF-CONT006-STAGE2.md і виконай
stage згідно бріфа. Перевір entry-умови до будь-яких дій."
