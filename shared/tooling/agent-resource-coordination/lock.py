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
   --ttl-min (default 45). Release explicitly when done; a forgotten lock
   expires by itself. Pass --anchor-pid to bind manual locks to a
   long-lived process you own (then liveness, not time, decides).

Stale handling: a lock whose owner PID is dead (verified by PID AND
process creation time, to survive Windows PID reuse), whose manual TTL
expired, or which is older than the hard --max-age-h cap, is taken over.
Takeovers are serialized by a short-lived `<resource>.lock.takeover`
guard with re-verification of the lock's identity, so two concurrent
takeovers cannot both succeed (review 2026-10-01, finding 1). The previous
file is parked as <resource>.lock.stale-<timestamp>, never silently
deleted.

GPU ground truth: `gpu` reads total memory.used from nvidia-smi and, when
an ollama server answers on 127.0.0.1:11434, its resident models with
VRAM sizes (ollama's own accounting; per-process attribution is
unavailable on Windows/WDDM). The busy decision uses nvidia-smi only;
ollama data is attribution info. --require-idle-gpu fails closed: if the
GPU cannot be measured or is above the threshold, nothing is held and the
command refuses to proceed. Treat an idle GPU as mandatory for any
timing/benchmark run, with or without a lock.

Exit codes:
  0    success
  1    usage, IO error, or repeated contention
  2    lock held by a live/fresh holder (stdout: holder JSON; stderr: human line)
  3    GPU busy or unmeasurable
  4    success after stale-lock takeover (warning on stderr; `acquire` only —
       `run` returns the child's exit code and reports a takeover in its JSON)
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
import platform
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_LOCK_DIR = Path(r"C:\projects\.locks")
DEFAULT_IDLE_THRESHOLD_MIB = 2048
DEFAULT_TTL_MIN = 45.0
DEFAULT_MAX_AGE_H = 24.0
GUARD_MAX_AGE_S = 30.0  # a .takeover guard older than this is removable
GUARD_WAIT_S = 5.0  # how long one takeover waits for the guard
OLLAMA_PS_URL = "http://127.0.0.1:11434/api/ps"
OLLAMA_TIMEOUT_S = 2.0
STILL_ACTIVE = 259  # Windows GetExitCodeProcess "still running" code
STALE_KEEP = 5  # parked stale files kept per resource


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def parse_utc(text: str) -> float:
    try:
        return datetime.fromisoformat(str(text)).timestamp()
    except (TypeError, ValueError):
        return 0.0


class _FILETIME(ctypes.Structure):
    _fields_ = [("dwLowDateTime", ctypes.c_ulong), ("dwHighDateTime", ctypes.c_ulong)]


def _open_process(pid: int) -> int:
    kernel32 = ctypes.windll.kernel32
    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    return kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)


def _process_creation_ts(pid: int) -> float | None:
    """Process creation time as unix seconds; None when unavailable.

    Comparing PID + creation time survives Windows PID reuse (review
    2026-10-01, finding 5): a reused PID has a different creation time.
    """
    if os.name != "nt":
        return None
    handle = _open_process(pid)
    if not handle:
        return None
    try:
        kernel32 = ctypes.windll.kernel32
        creation, exit_, kernel, user = _FILETIME(), _FILETIME(), _FILETIME(), _FILETIME()
        if not kernel32.GetProcessTimes(
            handle, ctypes.byref(creation), ctypes.byref(exit_), ctypes.byref(kernel), ctypes.byref(user)
        ):
            return None
        ticks = (creation.dwHighDateTime << 32) | creation.dwLowDateTime
        if ticks == 0:
            return None
        return ticks / 1e7 - 11644473600.0  # FILETIME epoch 1601-01-01 -> unix
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def pid_alive(pid: int | None) -> bool:
    """True if a process with this PID exists and is running.

    Never use os.kill(pid, 0) on Windows: any signal other than the two
    CTRL events terminates the target process there.
    """
    if not pid or pid < 0:
        return False
    if os.name == "nt":
        handle = _open_process(pid)
        if not handle:
            return False
        try:
            kernel32 = ctypes.windll.kernel32
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


def pid_owner_matches(pid: int | None, started_utc: str | None) -> bool:
    """PID liveness, disambiguated by process creation time when known."""
    if not pid_alive(pid):
        return False
    if started_utc is None:
        return True
    creation = _process_creation_ts(int(pid))  # type: ignore[arg-type]
    if creation is None:
        return True  # cannot verify further (non-Windows or access denied)
    return abs(creation - parse_utc(started_utc)) <= 1.0


def pid_started_utc(pid: int | None) -> str | None:
    if pid is None:
        return None
    creation = _process_creation_ts(pid)
    if creation is None:
        return None
    return datetime.fromtimestamp(creation, tz=timezone.utc).isoformat(timespec="seconds")


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


def ollama_state() -> dict:
    """Resident ollama models with VRAM (attribution only, never a decision).

    ollama's own accounting fills the gap nvidia-smi cannot on Windows/WDDM
    (review 2026-10-01, finding 4). Unreachable server is not an error.
    """
    try:
        with urllib.request.urlopen(OLLAMA_PS_URL, timeout=OLLAMA_TIMEOUT_S) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [
            {"name": m.get("name"), "size_vram_mib": round(float(m.get("size_vram") or 0) / 2**20, 1)}
            for m in data.get("models", [])
        ]
        return {"ok": True, "models": models}
    except (OSError, urllib.error.URLError, ValueError):
        return {"ok": False, "note": "no ollama server on 11434"}
    except Exception as exc:  # never let attribution break the protocol
        return {"ok": False, "note": str(exc)[:120]}


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
        started = record.get("pid_started_utc")
        if pid_owner_matches(int(pid), started) and age_h <= max_age_h:
            return True, f"owner pid {pid} alive, age {age_h:.1f}h"
        if not pid_owner_matches(int(pid), started):
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


