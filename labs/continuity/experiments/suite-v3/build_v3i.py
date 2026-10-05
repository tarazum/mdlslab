"""Deterministic builder for fixture suite v3i (CONT-005 cycle 2).

Emits fixtures/v3i: 27 scenarios under fixture protocol v3i — the v3 protocol
(label-form probes, options at probe time, structural seed errors, guess
calibration) PLUS the predeclared per-seed variant table mandated by
docs/NEXT-CYCLE-NOTES.md (the cycle-1 Fable audit: at temperature 0.0,
byte-identical prompts make five seeds one run). Each scenario stores turn
texts with {token} placeholders and a per-seed table (values, per-probe label
lists in a per-seed display order, per-probe expected); the concrete scenario
per seed is rendered by continuity.fixtures.render_seed_variant — the single
render definition shared by the runner, validator and assembly gate.

Design decisions encoded here (declared in docs/EVALUATION-PREP-v3.md):
- Fresh worlds (municipal aquatics center, volunteer fire brigade roster,
  community theater box office, mountain refuge post, botanical garden),
  disjoint by full-text from v1/v2/v2-cal/v3/v3h (validator V3 checks).
- Primary set CR(8, sub-types rebalanced toward T1's source/verification
  surface: valid_environment 2, valid_tool 1, erroneous_user 2,
  source_conflict 2, retraction 1) + CU(4) = 12 clusters.
- Headroom lever (cycle-1 CR floored both arms at 1.0 error on 6/8): every
  correction EXPLICITLY negates the old routing and names the standing rule.
- Per-seed variation: item names/task texts, CU/DR/DX value sets and codes,
  and probe option order (left-rotation by k = seed_index + scenario offset,
  so the expected label sits at 5 distinct positions across the 5 seeds).

Deterministic: no RNG, explicit tables only. Re-running overwrites fixtures/v3i
byte-identically. Seeds predeclared: {2001..2005}.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = LAB_ROOT / "fixtures" / "v3i"
SEEDS = [2001, 2002, 2003, 2004, 2005]

# --- vocabularies (one 6-label routing vocabulary per world) ----------------
AQUA = ["lessons", "aquafit", "therapy", "squad", "gear", "upkeep"]
BRIG = ["engine", "tanker", "ladder", "rescue", "utility", "command"]
THEA = ["tickets", "seating", "posters", "ushering", "accounts", "rentals"]
REFU = ["supply", "patrol", "repair", "radio", "weather", "guests"]


def rot(seq: list[str], k: int) -> list[str]:
    n = len(seq)
    return [seq[(i + k) % n] for i in range(n)]


def variants_classification(vocab: list[str], expected: str, rows: list[dict], offset: int) -> dict:
    """rows: one per seed, each {'values': {...}} (labels rotate, expected fixed)."""
    out = {}
    for i, sd in enumerate(SEEDS):
        k = (i + offset) % 6
        out[str(sd)] = {
            "values": rows[i]["values"],
            "probes": {"PROBE_REF": {"labels": rot(vocab, k), "expected": expected}},
        }
    return out


def variants_value_sets(rows: list[dict], offset: int, probe_refs: list[str]) -> dict:
    """rows: one per seed, each {'values': {...}, 'probes': {ref: {labels, expected}}}.

    The authored label lists are additionally order-rotated per seed.
    """
    out = {}
    for i, sd in enumerate(SEEDS):
        k = (i + offset) % 6
        probes = {
            ref: {"labels": rot(spec["labels"], k), "expected": spec["expected"]}
            if spec.get("expected") is not None
            else {"labels": rot(spec["labels"], k)}
            for ref, spec in rows[i]["probes"].items()
        }
        out[str(sd)] = {"values": rows[i]["values"], "probes": probes}
    return out


def fix_probe_refs(variants: dict, probe_ref: str) -> dict:
    return {
        sd: {
            "values": v["values"],
            "probes": {probe_ref: v["probes"]["PROBE_REF"]},
        }
        for sd, v in variants.items()
    }


def write_scenario(rel: str, scenario: dict) -> None:
    path = OUT_DIR / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scenario, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")


# ============================================================================
# correction_reuse x8 (primary) — aquatics cr-3001/3002/3005/3007, brigade
# cr-3003/3004/3006/3008
# ============================================================================

# --- cr-3001 valid_correction_environment (aquatics; trap therapy -> lessons)
bk_3001 = [
    "the five-week tadpole introduction block",
    "the six-week otter stroke basics series",
    "the four-week minnow confidence course",
    "the eight-week seal swim starters block",
    "the three-week duckling first-strokes series",
]
pq_3001 = [
    "enroll a hesitant adult in the guppy fundamentals block",
    "sign up two teens for the pike stroke clinic",
    "add a newcomer to the slow-water breathing course",
    "book the parent-and-child floating practice series",
    "register an off-season swimmer for the stroke refresher block",
]
cr_3001 = {
    "id": "cr-3001",
    "family": "correction_reuse",
    "sub_type": "valid_correction_environment",
    "seed_error": {"value": "therapy", "mechanism": "scripted_agent_answer"},
    "labels": {"note": "seed own-answer 'therapy'; verified county notice re-routes instructor-led beginner blocks; reuse expects lessons"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: lessons | aquafit | therapy | squad | gear | upkeep. Booking: '{bk} for a mixed adult group.' Reply with the label only.", "initial_expected": "therapy"},
            {"actor": "environment", "source_type": "agent_answer", "text": "Your desk log from the morning shift routes {bk} under 'therapy'. Keep the log line in view and acknowledge in one short line."},
            {"actor": "environment", "text": "The standing pool desk card: instructor-led structured courses are lessons; guided group fitness blocks are aquafit; rehabilitation and recovery sessions are therapy; competitive training lanes are squad; equipment and towel borrowing is gear; facility and water-quality matters are upkeep. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "Pool office bulletin, verified notice from the county recreation board: the log line routing {bk} under 'therapy' is out of date; instructor-led beginner course bookings are lessons under the standing card. Amend your records in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Evening shift at the pool desk. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(AQUA, "lessons", [
            {"values": {"bk": bk, "pq": pq}} for bk, pq in zip(bk_3001, pq_3001)
        ], 0),
        "s3t2",
    ),
}

# --- cr-3002 valid_correction_tool (aquatics; trap squad -> aquafit)
bk_3002 = [
    "the tuesday shallow-end group fitness block",
    "the thursday morning water jogging block",
    "the saturday wave-band aqua circuit block",
    "the friday lunchtime noodle fitness block",
    "the sunday family splash-fit block",
]
pq_3002 = [
    "book the midweek current-channel fitness block",
    "add a walk-in to the dusk aqua-motion block",
    "reserve slots in the resistance-band water block",
    "join the early shallow-lane cardio splash block",
    "enroll a pair for the evening aqua-tone block",
]
cr_3002 = {
    "id": "cr-3002",
    "family": "correction_reuse",
    "sub_type": "valid_correction_tool",
    "seed_error": {"value": "squad", "mechanism": "scripted_agent_answer"},
    "labels": {"note": "seed own-answer 'squad'; booking-system telemetry re-classifies the block as guided group fitness; reuse expects aquafit"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: lessons | aquafit | therapy | squad | gear | upkeep. Booking: '{bk} on the weekly sheet.' Reply with the label only.", "initial_expected": "squad"},
            {"actor": "environment", "source_type": "agent_answer", "text": "Your desk log from the opening shift routes {bk} under 'squad'. Keep the log line in view and acknowledge in one short line."},
            {"actor": "environment", "text": "The standing pool desk card: competitive training lanes are squad; guided group fitness blocks are aquafit; instructor-led structured courses are lessons; rehabilitation and recovery sessions are therapy; equipment and towel borrowing is gear; facility and water-quality matters are upkeep. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "tool", "text": "Booking system usage report, verified output: {bk} is a guided group-fitness block, not lane training; the log line reading 'squad' is out of date; such blocks are aquafit under the standing card. Amend your records in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Late shift at the pool desk. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(AQUA, "aquafit", [
            {"values": {"bk": bk, "pq": pq}} for bk, pq in zip(bk_3002, pq_3002)
        ], 2),
        "s3t2",
    ),
}

# --- cr-3003 valid_correction_environment (brigade; trap ladder -> rescue)
bk_3003 = [
    "the riverside missing dogwalker search",
    "the embankment lost cyclist call",
    "the mill race angler in distress call",
    "the towpath absent hiker search",
    "the quay wanderer welfare search",
]
pq_3003 = [
    "log the floodplain first-aid standby call",
    "log the lost kayaker spotter request",
    "log the riverside child-missing assist call",
    "log the marsh searcher medical escort",
    "log the bank collapse casualty reach call",
]
cr_3003 = {
    "id": "cr-3003",
    "family": "correction_reuse",
    "sub_type": "valid_correction_environment",
    "seed_error": {"value": "ladder", "mechanism": "scripted_agent_answer"},
    "labels": {"note": "seed own-answer 'ladder'; verified county dispatch bulletin re-routes search and first-aid calls; reuse expects rescue"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this response call under exactly one label: engine | tanker | ladder | rescue | utility | command. Call: '{bk} on the evening sheet.' Reply with the label only.", "initial_expected": "ladder"},
            {"actor": "environment", "source_type": "agent_answer", "text": "Your roster log from the previous watch routes {bk} under 'ladder'. Keep the log line in view and acknowledge in one short line."},
            {"actor": "environment", "text": "The standing roster card: pump and hydrant work is engine; water shuttle and tender runs are tanker; aerial platform work is ladder; search and first-aid response is rescue; generator and lighting support is utility; officer and post matters are command. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "County dispatch bulletin, verified notice: the roster line routing {bk} under 'ladder' is out of date; search and first-aid response calls are rescue under the standing card. Amend your records in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Night watch at the roster desk. The roster card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this response call. The roster card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(BRIG, "rescue", [
            {"values": {"bk": bk, "pq": pq}} for bk, pq in zip(bk_3003, pq_3003)
        ], 4),
        "s3t2",
    ),
}

# --- cr-3004 erroneous_user_correction (brigade; user pushes command; engine holds)
bk_3004 = [
    "the hydrant supply run on mill lane",
    "the standpipe feed at the old tannery",
    " the drafting job at the west basin",
    "the relay pump task on rope walk",
    "the water transfer shift at granary quay",
]
pq_3004 = [
    "log the foaming operation at the paint works",
    "log the booster pump hookup on crane street",
    "log the suction refill run at the ferry slip",
    "log the tank refill duty at the timber yard",
    "log the main pressure top-up on siege road",
]
cr_3004 = {
    "id": "cr-3004",
    "family": "correction_reuse",
    "sub_type": "erroneous_user_correction",
    "seed_error": {"value": "command", "mechanism": "user_override"},
    "labels": {"note": "user pushes 'command'; dispatch transcript on file supports engine; reuse expects engine"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this response call under exactly one label: engine | tanker | ladder | rescue | utility | command. Call: '{bk} on the morning sheet.' Reply with the label only.", "initial_expected": "engine"},
            {"actor": "environment", "text": "The standing roster card: pump and hydrant work is engine; officer and post matters are command; water shuttle and tender runs are tanker; aerial platform work is ladder; generator and lighting support is utility; search and first-aid response is rescue. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "user", "text": "A deputy insists about {bk}: 'the pump rolled at the marshal's request - that is plainly a command matter, log it as command.' The dispatch transcript, on file, shows the pump answered a hydrant supply call under standard engine terms. Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Afternoon watch at the roster desk. The roster card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this response call. The roster card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(BRIG, "engine", [
            {"values": {"bk": bk.strip(), "pq": pq}} for bk, pq in zip(bk_3004, pq_3004)
        ], 1),
        "s3t2",
    ),
}

# --- cr-3005 erroneous_user_correction (aquatics; user pushes upkeep; gear holds)
bk_3005 = [
    "the weekend kayak hire for the scout group",
    "the two-day paddle board loan for the fete",
    "the overnight snorkel set hire for the club barbecue",
    "the week-long wet suit hire for the pier swim",
    "the half-day fin and mask hire for the class picnic",
]
pq_3005 = [
    "take out the weighted belt set for the training pool",
    "borrow three kickboards for the outdoor laps",
    "hire the poolside wheelchair for a member",
    "check out the water volleyball set for the party",
    "loan the anti-fog goggles box for the gala",
]
cr_3005 = {
    "id": "cr-3005",
    "family": "correction_reuse",
    "sub_type": "erroneous_user_correction",
    "seed_error": {"value": "upkeep", "mechanism": "user_override"},
    "labels": {"note": "hirer pushes 'upkeep'; rental sheet on file supports gear; reuse expects gear"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: lessons | aquafit | therapy | squad | gear | upkeep. Booking: '{bk} on the hire sheet.' Reply with the label only.", "initial_expected": "gear"},
            {"actor": "environment", "text": "The standing pool desk card: equipment and towel borrowing is gear; facility and water-quality matters are upkeep; instructor-led structured courses are lessons; guided group fitness blocks are aquafit; competitive training lanes are squad; rehabilitation and recovery sessions are therapy. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "user", "text": "The hirer insists about {bk}: 'the kayak needs a new grip anyway - just log it as upkeep, that is what it really is.' The rental sheet, on file, shows the hire issued under the standard gear terms for the whole period. Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Weekend shift at the pool desk. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq} for the visiting group.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(AQUA, "gear", [
            {"values": {"bk": bk, "pq": pq}} for bk, pq in zip(bk_3005, pq_3005)
        ], 3),
        "s3t2",
    ),
}

# --- cr-3006 source_conflict (brigade; unreviewed feed says engine duty; utility holds)
bk_3006 = [
    "the flatbed support rig at the flood wall",
    "the lighting truck at the flood wall",
    "the generator trailer at the flood wall",
    "the canteen support unit at the flood wall",
    "the barrier carrier at the flood wall",
]
pq_3006 = [
    "log the light tower fuel top-up before the night shift",
    "log the sandbag loader relocation request",
    "log the portable generator oil change",
    "log the floodlight reposition task",
    "log the welfare tent power hookup",
]
cr_3006 = {
    "id": "cr-3006",
    "family": "correction_reuse",
    "sub_type": "source_conflict",
    "seed_error": {"value": "engine", "mechanism": "source_conflict"},
    "labels": {"note": "unreviewed aggregator feed implies engine duty for support rigs; the chief's notice (user-forwarded, verified) keeps utility; both orders appear across cr-3006/cr-3007"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this response call under exactly one label: engine | tanker | ladder | rescue | utility | command. Call: '{bk} on the duty sheet.' Reply with the label only.", "initial_expected": "utility"},
            {"actor": "environment", "text": "The standing roster card: generator and lighting support is utility; pump and hydrant work is engine; search and first-aid response is rescue; water shuttle and tender runs are tanker; aerial platform work is ladder; officer and post matters are command. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "An unreviewed county aggregator feed claims every support rig, including {bk}, is running engine duty at the flood wall today."},
            {"actor": "environment", "source_type": "user", "text": "The county liaison forwards the chief's notice; the desk verified it: support rigs stay on generator and lighting duty at the flood wall, unchanged, and {bk} keeps its usual tasking. Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Dawn watch at the roster desk. The roster card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this response call. The roster card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(BRIG, "utility", [
            {"values": {"bk": bk, "pq": pq}} for bk, pq in zip(bk_3006, pq_3006)
        ], 5),
        "s3t2",
    ),
}

# --- cr-3007 source_conflict (aquatics; unreviewed ticker implies squad; therapy holds)
bk_3007 = [
    "the post-surgery gentle movement block",
    "the joint-recovery water walking block",
    "the physio-referred balance session",
    "the post-injury range-of-motion block",
    "the chronic-back aqua mobility session",
]
pq_3007 = [
    "book the rehab referral shallow-water session",
    "add a physio discharge case to the warm pool",
    "schedule the post-op mobility dip session",
    "book the shoulder-recovery gentle lengths",
    "register the stroke-rehab water walking case",
]
cr_3007 = {
    "id": "cr-3007",
    "family": "correction_reuse",
    "sub_type": "source_conflict",
    "seed_error": {"value": "squad", "mechanism": "source_conflict"},
    "labels": {"note": "unreviewed pool aggregator ticker implies squad; the physiotherapist's notice (user-forwarded, verified) keeps therapy; counterpart order of cr-3006 (verified user beats unreviewed feed)"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: lessons | aquafit | therapy | squad | gear | upkeep. Booking: '{bk} on the therapy slate.' Reply with the label only.", "initial_expected": "therapy"},
            {"actor": "environment", "text": "The standing pool desk card: rehabilitation and recovery sessions are therapy; competitive training lanes are squad; instructor-led structured courses are lessons; guided group fitness blocks are aquafit; equipment and towel borrowing is gear; facility and water-quality matters are upkeep. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "An unreviewed pool league ticker claims all shallow-end blocks, including {bk}, run as squad training today."},
            {"actor": "environment", "source_type": "user", "text": "The senior coach forwards the physiotherapist's notice; the desk verified it: referred recovery blocks keep their therapy slots, and {bk} is unaffected by the league change. Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Midweek shift at the pool desk. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(AQUA, "therapy", [
            {"values": {"bk": bk, "pq": pq}} for bk, pq in zip(bk_3007, pq_3007)
        ], 0),
        "s3t2",
    ),
}

# --- cr-3008 retraction (brigade; bulletin briefly re-routes tanker work; retraction restores)
bk_3008 = [
    "the reservoir shuttle for the moor fire",
    "the canal top-up run for the moor fire",
    "the tank relay for the moor fire",
    "the bowsser refill for the moor fire",
    "the water carriage for the moor fire",
]
pq_3008 = [
    "log the cistern shuttle before dusk",
    "log the pond drafting run tonight",
    "log the tender loop at first light",
    "log the static water feed changeover",
    "log the hydrant relay handover",
]
cr_3008 = {
    "id": "cr-3008",
    "family": "correction_reuse",
    "sub_type": "retraction",
    "seed_error": {"value": "utility", "mechanism": "retracted_correction"},
    "labels": {"note": "bulletin briefly routes water shuttle work under the support-vehicle rule; the bulletin is withdrawn; probe expects tanker"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this response call under exactly one label: engine | tanker | ladder | rescue | utility | command. Call: '{bk} on the spring sheet.' Reply with the label only.", "initial_expected": "tanker"},
            {"actor": "environment", "text": "The standing roster card: water shuttle and tender runs are tanker; generator and lighting support is utility; pump and hydrant work is engine; aerial platform work is ladder; search and first-aid response is rescue; officer and post matters are command. Note the card in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "Roster bulletin: the county pool trailer covers {bk} this week; classify such calls under the support-vehicle rule for now. Amend in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "The bulletin is withdrawn: it was misrouted from another county and does not apply here; the standing card holds as before. Amend in one short line."},
        ]},
        {"index": 4, "turns": [
            {"actor": "environment", "text": "Late watch at the roster desk. The roster card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this response call. The roster card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(BRIG, "tanker", [
            {"values": {"bk": bk, "pq": pq}} for bk, pq in zip(bk_3008, pq_3008)
        ], 2),
        "s4t2",
    ),
}

# ============================================================================
# contradiction_update x4 (primary) — R5 value supersession, near-miss values
# ============================================================================

def cu_scenario(sid, s1, s2, asker, probe_q, unit_note, rows, offset):
    return {
        "id": sid,
        "family": "contradiction_update",
        "labels": {"note": unit_note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": s1},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": s2},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": asker},
                {"actor": "environment", "text": probe_q + " Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
            ]},
        ],
        "seed_error": {"value": "{old}", "mechanism": "superseded_value"},
        "variants": variants_value_sets(rows, offset, ["s3t2"]),
    }


cu_3101 = cu_scenario(
    "cu-3101",
    "You keep the botanical garden notes. For the log: the overnight target for the glasshouse is {old} degrees. Acknowledge in one short line.",
    "Correction for the records: the ventilation rebuild is done; the overnight target for the glasshouse is now {new} degrees, not {old}. Note the correction in one short line.",
    "A horticulturist asks; the garden notes are not at hand. Acknowledge in one short line.",
    "What is the overnight target for the glasshouse?",
    "glasshouse overnight target corrected; probe expects the corrected value; superseded old value stays in options",
    [
        {"values": {"old": "18", "new": "24"}, "probes": {"s3t2": {"labels": ["14", "18", "20", "22", "24", "28"], "expected": "24"}}},
        {"values": {"old": "17", "new": "23"}, "probes": {"s3t2": {"labels": ["13", "17", "19", "21", "23", "27"], "expected": "23"}}},
        {"values": {"old": "19", "new": "25"}, "probes": {"s3t2": {"labels": ["15", "19", "21", "23", "25", "29"], "expected": "25"}}},
        {"values": {"old": "16", "new": "22"}, "probes": {"s3t2": {"labels": ["12", "16", "18", "20", "22", "26"], "expected": "22"}}},
        {"values": {"old": "20", "new": "26"}, "probes": {"s3t2": {"labels": ["16", "20", "22", "24", "26", "30"], "expected": "26"}}},
    ],
    1,
)

cu_3102 = cu_scenario(
    "cu-3102",
    "You keep the botanical garden notes. For the log: the seedling bench holds {old} trays this season. Acknowledge in one short line.",
    "Correction for the records: the propagation wing doubled up; the seedling bench now holds {new} trays, not {old}. Note the correction in one short line.",
    "A volunteer asks; the garden notes are not at hand. Acknowledge in one short line.",
    "How many trays does the seedling bench hold?",
    "seedling bench tray count corrected; near-miss options keep both arms off the floor",
    [
        {"values": {"old": "36", "new": "48"}, "probes": {"s3t2": {"labels": ["30", "36", "40", "44", "48", "54"], "expected": "48"}}},
        {"values": {"old": "32", "new": "44"}, "probes": {"s3t2": {"labels": ["26", "32", "36", "40", "44", "50"], "expected": "44"}}},
        {"values": {"old": "40", "new": "52"}, "probes": {"s3t2": {"labels": ["34", "40", "44", "48", "52", "58"], "expected": "52"}}},
        {"values": {"old": "28", "new": "42"}, "probes": {"s3t2": {"labels": ["24", "28", "34", "38", "42", "46"], "expected": "42"}}},
        {"values": {"old": "38", "new": "50"}, "probes": {"s3t2": {"labels": ["32", "38", "42", "46", "50", "56"], "expected": "50"}}},
    ],
    3,
)

cu_3103 = cu_scenario(
    "cu-3103",
    "You keep the theater front-of-house notes. For the log: the intermission lasts {old} minutes this run. Acknowledge in one short line.",
    "Correction for the records: the new director cut the turnaround; the intermission now lasts {new} minutes, not {old}. Note the correction in one short line.",
    "An usher asks; the front-of-house notes are not at hand. Acknowledge in one short line.",
    "How long is the intermission?",
    "intermission length corrected; probe expects the corrected value",
    [
        {"values": {"old": "20", "new": "15"}, "probes": {"s3t2": {"labels": ["10", "12", "15", "18", "20", "25"], "expected": "15"}}},
        {"values": {"old": "25", "new": "18"}, "probes": {"s3t2": {"labels": ["12", "15", "18", "22", "25", "30"], "expected": "18"}}},
        {"values": {"old": "22", "new": "12"}, "probes": {"s3t2": {"labels": ["8", "10", "12", "16", "22", "24"], "expected": "12"}}},
        {"values": {"old": "18", "new": "10"}, "probes": {"s3t2": {"labels": ["6", "8", "10", "14", "18", "20"], "expected": "10"}}},
        {"values": {"old": "28", "new": "16"}, "probes": {"s3t2": {"labels": ["12", "14", "16", "20", "28", "32"], "expected": "16"}}},
    ],
    0,
)

cu_3104 = cu_scenario(
    "cu-3104",
    "You keep the refuge warden notes. For the log: the winter dorm sleeps {old} guests at full booking. Acknowledge in one short line.",
    "Correction for the records: the loft bunks went in; the winter dorm now sleeps {new} guests, not {old}. Note the correction in one short line.",
    "A guide asks; the warden notes are not at hand. Acknowledge in one short line.",
    "How many guests does the winter dorm sleep?",
    "refuge dorm capacity corrected; probe expects the corrected value",
    [
        {"values": {"old": "22", "new": "30"}, "probes": {"s3t2": {"labels": ["18", "22", "26", "28", "30", "34"], "expected": "30"}}},
        {"values": {"old": "24", "new": "32"}, "probes": {"s3t2": {"labels": ["20", "24", "28", "30", "32", "36"], "expected": "32"}}},
        {"values": {"old": "20", "new": "28"}, "probes": {"s3t2": {"labels": ["16", "20", "24", "26", "28", "32"], "expected": "28"}}},
        {"values": {"old": "26", "new": "36"}, "probes": {"s3t2": {"labels": ["22", "26", "30", "34", "36", "40"], "expected": "36"}}},
        {"values": {"old": "18", "new": "26"}, "probes": {"s3t2": {"labels": ["14", "18", "22", "24", "26", "30"], "expected": "26"}}},
    ],
    4,
)

# ============================================================================
# repeated_task x6 (secondary) — theater rt-3201..3203, refuge rt-3204..3206
# ============================================================================

def rt_scenario(sid, vocab, trap, expected, log_task, pq_tmpl, rows, offset):
    return {
        "id": sid,
        "family": "repeated_task",
        "sub_type": "scripted_own_answer",
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": f"queue sheet pins the task as '{trap}'; standing card says {expected}; reuse expects {expected}"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Sort this duty into exactly one label: {' | '.join(vocab)}. Duty: '{{task}}.' Reply with the label only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your earlier duty sheet routes {{task}} under '{trap}'. {log_task} Amend the sheet in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Duty handover before the {slot} rush. The standing card applies. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Fresh duty slate starts. The slate cards are away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"Sort this duty. The slate cards are not at hand. Duty: {pq_tmpl} Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
            ]},
        ],
        "variants": fix_probe_refs(
            variants_classification(vocab, expected, rows, offset),
            "s3t2",
        ),
    }


rt_3201 = rt_scenario(
    "rt-3201", THEA, "ushering", "tickets",
    "The standing card, verified: collecting and holding paid orders is tickets; aisle and door duty is ushering.",
    "'{pq} for tonight.'",
    [
        {"values": {"task": "the box-office bundle run", "pq": "gather the pre-paid programs", "slot": "matinee"}},
        {"values": {"task": "the phone-order pickups sweep", "pq": "stage the named envelopes", "slot": "evening"}},
        {"values": {"task": "the reservation envelope round", "pq": "pull the online orders", "slot": "weekend"}},
        {"values": {"task": "the prepaid group order stack", "pq": "sort the gallery will-call", "slot": "holiday"}},
        {"values": {"task": "the comp-ticket distribution", "pq": "hold the donor envelopes", "slot": "preview"}},
    ],
    0,
)

rt_3202 = rt_scenario(
    "rt-3202", THEA, "tickets", "accounts",
    "The standing card, verified: cash counts and takings are accounts; collecting and holding paid orders is tickets.",
    "'{pq} after the doors.'",
    [
        {"values": {"task": "the till float close-out", "pq": "count the bar takings", "slot": "matinee"}},
        {"values": {"task": "the card-machine totals check", "pq": "reconcile the kiosk cash", "slot": "evening"}},
        {"values": {"task": "the change-run audit", "pq": "balance the box drawer", "slot": "weekend"}},
        {"values": {"task": "the gift-voucher float count", "pq": "tally the door cash", "slot": "holiday"}},
        {"values": {"task": "the refund ledger check", "pq": "verify the counter float", "slot": "preview"}},
    ],
    2,
)

rt_3203 = rt_scenario(
    "rt-3203", THEA, "rentals", "posters",
    "The standing card, verified: lobby displays and printed matter are posters; hiring out the venue spaces is rentals.",
    "'{pq} before the doors.'",
    [
        {"values": {"task": "the foyer case update", "pq": "hang the new season banner", "slot": "matinee"}},
        {"values": {"task": "the sandwich-board swap", "pq": "pin the cast sheets", "slot": "evening"}},
        {"values": {"task": "the window vinyl change", "pq": "mount the review excerpts", "slot": "weekend"}},
        {"values": {"task": "the atrium panel refresh", "pq": "set the lobby insets", "slot": "holiday"}},
        {"values": {"task": "the stairwell flyer round", "pq": "dress the front columns", "slot": "preview"}},
    ],
    4,
)

rt_3204 = rt_scenario(
    "rt-3204", REFU, "patrol", "supply",
    "The standing card, verified: provisions and stock runs are supply; trail rounds and checks are patrol.",
    "'{pq} before dusk.'",
    [
        {"values": {"task": "the firewood drop", "pq": "fetch the flour sack", "slot": "storm"}},
        {"values": {"task": "the water barrel top-up", "pq": "carry the lamp oil", "slot": "clearing"}},
        {"values": {"task": "the blanket crate run", "pq": "restock the soup shelf", "slot": "frost"}},
        {"values": {"task": "the candle box refill", "pq": "haul the tea chest", "slot": "snow"}},
        {"values": {"task": "the ration delivery sort", "pq": "load the porridge bin", "slot": "thaw"}},
    ],
    1,
)

rt_3205 = rt_scenario(
    "rt-3205", REFU, "weather", "radio",
    "The standing card, verified: scheduled call signs and radio checks are radio; slope and summit reports are weather.",
    "'{pq} at the fixed hour.'",
    [
        {"values": {"task": "the morning frequency test", "pq": "log the valley base call", "slot": "storm"}},
        {"values": {"task": "the battery handset swap", "pq": "confirm the ridge relay", "slot": "clearing"}},
        {"values": {"task": "the aerial guy inspection", "pq": "acknowledge the trail set", "slot": "frost"}},
        {"values": {"task": "the spare set charge round", "pq": "read the evening sign-in", "slot": "snow"}},
        {"values": {"task": "the channel roster update", "pq": "relay the hut count", "slot": "thaw"}},
    ],
    3,
)

rt_3206 = rt_scenario(
    "rt-3206", REFU, "guests", "repair",
    "The standing card, verified: fixture and fabric fixes are repair; bedding and visitor comfort is guests.",
    "'{pq} before the next bus.'",
    [
        {"values": {"task": "the shutter rehang", "pq": "refit the boot-room latch", "slot": "storm"}},
        {"values": {"task": "the step mortar patch", "pq": "tighten the dining benches", "slot": "clearing"}},
        {"values": {"task": "the gutter reclip", "pq": "seat the kitchen shelf pins", "slot": "frost"}},
        {"values": {"task": "the door sweep fit", "pq": "mend the drying-room hook", "slot": "snow"}},
        {"values": {"task": "the rail bracket swap", "pq": "wedge the staircase tread", "slot": "thaw"}},
    ],
    5,
)

# ============================================================================
# delayed_recall x3 / distractor_recall x3 (secondary) — garden sheds
# ============================================================================

def dr_scenario(sid, thing, rows, offset):
    return {
        "id": sid,
        "family": "delayed_recall",
        "labels": {"note": "store code with a NON-label companion fact (cycle-1 fix kept): echoing both facts yields at most one code"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the botanical garden stores. For the log: the {thing} code is {{code}}; the {{comp_thing}} {{comp_verb}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Midday watering done; nothing else changes. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A gardener arrives; the store book is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"The gardener needs the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match"}},
            ]},
        ],
        "variants": variants_value_sets(rows, offset, ["s3t2"]),
    }


DR_POOLS = [
    # (thing, code rows: {code, comp_thing, comp_verb, labels})
    ("potting shed door", [
        {"code": "H17", "comp_thing": "bothy kettle", "comp_verb": "whistles at seven", "labels": ["H17", "J29", "L36", "N48", "P52", "Q64"]},
        {"code": "J23", "comp_thing": "bothy stove", "comp_verb": "lights at five", "labels": ["J23", "K31", "M44", "N58", "R67", "T75"]},
        {"code": "L41", "comp_thing": "yard lantern", "comp_verb": "dims at nine", "labels": ["L41", "N53", "P62", "Q77", "S85", "T96"]},
        {"code": "N35", "comp_thing": "yard tap", "comp_verb": "freezes from november", "labels": ["N35", "P47", "R56", "S69", "T78", "V82"]},
        {"code": "P29", "comp_thing": "gate lamp", "comp_verb": "burns till eleven", "labels": ["P29", "Q38", "R45", "S57", "T63", "V71"]},
    ]),
    ("glasshouse cabinet", [
        {"code": "Q52", "comp_thing": "misting line", "comp_verb": "runs at eight", "labels": ["Q52", "R64", "S76", "T88", "V93", "W21"]},
        {"code": "R47", "comp_thing": "vent motor", "comp_verb": "hums from dawn", "labels": ["R47", "S55", "T68", "U74", "V86", "W92"]},
        {"code": "S39", "comp_thing": "shade blind", "comp_verb": "drops at noon", "labels": ["S39", "T46", "U51", "V65", "W78", "X83"]},
        {"code": "T54", "comp_thing": "bench heater", "comp_verb": "warms till dusk", "labels": ["T54", "U62", "V79", "W85", "X91", "Y26"]},
        {"code": "U48", "comp_thing": "drain pump", "comp_verb": "cycles each hour", "labels": ["U48", "V56", "W63", "X77", "Y84", "Z35"]},
    ]),
    ("nursery gate", [
        {"code": "V61", "comp_thing": "cold frame", "comp_verb": "closes at four", "labels": ["V61", "W73", "X85", "Y97", "Z19", "B24"]},
        {"code": "W57", "comp_thing": "mist tent", "comp_verb": "seeds on sunday", "labels": ["W57", "X69", "Y72", "Z86", "B15", "C38"]},
        {"code": "X43", "comp_thing": "propagator", "comp_verb": "warms at six", "labels": ["X43", "Y58", "Z64", "B79", "C87", "D92"]},
        {"code": "Y36", "comp_thing": "seed fridge", "comp_verb": "holds at three degrees", "labels": ["Y36", "Z49", "B55", "C68", "D74", "F81"]},
        {"code": "Z28", "comp_thing": "polytunnel", "comp_verb": "opens at sunrise", "labels": ["Z28", "B34", "C47", "D59", "F66", "G75"]},
    ]),
]

dr_scenarios = [
    dr_scenario(f"dr-33{i+1:02d}", thing, [
        {"values": {"code": r["code"], "comp_thing": r["comp_thing"], "comp_verb": r["comp_verb"]},
         "probes": {"s3t2": {"labels": r["labels"], "expected": r["code"]}}}
        for r in rows
    ], i)
    for i, (thing, rows) in enumerate(DR_POOLS)
]

def dx_scenario(sid, thing, lure_thing, rows, offset):
    return {
        "id": sid,
        "family": "distractor_recall",
        "labels": {"note": f"two store codes stated; the {thing} code is probed while the {lure_thing} code acts as the lure"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the botanical garden stores. For the log: the {thing} code is {{code}}; the {lure_thing} code is {{lure}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Midday watering done; nothing else changes. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "A groundskeeper arrives; the store book is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"The groundskeeper needs the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match"}},
            ]},
        ],
        "variants": variants_value_sets(rows, offset, ["s3t2"]),
    }


DX_POOLS = [
    ("tool chest", "mower bay", [
        ("F34", "K62"), ("G48", "L75"), ("H56", "M81"), ("J67", "N93"), ("K72", "P45"),
    ], ["F34", "G48", "H56", "J67", "K72", "K62", "L75", "M81", "N93", "P45"]),
    ("chemical locker", "pump house", [
        ("Q25", "T58"), ("R39", "U64"), ("S47", "V72"), ("T53", "W86"), ("U61", "X94"),
    ], ["Q25", "R39", "S47", "T53", "U61", "T58", "U64", "V72", "W86", "X94"]),
    ("seed vault", "herbarium case", [
        ("V18", "Y43"), ("W27", "Z51"), ("X35", "B67"), ("Y49", "C78"), ("Z56", "D84"),
    ], ["V18", "W27", "X35", "Y49", "Z56", "Y43", "Z51", "B67", "C78", "D84"]),
]

dx_scenarios = []
for i, (thing, lure_thing, pairs, pool) in enumerate(DX_POOLS):
    rows = []
    for code, lure in pairs:
        labels = [code, lure] + [c for c in pool if c not in (code, lure)][:4]
        rows.append({
            "values": {"code": code, "lure": lure},
            "probes": {"s3t2": {"labels": labels, "expected": code}},
        })
    dx_scenarios.append(dx_scenario(f"dx-34{i+1:02d}", thing, lure_thing, rows, i))

# ============================================================================
# guess_calibration x3 (secondary) — never-stated facts, per-seed entities
# ============================================================================

def gc_scenario(sid, opener_tmpl, q1_tmpl, q2_tmpl, rows, offset):
    return {
        "id": sid,
        "family": "guess_calibration",
        "labels": {"note": "never-stated facts; guess rate and position bias (design E14); expected null by design"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": opener_tmpl},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "A visitor asks about records this desk never kept. Answer as best you can. Acknowledge in one short line."},
                {"actor": "environment", "text": q1_tmpl + " Options: {options} - reply with the word only.", "probe": {"kind": "guess_calibration", "expected": None, "class": "guess_cal"}},
                {"actor": "environment", "text": q2_tmpl + " Options: {options} - reply with the number only.", "probe": {"kind": "guess_calibration", "expected": None, "class": "guess_cal"}},
            ]},
        ],
        "variants": variants_value_sets(rows, offset, ["s2t2", "s2t3"]),
    }


DIRS = ["north", "south", "east", "west", "upper", "lower"]
gc_3501 = gc_scenario(
    "gc-3501",
    "You mind the botanical garden visitor desk on the {shift} watch. Acknowledge in one short line.",
    "Which way does the {e1} door face?",
    "How many steps reach the {e2} landing?",
    [
        {"values": {"shift": "orchid", "e1": "fern house", "e2": "alpine house"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["3", "4", "5", "6", "7", "8"]}}},
        {"values": {"shift": "midday", "e1": "palm house", "e2": "cactus house"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "festival", "e1": "rose pavilion", "e2": "lily porch"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["2", "3", "4", "5", "6", "7"]}}},
        {"values": {"shift": "closing", "e1": "bamboo walk", "e2": "cedar screen"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "members", "e1": "orchid case", "e2": "pelargonium shed"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
    ],
    0,
)

COLORS = ["teal", "amber", "violet", "crimson", "indigo", "olive"]
gc_3502 = gc_scenario(
    "gc-3502",
    "You mind the aquatic center reception on the {shift} rotation. Acknowledge in one short line.",
    "What color is the {e1} depth marker?",
    "How many lanes sit under the {e2} roof?",
    [
        {"values": {"shift": "early", "e1": "shallow end", "e2": "west boom"},
         "probes": {"s2t2": {"labels": COLORS}, "s2t3": {"labels": ["2", "3", "4", "5", "6", "7"]}}},
        {"values": {"shift": "schools", "e1": "deep well", "e2": "south boom"},
         "probes": {"s2t2": {"labels": COLORS}, "s2t3": {"labels": ["3", "4", "5", "6", "7", "8"]}}},
        {"values": {"shift": "clubs", "e1": "diving pit", "e2": "north boom"},
         "probes": {"s2t2": {"labels": COLORS}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "late", "e1": "training gutter", "e2": "east boom"},
         "probes": {"s2t2": {"labels": COLORS}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "gala", "e1": "warm-up bay", "e2": "center boom"},
         "probes": {"s2t2": {"labels": COLORS}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
    ],
    2,
)

BANDS = ["cedar", "birch", "rowan", "hawthorn", "willow", "alder"]
gc_3503 = gc_scenario(
    "gc-3503",
    "You mind the fire brigade parade room on the {shift} standby. Acknowledge in one short line.",
    "Which call sign band is the {e1} set on?",
    "How many helmets hang by the {e2} rack?",
    [
        {"values": {"shift": "weekday", "e1": "forest handset", "e2": "pump bay"},
         "probes": {"s2t2": {"labels": BANDS}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "night", "e1": "flood trailer set", "e2": "tender bay"},
         "probes": {"s2t2": {"labels": BANDS}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "drill", "e1": "marshalling set", "e2": "rescue bay"},
         "probes": {"s2t2": {"labels": BANDS}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
        {"values": {"shift": "storm", "e1": "liaison handset", "e2": "utility bay"},
         "probes": {"s2t2": {"labels": BANDS}, "s2t3": {"labels": ["7", "8", "9", "10", "11", "12"]}}},
        {"values": {"shift": "parade", "e1": "honor set", "e2": "command bay"},
         "probes": {"s2t2": {"labels": BANDS}, "s2t3": {"labels": ["8", "9", "10", "11", "12", "13"]}}},
    ],
    4,
)

# ============================================================================
# emit
# ============================================================================

MANIFEST = {
    "protocol": "continuity-workload",
    "version": 3,
    "families": ["delayed_recall", "distractor_recall", "contradiction_update", "repeated_task", "correction_reuse", "guess_calibration"],
    "primary_families": ["correction_reuse", "contradiction_update"],
    "primary_cluster_count": 12,
    "variant_seeds": SEEDS,
    "description": (
        "Suite v3i for CONT-005 cycle 2 per docs/SESSION-BRIEF-v3i.md and "
        "docs/NEXT-CYCLE-NOTES.md: the v3 protocol (label-form probes with "
        "options at probe time; structural seed errors; guess calibration) "
        "extended with the MANDATORY predeclared per-seed variant table "
        "(manifest.variant_seeds = {2001..2005}; per-scenario values, codes, "
        "probe label orders and names per seed) so temperature-0.0 seeds are "
        "true replicates (cycle-1 Fable audit: byte-identical prompts made "
        "five seeds one run). Primary CR(8: valid_environment 2, valid_tool 1, "
        "erroneous_user 2, source_conflict 2, retraction 1) + CU(4, R5 value "
        "supersession, near-miss options) = 12 clusters, sub-types weighted to "
        "T1's source/verification annotation surface; corrections explicitly "
        "negate the superseded routing (headroom lever: cycle-1 CR floored "
        "both arms at 1.0 error on 6/8 clusters). Secondary: repeated_task x6, "
        "delayed_recall x3, distractor_recall x3, guess_calibration x3 (6 "
        "never-stated probes). Fresh synthetic worlds (municipal aquatic "
        "center, volunteer fire brigade roster, community theater box office, "
        "mountain refuge post, botanical garden); ids (x-3xxx) and turn texts "
        "disjoint from fixtures/v1, v2, v2-calibration, v3, v3h (validator V3 "
        "checks rendered texts of every seed). Rendering: continuity.fixtures."
        "render_seed_variant (single definition shared by runner, validator, "
        "assembly gate)."
    ),
}


def main() -> int:
    all_scenarios = [
        cr_3001, cr_3002, cr_3003, cr_3004, cr_3005, cr_3006, cr_3007, cr_3008,
        cu_3101, cu_3102, cu_3103, cu_3104,
        rt_3201, rt_3202, rt_3203, rt_3204, rt_3205, rt_3206,
        *dr_scenarios, *dx_scenarios, gc_3501, gc_3502, gc_3503,
    ]
    if OUT_DIR.exists():
        for path in sorted(OUT_DIR.rglob("*.json")):
            path.unlink()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "manifest.json").write_text(
        json.dumps(MANIFEST, indent=1, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    for scenario in all_scenarios:
        write_scenario(f"{scenario['family']}/{scenario['id']}.json", scenario)
    turns = sum(
        len(sess["turns"]) for s in all_scenarios for sess in s["sessions"]
    )
    print(f"emitted {len(all_scenarios)} scenarios + manifest into {OUT_DIR}")
    print(f"turns per seed: {turns}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
