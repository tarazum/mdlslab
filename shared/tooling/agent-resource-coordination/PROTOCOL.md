# PROTOCOL — shared machine resources (binding for ALL agent sessions)

You are one of several agents working on this machine. **Other agents may be
running local models RIGHT NOW** (ollama, torch/CUDA). Before you launch
anything heavy, claim the resource; after you finish, release it. This is
mandatory for every session, including yours, even if your project's own
docs do not mention it.

## Definitions

- **Heavy** — anything that makes a local model load or run on the GPU,
  including calls to a shared ollama or gateway worker, and any large
  download/install. Torch/CUDA scripts, `ollama run`/API calls against
  resident models, and big pip/hf downloads all count.
- **Shared resources** — the single GPU (8 GB VRAM), the network for large
  downloads/installs, the model-weight directory (`C:\Models`).

Helper — use exactly this one, do not improvise your own locking:

```
python C:/projects/mdlslab/shared/tooling/agent-resource-coordination/lock.py
```

## Rules

1. **Scripted heavy runs** (preferred): run them under the lock so it is
   held exactly for the duration of the child process:

   ```
   lock.py run gpu --holder "<client>/<project>" --purpose "<what>" -- <command...>
   ```

2. **Interactive sessions**: acquire before GPU work, release after:

   ```
   lock.py acquire gpu --holder "<client>/<project>" --purpose "<what>" --require-idle-gpu
   lock.py release gpu --holder "<client>/<project>"
   ```

   A manual lock without a live anchor expires by heartbeat TTL
   (default 45 min; `lock.py touch gpu` refreshes it; `--ttl-min` overrides).

3. **Timings and benchmarks: ONLY on an idle GPU.** `lock.py gpu` shows
   total `memory.used` plus ollama's resident models (attribution; on
   Windows/WDDM per-process GPU memory is otherwise unavailable) and exits
   3 when busy (default idle threshold 2048 MiB). If busy: wait, or
   reschedule. Never report latency measured on a shared GPU — the numbers
   are invalid, not just noisy.

4. **Large downloads/installs**: same pattern with resource `download`
   (machine rule: one big download at a time).

5. **Stale locks are taken over automatically** (dead owner PID verified by
   PID + process creation time against Windows PID reuse; expired
   heartbeat; or over the hard age cap). Concurrent takeovers are
   serialized and verified, so exactly one agent can win. Old files are
   parked as `*.stale-<ts>` — do not delete them, do not delete anyone's
   active lock.

6. **NEVER kill, stop, or unload a process you did not start** — including
   ollama and its resident models. A polite unload (ollama `keep_alive: 0`)
   is not killing, but it still breaks whoever is using that model: do not
   unload while any lock or active run exists. If the GPU is busy with no
   lock held (foreign/unknown process): do not start; report it to the
   Owner in your session summary.

## Concurrency model (current)

Locks are exclusive. Consumers of one resident local model therefore
serialize; benchmarks additionally require an idle GPU. Shared/exclusive
(reader/writer) leases for concurrent consumers are specified as the next
iteration — see `TASK.md`, direction accepted 2026-10-01.

## Reference

- Exit codes: `0` ok · `2` lock held by a live holder · `3` GPU busy or
  unmeasurable (fail-closed) · `4` success after a stale takeover —
  `acquire` only; `run` returns the child's exit code and reports the
  takeover in its JSON/stderr · `1` error or repeated contention ·
  `130` `run` child interrupted.
- Lock records are JSON: holder, project, purpose, pid, pid_started_utc,
  started_utc, ttl_min, max_age_h, host, and (gpu) gpu_at_start — a probe
  snapshot for later audits. `lock.py status` shows them all.
- This protocol is advisory-but-mandatory; enforcement work is tracked in
  TASK.md.
