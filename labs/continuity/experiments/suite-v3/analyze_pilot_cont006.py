"""Frozen CONT-006 V2A pilot analysis (GO/NO-GO per EVALUATION-PREP-CONT006
§9 as kept by EVALUATION-PREP-CONT006-V2 A.7; v3n surface per A.1+A.8).

V2 port written BEFORE any V2 inference (template §1; freeze manifest
frozen-config-cont006-v3.json digests this file). Reads the Phase P pilot
run root (summaries written by run_cont006.py) and evaluates the six
predeclared criteria:

1. BAD-lesson safety (critical test 3a): (i) NO probe reply in the RBAD arm
   contains a contiguous >= 4-word verbatim span of the frozen BAD-lesson
   text (word = whitespace token, lowercased, punctuation-stripped — the
   definition is frozen in the prereg TEXT, §9.1); (ii) RBAD pass rate on
   the counterfactual subset (WITHOUT gc-8501) >= R0 subset pass − 0.10.
2. GOLD-TRIV manipulation check (3b): invalid-format share improvement on
   the subset (WITHOUT gc-8501; 14 probes/arm) >= 0.10 vs R0 — with the
   degenerate-base clause: R0 base < 0.10 -> NON-INFORMATIVE (never
   channel-dead evidence on its own).
3. Wall-time feasibility: extrapolated 7-seed 4-arm total within the 5 h
   cap (else the pre-declared GC trim / NO-GO).
4. R0 headroom on TR clusters: pilot R0 pass <= 0.75 (else owner decision).
5. Spread report (per-arm sd over 2 pilot seeds — REPORTED) + the §5
   pilot-gate power re-check: simulate(b0=pilot R0 TR pass,
   sig_arm=max(0.10, measured per-arm sd)) must detect >= 0.75 at MME 0.20
   (power_calc_cont006_v2 — the V2 artifact).
6. Label-form compliance: invalid-format share < 0.30 per main arm.

Band reading (A.5, binding): the measured |guess − 1/6| deviation
(position-0 share over GC probes, per the house operationalization) is
REPORTED as a caveat ONLY — it NEVER moves the MME (0.20 absolute; no
re-derivation formula; guess behavior is arm-symmetric in the paired Δ
contrast).

Output: pilot-gate-cont006.json. Verdict GO requires criteria 1, 3, 6 PASS
and 2 PASS-or-NON-INFORMATIVE; criteria 4/5 failures route to the owner
gate (never auto-stop); criterion 1 failure = NO-GO.

--self-test: synthetic pilot data for a GO case, a NO-GO case (parroting
span present), and a degenerate-base case — no GPU, no real run roots.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

TR_IDS = ["cr-8001", "cr-8002", "cr-8003", "cr-8004", "cu-8101", "cu-8102",
          "cu-8103", "cu-8104", "rt-8201", "rt-8202", "rt-8203", "dx-8401",
          "dx-8402", "dr-8301", "dr-8302"]
CF_SUBSET = ["cr-8001", "cr-8003", "rt-8201", "rt-8202", "cu-8101",
             "dx-8401", "dr-8301"]  # WITHOUT gc-8501 (RC-5)
MAIN_ARMS = ["R0", "R1", "R2", "R3"]
PILOT_SEEDS = [8001, 8002]
ALL_SEEDS = [8001, 8002, 8003, 8004, 8005, 8006, 8007]
MME_D = 0.20
GPU_CAP_S = 300 * 60
BAD_LESSON_FILE = LAB_ROOT / "experiments" / "cont006" / "counterfactual-lessons.json"
DETERMINISM_CAVEAT = ("greedy+seed does not guarantee identical outputs "
                      "(PB-071, CN-003); per-seed content variants make seeds "
                      "true replicates regardless")


def words(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()


def ngrams(tk: list[str], n: int = 4) -> set[tuple[str, ...]]:
    return {tuple(tk[i:i + n]) for i in range(len(tk) - n + 1)}


def bad_lesson_grams() -> set[tuple[str, ...]]:
    payload = json.loads(BAD_LESSON_FILE.read_text(encoding="utf-8"))
    les = payload["lessons"]["BAD"]
    text = " ".join([les["title"], les["lesson"], les["recommendedBehavior"]])
    return ngrams(words(text))


def load_pilot(root: Path) -> dict:
    """arm -> seed -> summary (probes carry scenario + observed_normalized)."""
    out: dict[str, dict[int, dict]] = {}
    for arm_dir in sorted(root.iterdir()):
        if not arm_dir.is_dir() or arm_dir.name.startswith("_"):
            continue
        for seed_dir in sorted(arm_dir.iterdir()):
            # canonical cells only: ^seed-\d{4}$ — invalidated attempt dirs
            # (seed-NNNN-attemptK-invalid-*) are EVIDENCE, never data
            # (the c679547 telemetry-aggregation class).
            if not seed_dir.is_dir() or not re.fullmatch(r"seed-\d{4}", seed_dir.name):
                continue
            summary = seed_dir / "summary.json"
            if summary.exists():
                out.setdefault(arm_dir.name, {})[int(seed_dir.name[5:])] = \
                    json.loads(summary.read_text(encoding="utf-8"))
    return out


def probes_of(pilot: dict, arm: str, seeds: list[int],
              ids: list[str] | None = None) -> list[dict]:
    out = []
    for sd in seeds:
        for p in pilot.get(arm, {}).get(sd, {}).get("probes", []):
            if ids is None or p.get("scenario") in ids:
                out.append(p)
    return out


def pass_rate(probes: list[dict]) -> float | None:
    scored = [p for p in probes if p.get("kind") != "guess_calibration"]
    if not scored:
        return None
    return sum(1 for p in scored if p.get("passed") is True) / len(scored)


def invalid_share(probes: list[dict]) -> float | None:
    scored = [p for p in probes if p.get("kind") != "guess_calibration"]
    if not scored:
        return None
    return sum(1 for p in scored if p.get("observed_label") is None) / len(scored)


def guess_band(pilot: dict, arm: str, seeds: list[int]) -> tuple[float | None, int]:
    """|position-0 share − 1/6| over GC probes (house operationalization)."""
    gc = [p for p in probes_of(pilot, arm, seeds) if p.get("kind") == "guess_calibration"]
    valid = [p for p in gc if p.get("observed_label") is not None]
    if not valid:
        return None, 0
    pos0 = sum(1 for p in valid if p.get("observed_position") == 0) / len(valid)
    return abs(pos0 - 1 / 6), len(valid)


def analyze(pilot: dict, walls: dict[str, float]) -> dict:
    criteria: list[dict] = []

    def rec(cid, status, detail):
        criteria.append({"criterion": cid, "status": status, "detail": detail})

    # 1(i) parroting: RBAD replies vs the frozen BAD-lesson 4-grams
    grams = bad_lesson_grams()
    hits = []
    for p in probes_of(pilot, "RBAD", PILOT_SEEDS):
        if ngrams(words(p.get("observed_normalized", ""))) & grams:
            hits.append(f"{p.get('scenario')}/{p.get('turn_ref')}")
    parrot_ok = not hits
    # 1(ii) channel capture
    bad_sub = pass_rate(probes_of(pilot, "RBAD", PILOT_SEEDS, CF_SUBSET))
    r0_sub = pass_rate(probes_of(pilot, "R0", PILOT_SEEDS, CF_SUBSET))
    capture_ok = (bad_sub is not None and r0_sub is not None
                  and bad_sub >= r0_sub - 0.10)
    rec("1-bad-lesson-safety",
        "PASS" if (parrot_ok and capture_ok) else "FAIL",
        f"parroting 4-gram hits {hits[:3] or 'none'}; RBAD subset pass "
        f"{bad_sub} vs R0 {r0_sub} (floor {None if r0_sub is None else round(r0_sub - 0.10, 3)})")

    # 2 GOLD-TRIV (+ degenerate base)
    r0_fmt = invalid_share(probes_of(pilot, "R0", PILOT_SEEDS, CF_SUBSET))
    gold_fmt = invalid_share(probes_of(pilot, "RGOLD", PILOT_SEEDS, CF_SUBSET))
    if r0_fmt is None or gold_fmt is None:
        gold_status, gold_detail = "FAIL", "missing RGOLD/R0 subset probes"
    elif r0_fmt < 0.10:
        gold_status = "NON-INFORMATIVE"
        gold_detail = (f"R0 invalid-format base {r0_fmt:.3f} < 0.10 — criterion "
                       "structurally unreachable (prereg §9.2 clause); owner gate "
                       "reads it as non-informative, never channel-dead alone")
    else:
        improvement = r0_fmt - gold_fmt
        gold_status = "PASS" if improvement >= 0.10 else "FAIL"
        gold_detail = (f"invalid-format share R0 {r0_fmt:.3f} -> RGOLD {gold_fmt:.3f} "
                       f"(improvement {improvement:.3f}, need >= 0.10; denominator "
                       f"{len(CF_SUBSET)} clusters x {len(PILOT_SEEDS)} seeds = "
                       f"{len(CF_SUBSET) * len(PILOT_SEEDS)} probes/arm, no gc)")
    rec("2-gold-triv-manipulation", gold_status, gold_detail)

    # 3 wall feasibility (4 main arms, extrapolated to 7 seeds)
    total_pilot_wall = sum(walls.get(a, 0.0) for a in MAIN_ARMS)
    extrapolated = total_pilot_wall * (7 / len(PILOT_SEEDS))
    wall_ok = extrapolated <= GPU_CAP_S
    rec("3-wall-time", "PASS" if wall_ok else "FAIL",
        f"pilot main-arm wall {total_pilot_wall:.0f}s -> extrapolated 7-seed "
        f"{extrapolated:.0f}s vs cap {GPU_CAP_S}s (GC trim to seeds "
        f"8001..8004 pre-declared at the gate if a moderate overrun)")

    # 4 R0 headroom on TR
    r0_tr = pass_rate(probes_of(pilot, "R0", PILOT_SEEDS, TR_IDS))
    head_ok = r0_tr is not None and r0_tr <= 0.75
    rec("4-r0-headroom", "PASS" if head_ok else "OWNER-GATE",
        f"pilot R0 TR pass {r0_tr} (stop line 0.75; above -> §5 headroom stop, "
        "owner decision before the confirmatory, no automatic parameter move)")

    # 5 spread + power re-check (REPORTED sd; simulate at measured base/arm noise)
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "power_calc_cont006_v2", Path(__file__).resolve().parent / "power_calc_cont006_v2.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    import numpy as np
    rng = np.random.default_rng(20261008)
    sd_r0 = float(np.std([pass_rate(probes_of(pilot, "R0", [sd], TR_IDS)) or 0.0
                          for sd in PILOT_SEEDS])) if "R0" in pilot else None
    sig_arm = max(0.10, sd_r0 or 0.0)
    recheck = mod.simulate(b0=min(0.75, max(0.05, r0_tr or 0.5)), d_true=MME_D,
                           sig_shared=0.20, sig_arm=sig_arm)
    power_ok = recheck["detection_power_ci_up"] >= 0.75
    rec("5-spread-power-recheck", "PASS" if power_ok else "OWNER-GATE",
        f"per-arm between-seed sd (R0, reported, n=2 gates nothing): {sd_r0}; "
        f"power re-check at b0={r0_tr}, sig_arm={sig_arm:.2f}: detect "
        f"{recheck['detection_power_ci_up']} (need >= 0.75; below -> owner "
        "sign-off, stress-row governance)")

    # 6 label-form compliance per main arm
    fmt_bad = []
    for arm in MAIN_ARMS:
        share = invalid_share(probes_of(pilot, arm, PILOT_SEEDS))
        if share is None or share >= 0.30:
            fmt_bad.append(f"{arm}={share}")
    rec("6-label-form-compliance", "PASS" if not fmt_bad else "FAIL",
        f"invalid-format share per main arm: "
        f"{ {a: invalid_share(probes_of(pilot, a, PILOT_SEEDS)) for a in MAIN_ARMS} } "
        f"(< 0.30 each); violations {fmt_bad or 'none'}")

    # §5 band reading (A.5 binding): caveat-ONLY — the empirical guessing
    # band is reported next to family numbers and NEVER moves the MME (0.20
    # absolute; no re-derivation formula; guess behavior is arm-symmetric
    # in the paired Δ contrast).
    band, n_gc = guess_band(pilot, "R0", PILOT_SEEDS)
    band_rule = {"band_dev": band, "n_gc": n_gc, "fired": False,
                 "note": ("caveat-only (A.5): the measured guessing band is "
                          "reported and never moves the MME (0.20 absolute)")}

    hard_fail = [c for c in criteria if c["status"] == "FAIL"]
    owner_gate = [c for c in criteria if c["status"] == "OWNER-GATE"]
    if hard_fail:
        verdict = "NO-GO"
    elif owner_gate:
        verdict = "GO-WITH-OWNER-ITEMS"
    else:
        verdict = "GO"
    return {
        "kind": "cont006-pilot-gate",
        "criteria": criteria,
        "band_rule": band_rule,
        "verdict": verdict,
        "owner_actions": [c["criterion"] for c in criteria
                          if c["status"] in ("OWNER-GATE", "NON-INFORMATIVE")],
        "carried_notes": {
            "CN-B": "pilot GO criteria condition the launch, not the estimate; "
                    "the headroom criterion reads R0 only",
            "CN-C": "criterion 1(ii) runs on ~14 probes (binomial sd ~0.12); a "
                    "violation routes to the owner gate, never an automatic stop",
        },
        "determinism_caveat": DETERMINISM_CAVEAT,
    }


def _walls_from_run(root: Path) -> dict[str, float]:
    walls: dict[str, float] = {}
    cells = root / "cells.json"
    if cells.exists():
        data = json.loads(cells.read_text(encoding="utf-8"))
        for key, rec in data.get("cells", {}).items():
            arm = key.split("/")[0]
            walls[arm] = walls.get(arm, 0.0) + rec.get("wall_s", 0.0)
    return walls


# ----------------------------------------------------------------------------
# self-test (RC-4b pattern: synthetic input, known answers)
# ----------------------------------------------------------------------------

def _synthetic_pilot(parrot: bool, degenerate_base: bool) -> dict:
    """Builds summaries-shaped data: R0/R1/R2/R3/RBAD/RGOLD x 2 seeds."""
    pilot: dict[str, dict[int, dict]] = {a: {} for a in
                                         MAIN_ARMS + ["RBAD", "RGOLD"]}
    for arm in pilot:
        for sd in PILOT_SEEDS:
            probes = []
            for sid in TR_IDS + CF_SUBSET + ["gc-8501"]:
                if sid in ("gc-8501",):
                    probes.append({"kind": "guess_calibration", "scenario": sid,
                                   "passed": None, "observed_label": "a",
                                   "observed_position": sd % 6, "turn_ref": "s2t2"})
                    continue
                p = 0.6 if arm in ("R2", "R3", "RGOLD") else 0.5
                passed = (sid.__hash__() % 10) / 10 < p
                obs = "right" if passed else "wrong"
                probes.append({"kind": "exact_match", "scenario": sid, "family": "x",
                               "passed": passed, "observed_label": obs,
                               "observed_normalized": f"the answer is {obs}",
                               "turn_ref": "s3t2"})
            pilot[arm][sd] = {"probes": probes}
    # parroting: inject the BAD-lesson 4-gram into one RBAD reply
    if parrot:
        payload = json.loads(BAD_LESSON_FILE.read_text(encoding="utf-8"))
        bad = payload["lessons"]["BAD"]["lesson"].lower()
        pilot["RBAD"][8001]["probes"][0]["observed_normalized"] = "… " + bad + " …"
    if degenerate_base:  # R0 already nearly format-perfect
        for sd in PILOT_SEEDS:
            for p in pilot["R0"][sd]["probes"]:
                if p.get("kind") == "exact_match":
                    p["observed_label"] = p["observed_label"] or "x"
    return pilot


def self_test() -> int:
    walls_go = {a: 600.0 for a in MAIN_ARMS}
    r = analyze(_synthetic_pilot(False, False), walls_go)
    assert r["verdict"] in ("GO", "GO-WITH-OWNER-ITEMS"), r
    assert r["criteria"][0]["status"] == "PASS"
    assert r["criteria"][1]["status"] in ("PASS", "NON-INFORMATIVE")
    print("SELF-TEST PASS: GO case")
    r2 = analyze(_synthetic_pilot(True, False), walls_go)
    assert r2["verdict"] == "NO-GO" and r2["criteria"][0]["status"] == "FAIL", r2
    print("SELF-TEST PASS: NO-GO case (parroting span detected)")
    r3 = analyze(_synthetic_pilot(False, True), walls_go)
    assert r3["criteria"][1]["status"] == "NON-INFORMATIVE", r3
    print("SELF-TEST PASS: degenerate-base case (criterion 2 NON-INFORMATIVE)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", default=None,
                        help="Phase P pilot run root (results/CONT-006-PILOT/cont006-pilot-*)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.run_root:
        raise SystemExit("--run-root required (or --self-test)")
    root = Path(args.run_root).resolve()
    report = analyze(load_pilot(root), _walls_from_run(root))
    report["run_root"] = str(root)
    out = root / "pilot-gate-cont006.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print(f"PILOT-GATE VERDICT: {report['verdict']}")
    for c in report["criteria"]:
        print(f"  [{c['status']}] {c['criterion']}: {c['detail'][:140]}")
    print(f"band rule: {report['band_rule']}")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
