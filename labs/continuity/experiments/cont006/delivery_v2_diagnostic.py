"""CONT-006 DELIVERY-DIAG (step 1): corrected-lesson-delivery probe-level
diagnostic on the SAME 8B, over the SAME recorded histories.

Implements docs/PREREG-CONT006-DELIVERY-DIAG.md (pre-registered BEFORE any
new inference; this file is digested by delivery-v2-freeze.json). The
executed V2A chain is READ-ONLY here: src/continuity modules are imported,
never modified; committed run roots are only read.

What it does, per the prereg:
  --gates        zero-GPU reconstruction gates G-A..G-E + completeness
  --emit-freeze  gates, then write delivery-v2-freeze.json (digests of the
                 prereg, this file, the session brief, the imported frozen
                 sources, both store pairs, and every trace/memory/summary
                 artifact the reconstruction reads)
  --preflight    re-verify the freeze digests fail-closed + pin the model
                 (no inference)
  --run          preflight + the 192 inference calls (84 b-corrected,
                 84 c-memory-only, 24 a-replay noise-floor subset) into
                 results/CONT-006-DELIVERY-DIAG/cont006-dd-<ts>/
  --analyze      pre-analysis completeness check + prediction evaluation
                 (P1/P1a/P2/P3/P4) + exploratory tables -> delivery-diag-
                 results.json
  --self-test    offline checks of the reconstruction/render helpers

Corrected delivery (variant b) is a SEPARATE mechanism (this module): the
lesson message is routed AT the probe turn, restricted to the
pre-registered applicability sets (prereg §5), rendered in full (title +
when + Rule + Behavior), no budget, one system message right before the
probe user turn; absent when no lesson applies.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import load_suite_for_seed  # noqa: E402
from continuity.lessons import LessonChannel, load_store  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import (  # noqa: E402
    ARM_A_SYSTEM_PROMPT, format_memory_block, score_probe)

P_ROOT = LAB_ROOT / "results" / "CONT-006-PILOT" / "cont006-p-20261010-132230"
C_ROOT = (LAB_ROOT / "results" / "CONT-006-CONFIRMATORY" /
          "cont006-c-20261010-144817")
V_ROOT = LAB_ROOT / "results" / "CONT-006-VAL" / "cont006-v-20261010-130154"
VAL_DIR = V_ROOT  # stores live here (both pin pairs)

SUITE_DIR = LAB_ROOT / "fixtures" / "v3n"
PREREG = LAB_ROOT / "docs" / "PREREG-CONT006-DELIVERY-DIAG.md"
BRIEF = LAB_ROOT / "docs" / "SESSION-BRIEF-CONT006-DELIVERY.md"
FREEZE = LAB_ROOT / "experiments" / "cont006" / "delivery-v2-freeze.json"
RESULTS = LAB_ROOT / "results" / "CONT-006-DELIVERY-DIAG"

WORKING_MODEL = "granite-code:8b"
WORKING_DIGEST_PREFIX = "36c3c3b9683b"
OLLAMA_VERSION_PREFIX = "0.34"
TEMPERATURE = 0.0
NUM_CTX = 4096
NUM_PREDICT = 256
KEEP_ALIVE = "30m"
TIMEOUT_S = 300
BOOT_DRAWS = 10_000
BOOT_SEED = 20261010

HARM_CLUSTERS = ("cr-8003", "cr-8004", "dx-8401", "dx-8402")
DIAG_CLUSTERS = ("cr-8003", "cr-8004", "dx-8401", "dx-8402",
                 "rt-8203", "rt-8204")
SEEDS = (8001, 8002, 8003, 8004, 8005, 8006, 8007)
ARMS = ("R2", "R3")
REPLAY_SEEDS = (8001, 8005)  # prereg §4: a-replay noise-floor subset

# store pin per (arm, root-kind) — prereg §2 (lesson CONTENT identical
# across pins; only the status field differs). P-root R2 cells are the
# reused CAL2 cells (kind "w2" -> evidence-validated store); P-root R3 and
# all C cells ran with the ACTIVE stores; V ran with kind "w2".
STORE_PINS = {
    ("R2", "P"): ("r2-store-evidence-validated.json", "f82efc3fcffe17e88ff714656326b4cbf4a2b1cb0e574b8b0e9be226346320b2"),
    ("R3", "P"): ("active-store-r3.json", "b2500b6b542a906d2a7ee3d1cfcd21cfd2b950abc24079dd1b3c12a5065c12cb"),
    ("R2", "C"): ("active-store-r2.json", "f99be96f2bad3e030c76cefa40f5d8f6cbc6cde64cd39471da392ffb25059302"),
    ("R3", "C"): ("active-store-r3.json", "b2500b6b542a906d2a7ee3d1cfcd21cfd2b950abc24079dd1b3c12a5065c12cb"),
    ("R2", "V"): ("r2-store-evidence-validated.json", "f82efc3fcffe17e88ff714656326b4cbf4a2b1cb0e574b8b0e9be226346320b2"),
    ("R3", "V"): ("r3-store-evidence-validated.json", "48064a0235500d8d66218b2ff3e6f0889cf06274489500f5097a58200626fafa"),
}

# prereg §5 applicability sets (cluster-level, seed-independent)
APPLICABILITY = {
    ("R2", "cr-8003"): ["LL-W-005"], ("R2", "cr-8004"): ["LL-W-005"],
    ("R2", "dx-8401"): ["LL-W-006"], ("R2", "dx-8402"): ["LL-W-006"],
    ("R2", "rt-8203"): ["LL-W-005"], ("R2", "rt-8204"): ["LL-W-005"],
    ("R3", "cr-8003"): ["LL-G-003", "LL-G-005", "LL-G-007"],
    ("R3", "cr-8004"): ["LL-G-003", "LL-G-005", "LL-G-007"],
    ("R3", "dx-8401"): ["LL-G-006", "LL-G-007"],
    ("R3", "dx-8402"): ["LL-G-006", "LL-G-007"],
    ("R3", "rt-8203"): ["LL-G-003", "LL-G-007"],
    ("R3", "rt-8204"): ["LL-G-003", "LL-G-007"],
}

DELIVERY_V2_HEADER = "Lessons learned in earlier work (apply where relevant):"
DETERMINISM_CAVEAT = ("greedy+seed does not guarantee identical outputs "
                      "(PB-071, CN-003); the a-replay subset measures the "
                      "resulting noise floor directly")

FROZEN_SOURCES = [
    "src/continuity/runner.py", "src/continuity/provider.py",
    "src/continuity/memory.py", "src/continuity/lessons.py",
    "src/continuity/events.py", "src/continuity/fixtures.py",
]


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# ----------------------------------------------------------------------------
# cell enumeration + trace parsing
# ----------------------------------------------------------------------------

def root_for(cluster: str, seed: int) -> Path:
    if cluster == "rt-8204":
        return V_ROOT
    return P_ROOT if seed in (8001, 8002) else C_ROOT


def cells() -> list[dict]:
    out = []
    for arm in ARMS:
        for cluster in DIAG_CLUSTERS:
            for seed in SEEDS:
                root = root_for(cluster, seed)
                out.append({"arm": arm, "seed": seed, "cluster": cluster,
                            "root": root,
                            "root_kind": root.name.split("-")[1].upper()})
    return out


def cell_dir(cell: dict) -> Path:
    return cell["root"] / cell["arm"] / f"seed-{cell['seed']}"


def parse_trace(cell: dict) -> dict:
    """All events of the cell's scenario + the probe-session facts."""
    events = []
    for line in (cell_dir(cell) / "trace.jsonl").read_text(
            encoding="utf-8").splitlines():
        e = json.loads(line)
        if e.get("scenario") == cell["cluster"]:
            events.append(e)
    probe_events = [e for e in events if e["type"] == "probe.result"]
    if len(probe_events) != 1:
        raise ValueError(f"{cell}: expected 1 probe, got {len(probe_events)}")
    probe = probe_events[0]
    session = probe["session"]
    sess_events = [e for e in events if e.get("session") == session]
    mem = [e for e in sess_events if e["type"] == "memory.injected"]
    les = [e for e in sess_events if e["type"] == "lessons.injected"]
    first_turn = [e for e in sess_events if e["type"] == "env.turn"
                  and e["payload"]["turn_ref"] == f"s{session}t1"]
    opts = [e["payload"]["options"] for e in sess_events
            if e["type"] == "agent.response"]
    reply = [e for e in sess_events if e["type"] == "agent.response"
             and e["payload"]["turn_ref"] == probe["payload"]["turn_ref"]]
    return {
        "events": events,
        "probe_turn_ref": probe["payload"]["turn_ref"],
        "probe_session": session,
        "recorded_probe": probe["payload"],
        "recorded_reply": reply[0]["payload"]["content"],
        "memory_injected": mem[0]["payload"] if mem else None,
        "lessons_injected": les[0]["payload"] if les else None,
        "first_turn_text": first_turn[0]["payload"]["text"],
        "options": opts[0] if opts else None,
    }


