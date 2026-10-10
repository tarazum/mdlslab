"""Deterministic builder for fixture suite v3o (CONT-006 STAGE 2 end-to-end
surface; owner-authorized 2026-10-10 via SESSION-BRIEF-CONT006-STAGE2.md).

Why a new suite: stage 2 needs the first END-TO-END (not replay) lesson-
transfer test on a surface where the STRONG model has headroom, with the rt
LINEN_CARD defect fixed by construction (audit defect 5: v3n rt-8203/8204
expected categories whose rules were never stated).

Composition identical to v3n (15 TR primary + 4 VAL + GC x3; every taxonomy
class >= 2 primary clusters), mechanics INHERITED from the frozen suites
only (v3i/v3j seed_error mechanisms incl. the cr-retraction sub-type and
initial_expected; v3k lure_value + label windows), ids x-9xxx, seeds
{9001..9007}, fresh worlds (slate quarry tally hut; tar kettle shed / net
loft mend bench / pump plunger lodge gauge row / maltings floor room / salt store
bin row; railway parcel office; mine lamp station / sawmill filing room /
gasworks meter house; apothecary still room / coaling jetty hopper deck;
tea warehouse loft / tram depot pit / cooper's yard shed). V18
world-freshness vs ALL prior suites incl. v3n.

Design folds (each lever declared, verified mechanically by the builder and
the fixture validator; model-level bands are verified by the in-run
baseline gate pre-registered with the stage-2 prereg — no separate
calibration phase in this stage):

- rt REPAIRED (defect 5, by construction): every rt cluster renders the
  FULL rule card (all six categories) in s1; the builder asserts every
  tag of the vocabulary appears in the rendered card text. No probe
  expects a category whose rule was never stated. FP-2 sheet-trap
  mechanism unchanged.
- cr HARDER (Q35 was 14/14 on v3n cr at every condition): (i) WITHIN-LINE
  PHRASE GENERALIZATION — v3n probe items repeated the SAME card head
  phrase as the learning item ("loam build" -> "loam build"); v3o probe
  items use the OTHER head phrase of the same card line ("froe split" at
  learning -> "cleave run" at probe), so the mapping is no longer verbatim
  echo; (ii) one cluster uses the inherited cr-RETRACTION sub-type
  (bulletin re-routes, withdrawal restores — a double reversal to track).
- cu: one cluster deepens the inherited superseded chain (old -> mid ->
  new; probe expects new; mid stays in options as a near-miss).
- dx HARDER (Q35 was 14/14 on v3n dx): TWO lures — one transposition-
  confusable with the target, one same-kind — and BOTH re-confirmed after
  the learning turn while the target code is stated once.
- dr: inherited two-entity interference, fresh worlds.
- GC unchanged in kind (expected null by design; fresh option pools
  disjoint from the validator-V2 C2 collision words).

Deterministic: no RNG, explicit tables only. Re-running overwrites
fixtures/v3o byte-identically.
"""

from __future__ import annotations

import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = LAB_ROOT / "fixtures" / "v3o"
SEEDS = [9001, 9002, 9003, 9004, 9005, 9006, 9007]

VALIDATION_IDS = ["cr-9005", "cu-9105", "rt-9204", "dx-9403"]


def rot(seq: list[str], k: int) -> list[str]:
    n = len(seq)
    return [seq[(i + k) % n] for i in range(n)]


def perm_orders(vocab: list[str], i: int) -> list[str]:
    """7 pairwise-distinct label orders over a FIXED 6-word vocabulary
    (6 rotations + a transposition of the identity; same device as v3l..v3n)."""
    orders = [rot(vocab, k) for k in range(6)]
    ident = list(vocab)
    ident[0], ident[1] = ident[1], ident[0]
    orders.append(ident)
    return orders[i]


def variants(rows: list[dict]) -> dict:
    return {str(sd): {"values": rows[i]["values"], "probes": rows[i]["probes"]}
            for i, sd in enumerate(SEEDS)}


def write_scenario(rel: str, scenario: dict) -> None:
    path = OUT_DIR / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scenario, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")


# ============================================================================
# correction_reuse x5 — slate quarry tally hut; vocab fixed.
# HARDER: within-line phrase generalization (probe uses the OTHER head
# phrase of the card line; v3n repeated the learning phrase verbatim) +
# one retraction cluster (double reversal).
# ============================================================================

SLATE = ["riving", "dressing", "hogging", "holing", "bedding", "hauloff"]
SLATE_CARD = ("The standing quarry card: froe splits and cleave runs are riving; "
              "plane passes and edge trims are dressing; coarse saws and bulk rips "
              "are hogging; hole punches and slot drills are holing; mortar beds "
              "and pin sets are bedding; sledge runs and wagon loads are hauloff.")
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]

# the two head-phrase families of each card line (singular form as used in
# items; the card text carries the plurals)
CR_LINE_PHRASES = {
    "riving": ("froe split", "cleave run"),
    "dressing": ("plane pass", "edge trim"),
    "hogging": ("coarse saw", "bulk rip"),
    "holing": ("hole punch", "slot drill"),
    "bedding": ("mortar bed", "pin set"),
    "hauloff": ("sledge run", "wagon load"),
}


def cr_probe_session() -> list[dict]:
    return [
        {"actor": "environment", "text": "Night desk at the quarry hut on {day}. The quarry card is away. Acknowledge in one short line."},
        {"actor": "environment", "text": "File this report. The quarry card is not at hand. Report: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
    ]


def cr_rows(bks: list[str], pqs: list[str], expected: str,
            probe_turn: str) -> list[dict]:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"bk": bks[i], "pq": pqs[i], "day": DAYS[i]},
            "probes": {probe_turn: {"labels": perm_orders(SLATE, i), "expected": expected}},
        })
    return rows


