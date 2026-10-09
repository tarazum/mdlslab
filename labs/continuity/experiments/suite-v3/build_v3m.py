"""Deterministic builder for fixture suite v3m (CONT-006 rethink, owner-directed 2026-10-09).

Fresh suite per the rethink reviews (REVIEW-FABLE-CONT006 C.6,
REVIEW-CONT006-CN012-RERUN): v3l is NOT reusable for a confirmatory
endpoint because the rethink decisions are informed by v3l per-cluster
results — v3m restores a clean test surface. Same composition as v3l
(15 TR primary + 4 VAL + 3 GC; every taxonomy class >= 2 primary
clusters), same INHERITED structural mechanics (v3i/v3j seed_error
mechanisms + initial_expected; v3k lure_value + label windows), NEW
worlds, ids x-7xxx, seeds {7001..7007}.

Difficulty intent (design-time, from the C2 memory-armed baselines — NOT
from v3l results, which were memoryless and uninterpretable): aim each
family mid-band for a memory-on agent (C2 T-arms: cr ~0.3-0.5, cu ~0.6-0.8,
rt ~0.25-0.45, dx/dr high); the calibration pilot verifies the bands with
memory ON before freeze (out of band -> a NEW suite, never a v3m edit).

Deterministic: no RNG, explicit tables only. Re-running overwrites
fixtures/v3m byte-identically.
"""

from __future__ import annotations

import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = LAB_ROOT / "fixtures" / "v3m"
SEEDS = [7001, 7002, 7003, 7004, 7005, 7006, 7007]

VALIDATION_IDS = ["cr-7005", "cu-7105", "rt-7204", "dx-7403"]


def rot(seq: list[str], k: int) -> list[str]:
    n = len(seq)
    return [seq[(i + k) % n] for i in range(n)]


def perm_orders(vocab: list[str], i: int) -> list[str]:
    """7 pairwise-distinct label orders over a FIXED 6-word vocabulary
    (6 rotations + a transposition of the identity; same device as v3l)."""
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
# correction_reuse x5 — city tram depot control room; vocab fixed.
# ============================================================================

TRAM = ["signaling", "traction", "tickets", "trackwork", "deposits", "rostering"]
TRAM_CARD = ("The standing depot card: signal faults and interlocking replies are "
             "signaling; power rail and pantograph matters are traction; fare sheets "
             "and pass issues are tickets; sleeper and switch repairs are trackwork; "
             "cash bags and fare floats are deposits; crew changes and shift swaps "
             "are rostering.")
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def cr_variants(bks: list[str], pqs: list[str], expected: str) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"bk": bks[i], "pq": pqs[i], "day": DAYS[i]},
            "probes": {"s3t2": {"labels": perm_orders(TRAM, i), "expected": expected}},
        })
    return variants(rows)


def cr_vce_vct(sid: str, sub: str, thing: str, note: str, corr: str,
               expected: str, trap: str, bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": sub,
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"File this report under exactly one label: {' | '.join(TRAM)}. Report: '{{bk}} {thing}.' Reply with the label only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your control-room log from the previous shift files {{bk}} {thing} under '{trap}'. Keep the log line in view and acknowledge in one short line."},
                {"actor": "environment", "text": TRAM_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr + " Amend your records in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Night desk at the tram depot on {day}. The depot card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"File this report. The depot card is not at hand. Report: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected),
    }


cr_7001 = cr_vce_vct(
    "cr-7001", "valid_correction_environment", "on the morning sheet",
    "point-fault reply logged 'tickets'; verified control notice re-routes to signaling (FP-3a)",
    "Control-room bulletin, verified notice from the network office: the log line filing "
    "{bk} under 'tickets' is out of date; interlocking and signal-board replies for it "
    "are signaling under the standing card.",
    "signaling", "tickets",
    ["the points fault at the east crossover", "the signal lamp outage near the museum loop",
     "the interlocking reply for the depot throat", "the board reset after the platform overrun",
     "the track-circuit flicker by the sorting siding", "the crossing-bell fault at the mill bridge",
     "the axle-counter trip on the north chord"],
    ["the lamp test for the night circuit", "the board check after the depot shunt",
     "the points round before the first tram", "the signal sweep at the museum stop",
     "the crossing tally at the goods gate", "the circuit look-over for the school run",
     "the bell pass by the canal bridge"],
)