def sqlite_episodes(cell: dict) -> dict[int, dict]:
    conn = sqlite3.connect(f"file:{cell_dir(cell) / 'memory.sqlite3'}?mode=ro",
                           uri=True)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT id, turn_ref, role, content FROM episodes WHERE scenario = ?",
        (cell["cluster"],)).fetchall()
    conn.close()
    return {r["id"]: dict(r) for r in rows}


# ----------------------------------------------------------------------------
# context reconstruction (prereg §3)
# ----------------------------------------------------------------------------

def reconstruct(cell: dict, stores: dict[tuple[str, str], LessonChannel]) -> dict:
    """Byte-exact probe context pieces for one cell (variant a/b/c inputs)."""
    t = parse_trace(cell)
    episodes = sqlite_episodes(cell)
    # G-B: sqlite content == trace text for every referenced episode
    env_text = {e["payload"]["turn_ref"]: e["payload"]["text"]
                for e in t["events"] if e["type"] == "env.turn"}
    agent_text = {e["payload"]["turn_ref"]: e["payload"]["content"]
                  for e in t["events"] if e["type"] == "agent.response"}
    episode_role = {}
    for e in t["events"]:
        if e["type"] == "memory.append":
            p = e["payload"]
            episode_role[p["episode_id"]] = (p["turn_ref"], p["role"])
    mi = t["memory_injected"]
    if mi is None or not mi["injected"]:
        raise ValueError(f"{cell}: probe session has no memory injection")
    block_episodes = []
    for eid in mi["episode_ids"]:
        ep = episodes[eid]
        ref, role = episode_role[eid]
        if (ep["turn_ref"], ep["role"]) != (ref, role):
            raise ValueError(f"{cell}: episode {eid} ref/role mismatch")
        trace_text = (env_text if role == "environment" else agent_text)[ref]
        if ep["content"] != trace_text:
            raise ValueError(f"{cell}: episode {eid} content != trace text")
        block_episodes.append({"turn_ref": ep["turn_ref"], "role": ep["role"],
                               "content": ep["content"]})
    memory_block = format_memory_block(block_episodes)
    # G-A: as-executed lesson block reproduces recorded ids + chars
    li = t["lessons_injected"]
    store = stores[(cell["arm"], cell["root_kind"])]
    selected = store.retrieve(t["first_turn_text"])
    block, rendered = store.render(selected)
    if [l["lessonId"] for l in rendered] != li["lesson_ids"]:
        raise ValueError(f"{cell}: rendered ids != recorded {li['lesson_ids']}")
    if len(block) != li["chars"]:
        raise ValueError(f"{cell}: block chars {len(block)} != {li['chars']}")
    # G-E: store digest pin
    if store.digest != li["store_sha256"]:
        raise ValueError(f"{cell}: store digest mismatch")
    # session turns before the probe
    session = t["probe_session"]
    history = []
    turn_refs = sorted(env_text, key=lambda r: int(r.split("t")[1]))
    for ref in turn_refs:
        if not ref.startswith(f"s{session}"):
            continue
        if ref == t["probe_turn_ref"]:
            break
        history.append({"role": "user", "content": env_text[ref]})
        history.append({"role": "assistant", "content": agent_text[ref]})
    probe_turn = {"role": "user", "content": env_text[t["probe_turn_ref"]]}
    # G-C: rendered fixture probe == recorded expected, at s3t2
    _, scenarios = load_suite_for_seed(str(SUITE_DIR), cell["seed"])
    fx = next(s for s in scenarios if s["id"] == cell["cluster"])
    fx_probe = None
    for sess in fx["sessions"]:
        for k, turn in enumerate(sess["turns"], start=1):
            if turn.get("probe") is not None:
                fx_probe = turn["probe"]
                if f"s{sess['index']}t{k}" != t["probe_turn_ref"]:
                    raise ValueError(f"{cell}: fixture probe turn mismatch")
    if fx_probe is None or fx_probe.get("expected") != t["recorded_probe"]["expected"]:
        raise ValueError(f"{cell}: fixture probe expected mismatch")
    # G-D: recorded options == pins
    want = {"temperature": TEMPERATURE, "seed": cell["seed"],
            "num_ctx": NUM_CTX, "num_predict": NUM_PREDICT}
    if t["options"] != want:
        raise ValueError(f"{cell}: options {t['options']} != {want}")
    system = {"role": "system", "content": ARM_A_SYSTEM_PROMPT}
    memory_msg = {"role": "system", "content": memory_block}
    ctx_a = [system, memory_msg,
             {"role": "system", "content": block}, *history, probe_turn]
    ctx_c = [system, memory_msg, *history, probe_turn]
    delivery = delivery_v2_block(cell["arm"], cell["cluster"], store.store)
    ctx_b = ([system, memory_msg, *history]
             + ([{"role": "system", "content": delivery}] if delivery else [])
             + [probe_turn])
    return {"t": t, "fx_probe": fx_probe, "ctx_a": ctx_a, "ctx_b": ctx_b,
            "ctx_c": ctx_c, "delivery_block": delivery}


