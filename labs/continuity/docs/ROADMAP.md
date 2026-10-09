# Continuity — autonomous arc roadmap

- **Arc goal:** from smoke to first ablation signal — complete P0b (pilot + sizing) and P1a (arms B–E as MVPs), and produce a first **exploratory** CONT-001 multi-arm result. The confirmatory CONT-001 run stays owner-gated.
- **Arc status:** COMPLETE (2026-10-02 02:21 FLEDT). All milestones M1–M8 DONE; closing record in `docs/ARC-REPORT.md`; owner decisions **RECORDED 2026-10-04** (see "Owner decisions" below).
- **Armed:** 2026-10-01 22:30 FLEDT. **Arc deadline:** 2026-10-02 11:30 FLEDT (extended 22:35 per owner: all owner work consolidated at arc end). After the deadline, every milestone executor must no-op.
- **No milestone waits on the owner.** Every owner decision is collected in the Owner morning list at the end of this file; the chain runs unattended.
- **Execution model:** one milestone per fresh session. The brief below is the only required reading; the repository is the sole state carrier between sessions (LOG.md, results/, git). Do not rely on conversation history.
- **Status legend:** TODO / IN_PROGRESS / DONE / BLOCKED (reason recorded in LOG.md) / SKIPPED (a written condition failed; reason recorded).

| Milestone | Stage | Status |
| --- | --- | --- |
| M1 | P0b: fixture suite v2 + arm A variance/headroom pilot + sizing | DONE |
| M2 | P1a: arm B — SQLite persistent memory | DONE |
| M2b | CONT-002 mechanics smoke (conditional: >= 45 min before deadline) | DONE |
| M3 | P1a: arm C — validated self-model | DONE |
| M4 | P1a: arm D — reflection/consolidation | DONE |
| M5 | P1a: arm E — world model + bounded policy | DONE |
| M6 | Exploratory CONT-001 pass (all arms) + pre-registration v1 committed | DONE |
| M6b | Independent pre-registration review (GO/NO-GO) | DONE |
| M7 | Confirmatory CONT-001 (conditional: M6b GO + >= 2h before deadline) | DONE |
| M8 | Final: housekeeping, arc report, owner morning list | DONE |

## Executor protocol (every session)

1. Read this file fully. If the arc is complete or past deadline → stop with a one-line reply.
2. Pick the first milestone with status **TODO**. Never pick IN_PROGRESS or BLOCKED for fresh execution: for IN_PROGRESS, check LOG.md and the shared GPU lock — if the milestone's latest start/progress note is under 2 hours old **or** the lock is held, another executor is active: stop without touching it. If the note is older than 2 hours and the lock is free, the executor died and you may resume from its checkpoint. Verify entry conditions of whatever you picked. Fail-closed: unmet conditions → LOG.md note + stop, no improvisation. Mark the milestone IN_PROGRESS in the status table as your first write, before doing any work.
3. Follow `labs/continuity/PROCESS.md` (start-note, artifact-proof, CN-NNN findings, budgets, sampling params per request, same-day lessons).
4. Take the shared GPU lock (`shared/tooling/agent-resource-coordination/`) around any local inference.
5. Finish within 110 minutes or checkpoint cleanly (LOG.md, status IN_PROGRESS, commit, stop).
6. Completion = exit artifacts committed and pushed + LOG.md numbers + status updated to DONE + a Mnemosyne note.

## M1 — P0b: fixture suite v2 + arm A pilot + sizing

