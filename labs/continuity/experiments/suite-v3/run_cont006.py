"""CONT-006 run script (frozen at FREEZE): the phased lesson-transfer chain.

Per docs/EVALUATION-PREP-CONT006.md (owner-accepted 2026-10-08, ROADMAP) and
docs/CONT-006-DESIGN.md. Phases (binding order):

  --phase W           worker pass: ONE batch call per corpus arm-seed trace
                      (reflector qwen36-35b-a3b:mdlslab, think-pin inherited)
                      -> raw-worker-log.jsonl + candidates.json + telemetry
                      + r2-store-evidence-validated.json
  --phase G-validate  run the §7.1 evidence validator over the blind-authored
                      R3 candidates file -> r3-store-evidence-validated.json
  --phase V           activation runs: R0/R2/R3 x seeds {6001..6007} on the
                      4 VALIDATION clusters only (results/CONT-006-VAL/)
  --phase V-activate  deterministic post-processing: S0/SX pass rates, the
                      frozen store-level rule (activate iff SX - S0 >= +0.05,
                      fail-closed on any missing/invalid VAL probe) ->
                      active-store-r2.json / active-store-r3.json (full copy
                      or EMPTY) + activation.json  (THE STORE FREEZE point:
                      stores commit here, BEFORE any transfer request)
  --phase P           pilot: seeds {6001,6002}; R0/R1/R2/R3 on TR+GC;
                      RBAD/RGOLD on the counterfactual subset
                      (results/CONT-006-PILOT/)
  --phase C           confirmatory: seeds {6003..6007}; R0/R1/R2/R3 on TR+GC
                      (results/CONT-006-CONFIRMATORY/; the analysis combines
                      the pilot seeds — single freeze)

Working core granite-code:8b (digest 36c3c3b9683b); arms per the runner's
R0/R1/R2/R3/RBAD/RGOLD wiring (R1 = byte-stable reflection.py MVP over the
frozen calibration self-model; R2/R3/RBAD/RGOLD = the lesson channel).
Lesson stores are PINNED BY DIGEST per phase: R2/R3 read the ACTIVE stores
(after Phase V-activate); RBAD/RGOLD read counterfactual-lessons.json.

Preflight re-verifies the freeze digests fail-closed BEFORE any inference;
--preflight-only is the gate's no-inference check. Wall accounting per
template §5 (cells.json derived; per-arm-seed summaries are the audit
path). Resume per PB-075 (completed arm-seeds skipped verbatim; attempts
kept as evidence). Budget stops per PROCESS rule 6.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.events import EventJournal  # noqa: E402
from continuity.fixtures import load_suite_for_seed  # noqa: E402
from continuity.lessons import (  # noqa: E402
    LessonChannel, empty_store, load_store, make_store, save_store,
    validate_candidate, CorpusIndex)
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.reflection import ReflectionEngine  # noqa: E402
from continuity.runner import Budget, run_scenario  # noqa: E402

SUITE_DIR = LAB_ROOT / "fixtures" / "v3l"
FREEZE_MANIFEST = LAB_ROOT / "experiments" / "suite-v3" / "frozen-config-cont006.json"
CORPUS_MANIFEST = LAB_ROOT / "experiments" / "cont006" / "experience-corpus-manifest.json"
CF_LESSONS = LAB_ROOT / "experiments" / "cont006" / "counterfactual-lessons.json"
SELFMODEL = (LAB_ROOT / "results" / "CONT-001-confirmatory" /
             "cont001-confirmatory-20261002-005711" / "selfmodel-v2-calibration.json")

ALL_SEEDS = [6001, 6002, 6003, 6004, 6005, 6006, 6007]
PILOT_SEEDS = [6001, 6002]
VAL_IDS = ["cr-6005", "cu-6105", "rt-6204", "dx-6403"]
TR_IDS = ["cr-6001", "cr-6002", "cr-6003", "cr-6004", "cu-6101", "cu-6102",
          "cu-6103", "cu-6104", "rt-6201", "rt-6202", "rt-6203", "dx-6401",
          "dx-6402", "dr-6301", "dr-6302"]
CF_SUBSET = ["cr-6001", "cr-6003", "rt-6201", "rt-6202", "cu-6101",
             "dx-6401", "dr-6301", "gc-6501"]  # incl. gc-6501 (telemetry-only use)
MAIN_ARMS = ["R0", "R1", "R2", "R3"]

WORKING_MODEL = "granite-code:8b"
WORKING_DIGEST_PREFIX = "36c3c3b9683b"
REFLECTOR_MODEL = "qwen36-35b-a3b:mdlslab"
REFLECTOR_DIGEST_PREFIX = "8a0fd5da454e"
OLLAMA_VERSION_PREFIX = "0.34"

TEMPERATURE = 0.0
NUM_CTX = 4096
NUM_PREDICT = 256
KEEP_ALIVE = "30m"
TIMEOUT_S = 300
BUDGET_PER_ARM_SEED = dict(max_turns=130, max_total_tokens=400_000, wall_clock_s=5400.0)
WALL_GUARD_S = 270 * 60  # no NEW arm-seed starts after this (cap 5 h declared)
ACTIVATION_THRESHOLD = 0.05

RESULTS = LAB_ROOT / "results"
GC_IDS = ["gc-6501", "gc-6502", "gc-6503"]
FROZEN_PATHS = [
    "docs/EVALUATION-PREP-CONT006.md",
    "docs/CONT-006-DESIGN.md",
    "docs/PR-REVIEW-CONT006.md",
    "docs/PREREG-REQUIREMENTS-V2.md",
    "docs/SUITE-V3-DESIGN.md",
    "docs/CONT006-TAXONOMY.md",
    "experiments/cont006/experience-corpus-manifest.json",
    "experiments/cont006/select_experience_corpus.py",
    "experiments/cont006/counterfactual-lessons.json",
    "experiments/cont006/check_counterfactual_lessons.py",
    "experiments/cont006/revalidate_stores.py",
    "experiments/suite-v3/validate_fixtures_v3.py",
    "experiments/suite-v3/build_v3l.py",
    "experiments/suite-v3/run_cont006.py",
    "experiments/suite-v3/analyze_pilot_cont006.py",
    "experiments/suite-v3/analyze_confirmatory_cont006.py",
    "experiments/suite-v3/power_calc_cont006.py",
    "experiments/suite-v3/power-results-cont006.json",
    "experiments/suite-v3/fixture-validation-v3l.json",
    "src/continuity/runner.py",
    "src/continuity/provider.py",
    "src/continuity/memory.py",
    "src/continuity/fixtures.py",
    "src/continuity/events.py",
    "src/continuity/claims.py",
    "src/continuity/lessons.py",
    "src/continuity/reflection_v2.py",
    "src/continuity/reflection.py",  # R1 baseline byte-stability witness
    "results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711/selfmodel-v2-calibration.json",
]
DETERMINISM_CAVEAT = ("greedy+seed does not guarantee identical outputs "
                      "(PB-071, CN-003); per-seed content variants make seeds "
                      "true replicates regardless")


def file_digest(rel: str) -> str:
    return hashlib.sha256((LAB_ROOT / rel).read_bytes()).hexdigest()


def suite_digest() -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in SUITE_DIR.rglob("*") if p.is_file()):
        h.update(path.relative_to(SUITE_DIR).as_posix().encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def rendered_seed_digest(seed: int) -> str:
    _, scenarios = load_suite_for_seed(str(SUITE_DIR), seed)
    h = hashlib.sha256()
    for scenario in sorted(scenarios, key=lambda s: s["id"]):
        h.update(json.dumps(scenario, sort_keys=True, ensure_ascii=True).encode("utf-8"))
    return h.hexdigest()


def content_digests() -> dict[str, str]:
    d = {f"fixtures/v3l_rendered_seed{sd}": rendered_seed_digest(sd) for sd in ALL_SEEDS}
    d["fixtures/v3l_suite"] = suite_digest()
    return d


def emit_freeze_manifest() -> None:
    manifest = {
        "kind": "cont006-freeze-manifest",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prereg": "docs/EVALUATION-PREP-CONT006.md (owner-accepted 2026-10-08)",
        "seeds": {"all": ALL_SEEDS, "pilot": PILOT_SEEDS,
                  "validation_clusters": VAL_IDS, "cf_subset": CF_SUBSET},
        "models": {
            "working_core": {"name": WORKING_MODEL, "digest_prefix": WORKING_DIGEST_PREFIX},
            "reflector": {"name": REFLECTOR_MODEL, "digest_prefix": REFLECTOR_DIGEST_PREFIX,
                          "options": "worker options frozen in reflection_v2.WORKER_OPTIONS"},
        },
        "environment_pin": {"ollama_version_prefix": OLLAMA_VERSION_PREFIX},
        "execution": {
            "phase_order": ["W", "G-validate", "V", "V-activate", "P", "C"],
            "arms": {"R0": "flat memory", "R1": "MVP reflection (byte-stable)",
                     "R2": "worker store via lesson channel",
                     "R3": "gold store via lesson channel",
                     "RBAD": "counterfactual BAD", "RGOLD": "counterfactual GOLD-TRIV"},
            "temperature": TEMPERATURE, "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT, "keep_alive": KEEP_ALIVE,
            "wall_guard_s": WALL_GUARD_S, "declared_gpu_cap_s": 300 * 60,
            "budget_per_arm_seed": BUDGET_PER_ARM_SEED,
            "activation_threshold": ACTIVATION_THRESHOLD,
        },
        "digests": content_digests() | {rel: file_digest(rel) for rel in FROZEN_PATHS},
    }
    FREEZE_MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=True) + "\n",
                               encoding="utf-8")
    print(f"freeze manifest written: {FREEZE_MANIFEST} ({len(manifest['digests'])} digests)")


def verify_freeze_digests() -> dict:
    if not FREEZE_MANIFEST.exists():
        raise SystemExit(f"FAIL-CLOSED: freeze manifest missing: {FREEZE_MANIFEST}")
    frozen = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))["digests"]
    for key, expected in content_digests().items():
        if frozen.get(key) != expected:
            raise SystemExit(f"FAIL-CLOSED: digest mismatch {key}")
    for rel in FROZEN_PATHS:
        if frozen.get(rel) != file_digest(rel):
            raise SystemExit(f"FAIL-CLOSED: digest mismatch for {rel}")
    return frozen


def preflight(base_url: str) -> dict:
    verify_freeze_digests()
    print("freeze digests verified (byte-match)")
    probe = OllamaProvider(base_url=base_url, model=WORKING_MODEL)
    version = probe.version()
    with urllib.request.urlopen(base_url + "/api/tags", timeout=30) as response:
        tags = [m.get("name", "") for m in json.loads(response.read().decode())["models"]]
    for model in (WORKING_MODEL, REFLECTOR_MODEL):
        if model not in tags:
            raise SystemExit(f"FAIL-CLOSED: model {model!r} missing (tags: {tags})")
    warmups = {}
    for model, prefix in ((WORKING_MODEL, WORKING_DIGEST_PREFIX),
                          (REFLECTOR_MODEL, REFLECTOR_DIGEST_PREFIX)):
        warm = OllamaProvider(base_url=base_url, model=model, temperature=TEMPERATURE,
                              seed=0, num_ctx=NUM_CTX, keep_alive=KEEP_ALIVE,
                              timeout_s=TIMEOUT_S)
        t0 = time.monotonic()
        warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
        warmups[model] = round(time.monotonic() - t0, 1)
        pin = OllamaProvider(base_url=base_url, model=model)
        info = pin.model_info()
        if not info.get("digest", "").startswith(prefix):
            raise SystemExit(f"FAIL-CLOSED: {model} digest {info.get('digest')!r} != {prefix!r}")
    return {"ollama_version": version,
            "ollama_version_prefix_ok": version.startswith(OLLAMA_VERSION_PREFIX),
            "warmup_s": warmups, "determinism_caveat": DETERMINISM_CAVEAT}


# ----------------------------------------------------------------------------
# arm-seed execution (Phases V/P/C)
# ----------------------------------------------------------------------------

def lesson_channel_for(arm: str, store_dir: Path | None,
                       store_kind: str) -> LessonChannel | None:
    """R2/R3 store resolution: Phase V injects the EVIDENCE-VALIDATED stores
    (activation is being measured); Phases P/C inject the ACTIVE stores
    (frozen at V-activate). Counterfactual arms always load
    counterfactual-lessons.json (digest-frozen at the PR-REVIEW fold)."""
    if arm in ("R2", "R3"):
        assert store_dir is not None, f"{arm} needs a lesson store dir"
        if store_kind == "active":
            path = store_dir / f"active-store-{arm.lower()}.json"
        else:
            path = store_dir / f"{arm.lower()}-store-evidence-validated.json"
        return LessonChannel.from_file(path)
    if arm == "RBAD":
        payload = json.loads(CF_LESSONS.read_text(encoding="utf-8"))
        return LessonChannel(make_store([payload["lessons"]["BAD"]],
                                        source="counterfactual", status="active"))
    if arm == "RGOLD":
        payload = json.loads(CF_LESSONS.read_text(encoding="utf-8"))
        return LessonChannel(make_store([payload["lessons"]["GOLD-TRIV"]],
                                        source="counterfactual", status="active"))
    return None


def run_arm_seed(arm: str, seed: int, scenario_ids: list[str], scenarios: list[dict],
                 out_dir: Path, run_id: str, base_url: str,
                 store_dir: Path | None, store_kind: str) -> dict[str, Any]:
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = OllamaProvider(base_url=base_url, model=WORKING_MODEL,
                              temperature=TEMPERATURE, seed=seed, num_ctx=NUM_CTX,
                              num_predict=NUM_PREDICT, keep_alive=KEEP_ALIVE,
                              timeout_s=TIMEOUT_S)
    memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    assert memory.count() == 0, "arm-seed must start from a verified-empty store"
    journal = EventJournal(str(out_dir / "trace.jsonl"), f"{run_id}-{arm}-seed{seed}")
    lessons = lesson_channel_for(arm, store_dir, store_kind)
    selfmodel = None
    reflection = None
    if arm == "R1":
        reflection = ReflectionEngine(
            selfmodel_path=str(SELFMODEL), memory=memory, journal=journal,
            run_seed=seed,
            source_artifact="results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711/selfmodel-v2-calibration.json")
        selfmodel = reflection.model
    by_id = {s["id"]: s for s in scenarios}
    plan = [by_id[sid] for sid in sorted(scenario_ids) if sid in by_id]
    probes: list[dict] = []
    budget = Budget(**BUDGET_PER_ARM_SEED)
    stopped_any = False
    t0 = time.monotonic()
    try:
        for scenario in plan:
            result = run_scenario(scenario, provider, journal, budget, arm=arm,
                                  memory=memory, selfmodel=selfmodel,
                                  reflection=reflection, lessons=lessons)
            stopped_any = stopped_any or bool(result.get("stopped"))
            probes.extend({**p, "scenario": scenario["id"], "family": scenario["family"]}
                          for p in result["probes"])
        wall_s = round(time.monotonic() - t0, 1)
        summary = {
            "kind": "cont006-arm-seed-summary", "run_id": run_id, "arm": arm,
            "seed": seed, "model": WORKING_MODEL,
            "lesson_store_sha256": lessons.digest if lessons else None,
            "lesson_store_status": lessons.status if lessons else None,
            "probes": probes,
            "probes_passed": sum(1 for p in probes if p.get("passed") is True),
            "probes_total": len(probes),
            "stopped": stopped_any, "budget_violation": budget.violation,
            "memory_episodes": memory.count(), "duration_s": wall_s,
            "completed": True, "determinism_caveat": DETERMINISM_CAVEAT,
        }
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
        return summary
    finally:
        journal.close()
        memory.close()


def arm_seed_complete(out_dir: Path) -> bool:
    marker = out_dir / "summary.json"
    if not marker.exists():
        return False
    try:
        return bool(json.loads(marker.read_text(encoding="utf-8")).get("completed"))
    except Exception:
        return False


def run_transfer_phase(phase: str, arms: list[str], seeds: list[int],
                       scenario_ids: list[str], base_url: str,
                       store_dir: Path | None, store_kind: str,
                       resume_root: Path | None, gc_trim: bool = False) -> Path:
    ts = time.strftime("%Y%m%d-%H%M%S")
    folder = {"V": "CONT-006-VAL", "P": "CONT-006-PILOT", "C": "CONT-006-CONFIRMATORY"}[phase]
    if resume_root is not None:
        out_root = resume_root
        run_id = out_root.name
    else:
        run_id = f"cont006-{phase.lower()}-{ts}"
        out_root = RESULTS / folder / run_id
    out_root.mkdir(parents=True, exist_ok=True)
    env = preflight(base_url)
    env.update({"run_id": run_id, "phase": phase, "arms": arms, "seeds": seeds,
                "scenario_ids": scenario_ids, "store_kind": store_kind,
                "store_dir": str(store_dir) if store_dir else None,
                "gc_trim": gc_trim})
    (out_root / "env.json").write_text(json.dumps(env, indent=1, ensure_ascii=True) + "\n",
                                       encoding="utf-8")
    print(f"{run_id}: arms={arms} seeds={seeds} scenarios={len(scenario_ids)}")
    t_start = time.monotonic()
    cells: dict[str, Any] = {"kind": "cont006-cells", "run_id": run_id,
                             "phase": phase, "derived": True, "cells": {}}
    existing_cells = out_root / "cells.json"
    if existing_cells.exists():  # resume/merge (counterfactual arms share the root)
        try:
            cells["cells"].update(json.loads(
                existing_cells.read_text(encoding="utf-8")).get("cells", {}))
        except Exception:
            pass
    gc_ids = set(GC_IDS)
    for arm in arms:
        for seed in seeds:
            if time.monotonic() - t_start > WALL_GUARD_S:
                print(f"WALL GUARD: stopping before {arm} seed {seed}", file=sys.stderr)
                cells["wall_guard_fired"] = True
                break
            ids = scenario_ids
            if gc_trim and seed not in (6001, 6002, 6003, 6004):
                ids = [i for i in ids if i not in gc_ids]
            _, scenarios = load_suite_for_seed(str(SUITE_DIR), seed)
            attempt = 1
            out_dir = out_root / arm / f"seed-{seed}"
            while attempt < 3:
                if arm_seed_complete(out_dir):
                    break
                attempt_dir = out_dir if attempt == 1 else out_root / arm / f"seed-{seed}-a{attempt}"
                if attempt_dir.exists():
                    shutil.rmtree(attempt_dir, ignore_errors=True)
                try:
                    run_arm_seed(arm, seed, ids, scenarios, attempt_dir,
                                 run_id, base_url, store_dir, store_kind)
                    out_dir = attempt_dir
                    break
                except Exception as exc:
                    print(f"{arm} seed {seed} attempt {attempt} failed: {exc}",
                          file=sys.stderr)
                    attempt += 1
            if arm_seed_complete(out_dir):
                s = json.loads((out_dir / "summary.json").read_text(encoding="utf-8"))
                cells["cells"][f"{arm}/seed-{seed}"] = {
                    "wall_s": s["duration_s"], "attempts": attempt,
                    "probes_total": s["probes_total"], "probes_passed": s["probes_passed"],
                    "lesson_store_sha256": s.get("lesson_store_sha256")}
                print(f"  {arm}/seed-{seed}: {s['probes_passed']}/{s['probes_total']} "
                      f"probes, {s['duration_s']}s")
            else:
                cells["cells"][f"{arm}/seed-{seed}"] = {"completed": False, "attempts": attempt}
                print(f"  {arm}/seed-{seed}: INCOMPLETE", file=sys.stderr)
    cells["total_wall_s"] = round(time.monotonic() - t_start, 1)
    (out_root / "cells.json").write_text(
        json.dumps(cells, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"phase {phase} complete: {out_root} (wall {cells['total_wall_s']}s)")
    return out_root


# ----------------------------------------------------------------------------
# Phase V-activate (deterministic; THE store freeze)
# ----------------------------------------------------------------------------

def phase_v_activate(val_root: Path) -> dict:
    def rates(arm: str) -> tuple[float | None, int, int]:
        """FIX-S (GATE-CONT006-VFIX): a VAL probe is INVALID iff MISSING
        (no summary / not completed / probe count != expected) or MALFORMED
        (record without kind/scenario/passed). A format-miss reply
        (observed_label None, passed False) is a VALID scored observation
        (prereg §14 category). Applied SYMMETRICALLY to R0 and the lesson
        arms (closes the VF-3 guard gap)."""
        passed = total = invalid = 0
        for seed in ALL_SEEDS:
            summary = val_root / arm / f"seed-{seed}" / "summary.json"
            if not summary.exists():
                return None, total, invalid
            data = json.loads(summary.read_text(encoding="utf-8"))
            if not data.get("completed"):
                return None, total, invalid
            probes = [p for p in data.get("probes", [])
                      if p.get("kind") != "guess_calibration"]
            if len(probes) != len(VAL_IDS):
                return None, total, invalid
            for p in probes:
                if not {"kind", "scenario", "passed"} <= set(p):
                    invalid += 1
                    continue
                total += 1
                passed += 1 if p.get("passed") is True else 0
        return (passed / total if total else None), total, invalid

    s0, n0, inv0 = rates("R0")
    result = {"kind": "cont006-activation", "val_root": str(val_root),
              "threshold": ACTIVATION_THRESHOLD, "arms": {}}
    if s0 is None:
        raise SystemExit("FAIL-CLOSED: R0 validation runs incomplete — activation "
                         "cannot run (missing-run handling: fail-closed)")
    for arm, ev_path in (("R2", val_root / "r2-store-evidence-validated.json"),
                         ("R3", val_root / "r3-store-evidence-validated.json")):
        sx, nx, invx = rates(arm)
        store = load_store(ev_path) if ev_path.exists() else None
        if store is None:
            raise SystemExit(f"FAIL-CLOSED: evidence-validated store missing: {ev_path}")
        if sx is None or invx > 0:
            # Fail-closed missing/invalid handling (prereg 7.2): any missing
            # or invalid VAL probe blocks activation of that store.
            activated = False
            note = ("fail-closed: lesson-arm validation runs incomplete"
                    if sx is None else
                    f"fail-closed: {invx} invalid VAL probe(s); store not activated")
        else:
            diff = sx - s0
            activated = diff >= ACTIVATION_THRESHOLD
            note = (f"SX-S0 = {diff:.4f} ({sx:.4f} vs {s0:.4f}, n={nx}); "
                    f"{'ACTIVATE' if activated else 'do not activate'}"
                    + ("; active-harm signal (<= -0.05)" if diff <= -ACTIVATION_THRESHOLD else ""))
        active = make_store(store["lessons"] if activated else [],
                            source=store["source"],
                            status="active" if activated else "empty")
        out = val_root / f"active-store-{arm.lower()}.json"
        digest = save_store(active, out)
        result["arms"][arm] = {"activated": activated, "note": note,
                               "active_store": out.name, "active_store_sha256": digest,
                               "s0": round(s0, 4), "sx": round(sx, 4) if sx is not None else None,
                               "invalid_probes": invx}
    val_root_join = val_root / "activation.json"
    val_root_join.write_text(json.dumps(result, indent=1, ensure_ascii=True) + "\n",
                             encoding="utf-8")
    print(json.dumps(result["arms"], indent=1))
    print(f"STORE FREEZE: active stores written under {val_root} "
          f"(BEFORE any transfer request — prereg §6/§7.2)")
    return result


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(description="CONT-006 phased run (frozen)")
    parser.add_argument("--phase", choices=["W", "G-validate", "V", "V-activate",
                                            "P", "C", "preflight"], required=True)
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--freeze-manifest", action="store_true")
    parser.add_argument("--preflight-only", action="store_true")
    parser.add_argument("--resume-root", default=None)
    parser.add_argument("--worker-dir", default=None,
                        help="Phase W output dir (for G/V wiring)")
    parser.add_argument("--r3-candidates", default=None,
                        help="Phase G-validate: path to the blind-authored candidates JSON")
    parser.add_argument("--val-root", default=None,
                        help="Phase V-activate: the Phase V run root")
    parser.add_argument("--active-dir", default=None,
                        help="Phase P/C: dir with active-store-r2/r3.json")
    parser.add_argument("--gc-trim", action="store_true",
                        help="pre-declared droppable-secondary trim: GC scenarios "
                             "run only on seeds 6001..6004 (primary untouchable)")
    args = parser.parse_args()

    if args.freeze_manifest:
        emit_freeze_manifest()
        return 0
    if args.phase == "preflight" or args.preflight_only:
        env = preflight(args.base_url)
        print(json.dumps(env, indent=1, ensure_ascii=True))
        print("PREFLIGHT-ONLY OK (no inference performed)")
        return 0

    if args.phase == "W":
        from continuity.reflection_v2 import run_worker
        ts = time.strftime("%Y%m%d-%H%M%S")
        out_dir = RESULTS / "CONT-006-WORKER" / f"cont006-worker-{ts}"
        verify_freeze_digests()
        # reflector pin: warm then digest (CN-001 order)
        warm = OllamaProvider(base_url=args.base_url, model=REFLECTOR_MODEL,
                              temperature=0.0, seed=0, num_ctx=8192,
                              keep_alive=KEEP_ALIVE, timeout_s=600)
        warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
        info = OllamaProvider(base_url=args.base_url, model=REFLECTOR_MODEL).model_info()
        if not info.get("digest", "").startswith(REFLECTOR_DIGEST_PREFIX):
            raise SystemExit(f"FAIL-CLOSED: reflector digest {info.get('digest')!r}")
        out_dir.mkdir(parents=True, exist_ok=True)
        telemetry = run_worker(CORPUS_MANIFEST, out_dir, args.base_url)
        print(json.dumps(telemetry, indent=1, ensure_ascii=True))
        print(f"Phase W complete: {out_dir}")
        return 0

    if args.phase == "G-validate":
        if not args.r3_candidates or not args.worker_dir:
            raise SystemExit("--r3-candidates and --worker-dir required")
        candidates_path = Path(args.r3_candidates)
        payload = json.loads(candidates_path.read_text(encoding="utf-8"))
        corpus = CorpusIndex(CORPUS_MANIFEST)
        accepted: list[dict] = []
        records = []
        for les in payload.get("lessons", []):
            lesson = {**les, "createdBy": "gold-author"}
            ok, reasons = validate_candidate(lesson, corpus, accepted)
            if ok:
                lesson["status"] = "evidence-validated"
                accepted.append(lesson)
            records.append({"disposition": "accepted" if ok else "rejected",
                            "reasons": reasons, "lesson": lesson})
        out = Path(args.worker_dir) / "r3-store-evidence-validated.json"
        store = make_store(accepted, source="gold-author", status="evidence-validated")
        digest = save_store(store, out)
        report = {"kind": "cont006-r3-validation",
                  "candidates": len(records),
                  "accepted": len(accepted),
                  "records": records,
                  "store_sha256": digest}
        (Path(args.worker_dir) / "r3-validation.json").write_text(
            json.dumps(report, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
        print(f"R3: {len(accepted)}/{len(records)} candidates evidence-validated; "
              f"store {digest[:12]}… -> {out}")
        return 0

    if args.phase == "V":
        if not args.worker_dir:
            raise SystemExit("Phase V needs --worker-dir (evidence-validated stores)")
        root = run_transfer_phase("V", ["R0", "R2", "R3"], ALL_SEEDS, VAL_IDS,
                                  args.base_url, store_dir=Path(args.worker_dir).resolve(),
                                  store_kind="evidence", resume_root=_opt(args.resume_root))
        # copy the evidence-validated stores into the val root for activation
        if args.worker_dir:
            for name in ("r2-store-evidence-validated.json",
                         "r3-store-evidence-validated.json"):
                src = Path(args.worker_dir) / name
                if src.exists():
                    shutil.copy2(src, root / name)
        return 0

    if args.phase == "V-activate":
        if not args.val_root:
            raise SystemExit("--val-root required")
        phase_v_activate(Path(args.val_root).resolve())
        return 0

    if args.phase == "P":
        active = Path(args.active_dir).resolve() if args.active_dir else None
        if active is None or not (active / "active-store-r2.json").exists():
            raise SystemExit("FAIL-CLOSED: Phase P needs --active-dir with the "
                             "frozen ACTIVE stores (run Phase V-activate first)")
        root = _opt(args.resume_root)
        run_transfer_phase("P", MAIN_ARMS, PILOT_SEEDS, TR_IDS + GC_IDS(),
                           args.base_url, store_dir=active, store_kind="active",
                           resume_root=root, gc_trim=args.gc_trim)
        run_transfer_phase("P", ["RBAD", "RGOLD"], PILOT_SEEDS, CF_SUBSET,
                           args.base_url, store_dir=active, store_kind="active",
                           resume_root=root, gc_trim=args.gc_trim)
        return 0

    if args.phase == "C":
        active = Path(args.active_dir).resolve() if args.active_dir else None
        if active is None or not (active / "active-store-r2.json").exists():
            raise SystemExit("FAIL-CLOSED: Phase C needs --active-dir with the "
                             "frozen ACTIVE stores")
        run_transfer_phase("C", MAIN_ARMS, [s for s in ALL_SEEDS if s not in PILOT_SEEDS],
                           TR_IDS + GC_IDS(), args.base_url, store_dir=active,
                           store_kind="active", resume_root=_opt(args.resume_root),
                           gc_trim=args.gc_trim)
        return 0
    return 0


def _opt(value: str | None) -> Path | None:
    return Path(value).resolve() if value else None


if __name__ == "__main__":
    raise SystemExit(main())
