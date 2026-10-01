"""Bounded deterministic action policy (arm E MVP, stdlib only).

M5 contract (docs/ROADMAP.md): a FIXED action set and deterministic rules on
EXPLICIT state signals. MVP action set: {answer_direct, retrieve_then_answer}.
Non-goals: Jev/System One integration, unbounded action spaces, new memory
semantics (retrieval weighting/filtering is the owner-gated CONT-005
trust-hierarchy proposal and is deliberately NOT implemented here).

Rules (first hit wins; both evaluate on signals observable BEFORE answering):
- R1 absence-of-records: the current environment turn contains one of the
  fixed ABSENCE_MARKERS (lowercase substring; e.g. "not at hand",
  "no logbook", "from your own records") -> retrieve_then_answer. The turn
  explicitly asks the agent to answer from its own records, so the records
  are re-surfaced immediately before answering.
- R2 corrected-fact probe: the current turn is a probe turn AND the
  scenario's stored environment episodes contain a corrective marker
  (reusing reflection.CORRECTIVE_MARKERS — the CN-008 correction signal
  already established in M4) -> retrieve_then_answer.
- Otherwise -> answer_direct.

Actuation (performed by the runner, recorded here as the contract): the ONLY
thing a retrieve_then_answer action may do is refresh/extend the memory
injection immediately before answering — using the SAME block renderer
(`runner.format_memory_block`), the SAME keyword retrieval rule and top-k as
the arm-B baseline session-start injection, with the CURRENT turn's text as
the query. No prompt-template changes, no new tools, no answer-path changes.
Dedup rule: if every retrieved episode id is already covered by what this
session injected (baseline + earlier policy injections this session), the
physical injection is skipped and recorded as a no-op — the action is still
counted, so "what the policy actually did" stays measurable.

The MVP policy does NOT consume world-model predictions (recorded decision:
keeps `worldmodel.*` purely observational — predictions never alter prompts
or answers in arm E).
"""

from __future__ import annotations

from typing import Any

from .reflection import CORRECTIVE_MARKERS

ACTION_SET = frozenset({"answer_direct", "retrieve_then_answer"})

# Fixed absence-of-records markers (lowercase substrings matched against the
# current environment turn). Drawn from the fixture protocol's probe phrasings
# ("no logbook at hand", "you have no paperwork in front of you", "the catalog
# is not at hand", "registry book not at hand", "From your own records", ...).
ABSENCE_MARKERS: tuple[str, ...] = (
    "not at hand",
    "no logbook",
    "no paperwork",
    "no papers",
    "no timetable",
    "from your own records",
    "from your records",
)


def absence_marker(turn_text: str) -> str | None:
    """First ABSENCE_MARKERS hit in the turn text (lowercase), if any."""
    lowered = turn_text.lower()
    return next((m for m in ABSENCE_MARKERS if m in lowered), None)


def corrective_marker_in(env_episodes: list[dict[str, Any]]) -> str | None:
    """First CORRECTIVE_MARKERS hit across the scenario's stored environment
    episodes (deterministic: episode id order), if any."""
    for episode in sorted(env_episodes, key=lambda e: e["id"]):
        if episode.get("role") != "environment":
            continue
        lowered = str(episode.get("content", "")).lower()
        marker = next((m for m in CORRECTIVE_MARKERS if m in lowered), None)
        if marker is not None:
            return marker
    return None


def decide(
    *,
    turn_text: str,
    is_probe: bool,
    env_episodes: list[dict[str, Any]],
) -> dict[str, Any]:
    """Deterministic action choice over the fixed action set.

    `env_episodes` = the scenario's episodes currently in the store (all of
    them are strictly earlier than the current turn — appends happen after an
    exchange completes). Pure function of its inputs; no state, no randomness.
    """
    a_marker = absence_marker(turn_text)
    if a_marker is not None:
        return {
            "action": "retrieve_then_answer",
            "rule": "R1-absence-of-records",
            "signals": {"absence_marker": a_marker, "probe_follows_correction": None},
        }
    c_marker = corrective_marker_in(env_episodes) if is_probe else None
    if c_marker is not None:
        return {
            "action": "retrieve_then_answer",
            "rule": "R2-corrected-fact-probe",
            "signals": {
                "absence_marker": None,
                "probe_follows_correction": True,
                "correction_marker": c_marker,
            },
        }
    return {
        "action": "answer_direct",
        "rule": "default",
        "signals": {
            "absence_marker": None,
            "probe_follows_correction": False if is_probe else None,
        },
    }


# --- offline selftest -------------------------------------------------------


def _selftest() -> int:
    env_eps = [
        {"id": 1, "role": "environment", "content": "Classify this ticket: slow app."},
        {"id": 2, "role": "assistant", "content": "bug"},
        {
            "id": 3,
            "role": "environment",
            "content": "Rubric: slowness without a crash gets perf — do not use bug.",
        },
    ]

    # R1: absence marker in the turn text -> retrieve.
    d = decide(
        turn_text="New shift, no logbook at hand. How many minutes between flashes?",
        is_probe=True, env_episodes=[],
    )
    assert d["action"] == "retrieve_then_answer" and d["rule"].startswith("R1"), d
    assert d["signals"]["absence_marker"] == "no logbook", d

    # R1 wins even when the store is empty and the turn is not a probe.
    d = decide(turn_text="...the catalog is not at hand: what year?", is_probe=False, env_episodes=[])
    assert d["action"] == "retrieve_then_answer", d

    # R2: probe + stored corrective record -> retrieve.
    d = decide(
        turn_text="Classify this ticket into exactly one label: billing | bug | account | perf.",
        is_probe=True, env_episodes=env_eps,
    )
    assert d["action"] == "retrieve_then_answer" and d["rule"].startswith("R2"), d
    assert d["signals"]["probe_follows_correction"] is True, d

    # R2 does NOT fire for non-probe turns (rubric-learning turn in session 1).
    d = decide(turn_text="Classify this ticket: another slow app.", is_probe=False, env_episodes=env_eps)
    assert d["action"] == "answer_direct" and d["rule"] == "default", d

    # Default: probe without absence marker and without stored correction.
    d = decide(
        turn_text="Classify this ticket: my invoice shows the wrong VAT.",
        is_probe=True,
        env_episodes=[{"id": 1, "role": "environment", "content": "an earlier plain record"}],
    )
    assert d["action"] == "answer_direct", d

    # Determinism: identical inputs -> identical decision.
    args = dict(
        turn_text="A researcher calls, the catalog is not at hand: what year was it cast?",
        is_probe=True, env_episodes=env_eps,
    )
    assert decide(**args) == decide(**args)

    # Assistant episodes never carry the correction signal.
    assert corrective_marker_in([{"id": 9, "role": "assistant", "content": "do not use"}]) is None

    # Bounded action set: both actions are the only ones ever returned.
    for text, probe in (
        ("no logbook", True), ("plain turn", False), ("plain probe turn", True),
    ):
        assert decide(turn_text=text, is_probe=probe, env_episodes=env_eps)["action"] in ACTION_SET
    print("policy selftest ok: fixed action set, deterministic R1/R2/default rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
