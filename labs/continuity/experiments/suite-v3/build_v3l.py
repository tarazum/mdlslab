"""Deterministic builder for fixture suite v3l (CONT-006 lesson transfer).

Emits fixtures/v3l: 22 scenarios under fixture protocol v3i (v3 protocol +
predeclared per-seed variant table), NEW predeclared seeds {6001..6007}, ids
x-6xxx, fresh worlds (city ferry terminal, campus equipment cage, greenhouse
mist line, kiln room, aquarium quarantine, print workshop ink line, cheese
cave; dx: ski patrol cache, harbor chandlery, rail museum signal box; dr:
bell foundry, seed vault; gc: municipal ice rink, weaving mill dyehouse,
lighthouse lamp room) — rendered turn texts disjoint from
v1/v2/v2-cal/v3/v3h/v3i/v3j/v3k (validator V3 covers every seed both ways).

CONT-006 design basis (docs/CONT-006-DESIGN.md, docs/CONT006-TAXONOMY.md
FROZEN before this authoring): the suite instantiates the taxonomy failure
classes with DIFFERENT surface wording on fresh worlds —
  PRIMARY transfer (TR, 15 clusters): cr-6001..6004 (FP-3a x2, FP-3b x2),
  cu-6101..6104 (FP-1: superseded x2 + retracted x2), rt-6201..6203 (FP-2),
  dx-6401..6402 (FP-4), dr-6301..6302 (FP-5);
  VALIDATION (VAL, 4 clusters, activation decisions only, never in the
  primary endpoint): cr-6005 (FP-3b), cu-6105 (FP-1), rt-6204 (FP-2),
  dx-6403 (FP-4);
  GC x3 (guess band on the working core).
FP-6 (format miss) is exercised by every label-form probe (no separate
scenarios; the invalid-format decomposition is a prereg secondary).

Structural vocabulary is INHERITED from the frozen suites only (v3i/v3j
seed_error mechanisms + initial_expected; v3k lure_value + label windows);
no new mechanics. Probe class transfer_eligible (the v3k analogue; VAL
clusters share it — validator V11/V17).

Deterministic: no RNG, explicit tables only. Re-running overwrites
fixtures/v3l byte-identically.
"""

from __future__ import annotations

import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = LAB_ROOT / "fixtures" / "v3l"
SEEDS = [6001, 6002, 6003, 6004, 6005, 6006, 6007]

VALIDATION_IDS = ["cr-6005", "cu-6105", "rt-6204", "dx-6403"]


def rot(seq: list[str], k: int) -> list[str]:
    n = len(seq)
    return [seq[(i + k) % n] for i in range(n)]


def perm_orders(vocab: list[str], i: int) -> list[str]:
    """7 pairwise-distinct label orders over a FIXED 6-word vocabulary
    (7 seeds exceed the 6 pure rotations — v3j had 5 seeds; the 7th order is
    a transposition of the identity, which no rotation equals)."""
    orders = [rot(vocab, k) for k in range(6)]
    ident = list(vocab)
    ident[0], ident[1] = ident[1], ident[0]
    orders.append(ident)
    return orders[i]


def variants(rows: list[dict], probe_refs: list[str]) -> dict:
    """rows: one per seed, each {'values': {...}, 'probes': {ref: spec}} —
    probe specs are authored FULLY per seed (order diversity for fixed-vocab
    families comes from perm_orders at authoring time)."""
    return {str(sd): {"values": rows[i]["values"], "probes": rows[i]["probes"]}
            for i, sd in enumerate(SEEDS)}


def write_scenario(rel: str, scenario: dict) -> None:
    path = OUT_DIR / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scenario, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")


# ============================================================================
# correction_reuse x5 — city ferry terminal; vocab fixed, per-seed orders via
# perm_orders; sub-types: vce/vct (FP-3a, agent's wrong first answer fixed by
# a verified correction), euc (FP-3b, unverified user push), sc (FP-3b,
# unverified source claims a reassignment). Mechanisms inherited from v3j.
# ============================================================================

FERRY = ["berthing", "cargo", "tickets", "safety", "fueling", "crewing"]
FERRY_CARD = ("The standing terminal card: slip assignments and gangway placement "
              "are berthing; vehicle decks and freight holds are cargo; passage sales "
              "and reservations are tickets; life drills and rail checks are safety; "
              "bunkering and pump work is fueling; roster changes and relief sign-ons "
              "are crewing.")
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def cr_variants(bks: list[str], pqs: list[str], expected: str,
                trap: str) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"bk": bks[i], "pq": pqs[i], "day": DAYS[i]},
            "probes": {"s3t2": {"labels": perm_orders(FERRY, i), "expected": expected}},
        })
    return variants(rows, ["s3t2"])