def guarded_park(path: Path, expected: tuple | None, reason: str) -> bool:
    """Park a stale lock under a takeover guard, re-verifying identity.

    Serializes concurrent takeovers: only the process holding the
    `<resource>.lock.takeover` guard may park, and it parks only if the
    lock's (pid, started_utc) still equals what was judged stale
    (review 2026-10-01, finding 1). Returns True when the park happened
    (or the lock vanished); False when the state changed or the guard
    stayed busy — the caller should re-evaluate from scratch.
    """
    guard = path.with_name(path.name + ".takeover")
    deadline = time.time() + GUARD_WAIT_S
    while time.time() < deadline:
        try:
            fd = os.open(guard, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            try:
                if time.time() - guard.stat().st_mtime > GUARD_MAX_AGE_S:
                    guard.unlink(missing_ok=True)  # wedged by a crash; age-capped
                    continue
            except OSError:
                pass
            time.sleep(0.1)
            continue
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump({"pid": os.getpid(), "started_utc": utcnow(), "reason": reason}, fh)
            if not path.exists():
                return True  # someone else already parked it
            cur = read_lock(path)
            identity = (cur.get("pid"), cur.get("started_utc")) if cur else None
            if identity != expected:
                return False  # a fresh lock appeared under us; re-evaluate
            park_stale(path, reason)
            return True
        finally:
            guard.unlink(missing_ok=True)
    return False


def write_lock(
    path: Path, args: argparse.Namespace, resource: str, pid: int | None, extra: dict
) -> dict:
    record = {
        "resource": resource,
        "holder": args.holder,
        "project": getattr(args, "project", "") or "",
        "purpose": getattr(args, "purpose", "") or "",
        "pid": pid,
        "pid_started_utc": pid_started_utc(pid),
        "started_utc": utcnow(),
        "ttl_min": getattr(args, "ttl_min", DEFAULT_TTL_MIN) or DEFAULT_TTL_MIN,
        "max_age_h": getattr(args, "max_age_h", DEFAULT_MAX_AGE_H) or DEFAULT_MAX_AGE_H,
        "host": platform.node(),
    }
    record.update(extra)
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    with os.fdopen(fd, "w", encoding="utf-8") as fh:
        json.dump(record, fh, indent=2, ensure_ascii=False)
    return record


def acquire_once(args: argparse.Namespace, resource: str, pid: int | None) -> tuple[int, dict, str]:
    """One acquire attempt. Returns (exit_code, record, event)."""
    path = lock_path(args, resource)
    path.parent.mkdir(parents=True, exist_ok=True)
    extra: dict = {}
    if resource == "gpu":
        snap = gpu_state(args.threshold_mib)
        extra["gpu_at_start"] = snap if snap["ok"] else {"probe": "unavailable", "error": snap.get("error")}
    try:
        record = write_lock(path, args, resource, pid, extra)
    except FileExistsError:
        prev = read_lock(path)
        if prev is not None:
            held, why = is_held(path, prev)
            if held:
                print(
                    json.dumps({"acquired": False, "resource": resource, "holder": prev, "why": why},
                               ensure_ascii=False)
                )
                print(
                    f"{resource}: held by {prev.get('holder')} (pid {prev.get('pid')}) "
                    f"since {prev.get('started_utc')}; purpose: {prev.get('purpose')}; {why}",
                    file=sys.stderr,
                )
                return 2, prev, "held"
            expected = (prev.get("pid"), prev.get("started_utc"))
            if guarded_park(path, expected, why):
                return 1, {}, "takeover-parked"
            return 1, {}, "state-changed"
        if guarded_park(path, None, "unreadable/corrupt"):
            return 1, {}, "takeover-parked"
        return 1, {}, "state-changed"
    if getattr(args, "require_idle_gpu", False):
        state = gpu_state(args.threshold_mib)
        if not state["ok"] or state["busy"]:
            path.unlink(missing_ok=True)
            print(json.dumps({"acquired": False, "resource": resource, "gpu": state}, ensure_ascii=False))
            detail = state.get("error") or f"used {state.get('used_mib')} MiB > {state.get('threshold_mib')} MiB"
            print(f"{resource}: refused, GPU not idle ({detail})", file=sys.stderr)
            return 3, {}, "refused-gpu"
    print(json.dumps({"acquired": True, "resource": resource, "lock": record}, ensure_ascii=False))
    return 0, record, "acquired"


def acquire_with_retry(args: argparse.Namespace, resource: str, pid: int | None, attempts: int = 3):
    """Retry loop around acquire_once; a takeover-park turns success into 4."""
    took_over = False
    for i in range(attempts):
        code, record, event = acquire_once(args, resource, pid)
        if code == 0:
            return (4 if took_over else 0), record
        if code in (2, 3):
            return code, record
        if event == "takeover-parked":
            took_over = True
        time.sleep(0.05 * (i + 1))
    print(f"{resource}: could not acquire after {attempts} attempts", file=sys.stderr)
    return 1, {}


def release_quiet(args: argparse.Namespace, resource: str) -> None:
    path = lock_path(args, resource)
    try:
        path.unlink(missing_ok=True)
    except OSError:
        pass


def cmd_acquire(args: argparse.Namespace) -> int:
    code, _ = acquire_with_retry(args, args.resource, args.anchor_pid)
    return code


def cmd_run(args: argparse.Namespace) -> int:
    code, _ = acquire_with_retry(args, args.resource, os.getpid())
    if code not in (0, 4):
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
    state["ollama"] = ollama_state()
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

    p_gpu = sub.add_parser("gpu", help="probe total GPU memory (and ollama residents); exit 3 if busy")
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
