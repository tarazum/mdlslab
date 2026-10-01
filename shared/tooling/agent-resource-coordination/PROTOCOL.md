# PROTOCOL — shared machine resources (binding for ALL agent sessions)

You are one of several agents working on this machine. **Other agents may be
running local models RIGHT NOW** (ollama, torch/CUDA). Before you launch
anything heavy, claim the resource; after you finish, release it. This is
mandatory for every session, including yours, even if your project's own
docs do not mention it.

Shared resources: **GPU** (single, 8 GB VRAM), **large downloads/installs**,
model weights directory (`C:\Models`).

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
   (default 240 min; `lock.py touch gpu` refreshes it).

3. **Timings and benchmarks: ONLY on an idle GPU.** `lock.py gpu` shows
   total `memory.used` and exits 3 when busy (default idle threshold
   2048 MiB). If busy: wait, or reschedule. Never report latency measured
   on a shared GPU — the numbers are invalid, not just noisy.

4. **Large downloads/installs**: same pattern with resource `download`
   (machine rule: one big download at a time).

5. **Stale locks are taken over automatically** (dead owner PID, expired
   heartbeat, or over the hard age cap). Old files are parked as
   `*.stale-<ts>` — do not delete them, do not delete anyone's active lock.

6. **NEVER kill or stop a process you did not start** (including ollama).
   If the GPU is busy with no lock held (foreign/unknown process): do not
   start; report it to the Owner in your session summary.

## Reference

- Exit codes: `0` ok · `2` lock held by a live holder · `3` GPU busy or
  unmeasurable (fail-closed) · `4` stale takeover (success + warning) ·
  `1` error · `130` `run` child interrupted.
- Lock records are JSON: holder, project, purpose, pid, started_utc,
  ttl_min, max_age_h, host. `lock.py status` shows them all.
- Windows/WDDM does not report per-process GPU memory reliably; the total
  `memory.used` is the signal.
- This protocol is advisory-but-mandatory; enforcement work is tracked in
  TASK.md.
