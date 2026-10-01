# Agent Resource Coordination

Shared tooling and binding rules for **concurrent coding agents working on
one physical machine**. Several cloud-model agent clients (ZCode, Anthropic
Claude Code, …) drive local projects and may launch local models
(ollama server, torch/CUDA scripts). The scarce shared resources are the
single GPU (8 GB VRAM), large downloads/installs, and the model-weight
directory.

Why this exists (observed 2026-10-01): an idle ollama server held ~6 of
8 GB VRAM while another agent needed the GPU for benchmark work; nothing
recorded "someone is running something right now". Written rules alone do
not guarantee anything — see TASK.md for enforcement layers that do not
depend on an agent having read them.

## Files

- `PROTOCOL.md` — binding rules for every agent session on this host.
  **Point any new agent/session at this file before it runs anything heavy.**
- `lock.py` — the single lock implementation: machine-wide advisory locks
  (atomic file create in `C:\projects\.locks`) + GPU ground-truth probe
  (`nvidia-smi` total memory; per-process attribution is unreliable on
  Windows/WDDM). Tested 2026-10-01: acquire/contend/release, `run` pattern,
  TTL expiry, stale takeover, GPU refusal.
- `TASK.md` — open task: research and design enforcement beyond advisory
  locks (watchdog, kernel primitives, self-defending entry points, local
  model server policy).

## Status

Protocol active since 2026-10-01 (advisory-but-mandatory). Recorded in the
machine-wide index `C:\projects\CROSS_PROJECT_DECISIONS.md`.