cr_7002 = cr_vce_vct(
    "cr-7002", "valid_correction_tool", "on the works list",
    "sleeper gang note logged 'traction'; service-verified works terminal re-routes to trackwork (FP-3a)",
    "The works terminal, service-verified this morning, reads {bk} as sleeper-and-switch "
    "repair: trackwork under the standing card; the old 'traction' filing is out of date.",
    "trackwork", "traction",
    ["the sleeper gang note for the river curve", "the switch grease round at the depot exit",
     "the ballast top-up near the coal siding", "the blade change on the west points",
     "the crossing renewal at the market street", "the rail swap on the goods chord",
     "the tamper pass by the old engine shed"],
    ["the sleeper tally at the river curve", "the switch round before the works tram",
     "the ballast check near the coal gate", "the blade look-over on the west lead",
     "the crossing count at market street", "the rail survey on the goods loop",
     "the tamper sweep by the engine shed"],
)


def cr_euc(sid: str, note: str, insist: str, expected: str, trap: str,
           bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": "erroneous_user_correction",
        "seed_error": {"value": trap, "mechanism": "user_override"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"File this report under exactly one label: {' | '.join(TRAM)}. Report: '{{bk}}.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": TRAM_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": insist + " Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Night desk at the tram depot on {day}. The depot card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"File this report. The depot card is not at hand. Report: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected),
    }


cr_7003 = cr_euc(
    "cr-7003",
    "fare-float pickup correctly 'deposits'; walk-up clerk pushes 'tickets' (FP-3b)",
    "A walk-up clerk insists about {bk}: 'that is just my fare paperwork - run it through "
    "as tickets, the old desk always did.' The float register, on file, keeps the pickup "
    "as it stands.",
    "deposits", "tickets",
    ["the fare-float pickup for the riverside terminus", "the cash bag round for the market trams",
     "the change delivery to the hill depot", "the float seal swap at the museum stop",
     "the coin count for the evening service", "the bag handover on the night circuit",
     "the float top-up before the festival run"],
    ["the float pickup at the riverside desk", "the bag round for the first market tram",
     "the change run to the hill stop", "the seal check at the museum terminus",
     "the coin tally for the dusk service", "the handover on the late circuit",
     "the top-up before the Sunday run"],
)


def cr_sc(sid: str, note: str, verified: str, unreviewed: str, expected: str,
          trap: str, bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": "source_conflict",
        "seed_error": {"value": trap, "mechanism": "source_conflict"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"File this report under exactly one label: {' | '.join(TRAM)}. Report: '{{bk}} on the watch sheet.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": TRAM_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": verified + " Note it in one short line."},
                {"actor": "environment", "source_type": "environment", "text": unreviewed},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Night desk at the tram depot on {day}. The depot card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"File this report. The depot card is not at hand. Report: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected),
    }


cr_7004 = cr_sc(
    "cr-7004",
    "pantograph check correctly 'traction'; unreviewed depot chat claims move to 'trackwork' (FP-3b)",
    "The depot office forwards the inspector's notice; the network verified it: pantograph "
    "and power-rail checks stay with traction matters, and {bk} remains as the card has it.",
    "An unreviewed depot chat channel claims every pantograph check, {bk} included, was "
    "moved to the sleeper works today.",
    "traction", "trackwork",
    ["the pantograph check for the morning express", "the power-rail walk on the elevated chord",
     "the shoe swap on the depot pilot", "the horn current test for the riverside run",
     "the roof gauge pass at the museum loop", "the pantograph raise after the night frost",
     "the rail earth check by the sorting yard"],
    ["the pantograph round for the dusk trams", "the power-rail tally on the chord",
     "the shoe look-over for the depot pilot", "the horn test at the riverside stop",
     "the gauge pass before the school run", "the raise check after the frost",
     "the earth survey by the sorting gate"],
)

cr_7005 = cr_sc(
    "cr-7005",
    "VAL cluster (activation only): crew swap correctly 'rostering'; unreviewed pinned snapshot claims 'signaling' (FP-3b)",
    "The roster clerk's memo, depot-verified: crew-change entries stay with rostering, "
    "and {bk} stays as the card has it.",
    "An unreviewed pinned snapshot by the crew door claims the swap entries, {bk} "
    "included, were moved to the signal board today.",
    "rostering", "signaling",
    ["the spare-driver swap for the evening service", "the guard change on the market run",
     "the shift handover for the hill depot", "the relief conductor entry for the festival trams",
     "the night-driver callout for the riverside circuit", "the apprentice swap at the museum loop",
     "the weekend crew listing for the goods chord"],
    ["the driver swap at the dusk change", "the guard round on the first market tram",
     "the handover at the hill desk", "the conductor entry before the festival",
     "the callout on the night circuit", "the apprentice check at the loop",
     "the crew tally for the goods run"],
)


# ============================================================================
# contradiction_update x5 — FP-1 (2 superseded + 2 retracted TR, 1 VAL).
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


cu_7101 = cu_superseded(
    "cu-7101",
    "ropewalk hemp line strands corrected; probe expects NEW value (FP-1)",
    "You keep the ropewalk notes. For the log: the hemp line lays {old} strands per twist. Acknowledge in one short line.",
    "Correction for the records: the strand guides were re-cut; the hemp line now lays {new} strands per twist, not {old}. Note the correction in one short line.",
    "A rope mate asks; the ropewalk sheet is away. Acknowledge in one short line.",
    "How many strands does the hemp line lay per twist?",
    52, 7,
)
cu_7102 = cu_superseded(
    "cu-7102",
    "village pump house valve turns corrected; probe expects NEW value (FP-1)",
    "You mind the pump house sheet. For the log: the inlet valve takes {old} turns to close. Acknowledge in one short line.",
    "Correction for the records: the spindle was re-seated; the inlet valve now takes {new} turns, not {old}. Note the correction in one short line.",
    "A bailiff asks; the pump house card is away. Acknowledge in one short line.",
    "How many turns does the inlet valve take?",
    23, 5,
)
cu_7103 = cu_retracted(
    "cu-7103",
    "mountain hut stove flue corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You tend the mountain hut records. For the log: the stove flue opens {old} turns for the night. Acknowledge in one short line.",
    "Correction for the records: the damper was rebuilt; the stove flue opens {new} turns, not {old}. Note the correction in one short line.",
    "The warden says the correction is withdrawn: the rebuild slip belonged to the lower hut and does not apply here; the standing setting from the first log holds as before. Amend in one short line.",
    "A walking guide asks; the hut sheet is away. Acknowledge in one short line.",
    "How many turns does the stove flue open?",
    41, 4,
)
cu_7104 = cu_retracted(
    "cu-7104",
    "tannery soak pit hide count corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You run the tannery tally. For the log: the soak pit takes {old} hides per load. Acknowledge in one short line.",
    "Correction for the records: the hide clerk re-counted; the soak pit takes {new} hides per load, not {old}. Note the correction in one short line.",
    "The foreman says the correction is withdrawn: the re-count slip was a draft from the bark store and does not apply; the standing count from the first log holds as before. Amend in one short line.",
    "A hide sorter asks; the tannery card is away. Acknowledge in one short line.",
    "How many hides does the soak pit take per load?",
    16, 6,
)
cu_7105 = cu_superseded(
    "cu-7105",
    "VAL cluster (activation only): windmill brake clicks corrected; probe expects NEW (FP-1)",
    "You mind the windmill log. For the log: the brake takes {old} clicks to seat. Acknowledge in one short line.",
    "Correction for the records: the pawl was replaced; the brake now takes {new} clicks, not {old}. Note the correction in one short line.",
    "A sweeps mate asks; the windmill tally is away. Acknowledge in one short line.",
    "How many clicks does the brake take?",
    33, 8,
)


# ============================================================================
# repeated_task x4 — campus print-room counter; FP-2.
# ============================================================================

PRINT = ["laminating", "binding", "copying", "finishing", "scanning", "delivery"]
PRINT_CARD = ("The standing counter card: pouch and film sealing is laminating; spine and "
              "staple assembly is binding; plate and drum runs are copying; trim, fold and "
              "pack work is finishing; sheet feed and capture jobs are scanning; courier "
              "and post runs are delivery.")
SLOTS = ["morning", "lecture", "lunch", "seminar", "afternoon", "deadline", "open-house"]


def rt_scenario(sid: str, trap: str, expected: str,
                tasks: list[str], pqs: list[str]) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"task": tasks[i], "pq": pqs[i], "slot": SLOTS[i]},
            "probes": {"s3t2": {"labels": perm_orders(PRINT, i), "expected": expected}},
        })
    return {
        "id": sid, "family": "repeated_task", "sub_type": "scripted_own_answer",
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": f"counter sheet pins '{trap}'; standing card says {expected}; probe expects {expected} (FP-2)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Pick exactly one tag: {' | '.join(PRINT)}. Errand: '{{task}}.' Reply with the tag only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your earlier counter sheet tags {{task}} as '{trap}'. The standing counter card, verified: spine and staple assembly is binding; pouch and film sealing is laminating. Amend the sheet in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Counter handover before the {slot} rush. The standing counter card applies. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "New round opens at the counter hatch. The slate cards are locked away. Acknowledge in one short line."},
                {"actor": "environment", "text": "Pick one tag for this errand. No cards are in reach. Errand: '{pq}.' Options: {options} - reply with the tag only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows),
    }


