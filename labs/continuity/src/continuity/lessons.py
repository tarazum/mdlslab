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
                # FIX-C (GATE-CONT006-POSTW): pure template tokens
                # ('{old}', '{new}', '{alt}') are fixture syntax, never
                # rendered label values — the rendered values stay blocked
                # by the numeral/code rules. Skip them.
                if not re.fullmatch(r"\{[a-z_]+\}", seed["value"]):
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
        self._probe_events: dict[str, set[str]] = {}

    def _refs_for_trace(self, trace_rel: str) -> set[str]:
        self._load_trace(trace_rel)
        return self._events[trace_rel]

    def _probes_for_trace(self, trace_rel: str) -> set[str]:
        self._load_trace(trace_rel)
        return self._probe_events[trace_rel]

    def _load_trace(self, trace_rel: str) -> None:
        if trace_rel in self._events:
            return
        keys: set[str] = set()
        probes: set[str] = set()
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
                    if e["type"] == "probe.result":
                        probes.add(f"{e['scenario']}|{ref}")
        self._events[trace_rel] = keys
        self._probe_events[trace_rel] = probes

    def resolve(self, ref: str) -> tuple[bool, str]:
        """FIX-A (GATE-CONT006-POSTW): accepts 5-part refs (exact event) and
        4-part refs RUN|ARM|seed-N|SCENARIO, which resolve DETERMINISTICALLY
        to that scenario-run's single probe event (every non-gc scenario-run
        in the corpus has exactly one probe — gate-verified exhaustively;
        fail-closed if a reachable scenario ever has probe count != 1)."""
        parts = ref.split("|")
        for trace_rel, t in self.traces.items():
            if (t["run"] == parts[0] and t["arm"] == parts[1]
                    and f"seed-{t['seed']}" == parts[2]):
                keys = self._refs_for_trace(trace_rel)
                if len(parts) == 5:
                    run, arm, seed_dir, scenario, turn = parts
                    ok = f"{scenario}|{turn}" in keys
                    return ok, ("resolved" if ok else "scenario/turn not in trace")
                if len(parts) == 4:
                    scenario = parts[3]
                    probes = self._probes_for_trace(trace_rel)
                    probe_turns = sorted(k.split("|")[1] for k in probes
                                         if k.startswith(f"{scenario}|"))
                    if len(probe_turns) == 1:
                        return True, f"resolved-to-probe {scenario}|{probe_turns[0]}"
                    return False, (f"scenario {scenario} has {len(probe_turns)} probes "
                                   "(fail-closed: 4-part resolution needs exactly 1)")
                return False, "ref must be RUN|ARM|seed-N|SCENARIO|TURN"
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
        parts = ref.split("|")
        trace_key = "|".join(parts[:3])
        if len(parts) == 5:
            scenario, turn = parts[3], parts[4]
        else:  # FIX-A: the why-string carries the resolved probe turn
            m = re.match(r"resolved-to-probe ([a-z]{2}-\d+)\|(.+)", why)
            if not m:
                reasons.append(f"unresolved evidence ref {ref!r}: {why}")
                continue
            scenario, turn = m.group(1), m.group(2)
        session = turn.split("t")[0]
        resolved_keys.add((trace_key, scenario, session))
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


def make_store(lessons: list[dict], source: str, status: str,
               provenance: str | None = None) -> dict:
    store = {
        "kind": "cont006-lesson-store",
        "status": status,  # evidence-validated | active | empty
        "source": source,  # worker | gold-author | counterfactual | activation
        "lessons": lessons,
    }
    if provenance is not None:
        store["provenance"] = provenance
    store["store_sha256"] = store_digest(store)
    return store


def load_store(path: Path) -> dict:
    store = json.loads(path.read_text(encoding="utf-8"))
    if store.get("store_sha256") != store_digest(store):
        raise ValueError(f"lesson store digest mismatch: {path}")
    return store


def save_store(store: dict, path: Path) -> str:
    """D-PW-7 fix (GATE-CONT006-POSTW): the file carries the store_sha256
    field so load_store round-trips; the digest is computed over the payload
    WITHOUT the field (semantics unchanged)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.loads(_canonical(store))
    payload["store_sha256"] = store["store_sha256"]
    path.write_text(json.dumps(payload, sort_keys=True, indent=1) + "\n",
                    encoding="utf-8")
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


def render_block(selected: list[dict]) -> tuple[str, list[dict]]:
    """Plain-prose rendering, one numbered line per lesson, imperative
    behavioral form, no quoting (design §7 anti-salience).

    FIX-R (GATE-CONT006-VFIX, predicate pinned): lessons are included
    GREEDILY in the given (frozen retrieval) order, stopping at the first
    lesson that would exceed the MAX_RENDER_WORDS budget; the block is
    renumbered over the lessons actually rendered. Hard error iff the
    header plus a SINGLE lesson exceeds the budget, or whenever NOTHING
    fits (never a header-only render of a non-empty selection). Returns
    (block, rendered_lessons) — telemetry must report the RENDERED ids."""
    def line_for(i: int, les: dict) -> str:
        when = "; ".join(str(a) for a in les.get("applicability", [])) or "relevant"
        return f"{i}. {les['title']}. When {when}: {les['recommendedBehavior']}"

    if not selected:
        raise ValueError("render_block: empty selection")
    header_words = len(LESSON_BLOCK_HEADER.split())
    single = len(line_for(1, selected[0]).split())
    if header_words + single > MAX_RENDER_WORDS:
        raise ValueError(
            f"single lesson renders {header_words + single} words > budget "
            f"{MAX_RENDER_WORDS} (header + first lesson)")
    lines = [LESSON_BLOCK_HEADER]
    rendered: list[dict] = []
    for les in selected:
        candidate = line_for(len(rendered) + 1, les)
        used = sum(len(x.split()) for x in lines)
        if used + len(candidate.split()) > MAX_RENDER_WORDS:
            break
        lines.append(candidate)
        rendered.append(les)
    if not rendered:
        raise ValueError("no lesson fits the render budget")
    return "\n".join(lines), rendered


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

    def render(self, selected: list[dict]) -> tuple[str, list[dict]]:
        return render_block(selected)


def empty_store() -> dict:
    return make_store([], source="activation", status="empty")