- **Goal:** measure run-to-run spread of candidate endpoints for arm A and size CONT-001.
- **Entry:** repo clean on `origin/main`; smoke artifacts exist under `results/CONT-000/`.
- **Scope:** extend `fixtures/v1` to >= 8 scenarios (add >= 1 distractor scenario: semantically related but irrelevant facts; >= 1 contradiction scenario: a fact corrected in a later session); predeclare seeds {11,22,33,44,55} in the run config before any run; run arm A over the full suite x all seeds (one process, warm model — PB-070); write `docs/SIZING.md` with per-family pass-rate spread, token/latency stats, and a recommended seed/session count for CONT-001; update the lab README state.
- **Non-goals:** any memory/self-model code; changing the runner's arm-A semantics.
- **Exit artifacts:** new fixtures; `results/CONT-000/pilot-armA-<run_id>/` (traces + aggregate JSON); `docs/SIZING.md`; LOG.md entry with numbers; README state updated.
- **Budget:** <= 90 min wall clock, <= 60 min GPU.

## M2 — P1a: arm B — SQLite persistent memory

- **Goal:** the "no persistent memory" ablation gains its counterpart.
- **Entry:** M1 DONE; SIZING.md exists.
- **Scope:** `src/continuity/memory.py` — SQLite-backed store (MVP operations: append episode, keyword/substring retrieval, export/import for CONT-002 later); a memory injection step in the runner behind an arm flag (`arm=A|B`), same prompts otherwise; smoke (1 scenario) + mini-pilot (3 seeds, full suite) for arm B; an A-vs-B table for `delayed_recall` in the results; LOG.md with numbers.
- **Non-goals:** semantic/vector retrieval; consolidation; self-model; changing arm A.
- **Exit artifacts:** memory.py + runner wiring; smoke + pilot artifacts; comparison table JSON; LOG.md; status DONE.
- **Budget:** <= 110 min, <= 30 min GPU.

## M2b — CONT-002 mechanics smoke (conditional, owner-ordered 2026-10-01)

- **Goal:** prove the state export/import mechanics between two different cores — plumbing only, zero behavioral claims. Placed right after M2 deliberately: it de-risks the CONT-002 state format BEFORE arms C–E add self-model/reflection/policy state on top of it.
- **Entry:** M2 DONE; the local GGUF `C:\Models\qwen36_Q4_K_M\Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` exists; at least 45 minutes remain before the arc deadline. If the time condition fails, mark SKIPPED (morning list picks it up).
- **Scope:** import the local GGUF into Ollama via a Modelfile (`FROM <local path>` — a local import, not a download); record the created model's digest; run the learning session of one scenario (dr-0001, seed 11) on core A (`granite-code:8b`, arm B) and export its persistent state; import the state and run the held-out probe session on core B (Qwen3.6-A3B) twice — once with the imported state, once clean. Verify: export/import round-trip is schema-valid and error-free; the state renders into core B's context; all traces re-validate from disk. Artifacts under `results/CONT-000/cont002-mechanics-<run_id>/`; LOG.md verdict per check. If the probe passes under B+state, record it as an observation only — no transfer claims.
- **Non-goals:** behavioral comparison; the retained-benefit ratio; any CONT-002 conclusion; multi-seed runs; judging model quality; fixing Ollama template issues beyond recording them as CN findings.
- **Exit artifacts:** imported-model digest record; core-A state export; two core-B traces; LOG.md mechanics verdict.
- **Budget:** <= 45 min, <= 30 min GPU (the 22 GB model load dominates).

## M3 — P1a: arm C — validated self-model

- **Goal:** arm C = B + a versioned self-model with measured (not self-declared) capabilities.
- **Entry:** M2 DONE.
- **Scope:** `src/continuity/selfmodel.py` — versioned JSON store; capability estimates derived from pilot metrics (per-family pass rates) with uncertainty; deterministic validation before commit; the runner injects the current self-model summary into the system prompt for arm C; smoke + mini-pilot (3 seeds); LOG.md.
- **Non-goals:** LLM-proposed revisions (that is arm D); behavior beyond prompt injection.
- **Exit artifacts:** selfmodel.py + wiring; artifacts; LOG.md.
- **Budget:** <= 110 min, <= 30 min GPU.

## M4 — P1a: arm D — reflection/consolidation