rt_scenarios = [
    rt_scenario(
        "rt-7201", "disposal" if False else "delivery", "finishing",
        ["the poster trim batch for the physics corridor", "the fold-and-pack run for the open day",
         "the zine trim round for the literature stall", "the booklet fold batch at the north bench",
         "the poster roll pack for the careers fair", "the leaflet trim for the union table",
         "the folder crease run for the architecture show"],
        ["the trim pass for the corridor posters", "the fold round before the open day",
         "the zine cut at the literature stall", "the booklet fold for the seminar packs",
         "the roll pack at the careers desk", "the leaflet trim for the union",
         "the crease run before the show"],
    ),
    rt_scenario(
        "rt-7202", "scanning", "copying",
        ["the thesis plate run for the history office", "the drum pass for the exam scripts",
         "the plate round for the maps annex", "the proof run for the press room",
         "the drum batch for the admissions mail", "the plate sweep for the library sets",
         "the proof pass for the yearbook"],
        ["the plate run for the history office", "the drum check for the scripts",
         "the round at the maps annex", "the proof print at the press room",
         "the batch for admissions", "the sweep for the library sets",
         "the pass before the yearbook"],
    ),
    rt_scenario(
        "rt-7203", "finishing", "binding",
        ["the zine spine batch for the fair", "the staple run for the course packs",
         "the spine round for the repair shelf", "the sewn quire batch for the archive",
         "the staple pass at the east bench", "the spine tape run for the music library",
         "the coil batch for the lab manuals"],
        ["the spine batch at the fair desk", "the staple run for the packs",
         "the round on the repair shelf", "the quire sew for the archive",
         "the pass at the east bench", "the tape run for the music desk",
         "the coil count for the manuals"],
    ),
    rt_scenario(
        "rt-7204", "copying", "laminating",
        ["the map pouch run for the field course", "the film seal batch for the registers",
         "the pouch round for the lab charts", "the ID card sealing for the new intake",
         "the film pass for the duty rosters", "the pouch batch for the gym passes",
         "the seal run for the noticeboards"],
        ["the pouch run for the field kits", "the seal batch at the register desk",
         "the round for the lab charts", "the card sealing for intake",
         "the pass for the rosters", "the batch for the gym desk",
         "the seal count for the boards"],
    ),
]


