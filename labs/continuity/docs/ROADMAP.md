# Continuity — autonomous arc roadmap

- **Arc goal:** from smoke to first ablation signal — complete P0b (pilot + sizing) and P1a (arms B–E as MVPs), and produce a first **exploratory** CONT-001 multi-arm result. The confirmatory CONT-001 run stays owner-gated.
- **Armed:** 2026-10-01 22:30 FLEDT. **Arc deadline:** 2026-10-02 10:30 FLEDT. After the deadline, every milestone executor must no-op.
- **Execution model:** one milestone per fresh session. The brief below is the only required reading; the repository is the sole state carrier between sessions (LOG.md, results/, git). Do not rely on conversation history.
- **Status legend:** TODO / IN_PROGRESS / DONE / BLOCKED (a BLOCKED milestone records why in LOG.md and leaves the rest of the chain to the next executor).

| Milestone | Stage | Status |
| --- | --- | --- |
| M1 | P0b: fixture suite v2 + arm A variance/headroom pilot + sizing | TODO |
| M2 | P1a: arm B — SQLite persistent memory | TODO |
| M3 | P1a: arm C — validated self-model | TODO |
| M4 | P1a: arm D — reflection/consolidation | TODO |
| M5 | P1a: arm E — world model + bounded policy | TODO |
| M6 | Exploratory CONT-001 pass (all arms) + pre-registration draft | TODO |
| M7 | Buffer: housekeeping, findings triage, arc report | TODO |

## Executor protocol (every session)

1. Read this file fully. If the arc is complete or past deadline → stop with a one-line reply.
2. Pick the first milestone not DONE. Verify its entry conditions. Fail-closed: unmet conditions → LOG.md note + stop, no improvisation.
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
- **Scope:** run arms A–E over the full suite with the seed count recommended by SIZING.md (hard cap: 3h GPU total; if over budget, reduce seeds and record the reduction); normalized results table (primary endpoint candidate: repeated-mistake rate / delayed-recall pass rate; report per-arm with spread); write `docs/EVALUATION-PREP.md` — a DRAFT pre-registration for the confirmatory CONT-001 (primary endpoint, contrast, thresholds, aggregation) marked OWNER-GATED; LOG.md with the table.
- **Non-goals:** any confirmatory claim; promoting secondary metrics; CONT-002.
- **Exit artifacts:** results/CONT-001-exploratory/…; EVALUATION-PREP.md (draft); LOG.md.
- **Budget:** <= 150 min, <= 180 min GPU. (Executor may split into two checkpoints.)

## M7 — buffer / housekeeping / arc report

- **Goal:** close the arc cleanly regardless of where the chain stopped.
- **Entry:** always available; run when M6 is DONE or the chain is BLOCKED.
- **Scope:** triage open CN-NNN cases; retry the deferred Mnemosyne consolidation; write `docs/ARC-REPORT.md` (what was achieved, numbers, failures, what is owner-gated next); mark the arc COMPLETE at the top of this file; final LOG.md entry; commit + push; Mnemosyne note.
- **Non-goals:** new features.
- **Exit artifacts:** ARC-REPORT.md; completed statuses; clean git state.

## Owner-gated (never autonomous)

- Executing the confirmatory CONT-001 after pre-registration review.
- Anything in CONT-002 (state export/import experiments) beyond the storage format built in M2.
- External actions outside this repository; publication decisions; model downloads > 1 GB.