def cr_vce_vct(sid: str, sub: str, thing: str, bk_note: str, corr_text: str,
               expected: str, trap: str, bks: list[str], pqs: list[str]) -> dict:
    """vce/vct shape (v3j cr-4001/4003): seeded own wrong answer + card +
    VERIFIED correction. seed mechanism scripted_agent_answer."""
    return {
        "id": sid,
        "family": "correction_reuse",
        "sub_type": sub,
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": f"{bk_note}; verified correction re-routes to {expected}"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Log this call under exactly one label: {' | '.join(FERRY)}. Call: '{{bk}} {thing}.' Reply with the label only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your counter log from the previous watch routes {{bk}} {thing} under '{trap}'. Keep the log line in view and acknowledge in one short line."},
                {"actor": "environment", "text": FERRY_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr_text + " Amend your records in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Late shift at the ferry terminal on {day}. The terminal card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"Log this call. The terminal card is not at hand. Call: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected, trap),
    }


cr_6001 = cr_vce_vct(
    "cr-6001", "valid_correction_environment", "on the morning sheet",
    "night buoy-line rig logged 'safety'; port captain's bulletin re-routes to berthing",
    "Terminal control bulletin, verified notice from the port captain's office: the log "
    "line routing {bk} under 'safety' is out of date; gangway and slip placement for it "
    "are berthing under the standing card.",
    "berthing", "safety",
    ["the night buoy-line rig for pier two", "the gangway plank shift on the river run",
     "the finger-slip realignment at gate three", "the mooring ladder swap on the east berth",
     "the pontoon walkway check at the north quay", "the slip rope re-lead by the pilot steps",
     "the quay ladder survey at the small-craft dock"],
    ["the stern ramp line-up for the mail boat", "the berth sweep before the day cruiser",
     "the gangway count for the school ferry", "the slip tally at the floating dock",
     "the ramp pin check for the night crossing", "the quay line round at the terminal wing",
     "the walkway bolt pass at pier nine"],
)

cr_6002 = cr_vce_vct(
    "cr-6002", "valid_correction_tool", "on the freight list",
    "van-row bundle logged 'tickets'; service-verified manifest scanner re-routes to cargo",
    "The manifest scanner, service-verified this morning, reads {bk} as vehicle-deck "
    "freight: cargo under the standing card; the old 'tickets' routing is out of date.",
    "cargo", "tickets",
    ["the crane lift for the breakbulk pallets", "the strap-down round for the van row",
     "the netting pass over the open trailer", "the chock swap on the lower car deck",
     "the lashing check for the steel coils", "the pallet count for the drum shipment",
     "the trestle move for the machine crates"],
    ["the deck seal look-over for the feed truck", "the strap audit for the crate ferry",
     "the net round on the livestock run", "the chock tally for the boatyard haul",
     "the lashing pass at the tailboard lift", "the drum count for the morning lighter",
     "the crate survey on the machinery deck"],
)


