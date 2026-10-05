"""Trust/supersession layer for the CONT-005 arms (suite v3, T0-T3).

Implements the memory-side of the CONT-005 proposal's claim discipline as a
DETERMINISTIC, versioned policy over episodes (append-only history preserved;
resolution happens only at assembly time, exactly as the proposal requires:
"resolving conflicts at retrieval/assembly time", "never silently delete").

Arms (suite v3; see docs/SUITE-V3-DESIGN.md and research-proposal.md CONT-005):
  T0  flat episodic injection - byte-identical to the arm-B renderer (baseline)
  T1  T0 + per-episode source/verification annotations (no verdicts)
  T2  T1 + conflict resolution: low-trust sources flagged and demoted,
      retracted corrections marked superseded by their retraction
  T3  T2 + the versioned trust-policy verdict header and per-episode trust rank

The policy consumes ONLY what a turn carries: its text and the fixture-protocol
v3 `source_type` field (environment | tool | user | agent_answer). It never reads
probe.expected, seed_error, or any scoring field - the layer orders and marks
evidence; the model still has to read it (that is the experiment).

Marker contract (fixture protocol v3, enforced by content, checked by the
assembly gate): verification markers are the words "verified" / "unreviewed" in
the turn text; retraction markers are "misrouted", "withdrawn", or
"does not apply here".
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TRUST_POLICY_VERSION = "trust-policy/v1"

# Rank table (higher = more trusted). Recency NEVER overrides a higher rank;
# within the same rank the newer statement governs (normal correction flow).
SOURCE_RANKS = {
    "environment": 2,          # plain environment statement
    "tool": 2,                  # plain tool output
    "user": 1,                  # unverified user statement/correction
    "agent_answer": 0,          # the agent's own earlier answer (CN-007)
}
VERIFIED_BUMP = 3              # rank for any source whose text says "verified"
UNREVIEWED_RANK = 1            # "unreviewed" feed text demotes environment to user level

RANK_NAMES = {3: "verified-observation", 2: "plain-statement", 1: "unverified-statement", 0: "own-earlier-answer"}

RETRACTION_MARKERS = ("misrouted", "withdrawn", "does not apply here")
CORRECTION_HINTS = ("bulletin", "accordingly", "classif", "amend")


@dataclass
class TurnMeta:
    """Classification of one episode's source turn (pure function of text+field)."""
    source_type: str            # environment | tool | user | agent_answer | "" (untyped)
    verified: bool
    unreviewed: bool
    retraction: bool            # this turn retracts an earlier correction
    rank: int
    flags: list[str] = field(default_factory=list)

    @property
    def trust_name(self) -> str:
        return RANK_NAMES.get(self.rank, "plain-statement")


def classify_turn(turn: dict) -> TurnMeta:
    text = turn.get("text", "")
    low = text.lower()
    source_type = turn.get("source_type", "")
    verified = "verified" in low
    unreviewed = "unreviewed" in low
    retraction = any(m in low for m in RETRACTION_MARKERS)
    if unreviewed:
        rank = UNREVIEWED_RANK
    elif verified:
        rank = VERIFIED_BUMP
    else:
        rank = SOURCE_RANKS.get(source_type, 2)
    return TurnMeta(source_type=source_type, verified=verified, unreviewed=unreviewed,
                    retraction=retraction, rank=rank)


def resolve_episodes(episodes: list[dict], turn_by_ref: dict[str, dict]) -> list[dict]:
    """Deterministic conflict resolution over one scenario's episodes.

    Returns the episodes with two additive per-episode fields:
      resolution_flag  - verdict line for T2/T3 ("" when none)
      superseded_by    - turn_ref of the retraction that retracted this episode
    Order is NOT changed here (the renderer demotes flagged episodes).

    Rules (trust-policy/v1):
      R1 unverified user statement (source_type=user, no 'verified' marker)
         -> flagged: cannot override verified evidence
      R2 unreviewed environment feed ('unreviewed' in text)
         -> flagged: demoted to unverified
      R3 the agent's own earlier answer (source_type=agent_answer)
         -> flagged: lowest trust; verified guides/observations govern
      R4 a retraction turn retracts the most recent prior environment
         correction turn (source_type=environment carrying a correction hint
         and not itself a retraction): that correction is marked superseded
         by the retraction's ref. Only the latest correction before the
         retraction is covered (targeted retraction, as authored).
      R5 (post-acceptance 2026-10-06, next cycle) an environment turn carrying
         the value-correction marker "correction for the records" supersedes
         the closest PRIOR plain environment statement of the same scenario
         (the s1 fact statement in the CU pattern). Closes the cu-2004 gap
         where supersession had no typed sources to act on.
    """
    metas = {ep["turn_ref"]: classify_turn(turn_by_ref.get(ep["turn_ref"], {})) for ep in episodes}
    out: list[dict] = []
    last_correction_ref: str | None = None
    for ep in episodes:
        item = dict(ep)
        item["resolution_flag"] = ""
        item["superseded_by"] = ""
        meta = metas[ep["turn_ref"]]
        if meta.retraction and ep["role"] == "environment":
            if last_correction_ref is not None:
                for prior in out:
                    if prior["turn_ref"] == last_correction_ref and not prior["superseded_by"]:
                        prior["superseded_by"] = ep["turn_ref"]
                        prior["resolution_flag"] = (
                            f"[RESOLVED: superseded by the retraction at {ep['turn_ref']}; "
                            "the prior standing rule holds]"
                        )
        elif (
            meta.source_type == "environment"
            and ep["role"] == "environment"
            and not meta.retraction
            and any(h in ep["content"].lower() for h in CORRECTION_HINTS)
        ):
            last_correction_ref = ep["turn_ref"]
        elif (
            ep["role"] == "environment"
            and "correction for the records" in ep["content"].lower()
        ):
            # R5: value-correction marker supersedes the closest prior plain
            # statement (no correction hint, no retraction, not this turn).
            for prior in reversed(out):
                if prior["role"] != "environment" or prior["turn_ref"] == ep["turn_ref"]:
                    continue
                prior_lower = prior["content"].lower()
                if (
                    metas.get(prior["turn_ref"]) is not None
                    and (metas[prior["turn_ref"]].retraction
                         or any(h in prior_lower for h in CORRECTION_HINTS)
                         or "correction for the records" in prior_lower)
                ):
                    continue
                if not prior["superseded_by"]:
                    prior["superseded_by"] = ep["turn_ref"]
                    prior["resolution_flag"] = (
                        f"[RESOLVED: superseded by the value correction at {ep['turn_ref']}; "
                        "the corrected value applies]"
                    )
                break
        if not item["resolution_flag"]:
            if meta.source_type == "user" and not meta.verified:
                item["resolution_flag"] = (
                    "[RESOLVED: unverified user statement - do not apply over verified evidence]"
                )
            elif meta.unreviewed:
                item["resolution_flag"] = (
                    "[RESOLVED: unreviewed feed - treat as unverified; verified evidence governs]"
                )
            elif meta.source_type == "agent_answer":
                item["resolution_flag"] = (
                    "[RESOLVED: the agent's own earlier answer - lowest trust; "
                    "verified guides and observations govern]"
                )
        out.append(item)
    return out


