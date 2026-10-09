"""R3 gold-store recap for the V2 chain (DESIGN-V2 section 10 / prereg A.4).

Re-validates the blind-authored gold candidates through the frozen section
7.1 rules (unchanged from the invalid chain's revalidate_stores.py pass —
the corpus and refs are untouched), attaches the declared taxonomy classes
(gold-lesson-classes.json), and applies the FP-6 store cap UNIFORMLY with
the worker store: at most ONE format-discipline lesson, keep-first in
lessonId order -> LL-G-007 stays, LL-G-008 drops (8 -> 7).

Deterministic, zero GPU (reads committed artifacts only). Outputs
r3-validation-v3.json (per-lesson dispositions incl. the cap) and
r3-store-v2.json (the recapped evidence-validated R3 store for the V2
chain; activation still happens at Phase V, owner-gated).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.lessons import (  # noqa: E402
    CorpusIndex, make_store, save_store, validate_candidate)
from continuity.reflection_v2 import apply_class_cap, class_coverage  # noqa: E402

CORPUS = LAB_ROOT / "experiments" / "cont006" / "experience-corpus-manifest.json"
R3_CANDIDATES = LAB_ROOT / "experiments" / "cont006" / "r3-candidates.json"
CLASSES = LAB_ROOT / "experiments" / "cont006" / "gold-lesson-classes.json"
OUT_DIR = LAB_ROOT / "experiments" / "cont006"


def main() -> int:
    corpus = CorpusIndex(CORPUS)
    payload = json.loads(R3_CANDIDATES.read_text(encoding="utf-8"))
    classes = json.loads(CLASSES.read_text(encoding="utf-8"))["classes"]
    accepted: list[dict] = []
    records = []
    for les in payload.get("lessons", []):
        lesson = {**les, "createdBy": "gold-author",
                  "class": classes[les["lessonId"]]["class"]}
        ok, reasons = validate_candidate(lesson, corpus, accepted)
        if ok:
            lesson["status"] = "evidence-validated"
            accepted.append(lesson)
        records.append({"disposition": "accepted" if ok else "rejected",
                        "reasons": reasons, "lesson": lesson})
    # FP-6 cap, uniform with the worker store (DESIGN-V2 section 4)
    kept, dropped = apply_class_cap(accepted)
    dropped_ids = {d["lessonId"] for d in dropped}
    for rec in records:
        if rec["lesson"]["lessonId"] in dropped_ids:
            rec["disposition"] = "accepted_then_capped"
            rec["reasons"] = ["FP-6 store cap (max 1; keep-first by lessonId)"]
    (OUT_DIR / "r3-validation-v3.json").write_text(
        json.dumps({"kind": "cont006-r3-validation-v3",
                    "provenance": "V2 recap: section 7.1 re-validation of the "
                                  "blind gold candidates + declared classes "
                                  "(gold-lesson-classes.json) + FP-6 store cap "
                                  "uniform with R2; zero GPU, deterministic",
                    "candidates": len(records), "accepted_pre_cap": len(accepted),
                    "store_lessons": len(kept),
                    "class_coverage_store": class_coverage(kept),
                    "records": records}, indent=1, ensure_ascii=True) + "\n",
        encoding="utf-8")
    store = make_store(
        kept, source="gold-author", status="evidence-validated",
        provenance="V2 recap (FP-6 cap applied; classes from "
                   "gold-lesson-classes.json)")
    digest = save_store(store, OUT_DIR / "r3-store-v2.json")
    print(f"R3 v2 recap: {len(accepted)}/{len(records)} section-7.1 accepted; "
          f"store {len(kept)} lessons after FP-6 cap "
          f"(dropped: {sorted(dropped_ids)}); sha256 {digest[:12]}…")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
