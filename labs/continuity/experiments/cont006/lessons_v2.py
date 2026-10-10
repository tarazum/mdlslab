"""CONT-006 validator V2 — anti-salience collision resolution (stage-2 task 1).

Implements docs/PREREG-CONT006-VALIDATOR-V2.md (committed BEFORE the
collision report / re-run). The frozen src/continuity/lessons.py is NEVER
edited; this module re-derives its vocabulary WITH provenance and exposes:

  - build_vocab_report()      : collision enumeration (C1/C2/C3) per §2
  - anti_salience_violations_v2() : frozen checks + the two §3 exemptions
  - validate_candidate_v2()   : frozen §7.1 validation with v2 anti-salience
  - consumption_vocab() / consumption_gate() : §4 fail-closed gate

V2 exemptions (pre-registered):
  C1  standalone digits 0-9 are never blocked as tokens;
  C2  tokens whose ENTIRE label provenance is expected-null probe options
      (guess_calibration-style, expected null BY DESIGN) are not blocked.
Everything else byte-identical to the frozen validator.
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.lessons import (  # noqa: E402
    CODE_RE, NUM_RE, jaccard, lesson_words,
    policy_violations, evidence_refs,
)

FROZEN_LESSONS_PATH = LAB_ROOT / "src" / "continuity" / "lessons.py"
SUITES = ("v3i", "v3j", "v3l")

# World-name phrases (frozen list, kept in lockstep with lessons.py; the
# frozen module exposes them only inside _blocked_vocab, so they are
# restated here verbatim and the audit asserts set equality at run time).
WORLD_PHRASES = {
    "ferry terminal", "equipment cage", "mist line", "kiln room",
    "quarantine tank", "print workshop", "cheese cave", "ski patrol",
    "chandlery", "signal box", "bell foundry", "seed vault",
    "ice rink", "dyehouse", "lamp room", "cable car", "stockroom",
    "props loft", "weighbridge", "orchard shed", "brewery cellar",
    "observatory dome", "museum desk", "harbor office", "bakery depot",
}


def _expected_null(spec: dict) -> bool:
    """A probe spec is expected-null by design iff it carries an `expected`
    that is None/absent (guess_calibration battery: no correct answer)."""
    return spec.get("expected") is None


def _iter_suite_sources(suite: str):
    """(fixture_id, field_kind, vocab_entry, answerable) tuples for one suite.

    Mirrors the frozen _blocked_vocab() walk entry-for-entry: scenario ids
    enter as ONE whole lowercase entry (frozen semantics); seed_error /
    initial_expected / labels / expected enter as their lesson_words()
    tokens. `answerable` is only meaningful for label/expected fields.
    """
    suite_dir = LAB_ROOT / "fixtures" / suite
    for path in sorted(suite_dir.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        s = json.loads(path.read_text(encoding="utf-8"))
        yield s["id"].lower(), "id", s["id"].lower(), False
        seed = s.get("seed_error") or {}
        if isinstance(seed.get("value"), str):
            if not re.fullmatch(r"\{[a-z_]+\}", seed["value"]):
                for w in sorted(lesson_words(seed["value"])):
                    yield (s["id"].lower(), "seed_error", w, True)
        if isinstance(s.get("initial_expected"), str):
            for w in sorted(lesson_words(s["initial_expected"])):
                yield (s["id"].lower(), "initial_expected", w, True)
        for var in (s.get("variants") or {}).values():
            for spec in (var.get("probes") or {}).values():
                answerable = not _expected_null(spec)
                for label in spec.get("labels", []):
                    for w in sorted(lesson_words(str(label))):
                        yield (s["id"].lower(), "label", w, answerable)
                if isinstance(spec.get("expected"), str):
                    for w in sorted(lesson_words(spec["expected"])):
                        yield (s["id"].lower(), "expected", w, True)


def build_vocab_report() -> dict:
    """§2 enumeration: every single-word blocked token with provenance and
    collision class; multi-word sources decompose into words exactly as the
    frozen vocab does (labels are never phrase-blocked in v1 or v2)."""
    token_sources: dict[str, list[dict]] = {}
    for suite in SUITES:
        for fid, kind, entry, answerable in _iter_suite_sources(suite):
            token_sources.setdefault(entry, []).append(
                {"suite": suite, "fixture": fid, "field": kind,
                 "answerable": answerable})

    colliders_c1, colliders_c2, retained = [], [], []
    for token in sorted(token_sources):
        srcs = token_sources[token]
        if token.isdigit() and len(token) == 1:
            cls = "C1"
        elif all(s["field"] == "label" and not s["answerable"] for s in srcs):
            cls = "C2"
        else:
            cls = "C3"
        entry = {
            "token": token,
            "provenance": [
                {"suite": s["suite"], "fixture": s["fixture"],
                 "field": s["field"], "answerable": s["answerable"]}
                for s in srcs
            ],
            "also_expected_answer_of_answerable_probe": any(
                s["field"] == "expected" for s in srcs),
        }
        if cls == "C1":
            colliders_c1.append(entry)
        elif cls == "C2":
            colliders_c2.append(entry)
        else:
            retained.append({"token": token,
                             "provenance_count": len(srcs),
                             "fields": sorted({s["field"] for s in srcs})})

    return {
        "kind": "cont006-validator-v2-collision-report",
        "v1_blocked_tokens": len(token_sources),
        "v2_blocked_tokens": len(retained),
        "phrase_entries": len(WORLD_PHRASES),
        "c1_structural_digits": colliders_c1,
        "c2_expected_null_option_words": colliders_c2,
        "c3_retained_count": len(retained),
        "c3_retained": retained,
    }


def v2_blocked_tokens(report: dict) -> set[str]:
    """V2 blocks exactly the C3 tokens (prereg §3: C1/C2 exempted)."""
    return {e["token"] for e in report["c3_retained"]}


def anti_salience_violations_v2(lesson: dict, blocked_tokens: set[str]) -> list[str]:
    """Frozen §7.1(d) checks with the two pre-registered exemptions.

    Mirrors lessons.anti_salience_violations byte-for-byte except the token
    set comes from the caller (v2-derived). Phrases: the frozen module blocks
    only world phrases; v1 never blocked label phrases (labels are split
    into words) — v2 keeps exactly that semantics (prereg §6).
    """
    text = " ".join(
        str(lesson.get(k, "")) for k in ("title", "lesson", "recommendedBehavior")
    ) + " " + " ".join(str(a) for a in lesson.get("applicability", []))
    low = " ".join(text.split()).lower()
    out: list[str] = []
    for phrase in sorted(WORLD_PHRASES):
        if phrase in low:
            out.append(f"blocked world phrase {phrase!r}")
    for token in sorted(lesson_words(text) & blocked_tokens):
        out.append(f"blocked label token {token!r}")
    if CODE_RE.search(text):
        out.append("code-like token ([A-Z]+digits)")
    if NUM_RE.search(text):
        out.append("standalone 2+ digit numeral")
    return out


def validate_candidate_v2(lesson: dict, corpus, accepted: list[dict],
                          blocked_tokens: set[str]) -> tuple[bool, list[str]]:
    """Frozen lessons.validate_candidate with the anti-salience call swapped
    for v2. All other §7.1 logic mirrored 1:1 from the frozen module."""
    reasons: list[str] = []
    refs = evidence_refs(lesson)
    if not refs:
        reasons.append("no evidence refs")
    resolved_keys: set[tuple[str, str, str]] = set()
    for ref in refs:
        ok, why = corpus.resolve(ref)
        if not ok:
            reasons.append(f"unresolved evidence ref {ref!r}: {why}")
            continue
        parts = ref.split("|")
        trace_key = "|".join(parts[:3])
        if len(parts) == 5:
            scenario, turn = parts[3], parts[4]
        else:
            m = re.match(r"resolved-to-probe ([a-z]{2}-\d+)\|(.+)", why)
            if not m:
                reasons.append(f"unresolved evidence ref {ref!r}: {why}")
                continue
            scenario, turn = m.group(1), m.group(2)
        session = turn.split("t")[0]
        resolved_keys.add((trace_key, scenario, session))
    traces = {k[0] for k in resolved_keys}
    if len(resolved_keys) < 2:
        reasons.append(f"support {len(resolved_keys)} session(s) < 2")
    if len(traces) < 2:
        reasons.append(f"support {len(traces)} trace(s) < 2")
    text = f"{lesson.get('title','')} {lesson.get('lesson','')}"
    words = lesson_words(text)
    for other in accepted:
        score = jaccard(words, lesson_words(
            f"{other.get('title','')} {other.get('lesson','')}"))
        if score >= 0.70:
            reasons.append(
                f"duplicate of {other.get('lessonId')} (jaccard {score:.2f} >= 0.70)")
    lesson_text = str(lesson.get("lesson", ""))
    n_words = len(lesson_text.split())
    if n_words == 0 or n_words > 60:
        reasons.append(f"lesson field {n_words} words (need 1..60)")
    if not lesson.get("applicability"):
        reasons.append("no applicability condition")
    if not str(lesson.get("recommendedBehavior", "")).strip():
        reasons.append("no recommendedBehavior")
    reasons.extend(anti_salience_violations_v2(lesson, blocked_tokens))
    reasons.extend(policy_violations(lesson))
    return (not reasons), reasons


# ----------------------------------------------------------------------------
# §4 consumption gate (fail-closed; used at W4 store freeze against v3o)
# ----------------------------------------------------------------------------

def consumption_vocab(consumption_suite_dirs: list[Path]) -> dict:
    """Answer vocabulary of the CONSUMPTION suites, ALL fields, no C1/C2
    exemptions: rendered labels + expected + ids + seed_error values +
    initial_expected, words AND multi-word phrases."""
    tokens: set[str] = set()
    phrases: set[str] = set()
    for suite_dir in consumption_suite_dirs:
        for path in sorted(Path(suite_dir).rglob("*.json")):
            if path.name == "manifest.json":
                continue
            s = json.loads(path.read_text(encoding="utf-8"))
            for kind, text in _all_answer_fields(s):
                low = " ".join(str(text).lower().split())
                w = low.split()
                if len(w) > 1:
                    phrases.add(low)
                    tokens |= lesson_words(low)
                else:
                    tokens |= lesson_words(low)
    return {"tokens": tokens, "phrases": phrases}


def _all_answer_fields(s: dict) -> list[tuple[str, str]]:
    out = [("id", s["id"])]
    seed = s.get("seed_error") or {}
    if isinstance(seed.get("value"), str):
        if not re.fullmatch(r"\{[a-z_]+\}", seed["value"]):
            out.append(("seed_error", seed["value"]))
    if isinstance(s.get("initial_expected"), str):
        out.append(("initial_expected", s["initial_expected"]))
    for var in (s.get("variants") or {}).values():
        for spec in (var.get("probes") or {}).values():
            for label in spec.get("labels", []):
                out.append(("label", label))
            if isinstance(spec.get("expected"), str):
                out.append(("expected", spec["expected"]))
    return out


def consumption_gate(lessons: list[dict], vocab: dict) -> tuple[list[str], list[dict]]:
    """(excluded_lessonIds_with_reasons, kept_lessons). ANY token/phrase hit
    excludes the lesson (prereg §4)."""
    excluded: list[str] = []
    kept: list[dict] = []
    for les in lessons:
        text = " ".join(
            str(les.get(k, "")) for k in ("title", "lesson", "recommendedBehavior")
        ) + " " + " ".join(str(a) for a in les.get("applicability", []))
        low = " ".join(text.split()).lower()
        hits = sorted(lesson_words(text) & vocab["tokens"])
        hits += [p for p in sorted(vocab["phrases"]) if p in low]
        if hits:
            excluded.append({"lessonId": les.get("lessonId"), "hits": hits})
        else:
            kept.append(les)
    return excluded, kept


# ----------------------------------------------------------------------------
# audit main: collision report + W3 disposition re-run (zero GPU)
# ----------------------------------------------------------------------------

def _w3_records() -> list[dict]:
    path = (LAB_ROOT / "results" / "CONT-006-WORKER" /
            "cont006-worker-v3-20261010-203420" / "candidates-v2.json")
    return json.loads(path.read_text(encoding="utf-8"))["records"]


def rerun_w3_dispositions(report: dict) -> dict:
    from continuity.lessons import CorpusIndex
    corpus = CorpusIndex(LAB_ROOT / "experiments" / "cont006" /
                         "experience-corpus-manifest.json")
    tokens = v2_blocked_tokens(report)
    accepted: list[dict] = []
    out = []
    for rec in _w3_records():
        les = rec["lesson"]
        ok, reasons = validate_candidate_v2(les, corpus, accepted, tokens)
        if ok:
            accepted.append(les)
        out.append({
            "lessonId": les.get("lessonId"),
            "class": les.get("class"),
            "v1_disposition": rec["disposition"],
            "v1_reasons": rec["reasons"],
            "v2_disposition": "accepted" if ok else "rejected",
            "v2_reasons": reasons,
        })
    coverage: dict[str, int] = {}
    for les in accepted:
        coverage[les.get("class", "?")] = coverage.get(les.get("class", "?"), 0) + 1
    return {"candidates": out, "would_be_store_classes": coverage,
            "would_be_store_size": len(accepted)}


def main() -> None:
    frozen_sha = hashlib.sha256(
        FROZEN_LESSONS_PATH.read_bytes()).hexdigest()
    report = build_vocab_report()
    # lockstep assertion: the frozen module's own vocab must equal our v1
    # reconstruction (tokens ∪ world phrases), else the walk diverged.
    from continuity.lessons import BLOCKED_VOCAB
    ours = ({e["token"] for e in report["c1_structural_digits"]}
            | {e["token"] for e in report["c2_expected_null_option_words"]}
            | {e["token"] for e in report["c3_retained"]}
            | WORLD_PHRASES)
    assert ours == BLOCKED_VOCAB, (
        "v2 walk diverged from the frozen vocabulary: "
        f"+{sorted(ours - BLOCKED_VOCAB)[:5]} "
        f"-{sorted(BLOCKED_VOCAB - ours)[:5]}")

    rerun = rerun_w3_dispositions(report)
    ts = __import__("time").strftime("%Y%m%d-%H%M%S")
    out_dir = LAB_ROOT / "results" / "CONT-006-VALIDATOR-AUDIT" / ts
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "kind": "cont006-validator-v2-audit",
        "prereg": "docs/PREREG-CONT006-VALIDATOR-V2.md",
        "frozen_lessons_sha256": frozen_sha,
        "collision_report": report,
        "w3_disposition_rerun": rerun,
    }
    (out_dir / "audit.json").write_text(
        json.dumps(payload, indent=1, ensure_ascii=True) + "\n",
        encoding="utf-8")
    c1 = report["c1_structural_digits"]
    c2 = report["c2_expected_null_option_words"]
    print(f"v1 blocked tokens: {report['v1_blocked_tokens']} -> "
          f"v2: {report['v2_blocked_tokens']}")
    print(f"C1 structural digits: {[e['token'] for e in c1]}")
    print(f"C1 also-expected (residual risk): "
          f"{[e['token'] for e in c1 if e['also_expected_answer_of_answerable_probe']]}")
    print(f"C2 expected-null option words: {[e['token'] for e in c2]}")
    print("W3 re-run:")
    for row in rerun["candidates"]:
        mark = "CHANGED" if row["v1_disposition"] != row["v2_disposition"] else "same"
        print(f"  {row['lessonId']} [{row['class']}] "
              f"{row['v1_disposition']} -> {row['v2_disposition']} ({mark})")
        if row["v2_reasons"]:
            print(f"    reasons: {row['v2_reasons']}")
    print(f"would-be store: {rerun['would_be_store_classes']} "
          f"(size {rerun['would_be_store_size']})")
    print(f"artifact: {out_dir / 'audit.json'}")


if __name__ == "__main__":
    main()
