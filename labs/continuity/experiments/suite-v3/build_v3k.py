"""Deterministic builder for fixture suite v3k (CONT-002 state transfer).

Emits fixtures/v3k: 18 scenarios under fixture protocol v3i (v3 protocol +
predeclared per-seed variant table), NEW predeclared seeds {5001..5007}, ids
x-5xxx, fresh worlds (mountain cable-car stations, university chemistry
stockroom, theater props loft, quarry weighbridge office; gc: orchard packing
shed, brewery cellar, observatory dome) — rendered turn texts disjoint from
v1/v2/v2-cal/v3/v3h/v3i/v3j (validator V3 covers every seed both ways).

CONT-002 design basis (docs/CONT-002-DESIGN.md): PRIMARY = delayed_recall x7
+ distractor_recall x8 (15 clusters). Family rationale: cycles 1-2 measured
the largest, cleanest memory benefit on DR/DX (pass ~1.0 with memory vs
0.13-0.15 without) — the R = dB/dA denominator stays far from zero by
construction — and the probe tests storage, not core-specific
conflict-resolution policy (CR/CU/RT are absent; memory-can-hurt transfer is
a different question, out of scope). SIZING: 15 clusters x 7 seeds is the
power_calc_cont002.py outcome (K12x5 detection power 0.604 at MME R 0.25 —
undersized; K15x7 = 0.801 conservative row, template section 6 bar).

Scenario shape serves the 2x2: s1 = learning fact(s), s2 = learning chore,
s3 = HELD-OUT probe session (label-form, k=6, class transfer_eligible) —
the state is learned ONCE per seed on core A (s1+s2) and the SAME exported
state is probed in all four cells (A+restored / A+clean / B+restored /
B+clean).

guess_calibration x3 (secondary, never-stated facts, 6 probes) stays: the
prereg template section 9 guess band is measured on BOTH cores.

Deterministic: no RNG, explicit tables only. Re-running overwrites
fixtures/v3k byte-identically.
"""

from __future__ import annotations

import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = LAB_ROOT / "fixtures" / "v3k"
SEEDS = [5001, 5002, 5003, 5004, 5005, 5006, 5007]


def rot(seq: list[str], k: int) -> list[str]:
    n = len(seq)
    return [seq[(i + k) % n] for i in range(n)]


def variants_value_sets(rows: list[dict], offset: int, probe_refs: list[str]) -> dict:
    """rows: one per seed, each {'values': {...}, 'probes': {ref: {labels, expected}}}.
    Authored label lists are order-rotated per seed (validator V5/V16).
    """
    out = {}
    for i, sd in enumerate(SEEDS):
        k = (i + offset) % 6
        probes = {
            ref: ({"labels": rot(spec["labels"], k), "expected": spec["expected"]}
                  if spec.get("expected") is not None
                  else {"labels": rot(spec["labels"], k)})
            for ref, spec in rows[i]["probes"].items()
        }
        out[str(sd)] = {"values": rows[i]["values"], "probes": probes}
    return out


def write_scenario(rel: str, scenario: dict) -> None:
    path = OUT_DIR / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(scenario, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")


# ============================================================================
# delayed_recall x7 (primary) — learning: code + NON-label companion fact
# (anti-echo kept from cycle 1); chore turn; held-out label-form probe.
# ============================================================================

CABLE = {
    "place": "mountain cable-car stations",
    "book": "station log",
    "chores": ["the dawn car run", "the midday grip inspection", "the evening wind check",
               "the night anchor test", "the dawn rope grease round", "the counterweight sweep",
               "the brake block look-over"],
    "roles": ["line fitter", "station attendant", "ropeway mechanic", "rescue marshal",
              "maintenance planner", "cable auditor", "night controller"],
}
CHEM = {
    "place": "university chemistry stockroom",
    "book": "store book",
    "chores": ["the bottle round", "the hood wipe-down", "the stock count",
               "the floor rinse", "the label rebind", "the glove restock",
               "the waste pickup"],
    "roles": ["lab technician", "store steward", "teaching assistant", "safety officer",
              "receiving clerk", "glassblower", "auditor"],
}


def window_rows(alphabet: list[str], world: dict, comp_thing: list[str],
                comp_verb: list[str]) -> list[dict]:
    """Sliding 6-code window per seed; expected = alphabet[i] (learned code)."""
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
            "probes": {"s3t2": {"labels": alphabet[i:i + 6], "expected": alphabet[i]}},
        })
    return rows