def cr_euc(sid: str, note: str, insist: str, expected: str, trap: str,
           bks: list[str], pqs: list[str]) -> dict:
    """euc shape (v3j cr-4005): first answer already CORRECT per card; an
    unverified walk-up user push contradicts it. seed user_override."""
    return {
        "id": sid,
        "family": "correction_reuse",
        "sub_type": "erroneous_user_correction",
        "seed_error": {"value": trap, "mechanism": "user_override"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Log this call under exactly one label: {' | '.join(FERRY)}. Call: '{{bk}}.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": FERRY_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": insist + " Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Late shift at the ferry terminal on {day}. The terminal card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"Log this call. The terminal card is not at hand. Call: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected, trap),
    }


cr_6003 = cr_euc(
    "cr-6003",
    "pump-room top-up correctly 'fueling'; walk-up customer pushes 'tickets' (FP-3b)",
    "A walk-up customer insists about {bk}: 'that is just my passage paperwork - run it "
    "through as tickets, that is what the old counter said.' The bunker register, on "
    "file, keeps the pump work as it stands.",
    "fueling", "tickets",
    ["the pump-room top-up for the coastal runner", "the bunker barge transfer at the fuel tier",
     "the hose test on the loading arm", "the tank sounding round for the night steamer",
     "the pump seal swap by the fuel pontoon", "the line purge for the dusk transfer",
     "the gauge check at the bunkering pillar"],
    ["the hose round for the day tanker", "the tank pass at the fuel tier",
     "the pump look-over for the mail steamer", "the line check on the bunker stairs",
     "the seal survey at the fuel shed", "the purge round for the night lighter",
     "the gauge sweep by the pump room"],
)


def cr_sc(sid: str, note: str, verified: str, unreviewed: str, expected: str,
          trap: str, bks: list[str], pqs: list[str]) -> dict:
    """sc shape (v3j cr-4007): first answer CORRECT; verified notice keeps it;
    an unreviewed source claims a reassignment (the trap). seed source_conflict."""
    return {
        "id": sid,
        "family": "correction_reuse",
        "sub_type": "source_conflict",
        "seed_error": {"value": trap, "mechanism": "source_conflict"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Log this call under exactly one label: {' | '.join(FERRY)}. Call: '{{bk}} on the watch list.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": FERRY_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": verified + " Note it in one short line."},
                {"actor": "environment", "source_type": "environment", "text": unreviewed},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Late shift at the ferry terminal on {day}. The terminal card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"Log this call. The terminal card is not at hand. Call: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected, trap),
    }


cr_6004 = cr_sc(
    "cr-6004",
    "relief sign-on correctly 'crewing'; unreviewed chat channel claims move to 'safety' (FP-3b)",
    "The duty office forwards the captain's notice; the terminal verified it: relief "
    "sign-ons for the night crossings stay with roster changes, and {bk} remains as the "
    "card has it.",
    "An unreviewed ferry chat channel claims every relief sign-on, {bk} included, was "
    "moved to the drill board today.",
    "crewing", "safety",
    ["the relief sign-on for the night crossing", "the substitute mate listing for the dawn run",
     "the extra deckhand entry for the weekend ferry", "the standby cook rostering for the mail boat",
     "the night lookout swap on the river run", "the spare engineer callout for the tide trip",
     "the relief purser line for the island service"],
    ["the sign-on tally for the dusk watch", "the mate listing at the crew door",
     "the deckhand round for the first ferry", "the cook callout on the night boat",
     "the lookout swap at the gangway hut", "the engineer entry for the noon trip",
     "the purser line at the roster desk"],
)

cr_6005 = cr_sc(
    "cr-6005",
    "VAL cluster (activation only): slip-share booking correctly 'berthing'; unreviewed noticeboard photo claims 'cargo' (FP-3b)",
    "The berthing master's circular, terminal-verified: shared-slip bookings keep their "
    "gangway and slip placement, and {bk} stays as the card has it.",
    "An unreviewed noticeboard photo down by the ramp claims the shared-slip bookings, "
    "{bk} included, were reassigned to the freight holds today.",
    "berthing", "cargo",
    ["the shared-slip booking for the pilot launch", "the slip-share entry for the workboat",
     "the joint berth line for the survey skiff", "the shared slip pass for the dredge tender",
     "the twin-berth note for the cargo launch crew", "the slip split for the harbor tug",
     "the common berth sheet for the fishing run"],
    ["the pilot slip count at dawn", "the workboat berth pass at the gate",
     "the skiff slip tally by the ramp", "the tender line at the shared pontoon",
     "the launch berth round at noon", "the tug slip entry at the wing",
     "the shared sheet check at dusk"],
)


# ============================================================================
# contradiction_update x5 — FP-1 (supersession-resolution miss). Two
# mechanisms inherited from v3j: superseded_value (state -> correction stands;
# probe expects NEW, trap = old) and retracted_correction (state -> correction
# -> withdrawal; probe expects ORIGINAL, trap = the withdrawn correction).
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
        "id": sid,
        "family": "contradiction_update",
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
        "variants": variants(rows, ["s3t2"]),
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
        "id": sid,
        "family": "contradiction_update",
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
        "variants": variants(rows, ["s4t2"]),
    }


cu_6101 = cu_superseded(
    "cu-6101",
    "greenhouse mist line setting corrected; probe expects NEW value (FP-1)",
    "You keep the greenhouse notes. For the log: the mist line runs {old} clicks overnight. Acknowledge in one short line.",
    "Correction for the records: the regulator was swapped; the mist line now runs {new} clicks, not {old}. Note the correction in one short line.",
    "A grower asks; the greenhouse book is not at hand. Acknowledge in one short line.",
    "What does the mist line run overnight?",
    62, 7,
)
cu_6102 = cu_superseded(
    "cu-6102",
    "kiln room soak count corrected; probe expects NEW value (FP-1)",
    "You mind the pottery kiln room. For the log: the glaze load soaks {old} hours before firing. Acknowledge in one short line.",
    "Correction for the records: the schedule changed; the glaze load now soaks {new} hours, not {old}. Note the correction in one short line.",
    "A studio aide asks; the kiln log is not at hand. Acknowledge in one short line.",
    "How long does the glaze load soak?",
    14, 5,
)
cu_6103 = cu_retracted(
    "cu-6103",
    "aquarium quarantine salinity corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You tend the quarantine tanks. For the log: the isolation bank sits at {old} points of salinity. Acknowledge in one short line.",
    "Correction for the records: the meter was recalibrated; the isolation bank sits at {new} points, not {old}. Note the correction in one short line.",
    "The lab says the correction is withdrawn: the recalibration slip belonged to the display tank next door and does not apply here; the standing level from the first log holds as before. Amend in one short line.",
    "A keeper asks; the tank sheet is not at hand. Acknowledge in one short line.",
    "What is the isolation bank salinity?",
    31, 4,
)
cu_6104 = cu_retracted(
    "cu-6104",
    "print workshop ink grade corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You run the print workshop notes. For the log: the platen line feeds grade {old} ink. Acknowledge in one short line.",
    "Correction for the records: the supplier sheet was re-read; the platen line feeds grade {new}, not {old}. Note the correction in one short line.",
    "The foreman says the correction is withdrawn: the re-read sheet was a draft from the label room and does not apply; the standing grade from the first log holds as before. Amend in one short line.",
    "An apprentice asks; the workshop card is not at hand. Acknowledge in one short line.",
    "Which grade does the platen line feed?",
    26, 6,
)
cu_6105 = cu_superseded(
    "cu-6105",
    "VAL cluster (activation only): cheese cave humidity corrected; probe expects NEW (FP-1)",
    "You mind the cheese cave sheet. For the log: the aging room holds {old} steps of humidity. Acknowledge in one short line.",
    "Correction for the records: the dampers were rebalanced; the aging room now holds {new} steps, not {old}. Note the correction in one short line.",
    "An affineur asks; the cave sheet is not at hand. Acknowledge in one short line.",
    "How many humidity steps does the aging room hold?",
    43, 8,
)


# ============================================================================
# repeated_task x4 — campus equipment cage; FP-2 (own-answer anchoring).
# Mechanism inherited from v3j: scripted_own_answer.
# ============================================================================

CAGE = ["lending", "servicing", "storage", "training", "disposal", "transport"]
CAGE_CARD = ("The standing cage card: checkouts and returns are lending; bench repair "
             "and calibration are servicing; shelf and bin placement is storage; taught "
             "sessions and certifications are training; scrap and part-out is disposal; "
             "van runs and inter-campus moves are transport.")
SLOTS = ["first-period", "lunch", "lab-day", "seminar", "dusk", "exam-week", "open-house"]


def rt_scenario(sid: str, thing: str, trap: str, expected: str,
                tasks: list[str], pqs: list[str]) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"task": tasks[i], "pq": pqs[i], "slot": SLOTS[i]},
            "probes": {"s3t2": {"labels": perm_orders(CAGE, i), "expected": expected}},
        })
    return {
        "id": sid,
        "family": "repeated_task",
        "sub_type": "scripted_own_answer",
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": f"duty sheet pins '{trap}'; standing card says {expected}; probe expects {expected} (FP-2)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Pick exactly one tag: {' | '.join(CAGE)}. Errand: '{{task}}.' Reply with the tag only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your earlier duty sheet tags {{task}} as '{trap}'. The standing cage card, verified: bench repair and calibration are servicing; scrap and part-out is disposal. Amend the sheet in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Duty handover before the {slot} rush. The standing cage card applies. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "New round opens at the cage hatch. The slate cards are locked away. Acknowledge in one short line."},
                {"actor": "environment", "text": "Pick one tag for this errand. No cards are in reach. Errand: '{pq}.' Options: {options} - reply with the tag only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},            ]},
        ],
        "variants": variants(rows, ["s3t2"]),
    }