def cr_vce_vct(sid: str, sub: str, thing: str, note: str, corr: str,
               expected: str, trap: str, bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": sub,
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"For the quarry desk: log this report under exactly one label: {' | '.join(SLATE)}. Report: '{{bk}} {thing}.' Reply with the label only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your tally-hut log from the previous shift files {{bk}} {thing} under '{trap}'. Keep the log line in view and acknowledge in one short line."},
                {"actor": "environment", "text": SLATE_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr + " Amend your records in one short line."},
            ]},
            {"index": 3, "turns": cr_probe_session()},
        ],
        "variants": variants(cr_rows(bks, pqs, expected, "s3t2")),
    }


cr_9001 = cr_vce_vct(
    "cr-9001", "valid_correction_environment", "on the day sheet",
    "froe split logged 'dressing'; quarry notice re-routes to riving (FP-3a); probe uses the line's OTHER phrase (cleave run)",
    "Quarry bulletin, verified notice from the bench master: the log line "
    "filing {bk} under 'dressing' is out of date; froe splits and cleave "
    "runs are riving under the standing card.",
    "riving", "dressing",
    # bks: phrase A (froe split) of the riving line
    ["the froe split for the south vein", "the froe split at the top bench",
     "the froe split on the sample block", "the froe split for the gable set",
     "the froe split at the east face", "the froe split on the roof stock",
     "the froe split for the ridge lot"],
    # pqs: phrase B (cleave run) of the SAME line
    ["the cleave run before the night cast", "the cleave run past the gate close",
     "the cleave run on the spare blocks", "the cleave run for the day gables",
     "the cleave run at the far bench", "the cleave run for the roof lots",
     "the cleave run under the tally rule"],
)


def cr_euc(sid: str, note: str, insist: str, expected: str, trap: str,
           bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": "erroneous_user_correction",
        "seed_error": {"value": trap, "mechanism": "user_override"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"For the quarry desk: log this report under exactly one label: {' | '.join(SLATE)}. Report: '{{bk}}.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": SLATE_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": insist + " Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": cr_probe_session()},
        ],
        "variants": variants(cr_rows(bks, pqs, expected, "s3t2")),
    }


cr_9003 = cr_euc(
    "cr-9003",
    "wagon load correctly 'hauloff'; shed hand pushes 'bedding' (FP-3b); probe uses the line's OTHER phrase (sledge run)",
    "A shed hand presses about {bk}: 'count that one as bedding for my pin "
    "list - every earlier tally has done so.' The sledge book, on file, keeps "
    "the entry as it stands.",
    "hauloff", "bedding",
    # bks: phrase A (wagon load) of the hauloff line
    ["the wagon load for the rail siding", "the wagon load at the north tip",
     "the wagon load for the harbour cart", "the wagon load on the waste day",
     "the wagon load for the broad gauge", "the wagon load at the slate foot",
     "the wagon load for the mill dray"],
    # pqs: phrase B (sledge run) of the SAME line
    ["the sledge run before the night cast", "the sledge run past the tip gate",
     "the sledge run on the waste road", "the sledge run for the day siding",
     "the sledge run at the far yard", "the sledge run for the rail lots",
     "the sledge run under the tally rule"],
)


def cr_retraction(sid: str, note: str, bulletin: str, withdraw: str,
                  expected: str, trap: str, bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": "retraction",
        "seed_error": {"value": trap, "mechanism": "retracted_correction"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"For the quarry desk: log this report under exactly one label: {' | '.join(SLATE)}. Report: '{{bk}} on the day sheet.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": SLATE_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": bulletin + " Amend in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "source_type": "environment", "text": withdraw + " Amend in one short line."},
            ]},
            {"index": 4, "turns": cr_probe_session()},
        ],
        "variants": variants(cr_rows(bks, pqs, expected, "s4t2")),
    }


cr_9004 = cr_retraction(
    "cr-9004",
    "plane pass correctly 'dressing'; bulletin briefly routes under 'hogging', then withdrawn; probe expects dressing (FP-1 retraction, double reversal; probe uses the line's OTHER phrase: edge trim)",
    "Quarry bulletin: the engine bench covers {bk} this week; classify such "
    "work under the coarse-saw rule for now. Amend in one short line.",
    "The bulletin is withdrawn: it was misrouted from the engine bench and "
    "does not apply here; the standing card holds as before. Amend in one "
    "short line.",
    "dressing", "hogging",
    # bks: phrase A (plane pass) of the dressing line
    ["the plane pass for the sill stock", "the plane pass at the long bench",
     "the plane pass on the lintel set", "the plane pass for the step pieces",
     "the plane pass at the west bench", "the plane pass on the cill blocks",
     "the plane pass for the door stock"],
    # pqs: phrase B (edge trim) of the SAME line
    ["the edge trim before the night cast", "the edge trim past the gate close",
     "the edge trim on the spare lintels", "the edge trim for the day steps",
     "the edge trim at the far bench", "the edge trim for the door lots",
     "the edge trim under the tally rule"],
)


def cr_sc(sid: str, note: str, verified: str, unreviewed: str, expected: str,
          trap: str, bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": "source_conflict",
        "seed_error": {"value": trap, "mechanism": "source_conflict"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"For the quarry desk: log this report under exactly one label: {' | '.join(SLATE)}. Report: '{{bk}} on the watch sheet.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": SLATE_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": verified + " Note it in one short line."},
                {"actor": "environment", "source_type": "environment", "text": unreviewed},
            ]},
            {"index": 3, "turns": cr_probe_session()},
        ],
        "variants": variants(cr_rows(bks, pqs, expected, "s3t2")),
    }