- **Goal:** arm D = C + a bounded post-session reflection pass.
- **Entry:** M3 DONE.
- **Scope:** `src/continuity/reflection.py` — after each session, one bounded pass (LLM or deterministic MVP) that proposes episode summaries / self-model revisions as *proposals*; a deterministic validator (schema + evidence reference required) commits or rejects; immutable events are never rewritten; arm D wiring; smoke + mini-pilot; any observed reflection drift → CN-NNN immediately.
- **Non-goals:** autonomous policy changes; touching permissions/tools; background cycles (CONT-003).
- **Exit artifacts:** reflection.py + validator + wiring; artifacts; LOG.md.
- **Budget:** <= 110 min, <= 40 min GPU.

## M5 — P1a: arm E — world model + bounded policy

- **Goal:** arm E = D + explicit ex-ante predictions and a bounded action policy.
- **Entry:** M4 DONE.
- **Scope:** `src/continuity/worldmodel.py` (record prediction + confidence before answering probe turns; compare with outcome after) and `src/continuity/policy.py` (choose among a fixed action set, MVP: {answer_direct, retrieve_then_answer}; deterministic rules on uncertainty/repetition signals); calibration counters in telemetry; smoke + mini-pilot; LOG.md.
- **Non-goals:** Jev/System One integration (later comparison); unbounded action spaces.
- **Exit artifacts:** worldmodel.py, policy.py + wiring; artifacts; LOG.md.
- **Budget:** <= 110 min, <= 40 min GPU.

## M6 — exploratory CONT-001 pass

- **Goal:** first multi-arm comparison, explicitly **exploratory**, feeding the pre-registration.
- **Entry:** M1–M5 DONE.
- **Scope:** run arms A–E over the full suite with the seed count recommended by SIZING.md (hard cap: 3h GPU total; if over budget, reduce seeds and record the reduction); normalized results table (primary endpoint candidate: repeated-mistake rate / delayed-recall pass rate; report per-arm with spread); write `docs/EVALUATION-PREP.md` — pre-registration v1 (primary endpoint, primary contrast, minimum meaningful effect, thresholds, aggregation, missing-run handling, held-out data plan), committed BEFORE any confirmatory data exists; LOG.md with the table.
- **Non-goals:** executing the confirmatory run (M7); promoting secondary metrics; CONT-002.
- **Exit artifacts:** results/CONT-001-exploratory/…; EVALUATION-PREP.md; LOG.md.
- **Budget:** <= 150 min, <= 180 min GPU. (Executor may split into two checkpoints.)

## M6b — independent pre-registration review

- **Goal:** a fresh session checks the pre-registration before any confirmatory data exists (author/reviewer separation, same pattern as the proposal/review cycle).
- **Entry:** M6 DONE.
- **Scope:** verify against a fixed checklist: the primary endpoint is measurable with the existing harness; the primary contrast and minimum meaningful effect are stated and falsifiable; aggregation and treatment of missing/failed runs are defined; the held-out plan uses scenarios/seeds not used in M6; thresholds are not reverse-engineered from the exploratory results to guarantee success. Write `docs/PR-REVIEW.md` with verdict GO or NO-GO plus reasons. Do NOT edit EVALUATION-PREP.md; if a fix is needed, record it as a required change and verdict NO-GO.
- **Non-goals:** modifying the pre-registration; running anything.
- **Exit artifacts:** PR-REVIEW.md; LOG.md; status DONE (record the verdict regardless of GO/NO-GO).
- **Budget:** <= 30 min, 0 GPU.

## M7 — confirmatory CONT-001 (conditional, agent-pre-registered)