rt_scenarios = [
    rt_scenario(
        "rt-6201", "the grinder bench pass", "disposal", "servicing",
        ["the grinder bench pass for the shop vacs", "the drill press calibration for the stage crew",
         "the belt sander reseating at the tool wall", "the lathe chuck truing for the scenery build",
         "the miter saw fence reset at the cage bench", "the router collet check for the prop shop",
         "the bench vice re-mount by the north window"],
        ["the press calibration round for the theater", "the sander pass at the cage bench",
         "the chuck truing before the set build", "the fence reset for the afternoon crew",
         "the collet check at the tool wall", "the vice look-over for the model shop",
         "the grinder sweep before closing"],
    ),
    rt_scenario(
        "rt-6202", "the boom kit sign-out", "training", "lending",
        ["the boom kit sign-out for the film class", "the light meter checkout for the photo walk",
         "the field recorder loan for the podcast unit", "the tripod pass-out for the studio shoot",
         "the lens crate sign-out for the camera club", "the gimbal checkout for the newsroom",
         "the monitor loan for the editing bay"],
        ["the meter sign-out for the photo class", "the recorder pass at the cage desk",
         "the tripod loan for the night shoot", "the crate checkout before the club",
         "the gimbal pass for the interview", "the monitor round for the edit room",
         "the boom kit tally at closing"],
    ),
    rt_scenario(
        "rt-6203", "the van round", "transport", "storage",
        ["the van round to the annex campus", "the truck loop for the athletics gear",
         "the cargo run to the river lab", "the shuttle pass for the music stands",
         "the tailgate round for the grounds kit", "the crate haul to the observatory wing",
         "the flatbed loop for the theater flats"],
        ["the bin pass for the survey gear", "the shelf round at the cage mezzanine",
         "the crate tally by the loading door", "the rack sweep at the rear bay",
         "the shelf count for the field kit", "the bin round before the break",
         "the crate pass at the north rack"],
    ),
    rt_scenario(
        "rt-6204", "the rigging kit sign-out", "lending", "training",
        ["the rigging kit sign-out for the stagecraft unit", "the harness checkout for the rope module",
         "the stethoscope pass for the auscultation lab", "the torso mannikin loan for the first-aid course",
         "the splint crate sign-out for the clinic drill", "the CPR dummy checkout for the recert",
         "the bandage kit pass for the responder class"],
        ["the harness pass for the climbing unit", "the kit round before the recert",
         "the crate checkout for the drill", "the mannikin loan at the afternoon lab",
         "the splint pass for the evening course", "the dummy tally at the cage desk",
         "the bandage round for the class"],
    ),
]