cr_9002 = cr_sc(
    "cr-9002",
    "slot drill correctly 'holing'; unreviewed rack slate claims 'hogging' (FP-3b); probe uses the line's OTHER phrase (hole punch)",
    "The bench clerk's memo, quarry-verified: hole punches and slot drills "
    "stay with holing, and {bk} stays as the card has it.",
    "An unreviewed rack slate by the skip door claims every slot drill, "
    "{bk} included, was moved to the saw bench today.",
    "holing", "hogging",
    # bks: phrase B (slot drill) of the holing line — learning uses B, probe A
    ["the slot drill for the door stock", "the slot drill on the stair pieces",
     "the slot drill at the gate jamb", "the slot drill for the sill bolts",
     "the slot drill on the ridge pieces", "the slot drill at the lintel bore",
     "the slot drill for the porch set"],
    # pqs: phrase A (hole punch) of the SAME line
    ["the hole punch before the night cast", "the hole punch past the gate close",
     "the hole punch on the spare jambs", "the hole punch for the day sills",
     "the hole punch at the far bench", "the hole punch for the ridge lots",
     "the hole punch under the tally rule"],
)

cr_9005 = cr_sc(
    "cr-9005",
    "VAL cluster (activation only): mortar bed correctly 'bedding'; unreviewed tip board claims 'riving' (FP-3b); probe uses the line's OTHER phrase (pin set)",
    "The stores clerk's memo, quarry-verified: mortar beds and pin sets stay "
    "with bedding, and {bk} stays as the card has it.",
    "An unreviewed tip board claims the mortar beds, {bk} included, were "
    "moved to the split bench today.",
    "bedding", "riving",
    # bks: phrase A (mortar bed) of the bedding line
    ["the mortar bed for the porch floor", "the mortar bed at the gable foot",
     "the mortar bed on the sill course", "the mortar bed for the step rises",
     "the mortar bed at the jamb build", "the mortar bed on the cope stones",
     "the mortar bed for the hearth slabs"],
    # pqs: phrase B (pin set) of the SAME line
    ["the pin set before the night cast", "the pin set past the gate close",
     "the pin set on the spare jambs", "the pin set for the day sills",
     "the pin set at the far bench", "the pin set for the gable lots",
     "the pin set under the tally rule"],
)

cr_scenarios = [cr_9001, cr_9002, cr_9003, cr_9004, cr_9005]


# ============================================================================
# contradiction_update x5 — FP-1. One cluster deepens the superseded chain
# (old -> mid -> new; probe expects NEW; mid stays in options).
# ============================================================================

