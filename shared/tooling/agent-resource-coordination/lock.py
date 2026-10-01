#!/usr/bin/env python3
"""Machine-wide advisory locks for resources shared by concurrent agents.

Canonical helper of the agent resource-coordination protocol
(mdlslab shared/tooling/agent-resource-coordination/PROTOCOL.md).
Stdlib only; Windows-first, POSIX-compatible.

Locks are JSON files <resource>.lock inside the lock directory
(AGENT_LOCK_DIR env var, --dir, or default C:\\projects\\.locks), e.g.
gpu.lock, download.lock. Acquisition is atomic (O_CREAT | O_EXCL).

Two holding patterns:

1. `run` (recommended for scripted work) — lock lifetime is bound to a
   child process: lock.py acquires, starts the command, waits, and always
   releases afterwards. The recorded PID is alive exactly while the
   resource is in use, so liveness is meaningful.

2. `acquire`/`release` (manual, for interactive agent sessions) — no
   durable PID exists, so freshness is time-based: the lock is held while
   its heartbeat (file mtime, refreshable via `touch`) is younger than
   --ttl-min. Release explicitly when done; a forgotten lock expires by
   itself. Pass --anchor-pid to bind manual locks to a long-lived process
   you own (then liveness, not time, decides).

In both patterns a stale lock (dead owner PID, or heartbeat/TTL expired,
or older than the hard --max-age-h cap) is taken over automatically; the
previous file is parked as <resource>.lock.stale-<timestamp> for
inspection, never silently deleted.

GPU ground truth: `gpu` reads total memory.used from nvidia-smi. On
Windows/WDDM per-process GPU memory is not reported reliably, so the total
is the signal. --require-idle-gpu makes acquisition fail closed: if the
GPU cannot be measured or is above the threshold, nothing is held and the
command refuses to proceed. Treat an idle GPU as mandatory for any
timing/benchmark run, with or without a lock.

Exit codes:
  0  success
  1  usage or IO error
  2  lock held by a live/fresh holder (stdout: holder JSON; stderr: human line)
  3  GPU busy or unmeasurable
  4  success after stale-lock takeover (warning on stderr)
 130  `run`: child interrupted

Examples:
  python lock.py run gpu --holder zcode/timesfm --purpose "phase3 walk-forward" -- python train.py
  python lock.py acquire gpu --holder zcode/timesfm --require-idle-gpu
  python lock.py touch gpu            # refresh a manual lock's heartbeat
  python lock.py status
  python lock.py release gpu --holder zcode/timesfm
  python lock.py gpu --threshold-mib 2048
"""

from __future__ import annotations

import argparse
import ctypes
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOCK_DIR = Path(r"C:\projects\.locks")
DEFAULT_IDLE_THRESHOLD_MIB = 2048
DEFAULT_TTL_MIN = 240.0
DEFAULT_MAX_AGE_H = 24.0
STILL_ACTIVE = 259  # Windows GetExitCodeProcess "still running" code
STALE_KEEP = 5  # parked stale files kept per resource


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_utc(text: str) -> float:
    try:
        return datetime.fromisoformat(str(text)).timestamp()
    except (TypeError, ValueError):
        return 0.0


def pid_alive(pid: int | None) -> bool:
    """True if a process with this PID exists and is running.

    Never use os.kill(pid, 0) on Windows: any signal other than the two
    CTRL events terminates the target process there.
    """
    if not pid or pid < 0:
        return False
    if os.name == "nt":
        kernel32 = ctypes.windll.kernel32
        PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            return False
        try:
            code = ctypes.c_ulong()
            if not kernel32.GetExitCodeProcess(handle, ctypes.byref(code)):
                return False
            return code.value == STILL_ACTIVE
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def gpu_state(threshold_mib: int) -> dict:
    """Total GPU memory from nvidia-smi; `ok` is False when unmeasurable."""
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"ok": False, "error": f"nvidia-smi unavailable: {exc}"}
    lines = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
    if proc.returncode != 0 or not lines:
        return {"ok": False, "error": f"nvidia-smi rc={proc.returncode}: {proc.stderr.strip()[:200]}"}
    parts = [p.strip() for p in lines[0].split(",")]
    if len(parts) != 2 or not all(p.isdigit() for p in parts):
        return {"ok": False, "error": f"unparsed output: {lines[0]!r}"}
    used, total = int(parts[0]), int(parts[1])
    return {
        "ok": True,
        "used_mib": used,
        "total_mib": total,
        "threshold_mib": threshold_mib,
        "busy": used > threshold_mib,
    }


def lock_path(args: argparse.Namespace, resource: str) -> Path:
    base = Path(os.environ.get("AGENT_LOCK_DIR") or getattr(args, "dir", None) or DEFAULT_LOCK_DIR)
    return base / f"{resource}.lock"


