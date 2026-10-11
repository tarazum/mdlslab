"""CONT-006 STAGE 2 end-to-end runner wrapper (NEW versioned code; the
frozen src/continuity/runner.py is imported, never modified).

Implements docs/PREREG-CONT006-STAGE2.md (authored BEFORE any v3o consumer
inference; this file + the analyzer are digested by the stage-2 EXEC
FREEZE). Executes the first END-TO-END (not replay) lesson-transfer design
on suite v3o: persistent memory ON in EVERY cell (R0-equivalent mechanics,
the CN-012-fixed path) with the corrected delivery (step-1 mechanism:
applicability-annotated routing, full-field rendering, no budget) at a
declared POSITION:

  position "none"          -> no block (the NONE baseline; byte-identical
                               mechanics to frozen run_scenario arm R0 —
                               enforced by the --smoke parity gate)
  position "session_start" -> the block is injected as ONE system message
                               at the start of EVERY session, in the frozen
                               R2/R3 lesson slot (after the memory block) —
                               the ORIGINAL delivery position, with
                               corrected content mechanics
  position "probe_time"    -> the block is injected as ONE system message
                               immediately before the probe user turn — the
                               step-1 corrected position

Subcommands:
  --smoke        zero-GPU offline gates: design checks, NONE parity vs the
                 frozen runner (stub provider, byte-equal message
                 sequences), injection-position asserts, CN-012 guard
                 self-test, neutral word-match
  --preflight    freeze digest verification + model pins + ollama version +
                 Q35 consumer latency measurement (2 timed calls; budget
                 re-estimate printed) — no consumer inference
  --run-phase N  execute phase N (one cell; resumable; wall-guarded)
  --gate         live-telemetry/completeness gate over a run root (MUST
                 pass before the analyzer runs)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))
sys.path.insert(0, str(LAB_ROOT / "experiments" / "cont006"))

from continuity.events import EventJournal  # noqa: E402
from continuity.fixtures import load_suite_for_seed  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import (  # noqa: E402
    ARM_A_SYSTEM_PROMPT, Budget, MEMORY_TOP_K, format_memory_block,
    run_scenario, score_probe)

import stage2_design as D  # noqa: E402

SUITE = LAB_ROOT / "fixtures" / "v3o"
FREEZE = LAB_ROOT / "experiments" / "cont006" / "stage2-freeze.json"
EXEC_FREEZE = LAB_ROOT / "experiments" / "cont006" / "stage2-exec-freeze.json"
RESULTS = LAB_ROOT / "results" / "CONT-006-STAGE2"
BASE_URL = "http://localhost:11434"

MODELS = {"G8B": "granite-code:8b", "Q35": "qwen36-35b-a3b:mdlslab"}
MODEL_PINS = {"G8B": "36c3c3b9683b", "Q35": "8a0fd5da454e"}

TEMPERATURE = 0.0
NUM_CTX = 8192
NUM_PREDICT = 256
KEEP_ALIVE = "30m"
TIMEOUT_S = 600
BUDGET_PER_CELL_SEED = dict(max_turns=130, max_total_tokens=400_000,
                            wall_clock_s=5400.0)
PHASE_WALL_S = 4 * 3600  # no new cell-seed starts after this within a phase

# Phase table (declared order; G8B block first, then Q35; baseline gates
# after phases 1 and 8). Cell = (content, position); scope = which scenario
# ids the cell runs.
FULL_SCOPE = list(D.PRIMARY_CLUSTERS) + list(D.VALIDATION_CLUSTERS) + list(D.GC_IDS)
NEWF2_PT_SCOPE = list(D.PRIMARY_CLUSTERS) + list(D.VALIDATION_CLUSTERS)
PRIMARY_SCOPE = list(D.PRIMARY_CLUSTERS)

PHASES = [
    # (model, content, position, scope)
    ("G8B", "NONE", "none", FULL_SCOPE),          # 1 — baseline gate G8B after
    ("G8B", "NEWF2", "probe_time", NEWF2_PT_SCOPE),   # 2 co-primary
    ("G8B", "NEUTRAL", "probe_time", PRIMARY_SCOPE),  # 3
    ("G8B", "NEWF2", "session_start", PRIMARY_SCOPE),  # 4
    ("G8B", "OLDG", "probe_time", PRIMARY_SCOPE),      # 5
    ("G8B", "OLDG", "session_start", PRIMARY_SCOPE),   # 6
    ("G8B", "NEUTRAL", "session_start", PRIMARY_SCOPE),  # 7
    ("Q35", "NONE", "none", FULL_SCOPE),          # 8 — baseline gate Q35 after
    ("Q35", "NEWF2", "probe_time", NEWF2_PT_SCOPE),   # 9 co-primary
    ("Q35", "NEUTRAL", "probe_time", PRIMARY_SCOPE),  # 10
    ("Q35", "NEWF2", "session_start", PRIMARY_SCOPE),  # 11
    ("Q35", "OLDG", "probe_time", PRIMARY_SCOPE),      # 12
    ("Q35", "OLDG", "session_start", PRIMARY_SCOPE),   # 13
    ("Q35", "NEUTRAL", "session_start", PRIMARY_SCOPE),  # 14
]


# ----------------------------------------------------------------------------
# the per-scenario loop (R0 mechanics + positional injections)
# ----------------------------------------------------------------------------

def run_scenario_stage2(scenario: dict, provider, journal: EventJournal,
                        budget: Budget, memory: MemoryStore,
                        block: str | None, position: str,
                        condition: str) -> dict:
    """Frozen run_scenario's R0 path (memory ON, no lesson channel),
    mechanically copied, with the ONE addition this experiment tests: the
    delivered block at the declared position. NONE parity (block=None,
    position='none') is enforced against the frozen runner by --smoke."""
    sid = scenario["id"]
    journal.emit("scenario.start", {
        "scenario": sid, "family": scenario["family"], "arm": "S2",
        "condition": condition, "position": position,
        "block_chars": len(block) if block else 0}, scenario=sid)
    probes: list[dict] = []
    stopped = False
    injected_sessions = 0

    for session in scenario["sessions"]:
        journal.emit("session.start", {"index": session["index"]},
                     scenario=sid, session=session["index"])
        context: list[dict] = [{"role": "system", "content": ARM_A_SYSTEM_PROMPT}]
        journal.emit("session.context_reset",
                     {"reason": "stage2 session-local reset; persistent memory "
                                "store retained (R0-equivalent)"},
                     scenario=sid, session=session["index"])
        if session["index"] >= 2:
            query_text = session["turns"][0]["text"]
            episodes = memory.retrieve(query_text, scenario=sid,
                                       limit=MEMORY_TOP_K)
            if episodes:
                context.append({"role": "system",
                                "content": format_memory_block(episodes)})
            journal.emit("memory.injected", {
                "query_turn_ref": f"s{session['index']}t1",
                "episode_count": len(episodes),
                "episode_ids": [ep["id"] for ep in episodes],
                "top_k": MEMORY_TOP_K, "injected": bool(episodes),
                "renderer": "flat"}, scenario=sid, session=session["index"])
        if position == "session_start" and block:
            # the frozen R2/R3 lesson slot: after the memory block
            context.append({"role": "system", "content": block})
            injected_sessions += 1
            journal.emit("lessons.injected", {
                "position": position, "session": session["index"],
                "lesson_ids": D.NEWF2_APPL.get(sid, []) if condition == "NEWF2"
                else (D.OLDG_APPL.get(sid, []) if condition == "OLDG" else []),
                "content": condition, "chars": len(block),
                "injected": True}, scenario=sid, session=session["index"])
        probe_turn_idxs = [k for k, t in enumerate(session["turns"], start=1)
                           if t.get("probe") is not None]
        for turn_no, turn in enumerate(session["turns"], start=1):
            turn_ref = f"s{session['index']}t{turn_no}"
            journal.emit("env.turn",
                         {"turn_ref": turn_ref, "text": turn["text"]},
                         scenario=sid, session=session["index"])
            if (position == "probe_time" and block
                    and turn_no in probe_turn_idxs):
                context.append({"role": "system", "content": block})
                journal.emit("lessons.injected", {
                    "position": position, "turn_ref": turn_ref,
                    "lesson_ids": D.NEWF2_APPL.get(sid, []) if condition == "NEWF2"
                    else (D.OLDG_APPL.get(sid, []) if condition == "OLDG" else []),
                    "content": condition, "chars": len(block),
                    "injected": True}, scenario=sid, session=session["index"])
            context.append({"role": "user", "content": turn["text"]})
            reply = provider.chat(context)
            budget.turns += 1
            budget.tokens += reply["usage"]["total_tokens"]
            context.append({"role": "assistant", "content": reply["content"]})
            journal.emit("agent.response", {
                "turn_ref": turn_ref, "content": reply["content"],
                "usage": reply["usage"],
                "total_duration_ms": reply["total_duration_ms"],
                "options": dict(provider.options), "model": provider.model},
                scenario=sid, session=session["index"])
            for role, content in (("environment", turn["text"]),
                                  ("assistant", reply["content"])):
                episode_id = memory.append_episode(
                    run_id=journal.run_id, scenario=sid,
                    session=session["index"], turn_ref=turn_ref,
                    role=role, content=content)
                journal.emit("memory.append",
                             {"episode_id": episode_id, "turn_ref": turn_ref,
                              "role": role},
                             scenario=sid, session=session["index"])
            probe = turn.get("probe")
            if probe is not None:
                result = score_probe(probe, reply["content"])
                result["turn_ref"] = turn_ref
                probes.append(result)
                journal.emit("probe.result", dict(result), scenario=sid,
                             session=session["index"])
            violation = budget.check()
            if violation is not None:
                journal.emit("budget.stop", {"violation": violation},
                             scenario=sid)
                stopped = True
                break
        if stopped:
            break

    # CN-012 fail-closed guard (V2A convention): a memory run with no
    # appends or no non-empty injection at session >= 2 is INVALID, not
    # completed — completeness judges downstream; silent memoryless runs
    # are void.
    appends = memory.count(scenario=sid)
    injected_ok = True
    if len(scenario["sessions"]) >= 2:
        with open(journal.path, encoding="utf-8") as fh:
            events = [json.loads(line) for line in fh]
        inj = [e for e in events if e["type"] == "memory.injected"
               and e.get("scenario") == sid]
        injected_ok = any(e["payload"]["injected"] for e in inj)
    valid = appends > 0 and injected_ok and not stopped
    summary = {
        "scenario": sid, "family": scenario["family"], "condition": condition,
        "position": position, "arm": "S2",
        "sessions_planned": len(scenario["sessions"]),
        "memory_episodes": appends, "memory_guard_ok": valid,
        "turns": budget.turns, "tokens_total": budget.tokens,
        "probes": probes,
        "probes_passed": sum(1 for p in probes if p["passed"]),
        "probes_total": len(probes),
        "stopped": stopped, "budget_violation": budget.violation,
        "block_chars": len(block) if block else 0,
        "injected_sessions": injected_sessions,
        "valid": valid,
        "duration_s": 0.0,
    }
    journal.emit("scenario.end", dict(summary), scenario=sid)
    return summary


# ----------------------------------------------------------------------------
# cell execution
# ----------------------------------------------------------------------------

def run_cell_seed(model: str, content: str, position: str, scope: list[str],
                  seed: int, out_dir: Path, calls_fh, wall_deadline: float) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    if (out_dir / "summary.json").exists():
        return {"skipped": True, "path": str(out_dir)}  # resumability
    if time.monotonic() > wall_deadline:
        return {"wall_skipped": True, "path": str(out_dir)}
    provider = _RecordingProvider(
        base_url=BASE_URL, model=MODELS[model], temperature=TEMPERATURE,
        seed=seed, num_ctx=NUM_CTX, num_predict=NUM_PREDICT,
        keep_alive=KEEP_ALIVE, timeout_s=TIMEOUT_S, calls_fh=calls_fh,
        cell=f"{model}|{content}|{position}", seed_tag=seed)
    memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    assert memory.count() == 0, "cell-seed must start from a verified-empty store"
    journal = EventJournal(str(out_dir / "trace.jsonl"),
                           f"s2-{model}-{content}-{position}-seed{seed}")
    _, scenarios = load_suite_for_seed(str(SUITE), seed)
    by_id = {s["id"]: s for s in scenarios}
    budget = Budget(**BUDGET_PER_CELL_SEED)
    t0 = time.monotonic()
    probes: list[dict] = []
    summaries = []
    try:
        for sid in sorted(scope):
            scenario = by_id[sid]
            block = D.block_for(content, sid)
            result = run_scenario_stage2(
                scenario, provider, journal, budget, memory, block,
                position, condition=content)
            summaries.append(result)
            probes.extend({**p, "scenario": sid, "family": scenario["family"]}
                          for p in result["probes"])
    finally:
        summary = {
            "kind": "cont006-stage2-cell-seed",
            "model": model, "content": content, "position": position,
            "seed": seed, "scope": scope,
            "probes": probes,
            "probes_passed": sum(1 for p in probes if p["passed"]),
            "probes_total": len(probes),
            "scenarios": [{k: v for k, v in s.items() if k != "probes"}
                          for s in summaries],
            "invalid_any": any(not s["valid"] for s in summaries),
            "stopped_any": any(s["stopped"] for s in summaries),
            "duration_s": round(time.monotonic() - t0, 1),
            "options": dict(provider.options), "model_name": MODELS[model],
        }
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=1, ensure_ascii=True) + "\n",
            encoding="utf-8")
    return summary


class _RecordingProvider(OllamaProvider):
    """Thin proxy recording every call (context hash + usage + duration)
    into the cell calls.jsonl — the live-telemetry feed for the gate."""

    def __init__(self, *a, cell: str, seed_tag: int, calls_fh, **kw):
        super().__init__(*a, **kw)
        self._cell = cell
        self._seed = seed_tag
        self._fh = calls_fh

    def chat(self, messages: list[dict]) -> dict:
        ctx_sha = hashlib.sha256(json.dumps(
            messages, sort_keys=True, ensure_ascii=True).encode()).hexdigest()
        reply = super().chat(messages)
        self._fh.write(json.dumps({
            "cell": self._cell, "seed": self._seed,
            "turn": len(messages),
            "context_sha256": ctx_sha,
            "prompt_tokens": reply["usage"]["prompt_tokens"],
            "eval_tokens": reply["usage"]["eval_tokens"],
            "total_duration_ms": reply["total_duration_ms"],
            "options": dict(self.options), "model": self.model,
        }, ensure_ascii=True) + "\n")
        self._fh.flush()
        return reply


def run_phase(phase_no: int, run_root: Path) -> dict:
    model, content, position, scope = PHASES[phase_no - 1]
    cell_dir = run_root / model / f"{content}-{position}"
    cell_dir.mkdir(parents=True, exist_ok=True)
    calls_path = cell_dir / "calls.jsonl"
    wall_deadline = time.monotonic() + PHASE_WALL_S
    # model warm + pin (CN-001 order: warm, then pin via /api/ps)
    warm = OllamaProvider(base_url=BASE_URL, model=MODELS[model],
                          temperature=0.0, seed=0, num_ctx=NUM_CTX,
                          keep_alive=KEEP_ALIVE, timeout_s=TIMEOUT_S)
    warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
    info = OllamaProvider(base_url=BASE_URL, model=MODELS[model]).model_info()
    if not info.get("digest", "").startswith(MODEL_PINS[model]):
        raise SystemExit(f"FAIL-CLOSED: {model} digest {info.get('digest')!r}")
    done = 0
    with calls_path.open("a", encoding="utf-8") as calls_fh:
        for seed in D.SEEDS:
            res = run_cell_seed(model, content, position, scope, seed,
                                cell_dir / f"seed-{seed}", calls_fh,
                                wall_deadline)
            if not res.get("skipped") and not res.get("wall_skipped"):
                done += 1
            print(f"  seed {seed}: "
                  + ("SKIP(done)" if res.get("skipped")
                     else ("WALL-SKIP" if res.get("wall_skipped")
                           else f"pass {res['probes_passed']}/{res['probes_total']}"
                                f" invalid={res['invalid_any']} "
                                f"{res['duration_s']}s")), flush=True)
    return {"phase": phase_no, "model": model, "content": content,
            "position": position, "executed": done}


def baseline_gate(run_root: Path, model: str) -> dict:
    """The pre-registered in-run difficulty gate: pooled PRIMARY pass rate
    of the NONE cell must lie inside the declared band, else the stage
    STOPS OUT OF BAND (new suite, never a v3o edit — v3m precedent A.3)."""
    band = (0.15, 0.85) if model == "G8B" else (0.35, 0.85)
    total = passed = 0
    for seed in D.SEEDS:
        s = json.loads((run_root / model / "NONE-none" / f"seed-{seed}"
                        / "summary.json").read_text(encoding="utf-8"))
        for p in s["probes"]:
            if p["scenario"] in D.PRIMARY_CLUSTERS:
                total += 1
                passed += 1 if p["passed"] else 0
    rate = passed / total if total else 0.0
    ok = band[0] <= rate <= band[1] and total == len(D.PRIMARY_CLUSTERS) * len(D.SEEDS)
    return {"model": model, "pooled_primary": f"{passed}/{total}",
            "rate": round(rate, 4), "band": band, "ok": ok}


# ----------------------------------------------------------------------------
# --smoke (zero GPU), --preflight, --gate
# ----------------------------------------------------------------------------

class _StubProvider:
    """Deterministic stub for the offline smoke: records every context it
    receives; returns a fixed short reply with synthetic usage."""

    def __init__(self) -> None:
        self.model = "stub"
        self.options = {"temperature": 0.0, "seed": 1, "num_ctx": 8192,
                        "num_predict": 256}
        self.contexts: list[list[dict]] = []

    def chat(self, messages: list[dict]) -> dict:
        import copy
        self.contexts.append(copy.deepcopy(messages))
        return {"content": "moulding",
                "usage": {"prompt_tokens": 10, "eval_tokens": 2,
                          "total_tokens": 12},
                "total_duration_ms": 1.0}


def _close_store(store) -> None:
    conn = getattr(store, "_conn", None)
    if conn is not None:
        conn.close()


class _TempDir:
    """tempfile.TemporaryDirectory that tolerates Windows' open-sqlite
    handles: stores are closed first, cleanup is best-effort."""

    def __init__(self) -> None:
        import tempfile
        self.path = Path(tempfile.mkdtemp())

    def __enter__(self) -> Path:
        return self.path

    def __exit__(self, *exc) -> None:
        import gc
        import shutil
        gc.collect()  # drop store references so sqlite handles close
        shutil.rmtree(self.path, ignore_errors=True)


def _smoke() -> int:
    problems: list[str] = []
    # (1) design checks (annotations/word-match/vocab)
    if D.check_annotations():
        problems.append(f"annotations: {D.check_annotations()}")
    bad = {c: v for c, v in D.check_neutral_word_match().items() if not v["ok"]}
    if bad:
        problems.append(f"word match: {bad}")
    fatal, _oldg = D.check_neutral_vocab()
    if fatal:
        problems.append(f"vocab: {fatal}")

    _, scenarios = load_suite_for_seed(str(SUITE), 9001)
    scenario = next(s for s in scenarios if s["id"] == "cr-9001")

    # (2) NONE parity: my wrapper vs the frozen runner (arm R0) — the
    # message sequences the provider receives must be BYTE-EQUAL.
    from continuity.memory import MemoryStore as MS
    import tempfile
    with _TempDir() as td:
        m1 = MS(str(td / "m1.sqlite3")); m2 = MS(str(td / "m2.sqlite3"))
        j1 = EventJournal(str(td / "t1.jsonl"), "smoke-s2")
        j2 = EventJournal(str(td / "t2.jsonl"), "smoke-frozen")
        p1, p2 = _StubProvider(), _StubProvider()
        run_scenario_stage2(scenario, p1, j1, Budget(), m1, None, "none",
                            condition="NONE")
        run_scenario(scenario, p2, j2, Budget(), arm="R0", memory=m2)
        if [json.dumps(c, sort_keys=True) for c in p1.contexts] != \
           [json.dumps(c, sort_keys=True) for c in p2.contexts]:
            problems.append("NONE parity FAIL: message sequences differ "
                            "from the frozen R0 runner")

    # (3) probe_time injection: block present as the message immediately
    # before the probe user turn, exactly once, nowhere else.
    block = D.block_for("NEWF2", "cr-9001")
    with _TempDir() as td:
        m = MS(str(td / "m.sqlite3"))
        j = EventJournal(str(td / "t.jsonl"), "smoke-pt")
        p = _StubProvider()
        run_scenario_stage2(scenario, p, j, Budget(), m, block,
                            "probe_time", condition="NEWF2")
        hits = [i for i, ctx in enumerate(p.contexts) if any(
            msg.get("role") == "system" and msg.get("content") == block
            for msg in ctx)]
        if len(hits) != 1:
            problems.append(f"probe_time injection count {len(hits)} != 1")
        else:
            ctx = p.contexts[hits[0]]
            idx = next(i for i, msg in enumerate(ctx)
                       if msg.get("content") == block)
            probe_turns = [i for i, msg in enumerate(ctx)
                           if msg.get("role") == "user"
                           and "reply with the label only" in msg.get("content", "")]
            if not probe_turns or idx != probe_turns[-1] - 1:
                problems.append("probe_time block not immediately before "
                                "the probe user turn")

    # (4) session_start injection: in EVERY session's preamble, after the
    # memory block where one exists.
    with _TempDir() as td:
        m = MS(str(td / "m.sqlite3"))
        j = EventJournal(str(td / "t.jsonl"), "smoke-ss")
        p = _StubProvider()
        run_scenario_stage2(scenario, p, j, Budget(), m, block,
                            "session_start", condition="NEWF2")
        last_ctx_of_session: dict[int, list[dict]] = {}
        # contexts grow within a session; the LAST context of each session
        # still carries the preamble block
        n_sessions = len(scenario["sessions"])
        # find context boundaries by counting turns: simpler check — every
        # recorded context of every session contains the block exactly once
        # and contexts reset per session (first context has 2 messages:
        # base + block)
        first_ctx = p.contexts[0]
        if not (len(first_ctx) == 3 and first_ctx[0]["role"] == "system"
                and first_ctx[1].get("content") == block
                and first_ctx[2]["role"] == "user"):
            problems.append("session_start block not in session-1 preamble")
        if not all(sum(1 for msg in ctx if msg.get("content") == block) == 1
                   for ctx in p.contexts):
            problems.append("session_start block count != 1 in some context")
        # the LAST session's contexts must carry the block after the memory
        # block (memory injection exists at session >= 2)
        deep = p.contexts[-1]
        sys_msgs = [i for i, msg in enumerate(deep) if msg.get("role") == "system"]
        block_pos = next((i for i in sys_msgs if deep[i].get("content") == block), None)
        mem_pos = next((i for i in sys_msgs
                        if deep[i].get("content", "").startswith(
                            "Your persistent memory:")), None)
        if block_pos is None or (mem_pos is not None and block_pos < mem_pos):
            problems.append("session_start block not after the memory block")

    # (5) CN-012 guard self-test: a memoryless run must be flagged invalid
    class _Memoryless(MS):
        def append_episode(self, *a, **kw):  # simulate the CN-012 defect
            return 0
    with _TempDir() as td:
        m = _Memoryless(str(td / "m.sqlite3"))
        j = EventJournal(str(td / "t.jsonl"), "smoke-guard")
        res = run_scenario_stage2(scenario, _StubProvider(), j, Budget(), m,
                                  None, "none", condition="NONE")
        if res["valid"]:
            problems.append("CN-012 guard did not flag a memoryless run")

    print("SMOKE", "PASS" if not problems else "FAIL")
    for p_ in problems:
        print("  -", p_)
    return 0 if not problems else 2


def _preflight() -> int:
    freeze = json.loads(FREEZE.read_text(encoding="utf-8"))
    bad = []
    def _norm_digest(rel: str) -> str:
        raw = (LAB_ROOT / rel).read_bytes()
        return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()

    for rel, sha in freeze["digests"].items():
        if _norm_digest(rel) != sha:
            bad.append(rel)
    if EXEC_FREEZE.exists():
        ef = json.loads(EXEC_FREEZE.read_text(encoding="utf-8"))
        for rel, sha in ef["digests"].items():
            if _norm_digest(rel) != sha:
                bad.append(rel)
    print(f"freeze digests: {len(freeze['digests'])} + "
          f"{len(json.loads(EXEC_FREEZE.read_text(encoding='utf-8'))['digests']) if EXEC_FREEZE.exists() else 0} checked; "
          f"mismatches: {bad or 'none'}")
    version = OllamaProvider(base_url=BASE_URL).version()
    print("ollama:", version)
    for model, pin in MODEL_PINS.items():
        probe = OllamaProvider(base_url=BASE_URL, model=MODELS[model])
        t0 = time.monotonic()
        warm = OllamaProvider(base_url=BASE_URL, model=MODELS[model],
                              temperature=0.0, seed=0, num_ctx=NUM_CTX,
                              keep_alive=KEEP_ALIVE, timeout_s=TIMEOUT_S)
        warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
        info = probe.model_info()
        ok = info.get("digest", "").startswith(pin)
        print(f"{model}: digest {info.get('digest')} pin {'OK' if ok else 'FAIL'}; "
              f"warm {time.monotonic()-t0:.1f}s")
        if not ok:
            bad.append(f"{model} pin")
    # Q35 consumer latency: two timed representative calls (session-shaped)
    if not bad:
        prompt = ("You cover the slate quarry tally hut. For the log: the "
                  "force pump counts 43 stroke turns per hour. Acknowledge "
                  "in one short line.")
        for i in range(2):
            prov = OllamaProvider(base_url=BASE_URL, model=MODELS["Q35"],
                                  temperature=0.0, seed=9001, num_ctx=NUM_CTX,
                                  num_predict=NUM_PREDICT,
                                  keep_alive=KEEP_ALIVE, timeout_s=TIMEOUT_S)
            t0 = time.monotonic()
            r = prov.chat([{"role": "system", "content": ARM_A_SYSTEM_PROMPT},
                           {"role": "user", "content": prompt}])
            print(f"Q35 latency probe {i+1}: {time.monotonic()-t0:.1f}s "
                  f"(prompt {r['usage']['prompt_tokens']} tok, "
                  f"eval {r['usage']['eval_tokens']} tok)")
    print("PREFLIGHT", "PASS" if not bad else "FAIL")
    return 0 if not bad else 2


def _gate(run_root: Path) -> int:
    problems = []
    expected_calls = 0
    for phase_no, (model, content, position, scope) in enumerate(PHASES, 1):
        cell_dir = run_root / model / f"{content}-{position}"
        if not cell_dir.exists():
            problems.append(f"phase {phase_no}: cell dir missing")
            continue
        for seed in D.SEEDS:
            sd = cell_dir / f"seed-{seed}"
            if not (sd / "summary.json").exists():
                problems.append(f"phase {phase_no}: seed {seed} missing")
                continue
            s = json.loads((sd / "summary.json").read_text(encoding="utf-8"))
            if s.get("invalid_any"):
                problems.append(f"{model}/{content}-{position}/seed-{seed}: "
                                "INVALID (memory guard)")
            if s.get("stopped_any"):
                problems.append(f"{model}/{content}-{position}/seed-{seed}: "
                                "budget stop")
            n_scen = len(s["scope"])
            if s["probes_total"] != n_scen:
                problems.append(f"{model}/{content}-{position}/seed-{seed}: "
                                f"probes {s['probes_total']} != {n_scen}")
    # headroom check over all calls
    for calls in run_root.glob("*/*/calls.jsonl"):
        for line in calls.read_text(encoding="utf-8").splitlines():
            e = json.loads(line)
            expected_calls += 1
            if e["prompt_tokens"] > NUM_CTX - 512:
                problems.append(f"headroom: {calls.parent.name} "
                                f"prompt {e['prompt_tokens']}")
    print(f"GATE over {run_root.name}: calls {expected_calls}")
    print("GATE", "PASS" if not problems else "FAIL")
    for p_ in problems[:20]:
        print("  -", p_)
    if not problems:
        (run_root / "gate-PASS.json").write_text(json.dumps({
            "kind": "cont006-stage2-gate", "run_root": run_root.name,
            "calls": expected_calls,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%Z",
                                         time.gmtime())}, indent=1) + "\n",
            encoding="utf-8")
        print("wrote", run_root / "gate-PASS.json")
    return 0 if not problems else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--preflight", action="store_true")
    ap.add_argument("--run-phase", type=int, default=None)
    ap.add_argument("--run-root", default=None)
    ap.add_argument("--gate", action="store_true")
    ap.add_argument("--baseline-gate", default=None,
                    help="model name: check the NONE-cell difficulty band")
    args = ap.parse_args()
    if args.smoke:
        return _smoke()
    if args.preflight:
        return _preflight()
    if args.baseline_gate:
        root = Path(args.run_root) if args.run_root else _latest_root()
        print(json.dumps(baseline_gate(root, args.baseline_gate), indent=1))
        return 0
    if args.gate:
        root = Path(args.run_root) if args.run_root else _latest_root()
        return _gate(root)
    if args.run_phase:
        root = Path(args.run_root) if args.run_root else _latest_root(create=True)
        res = run_phase(args.run_phase, root)
        print(json.dumps(res, indent=1))
        if res["model"] == "NONE":
            pass
        # baseline gates after phases 1 and 8
        if args.run_phase in (1, 8):
            model = PHASES[args.run_phase - 1][0]
            print(json.dumps(baseline_gate(root, model), indent=1))
        return 0
    ap.print_help()
    return 1


def _latest_root(create: bool = False) -> Path:
    if RESULTS.exists():
        roots = sorted(p for p in RESULTS.iterdir() if p.is_dir())
        if roots:
            return roots[-1]
    if not create:
        raise SystemExit("no run root; pass --run-root")
    root = RESULTS / f"cont006-s2-{time.strftime('%Y%m%d-%H%M%S')}"
    root.mkdir(parents=True, exist_ok=True)
    return root


if __name__ == "__main__":
    raise SystemExit(main())