def cu_superseded(sid: str, note: str, state: str, corr: str, ask: str,
                  q: str, base: int, step_new: int) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        old, new = base + 3 * i, base + 3 * i + step_new
        labs = [str(x) for x in rot([old, new, old - 4, new + 4, old - 8, new + 8], (i + 1) % 6)]
        rows.append({"values": {"old": str(old), "new": str(new)},
                     "probes": {"s3t2": {"labels": labs, "expected": str(new)}}})
    return {
        "id": sid, "family": "contradiction_update",
        "seed_error": {"value": "{old}", "mechanism": "superseded_value"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "source_type": "environment", "text": state},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": ask},
                {"actor": "environment", "text": q + " Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows),
    }


def cu_superseded_twice(sid: str, note: str, state: str, corr1: str, corr2: str,
                        ask: str, q: str, base: int) -> dict:
    """v3o difficulty fold: a DEEPER superseded chain — old -> mid (s2) ->
    new (s3); probe expects NEW; mid stays in options as a near-miss."""
    rows = []
    for i in range(len(SEEDS)):
        old, mid, new = base + 3 * i, base + 3 * i + 2, base + 3 * i + 6
        labs = [str(x) for x in rot([old, mid, new, old - 5, mid + 6, new + 4], (i + 1) % 6)]
        rows.append({"values": {"old": str(old), "mid": str(mid), "new": str(new)},
                     "probes": {"s4t2": {"labels": labs, "expected": str(new)}}})
    return {
        "id": sid, "family": "contradiction_update",
        "seed_error": {"value": "{old}", "mechanism": "superseded_value"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "source_type": "environment", "text": state},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr1},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr2},
            ]},
            {"index": 4, "turns": [
                {"actor": "environment", "text": ask},
                {"actor": "environment", "text": q + " Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows),
    }


def cu_retracted(sid: str, note: str, state: str, corr: str, withdraw: str,
                 ask: str, q: str, base: int, step_new: int) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        old, new = base + 3 * i, base + 3 * i + step_new
        labs = [str(x) for x in rot([old, new, old - 5, new + 5, old - 10, new + 10], (i + 2) % 6)]
        rows.append({"values": {"old": str(old), "new": str(new)},
                     "probes": {"s4t2": {"labels": labs, "expected": str(old)}}})
    return {
        "id": sid, "family": "contradiction_update",
        "seed_error": {"value": "{new}", "mechanism": "retracted_correction"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "source_type": "environment", "text": state},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "source_type": "environment", "text": withdraw},
            ]},
            {"index": 4, "turns": [
                {"actor": "environment", "text": ask},
                {"actor": "environment", "text": q + " Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows),
    }


cu_9101 = cu_superseded(
    "cu-9101",
    "tar kettle shed pail counts corrected; probe expects NEW value (FP-1)",
    "You keep the tar kettle shed book. For the log: the boiling kettle takes {old} tallow pails per charge. Acknowledge in one short line.",
    "Correction for the records: the ladle size changed; the boiling kettle now takes {new} tallow pails per charge, not {old}. Note the correction in one short line.",
    "A tar hand asks; the shed book is away. Acknowledge in one short line.",
    "How many tallow pails does the boiling kettle take per charge?",
    43, 6,
)
cu_9102 = cu_superseded_twice(
    "cu-9102",
    "net loft patch counts corrected TWICE (old->mid->new); probe expects NEW (FP-1, chained)",
    "You tend the net loft mend bench. For the log: the drift net takes {old} mesh patches per panel. Acknowledge in one short line.",
    "Correction for the records: the twine gauge changed; the drift net now takes {mid} mesh patches per panel, not {old}. Note the correction in one short line.",
    "Further correction for the records: the panel width was re-cut; the drift net now takes {new} mesh patches per panel, not {mid}. Note this correction in one short line.",
    "A skipper asks; the loft bench card is away. Acknowledge in one short line.",
    "How many mesh patches does the drift net take per panel?",
    25,
)
cu_9103 = cu_retracted(
    "cu-9103",
    "plunger lodge stroke counts corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You mind the plunger lodge gauge row. For the log: the force pump counts {old} stroke turns per hour. Acknowledge in one short line.",
    "Correction for the records: the valve cam was swapped; the force pump now counts {new} stroke turns per hour, not {old}. Note the correction in one short line.",
    "The pump master says the correction is withdrawn: the swapped cam belonged to the standby pump and does not apply here; the standing count from the first log holds as before. Amend in one short line.",
    "A fitter asks; the lodge card is away. Acknowledge in one short line.",
    "How many stroke turns does the force pump count per hour?",
    34, 5,
)
cu_9104 = cu_retracted(
    "cu-9104",
    "maltings turn counts corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You run the maltings floor room. For the log: the floor malt takes {old} turn spans per day. Acknowledge in one short line.",
    "Correction for the records: the rakes were re-set; the floor malt now takes {new} turn spans per day, not {old}. Note the correction in one short line.",
    "The maltster says the correction is withdrawn: the re-set slip came from the steep house floor and does not apply; the standing turns from the first log hold as before. Amend in one short line.",
    "A kiln man asks; the floor card is away. Acknowledge in one short line.",
    "How many turn spans does the floor malt take per day?",
    17, 6,
)
cu_9105 = cu_superseded(
    "cu-9105",
    "VAL cluster (activation only): salt store tier counts corrected; probe expects NEW (FP-1)",
    "You mind the salt store bin row. For the log: the bay salt stacks {old} bin tiers per rank. Acknowledge in one short line.",
    "Correction for the records: the bin frames were rebuilt; the bay salt now stacks {new} bin tiers per rank, not {old}. Note the correction in one short line.",
    "A lighter man asks; the store card is away. Acknowledge in one short line.",
    "How many bin tiers does the bay salt stack per rank?",
    28, 7,
)

cu_scenarios = [cu_9101, cu_9102, cu_9103, cu_9104, cu_9105]


# ============================================================================
# repeated_task x4 — railway parcel office counter; FP-2.
# REPAIRED (stage-2 defect fix): the FULL rule card (all six categories) is
# rendered in s1 for EVERY cluster — no probe expects a category whose rule
# was never stated. FP-2 sheet-trap mechanism unchanged from v3n.
# ============================================================================

PARCEL = ["booking", "sorting", "packing", "securing", "hauling", "filing"]
PARCEL_CARD = ("The standing parcel card: waybill takes and fare notes are "
               "booking; bin drops and shelf stackings are sorting; string "
               "ties and wrapper seals are packing; strap tensions and corner "
               "guards are securing; trolley runs and yard pushes are hauling; "
               "signature slips and receipt stubs are filing.")
SLOTS = ["morning", "van load", "lunch", "mail day", "afternoon", "express", "night shift"]

RT_LINE_PHRASES = {
    "booking": ("waybill take", "fare note"),
    "sorting": ("bin drop", "shelf stacking"),
    "packing": ("string tie", "wrapper seal"),
    "securing": ("strap tension", "corner guard"),
    "hauling": ("trolley run", "yard push"),
    "filing": ("signature slip", "receipt stub"),
}


def rt_scenario(sid: str, trap: str, expected: str,
                tasks: list[str], pqs: list[str]) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"task": tasks[i], "pq": pqs[i], "slot": SLOTS[i]},
            "probes": {"s3t2": {"labels": perm_orders(PARCEL, i), "expected": expected}},
        })
    return {
        "id": sid, "family": "repeated_task", "sub_type": "scripted_own_answer",
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": f"counter sheet pins '{trap}'; standing card says {expected}; FULL card stated in s1; probe expects {expected} (FP-2)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Pick exactly one tag: {' | '.join(PARCEL)}. Errand: '{{task}}.' Reply with the tag only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your earlier counter sheet tags {{task}} as '{trap}'. {PARCEL_CARD} Amend the sheet in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Counter handover before {slot}. The standing parcel card applies. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "New round opens at the parcel counter. The slate cards are locked away. Acknowledge in one short line."},
                {"actor": "environment", "text": "Pick one tag for this errand. No cards are in reach. Errand: '{pq}.' Options: {options} - reply with the tag only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows),
    }


rt_scenarios = [
    rt_scenario(
        "rt-9201", "hauling", "packing",
        ["the string tie round for the evening post", "the string tie round for the fair bundles",
         "the string tie round on the hat boxes", "the string tie round for the seed packets",
         "the string tie round for the night bags", "the string tie round on the ribbon rolls",
         "the string tie round for the parcel post"],
        ["the wrapper seal round for the morning crate", "the wrapper seal round before the van load",
         "the wrapper seal round on the spare boxes", "the wrapper seal round for the book packets",
         "the wrapper seal round at the far bench", "the wrapper seal round for the mail bags",
         "the wrapper seal round before the shut"],
    ),
    rt_scenario(
        "rt-9202", "booking", "filing",
        ["the signature slip round for the claim desk", "the signature slip round for the dead letter room",
         "the signature slip round on the insured tray", "the signature slip round for the penny post",
         "the signature slip round for the cod counter", "the signature slip round on the ledger shelf",
         "the signature slip round for the night bag"],
        ["the receipt stub round for the dawn bag", "the receipt stub round before the mail day",
         "the receipt stub round on the late tray", "the receipt stub round for the sample post",
         "the receipt stub round at the side desk", "the receipt stub round for the cod bags",
         "the receipt stub round after the count"],
    ),
    rt_scenario(
        "rt-9203", "sorting", "securing",
        ["the strap tension check for the crate lot", "the strap tension check for the mirror crate",
         "the strap tension check on the tool chest", "the strap tension check for the clock case",
         "the strap tension check for the organ crate", "the strap tension check on the glass rack",
         "the strap tension check for the tile box"],
        ["the corner guard round for the evening lot", "the corner guard round before the express",
         "the corner guard round on the spare chest", "the corner guard round for the frame case",
         "the corner guard round at the north door", "the corner guard round for the slate rack",
         "the corner guard round after the tally"],
    ),
    rt_scenario(
        "rt-9204", "packing", "sorting",
        ["the bin drop round for the letter flats", "the bin drop round for the parcel tubs",
         "the bin drop round on the paper sacks", "the bin drop round for the sample trays",
         "the bin drop round for the news bundles", "the bin drop round on the label racks",
         "the bin drop round for the night sacks"],
        ["the shelf stacking round for the morning flats", "the shelf stacking round before the van load",
         "the shelf stacking round on the spare sacks", "the shelf stacking round for the mail tubs",
         "the shelf stacking round at the east wall", "the shelf stacking round for the wire trays",
         "the shelf stacking round after the count"],
    ),
]


