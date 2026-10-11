"""Build experiments/cont006/stage2-exec-freeze.json — the CONT-006 STAGE 2
EXECUTION freeze (task 4): the prereg, the design tables, the runner
wrapper and the frozen analyzer are digest-pinned BEFORE the first
--run-phase (any v3o consumer inference). Deterministic; zero GPU.
"""
import hashlib
import json
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]


def sha(rel: str) -> str:
    """CRLF-normalized digest (see stage2-freeze.json digest_note)."""
    raw = (LAB / rel).read_bytes()
    return hashlib.sha256(raw.replace(b"\r\n", b"\n")).hexdigest()


files = {
    "docs/PREREG-CONT006-STAGE2.md": None,
    "docs/SESSION-BRIEF-CONT006-STAGE2.md": None,
    "docs/SESSION-BRIEF-CONT006-STAGE2-ADDENDUM.md": None,
    "experiments/cont006/stage2_design.py": None,
    "experiments/cont006/stage2_endtoend.py": None,
    "experiments/cont006/analyze_stage2.py": None,
    "experiments/cont006/stage2-freeze.json": None,
    # frozen machinery the wrapper imports (re-pinned; also in stage2-freeze)
    "src/continuity/runner.py": None,
    "src/continuity/provider.py": None,
    "src/continuity/memory.py": None,
    "src/continuity/events.py": None,
    "src/continuity/fixtures.py": None,
}
digests = {rel: sha(rel) for rel in files}

manifest = {
    "kind": "cont006-stage2-exec-freeze",
    "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    "prereg": "docs/PREREG-CONT006-STAGE2.md",
    "note": "execution half pinned BEFORE any v3o consumer inference: "
            "prereg (endpoints/MME 0.20/predictions/gates), design tables "
            "(annotations + neutral pool + composer), the end-to-end "
            "wrapper (positions, CN-012 guard, phases, wall guards), the "
            "frozen analyzer (self-test PASS), and the task-3 store freeze "
            "(stage2-freeze.json). --smoke PASS is a precondition for "
            "--preflight and --run-phase (PREREG §6).",
    "model_pins": {
        "G8B": "granite-code:8b 36c3c3b9683b",
        "Q35": "qwen36-35b-a3b:mdlslab 8a0fd5da454e",
    },
    "phases": [
        "1 G8B NONE (baseline gate)", "2 G8B NEWF2@pt", "3 G8B NEUTRAL@pt",
        "4 G8B NEWF2@ss", "5 G8B OLDG@pt", "6 G8B OLDG@ss",
        "7 G8B NEUTRAL@ss", "8 Q35 NONE (baseline gate)", "9 Q35 NEWF2@pt",
        "10 Q35 NEUTRAL@pt", "11 Q35 NEWF2@ss", "12 Q35 OLDG@pt",
        "13 Q35 OLDG@ss", "14 Q35 NEUTRAL@ss",
    ],
    "digests": digests,
}
out = LAB / "experiments" / "cont006" / "stage2-exec-freeze.json"
out.write_text(json.dumps(manifest, indent=1, ensure_ascii=True) + "\n",
               encoding="utf-8")
print(f"exec freeze: {len(digests)} digests")
print("written:", out)
