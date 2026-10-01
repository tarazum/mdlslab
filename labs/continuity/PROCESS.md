# Continuity Lab — working process

Working agreement for any agent session in this lab. Aligned with the repository's `docs/architecture.md`; house conventions are applied in their public-safe form.

1. **Start-note before long chains.** Before any multi-stage run (pilot, experiment arm, migration of the harness), append a start-note to `LOG.md`: plan + current state. Before an irreversible or long phase, state the exact next command in the chat.
2. **Evidence is an artifact.** No number without a result file under `results/` (trace, summary JSON, environment snapshot). Exit codes and console output are not proof (PB-067).
3. **Determinism is explicit.** Sampling parameters travel in every inference request (PB-071). Greedy decoding plus a seed does not guarantee identical outputs across batch sizes or backends — record the caveat with any determinism claim.
4. **Findings immediately.** Anomaly, odd number, doc/code mismatch → same-moment entry in `docs/FINDINGS.md` as `CN-NNN`. Open cases are re-read before each new stage; the stage either closes a case or explicitly declares it out of scope.
5. **Lessons the same day.** Root cause found → same-day entry in `LOG.md` (Context → What happened → Lesson → Change). Universal lessons are promoted to the machine-level lessons repository (PB-NNN with back-link); lab-local lessons stay here.
6. **Budgets and stop conditions.** Every runner embeds max turns / tokens / wall-clock; violations stop the run and are recorded as events. GPU-heavy runs take the shared agent-resource lock when the machine is contended.
7. **Commit + push after each completed stage.** Public-safe content only: no private paths, credentials, or non-synthetic data in committed artifacts.
8. **Session summary.** End each working session with: results/numbers → what was done → next stage + owner actions → an explicit note on what was recorded to memory.
