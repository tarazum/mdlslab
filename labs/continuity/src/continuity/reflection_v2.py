"""CONT-006 reflection worker v2 — the asynchronous lesson-extraction pass.

NEW versioned module (RN-5): src/continuity/reflection.py stays byte-stable
as the R1 deterministic baseline; this module implements the Phase W worker
of docs/EVALUATION-PREP-CONT006.md §1/§6.

Frozen at FREEZE: the reflection prompt template, the session-bundle
assembly rule, the worker sampling config and this code are digested in
frozen-config-cont006.json BEFORE the worker runs.

Trigger (frozen): post-experience single batch — ONE pass, one call per
arm-seed trace bundle (50 calls over the committed CONT-005-C2 corpus; the
"may inspect MULTIPLE sessions" batch semantics hold WITHIN a bundle: every
bundle carries all of that trace's scenario-runs).

Bundle assembly: per arm-seed trace, a condensed digest — per scenario-run:
family, taxonomy class, the key environment facts (learning/correction
turns, source types), abbreviated agent answers, and the probe result
(expected vs observed, pass/fail, format flag). Every digest line carries
its evidence-ref prefix (RUN|ARM|seed-N|SCENARIO|TURN) verbatim so the
worker can only cite resolvable refs.

Raw worker log (never replaced by telemetry): every call records the bundle
id, the prompt sha256, the response sha256, prompt/eval token counts and
the done_reason truncation flag (N-6: a NO_LESSON from a truncated bundle
must be distinguishable from a genuine NO_LESSON).

Outputs (Phase W): raw-worker-log.jsonl + candidates.json (every candidate
+ rejection reasons from the deterministic §7.1 validator) + telemetry.json
+ the evidence-validated R2 store (continuity.lessons).
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path
from typing import Any

from .lessons import CorpusIndex, make_store, save_store, validate_candidate

LAB_ROOT = Path(__file__).resolve().parents[2]

REFLECTOR_MODEL = "qwen36-35b-a3b:mdlslab"
REFLECTOR_DIGEST_PREFIX = "8a0fd5da454e"  # M2b / CN-001 pin
WORKER_OPTIONS = {"temperature": 0.0, "seed": 42, "num_ctx": 8192,
                  "num_predict": 768}
WORKER_TIMEOUT_S = 600
WORKER_KEEP_ALIVE = "30m"

REFLECTION_PROMPT_TEMPLATE = """You are a reflection worker reviewing the completed work log of an assistant agent that performed scheduled desk duties across many small scenarios (shift logs, codes, classifications, corrections).

Your job: decide whether ANY reusable lesson should be carried to future work. A lesson is a generalized behavioral rule backed by evidence in THIS log. Do not invent rules the log does not support.

Taxonomy of failure patterns seen across past work:
- FP-1 supersession-resolution miss: an updated or withdrawn value was ignored; the outdated value was answered.
- FP-2 own-answer anchoring: the agent repeated its own earlier wrong answer against a standing rule or a verified correction.
- FP-3a correction-application miss: a verified correction existed and was not applied.
- FP-3b unverified-source deference: an unverified source overrode the standing verified rule.
- FP-4 distractor susceptibility: a similar lure value was picked instead of the stated target.
- FP-5 storage miss: a plainly stated fact was not retrievable at question time.
- FP-6 format miss: the reply was not exactly one option label (prose, multiple labels, or empty).

Work log digest — @@RUN@@|@@ARM@@|seed-@@SEED@@ (@@N@@ scenario-runs; each line is prefixed by its evidence ref; scenario metadata: family, taxonomy class, key facts, abbreviated agent answers, probe result):

@@DIGEST@@