def read_lock(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else None
    except (OSError, ValueError):
        return None


def lock_age_s(path: Path, record: dict) -> float:
    """Seconds since the lock's strongest freshness signal (mtime heartbeat)."""
    try:
        return max(0.0, time.time() - path.stat().st_mtime)
    except OSError:
        return time.time() - parse_utc(record.get("started_utc", ""))


def is_held(path: Path, record: dict) -> tuple[bool, str]:
    """Decide whether an existing lock still counts, and why (or why not)."""
    pid = record.get("pid")
    age_h = lock_age_s(path, record) / 3600.0
    max_age_h = float(record.get("max_age_h") or DEFAULT_MAX_AGE_H)
    if pid is not None:
        if pid_alive(int(pid)) and age_h <= max_age_h:
            return True, f"owner pid {pid} alive, age {age_h:.1f}h"
        if not pid_alive(int(pid)):
            return False, f"owner pid {pid} dead"
        return False, f"age {age_h:.1f}h over hard cap {max_age_h}h"
    ttl_min = float(record.get("ttl_min") or DEFAULT_TTL_MIN)
    age_min = age_h * 60.0
    if age_min <= ttl_min:
        return True, f"manual lock, heartbeat age {age_min:.0f}min <= ttl {ttl_min:.0f}min"
    return False, f"manual lock expired: heartbeat age {age_min:.0f}min > ttl {ttl_min:.0f}min"


def park_stale(path: Path, reason: str) -> None:
    """Move a stale/corrupt lock aside instead of deleting evidence."""
    parked = path.with_name(f"{path.name}.stale-{int(time.time())}")
    try:
        path.replace(parked)
    except OSError as exc:
        print(f"error: cannot park stale lock {path}: {exc}", file=sys.stderr)
        return
    siblings = sorted(path.parent.glob(f"{path.name}.stale-*"), key=lambda p: p.stat().st_mtime)
    for old in siblings[:-STALE_KEEP]:
        old.unlink(missing_ok=True)
    print(f"warning: took over {path.name} ({reason}); previous parked at {parked.name}", file=sys.stderr)


def write_lock(path: Path, args: argparse.Namespace, resource: str, pid: int | None) -> dict:
    record = {
        "resource": resource,
        "holder": args.holder,
        "project": getattr(args, "project", "") or "",
        "purpose": getattr(args, "purpose", "") or "",
        "pid": pid,
        "started_utc": utcnow(),
        "ttl_min": getattr(args, "ttl_min", DEFAULT_TTL_MIN) or DEFAULT_TTL_MIN,
        "max_age_h": getattr(args, "max_age_h", DEFAULT_MAX_AGE_H) or DEFAULT_MAX_AGE_H,
        "host": os.environ.get("COMPUTERNAME") or os.uname().nodename,
    }
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    return record


def acquire_once(args: argparse.Namespace, resource: str, pid: int | None) -> tuple[int, dict]:
    """One acquire attempt; returns (exit_code, lock_record_or_holder)."""
    path = lock_path(args, resource)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        record = write_lock(path, args, resource, pid)
    except FileExistsError:
        prev = read_lock(path)
        if prev is None:
            park_stale(path, "unreadable/corrupt")
            return 1, {}
        held, why = is_held(path, prev)
        if held:
            print(json.dumps({"acquired": False, "resource": resource, "holder": prev, "why": why}, ensure_ascii=False))
            print(
                f"{resource}: held by {prev.get('holder')} (pid {prev.get('pid')}) "
                f"since {prev.get('started_utc')}; purpose: {prev.get('purpose')}; {why}",
                file=sys.stderr,
            )
            return 2, prev
        park_stale(path, why)
        return 1, {}
    if getattr(args, "require_idle_gpu", False):
        state = gpu_state(args.threshold_mib)
        if not state["ok"] or state["busy"]:
            path.unlink(missing_ok=True)
            print(json.dumps({"acquired": False, "resource": resource, "gpu": state}, ensure_ascii=False))
            detail = state.get("error") or f"used {state.get('used_mib')} MiB > {state.get('threshold_mib')} MiB"
            print(f"{resource}: refused, GPU not idle ({detail})", file=sys.stderr)
            return 3, {}
    print(json.dumps({"acquired": True, "resource": resource, "lock": record}, ensure_ascii=False))
    return 0, record


def release_quiet(args: argparse.Namespace, resource: str) -> None:
    path = lock_path(args, resource)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def cmd_acquire(args: argparse.Namespace) -> int:
    pid = args.anchor_pid
    for _attempt in (1, 2):
        code, _ = acquire_once(args, args.resource, pid)
        if code != 1:
            return code
    print(f"{args.resource}: could not acquire (repeated contention)", file=sys.stderr)
    return 1


def cmd_run(args: argparse.Namespace) -> int:
    code, record = acquire_once(args, args.resource, os.getpid())
    if code == 1:  # stale takeover happened once; one clean retry
        code, record = acquire_once(args, args.resource, os.getpid())
    if code != 0:
        return code
    child = None
    try:
        child = subprocess.Popen(args.command)
        rc = child.wait()
        print(json.dumps({"resource": args.resource, "command": args.command, "exit_code": rc}))
        return rc
    except KeyboardInterrupt:
        if child is not None:
            child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
        print(f"{args.resource}: interrupted, child terminated, lock released", file=sys.stderr)
        return 130
    finally:
        release_quiet(args, args.resource)


def cmd_release(args: argparse.Namespace) -> int:
    path = lock_path(args, args.resource)
    if not path.exists():
        print(json.dumps({"released": True, "resource": args.resource, "note": "no lock existed"}))
        return 0
    record = read_lock(path) or {}
    mine = record.get("pid") == os.getpid() or record.get("holder") == args.holder
    if not mine and not args.force:
        print(json.dumps({"released": False, "resource": args.resource, "holder": record}, ensure_ascii=False))
        print(
            f"{args.resource}: lock belongs to {record.get('holder')} (pid {record.get('pid')}); "
            "use --force only if you own it",
            file=sys.stderr,
        )
        return 2
    path.unlink(missing_ok=True)
    print(json.dumps({"released": True, "resource": args.resource, "previous_holder": record.get("holder")}))
    return 0


def cmd_touch(args: argparse.Namespace) -> int:
    path = lock_path(args, args.resource)
    if not path.exists():
        print(f"{args.resource}: no lock to touch", file=sys.stderr)
        return 1
    os.utime(path, None)
    print(json.dumps({"touched": True, "resource": args.resource, "heartbeat_utc": utcnow()}))
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    base = lock_path(args, args.resource if args.resource else "*").parent
    if args.resource:
        paths = [base / f"{args.resource}.lock"]
    else:
        base.mkdir(parents=True, exist_ok=True)
        paths = sorted(base.glob("*.lock"))
    locks = []
    for path in paths:
        if not path.exists():
            continue
        record = read_lock(path) or {"unreadable": True, "path": str(path)}
        held, why = is_held(path, record) if "pid" in record else (False, "unreadable")
        record["_held"] = held
        record["_why"] = why
        record["_path"] = str(path)
        locks.append(record)
    print(json.dumps({"lock_dir": str(base), "locks": locks}, indent=2, ensure_ascii=False))
    return 0


def cmd_gpu(args: argparse.Namespace) -> int:
    state = gpu_state(args.threshold_mib)
    print(json.dumps(state, ensure_ascii=False))
    if not state["ok"] or state["busy"]:
        return 3
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    # `run` takes a command after "--"; cut it out before argparse so that
    # options like --holder are not swallowed by positional parsing.
    run_tail: list[str] | None = None
    for i in (0, 2):  # subcommand slot, possibly after a global --dir VALUE
        if len(argv) > i and argv[i] == "run":
            if "--" in argv[i:]:
                j = argv.index("--", i)
                run_tail = argv[j + 1 :]
                argv = argv[:j]
            break
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dir", help="lock directory (default: AGENT_LOCK_DIR or C:\\projects\\.locks)")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p: argparse.ArgumentParser, with_gpu: bool = False) -> None:
        p.add_argument("resource", help="e.g. gpu, download")
        p.add_argument("--holder", required=True, help='"<client>/<project>", e.g. zcode/timesfm')
        p.add_argument("--purpose", default="", help="what the run does")
        p.add_argument("--project", default="", help="project path or name")
        p.add_argument("--ttl-min", type=float, default=DEFAULT_TTL_MIN, help="manual-lock heartbeat TTL")
        p.add_argument("--max-age-h", type=float, default=DEFAULT_MAX_AGE_H, help="hard staleness cap")
        if with_gpu:
            p.add_argument("--require-idle-gpu", action="store_true", help="fail closed if GPU is busy/unmeasurable")
            p.add_argument("--threshold-mib", type=int, default=DEFAULT_IDLE_THRESHOLD_MIB)

    p_run = sub.add_parser("run", help="hold the lock for the duration of a command")
    common(p_run, with_gpu=True)
    p_run.set_defaults(func=cmd_run)

    p_acquire = sub.add_parser("acquire", help="claim a resource (manual; release explicitly)")
    common(p_acquire, with_gpu=True)
    p_acquire.add_argument("--anchor-pid", type=int, default=None, help="bind liveness to a long-lived PID you own")
    p_acquire.set_defaults(func=cmd_acquire)

    p_release = sub.add_parser("release", help="release a lock you hold")
    p_release.add_argument("resource")
    p_release.add_argument("--holder", default="", help="must match acquisition holder or pid")
    p_release.add_argument("--force", action="store_true", help="release despite holder mismatch (own locks only)")
    p_release.set_defaults(func=cmd_release)

    p_touch = sub.add_parser("touch", help="refresh a manual lock's heartbeat")
    p_touch.add_argument("resource")
    p_touch.set_defaults(func=cmd_touch)

    p_status = sub.add_parser("status", help="show lock(s)")
    p_status.add_argument("resource", nargs="?", default=None)
    p_status.set_defaults(func=cmd_status)

    p_gpu = sub.add_parser("gpu", help="probe total GPU memory; exit 3 if busy")
    p_gpu.add_argument("--threshold-mib", type=int, default=DEFAULT_IDLE_THRESHOLD_MIB)
    p_gpu.set_defaults(func=cmd_gpu)

    args = parser.parse_args(argv)
    if args.func is cmd_run:
        if not run_tail:
            parser.error('run: expected "--" followed by the command to hold the lock for')
        args.command = run_tail
    try:
        return args.func(args)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
