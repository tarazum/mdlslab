"""CONT-006 lesson pipeline: store, deterministic evidence validator (prereg
§7.1), dedup, retrieval, prose renderer, anti-salience mechanical checks.

Frozen at FREEZE (digest in frozen-config-cont006.json). The reflection
worker is a SEPARATE module (reflection_v2.py); this module is the
deterministic machinery shared by R2 (worker store), R3 (blind gold store),
the counterfactual pilot arms (BAD / GOLD-TRIV) and the runner's lesson
channel.

Lesson schema (prereg §5): lessonId, status, title, context, observation,
lesson, applicability (conditions), recommendedBehavior, evidence (trace
refs — IDS ONLY), createdBy, createdUtc, supersedesLessonIds.

Anti-salience / anti-overfit mechanical rule (§7.1d, RC-3 of the proposal):
lesson text must NOT name specific scenarios, ids, codes, label values or
worlds. Enforced by token checks: (a) no token matching the blocked-label
vocabulary collected from the CORPUS suites (v3i/v3j) and the TRANSFER
suite (v3l) — probe labels, seed_error values, initial_expected, scenario
ids; (b) no alphanumeric code pattern ([A-Z]\\d{2,4}); (c) no standalone
numeral of 2+ digits (corpus numeric labels); (d) no world-name phrases of
the frozen suites.
"""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]

WORD_RE = re.compile(r"[A-Za-z0-9]+")
CODE_RE = re.compile(r"\b[A-Z]\d{2,4}\b")
NUM_RE = re.compile(r"\b\d{2,}\b")

# Lesson-channel rendering budget (design §7): one prose block, <= 220
# tokens (~= 165 words / 900 chars for these short deterministic texts).
LESSON_TOP_K = 3
MAX_RENDER_WORDS = 165
LESSON_BLOCK_HEADER = "Lessons learned in earlier work (apply where relevant):"

# §7.1(e) policy boundary denylist (substring, lowercase).
POLICY_DENYLIST = (
    "permission", "safety policy", "tool authority", "hidden runtime",
    "system prompt", "ignore instructions", "override instructions",
    "delete", "credential", "api key", "execute shell", "run commands",
)