# ============================================================================
# distractor_recall x3 (FP-4) — HARDER than v3n (Q35 was 14/14 there): TWO
# lures — one transposition-confusable with the target, one same-kind — and
# BOTH re-confirmed after the learning turn while the target code is stated
# once in s1.
# ============================================================================

MINE = {"place": "mine lamp station", "book": "lamp station book",
        "chores": ["the cage gate grease", "the lamp rack wipe", "the oil can fill",
                   "the reflector polish", "the trough rinse", "the bench brush", "the dusk lamp count"],
        "roles": ["banksman", "lamp man", "onsetter", "shaft keeper",
                  "road layer", "cage tender", "night viewer"],
        "lure_holder": "pit top office"}
SAWMILL = {"place": "sawmill filing room", "book": "filing room book",
           "chores": ["the swage seat clean", "the gauge set oil", "the anvil toll count",
                      "the hammer face polish", "the rivet tray sort", "the bench dust", "the dusk shutter bar"],
           "roles": ["filer", "saw doctor", "mill man", "bench hand",
                     "log clerk", "carriage setter", "night miller"],
           "lure_holder": "log scale office"}
GASWORKS = {"place": "gasworks meter house", "book": "meter house book",
            "chores": ["the index glass wipe", "the seal tin count", "the bypass valve oil",
                       "the test dial brush", "the governor dust", "the pipe clip check", "the dusk lamp round"],
            "roles": ["meter man", "stoker", "fitter", "purifier hand",
                      "retort man", "works clerk", "night meter"],
            "lure_holder": "works office"}

DX_DIGITS = [(17, 71), (23, 32), (45, 54), (68, 86), (19, 91), (26, 62), (38, 83)]


def dx_rows(prefix: str, world: dict) -> list[dict]:
    """Per seed i: target = pairs[i][0], lureA (transposition twin) =
    pairs[i][1], lureB (same-kind) = pairs[(i+1)%7][1]; three fillers walk
    the ladder so every seed's 6-code option set is pairwise distinct."""
    pairs = [(f"{prefix}{a}", f"{prefix}{b}") for a, b in DX_DIGITS]
    rows = []
    for i in range(len(SEEDS)):
        code = pairs[i][0]
        lurea, lureb = pairs[i][1], pairs[(i + 1) % 7][1]
        fillers = [pairs[(i + 2) % 7][0], pairs[(i + 3) % 7][0], pairs[(i + 4) % 7][1]]
        labels = rot([code, lurea, lureb, *fillers], i % 6)
        rows.append({
            "values": {"code": code, "lurea": lurea, "lureb": lureb,
                       "chore": world["chores"][i], "role": world["roles"][i]},
            "probes": {"s3t2": {"labels": labels, "expected": code}},
        })
    return rows