# ============================================================================
# distractor_recall x3 (FP-4) + delayed_recall x2 (FP-5) — v3k patterns.
# ============================================================================

AQUARIUM = {"place": "town aquarium back office", "book": "feed log",
            "chores": ["the dawn glass wipe", "the pump strainer rinse", "the salt mix round",
                       "the kelp trim", "the hood light check", "the bucket scrub", "the dusk top-off"],
            "roles": ["keeper", "aquarist", "filter tender", "ticket lead",
                      "diver", "curator", "night watcher"]}
LODGE = {"place": "ski lodge gear room", "book": "gear ledger",
         "chores": ["the boot dry rack", "the pole strap check", "the wax bench tidy",
                    "the helmet shelf wipe", "the binding gauge round", "the glove bin sort", "the evening stove fill"],
         "roles": ["lift operator", "patroller", "boot fitter", "night porter",
                   "instructor", "shuttle driver", "gear steward"]}
HANGAR = {"place": "gliding club hangar", "book": "rigging book",
          "chores": ["the wing cover round", "the tire pressure check", "the canopy polish",
                     "the tail dolly grease", "the rope coil tidy", "the pitot cover swap", "the dusk tie-down"],
          "roles": ["duty pilot", "winch driver", "rigger", "cadet lead",
                    "instructor", "hangar keeper", "night watchman"]}


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
        "id": sid, "family": "distractor_recall",
        "labels": {"note": f"two codes stated at learning ({thing} target, {lure_thing} lure); "
                           "probe asks the target with the lure in options; lure_value declared "
                           "for validator V8R (FP-4)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}; the {lure_thing} code is {{lure}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} finished; all else stands as before. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives; the {world['book']} is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "lure_value": "{lure}",
        "variants": variants(rows),
    }


