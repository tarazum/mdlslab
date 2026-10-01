"""CONT-002 mechanics smoke (M2b, owner-ordered 2026-10-01): prove the state
export/import plumbing between two DIFFERENT cores. Mechanics only — ZERO
behavioral claims, no R ratio, single seed, no model-quality judgments.

Usage (from anywhere; MUST run under the shared GPU lock, see
shared/tooling/agent-resource-coordination/PROTOCOL.md — the 22 GB core-B
load dominates the GPU budget):

    python labs/continuity/experiments/CONT-000/run_cont002_mechanics.py

Phases (all inside one process, one lock hold):
1. Import the LOCAL GGUF into Ollama via a Modelfile (`FROM <local path>` — a
   local import, not a download) under a collision-free name; record the
   created model's digest via /api/ps after loading (CN-001 method).
2. Core A (granite-code:8b, digest pinned) runs the dr-0001 LEARNING session
   only (session 1, seed 11, arm B) and exports memory-export.json
   (continuity-memory-export v1 — the CONT-002 state carrier).
3. The export is imported into a FRESH core-B store; schema + round-trip are
   verified offline (re-export must equal the original episodes exactly).
4. Core B (the imported model) runs the dr-0001 HELD-OUT probe session only
   (session 2) twice: with the imported state, then with a clean (empty)
   store. Sampling options travel in every request (temp 0.0, seed 11,
   num_ctx 4096 — PB-071). The fixture file is never modified; session
   slicing happens on the validated in-memory scenario dict.
5. Checklist JSON: (1) import+digest, (2) schema-valid round-trip,
   (3) memory.injected visible in the core-B trace, (4) both core-B traces
   re-validate from disk, (5) no cross-core plumbing errors.

Probe outcomes are recorded as OBSERVATIONS ONLY. Suspect core-B output
(possible chat-template mismatch on GGUF import) is recorded for a CN-NNN
finding and does not fail the plumbing checks (2)-(5).

Fail-closed: GGUF missing or Ollama unreachable -> exit 2 before any work.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity import PROTOCOL_VERSION  # noqa: E402
from continuity.events import EventJournal, validate_trace  # noqa: E402
from continuity.fixtures import load_scenario  # noqa: E402
from continuity.memory import (  # noqa: E402
    EXPORT_FORMAT,
    EXPORT_VERSION,
    MemoryStore,
)
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import MEMORY_TOP_K, Budget, run_scenario  # noqa: E402

# --- fixed configuration (M2b brief) ---
SCENARIO_ID = "dr-0001"
CORE_A_MODEL = "granite-code:8b"
CORE_A_DIGEST_PREFIX = "36c3c3b9683b"  # pinned since P0a (CN-001)
CORE_B_MODEL = "qwen36-35b-a3b:mdlslab"  # collision-free local import name
GGUF_PATH = "C:/Models/qwen36_Q4_K_M/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
SEED = 11
TEMPERATURE = 0.0
NUM_CTX = 4096
WARMUP_PROMPT = "Reply with the single word: ready."
SCENARIO_BUDGET = {"max_turns": 10, "max_total_tokens": 50_000, "wall_clock_s": 600.0}
DETERMINISM_CAVEAT = (
    "greedy+seed does not guarantee identical outputs across batch sizes or "
    "backends (PB-071); cross-core outputs are in no way expected to match"
)

REQUIRED_EPISODE_FIELDS = (
    "created_utc", "run_id", "scenario", "session", "turn_ref", "role", "content",
)


def git_rev() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(LAB_ROOT), stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def http_get_json(url: str, timeout: int = 30) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def ollama_tags(base_url: str) -> list[str]:
    return [m.get("name", "") for m in http_get_json(base_url + "/api/tags").get("models", [])]


def ps_snapshot(base_url: str) -> list[dict]:
    """Ollama /api/ps attribution snapshot (CN-005 monitoring rule)."""
    try:
        return [
            {
                "name": m.get("name", ""),
                "digest": m.get("digest", ""),
                "size_vram": m.get("size_vram", 0),
            }
            for m in http_get_json(base_url + "/api/ps").get("models", [])
        ]
    except Exception as exc:
        return [{"error": f"/api/ps failed: {exc}"}]


def show_summary(base_url: str, model: str) -> dict:
    """Non-digest model facts from /api/show (chat-template presence)."""
    request = urllib.request.Request(
        base_url + "/api/show",
        data=json.dumps({"model": model}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        return {"error": f"/api/show failed: {exc}"}
    template = data.get("template") or ""
    return {
        "chat_template_present": bool(template.strip()),
        "chat_template_chars": len(template),
        "families": data.get("details", {}).get("families", []),
        "parameter_size": data.get("details", {}).get("parameter_size", ""),
    }


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=True), encoding="utf-8")


def load_phase_scenarios() -> tuple[dict, dict]:
    """Validated dr-0001 fixture sliced into learning (s1) / probe (s2)."""
    scenario = load_scenario(
        str(LAB_ROOT / "fixtures" / "v1" / "delayed_recall" / f"{SCENARIO_ID}.json")
    )
    by_index = {s["index"]: s for s in scenario["sessions"]}
    learning = dict(scenario, sessions=[by_index[1]])
    probe = dict(scenario, sessions=[by_index[2]])
    return learning, probe


def emit_run_start(
    journal: EventJournal, kind: str, model: str, extra: dict[str, Any]
) -> None:
    journal.emit(
        "run.start",
        {
            "protocol_version": PROTOCOL_VERSION,
            "kind": kind,
            "arm": "B",
            "scenario": SCENARIO_ID,
            "model": model,
            "seed": SEED,
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "determinism_caveat": DETERMINISM_CAVEAT,
            "git_rev": git_rev(),
            **extra,
        },
    )


def finalize_run(
    journal: EventJournal,
    out_dir: Path,
    run_id: str,
    summary: dict[str, Any],
    provider: OllamaProvider,
) -> tuple[bool, list[str]]:
    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))
    summary["model_digest"] = pinned["digest"]
    trace_ok, trace_errors = validate_trace(str(out_dir / "trace.jsonl"))
    summary["run_id"] = run_id
    summary["trace_schema_valid"] = trace_ok
    summary["trace_validation_errors"] = trace_errors
    summary["completed"] = (not summary["stopped"]) and trace_ok
    journal.emit(
        "run.end",
        {
            "completed": summary["completed"],
            "trace_schema_valid": trace_ok,
            "probes_passed": summary["probes_passed"],
            "probes_total": summary["probes_total"],
        },
    )
    journal.close()
    write_json(out_dir / "summary.json", summary)
    return trace_ok, trace_errors


def verify_roundtrip(export_path: Path, fresh_store_path: Path, probe_query: str) -> dict:
    """Offline check (2): schema validity + import into a fresh store +
    exact round-trip + deterministic retrieval on the probe query."""
    data = json.loads(export_path.read_text(encoding="utf-8"))
    errors: list[str] = []
    if data.get("format") != EXPORT_FORMAT:
        errors.append(f"format is {data.get('format')!r}, expected {EXPORT_FORMAT!r}")
    if data.get("version") != EXPORT_VERSION:
        errors.append(f"version is {data.get('version')!r}, expected {EXPORT_VERSION!r}")
    episodes = data.get("episodes")
    if not isinstance(episodes, list) or not episodes:
        errors.append("episodes missing/empty")
        episodes = []
    for i, ep in enumerate(episodes):
        missing = [f for f in REQUIRED_EPISODE_FIELDS if f not in ep]
        if missing:
            errors.append(f"episode {i} missing fields {missing}")
    imported_count = 0
    retrieval_refs: list[str] = []
    episodes_equal = False
    if not errors:
        store = MemoryStore(str(fresh_store_path))
        try:
            imported_count = store.import_json(str(export_path))
            re_export = store.export_dict()
            episodes_equal = re_export["episodes"] == episodes
            if not episodes_equal:
                errors.append("round-trip re-export differs from source export")
            hits = store.retrieve(probe_query, scenario=SCENARIO_ID, limit=MEMORY_TOP_K)
            retrieval_refs = [f"{h['turn_ref']}|{h['role']}" for h in hits]
        finally:
            store.close()
    return {
        "export_path": export_path.name,
        "format": data.get("format"),
        "version": data.get("version"),
        "episode_count": len(episodes),
        "imported_count": imported_count,
        "round_trip_episodes_equal": episodes_equal,
        "fresh_store": fresh_store_path.name,
        "probe_query_retrieval_refs": retrieval_refs,
        "errors": errors,
        "pass": not errors and imported_count == len(episodes),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    args = parser.parse_args()
    base_url = args.base_url.rstrip("/")

    # --- fail-closed preflight (no inference yet) ---
    gguf = Path(GGUF_PATH)
    if not gguf.is_file():
        print(f"FAIL-CLOSED: GGUF not found: {GGUF_PATH}", file=sys.stderr)
        return 2
    ollama_exe = shutil.which("ollama")
    if ollama_exe is None:
        print("FAIL-CLOSED: ollama CLI not on PATH", file=sys.stderr)
        return 2
    try:
        ollama_version = http_get_json(base_url + "/api/version").get("version", "?")
    except Exception as exc:
        print(f"FAIL-CLOSED: Ollama unreachable at {base_url}: {exc}", file=sys.stderr)
        return 2
    tags_before = ollama_tags(base_url)
    if CORE_B_MODEL in tags_before:
        print(
            f"FAIL-CLOSED: model name {CORE_B_MODEL!r} already exists (collision); "
            "refusing to overwrite",
            file=sys.stderr,
        )
        return 2
    if CORE_A_MODEL not in tags_before:
        print(f"FAIL-CLOSED: core A model {CORE_A_MODEL!r} missing", file=sys.stderr)
        return 2

    run_id = time.strftime("cont002-mechanics-%Y%m%d-%H%M%S")
    out_root = LAB_ROOT / "results" / "CONT-000" / run_id
    out_root.mkdir(parents=True, exist_ok=True)
    cross_core_errors: list[str] = []
    gpu_at_start = ps_snapshot(base_url)
    print(f"run_id: {run_id}")
    print(f"artifacts: {out_root}")

    learning, probe = load_phase_scenarios()
    probe_query = probe["sessions"][0]["turns"][0]["text"]

    # --- phase 1: Modelfile import of the local GGUF (no download) ---
    modelfile = out_root / "Modelfile"
    modelfile.write_text(
        f"# CONT-002 mechanics smoke (M2b) — local import, not a download\n"
        f"FROM {GGUF_PATH}\n",
        encoding="utf-8",
    )
    create_started = time.monotonic()
    create = subprocess.run(
        [ollama_exe, "create", CORE_B_MODEL, "-f", str(modelfile)],
        capture_output=True,
        text=True,
        timeout=1200,
    )
    create_s = round(time.monotonic() - create_started, 1)
    tags_after = ollama_tags(base_url)
    check1 = {
        "model": CORE_B_MODEL,
        "modelfile": "Modelfile",
        "from": GGUF_PATH,
        "create_exit": create.returncode,
        "create_stdout_tail": (create.stdout or "")[-400:],
        "create_stderr_tail": (create.stderr or "")[-400:],
        "create_wall_s": create_s,
        "tags_contains_model_after_create": CORE_B_MODEL in tags_after,
        "show": show_summary(base_url, CORE_B_MODEL),
    }
    check1["pass"] = (
        create.returncode == 0
        and CORE_B_MODEL in tags_after
        and "error" not in check1["show"]
    )
    print(f"[1] modelfile import: pass={check1['pass']} ({create_s}s) show={check1['show']}")
    if not check1["pass"]:
        write_json(out_root / "model-digests.json", {"ollama_version": ollama_version,
                                                      "tags_before": tags_before})
        write_json(out_root / "checklist.json", {"run_id": run_id, "checks":
                      {"1_modelfile_import": check1}, "cross_core_errors": cross_core_errors})
        print("Modelfile import FAILED (mechanics check 1); stopping before inference",
              file=sys.stderr)
        return 1

    digests: dict[str, Any] = {
        "created_utc": utc_now(),
        "ollama_version": ollama_version,
        "gpu_at_start": gpu_at_start,
        "core_a_model": CORE_A_MODEL,
        "core_b_model": CORE_B_MODEL,
        "core_b_created_wall_s": create_s,
        "core_b_show": check1["show"],
        "tags_before_create": tags_before,
    }

    # --- phase 2: core A learning session (arm B) + state export ---
    coreA_dir = out_root / "coreA"
    coreA_dir.mkdir(exist_ok=True)
    provider_a = OllamaProvider(
        base_url=base_url, model=CORE_A_MODEL,
        temperature=TEMPERATURE, seed=SEED, num_ctx=NUM_CTX, keep_alive="30m",
    )
    try:
        learn_started = time.monotonic()
        warm_a_started = time.monotonic()
        warm_a = provider_a.chat([{"role": "user", "content": WARMUP_PROMPT}])
        warm_a_s = round(time.monotonic() - warm_a_started, 1)
        pin_a = provider_a.model_info()
        if not pin_a["digest"].startswith(CORE_A_DIGEST_PREFIX):
            raise RuntimeError(
                f"core-A digest {pin_a['digest']!r} != pinned prefix {CORE_A_DIGEST_PREFIX!r}"
            )
        digests["core_a_digest"] = pin_a["digest"]
        digests["core_a_warmup_s"] = warm_a_s
        digests["core_a_warmup_reply"] = warm_a["content"][:200]
        journal_a = EventJournal(str(coreA_dir / "trace.jsonl"), f"{run_id}-coreA-learn")
        emit_run_start(
            journal_a, "cont002-mechanics-coreA-learn", CORE_A_MODEL,
            {
                "phase": "learning session (dr-0001 session 1 only)",
                "memory": {"backend": "sqlite", "db": "coreA/memory.sqlite3",
                           "note": "core-A local store; export is the CONT-002 carrier"},
            },
        )
        journal_a.emit(
            "env.snapshot",
            {
                "python": platform.python_version(),
                "platform": platform.platform(),
                "ollama_version": ollama_version,
                "model": CORE_A_MODEL,
                "model_digest": pin_a["digest"],
                "seed": SEED,
                "arm": "B",
                "determinism_caveat": DETERMINISM_CAVEAT,
            },
        )
        memory_a = MemoryStore(str(coreA_dir / "memory.sqlite3"))
        summary_a = run_scenario(learning, provider_a, journal_a,
                                 Budget(**SCENARIO_BUDGET), arm="B", memory=memory_a)
        export_a = memory_a.export_json(str(coreA_dir / "memory-export.json"))
        summary_a["memory_episodes_exported"] = export_a["episode_count"]
        memory_a.close()
        trace_a_ok, trace_a_errors = finalize_run(
            journal_a, coreA_dir, f"{run_id}-coreA-learn", summary_a, provider_a
        )
        digests["core_a_learn_wall_s"] = round(time.monotonic() - learn_started, 1)
        print(
            f"[2] coreA learning: turns={summary_a['turns']} "
            f"episodes={export_a['episode_count']} trace_ok={trace_a_ok}"
        )
    except Exception as exc:
        cross_core_errors.append(f"coreA learning phase: {type(exc).__name__}: {exc}")
        print(f"ERROR coreA phase: {exc}", file=sys.stderr)
        trace_a_ok, trace_a_errors, summary_a = False, [str(exc)], {}

    # --- phase 3: import into a fresh core-B store + round-trip verify ---
    coreB_state_dir = out_root / "coreB-state"
    coreB_state_dir.mkdir(exist_ok=True)
    if (coreA_dir / "memory-export.json").is_file():
        check2 = verify_roundtrip(
            coreA_dir / "memory-export.json",
            coreB_state_dir / "memory.sqlite3",
            probe_query,
        )
    else:
        check2 = {
            "errors": ["coreA/memory-export.json missing (core-A phase failed)"],
            "pass": False,
        }
    print(f"[3] round-trip: pass={check2['pass']} imported={check2.get('imported_count')}")

    # --- phase 4: core B probe runs (state, then clean) ---
    provider_b = OllamaProvider(
        base_url=base_url, model=CORE_B_MODEL,
        temperature=TEMPERATURE, seed=SEED, num_ctx=NUM_CTX,
        keep_alive="45m", timeout_s=900,
    )
    coreB_results: dict[str, dict] = {}
    # The state store IS the fresh store populated by verify_roundtrip (the
    # import above); the clean run gets a brand-new empty store.
    try:
        warm_b_started = time.monotonic()
        warm_b = provider_b.chat([{"role": "user", "content": WARMUP_PROMPT}])
        warm_b_s = round(time.monotonic() - warm_b_started, 1)
        pin_b = provider_b.model_info()  # created-model digest via /api/ps (CN-001)
        digests["core_b_digest"] = pin_b["digest"]
        digests["core_b_size_vram"] = pin_b.get("size_vram", 0)
        digests["core_b_load_warmup_s"] = warm_b_s
        digests["core_b_warmup_reply"] = warm_b["content"][:400]
        digests["core_b_warmup_reply_has_ready"] = "ready" in warm_b["content"].lower()
        digests["gpu_at_coreB_loaded"] = ps_snapshot(base_url)
        print(
            f"[4] coreB loaded: digest={pin_b['digest'][:16]}... "
            f"load+warmup {warm_b_s}s reply={warm_b['content'][:60]!r}"
        )

        for label, out_dir, state_note in (
            (
                "state",
                coreB_state_dir,
                "imported from coreA/memory-export.json (continuity-memory-export v1)",
            ),
            ("clean", out_root / "coreB-clean", "clean empty store (no imported state)"),
        ):
            out_dir.mkdir(exist_ok=True)
            memory_b = MemoryStore(str(out_dir / "memory.sqlite3"))
            episodes_at_start = memory_b.count()
            journal_b = EventJournal(
                str(out_dir / "trace.jsonl"), f"{run_id}-coreB-{label}"
            )
            emit_run_start(
                journal_b, f"cont002-mechanics-coreB-{label}", CORE_B_MODEL,
                {
                    "phase": "held-out probe session (dr-0001 session 2 only)",
                    "state": state_note,
                    "cross_core": (
                        f"state exported from {CORE_A_MODEL}, replayed on "
                        f"{CORE_B_MODEL} (different core)"
                    ),
                },
            )
            journal_b.emit(
                "env.snapshot",
                {
                    "python": platform.python_version(),
                    "platform": platform.platform(),
                    "ollama_version": ollama_version,
                    "model": CORE_B_MODEL,
                    "model_digest": pin_b["digest"],
                    "seed": SEED,
                    "arm": "B",
                    "determinism_caveat": DETERMINISM_CAVEAT,
                },
            )
            summary_b = run_scenario(probe, provider_b, journal_b,
                                     Budget(**SCENARIO_BUDGET), arm="B", memory=memory_b)
            summary_b["memory_episodes_at_start"] = episodes_at_start
            memory_b.close()
            trace_ok, trace_errors = finalize_run(
                journal_b, out_dir, f"{run_id}-coreB-{label}", summary_b, provider_b
            )
            coreB_results[label] = {
                "dir": out_dir.name,
                "trace_schema_valid": trace_ok,
                "trace_validation_errors": trace_errors,
                "probes": summary_b.get("probes", []),
                "answer_excerpt": (
                    summary_b["probes"][0]["observed_normalized"][:200]
                    if summary_b.get("probes")
                    else ""
                ),
                "turns": summary_b.get("turns", 0),
                "tokens_total": summary_b.get("tokens_total", 0),
            }
            print(
                f"    coreB-{label}: trace_ok={trace_ok} "
                f"probes={summary_b.get('probes_passed', 0)}/{summary_b.get('probes_total', 0)} "
                f"answer={coreB_results[label]['answer_excerpt'][:80]!r}"
            )
    except Exception as exc:
        cross_core_errors.append(f"coreB probe phase: {type(exc).__name__}: {exc}")
        print(f"ERROR coreB phase: {exc}", file=sys.stderr)

    # --- phase 5: checks 3-5 from the recorded evidence ---
    state_trace = coreB_state_dir / "trace.jsonl"
    injected_events: list[dict] = []
    if state_trace.is_file():
        with open(state_trace, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    record = json.loads(line)
                    if record.get("type") == "memory.injected":
                        injected_events.append(record["payload"])
    export_ids: list[int] = []
    export_file = coreA_dir / "memory-export.json"
    if export_file.is_file():
        export_ids = [ep["id"] for ep in json.loads(
            export_file.read_text(encoding="utf-8")).get("episodes", [])]
    injected_ids = injected_events[0].get("episode_ids", []) if injected_events else []
    check3 = {
        "evidence": "memory.injected events in coreB-state/trace.jsonl",
        "injected_events": len(injected_events),
        "injected": bool(injected_events) and injected_events[0].get("injected", False),
        "episode_count": injected_events[0].get("episode_count", 0) if injected_events else 0,
        "episode_refs": injected_events[0].get("episode_refs", []) if injected_events else [],
        "episode_ids_from_core_a": injected_ids,
        "injected_ids_subset_of_export": bool(injected_ids) and all(
            i in export_ids for i in injected_ids
        ),
        "export_episode_ids": export_ids,
    }
    check3["pass"] = bool(
        injected_events
        and injected_events[0].get("injected")
        and injected_events[0].get("episode_count", 0) > 0
        and check3["injected_ids_subset_of_export"]
    )
    check4 = {
        "coreB_state_trace_valid": coreB_results.get("state", {}).get(
            "trace_schema_valid", False
        ),
        "coreB_clean_trace_valid": coreB_results.get("clean", {}).get(
            "trace_schema_valid", False
        ),
        "coreA_trace_valid": trace_a_ok,
        "coreA_trace_errors": trace_a_errors,
    }
    check4["pass"] = (
        check4["coreB_state_trace_valid"] and check4["coreB_clean_trace_valid"]
    )
    check5 = {"errors": cross_core_errors, "pass": not cross_core_errors}

    checklist = {
        "kind": "cont002-mechanics-checklist",
        "run_id": run_id,
        "created_utc": utc_now(),
        "milestone": "M2b",
        "claim_scope": (
            "plumbing proof only — no behavioral claims, no transfer claims, "
            "single seed, observation section is not evidence of anything"
        ),
        "checks": {
            "1_modelfile_import": check1,
            "2_export_schema_valid_roundtrip": check2,
            "3_state_renders_into_coreB_context": check3,
            "4_coreB_traces_revalidate": check4,
            "5_no_cross_core_errors": check5,
        },
        "observations_only": {
            "probe_state_run": coreB_results.get("state", {}).get("probes", []),
            "probe_clean_run": coreB_results.get("clean", {}).get("probes", []),
            "coreB_template_suspect": not digests.get(
                "core_b_warmup_reply_has_ready", False
            ),
            "note": (
                "probe outcomes under a different core are observations only; "
                "R ratio and any CONT-002 conclusion are owner-gated"
            ),
        },
        "digests_file": "model-digests.json",
    }
    write_json(out_root / "model-digests.json", digests)
    write_json(out_root / "checklist.json", checklist)

    all_pass = all(c["pass"] for c in checklist["checks"].values())
    print("\n=== M2b mechanics checklist ===")
    for name, c in checklist["checks"].items():
        print(f"  {'PASS' if c['pass'] else 'FAIL'}  {name}")
    print(f"mechanics verdict: {'ALL PASS' if all_pass else 'AT LEAST ONE FAIL'}")
    print(f"checklist: {out_root / 'checklist.json'}")
    return 0 if all_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
