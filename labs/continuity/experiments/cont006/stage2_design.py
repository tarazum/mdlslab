"""CONT-006 STAGE 2 frozen design data: applicability annotations, neutral
control pool, corrected-delivery block rendering, and the mechanical checks
the wrapper/analyzer/prereg all share. Authored BEFORE any v3o consumer
inference; digested by the stage-2 EXEC FREEZE.

Stores (frozen by experiments/cont006/stage2-freeze.json):
  NEWF-v2 = results/CONT-006-WORKER/cont006-worker-v4-20261010-224921/
            newf2-store-postgate.json  (8 lessons, sha 145cc88c…)
  OLDG    = results/CONT-006-VAL/cont006-v-20261010-130154/
            r3-store-evidence-validated.json (7 lessons)

Annotation procedure (mirrors PREREG-CONT006-DELIVERY-DIAG §5): one
annotator (the implementer), cluster-level, seed-independent, produced
BEFORE any v3o consumer inference. Every judgment call is flagged in
FLAGGED_CALLS below and mirrored in the prereg §6. Delivery = corrected
rendering (title + When + Rule + Behavior, store order, NO budget), the
delivery-v2 mechanism of step 1.

FLAGGED_CALLS:
  F1 rt clusters get LL-W-002+LL-W-003 although the mechanism-fit FP-2
     lesson (W4's LL-W-010) was EXCLUDED by the v3o consumption gate
     ('sorting' answer-tag hit) — 003's "do not rely on your own previous
     incorrect answer" clause is the closest FP-2 content in the store.
  F2 dr clusters get the FP-4 lesson LL-W-009 although the mechanism-fit
     FP-5 lesson was REJECTED by the mining validator (1-trace support);
     009's entity-first binding text is the nearest mechanism in the store.
  F3 cu superseded clusters get LL-W-003 (log-entry invalidation) over
     LL-W-006, whose withdrawal clause is inert on superseded chains
     (borderline-excluded; recorded).
  F4 OLDG sets carry LL-G-007 (the cross-cutting closed-list format
     lesson) on EVERY cluster, mirroring the step-1 G-annotation pattern
     where G-007 accompanied every annotated cluster.
"""

from __future__ import annotations

import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
NEWF2_STORE = (LAB_ROOT / "results" / "CONT-006-WORKER" /
               "cont006-worker-v4-20261010-224921" / "newf2-store-postgate.json")
OLDG_STORE = (LAB_ROOT / "results" / "CONT-006-VAL" /
              "cont006-v-20261010-130154" / "r3-store-evidence-validated.json")

NEWF2_STORE_SHA = "145cc88cca587459"  # prefix of the frozen store digest
OLDG_STORE_SHA = "48064a0235500d8d66218b2ff3e6f0889cf06274489500f5097a58200626fafa"

PRIMARY_CLUSTERS = (
    "cr-9001", "cr-9002", "cr-9003", "cr-9004",
    "cu-9101", "cu-9102", "cu-9103", "cu-9104",
    "rt-9201", "rt-9202", "rt-9203",
    "dx-9401", "dx-9402",
    "dr-9301", "dr-9302",
)
VALIDATION_CLUSTERS = ("cr-9005", "cu-9105", "rt-9204", "dx-9403")
GC_IDS = ("gc-9501", "gc-9502", "gc-9503")
SEEDS = (9001, 9002, 9003, 9004, 9005, 9006, 9007)

DELIVERY_HEADER = "Lessons learned in earlier work (apply where relevant):"

# --- applicability annotations (cluster -> lesson ids, store order) --------
NEWF2_APPL = {
    "cr-9001": ["LL-W-002"],
    "cr-9002": ["LL-W-005"],
    "cr-9003": ["LL-W-004"],
    "cr-9004": ["LL-W-001", "LL-W-007"],
    "cr-9005": ["LL-W-005"],
    "cu-9101": ["LL-W-003"],
    "cu-9102": ["LL-W-003"],
    "cu-9103": ["LL-W-007"],
    "cu-9104": ["LL-W-007"],
    "cu-9105": ["LL-W-003"],
    "rt-9201": ["LL-W-002", "LL-W-003"],
    "rt-9202": ["LL-W-002", "LL-W-003"],
    "rt-9203": ["LL-W-002", "LL-W-003"],
    "rt-9204": ["LL-W-002", "LL-W-003"],
    "dx-9401": ["LL-W-009"],
    "dx-9402": ["LL-W-009"],
    "dx-9403": ["LL-W-009"],
    "dr-9301": ["LL-W-009"],
    "dr-9302": ["LL-W-009"],
}
OLDG_APPL = {
    "cr-9001": ["LL-G-004", "LL-G-007"],
    "cr-9002": ["LL-G-005", "LL-G-007"],
    "cr-9003": ["LL-G-005", "LL-G-007"],
    "cr-9004": ["LL-G-002", "LL-G-007"],
    "cu-9101": ["LL-G-001", "LL-G-007"],
    "cu-9102": ["LL-G-001", "LL-G-007"],
    "cu-9103": ["LL-G-002", "LL-G-007"],
    "cu-9104": ["LL-G-002", "LL-G-007"],
    "rt-9201": ["LL-G-003", "LL-G-007"],
    "rt-9202": ["LL-G-003", "LL-G-007"],
    "rt-9203": ["LL-G-003", "LL-G-007"],
    "dx-9401": ["LL-G-006", "LL-G-007"],
    "dx-9402": ["LL-G-006", "LL-G-007"],
    "dr-9301": ["LL-G-006", "LL-G-007"],
    "dr-9302": ["LL-G-006", "LL-G-007"],
}