# --- Renderers ---------------------------------------------------------------

T0_HEADER = (
    "Your persistent memory: relevant records from your earlier sessions "
    "(most relevant first). Use them when the current session does not "
    "provide the information."
)
T1_HEADER = (
    "Your persistent memory: relevant records from your earlier sessions "
    "(most relevant first), each tagged with its source and verification "
    "status. Use them when the current session does not provide the information."
)
T2_HEADER = (
    "Your persistent memory: relevant records from your earlier sessions, "
    "with sources and conflict resolution already applied - flagged records "
    "are demoted and MUST NOT override unflagged verified evidence; records "
    "marked superseded by a retraction no longer apply."
)
T3_HEADER = (
    "Your persistent memory: relevant records from your earlier sessions under "
    f"trust policy {TRUST_POLICY_VERSION}: verified observations outrank plain "
    "statements, which outrank unverified user statements and your own earlier "
    "answers; recency never overrides provenance; a retraction restores the "
    "prior standing rule. Records are ordered by trust, most trusted first."
)


def _meta_tag(meta: TurnMeta) -> str:
    parts = []
    if meta.source_type:
        parts.append(f"source: {meta.source_type}")
    if meta.verified:
        parts.append("verification: verified")
    elif meta.unreviewed:
        parts.append("verification: unreviewed")
    return "|".join(parts)


def format_trust_block(
    episodes: list[dict],
    turn_by_ref: dict[str, dict],
    arm: str,
) -> str:
    """Render the memory block for T1/T2/T3 (T0 uses runner.format_memory_block).

    T1: annotations only. T2/T3: resolution flags + trust demotion ordering
    (unflagged first, stable within groups). T3 adds the policy header and a
    per-episode trust rank.
    """
    if arm == "T1":
        lines = [T1_HEADER]
        for ep in episodes:
            meta = classify_turn(turn_by_ref.get(ep["turn_ref"], {}))
            lines.append(f"{_prose_prefix(ep, meta)} {ep['content']}")
        return "\n".join(lines)

    resolved = resolve_episodes(episodes, turn_by_ref)
    unflagged = [e for e in resolved if not e["resolution_flag"]]
    flagged = [e for e in resolved if e["resolution_flag"]]
    header = T3_HEADER if arm == "T3" else T2_HEADER
    lines = [header]
    for ep in unflagged + flagged:
        meta = classify_turn(turn_by_ref.get(ep["turn_ref"], {}))
        line = f"{_prose_prefix(ep, meta, with_trust=arm == 'T3')} {ep['content']}"
        if ep["resolution_flag"]:
            line += " " + ep["resolution_flag"]
        lines.append(line)
    return "\n".join(lines)


def _prose_prefix(ep: dict, meta: TurnMeta, with_trust: bool = False) -> str:
    """(recorded in session N; source: X; verification: Y[; trust: Z]) — prose
    annotations only. The v3h run showed the square-bracket/pipe markup
    echoing into model answers (invalid-format errors), so no brackets/pipes."""
    session_no = ep["turn_ref"].lstrip("s").split("t")[0] if ep["turn_ref"].startswith("s") else "?"
    bits = [f"recorded in session {session_no}"]
    if meta.source_type:
        bits.append(f"source: {meta.source_type}")
    if meta.verified:
        bits.append("verification: verified")
    elif meta.unreviewed:
        bits.append("verification: unreviewed")
    if with_trust:
        bits.append(f"trust: {meta.trust_name}")
    return "(" + "; ".join(bits) + ")"
