# Continuity — autonomous arc roadmap

- **Arc goal:** from smoke to first ablation signal — complete P0b (pilot + sizing) and P1a (arms B–E as MVPs), and produce a first **exploratory** CONT-001 multi-arm result. The confirmatory CONT-001 run stays owner-gated.
- **Armed:** 2026-10-01 22:30 FLEDT. **Arc deadline:** 2026-10-02 11:30 FLEDT (extended 22:35 per owner: all owner work consolidated at arc end). After the deadline, every milestone executor must no-op.
- **No milestone waits on the owner.** Every owner decision is collected in the Owner morning list at the end of this file; the chain runs unattended.
- **Execution model:** one milestone per fresh session. The brief below is the only required reading; the repository is the sole state carrier between sessions (LOG.md, results/, git). Do not rely on conversation history.
- **Status legend:** TODO / IN_PROGRESS / DONE / BLOCKED (reason recorded in LOG.md) / SKIPPED (a written condition failed; reason recorded).

| Milestone | Stage | Status |
| --- | --- | --- |
| M1 | P0b: fixture suite v2 + arm A variance/headroom pilot + sizing | DONE |
| M2 | P1a: arm B — SQLite persistent memory | IN_PROGRESS |
| M2b | CONT-002 mechanics smoke (conditional: >= 45 min before deadline) | TODO |
| M3 | P1a: arm C — validated self-model | TODO |
| M4 | P1a: arm D — reflection/consolidation | TODO |
| M5 | P1a: arm E — world model + bounded policy | TODO |
| M6 | Exploratory CONT-001 pass (all arms) + pre-registration v1 committed | TODO |
| M6b | Independent pre-registration review (GO/NO-GO) | TODO |
| M7 | Confirmatory CONT-001 (conditional: M6b GO + >= 2h before deadline) | TODO |
| M8 | Final: housekeeping, arc report, owner morning list | TODO |

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

## Never autonomous (unchanged)

- CONT-002 behavioral experiments — anything that measures transfer quality. The single exception is the M2b mechanics smoke (owner-ordered 2026-10-01): export/import plumbing proof only, explicitly no behavioral claims.
- External actions outside this repository; publication decisions; model downloads > 1 GB (importing an already-local GGUF via a Modelfile is not a download).