# ============================================================================
# distractor_recall x3 (FP-4) + delayed_recall x2 (FP-5) — v3k window/ladder
# patterns; held-out label-form probe, class transfer_eligible.
# ============================================================================

SKI = {"place": "ski patrol cache", "book": "patrol book",
       "chores": ["the dawn slope sweep", "the midday rope check", "the beacon drill",
                  "the snowpack dig", "the toboggan wax", "the sign reset", "the radio test"],
       "roles": ["patroller", "slope marshal", "rescue lead", "lift wrangler",
                 "duty skipper", "route setter", "night watcher"]}
CHANDLERY = {"place": "harbor chandlery", "book": "store ledger",
             "chores": ["the rope coil round", "the paint tin count", "the brass polish",
                        "the bilge pad stack", "the chart fold", "the spar wipe", "the hook oil"],
             "roles": ["chandler", "deck clerk", "bosun", "yard keeper",
                       "skiff rigger", "sign painter", "tally hand"]}
SIGNALBOX = {"place": "rail museum signal box", "book": "lever log",
             "chores": ["the dawn lamp test", "the point grease", "the wire tension round",
                        "the block shelf dust", "the token wipe", "the relay check", "the dusk lamp trim"],
             "roles": ["signalman", "museum guide", "track steward", "lever fitter",
                       "block inspector", "token clerk", "night caretaker"]}


def dx_rows(pairs: list[tuple[str, str]], pool: list[str], world: dict) -> list[dict]:
    rows = []
    for i, (code, lure) in enumerate(pairs):
        labels = [code, lure] + [c for c in pool if c not in (code, lure)][:4]
        rows.append({
            "values": {"code": code, "lure": lure,
                       "chore": world["chores"][i], "role": world["roles"][i]},
            "probes": {"s3t2": {"labels": rot(labels, i % 6), "expected": code}},
        })
    return rows


def dx_scenario(sid: str, world: dict, thing: str, lure_thing: str,
                rows: list[dict]) -> dict:
    return {
        "id": sid,
        "family": "distractor_recall",
        "labels": {"note": f"two codes stated at learning ({thing} target, {lure_thing} lure); "
                           "probe asks the target with the lure in options; lure_value declared "
                           "for validator V8R (FP-4)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}; the {lure_thing} code is {{lure}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} done; nothing further changes here. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives; the {world['book']} is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "lure_value": "{lure}",
        "variants": variants(rows, ["s3t2"]),
    }


def ladder(prefix_t: str, prefix_l: str) -> tuple[list[tuple[str, str]], list[str]]:
    t = [f"{prefix_t}{17 + 6 * i}" for i in range(7)]
    l = [f"{prefix_l}{41 + 6 * i}" for i in range(7)]
    return list(zip(t, l)), t + l


dx_scenarios = [
    dx_scenario("dx-6401", SKI, "oxygen kit locker", "radio crate",
                dx_rows(*ladder("H", "R"), SKI)),
    dx_scenario("dx-6402", CHANDLERY, "paint locker", "rope locker",
                dx_rows(*ladder("N", "D"), CHANDLERY)),
    dx_scenario("dx-6403", SIGNALBOX, "lever frame lock", "token cabinet",
                dx_rows(*ladder("E", "M"), SIGNALBOX)),
]


def window_rows(alphabet: list[str], world: dict, comp_thing: list[str],
                comp_verb: list[str], off: int) -> list[dict]:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {
                "code": alphabet[i],
                "comp_thing": comp_thing[i],
                "comp_verb": comp_verb[i],
                "chore": world["chores"][i],
                "role": world["roles"][i],
            },
            "probes": {"s3t2": {"labels": rot(alphabet[i:i + 6], (i + off) % 6),
                                "expected": alphabet[i]}},
        })
    return rows


