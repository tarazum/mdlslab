"""EXPLORATORY analysis of the sealed G8B stage-2 block (owner-authorized
2026-10-11, STOP option C; ROADMAP "Owner decisions — recorded
2026-10-11" item 2).

NOT the pre-registered analysis. analyze_stage2.py (frozen) is fail-closed
on gate-PASS.json over the full 14-cell run root, which does not exist by
design after STOP-OUT-OF-BAND — this script therefore imports its loading
helpers read-only and reports DIAGNOSTICS ONLY:

  - no confirmatory branches, no MME verdicts, no retroactive endpoints;
  - paired cluster bootstrap CIs are descriptive (same mechanics as the
    prereg bootstrap, fixed seed, labels stripped);
  - Q35 cells: NONE only (the gated baseline) — recorded here as the
    bounded ceiling result (STOP option D), not contrasted.

Output: exploratory-g8b.json next to the run root + human summary on
stdout. Zero GPU; reads committed artifacts only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
import stage2_design as D                     # noqa: E402  (frozen, read-only)
from analyze_stage2 import (                  # noqa: E402  (frozen, read-only)
    load_cell, six_gram_echo,
)

RUN_ROOT = Path(__file__).parents[2] / "results" / "CONT-006-STAGE2" \
    / "cont006-s2-20261011-120000"
OUT = RUN_ROOT / "exploratory-g8b.json"

BOOT = 10_000
RNG_SEED = 20261011  # distinct from the prereg seed; this is exploratory

G8B_CELLS = [
    ("NONE", "none"),
    ("NEWF2", "probe_time"),
    ("NEWF2", "session_start"),
    ("NEUTRAL", "probe_time"),
    ("NEUTRAL", "session_start"),
    ("OLDG", "probe_time"),
    ("OLDG", "session_start"),
]

PRIMARY = list(D.PRIMARY_CLUSTERS)
VAL = list(D.VALIDATION_CLUSTERS)
GC = list(D.GC_IDS)
FAMILIES = ("cr", "cu", "rt", "dx", "dr")


def matrix(cell, clusters):
    return np.array([[cell[c][str(s)]["passed"] for s in D.SEEDS]
                     for c in clusters], dtype=float)


def boot_ci(a, b):
    """Paired cluster-mean delta, percentile CI. Descriptive only."""
    rng = np.random.default_rng(RNG_SEED)
    d_c = a.mean(axis=1) - b.mean(axis=1)
    idx = rng.integers(0, len(d_c), size=(BOOT, len(d_c)))
    lo, hi = np.percentile(d_c[idx].mean(axis=1), [2.5, 97.5])
    return {"d": round(float(d_c.mean()), 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "ci_excludes_zero": bool(lo > 0 or hi < 0)}


def error_modes(cell):
    wl = fm = 0
    for c in PRIMARY:
        for s in D.SEEDS:
            r = cell[c][str(s)]
            if not r["passed"]:
                if r["observed_label"] is None:
                    fm += 1
                else:
                    wl += 1
    return {"wrong_label": wl, "format_miss": fm}


def echo_count(cell, content):
    hits = 0
    for c in PRIMARY:
        block = D.block_for(content, c)
        for s in D.SEEDS:
            reply = cell[c][str(s)]["observed_label"]
            if block and isinstance(reply, str) and reply \
                    and six_gram_echo(block, reply):
                hits += 1
    return hits


def main() -> int:
    cells = {}
    for content, pos in G8B_CELLS:
        cells[(content, pos)] = load_cell(RUN_ROOT, "G8B", content, pos)
        missing = [c for c in PRIMARY if c not in cells[(content, pos)]]
        if missing:
            raise SystemExit(f"G8B {content}-{pos}: missing clusters {missing}")

    none = cells[("NONE", "none")]
    qnone = load_cell(RUN_ROOT, "Q35", "NONE", "none")

    out = {
        "kind": "cont006-stage2-exploratory-g8b",
        "status": "EXPLORATORY ONLY — owner-authorized diagnostics on the "
                  "sealed G8B block after STOP-OUT-OF-BAND; no confirmatory "
                  "verdict, no retroactive endpoint change; Q35 treatment "
                  "cells were never run",
        "run_root": RUN_ROOT.name,
        "seeds": list(D.SEEDS),
        "primary_clusters": len(PRIMARY),
    }

    # -- pooled rates per cell ------------------------------------------
    out["g8b_pooled_primary"] = {
        f"{c}@{p}": round(float(matrix(cells[(c, p)], PRIMARY).mean()), 4)
        for c, p in G8B_CELLS
    }

    # -- contrasts of interest (review §"Questions worth answering") ----
    contrasts = {
        "NEWF2@pt - NONE": boot_ci(matrix(cells[("NEWF2", "probe_time")], PRIMARY),
                                   matrix(none, PRIMARY)),
        "NEWF2@ss - NONE": boot_ci(matrix(cells[("NEWF2", "session_start")], PRIMARY),
                                   matrix(none, PRIMARY)),
        "NEWF2@pt - NEUTRAL@pt": boot_ci(matrix(cells[("NEWF2", "probe_time")], PRIMARY),
                                         matrix(cells[("NEUTRAL", "probe_time")], PRIMARY)),
        "NEWF2@ss - NEUTRAL@ss": boot_ci(matrix(cells[("NEWF2", "session_start")], PRIMARY),
                                         matrix(cells[("NEUTRAL", "session_start")], PRIMARY)),
        "OLDG@pt - NEWF2@pt": boot_ci(matrix(cells[("OLDG", "probe_time")], PRIMARY),
                                      matrix(cells[("NEWF2", "probe_time")], PRIMARY)),
        "OLDG@ss - NEWF2@ss": boot_ci(matrix(cells[("OLDG", "session_start")], PRIMARY),
                                      matrix(cells[("NEWF2", "session_start")], PRIMARY)),
        "position ss-pt (NEWF2)": boot_ci(matrix(cells[("NEWF2", "session_start")], PRIMARY),
                                          matrix(cells[("NEWF2", "probe_time")], PRIMARY)),
        "position ss-pt (NEUTRAL)": boot_ci(matrix(cells[("NEUTRAL", "session_start")], PRIMARY),
                                            matrix(cells[("NEUTRAL", "probe_time")], PRIMARY)),
        "position ss-pt (OLDG)": boot_ci(matrix(cells[("OLDG", "session_start")], PRIMARY),
                                         matrix(cells[("OLDG", "probe_time")], PRIMARY)),
    }
    out["contrasts_descriptive"] = contrasts

    # -- VAL activation (NEWF2@pt vs NONE; both cells ran VAL) ----------
    out["val_activation"] = {
        "clusters": len(VAL),
        "NONE": round(float(matrix(none, VAL).mean()), 4),
        "NEWF2@pt": round(float(matrix(cells[("NEWF2", "probe_time")], VAL).mean()), 4),
        "delta_ci": boot_ci(matrix(cells[("NEWF2", "probe_time")], VAL),
                            matrix(none, VAL)),
    }

    # -- per-family rates ------------------------------------------------
    fam = {}
    for f in FAMILIES:
        clusters = [c for c in PRIMARY if c.startswith(f)]
        fam[f] = {
            f"{c}@{p}": round(float(matrix(cells[(c, p)], clusters).mean()), 4)
            for c, p in G8B_CELLS
        }
    out["g8b_family_rates"] = fam

    # -- error modes + echo + confound ------------------------------------
    out["g8b_error_modes_primary"] = {
        f"{c}@{p}": error_modes(cells[(c, p)]) for c, p in G8B_CELLS
    }
    out["g8b_lesson_echo_6gram"] = {
        f"{c}@{p}": echo_count(cells[(c, p)], c)
        for c, p in G8B_CELLS if c != "NONE"
    }
    out["oldg_sorting_confound_rt"] = {
        f"OLDG@{p}": sum(1 for c in PRIMARY if c.startswith("rt")
                         for s in D.SEEDS
                         if cells[("OLDG", p)][c][str(s)]["observed_label"] == "sorting")
        for p in ("probe_time", "session_start")
    }
    out["g8b_gc_monitoring"] = {
        "note": "GC probes ran only in the NONE cell (FULL scope)",
        "NONE": f"{int(matrix(none, GC).sum())}/{matrix(none, GC).size}",
    }

    # -- Q35 bounded ceiling record (STOP option D) ------------------------
    qfam = {}
    for f in FAMILIES:
        clusters = [c for c in PRIMARY if c.startswith(f)]
        qfam[f] = round(float(matrix(qnone, clusters).mean()), 4)
    out["q35_ceiling_record"] = {
        "status": "bounded measurement result (STOP option D): property of "
                  "the v3o surface for a stronger consumer; NOT a Reflection "
                  "success/failure",
        "pooled_primary": round(float(matrix(qnone, PRIMARY).mean()), 4),
        "pooled_primary_counts": f"{int(matrix(qnone, PRIMARY).sum())}/"
                                 f"{matrix(qnone, PRIMARY).size}",
        "family_rates": qfam,
        "band": [0.35, 0.85],
        "gate": "0.9333 > 0.85 upper bound — STOP-OUT-OF-BAND (prereg P0)",
    }

    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print("wrote", OUT)

    print("\n== G8B pooled primary ==")
    for k, v in out["g8b_pooled_primary"].items():
        print(f"  {k:24s} {v}")
    print("\n== contrasts (descriptive CIs) ==")
    for k, v in contrasts.items():
        print(f"  {k:28s} d={v['d']:+.4f}  CI {v['ci95']}  "
              f"excl0={v['ci_excludes_zero']}")
    print("\n== families ==")
    for f, row in fam.items():
        print(f"  {f}: " + "  ".join(f"{k}={v}" for k, v in row.items()))
    print("\n== error modes (primary) ==")
    for k, v in out["g8b_error_modes_primary"].items():
        print(f"  {k:24s} wrong_label={v['wrong_label']:3d}  "
              f"format_miss={v['format_miss']:3d}")
    print("\n== echo / confound ==")
    print(" ", out["g8b_lesson_echo_6gram"])
    print(" ", out["oldg_sorting_confound_rt"])
    print("\n== Q35 ceiling record ==")
    print(" ", out["q35_ceiling_record"]["pooled_primary_counts"],
          out["q35_ceiling_record"]["family_rates"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
