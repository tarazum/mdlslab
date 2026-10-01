# TASK — enforcement layers beyond advisory rules

**Status:** OPEN (created 2026-10-01, ZCode session, timesfm-playground).

## Accepted directions from review 2026-10-01 (`REVIEW-2026-10-01-claude-code.md`)

Fixed immediately (lock.py v1.1): stale takeovers serialized via a
`.takeover` guard with identity re-verification; exit code 4 now actually
returned after a takeover; PID identity hardened with process creation
time (Windows PID reuse); `platform.node()` host fallback; manual TTL
default lowered to 45 min; `gpu_at_start` probe snapshot in gpu lock
records; ollama `/api/ps` added to `gpu` output as attribution.

Deferred to this task (design changes, own iteration with tests):

6. **Shared/exclusive (reader/writer) leases** — review finding 3.
   Ordinary local-model use takes a *shared* lease (one file per holder in
   `gpu.shared/`); benchmarks/timing take the *exclusive* lock, granted
   only when no live shared lease exists and the GPU is idle; a pending
   exclusive request blocks new shared leases so benchmarks cannot starve.
   Consumers of one resident ollama model stop serializing needlessly.
7. **Gateway-held leases** — review question 2: the agent-pool gateway
   (fronts ollama for several projects) could take the shared lease per
   request on behalf of callers — the "self-defending entry point" of
   item 3 for every gateway client, with zero agent behavior required.

Open owner questions from the review: build shared leases before more
agents rely on the protocol, or is serializing consumers acceptable for
now? Should the gateway hold leases on behalf of callers?

## Problem

Owner decision 2026-10-01: written rules (AGENTS.md, PROTOCOL.md) are
necessary but insufficient — **there is no guarantee a model read them**.
The advisory lock protocol in this folder works only when the agent calls
`lock.py`. This task researches and designs protection that does not depend
on agent goodwill.

## Context

- 2+ cloud-model coding agents (ZCode, Anthropic-class clients) work
  concurrently on one Windows 11 laptop; each can launch local models
  (ollama server, torch/CUDA scripts) for its project.
- Observed 2026-10-01: idle ollama held ~6 of 8 GB VRAM while another
  agent needed the GPU; `nvidia-smi` per-process attribution is unavailable
  on Windows/WDDM, so total `memory.used` is the only reliable signal.
- Cost of failure: corrupted benchmarks (latency measured under contention),
  OOM crashes of someone's active run, silent interference between agents.

## Research questions

1. **Enforcement watchdog ("mini-Slurm")** — a scheduled sampler pairing
   `nvidia-smi` totals with the lock registry; policies from notify-only to
   Owner-authorized termination of GPU consumers that hold no lock. What do
   Slurm / HTCondor / simple queue daemons look like at desktop scale — is
   a local job queue justified for 2 agents?
2. **Kernel primitives** — Windows named mutexes / semaphores (auto-release
   on process death → no stale locks) vs lock files; interop from Python,
   PowerShell, Node (the three runtimes agents actually use here).
3. **Self-defending entry points** — a shared `preflight` module that heavy
   scripts import and that refuses to run when the GPU is busy or the lock
   is held by someone else. The check rides with the code, not with
   instructions. Retrofit into existing harnesses first (timesfm-playground
   scripts, local model launchers).
4. **Local-model server policy** — `OLLAMA_KEEP_ALIVE`, 
   `OLLAMA_MAX_LOADED_MODELS`, explicit unload hooks: config-level
   anti-squatting that requires no agent behavior at all.
5. **Agent-standard surfaces** — is there (or will there be) a standard MCP
   resource-lock server that all MCP-capable clients could share? Survey
   before building custom; an MCP tool surface would at least make locks
   uniformly discoverable by every client.

## Prior art to survey (initial scan 2026-10-01)

- HPC schedulers at desktop scale (Slurm, HTCondor); GPU allocation
  conventions in ML clusters (`CUDA_VISIBLE_DEVICES` partitioning, MPS,
  MIG — note: MIG is unavailable on GeForce laptop GPUs).
- Multi-agent coding practice converges on git worktrees + non-overlapping
  task slices + file/lock coordination; **no standard runtime
  "agent presence" protocol exists as of 2026-10**:
  - [Best practices for isolating parallel AI agents in a single environment](https://www.reddit.com/r/ClaudeWorkflows/comments/1wg24jb/workflow_community_consensus_best_practices_for)
  - [Multi-agent systems with MCP (resource locking section)](https://www.truefoundry.com/blog/multi-agent-system-with-mcp)
  - [Multi-agent coordination strategies](https://www.splunk.com/en_us/blog/artificial-intelligence/multi-agent-coordination-strategies.html)
  - [Agentic GPU infrastructure topologies](https://www.spheron.network/blog/multi-agent-ai-system-gpu-infrastructure)

## Constraints

- Public repo: no secrets, no private data.
- Never kill processes without an explicit Owner-approved policy and
  false-positive guards.
- Benchmarks require an exclusive idle GPU — any design must preserve this.
- Windows-first; Python 3.12, Node, PowerShell, Git Bash available.

## Acceptance criteria

An agent that has read **nothing** must still be unable to silently corrupt
a benchmark or OOM another agent's run: it is either blocked, queued, or
detected and reported to the Owner within minutes. No false positives
during normal single-agent work. Any kill switch stays Owner-controlled.

## Deliverable

Design doc + (if adopted) implementation + updates to `PROTOCOL.md` and the
machine-wide index `C:\projects\CROSS_PROJECT_DECISIONS.md`.