- **Goal:** execute the frozen pre-registration on fresh held-out data, fully autonomously, labeled as pending owner acceptance.
- **Entry:** M6b DONE with verdict GO **and** at least 2 hours remaining before the arc deadline. If either condition fails, mark M7 SKIPPED with the reason and leave the run to the owner morning list — never run it late or rushed.
- **Scope:** generate the held-out scenario set per EVALUATION-PREP.md (new scenarios, never used for calibration; synthetic and public-safe); freeze and record the config; run arms A–E exactly per the frozen protocol (GPU cap 3h; if over budget, stop and record — do not silently reduce seeds); produce the analysis strictly as pre-registered; label every artifact and the LOG entry "agent-pre-registered, pending owner acceptance"; no post-hoc metric switching.
- **Non-goals:** deviating from the frozen protocol; CONT-002; external claims.
- **Exit artifacts:** results/CONT-001-confirmatory/…; analysis per pre-registration; LOG.md; status DONE or SKIPPED (with reason).
- **Budget:** <= 150 min, <= 180 min GPU.

## M8 — final: housekeeping, arc report, owner morning list

- **Goal:** close the arc cleanly regardless of where the chain stopped.
- **Entry:** always available; run when no earlier milestone is open (or the chain is BLOCKED).
- **Scope:** triage open CN-NNN cases; retry the deferred Mnemosyne consolidation; write `docs/ARC-REPORT.md` (numbers, failures, what ran and what did not, an explicit "pending owner acceptance" section); assemble the Owner morning list with concrete pointers; mark the arc COMPLETE at the top of this file; final LOG.md entry; commit + push; Mnemosyne note.
- **Non-goals:** new features; starting M7 if it was skipped.
- **Exit artifacts:** ARC-REPORT.md; completed statuses; clean git state.

## Owner morning list (all owner work is here; nothing before it)

1. Read `docs/ARC-REPORT.md`, `docs/SIZING.md`, `docs/PR-REVIEW.md`, and (if M7 ran) the confirmatory results.
2. Accept or reject the agent-pre-registered confirmatory result: accept / re-run with amendments / discard.
3. Decide the CONT-002 program. **No download is required** — local core-B candidates already exist: `Qwen3.6-35B-A3B` GGUF in `C:\Models` (22 GB MoE with ~3B active parameters — fastest option under VRAM offload; import into Ollama via a one-line Modelfile), plus Ollama-local `gemma4:26b` / `qwen3.8:27b` / `devstral-small-2` / `starcoder2:instruct` (9–18 GB dense; slower offload, but 63 GB RAM makes them viable). The 2×2 analysis (R = ΔB/ΔA with the B+clean cell) is designed to tolerate intrinsic capability differences, so any instruct-capable core works. A ~4–5 GB compact download remains an optional speed optimization, not a requirement. The M2 storage format is already in place.
4. External actions, publication decisions, any scope change to this roadmap.
5. Finding CN-005 (GPU idle threshold cannot attribute residency-only load in the shared coordination tooling) explicitly requests an owner decision on the shared tooling direction.
6. Review the CONT-005 "Memory Trust Hierarchy" next-cycle proposal (owner-added, commit c8176c9): scope, priority, and whether it becomes the next arc after CONT-001.

## Owner decisions — recorded 2026-10-04 (all six morning-list items decided)

Basis: `docs/ARC-REPORT.md`, `docs/REVIEW-FABLE.md` (external Fable review 2026-10-04; all load-bearing claims reproduced by the implementing agent, 8/8), `docs/OBSERVER-NOTES.md` final pass, and the same-day GLM-5.3-Flash review. Owner verdict: **accept the Fable recommendations in full**, including flaw remediation before the next arc.

