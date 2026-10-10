"""Build experiments/cont006/stage2-freeze.json — the CONT-006 STAGE 2
store freeze (tasks 1-3 complete; house rule: store frozen BEFORE any
consumer inference). Deterministic digest manifest; zero GPU.
"""
import hashlib
import json
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]


def sha(rel: str) -> str:
    return hashlib.sha256((LAB / rel).read_bytes()).hexdigest()


W4 = "results/CONT-006-WORKER/cont006-worker-v4-20261010-224921"
files = {
    # validator V2 (task 1)
    "docs/PREREG-CONT006-VALIDATOR-V2.md": None,
    "experiments/cont006/lessons_v2.py": None,
    "results/CONT-006-VALIDATOR-AUDIT/20261010-222935/audit.json": None,
    # suite v3o (task 2)
    "experiments/suite-v3/build_v3o.py": None,
    "experiments/suite-v3/fixture-validation-v3o.json": None,
    "experiments/suite-v3/fixture-validation-regressions-post-v3o.json": None,
    "experiments/suite-v3/power_calc_stage2.py": None,
    "experiments/suite-v3/power-results-cont006-stage2.json": None,
    # balanced corpus + W4 (task 3)
    "experiments/cont006/worker_v4_bundles.py": None,
    "experiments/cont006/worker_v4_bundles.json": None,
    "experiments/cont006/_w4_driver.py": None,
    f"{W4}/raw-worker-log-v2.jsonl": None,
    f"{W4}/candidates-v2.json": None,
    f"{W4}/telemetry-v2.json": None,
    f"{W4}/r2-store-v2.json": None,
    f"{W4}/consumption-gate.json": None,
    f"{W4}/newf2-store-postgate.json": None,
    # consumption-side + corpus + frozen machinery
    "experiments/cont006/experience-corpus-manifest.json": None,
    "results/CONT-006-VAL/cont006-v-20261010-130154/r3-store-evidence-validated.json": None,
    "src/continuity/runner.py": None,
    "src/continuity/provider.py": None,
    "src/continuity/memory.py": None,
    "src/continuity/lessons.py": None,
    "src/continuity/reflection_v2.py": None,
    "src/continuity/events.py": None,
    "src/continuity/fixtures.py": None,
}
digests = {rel: sha(rel) for rel in files}

manifest = {
    "kind": "cont006-stage2-freeze",
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "brief": "docs/SESSION-BRIEF-CONT006-STAGE2.md",
    "note": "store freeze BEFORE any consumer inference (tasks 1-3: "
            "validator V2 audit; suite v3o authored+validated; balanced "
            "faithful W4 pass with the audited validator + v3o consumption "
            "gate). The stage-2 NEWF-v2 store = newf2-store-postgate.json "
            "(8 lessons, post consumption-gate; the FP-2 lesson excluded "
            "fail-closed for the 'sorting' answer-vocabulary hit). The "
            "prereg (task 4) is authored and committed BEFORE any v3o "
            "consumer inference; execution is task 5.",
    "model_pins": {
        "G8B": "granite-code:8b 36c3c3b9683b",
        "Q35": "qwen36-35b-a3b:mdlslab 8a0fd5da454e (consumer AND worker reflector)",
    },
    "newf2_store": {
        "path": f"{W4}/newf2-store-postgate.json",
        "store_sha256": json.loads(
            (LAB / f"{W4}/newf2-store-postgate.json").read_text(encoding="utf-8")
        )["store_sha256"],
        "lessons": 8,
        "classes": {"FP-1": 3, "FP-3a": 2, "FP-3b": 2, "FP-4": 1},
        "consumption_gate": "1 exclusion (LL-W-010 FP-2, hit 'sorting' in "
                            "applicability — a v3o PARCEL answer tag); "
                            "fail-closed per prereg validator-V2 §4",
    },
    "oldg_store": {
        "path": "results/CONT-006-VAL/cont006-v-20261010-130154/r3-store-evidence-validated.json",
        "note": "the executed gold store (frozen; capacity-freeze reference)",
    },
    "v3o_suite_sha256": json.loads(
        (LAB / "experiments/suite-v3/fixture-validation-v3o.json")
        .read_text(encoding="utf-8"))["suite_sha256"],
    "digests": digests,
}
out = LAB / "experiments" / "cont006" / "stage2-freeze.json"
out.write_text(json.dumps(manifest, indent=1, ensure_ascii=True) + "\n",
               encoding="utf-8")
print(f"freeze manifest: {len(digests)} digests")
print("NEWF-v2 store sha:", manifest["newf2_store"]["store_sha256"][:16])
print("written:", out)
