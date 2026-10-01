# Findings — Continuity lab

Format: `CN-NNN | date | stage | finding (1-2 sentences) | status`

Findings are recorded at the moment of discovery. Before each new stage, open cases are re-read; the stage either closes or explicitly declares them out of scope.

---

CN-001 | 2026-10-01 | P0a | Ollama 0.34.2 `/api/show` does not expose a model digest, so model identity cannot be pinned from it; `/api/ps` does expose the digest, but only for currently loaded models. | CLOSED 2026-10-01: provider pins the model via `/api/ps` after the run (keep_alive guarantees the model stays loaded); verified by smoke run `cont000-smoke-dr-0001-20261001-220201` (digest `36c3c3b9…`)

CN-002 | 2026-10-01 | P0b | Ollama-reported `total_duration` (mean 265.5 ms, p95 527.3 ms, warm) understates effective per-request latency: wall time between `env.turn` and `agent.response` trace events is ~2.3 s per request (mean 2.31 s, min 2 s, max 3 s at 1 s timestamp resolution), reproducibly across seeds. Root cause not identified (out of M1 scope). | OPEN — planning rule until closed: use wall-clock per seed (~60 s for 26 requests) for throughput/GPU budgets; `total_duration` only for relative inference timing.

CN-003 | 2026-10-01 | P0b | Temperature 0.0 does not fully determinize outputs across seeds on one backend: seed 11 vs seed 55 differ in 4/26 responses (e.g. cu-0001 "20" vs "200 passengers", dr-0002 "[Name]" vs "Dr. Jane Smith"); pass/fail outcomes were identical in this pilot (token totals 2478 vs 2473). PB-071 caveat empirically confirmed. | OPEN — monitor from M2 on; any marginal probe flip caused by seed-only variation escalates this case.

CN-004 | 2026-10-01 | P0b | Fixture rt-0003 lists `perf` among the probe's label options, which partially leaks the rubric-dependent answer: arm A (no memory) answered `perf` on 5/5 seeds. The scenario still discriminates (an answer of `bug` fails), but its arm-A ceiling is inflated. | OPEN — fixture v2 decision (options without `perf`, or free-form label); do not change mid-pilot.

CN-005 | 2026-10-01 | P0b | Shared GPU protocol idle threshold (2048 MiB) cannot distinguish "resident target model" from "active foreign compute": at pilot start nvidia-smi showed 5987 MiB used while ollama `/api/ps` attributed 5064.6 MiB to the only resident model, granite-code:8b (the pilot's own target), and no lock was held. The pilot ran under the exclusive lock without `--require-idle-gpu`, with the attribution snapshot recorded in `aggregate.json` (`pilot.gpu_lock_note`, `gpu_at_start`). | OPEN — reported to the Owner; threshold/attribution refinement belongs to `shared/tooling/agent-resource-coordination`.

CN-006 | 2026-10-01 | P0b | `labs/continuity/README.md` still said "No implementation or experimental results yet" although the P0a smoke had already passed (doc/repo mismatch left over from the proposal stage). | CLOSED 2026-10-01: status line rewritten to the actual P0-complete state in the same M1 commit.
