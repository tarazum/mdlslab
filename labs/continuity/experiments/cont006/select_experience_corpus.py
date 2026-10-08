"""Deterministic experience-corpus selector for CONT-006 (zero GPU).

Implements the REFLECTION-V2-PROPOSAL "Data split" recommendation and the
implementing-agent review RN-1: the experience corpus is the ALREADY-COMMITTED
CONT-005-C2 trace corpus (suite v3j, 50 arm-seed traces = C2-pilot 25 +
C2-confirmatory 25) — no new inference for the experience phase. This script
enumerates those traces, digests each trace.jsonl (sha256), and labels every
probe outcome with the FROZEN failure-pattern taxonomy
(docs/CONT006-TAXONOMY.md; its digest is embedded here as the ordering
evidence that taxonomy freezing preceded corpus labeling).

Class mapping is mechanical (docs/CONT006-TAXONOMY.md "Mapping"): family +
cr-sub-type -> FP class; fails with observed_label null co-count FP-6;
passed non-guess probes and guess probes count as no-failure (FP-0)
observations at probe granularity (declared approximation: FP-0 is
session-level in the taxonomy, probe-level here).

Selection rule (frozen): ALL 50 C2 arm-seeds are selected (every taxonomy
class FP-1..FP-6 has >= 20 failure instances pooled — see the manifest's
coverage table; no fresh supplement needed). Reserve, NOT selected:
CONT-001-confirmatory (25 traces, v2 free-form probes — the label-form caveat
of PR-REVIEW note 2; its CN-007/M7 parroting evidence is cited in the
taxonomy but its traces are not worker input) and the CONT-005 cycle-1 runs
(superseded by C2 on the same question). Fresh-supplement rule: a fresh
experience run is added ONLY if a taxonomy class lacks coverage in the
selected corpus (none does at selection time) or the worker telemetry shows
a class-starved corpus; any supplement is a new owner-gated run with its own
digest, never an edit of closed artifacts.

Deterministic: no RNG, no wall-clock in the output. Re-running overwrites
experiments/cont006/experience-corpus-manifest.json byte-identically.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
RUNS = [
    ("CONT-005-C2-PILOT", "CONT-005-C2-PILOT/pilot-c2-20261006-093202"),
    ("CONT-005-C2-CONFIRMATORY", "CONT-005-C2-CONFIRMATORY/confirm-c2-20261006-230445"),
]
SUITE_DIRS = [
    ("v3i", LAB_ROOT / "fixtures" / "v3i"),   # C2-pilot suite (ids x-3xxx)
    ("v3j", LAB_ROOT / "fixtures" / "v3j"),   # C2-confirmatory suite (ids x-4xxx)
]
TAXONOMY = LAB_ROOT / "docs" / "CONT006-TAXONOMY.md"
OUT = Path(__file__).resolve().parent / "experience-corpus-manifest.json"

# cr sub-type -> class (docs/CONT006-TAXONOMY.md Mapping; frozen).
CR_SUBTYPE_CLASS = {
    "valid_correction_environment": "FP-3a",
    "valid_correction_tool": "FP-3a",
    "erroneous_user_correction": "FP-3b",
    "source_conflict": "FP-3b",
    "retraction": "FP-1",
    "scripted_agent_answer": "FP-2",
}
FAMILY_CLASS = {"cu": "FP-1", "rt": "FP-2", "dx": "FP-4", "dr": "FP-5"}


def scenario_classes() -> dict[str, str]:
    """id -> taxonomy class of a FAIL on that scenario (cr uses its sub-type).

    Both experience suites are loaded: the C2 pilot ran fixtures/v3i (ids
    x-3xxx), the C2 confirmatory ran fixtures/v3j (ids x-4xxx); the two
    suites share the family/sub-type vocabulary, so one mapping table covers
    both.
    """
    out = {}
    for _, suite_dir in SUITE_DIRS:
        for path in sorted(suite_dir.rglob("*.json")):
            if path.name == "manifest.json":
                continue
            s = json.loads(path.read_text(encoding="utf-8"))
            fam = s["id"][:2]
            if fam == "cr":
                out[s["id"]] = CR_SUBTYPE_CLASS[s.get("sub_type", "?")]
            elif fam in FAMILY_CLASS:
                out[s["id"]] = FAMILY_CLASS[fam]
            else:  # gc: expected-null probes are never failures (FP-0 material)
                out[s["id"]] = "FP-0"
    return out


def main() -> int:
    classes = scenario_classes()
    traces = []
    pooled = {}
    for run_tag, rel in RUNS:
        run_dir = LAB_ROOT / "results" / rel
        for arm in sorted(p.name for p in run_dir.iterdir() if p.is_dir()):
            arm_dir = run_dir / arm
            for seed_dir in sorted(p for p in arm_dir.iterdir() if p.is_dir()):
                trace = seed_dir / "trace.jsonl"
                if not trace.exists():
                    continue
                digest = hashlib.sha256(trace.read_bytes()).hexdigest()
                hist = {k: 0 for k in ("FP-0", "FP-1", "FP-2", "FP-3a", "FP-3b", "FP-4", "FP-5", "FP-6", "FP-X")}
                probes = fails = fmt = 0
                for line in trace.read_text(encoding="utf-8").splitlines():
                    e = json.loads(line)
                    if e.get("type") != "probe.result":
                        continue
                    p = e["payload"]
                    probes += 1
                    cls = classes.get(e.get("scenario", ""), "FP-X")
                    if p.get("kind") == "guess_calibration":
                        hist["FP-0"] += 1  # expected-null: no failure possible
                        continue
                    if not p.get("passed"):
                        fails += 1
                        hist[cls] += 1
                        if p.get("observed_label") is None:
                            fmt += 1
                            hist["FP-6"] += 1  # co-counted, never exclusive
                    else:
                        hist["FP-0"] += 1
                for k, v in hist.items():
                    pooled[k] = pooled.get(k, 0) + v
                traces.append({
                    "run": run_tag,
                    "arm": arm,
                    "seed": int(seed_dir.name.removeprefix("seed-")),
                    "trace": f"results/{rel}/{arm}/{seed_dir.name}/trace.jsonl",
                    "trace_sha256": digest,
                    "probes": probes,
                    "fails": fails,
                    "format_miss": fmt,
                    "failure_classes": {k: v for k, v in hist.items() if k != "FP-0"},
                    "no_failure_observations": hist["FP-0"],
                })
    manifest = {
        "kind": "cont006-experience-corpus-manifest",
        "taxonomy": {
            "file": "docs/CONT006-TAXONOMY.md",
            "sha256": hashlib.sha256(TAXONOMY.read_bytes()).hexdigest(),
            "status": "FROZEN for authoring purposes 2026-10-08, before lesson "
                      "authoring and transfer-fixture authoring",
        },
        "selection_rule": (
            "ALL committed CONT-005-C2 arm-seed traces (suite v3j; pilot 25 + "
            "confirmatory 25) are selected as the CONT-006 experience corpus; "
            "every taxonomy class FP-1..FP-6 has >= 20 pooled failure instances "
            "(coverage table below), so the fresh-supplement rule does not fire. "
            "Reserve NOT selected: CONT-001-confirmatory (v2 free-form probes, "
            "PR-REVIEW note-2 label-form caveat; cited as evidence in the "
            "taxonomy, not worker input) and CONT-005 cycle-1 runs (superseded "
            "by C2). Fresh supplement ONLY if a taxonomy class lacks coverage; "
            "any supplement is a new owner-gated run with its own digest."
        ),
        "counts": {
            "traces": len(traces),
            "probes": sum(t["probes"] for t in traces),
            "fails": sum(t["fails"] for t in traces),
            "format_miss": sum(t["format_miss"] for t in traces),
        },
        "coverage": pooled,
        "traces": traces,
    }
    OUT.write_text(json.dumps(manifest, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"corpus: {len(traces)} traces, {manifest['counts']}")
    for k in sorted(pooled):
        print(f"  {k}: {pooled[k]}")
    print("written:", OUT)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
