"""CONT-005 cycle-2 PILOT GO/NO-GO analysis — EXACTLY as frozen in
docs/EVALUATION-PREP-v3.md (FREEZE-A manifest, PR-REVIEW-v3 RC2).

This script is part of the FREEZE-A MANIFEST (PREREG-REQUIREMENTS-V2 §1):
its digest is recorded in frozen-config-v3a.json BEFORE any v3i inference,
and it must not change after the freeze. It computes the four predeclared
pilot GO/NO-GO clauses (EVALUATION-PREP-v3 §2) plus the standard reporting
tables; the CONFIRMATORY analysis (v3j, bootstrap verdict) is a separate
script written at FREEZE-B.

  Clause 1  Headroom PER FAMILY (PR-REVIEW-v3 RC1; a pooled mean passed the
            exact cycle-1 pathology T0 pooled 0.50 = 6/8 CR floored + 4/4 CU
            ceilinged): the CR family-mean (8 clusters) AND the CU family-mean
            (4 clusters) primary error strictly inside (0.15, 0.85) in BOTH
            primary arms (T0, T1). A failed family is rebalanced in v3j at
            FREEZE-B (declared openly) — never silently.
  Clause 2  Spread: per-arm sd of the 5 per-seed primary means, reported with
            its n=5 (df=4) chi-square 95% CI, not a point estimate. Any
            primary arm sd > 0.25 -> stress row (P4) of power-results-v3.json
            governs + owner sign-off before FREEZE-B.
  Clause 3  Concentration: LIVE clusters = both primary arms' cluster error
            strictly inside (0.10, 0.90). Fewer than 8 of 12 live -> the P5
            row of the power artifact governs (0.705 at 8/12) + owner
            sign-off before FREEZE-B.
  Clause 4  Residual echo: no "[RESOLVED" substring in any T2/T3 answer
            (traces); per-arm invalid-format rate reported. Echo found ->
            flags move to plain "NOTE:" prose at FREEZE-B (pre-authorized
            fix class, recorded in the run record).

Usage:
    python labs/continuity/experiments/suite-v3/analyze_pilot_v3.py \
        --run-root <pilot run dir> [--out <path>/pilot-go-nogo.json]

Exit 0 on a well-formed report (including verdict flags that require action);
exit 2 fail-closed on structural violations. Missing primary arm-seeds ->
verdict "incomplete" (exit 0): the GO/NO-GO is simply not evaluable yet.
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import load_suite  # noqa: E402

# --- Frozen constants (EVALUATION-PREP-v3 §2 as amended by PR-REVIEW-v3) ---
SEEDS = (2001, 2002, 2003, 2004, 2005)
PRIMARY_ARMS = ("T0", "T1")
ECHO_ARMS = ("T2", "T3")
ALL_ARMS = ("A", "T0", "T1", "T2", "T3")
PRIMARY_FAMILIES = ("correction_reuse", "contradiction_update")
HEADROOM = (0.15, 0.85)
LIVE = (0.10, 0.90)
LIVE_MIN = 8
SPREAD_MAX = 0.25
ECHO_MARKER = "[RESOLVED"
GUESS_K = 6
# chi-square two-sided 95% quantiles for df=4 (n=5): sd CI multiplier
# (n-1)s^2/chi2_hi .. (n-1)s^2/chi2_lo -> sd CI = (s*sqrt(4/11.1433), s*sqrt(4/0.4844))
CHI2_DF4 = {"lo": 0.484419, "hi": 11.143287}
SD_CI_LO_MULT = math.sqrt(4.0 / CHI2_DF4["hi"])   # ~0.5995 (Fable: ~0.6x)
SD_CI_HI_MULT = math.sqrt(4.0 / CHI2_DF4["lo"])   # ~2.8740 (Fable: ~2.9x)


def load_summary(run_root: Path, arm: str, seed: int) -> dict | None:
    for stem in (f"seed-{seed}", f"seed-{seed}-a2"):
        p = run_root / arm / stem / "summary.json"
        if p.exists():
            summary = json.loads(p.read_text(encoding="utf-8"))
            summary["_dir"] = f"{arm}/{stem}"
            return summary
    return None


def primary_rows(summary: dict) -> list[dict]:
    rows = []
    for sc in summary["scenario_summaries"]:
        if sc["family"] not in PRIMARY_FAMILIES:
            continue
        for p in sc["probes"]:
            if p["passed"] is None:
                continue
            rows.append({"scenario": sc["scenario"], "family": sc["family"], **p})
    return rows


def echo_scan(run_root: Path, arm: str) -> dict:
    """Clause 4: count '[RESOLVED' occurrences in T2/T3 assistant replies."""
    hits = 0
    replies = 0
    arms_present = False
    for seed in SEEDS:
        for stem in (f"seed-{seed}", f"seed-{seed}-a2"):
            t = run_root / arm / stem / "trace.jsonl"
            if not t.exists():
                continue
            arms_present = True
            for line in t.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("type") == "agent.response":
                    content = rec.get("payload", {}).get("content", "")
                    replies += 1
                    if ECHO_MARKER in content:
                        hits += 1
    return {"arm": arm, "present": arms_present, "replies": replies, "bracket_hits": hits}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    run_root = Path(args.run_root)

    manifest, fixtures = load_suite(str(LAB_ROOT / "fixtures" / "v3i"))
    fam_of = {s["id"]: s["family"] for s in fixtures}
    primary_ids = sorted(i for i, f in fam_of.items() if f in PRIMARY_FAMILIES)

    summaries: dict[tuple[str, int], dict] = {}
    missing: list[str] = []
    for arm in ALL_ARMS:
        for seed in SEEDS:
            s = load_summary(run_root, arm, seed)
            if s is None:
                missing.append(f"{arm}/seed-{seed}")
                continue
            summaries[(arm, seed)] = s

    # Completeness for the GO/NO-GO: both PRIMARY arms x all seeds x 12 probes.
    primary_probes = {arm: {} for arm in PRIMARY_ARMS}
    for arm in PRIMARY_ARMS:
        for seed in SEEDS:
            s = summaries.get((arm, seed))
            primary_probes[arm][seed] = primary_rows(s) if s else []
    incomplete = [
        f"{arm}/seed-{seed}"
        for arm in PRIMARY_ARMS
        for seed in SEEDS
        if len(primary_probes[arm][seed]) != len(primary_ids)
    ]

    report: dict = {
        "kind": "cont005-c2-pilot-go-nogo",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spec": "docs/EVALUATION-PREP-v3.md §2 clauses 1-4 (PR-REVIEW-v3 RC1-RC3 folded)",
        "run_root": str(run_root),
        "seeds": list(SEEDS),
        "completeness": {
            "primary_arm_seeds_expected": len(PRIMARY_ARMS) * len(SEEDS),
            "primary_missing": incomplete,
            "secondary_missing": [m for m in missing if m.split("/")[0] not in PRIMARY_ARMS],
        },
    }

    if incomplete:
        report["verdict"] = "incomplete"
        report["verdict_note"] = (
            "primary arm-seeds incomplete; the GO/NO-GO is not evaluable "
            "(no substitution, no seed re-draws — EVALUATION-PREP-v3 §7)"
        )
        if args.out:
            Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
        print(json.dumps(report["completeness"], indent=1))
        print("VERDICT: incomplete")
        return 0

    # ---- per-cluster / per-family error tables (primary arms) ----
    per_cluster: dict[str, dict[str, float]] = {cid: {} for cid in primary_ids}
    family_errors: dict[str, dict[str, list[float]]] = {
        arm: {fam: [] for fam in PRIMARY_FAMILIES} for arm in PRIMARY_ARMS
    }
    per_seed_means: dict[str, dict[int, float]] = {arm: {} for arm in ALL_ARMS}
    for arm in ALL_ARMS:
        for seed in SEEDS:
            s = summaries.get((arm, seed))
            if s is None:
                continue
            rows = primary_rows(s)
            if not rows:
                continue
            errs = [0.0 if r["passed"] else 1.0 for r in rows]
            per_seed_means[arm][seed] = sum(errs) / len(errs)
            if arm in PRIMARY_ARMS:
                by_cluster: dict[str, list[float]] = {cid: [] for cid in primary_ids}
                for r in rows:
                    by_cluster[r["scenario"]].append(0.0 if r["passed"] else 1.0)
                for cid, vals in by_cluster.items():
                    per_cluster[cid][arm] = sum(vals) / len(vals)
                for r in rows:
                    family_errors[arm][r["family"]].append(0.0 if r["passed"] else 1.0)

    # ---- Clause 1: per-family headroom ----
    headroom_rows = []
    headroom_fail: list[str] = []
    for arm in PRIMARY_ARMS:
        for fam in PRIMARY_FAMILIES:
            mean_err = statistics.fmean(family_errors[arm][fam])
            ok = HEADROOM[0] < mean_err < HEADROOM[1]
            headroom_rows.append(
                {"arm": arm, "family": fam, "clusters": len(family_errors[arm][fam]) // len(SEEDS),
                 "mean_error": round(mean_err, 4), "inside_(0.15,0.85)": ok}
            )
            if not ok:
                headroom_fail.append(f"{arm}/{fam}={mean_err:.3f}")
    clause1 = not headroom_fail

    # ---- Clause 2: between-seed spread with df=4 CI ----
    spread_rows = []
    spread_exceeds: list[str] = []
    for arm in ALL_ARMS:
        vals = [per_seed_means[arm][sd] for sd in SEEDS if sd in per_seed_means[arm]]
        if len(vals) < len(SEEDS):
            spread_rows.append({"arm": arm, "note": "incomplete; skipped"})
            continue
        sd = statistics.stdev(vals)
        row = {
            "arm": arm,
            "per_seed_primary_means": [round(v, 4) for v in vals],
            "sd": round(sd, 4),
            "sd_ci95": [round(sd * SD_CI_LO_MULT, 4), round(sd * SD_CI_HI_MULT, 4)],
            "ci_note": "chi-square df=4 (n=5); threshold judged on the point sd, CI reported (PR-REVIEW-v3 N3)",
        }
        if arm in PRIMARY_ARMS:
            row["exceeds_0.25"] = sd > SPREAD_MAX
            if sd > SPREAD_MAX:
                spread_exceeds.append(f"{arm} sd={sd:.3f}")
        spread_rows.append(row)
    clause2 = not spread_exceeds

    # ---- Clause 3: live clusters ----
    live_list = []
    for cid in primary_ids:
        t0, t1 = per_cluster[cid]["T0"], per_cluster[cid]["T1"]
        is_live = LIVE[0] < t0 < LIVE[1] and LIVE[0] < t1 < LIVE[1]
        live_list.append({"cluster": cid, "T0": round(t0, 3), "T1": round(t1, 3), "live": is_live})
    live_count = sum(1 for x in live_list if x["live"])
    clause3 = live_count >= LIVE_MIN

    # ---- Clause 4: residual echo + invalid-format decomposition ----
    echo_rows = [echo_scan(run_root, arm) for arm in ECHO_ARMS]
    echo_hits = sum(r["bracket_hits"] for r in echo_rows)
    decomposition: dict[str, dict[str, int]] = {}
    for arm in ALL_ARMS:
        counts = {"correct": 0, "wrong_label": 0, "invalid_format": 0}
        for seed in SEEDS:
            s = summaries.get((arm, seed))
            if not s:
                continue
            for r in primary_rows(s):
                if r["passed"]:
                    counts["correct"] += 1
                elif r.get("observed_label") is None:
                    counts["invalid_format"] += 1
                else:
                    counts["wrong_label"] += 1
        decomposition[arm] = counts
    clause4 = echo_hits == 0

    # ---- reporting extras (not GO/NO-GO): family pass rates, guess ----
    family_pass: dict[str, dict[str, float]] = {}
    for arm in ALL_ARMS:
        fam_vals: dict[str, list[int]] = {}
        for seed in SEEDS:
            s = summaries.get((arm, seed))
            if not s:
                continue
            for sc in s["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is None:
                        continue
                    fam_vals.setdefault(sc["family"], []).append(1 if p["passed"] else 0)
        family_pass[arm] = {f: round(statistics.fmean(v), 4) for f, v in sorted(fam_vals.items())}
    guess = {}
    for arm in ALL_ARMS:
        probes = valid = 0
        positions: dict[str, int] = {}
        for seed in SEEDS:
            s = summaries.get((arm, seed))
            if not s:
                continue
            for sc in s["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is not None:
                        continue
                    probes += 1
                    if p.get("observed_label") is not None:
                        valid += 1
                    pos = p.get("observed_position")
                    if pos is not None:
                        positions[str(pos)] = positions.get(str(pos), 0) + 1
        guess[arm] = {
            "probes": probes, "valid_fraction": round(valid / probes, 3) if probes else None,
            "max_position_share": round(max(positions.values()) / probes, 3) if probes else None,
        }

    go_no_go = {
        "clause1_headroom_per_family": {"pass": clause1, "rows": headroom_rows,
                                        "failures": headroom_fail},
        "clause2_spread": {"pass": clause2, "rows": spread_rows, "exceeds": spread_exceeds,
                           "routing": "any exceed -> stress row P4 governs + owner sign-off before FREEZE-B"},
        "clause3_live_clusters": {"pass": clause3, "live_count": live_count, "need": LIVE_MIN,
                                  "rows": live_list,
                                  "routing": f"< {LIVE_MIN} live -> P5 row governs (0.705 at 8/12) + owner sign-off before FREEZE-B"},
        "clause4_residual_echo": {"pass": clause4, "rows": echo_rows,
                                  "routing": "echo found -> flags move to plain NOTE: prose at FREEZE-B (pre-authorized)"},
    }
    actions = []
    if not clause1:
        actions.append(f"REBALANCE at FREEZE-B (openly declared): {', '.join(headroom_fail)}")
    if not clause2:
        actions.append("OWNER SIGN-OFF (spread > 0.25 -> P4 stress row governs)")
    if not clause3:
        actions.append(f"OWNER SIGN-OFF (live clusters {live_count}/12 < {LIVE_MIN} -> P5 row governs)")
    if not clause4:
        actions.append("ECHO FIX at FREEZE-B (NOTE: prose, pre-authorized)")
    verdict = "PROCEED-FREEZE-B" if not actions else " | ".join(actions)

    report["per_cluster_primary"] = per_cluster
    report["error_decomposition_primary"] = decomposition
    report["family_pass_by_arm"] = family_pass
    report["guess_by_arm"] = guess
    report["go_no_go"] = go_no_go
    report["verdict"] = verdict
    report["verdict_note"] = (
        "GO/NO-GO for the confirmatory stage only; the pilot makes NO confirmatory claims "
        "(no bootstrap verdict is computed here — that is the FREEZE-B analysis script)"
    )

    out_path = Path(args.out) if args.out else run_root / "pilot-go-nogo.json"
    out_path.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
    print(f"written: {out_path}")
    print(f"VERDICT: {verdict}")
    for key, block in go_no_go.items():
        print(f"  {key}: {'PASS' if block['pass'] else 'FAIL'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