def delivery_v2_block(arm: str, cluster: str, store: dict) -> str | None:
    """Corrected delivery render (prereg §4/§5): full fields, store order,
    no budget; None when no lesson applies."""
    ids = APPLICABILITY[(arm, cluster)]
    if not ids:
        return None
    by_id = {l["lessonId"]: l for l in store["lessons"]}
    lines = [DELIVERY_V2_HEADER]
    for i, lid in enumerate(ids, start=1):
        les = by_id[lid]
        when = "; ".join(str(a) for a in les.get("applicability", [])) or "relevant"
        lines.append(f"{i}. {les['title']}. When {when}: "
                     f"Rule: {les['lesson']} Behavior: {les['recommendedBehavior']}")
    return "\n".join(lines)


def load_stores() -> dict[tuple[str, str], LessonChannel]:
    out = {}
    for arm in ARMS:
        for kind in ("P", "C", "V"):
            fname, digest = STORE_PINS[(arm, kind)]
            store = load_store(VAL_DIR / fname)
            if store["store_sha256"] != digest:
                raise ValueError(f"store pin mismatch: {fname}")
            out[(arm, kind)] = LessonChannel(store)
    return out


# ----------------------------------------------------------------------------
# gates / freeze / preflight
# ----------------------------------------------------------------------------