def dx_scenario(sid: str, world: dict, thing: str, lurea_thing: str,
                lureb_thing: str, rows: list[dict]) -> dict:
    return {
        "id": sid, "family": "distractor_recall",
        "labels": {"note": f"three codes stated at learning ({thing} target; "
                           f"{lurea_thing} and {lureb_thing} lures); BOTH lures are "
                           "re-confirmed in s2 while the target code is stated once "
                           "(v3o difficulty fold); probe asks the target with all "
                           "three in options; lure_value declared for validator "
                           "V8R (FP-4)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}; the {lurea_thing} code is {{lurea}}; the {lureb_thing} code is {{lureb}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": f"Reminder from the {world['lure_holder']}: the {lurea_thing} code {{lurea}} and the {lureb_thing} code {{lureb}} were re-checked this morning and still stand. {{chore}} finished. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives from the {world['lure_holder']} run; the {world['book']} is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "lure_value": "{lurea}",
        "variants": variants(rows),
    }


dx_scenarios = [
    dx_scenario("dx-9401", MINE, "self-rescuer cabinet", "battery tray",
                "cap lamp rail", dx_rows("L", MINE)),
    dx_scenario("dx-9402", SAWMILL, "blade crate", "swage box",
                "gauge kit", dx_rows("G", SAWMILL)),
    dx_scenario("dx-9403", GASWORKS, "meter key", "index card",
                "seal tin", dx_rows("Q", GASWORKS)),
]


# ============================================================================
# delayed_recall x2 (FP-5) — inherited v3n mechanics (two other entities'
# codes of the same kind logged in s2; lure_value = first interference
# code); fresh worlds.
# ============================================================================

STILL = {"place": "apothecary still room", "book": "still room ledger",
         "chores": ["the worm coil wipe", "the alembic joint paste", "the jar shelf count",
                    "the brazier rake", "the funnel rinse", "the bench dust", "the dusk shutter bar"],
         "roles": ["apothecary", "journeyman", "herb wife", "porter",
                   "physician", "clerk", "night watch"]}
JETTY = {"place": "coaling jetty hopper deck", "book": "hopper deck slate",
         "chores": ["the chute gate oil", "the boom brace check", "the bucket count",
                    "the screen rake", "the apron sweep", "the rail dust", "the dusk lamp round"],
         "roles": ["wharfinger", "hoist man", "trimmer", "tally clerk",
                   "barge mate", "coal viewer", "night watch"]}


def dr_rows(alphabet: list[str], world: dict) -> list[dict]:
    rows = []
    n = len(alphabet)
    for i in range(len(SEEDS)):
        code = alphabet[i % n]
        o1, o2 = alphabet[(i + 1) % n], alphabet[(i + 2) % n]
        window = [alphabet[(i + k) % n] for k in range(6)]
        labels = rot(window, i % 6)
        rows.append({
            "values": {"code": code, "o1": o1, "o2": o2,
                       "chore": world["chores"][i], "role": world["roles"][i]},
            "probes": {"s3t2": {"labels": labels, "expected": code}},
        })
    return rows


def dr_scenario(sid: str, world: dict, thing: str, other_things: list[str],
                rows: list[dict]) -> dict:
    return {
        "id": sid, "family": "delayed_recall",
        "labels": {"note": f"{thing} code stated at learning; s2 logs TWO other "
                           "entities' codes of the same kind (interference); probe "
                           f"asks the {thing} code with all three in options; "
                           "lure_value = the first interference code (FP-5 binding "
                           "under interference)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": f"For the log: the {other_things[0]} code is {{o1}}; the {other_things[1]} code is {{o2}}; all else stands as before. {{chore}} finished. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives; the {world['book']} is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "lure_value": "{o1}",
        "variants": variants(rows),
    }


dr_scenarios = [
    dr_scenario("dr-9301", STILL, "essence cabinet",
                ["retort stand", "oil press"], dr_rows(
                    ["V21", "V27", "V33", "V39", "V45", "V51", "V57",
                     "V63", "V69", "V75", "V81", "V87"], STILL)),
    dr_scenario("dr-9302", JETTY, "grab crane",
                ["trim hopper", "spurn guard"], dr_rows(
                    ["W24", "W30", "W36", "W42", "W48", "W54", "W60",
                     "W66", "W72", "W78", "W84", "W90"], JETTY)),
]


# ============================================================================
# guess_calibration x3 — never-stated facts (word + number), fresh pools,
# DISJOINT from the validator-V2 C2 collision words (so the v3o consumption
# vocabulary cannot collide with C2-exempt mining-side lesson words).
# ============================================================================

TEAS = ["assam", "keemun", "ceylon", "oolong", "lapsang", "sencha", "jasmine"]
GREASES = ["tallow", "graphite", "stearin", "lanolin", "spermaceti", "beeswax", "petrolatum"]
HOOP_WOODS = ["oak", "ash", "elm", "beech", "maple", "chestnut", "poplar"]


def win(pool: list[str], i: int) -> list[str]:
    return rot(pool, i)[:6]


def gc_scenario(sid: str, opener: str, asker: str, q1: str, q2: str,
                word_labels: list[str], rows: list[dict]) -> dict:
    return {
        "id": sid, "family": "guess_calibration",
        "labels": {"note": "never-stated facts; guess rate and position bias; expected "
                           "null by design; run on the working core"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": opener},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": asker},
                {"actor": "environment", "text": q1 + " Options: {options} - reply with the word only.", "probe": {"kind": "guess_calibration", "expected": None, "class": "guess_cal"}},
                {"actor": "environment", "text": q2 + " Options: {options} - reply with the number only.", "probe": {"kind": "guess_calibration", "expected": None, "class": "guess_cal"}},
            ]},
        ],
        "variants": variants(rows),
    }


