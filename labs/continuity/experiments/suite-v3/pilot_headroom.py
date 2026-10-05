"""CONT-005 headroom pilot: arms A / T0 / T2 over fixture suite v3 (label-form).

Zero-inference design gates already passed (fixture validator V1-V13 PASS,
assembly gate G1-G6 PASS). This pilot is the first GPU touch of suite v3 and
the T-arms; its job is HEADROOM, not confirmation (exploratory, pilot scale):

  X1  guessing baseline: on guess_calibration probes (never-stated facts) the
      reply is a valid label ~always and the position distribution is not
      concentrated (no positional artifact) - across arms equally (no memory
      advantage possible: the facts were never stated).
  X2  the v2 floor pathology is gone: no scored family sits at 0.000 in every
      arm (v2 ended with loose RM 1.0 / A 0/70).
  X3  recall anchors behave: delayed_recall/distractor_recall low for arm A,
      clearly higher for T0/T2.
  X4  directional RM signal: strict repeated-mistake (reply == the scripted
      trap) higher for T0 (flat memory) than T2 (trust resolution) on the CR
      sub-types the policy targets - exploratory direction only.

Predeclared: seeds (11, 22, 33), arms (A, T0, T2), model granite-code:8b pinned
by digest prefix (CN-001), temperature 0.0, options in every request (PB-071),
one warm process per arm-seed run (PB-070). Artifacts under
results/CONT-005-PILOT/pilot-headroom-<ts>/<arm>/seed-<n>/: trace.jsonl (primary),
summary.json, env.json, memory.sqlite3 (T-arms). aggregate.json is derived.

Fail-closed preflight (Ollama reachable, model present, digest pinned, warmup).
Wall guard: no NEW arm-seed starts after 50 min (PROCESS.md rule 6).

Usage:
    python labs/continuity/experiments/suite-v3/pilot_headroom.py
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import statistics
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
from continuity.fixtures import load_suite  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.provider import OllamaProvider, ProviderError  # noqa: E402
from continuity.runner import Budget, run_scenario  # noqa: E402

TRANSIENT = (TimeoutError, ProviderError, OSError)  # one hung/reset Ollama request

# --- Predeclared run configuration ---
SEEDS: tuple[int, ...] = (11, 22, 33)
ARMS: tuple[str, ...] = ("A", "T0", "T2")
MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned since P0a (CN-001)
TEMPERATURE = 0.0
NUM_CTX = 4096
NUM_PREDICT = 256  # CN-011: cap generation; unbounded loops hung requests >300 s
KEEP_ALIVE = "30m"
PILOT_WALL_CLOCK_S = 75 * 60.0  # corrected pre-run: measured ~8 min/arm-seed x 9 = ~72 min
SCENARIO_BUDGET = {"max_turns": 40, "max_total_tokens": 100_000, "wall_clock_s": 600.0}
DETERMINISM_CAVEAT = "greedy+seed does not guarantee identical outputs (PB-071, CN-003)"

EXPECTATIONS_EX_ANTE = [
    "X1 guess probes: valid-label fraction >= 0.9, max position share <= 0.5, equal across arms",
    "X2 no scored family at 0.000 in every arm (v2 floor pathology gone)",
    "X3 DR/DX: arm A low, T0/T2 clearly higher (recall anchors)",
    "X4 strict RM(reply == scripted trap): T0 > T2 directionally on policy-targeted CR sub-types",
]


def git_rev() -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=str(LAB_ROOT), stderr=subprocess.DEVNULL
        ).decode().strip()
    except Exception:
        return "unknown"


def preflight(base_url: str) -> dict[str, Any]:
    probe = OllamaProvider(base_url=base_url, model=MODEL)
    try:
        version = probe.version()
    except Exception as exc:
        print(f"FAIL-CLOSED: Ollama unreachable at {base_url}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    with urllib.request.urlopen(base_url + "/api/tags", timeout=30) as response:
        tags = [m.get("name", "") for m in json.loads(response.read().decode())["models"]]
    if MODEL not in tags:
        print(f"FAIL-CLOSED: model {MODEL!r} missing (tags: {tags})", file=sys.stderr)
        raise SystemExit(2)
    warm = OllamaProvider(base_url=base_url, model=MODEL, temperature=TEMPERATURE,
                          seed=0, num_ctx=NUM_CTX, keep_alive=KEEP_ALIVE)
    t0 = time.monotonic()
    warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
    warmup_s = round(time.monotonic() - t0, 1)
    pinned = probe.model_info()
    if not pinned.get("digest", "").startswith(EXPECTED_DIGEST_PREFIX):
        print(f"FAIL-CLOSED: digest {pinned.get('digest')!r} != pinned {EXPECTED_DIGEST_PREFIX!r}",
              file=sys.stderr)
        raise SystemExit(2)
    return {"ollama_version": version, "digest": pinned["digest"], "warmup_s": warmup_s}


def run_one(arm: str, seed: int, scenarios: list[dict], out_root: Path, run_id: str,
            base_url: str, env_common: dict[str, Any], attempt: int = 1) -> dict[str, Any]:
    stem = f"seed-{seed}" if attempt == 1 else f"seed-{seed}-a{attempt}"
    out_dir = out_root / arm / stem
    out_dir.mkdir(parents=True, exist_ok=True)
    provider = OllamaProvider(base_url=base_url, model=MODEL, temperature=TEMPERATURE,
                              seed=seed, num_ctx=NUM_CTX, num_predict=NUM_PREDICT,
                              keep_alive=KEEP_ALIVE)
    memory = None
    if arm != "A":
        memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    journal = EventJournal(str(out_dir / "trace.jsonl"), f"{run_id}-{arm}-seed{seed}")
    try:
        return _run_one_body(arm, seed, scenarios, out_dir, out_root, run_id, provider,
                             journal, memory, env_common)
    finally:
        # Release Windows file handles before any caller-side directory moves
        # (run-5 lesson: open journal handle -> PermissionError on rename).
        journal.close()
        if memory is not None:
            memory.close()


def _run_one_body(arm: str, seed: int, scenarios: list[dict], out_dir: Path,
                  out_root: Path, run_id: str, provider: OllamaProvider,
                  journal: EventJournal, memory, env_common: dict[str, Any]) -> dict[str, Any]:
    journal.emit("run.start", {
        "protocol_version": PROTOCOL_VERSION, "kind": "pilot-headroom",
        "pilot_run_id": run_id, "arm": arm, "model": MODEL, "seed": seed,
        "seeds_predeclared": list(SEEDS), "arms_predeclared": list(ARMS),
        "temperature": TEMPERATURE, "num_ctx": NUM_CTX, "keep_alive": KEEP_ALIVE,
        "scenario_order": [s["id"] for s in scenarios], "git_rev": env_common["git_rev"],
        "expectations_ex_ante": EXPECTATIONS_EX_ANTE,
    })
    env_snapshot = {
        "python": platform.python_version(), "platform": platform.platform(),
        "ollama_version": env_common["ollama_version"], "model": MODEL,
        "model_digest": env_common["digest"], "arm": arm, "seed": seed,
        "determinism_caveat": DETERMINISM_CAVEAT,
    }
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(json.dumps(env_snapshot, indent=2), encoding="utf-8")

    started = time.monotonic()
    scenario_summaries: list[dict[str, Any]] = []
    budget_stops = 0
    for scenario in scenarios:
        budget = Budget(**SCENARIO_BUDGET)
        scenario_summaries.append(
            run_scenario(scenario, provider, journal, budget, arm=arm, memory=memory)
        )
        if scenario_summaries[-1]["stopped"]:
            budget_stops += 1
    wall_s = round(time.monotonic() - started, 1)
    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))

    scored = [p for s in scenario_summaries for p in s["probes"] if p["passed"] is not None]
    summary = {
        "run_id": f"{run_id}-{arm}-seed{seed}", "arm": arm, "seed": seed,
        "model": MODEL, "model_digest": pinned["digest"],
        "scenario_summaries": scenario_summaries,
        "probes_passed": sum(1 for p in scored if p["passed"]),
        "probes_total": len(scored),
        "guess_probes": sum(1 for s in scenario_summaries for p in s["probes"] if p["passed"] is None),
        "turns": sum(s["turns"] for s in scenario_summaries),
        "tokens_total": sum(s["tokens_total"] for s in scenario_summaries),
        "budget_stops": budget_stops, "wall_s": wall_s,
    }
    if memory is not None:
        summary["memory_episodes"] = memory.count()
    trace_ok, trace_errors = validate_trace(str(out_dir / "trace.jsonl"))
    summary["trace_schema_valid"] = trace_ok
    summary["trace_validation_errors"] = trace_errors
    summary["completed"] = (not budget_stops) and trace_ok and summary["probes_total"] > 0
    summary["dir"] = f"{arm}/{out_dir.name}"
    journal.emit("run.end", {
        "completed": summary["completed"], "trace_schema_valid": trace_ok,
        "probes_passed": summary["probes_passed"], "probes_total": summary["probes_total"],
        "wall_s": wall_s,
    })
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=True),
                                          encoding="utf-8")
    return summary


def build_aggregate(run_id: str, out_root: Path, scenarios: list[dict],
                    summaries: dict[tuple[str, int], dict], env_common: dict) -> dict:
    fam_of = {s["id"]: s["family"] for s in scenarios}
    sub_of = {s["id"]: s.get("sub_type", "") for s in scenarios}
    trap_of = {s["id"]: s.get("seed_error", {}).get("value", "").lower() for s in scenarios}

    per_arm: dict[str, Any] = {}
    for arm in ARMS:
        fam_pass: dict[str, list[int]] = {}
        rm = {"eligible": 0, "strict_repeat": 0, "incorrect": 0, "by_subtype": {}}
        guess = {"probes": 0, "valid_label": 0, "positions": {}}
        for seed in SEEDS:
            s_sum = summaries[(arm, seed)]
            for sc in s_sum["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is None:  # guess probe
                        guess["probes"] += 1
                        pos = p.get("observed_position")
                        if p.get("observed_label") is not None:
                            guess["valid_label"] += 1
                        if pos is not None:
                            guess["positions"][str(pos)] = guess["positions"].get(str(pos), 0) + 1
                        continue
                    fam_pass.setdefault(sc["family"], []).append(1 if p["passed"] else 0)
        per_arm[arm] = {
            "per_family_pass": {
                f: {"mean": round(statistics.fmean(v), 3), "n": len(v)}
                for f, v in fam_pass.items()
            },
            "guess": {
                **guess,
                "valid_fraction": round(guess["valid_label"] / guess["probes"], 3)
                if guess["probes"] else None,
                "max_position_share": round(
                    max(guess["positions"].values()) / guess["probes"], 3
                ) if guess["positions"] else None,
            },
        }

    # RM strict analysis: reply equals the scripted trap on rm-classed probes
    for arm in ARMS:
        rm = {"eligible": 0, "strict_repeat": 0, "incorrect": 0, "by_subtype": {}}
        for seed in SEEDS:
            s_sum = summaries[(arm, seed)]
            for sc in s_sum["scenario_summaries"]:
                sid = sc["scenario"]
                if fam_of.get(sid) not in ("correction_reuse", "repeated_task"):
                    continue
                trap = trap_of.get(sid, "")
                sub = sub_of.get(sid, "")
                slot = rm["by_subtype"].setdefault(
                    sub or fam_of[sid], {"eligible": 0, "strict_repeat": 0, "incorrect": 0}
                )
                for p in sc["probes"]:
                    if p["passed"] is None:
                        continue
                    rm["eligible"] += 1
                    slot["eligible"] += 1
                    if p["observed_normalized"] == trap:
                        rm["strict_repeat"] += 1
                        slot["strict_repeat"] += 1
                    if not p["passed"]:
                        rm["incorrect"] += 1
                        slot["incorrect"] += 1
        rm["strict_rate"] = round(rm["strict_repeat"] / rm["eligible"], 3) if rm["eligible"] else None
        rm["error_rate"] = round(rm["incorrect"] / rm["eligible"], 3) if rm["eligible"] else None
        for slot in rm["by_subtype"].values():
            slot["strict_rate"] = round(slot["strict_repeat"] / slot["eligible"], 3) if slot["eligible"] else None
        per_arm[arm]["rm_primary"] = rm

    runs = [
        {
            "arm": s["arm"], "seed": s["seed"], "dir": s.get("dir", f"{s['arm']}/seed-{s['seed']}"),
            "completed": s["completed"], "trace_schema_valid": s["trace_schema_valid"],
            "budget_stops": s["budget_stops"], "probes_passed": s["probes_passed"],
            "probes_total": s["probes_total"], "guess_probes": s["guess_probes"],
            "turns": s["turns"], "tokens_total": s["tokens_total"],
            "wall_s": s["wall_s"], **({"memory_episodes": s["memory_episodes"]} if "memory_episodes" in s else {}),
        }
        for s in summaries.values()
    ]
    total_wall = round(sum(s["wall_s"] for s in summaries.values()), 1)
    total_tokens = sum(s["tokens_total"] for s in summaries.values())
    return {
        "pilot": {
            "run_id": run_id, "kind": "pilot-headroom", "created_utc":
            time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "git_rev": env_common["git_rev"], "model": MODEL,
            "model_digest": env_common["digest"],
            "ollama_version": env_common["ollama_version"],
            "arms_predeclared": list(ARMS), "seeds_predeclared": list(SEEDS),
            "suite": "fixtures/v3 (27 scenarios, label-form)",
            "expectations_ex_ante": EXPECTATIONS_EX_ANTE,
            "determinism_caveat": DETERMINISM_CAVEAT,
            "gpu_note": "run held the shared gpu lock; wall clock is the GPU metric (CN-002)",
            "total_wall_s": total_wall, "total_tokens": total_tokens,
            "requests_estimated": sum(s["turns"] for s in summaries.values()),
        },
        "runs": runs,
        "per_arm": per_arm,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument(
        "--resume", default=None,
        help="previous pilot run root: arm-seeds with completed summary.json are "
             "copied (zero repeated inference); the rest run into the new root",
    )
    args = parser.parse_args()

    manifest, scenarios = load_suite(str(LAB_ROOT / "fixtures" / "v3"))
    total_turns = sum(len(sess["turns"]) for s in scenarios for sess in s["sessions"])
    print(f"suite v3: {len(scenarios)} scenarios, {total_turns} turns/seed")
    print(f"plan: {len(ARMS)} arms x {len(SEEDS)} seeds = {len(ARMS) * len(SEEDS)} arm-seeds "
          f"({len(ARMS) * len(SEEDS) * total_turns} requests)")

    env_common = preflight(args.base_url)
    env_common["git_rev"] = git_rev()
    print(f"preflight ok: ollama {env_common['ollama_version']}, digest "
          f"{env_common['digest'][:12]}..., warmup {env_common['warmup_s']}s")

    run_id = time.strftime("pilot-headroom-%Y%m%d-%H%M%S")
    out_root = LAB_ROOT / "results" / "CONT-005-PILOT" / run_id
    out_root.mkdir(parents=True, exist_ok=True)

    started = time.monotonic()
    summaries: dict[tuple[str, int], dict] = {}
    skipped: list[str] = []
    resumed: list[str] = []
    if args.resume:
        resume_root = Path(args.resume)
        for arm in ARMS:
            for seed in SEEDS:
                prev = None
                for stem in (f"seed-{seed}", f"seed-{seed}-a2"):
                    candidate = resume_root / arm / stem / "summary.json"
                    if candidate.exists():
                        prev = candidate
                        break
                if prev is None:
                    continue
                prev_summary = json.loads(prev.read_text(encoding="utf-8"))
                if not prev_summary.get("completed"):
                    continue  # incomplete arm-seed re-runs (its trace stays in the old root)
                dest = out_root / arm / prev.parent.name
                shutil.copytree(prev.parent, dest)
                summaries[(arm, seed)] = prev_summary
                resumed.append(f"{arm}/seed-{seed}")
                print(f"resumed {arm}/seed-{seed} from {resume_root.name} (completed, zero repeated inference)")
    for arm in ARMS:
        for seed in SEEDS:
            if (arm, seed) in summaries:
                continue
            elapsed = time.monotonic() - started
            if elapsed > PILOT_WALL_CLOCK_S:
                skipped.append(f"{arm}/seed-{seed}")
                print(f"wall guard hit ({elapsed:.0f}s): skipping {arm}/seed-{seed}",
                      file=sys.stderr)
                continue
            print(f"--- {arm} seed {seed} ({time.strftime('%H:%M:%S')})")
            # Transient-infra hardening (run-4 lesson): a single hung Ollama
            # request kills at most one attempt. Retry the WHOLE arm-seed fresh
            # (clean journal/store) up to once; partials kept as evidence.
            placed = False
            for attempt in (1, 2):
                try:
                    summaries[(arm, seed)] = run_one(arm, seed, scenarios, out_root,
                                                     run_id, args.base_url, env_common,
                                                     attempt=attempt)
                    placed = True
                    break
                except TRANSIENT as exc:
                    # Attempt dirs are attempt-scoped (seed-N, seed-N-a2): the
                    # partial stays where it is as evidence; no renames.
                    msg = f"{arm}/seed-{seed} attempt {attempt} failed: {type(exc).__name__}: {str(exc)[:100]}"
                    if attempt == 1:
                        print(msg + " -> retrying the arm-seed fresh in 15s", file=sys.stderr)
                        time.sleep(15)
                    else:
                        print(msg + " -> giving up on this arm-seed", file=sys.stderr)
            if not placed:
                skipped.append(f"{arm}/seed-{seed} (transient x2)")
                continue
            s = summaries[(arm, seed)]
            print(f"{arm} seed {seed}: scored {s['probes_passed']}/{s['probes_total']} "
                  f"(+{s['guess_probes']} guess), tokens {s['tokens_total']}, "
                  f"wall {s['wall_s']}s, completed={s['completed']}")

    aggregate = build_aggregate(run_id, out_root, scenarios, summaries, env_common)
    aggregate["pilot"]["skipped"] = skipped
    if resumed:
        aggregate["pilot"]["resumed_from"] = str(Path(args.resume).name)
        aggregate["pilot"]["resumed_arm_seeds"] = resumed
    (out_root / "aggregate.json").write_text(json.dumps(aggregate, indent=2, ensure_ascii=True),
                                             encoding="utf-8")
    print(f"\naggregate: {out_root / 'aggregate.json'}")
    for arm in ARMS:
        pa = aggregate["per_arm"][arm]
        fams = ", ".join(f"{f}={v['mean']}" for f, v in sorted(pa["per_family_pass"].items()))
        rm = pa["rm_primary"]
        g = pa["guess"]
        print(f"  {arm}: {fams}")
        print(f"      rm strict {rm['strict_repeat']}/{rm['eligible']} "
              f"(rate {rm['strict_rate']}), errors {rm['error_rate']}; "
              f"guess valid {g['valid_fraction']}, maxpos {g['max_position_share']}")
    ok = all(s["completed"] for s in summaries.values()) and not skipped
    print(f"pilot completed={ok}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