def run_gates() -> dict:
    stores = load_stores()
    recon = {}
    errors = []
    for cell in cells():
        try:
            recon[key(cell)] = reconstruct(cell, stores)
        except Exception as exc:  # gate report, not a crash
            errors.append(f"{key(cell)}: {exc}")
    report = {"cells_total": len(cells()), "gates_passed": not errors,
              "errors": errors,
              "delivery_sets": {f"{a}/{c}": APPLICABILITY[(a, c)]
                                for a in ARMS for c in DIAG_CLUSTERS}}
    return report


def freeze_digests() -> dict[str, str]:
    d = {
        "docs/PREREG-CONT006-DELIVERY-DIAG.md": file_digest(PREREG),
        "docs/SESSION-BRIEF-CONT006-DELIVERY.md": file_digest(BRIEF),
        "experiments/cont006/delivery_v2_diagnostic.py": file_digest(Path(__file__)),
    }
    for rel in FROZEN_SOURCES:
        d[rel] = file_digest(LAB_ROOT / rel)
    for arm in ARMS:
        for kind in ("P", "C", "V"):
            fname, _ = STORE_PINS[(arm, kind)]
            rel = f"results/CONT-006-VAL/cont006-v-20261010-130154/{fname}"
            d[rel] = file_digest(LAB_ROOT / rel)
    for cell in cells():
        cd = cell_dir(cell)
        rel_root = cd.relative_to(LAB_ROOT).as_posix()
        d[rel_root + "/trace.jsonl"] = file_digest(cd / "trace.jsonl")
        d[rel_root + "/memory.sqlite3"] = file_digest(cd / "memory.sqlite3")
    # R0 reference summaries + suite rendered digests per seed (scoring source)
    for root, kind in ((P_ROOT, "P"), (C_ROOT, "C"), (V_ROOT, "V")):
        for arm_dir in sorted(root.iterdir()):
            if not arm_dir.is_dir():
                continue
            for seed_dir in sorted(arm_dir.iterdir()):
                s = seed_dir / "summary.json"
                if s.exists():
                    d[s.relative_to(LAB_ROOT).as_posix()] = file_digest(s)
    _, scenarios_probe = load_suite_for_seed(str(SUITE_DIR), 8001)
    h = hashlib.sha256()
    for scenario in sorted(scenarios_probe, key=lambda s: s["id"]):
        h.update(json.dumps(scenario, sort_keys=True, ensure_ascii=True).encode())
    d["fixtures/v3n_rendered_seed8001_witness"] = h.hexdigest()
    return d


