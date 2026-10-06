"""Deterministic builder for fixture suite v3j (CONT-005 cycle 2, FREEZE-B).

Emits fixtures/v3j: 27 scenarios under fixture protocol v3i (v3 protocol +
predeclared per-seed variant table), NEW predeclared seeds {3001..3005}, ids
x-4xxx, fresh worlds (municipal museum front desk, marina harbor office,
bakery depot, regional airport ground stores) — rendered turn texts disjoint
from v1/v2/v2-cal/v3/v3h/v3i (validator V3 covers every seed both ways).

Pilot-informed difficulty calibration (v3i pilot GO/NO-GO, c94cbac; declared
openly per EVALUATION-PREP-v3 section 2 stage 2 — fixture-authoring exposure
acknowledged, mitigation = fresh content + independent gate review incl. the
arm-neutrality check):
- CU rebalanced HARDER (clause-1 FAIL: v3i CU error 0.050 — near-miss options
  did not beat the recency heuristic). v3j CU defeats pure recency in 3 of 4
  clusters by making the correct answer NOT the most recent value statement:
    cu-4101 retracted_correction — a verified value correction is later
          withdrawn (misrouted); the ORIGINAL value governs; recency picks the
          retracted value (trap).
    cu-4102 user_override — an unverified user pushes a value correction; the
          verified original statement governs; recency picks the push (trap).
    cu-4103 user_override — a verified tool readout corrects the value, then a
          user pushes a DIFFERENT value; the verified correction governs;
          recency picks the push (trap).
    cu-4104 superseded_value — the v3i pattern kept as the family's
          mid-to-easy anchor (expected = corrected value; trap = old value).
  Family target: mean error strictly inside (0.15, 0.85) in both arms.
- CR sub-type composition kept IDENTICAL to v3i (valid_environment 2,
  valid_tool 1, erroneous_user 2, source_conflict 2, retraction 1 — no
  post-pilot sub-type cherry-picking). Difficulty re-aimed mid-scale via
  wording levers only: indirect counter-evidence (the on-file record states
  the fact without the label word where v3i named it), probe cases whose
  surface wording pulls toward the trap category while the corrected rule
  covers them, and the retraction cluster restates the standing rule with its
  label at withdrawal (v3i cr-3008 floored at 1.0 with a paraphrase-only
  bulletin).
- source_conflict keeps BOTH orders across the two clusters: cr-4006
  unreviewed-feed-then-verified-user (v3i order), cr-4007 verified-user-then-
  unreviewed-feed (reversed).
- NOTE: prose resolution flags (claims.py FREEZE-B fix) — no bracket markup
  anywhere in rendered memory blocks.

Deterministic: no RNG, explicit tables only. Re-running overwrites
fixtures/v3j byte-identically.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = LAB_ROOT / "fixtures" / "v3j"
SEEDS = [3001, 3002, 3003, 3004, 3005]

# --- vocabularies (one 6-label routing vocabulary per world) ----------------
MUSE = ["exhibits", "tours", "conservation", "security", "memberships", "facilities"]
MARI = ["berths", "moorings", "fuel", "repairs", "charters", "safety"]

MUSE_CARD = (
    "The standing museum desk card: docent-guided visits and walking programs are "
    "tours; patron schemes and season passes are memberships; artifact care and "
    "restoration handling is conservation; display and case installations are "
    "exhibits; access control and surveillance matters are security; building and "
    "room upkeep is facilities. Note the card in one short line."
)
MARI_CARD = (
    "The standing harbor office card: slip allocation and quay assignments are "
    "berths; anchor lines and buoy positioning is moorings; dockside refueling and "
    "tank transfers is fuel; hull and engine fixing work is repairs; hired boat "
    "trips and skippered outings are charters; life equipment and water rules are "
    "safety. Note the card in one short line."
)
MUSE_DAYS = ["monday", "wednesday", "friday", "saturday", "sunday"]
MARI_DAYS = ["tuesday", "thursday", "saturday", "sunday", "monday"]


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


def values_rows(keys_and_lists: dict[str, list[str]]) -> list[dict]:
    """Zip per-seed lists into variant rows: [{'values': {...}}, ...]."""
    n = len(SEEDS)
    return [
        {"values": {k: lists[i] for k, lists in keys_and_lists.items()}}
        for i in range(n)
    ]


# ============================================================================
# correction_reuse x8 (primary) — museum cr-4001/4002/4005/4007, marina
# cr-4003/4004/4006/4008
# ============================================================================

# --- cr-4001 valid_correction_environment (museum; trap memberships -> tours)
cr_4001 = {
    "id": "cr-4001",
    "family": "correction_reuse",
    "sub_type": "valid_correction_environment",
    "seed_error": {"value": "memberships", "mechanism": "scripted_agent_answer"},
    "labels": {"note": "seed own-answer 'memberships'; verified county bulletin re-routes docent-guided patron walks; reuse expects tours"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: exhibits | tours | conservation | security | memberships | facilities. Booking: '{bk} for the patron circle.' Reply with the label only.", "initial_expected": "memberships"},
            {"actor": "environment", "source_type": "agent_answer", "text": "Your desk log from the morning shift routes {bk} under 'memberships'. Keep the log line in view and acknowledge in one short line."},
            {"actor": "environment", "text": MUSE_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "Museum office bulletin, verified notice from the county heritage board: the log line routing {bk} under 'memberships' is out of date; docent-guided visits are tours under the standing card. Amend your records in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Evening shift at the museum desk on {day}. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MUSE, "tours", values_rows({
            "bk": [
                "the patrons' autumn gallery walk",
                "the season-pass holders' bronze-age tour",
                "the patron circle's silver vault walk",
                "the donors' monthly archive stroll",
                "the friends-of-the-museum chapel visit",
            ],
            "pq": [
                "register the fellowship group for the twilight cellar visit",
                "enroll the subscriber party in the dawn aviary walk",
                "add the guild members to the storeroom viewing round",
                "book the association's map-room stroll",
                "sign up the heritage league for the fresco walk",
            ],
            "day": MUSE_DAYS,
        }), 0),
        "s3t2",
    ),
}

# --- cr-4002 valid_correction_tool (museum; trap conservation -> exhibits)
cr_4002 = {
    "id": "cr-4002",
    "family": "correction_reuse",
    "sub_type": "valid_correction_tool",
    "seed_error": {"value": "conservation", "mechanism": "scripted_agent_answer"},
    "labels": {"note": "seed own-answer 'conservation'; case-sensor telemetry re-classifies climate-adjacent installs as display work; reuse expects exhibits"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: exhibits | tours | conservation | security | memberships | facilities. Booking: '{bk} on the install sheet.' Reply with the label only.", "initial_expected": "conservation"},
            {"actor": "environment", "source_type": "agent_answer", "text": "Your desk log from the opening shift routes {bk} under 'conservation'. Keep the log line in view and acknowledge in one short line."},
            {"actor": "environment", "text": MUSE_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "tool", "text": "Case-sensor report, verified output: {bk} is a display-and-case installation, not climate care; the log line reading 'conservation' is out of date; such installs are exhibits under the standing card. Amend your records in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Late shift at the museum desk on {day}. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MUSE, "exhibits", values_rows({
            "bk": [
                "the humidity case swap for the parchment vitrine",
                "the UV film change for the map case",
                "the silica tray refresh inside the coin cabinet",
                "the light-baffle refit for the textile case",
                "the gasket renewal for the butterfly drawer",
            ],
            "pq": [
                "log the riser mount for the fossil showcase",
                "book the bracket set for the armor display",
                "add the glass shelf for the medal case",
                "schedule the base plate for the sculpture plinth",
                "clear the travel frame for the loan crate",
            ],
            "day": MUSE_DAYS,
        }), 2),
        "s3t2",
    ),
}

# --- cr-4003 valid_correction_environment (marina; trap safety -> moorings)
cr_4003 = {
    "id": "cr-4003",
    "family": "correction_reuse",
    "sub_type": "valid_correction_environment",
    "seed_error": {"value": "safety", "mechanism": "scripted_agent_answer"},
    "labels": {"note": "seed own-answer 'safety'; verified port bulletin re-routes life-gear-adjacent buoy tasks; reuse expects moorings"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this call under exactly one label: berths | moorings | fuel | repairs | charters | safety. Call: '{bk} on the evening sheet.' Reply with the label only.", "initial_expected": "safety"},
            {"actor": "environment", "source_type": "agent_answer", "text": "Your duty log from the previous watch routes {bk} under 'safety'. Keep the log line in view and acknowledge in one short line."},
            {"actor": "environment", "text": MARI_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "Harbor office bulletin, verified notice from the port authority: the log line routing {bk} under 'safety' is out of date; buoy-line and anchorage gear tasks are moorings under the standing card. Amend your records in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Night watch at the harbor office on {day}. The office card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this call. The office card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MARI, "moorings", values_rows({
            "bk": [
                "the lifebuoy rehang at the east jetty",
                "the horseshoe ring check at the fuel quay",
                "the grab-line coil audit on the launch",
                "the flare box restrap in the tender",
                "the throw-line repack for the patrol skiff",
            ],
            "pq": [
                "log the marker buoy swap at the north trot",
                "check the pick-up buoy at the guest anchorage",
                "re-lead the ground line at the mid pontoon",
                "swap the mooring pennant on the visitors' trot",
                "inspect the trot weights at the south buoys",
            ],
            "day": MARI_DAYS,
        }), 4),
        "s3t2",
    ),
}

# --- cr-4004 erroneous_user_correction (marina; user pushes repairs; fuel holds)
cr_4004 = {
    "id": "cr-4004",
    "family": "correction_reuse",
    "sub_type": "erroneous_user_correction",
    "seed_error": {"value": "repairs", "mechanism": "user_override"},
    "labels": {"note": "skipper pushes 'repairs'; fuel ledger on file supports fuel; reuse expects fuel"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this call under exactly one label: berths | moorings | fuel | repairs | charters | safety. Call: '{bk} on the morning sheet.' Reply with the label only.", "initial_expected": "fuel"},
            {"actor": "environment", "text": MARI_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "user", "text": "The skipper insists about {bk}: 'the engine was coughing all the way in - that is repair work, log it under repairs.' The fuel ledger, on file, shows the run drew from the duty tank under standard fuel terms. Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Afternoon watch at the harbor office on {day}. The office card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this call. The office card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MARI, "fuel", values_rows({
            "bk": [
                "the patrol launch refuel at the duty pump",
                "the rescue boat tank top-up at the quay",
                "the tender jerry-can run for the moorings round",
                "the workboat bowser draw at the fuel barge",
                "the club boat uplift before the regatta",
            ],
            "pq": [
                "log the two-stroke top-up after the engine service",
                "record the duty-tank draw for the crane launch",
                "book the jerry-can refill for the crew rib",
                "note the bowser uplift after the gearbox swap",
                "enter the petrol run for the mail boat",
            ],
            "day": MARI_DAYS,
        }), 1),
        "s3t2",
    ),
}

# --- cr-4005 erroneous_user_correction (museum; user pushes memberships; tours holds; INDIRECT counter)
cr_4005 = {
    "id": "cr-4005",
    "family": "correction_reuse",
    "sub_type": "erroneous_user_correction",
    "seed_error": {"value": "memberships", "mechanism": "user_override"},
    "labels": {"note": "donor pushes 'memberships'; visits register on file shows a docent-led walking program (indirect - no label word); reuse expects tours"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: exhibits | tours | conservation | security | memberships | facilities. Booking: '{bk} on the visits sheet.' Reply with the label only.", "initial_expected": "tours"},
            {"actor": "environment", "text": MUSE_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "user", "text": "The donor insists about {bk}: 'these are our own patrons - put it through as memberships, that is what it really is.' The visits register, on file, shows the group was booked for a docent-led walking program under the standard visit terms. Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Weekend shift at the museum desk on {day}. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq} for the incoming group.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MUSE, "tours", values_rows({
            "bk": [
                "the founders' circle evening walk",
                "the patrons' pre-view stroll",
                "the benefactors' storage wing round",
                "the trustees' attic steps visit",
                "the sponsors' after-hours gallery round",
            ],
            "pq": [
                "add the heritage society to the copper-mine walk",
                "queue the fellows' group for the clock-tower stroll",
                "register the antiquarian club for the vault round",
                "book the academy party for the mosaic visit",
                "sign up the guild for the plaster-cast walk",
            ],
            "day": MUSE_DAYS,
        }), 3),
        "s3t2",
    ),
}

# --- cr-4006 source_conflict (marina; unreviewed feed implies charters; berths holds) — feed FIRST
cr_4006 = {
    "id": "cr-4006",
    "family": "correction_reuse",
    "sub_type": "source_conflict",
    "seed_error": {"value": "charters", "mechanism": "source_conflict"},
    "labels": {"note": "unreviewed harbor feed refiles visitor boats under charters; the harbormaster's notice (user-forwarded, verified) keeps berths (indirect); v3i conflict order: feed first"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this call under exactly one label: berths | moorings | fuel | repairs | charters | safety. Call: '{bk} on the duty sheet.' Reply with the label only.", "initial_expected": "berths"},
            {"actor": "environment", "text": MARI_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "An unreviewed harbor aggregator feed claims every regatta visitor boat, including {bk}, was refiled under charters on the duty board today."},
            {"actor": "environment", "source_type": "user", "text": "The regatta secretary forwards the harbormaster's notice; the desk verified it: visitor boat allocations stay on the quay assignment roster, unchanged, and {bk} keeps its usual tasking. Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Dawn watch at the harbor office on {day}. The office card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this call. The office card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MARI, "berths", values_rows({
            "bk": [
                "the pontoon allocation for the regatta visitors",
                "the guest quay draw for the rally fleet",
                "the visitors' trot layout for the festival boats",
                "the rally fleet plan for the classic flotilla",
                "the guest moorings roster for the sail-past",
            ],
            "pq": [
                "log the visiting yacht pair at the guest quay",
                "record the rally sloops on the north trot",
                "place the festival gaffs on the east pontoon",
                "assign the cruising club boats to the south quay",
                "note the classic dinghies at the visitors' ladder",
            ],
            "day": MARI_DAYS,
        }), 5),
        "s3t2",
    ),
}

# --- cr-4007 source_conflict (museum; verified notice FIRST, unreviewed feed later; security holds)
cr_4007 = {
    "id": "cr-4007",
    "family": "correction_reuse",
    "sub_type": "source_conflict",
    "seed_error": {"value": "conservation", "mechanism": "source_conflict"},
    "labels": {"note": "curator's notice (user-forwarded, verified) keeps loan screenings with door checks (indirect); a LATER unreviewed feed claims conservation - reversed conflict order of cr-4006 (verified early vs unreviewed late)"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Sort this booking into exactly one label: exhibits | tours | conservation | security | memberships | facilities. Booking: '{bk} on the screening list.' Reply with the label only.", "initial_expected": "security"},
            {"actor": "environment", "text": MUSE_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "user", "text": "The county liaison forwards the curator's notice; the desk verified it: the loan screenings stay with door checks and bag surveillance, unchanged, and {bk} keeps its slot. Reply in one short line."},
            {"actor": "environment", "source_type": "environment", "text": "An unreviewed museum forum feed claims all loan-screening slots, including {bk}, were reassigned to conservation on the duty board today."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "Midweek shift at the museum desk on {day}. The desk card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Sort this booking. The desk card is not at hand. Booking: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MUSE, "security", values_rows({
            "bk": [
                "the loan screening for the amber case",
                "the collection view for the insurance assessor",
                "the silver gallery opening check",
                "the private view sweep for the donors' evening",
                "the strongroom access check for the audit visit",
            ],
            "pq": [
                "roster the night checks for the crown display",
                "walk the bag sweep before the auction viewing",
                "cover the door watch at the gala preview",
                "run the cordon check for the film crew visit",
                "log the camera round after the loan unload",
            ],
            "day": MUSE_DAYS,
        }), 0),
        "s3t2",
    ),
}

# --- cr-4008 retraction (marina; bulletin briefly routes fuel work under repairs; withdrawn)
cr_4008 = {
    "id": "cr-4008",
    "family": "correction_reuse",
    "sub_type": "retraction",
    "seed_error": {"value": "repairs", "mechanism": "retracted_correction"},
    "labels": {"note": "bulletin briefly routes dockside fuel work under repairs; bulletin withdrawn (misrouted); withdrawal restates the standing rule WITH its label (v3i cr-3008 lesson); probe expects fuel"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "Log this call under exactly one label: berths | moorings | fuel | repairs | charters | safety. Call: '{bk} on the spring sheet.' Reply with the label only.", "initial_expected": "fuel"},
            {"actor": "environment", "text": MARI_CARD},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "Roster bulletin: the county workshop barge covers {bk} this week; classify such calls under repairs on the duty board for now. Amend in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "The bulletin is withdrawn: it was misrouted from another harbor and does not apply here; dockside refueling stays fuel under the standing card. Amend in one short line."},
        ]},
        {"index": 4, "turns": [
            {"actor": "environment", "text": "Late watch at the harbor office on {day}. The office card is away. Acknowledge in one short line."},
            {"actor": "environment", "text": "Log this call. The office card is not at hand. Call: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "variants": fix_probe_refs(
        variants_classification(MARI, "fuel", values_rows({
            "bk": [
                "the berth-side bowser top-up for the trip boats",
                "the quay tank transfer for the fishing fleet",
                "the duty-pump uplift for the patrol launch",
                "the jerry-can run for the tide watch",
                "the fuel barge draw for the dredger",
            ],
            "pq": [
                "log the marina office tank refill before the rush",
                "record the pump-room uplift at first light",
                "book the bowser round for the pontoons",
                "note the two-stroke draw for the patrol rib",
                "enter the duty-tank transfer for the workboats",
            ],
            "day": MARI_DAYS,
        }), 2),
        "s4t2",
    ),
}

# ============================================================================
# contradiction_update x4 (primary) — recency-defeat designs + one v3i anchor
# ============================================================================

# cu-4101 retracted_correction: verified correction WITHDRAWN; original governs.
cu_4101 = {
    "id": "cu-4101",
    "family": "contradiction_update",
    "labels": {"note": "proof-cabinet setting corrected, then the correction withdrawn (misrouted); probe expects the ORIGINAL value; recency picks the retracted value (trap); R5 keeps marking s1 superseded in T2/T3 (declared blind spot)"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "You keep the bakery depot notes. For the log: the proof cabinet holds {old} degrees overnight. Acknowledge in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "Correction for the records: the thermostat was replaced; the proof cabinet now holds {new} degrees, not {old}. Note the correction in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "The maintenance desk says the correction is withdrawn: it was misrouted from the riverside branch and does not apply here; the standing setting from the first log holds as before. Amend in one short line."},
        ]},
        {"index": 4, "turns": [
            {"actor": "environment", "text": "A night baker asks; the depot notes are not at hand. Acknowledge in one short line."},
            {"actor": "environment", "text": "What does the proof cabinet hold overnight? Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "seed_error": {"value": "{new}", "mechanism": "retracted_correction"},
    "variants": variants_value_sets([
        {"values": {"old": "74", "new": "81"}, "probes": {"s4t2": {"labels": ["70", "74", "78", "81", "85", "89"], "expected": "74"}}},
        {"values": {"old": "76", "new": "82"}, "probes": {"s4t2": {"labels": ["72", "76", "79", "82", "86", "90"], "expected": "76"}}},
        {"values": {"old": "78", "new": "84"}, "probes": {"s4t2": {"labels": ["74", "78", "81", "84", "88", "92"], "expected": "78"}}},
        {"values": {"old": "72", "new": "79"}, "probes": {"s4t2": {"labels": ["68", "72", "75", "79", "83", "87"], "expected": "72"}}},
        {"values": {"old": "77", "new": "85"}, "probes": {"s4t2": {"labels": ["73", "77", "81", "85", "89", "93"], "expected": "77"}}},
    ], 1, ["s4t2"]),
}

# cu-4102 user_override: unverified user push; verified original governs.
cu_4102 = {
    "id": "cu-4102",
    "family": "contradiction_update",
    "labels": {"note": "verified tally-screen count stands; weekend baker pushes a new count (unverified); probe expects the verified ORIGINAL; recency picks the push (trap)"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "source_type": "tool", "text": "You keep the bakery depot notes. The tally screen, verified readout: the morning batch is {old} trays. Acknowledge in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "user", "text": "The weekend baker insists: 'correction for the records - the morning batch is {new} trays today, not {old}.' Reply in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "A counter clerk asks; the depot notes are not at hand. Acknowledge in one short line."},
            {"actor": "environment", "text": "How many trays is the morning batch? Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "seed_error": {"value": "{new}", "mechanism": "user_override"},
    "variants": variants_value_sets([
        {"values": {"old": "26", "new": "31"}, "probes": {"s3t2": {"labels": ["22", "26", "29", "31", "34", "38"], "expected": "26"}}},
        {"values": {"old": "28", "new": "33"}, "probes": {"s3t2": {"labels": ["24", "28", "31", "33", "36", "40"], "expected": "28"}}},
        {"values": {"old": "25", "new": "30"}, "probes": {"s3t2": {"labels": ["21", "25", "28", "30", "33", "37"], "expected": "25"}}},
        {"values": {"old": "27", "new": "32"}, "probes": {"s3t2": {"labels": ["23", "27", "30", "32", "35", "39"], "expected": "27"}}},
        {"values": {"old": "29", "new": "34"}, "probes": {"s3t2": {"labels": ["25", "29", "32", "34", "37", "41"], "expected": "29"}}},
    ], 3, ["s3t2"]),
}

# cu-4103 user_override: verified tool correction, then user pushes a different value.
cu_4103 = {
    "id": "cu-4103",
    "family": "contradiction_update",
    "labels": {"note": "verified building-monitor readout corrects the setpoint; a contractor later pushes a different value; probe expects the verified correction; recency picks the push (trap)"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "source_type": "environment", "text": "You keep the museum climate notes. For the log: the print-room setpoint is {old} degrees. Acknowledge in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "source_type": "tool", "text": "Building monitor, verified readout - correction for the records: the print-room setpoint is now {new}, not {old}. Note the correction in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "source_type": "user", "text": "A contractor insists: 'the dial reads {alt} - go with {alt}.' Reply in one short line."},
        ]},
        {"index": 4, "turns": [
            {"actor": "environment", "text": "A registrar asks; the climate notes are not at hand. Acknowledge in one short line."},
            {"actor": "environment", "text": "What is the print-room setpoint? Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "seed_error": {"value": "{alt}", "mechanism": "user_override"},
    "variants": variants_value_sets([
        {"values": {"old": "20", "new": "24", "alt": "22"}, "probes": {"s4t2": {"labels": ["18", "20", "22", "24", "26", "28"], "expected": "24"}}},
        {"values": {"old": "21", "new": "25", "alt": "23"}, "probes": {"s4t2": {"labels": ["19", "21", "23", "25", "27", "29"], "expected": "25"}}},
        {"values": {"old": "19", "new": "23", "alt": "21"}, "probes": {"s4t2": {"labels": ["17", "19", "21", "23", "25", "27"], "expected": "23"}}},
        {"values": {"old": "22", "new": "26", "alt": "24"}, "probes": {"s4t2": {"labels": ["20", "22", "24", "26", "28", "30"], "expected": "26"}}},
        {"values": {"old": "18", "new": "22", "alt": "20"}, "probes": {"s4t2": {"labels": ["16", "18", "20", "22", "24", "26"], "expected": "22"}}},
    ], 0, ["s4t2"]),
}

# cu-4104 superseded_value: the v3i pattern kept as the family anchor.
cu_4104 = {
    "id": "cu-4104",
    "family": "contradiction_update",
    "labels": {"note": "fuel-berth depth allowance corrected after the dredge; probe expects the corrected value; superseded old value stays in options (v3i anchor cluster)"},
    "sessions": [
        {"index": 1, "turns": [
            {"actor": "environment", "text": "You keep the marina notes. For the log: the fuel berth depth allowance is {old} meters. Acknowledge in one short line."},
        ]},
        {"index": 2, "turns": [
            {"actor": "environment", "text": "Correction for the records: the dredge finished; the fuel berth depth allowance is now {new} meters, not {old}. Note the correction in one short line."},
        ]},
        {"index": 3, "turns": [
            {"actor": "environment", "text": "A skiff owner asks; the marina notes are not at hand. Acknowledge in one short line."},
            {"actor": "environment", "text": "What is the fuel berth depth allowance? Options: {options} - reply with the number only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
        ]},
    ],
    "seed_error": {"value": "{old}", "mechanism": "superseded_value"},
    "variants": variants_value_sets([
        {"values": {"old": "5", "new": "6"}, "probes": {"s3t2": {"labels": ["4", "5", "6", "8", "10", "12"], "expected": "6"}}},
        {"values": {"old": "4", "new": "7"}, "probes": {"s3t2": {"labels": ["3", "4", "5", "7", "9", "11"], "expected": "7"}}},
        {"values": {"old": "6", "new": "8"}, "probes": {"s3t2": {"labels": ["4", "6", "7", "8", "10", "12"], "expected": "8"}}},
        {"values": {"old": "5", "new": "9"}, "probes": {"s3t2": {"labels": ["4", "5", "6", "9", "11", "13"], "expected": "9"}}},
        {"values": {"old": "7", "new": "10"}, "probes": {"s3t2": {"labels": ["5", "7", "8", "10", "12", "14"], "expected": "10"}}},
    ], 4, ["s3t2"]),
}

# ============================================================================
# repeated_task x6 (secondary) — museum rt-4201..3203, marina rt-4204..4206
# ============================================================================

def rt_scenario(sid, vocab, trap, expected, card_line, rows, offset):
    return {
        "id": sid,
        "family": "repeated_task",
        "sub_type": "scripted_own_answer",
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": f"duty sheet pins the task as '{trap}'; standing card says {expected}; reuse expects {expected}"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Sort this duty into exactly one label: {' | '.join(vocab)}. Duty: '{{task}}.' Reply with the label only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your earlier duty sheet routes {{task}} under '{trap}'. {card_line} Amend the sheet in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Duty handover before the {slot} rush. The standing card applies. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Fresh duty round begins. The slate cards are away. Acknowledge in one short line."},
                {"actor": "environment", "text": "Sort this duty. The slate cards are not at hand. Duty: '{pq}.' Options: {options} - reply with the label only.", "probe": {"kind": "exact_match", "class": "rm_eligible"}},
            ]},
        ],
        "variants": fix_probe_refs(
            variants_classification(vocab, expected, rows, offset),
            "s3t2",
        ),
    }


SLOTS_MUSE = ["school", "lecture", "loan", "gala", "fitting"]
SLOTS_MARI = ["regatta", "tide", "gale", "haul", "patrol"]

rt_4201 = rt_scenario(
    "rt-4201", MUSE, "memberships", "tours",
    "The standing card, verified: docent-guided visits and walking programs are tours; patron schemes and season passes are memberships.",
    values_rows({
        "task": [
            "the patron badge print run",
            "the season-pass mail-out",
            "the friends' renewal desk",
            "the donor lanyard sort",
            "the subscriber card batch",
        ],
        "pq": [
            "queue the school group for the cellar walk",
            "guide the visitors' hour round the kiln",
            "walk the newcomers through the ship hall",
            "lead the lunchtime group round the looms",
            "host the evening club round the presses",
        ],
        "slot": SLOTS_MUSE,
    }), 1,
)

rt_4202 = rt_scenario(
    "rt-4202", MUSE, "exhibits", "conservation",
    "The standing card, verified: display and case installations are exhibits; artifact care and restoration handling is conservation.",
    values_rows({
        "task": [
            "the coin cabinet dust-down",
            "the textile case light check",
            "the bronze shelf wipe",
            "the fresco room monitor swap",
            "the vitrine seal inspection",
        ],
        "pq": [
            "log the dust-cover change for the statues",
            "record the humidity tray swap in the map room",
            "brush the salt off the ship timbers",
            "check the adhesive on the mural edge",
            "clean the glass over the butterfly trays",
        ],
        "slot": SLOTS_MUSE,
    }), 3,
)

rt_4203 = rt_scenario(
    "rt-4203", MUSE, "security", "facilities",
    "The standing card, verified: access control and surveillance matters are security; building and room upkeep is facilities.",
    values_rows({
        "task": [
            "the storeroom lock test",
            "the keycard batch audit",
            "the camera lens wipe",
            "the night alarm walk",
            "the door-code change",
        ],
        "pq": [
            "report the gallery roof drip",
            "swap the burnt corridor lamp",
            "refit the cloakroom door sweep",
            "unblock the yard drain",
            "patch the plaster in the stairwell",
        ],
        "slot": SLOTS_MUSE,
    }), 5,
)

rt_4204 = rt_scenario(
    "rt-4204", MARI, "charters", "moorings",
    "The standing card, verified: anchor lines and buoy positioning is moorings; hired boat trips and skippered outings are charters.",
    values_rows({
        "task": [
            "the club's birthday launch outing",
            "the sunset skipper run",
            "the stag-party boat hire",
            "the corporate yacht morning",
            "the angling club's hired launch",
        ],
        "pq": [
            "re-lead the ground line at the mid trot",
            "swap the guest buoy at the north anchorage",
            "check the pickup lines on the visitors' buoy",
            "sink the new mooring block off the quay",
            "buoy-mark the shallow patch for the rally",
        ],
        "slot": SLOTS_MARI,
    }), 0,
)

rt_4205 = rt_scenario(
    "rt-4205", MARI, "repairs", "fuel",
    "The standing card, verified: dockside refueling and tank transfers is fuel; hull and engine fixing work is repairs.",
    values_rows({
        "task": [
            "the engine winterization",
            "the gearbox strip-down",
            "the propeller re-pitch",
            "the hull scrape and repaint",
            "the stern gland repack",
        ],
        "pq": [
            "log the jerry-can transfer for the tide watch",
            "record the bowser uplift at the duty barge",
            "book the duty-tank draw for the launch",
            "note the petrol run for the mail boat",
            "enter the two-stroke top-up for the rib",
        ],
        "slot": SLOTS_MARI,
    }), 2,
)

rt_4206 = rt_scenario(
    "rt-4206", MARI, "berths", "safety",
    "The standing card, verified: life equipment and water rules is safety; slip allocation and quay assignments are berths.",
    values_rows({
        "task": [
            "the visitor slip draw",
            "the guest quay ballot",
            "the rally trot allocation",
            "the festival pontoon roster",
            "the waiting-list quay draw",
        ],
        "pq": [
            "restock the life-vest crate",
            "check the flare expiry dates",
            "service the horseshoe rings",
            "audit the throw-line lockers",
            "rehang the ladder boards",
        ],
        "slot": SLOTS_MARI,
    }), 4,
)

# ============================================================================
# delayed_recall x3 / distractor_recall x3 (secondary) — airport ground stores
# ============================================================================

AIR_CHORES = ["the dawn sweep", "the taxiway check", "the beacon test", "the fence walk", "the drain clear"]
AIR_ROLES = ["duty engineer", "grounds keeper", "night fitter", "line mechanic", "base technician"]


def dr_scenario(sid, thing, rows, offset):
    return {
        "id": sid,
        "family": "delayed_recall",
        "labels": {"note": "store code with a NON-label companion fact (cycle-1 fix kept): echoing both facts yields at most one code"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the regional airport ground stores. For the log: the {thing} code is {{code}}; the {{comp_thing}} {{comp_verb}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} done; nothing else changes. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "A {role} arrives; the store book is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"The crew member needs the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match"}},
            ]},
        ],
        "variants": variants_value_sets(rows, offset, ["s3t2"]),
    }


DR_POOLS = [
    ("radio locker", [
        {"code": "D14", "comp_thing": "crew kettle", "comp_verb": "whistles at six", "labels": ["D14", "E27", "F33", "G41", "H29", "J52"]},
        {"code": "E27", "comp_thing": "floor drain", "comp_verb": "gurgles at noon", "labels": ["E27", "F33", "G41", "H29", "J52", "K64"]},
        {"code": "F33", "comp_thing": "yard lamp", "comp_verb": "flickers at dusk", "labels": ["F33", "G41", "H29", "J52", "K64", "L78"]},
        {"code": "G41", "comp_thing": "gate horn", "comp_verb": "sounds at dawn", "labels": ["G41", "H29", "J52", "K64", "L78", "M85"]},
        {"code": "H29", "comp_thing": "wind sock", "comp_verb": "frays in storms", "labels": ["H29", "J52", "K64", "L78", "M85", "N97"]},
    ]),
    ("deicing store", [
        {"code": "K52", "comp_thing": "crew fridge", "comp_verb": "hums all night", "labels": ["K52", "L48", "M61", "N37", "P45", "Q79"]},
        {"code": "L48", "comp_thing": "apron heater", "comp_verb": "ticks when cold", "labels": ["L48", "M61", "N37", "P45", "Q79", "R83"]},
        {"code": "M61", "comp_thing": "hose reel", "comp_verb": "squeals at frost", "labels": ["M61", "N37", "P45", "Q79", "R83", "S96"]},
        {"code": "N37", "comp_thing": "spill bin", "comp_verb": "fills by friday", "labels": ["N37", "P45", "Q79", "R83", "S96", "T28"]},
        {"code": "P45", "comp_thing": "ladder rack", "comp_verb": "rattles on tow", "labels": ["P45", "Q79", "R83", "S96", "T28", "U51"]},
    ]),
    ("runway cabinet", [
        {"code": "Q83", "comp_thing": "badge press", "comp_verb": "thumps at eight", "labels": ["Q83", "R59", "S66", "T74", "U88", "V32"]},
        {"code": "R59", "comp_thing": "tool bench", "comp_verb": "slides when wet", "labels": ["R59", "S66", "T74", "U88", "V32", "W47"]},
        {"code": "S66", "comp_thing": "parts washer", "comp_verb": "spins till noon", "labels": ["S66", "T74", "U88", "V32", "W47", "X69"]},
        {"code": "T74", "comp_thing": "battery rack", "comp_verb": "buzzes on charge", "labels": ["T74", "U88", "V32", "W47", "X69", "Y54"]},
        {"code": "U88", "comp_thing": "rain gauge", "comp_verb": "tips at showers", "labels": ["U88", "V32", "W47", "X69", "Y54", "Z21"]},
    ]),
]

dr_scenarios = []
for i, (thing, rows) in enumerate(DR_POOLS):
    value_rows = []
    for j, r in enumerate(rows):
        value_rows.append({
            "values": {"code": r["code"], "comp_thing": r["comp_thing"],
                       "comp_verb": r["comp_verb"], "chore": AIR_CHORES[j], "role": AIR_ROLES[j]},
            "probes": {"s3t2": {"labels": r["labels"], "expected": r["code"]}},
        })
    dr_scenarios.append(dr_scenario(f"dr-43{i+1:02d}", thing, value_rows, i))


def dx_scenario(sid, thing, lure_thing, rows, offset):
    return {
        "id": sid,
        "family": "distractor_recall",
        "labels": {"note": f"two store codes stated; the {thing} code is probed while the {lure_thing} code acts as the lure"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the regional airport ground stores. For the log: the {thing} code is {{code}}; the {lure_thing} code is {{lure}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} done; nothing else changes. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "A {role} arrives; the store book is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"The crew member needs the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match"}},
            ]},
        ],
        "variants": variants_value_sets(rows, offset, ["s3t2"]),
    }


DX_POOLS = [
    ("tool crate", "spare parts shelf", [
        ("C21", "V56"), ("D35", "W67"), ("E49", "X71"), ("F53", "Y82"), ("G67", "Z93"),
    ], ["C21", "D35", "E49", "F53", "G67", "V56", "W67", "X71", "Y82", "Z93"]),
    ("lighting cart", "generator shed", [
        ("J24", "B39"), ("K38", "C45"), ("L46", "D57"), ("M59", "E63"), ("N63", "F78"),
    ], ["J24", "K38", "L46", "M59", "N63", "B39", "C45", "D57", "E63", "F78"]),
    ("grit hopper", "sand bay", [
        ("P17", "G28"), ("Q29", "H36"), ("R34", "J48"), ("S48", "K55"), ("T55", "L69"),
    ], ["P17", "Q29", "R34", "S48", "T55", "G28", "H36", "J48", "K55", "L69"]),
]

dx_scenarios = []
for i, (thing, lure_thing, pairs, pool) in enumerate(DX_POOLS):
    rows = []
    for j, (code, lure) in enumerate(pairs):
        labels = [code, lure] + [c for c in pool if c not in (code, lure)][:4]
        rows.append({
            "values": {"code": code, "lure": lure, "chore": AIR_CHORES[j], "role": AIR_ROLES[j]},
            "probes": {"s3t2": {"labels": labels, "expected": code}},
        })
    dx_scenarios.append(dx_scenario(f"dx-44{i+1:02d}", thing, lure_thing, rows, i))

# ============================================================================
# guess_calibration x3 (secondary) — never-stated facts, per-seed entities
# ============================================================================

def gc_scenario(sid, opener_tmpl, asker_tmpl, q1_tmpl, q2_tmpl, rows, offset):
    return {
        "id": sid,
        "family": "guess_calibration",
        "labels": {"note": "never-stated facts; guess rate and position bias (design E14); expected null by design"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": opener_tmpl},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": asker_tmpl},
                {"actor": "environment", "text": q1_tmpl + " Options: {options} - reply with the word only.", "probe": {"kind": "guess_calibration", "expected": None, "class": "guess_cal"}},
                {"actor": "environment", "text": q2_tmpl + " Options: {options} - reply with the number only.", "probe": {"kind": "guess_calibration", "expected": None, "class": "guess_cal"}},
            ]},
        ],
        "variants": variants_value_sets(rows, offset, ["s2t2", "s2t3"]),
    }


GLAZES = ["amber", "ruby", "honey", "cocoa", "cream", "mint"]
DIRS = ["north", "south", "east", "west", "upper", "lower"]
FLAGC = ["red", "blue", "green", "white", "yellow", "orange"]

gc_4501 = gc_scenario(
    "gc-4501",
    "You mind the bakery counter on the {shift} watch. Acknowledge in one short line.",
    "{visitor} asks about records this counter never kept. Answer as best you can. Acknowledge in one short line.",
    "What glaze color is the {e1} batch?",
    "How many trays sit on the {e2} rack?",
    [
        {"values": {"shift": "early", "visitor": "a courier", "e1": "almond ring", "e2": "proving"},
         "probes": {"s2t2": {"labels": GLAZES}, "s2t3": {"labels": ["3", "4", "5", "6", "7", "8"]}}},
        {"values": {"shift": "market", "visitor": "a driver", "e1": "plait loaf", "e2": "cooling"},
         "probes": {"s2t2": {"labels": GLAZES}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "school", "visitor": "a fitter", "e1": "seed cob", "e2": "slicing"},
         "probes": {"s2t2": {"labels": GLAZES}, "s2t3": {"labels": ["2", "3", "4", "5", "6", "7"]}}},
        {"values": {"shift": "weekend", "visitor": "a cleaner", "e1": "fruit slab", "e2": "packing"},
         "probes": {"s2t2": {"labels": GLAZES}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "closing", "visitor": "a guard", "e1": "rye tin", "e2": "display"},
         "probes": {"s2t2": {"labels": GLAZES}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
    ],
    0,
)

gc_4502 = gc_scenario(
    "gc-4502",
    "You mind the regional airport help desk on the {shift} rotation. Acknowledge in one short line.",
    "{visitor} asks about records this desk never kept. Answer as best you can. Acknowledge in one short line.",
    "Which way does the {e1} door face?",
    "How many trolleys wait at the {e2} bay?",
    [
        {"values": {"shift": "dawn", "visitor": "a courier", "e1": "baggage hall", "e2": "far stand"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["2", "3", "4", "5", "6", "7"]}}},
        {"values": {"shift": "schools", "visitor": "a trainee", "e1": "check-in row", "e2": "near stand"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["3", "4", "5", "6", "7", "8"]}}},
        {"values": {"shift": "clubs", "visitor": "a pilot", "e1": "crew porch", "e2": "old pen"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "late", "visitor": "a cleaner", "e1": "cargo pen", "e2": "new pen"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "night", "visitor": "a guard", "e1": "fly crew door", "e2": "far carousel"},
         "probes": {"s2t2": {"labels": DIRS}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
    ],
    2,
)

gc_4503 = gc_scenario(
    "gc-4503",
    "You mind the marina office on the {shift} standby. Acknowledge in one short line.",
    "{visitor} asks about records this office never kept. Answer as best you can. Acknowledge in one short line.",
    "What color is the {e1} flag?",
    "How many fenders hang on the {e2} side?",
    [
        {"values": {"shift": "weekday", "visitor": "a courier", "e1": "fuel quay", "e2": "workboat"},
         "probes": {"s2t2": {"labels": FLAGC}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "night", "visitor": "a ferry hand", "e1": "visitors' trot", "e2": "launch"},
         "probes": {"s2t2": {"labels": FLAGC}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "drill", "visitor": "a rigger", "e1": "guest pontoon", "e2": "tender"},
         "probes": {"s2t2": {"labels": FLAGC}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
        {"values": {"shift": "storm", "visitor": "a warden", "e1": "north jetty", "e2": "barge"},
         "probes": {"s2t2": {"labels": FLAGC}, "s2t3": {"labels": ["7", "8", "9", "10", "11", "12"]}}},
        {"values": {"shift": "regatta", "visitor": "a scorer", "e1": "rally moorings", "e2": "skiff"},
         "probes": {"s2t2": {"labels": FLAGC}, "s2t3": {"labels": ["8", "9", "10", "11", "12", "13"]}}},
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
        "Suite v3j for CONT-005 cycle 2 (FREEZE-B, held-out confirmatory): the "
        "v3i protocol (v3 label-form probes + predeclared per-seed variant "
        "table, manifest.variant_seeds = {3001..3005}) with fresh worlds "
        "(municipal museum front desk, marina harbor office, bakery depot, "
        "regional airport ground stores) and ids x-4xxx, disjoint from "
        "v1/v2/v2-calibration/v3/v3h/v3i (validator V3 covers every rendered "
        "seed). Pilot-informed difficulty calibration, declared openly per "
        "EVALUATION-PREP-v3 section 2 stage 2: CU rebalanced HARDER (v3i "
        "clause-1 FAIL at 0.050 error - near-miss options did not beat the "
        "recency heuristic) via recency-defeat designs in 3/4 clusters "
        "(retracted_correction cu-4101: correction withdrawn, original "
        "governs; user_override cu-4102/cu-4103: unverified user push vs "
        "verified original/verified correction) + the v3i superseded_value "
        "anchor cu-4104; CR sub-type composition IDENTICAL to v3i "
        "(valid_environment 2, valid_tool 1, erroneous_user 2, "
        "source_conflict 2, retraction 1 - no post-pilot sub-type "
        "cherry-picking), difficulty re-aimed mid-scale via wording levers "
        "only (indirect counter-evidence, probe-case surface pull toward the "
        "trap, withdrawal restating the standing rule with its label, BOTH "
        "source-conflict orders across cr-4006/cr-4007). Resolution flags "
        "render as plain NOTE: prose (claims.py FREEZE-B fix, pre-authorized "
        "pilot clause-4). Secondary: repeated_task x6, delayed_recall x3, "
        "distractor_recall x3, guess_calibration x3 (6 never-stated probes). "
        "Rendering: continuity.fixtures.render_seed_variant (single "
        "definition shared by runner, validator, assembly gate)."
    ),
}


def main() -> int:
    all_scenarios = [
        cr_4001, cr_4002, cr_4003, cr_4004, cr_4005, cr_4006, cr_4007, cr_4008,
        cu_4101, cu_4102, cu_4103, cu_4104,
        rt_4201, rt_4202, rt_4203, rt_4204, rt_4205, rt_4206,
        *dr_scenarios, *dx_scenarios, gc_4501, gc_4502, gc_4503,
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