Rules for output:
- Reply with ONE JSON object only, no other text: {"verdict": "NO_LESSON"} or {"verdict": "NEW_LESSON", "lessons": [ ... one to three objects ... ]}.
- Each lesson object: {"title": ..., "context": ..., "observation": ..., "lesson": ..., "applicability": [ ... conditions ... ], "recommendedBehavior": ..., "evidence": [ "RUN|ARM|seed-N|SCENARIO|TURN", ... ]}.
- Cite evidence ONLY as refs copied verbatim from the digest line prefixes. At least two distinct scenario-runs in THIS log must support the lesson.
- Imperative behavioral form. NEVER quote the agent's wrong answer, specific codes, label values, or scenario names in the lesson text; evidence refs are ids, not content.
- At most 60 words in "lesson". No rules about permissions, safety policy, tools, or hidden runtime behavior.
- If nothing in this log generalizes to future work, reply {"verdict": "NO_LESSON"} — that is a valid, expected answer."""

# Families/classes carried into the digest line headers (from the corpus
# manifest taxonomy labels; v3i/v3j families only — the corpus is frozen).
FAMILY_CLASS = {"cu": "FP-1", "rt": "FP-2", "dx": "FP-4", "dr": "FP-5", "gc": "FP-0"}
CR_SUBTYPE_CLASS = {
    "valid_correction_environment": "FP-3a", "valid_correction_tool": "FP-3a",
    "erroneous_user_correction": "FP-3b", "source_conflict": "FP-3b",
    "retraction": "FP-1", "scripted_agent_answer": "FP-2",
}
_FAMILY_DIR = {
    "cr": "correction_reuse", "cu": "contradiction_update",
    "rt": "repeated_task", "dr": "delayed_recall", "dx": "distractor_recall",
}


def _scenario_classes() -> dict[str, str]:
    """id -> taxonomy class for every corpus scenario (v3i + v3j fixtures)."""
    out: dict[str, str] = {}
    for suite in ("v3i", "v3j"):
        for path in sorted((LAB_ROOT / "fixtures" / suite).rglob("*.json")):
            if path.name == "manifest.json":
                continue
            s = json.loads(path.read_text(encoding="utf-8"))
            fam = s["id"][:2]
            if fam == "cr":
                out[s["id"]] = CR_SUBTYPE_CLASS.get(s.get("sub_type", "?"), "?")
            else:
                out[s["id"]] = FAMILY_CLASS.get(fam, "?")
    return out


SCENARIO_CLASSES = _scenario_classes()


def _abbreviate(text: str, n_words: int = 12) -> str:
    words = " ".join(text.split()).split(" ")
    out = " ".join(words[:n_words])
    return out + ("…" if len(words) > n_words else "")


def build_bundle(trace: dict) -> str:
    """Condensed digest of one arm-seed trace (the frozen assembly rule).

    Per scenario-run: family/class header; then KEY TURNS ONLY (num_ctx
    budget — plain chore/ack turns carry no failure evidence and are
    dropped): environment turns WITH a source_type marker (corrections,
    retractions, own-answer injections), the first environment turn of the
    scenario (the stated facts), the probe question; agent replies only on
    the initial classification turn and the probe turn; one compact PROBE
    verdict line. Every line carries its evidence ref verbatim.
    """
    path = LAB_ROOT / trace["trace"]
    events: dict[str, list[dict]] = {}
    order: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        sid = e.get("scenario")
        if not sid or sid[:2] == "gc":
            continue
        if e.get("type") in ("env.turn", "agent.response", "probe.result"):
            if sid not in events:
                order.append(sid)
            events.setdefault(sid, []).append(e)
    prefix = f"{trace['run']}|{trace['arm']}|seed-{trace['seed']}"
    lines: list[str] = []
    for sid in order:
        evs = events[sid]
        sub = SCENARIO_CLASSES.get(sid, "?")
        lines.append(f"### {prefix}|{sid} family={sid[:2]} class={sub}")
        probe_refs = {(e.get("payload") or {}).get("turn_ref") for e in evs
                      if e["type"] == "probe.result"}
        first_env_seen = False
        for e in evs:
            pl = e.get("payload") or {}
            ref = f"{prefix}|{sid}|{pl.get('turn_ref', '?')}"
            turn_ref = pl.get("turn_ref", "")
            if e["type"] == "env.turn":
                src = pl.get("source_type")
                if src:
                    lines.append(f"{ref} ENV [source: {src}]: "
                                 f"{_abbreviate(pl.get('text', ''), 14)}")
                elif turn_ref in probe_refs:
                    lines.append(f"{ref} PROBE-Q: "
                                 f"{_abbreviate(pl.get('text', ''), 10)}")
                elif not first_env_seen:
                    first_env_seen = True
                    lines.append(f"{ref} ENV: "
                                 f"{_abbreviate(pl.get('text', ''), 14)}")
            elif e["type"] == "agent.response":
                if (turn_ref.startswith("s1") and turn_ref.endswith("t1")) \
                        or turn_ref in probe_refs:
                    lines.append(f"{ref} AGENT: "
                                 f"{_abbreviate(pl.get('content', ''), 6)}")
            else:
                fmt = "format-miss" if pl.get("observed_label") is None else (
                    "pass" if pl.get("passed") else "wrong-label")
                lines.append(f"{ref} PROBE: expected={pl.get('expected')!r} "
                             f"observed={pl.get('observed_label')!r} -> {fmt}")
    return "\n".join(lines)


def parse_worker_reply(content: str) -> dict:
    """Lenient JSON extraction (the reply must be one JSON object; anything
    unparseable is recorded as parse_error and counts as NO_LESSON-with-
    reason, never silently dropped)."""
    text = content.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        return {"verdict": "PARSE_ERROR", "raw": text[:400]}
    try:
        parsed = json.loads(text[start:end + 1])
    except json.JSONDecodeError:
        return {"verdict": "PARSE_ERROR", "raw": text[:400]}
    if not isinstance(parsed, dict) or parsed.get("verdict") not in (
        "NO_LESSON", "NEW_LESSON"
    ):
        return {"verdict": "PARSE_ERROR", "raw": text[:400]}
    if parsed["verdict"] == "NEW_LESSON" and not isinstance(parsed.get("lessons"), list):
        return {"verdict": "PARSE_ERROR", "raw": text[:400]}
    return parsed


def run_worker(
    corpus_manifest: Path,
    out_dir: Path,
    base_url: str,
    provider=None,
) -> dict:
    """Phase W: the single batch pass. Returns telemetry; writes the raw
    log, the candidates file (with §7.1 verdicts) and the evidence-validated
    R2 store."""
    # Deferred imports keep this module importable without the provider.
    from .provider import OllamaProvider
    from .events import _utc_now

    manifest = json.loads(corpus_manifest.read_text(encoding="utf-8"))
    corpus = CorpusIndex(corpus_manifest)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_log_path = out_dir / "raw-worker-log.jsonl"
    prov = provider or OllamaProvider(
        base_url=base_url, model=REFLECTOR_MODEL,
        temperature=WORKER_OPTIONS["temperature"], seed=WORKER_OPTIONS["seed"],
        num_ctx=WORKER_OPTIONS["num_ctx"], num_predict=WORKER_OPTIONS["num_predict"],
        keep_alive=WORKER_KEEP_ALIVE, timeout_s=WORKER_TIMEOUT_S,
    )
    accepted: list[dict] = []
    candidates: list[dict] = []
    telemetry = {
        "kind": "cont006-worker-telemetry",
        "sessions_analyzed": 0,
        "sessions_with_candidates": 0,
        "candidate_lessons": 0,
        "accepted": 0,
        "rejected_duplicates": 0,
        "rejected_unsupported": 0,
        "rejected_too_specific_or_unsafe": 0,
        "no_lesson_sessions": 0,
        "parse_error_calls": 0,
        "truncated_call_count": 0,
    }
    with raw_log_path.open("w", encoding="utf-8") as raw_log:
        for trace in manifest["traces"]:
            digest = build_bundle(trace)
            # Token substitution (NOT str.format — the template carries
            # literal JSON braces in its output contract). Phase-W crash-fix
            # before ANY worker call (prereg section 11 rendering class).
            prompt = (
                REFLECTION_PROMPT_TEMPLATE
                .replace("@@RUN@@", trace["run"])
                .replace("@@ARM@@", trace["arm"])
                .replace("@@SEED@@", str(trace["seed"]))
                .replace("@@N@@", str(digest.count("### ")))
                .replace("@@DIGEST@@", digest)
            )
            reply = prov.chat([{"role": "user", "content": prompt}])
            parsed = parse_worker_reply(reply["content"])
            truncated = reply["usage"]["eval_tokens"] >= WORKER_OPTIONS["num_predict"]
            if truncated:
                telemetry["truncated_call_count"] += 1
            raw_log.write(json.dumps({
                "ts": _utc_now(),
                "bundle": f"{trace['run']}|{trace['arm']}|seed-{trace['seed']}",
                "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
                "response_sha256": hashlib.sha256(
                    reply["content"].encode("utf-8")).hexdigest(),
                "prompt_tokens": reply["usage"]["prompt_tokens"],
                "eval_tokens": reply["usage"]["eval_tokens"],
                "done_truncated": truncated,
                "parsed_verdict": parsed["verdict"],
                "response_raw": reply["content"][:4000],
            }, ensure_ascii=True) + "\n")
            telemetry["sessions_analyzed"] += 1
            if parsed["verdict"] == "PARSE_ERROR":
                telemetry["parse_error_calls"] += 1
                telemetry["no_lesson_sessions"] += 1
                continue
            if parsed["verdict"] == "NO_LESSON":
                telemetry["no_lesson_sessions"] += 1
                continue
            telemetry["sessions_with_candidates"] += 1
            for les in parsed["lessons"]:
                telemetry["candidate_lessons"] += 1
                lesson = {
                    "lessonId": les.get("lessonId") or f"LL-W-{len(candidates) + 1:03d}",
                    "status": "candidate",
                    "title": str(les.get("title", "")).strip(),
                    "context": str(les.get("context", "")).strip(),
                    "observation": str(les.get("observation", "")).strip(),
                    "lesson": str(les.get("lesson", "")).strip(),
                    "applicability": [str(a) for a in les.get("applicability", [])],
                    "recommendedBehavior": str(les.get("recommendedBehavior", "")).strip(),
                    "evidence": [str(e) for e in les.get("evidence", [])],
                    "createdBy": "reflection-worker",
                    "createdUtc": _utc_now(),
                    "supersedesLessonIds": [],
                }
                ok, reasons = validate_candidate(lesson, corpus, accepted)
                if ok:
                    lesson["status"] = "evidence-validated"
                    accepted.append(lesson)
                    telemetry["accepted"] += 1
                    disposition = "accepted"
                else:
                    if any("duplicate" in r for r in reasons):
                        telemetry["rejected_duplicates"] += 1
                    elif any("support" in r or "ref" in r for r in reasons):
                        telemetry["rejected_unsupported"] += 1
                    else:
                        telemetry["rejected_too_specific_or_unsafe"] += 1
                    disposition = "rejected"
                candidates.append({"disposition": disposition,
                                   "reasons": reasons, "lesson": lesson})
    (out_dir / "candidates.json").write_text(
        json.dumps({"kind": "cont006-worker-candidates", "candidates": candidates},
                   indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    telemetry["created_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (out_dir / "telemetry.json").write_text(
        json.dumps(telemetry, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    store = make_store(accepted, source="worker", status="evidence-validated")
    digest = save_store(store, out_dir / "r2-store-evidence-validated.json")
    telemetry["r2_store_sha256"] = digest
    return telemetry


# ============================================================================
# V2 (rethink; docs/CONT-006-DESIGN-V2.md §3-§4, EVALUATION-PREP-CONT006-V2
# A.4): multi-trace family bundles + the lesson "class" schema + the FP-6
# store cap + class-coverage telemetry. The V1 per-trace pass above stays as
# the invalidated chain's record; ALL V2 worker passes run run_worker_v2.
# ============================================================================

WORKER_V2_PROMPT_TEMPLATE = """You are a reflection worker reviewing completed work logs of an assistant agent that performed scheduled desk duties across many small scenarios (shift logs, codes, classifications, corrections).

