"""CONT-006 STAGE 2 frozen analyzer (authored BEFORE any v3o consumer
inference; digested by the stage-2 EXEC FREEZE). Reads a run root produced
by stage2_endtoend.py after its --gate PASSED; emits
stage2-results.json. Verdict machinery per docs/PREREG-CONT006-STAGE2.md:

  CO-PRIMARY (per model m): d_m = pass(NEWF2, probe_time) - pass(NONE)
  pooled over the 15 primary clusters x 7 seeds; two-sided 95% cluster
  percentile bootstrap (10k, RNG 20261011); MME 0.20 (power 0.86 at
  K15x7 — power-results-cont006-stage2.json row W2/W9). Branches:
  established / directional-below-MME / harm / no-difference.

  SECONDARY: interaction I = d_G8B - d_Q35 (powered only at I >= 0.25 —
  row I8; directional below, DECLARED); neutral contrast
  (NEWF2pt - NEUTRALpt) per model; session-start contrasts (open
  hypothesis); OLDG contrasts; per-family decomposition (exploratory);
  error modes; lesson-echo (6-gram verbatim, expected 0); the OLDG
  'sorting' collision check (declared confound of the old-generation
  store); GC + VAL monitoring (descriptive).

Determinism caveat (PB-071/CN-003): temp-0 + seed does not fully
determinize outputs; there is NO replay noise-floor arm in this
end-to-end design — branch wording carries that limitation.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "experiments" / "cont006"))
import stage2_design as D  # noqa: E402

BOOT = 10_000
RNG_SEED = 20261011
MME = 0.20
MME_INTERACTION = 0.25  # powered threshold (row I8); below = directional
MODELS = ("G8B", "Q35")


def load_cell(run_root: Path, model: str, content: str, position: str
              ) -> dict[str, dict[str, dict]]:
    """cluster -> seed -> probe result (pass bool + observed label)."""
    cell = run_root / model / f"{content}-{position}"
    out: dict[str, dict[str, dict]] = {}
    for seed in D.SEEDS:
        s = json.loads((cell / f"seed-{seed}" / "summary.json")
                       .read_text(encoding="utf-8"))
        for p in s["probes"]:
            out.setdefault(p["scenario"], {})[str(seed)] = {
                "passed": 1 if p["passed"] else 0,
                "observed_label": p.get("observed_label"),
                "expected": p.get("expected"),
                "turn_ref": p.get("turn_ref"),
            }
    return out


def pass_matrix(cell: dict, clusters: list[str]) -> np.ndarray:
    """clusters x seeds pass matrix."""
    return np.array([[cell[c][str(s)]["passed"] for s in D.SEEDS]
                     for c in clusters], dtype=float)


def boot_delta(a: np.ndarray, b: np.ndarray) -> dict:
    """Cluster-mean delta of two cells with the paired cluster bootstrap
    (the power_calc_stage2 analysis replicated exactly)."""
    rng = np.random.default_rng(RNG_SEED)
    d_c = a.mean(axis=1) - b.mean(axis=1)
    d = float(d_c.mean())
    idx = rng.integers(0, len(d_c), size=(BOOT, len(d_c)))
    lo, hi = np.percentile(d_c[idx].mean(axis=1), [2.5, 97.5])
    if lo > 0:
        branch = ("established" if d >= MME else "directional-below-MME")
    elif hi < 0:
        branch = "harm"
    else:
        branch = "no-difference"
    return {"d": round(d, 4), "ci": [round(lo, 4), round(hi, 4)],
            "branch": branch}


def boot_interaction(none_g: np.ndarray, newf_g: np.ndarray,
                     none_q: np.ndarray, newf_q: np.ndarray) -> dict:
    rng = np.random.default_rng(RNG_SEED)
    i_c = (newf_g.mean(axis=1) - none_g.mean(axis=1)) \
        - (newf_q.mean(axis=1) - none_q.mean(axis=1))
    i = float(i_c.mean())
    idx = rng.integers(0, len(i_c), size=(BOOT, len(i_c)))
    lo, hi = np.percentile(i_c[idx].mean(axis=1), [2.5, 97.5])
    branch = ("interaction-established" if (lo > 0 and i >= MME_INTERACTION)
              else "interaction-harm" if hi < 0 else "directional"
              if lo > 0 or hi < 0 else "no-difference")
    return {"I": round(i, 4), "ci": [round(lo, 4), round(hi, 4)],
            "branch": branch,
            "power_caveat": "powered only at |I| >= 0.25 (power artifact "
                            "row I8: 0.800); below that this is directional "
                            "only — DECLARED at prereg"}


def six_gram_echo(block: str, reply: str) -> bool:
    words_b = block.lower().split()
    words_r = reply.lower().split()
    grams = {" ".join(words_b[i:i + 6]) for i in range(len(words_b) - 5)}
    return any(" ".join(words_r[i:i + 6]) in grams
               for i in range(len(words_r) - 5))


def analyze(run_root: Path) -> dict:
    primary = list(D.PRIMARY_CLUSTERS)
    cells: dict[tuple, dict] = {}
    for model in MODELS:
        cells[(model, "NONE", "none")] = load_cell(run_root, model, "NONE", "none")
        for content in ("NEWF2", "NEUTRAL", "OLDG"):
            for pos in ("probe_time", "session_start"):
                cells[(model, content, pos)] = load_cell(
                    run_root, model, content, pos)

    # ---- completeness (fail-closed) ----
    problems = []
    for key, cell in cells.items():
        scope = primary + (list(D.VALIDATION_CLUSTERS)
                           if (key[1] == "NEWF2" and key[2] == "probe_time")
                           or key[1] == "NONE" else [])
        for c in scope:
            if c not in cell or len(cell[c]) != len(D.SEEDS):
                problems.append(f"{key}: {c} incomplete")
    if problems:
        return {"kind": "cont006-stage2-results", "verdict": "INCOMPLETE",
                "completeness_problems": problems[:20]}

    none_g = pass_matrix(cells[("G8B", "NONE", "none")], primary)
    none_q = pass_matrix(cells[("Q35", "NONE", "none")], primary)
    newf_g = pass_matrix(cells[("G8B", "NEWF2", "probe_time")], primary)
    newf_q = pass_matrix(cells[("Q35", "NEWF2", "probe_time")], primary)

    results: dict = {
        "kind": "cont006-stage2-results",
        "run_root": run_root.name,
        "pooled": {
            f"{m}|{c}|{p}": round(float(pass_matrix(cells[(m, c, p)],
                                                    primary).mean()), 4)
            for (m, c, p) in cells
        },
        # ---- co-primary ----
        "co_primary": {
            "G8B": boot_delta(newf_g, none_g),
            "Q35": boot_delta(newf_q, none_q),
            "mme": MME,
        },
        # ---- secondary ----
        "interaction": boot_interaction(none_g, newf_g, none_q, newf_q),
        "neutral_contrast": {
            m: boot_delta(
                pass_matrix(cells[(m, "NEWF2", "probe_time")], primary),
                pass_matrix(cells[(m, "NEUTRAL", "probe_time")], primary))
            for m in MODELS},
        "session_start": {
            "open_hypothesis": True,
            "ss_vs_none": {
                m: boot_delta(
                    pass_matrix(cells[(m, "NEWF2", "session_start")], primary),
                    none_g if m == "G8B" else none_q)
                for m in MODELS},
            "ss_vs_pt": {
                m: boot_delta(
                    pass_matrix(cells[(m, "NEWF2", "session_start")], primary),
                    pass_matrix(cells[(m, "NEWF2", "probe_time")], primary))
                for m in MODELS},
        },
        "oldg": {
            f"{m}|{pos}": boot_delta(
                pass_matrix(cells[(m, "OLDG", pos)], primary),
                none_g if m == "G8B" else none_q)
            for m in MODELS for pos in ("probe_time", "session_start")},
    }

    # ---- per-family decomposition (exploratory) ----
    fam = {}
    for f_prefix in ("cr", "cu", "rt", "dx", "dr"):
        clusters = [c for c in primary if c.startswith(f_prefix)]
        fam[f_prefix] = {
            f"{m}|{c}|{p}": round(float(pass_matrix(cells[(m, c, p)],
                                                    clusters).mean()), 4)
            for (m, c, p) in cells}

    # ---- error modes on the co-primary cells ----
    def error_modes(m: str) -> dict:
        out = {}
        for content, pos in (("NONE", "none"), ("NEWF2", "probe_time")):
            cell = cells[(m, content, pos)]
            wl = fm = 0
            for c in primary:
                for s in D.SEEDS:
                    r = cell[c][s]
                    if not r["passed"]:
                        if r["observed_label"] is None:
                            fm += 1
                        else:
                            wl += 1
            out[f"{content}-{pos}"] = {"wrong_label": wl, "format_miss": fm}
        return out

    # ---- lesson echo + OLDG 'sorting' confound ----
    echo = {f"{m}|{c}|{p}": 0 for (m, c, p) in cells if c != "NONE"}
    sorting_hits = {}
    for m in MODELS:
        for content in ("NEWF2", "NEUTRAL", "OLDG"):
            for pos in ("probe_time", "session_start"):
                cell = cells[(m, content, pos)]
                hits = 0
                for c in primary:
                    block = D.block_for(content, c)
                    for s in D.SEEDS:
                        reply = cell[c][s]["observed_label"]
                        full_reply = reply if isinstance(reply, str) else ""
                        if block and full_reply and six_gram_echo(block, full_reply):
                            echo[f"{m}|{content}|{pos}"] += 1
                if content == "OLDG":
                    sorting_hits[f"{m}|{pos}"] = sum(
                        1 for c in primary if c.startswith("rt")
                        for s in D.SEEDS
                        if cell[c][s]["observed_label"] == "sorting")

    # ---- GC + VAL monitoring (descriptive) ----
    gc_mon = {}
    for m in MODELS:
        cell = cells[(m, "NONE", "none")]
        gc_mon[m] = {g: [cell[g][str(s)]["observed_label"] for s in D.SEEDS]
                     for g in D.GC_IDS}
    val_act = {}
    for m in MODELS:
        val_none = pass_matrix(cells[(m, "NONE", "none")],
                               list(D.VALIDATION_CLUSTERS))
        val_newf = pass_matrix(cells[(m, "NEWF2", "probe_time")],
                               list(D.VALIDATION_CLUSTERS))
        val_act[m] = {"none": round(float(val_none.mean()), 4),
                      "newf2_pt": round(float(val_newf.mean()), 4),
                      "delta": round(float(val_newf.mean() - val_none.mean()), 4)}

    results["exploratory"] = {
        "per_family": fam,
        "error_modes": {m: error_modes(m) for m in MODELS},
        "lesson_echo_6gram": echo,
        "oldg_sorting_collision_rt": sorting_hits,
        "declared_confounds": [
            "OLDG rt blocks contain 'sorting' (a v3o answer tag) — the old "
            "generation predates the consumption-gate discipline; delivered "
            "AS AUTHORED; measured here, never silently edited",
        ],
    }
    results["monitoring"] = {"gc_observed_labels_NONE": gc_mon,
                             "val_activation": val_act}
    return results


def _self_test() -> int:
    """Synthetic-cell test of the bootstrap branches: a fixed +1 effect on
    every cluster yields established (d=1.0, CI>0); identical cells yield
    no-difference with CI containing 0."""
    rng = np.random.default_rng(7)
    a = (rng.random((15, 7)) > 0.5).astype(float)
    r1 = boot_delta(a + 1.0, a)
    r2 = boot_delta(a, a.copy())
    i_true = boot_interaction(a, a + 0.3, a, a)
    ok = (r1["branch"] == "established" and r1["d"] == 1.0
          and r2["branch"] == "no-difference" and r2["ci"][0] <= 0 <= r2["ci"][1]
          and i_true["branch"] == "interaction-established")
    print("self-test:", "PASS" if ok else "FAIL",
          json.dumps({"r1": r1, "r2": r2, "i": i_true}))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--run-root", default=None)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        return _self_test()
    if not args.run_root:
        ap.print_help()
        return 1
    root = Path(args.run_root)
    gate = root / "gate-PASS.json"
    if not gate.exists():
        print("FAIL-CLOSED: run --gate first (live telemetry gate must "
              "PASS before the analyzer)")
        return 2
    out = analyze(root)
    dest = root / "stage2-results.json"
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=True) + "\n",
                    encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items()
                      if k in ("verdict", "co_primary", "interaction",
                               "completeness_problems")}, indent=1)[:2000])
    print("written:", dest)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