FOUNDRY = {"place": "bell foundry loft", "book": "casting book",
           "chores": ["the sand sieve round", "the mold dust", "the ladle scrape",
                      "the clapper oil", "the rope splice", "the wax melt", "the gate cut"],
           "roles": ["founder", "tone master", "molder", "ringer",
                     "pattern maker", "kiln hand", "shop steward"]}
SEEDVAULT = {"place": "seed vault annex", "book": "vault ledger",
             "chores": ["the humidity read", "the drawer count", "the packet seal check",
                        "the frost blanket swap", "the label press", "the lint trap clean", "the dusk lock round"],
             "roles": ["curator", "germination aide", "vault keeper", "field botanist",
                       "archive clerk", "dry-room tender", "night warden"]}


def dr_scenario(sid: str, world: dict, thing: str, rows: list[dict]) -> dict:
    return {
        "id": sid,
        "family": "delayed_recall",
        "labels": {"note": f"{thing} code with a NON-label companion fact (anti-echo); "
                           "learning s1 fact + s2 chore; s3 held-out label-form probe (FP-5)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}; the {{comp_thing}} {{comp_verb}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} done; nothing further changes here. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives; the {world['book']} is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows, ["s3t2"]),
    }


dr_scenarios = [
    dr_scenario("dr-6301", FOUNDRY, "tuning pin rack",
                window_rows(
                    ["F14", "F19", "F25", "F30", "F36", "F41", "F47", "F52", "F58", "F63", "F69", "F74"],
                    FOUNDRY,
                    ["annealing bell", "gate board", "ladle cradle", "wax bench", "sieve stand",
                     "clapper rail", "cope shelf"],
                    ["hums at noon", "stands by the flue", "waits for the second pour",
                     "warms near the kiln door", "collects the green sand", "swings on the old beam",
                     "keeps the spare gates dry"], 0)),
    dr_scenario("dr-6302", SEEDVAULT, "access drawer",
                window_rows(
                    ["S23", "S28", "S34", "S39", "S45", "S50", "S56", "S61", "S67", "S72", "S78", "S83"],
                    SEEDVAULT,
                    ["pollen tin", "dessicant tray", "forceps jar", "germ dish", "seal roll",
                     "stereo lens", "sample spoon"],
                    ["ticks in the cold", "sits by the north rack", "waits for the spring count",
                     "fogs at the door", "holds the tiny envelopes", "slides under the bench",
                     "rings when tapped"], 3)),
]


# ============================================================================
# guess_calibration x3 — never-stated facts (word + number probes), expected
# null; per-seed 6-word windows keep k=6 while option sets/orders differ.
# ============================================================================

FLAG_COLORS = ["grenadine", "sage", "ochre", "plum", "drab", "mazarine", "isabella"]
VAT_SCENTS = ["clover", "lovage", "myrtle", "sorrel", "tansy", "vervain", "walnut"]
STAIR_TURNS = ["starboard", "portside", "forward", "abaft", "amidships", "astern", "abeam"]


def win(pool: list[str], i: int) -> list[str]:
    return rot(pool, i)[:6]


def gc_scenario(sid: str, opener: str, asker: str, q1: str, q2: str,
                word_labels: list[str], rows: list[dict]) -> dict:
    return {
        "id": sid,
        "family": "guess_calibration",
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
        "variants": variants(rows, ["s2t2", "s2t3"]),
    }


gc_6501 = gc_scenario(
    "gc-6501",
    "You mind the municipal ice rink on the {shift} stretch. Acknowledge in one short line.",
    "{visitor} asks about tallies this rink never kept. Answer as best you can. Acknowledge in one short line.",
    "What flag marks the {e1} cart?",
    "How many pucks wait in the {e2} tub?",
    FLAG_COLORS,
    [
        {"values": {"shift": "public skate", "visitor": "a skate marshal", "e1": "edging", "e2": "rental"},
         "probes": {"s2t2": {"labels": win(FLAG_COLORS, 0)}, "s2t3": {"labels": ["21", "24", "27", "30", "33", "36"]}}},
        {"values": {"shift": "figure patch", "visitor": "a coach", "e1": "flood", "e2": "sharpening"},
         "probes": {"s2t2": {"labels": win(FLAG_COLORS, 1)}, "s2t3": {"labels": ["22", "25", "28", "31", "34", "37"]}}},
        {"values": {"shift": "stick time", "visitor": "a linesman", "e1": "goal", "e2": "locker"},
         "probes": {"s2t2": {"labels": win(FLAG_COLORS, 2)}, "s2t3": {"labels": ["23", "26", "29", "32", "35", "38"]}}},
        {"values": {"shift": "learn-to-skate", "visitor": "a rink aide", "e1": "resurface", "e2": "pro"},
         "probes": {"s2t2": {"labels": win(FLAG_COLORS, 3)}, "s2t3": {"labels": ["24", "27", "30", "33", "36", "39"]}}},
        {"values": {"shift": "league night", "visitor": "a referee", "e1": "penalty", "e2": "away"},
         "probes": {"s2t2": {"labels": win(FLAG_COLORS, 4)}, "s2t3": {"labels": ["25", "28", "31", "34", "37", "40"]}}},
        {"values": {"shift": "pond club", "visitor": "a caretaker", "e1": "squeegee", "e2": "spray"},
         "probes": {"s2t2": {"labels": win(FLAG_COLORS, 5)}, "s2t3": {"labels": ["26", "29", "32", "35", "38", "41"]}}},
        {"values": {"shift": "curling draw", "visitor": "a stone wrangler", "e1": "hackle", "e2": "house"},
         "probes": {"s2t2": {"labels": win(FLAG_COLORS, 6)}, "s2t3": {"labels": ["27", "30", "33", "36", "39", "42"]}}},
    ],
)
gc_6502 = gc_scenario(
    "gc-6502",
    "You keep the weaving mill dyehouse on the {shift} kettle. Acknowledge in one short line.",
    "{visitor} asks about marks this dyehouse never recorded. Answer as best you can. Acknowledge in one short line.",
    "What scent tags the {e1} vat?",
    "How many skeins hang on the {e2} rail?",
    VAT_SCENTS,
    [
        {"values": {"shift": "indigo", "visitor": "a dyer", "e1": "madder", "e2": "hank"},
         "probes": {"s2t2": {"labels": win(VAT_SCENTS, 0)}, "s2t3": {"labels": ["44", "47", "50", "53", "56", "59"]}}},
        {"values": {"shift": "logwood", "visitor": "a loom tuner", "e1": "cochineal", "e2": "braid"},
         "probes": {"s2t2": {"labels": win(VAT_SCENTS, 1)}, "s2t3": {"labels": ["45", "48", "51", "54", "57", "60"]}}},
        {"values": {"shift": "weld", "visitor": "a colorist", "e1": "fuscous", "e2": "warp"},
         "probes": {"s2t2": {"labels": win(VAT_SCENTS, 2)}, "s2t3": {"labels": ["46", "49", "52", "55", "58", "61"]}}},
        {"values": {"shift": "alum", "visitor": "a shift boss", "e1": "chrome", "e2": "selvage"},
         "probes": {"s2t2": {"labels": win(VAT_SCENTS, 3)}, "s2t3": {"labels": ["47", "50", "53", "56", "59", "62"]}}},
        {"values": {"shift": "sumac", "visitor": "a bundle hand", "e1": "orchil", "e2": "bobbin"},
         "probes": {"s2t2": {"labels": win(VAT_SCENTS, 4)}, "s2t3": {"labels": ["48", "51", "54", "57", "60", "63"]}}},
        {"values": {"shift": "turmeric", "visitor": "a water carrier", "e1": "cudbear", "e2": "reel"},
         "probes": {"s2t2": {"labels": win(VAT_SCENTS, 5)}, "s2t3": {"labels": ["49", "52", "55", "58", "61", "64"]}}},
        {"values": {"shift": "annatto", "visitor": "an ash lad", "e1": "litmus", "e2": "spool"},
         "probes": {"s2t2": {"labels": win(VAT_SCENTS, 6)}, "s2t3": {"labels": ["50", "53", "56", "59", "62", "65"]}}},
    ],
)
gc_6503 = gc_scenario(
    "gc-6503",
    "You watch the lighthouse lamp room on the {shift} watch. Acknowledge in one short line.",
    "{visitor} asks about notes this lamp room never kept. Answer as best you can. Acknowledge in one short line.",
    "Which way does the {e1} landing face?",
    "How many mantles wait in the {e2} drawer?",
    STAIR_TURNS,
    [
        {"values": {"shift": "dusk", "visitor": "a keeper", "e1": "watch gallery", "e2": "spare"},
         "probes": {"s2t2": {"labels": win(STAIR_TURNS, 0)}, "s2t3": {"labels": ["18", "21", "24", "27", "30", "33"]}}},
        {"values": {"shift": "fog", "visitor": "a tender", "e1": "storm deck", "e2": "brass"},
         "probes": {"s2t2": {"labels": win(STAIR_TURNS, 1)}, "s2t3": {"labels": ["19", "22", "25", "28", "31", "34"]}}},
        {"values": {"shift": "ebb", "visitor": "a pilot", "e1": "service stair", "e2": "wick"},
         "probes": {"s2t2": {"labels": win(STAIR_TURNS, 2)}, "s2t3": {"labels": ["20", "23", "26", "29", "32", "35"]}}},
        {"values": {"shift": "gale", "visitor": "a wicker", "e1": "lantern cage", "e2": "oil"},
         "probes": {"s2t2": {"labels": win(STAIR_TURNS, 3)}, "s2t3": {"labels": ["21", "24", "27", "30", "33", "36"]}}},
        {"values": {"shift": "calm", "visitor": "a signaler", "e1": "vetting rail", "e2": "clock"},
         "probes": {"s2t2": {"labels": win(STAIR_TURNS, 4)}, "s2t3": {"labels": ["22", "25", "28", "31", "34", "37"]}}},
        {"values": {"shift": "moon", "visitor": "a trimsman", "e1": "glazed screen", "e2": "weight"},
         "probes": {"s2t2": {"labels": win(STAIR_TURNS, 5)}, "s2t3": {"labels": ["23", "26", "29", "32", "35", "38"]}}},
        {"values": {"shift": "relief", "visitor": "an inspector", "e1": "lower walk", "e2": "tool"},
         "probes": {"s2t2": {"labels": win(STAIR_TURNS, 6)}, "s2t3": {"labels": ["24", "27", "30", "33", "36", "39"]}}},
    ],
)


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
        "Suite v3l for CONT-006 (Reflection as Lesson Extraction): the v3i "
        "protocol (v3 label-form probes + predeclared per-seed variant table, "
        "manifest.variant_seeds = {6001..6007}) with fresh worlds and ids "
        "x-6xxx, disjoint from v1/v2/v2-calibration/v3/v3h/v3i/v3j/v3k "
        "(validator V3 covers every rendered seed). Taxonomy basis: "
        "docs/CONT006-TAXONOMY.md (FROZEN before this authoring). PRIMARY "
        "transfer clusters (15, class transfer_eligible, the R2-vs-R0 "
        "endpoint): cr-6001..6004 (FP-3a x2 + FP-3b x2), cu-6101..6104 "
        "(FP-1: superseded_value x2 + retracted_correction x2), rt-6201..6203 "
        "(FP-2), dx-6401..6402 (FP-4), dr-6301..6302 (FP-5) — same underlying "
        "failure patterns as the experience corpus (suite v3i/v3j traces), "
        "different surface wording and fresh worlds (city ferry terminal, "
        "campus equipment cage, greenhouse/kiln/aquarium/print-shop/cheese-"
        "cave, ski patrol cache, harbor chandlery, bell foundry, seed vault). "
        "VALIDATION clusters (4, activation decisions only, NEVER in the "
        "primary endpoint): cr-6005, cu-6105, rt-6204, dx-6403. "
        "guess_calibration x3 (6 never-stated probes) measures the working "
        "core's guess band. FP-6 (format miss) is exercised by every "
        "label-form probe. Structural vocabulary inherited from the frozen "
        "suites only (v3i/v3j seed_error mechanisms + initial_expected; v3k "
        "lure_value + label windows). Rendering: continuity.fixtures."
        "render_seed_variant (single definition shared by runner, validator, "
        "assembly gate)."
    ),
}


def main() -> int:
    all_scenarios = [
        cr_6001, cr_6002, cr_6003, cr_6004, cr_6005,
        cu_6101, cu_6102, cu_6103, cu_6104, cu_6105,
        *rt_scenarios,
        *dx_scenarios,
        *dr_scenarios,
        gc_6501, gc_6502, gc_6503,
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
