"""CONT-005 CYCLE-2 CONFIRMATORY analysis — EXACTLY as frozen in
docs/EVALUATION-PREP-v3.md (FREEZE-B manifest; authoring order per its
section 10: this script is written FIRST, before fixtures/v3j is authored).

This script is part of the FREEZE-B MANIFEST (PREREG-REQUIREMENTS-V2 section 1):
its digest is recorded in frozen-config-v3b.json BEFORE any v3j inference, and
it must not change after the freeze. It implements:

  - Primary endpoint (section 3): label-form error rate (1 - pass, v3
    extraction scoring) over the 12 primary clusters (CR x8 + CU x4); per
    cluster the mean error over its 5 seed-variant observations.
  - Primary contrast (section 4): T0 - T1 (positive = the source/verification
    annotations REDUCE errors); two-sided, no post-hoc switch.
  - Decision rule (section 6): two-sided 95% cluster percentile bootstrap over
    the 12 clusters, 10,000 resamples, RNG seed 20261006 (recorded at
    FREEZE-B); frozen four-case wording incl. the reverse direction.
  - Completeness guard (section 7): all 12 clusters x 5 seeds in BOTH primary
    arms, else verdict "incomplete" (no substitution, no seed re-draws);
    secondary-arm incompleteness is reported, never voids the primary.
  - Variant-integrity guard (section 7): per-seed traps/expected are read from
    the FROZEN rendered v3j suite (render_seed_variant), so the analysis
    cannot silently drift from the suite the arms actually saw.
  - Echo checks: zero "[RESOLVED" in T2/T3 replies (flags moved to plain
    NOTE: prose at FREEZE-B, pre-authorized pilot clause-4 fix); residual
    "NOTE:" prose echo rate reported alongside the invalid-format rate.
  - Mandatory secondaries (section 8): wrong-label vs invalid-format
    decomposition; label-level scripted-trap repeat rate; between-seed spread
    with the n=5/df=4 chi-square CI; T2-T0 and T3-T0 post-fix re-measures
    (same bootstrap machinery, exploratory); DR/DX/RT family pass rates;
    per-arm guess rate/position; token cost per arm; CU superseded-value
    choice share.
  - Guess-band rule (section 12, v2 operationalization): guess_rate(arm) :=
    the maximum position share of that arm's guess-calibration replies
    (k = 6); band(arm) := |guess_rate - 1/6|; caveat when the primary delta
    < 2 x max-arm band — reported, never moves the MME.

Usage:
    python labs/continuity/experiments/suite-v3/analyze_confirmatory_v3.py \
        --run-root <confirmatory run dir> [--out <path>/results-summary.json]

Exit 0 on a well-formed report (including "incomplete"); exit 2 fail-closed on
structural violations (suite/run mismatch, probe-count drift).
"""

from __future__ import annotations

import argparse
import json
import math
import random
import statistics
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import load_suite_for_seed  # noqa: E402

# --- Frozen constants (EVALUATION-PREP-v3 sections 3-8, 12) ---
SEEDS = (3001, 3002, 3003, 3004, 3005)
PRIMARY_ARMS = ("T0", "T1")
SECONDARY_CONTRASTS = {"T2": 1, "T3": 2}  # arm -> RNG offset (T0 - arm)
ALL_ARMS = ("A", "T0", "T1", "T2", "T3")
PRIMARY_FAMILIES = {"correction_reuse", "contradiction_update"}
MME = 0.25
BOOT = 10_000
RNG_SEED = 20261006  # recorded at FREEZE-B (section 6)
GUESS_K = 6
ECHO_MARKER = "[RESOLVED"
NOTE_MARKER = "NOTE:"
# chi-square two-sided 95% quantiles, df=4 (n=5): sd CI multipliers
CHI2_DF4 = {"lo": 0.484419, "hi": 11.143287}
SD_CI_LO_MULT = math.sqrt(4.0 / CHI2_DF4["hi"])   # ~0.5995
SD_CI_HI_MULT = math.sqrt(4.0 / CHI2_DF4["lo"])   # ~2.8740

VERDICT_ESTABLISHED = "confirmatory difference established (annotations reduce errors)"
VERDICT_ESTABLISHED_REVERSE = (
    "confirmatory difference established in the reverse direction (annotations increase errors)"
)
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


def echo_scan(run_root: Path, arm: str) -> dict:
    """Bracket echo (must be zero post NOTE-fix) + residual NOTE: prose echo."""
    bracket = note = replies = 0
    for seed in SEEDS:
        for stem in (f"seed-{seed}", f"seed-{seed}-a2"):
            t = run_root / arm / stem / "trace.jsonl"
            if not t.exists():
                continue
            for line in t.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                if rec.get("type") == "agent.response":
                    content = rec.get("payload", {}).get("content", "")
                    replies += 1
                    if ECHO_MARKER in content:
                        bracket += 1
                    if NOTE_MARKER in content:
                        note += 1
    return {"arm": arm, "replies": replies, "bracket_hits": bracket, "note_hits": note}