Your job: decide whether ANY reusable lesson should be carried to future work. A lesson is a generalized behavioral rule backed by evidence in THIS log bundle. The bundle groups scenario-runs OF THE SAME KIND from SEVERAL different work logs, so a pattern that repeats across them is exactly what a lesson should capture. Do not invent rules the logs do not support.

Taxonomy of failure patterns seen across past work:
- FP-1 supersession-resolution miss: an updated or withdrawn value was ignored; the outdated value was answered.
- FP-2 own-answer anchoring: the agent repeated its own earlier wrong answer against a standing rule or a verified correction.
- FP-3a correction-application miss: a verified correction existed and was not applied.
- FP-3b unverified-source deference: an unverified source overrode the standing verified rule.
- FP-4 distractor susceptibility: a similar lure value was picked instead of the stated target.
- FP-5 storage miss: a plainly stated fact was not retrievable at question time.
- FP-6 format miss: the reply was not exactly one option label (prose, multiple labels, or empty).

Work log digest — bundle {bundle} ({n_runs} scenario-runs from {n_traces} different work logs; each line prefixed by its evidence ref):

{digest}

Rules for output:
- Reply with ONE JSON object only, no other text: {{"verdict": "NO_LESSON"}} or {{"verdict": "NEW_LESSON", "lessons": [ ... one to three objects ... ]}}.
- Each lesson object: {{"title": ..., "class": ..., "context": ..., "observation": ..., "lesson": ..., "applicability": [ ... conditions ... ], "recommendedBehavior": ..., "evidence": [ "RUN|ARM|seed-N|SCENARIO|TURN", ... ]}}.
- "class" is the taxonomy class this lesson addresses, exactly one of FP-1, FP-2, FP-3a, FP-3b, FP-4, FP-5, FP-6. Use FP-6 ONLY for lessons about reply formatting discipline (how to shape the reply); a lesson about WHICH value governs is never FP-6.
- Evidence refs are EXACTLY five pipe-separated parts copied from the digest line prefixes, e.g. "CONT-05-C2-CONFIRMATORY|T2|seed-3001|cr-4001|s3t2" (run|arm|seed-dir|scenario-id|turn-ref). Cite at least two DIFFERENT work logs (different run|arm|seed prefix) per lesson — the bundle was grouped so you can.
- Imperative behavioral form. NEVER quote the agent's wrong answer, specific codes, label values, or scenario names in the lesson text; evidence refs are ids, not content.
- At most 60 words in "lesson". No rules about permissions, safety policy, tools, or hidden runtime behavior.
- Prefer LESSONS ABOUT THE SUBSTANCE of the failures (which value governs, when to re-derive, how to resist distractors) over lessons about reply formatting — formatting discipline is already known.
- If nothing in this bundle generalizes, reply {{"verdict": "NO_LESSON"}} — a valid, expected answer."""

VALID_CLASSES = ("FP-1", "FP-2", "FP-3a", "FP-3b", "FP-4", "FP-5", "FP-6")
FP6_CAP_CLASS = "FP-6"
FP6_CAP_MAX = 1  # DESIGN-V2 §4: at most ONE format-discipline lesson per store


def bundle_prompt(bundle: dict) -> str:
    """Render the V2 worker prompt for one pre-computed bundle. The template
    doubles every literal JSON brace, so str.format is safe here."""
    return WORKER_V2_PROMPT_TEMPLATE.format(
        bundle=bundle["bundle"], n_runs=bundle["n_runs"],
        n_traces=bundle["n_traces"], digest=bundle["digest"])


def lesson_class(lesson: dict) -> str:
    cls = str(lesson.get("class", "")).strip()
    return cls if cls in VALID_CLASSES else ""


def apply_class_cap(lessons: list[dict], capped_class: str = FP6_CAP_CLASS,
                    max_per_store: int = FP6_CAP_MAX,
                    ) -> tuple[list[dict], list[dict]]:
    """Deterministic store cap: keep the FIRST max_per_store lessons of the
    capped class in list order, drop the rest. Uniform for R2 and R3."""
    kept: list[dict] = []
    dropped: list[dict] = []
    seen = 0
    for les in lessons:
        if lesson_class(les) == capped_class:
            seen += 1
            if seen > max_per_store:
                dropped.append(les)
                continue
        kept.append(les)
    return kept, dropped


def class_coverage(lessons: list[dict]) -> dict[str, int]:
    cov: dict[str, int] = {}
    for les in lessons:
        cls = lesson_class(les) or "untagged"
        cov[cls] = cov.get(cls, 0) + 1
    return cov


def run_worker_v2(
    bundles_path: Path,
    out_dir: Path,
    corpus_manifest: Path,
    base_url: str,
    provider=None,
) -> dict:
    """Phase W v2: ONE worker call per PRE-COMPUTED multi-trace bundle
    (experiments/cont006/worker_v2_bundles.json — deterministic artifact).
    Cross-trace support is native (every bundle spans >= 3 traces), so §7.1
    rule (b) is evaluated as designed with no post-hoc merge. The FP-6 store
    cap and class-coverage telemetry apply to the final R2 store. Zero-GPU
    to define; the pass itself is owner-gated (never-autonomous)."""
    from .provider import OllamaProvider
    from .events import _utc_now

    bundles = json.loads(Path(bundles_path).read_text(encoding="utf-8"))["bundles"]
    corpus = CorpusIndex(corpus_manifest)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    raw_log_path = out_dir / "raw-worker-log-v2.jsonl"
    prov = provider or OllamaProvider(
        base_url=base_url, model=REFLECTOR_MODEL,
        temperature=WORKER_OPTIONS["temperature"], seed=WORKER_OPTIONS["seed"],
        num_ctx=WORKER_OPTIONS["num_ctx"], num_predict=WORKER_OPTIONS["num_predict"],
        keep_alive=WORKER_KEEP_ALIVE, timeout_s=WORKER_TIMEOUT_S,
    )
    accepted: list[dict] = []
    records: list[dict] = []
    telemetry: dict[str, Any] = {
        "kind": "cont006-worker-v2-telemetry",
        "calls": 0,
        "parse_error_calls": 0,
        "truncated_call_count": 0,
        "no_lesson_bundles": 0,
        "candidate_lessons": 0,
        "accepted": 0,
        "rejected_duplicates": 0,
        "rejected_unsupported": 0,
        "rejected_too_specific_or_unsafe": 0,
        "untagged_or_invalid_class": 0,
        "dropped_by_fp6_cap": [],
        "class_coverage_pre_cap": {},
        "class_coverage_store": {},
    }
    with raw_log_path.open("w", encoding="utf-8") as raw_log:
        for bundle in bundles:
            prompt = bundle_prompt(bundle)
            reply = prov.chat([{"role": "user", "content": prompt}])
            parsed = parse_worker_reply(reply["content"])
            truncated = reply["usage"]["eval_tokens"] >= WORKER_OPTIONS["num_predict"]
            if truncated:
                telemetry["truncated_call_count"] += 1
            telemetry["calls"] += 1
            raw_log.write(json.dumps({
                "ts": _utc_now(),
                "bundle": bundle["bundle"],
                "prompt_sha256": hashlib.sha256(
                    prompt.encode("utf-8")).hexdigest(),
                "response_sha256": hashlib.sha256(
                    reply["content"].encode("utf-8")).hexdigest(),
                "prompt_tokens": reply["usage"]["prompt_tokens"],
                "eval_tokens": reply["usage"]["eval_tokens"],
                "done_truncated": truncated,
                "parsed_verdict": parsed["verdict"],
                "response_raw": reply["content"][:4000],
            }, ensure_ascii=True) + "\n")
            if parsed["verdict"] == "PARSE_ERROR":
                telemetry["parse_error_calls"] += 1
                telemetry["no_lesson_bundles"] += 1
                continue
            if parsed["verdict"] == "NO_LESSON":
                telemetry["no_lesson_bundles"] += 1
                continue
            for les in parsed["lessons"]:
                telemetry["candidate_lessons"] += 1
                cls = str(les.get("class", "")).strip()
                if cls not in VALID_CLASSES:
                    cls = ""
                    telemetry["untagged_or_invalid_class"] += 1
                lesson = {
                    "lessonId": les.get("lessonId") or f"LL-W-{len(records) + 1:03d}",
                    "status": "candidate",
                    "class": cls,
                    "title": str(les.get("title", "")).strip(),
                    "context": str(les.get("context", "")).strip(),
                    "observation": str(les.get("observation", "")).strip(),
                    "lesson": str(les.get("lesson", "")).strip(),
                    "applicability": [str(a) for a in les.get("applicability", [])],
                    "recommendedBehavior": str(
                        les.get("recommendedBehavior", "")).strip(),
                    "evidence": [str(e) for e in les.get("evidence", [])],
                    "createdBy": "reflection-worker",
                    "createdUtc": _utc_now(),
                    "supersedesLessonIds": [],
                    "bundle": bundle["bundle"],
                }
                ok, reasons = validate_candidate(lesson, corpus, accepted)
                if ok:
                    lesson["status"] = "evidence-validated"
                    accepted.append(lesson)
                    telemetry["accepted"] += 1
                    disposition = "accepted"
                else:
                    if any("duplicate" in r for r in reasons):
                        telemetry["rejected_duplicates"] += 1
                    elif any("support" in r or "ref" in r for r in reasons):
                        telemetry["rejected_unsupported"] += 1
                    else:
                        telemetry["rejected_too_specific_or_unsafe"] += 1
                    disposition = "rejected"
                records.append({"disposition": disposition, "reasons": reasons,
                                "lesson": lesson})
    # FP-6 store cap + class-coverage telemetry (DESIGN-V2 §4)
    telemetry["class_coverage_pre_cap"] = class_coverage(accepted)
    kept, dropped = apply_class_cap(accepted)
    telemetry["dropped_by_fp6_cap"] = [d["lessonId"] for d in dropped]
    telemetry["class_coverage_store"] = class_coverage(kept)
    for rec in records:
        if rec["lesson"]["lessonId"] in telemetry["dropped_by_fp6_cap"]:
            rec["disposition"] = "accepted_then_capped"
            rec["reasons"] = [f"FP-6 store cap (max {FP6_CAP_MAX})"]
    (out_dir / "candidates-v2.json").write_text(
        json.dumps({"kind": "cont006-worker-candidates-v2",
                    "candidate_record_count": len(records),
                    "records": records}, indent=1, ensure_ascii=True) + "\n",
        encoding="utf-8")
    telemetry["created_utc"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    (out_dir / "telemetry-v2.json").write_text(
        json.dumps(telemetry, indent=1, ensure_ascii=True) + "\n",
        encoding="utf-8")
    store = make_store(
        kept, source="worker", status="evidence-validated",
        provenance=("V2 multi-trace bundles (worker_v2_bundles.json); FP-6 "
                    f"store cap <= {FP6_CAP_MAX}; class-coverage telemetry in "
                    "telemetry-v2.json"))
    digest = save_store(store, out_dir / "r2-store-v2.json")
    telemetry["r2_store_sha256"] = digest
    return telemetry
