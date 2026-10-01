"""CONT-001 CONFIRMATORY analysis (M7) — executes docs/EVALUATION-PREP.md
EXACTLY as pre-registered (frozen at commit a845fc5). No post-hoc switches.

Primary endpoint (section 1.1): repeated-mistake (RM) rate.
  - initial answer  = normalized agent reply to s1t1 (session-1 FIRST task
    turn, before the rubric/correction record);
  - initial error   = initial answer != the fixture's initial_expected field
    (v2: an explicit fixture field on s1t1 — no author-derived mapping);
  - eligible        = an initial error occurred (per-arm denominator);
  - RM probes are selected by the fixture marker probe.class == "rm_eligible"
    (section 6.4), not by family name;
  - repeated mistake (strict, primary) = eligible AND probe incorrect AND
    probe answer == the agent's own initial answer (normalized);
  - loose / common-eligible variants are pre-declared sensitivities only.

Primary contrast (section 3): RM(E) - RM(A), two-sided.
Decision rule (section 4): the primary claim is supported iff BOTH the 95%
percentile bootstrap CI excludes 0 AND |point estimate| >= 0.15 (MME);
otherwise "no confirmatory difference established". Underpowered guard:
either arm's pooled eligible denominator < 10 -> inconclusive, no claim.

Uncertainty (section 5): paired cluster bootstrap over scenarios (the
exchangeable unit), 10,000 resamples, percentile 95% CI, RNG seed 20261002.
Both arms recomputed on the SAME resampled scenario set; empty-eligible
resamples redrawn; > 500 redraws (5%) -> eligibility degenerate, halt.

Missing/failed runs (section 8): seed-runs with budget stops, trace
validation failures, or missing probe results are excluded and REPORTED;
> 1 exclusion in any arm, or any scenario missing in >= 3/5 seeds of any
arm -> HALT, inconclusive-with-cause. Contamination checks halt too.

Secondaries (section 3; exploratory-attribution, never promotable):
B-A, C-B, D-C, E-D on RM rate; delayed-recall and contradiction-update
family pass rates for E-A and C-B; token cost per arm; arm-E policy
actuation vs the ex-ante expectation (section 6.7).

Usage:
    python labs/continuity/experiments/CONT-001/analyze_confirmatory.py \
        --run-root labs/continuity/results/CONT-001-confirmatory/<run_id>

Writes repeated-mistake-analysis.{json,md}, secondary-analyses.{json,md},
results-summary.md into the run root. All labeled
"agent-pre-registered, pending owner acceptance".
"""

from __future__ import annotations

import argparse
import json
import random
import re
import statistics
import sys
import time
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import load_suite  # noqa: E402

EVAL_DIR = LAB_ROOT / "fixtures" / "v2"
PREP_DOC = LAB_ROOT / "docs" / "EVALUATION-PREP.md"
LABEL = "agent-pre-registered, pending owner acceptance"

# --- Pre-registered constants (EVALUATION-PREP.md sections 4-5, frozen) ---
MME = 0.15
BOOTSTRAP_RESAMPLES = 10_000
BOOTSTRAP_SEED = 20261002
REDRAW_LIMIT = 500  # 5% of 10,000
UNDERPOWERED_MIN_ELIGIBLE = 10
CONFIRMATORY_SEEDS = (101, 202, 303, 404, 505)
ARMS = ("A", "B", "C", "D", "E")
PRIMARY = ("E", "A")