1. **M7 confirmatory result: ACCEPTED** as "no confirmatory difference established", with two interpretive caveats now on record: (i) the strict-RM primary lost construct validity on free-form probes (loose RM = 1.0 in every arm; arm A's strict 0.0 reflects drifting-wrong answers, not error avoidance); (ii) the 7-cluster bootstrap was structurally unlikely to exclude 0 (would have required repeats in ≥3/7 clusters; arm E had 2). The mid-run contamination-gate softening (`c679547`) is acknowledged and covered by this acceptance; future protocols freeze analysis code and route multi-rev tolerance through a pre-registered clause. The residual fixture-authoring exposure (PR-REVIEW note 1) is hereby explicitly acknowledged as present in this run's provenance.
2. **CONT-002: DEFERRED** until probe elicitation is reworked (label-form probes); the mechanics proof (5/5) stands.
3. **CONT-005 Memory Trust Hierarchy: APPROVED as the next arc**, conditional on the suite/protocol redesign below.
4. **CN-005: CLOSED as budgeting-only** — the wall-clock budgeting rule stays; no further shared-tooling investment for now.
5. **Publications/external actions from this arc: NONE** (the only CI excluding 0 is a secondary result); an optional methodology note about the protocol itself may be considered later.
6. **Scope amendments adopted for all future pre-registrations:** (a) analysis code frozen by digest alongside frozen content; (b) label-form probe elicitation (no free-form floors); (c) cluster-level power calculation with ≥12–15 RM clusters; (d) contamination/independence gates executed by a non-executor session; (e) run-record aggregates must be internally consistent across resume attempts (complete wall-time accounting).

### Next work package (owner-approved direction)

Suite v3 + protocol amendments (zero GPU): fixture family redesign per 6(b)/6(c), pre-registration template updates per 6(a)/6(d)/6(e), then the CONT-005 proposal review cycle and a fresh arc plan. CONT-002 behavioral work is gated on 6(b).

## Owner decisions — recorded 2026-10-07 (CONT-005 cycle-2 closing)

Basis: `docs/OWNER-BRIEF-CONT005-C2-CONFIRMATORY.md`, the frozen
`results-summary.json` (confirm-c2-20261006-230445), and `docs/GATE-V3B.md`.
Owner verdict: **"все так" (all defaults accepted), with two follow-ups**
(below).

1. **Cycle-2 confirmatory result: ACCEPTED** — "no confirmatory difference
   established" (T0-T1 -0.017, CI [-0.167, 0.100]; CI excludes the
   pre-registered +-0.25 in both directions). CONT-005 (Memory Trust
   Hierarchy) is CLOSED: provenance annotations and trust machinery do not
   improve label-form accuracy on this core; T1 stays +5.6% tokens for
   auditability only.
2. **GATE-V3B Opus substitution: ACCEPTED.** Standing reviewer queue for
   this lab from now on: **Fable first; if unavailable, Opus; if both
   unavailable, the local GLM 5.3 Flash** (owner directive 2026-10-07).
3. **RESULTS-DIGEST-2026-10.md annotated** with the cycle-2 outcome (the
   cycle-1 "T1 0/90 promising signal" reclassified as a surface artifact:
   8/60 vs T0 7/60 on the rebalanced surface).
4. **Next direction: DECIDED 2026-10-07 ("ок")** — (1) CONT-006 proposal
   review cycle NOW (zero GPU; implementing-agent review file + independent
   reviewer from the queue); (2) CONT-002 is the next arc (session brief
   `docs/SESSION-BRIEF-CONT002.md`; design + pre-registration first, the
   behavioral run stays owner-gated per "Never autonomous"); (3) CONT-006
   build after CONT-002 — its critical test 4 (cross-model lesson transfer)
   reuses the CONT-002 cross-core machinery.

## Owner decisions — recorded 2026-10-07 (CONT-002 pre-registration ACCEPTED)

Basis: `docs/EVALUATION-PREP-CONT002.md` (with the PR-REVIEW-CONT002 RC-1..RC-5
fold), `docs/PR-REVIEW-CONT002.md` (Fable GO-with-changes -> folded ->
verify-pass GO), and the plain-language briefing delivered in chat the same
day. Owner verdict (chat): **"приймаю пре-реєстрацію CONT-002"** — the
behavioral chain (FREEZE -> non-executor gate -> pilot -> pilot-gate
checkpoint -> confirmatory) is UNBLOCKED. The never-autonomous clause is
satisfied by this explicit acceptance; all further owner touchpoints are the
pre-declared ones (pilot GO/NO-GO outcome, MME re-derivation at the
pilot-gate checkpoint if it fires, stress-governance sign-offs).