def dr_scenario(sid: str, world: dict, thing: str, rows: list[dict], offset: int) -> dict:
    return {
        "id": sid,
        "family": "delayed_recall",
        "labels": {"note": f"{thing} code with a NON-label companion fact (anti-echo); "
                           "learning s1 fact + s2 chore; s3 held-out label-form probe"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the log: the {thing} code is {{code}}; the {{comp_thing}} {{comp_verb}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} complete; nothing else changes. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives; the {world['book']} is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants_value_sets(rows, offset, ["s3t2"]),
    }


DR_POOLS = [
    # cable-car stations: dr-5301 haul motor, dr-5302 grip carriage, dr-5303 brake rig
    ("dr-5301", CABLE, "haul motor",
     ["A12", "A17", "A21", "A26", "A31", "A35", "A39", "A43", "A47", "A51", "A55", "A59"],
     ["duty kettle", "portal lamp", "bench radio", "raft hook", "boot dryer",
      "coat rail", "spare fuse box"],
     ["whistles at six", "glows amber at dusk", "hums on standby", "rattles in crosswind",
      "ticks after frost", "sags under load", "buzzes when wet"], 0),
    ("dr-5302", CABLE, "grip carriage",
     ["G41", "G46", "G52", "G57", "G63", "G68", "G74", "G79", "G85", "G90", "G96", "G101"],
     ["cable saddle", "bunker heater", "towel rail", "lantern shelf", "tool cabinet",
      "sign frame", "grease drum"],
     ["creaks at sunrise", "warms the morning shift", "steams by noon", "sings in the dusk run",
      "locks at close", "swings in gusts", "drips by the drain"], 2),
    ("dr-5303", CABLE, "brake rig",
     ["N14", "N19", "N25", "N30", "N36", "N41", "N47", "N52", "N58", "N63", "N69", "N74"],
     ["bucket bench", "mop rack", "bin store", "rope cradle", "torch box",
      "post sander", "chalk tin"],
     ["holds the evening kit", "stands by the portal", "wobbles on the grate",
      "waits for the second shift", "shines after oiling", "collects the tags",
      "keeps the spares dry"], 4),
    # chemistry stockroom: dr-5304 reagent fridge, dr-5305 glassware cart,
    # dr-5306 balances bench, dr-5307 solvent cabinet
    ("dr-5304", CHEM, "reagent fridge",
     ["U51", "U56", "U62", "U67", "U73", "U78", "U84", "U89", "U95", "U99", "U104", "U109"],
     ["fume hood fan", "drying oven", "spill tray", "badge drawer", "sample rack",
      "sink tap", "first-aid tin"],
     ["hums all day", "ticks at noon", "slides when full", "sticks in damp",
      "fills by friday", "drips at the seam", "rings when bumped"], 1),
    ("dr-5305", CHEM, "glassware cart",
     ["V18", "V23", "V29", "V34", "V40", "V45", "V51", "V56", "V62", "V67", "V72", "V77"],
     ["acid cabinet", "trolley brake", "pipette jar", "glove box", "wash bottle crate",
      "burette stand", "cork tray"],
     ["stands by the wall", "squeals at frost", "foams after use", "sits on the top shelf",
      "waits by the sink", "rocks on the third wheel", "clicks when locked"], 3),
    ("dr-5306", CHEM, "balances bench",
     ["W72", "W77", "W83", "W88", "W94", "W99", "W104", "W109", "W115", "W120", "W126", "W131"],
     ["desiccator lid", "weights tray", "stool pad", "log binder", "calibration card",
      "dust cloth", "spare bulb"],
     ["fogs in the morning", "rattles on the move", "wears thin at one corner",
      "opens with a pop", "curls at the edges", "fades in the sun", "snags on the hinge"], 5),
    ("dr-5307", CHEM, "solvent cabinet",
     ["X21", "X26", "X32", "X37", "X43", "X48", "X54", "X59", "X65", "X70", "X76", "X81"],
     ["vent flap", "catch basin", "funnel rack", "rag bin", "label roll",
      "tweezer pot", "goggles shelf"],
     ["flutters in the draft", "catches the odd drip", "warms near the door",
      "fills by the week's end", "unrolls crooked", "lives by the scale",
      "holds the spare strap"], 0),
]

dr_scenarios = [dr_scenario(sid, world, thing, window_rows(alphabet, world, comp_t, comp_v), off)
                for sid, world, thing, alphabet, comp_t, comp_v, off in DR_POOLS]


# ============================================================================
# distractor_recall x8 (primary) — learning: target code + lure code stated
# together; held-out probe asks the TARGET with the LURE among the options.
# ============================================================================

THEATER = {
    "place": "theater props loft",
    "book": "loft register",
    "chores": ["the rigging check", "the costume press", "the set sweep",
               "the sound walk", "the lamp dusting", "the rope coil round",
               "the stair clear-out"],
    "roles": ["stage manager", "props master", "dresser", "fly operator", "night watchman",
              "set painter", "ushering lead"],
}
QUARRY = {
    "place": "quarry weighbridge office",
    "book": "weight ledger",
    "chores": ["the dawn weigh round", "the ticket audit", "the belt inspection",
               "the wheel wash", "the slate tally", "the lamp fuel fill",
               "the fence walk"],
    "roles": ["weighbridge clerk", "haul driver", "site foreman", "sample runner",
              "geologist", "fitter", "shipment planner"],
}


def dx_rows(pairs: list[tuple[str, str]], pool: list[str], world: dict) -> list[dict]:
    rows = []
    for i, (code, lure) in enumerate(pairs):
        labels = [code, lure] + [c for c in pool if c not in (code, lure)][:4]
        rows.append({
            "values": {"code": code, "lure": lure,
                       "chore": world["chores"][i], "role": world["roles"][i]},
            "probes": {"s3t2": {"labels": labels, "expected": code}},
        })
    return rows


def dx_scenario(sid: str, world: dict, thing: str, lure_thing: str,
                rows: list[dict], offset: int) -> dict:
    return {
        "id": sid,
        "family": "distractor_recall",
        "labels": {"note": f"two codes stated at learning ({thing} target, {lure_thing} lure); "
                           "probe asks the target with the lure in options; lure_value declared "
                           "for validator V8R"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the log: the {thing} code is {{code}}; the {lure_thing} code is {{lure}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "{chore} complete; nothing else changes. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives; the {world['book']} is not at hand. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "lure_value": "{lure}",
        "variants": variants_value_sets(rows, offset, ["s3t2"]),
    }


def ladder(prefix_t: str, prefix_l: str) -> tuple[list[tuple[str, str]], list[str]]:
    """7 (target, lure) pairs on two letter prefixes, pool = all 14 codes."""
    t = [f"{prefix_t}{11 + 5 * i}" for i in range(7)]
    l = [f"{prefix_l}{33 + 5 * i}" for i in range(7)]
    return list(zip(t, l)), t + l


DX_POOLS = [
    # theater props loft: dx-5401..5404
    ("dx-5401", THEATER, "costume rack", "trap room crate", *ladder("J", "K"), 0),
    ("dx-5402", THEATER, "wig cabinet", "prop trunk", *ladder("L", "M"), 2),
    ("dx-5403", THEATER, "script archive", "lighting case", *ladder("P", "Q"), 4),
    ("dx-5404", THEATER, "fly gallery ladder", "backdrop roll rack", *ladder("S", "T"), 1),
    # quarry weighbridge office: dx-5405..5408
    ("dx-5405", QUARRY, "scale house locker", "fuel bowser cabinet", *ladder("U", "V"), 3),
    ("dx-5406", QUARRY, "sample store room", "ticket bin", *ladder("W", "X"), 5),
    ("dx-5407", QUARRY, "tally board rack", "hose reel cradle", *ladder("Y", "Z"), 0),
    ("dx-5408", QUARRY, "weighbridge console", "ledger cupboard", *ladder("B", "C"), 2),
]

dx_scenarios = [dx_scenario(sid, world, thing, lure_thing, dx_rows(pairs, pool, world), off)
                for sid, world, thing, lure_thing, pairs, pool, off in DX_POOLS]


# ============================================================================
# guess_calibration x3 (secondary) — never-stated facts, per-seed entities,
# run clean on BOTH cores (per-core guess bands for dA and dB)
# ============================================================================

def gc_scenario(sid: str, opener_tmpl: str, asker_tmpl: str, q1_tmpl: str,
                q2_tmpl: str, word_labels: list[str], rows: list[dict], offset: int) -> dict:
    return {
        "id": sid,
        "family": "guess_calibration",
        "labels": {"note": "never-stated facts; guess rate and position bias (design E14); "
                           "expected null by design; run clean on both cores"},
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


# 7-word pools with a sliding 6-word window per seed: k stays 6 (guess rate
# 1/6) while every seed's option SET and ORDER differ (validator V16 — 7
# seeds exceed the 6 pure rotations, so fixed lists would duplicate orders).
WAXES = ["carnauba", "beeswax", "shellac", "paraffin", "cacao", "linseed", "lanolin"]
COLLARS = ["crimson", "violet", "teal", "mustard", "slate", "coral", "ochre"]
HATCH = ["north", "south", "east", "west", "uphill", "downhill", "seaward"]


def win(pool: list[str], i: int) -> list[str]:
    return rot(pool, i)[:6]


gc_5501 = gc_scenario(
    "gc-5501",
    "You mind the orchard packing shed on the {shift} stint. Acknowledge in one short line.",
    "{visitor} asks about records this shed never kept. Answer as best you can. Acknowledge in one short line.",
    "What wax coats the {e1} trays?",
    "How many crates wait on the {e2} stack?",
    WAXES,
    [
        {"values": {"shift": "dawn", "visitor": "a picker", "e1": "pear", "e2": "pallet"},
         "probes": {"s2t2": {"labels": win(WAXES, 0)}, "s2t3": {"labels": ["3", "4", "5", "6", "7", "8"]}}},
        {"values": {"shift": "market", "visitor": "a driver", "e1": "plum", "e2": "trestle"},
         "probes": {"s2t2": {"labels": win(WAXES, 1)}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "cider", "visitor": "a cooper", "e1": "quince", "e2": "ramp"},
         "probes": {"s2t2": {"labels": win(WAXES, 2)}, "s2t3": {"labels": ["2", "3", "4", "5", "6", "7"]}}},
        {"values": {"shift": "lunch", "visitor": "a grader", "e1": "apple", "e2": "shelf"},
         "probes": {"s2t2": {"labels": win(WAXES, 3)}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "close", "visitor": "a tally keeper", "e1": "greengage", "e2": "bin"},
         "probes": {"s2t2": {"labels": win(WAXES, 4)}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
        {"values": {"shift": "press", "visitor": "a blender", "e1": "medlar", "e2": "corner rack"},
         "probes": {"s2t2": {"labels": win(WAXES, 5)}, "s2t3": {"labels": ["7", "8", "9", "10", "11", "12"]}}},
        {"values": {"shift": "dispatch", "visitor": "a sorter", "e1": "mulberry", "e2": "lane"},
         "probes": {"s2t2": {"labels": win(WAXES, 6)}, "s2t3": {"labels": ["8", "9", "10", "11", "12", "13"]}}},
    ],
    0,
)

gc_5502 = gc_scenario(
    "gc-5502",
    "You mind the brewery cellar on the {shift} watch. Acknowledge in one short line.",
    "{visitor} asks about records this cellar never kept. Answer as best you can. Acknowledge in one short line.",
    "What color is the {e1} hose collar?",
    "How many casks rest in the {e2} row?",
    COLLARS,
    [
        {"values": {"shift": "mash", "visitor": "a drayman", "e1": "transfer line", "e2": "outer"},
         "probes": {"s2t2": {"labels": win(COLLARS, 0)}, "s2t3": {"labels": ["4", "5", "6", "7", "8", "9"]}}},
        {"values": {"shift": "boil", "visitor": "a fitter", "e1": "racking arm", "e2": "inner"},
         "probes": {"s2t2": {"labels": win(COLLARS, 1)}, "s2t3": {"labels": ["5", "6", "7", "8", "9", "10"]}}},
        {"values": {"shift": "fining", "visitor": "a cooper", "e1": "sample tap", "e2": "third"},
         "probes": {"s2t2": {"labels": win(COLLARS, 2)}, "s2t3": {"labels": ["6", "7", "8", "9", "10", "11"]}}},
        {"values": {"shift": "bottling", "visitor": "a courier", "e1": "vent line", "e2": "fourth"},
         "probes": {"s2t2": {"labels": win(COLLARS, 3)}, "s2t3": {"labels": ["7", "8", "9", "10", "11", "12"]}}},
        {"values": {"shift": "racking", "visitor": "a warden", "e1": "drain cock", "e2": "fifth"},
         "probes": {"s2t2": {"labels": win(COLLARS, 4)}, "s2t3": {"labels": ["8", "9", "10", "11", "12", "13"]}}},
        {"values": {"shift": "milling", "visitor": "a chandler", "e1": "grist chute", "e2": "sixth"},
         "probes": {"s2t2": {"labels": win(COLLARS, 5)}, "s2t3": {"labels": ["9", "10", "11", "12", "13", "14"]}}},
        {"values": {"shift": "cleansing", "visitor": "a plumber", "e1": "spirit safe", "e2": "seventh"},
         "probes": {"s2t2": {"labels": win(COLLARS, 6)}, "s2t3": {"labels": ["10", "11", "12", "13", "14", "15"]}}},
    ],
    2,
)

gc_5503 = gc_scenario(
    "gc-5503",
    "You mind the observatory dome on the {shift} rotation. Acknowledge in one short line.",
    "{visitor} asks about records this dome never kept. Answer as best you can. Acknowledge in one short line.",
    "Which way does the {e1} hatch point?",
    "How many steps climb to the {e2} platform?",
    HATCH,
    [
        {"values": {"shift": "dusk", "visitor": "a stargazer", "e1": "main shutter", "e2": "ring catwalk"},
         "probes": {"s2t2": {"labels": win(HATCH, 0)}, "s2t3": {"labels": ["9", "10", "11", "12", "13", "14"]}}},
        {"values": {"shift": "night", "visitor": "a lens cleaner", "e1": "side shutter", "e2": "inner catwalk"},
         "probes": {"s2t2": {"labels": win(HATCH, 1)}, "s2t3": {"labels": ["10", "11", "12", "13", "14", "15"]}}},
        {"values": {"shift": "moon", "visitor": "a recorder", "e1": "spare shutter", "e2": "outer catwalk"},
         "probes": {"s2t2": {"labels": win(HATCH, 2)}, "s2t3": {"labels": ["11", "12", "13", "14", "15", "16"]}}},
        {"values": {"shift": "dawn", "visitor": "a rigger", "e1": "rear shutter", "e2": "spiral stair"},
         "probes": {"s2t2": {"labels": win(HATCH, 3)}, "s2t3": {"labels": ["12", "13", "14", "15", "16", "17"]}}},
        {"values": {"shift": "day", "visitor": "a curator", "e1": "zenith panel", "e2": "main floor"},
         "probes": {"s2t2": {"labels": win(HATCH, 4)}, "s2t3": {"labels": ["13", "14", "15", "16", "17", "18"]}}},
        {"values": {"shift": "solar", "visitor": "a glazier", "e1": "view slit", "e2": "control deck"},
         "probes": {"s2t2": {"labels": win(HATCH, 5)}, "s2t3": {"labels": ["14", "15", "16", "17", "18", "19"]}}},
        {"values": {"shift": "closing", "visitor": "a caretaker", "e1": "vent flap", "e2": "entry landing"},
         "probes": {"s2t2": {"labels": win(HATCH, 6)}, "s2t3": {"labels": ["15", "16", "17", "18", "19", "20"]}}},
    ],
    4,
)

# ============================================================================
# emit
# ============================================================================

MANIFEST = {
    "protocol": "continuity-workload",
    "version": 3,
    "families": ["delayed_recall", "distractor_recall", "guess_calibration"],
    "primary_families": ["delayed_recall", "distractor_recall"],
    "primary_cluster_count": 15,
    "variant_seeds": SEEDS,
    "description": (
        "Suite v3k for CONT-002 (state transfer across cores, R = dB/dA): "
        "the v3i protocol (v3 label-form probes + predeclared per-seed variant "
        "table, manifest.variant_seeds = {5001..5007}) with fresh worlds "
        "(mountain cable-car stations, university chemistry stockroom, theater "
        "props loft, quarry weighbridge office; gc: orchard packing shed, "
        "brewery cellar, observatory dome) and ids x-5xxx, disjoint from "
        "v1/v2/v2-calibration/v3/v3h/v3i/v3j (validator V3 covers every "
        "rendered seed). PRIMARY = delayed_recall x7 + distractor_recall x8 "
        "(15 clusters x 7 seeds; sizing per power_calc_cont002.py: K12x5 "
        "detection power 0.604 at MME R 0.25 - undersized; K15x7 = 0.801 "
        "conservative row). Family rationale: cycles 1-2 measured the "
        "largest, cleanest memory benefit on DR/DX (pass ~1.0 with memory vs "
        "0.13-0.15 without), keeping the R denominator estimable by "
        "construction; the probe tests storage, not core-specific "
        "conflict-resolution policy, so CR/CU/RT are absent (memory-can-hurt "
        "transfer is a different question, out of scope per "
        "docs/CONT-002-DESIGN.md). Scenario shape serves the 2x2: s1 "
        "learning fact(s) (code + non-label companion / target + lure), s2 "
        "chore, s3 HELD-OUT probe session (class transfer_eligible) learned "
        "once per seed on core A and probed in all four cells (A+restored / "
        "A+clean / B+restored / B+clean). guess_calibration x3 (6 "
        "never-stated probes) measured clean on BOTH cores (per-core guess "
        "bands). Rendering: continuity.fixtures.render_seed_variant (single "
        "definition shared by runner, validator, assembly gate)."
    ),
}


def main() -> int:
    all_scenarios = [*dr_scenarios, *dx_scenarios, gc_5501, gc_5502, gc_5503]
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