import hashlib


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def suite_digest(fixture_dir: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in fixture_dir.rglob("*") if p.is_file()):
        h.update(path.relative_to(fixture_dir).as_posix().encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def percentile_ci(values: list[float]) -> tuple[float, float]:
    """Percentile 95% CI (2.5th, 97.5th) with inclusive interpolation."""
    q = statistics.quantiles(values, n=10_000, method="inclusive")
    return round(q[249], 4), round(q[9_749], 4)


# ---------------------------------------------------------------- RM rows


def rm_fixture_index() -> dict[str, dict[str, str]]:
    """{scenario_id: {"initial_expected": ..., "probe_turn": "s2t2"}} for every
    scenario whose single probe carries probe.class == "rm_eligible"."""
    _, scenarios = load_suite(str(EVAL_DIR))
    index: dict[str, dict[str, str]] = {}
    for scenario in scenarios:
        rm_probes = []
        for session in scenario["sessions"]:
            for j, turn in enumerate(session["turns"], start=1):
                if turn.get("probe", {}).get("class") == "rm_eligible":
                    rm_probes.append((f"s{session['index']}t{j}", turn))
        if not rm_probes:
            continue
        assert len(rm_probes) == 1, scenario["id"]
        s1t1 = scenario["sessions"][0]["turns"][0]
        index[scenario["id"]] = {
            "initial_expected": s1t1["initial_expected"],
            "probe_turn": rm_probes[0][0],
            "probe_expected": rm_probes[0][1]["probe"]["expected"],
            "probe_kind": rm_probes[0][1]["probe"]["kind"],
        }
    return index


def parse_seed_trace(trace_path: Path, rm_index: dict[str, dict[str, str]]) -> dict[str, dict[str, Any]]:
    """{scenario: {initial_answer, probe: {observed, passed}}} for RM scenarios."""
    out: dict[str, dict[str, Any]] = {}
    with open(trace_path, "r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            sid = record.get("scenario") or ""
            if sid not in rm_index:
                continue
            slot = out.setdefault(sid, {"initial_answer": None, "probe": None})
            if record["type"] == "agent.response":
                if record["payload"]["turn_ref"] == "s1t1":
                    slot["initial_answer"] = normalize(record["payload"]["content"])
            elif record["type"] == "probe.result":
                if record["payload"]["turn_ref"] == rm_index[sid]["probe_turn"]:
                    slot["probe"] = {
                        "observed": record["payload"]["observed_normalized"],
                        "passed": record["payload"]["passed"],
                    }
    return out


def build_rm_rows(run_root: Path, rm_index: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for arm_dir in sorted(run_root.glob("arm-*")):
        arm = arm_dir.name.split("-", 1)[1]
        for seed_dir in sorted(arm_dir.glob("seed-*")):
            seed = int(seed_dir.name.split("-", 1)[1])
            for sid, slot in sorted(
                parse_seed_trace(seed_dir / "trace.jsonl", rm_index).items()
            ):
                initial = slot["initial_answer"]
                probe = slot["probe"]
                if initial is None or probe is None:
                    rows.append(
                        {"arm": arm, "seed": seed, "scenario": sid,
                         "parse_error": "missing s1t1 answer or probe result"}
                    )
                    continue
                expected_initial = rm_index[sid]["initial_expected"]
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
    return rows


# ------------------------------------------------------- missing-run policy


def exclusion_report(run_root: Path) -> dict[str, Any]:
    """Section 8: identify excluded seed-runs and missing scenarios."""
    exclusions: list[dict[str, Any]] = []
    scenario_missing: dict[str, dict[str, set[int]]] = {}
    planned = {a: list(CONFIRMATORY_SEEDS) for a in ARMS}
    for arm in ARMS:
        for seed in CONFIRMATORY_SEEDS:
            seed_dir = run_root / f"arm-{arm}" / f"seed-{seed}"
            summary_path = seed_dir / "summary.json"
            if not summary_path.exists():
                exclusions.append({"arm": arm, "seed": seed, "reason": "summary.json missing"})
                continue
            s = json.loads(summary_path.read_text(encoding="utf-8"))
            reasons = []
            if s.get("budget_stops"):
                reasons.append(f"budget_stops={s['budget_stops']}")
            if not s.get("trace_schema_valid", False):
                reasons.append("trace validation failure")
            if s.get("probes_total", 0) == 0:
                reasons.append("missing probe results")
            if reasons:
                exclusions.append({"arm": arm, "seed": seed, "reason": "; ".join(reasons)})
            else:
                for ss in s.get("scenario_summaries", []):
                    if ss.get("probes_total", 0) == 0:
                        scenario_missing.setdefault(ss["scenario"], {}).setdefault(arm, set()).add(seed)
    halt_reasons: list[str] = []
    per_arm_excluded = {a: [e for e in exclusions if e["arm"] == a] for a in ARMS}
    for arm, exs in per_arm_excluded.items():
        if len(exs) > 1:
            halt_reasons.append(f"arm {arm} has {len(exs)} excluded seed-runs (> 1): {[(e['seed'], e['reason']) for e in exs]}")
    for sid, per_arm in scenario_missing.items():
        for arm, seeds in per_arm.items():
            if len(seeds) >= 3:
                halt_reasons.append(f"scenario {sid} missing in {len(seeds)}/5 seeds of arm {arm}")
    return {
        "planned": planned,
        "exclusions": exclusions,
        "scenario_missing": {sid: {a: sorted(s) for a, s in per.items()} for sid, per in scenario_missing.items()},
        "halt": bool(halt_reasons),
        "halt_reasons": halt_reasons,
    }


def contamination_checks(run_root: Path) -> list[str]:
    """Section 8 contamination halts + 6.9 freeze discipline."""
    problems: list[str] = []
    frozen_path = run_root / "frozen-config.json"
    if not frozen_path.exists():
        return ["frozen-config.json missing"]
    frozen = json.loads(frozen_path.read_text(encoding="utf-8"))

    prep_sha = sha256_file(PREP_DOC)
    if prep_sha != frozen["protocol"]["evaluation_prep_sha256"]:
        problems.append("EVALUATION-PREP.md edited after freeze")
    if suite_digest(EVAL_DIR) != frozen["fixtures"]["evaluation_suite_sha256"]:
        problems.append("fixtures/v2 edited after freeze")
    if suite_digest(LAB_ROOT / "fixtures" / "v2-calibration") != frozen["fixtures"]["calibration_suite_sha256"]:
        problems.append("fixtures/v2-calibration edited after freeze")

    sm = json.loads((run_root / "selfmodel-v2-calibration.json").read_text(encoding="utf-8"))
    if sm.get("provenance", {}).get("derived_from") != frozen["selfmodel"]["calibration_aggregate_rel"]:
        problems.append("self-model provenance does not point at the calibration artifact")
    cal_agg = json.loads((run_root / frozen["selfmodel"]["calibration_aggregate_rel"]).read_text(encoding="utf-8"))
    cal_ids = set(cal_agg.get("pilot", {}).get("scenario_order", []))
    _, eval_scenarios = load_suite(str(EVAL_DIR))
    eval_ids = {s["id"] for s in eval_scenarios}
    if cal_ids & eval_ids:
        problems.append(f"calibration/evaluation id overlap: {sorted(cal_ids & eval_ids)}")
    # run-time rev chain of custody: every run.start must record the same rev,
    # which must be the rev attested by the runner's freeze verification
    # (which itself passed the full freeze check at run start)
    fv_path = run_root / "freeze-verification.json"
    if not fv_path.exists():
        problems.append("freeze-verification.json missing (runner did not verify the freeze)")
    else:
        fv = json.loads(fv_path.read_text(encoding="utf-8"))
        if not fv.get("passed"):
            problems.append("runner-side freeze verification did not pass")
        run_revs = set()
        for arm in ARMS:
            p = run_root / f"arm-{arm}" / f"seed-{CONFIRMATORY_SEEDS[0]}" / "trace.jsonl"
            if p.exists():
                with open(p, "r", encoding="utf-8") as fh:
                    for line in fh:
                        rec = json.loads(line)
                        if rec.get("type") == "run.start":
                            run_revs.add(rec["payload"].get("git_rev"))
                            break
        if len(run_revs) > 1:
            problems.append(f"run.start git_revs disagree across arms: {run_revs}")
        for rev in run_revs:
            if rev and fv.get("git_rev") and rev != fv["git_rev"]:
                problems.append(f"run.start git_rev {rev} != freeze-verification rev {fv['git_rev']}")
    return problems


# ----------------------------------------------------------------- bootstrap


def per_scenario_counts(rows: list[dict[str, Any]], arm: str, strict_key: str = "repeated_mistake_strict") -> dict[str, dict[str, int]]:
    """{scenario: {eligible, repeated}} pooled over seeds for one arm."""
    out: dict[str, dict[str, int]] = {}
    for r in rows:
        if r.get("arm") != arm or "parse_error" in r:
            continue
        slot = out.setdefault(r["scenario"], {"eligible": 0, "repeated": 0})
        if r["eligible"]:
            slot["eligible"] += 1
            if r[strict_key]:
                slot["repeated"] += 1
    return out


def paired_bootstrap(
    counts_x: dict[str, dict[str, int]],
    counts_y: dict[str, dict[str, int]],
    *,
    seed: int = BOOTSTRAP_SEED,
) -> dict[str, Any]:
    """Section 5 paired cluster bootstrap: RM(x) - RM(y) over scenario resamples."""
    scenarios = sorted(counts_x)
    if not scenarios:
        return {"error": "no scenarios", "delta_mean": None, "ci95": None}
    rng = random.Random(seed)
    deltas: list[float] = []
    redraws = 0
    draws = 0
    while draws < BOOTSTRAP_RESAMPLES:
        sample = rng.choices(scenarios, k=len(scenarios))
        elig_x = sum(counts_x[s]["eligible"] for s in sample)
        elig_y = sum(counts_y[s]["eligible"] for s in sample)
        if elig_x == 0 or elig_y == 0:
            redraws += 1
            if redraws > REDRAW_LIMIT:
                return {"error": f"degenerate eligibility: {redraws} redraws > {REDRAW_LIMIT} (5% of {BOOTSTRAP_RESAMPLES})", "delta_mean": None, "ci95": None}
            continue
        rm_x = sum(counts_x[s]["repeated"] for s in sample) / elig_x
        rm_y = sum(counts_y[s]["repeated"] for s in sample) / elig_y
        deltas.append(rm_x - rm_y)
        draws += 1
    ci = percentile_ci(deltas)
    return {
        "bootstrap_unit": "scenario (paired, same resampled set for both arms)",
        "resamples": BOOTSTRAP_RESAMPLES,
        "rng_seed": seed,
        "redraws": redraws,
        "delta_mean": round(statistics.fmean(deltas), 4),
        "ci95": ci,
        "ci_excludes_zero": (ci[0] > 0) or (ci[1] < 0),
    }


def pooled_rm(rows: list[dict[str, Any]], arm: str, strict_key: str = "repeated_mistake_strict") -> dict[str, Any]:
    arm_rows = [r for r in rows if r.get("arm") == arm and "parse_error" not in r]
    elig = sum(1 for r in arm_rows if r["eligible"])
    rep = sum(1 for r in arm_rows if r[strict_key])
    return {
        "eligible": elig,
        "repeated": rep,
        "rm_rate": round(rep / elig, 4) if elig else None,
    }


def per_seed_rm(rows: list[dict[str, Any]], arm: str) -> dict[str, Any]:
    arm_rows = [r for r in rows if r.get("arm") == arm and "parse_error" not in r]
    by_seed: dict[str, Any] = {}
    for seed in sorted({r["seed"] for r in arm_rows}):
        srows = [r for r in arm_rows if r["seed"] == seed]
        elig = sum(1 for r in srows if r["eligible"])
        rep = sum(1 for r in srows if r["repeated_mistake_strict"])
        by_seed[str(seed)] = {
            "eligible": elig,
            "repeated_strict": rep,
            "rm_rate_strict": round(rep / elig, 3) if elig else None,
        }
    rates = [v["rm_rate_strict"] for v in by_seed.values() if v["rm_rate_strict"] is not None]
    return {
        "per_seed": by_seed,
        "range": [min(rates), max(rates)] if rates else None,
    }


# ------------------------------------------------------------------- arm-E actuation


def actuation_counts(run_root: Path) -> dict[str, Any]:
    per_seed: dict[str, int] = {}
    per_seed_retrieves: dict[str, int] = {}
    for seed in CONFIRMATORY_SEEDS:
        trace = run_root / "arm-E" / f"seed-{seed}" / "trace.jsonl"
        injections = 0
        retrieves = 0
        if trace.exists():
            with open(trace, "r", encoding="utf-8") as fh:
                for line in fh:
                    rec = json.loads(line)
                    if rec.get("type") == "policy.action":
                        if rec["payload"].get("action") == "retrieve_then_answer":
                            retrieves += 1
                        retr = rec["payload"].get("retrieval") or {}
                        if retr.get("injected") is True:
                            injections += 1
        per_seed[str(seed)] = injections
        per_seed_retrieves[str(seed)] = retrieves
    zero_every_seed = all(v == 0 for v in per_seed.values())
    return {
        "expectation_predeclared": ">= 1 physical policy injection per seed (section 6.7)",
        "physical_injections_by_seed": per_seed,
        "retrieve_actions_by_seed": per_seed_retrieves,
        "expectation_met": not zero_every_seed and all(v >= 1 for v in per_seed.values()),
        "actuation_inert": zero_every_seed,
        "verdict_predeclared_on_zero": (
            "if the observed physical-injection count is 0 for every seed, arm E "
            "is declared 'actuation-inert on fixture v2', the E-D contrast is "
            "reported as a null increment WITH that caveat, and no policy-level "
            "claim is made"
        ),
    }


# --------------------------------------------------------------------- family pass rates


def family_pass_counts(run_root: Path, family: str) -> dict[str, dict[str, dict[str, int]]]:
    """{arm: {scenario: {passed, total}}} pooled over seeds for one family."""
    _, scenarios = load_suite(str(EVAL_DIR))
    fam_ids = [s["id"] for s in scenarios if s["family"] == family]
    out: dict[str, dict[str, dict[str, int]]] = {}
    for arm in ARMS:
        out[arm] = {}
        for sid in fam_ids:
            passed = total = 0
            for seed in CONFIRMATORY_SEEDS:
                sp = run_root / f"arm-{arm}" / f"seed-{seed}" / "summary.json"
                if not sp.exists():
                    continue
                s = json.loads(sp.read_text(encoding="utf-8"))
                for ss in s.get("scenario_summaries", []):
                    if ss["scenario"] == sid:
                        passed += ss["probes_passed"]
                        total += ss["probes_total"]
            out[arm][sid] = {"passed": passed, "total": total}
    return out


def family_contrast_bootstrap(
    counts: dict[str, dict[str, dict[str, int]]], arm_x: str, arm_y: str
) -> dict[str, Any]:
    """Paired cluster bootstrap of (pass rate x) - (pass rate y) over scenarios."""
    scenarios = sorted(counts[arm_x])
    rng = random.Random(BOOTSTRAP_SEED)
    deltas: list[float] = []
    for _ in range(BOOTSTRAP_RESAMPLES):
        sample = rng.choices(scenarios, k=len(scenarios))
        px = sum(counts[arm_x][s]["passed"] for s in sample)
        tx = sum(counts[arm_x][s]["total"] for s in sample)
        py = sum(counts[arm_y][s]["passed"] for s in sample)
        ty = sum(counts[arm_y][s]["total"] for s in sample)
        if tx == 0 or ty == 0:
            continue
        deltas.append(px / tx - py / ty)
    point_x = sum(counts[arm_x][s]["passed"] for s in scenarios) / max(
        1, sum(counts[arm_x][s]["total"] for s in scenarios)
    )
    point_y = sum(counts[arm_y][s]["passed"] for s in scenarios) / max(
        1, sum(counts[arm_y][s]["total"] for s in scenarios)
    )
    return {
        "pass_rate": {arm_x: round(point_x, 4), arm_y: round(point_y, 4)},
        "delta": round(point_x - point_y, 4),
        "ci95": percentile_ci(deltas) if deltas else None,
        "resamples": len(deltas),
    }


# ------------------------------------------------------------------------- main


def render_rm_markdown(analysis: dict[str, Any]) -> str:
    lines = [
        "# CONT-001 confirmatory — repeated-mistake rate (primary endpoint, M7)",
        "",
        f"**{LABEL}**",
        "",
        f"- source: `{analysis['run_root']}` (held-out fixture v2)",
        f"- primary operationalization: strict (probe repeats the agent's own "
        "initial wrong answer, both at s1t1 / probe normalized); denominator: "
        "per-arm eligible subsequent tasks (initial error vs the fixture's "
        "initial_expected)",
        f"- primary contrast: RM(E) - RM(A), two-sided; MME {MME}; decision rule: "
        "95% paired cluster bootstrap CI excludes 0 AND |delta| >= MME",
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
    p = analysis["primary"]
    lines += [
        "",
        f"**Primary contrast RM(E) - RM(A): point {p['delta_point']:.4f}, 95% CI "
        f"[{p['bootstrap']['ci95'][0]}, {p['bootstrap']['ci95'][1]}] "
        f"(paired cluster bootstrap over scenarios, {p['bootstrap']['resamples']:,} "
        f"resamples, RNG seed {p['bootstrap']['rng_seed']}, {p['bootstrap']['redraws']} redraws).**",
        "",
        f"**Decision rule verdict: {p['verdict']}** ({p['verdict_reason']})",
    ]
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--run-root", required=True,
        help="confirmatory run root (contains arm-*/seed-*/trace.jsonl)",
    )
    args = parser.parse_args()
    run_root = Path(args.run_root)
    if not run_root.is_absolute():
        # accept CWD-relative, lab-relative, and repo-root-relative forms
        if run_root.exists():
            run_root = run_root.resolve()
        elif (LAB_ROOT / run_root).exists():
            run_root = (LAB_ROOT / run_root).resolve()
        else:
            run_root = (LAB_ROOT.parents[1] / run_root).resolve()
    if not run_root.exists():
        print(f"FAIL-CLOSED: run root not found: {run_root}", file=sys.stderr)
        return 2

    halted: dict[str, Any] = {"halt": False, "reasons": []}

    # --- contamination checks (section 8) -----------------------------------
    problems = contamination_checks(run_root)
    if problems:
        halted = {"halt": True, "reasons": ["contamination: " + p for p in problems]}

    # --- missing/failed-run policy (section 8) ------------------------------
    excl = exclusion_report(run_root)
    if excl["halt"]:
        halted["halt"] = True
        halted["reasons"] += ["missing-run policy: " + r for r in excl["halt_reasons"]]

    if halted["halt"]:
        verdict_doc = {
            "kind": "cont001-confirmatory-repeated-mistake-analysis",
            "label": LABEL,
            "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "run_root": str(run_root.relative_to(LAB_ROOT)).replace("\\", "/"),
            "HALTED": halted,
            "confirmatory_outcome": "INCONCLUSIVE-WITH-CAUSE (protocol did not execute; no claim)",
        }
        (run_root / "repeated-mistake-analysis.json").write_text(
            json.dumps(verdict_doc, indent=2, ensure_ascii=True), encoding="utf-8"
        )
        (run_root / "results-summary.md").write_text(
            "# CONT-001 confirmatory — HALTED (agent-pre-registered, pending owner acceptance)\n\n"
            + "\n".join(f"- {r}" for r in halted["reasons"])
            + "\n\nOutcome: INCONCLUSIVE-WITH-CAUSE — the pre-registered protocol did not "
            "execute as written; no confirmatory claim.\n",
            encoding="utf-8",
        )
        print("HALTED: " + "; ".join(halted["reasons"]), file=sys.stderr)
        return 2

    # --- RM rows (section 1.1 on fixture v2) ---------------------------------
    rm_index = rm_fixture_index()
    rows = build_rm_rows(run_root, rm_index)

    per_arm: dict[str, Any] = {}
    for arm in ARMS:
        strict = pooled_rm(rows, arm, "repeated_mistake_strict")
        loose = pooled_rm(rows, arm, "repeated_mistake_loose")
        seed_view = per_seed_rm(rows, arm)
        per_arm[arm] = {
            "seeds": sorted({r["seed"] for r in rows if r.get("arm") == arm and "parse_error" not in r}),
            "pooled": {
                "eligible": strict["eligible"],
                "repeated_strict": strict["repeated"],
                "rm_rate_strict": strict["rm_rate"],
                "repeated_loose": loose["repeated"],
                "rm_rate_loose": loose["rm_rate"],
            },
            "per_seed": seed_view["per_seed"],
            "per_seed_range": seed_view["range"],
        }

    counts = {arm: per_scenario_counts(rows, arm) for arm in ARMS}

    # --- primary contrast E - A (sections 3-5) --------------------------------
    e_counts, a_counts = counts["E"], counts["A"]
    elig_e = per_arm["E"]["pooled"]["eligible"]
    elig_a = per_arm["A"]["pooled"]["eligible"]
    delta_point = per_arm["E"]["pooled"]["rm_rate_strict"] - per_arm["A"]["pooled"]["rm_rate_strict"]
    bootstrap = paired_bootstrap(e_counts, a_counts)

    underpowered = (elig_e < UNDERPOWERED_MIN_ELIGIBLE) or (elig_a < UNDERPOWERED_MIN_ELIGIBLE)
    if "error" in bootstrap:
        primary = {
            "delta_point": delta_point,
            "bootstrap": bootstrap,
            "verdict": "INCONCLUSIVE (bootstrap degenerate)",
            "verdict_reason": bootstrap["error"],
        }
    elif underpowered:
        primary = {
            "delta_point": delta_point,
            "bootstrap": bootstrap,
            "verdict": "INCONCLUSIVE (underpowered guard)",
            "verdict_reason": (
                f"pooled eligible denominator arm E {elig_e} / arm A {elig_a} < "
                f"{UNDERPOWERED_MIN_ELIGIBLE}: the MME cannot be distinguished from probe granularity"
            ),
        }
    else:
        ci = bootstrap["ci95"]
        excludes0 = bootstrap["ci_excludes_zero"]
        meets_mme = abs(delta_point) >= MME
        if excludes0 and meets_mme:
            direction = "harm (RM(E) > RM(A): the continuity stack worsens repeated mistakes)" if delta_point > 0 \
                else "benefit (RM(E) < RM(A): the continuity stack reduces repeated mistakes)"
            primary = {
                "delta_point": delta_point,
                "bootstrap": bootstrap,
                "verdict": f"SUPPORTED — {direction}",
                "verdict_reason": (
                    f"95% CI [{ci[0]}, {ci[1]}] excludes 0 AND |{delta_point:.4f}| >= MME {MME}"
                ),
            }
        else:
            primary = {
                "delta_point": delta_point,
                "bootstrap": bootstrap,
                "verdict": "NO CONFIRMATORY DIFFERENCE ESTABLISHED",
                "verdict_reason": (
                    f"CI [{ci[0]}, {ci[1]}] excludes 0: {excludes0}; |{delta_point:.4f}| >= MME {MME}: {meets_mme}"
                ),
            }

    # --- sensitivities (pre-declared, not primary) ----------------------------
    common_rows: list[dict[str, Any]] = []
    eligibility = {(r["arm"], r["seed"], r["scenario"]): r["eligible"] for r in rows if "parse_error" not in r}
    row_lookup = {(r["arm"], r["seed"], r["scenario"]): r for r in rows if "parse_error" not in r}
    for (arm, seed, sid), r_e in row_lookup.items():
        if arm != "E":
            continue
        r_a = row_lookup.get(("A", seed, sid))
        if r_a is None:
            continue
        if r_e["eligible"] and r_a["eligible"]:
            common_rows.append(r_e)
            common_rows.append(r_a)
    common_counts = {
        arm: per_scenario_counts(
            [r for r in common_rows if r["arm"] == arm], arm
        )
        for arm in ("E", "A")
    }
    sensitivity_common = paired_bootstrap(common_counts["E"], common_counts["A"])

    analysis = {
        "kind": "cont001-confirmatory-repeated-mistake-analysis",
        "label": LABEL,
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "run_root": str(run_root.relative_to(LAB_ROOT)).replace("\\", "/"),
        "definition": {
            "initial_answer": "normalized agent answer at s1t1 (task before rubric exposure)",
            "initial_expected": "explicit fixture field on s1t1 (per scenario; no author-derived mapping)",
            "rm_probe_selection": "probe.class == 'rm_eligible' fixture marker (EVALUATION-PREP.md 6.4)",
            "eligible": "initial answer incorrect per initial_expected (per-agent denominator)",
            "repeated_mistake_strict": "eligible AND probe incorrect AND probe answer == initial answer",
            "repeated_mistake_loose": "eligible AND probe incorrect (sensitivity a)",
            "common_eligible": "only scenarios where BOTH contrasted arms erred initially (sensitivity b)",
            "decision_rule": f"95% paired cluster bootstrap CI excludes 0 AND |delta| >= MME {MME}; two-sided; alpha 0.05; single primary contrast",
            "underpowered_guard": f"either arm pooled eligible < {UNDERPOWERED_MIN_ELIGIBLE} -> inconclusive",
        },
        "missing_run_policy": excl,
        "contamination_checks": {"problems": problems},
        "rm_scenarios": sorted(rm_index),
        "per_arm": per_arm,
        "primary": {
            "contrast": "RM(E) - RM(A)",
            "eligible_denominators": {"E": elig_e, "A": elig_a},
            "rm_rates": {"E": per_arm["E"]["pooled"]["rm_rate_strict"], "A": per_arm["A"]["pooled"]["rm_rate_strict"]},
            "delta_point": delta_point,
            "bootstrap": bootstrap,
            "mme": MME,
            "underpowered": underpowered,
            **primary,
        },
        "sensitivities": {
            "loose_rm_rates": {arm: per_arm[arm]["pooled"]["rm_rate_loose"] for arm in ARMS},
            "common_eligible_E_minus_A": sensitivity_common,
        },
        "rows": rows,
    }
    (run_root / "repeated-mistake-analysis.json").write_text(
        json.dumps(analysis, indent=2, ensure_ascii=True), encoding="utf-8"
    )
    (run_root / "repeated-mistake-analysis.md").write_text(
        render_rm_markdown(analysis), encoding="utf-8"
    )
    print(f"wrote {run_root / 'repeated-mistake-analysis.md'}")
    for arm in ARMS:
        print(f"  arm {arm}: pooled {per_arm[arm]['pooled']}")
    print(f"primary: delta={delta_point:.4f} ci={bootstrap.get('ci95')} verdict={primary['verdict']}")

    # --- secondaries (section 3; exploratory-attribution) ---------------------
    actuation = actuation_counts(run_root)
    secondary_rm = {}
    for x, y in (("B", "A"), ("C", "B"), ("D", "C"), ("E", "D")):
        secondary_rm[f"{x}-{y}"] = paired_bootstrap(counts[x], counts[y])
    fam_secondaries = {}
    for family in ("delayed_recall", "contradiction_update"):
        fc = family_pass_counts(run_root, family)
        fam_secondaries[family] = {
            f"{x}-{y}": family_contrast_bootstrap(fc, x, y)
            for x, y in (("E", "A"), ("C", "B"))
        }
    tokens = {}
    for arm in ARMS:
        agg_path = run_root / f"arm-{arm}" / f"aggregate-arm-{arm}.json"
        if agg_path.exists():
            agg = json.loads(agg_path.read_text(encoding="utf-8"))
            tokens[arm] = agg["request_stats"]["tokens"]["total_sum"]
    secondary = {
        "kind": "cont001-confirmatory-secondary-analyses",
        "label": LABEL,
        "attribution": (
            "pre-declared secondary contrasts (EVALUATION-PREP.md section 3): "
            "mechanism attribution only, exploratory-attribution, never "
            "promotable to primary claims; CIs reported, no threshold claims"
        ),
        "rm_rate_contrasts": secondary_rm,
        "family_pass_rate_contrasts": fam_secondaries,
        "token_cost_per_arm": tokens,
        "arm_e_policy_actuation": actuation,
    }
    if actuation["actuation_inert"]:
        secondary["arm_e_actuation_inert_note"] = (
            "arm E is declared 'actuation-inert on fixture v2': the E-D contrast "
            "is reported as a null increment WITH this caveat and no policy-level "
            "claim is made (pre-declared outcome, section 6.7)"
        )
    (run_root / "secondary-analyses.json").write_text(
        json.dumps(secondary, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    # --- results summary (the confirmatory outcome, plainly) ------------------
    ci = bootstrap.get("ci95")
    summary_lines = [
        "# CONT-001 confirmatory result — M7",
        "",
        f"**{LABEL}**",
        "",
        f"- Run: `{analysis['run_root']}`; pre-registration "
        "`docs/EVALUATION-PREP.md` frozen at `a845fc5`; review GO "
        "(`docs/PR-REVIEW.md`).",
        "- Held-out fixture v2 (14 scenarios; 7 RM-eligible probes/seed), fresh "
        "seeds {101, 202, 303, 404, 505}, model granite-code:8b (digest "
        "36c3c3b9683b...), temperature 0.0, num_ctx 4096; calibration-derived "
        "self-model revision 1' (disjoint calibration suite, seeds {11,22,33}).",
        "",
        "## Primary endpoint (pre-registered): repeated-mistake rate",
        "",
        "| arm | eligible | repeated (strict) | RM rate |",
        "| --- | --- | --- | --- |",
    ]
    for arm in ARMS:
        p = per_arm[arm]["pooled"]
        rate = p["rm_rate_strict"] if p["rm_rate_strict"] is not None else "n/a"
        summary_lines.append(f"| {arm} | {p['eligible']} | {p['repeated_strict']} | {rate} |")
    summary_lines += [
        "",
        f"**Primary contrast RM(E) - RM(A): {delta_point:+.4f} "
        f"(E {per_arm['E']['pooled']['rm_rate_strict']} vs A "
        f"{per_arm['A']['pooled']['rm_rate_strict']}), 95% CI "
        f"[{ci[0] if ci else 'n/a'}, {ci[1] if ci else 'n/a'}]** "
        f"(paired cluster bootstrap over scenarios, {BOOTSTRAP_RESAMPLES:,} resamples, "
        f"RNG seed {BOOTSTRAP_SEED}, {bootstrap.get('redraws')} redraws).",
        "",
        f"## Confirmatory outcome per the pre-registered rule",
        "",
        f"**{primary['verdict']}** — {primary['verdict_reason']}",
        "",
    ]
    if primary["verdict"].startswith("SUPPORTED") and delta_point > 0:
        summary_lines += [
            "Reported plainly: the direction is HARM — on this suite the full "
            "continuity stack (arm E) repeated its own initial mistakes at a "
            "higher rate than the no-persistent-memory ablation (arm A). This "
            "is a legitimate confirmatory finding, not a failure to be spun.",
            "",
        ]
    summary_lines += [
        "## Secondary analyses (exploratory-attribution, not promotable)",
        "",
        "- RM contrasts: "
        + "; ".join(
            f"{k}: {v.get('delta_mean')} CI {v.get('ci95')}"
            for k, v in secondary_rm.items()
        ),
        "- delayed_recall E-A: "
        f"{fam_secondaries['delayed_recall']['E-A']['delta']} CI {fam_secondaries['delayed_recall']['E-A']['ci95']}; "
        "C-B: "
        f"{fam_secondaries['delayed_recall']['C-B']['delta']} CI {fam_secondaries['delayed_recall']['C-B']['ci95']}",
        "- contradiction_update E-A: "
        f"{fam_secondaries['contradiction_update']['E-A']['delta']} CI {fam_secondaries['contradiction_update']['E-A']['ci95']}; "
        "C-B: "
        f"{fam_secondaries['contradiction_update']['C-B']['delta']} CI {fam_secondaries['contradiction_update']['C-B']['ci95']}",
        f"- token cost per arm: {tokens}",
        f"- arm-E policy actuation (physical injections by seed): "
        f"{actuation['physical_injections_by_seed']} — expectation "
        f">= 1/seed met: {actuation['expectation_met']}; actuation-inert: "
        f"{actuation['actuation_inert']}",
        "",
        "## Scope bounds (per the pre-registration, section 9)",
        "",
        "Synthetic public-safe fixtures, one core model at temperature 0.0, the "
        "v2 suite's families; no external-validity claims beyond that. "
        "Determinism caveat PB-071/CN-003 travels with every number.",
        "",
        f"Interpretation and acceptance belong to the owner (ROADMAP morning "
        "list). {LABEL}.",
    ]
    (run_root / "results-summary.md").write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"wrote {run_root / 'results-summary.md'}")
    print(f"wrote {run_root / 'secondary-analyses.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
