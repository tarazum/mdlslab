"""Frozen CONT-006 V2 calibration verdict (prereg A.3, EVALUATION-PREP-
CONT006-V2.md; DESIGN-V2 §9).

Written BEFORE the calibration pilot runs (template §1; RC-4b discipline:
the --self-test over synthetic run roots ran BEFORE this file was digested
into frozen-config-cont006-v3.json). Reads the Phase CAL run root
(results/CONT-006-CAL/cont006-cal-*; R0+R2 x seeds {8001,8002} over the
full v3n set, memory ON, summaries written by run_cont006.py) and the
live-telemetry gate verdict that must have been produced FIRST (A.2.2
binding order: gate exit 0 before any analyzer reads the root).

Pre-declared checks (GO required for the transfer phases):
  1. Per-family headroom: EVERY TR family mean pass in (0.15, 0.85) for
     BOTH R0 and R2 (families cr/cu/rt/dx/dr; means over both seeds' probes
     pooled; exact_match probes only, gc excluded).
  2. Anchor: |R0 pooled TR pass - 0.525| <= 0.15 (the C2 memory-armed
     anchor; a larger divergence = halt & investigate — F-3).
  3. Live-telemetry gate verdict file present and PASS.
  4. Invalid-share (observed_label is None) < 0.30 per arm; wall
     feasibility NOTE (reported, not gating).

Verdict GO / STOP-OUT-OF-BAND with the offending numbers. Out of band ->
the chain STOPS: commit the record, write the owner brief, NO v3m edits,
NO parameter moves (a NEW suite is authored only after the owner decides).
In band -> the calibration cells are PART OF THE FINAL DATASET (single
freeze; CONT-002 pattern) and Phase P REUSES the R0/R2 cells
(resume semantics — never re-run inference for an existing healthy cell).

Exit 0 = GO; exit 2 = STOP-OUT-OF-BAND (the verdict file is written either
way — the STOP record is a legitimate, committable outcome).

--self-test (zero GPU): synthetic CAL roots for the in-band GO case, a
family-band breach, and an anchor breach.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]

TR_IDS = ["cr-8001", "cr-8002", "cr-8003", "cr-8004", "cu-8101", "cu-8102",
          "cu-8103", "cu-8104", "rt-8201", "rt-8202", "rt-8203", "dx-8401",
          "dx-8402", "dr-8301", "dr-8302"]
VAL_IDS = ["cr-8005", "cu-8105", "rt-8204", "dx-8403"]
CAL_SEEDS = [8001, 8002]
CAL_ARMS = ["R0", "R2"]
FAMILIES = ["cr", "cu", "rt", "dx", "dr"]
FAMILY_LO = 0.15
FAMILY_HI = 0.85
ANCHOR = 0.525
ANCHOR_TOL = 0.15
INVALID_MAX = 0.30
GPU_CAP_S = 300 * 60
DETERMINISM_CAVEAT = ("greedy+seed does not guarantee identical outputs "
                      "(PB-071, CN-003); per-seed content variants make seeds "
                      "true replicates regardless")


def load_cell(root: Path, arm: str, seed: int) -> dict | None:
    summary = root / arm / f"seed-{seed}" / "summary.json"
    if not summary.exists():
        return None
    return json.loads(summary.read_text(encoding="utf-8"))


def scored_probes(summary: dict, ids: list[str] | None = None) -> list[dict]:
    return [p for p in summary.get("probes", [])
            if p.get("kind") != "guess_calibration"
            and (ids is None or p.get("scenario") in ids)]


def analyze(root: Path) -> dict:
    criteria: list[dict] = []

    def rec(cid, status, detail):
        criteria.append({"criterion": cid, "status": status, "detail": detail})

    # data load (fail-closed on missing/incomplete cells)
    cells: dict[tuple, dict] = {}
    missing: list[str] = []
    for arm in CAL_ARMS:
        for sd in CAL_SEEDS:
            data = load_cell(root, arm, sd)
            if data is None or not data.get("completed"):
                missing.append(f"{arm}/seed-{sd}")
            else:
                cells[(arm, sd)] = data
    expected_probes = len(TR_IDS) + len(VAL_IDS)
    for key, data in sorted(cells.items()):
        if len(scored_probes(data)) != expected_probes:
            missing.append(f"{key[0]}/seed-{key[1]} "
                           f"({len(scored_probes(data))}/{expected_probes} scored probes)")
    if missing:
        rec("0-completeness", "STOP", f"incomplete cells: {missing}")
        report = verdict_record(root, criteria, "STOP-OUT-OF-BAND",
                                [c["criterion"] for c in criteria
                                 if c["status"] == "STOP"])
        return report

    # 1 per-family headroom (both arms; TR families only; pooled both seeds)
    family_means: dict[str, dict[str, float]] = {}
    breaches: list[str] = []
    for arm in CAL_ARMS:
        family_means[arm] = {}
        for fam in FAMILIES:
            ids = [sid for sid in TR_IDS if sid.startswith(fam + "-")]
            probes = [p for sd in CAL_SEEDS
                      for p in scored_probes(cells[(arm, sd)], ids)]
            mean = (sum(1 for p in probes if p.get("passed") is True) / len(probes)
                    if probes else None)
            family_means[arm][fam] = round(mean, 4) if mean is not None else None
            if mean is None or not (FAMILY_LO < mean < FAMILY_HI):
                breaches.append(f"{arm}/{fam}={mean}")
    rec("1-family-headroom", "PASS" if not breaches else "STOP",
        "; ".join(f"{a}/{f}={v}" for a in family_means for f, v in
                  family_means[a].items())
        + (f"; breaches (need strictly inside ({FAMILY_LO}, {FAMILY_HI})): "
           f"{breaches}" if breaches else ""))

    # 2 anchor (R0 pooled TR pass over both seeds)
    tr_probes = [p for sd in CAL_SEEDS for p in scored_probes(cells[("R0", sd)], TR_IDS)]
    r0_tr = (sum(1 for p in tr_probes if p.get("passed") is True) / len(tr_probes)
             if tr_probes else None)
    anchor_dev = abs(r0_tr - ANCHOR) if r0_tr is not None else None
    anchor_ok = anchor_dev is not None and anchor_dev <= ANCHOR_TOL
    rec("2-anchor", "PASS" if anchor_ok else "STOP",
        f"R0 pooled TR pass {r0_tr} vs anchor {ANCHOR} "
        f"(|dev| = {None if anchor_dev is None else round(anchor_dev, 4)} "
        f"<= {ANCHOR_TOL}; a larger divergence = halt & investigate — F-3)")

    # 3 live-gate verdict present and PASS (A.2.2: gate ran FIRST)
    gate_file = root / "live-telemetry-gate.json"
    gate_ok = False
    if gate_file.exists():
        gate = json.loads(gate_file.read_text(encoding="utf-8"))
        gate_ok = (gate.get("verdict") == "PASS" and gate.get("traces_checked", 0) > 0
                   and gate.get("failures") == 0)
        rec("3-live-gate", "PASS" if gate_ok else "STOP",
            f"{gate.get('verdict')} ({gate.get('traces_checked')} traces, "
            f"{gate.get('failures')} failures) -> {gate_file.name}")
    else:
        rec("3-live-gate", "STOP", f"verdict file missing: {gate_file}")

    # 4 invalid-share per arm + wall feasibility NOTE (never a gate)
    invalid = {}
    for arm in CAL_ARMS:
        probes = [p for sd in CAL_SEEDS for p in scored_probes(cells[(arm, sd)])]
        invalid[arm] = round(sum(1 for p in probes
                                 if p.get("observed_label") is None) / len(probes), 4)
    fmt_ok = all(v < INVALID_MAX for v in invalid.values())
    rec("4-invalid-share", "PASS" if fmt_ok else "STOP",
        f"invalid-format share per arm {invalid} (< {INVALID_MAX} each)")
    wall_note = None
    cells_file = root / "cells.json"
    if cells_file.exists():
        data = json.loads(cells_file.read_text(encoding="utf-8"))
        total = sum(c.get("wall_s", 0.0) for c in data.get("cells", {}).values())
        extrapolated = total * 7.0  # 4 cells -> 4 arms x 7 seeds
        wall_note = (f"CAL wall {total:.0f}s over 4 cells -> extrapolated "
                     f"7-seed 4-arm {extrapolated:.0f}s vs declared cap "
                     f"{GPU_CAP_S}s (NOTE: reported, not gating)")
    out = verdict_record(root, criteria, None, None)
    out["family_means"] = family_means
    out["r0_tr_pooled"] = r0_tr
    out["anchor_dev"] = None if anchor_dev is None else round(anchor_dev, 4)
    out["invalid_share"] = invalid
    out["wall_note"] = wall_note
    stopped = [c for c in criteria if c["status"] == "STOP"]
    out["verdict"] = "GO" if not stopped else "STOP-OUT-OF-BAND"
    out["offending"] = [c["criterion"] for c in stopped]
    return out


def verdict_record(root: Path, criteria: list[dict], verdict: str | None,
                   offending: list[str] | None) -> dict:
    return {
        "kind": "cont006-calibration-verdict",
        "prereg": "EVALUATION-PREP-CONT006-V2.md A.3 (frozen check)",
        "run_root": str(root),
        "criteria": criteria,
        "verdict": verdict,
        "offending": offending,
        "consequence": ("in band: the 4 calibration cells are PART OF THE FINAL "
                        "DATASET (single freeze); Phase P reuses the R0/R2 cells"
                        if verdict == "GO" else
                        "OUT OF BAND: the chain STOPS — commit the record, write "
                        "the owner brief, NO v3m edits, NO parameter moves; a NEW "
                        "suite is authored only after the owner decides"),
        "determinism_caveat": DETERMINISM_CAVEAT,
    }


# ----------------------------------------------------------------------------
# self-test (RC-4b: synthetic run roots, known answers — ran BEFORE freeze)
# ----------------------------------------------------------------------------

def _synthetic_root(tmp: Path, name: str, r0_tr_pass: float,
                    family_override: tuple[str, float] | None = None) -> Path:
    """Builds a CAL-shaped root: R0/R2 x seed-8001/8002 x 19 scored probes
    (+ 6 gc), a PASS live-gate verdict, and a cells.json with modest walls.
    r0_tr_pass drives the R0 TR pass pattern; family_override forces one
    R0 family's pass rate (family-band breach case)."""
    root = tmp / name
    for arm in CAL_ARMS:
        for sd in CAL_SEEDS:
            probes = []
            for sid in TR_IDS + VAL_IDS:
                fam = sid[:2]
                p_pass = r0_tr_pass if arm == "R0" else min(0.85, r0_tr_pass + 0.05)
                if family_override and arm == "R0" and sid.startswith(family_override[0] + "-"):
                    p_pass = family_override[1]
                # deterministic pattern: pass the first round(p*n) of 2
                n_pass = round(p_pass * 2)
                idx = (TR_IDS + VAL_IDS).index(sid)
                passed = (idx % 2) < n_pass
                probes.append({"kind": "exact_match", "scenario": sid, "family": fam,
                               "passed": passed, "observed_label": "x" if passed else "y",
                               "turn_ref": "s3t2"})
            for g in range(6):
                probes.append({"kind": "guess_calibration", "scenario": f"gc-750{g % 3 + 1}",
                               "passed": None, "observed_label": "a",
                               "observed_position": g % 6, "turn_ref": "s2t2"})
            cell = root / arm / f"seed-{sd}"
            cell.mkdir(parents=True)
            (cell / "summary.json").write_text(json.dumps({
                "kind": "cont006-arm-seed-summary", "arm": arm, "seed": sd,
                "completed": True, "probes": probes,
                "probes_passed": sum(1 for p in probes if p.get("passed") is True),
                "memory_episodes": 12, "duration_s": 240.0}, indent=1) + "\n",
                encoding="utf-8")
    (root / "live-telemetry-gate.json").write_text(json.dumps({
        "kind": "cont006-live-telemetry-gate", "run_root": str(root),
        "traces_checked": 4, "failures": 0, "verdict": "PASS"}, indent=1) + "\n",
        encoding="utf-8")
    (root / "cells.json").write_text(json.dumps({
        "kind": "cont006-cells", "cells": {f"{a}/seed-{s}": {"wall_s": 240.0}
                                           for a in CAL_ARMS for s in CAL_SEEDS}},
        indent=1) + "\n", encoding="utf-8")
    return root


