# Findings — Continuity lab

Format: `CN-NNN | date | stage | finding (1-2 sentences) | status`

Findings are recorded at the moment of discovery. Before each new stage, open cases are re-read; the stage either closes or explicitly declares them out of scope.

---

CN-001 | 2026-10-01 | P0a | Ollama 0.34.2 `/api/show` does not expose a model digest, so model identity cannot be pinned from it; `/api/ps` does expose the digest, but only for currently loaded models. | CLOSED 2026-10-01: provider pins the model via `/api/ps` after the run (keep_alive guarantees the model stays loaded); verified by smoke run `cont000-smoke-dr-0001-20261001-220201` (digest `36c3c3b9…`)