## Owner decisions — recorded 2026-10-08 (CONT-002 result ACCEPTED; CONT-006 GO)

Basis: the CONT-002 confirmatory record (`results/CONT-002-CONFIRMATORY/cont002-confirmatory-20261008-020902/results-summary.json`), the frozen analysis verdict, and the plain-language owner brief delivered in chat. Owner verdict (chat): **"accept, go CONT-006"**.

1. **CONT-002 result: ACCEPTED** — "retained benefit established" (R = 0.989,
   95% CI [0.944, 1.035]; dA = 0.867 [0.810, 0.924]). CONT-002 is **CLOSED**
   with a positive verdict: on the v3k recall surface, the learned persistent
   state transfers across cores essentially in full (scope: the two pinned
   cores @ temp 0; synthetic content; correction-family state out of scope by
   design). The "agent-pre-registered, pending owner acceptance" label is
   satisfied by this entry.
2. **CONT-006 ("Reflection as Lesson Extraction", REFLECTION-V2-PROPOSAL.md
   with RC-1..RC-5 folded at 562a1cb): GO** — the build starts with a
   design + pre-registration milestone (zero GPU) per the house
   one-milestone-per-session model; its critical test 4 (cross-model lesson
   transfer) reuses the now-proven CONT-002 four-cell machinery. Behavioral
   runs remain owner-gated per the standing never-autonomous clause.

## Owner decisions — recorded 2026-10-08 (CONT-006 pre-registration ACCEPTED)

Basis: the design milestone (commit 0bf6352: frozen taxonomy FP-0..FP-6,
experience corpus 50 traces, suite v3l validator PASS 19/19 + regressions
PASS x5, power artifact) and the independent PR-REVIEW cycle
(docs/PR-REVIEW-CONT006.md, commit c7a5b27: Fable GO-with-changes RC-1..RC-5,
all folded same session, verify-pass GO, curatorial verification 5/5
CONFIRMED). Owner verdict (chat): **"приймаю пре-реєстрацію CONT-006"** —
the full behavioral chain is UNBLOCKED under the pre-declared gates:
FREEZE (analysis scripts first) -> non-executor fixture/freeze gates ->
Phase W (worker pass) -> Phase G (R3 blind authoring) -> contamination
gate -> Phase V (activation; active stores committed + digested BEFORE any
transfer request) -> Phase P (pilot incl. BAD-lesson safety + GOLD-TRIV
manipulation checks) -> pilot-gate checkpoint (owner-visible; stop
conditions route back to the owner) -> Phase C (confirmatory). Bounded
later stage after verdict: critical test 4 (cross-model lesson transfer on
the CONT-002 machinery, own budget, non-estimable clause).

## Owner decisions — recorded 2026-10-09 (CONT-006 pilot NO-GO OVERRIDDEN; confirmatory authorized)

Basis: the pilot record (results/CONT-006-PILOT/cont006-p-20261008-232209/pilot-gate-cont006.json — frozen analyzer verdict NO-GO: criterion 1(i) BAD-lesson parroting verbatim in an RBAD reply; criterion 2 GOLD-TRIV 0.071 < 0.10; criteria 3/4/5/6 PASS; band rule fired, MME re-derived upward to 0.333) and the plain-language owner brief. Owner verdict (chat): **"(b) Дозволити фінальний забіг попри NO-GO"** — an explicit owner-gate override, pre-declared as a legal branch by prereg §9 ("owner decision recorded either way"). The primary R2−R0 endpoint is not compromised by the pilot findings (the counterfactual arms never enter the primary); the harm-containment finding rides the final run record as a headline secondary (PW-OVERRIDE carried note). Re-authoring of v3l remains banned; the frozen analysis runs unchanged with the band-derived MME 0.333.

