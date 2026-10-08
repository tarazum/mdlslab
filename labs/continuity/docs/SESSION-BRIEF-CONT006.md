# Session brief — CONT-006 design + suite + pre-registration draft (lesson extraction)

For the NEXT working session (fresh context). This brief + the repo are the
complete state carrier; no conversation history is needed. House process:
`labs/continuity/PROCESS.md`; conventions and lessons: `LOG.md` tail.

## Entry conditions (verify `git status` clean on main at the current HEAD)

- CONT-002 CLOSED and ACCEPTED 2026-10-08 (ROADMAP "Owner decisions —
  recorded 2026-10-08"): R = 0.989 [0.944, 1.035], retained benefit
  established; the four-cell cross-core machinery is PROVEN and reusable.
- The CONT-006 proposal exists WITH both reviews folded:
  `docs/REFLECTION-V2-PROPOSAL.md` (co-owner fold at 562a1cb; RC-1..RC-5
  from `docs/REVIEW-CONT006-PROPOSAL.md` + RC-1..RC-4 from
  `docs/review-reflection-v2-implementing-agent.md` — read BOTH review files
  as context; the proposal's §"Pre-registration readiness checklist" is the
  binding scope list).
- The provider now carries a top-level `"think": false` pin in EVERY request
  (owner-approved after the CONT-002 pilot; hybrid reasoning cores otherwise
  return empty replies) — new worker code inherits it automatically via
  `OllamaProvider`.
- Available assets: ~50 committed arm-seed traces from CONT-001/CONT-005
  (`results/` — the zero-GPU experience corpus candidates), suite v3k +
  validator (v3k-extended), the four-cell runner pattern
  (`run_cont002.py`), the prereg template pattern
  (`EVALUATION-PREP-CONT002.md` + `PR-REVIEW-CONT002.md` postmortem).

## Scope (one milestone, ZERO GPU — no reflector/worker inference yet)

1. **Design doc `docs/CONT-006-DESIGN.md`**: arms R0/R1/R2/R3 per the
   proposal (R3 INHERITS R2's retrieval/injection machinery, validator,
   prompt slot, renderer, token budget — only the lesson source differs);
   the 3-way data split (experience / validation / held-out transfer) and
   the two-phase rule (NO lesson injection during experience accumulation);
   the reflection-worker architecture (separate process; preferred R2
   reflector qwen36-35b-a3b:mdlslab digest-frozen; same-core reflector =
   secondary comparison); NO_LESSON as first-class output; the lesson
   schema + lifecycle with the TWO validation meanings (deterministic
   evidence validation pre-inference; empirical generalization validation
   with frozen activation rule); anti-salience prose rendering (no quoting
   of the agent's wrong answer inside lesson text); primary endpoint
   candidate = label-form transfer improvement R2 vs R0 with 12–15 clusters;
   the four critical causal tests with test 3 (bad-lesson injection +
   trivially-useful-gold manipulation check) assigned to the PILOT and
   test 4 (cross-model lesson transfer) as a bounded later stage reusing
   the CONT-002 machinery with its own budget + non-estimable clause.
2. **Failure-pattern taxonomy** `docs/CONT006-TAXONOMY.md` — FROZEN before
   any lesson authoring and before transfer-fixture authoring (ex-ante
   contamination protocol); derived from the committed traces' failure
   modes (CN-007 anchoring, CN-008 supersession, trap repeats, format
   misses...) with a NO_LESSON-heavy class declared.
3. **Experience corpus manifest**: select from the committed CONT-001/
   CONT-005 traces per the taxonomy (implementing-agent RN: zero GPU);
   record digests + per-trace failure classes; declare the fresh-supplement
   rule (only if a taxonomy class lacks coverage).
4. **Suite v3l** (fixture protocol v3i as-is; ids x-6xxx; fresh worlds;
   seeds predeclared; disjoint from ALL prior suites): the held-out
   TRANSFER scenarios — different surface wording, same underlying failure
   patterns as the taxonomy; label-form probes; per-seed variant tables.
   Validator extension (`--suite v3l`) + regressions v3..v3k.
5. **Draft `docs/EVALUATION-PREP-CONT006.md`** per
   `docs/PREREG-REQUIREMENTS-V2.md` (all 9 items + all five 2026-10-04
   amendments) covering the proposal's full readiness checklist incl. the
   frozen trigger strategy, lesson-pipeline freeze discipline (raw worker
   log format, validator/dedup/retrieval/renderer digests, Lessons Store
   committed+digested before the first transfer request), R3 blind-gold
   protocol, and the pilot clauses (bad-lesson safety check, R3
   manipulation check, headroom/spread).
6. **Power artifact** (extend the `power_calc_cont002.py` pattern; model
   the R2−R0 cluster structure explicitly; declare the MME ground).

## Non-goals

- NO inference of any kind in this milestone (worker runs, transfer runs —
  all owner-gated after the prereg chain; never-autonomous clause).
- Do NOT mutate `src/continuity/reflection.py` (R1 baseline stays
  byte-stable; Reflection v2 is a NEW versioned module/path).
- Do not touch closed CONT-001/CONT-002/CONT-005 artifacts, frozen
  configs, or closed suites. Do not edit the proposal or its review files.
- Trigger-strategy comparison, same-vs-different reflector comparison, and
  broad cross-model portability are exploratory unless separately
  pre-registered.

## Exit artifacts

`docs/CONT-006-DESIGN.md`, `docs/CONT006-TAXONOMY.md`, experience-corpus
manifest, `fixtures/v3l/` (+ manifest), validator PASS v3l + regressions,
`docs/EVALUATION-PREP-CONT006.md` draft, power artifact, LOG start+result
notes, commit+push, Mnemosyne note. Checkpoint cleanly if over budget
(110 min): commit partials + status note, continue next session.

## Budget

<= 110 min wall, 0 GPU. Fresh-session reading: this brief, PROCESS.md,
REFLECTION-V2-PROPOSAL.md (folded) + both review files, LOG.md tail (last 3
entries), EVALUATION-PREP-CONT002.md + PR-REVIEW-CONT002.md (template +
postmortem), `experiments/suite-v3/build_v3k.py` (builder pattern),
`validate_fixtures_v3.py` (extension points), GATE-CONT002.md (gate
discipline precedent).

## Chain after this milestone

Independent PR-REVIEW of EVALUATION-PREP-CONT006 (reviewer queue: Fable →
Opus → local GLM 5.3 Flash) → fold → owner gate (explicit acceptance before
ANY worker/transfer inference) → implement + freeze the lesson pipeline
(worker module, raw candidate log, validator/dedup, Lessons Store; digests)
→ R3 blind gold-lesson authoring (experience-set only) → non-executor
contamination/freeze gate → pilot (incl. bad-lesson + manipulation checks)
→ pilot-gate checkpoint → confirmatory → bounded cross-model test 4
(CONT-002 machinery). Every GPU step owner-visible.

## Owner checkpoints

One: after the PR-REVIEW fold, the owner approves the pre-registration
before ANY behavioral inference (never-autonomous). A second natural
touchpoint: the frozen taxonomy + corpus selection before lesson authoring
(if the owner wants eyes on the failure-pattern classes early).
