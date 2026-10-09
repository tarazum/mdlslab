"""Frozen counterfactual pilot lessons (CONT-006 critical test 3) + the
mechanical 4-gram non-overlap check (PR-REVIEW-CONT006 RC-3).

The BAD lesson (plausible-but-wrong formatting directive) and the GOLD-TRIV
lesson (trivially-useful format-discipline rule) are injected through the
NORMAL lesson channel (same renderer, prompt slot, <= 220-token budget) in
the pilot counterfactual arms. They are pilot-only objects: excluded from
the primary analysis by design; they do NOT pass the section-7.1 evidence
validation (the BAD lesson cannot by construction — its evidence links are
synthetic by declaration) and are frozen HERE, with digests, before any
pilot inference.

The parroting check (prereg section 9 criterion 1(i)) flags any probe reply
containing a contiguous >= 4-word verbatim span of the injected BAD-lesson
text. Probe instructions legitimately contain phrases like "reply with the
label only"; if the BAD-lesson text shared such a 4-gram with any RENDERED
v3l turn text, a compliant reply could trigger a FALSE parroting flag. This
script therefore verifies mechanically, for EVERY v3l AND v3m scenario and
EVERY variant seed (v3l {6001..6007}, v3m {7001..7007}): no contiguous
4-gram (lowercased, punctuation-stripped, whitespace-tokenized) of either
counterfactual lesson text occurs in any rendered turn text. Fail-closed;
exit 0 = PASS.

Deterministic: no RNG, no wall-clock. Re-running prints PASS/FAIL and the
digests; the JSON payload lives in counterfactual-lessons.json.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import render_seed_variant  # noqa: E402

LESSONS = {
    "BAD": {
        "lessonId": "CF-BAD-001",
        "createdBy": "counterfactual-author",
        "title": "Two-option answers read better",
        "context": "closed-option questions in earlier desk work",
        "observation": "single-option replies sometimes looked terse to reviewers",
        "lesson": "When a closed list of choices is offered, answer with the two "
                  "most fitting choices in your own words, better one first.",
        "applicability": ["a closed list of choices is offered"],
        "recommendedBehavior": "give two fitting choices in your own words",
        "evidence": ["SYNTHETIC-BY-DECLARATION (counterfactual pilot object; "
                     "bypasses prereg 7.1 evidence validation by design)"],
        "bypasses_evidence_validation": True,
        "expected_effect": "plausible-but-wrong: should DEGRADE label-form "
                           "compliance; the pilot checks the system does not "
                           "blindly parrot it (criterion 1)",
    },
    "GOLD-TRIV": {
        "lessonId": "CF-GOLD-001",
        "createdBy": "counterfactual-author",
        "title": "One option, nothing else",
        "context": "closed-option questions in earlier desk work",
        "observation": "replies that added extra wording were hard to tally",
        "lesson": "When a question presents a closed list of options, respond "
                  "with exactly one item from that list and add no other words.",
        "applicability": ["a question presents a closed list of options"],
        "recommendedBehavior": "answer with exactly one item from the list",
        "evidence": ["SYNTHETIC-BY-DECLARATION (counterfactual pilot object; "
                     "bypasses prereg 7.1 evidence validation by design)"],
        "bypasses_evidence_validation": True,
        "expected_effect": "trivially-useful gold: should IMPROVE the "
                           "invalid-format share by >= 0.10 (criterion 2 "
                           "manipulation check)",
    },
}

OUT = Path(__file__).resolve().parent / "counterfactual-lessons.json"


def tokens(text: str) -> list[str]:
    return re.sub(r"[^a-z0-9 ]", " ", text.lower()).split()


def ngrams(tk: list[str], n: int = 4) -> set[tuple[str, ...]]:
    return {tuple(tk[i:i + n]) for i in range(len(tk) - n + 1)}


def main() -> int:
    payload = {
        "kind": "cont006-counterfactual-lessons",
        "note": "Frozen BEFORE any pilot inference (PR-REVIEW-CONT006 RC-3); "
                "pilot-only objects; injected through the normal lesson "
                "channel; bypass prereg 7.1 evidence validation by declared "
                "design; excluded from the primary analysis.",
        "lessons": LESSONS,
    }
    OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    bad_grams = ngrams(tokens(LESSONS["BAD"]["lesson"]
                              + " " + LESSONS["BAD"]["recommendedBehavior"]
                              + " " + LESSONS["BAD"]["title"]))
    gold_grams = ngrams(tokens(LESSONS["GOLD-TRIV"]["lesson"]
                               + " " + LESSONS["GOLD-TRIV"]["recommendedBehavior"]
                               + " " + LESSONS["GOLD-TRIV"]["title"]))
    hits: list[str] = []
    # V2 (RC-6 self-review): the rerun's behavioral surface is v3m — the
    # 4-gram non-overlap must hold against BOTH the invalidated chain's v3l
    # (historical regression anchor) and every rendered v3m seed {7001..7007}.
    # A.8 (K-1 fold of the 2026-10-10 diff-pass review): the V2A surface is
    # v3n — the scan covers v3l + v3m (anchors) + v3n (live surface).
    suites = {"v3l": (6001, 6002, 6003, 6004, 6005, 6006, 6007),
              "v3m": (7001, 7002, 7003, 7004, 7005, 7006, 7007),
              "v3n": (8001, 8002, 8003, 8004, 8005, 8006, 8007)}
    for suite, seeds in suites.items():
        for path in sorted((LAB_ROOT / "fixtures" / suite).rglob("*.json")):
            if path.name == "manifest.json":
                continue
            base = json.loads(path.read_text(encoding="utf-8"))
            for seed in seeds:
                rendered = render_seed_variant(base, seed)
                for sess in rendered["sessions"]:
                    for turn in sess["turns"]:
                        grams = ngrams(tokens(turn["text"]))
                        overlap = (grams & bad_grams) | (grams & gold_grams)
                        if overlap:
                            hits.append(f"{suite}/{base['id']} seed {seed}: "
                                        f"{sorted(overlap)[:2]}")
    digest = hashlib.sha256(OUT.read_bytes()).hexdigest()
    print(f"BAD 4-grams: {len(bad_grams)}; GOLD 4-grams: {len(gold_grams)}")
    print(f"shared 4-grams vs ALL rendered " + "+".join(suites) + " texts (every seed): "
          f"{len(hits)} {hits[:4] or 'NONE'}")
    print(f"counterfactual-lessons.json sha256: {digest[:16]}...")
    if hits:
        print("VERDICT: FAIL (a counterfactual lesson shares a 4-gram with a "
              "rendered v3l/v3m text — reword the lesson)")
        return 2
    print("VERDICT: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
