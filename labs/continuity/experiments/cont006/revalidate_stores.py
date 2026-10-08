"""Deterministic post-W re-validation (GATE-CONT006-POSTW, GO-with-fixes).

Single-shot (gate condition 4): re-parses the COMMITTED Phase W raw worker
log (zero new inference — condition 9), applies the gate-approved validator
(FIX-A 4-part ref resolution to the single probe event; FIX-B cross-trace
support assembly: near-duplicate candidates from different bundles are
clustered — greedy sequential over manifest order, join iff Jaccard >= 0.70
vs ANY member on title+lesson, the SAME frozen threshold rule (c) uses —
their evidence unions, and rule (b) is evaluated on the union) and re-runs
the R3 candidates through FIX-C (template-token skip). Writes the v2
artifacts into a SIBLING DIRECTORY (canonical filenames, no overwrite —
gate condition 7), each store carrying the provenance note (condition 1).
The pre-fix artifacts stay byte-untouched forever (condition 5).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.lessons import (  # noqa: E402
    CorpusIndex, jaccard, lesson_words, make_store, save_store,
    validate_candidate)
from continuity.reflection_v2 import parse_worker_reply  # noqa: E402

WORKER_DIR = (LAB_ROOT / "results" / "CONT-006-WORKER" /
              "cont006-worker-20261008-215103")
OUT_DIR = WORKER_DIR.parent / (WORKER_DIR.name + "-v2")
CORPUS = LAB_ROOT / "experiments" / "cont006" / "experience-corpus-manifest.json"
R3_CANDIDATES = LAB_ROOT / "experiments" / "cont006" / "r3-candidates.json"

PROVENANCE = (
    "Post-W re-validation per GATE-CONT006-POSTW (GO-with-fixes; local GLM "
    "5.3 Flash non-executor gate, substitution declared): FIX-A 4-part ref "
    "resolution to the single probe event; FIX-B cross-trace support "
    "assembly (greedy clustering, Jaccard >= 0.70 vs any member, "
    "first-appearing text, unioned evidence); FIX-C template-token skip. "
    "Derived from the committed raw-worker-log.jsonl with ZERO new "
    "inference; single-shot (condition 4). The pre-fix record "
    "(58 candidates, 0 accepted — frozen-prompt-vs-frozen-validator "
    "contradiction, gate finding PW-2/PW-3) stays byte-untouched in the "
    "original worker dir."
)


def cluster(candidates: list[dict]) -> list[list[dict]]:
    """Greedy sequential clustering (gate condition 3): iterate candidates
    in order; join the first cluster whose ANY member has Jaccard >= 0.70
    on title+lesson; else open a new cluster."""
    clusters: list[list[dict]] = []
    for cand in candidates:
        words = lesson_words(f"{cand['title']} {cand['lesson']}")
        placed = False
        for cluster_ in clusters:
            member_words = [lesson_words(f"{m['title']} {m['lesson']}")
                            for m in cluster_]
            if any(jaccard(words, mw) >= 0.70 for mw in member_words):
                cluster_.append(cand)
                placed = True
                break
        if not placed:
            clusters.append([cand])
    return clusters


def main() -> int:
    corpus = CorpusIndex(CORPUS)
    raw = [json.loads(line) for line in
           (WORKER_DIR / "raw-worker-log.jsonl").read_text(encoding="utf-8")
           .splitlines()]
    assert len(raw) == 50, len(raw)

    # 1) re-parse every response (gate-verified lossless)
    candidates = []
    for entry in raw:
        parsed = parse_worker_reply(entry["response_raw"])
        if parsed["verdict"] == "NEW_LESSON":
            for les in parsed["lessons"]:
                candidates.append({
                    "lessonId": les.get("lessonId") or f"LL-W-{len(candidates)+1:03d}",
                    "status": "candidate",
                    "title": str(les.get("title", "")).strip(),
                    "context": str(les.get("context", "")).strip(),
                    "observation": str(les.get("observation", "")).strip(),
                    "lesson": str(les.get("lesson", "")).strip(),
                    "applicability": [str(a) for a in les.get("applicability", [])],
                    "recommendedBehavior": str(les.get("recommendedBehavior", "")).strip(),
                    "evidence": [str(e) for e in les.get("evidence", [])],
                    "createdBy": "reflection-worker",
                    "createdUtc": entry["ts"],
                    "supersedesLessonIds": [],
                    "bundle": entry["bundle"],
                })
    print(f"re-parsed candidates: {len(candidates)}")

    # 2) FIX-B: cluster near-duplicates across bundles, union evidence
    all_clusters = cluster(candidates)
    clusters = [c for c in all_clusters if len(c) > 1]
    merged = []
    for group in clusters:
        first = dict(group[0])
        refs = []
        for g in group:
            refs.extend(g["evidence"])
        # dedupe refs preserving order
        seen: set[str] = set()
        first["evidence"] = [r for r in refs if not (r in seen or seen.add(r))]
        first["merged_from_bundles"] = sorted({g["bundle"] for g in group})
        first["merged_candidate_count"] = len(group)
        merged.append(first)
    print(f"clusters spanning >1 candidate: {len(clusters)} "
          f"(merged lessons: {len(merged)}); singleton candidates: "
          f"{len(candidates) - sum(c['merged_candidate_count'] for c in merged)}")

    # 3) validate merged clusters AND every singleton through the frozen
    #    rules (R-1: the artifact carries ALL 58 records with dispositions)
    accepted: list[dict] = []
    records = []  # one record PER CANDIDATE (58 total; R-1 exact)
    cluster_section = []
    clustered_ids: set[str] = set()
    for ci, group in enumerate(clusters):
        les = dict(group[0])
        refs = []
        for g in group:
            refs.extend(g["evidence"])
        seen: set[str] = set()
        les["evidence"] = [r for r in refs if not (r in seen or seen.add(r))]
        les["merged_from_bundles"] = sorted({g["bundle"] for g in group})
        les["merged_candidate_count"] = len(group)
        les["cluster_id"] = f"C{ci:02d}"
        ok, reasons = validate_candidate(les, corpus, accepted)
        if ok:
            les["status"] = "evidence-validated"
            accepted.append(les)
        cluster_section.append({
            "cluster_id": les["cluster_id"], "size": len(group),
            "member_lesson_ids": [g["lessonId"] for g in group],
            "merged_lesson": les, "disposition": "accepted" if ok else "rejected",
            "reasons": reasons})
        for g in group:
            clustered_ids.add(g["lessonId"])
            records.append({
                "disposition": "accepted" if ok else "rejected",
                "cluster_id": les["cluster_id"], "cluster_size": len(group),
                "member_lesson_ids": [g["lessonId"] for g in group],
                "reasons": reasons, "lesson": g,
                "canonical_merged_lesson": les if g is group[0] else None})
    for cand in candidates:
        if cand["lessonId"] in clustered_ids:
            continue
        ok, reasons = validate_candidate(cand, corpus, accepted)
        records.append({
            "disposition": "accepted" if ok else "rejected",
            "cluster_id": None, "cluster_size": 1,
            "member_lesson_ids": [cand["lessonId"]],
            "reasons": reasons, "lesson": cand,
            "canonical_merged_lesson": None})
    assert len(records) == len(candidates), (len(records), len(candidates))
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "candidates-v2.json").write_text(
        json.dumps({"kind": "cont006-worker-candidates-v2",
                    "provenance": PROVENANCE,
                    "candidate_record_count": len(records),
                    "clusters": cluster_section, "candidates": records},
                   indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    store = make_store(accepted, source="worker", status="evidence-validated",
                       provenance=PROVENANCE)
    digest = save_store(store, OUT_DIR / "r2-store-evidence-validated.json")
    print(f"R2 v2 store: {len(accepted)} accepted lessons, sha256 {digest[:12]}…")

    # 4) FIX-C re-run for R3
    payload = json.loads(R3_CANDIDATES.read_text(encoding="utf-8"))
    r3_accepted: list[dict] = []
    r3_records = []
    for les in payload.get("lessons", []):
        lesson = {**les, "createdBy": "gold-author"}
        ok, reasons = validate_candidate(lesson, corpus, r3_accepted)
        if ok:
            lesson["status"] = "evidence-validated"
            r3_accepted.append(lesson)
        r3_records.append({"disposition": "accepted" if ok else "rejected",
                           "reasons": reasons, "lesson": lesson})
    (OUT_DIR / "r3-validation-v2.json").write_text(
        json.dumps({"kind": "cont006-r3-validation-v2",
                    "provenance": PROVENANCE,
                    "candidates": len(r3_records), "accepted": len(r3_accepted),
                    "records": r3_records}, indent=1, ensure_ascii=True) + "\n",
        encoding="utf-8")
    r3_store = make_store(r3_accepted, source="gold-author",
                          status="evidence-validated", provenance=PROVENANCE)
    r3_digest = save_store(r3_store, OUT_DIR / "r3-store-evidence-validated.json")
    print(f"R3 v2 store: {len(r3_accepted)}/{len(r3_records)} accepted, "
          f"sha256 {r3_digest[:12]}…")
    (OUT_DIR / "provenance.json").write_text(
        json.dumps({"provenance": PROVENANCE,
                    "r2_store_sha256": digest, "r3_store_sha256": r3_digest,
                    "gate": "docs/GATE-CONT006-POSTW.md"}, indent=1,
                   ensure_ascii=True) + "\n", encoding="utf-8")
    print(f"written: {OUT_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