def verify_freeze() -> None:
    if not FREEZE.exists():
        raise SystemExit(f"FAIL-CLOSED: freeze manifest missing: {FREEZE}")
    frozen = json.loads(FREEZE.read_text(encoding="utf-8"))["digests"]
    current = freeze_digests()
    for k, expected in frozen.items():
        if current.get(k) != expected:
            raise SystemExit(f"FAIL-CLOSED: digest mismatch {k}")
    print(f"freeze digests verified ({len(frozen)} entries, byte-match)")


def preflight(base_url: str) -> dict:
    verify_freeze()
    probe = OllamaProvider(base_url=base_url, model=WORKING_MODEL)
    version = probe.version()
    if not version.startswith(OLLAMA_VERSION_PREFIX):
        raise SystemExit(f"FAIL-CLOSED: ollama {version} != {OLLAMA_VERSION_PREFIX}.x")
    # warm-then-pin (CN-001 house order): /api/ps lists only loaded models
    warm = OllamaProvider(base_url=base_url, model=WORKING_MODEL,
                          temperature=TEMPERATURE, seed=0, num_ctx=NUM_CTX,
                          keep_alive=KEEP_ALIVE, timeout_s=TIMEOUT_S)
    t0 = time.monotonic()
    warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
    warmup_s = round(time.monotonic() - t0, 1)
    info = probe.model_info()
    if not info.get("digest", "").startswith(WORKING_DIGEST_PREFIX):
        raise SystemExit(f"FAIL-CLOSED: model digest {info.get('digest')!r}")
    return {"ollama_version": version, "model_digest": info["digest"],
            "warmup_s": warmup_s, "determinism_caveat": DETERMINISM_CAVEAT}


def key(cell: dict) -> str:
    return f"{cell['arm']}/seed-{cell['seed']}/{cell['cluster']}"


# ----------------------------------------------------------------------------
# GPU part (prereg §4)
# ----------------------------------------------------------------------------