# --- neutral control pool (fixed texts; numbered-line shape matched to the
# treatment block, NO instruction force, NO surface/label vocabulary —
# the Addendum-C lesson: no format/workflow content, no identifiers).
# Base lines (~48 words) are extended by tail sentences (~15 words each,
# appended round-robin to the numbered lines) until the block's word total
# lands inside ±25% of the treatment block — per-cluster mechanical match.
NEUTRAL_POOL = (
    "The depot keeps a kettle on the north counter. It whistles a little "
    "before ten most mornings. The window above it fogs in cold weeks, and "
    "the afternoon light lands on the shelf where the spare pens wait in a "
    "chipped cup.",
    "A tabby cat crosses the yard near dusk on most working days. It pauses "
    "by the step, watches the door a while, and moves on along the fence "
    "toward the far gate, where the gravel gives way to older paving.",
    "The wall clock runs about a minute slow through the winter. Nobody "
    "minds this much. It was bought secondhand, the story goes, from a "
    "closed market further up the valley, and it keeps its own idea of the "
    "hour.",
    "Rain gathers in the low corner of the yard by the old well. Leaves "
    "collect there through autumn, and someone sweeps them into a heap by "
    "the wall every few days, where they settle and darken until spring.",
    "The book shelf stands by the window where the light holds longest. Its "
    "lower rows hold older volumes with cloth spines, and a pressed flower "
    "marks a place in one of them, left there by someone long since moved "
    "on.",
    "A flight of geese passes over the yard most autumn evenings. Their "
    "sound arrives before they do, a loose calling that lifts the quiet for "
    "half a minute, then fades toward the river and whatever lies beyond "
    "the trees.",
)
NEUTRAL_TAILS = (
    "The cleaner mentions it now and then, usually on quiet afternoons.",
    "Nobody has settled the matter for good, and nobody seems inclined to.",
    "It has been this way for years, through several changes of staff.",
    "The paint on the sill is older still, and flaking at the edges.",
    "In summer the whole corner dries out and the pattern reverses.",
    "Newcomers hear about it within a week, usually over the midday break.",
    "The story outgrew the telling of it some generations back.",
    "Some mornings it simply does not happen, and nobody asks why.",
)


def load_store(path: Path, expect_sha_prefix: str) -> dict:
    store = json.loads(path.read_text(encoding="utf-8"))
    if not store["store_sha256"].startswith(expect_sha_prefix):
        raise ValueError(f"store pin mismatch: {path}")
    return store


def corrected_block(ids: list[str], store: dict) -> str | None:
    """The step-1 corrected rendering verbatim (delivery_v2_block): full
    fields, store order, no budget; None when nothing applies."""
    if not ids:
        return None
    by_id = {l["lessonId"]: l for l in store["lessons"]}
    lines = [DELIVERY_HEADER]
    for i, lid in enumerate(ids, start=1):
        les = by_id[lid]
        when = "; ".join(str(a) for a in les.get("applicability", [])) or "relevant"
        lines.append(f"{i}. {les['title']}. When {when}: "
                     f"Rule: {les['lesson']} Behavior: {les['recommendedBehavior']}")
    return "\n".join(lines)


def neutral_band(target: int) -> tuple[int, int]:
    """Shared ±25% band (ceil/floor — one definition for the composer and
    the checker so they can never disagree on the boundary)."""
    import math
    return math.ceil(target * 0.75), math.floor(target * 1.25)


def neutral_block(cluster: str) -> str | None:
    """Numbered-line shape matched to the treatment (line count == the
    NEWF-v2 delivery set size); pool lines chosen deterministically; tail
    sentences appended round-robin (smallest count first) until the word
    total lands inside ±25% of the treatment block. None when NEWF
    delivers nothing."""
    ids = NEWF2_APPL.get(cluster, [])
    if not ids:
        return None
    treatment = corrected_block(
        ids, load_store(NEWF2_STORE, NEWF2_STORE_SHA))
    target = len(treatment.split())
    lo, hi = neutral_band(target)
    idx = sorted(NEWF2_APPL).index(cluster)
    k = len(ids)
    for j in range(len(NEUTRAL_TAILS) + 1):
        lines = [DELIVERY_HEADER]
        bodies = [NEUTRAL_POOL[(idx + i) % len(NEUTRAL_POOL)] for i in range(k)]
        for t in range(j):
            bodies[t % k] = bodies[t % k].rstrip(".") + ". " + NEUTRAL_TAILS[t]
        for i, body in enumerate(bodies, start=1):
            lines.append(f"{i}. {body}")
        total = len(" ".join(lines).split())
        if lo <= total <= hi:
            return "\n".join(lines)
    raise ValueError(f"neutral composition failed for {cluster}: "
                     f"target {target} band [{lo},{hi}]")