gc_9501 = gc_scenario(
    "gc-9501",
    "You mind the tea warehouse loft on the {shift} stint. Acknowledge in one short line.",
    "{visitor} asks about blends this loft never marked. Answer as best you can. Acknowledge in one short line.",
    "What leaf fills the {e1} chest?",
    "How many chests ride the {e2} pallet?",
    TEAS,
    [
        {"values": {"shift": "first picking", "visitor": "a blender", "e1": "morning", "e2": "north"},
         "probes": {"s2t2": {"labels": win(TEAS, 0)}, "s2t3": {"labels": ["31", "34", "37", "40", "43", "46"]}}},
        {"values": {"shift": "auction eve", "visitor": "a broker", "e1": "midday", "e2": "south"},
         "probes": {"s2t2": {"labels": win(TEAS, 1)}, "s2t3": {"labels": ["32", "35", "38", "41", "44", "47"]}}},
        {"values": {"shift": "monsoon watch", "visitor": "a taster", "e1": "evening", "e2": "east"},
         "probes": {"s2t2": {"labels": win(TEAS, 2)}, "s2t3": {"labels": ["33", "36", "39", "42", "45", "48"]}}},
        {"values": {"shift": "sampling day", "visitor": "a buyer", "e1": "night", "e2": "west"},
         "probes": {"s2t2": {"labels": win(TEAS, 3)}, "s2t3": {"labels": ["34", "37", "40", "43", "46", "49"]}}},
        {"values": {"shift": "blending week", "visitor": "a grower", "e1": "dawn", "e2": "top"},
         "probes": {"s2t2": {"labels": win(TEAS, 4)}, "s2t3": {"labels": ["35", "38", "41", "44", "47", "50"]}}},
        {"values": {"shift": "pack out", "visitor": "a tally lad", "e1": "dusk", "e2": "lower"},
         "probes": {"s2t2": {"labels": win(TEAS, 5)}, "s2t3": {"labels": ["36", "39", "42", "45", "48", "51"]}}},
        {"values": {"shift": "fumigation", "visitor": "a warehouse man", "e1": "small hours", "e2": "far"},
         "probes": {"s2t2": {"labels": win(TEAS, 6)}, "s2t3": {"labels": ["37", "40", "43", "46", "49", "52"]}}},
    ],
)
gc_9502 = gc_scenario(
    "gc-9502",
    "You keep the tram depot pit on the {shift} turn. Acknowledge in one short line.",
    "{visitor} asks about notes this pit never kept. Answer as best you can. Acknowledge in one short line.",
    "What grease packs the {e1} box?",
    "How many lamps ride the {e2} pole?",
    GREASES,
    [
        {"values": {"shift": "first car in", "visitor": "a motorman", "e1": "axle", "e2": "corner"},
         "probes": {"s2t2": {"labels": win(GREASES, 0)}, "s2t3": {"labels": ["51", "54", "57", "60", "63", "66"]}}},
        {"values": {"shift": "peak grid", "visitor": "a conductor", "e1": "motor", "e2": "mid"},
         "probes": {"s2t2": {"labels": win(GREASES, 1)}, "s2t3": {"labels": ["52", "55", "58", "61", "64", "67"]}}},
        {"values": {"shift": "slack noon", "visitor": "a shed hand", "e1": "trailing", "e2": "span"},
         "probes": {"s2t2": {"labels": win(GREASES, 2)}, "s2t3": {"labels": ["53", "56", "59", "62", "65", "68"]}}},
        {"values": {"shift": "wash pad", "visitor": "a fitter", "e1": "leading", "e2": "end"},
         "probes": {"s2t2": {"labels": win(GREASES, 3)}, "s2t3": {"labels": ["54", "57", "60", "63", "66", "69"]}}},
        {"values": {"shift": "night spray", "visitor": "a sprayer", "e1": "centre", "e2": "top"},
         "probes": {"s2t2": {"labels": win(GREASES, 4)}, "s2t3": {"labels": ["55", "58", "61", "64", "67", "70"]}}},
        {"values": {"shift": "frost guard", "visitor": "a watchman", "e1": "rear", "e2": "base"},
         "probes": {"s2t2": {"labels": win(GREASES, 5)}, "s2t3": {"labels": ["56", "59", "62", "65", "68", "71"]}}},
        {"values": {"shift": "pull in", "visitor": "an inspector", "e1": "front", "e2": "foot"},
         "probes": {"s2t2": {"labels": win(GREASES, 6)}, "s2t3": {"labels": ["57", "60", "63", "66", "69", "72"]}}},
    ],
)
gc_9503 = gc_scenario(
    "gc-9503",
    "You tend the cooper's yard shed on the {shift} stretch. Acknowledge in one short line.",
    "{visitor} drops by and asks about tallies this shed never logged. Answer as best you can. Acknowledge in one short line.",
    "What wood hoops the {e1} cask?",
    "How many staves wait on the {e2} horse?",
    HOOP_WOODS,
    [
        {"values": {"shift": "first shave", "visitor": "a journeyman", "e1": "wash", "e2": "near"},
         "probes": {"s2t2": {"labels": win(HOOP_WOODS, 0)}, "s2t3": {"labels": ["61", "64", "67", "70", "73", "76"]}}},
        {"values": {"shift": "truss day", "visitor": "a brewer", "e1": "wine", "e2": "far"},
         "probes": {"s2t2": {"labels": win(HOOP_WOODS, 1)}, "s2t3": {"labels": ["62", "65", "68", "71", "74", "77"]}}},
        {"values": {"shift": "fire bending", "visitor": "an apprentice", "e1": "spirit", "e2": "mid"},
         "probes": {"s2t2": {"labels": win(HOOP_WOODS, 2)}, "s2t3": {"labels": ["63", "66", "69", "72", "75", "78"]}}},
        {"values": {"shift": "charcoal round", "visitor": "a distiller", "e1": "pickle", "e2": "end"},
         "probes": {"s2t2": {"labels": win(HOOP_WOODS, 3)}, "s2t3": {"labels": ["64", "67", "70", "73", "76", "79"]}}},
        {"values": {"shift": "hoop stock", "visitor": "a vintner", "e1": "water", "e2": "top"},
         "probes": {"s2t2": {"labels": win(HOOP_WOODS, 4)}, "s2t3": {"labels": ["65", "68", "71", "74", "77", "80"]}}},
        {"values": {"shift": "close down", "visitor": "a carter", "e1": "oil", "e2": "low"},
         "probes": {"s2t2": {"labels": win(HOOP_WOODS, 5)}, "s2t3": {"labels": ["66", "69", "72", "75", "78", "81"]}}},
        {"values": {"shift": "watch night", "visitor": "a cellar man", "e1": "beer", "e2": "outer"},
         "probes": {"s2t2": {"labels": win(HOOP_WOODS, 6)}, "s2t3": {"labels": ["67", "70", "73", "76", "79", "82"]}}},
    ],
)

gc_scenarios = [gc_9501, gc_9502, gc_9503]


# ============================================================================
# design-time mechanical assertions (difficulty-fold derivability)
# ============================================================================

def _phrase_hits(item: str, phrases: tuple[str, ...]) -> set[str]:
    return {p for p in phrases if p in item}


def assert_cr_derivability() -> None:
    """Every cr item (bk AND pq) contains the head phrase of EXACTLY ONE
    card line — the decisive mapping — and pq uses the OTHER phrase of the
    line than bk (the v3o within-line generalization fold; v3n repeated
    the same phrase)."""
    for sc in cr_scenarios:
        expected = next(iter(next(iter(sc["variants"].values()))
                             ["probes"].values()))["expected"]
        for sd, var in sc["variants"].items():
            pq, bk = var["values"]["pq"], var["values"]["bk"]
            for item, kind in ((bk, "bk"), (pq, "pq")):
                hits = {line for line, phr in CR_LINE_PHRASES.items()
                        if _phrase_hits(item, phr)}
                assert hits == {expected}, (sc["id"], sd, kind, item, hits)
            bk_ph = _phrase_hits(bk, CR_LINE_PHRASES[expected])
            pq_ph = _phrase_hits(pq, CR_LINE_PHRASES[expected])
            assert bk_ph and pq_ph and bk_ph != pq_ph, (
                sc["id"], sd, "pq must use the line's OTHER phrase", bk, pq)