## Owner decisions — recorded 2026-10-09 (CONT-006 V2 pre-registration ACCEPTED; rerun UNBLOCKED; co-owner review step WAIVED)

Basis: the RC-6 review chain on the V2 (rethink) package after the CN-012
invalidation — implementer self-review `docs/SELF-REVIEW-CONT006-V2.md`
(9 findings SR-1..SR-9, all folded same session, commit 7450b08), Fable
independent review `docs/REVIEW-FABLE-CONT006-V2.md` (GO-with-changes;
5 critical K-1..K-5 + Б-1..Б-7, ALL folded same session with 100% curation
confirmation, commit fa44fd6), and the plain-language chat briefing
(reflection-v2 status: the main question is still OPEN and untested; the
invalid run was an accidental lessons-WITHOUT-memory ablation). Owner
verdict (chat): **"даю дозвіл на старт експерименту. ревю фабла досить. на
ко-овнера чекати не будемо"** — explicitly: (1) the V2 pre-registration
(docs/EVALUATION-PREP-CONT006-V2.md, amendments A.1-A.7) is ACCEPTED;
(2) the RC-6 step-3 co-owner review is WAIVED by owner decision (Fable's
review judged sufficient; the co-owner remains free to review post-hoc and
any findings feed the next amendment cycle); (3) the behavioral execution
chain (FREEZE V2 -> worker v2 pass -> R3 recap -> contamination gate ->
calibration pilot -> Phase V -> store freeze -> Phase P pilot ->
pilot-gate checkpoint -> Phase C -> frozen analyzer -> verdict) is
UNBLOCKED, to run in a fresh session per
`docs/SESSION-BRIEF-CONT006-V2-EXEC.md`. The never-autonomous clause is
satisfied by this explicit acceptance; all further owner touchpoints are
the pre-declared ones: calibration out-of-band -> STOP + owner; the
pilot-gate checkpoint outcome; any halt-and-investigate firing
(anchor-divergence, live-gate FAIL, freeze-digest guard).

## Owner decisions — recorded 2026-10-10 (CONT-006 V2 calibration STOP: all three brief defaults ACCEPTED)

Basis: the calibration STOP record
(results/CONT-006-CAL/cont006-cal-20261010-000940/calibration-verdict.json
— family-headroom breach dx=1.0/dr=1.0 both arms, cr floor R0 0.25 / R2
0.0; anchor PASS 0.533 vs 0.525; live gate PASS) and the plain-language
owner brief `docs/OWNER-BRIEF-CONT006-V2-CAL-STOP.md`. Owner verdict
(chat): **"ок по дефолтах"** — all three defaults accepted: (1) NEW suite
(v3n) authoring AUTHORIZED (harder dx/dr, easier cr, fresh worlds, zero
v3m text reuse); (2) the zero-GPU diagnostic read of the cr calibration
traces AUTHORIZED and runs FIRST (its findings feed the v3n authoring);
(3) the CONT-006 arc is NOT stopped. The V2 stores (W2 worker output +
R3 recap) are suite-independent artifacts and remain valid evidence; the
re-run chain (re-freeze on v3n -> Fable diff-pass per its closing note ->
calibration -> V -> P -> C) is prepared as DRAFT amendments, and any
behavioral inference on v3n requires the next pre-registration
acceptance (never-autonomous clause unchanged).

## Never autonomous (unchanged)

- CONT-002 behavioral experiments — anything that measures transfer quality. The single exception is the M2b mechanics smoke (owner-ordered 2026-10-01): export/import plumbing proof only, explicitly no behavioral claims.
- External actions outside this repository; publication decisions; model downloads > 1 GB (importing an already-local GGUF via a Modelfile is not a download).
