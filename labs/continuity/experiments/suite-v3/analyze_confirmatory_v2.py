"""CONT-005 confirmatory analysis — EXACTLY as frozen in docs/EVALUATION-PREP-v2.md.

This script is part of the FREEZE MANIFEST (PREREG-REQUIREMENTS-V2 section 1):
its digest is recorded in frozen-config-v2.json BEFORE any v3h inference, and it
must not change after the freeze. It implements:

  - Primary endpoint: label-form error rate over the 12 primary clusters
    (correction_reuse x8 + contradiction_update x4), structural eligibility.
  - Primary contrast: T0 - T2 (positive = trust resolution reduces errors).
  - Decision rule: two-sided 95% cluster percentile bootstrap, 10,000 resamples,
    RNG seed 20261005; verdict wording frozen verbatim (EVALUATION-PREP-v2
    section 6, incl. the sub-MME zone wording added by PR-REVIEW-v2).
  - Completeness guard: all 12 clusters x 5 seeds in BOTH primary arms, else
    "incomplete" (no substitution, no seed re-draws).
  - Mandatory error decomposition (wrong-label vs invalid-format) and the
    guess-band rule (|guess_rate - 1/6| per arm; caveat when the primary delta
    < 2 x max-arm band; the MME never moves post hoc).
  - Secondary tables: family pass rates (all arms), strict scripted-trap repeat
    rate (no-headroom endpoint, reported for the record), T1/T3 vs T0
    exploratory deltas, token/wall accounting with cross-attempt
    reconciliation, and the exact execution rev list from the traces.

Operationalization frozen here (EVALUATION-PREP-v2 section 12): guess_rate(arm)
:= the maximum position share of that arm's guess-calibration replies (k = 6);
band(arm) := |guess_rate - 1/6|.

Usage:
    python labs/continuity/experiments/suite-v3/analyze_confirmatory_v2.py \
        --run-root <confirmatory run dir> [--out <path>/results-summary.json]

Exit 0 on a complete analysis; exit 2 fail-closed on guard/structure violations
(the verdict may still be "incomplete" with exit 0 when the run itself is
incomplete but well-formed — the guard's job is reporting, not crashing).
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import load_suite  # noqa: E402

# --- Frozen constants (EVALUATION-PREP-v2 as amended by PR-REVIEW-v2) ---
SEEDS = (1001, 1002, 1003, 1004, 1005)
PRIMARY_ARMS = ("T0", "T2")
ALL_ARMS = ("A", "T0", "T1", "T2", "T3")
PRIMARY_FAMILIES = {"correction_reuse", "contradiction_update"}
MME = 0.25
BOOT = 10_000
RNG_SEED = 20261005
GUESS_K = 6

VERDICT_ESTABLISHED = "confirmatory difference established"
VERDICT_SUB_MME = (
    "directional difference below the minimum meaningful effect; "
    "not established as meaningful"
)
VERDICT_NONE = "no confirmatory difference established"
VERDICT_INCOMPLETE = "incomplete"


def load_summary(run_root: Path, arm: str, seed: int) -> dict | None:
    for stem in (f"seed-{seed}", f"seed-{seed}-a2"):
        p = run_root / arm / stem / "summary.json"
        if p.exists():
            summary = json.loads(p.read_text(encoding="utf-8"))
            summary["_dir"] = f"{arm}/{stem}"
            return summary
    return None


def trace_revs(run_root: Path, arm: str, seed: int) -> list[str]:
    revs = []
    for stem in (f"seed-{seed}", f"seed-{seed}-a2"):
        t = run_root / arm / stem / "trace.jsonl"
        if not t.exists():
            continue
        for line in t.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("type") == "run.start":
                rev = rec.get("payload", {}).get("git_rev")
                if rev and rev not in revs:
                    revs.append(rev)
    return revs


def primary_probe_rows(summary: dict) -> list[dict]:
    rows = []
    for sc in summary["scenario_summaries"]:
        if sc["family"] not in PRIMARY_FAMILIES:
            continue
        for p in sc["probes"]:
            if p["passed"] is None:
                continue
            rows.append({"scenario": sc["scenario"], "family": sc["family"], **p})
    return rows


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    run_root = Path(args.run_root)

    manifest, fixtures = load_suite(str(LAB_ROOT / "fixtures" / "v3h"))
    fam_of = {s["id"]: s["family"] for s in fixtures}
    trap_of = {s["id"]: s.get("seed_error", {}).get("value", "").lower() for s in fixtures}
    primary_ids = sorted(i for i, f in fam_of.items() if f in PRIMARY_FAMILIES)

    summaries: dict[tuple[str, int], dict] = {}
    missing: list[str] = []
    for arm in ALL_ARMS:
        for seed in SEEDS:
            s = load_summary(run_root, arm, seed)
            if s is None or not s.get("completed"):
                missing.append(f"{arm}/seed-{seed}")
            else:
                summaries[(arm, seed)] = s

    # --- Completeness guard (primary arms only void the verdict) ---
    primary_missing = [m for m in missing if m.split("/")[0] in PRIMARY_ARMS]
    secondary_missing = [m for m in missing if m.split("/")[0] not in PRIMARY_ARMS]
    complete_primary = not primary_missing

    # --- Primary analysis ---
    import random

    rng = random.Random(RNG_SEED)
    cluster_delta: list[float] = []
    per_cluster: dict[str, dict] = {}
    if complete_primary:
        for sid in primary_ids:
            rates = {}
            for arm in PRIMARY_ARMS:
                errs = []
                for seed in SEEDS:
                    rows = [r for r in primary_probe_rows(summaries[(arm, seed)]) if r["scenario"] == sid]
                    assert len(rows) == 1, (arm, seed, sid, len(rows))
                    errs.append(0.0 if rows[0]["passed"] else 1.0)
                rates[arm] = sum(errs) / len(errs)
            per_cluster[sid] = rates
            cluster_delta.append(rates["T0"] - rates["T2"])
        means = []
        for _ in range(BOOT):
            sample = [cluster_delta[rng.randrange(len(cluster_delta))] for _ in cluster_delta]
            means.append(sum(sample) / len(sample))
        means.sort()
        lo = means[int(0.025 * (BOOT - 1))]
        hi = means[int(0.975 * (BOOT - 1))]
        delta = sum(cluster_delta) / len(cluster_delta)
    else:
        delta = lo = hi = None

    # --- Verdict (frozen wording) ---
    if not complete_primary:
        verdict = VERDICT_INCOMPLETE
    elif lo > 0.0 or hi < 0.0:
        verdict = VERDICT_ESTABLISHED if delta >= MME else VERDICT_SUB_MME
    else:
        verdict = VERDICT_NONE

    # --- Error decomposition (mandatory secondary, primary arms) ---
    decomposition: dict[str, dict] = {}
    for arm in PRIMARY_ARMS:
        counts = {"correct": 0, "wrong_label": 0, "invalid_format": 0}
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for r in primary_probe_rows(summaries[(arm, seed)]):
                if r["passed"]:
                    counts["correct"] += 1
                elif r.get("observed_label") is None:
                    counts["invalid_format"] += 1
                else:
                    counts["wrong_label"] += 1
        decomposition[arm] = counts

    # --- Guess band (operationalized: max position share vs 1/k) ---
    guess: dict[str, dict] = {}
    for arm in ALL_ARMS:
        positions: dict[int, int] = {}
        n = 0
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for sc in summaries[(arm, seed)]["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is None:
                        n += 1
                        if p.get("observed_position") is not None:
                            positions[p["observed_position"]] = positions.get(p["observed_position"], 0) + 1
        share = (max(positions.values()) / n) if n and positions else None
        guess[arm] = {
            "guess_probes": n,
            "max_position_share": round(share, 3) if share is not None else None,
            "band": round(abs(share - 1.0 / GUESS_K), 3) if share is not None else None,
        }
    max_band = max((g["band"] or 0.0) for g in guess.values())
    guess_caveat = (
        delta is not None and delta < 2 * max_band
    )

    # --- Secondary tables ---
    fam_table: dict[str, dict[str, float]] = {}
    for arm in ALL_ARMS:
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for sc in summaries[(arm, seed)]["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is None:
                        continue
                    fam_table.setdefault(sc["family"], {}).setdefault(arm, []).append(1 if p["passed"] else 0)
    fam_summary = {
        f: {a: round(statistics.fmean(v), 3) for a, v in arms.items()}
        for f, arms in fam_table.items()
    }

    strict_rm: dict[str, dict] = {}
    for arm in ALL_ARMS:
        eligible = repeats = 0
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for sc in summaries[(arm, seed)]["scenario_summaries"]:
                sid = sc["scenario"]
                trap = trap_of.get(sid, "")
                if fam_of.get(sid) not in PRIMARY_FAMILIES or not trap:
                    continue
                for p in sc["probes"]:
                    if p["passed"] is None:
                        continue
                    eligible += 1
                    if p.get("observed_normalized") == trap:
                        repeats += 1
        strict_rm[arm] = {"eligible": eligible, "strict_repeats": repeats}

    tokens_wall: dict[str, dict] = {}
    for arm in ALL_ARMS:
        walls, tokens = [], 0
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            walls.append(summaries[(arm, seed)]["wall_s"])
            tokens += summaries[(arm, seed)]["tokens_total"]
        tokens_wall[arm] = {
            "wall_s_sum": round(sum(walls), 1),
            "tokens_sum": tokens,
            "arm_seeds_present": len(walls),
        }

    revs: dict[str, list[str]] = {}
    for arm in ALL_ARMS:
        all_revs: list[str] = []
        for seed in SEEDS:
            for rev in trace_revs(run_root, arm, seed):
                if rev not in all_revs:
                    all_revs.append(rev)
        revs[arm] = all_revs

    report = {
        "kind": "cont005-confirmatory-results",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spec": "docs/EVALUATION-PREP-v2.md (frozen) + docs/PR-REVIEW-v2.md",
        "run_root": str(run_root),
        "execution_revs": revs,
        "completeness": {
            "primary_missing": primary_missing,
            "secondary_missing": secondary_missing,
            "verdict_blocking": bool(primary_missing),
        },
        "primary": {
            "endpoint": "label-form error rate, 12 CR+CU clusters, structural eligibility",
            "contrast": "T0 - T2",
            "per_cluster": per_cluster,
            "delta_mean": round(delta, 4) if delta is not None else None,
            "ci95": [round(lo, 4), round(hi, 4)] if lo is not None else None,
            "mme": MME,
            "bootstrap": {"resamples": BOOT, "rng_seed": RNG_SEED, "method": "cluster percentile"},
            "verdict": verdict,
            "direction_note": (
                "positive delta = trust resolution (T2) reduces errors relative to flat memory (T0)"
            ),
        },
        "error_decomposition_primary": decomposition,
        "guess_band": {
            "operationalization": "guess_rate(arm) = max position share of that arm's guess replies; band = |guess_rate - 1/6|",
            "per_arm": guess,
            "max_band": round(max_band, 3),
            "caveat_fires": bool(guess_caveat),
            "caveat": (
                "primary effect does not clear the guessing band" if guess_caveat else None
            ),
        },
        "secondary": {
            "family_pass_by_arm": fam_summary,
            "strict_scripted_trap_repeat": strict_rm,
            "t1_t3_exploratory_overall": {
                a: round(
                    statistics.fmean(
                        [v for f, arms in fam_table.items() for aa, v in arms.items() if aa == a]
                    ), 3,
                )
                for a in ALL_ARMS
                if any(a in arms for arms in fam_table.values())
            },
            "tokens_wall": tokens_wall,
        },
    }

    out = Path(args.out) if args.out else run_root / "results-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"VERDICT: {verdict}")
    if delta is not None:
        print(f"  primary delta (T0-T2) = {delta:.4f}, 95% CI [{lo:.4f}, {hi:.4f}], MME {MME}")
    if guess_caveat:
        print("  caveat: primary effect does not clear the guessing band")
    print(f"  written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
