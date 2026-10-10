"""CONT-006 CAPACITY-×-CONTENT (step 3): two models × five delivery
conditions over the step-1 recorded probe cells; corrected delivery held
fixed; the neutral block separates content from generic interference.

Implements docs/PREREG-CONT006-CAPACITY-CONTENT.md (pre-registered before
any consumer inference; digested by capacity-freeze.json). Reuses the
step-1 machinery (delivery_v2_diagnostic.py — imported read-only: cells,
reconstruction, stores, pins, gates) and the W3 faithful worker store.

Models: G8B granite-code:8b (36c3c3b9683b) and Q35 qwen36-35b-a3b:mdlslab
(8a0fd5da454e) under IDENTICAL sampling pins (temp 0.0, seed = cell seed,
num_ctx 4096, num_predict 256, think:false, keep_alive 30m) and
byte-identical prompts per condition.

Conditions (one system message right before the probe turn for 2..5):
  NONE   no lesson block (G8B reuses the step-1 (c) calls)
  NEUTRAL matched control (prereg §5 texts; N = |OLDG set| per cluster)
  OLDW   executed worker store + step-1 W-annotation (G8B reuses the
         arm-matched step-1 (b) calls; cross-arm cells are new)
  OLDG   executed gold store + step-1 G-annotation (same reuse rule)
  NEWF   W3 faithful-evidence store + prereg §6 annotation

  --gates        zero-GPU gates (incl. context-sha256 equality for the
                 168 reused step-1 calls) + NEWF annotation completeness
  --emit-freeze  gates, then write capacity-freeze.json
  --preflight    re-verify freeze + warm-then-pin BOTH models
  --run          the 696 new inference calls -> results/CONT-006-CAPACITY/
  --analyze      endpoints E1-E4 + tables -> capacity-results.json
  --self-test    offline render/reuse checks
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

import delivery_v2_diagnostic as dd  # noqa: E402 (step-1 module, read-only)

from continuity.lessons import load_store  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import score_probe  # noqa: E402

MODELS = {
    "G8B": ("granite-code:8b", "36c3c3b9683b"),
    "Q35": ("qwen36-35b-a3b:mdlslab", "8a0fd5da454e"),
}
CONDITIONS = ("NONE", "NEUTRAL", "OLDW", "OLDG", "NEWF")
HARM_CLUSTERS = dd.HARM_CLUSTERS  # cr-8003/8004 + dx-8401/8402
DUP_SEEDS = (8001, 8005)

VAL_ROOT = dd.V_ROOT
STEP1_ROOT = (LAB_ROOT / "results" / "CONT-006-DELIVERY-DIAG" /
              "cont006-dd-20261010-183404")
FREEZE = LAB_ROOT / "experiments" / "cont006" / "capacity-freeze.json"
RESULTS = LAB_ROOT / "results" / "CONT-006-CAPACITY"
PREREG = LAB_ROOT / "docs" / "PREREG-CONT006-CAPACITY-CONTENT.md"

# W3 output dir (the faithful store) — pinned at freeze time
W3_GLOB = "cont006-worker-v3-*"

# prereg §5 neutral texts (fixed; ~95-105 words each so that N-line totals
# sit within ±25% of the OLDG block for every cluster: cr 3 lines vs ~290
# words, dx/rt 2 lines vs ~191-200 words)
NEUTRAL_TEXTS = [
    ("Shift handover hygiene",
     "a shift ends and a handover note is written for the incoming desk "
     "worker",
     "record only the start and end times of the shift, the desk location, "
     "and whether the keys were returned; nothing about ongoing tasks "
     "belongs in the note, because the task board is updated separately by "
     "the rota lead each morning and duplicate notes cause confusion",
     "write the note in the same order every time, keep it to a few short "
     "lines, date it at the top, and leave it in the tray under the desk "
     "lamp rather than pinning it to the wall where previous notes have "
     "gone missing during busy hours"),
    ("Supply shelf order",
     "the supply shelf is restocked during a quiet period before the "
     "weekly count",
     "arrange items by size with the tallest containers at the back and "
     "the smallest in front, keep one clear aisle between the glassware "
     "and the paper stock, and never stack loose pens or brushes on top of "
     "the ledgers that live on the lower level of the same shelf",
     "wipe the shelf before restocking, label any box that has lost its "
     "mark, fold the step stool against the wall afterwards, and note the "
     "count date on the clipboard so the next shift knows the shelf was "
     "already checked and can trust the arrangement they inherit"),
    ("Visitor greeting practice",
     "a visitor arrives at the desk during daytime hours while the sign-in "
     "book is open",
     "greet the visitor first, then ask the purpose of the visit, then "
     "point to the floor plan only if the purpose actually needs one; "
     "courier deliveries go to the side hatch, never the front desk, and "
     "contractors must show a badge before being waved through",
     "keep the floor-plan reference brief, offer the chair by the window "
     "to anyone who has to wait, return the visitor badge tray to its "
     "drawer after use, and log the visit with initials rather than full "
     "names so the sign-in line keeps moving at busy times"),
]

# prereg §6 — NEWF lessons annotated NOT applicable at every cluster
NEWF_NEVER_APPLICABLE = ("LL-W-002", "LL-W-003")

# prereg §6 — NEWF applicability annotation, cluster -> [lessonId]
# (from the W3 store BEFORE the freeze; bases in the prereg table)
NEWF_ANNOTATION: dict[str, list[str]] = {
    "cr-8003": ["LL-W-004"],
    "cr-8004": ["LL-W-005"],
    "dx-8401": [],
    "dx-8402": [],
    "rt-8203": [],
    "rt-8204": [],
}


def w3_dir() -> Path:
    matches = sorted((LAB_ROOT / "results" / "CONT-006-WORKER").glob(W3_GLOB))
    if not matches:
        raise FileNotFoundError("W3 worker output dir not found")
    return matches[-1]


def newf_store() -> dict:
    path = w3_dir() / "r2-store-v2.json"
    return load_store(path)


def render_full(store: dict, ids: list[str]) -> str | None:
    """The corrected-delivery full-field renderer (byte-consistent with
    dd.delivery_v2_block — asserted in --self-test)."""
    if not ids:
        return None
    by_id = {l["lessonId"]: l for l in store["lessons"]}
    lines = [dd.DELIVERY_V2_HEADER]
    for i, lid in enumerate(ids, start=1):
        les = by_id[lid]
        when = "; ".join(str(a) for a in les.get("applicability", [])) or "relevant"
        lines.append(f"{i}. {les['title']}. When {when}: "
                     f"Rule: {les['lesson']} Behavior: {les['recommendedBehavior']}")
    return "\n".join(lines)


def neutral_block(cluster: str) -> str:
    n = len(dd.APPLICABILITY[("R3", cluster)])  # |OLDG set| per cluster
    lines = [dd.DELIVERY_V2_HEADER]
    for i, (title, when, rule, beh) in enumerate(NEUTRAL_TEXTS[:n], start=1):
        lines.append(f"{i}. {title}. When {when}: Rule: {rule} Behavior: {beh}")
    return "\n".join(lines)


def condition_block(condition: str, cluster: str,
                    r2_store: dict, r3_store: dict, nf_store: dict) -> str | None:
    if condition == "NONE":
        return None
    if condition == "NEUTRAL":
        return neutral_block(cluster)
    if condition == "OLDW":
        return render_full(r2_store, dd.APPLICABILITY[("R2", cluster)])
    if condition == "OLDG":
        return render_full(r3_store, dd.APPLICABILITY[("R3", cluster)])
    if condition == "NEWF":
        return render_full(nf_store, NEWF_ANNOTATION.get(cluster, []))
    raise ValueError(condition)


def build_contexts(recon: dict, cell: dict, stores: dict) -> dict[str, list]:
    ctx_c = recon["ctx_c"]
    blocks = {c: condition_block(c, cell["cluster"], stores["R2"],
                                 stores["R3"], stores["NEWF"])
              for c in CONDITIONS}
    out = {}
    for cond in CONDITIONS:
        block = blocks[cond]
        if block is None:
            out[cond] = ctx_c
        else:
            out[cond] = ctx_c[:-1] + [{"role": "system", "content": block},
                                      ctx_c[-1]]
    return out


def load_step1_calls() -> dict[tuple[str, str], dict]:
    path = STEP1_ROOT / "calls.jsonl"
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        r = json.loads(line)
        out[(r["cell"], r["variant"])] = r
    return out


# ----------------------------------------------------------------------------
# gates / freeze / preflight
# ----------------------------------------------------------------------------

def run_gates() -> dict:
    errors = []
    # step-1 gates re-run over all cells (G-A..G-E inside dd.reconstruct)
    dd_stores = dd.load_stores()
    recon = {}
    for cell in dd.cells():
        try:
            recon[dd.key(cell)] = dd.reconstruct(cell, dd_stores)
        except Exception as exc:
            errors.append(f"{dd.key(cell)}: {exc}")
    # stores for conditions
    stores = {"R2": dd_stores[("R2", "P")].store, "R3": dd_stores[("R3", "P")].store}
    try:
        stores["NEWF"] = newf_store()
    except Exception as exc:
        errors.append(f"NEWF store: {exc}")
        stores["NEWF"] = {"lessons": []}
    # NEWF annotation completeness: every W3 lesson rated for every cluster
    nf_ids = {l["lessonId"] for l in stores["NEWF"].get("lessons", [])}
    if nf_ids:
        for cluster in dd.DIAG_CLUSTERS:
            ids = NEWF_ANNOTATION.get(cluster, [])
            unknown = [i for i in ids if i not in nf_ids]
            if unknown:
                errors.append(f"NEWF annotation {cluster}: unknown ids {unknown}")
        rated = set(i for ids in NEWF_ANNOTATION.values() for i in ids)
        unrated = nf_ids - rated - set(NEWF_NEVER_APPLICABLE)
        if unrated:
            errors.append(f"NEWF annotation incomplete (neither delivered "
                          f"anywhere nor in NEWF_NEVER_APPLICABLE): "
                          f"{sorted(unrated)}")
    else:
        if NEWF_ANNOTATION:
            errors.append("NEWF annotation non-empty but the W3 store is empty")
    # context-sha equality vs the step-1 records
    step1 = load_step1_calls()
    reused = 0
    for cell in dd.cells():
        k = dd.key(cell)
        ctxs = build_contexts(recon[k], cell, stores)
        for cond, variant in (("NONE", "c"),):
            want = step1.get((k, variant), {}).get("context_sha256")
            if want and dd.messages_digest(ctxs[cond]) != want:
                errors.append(f"{k} {cond}: sha != step-1 {variant}")
        arm_matched = "OLDW" if cell["arm"] == "R2" else "OLDG"
        want = step1.get((k, "b"), {}).get("context_sha256")
        if want:
            if dd.messages_digest(ctxs[arm_matched]) != want:
                errors.append(f"{k} {arm_matched}: sha != step-1 b")
            reused += 1
    # neutral word budget: within ±25% of the OLDG block per cluster
    for cluster in dd.DIAG_CLUSTERS:
        g = condition_block("OLDG", cluster, stores["R2"], stores["R3"],
                            stores["NEWF"]) or ""
        n = neutral_block(cluster)
        wg, wn = len(g.split()), len(n.split())
        if abs(wn - wg) > 0.25 * wg:
            errors.append(f"neutral words {wn} vs OLDG {wg} ({cluster}) >±25%")
    report = {
        "cells": len(dd.cells()),
        "reused_step1_records": reused + 84,
        "newf_lessons": sorted(nf_ids),
        "newf_annotation": NEWF_ANNOTATION,
        "gates_passed": not errors,
        "errors": errors,
    }
    return report


def freeze_digests() -> dict[str, str]:
    d = dd.freeze_digests()  # step-1's full input surface (sources, stores,
    # traces, memories, summaries, the step-1 module itself, prereg, brief)
    d["docs/PREREG-CONT006-CAPACITY-CONTENT.md"] = dd.file_digest(PREREG)
    d["experiments/cont006/capacity_content_diag.py"] = dd.file_digest(
        Path(__file__))
    d["experiments/cont006/worker_v3_bundles.py"] = dd.file_digest(
        LAB_ROOT / "experiments" / "cont006" / "worker_v3_bundles.py")
    d["experiments/cont006/worker_v3_bundles.json"] = dd.file_digest(
        LAB_ROOT / "experiments" / "cont006" / "worker_v3_bundles.json")
    w3 = w3_dir()
    for name in ("r2-store-v2.json", "candidates-v2.json",
                 "telemetry-v2.json", "raw-worker-log-v2.jsonl"):
        rel = (w3 / name).relative_to(LAB_ROOT).as_posix()
        d[rel] = dd.file_digest(w3 / name)
    for name in ("calls.jsonl", "env.json", "delivery-diag-results.json"):
        rel = (STEP1_ROOT / name).relative_to(LAB_ROOT).as_posix()
        d[rel] = dd.file_digest(STEP1_ROOT / name)
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
    out = {"ollama_version": None, "models": {}}
    for tag, (model, prefix) in MODELS.items():
        probe = OllamaProvider(base_url=base_url, model=model)
        version = probe.version()
        if out["ollama_version"] is None:
            out["ollama_version"] = version
            if not version.startswith("0.34"):
                raise SystemExit(f"FAIL-CLOSED: ollama {version}")
        warm = OllamaProvider(base_url=base_url, model=model, temperature=0.0,
                              seed=0, num_ctx=dd.NUM_CTX, keep_alive="30m",
                              timeout_s=600)
        t0 = time.monotonic()
        warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
        info = probe.model_info()
        if not info.get("digest", "").startswith(prefix):
            raise SystemExit(f"FAIL-CLOSED: {model} digest {info.get('digest')!r}")
        out["models"][tag] = {"name": model, "digest": info["digest"],
                              "warmup_s": round(time.monotonic() - t0, 1)}
    out["determinism_caveat"] = dd.DETERMINISM_CAVEAT
    return out


# ----------------------------------------------------------------------------
# GPU part
# ----------------------------------------------------------------------------

def planned_calls() -> int:
    g8b_new = 84 * 2 + 42 * 2          # NEUTRAL+NEWF all cells, cross-arm OLDW/OLDG
    q35 = 84 * len(CONDITIONS)          # all conditions on all cells
    dup = 24                            # Q35 NONE duplicates (seeds 8001/8005)
    return g8b_new + q35 + dup


def run(base_url: str) -> Path:
    env = preflight(base_url)
    dd_stores = dd.load_stores()
    stores = {"R2": dd_stores[("R2", "P")].store, "R3": dd_stores[("R3", "P")].store,
              "NEWF": newf_store()}
    recon = {dd.key(c): dd.reconstruct(c, dd_stores) for c in dd.cells()}
    step1 = load_step1_calls()
    ts = time.strftime("%Y%m%d-%H%M%S")
    out_root = RESULTS / f"cont006-cap-{ts}"
    out_root.mkdir(parents=True, exist_ok=True)
    env.update({"run_id": out_root.name, "kind": "cont006-capacity-content",
                "prereg": "docs/PREREG-CONT006-CAPACITY-CONTENT.md",
                "planned_new_calls": planned_calls(),
                "reused_step1_calls": 168})
    (out_root / "env.json").write_text(
        json.dumps(env, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    providers = {
        tag: OllamaProvider(base_url=base_url, model=model, temperature=0.0,
                            seed=0, num_ctx=dd.NUM_CTX, num_predict=256,
                            keep_alive="30m", timeout_s=600)
        for tag, (model, _) in MODELS.items()}
    calls_path = out_root / "calls.jsonl"
    n = 0

    def emit(record: dict, fh) -> None:
        fh.write(json.dumps(record, ensure_ascii=True) + "\n")

    def call_and_score(tag, cond, cell, ctx, recon_entry, fh, note=None):
        nonlocal n
        providers[tag].options["seed"] = cell["seed"]
        attempts = 0
        while True:
            attempts += 1
            try:
                reply = providers[tag].chat(ctx)
                break
            except Exception:
                if attempts >= 3:
                    raise
        scored = score_probe(recon_entry["fx_probe"], reply["content"])
        n += 1
        rec = {"cell": dd.key(cell), "arm": cell["arm"], "seed": cell["seed"],
               "cluster": cell["cluster"], "model": tag, "condition": cond,
               "options": dict(providers[tag].options),
               "context_sha256": dd.messages_digest(ctx),
               "content": reply["content"], "usage": reply["usage"],
               "attempts": attempts, "passed": scored["passed"],
               "observed_label": scored.get("observed_label")}
        if note:
            rec["note"] = note
        if reply["usage"]["prompt_tokens"] >= dd.NUM_CTX:
            rec["HEADROOM_VIOLATION"] = True
        emit(rec, fh)
        print(f"[{n:03d}] {tag} {cond:7s} {dd.key(cell)}: {scored['passed']}")

    with calls_path.open("w", encoding="utf-8") as fh:
        # G8B first (fast; validates contexts), then Q35
        for cell in dd.cells():
            k = dd.key(cell)
            ctxs = build_contexts(recon[k], cell, stores)
            for cond in ("NEUTRAL", "NEWF"):
                call_and_score("G8B", cond, cell, ctxs[cond], recon[k], fh)
            cross = "OLDG" if cell["arm"] == "R2" else "OLDW"
            call_and_score("G8B", cross, cell, ctxs[cross], recon[k], fh)
            # reuse arm-matched + NONE from step 1 (records referenced)
            for cond, variant in (("NONE", "c"),):
                s1 = step1[(k, variant)]
                emit({"cell": k, "arm": cell["arm"], "seed": cell["seed"],
                      "cluster": cell["cluster"], "model": "G8B",
                      "condition": cond,
                      "options": s1["options"],
                      "context_sha256": s1["context_sha256"],
                      "content": s1["content"], "usage": s1["usage"],
                      "attempts": s1.get("attempts", 1),
                      "passed": s1["passed"],
                      "observed_label": s1.get("observed_label"),
                      "note": f"reused step-1 {variant}"}, fh)
            arm_matched = "OLDW" if cell["arm"] == "R2" else "OLDG"
            s1 = step1[(k, "b")]
            emit({"cell": k, "arm": cell["arm"], "seed": cell["seed"],
                  "cluster": cell["cluster"], "model": "G8B",
                  "condition": arm_matched, "options": s1["options"],
                  "context_sha256": s1["context_sha256"],
                  "content": s1["content"], "usage": s1["usage"],
                  "attempts": s1.get("attempts", 1), "passed": s1["passed"],
                  "observed_label": s1.get("observed_label"),
                  "note": "reused step-1 b"}, fh)
        for cell in dd.cells():
            k = dd.key(cell)
            ctxs = build_contexts(recon[k], cell, stores)
            for cond in CONDITIONS:
                call_and_score("Q35", cond, cell, ctxs[cond], recon[k], fh)
            if cell["seed"] in DUP_SEEDS:
                call_and_score("Q35", "NONE-dup", cell, ctxs["NONE"],
                               recon[k], fh, note="determinism duplicate")
    print(f"run complete: {n} new calls -> {calls_path}")
    return out_root


# ----------------------------------------------------------------------------
# analysis
# ----------------------------------------------------------------------------

def analyze(run_root: Path) -> dict:
    calls = [json.loads(l) for l in
             (run_root / "calls.jsonl").read_text(encoding="utf-8").splitlines()]
    by = {(c["cell"], c["model"], c["condition"]): c for c in calls}
    cells = dd.cells()
    hcells = [c for c in cells if c["cluster"] in HARM_CLUSTERS]

    def s(model: str, cond: str, pool) -> tuple[int, int]:
        hit = tot = 0
        for cell in pool:
            r = by.get((dd.key(cell), model, cond))
            if r is None:
                continue
            tot += 1
            hit += 1 if r["passed"] else 0
        return hit, tot

    def delta(model: str, cond: str, pool) -> tuple[int, int, int]:
        lx, n1 = s(model, cond, pool)
        ln, n0 = s(model, "NONE", pool)
        return lx - ln, n1, n0

    report: dict = {"kind": "cont006-capacity-results",
                    "run_root": str(run_root.relative_to(LAB_ROOT)),
                    "prereg": "docs/PREREG-CONT006-CAPACITY-CONTENT.md"}
    completeness = {
        "records": len(calls),
        "planned": 168 + planned_calls(),
        "headroom_violations": sum(1 for c in calls if c.get("HEADROOM_VIOLATION")),
        "reused": sum(1 for c in calls if str(c.get("note", "")).startswith("reused")),
    }
    report["completeness"] = completeness
    harm = {}
    for model in MODELS:
        for cond in CONDITIONS:
            hit, tot = s(model, cond, hcells)
            harm[f"{model}/{cond}"] = f"{hit}/{tot}"
    report["harm_pools"] = harm
    e = {}
    for cond in ("OLDW", "OLDG", "NEWF"):
        dq, _, _ = delta("Q35", cond, hcells)
        dg, _, _ = delta("G8B", cond, hcells)
        e[f"I_{cond}"] = {"interaction_probes": dq - dg,
                          "q35_delta_probes": dq, "g8b_delta_probes": dg,
                          "positive": (dq - dg) > 0,
                          "band_met": (dq - dg) >= 4}
    report["E1_capacity"] = e
    dn = {}
    for model in MODELS:
        dnm, _, _ = delta(model, "NEUTRAL", hcells)
        dn[model] = dnm
    # fixed E2 reading rule
    dg_oldg, _, _ = delta("G8B", "OLDG", hcells)
    e2 = {"neutral_minus_none_probes": dn,
          "neutral_reproduces_at_least_-3": dn["G8B"] <= -3,
          "neutral_within_3_of_none": abs(dn["G8B"]) <= 3,
          "neutral_vs_oldg_gap_le_3": abs(dn["G8B"] - dg_oldg) <= 3,
          "reading": ("neutral reproduces the lesson deficit -> generic "
                      "prompt interference" if dn["G8B"] <= -3
                      and abs(dn["G8B"] - dg_oldg) <= 3 else
                      "lesson deficit is content-specific" if abs(dn["G8B"]) <= 3
                      and dg_oldg <= -3 else "mixed/indeterminate (see pools)")}
    report["E2_interference"] = e2
    e3 = {}
    for model in MODELS:
        dnf, _, _ = delta(model, "NEWF", hcells)
        dow, _, _ = delta(model, "OLDW", hcells)
        e3[model] = {"newf_delta_probes": dnf, "oldw_delta_probes": dow,
                     "newf_ge_oldw": dnf >= dow}
    report["E3_fidelity"] = e3
    nq = s("Q35", "NONE", hcells)
    ng = s("G8B", "NONE", hcells)
    report["E4_level_nonprimary"] = {"q35_none": nq, "g8b_none": ng}
    dups = [c for c in calls if c["condition"] == "NONE-dup"]
    base_none = {c["cell"]: c for c in calls
                 if c["model"] == "Q35" and c["condition"] == "NONE"}
    agree = sum(1 for c in dups
                if (c["passed"] is True) == (base_none[c["cell"]]["passed"] is True))
    report["noise_floors"] = {
        "g8b_step1_replay": "1/24 score disagreement (carried)",
        "q35_duplicates": {"n": len(dups), "score_agreements": agree},
        "q35_dup_noise_rate": round(1 - agree / len(dups), 4) if dups else None}
    per_cluster = {}
    for cluster in dd.DIAG_CLUSTERS:
        pool = [c for c in cells if c["cluster"] == cluster]
        per_cluster[cluster] = {
            f"{m}/{cond}": "/".join(map(str, s(m, cond, pool)))
            for m in MODELS for cond in CONDITIONS}
    report["per_cluster"] = per_cluster
    err = {}
    for model in MODELS:
        for cond in CONDITIONS:
            fm = wl = 0
            for cell in hcells:
                r = by.get((dd.key(cell), model, cond))
                if r is not None and not r["passed"]:
                    if r["observed_label"] is None:
                        fm += 1
                    else:
                        wl += 1
            err[f"{model}/{cond}"] = {"wrong_label": wl, "format_miss": fm}
    report["error_modes_harm"] = err
    usage = {"prompt_tokens_max": max(c["usage"]["prompt_tokens"] for c in calls),
             "eval_tokens_max": max(c["usage"]["eval_tokens"] for c in calls)}
    report["usage"] = usage
    # exploratory bootstrap for I_OLDG (cluster-level)
    import random
    rng = random.Random(20261011)
    per_cluster_deltas = []
    for cluster in HARM_CLUSTERS:
        pool = [c for c in cells if c["cluster"] == cluster]
        dq, _, _ = delta("Q35", "OLDG", pool)
        dg, _, _ = delta("G8B", "OLDG", pool)
        per_cluster_deltas.append((dq - dg) / len(pool))
    stars = []
    if per_cluster_deltas:
        for _ in range(10_000):
            sample = [per_cluster_deltas[rng.randrange(len(per_cluster_deltas))]
                      for _ in per_cluster_deltas]
            stars.append(sum(sample) / len(sample))
        stars.sort()
        report["bootstrap_I_OLDG_exploratory"] = {
            "mean": round(sum(per_cluster_deltas) / len(per_cluster_deltas), 4),
            "ci_lo": round(stars[int(0.025 * 10_000)], 4),
            "ci_hi": round(stars[int(0.975 * 10_000)], 4),
            "note": "exploratory diagnostic; never promotable"}
    report["determinism_caveat"] = dd.DETERMINISM_CAVEAT
    report["non_goals"] = ("registered verdicts untouched; stage-2 suite "
                           "(v3o, balanced sampling, end-to-end) is a "
                           "separate brief")
    out = run_root / "capacity-results.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print(f"analysis written: {out}")
    print(json.dumps({k: report[k] for k in ("harm_pools", "E1_capacity",
                                             "E2_interference", "E3_fidelity",
                                             "noise_floors")}, indent=1))
    return report


def self_test() -> int:
    dd_stores = dd.load_stores()
    stores = {"R2": dd_stores[("R2", "P")].store, "R3": dd_stores[("R3", "P")].store}
    # renderer consistency vs the step-1 module
    for cluster in dd.DIAG_CLUSTERS:
        for arm in ("R2", "R3"):
            mine = render_full(stores[arm], dd.APPLICABILITY[(arm, cluster)])
            theirs = dd.delivery_v2_block(arm, cluster, stores[arm])
            assert mine == theirs, (arm, cluster)
    # neutral line counts match |OLDG| per cluster
    for cluster in dd.DIAG_CLUSTERS:
        nb = neutral_block(cluster)
        assert nb.count("\n") == len(dd.APPLICABILITY[("R3", cluster)])
    print("SELF-TEST PASS: render consistency + neutral line counts")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--gates", action="store_true")
    parser.add_argument("--emit-freeze", action="store_true")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--run", action="store_true")
    parser.add_argument("--analyze", default=None)
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.gates:
        rep = run_gates()
        print(json.dumps({k: v for k, v in rep.items() if k != "errors"}, indent=1))
        if rep["errors"]:
            print("GATE ERRORS:", *rep["errors"], sep="\n  ")
            return 1
        print("GATES PASS")
        return 0
    if args.emit_freeze:
        rep = run_gates()
        if rep["errors"]:
            raise SystemExit("gates failed; freeze refused")
        manifest = {
            "kind": "cont006-capacity-freeze",
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "prereg": "docs/PREREG-CONT006-CAPACITY-CONTENT.md",
            "gates": "passed before emission (incl. 168-call reuse sha equality)",
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