def bootstrap_ci(cluster_deltas: list[float], rng_seed: int) -> tuple[float, float]:
    rng = random.Random(rng_seed)
    means = []
    for _ in range(BOOT):
        sample = [cluster_deltas[rng.randrange(len(cluster_deltas))] for _ in cluster_deltas]
        means.append(sum(sample) / len(sample))
    means.sort()
    return means[int(0.025 * (BOOT - 1))], means[int(0.975 * (BOOT - 1))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", required=True)
    parser.add_argument("--out", default=None)
    args = parser.parse_args()
    run_root = Path(args.run_root)

    # Frozen suite: per-seed rendered traps/expected (variant-integrity guard).
    suite_dir = str(LAB_ROOT / "fixtures" / "v3j")
    fam_of: dict[str, str] = {}
    trap_of: dict[tuple[int, str], str] = {}
    for seed in SEEDS:
        _, scenarios = load_suite_for_seed(suite_dir, seed)
        for s in scenarios:
            fam_of[s["id"]] = s["family"]
            trap_of[(seed, s["id"])] = s.get("seed_error", {}).get("value", "").lower()
    primary_ids = sorted(i for i, f in fam_of.items() if f in PRIMARY_FAMILIES)
    if len(primary_ids) != 12:
        print(f"FAIL-CLOSED: v3j primary cluster count {len(primary_ids)} != 12", file=sys.stderr)
        return 2

    summaries: dict[tuple[str, int], dict] = {}
    missing: list[str] = []
    for arm in ALL_ARMS:
        for seed in SEEDS:
            s = load_summary(run_root, arm, seed)
            if s is None or not s.get("completed"):
                missing.append(f"{arm}/seed-{seed}")
            else:
                summaries[(arm, seed)] = s

    primary_missing = [m for m in missing if m.split("/")[0] in PRIMARY_ARMS]
    secondary_missing = [m for m in missing if m.split("/")[0] not in PRIMARY_ARMS]
    complete_primary = not primary_missing

    # Structural guard: exactly one primary probe row per (arm, seed, cluster).
    cluster_errors: dict[str, dict[str, list[float]]] = {cid: {} for cid in primary_ids}
    structural_bad: list[str] = []
    if complete_primary:
        for arm in PRIMARY_ARMS:
            for seed in SEEDS:
                rows = primary_probe_rows(summaries[(arm, seed)])
                for cid in primary_ids:
                    hits = [r for r in rows if r["scenario"] == cid]
                    if len(hits) != 1:
                        structural_bad.append(f"{arm}/seed-{seed}/{cid}: {len(hits)} probes")
                        continue
                    cluster_errors[cid].setdefault(arm, []).append(0.0 if hits[0]["passed"] else 1.0)
        if structural_bad:
            print(f"FAIL-CLOSED: probe-count drift: {structural_bad[:5]}", file=sys.stderr)
            return 2

    # --- Primary contrast T0 - T1 (cluster percentile bootstrap) ---
    per_cluster: dict[str, dict[str, float]] = {}
    cluster_delta: list[float] = []
    delta = lo = hi = None
    if complete_primary:
        for cid in primary_ids:
            rates = {arm: statistics.fmean(cluster_errors[cid][arm]) for arm in PRIMARY_ARMS}
            per_cluster[cid] = rates
            cluster_delta.append(rates["T0"] - rates["T1"])
        delta = sum(cluster_delta) / len(cluster_delta)
        lo, hi = bootstrap_ci(cluster_delta, RNG_SEED)

    # --- Verdict (frozen four-case wording, section 6) ---
    if not complete_primary:
        verdict = VERDICT_INCOMPLETE
        verdict_note = (
            "primary arm-seeds incomplete; no substitution, no seed re-draws "
            "(EVALUATION-PREP-v3 section 7)"
        )
    elif lo > 0.0 or hi < 0.0:
        if delta >= MME:
            verdict = VERDICT_ESTABLISHED
        elif delta <= -MME:
            verdict = VERDICT_ESTABLISHED_REVERSE
        else:
            verdict = VERDICT_SUB_MME
        verdict_note = None
    else:
        verdict = VERDICT_NONE
        verdict_note = None

    # --- Error decomposition (wrong-label vs invalid-format, primary arms) ---
    decomposition: dict[str, dict[str, int]] = {}
    for arm in ALL_ARMS:
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

    # --- Label-level scripted-trap repeat rate (reply == trap label) ---
    trap_repeat: dict[str, dict[str, int]] = {}
    for arm in ALL_ARMS:
        eligible = repeats = 0
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for sc in summaries[(arm, seed)]["scenario_summaries"]:
                sid = sc["scenario"]
                if fam_of.get(sid) not in PRIMARY_FAMILIES:
                    continue
                trap = trap_of.get((seed, sid), "")
                if not trap:
                    continue
                for p in sc["probes"]:
                    if p["passed"] is None:
                        continue
                    eligible += 1
                    if p.get("observed_normalized") == trap:
                        repeats += 1
        trap_repeat[arm] = {"eligible": eligible, "trap_repeats": repeats}

    # --- CU superseded-value choice share (old value chosen inside options) ---
    cu_trap_share: dict[str, dict] = {}
    for arm in ALL_ARMS:
        chosen = valid = 0
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for sc in summaries[(arm, seed)]["scenario_summaries"]:
                sid = sc["scenario"]
                if fam_of.get(sid) != "contradiction_update":
                    continue
                trap = trap_of.get((seed, sid), "")
                for p in sc["probes"]:
                    if p["passed"] is None:
                        continue
                    if p.get("observed_label") is not None:
                        valid += 1
                        if p["observed_normalized"] == trap:
                            chosen += 1
        cu_trap_share[arm] = {"valid": valid, "chose_superseded": chosen,
                              "share": round(chosen / valid, 3) if valid else None}

    # --- Between-seed spread (per-arm sd of the 5 per-seed primary means) ---
    spread_rows = []
    for arm in ALL_ARMS:
        vals = []
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            rows = primary_probe_rows(summaries[(arm, seed)])
            if len(rows) != len(primary_ids):
                continue
            vals.append(statistics.fmean([0.0 if r["passed"] else 1.0 for r in rows]))
        if len(vals) < len(SEEDS):
            spread_rows.append({"arm": arm, "note": "incomplete; skipped"})
            continue
        sd = statistics.stdev(vals)
        spread_rows.append({
            "arm": arm,
            "per_seed_primary_means": [round(v, 4) for v in vals],
            "sd": round(sd, 4),
            "sd_ci95": [round(sd * SD_CI_LO_MULT, 4), round(sd * SD_CI_HI_MULT, 4)],
        })

    # --- Guess band (v2 operationalization) ---
    guess: dict[str, dict] = {}
    for arm in ALL_ARMS:
        positions: dict[int, int] = {}
        n = valid = 0
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for sc in summaries[(arm, seed)]["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is not None:
                        continue
                    n += 1
                    if p.get("observed_label") is not None:
                        valid += 1
                    if p.get("observed_position") is not None:
                        positions[p["observed_position"]] = positions.get(p["observed_position"], 0) + 1
        share = (max(positions.values()) / n) if n and positions else None
        guess[arm] = {
            "guess_probes": n,
            "valid_label_fraction": round(valid / n, 3) if n else None,
            "max_position_share": round(share, 3) if share is not None else None,
            "band": round(abs(share - 1.0 / GUESS_K), 3) if share is not None else None,
        }
    max_band = max((g["band"] or 0.0) for g in guess.values())
    guess_caveat = delta is not None and delta < 2 * max_band

    # --- Secondary contrasts T0-T2 / T0-T3 (post-fix re-measures) ---
    secondary_contrasts = {}
    for sec_arm, offset in SECONDARY_CONTRASTS.items():
        usable = complete_primary and all(
            (sec_arm, seed) in summaries for seed in SEEDS
        )
        if not usable:
            secondary_contrasts[f"T0-{sec_arm}"] = {"note": "incomplete; skipped"}
            continue
        deltas = []
        per_cluster_sec = {}
        for cid in primary_ids:
            rates = {"T0": statistics.fmean(cluster_errors[cid]["T0"])}
            errs = []
            for seed in SEEDS:
                rows = [r for r in primary_probe_rows(summaries[(sec_arm, seed)])
                        if r["scenario"] == cid]
                if len(rows) != 1:
                    structural_bad.append(f"{sec_arm}/seed-{seed}/{cid}: {len(rows)} probes")
                    errs = None
                    break
                errs.append(0.0 if rows[0]["passed"] else 1.0)
            if errs is None:
                continue
            rates[sec_arm] = statistics.fmean(errs)
            per_cluster_sec[cid] = rates
            deltas.append(rates["T0"] - rates[sec_arm])
        if len(deltas) != 12:
            secondary_contrasts[f"T0-{sec_arm}"] = {
                "note": f"probe-count drift: {structural_bad[-3:]}"}
            continue
        s_delta = sum(deltas) / len(deltas)
        s_lo, s_hi = bootstrap_ci(deltas, RNG_SEED + offset)
        secondary_contrasts[f"T0-{sec_arm}"] = {
            "per_cluster": per_cluster_sec,
            "delta_mean": round(s_delta, 4),
            "ci95": [round(s_lo, 4), round(s_hi, 4)],
            "bootstrap": {"resamples": BOOT, "rng_seed": RNG_SEED + offset,
                          "method": "cluster percentile"},
            "note": "secondary/exploratory: cycle-1 contrast re-measured post-fix; not promotable",
        }

    # --- Family pass rates (all arms, all scored families) ---
    fam_table: dict[str, dict[str, list[int]]] = {}
    for arm in ALL_ARMS:
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            for sc in summaries[(arm, seed)]["scenario_summaries"]:
                for p in sc["probes"]:
                    if p["passed"] is None:
                        continue
                    fam_table.setdefault(sc["family"], {}).setdefault(arm, []).append(
                        1 if p["passed"] else 0)
    fam_summary = {
        f: {a: round(statistics.fmean(v), 3) for a, v in arms.items()}
        for f, arms in sorted(fam_table.items())
    }

    # --- Tokens / wall accounting ---
    tokens_wall = {}
    for arm in ALL_ARMS:
        walls, tokens = [], 0
        for seed in SEEDS:
            if (arm, seed) not in summaries:
                continue
            walls.append(summaries[(arm, seed)]["wall_s"])
            tokens += summaries[(arm, seed)]["tokens_total"]
        tokens_wall[arm] = {
            "wall_s_sum": round(sum(walls), 1) if walls else None,
            "tokens_sum": tokens,
            "arm_seeds_present": len(walls),
        }

    # --- Execution revs (multi-rev pre-declared, section 11) ---
    revs: dict[str, list[str]] = {}
    for arm in ALL_ARMS:
        all_revs: list[str] = []
        for seed in SEEDS:
            for rev in trace_revs(run_root, arm, seed):
                if rev not in all_revs:
                    all_revs.append(rev)
        revs[arm] = all_revs

    # --- Echo scans (T2/T3) ---
    echo_rows = [echo_scan(run_root, arm) for arm in ("T2", "T3")]

    report = {
        "kind": "cont005-c2-confirmatory-results",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spec": "docs/EVALUATION-PREP-v3.md (FREEZE-B) sections 3-8, 12",
        "run_root": str(run_root),
        "execution_revs": revs,
        "completeness": {
            "primary_missing": primary_missing,
            "secondary_missing": secondary_missing,
            "verdict_blocking": bool(primary_missing),
        },
        "primary": {
            "endpoint": "label-form error rate, 12 CR+CU clusters, structural eligibility",
            "contrast": "T0 - T1",
            "per_cluster": {cid: {a: round(v, 3) for a, v in r.items()}
                            for cid, r in per_cluster.items()},
            "delta_mean": round(delta, 4) if delta is not None else None,
            "ci95": [round(lo, 4), round(hi, 4)] if lo is not None else None,
            "mme": MME,
            "bootstrap": {"resamples": BOOT, "rng_seed": RNG_SEED,
                          "method": "cluster percentile"},
            "verdict": verdict,
            "direction_note": "positive delta = T1 annotations reduce errors relative to flat T0",
        },
        "echo_checks": {
            "spec": "pilot clause-4 fix applied at FREEZE-B: flags are plain NOTE: prose",
            "rows": echo_rows,
            "bracket_hits_total": sum(r["bracket_hits"] for r in echo_rows),
        },
        "error_decomposition_primary": decomposition,
        "trap_repeat_label_level": trap_repeat,
        "cu_superseded_value_choice": cu_trap_share,
        "between_seed_spread": spread_rows,
        "guess_band": {
            "operationalization": "guess_rate(arm) = max position share of guess replies; band = |guess_rate - 1/6|",
            "per_arm": guess,
            "max_band": round(max_band, 3),
            "caveat_fires": bool(guess_caveat),
            "caveat": "primary effect does not clear the guessing band" if guess_caveat else None,
        },
        "secondary_contrasts": secondary_contrasts,
        "family_pass_by_arm": fam_summary,
        "tokens_wall": tokens_wall,
    }
    if verdict_note:
        report["primary"]["verdict_note"] = verdict_note

    out = Path(args.out) if args.out else run_root / "results-summary.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"VERDICT: {verdict}")
    if delta is not None:
        print(f"  primary delta (T0-T1) = {delta:.4f}, 95% CI [{lo:.4f}, {hi:.4f}], MME {MME}")
    if guess_caveat:
        print("  caveat: primary effect does not clear the guessing band")
    print(f"  written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
