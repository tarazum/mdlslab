"""CONT-006 V2 contamination gate (SESSION-BRIEF-CONT006-V2-EXEC Step 4).

4-gram scan of ALL lesson texts (title + lesson + recommendedBehavior) in
the V2 lesson stores — r2-store-v2.json (the W2 worker-v2 output) AND
r3-store-v2.json (the recap artifact) — against EVERY rendered v3m turn
text (all 7 seeds {7001..7007}). Required: ZERO shared 4-grams. Tokenizer
and n-gram functions are REUSED from check_counterfactual_lessons.py (the
counterfactual lessons themselves are already covered by that script).

Fail-closed: exit 0 = PASS, exit 2 = FAIL. Deterministic (no RNG, no
wall-clock in the verdict fields). The verdict artifact commits with the
phase (--r2-store's directory: contamination-gate-v2.json).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_counterfactual_lessons import ngrams, tokens  # noqa: E402
from continuity.fixtures import render_seed_variant  # noqa: E402

R3_STORE = LAB_ROOT / "experiments" / "cont006" / "r3-store-v2.json"
SEEDS = (7001, 7002, 7003, 7004, 7005, 7006, 7007)
FIELDS = ("title", "lesson", "recommendedBehavior")


def store_grams(store_path: Path) -> dict[str, set[tuple[str, ...]]]:
    """lessonId -> 4-grams of title + lesson + recommendedBehavior."""
    payload = json.loads(store_path.read_text(encoding="utf-8"))
    out: dict[str, set[tuple[str, ...]]] = {}
    for les in payload.get("lessons", []):
        text = " ".join(str(les.get(f, "")) for f in FIELDS)
        out[les.get("lessonId", "?")] = ngrams(tokens(text))
    return out


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--r2-store", required=True,
                        help="path to the W2 output r2-store-v2.json")
    args = parser.parse_args()
    r2_path = Path(args.r2_store).resolve()

    stores = {"R2": r2_path, "R3": R3_STORE}
    grams_by_store = {name: store_grams(path) for name, path in stores.items()}

    hits: list[str] = []
    for path in sorted((LAB_ROOT / "fixtures" / "v3m").rglob("*.json")):
        if path.name == "manifest.json":
            continue
        base = json.loads(path.read_text(encoding="utf-8"))
        for seed in SEEDS:
            rendered = render_seed_variant(base, seed)
            for sess in rendered["sessions"]:
                for turn in sess["turns"]:
                    turn_grams = ngrams(tokens(turn["text"]))
                    for name, per_lesson in grams_by_store.items():
                        for lid, grams in per_lesson.items():
                            overlap = grams & turn_grams
                            if overlap:
                                hits.append(f"{name}/{lid} vs {base['id']} "
                                            f"seed {seed}: {sorted(overlap)[:2]}")
    verdict = {
        "kind": "cont006-v2-contamination-gate",
        "prereg": "EVALUATION-PREP-CONT006-V2.md A.1/A.6 (contamination gate)",
        "r2_store": str(r2_path),
        "r2_store_sha256": hashlib.sha256(r2_path.read_bytes()).hexdigest(),
        "r3_store_sha256": hashlib.sha256(R3_STORE.read_bytes()).hexdigest(),
        "lessons_scanned": {name: len(g) for name, g in grams_by_store.items()},
        "rendered_surface": "fixtures/v3m, every turn text, seeds 7001..7007",
        "shared_4grams": len(hits),
        "hits": hits[:10],
        "verdict": "PASS" if not hits else "FAIL",
    }
    out = r2_path.parent / "contamination-gate-v2.json"
    out.write_text(json.dumps(verdict, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print(f"lessons scanned: {verdict['lessons_scanned']}")
    print(f"shared 4-grams vs ALL rendered v3m turn texts (7 seeds): "
          f"{len(hits)} {hits[:4] or 'NONE'}")
    print(f"r2 store sha256: {verdict['r2_store_sha256'][:16]}…; "
          f"r3 store sha256: {verdict['r3_store_sha256'][:16]}…")
    print(f"VERDICT: {verdict['verdict']} -> {out}")
    return 0 if not hits else 2


if __name__ == "__main__":
    raise SystemExit(main())