def assert_rt_full_card() -> None:
    """The defect-5 fix by construction: every tag of the rt vocabulary is
    stated in the FULL card rendered in s1 of EVERY rt cluster, and every
    task/pq item carries the head phrase of exactly its expected line."""
    for sc in rt_scenarios:
        expected = next(iter(next(iter(sc["variants"].values()))
                             ["probes"].values()))["expected"]
        card_text = sc["sessions"][0]["turns"][1]["text"]
        for tag in PARCEL:
            assert tag in card_text, (sc["id"], "card missing", tag)
        for sd, var in sc["variants"].items():
            for field in ("task", "pq"):
                item = var["values"][field]
                hits = {line for line, phr in RT_LINE_PHRASES.items()
                        if _phrase_hits(item, phr)}
                assert hits == {expected}, (sc["id"], sd, field, item, hits)


def assert_no_primary_label_leak_in_probe_session() -> None:
    """Session-scoped anti-leakage (mirror of validator V6) as a builder
    self-check: no probe-session turn text (options stripped) may contain
    an answer label word of its own scenario."""
    for sc in [*cr_scenarios, *cu_scenarios, *rt_scenarios, *dx_scenarios, *dr_scenarios]:
        probe_sessions = {sess["index"] for sess in sc["sessions"]
                          if any(t.get("probe") for t in sess["turns"])}
        labels = set()
        for var in sc["variants"].values():
            for spec in var["probes"].values():
                labels |= {str(x).lower() for x in spec["labels"]}
        for sess in sc["sessions"]:
            if sess["index"] not in probe_sessions:
                continue
            for t in sess["turns"]:
                text = t["text"].split("Options:")[0].lower()
                for lab in labels:
                    assert f" {lab} " not in f" {text} ", (
                        sc["id"], sess["index"], "probe-session leak", lab)


# ============================================================================
# emit
# ============================================================================

MANIFEST = {
    "protocol": "continuity-workload",
    "version": 3,
    "families": ["correction_reuse", "contradiction_update", "repeated_task",
                 "distractor_recall", "delayed_recall", "guess_calibration"],
    "primary_families": ["correction_reuse", "contradiction_update", "repeated_task",
                         "distractor_recall", "delayed_recall"],
    "primary_cluster_count": 15,
    "validation_cluster_ids": VALIDATION_IDS,
    "variant_seeds": SEEDS,
    "description": (
        "Suite v3o for CONT-006 STAGE 2 (owner-authorized 2026-10-10, "
        "SESSION-BRIEF-CONT006-STAGE2.md): the first end-to-end lesson-"
        "transfer surface with the rt LINEN_CARD defect fixed by construction "
        "(FULL rule card rendered in s1 of every rt cluster — no probe expects "
        "a category whose rule was never stated) and difficulty re-aimed so "
        "the STRONG model has headroom (cr: within-line phrase generalization "
        "— the probe uses the card line's OTHER head phrase — plus the "
        "inherited retraction sub-type; dx: two lures, both re-confirmed; "
        "cu: one chained superseded old->mid->new). Composition identical to "
        "v3n (15 TR primary + 4 VAL + GC x3; every taxonomy class >= 2 "
        "primary clusters), mechanics INHERITED from the frozen suites only "
        "(v3i/v3j seed_error mechanisms incl. cr-retraction + "
        "initial_expected; v3k lure_value + label windows), fresh worlds "
        "(slate quarry tally hut; tar kettle shed/net loft mend bench/pump "
        "house gauge row/maltings floor room/salt store bin row; railway "
        "parcel office; mine lamp station/sawmill filing room/gasworks "
        "meter house; apothecary still room/coaling jetty hopper deck; tea "
        "warehouse loft/tram depot pit/cooper's yard shed), ids x-9xxx, "
        "seeds {9001..9007}, disjoint from ALL prior suites incl. v3n "
        "(validator V3 every seed both ways + V18 world-freshness). GC "
        "option pools disjoint from the validator-V2 C2 collision words. "
        "Model-level difficulty bands are verified by the pre-registered "
        "in-run baseline gate (stage-2 prereg), not by a separate "
        "calibration phase. Rendering: continuity.fixtures.render_seed_variant."
    ),
}


def main() -> int:
    assert_cr_derivability()
    assert_rt_full_card()
    assert_no_primary_label_leak_in_probe_session()
    all_scenarios = [
        *cr_scenarios, *cu_scenarios, *rt_scenarios,
        *dx_scenarios, *dr_scenarios, *gc_scenarios,
    ]
    assert len(all_scenarios) == 22, len(all_scenarios)
    tr = [s["id"] for s in all_scenarios
          if s["id"] not in VALIDATION_IDS and s["family"] != "guess_calibration"]
    assert len(tr) == 15, tr
    if OUT_DIR.exists():
        for path in sorted(OUT_DIR.rglob("*.json")):
            path.unlink()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(MANIFEST, indent=1, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    for scenario in all_scenarios:
        write_scenario(f"{scenario['family']}/{scenario['id']}.json", scenario)
    turns = sum(len(sess["turns"]) for s in all_scenarios for sess in s["sessions"])
    print(f"emitted {len(all_scenarios)} scenarios + manifest into {OUT_DIR}")
    print(f"turns per seed: {turns}")
    print(f"TR primary: {sorted(tr)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
