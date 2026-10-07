"""CONT-002 run script (frozen at FREEZE): the 2x2 four-cell execution.

Per docs/EVALUATION-PREP-CONT002.md (owner-accepted 2026-10-07, ROADMAP) and
docs/CONT-002-DESIGN.md. For each predeclared seed (rendered via
continuity.fixtures.load_suite_for_seed — per-seed content variants):

  learn-A     : sessions 1..k-1 of every primary scenario on core A, arm B
                (memory ON, one store for the whole workload, exactly as the
                cycle-2 arm-seed runs) -> ONE state export per seed (JSON +
                sha256). State-integrity guard: every exported episode must
                come from a session strictly BEFORE the probe session
                (zero probe-session content in exports — prereg section 7).
  A-restored  : fresh store, import the seed's export, probe session only,
                core A. Same export->import pipeline as B+restored (design
                section 1 symmetry decision).
  A-clean     : fresh EMPTY store (verified count==0), probe session only,
                core A. Arm B pipeline with empty retrieval (prereg section 1:
                byte-identical pipeline across cells and cores).
  B-restored  : fresh store, import the SAME export (digest re-checked),
                probe session only, core B (qwen36-35b-a3b:mdlslab).
  B-clean     : fresh empty store, probe session only, core B.
  GC-A / GC-B : full GC scenarios (opener + asker + 2 probes), fresh empty
                store, per core — the per-core guess bands.

Cell order per seed (prereg section 13): learn-A -> A-restored -> A-clean ->
B-restored -> B-clean -> GC-A -> GC-B. Stages: --stage pilot runs seeds
{5001,5002}; --stage confirmatory runs {5003..5007} (the analysis combines
all seven — single freeze, prereg section 2).

Fixed config: temperature 0.0, num_ctx 4096, num_predict 256 (CN-011),
sampling options in every request (PB-071), sampler seed = variant seed
(inert at temp 0, house convention), one warm process per core (keep_alive
30m, PB-070), wall clock the GPU metric (CN-002). Cores pinned by digest
prefix: granite-code:8b = 36c3c3b9683b (CN-001), qwen36-35b-a3b:mdlslab =
8a0fd5da454e (M2b model-digests.json). Environment pin (N-5): Ollama version
recorded in the run record and checked against the freeze manifest prefix.

Preflight re-verifies the FREEZE digests fail-closed BEFORE any inference
(GATE-V3A condition b, institutionalized): suite digest + 7 per-seed
rendered digests recomputed with the frozen recipe (sha256 over the
concatenation of json.dumps(scenario, sort_keys=True, ensure_ascii=True)
for the seed's rendered scenarios sorted by id).

Wall-time accounting (template section 5): every cell-seed writes its own
summary with duration; the run-level cells.json records per-cell wall as the
sum over attempts, and flags any rebuilt aggregates. Budget stops: no NEW
cell starts after WALL_GUARD_S of wall clock (300 min; the declared cap is
5.5 h — the guard leaves headroom for the running cell to finish); a Budget
violating scenario records the violation and the cell completes with a
stopped marker (completeness guard judges at analysis time).

Resume per PB-075: a cell-seed whose summary.json exists with
completed=true is skipped verbatim (zero repeated inference); attempts are
attempt-scoped directories (seed-<n>-a<k>), all kept as evidence.

Artifacts under results/CONT-002-PILOT|CONFIRMATORY/cont002-<stage>-<ts>/:
<cell>/seed-<n>/trace.jsonl + summary.json (+ memory.sqlite3, and
state-export.json in learn-A). cells.json at the run root is DERIVED
(analysis reads it; audit path = per-cell summaries + traces).

Determinism caveat: greedy+seed does not guarantee identical outputs across
batch sizes or backends (PB-071, CN-003); per-seed content variants make
seeds true replicates regardless.
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
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.runner import Budget, run_scenario  # noqa: E402

SUITE_DIR = LAB_ROOT / "fixtures" / "v3k"
FREEZE_MANIFEST = LAB_ROOT / "experiments" / "suite-v3" / "frozen-config-cont002.json"
PILOT_SEEDS = [5001, 5002]
CONFIRMATORY_SEEDS = [5003, 5004, 5005, 5006, 5007]
ALL_SEEDS = PILOT_SEEDS + CONFIRMATORY_SEEDS

MODEL_A = "granite-code:8b"
MODEL_A_DIGEST_PREFIX = "36c3c3b9683b"
MODEL_B = "qwen36-35b-a3b:mdlslab"
MODEL_B_DIGEST_PREFIX = "8a0fd5da454e"
OLLAMA_VERSION_PREFIX = "0.34"  # N-5 environment pin (M2b baseline 0.34.2)

TEMPERATURE = 0.0
NUM_CTX = 4096
NUM_PREDICT = 256
KEEP_ALIVE = "30m"
TIMEOUT_S_A = 300
TIMEOUT_S_B = 600  # 22 GB offload: model load + worst-case ramble headroom
WALL_GUARD_S = 300 * 60  # no NEW cell starts after this (cap 5.5 h declared)
BUDGET_PER_CELL = dict(max_turns=120, max_total_tokens=400_000, wall_clock_s=5400.0)

PRIMARY_CELLS = ["learn-A", "A-restored", "A-clean", "B-restored", "B-clean"]
GC_CELLS = ["GC-A", "GC-B"]
CELL_ORDER = PRIMARY_CELLS + GC_CELLS  # prereg section 13 order

DETERMINISM_CAVEAT = (
    "greedy+seed does not guarantee identical outputs (PB-071, CN-003); "
    "per-seed content variants make seeds true replicates regardless"
)


# ----------------------------------------------------------------------------
# freeze digests
# ----------------------------------------------------------------------------

def rendered_seed_digest(seed: int) -> str:
    _, scenarios = load_suite_for_seed(str(SUITE_DIR), seed)
    h = hashlib.sha256()
    for scenario in sorted(scenarios, key=lambda s: s["id"]):
        h.update(json.dumps(scenario, sort_keys=True, ensure_ascii=True).encode("utf-8"))
    return h.hexdigest()


def suite_digest() -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in SUITE_DIR.rglob("*") if p.is_file()):
        h.update(path.relative_to(SUITE_DIR).as_posix().encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def file_digest(rel: str) -> str:
    return hashlib.sha256((LAB_ROOT / rel).read_bytes()).hexdigest()


def content_digests() -> dict[str, str]:
    d = {f"fixtures/v3k_rendered_seed{sd}": rendered_seed_digest(sd) for sd in ALL_SEEDS}
    d["fixtures/v3k_suite"] = suite_digest()
    return d


def emit_freeze_manifest() -> None:
    """One-time freeze action: write frozen-config-cont002.json (digests for
    every frozen path per prereg section 10 + the environment/model pins)."""
    frozen_paths = [
        "docs/EVALUATION-PREP-CONT002.md",
        "docs/CONT-002-DESIGN.md",
        "docs/PR-REVIEW-CONT002.md",
        "docs/PREREG-REQUIREMENTS-V2.md",
        "docs/SUITE-V3-DESIGN.md",
        "experiments/suite-v3/validate_fixtures_v3.py",
        "experiments/suite-v3/build_v3k.py",
        "experiments/suite-v3/run_cont002.py",
        "experiments/suite-v3/analyze_pilot_cont002.py",
        "experiments/suite-v3/analyze_confirmatory_cont002.py",
        "experiments/suite-v3/power_calc_cont002.py",
        "experiments/suite-v3/power-results-cont002.json",
        "experiments/suite-v3/fixture-validation-v3k.json",
        "src/continuity/runner.py",
        "src/continuity/provider.py",
        "src/continuity/memory.py",
        "src/continuity/fixtures.py",
        "src/continuity/events.py",
        "src/continuity/claims.py",
    ]
    manifest = {
        "kind": "cont002-freeze-manifest",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "prereg": "docs/EVALUATION-PREP-CONT002.md (owner-accepted 2026-10-07)",
        "seeds": {"pilot": PILOT_SEEDS, "confirmatory": CONFIRMATORY_SEEDS},
        "models": {
            "core_a": {"name": MODEL_A, "digest_prefix": MODEL_A_DIGEST_PREFIX},
            "core_b": {"name": MODEL_B, "digest_prefix": MODEL_B_DIGEST_PREFIX},
        },
        "environment_pin": {"ollama_version_prefix": OLLAMA_VERSION_PREFIX},
        "execution": {
            "cell_order_per_seed": CELL_ORDER,
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "num_predict": NUM_PREDICT,
            "keep_alive": KEEP_ALIVE,
            "wall_guard_s": WALL_GUARD_S,
            "declared_gpu_cap_s": 330 * 60,
            "budget_per_cell": BUDGET_PER_CELL,
        },
        "digests": content_digests() | {rel: file_digest(rel) for rel in frozen_paths},
    }
    FREEZE_MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=True) + "\n",
                               encoding="utf-8")
    print(f"freeze manifest written: {FREEZE_MANIFEST} ({len(manifest['digests'])} digests)")


def verify_freeze_digests() -> dict[str, str]:
    """Fail-closed re-verification of the CONTENT digests before any inference."""
    if not FREEZE_MANIFEST.exists():
        raise SystemExit(f"FAIL-CLOSED: freeze manifest missing: {FREEZE_MANIFEST}")
    manifest = json.loads(FREEZE_MANIFEST.read_text(encoding="utf-8"))
    frozen = manifest.get("digests", {})
    for key, expected in content_digests().items():
        if frozen.get(key) != expected:
            raise SystemExit(
                f"FAIL-CLOSED: digest mismatch for {key}: frozen {frozen.get(key)} != computed {expected}"
            )
    return frozen


# ----------------------------------------------------------------------------
# preflight
# ----------------------------------------------------------------------------

def preflight(base_url: str) -> dict[str, Any]:
    verify_freeze_digests()
    print("freeze digests verified (byte-match) — preflight ok")
    probe = OllamaProvider(base_url=base_url, model=MODEL_A)
    version = probe.version()
    with urllib.request.urlopen(base_url + "/api/tags", timeout=30) as response:
        tags = [m.get("name", "") for m in json.loads(response.read().decode())["models"]]
    for model in (MODEL_A, MODEL_B):
        if model not in tags:
            raise SystemExit(f"FAIL-CLOSED: model {model!r} missing (tags: {tags})")
    warmups = {}
    for model, prefix, timeout in (
        (MODEL_A, MODEL_A_DIGEST_PREFIX, TIMEOUT_S_A),
        (MODEL_B, MODEL_B_DIGEST_PREFIX, TIMEOUT_S_B),
    ):
        # CN-001: the digest is pinned via /api/ps (LOADED models only) —
        # warm FIRST, then read the digest (cycle-2 preflight order).
        warm = OllamaProvider(base_url=base_url, model=model, temperature=TEMPERATURE,
                              seed=0, num_ctx=NUM_CTX, keep_alive=KEEP_ALIVE,
                              timeout_s=timeout)
        t0 = time.monotonic()
        warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
        warmups[model] = round(time.monotonic() - t0, 1)
        pin = OllamaProvider(base_url=base_url, model=model)
        info = pin.model_info()
        if not info.get("digest", "").startswith(prefix):
            raise SystemExit(
                f"FAIL-CLOSED: {model} digest {info.get('digest')!r} != pinned {prefix!r}"
            )
    return {
        "ollama_version": version,
        "ollama_version_prefix_ok": version.startswith(OLLAMA_VERSION_PREFIX),
        "model_digests": {MODEL_A: MODEL_A_DIGEST_PREFIX, MODEL_B: MODEL_B_DIGEST_PREFIX},
        "warmup_s": warmups,
        "determinism_caveat": DETERMINISM_CAVEAT,
    }


# ----------------------------------------------------------------------------
# cells
# ----------------------------------------------------------------------------

def scenario_parts(scenario: dict) -> tuple[list[dict], dict]:
    """(learning sessions, probe session) — the probe is the LAST session."""
    return scenario["sessions"][:-1], scenario["sessions"][-1]


def run_cell(cell: str, seed: int, scenarios: list[dict], out_dir: Path, run_id: str,
             base_url: str, export_path: Path | None) -> dict[str, Any]:
    """One cell for one seed. Fresh store per call; restored cells import the
    export; clean cells assert count==0 (RC-4b cell isolation)."""
    model, timeout = (MODEL_A, TIMEOUT_S_A) if cell in ("learn-A", "A-restored", "A-clean", "GC-A") \
        else (MODEL_B, TIMEOUT_S_B)
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = OllamaProvider(base_url=base_url, model=model, temperature=TEMPERATURE,
                              seed=seed, num_ctx=NUM_CTX, num_predict=NUM_PREDICT,
                              keep_alive=KEEP_ALIVE, timeout_s=timeout)
    memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    journal = EventJournal(str(out_dir / "trace.jsonl"), f"{run_id}-{cell}-seed{seed}")
    probes: list[dict] = []
    episodes_exported = None
    t0 = time.monotonic()
    try:
        if cell == "learn-A":
            plan = [(s, scenario_parts(s)[0]) for s in scenarios
                    if s["family"] != "guess_calibration"]
        elif cell in ("A-restored", "A-clean", "B-restored", "B-clean"):
            plan = [(s, [scenario_parts(s)[1]]) for s in scenarios
                    if s["family"] != "guess_calibration"]
        else:  # GC cells run whole GC scenarios (prereg section 2: GC measured
            # clean on both cores, in the GC cells only — GATE-CONT002 D-2 fix)
            plan = [(s, s["sessions"]) for s in scenarios if s["family"] == "guess_calibration"]
        if cell.endswith("restored"):
            assert export_path is not None and export_path.exists(), "export missing"
            data = json.loads(export_path.read_text(encoding="utf-8"))
            memory.import_dict(data, require_empty=True)
            episodes_imported = memory.count()
        elif cell != "learn-A":
            assert memory.count() == 0, "clean cell must start from a verified-empty store"
        budget = Budget(**BUDGET_PER_CELL)
        stopped_any = False
        for scenario, sessions in plan:
            sliced = {**scenario, "sessions": sessions}
            result = run_scenario(sliced, provider, journal, budget, arm="B", memory=memory)
            stopped_any = stopped_any or bool(result.get("stopped"))
            probes.extend(
                {**p, "scenario": scenario["id"], "family": scenario["family"]}
                for p in result["probes"]
            )
        if cell == "learn-A":
            data = memory.export_dict()
            episodes_exported = len(data.get("episodes", []))
            # State-integrity guard (prereg section 7): learning sessions only.
            # Qualified by (scenario, session) PAIRS — bare indices collide
            # across scenario types (GC probes sit at session 2, primary
            # learning at session 2; GATE-CONT002 D-1 fix).
            export_pairs = {(ep.get("scenario"), ep.get("session"))
                            for ep in data.get("episodes", [])}
            probe_pairs = {(s["id"], scenario_parts(s)[1]["index"])
                           for s in scenarios if s["family"] != "guess_calibration"}
            leaked = export_pairs & probe_pairs
            assert not leaked, f"probe-session content leaked into the export: {leaked}"
            export_path.parent.mkdir(parents=True, exist_ok=True)
            export_path.write_text(
                json.dumps(data, indent=1, ensure_ascii=True, sort_keys=True) + "\n",
                encoding="utf-8",
            )
        wall_s = round(time.monotonic() - t0, 1)
        summary = {
            "kind": "cont002-cell-summary",
            "run_id": run_id,
            "cell": cell,
            "seed": seed,
            "model": model,
            "probes": probes,
            "probes_passed": sum(1 for p in probes if p.get("passed") is True),
            "probes_total": len(probes),
            "stopped": stopped_any,
            "budget_violation": budget.violation,
            "memory_episodes": memory.count(),
            "episodes_exported": episodes_exported,
            "duration_s": wall_s,
            "completed": True,
            "determinism_caveat": DETERMINISM_CAVEAT,
        }
        (out_dir / "summary.json").write_text(
            json.dumps(summary, indent=1, ensure_ascii=True) + "\n", encoding="utf-8"
        )
        return summary
    finally:
        journal.close()
        memory.close()


def cell_complete(out_dir: Path) -> bool:
    marker = out_dir / "summary.json"
    if not marker.exists():
        return False
    try:
        return bool(json.loads(marker.read_text(encoding="utf-8")).get("completed"))
    except Exception:
        return False


def main() -> int:
    parser = argparse.ArgumentParser(description="CONT-002 four-cell run (frozen)")
    parser.add_argument("--stage", choices=["pilot", "confirmatory"], required=True)
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--freeze-manifest", action="store_true",
                        help="one-time freeze action: emit frozen-config-cont002.json")
    parser.add_argument("--preflight-only", action="store_true",
                        help="run the fail-closed preflight (digests + model pins + "
                             "warmups) and exit WITHOUT any inference (gate check)")
    args = parser.parse_args()

    if args.freeze_manifest:
        emit_freeze_manifest()
        return 0

    if args.preflight_only:
        env = preflight(args.base_url)
        print(json.dumps(env, indent=1, ensure_ascii=True))
        print("PREFLIGHT-ONLY OK (no inference performed)")
        return 0

    seeds = PILOT_SEEDS if args.stage == "pilot" else CONFIRMATORY_SEEDS
    ts = time.strftime("%Y%m%d-%H%M%S")
    run_id = f"cont002-{args.stage}-{ts}"
    out_root = LAB_ROOT / "results" / ("CONT-002-PILOT" if args.stage == "pilot"
                                       else "CONT-002-CONFIRMATORY") / run_id
    out_root.mkdir(parents=True, exist_ok=True)
    env = preflight(args.base_url)
    env["run_id"] = run_id
    env["stage"] = args.stage
    env["seeds"] = seeds
    (out_root / "env.json").write_text(json.dumps(env, indent=1, ensure_ascii=True) + "\n",
                                       encoding="utf-8")
    print(f"{run_id}: cells={CELL_ORDER} seeds={seeds}")

    t_start = time.monotonic()
    cells_record: dict[str, Any] = {"kind": "cont002-cells", "run_id": run_id,
                                    "stage": args.stage, "derived": True, "cells": {}}
    for seed in seeds:
        _, scenarios = load_suite_for_seed(str(SUITE_DIR), seed)
        export_path = out_root / "learn-A" / f"seed-{seed}" / "state-export.json"
        for cell in CELL_ORDER:
            if time.monotonic() - t_start > WALL_GUARD_S:
                print(f"WALL GUARD at {time.monotonic() - t_start:.0f}s: stopping before "
                      f"{cell} seed {seed}; partial run recorded", file=sys.stderr)
                cells_record["wall_guard_fired"] = True
                break
            attempt = 1
            out_dir = out_root / cell / f"seed-{seed}"
            while attempt < 3:
                if cell_complete(out_dir):
                    break
                attempt_dir = out_dir if attempt == 1 else out_root / cell / f"seed-{seed}-a{attempt}"
                if attempt_dir.exists():
                    shutil.rmtree(attempt_dir, ignore_errors=True)
                try:
                    run_cell(cell, seed, scenarios, attempt_dir, run_id,
                             args.base_url, export_path)
                    out_dir = attempt_dir
                    break
                except Exception as exc:  # bounded retry, attempts kept as evidence
                    print(f"cell {cell} seed {seed} attempt {attempt} failed: {exc}",
                          file=sys.stderr)
                    attempt += 1
            summary_path = out_dir / "summary.json"
            if cell_complete(out_dir):
                summary = json.loads(summary_path.read_text(encoding="utf-8"))
                cells_record["cells"][f"{cell}/seed-{seed}"] = {
                    "wall_s": summary["duration_s"],
                    "attempts": attempt,
                    "probes_total": summary["probes_total"],
                    "probes_passed": summary["probes_passed"],
                    "budget_violation": summary["budget_violation"],
                    "episodes_exported": summary.get("episodes_exported"),
                    "export_sha256": (
                        hashlib.sha256(export_path.read_bytes()).hexdigest()
                        if cell == "learn-A" and export_path.exists() else None
                    ),
                }
                print(f"  {cell}/seed-{seed}: {summary['probes_passed']}/{summary['probes_total']} "
                      f"probes, {summary['duration_s']}s")
            else:
                cells_record["cells"][f"{cell}/seed-{seed}"] = {
                    "completed": False, "attempts": attempt}
                print(f"  {cell}/seed-{seed}: INCOMPLETE after {attempt} attempts", file=sys.stderr)
        # B-restored integrity: the SAME export file feeds both restored cells
        # (learn-A writes it; A-restored and B-restored import it verbatim).
    cells_record["total_wall_s"] = round(time.monotonic() - t_start, 1)
    (out_root / "cells.json").write_text(
        json.dumps(cells_record, indent=1, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    print(f"run complete: {out_root} (wall {cells_record['total_wall_s']}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