def lesson_words(text: str) -> set[str]:
    return {w.lower() for w in WORD_RE.findall(text)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _blocked_vocab() -> set[str]:
    """Label values / ids / codes from the corpus suites (v3i, v3j) and the
    transfer suite (v3l) — the anti-overfit vocabulary (frozen at import)."""
    vocab: set[str] = set()
    for suite in ("v3i", "v3j", "v3l"):
        suite_dir = LAB_ROOT / "fixtures" / suite
        if not suite_dir.exists():
            continue
        for path in sorted(suite_dir.rglob("*.json")):
            if path.name == "manifest.json":
                continue
            s = json.loads(path.read_text(encoding="utf-8"))
            vocab.add(s["id"].lower())
            seed = s.get("seed_error") or {}
            if isinstance(seed.get("value"), str):
                vocab |= lesson_words(seed["value"])
            if isinstance(s.get("initial_expected"), str):
                vocab |= lesson_words(s["initial_expected"])
            for var in (s.get("variants") or {}).values():
                for spec in (var.get("probes") or {}).values():
                    for label in spec.get("labels", []):
                        vocab |= lesson_words(str(label))
                    if isinstance(spec.get("expected"), str):
                        vocab |= lesson_words(spec["expected"])
    # World-name phrases (frozen suites; multi-word so token sets cannot
    # collide with legit lesson words like "terminal" alone).
    vocab |= {
        "ferry terminal", "equipment cage", "mist line", "kiln room",
        "quarantine tank", "print workshop", "cheese cave", "ski patrol",
        "chandlery", "signal box", "bell foundry", "seed vault",
        "ice rink", "dyehouse", "lamp room", "cable car", "stockroom",
        "props loft", "weighbridge", "orchard shed", "brewery cellar",
        "observatory dome", "museum desk", "harbor office", "bakery depot",
    }
    return vocab


BLOCKED_VOCAB = _blocked_vocab()
_BLOCKED_PHRASES = {v for v in BLOCKED_VOCAB if " " in v}
_BLOCKED_TOKENS = {v for v in BLOCKED_VOCAB if " " not in v}


def anti_salience_violations(lesson: dict) -> list[str]:
    """§7.1(d) mechanical checks. Returns a list of violation strings."""
    text = " ".join(
        str(lesson.get(k, "")) for k in ("title", "lesson", "recommendedBehavior")
    ) + " " + " ".join(str(a) for a in lesson.get("applicability", []))
    low = " ".join(text.split()).lower()
    out: list[str] = []
    for phrase in sorted(_BLOCKED_PHRASES):
        if phrase in low:
            out.append(f"blocked world phrase {phrase!r}")
    for token in lesson_words(text):
        if token in _BLOCKED_TOKENS:
            out.append(f"blocked label token {token!r}")
    if CODE_RE.search(text):
        out.append("code-like token ([A-Z]+digits)")
    if NUM_RE.search(text):
        out.append("standalone 2+ digit numeral")
    return out


def policy_violations(lesson: dict) -> list[str]:
    text = " ".join(
        str(lesson.get(k, "")) for k in ("title", "lesson", "recommendedBehavior", "context")
    ).lower()
    return [f"policy denylist hit {phrase!r}" for phrase in POLICY_DENYLIST if phrase in text]


def evidence_refs(lesson: dict) -> list[str]:
    return [str(e) for e in lesson.get("evidence", [])]


class CorpusIndex:
    """Resolves evidence refs against the committed experience corpus.

    Ref format (worker contract): RUN|ARM|seed-N|SCENARIO|TURN — e.g.
    "CONT-005-C2-CONFIRMATORY|T2|seed-3001|cr-4001|s2t1". Resolution = the
    trace file named by the corpus manifest contains an event for that
    scenario+turn (env.turn / agent.response / probe.result).
    """

    def __init__(self, manifest_path: Path | None = None) -> None:
        path = manifest_path or (
            LAB_ROOT / "experiments" / "cont006" / "experience-corpus-manifest.json"
        )
        self.manifest = json.loads(path.read_text(encoding="utf-8"))
        self.traces = {t["trace"]: t for t in self.manifest["traces"]}
        self._events: dict[str, set[str]] = {}

    def _refs_for_trace(self, trace_rel: str) -> set[str]:
        if trace_rel not in self._events:
            keys: set[str] = set()
            path = LAB_ROOT / trace_rel
            for line in path.read_text(encoding="utf-8").splitlines():
                try:
                    e = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if e.get("type") in ("env.turn", "agent.response", "probe.result"):
                    ref = (e.get("payload") or {}).get("turn_ref")
                    if ref and e.get("scenario"):
                        keys.add(f"{e['scenario']}|{ref}")
            self._events[trace_rel] = keys
        return self._events[trace_rel]

    def resolve(self, ref: str) -> tuple[bool, str]:
        parts = ref.split("|")
        if len(parts) != 5:
            return False, "ref must be RUN|ARM|seed-N|SCENARIO|TURN"
        run, arm, seed_dir, scenario, turn = parts
        for trace_rel, t in self.traces.items():
            if t["run"] == run and t["arm"] == arm and f"seed-{t['seed']}" == seed_dir:
                ok = f"{scenario}|{turn}" in self._refs_for_trace(trace_rel)
                return ok, ("resolved" if ok else "scenario/turn not in trace")
        return False, "no such trace in the corpus manifest"


def validate_candidate(
    lesson: dict,
    corpus: CorpusIndex,
    accepted: list[dict],
) -> tuple[bool, list[str]]:
    """§7.1 evidence validation. Deterministic, pre-written, zero GPU."""
    reasons: list[str] = []
    # (a) every evidence ref resolves
    refs = evidence_refs(lesson)
    if not refs:
        reasons.append("no evidence refs")
    resolved_keys: set[tuple[str, str, str]] = set()
    for ref in refs:
        ok, why = corpus.resolve(ref)
        if not ok:
            reasons.append(f"unresolved evidence ref {ref!r}: {why}")
            continue
        run, arm, seed_dir, scenario, turn = ref.split("|")
        session = turn.split("t")[0]
        resolved_keys.add((f"{run}|{arm}|{seed_dir}", scenario, session))
    # (b) >= 2 distinct sessions in >= 2 distinct traces
    traces = {k[0] for k in resolved_keys}
    if len(resolved_keys) < 2:
        reasons.append(f"support {len(resolved_keys)} session(s) < 2")
    if len(traces) < 2:
        reasons.append(f"support {len(traces)} trace(s) < 2")
    # (c) dedup vs accepted
    text = f"{lesson.get('title','')} {lesson.get('lesson','')}"
    words = lesson_words(text)
    for other in accepted:
        score = jaccard(words, lesson_words(f"{other.get('title','')} {other.get('lesson','')}"))
        if score >= 0.70:
            reasons.append(f"duplicate of {other.get('lessonId')} (jaccard {score:.2f} >= 0.70)")
    # (d) specificity / scope / anti-salience
    lesson_text = str(lesson.get("lesson", ""))
    n_words = len(lesson_text.split())
    if n_words == 0 or n_words > 60:
        reasons.append(f"lesson field {n_words} words (need 1..60)")
    if not lesson.get("applicability"):
        reasons.append("no applicability condition")
    if not str(lesson.get("recommendedBehavior", "")).strip():
        reasons.append("no recommendedBehavior")
    reasons.extend(anti_salience_violations(lesson))
    # (e) policy boundary
    reasons.extend(policy_violations(lesson))
    return (not reasons), reasons


# ----------------------------------------------------------------------------
# store
# ----------------------------------------------------------------------------

def _canonical(store: dict) -> str:
    payload = {k: v for k, v in store.items() if k != "store_sha256"}
    return json.dumps(payload, sort_keys=True, ensure_ascii=True, indent=1)


def store_digest(store: dict) -> str:
    return hashlib.sha256(_canonical(store).encode("utf-8")).hexdigest()


def make_store(lessons: list[dict], source: str, status: str) -> dict:
    store = {
        "kind": "cont006-lesson-store",
        "status": status,  # evidence-validated | active | empty
        "source": source,  # worker | gold-author | counterfactual | activation
        "lessons": lessons,
    }
    store["store_sha256"] = store_digest(store)
    return store


def load_store(path: Path) -> dict:
    store = json.loads(path.read_text(encoding="utf-8"))
    if store.get("store_sha256") != store_digest(store):
        raise ValueError(f"lesson store digest mismatch: {path}")
    return store


def save_store(store: dict, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_canonical(store) + "\n", encoding="utf-8")
    return store["store_sha256"]


# ----------------------------------------------------------------------------
# retrieval + renderer (the R2/R3 delivery channel; design §7)
# ----------------------------------------------------------------------------

def tokenize(text: str) -> list[str]:
    return [w.lower() for w in WORD_RE.findall(text) if len(w) > 2]


def score_lesson(query_tokens: list[str], lesson: dict) -> float:
    content = " ".join(
        [str(lesson.get("title", "")), str(lesson.get("lesson", "")),
         str(lesson.get("recommendedBehavior", ""))]
        + [str(a) for a in lesson.get("applicability", [])]
    )
    tokens = set(tokenize(content))
    if not tokens:
        return 0.0
    return sum(1 for q in query_tokens if q in tokens)


def retrieve(query_text: str, store: dict, top_k: int = LESSON_TOP_K) -> list[dict]:
    """Keyword retrieval against the session's first turn (design §7)."""
    q = tokenize(query_text)
    if not q:
        return []
    scored = sorted(
        ((score_lesson(q, les), les) for les in store.get("lessons", [])),
        key=lambda pair: (-pair[0], pair[1].get("lessonId", "")),
    )
    return [les for score, les in scored if score > 0][:top_k]


def render_block(selected: list[dict]) -> str:
    """Plain-prose rendering, one numbered line per lesson, imperative
    behavioral form, no quoting (design §7 anti-salience)."""
    lines = [LESSON_BLOCK_HEADER]
    for i, les in enumerate(selected, start=1):
        when = "; ".join(str(a) for a in les.get("applicability", [])) or "relevant"
        lines.append(f"{i}. {les['title']}. When {when}: {les['recommendedBehavior']}")
    block = "\n".join(lines)
    if len(block.split()) > MAX_RENDER_WORDS:
        raise ValueError(
            f"rendered lesson block {len(block.split())} words > budget {MAX_RENDER_WORDS}"
        )
    return block


class LessonChannel:
    """Per-run view over one store: retrieval + render + digest pinning."""

    def __init__(self, store: dict) -> None:
        self.store = store
        self.digest = store["store_sha256"]
        self.status = store["status"]
        self.source = store["source"]

    @classmethod
    def from_file(cls, path: Path) -> "LessonChannel":
        return cls(load_store(path))

    def retrieve(self, query_text: str) -> list[dict]:
        return retrieve(query_text, self.store)

    def render(self, selected: list[dict]) -> str:
        return render_block(selected)


def empty_store() -> dict:
    return make_store([], source="activation", status="empty")