def messages_digest(messages: list[dict]) -> str:
    return hashlib.sha256(json.dumps(
        messages, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def run(base_url: str) -> Path:
    env = preflight(base_url)
    stores = load_stores()
    recon = {key(c): reconstruct(c, stores) for c in cells()}
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_root = RESULTS / f"cont006-dd-{ts}"
    out_root.mkdir(parents=True, exist_ok=True)
    env.update({"run_id": out_root.name, "kind": "cont006-delivery-diag",
                "prereg": "docs/PREREG-CONT006-DELIVERY-DIAG.md",
                "calls_planned": 84 * 2 + len(REPLAY_SEEDS) * len(DIAG_CLUSTERS) * len(ARMS)})
    (out_root / "env.json").write_text(
        json.dumps(env, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    provider = OllamaProvider(base_url=base_url, model=WORKING_MODEL,
                              temperature=TEMPERATURE, seed=0, num_ctx=NUM_CTX,
                              num_predict=NUM_PREDICT, keep_alive=KEEP_ALIVE,
                              timeout_s=TIMEOUT_S)
    calls_path = out_root / "calls.jsonl"
    n = 0
    with calls_path.open("w", encoding="utf-8") as fh:
        for cell in cells():
            k = key(cell)
            r = recon[k]
            variants = [("b", r["ctx_b"]), ("c", r["ctx_c"])]
            if cell["seed"] in REPLAY_SEEDS:
                variants.append(("a-replay", r["ctx_a"]))
            for variant, ctx in variants:
                provider.options["seed"] = cell["seed"]  # per-cell pin
                attempts = 0
                while True:
                    attempts += 1
                    try:
                        reply = provider.chat(ctx)
                        break
                    except Exception:
                        if attempts >= 2:
                            raise
                scored = score_probe(r["fx_probe"], reply["content"])
                record = {
                    "cell": k, "arm": cell["arm"], "seed": cell["seed"],
                    "cluster": cell["cluster"], "variant": variant,
                    "options": dict(provider.options),
                    "context_sha256": messages_digest(ctx),
                    "delivery_block": (r["delivery_block"] if variant == "b"
                                       else None),
                    "content": reply["content"],
                    "usage": reply["usage"],
                    "total_duration_ms": reply["total_duration_ms"],
                    "attempts": attempts,
                    "passed": scored["passed"],
                    "observed_label": scored.get("observed_label"),
                    "recorded_passed": r["t"]["recorded_probe"]["passed"],
                    "recorded_reply": r["t"]["recorded_reply"],
                }
                if reply["usage"]["prompt_tokens"] >= NUM_CTX:
                    record["HEADROOM_VIOLATION"] = True
                fh.write(json.dumps(record, ensure_ascii=True) + "\n")
                n += 1
                print(f"[{n:03d}] {k} {variant}: passed={scored['passed']}")
    print(f"run complete: {n} calls -> {calls_path}")
    return out_root


# ----------------------------------------------------------------------------
# analysis (prereg §7)
# ----------------------------------------------------------------------------

def load_calls(run_root: Path) -> list[dict]:
    return [json.loads(l) for l in
            (run_root / "calls.jsonl").read_text(encoding="utf-8").splitlines()]


def recorded_baseline() -> dict:
    """(a) recorded pass/fail per cell key — from the committed traces."""
    out = {}
    for cell in cells():
        t = parse_trace(cell)
        out[key(cell)] = t["recorded_probe"]["passed"] is True
    return out


def analyze(run_root: Path) -> dict:
    calls = load_calls(run_root)
    base = recorded_baseline()
    by = {(c["cell"], c["variant"]): c for c in calls}
    planned = 84 * 2 + len(REPLAY_SEEDS) * len(DIAG_CLUSTERS) * len(ARMS)
    missing = []
    headroom = [c for c in calls if c.get("HEADROOM_VIOLATION")]
    for cell in cells():
        for variant in ("b", "c"):
            if (key(cell), variant) not in by:
                missing.append(f"{key(cell)}/{variant}")
        if cell["seed"] in REPLAY_SEEDS and (key(cell), "a-replay") not in by:
            missing.append(f"{key(cell)}/a-replay")
    def rate(variant: str, clusters, arms) -> tuple[int, int]:
        hit = tot = 0
        for cell in cells():
            if cell["cluster"] in clusters and cell["arm"] in arms:
                tot += 1
                if variant == "a":
                    hit += 1 if base[key(cell)] else 0
                else:
                    hit += 1 if by[(key(cell), variant)]["passed"] else 0
        return hit, tot
    # P4: replay noise floor
    replays = [c for c in calls if c["variant"] == "a-replay"]
    exact = sum(1 for c in replays
                if c["content"].strip() == c["recorded_reply"].strip())
    score_agree = sum(1 for c in replays
                      if (c["passed"] is True) == (c["recorded_passed"] is True))
    harm_b, harm_n = rate("b", HARM_CLUSTERS, ARMS)
    harm_c, _ = rate("c", HARM_CLUSTERS, ARMS)
    harm_a, _ = rate("a", HARM_CLUSTERS, ARMS)
    r3_harm_b, _ = rate("b", HARM_CLUSTERS, ("R3",))
    r3_harm_a, _ = rate("a", HARM_CLUSTERS, ("R3",))
    rt84_b, rt84_n = rate("b", ("rt-8204",), ARMS)
    noise_rate = (len(replays) - score_agree) / len(replays) if replays else None
    p1_delta = harm_b / harm_n - harm_a / harm_n
    predictions = {
        "P1_delivery_fixes_harm": {
            "b_pooled": f"{harm_b}/{harm_n}", "a_pooled": f"{harm_a}/{harm_n}",
            "delta": round(p1_delta, 4),
            "directional": p1_delta > 0,
            "beyond_noise": (p1_delta > noise_rate if noise_rate is not None
                             else p1_delta > 0),
            "meaningful_band_ge": "42/56",
            "meaningful_band_met": harm_b >= 42,
        },
        "P1a_r3_recovery": {
            "b_r3": f"{r3_harm_b}/28", "a_r3": f"{r3_harm_a}/28",
            "directional": r3_harm_b > r3_harm_a,
            "band_ge": "21/28", "band_met": r3_harm_b >= 21,
        },
        "P2_rt8204_gains_retained": {
            "b_pooled": f"{rt84_b}/{rt84_n}", "threshold_ge": "7/14",
            "met": rt84_b >= 7,
            "recorded_a": "12/14", "recorded_r0": "2/14",
        },
        "P3_discriminating": {
            "b_le_a": p1_delta <= 0,
            "b_lt_c": harm_b < harm_c,
            "reading": ("delivery defects alone do NOT explain (b<=a); "
                        "corrected lessons actively hurt vs none (b<c) -> "
                        "content/capacity strengthen" if harm_b < harm_c else
                        "see per-cluster detail"),
        },
        "P4_noise_floor": {
            "replays": len(replays), "exact_content_matches": exact,
            "score_agreements": score_agree, "noise_rate": noise_rate,
        },
        "c_memory_only_harm_pooled": f"{harm_c}/56",
    }
    per_cluster = {}
    for cluster in DIAG_CLUSTERS:
        row = {"r0_reference": None, "a": None, "b": None, "c": None}
        for variant in ("a", "b", "c"):
            hit, tot = rate(variant, (cluster,), ARMS)
            row[variant] = f"{hit}/{tot}"
        per_cluster[cluster] = row
    per_arm = {}
    for arm in ARMS:
        per_arm[arm] = {
            v: {c: rate(v, (c,), (arm,)) for c in DIAG_CLUSTERS}
            for v in ("a", "b", "c")}
    # error modes per variant (harm clusters)
    err = {}
    for variant in ("a", "b", "c"):
        if variant == "a":
            continue
        fm = wl = 0
        for cell in cells():
            if cell["cluster"] in HARM_CLUSTERS:
                c = by[(key(cell), variant)]
                if not c["passed"]:
                    if c["observed_label"] is None:
                        fm += 1
                    else:
                        wl += 1
        err[variant] = {"wrong_label": wl, "format_miss": fm}
    # lesson-echo telemetry: reply shares >=6 consecutive words with a lesson line
    def echo(c: dict) -> bool:
        block = c.get("delivery_block")
        if not block:
            return False
        reply_words = c["content"].lower().split()
        for line in block.splitlines()[1:]:
            lw = [w.strip(".,:;") for w in line.lower().split()]
            for i in range(len(lw) - 5):
                gram = " ".join(lw[i:i + 6])
                if gram in " ".join(reply_words):
                    return True
        return False
    echo_b = sum(1 for c in calls if c["variant"] == "b" and echo(c))
    # exploratory bootstrap over harm-cluster deltas (b-a, b-c), cluster level
    import random
    rng = random.Random(BOOT_SEED)
    boot = {}
    for label, variant in (("b_minus_a", "b"), ("b_minus_c", "c")):
        deltas = []
        for cluster in HARM_CLUSTERS:
            hit_x, tot = rate(variant, (cluster,), ARMS)
            if variant == "b":
                hit_y, _ = rate("a", (cluster,), ARMS)
            else:
                hit_y, _ = rate("c", (cluster,), ARMS)
            deltas.append(hit_x / tot - hit_y / tot)
        stars = []
        for _ in range(BOOT_DRAWS):
            sample = [deltas[rng.randrange(len(deltas))] for _ in deltas]
            stars.append(sum(sample) / len(sample))
        stars.sort()
        boot[label] = {"mean": round(sum(deltas) / len(deltas), 4),
                       "ci_lo": round(stars[int(0.025 * BOOT_DRAWS)], 4),
                       "ci_hi": round(stars[int(0.975 * BOOT_DRAWS)], 4),
                       "note": "exploratory diagnostic; never promotable"}
    usage = {"prompt_tokens_max": max(c["usage"]["prompt_tokens"] for c in calls),
             "eval_tokens_max": max(c["usage"]["eval_tokens"] for c in calls)}
    report = {
        "kind": "cont006-delivery-diag-results",
        "run_root": str(run_root.relative_to(LAB_ROOT)),
        "prereg": "docs/PREREG-CONT006-DELIVERY-DIAG.md",
        "completeness": {"calls": len(calls), "planned": planned,
                         "missing": missing, "headroom_violations": len(headroom)},
        "recorded_baselines": {"harm_pooled": {"R0": "25/28", "R2(a)": "19/28",
                                               "R3(a)": "17/28"}},
        "predictions": predictions,
        "per_cluster_arms_pooled": per_cluster,
        "per_arm_detail": per_arm,
        "error_modes_harm_clusters": err,
        "lesson_echo_b_variant": {"count": echo_b, "of": sum(
            1 for c in calls if c["variant"] == "b")},
        "bootstrap_exploratory": boot,
        "usage": usage,
        "determinism_caveat": DETERMINISM_CAVEAT,
        "non_goals": ("registered V2A verdict and artifacts untouched; "
                      "diagnostic only"),
    }
    out = run_root / "delivery-diag-results.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print(f"analysis written: {out}")
    print(json.dumps(predictions, indent=1))
    return report


# ----------------------------------------------------------------------------
# self-test (offline)
# ----------------------------------------------------------------------------

def self_test() -> int:
    stores = load_stores()
    # delivery render: full fields, deterministic
    b = delivery_v2_block("R3", "cr-8003", stores[("R3", "P")].store)
    assert b.startswith(DELIVERY_V2_HEADER)
    assert "Rule:" in b and "Behavior:" in b
    assert "LL-G-003" not in b  # ids never rendered (anti-salience carryover)
    assert b.count("\n") == 3, b  # header + 3 lessons
    assert delivery_v2_block(
        "R2", "cr-8003", stores[("R2", "P")].store).count("\n") == 1
    # gates on 4 stratified cells (fast offline check; full gates run separately)
    for cell in cells()[:2]:
        r = reconstruct(cell, stores)
        assert r["ctx_a"][0]["content"] == ARM_A_SYSTEM_PROMPT
        assert r["ctx_c"][1]["role"] == "system"
        assert r["ctx_b"][-1]["role"] == "user"
    print("SELF-TEST PASS: delivery render + reconstruction helpers")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--gates", action="store_true")
    parser.add_argument("--emit-freeze", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--analyze", default=None,
                        help="run root of the completed diagnostic")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.gates:
        report = run_gates()
        print(json.dumps({k: v for k, v in report.items() if k != "errors"},
                         indent=1))
        if report["errors"]:
            print("GATE ERRORS:", *report["errors"], sep="\n  ")
            return 1
        print("GATES PASS (G-A..G-E, 84/84 cells)")
        return 0
    if args.emit_freeze:
        report = run_gates()
        if report["errors"]:
            raise SystemExit("gates failed; freeze refused")
        manifest = {
            "kind": "cont006-delivery-diag-freeze",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "prereg": "docs/PREREG-CONT006-DELIVERY-DIAG.md",
            "gates": "G-A..G-E passed on all 84 cells before emission",
            "digests": freeze_digests(),
        }
        FREEZE.write_text(json.dumps(manifest, indent=1, ensure_ascii=True)
                          + "\n", encoding="utf-8")
        print(f"freeze manifest written: {FREEZE} "
              f"({len(manifest['digests'])} digests)")
        return 0
    if args.preflight:
        print(json.dumps(preflight(args.base_url), indent=1))
        print("PREFLIGHT OK (no inference performed)")
        return 0
    if args.run:
        run(args.base_url)
        return 0
    if args.analyze:
        analyze(Path(args.analyze).resolve())
        return 0
    parser.print_help()
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
