"""Repeated-mistake (RM) analysis over CONT-001 exploratory traces (M6).

Operationalizes the proposal's CONT-001 repeated-mistake endpoint on the
current (v1) suite: per arm/seed and per `repeated_task` scenario,

  - initial answer  = normalized agent answer to the session-1 FIRST task
    turn (s1t1), before the rubric record of s1t2;
  - initial error   = initial answer != INITIAL_EXPECTED (the independently
    labelled correct category for the initial task, derived here from the
    fixture rubric sentence — author-derived mapping, see
    docs/EVALUATION-PREP.md for the v1 mapping table and its limits);
  - eligible        = an initial error exists (only an agent that erred can
    repeat its own mistake; the denominator is the agent's OWN eligible
    subsequent tasks, per the proposal);
  - repeated mistake (strict, primary) = eligible AND the probe answer is
    incorrect AND equals the initial answer (normalized);
  - repeated mistake (loose, sensitivity) = eligible AND probe incorrect
    (any wrong label, not necessarily the same one).

Fixture v1 initial-expected mapping (rubric-textual, recorded once):
  rt-0001 'bug' (crash on export), rt-0002 'billing' (wrong VAT on
  invoice), rt-0003 'perf' (slow but working settings page).

Usage:
    python labs/continuity/experiments/CONT-001/analyze_repeated_mistakes.py \
        --run-root labs/continuity/results/CONT-001-exploratory/<run_id>

Writes repeated-mistake-analysis.{json,md} into the run root.
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity

INITIAL_EXPECTED = {
    "rt-0001": "bug",
    "rt-0002": "billing",
    "rt-0003": "perf",
}

MAPPING_PROVENANCE = (
    "author-derived from the fixture rubric sentences (independently labelled "
    "error categories, docs/research-proposal.md CONT-001); fixture v2 must "
    "carry initial_expected as an explicit fixture field"
)


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def parse_seed_trace(trace_path: Path) -> dict[str, dict[str, Any]]:
    """{scenario: {initial_answer, probe: {observed, passed}}} for rt scenarios."""
    out: dict[str, dict[str, Any]] = {}
    with open(trace_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            sid = record.get("scenario") or ""
            if sid not in INITIAL_EXPECTED:
                continue
            slot = out.setdefault(sid, {"initial_answer": None, "probe": None})
            if record["type"] == "agent.response":
                turn_ref = record["payload"]["turn_ref"]
                if turn_ref == "s1t1":
                    slot["initial_answer"] = normalize(record["payload"]["content"])
            elif record["type"] == "probe.result":
                slot["probe"] = {
                    "observed": record["payload"]["observed_normalized"],
                    "passed": record["payload"]["passed"],
                }
    return out


def analyze_run_root(run_root: Path) -> dict[str, Any]:
    run_root = run_root.resolve()
    rows: list[dict[str, Any]] = []
    for arm_dir in sorted(run_root.glob("arm-*")):
        arm = arm_dir.name.split("-", 1)[1]
        for seed_dir in sorted(arm_dir.glob("seed-*")):
            seed = int(seed_dir.name.split("-", 1)[1])
            for sid, slot in sorted(parse_seed_trace(seed_dir / "trace.jsonl").items()):
                initial = slot["initial_answer"]
                probe = slot["probe"]
                if initial is None or probe is None:
                    rows.append(
                        {
                            "arm": arm, "seed": seed, "scenario": sid,
                            "parse_error": "missing s1t1 answer or probe result",
                        }
                    )
                    continue
                expected_initial = INITIAL_EXPECTED[sid]
                initial_error = initial != expected_initial
                eligible = initial_error
                probe_incorrect = not probe["passed"]
                strict = eligible and probe_incorrect and probe["observed"] == initial
                loose = eligible and probe_incorrect
                rows.append(
                    {
                        "arm": arm,
                        "seed": seed,
                        "scenario": sid,
                        "initial_answer": initial,
                        "initial_expected": expected_initial,
                        "initial_error": initial_error,
                        "eligible": eligible,
                        "probe_observed": probe["observed"],
                        "probe_passed": probe["passed"],
                        "repeated_mistake_strict": strict,
                        "repeated_mistake_loose": loose,
                    }
                )
    per_arm: dict[str, Any] = {}
    for arm in sorted({r["arm"] for r in rows if "arm" in r}):
        arm_rows = [r for r in rows if r.get("arm") == arm and "parse_error" not in r]
        seeds = sorted({r["seed"] for r in arm_rows})
        by_seed: dict[str, dict[str, Any]] = {}
        for seed in seeds:
            srows = [r for r in arm_rows if r["seed"] == seed]
            elig = sum(1 for r in srows if r["eligible"])
            strict = sum(1 for r in srows if r["repeated_mistake_strict"])
            loose = sum(1 for r in srows if r["repeated_mistake_loose"])
            by_seed[str(seed)] = {
                "eligible": elig,
                "repeated_strict": strict,
                "rm_rate_strict": round(strict / elig, 3) if elig else None,
                "repeated_loose": loose,
                "rm_rate_loose": round(loose / elig, 3) if elig else None,
            }
        elig_total = sum(v["eligible"] for v in by_seed.values())
        strict_total = sum(v["repeated_strict"] for v in by_seed.values())
        loose_total = sum(v["repeated_loose"] for v in by_seed.values())
        per_arm[arm] = {
            "seeds": seeds,
            "per_seed": by_seed,
            "pooled": {
                "eligible": elig_total,
                "repeated_strict": strict_total,
                "rm_rate_strict": round(strict_total / elig_total, 3) if elig_total else None,
                "repeated_loose": loose_total,
                "rm_rate_loose": round(loose_total / elig_total, 3) if elig_total else None,
            },
        }

    return {
        "kind": "cont001-exploratory-repeated-mistake-analysis",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_root": str(run_root.relative_to(LAB_ROOT)).replace("\\", "/"),
        "definition": {
            "initial_answer": "normalized agent answer at s1t1 (task before rubric exposure)",
            "initial_expected": INITIAL_EXPECTED,
            "mapping_provenance": MAPPING_PROVENANCE,
            "eligible": "initial answer incorrect per initial_expected (per-agent denominator)",
            "repeated_mistake_strict": "eligible AND probe incorrect AND probe answer == initial answer",
            "repeated_mistake_loose": "eligible AND probe incorrect (sensitivity)",
            "limits": [
                "v1 suite: repeated_task family has only 3 scenarios; rt-0001 is "
                "ineligible for every arm in all pilots so far (no initial error), "
                "leaving an effective denominator of <= 2 scenarios x seeds",
                "CN-004: rt-0003 lists 'perf' among the probe options, which lets a "
                "no-memory agent pass without learning (arm A 5/5) — rt-0003 "
                "understates the memory arms' relative RM and inflates arm A",
                "author-derived initial_expected mapping (see provenance)",
            ],
        },
        "rows": rows,
        "per_arm": per_arm,
    }


def render_markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# CONT-001 exploratory — repeated-mistake rate (M6)",
        "",
        f"- source: `{analysis['run_root']}` (exploratory; NOT confirmatory)",
        "- primary operationalization: strict (probe repeats the agent's own "
        "initial wrong answer); loose variant reported as sensitivity",
        "- denominator: per-arm eligible subsequent tasks (initial error at s1t1 "
        "per the recorded initial_expected mapping)",
        "",
        "| arm | seeds | eligible (pooled) | repeated (strict) | RM rate strict | RM rate loose |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for arm, view in analysis["per_arm"].items():
        pooled = view["pooled"]
        lines.append(
            f"| {arm} | {len(view['seeds'])} | {pooled['eligible']} | "
            f"{pooled['repeated_strict']} | {pooled['rm_rate_strict']} | "
            f"{pooled['rm_rate_loose']} |"
        )
    lines += [
        "",
        "Limits (v1 suite): 3-probe family, rt-0001 typically ineligible "
        "(effective denominator <= 2 scenarios x seeds), CN-004 option leakage "
        "on rt-0003. Full list in the JSON. These are the exploratory numbers "
        "the pre-registration (docs/EVALUATION-PREP.md) is grounded in; the "
        "confirmatory endpoint runs on the held-out fixture v2 per that plan.",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--run-root", required=True,
        help="CONT-001 exploratory run root (contains arm-*/seed-*/trace.jsonl)",
    )
    args = parser.parse_args()
    run_root = Path(args.run_root)
    if not run_root.is_absolute():
        run_root = LAB_ROOT / run_root
    if not run_root.exists():
        print(f"FAIL-CLOSED: run root not found: {run_root}", file=sys.stderr)
        return 2
    analysis = analyze_run_root(run_root)
    (run_root / "repeated-mistake-analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    (run_root / "repeated-mistake-analysis.md").write_text(
        render_markdown(analysis), encoding="utf-8"
    )
    print(f"wrote {run_root / 'repeated-mistake-analysis.md'}")
    for arm, view in analysis["per_arm"].items():
        print(f"  arm {arm}: pooled {view['pooled']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
