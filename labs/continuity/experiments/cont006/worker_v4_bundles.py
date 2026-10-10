"""CONT-006 STAGE 2: BALANCED faithful worker bundles (v4).

Worker_v3 rendering (all env turns verbatim with source_type/actor recovered
positionally; agent replies every turn capped 80 words; full probe questions;
trace/fixture text-mismatch fail-closed) with the SELECTION REPAIRED per
stage-2 brief §3 / audit defect 2: the executed v2/v3 selection was fails-
first over the whole corpus, which drew 97/108 scenario-runs from arm A
(NO-MEMORY) — a fails-first sampling bias, since arm A fails most by design.

V4 selection rule (pre-declared, deterministic):
- grouping identical (fixture-derived family/sub-type groups);
- ranking identical (fails first; scenario-interleaved rank; then
  run/arm/seed/sid);
- selection: greedy in rank order subject to PER-ARM CAP 3 and the total
  cap 12 — no arm contributes more than 3 runs of a bundle, so a full
  bundle spans >= 4 distinct arms and arm A is capped at 25% (vs 90% in
  the executed v3 selection);
- digest budget trim unchanged from v3 (declared, lowest-rank-first from
  the tail, floor 2 runs) — the trim now reports per-arm counts too.

Mechanical gates (main): every bundle digest carries >= 1 "ENV [source:"
line; FULL env coverage (env_lines == env_turns); per-arm balance report;
prompt renders via the frozen bundle_prompt.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from worker_v2_bundles import (  # noqa: E402
    CORPUS, MAX_RUNS_PER_BUNDLE, group_for, scenario_runs)
from worker_v3_bundles import (  # noqa: E402
    MAX_DIGEST_CHARS, faithful_lines, fixture_turns)

PER_ARM_CAP = 3


def build_bundles_v4() -> list[dict]:
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    runs_by_group: dict[str, list[dict]] = {}
    for trace in manifest["traces"]:
        prefix = f"{trace['run']}|{trace['arm']}|seed-{trace['seed']}"
        fx = fixture_turns(trace["run"], trace["seed"])
        for run in scenario_runs(trace):
            name = group_for(run["sid"], run["sub_type"])
            if name is None:
                continue
            runs_by_group.setdefault(name, []).append(
                {**run, "prefix": prefix, "trace_key": prefix, "fx": fx})
    bundles = []
    for name, runs in runs_by_group.items():
        # ranking identical to v2/v3 (fails first; scenario-interleaved)
        runs.sort(key=lambda r: (not r["failed"], r["prefix"], r["sid"]))
        by_sid: dict[str, list[dict]] = {}
        for r in runs:
            by_sid.setdefault(r["sid"], []).append(r)
        ranked = [{**r, "_rank": i}
                  for rs in by_sid.values() for i, r in enumerate(rs)]
        ranked.sort(key=lambda r: (not r["failed"], r["_rank"],
                                   r["prefix"], r["sid"]))
        # V4: greedy rank-order selection under PER_ARM_CAP
        arm_count: Counter[str] = Counter()
        kept = []
        for r in ranked:
            arm = r["prefix"].split("|")[1]
            if len(kept) >= MAX_RUNS_PER_BUNDLE:
                break
            if arm_count[arm] >= PER_ARM_CAP:
                continue
            arm_count[arm] += 1
            kept.append(r)
        digest_lines: list[str] = []
        for r in kept:
            digest_lines.extend(faithful_lines(
                r["prefix"], r["sid"], r["cls"], r["sub_type"],
                r["events"], r["fx"]))
        # declared trim (v3 semantics): drop lowest-ranked kept run from the
        # tail while over budget; never below 2 runs
        trimmed = 0
        while sum(len(l) + 1 for l in digest_lines) > MAX_DIGEST_CHARS \
                and len(kept) > 2:
            r = kept[-1]
            arm_count[r["prefix"].split("|")[1]] -= 1
            removed = faithful_lines(r["prefix"], r["sid"], r["cls"],
                                     r["sub_type"], r["events"], r["fx"])
            digest_lines = digest_lines[:len(digest_lines) - len(removed)]
            kept = kept[:-1]
            trimmed += 1
        digest = "\n".join(digest_lines)
        env_turns_total = sum(
            1 for r in kept for e in r["events"] if e["type"] == "env.turn")
        bundles.append({
            "bundle": name,
            "n_runs": len(kept),
            "n_traces": len({r["trace_key"] for r in kept}),
            "n_scenarios": len({r["sid"] for r in kept}),
            "arm_counts": dict(sorted(arm_count.items())),
            "n_failed_runs": sum(1 for r in kept if r["failed"]),
            "digest": digest,
            "skipped_runs": len(runs) - len(kept) - trimmed,
            "trimmed_for_ctx": trimmed,
            "env_turns_total": env_turns_total,
            "env_lines_total": sum(
                1 for l in digest_lines
                if (" ENV [" in l or " PROBE-Q: " in l)),
        })
    bundles.sort(key=lambda b: b["bundle"])
    return bundles


def main() -> int:
    from continuity.reflection_v2 import bundle_prompt
    bundles = build_bundles_v4()
    probe_prompt = bundle_prompt(bundles[0])
    assert bundles[0]["digest"].splitlines()[0] in probe_prompt
    total_src = 0
    arm_totals: Counter[str] = Counter()
    for b in bundles:
        assert b["env_lines_total"] == b["env_turns_total"], (
            f"gate FAIL: {b['bundle']} env coverage "
            f"{b['env_lines_total']}/{b['env_turns_total']}")
        n_src = sum(1 for l in b["digest"].splitlines() if "ENV [source:" in l)
        total_src += n_src
        arm_totals.update(b["arm_counts"])
        print(f"  {b['bundle']:14s} runs={b['n_runs']:2d} traces={b['n_traces']:2d} "
              f"chars={len(b['digest']):5d} (~{len(b['digest'])//4} tok) "
              f"env={b['env_lines_total']}/{b['env_turns_total']} "
              f"src={n_src} trimmed={b['trimmed_for_ctx']} "
              f"arms={b['arm_counts']} fails={b['n_failed_runs']}")
    cr_src = sum(1 for b in bundles if b["bundle"].startswith("cr")
                 for l in b["digest"].splitlines() if "ENV [source:" in l)
    assert cr_src > 0, "gate FAIL: cr bundles carry no source-marked lines"
    total_runs = sum(b["n_runs"] for b in bundles)
    share_a = arm_totals.get("A", 0) / total_runs
    assert share_a <= 0.30, f"gate FAIL: arm-A share {share_a:.2f} > 0.30"
    print(f"bundles: {len(bundles)}, runs total {total_runs}, "
          f"arm shares: {dict(sorted(arm_totals.items()))} "
          f"(arm A {share_a:.0%}; v3 executed ~90%)")
    print(f"source-marked lines total {total_src} (cr: {cr_src})")
    out = LAB_ROOT / "experiments" / "cont006" / "worker_v4_bundles.json"
    out.write_text(json.dumps(
        {"kind": "cont006-worker-v4-bundles-faithful-balanced",
         "note": "worker_v3 faithful rendering + the V4 BALANCED selection "
                 "(per-arm cap 3, total cap 12, rank order identical to "
                 "v2/v3; repairs audit defect 2 — the executed selection drew "
                 "97/108 runs from arm A). Feeds run_worker_v2 unchanged (the "
                 "W4 driver pins the audited validator V2 via "
                 "lessons_v2.validate_candidate_v2).",
         "bundles": bundles}, indent=1, ensure_ascii=True) + "\n",
        encoding="utf-8")
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