def ladder(prefix_t: str, prefix_l: str) -> tuple[list[tuple[str, str]], list[str]]:
    t = [f"{prefix_t}{13 + 6 * i}" for i in range(7)]
    l = [f"{prefix_l}{47 + 6 * i}" for i in range(7)]
    return list(zip(t, l)), t + l


dx_scenarios = [
    dx_scenario("dx-7401", AQUARIUM, "pump room locker", "kitchen crate",
                dx_rows(*ladder("T", "Q"), AQUARIUM)),
    dx_scenario("dx-7402", LODGE, "avalanche locker", "boot cabinet",
                dx_rows(*ladder("V", "B"), LODGE)),
    dx_scenario("dx-7403", HANGAR, "parachute rack", "trailer box",
                dx_rows(*ladder("X", "G"), HANGAR)),
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


MINT = {"place": "old mint assay room", "book": "assay book",
        "chores": ["the scale zero check", "the crucible brush", "the drawer count",
                   "the flux tin shake", "the tray polish", "the weight set wipe", "the dusk lock round"],
        "roles": ["assayer", "melter", "clerk", "guard",
                  "polisher", "apprentice", "night warden"]}
APIARY = {"place": "farm apiary shed", "book": "hive ledger",
          "chores": ["the smoker fuel fill", "the frame lift round", "the veil wash",
                     "the feeder mix", "the entrance reducer check", "the wax box tidy", "the dusk strap pass"],
          "roles": ["beekeeper", "farm hand", "inspector", "helper",
                    "honey packer", "student", "night watch"]}


def dr_scenario(sid: str, world: dict, thing: str, rows: list[dict]) -> dict:
    return {
        "id": sid, "family": "delayed_recall",
        "labels": {"note": f"{thing} code with a NON-label companion fact (anti-echo); "
                           "learning s1 fact + s2 chore; s3 held-out label-form probe (FP-5)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}; the {{comp_thing}} {{comp_verb}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} finished; all else stands as before. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives; the {world['book']} is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows),
    }


dr_scenarios = [
    dr_scenario("dr-7301", MINT, "bullion drawer",
                window_rows(
                    ["K19", "K24", "K30", "K35", "K41", "K46", "K52", "K57", "K63", "K68", "K74", "K79"],
                    MINT,
                    ["ingot tray", "crucible rack", "flux pot", "weight box", "tongs rail",
                     "mould shelf", "punch case"],
                    ["warms by the furnace", "sits by the pour bench", "waits for the evening melt",
                     "gathers dust under the hood", "clicks when the door swings", "hangs by the ledger desk",
                     "keeps the spare gates dry"], 0)),
    dr_scenario("dr-7302", APIARY, "queen cage drawer",
                window_rows(
                    ["P27", "P32", "P38", "P43", "P49", "P54", "P60", "P65", "P71", "P76", "P82", "P87"],
                    APIARY,
                    ["smoker bellows", "hive tool tin", "veil peg", "feeder jar", "wax block",
                     "queen cage rack", "glove clip"],
                    ["hisses when lit", "sits by the door", "waits for the spring round",
                     "fogs in the cold", "rings when tapped", "slips on the shelf edge",
                     "holds the tiny tacks"], 3)),
]


# ============================================================================
# guess_calibration x3 — never-stated facts (word + number), fresh pools.
# ============================================================================

ROPE_TWINE = ["jute", "sisal", "hemp", "coir", "manila", "flax", "cotton"]
BIRD_CALLS = ["churr", "tsweet", "peep", "trill", "chirr", "warble", "tseet"]
SLATE_GREYS = ["ashen", "dove", "charcoal", "graphite", "pearl", "pewter", "stone"]


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


gc_7501 = gc_scenario(
    "gc-7501",
    "You mind the boatyard rigging loft on the {shift} stretch. Acknowledge in one short line.",
    "{visitor} asks about tallies this loft never kept. Answer as best you can. Acknowledge in one short line.",
    "What twine wraps the {e1} splice?",
    "How many fathom coils wait in the {e2} bin?",
    ROPE_TWINE,
    [
        {"values": {"shift": "haul-out", "visitor": "a rigger", "e1": "jib", "e2": "tar"},
         "probes": {"s2t2": {"labels": win(ROPE_TWINE, 0)}, "s2t3": {"labels": ["31", "34", "37", "40", "43", "46"]}}},
        {"values": {"shift": "varnish", "visitor": "a boatwright", "e1": "main", "e2": "splicing"},
         "probes": {"s2t2": {"labels": win(ROPE_TWINE, 1)}, "s2t3": {"labels": ["32", "35", "38", "41", "44", "47"]}}},
        {"values": {"shift": "tide-work", "visitor": "a tender", "e1": "mizzen", "e2": "spare"},
         "probes": {"s2t2": {"labels": win(ROPE_TWINE, 2)}, "s2t3": {"labels": ["33", "36", "39", "42", "45", "48"]}}},
        {"values": {"shift": "lay-day", "visitor": "a keeper", "e1": "staysail", "e2": "drying"},
         "probes": {"s2t2": {"labels": win(ROPE_TWINE, 3)}, "s2t3": {"labels": ["34", "37", "40", "43", "46", "49"]}}},
        {"values": {"shift": "launch day", "visitor": "a haulmaster", "e1": "spanker", "e2": "oakum"},
         "probes": {"s2t2": {"labels": win(ROPE_TWINE, 4)}, "s2t3": {"labels": ["35", "38", "41", "44", "47", "50"]}}},
        {"values": {"shift": "survey", "visitor": "an usher", "e1": "gaff", "e2": "chain"},
         "probes": {"s2t2": {"labels": win(ROPE_TWINE, 5)}, "s2t3": {"labels": ["36", "39", "42", "45", "48", "51"]}}},
        {"values": {"shift": "winter lay", "visitor": "a ferryman", "e1": "whisker", "e2": "laid-up"},
         "probes": {"s2t2": {"labels": win(ROPE_TWINE, 6)}, "s2t3": {"labels": ["37", "40", "43", "46", "49", "52"]}}},
    ],
)
gc_7502 = gc_scenario(
    "gc-7502",
    "You keep the marsh field station on the {shift} watch. Acknowledge in one short line.",
    "{visitor} asks about notes this station never kept. Answer as best you can. Acknowledge in one short line.",
    "What call marks the {e1} hide?",
    "How many nest boxes line the {e2} path?",
    BIRD_CALLS,
    [
        {"values": {"shift": "dawn", "visitor": "a warden", "e1": "reed", "e2": "boardwalk"},
         "probes": {"s2t2": {"labels": win(BIRD_CALLS, 0)}, "s2t3": {"labels": ["28", "31", "34", "37", "40", "43"]}}},
        {"values": {"shift": "high tide", "visitor": "a ringer", "e1": "mudflat", "e2": "causeway"},
         "probes": {"s2t2": {"labels": win(BIRD_CALLS, 1)}, "s2t3": {"labels": ["29", "32", "35", "38", "41", "44"]}}},
        {"values": {"shift": "dusk", "visitor": "a counter", "e1": "saltings", "e2": "track"},
         "probes": {"s2t2": {"labels": win(BIRD_CALLS, 2)}, "s2t3": {"labels": ["30", "33", "36", "39", "42", "45"]}}},
        {"values": {"shift": "gale", "visitor": "a surveyor", "e1": "scrape", "e2": "dike"},
         "probes": {"s2t2": {"labels": win(BIRD_CALLS, 3)}, "s2t3": {"labels": ["31", "34", "37", "40", "43", "46"]}}},
        {"values": {"shift": "frost", "visitor": "a photographer", "e1": "pit", "e2": "gate"},
         "probes": {"s2t2": {"labels": win(BIRD_CALLS, 4)}, "s2t3": {"labels": ["32", "35", "38", "41", "44", "47"]}}},
        {"values": {"shift": "fog", "visitor": "a bailiff", "e1": "screen", "e2": "sluice"},
         "probes": {"s2t2": {"labels": win(BIRD_CALLS, 5)}, "s2t3": {"labels": ["33", "36", "39", "42", "45", "48"]}}},
        {"values": {"shift": "moon", "visitor": "a logger", "e1": "tower", "e2": "hinge"},
         "probes": {"s2t2": {"labels": win(BIRD_CALLS, 6)}, "s2t3": {"labels": ["34", "37", "40", "43", "46", "49"]}}},
    ],
)
gc_7503 = gc_scenario(
    "gc-7503",
    "You mind the quarry slate store on the {shift} stint. Acknowledge in one short line.",
    "{visitor} asks about tallies this store never kept. Answer as best you can. Acknowledge in one short line.",
    "What grey dresses the {e1} stack?",
    "How many slabs lean on the {e2} rack?",
    SLATE_GREYS,
    [
        {"values": {"shift": "first cut", "visitor": "a splitter", "e1": "roofing", "e2": "dressing"},
         "probes": {"s2t2": {"labels": win(SLATE_GREYS, 0)}, "s2t3": {"labels": ["52", "55", "58", "61", "64", "67"]}}},
        {"values": {"shift": "haul", "visitor": "a driver", "e1": "flooring", "e2": "trimming"},
         "probes": {"s2t2": {"labels": win(SLATE_GREYS, 1)}, "s2t3": {"labels": ["53", "56", "59", "62", "65", "68"]}}},
        {"values": {"shift": "split", "visitor": "a foreman", "e1": "walling", "e2": "punching"},
         "probes": {"s2t2": {"labels": win(SLATE_GREYS, 2)}, "s2t3": {"labels": ["54", "57", "60", "63", "66", "69"]}}},
        {"values": {"shift": "dress", "visitor": "a sampler", "e1": "flag", "e2": "grading"},
         "probes": {"s2t2": {"labels": win(SLATE_GREYS, 3)}, "s2t3": {"labels": ["55", "58", "61", "64", "67", "70"]}}},
        {"values": {"shift": "load", "visitor": "a weigher", "e1": "lintel", "e2": "boxing"},
         "probes": {"s2t2": {"labels": win(SLATE_GREYS, 4)}, "s2t3": {"labels": ["56", "59", "62", "65", "68", "71"]}}},
        {"values": {"shift": "blast", "visitor": "a shot-firer", "e1": "sill", "e2": "cradle"},
         "probes": {"s2t2": {"labels": win(SLATE_GREYS, 5)}, "s2t3": {"labels": ["57", "60", "63", "66", "69", "72"]}}},
        {"values": {"shift": "close", "visitor": "a caretaker", "e1": "coping", "e2": "pallet"},
         "probes": {"s2t2": {"labels": win(SLATE_GREYS, 6)}, "s2t3": {"labels": ["58", "61", "64", "67", "70", "73"]}}},
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
        "Suite v3m for the CONT-006 RETHINK (owner-directed 2026-10-09; "
        "REVIEW-FABLE-CONT006 C.6 + REVIEW-CONT006-CN012-RERUN): a FRESH "
        "confirmatory surface — the rethink decisions are informed by v3l "
        "per-cluster results, so v3l cannot serve as the new endpoint. "
        "Composition identical to v3l (15 TR primary transfer clusters of "
        "class transfer_eligible + 4 VAL activation-only + GC x3; every "
        "taxonomy class >= 2 primary clusters), mechanics INHERITED from the "
        "frozen suites only (v3i/v3j seed_error mechanisms + "
        "initial_expected; v3k lure_value + label windows), fresh worlds "
        "(tram depot control room, print-room counter, ropewalk/pump "
        "house/mountain hut/tannery/windmill, aquarium/ski lodge/"
        "gliding hangar, mint assay room, apiary shed, rigging loft/marsh "
        "station/slate store), ids x-7xxx, seeds {7001..7007}, disjoint "
        "from ALL prior suites (validator V3 every seed both ways + V18 "
        "world-freshness: cross-suite rare-vocabulary and opening-phrase "
        "overlap; K-2 fold of REVIEW-FABLE-CONT006-V2 — the first cut "
        "reused the planetarium (v3h) and pottery-kiln (v3l) worlds). "
        "Design-time difficulty intent: C2 memory-armed family bands (the "
        "calibration pilot verifies with memory ON before freeze; out of "
        "band -> a NEW suite, never a v3m edit). Rendering: "
        "continuity.fixtures.render_seed_variant."
    ),
}


def main() -> int:
    all_scenarios = [
        cr_7001, cr_7002, cr_7003, cr_7004, cr_7005,
        cu_7101, cu_7102, cu_7103, cu_7104, cu_7105,
        *rt_scenarios,
        *dx_scenarios,
        *dr_scenarios,
        gc_7501, gc_7502, gc_7503,
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
