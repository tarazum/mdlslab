# Review of PROTOCOL.md and lock.py — for discussion

**Reviewer:** Claude Code session in `trend-signal-engine` (TSE).
**Date:** 2026-10-01.
**Scope:** PROTOCOL.md, README.md, TASK.md, lock.py at `9266d86`.
**Method:** code reading. Nothing below was tested against a second live process
unless stated.

## Summary

The protocol is short, readable and points to one helper — the right shape. The
`run` pattern ties the lock to a child process's lifetime, the GPU probe fails
closed, stale locks are parked rather than deleted, and the "never kill what you
did not start" rule is correct.

Three issues matter before relying on the protocol:

1. a race in the stale takeover;
2. exclusive-only locks do not fit a shared ollama server;
3. a documented exit code is never returned.

## Findings

### 1. Stale takeover can hand the lock to two agents (correctness)

`acquire_once` reacts to `FileExistsError` by reading the record. If the lock is
stale, it calls `park_stale`, which does `path.replace(parked)` on whatever file is
at `path` *now*. Interleaving that breaks it:

1. A and B both read the same stale record.
2. A parks it and creates a fresh lock (`O_EXCL` succeeds).
3. B, still acting on its old read, parks **A's fresh lock** and creates its own.

Both believe they hold the GPU.

Suggested fix — serialize takeovers:
- take a short `O_EXCL` guard file (`<resource>.lock.takeover`);
- re-read the lock under the guard and park only if its `pid` and `started_utc`
  still equal what was judged stale;
- remove the guard.

The guard needs its own short age cap, so a crash cannot wedge it.

### 2. Exit code 4 is documented but never produced (doc/code mismatch)

PROTOCOL.md and the docstring say `4 = success after stale-lock takeover`.
`acquire_once` returns 1 after parking; `cmd_acquire` / `cmd_run` retry and return 0.
No path returns 4 (`grep "return 4"` is empty). Either return 4 after a successful
retry that followed a takeover, or drop it from the docs. Callers scripting on exit
codes will otherwise misread a takeover as a plain acquire.

### 3. Exclusive locks do not model a shared local-model server (design)

TSE's falsifier calls `local-qwen3-8` (ollama) as a shadow judge in every run, while
other agents may call the same ollama server. These are concurrent *consumers* of
one resident model, not competing owners of the GPU. With one exclusive `gpu` lock:

- consumers serialize needlessly, or skip the lock;
- `--require-idle-gpu` refuses even the agent whose own model is resident: an idle
  ollama with a loaded model is "busy", which was the 2026-10-01 trigger.

Suggestion: **shared/exclusive (reader/writer) semantics.**
- Ordinary model use takes a *shared* lease, one file per holder in a
  `gpu.shared/` directory.
- Benchmarks and timing runs take the *exclusive* lock. It is granted only when no
  live shared lease exists and the GPU is idle.
- A pending exclusive request blocks new shared leases, so benchmarks cannot starve.

This keeps rule 3 (timings only on an idle GPU) and stops consumers blocking each
other.

### 4. Use ollama's own accounting where nvidia-smi cannot attribute (improvement)

On Windows/WDDM, per-process VRAM is unavailable, but ollama reports resident models
and their VRAM through `GET http://127.0.0.1:11434/api/ps` (`size_vram`). The probe
could report "ollama holds X MiB in models [m1, m2]" separately from other usage.
That turns "GPU busy, unknown owner" into an attributable state and supports
TASK.md item 4.

A polite unload (`keep_alive: 0` on a request for that model) is not killing a
process. Rule 6 should still apply to it while any shared lease is live: unloading
under another agent's run would break it.

### 5. PID reuse on Windows (robustness)

`pid_alive` treats any live process with the recorded PID as the owner. Windows
reuses PIDs, so a crashed holder's PID can belong to an unrelated process for up to
`max_age_h` (24 h). Recording the owner's creation time (`GetProcessTimes`) next to
the PID, and comparing both, closes this. The `run` pattern makes it rare, but a
24-hour wrong hold of the GPU is the costly failure.

### 6. Smaller points

- `write_lock`: `os.environ.get("COMPUTERNAME") or os.uname().nodename` raises
  `AttributeError` on Windows when `COMPUTERNAME` is unset (`os.uname` does not exist
  there). `platform.node()` works everywhere.
- Default manual TTL of 240 min is long for an interactive session that forgets to
  release; 30–60 min with `touch` is safer. The `run` pattern is unaffected.
- `run gpu` without `--require-idle-gpu` does not check the GPU at all. For the `gpu`
  resource, an informational probe in the lock record (used MiB at start) would help
  later audits even when idleness is not required.
- "Heavy" is undefined. Proposed wording: anything that makes a local model load or
  run on the GPU, including calls to a shared ollama/gateway worker, counts. Under
  that wording TSE's shadow-judge calls are covered; without it a reader could think
  only their own torch scripts are.

## How TSE will follow it now

Until shared leases exist, each TSE falsify/benchmark run that uses a local model
(the shadow judge) runs as:

```
python C:/projects/mdlslab/shared/tooling/agent-resource-coordination/lock.py run gpu --holder "claude-code/trend-signal-engine" --purpose "<run>" -- <command>
```

No `--require-idle-gpu`, because these runs are not timing measurements. A refusal
(exit 2) means wait; TSE never stops a foreign process.

## Questions for the owner

1. Should shared leases (finding 3) be built before more agents rely on the
   protocol, or is serializing every local-model consumer acceptable for now?
2. Should the TSE agent-pool gateway (which fronts ollama for several projects) take
   the lease per request on behalf of callers? That would be the "self-defending
   entry point" of TASK.md item 3 for every client of that gateway.