def self_test() -> int:
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    # in-band GO: R0 TR pass 0.533 (16/30), all families inside the band,
    # anchor |0.533-0.525| = 0.008 <= 0.15
    r = analyze(_synthetic_root(tmp, "go", 16 / 30))
    assert r["verdict"] == "GO", r
    assert not r["offending"], r
    print("SELF-TEST PASS: in-band GO case")
    # family-band breach: cr family forced to 1.0 (> 0.85) — STOP
    r = analyze(_synthetic_root(tmp, "fam", 16 / 30, family_override=("cr", 1.0)))
    assert r["verdict"] == "STOP-OUT-OF-BAND", r
    assert "1-family-headroom" in r["offending"], r
    print("SELF-TEST PASS: family-band breach -> STOP-OUT-OF-BAND")
    # anchor breach: R0 TR pass 6/30 = 0.2 -> |0.2-0.525| = 0.325 > 0.15
    r = analyze(_synthetic_root(tmp, "anchor", 6 / 30))
    assert r["verdict"] == "STOP-OUT-OF-BAND", r
    assert "2-anchor" in r["offending"], r
    print("SELF-TEST PASS: anchor breach -> STOP-OUT-OF-BAND")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--run-root", default=None,
                        help="Phase CAL run root (results/CONT-006-CAL/cont006-cal-*)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if not args.run_root:
        raise SystemExit("--run-root required (or --self-test)")
    root = Path(args.run_root).resolve()
    report = analyze(root)
    out = root / "calibration-verdict.json"
    out.write_text(json.dumps(report, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print(f"CALIBRATION VERDICT: {report['verdict']}")
    for c in report["criteria"]:
        print(f"  [{c['status']}] {c['criterion']}: {c['detail'][:150]}")
    if report.get("wall_note"):
        print(f"  wall: {report['wall_note']}")
    print(f"written: {out}")
    return 0 if report["verdict"] == "GO" else 2


if __name__ == "__main__":
    raise SystemExit(main())