def block_for(content: str, cluster: str) -> str | None:
    """The delivered block for (content, cluster); None = no delivery."""
    if content == "NONE":
        return None
    if content == "NEUTRAL":
        return neutral_block(cluster)
    if content == "NEWF2":
        return corrected_block(NEWF2_APPL[cluster], load_store(NEWF2_STORE, NEWF2_STORE_SHA))
    if content == "OLDG":
        return corrected_block(OLDG_APPL[cluster], load_store(OLDG_STORE, OLDG_STORE_SHA))
    raise ValueError(f"unknown content {content!r}")


# --- mechanical checks (used by --smoke and the exec-freeze gate) ---------

def check_neutral_word_match() -> dict[str, dict]:
    """Per cluster: NEUTRAL block words within ±25% of the NEWF-v2 block
    (the registered per-cluster control match; Addendum C's fix)."""
    newf2 = load_store(NEWF2_STORE, NEWF2_STORE_SHA)
    out = {}
    for cluster in PRIMARY_CLUSTERS:
        t = len((corrected_block(NEWF2_APPL[cluster], newf2) or "").split())
        n = len((neutral_block(cluster) or "").split())
        lo, hi = neutral_band(t)
        ok = lo <= n <= hi
        out[cluster] = {"newf2_words": t, "neutral_words": n,
                        "ratio": round(n / t, 2) if t else None, "ok": ok}
    return out


def check_neutral_vocab() -> tuple[list[str], list[str]]:
    """NEUTRAL and NEWF2 block words must NOT collide with the v3o ANSWER
    vocabulary (labels/expected/ids/seed values/initial_expected) —
    fail-closed symmetric treatment (the control and the primary treatment
    must not leak answers). OLDG collisions are REPORT-ONLY: the old gold
    store predates the v3o vocabulary discipline and is delivered AS
    AUTHORED (its known collision — LL-G-003 'sorting' on rt — is a
    declared confound of the OLDG arm, measured by a pre-registered
    exploratory check in the analyzer, never silently edited)."""
    import sys
    sys.path.insert(0, str(LAB_ROOT / "experiments" / "cont006"))
    from lessons_v2 import consumption_vocab
    vocab = consumption_vocab([LAB_ROOT / "fixtures" / "v3o"])
    fatal: list[str] = []
    oldg_report: list[str] = []
    newf2 = load_store(NEWF2_STORE, NEWF2_STORE_SHA)
    for cluster in PRIMARY_CLUSTERS:
        for content in ("NEUTRAL", "NEWF2", "OLDG"):
            block = block_for(content, cluster)
            if block is None:
                continue
            words = {w.lower() for w in block.replace(".", " ").split()}
            clash = sorted(words & vocab["tokens"])
            if not clash:
                continue
            entry = f"{content}/{cluster}: {clash}"
            if content == "OLDG":
                oldg_report.append(entry)
            else:
                fatal.append(entry)
    return fatal, oldg_report


def check_annotations() -> list[str]:
    """Every id resolves in its store; every NEWF2/OLDG annotated cluster
    is a known v3o cluster; every primary + VAL cluster has a NEWF2 set."""
    newf2 = load_store(NEWF2_STORE, NEWF2_STORE_SHA)
    oldg = load_store(OLDG_STORE, OLDG_STORE_SHA)
    problems = []
    for appl, store, scope in ((NEWF2_APPL, newf2, PRIMARY_CLUSTERS + VALIDATION_CLUSTERS),
                               (OLDG_APPL, oldg, PRIMARY_CLUSTERS)):
        known = {l["lessonId"] for l in store["lessons"]}
        for cluster, ids in appl.items():
            for lid in ids:
                if lid not in known:
                    problems.append(f"{cluster}: unknown lesson {lid}")
        for cluster in scope:
            if cluster not in appl or not appl[cluster]:
                problems.append(f"{cluster}: empty delivery set")
    return problems


if __name__ == "__main__":
    problems = check_annotations()
    match = check_neutral_word_match()
    bad_match = {c: v for c, v in match.items() if not v["ok"]}
    fatal, oldg_collisions = check_neutral_vocab()
    print("annotation problems:", problems or "none")
    print("word-match failures:", bad_match or "none")
    print("answer-vocab collisions (NEUTRAL/NEWF2, FATAL):", fatal or "none")
    print("answer-vocab collisions (OLDG, declared/report-only):",
          oldg_collisions or "none")
    for c, v in match.items():
        print(f"  {c}: newf2={v['newf2_words']}w neutral={v['neutral_words']}w "
              f"ratio={v['ratio']} {'OK' if v['ok'] else 'FAIL'}")
    raise SystemExit(0 if not (problems or bad_match or fatal) else 2)
