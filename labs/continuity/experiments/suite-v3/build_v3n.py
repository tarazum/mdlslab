"""Deterministic builder for fixture suite v3n (CONT-006 V2 rerun surface,
owner-authorized 2026-10-10 — ROADMAP "Owner decisions — recorded
2026-10-10"; diagnostic basis: docs/DIAGNOSTIC-CONT006-V2-CR.md).

Why a new suite: the v3m calibration pilot STOPPED out of band
(dx=1.0/dr=1.0 ceiling in BOTH arms; cr floor R0 0.25 / R2 0.0). Per prereg
A.3 the chain halts and a NEW suite is authored — never a v3m edit.

Composition identical to v3m (15 TR primary + 4 VAL + 3 GC; every taxonomy
class >= 2 primary clusters), mechanics INHERITED from the frozen suites
(v3i/v3j seed_error mechanisms + initial_expected; v3k lure_value + label
windows), ids x-8xxx, seeds {8001..8007}, fresh worlds (bell foundry,
linen room, greenhouse/chandlery/weaving loft/cider press/clock bench,
refuge/ferry/greenhouse, bindery vault/grain bourse; V18 world-freshness
vs ALL prior suites incl. v3m).

Difficulty re-aim (design-time, from the v3m CALIBRATION evidence — the
first suite whose bands were verified with memory ON before freeze):
- cr EASIER (R0 0.25 -> aim ~0.4-0.6): every probe report carries the
  exact head-noun phrase of exactly one card line ("loam build", "metal
  tap", "strike check", "flash trim", "clapper store", "crated load");
  card lines are short and mutually exclusive in vocabulary; probe reports
  are minimal paraphrases of the learning report (same head noun).
- dx HARDER (1.0 -> aim ~0.4-0.7): the LURE is re-confirmed after the
  learning turn (s2 reminder + s3 opener mention) while the expected code
  is stated ONCE in s1 — salience competition (FP-4 as designed); codes
  share a prefix and digit set (transposition-confusable).
- dr HARDER (1.0 -> aim ~0.4-0.7): same-type interference — two OTHER
  entities' codes of the same kind are logged in s2; the probe asks for
  the target entity with all three in options (FP-5 binding under
  interference; lure_value declared = the nearest interference code).
- cu/rt/gc: v3m mechanics unchanged, new worlds/texts (bands were in-band
  at calibration: cu 0.5, rt 0.33, gc unaffected).

Deterministic: no RNG, explicit tables only. Re-running overwrites
fixtures/v3n byte-identically.
"""

from __future__ import annotations

import json
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
OUT_DIR = LAB_ROOT / "fixtures" / "v3n"
SEEDS = [8001, 8002, 8003, 8004, 8005, 8006, 8007]

VALIDATION_IDS = ["cr-8005", "cu-8105", "rt-8204", "dx-8403"]


def rot(seq: list[str], k: int) -> list[str]:
    n = len(seq)
    return [seq[(i + k) % n] for i in range(n)]


def perm_orders(vocab: list[str], i: int) -> list[str]:
    """7 pairwise-distinct label orders over a FIXED 6-word vocabulary
    (6 rotations + a transposition of the identity; same device as v3l/v3m)."""
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
# correction_reuse x5 — bell foundry casting office; vocab fixed.
# EASIER: each card line owns an exact head-noun phrase; probe reports keep
# the head noun of the learning report (minimal paraphrase).
# ============================================================================

BELL = ["moulding", "pouring", "tuning", "fettling", "stocking", "dispatch"]
BELL_CARD = ("The standing foundry card: loam builds and cope ramming are moulding; "
             "metal taps and ladle melts are pouring; strike checks and note listens "
             "are tuning; flash trims and seam scrapes are fettling; clapper stores "
             "and wedge racks are stocking; crated loads and hauler pickups are "
             "dispatch.")
DAYS = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]


def cr_variants(bks: list[str], pqs: list[str], expected: str) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"bk": bks[i], "pq": pqs[i], "day": DAYS[i]},
            "probes": {"s3t2": {"labels": perm_orders(BELL, i), "expected": expected}},
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
                {"actor": "environment", "text": f"For the foundry desk: file this report under exactly one label: {' | '.join(BELL)}. Report: '{{bk}} {thing}.' Reply with the label only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your casting-office log from the previous shift files {{bk}} {thing} under '{trap}'. Keep the log line in view and acknowledge in one short line."},
                {"actor": "environment", "text": BELL_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": corr + " Amend your records in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Night desk at the bell foundry on {day}. The foundry card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"File this report. The foundry card is not at hand. Report: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected),
    }


cr_8001 = cr_vce_vct(
    "cr-8001", "valid_correction_environment", "on the day sheet",
    "loam build logged 'pouring'; verified foundry notice re-routes to moulding (FP-3a)",
    "Casting-office bulletin, verified notice from the foundry master: the log line "
    "filing {bk} under 'pouring' is out of date; loam builds and cope ramming are "
    "moulding under the standing card.",
    "moulding", "pouring",
    ["the loam build for the east pit", "the cope ramming at the tenor pit",
     "the loam build on the false bell", "the cope ramming for the tenor crown",
     "the loam build at the south pit", "the cope ramming on the bell core",
     "the loam build for the great bell"],
    ["the loam build for the night cast", "the cope ramming before the morning melt",
     "the loam build on the pattern", "the cope ramming at the west pit",
     "the loam build after the sift", "the cope ramming for the flat crown",
     "the loam build before the pour"],
)

cr_8002 = cr_vce_vct(
    "cr-8002", "valid_correction_tool", "on the pitch list",
    "strike check logged 'fettling'; tuning-fork sheet re-routes to tuning (FP-3a)",
    "The tuning-fork sheet, bench-verified this morning, reads {bk} as a strike "
    "check and note listen: tuning under the standing card; the old 'fettling' "
    "filing is out of date.",
    "tuning", "fettling",
    ["the strike check on the treble bell", "the note listen for the mezzo bell",
     "the strike check at the frame head", "the note listen on the bass bell",
     "the strike check for the practice round", "the note listen at the clapper gap",
     "the strike check on the new casting"],
    ["the strike check for the dusk round", "the note listen before the gate close",
     "the strike check on the flat bell", "the note listen for the morning round",
     "the strike check at the yoke", "the note listen on the small bell",
     "the strike check after the hang"],
)


def cr_euc(sid: str, note: str, insist: str, expected: str, trap: str,
           bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": "erroneous_user_correction",
        "seed_error": {"value": trap, "mechanism": "user_override"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"For the foundry desk: file this report under exactly one label: {' | '.join(BELL)}. Report: '{{bk}}.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": BELL_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": insist + " Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Night desk at the bell foundry on {day}. The foundry card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"File this report. The foundry card is not at hand. Report: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected),
    }


cr_8003 = cr_euc(
    "cr-8003",
    "crated load correctly 'dispatch'; yard clerk pushes 'stocking' (FP-3b)",
    "A shed hand presses about {bk}: 'count that one as stocking for my shelf "
    "list - every earlier tally has done so.' The hauler book, on file, keeps "
    "the entry as it stands.",
    "dispatch", "stocking",
    ["the crated load for the river wharf", "the hauler pickup at the north gate",
     "the crated load for the parish church", "the hauler pickup on the load day",
     "the crated load for the belfry job", "the hauler pickup at the canal yard",
     "the crated load for the fair field"],
    ["the crated load for the night haul", "the hauler pickup before the gate shut",
     "the crated load on the sledge", "the hauler pickup for the dusk run",
     "the crated load at the wharf door", "the hauler pickup after the tally",
     "the crated load for the second bell"],
)


def cr_sc(sid: str, note: str, verified: str, unreviewed: str, expected: str,
          trap: str, bks: list[str], pqs: list[str]) -> dict:
    return {
        "id": sid, "family": "correction_reuse", "sub_type": "source_conflict",
        "seed_error": {"value": trap, "mechanism": "source_conflict"},
        "labels": {"note": note},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"For the foundry desk: file this report under exactly one label: {' | '.join(BELL)}. Report: '{{bk}} on the watch sheet.' Reply with the label only.", "initial_expected": expected},
                {"actor": "environment", "text": BELL_CARD + " Note the card in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "user", "text": verified + " Note it in one short line."},
                {"actor": "environment", "source_type": "environment", "text": unreviewed},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "Night desk at the bell foundry on {day}. The foundry card is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"File this report. The foundry card is not at hand. Report: '{{pq}}.' Options: {{options}} - reply with the label only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": cr_variants(bks, pqs, expected),
    }


cr_8004 = cr_sc(
    "cr-8004",
    "metal tap correctly 'pouring'; unreviewed yard chalkboard claims 'dispatch' (FP-3b)",
    "The casting office forwards the founder's notice; the foundry verified it: "
    "metal taps and ladle melts stay with pouring matters, and {bk} remains as "
    "the card has it.",
    "An unreviewed yard chalkboard claims every metal tap, {bk} included, was "
    "moved to the hauler slate today.",
    "pouring", "dispatch",
    ["the metal tap for the morning melt", "the ladle melt on the big pour",
     "the metal tap at the cupola lip", "the ladle melt for the second cast",
     "the metal tap before the skim", "the ladle melt on the night charge",
     "the metal tap for the recast"],
    ["the metal tap for the dusk melt", "the ladle melt on the small pour",
     "the metal tap at the spout", "the ladle melt for the top cast",
     "the metal tap after the rest", "the ladle melt on the late charge",
     "the metal tap for the last pour"],
)

cr_8005 = cr_sc(
    "cr-8005",
    "VAL cluster (activation only): clapper store correctly 'stocking'; unreviewed pinboard claims 'moulding' (FP-3b)",
    "The stores clerk's memo, foundry-verified: clapper stores stay with stocking, "
    "and {bk} stays as the card has it.",
    "An unreviewed pinboard by the shed door claims the clapper stores, {bk} "
    "included, were moved to the loam bench today.",
    "stocking", "moulding",
    ["the clapper store for the treble set", "the wedge rack at the shed wall",
     "the clapper store for the bass bell", "the wedge rack on the bench side",
     "the clapper store for the field kit", "the wedge rack at the north shed",
     "the clapper store for the spare set"],
    ["the clapper store for the night check", "the wedge rack before the hang",
     "the clapper store on the shelf", "the wedge rack for the dusk round",
     "the clapper store at the door", "the wedge rack after the count",
     "the clapper store for the new pin"],
)


# ============================================================================
# contradiction_update x5 — FP-1 (2 superseded + 2 retracted TR, 1 VAL).
# Mechanics unchanged from v3m (cu was in-band at calibration); new worlds.
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


cu_8101 = cu_superseded(
    "cu-8101",
    "greenhouse bench soil scoops corrected; probe expects NEW value (FP-1)",
    "You keep the greenhouse bench book. For the log: the seed tray takes {old} soil scoops per fill. Acknowledge in one short line.",
    "Correction for the records: the scoop gauge was swapped; the seed tray now takes {new} soil scoops per fill, not {old}. Note the correction in one short line.",
    "A grower asks; the bench book is away. Acknowledge in one short line.",
    "How many soil scoops does the seed tray take per fill?",
    47, 6,
)
cu_8102 = cu_superseded(
    "cu-8102",
    "chandlery spar coats corrected; probe expects NEW value (FP-1)",
    "You mind the chandlery ledger. For the log: the new spar takes {old} varnish coats. Acknowledge in one short line.",
    "Correction for the records: the thinner batch changed; the new spar takes {new} varnish coats, not {old}. Note the correction in one short line.",
    "A rigger asks; the chandlery card is away. Acknowledge in one short line.",
    "How many varnish coats does the new spar take?",
    21, 7,
)
cu_8103 = cu_retracted(
    "cu-8103",
    "weaving loft warp threads corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You tend the weaving loft tally. For the log: the linen warp holds {old} threads per span. Acknowledge in one short line.",
    "Correction for the records: the reed was re-slotted; the linen warp holds {new} threads per span, not {old}. Note the correction in one short line.",
    "The weaver says the correction is withdrawn: the re-slotted reed belonged to the sample loom and does not apply here; the standing count from the first log holds as before. Amend in one short line.",
    "A cloth merchant asks; the loft tally is away. Acknowledge in one short line.",
    "How many threads does the linen warp hold per span?",
    38, 5,
)
cu_8104 = cu_retracted(
    "cu-8104",
    "cider press house rack turns corrected then withdrawn; probe expects ORIGINAL (FP-1)",
    "You run the press house sheet. For the log: the cheese rack winds {old} turns per pressing. Acknowledge in one short line.",
    "Correction for the records: the screw was re-set; the cheese rack winds {new} turns per pressing, not {old}. Note the correction in one short line.",
    "The press master says the correction is withdrawn: the re-set slip came from the mill house press and does not apply; the standing turns from the first log hold as before. Amend in one short line.",
    "An orchard hand asks; the press sheet is away. Acknowledge in one short line.",
    "How many turns does the cheese rack wind per pressing?",
    14, 6,
)
cu_8105 = cu_superseded(
    "cu-8105",
    "VAL cluster (activation only): clock bench beat counts corrected; probe expects NEW (FP-1)",
    "You mind the clock bench card. For the log: the gallery beat counts {old} ticks per swing. Acknowledge in one short line.",
    "Correction for the records: the pendulum was shortened; the gallery beat now counts {new} ticks per swing, not {old}. Note the correction in one short line.",
    "A clock mate asks; the bench card is away. Acknowledge in one short line.",
    "How many ticks does the gallery beat count per swing?",
    29, 8,
)


# ============================================================================
# repeated_task x4 — hospital linen room counter; FP-2. Mechanics unchanged
# (rt was in-band at calibration: 0.33).
# ============================================================================

LINEN = ["washing", "drying", "mending", "pressing", "folding", "collection"]
LINEN_CARD = ("The standing linen card: soiled bundles and sluice runs are washing; "
              "rack airs and line hangs are drying; stitch and patch work is "
              "mending; iron and steam passes are pressing; stack and shelf sets "
              "are folding; ward rounds and hamper pickups are collection.")
SLOTS = ["morning", "ward round", "lunch", "theatre list", "afternoon", "admissions", "night shift"]


def rt_scenario(sid: str, trap: str, expected: str,
                tasks: list[str], pqs: list[str]) -> dict:
    rows = []
    for i in range(len(SEEDS)):
        rows.append({
            "values": {"task": tasks[i], "pq": pqs[i], "slot": SLOTS[i]},
            "probes": {"s3t2": {"labels": perm_orders(LINEN, i), "expected": expected}},
        })
    return {
        "id": sid, "family": "repeated_task", "sub_type": "scripted_own_answer",
        "seed_error": {"value": trap, "mechanism": "scripted_agent_answer"},
        "labels": {"note": f"counter sheet pins '{trap}'; standing card says {expected}; probe expects {expected} (FP-2)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"Pick exactly one tag: {' | '.join(LINEN)}. Errand: '{{task}}.' Reply with the tag only.", "initial_expected": trap},
                {"actor": "environment", "source_type": "agent_answer", "text": f"Your earlier hatch sheet tags {{task}} as '{trap}'. The standing linen card, verified: stitch and patch work is mending; iron and steam passes are pressing. Amend the sheet in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "text": "Hatch handover before {slot}. The standing linen card applies. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": "New round opens at the linen hatch. The slate cards are locked away. Acknowledge in one short line."},
                {"actor": "environment", "text": "Pick one tag for this errand. No cards are in reach. Errand: '{pq}.' Options: {options} - reply with the tag only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "variants": variants(rows),
    }


rt_scenarios = [
    rt_scenario(
        "rt-8201", "collection", "pressing",
        ["the iron pass for the theatre linen", "the steam run for the ward sheets",
         "the iron pass on the pillow slips", "the steam run for the clinic gowns",
         "the iron pass for the night bedding", "the steam run on the table linen",
         "the iron pass for the admission packs"],
        ["the iron pass for the evening linen", "the steam run before the ward round",
         "the iron pass on the cot sheets", "the steam run for the day gowns",
         "the iron pass at the far bench", "the steam run for the theatre packs",
         "the iron pass before the shut"],
    ),
    rt_scenario(
        "rt-8202", "drying", "mending",
        ["the patch round for the staff coats", "the stitch run for the curtain sides",
         "the patch round on the blanket sets", "the stitch run for the screen covers",
         "the patch round for the gown tears", "the stitch run on the sheet hems",
         "the patch round for the cubicle drapes"],
        ["the patch round for the day coats", "the stitch run before the theatre list",
         "the patch round on the bed sets", "the stitch run for the veil nets",
         "the patch round at the north table", "the stitch run for the towel rails",
         "the patch round after the sort"],
    ),
    rt_scenario(
        "rt-8203", "washing", "folding",
        ["the stack set for the linen store", "the shelf run for the blanket room",
         "the stack set on the gown shelves", "the shelf run for the sheet press",
         "the stack set for the pad trolley", "the shelf run on the towel racks",
         "the stack set for the night cupboard"],
        ["the stack set for the morning store", "the shelf run before the lunch rush",
         "the stack set on the spare shelves", "the shelf run for the fresh packs",
         "the stack set at the east wall", "the shelf run for the gown racks",
         "the stack set after the count"],
    ),
    rt_scenario(
        "rt-8204", "folding", "collection",
        ["the hamper pickup for the east wing", "the ward round on the surgical floor",
         "the hamper pickup at the sluice door", "the ward round for the children's bay",
         "the hamper pickup on the clinic run", "the ward round at the day room",
         "the hamper pickup for the night wing"],
        ["the hamper pickup for the evening wing", "the ward round before the theatre list",
         "the hamper pickup at the side door", "the ward round for the observation bay",
         "the hamper pickup on the late run", "the ward round at the east desk",
         "the hamper pickup after the tally"],
    ),
]


# ============================================================================
# distractor_recall x3 (FP-4) — HARDER: the lure is re-confirmed AFTER the
# learning turn (s2 reminder names the lure again; the s3 opener mentions the
# lure's holder) while the expected code is stated once in s1. Codes share a
# prefix and digit set (transposition-confusable).
# ============================================================================

REFUGE = {"place": "alpine refuge stove room", "book": "stove log",
          "chores": ["the boot rack sweep", "the kindling box fill", "the window scrape",
                     "the lantern glass wipe", "the water urn rinse", "the bench brush", "the dusk shutter bar"],
          "roles": ["warden", "guide", "custodian", "night porter",
                    "patroller", "carrier", "hut keeper"],
          "lure_holder": "fuel depot"}
FERRY = {"place": "ferry engine room", "book": "engine book",
         "chores": ["the crank case wipe", "the cooling strainer rinse", "the deck plate sweep",
                    "the gauge glass polish", "the drip tray empty", "the tool rail tidy", "the dusk lamp check"],
         "roles": ["engineer", "mate", "fitter", "deckhand",
                   "purser", "skipper", "night watch"],
         "lure_holder": "yard office"}
GREENHOUSE = {"place": "botanical greenhouse potting shed", "book": "potting book",
              "chores": ["the mist line flush", "the tray rack wipe", "the cane store tidy",
                         "the label drawer sort", "the sand bin top-up", "the hose coil hang", "the dusk vent wind"],
              "roles": ["gardener", "grower", "curator", "helper",
                        "student", "porter", "night waterer"],
              "lure_holder": "estate store"}


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
                           "the LURE is re-confirmed in s2 (salience competition — v3n "
                           "difficulty fold); probe asks the target with the lure in "
                           "options; lure_value declared for validator V8R (FP-4)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}; the {lure_thing} code is {{lure}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": f"Reminder from the {world['lure_holder']}: the {lure_thing} code {{lure}} was re-confirmed this morning and still stands. {{chore}} finished. Acknowledge in one short line."},
            ]},
            {"index": 3, "turns": [
                {"actor": "environment", "text": f"A {{role}} arrives from the {world['lure_holder']} run; the {world['book']} is away. Acknowledge in one short line."},
                {"actor": "environment", "text": f"They need the {thing} code. Options: {{options}} - reply with the code only.", "probe": {"kind": "exact_match", "class": "transfer_eligible"}},
            ]},
        ],
        "lure_value": "{lure}",
        "variants": variants(rows),
    }


def dx_ladder(prefix: str) -> tuple[list[tuple[str, str]], list[str]]:
    """7 true transposition pairs (C17/C71, C23/C32, …) — the two codes of a
    seed share prefix and digit set, maximizing FP-4 confusion. The 14 values
    are pairwise distinct; the flat pool feeds the 4 filler options."""
    digits = [(17, 71), (23, 32), (45, 54), (68, 86), (19, 91), (26, 62), (38, 83)]
    pairs = [(f"{prefix}{a}", f"{prefix}{b}") for a, b in digits]
    # pool ordered all-first then all-second (the v3m ladder device): the
    # [:4] fillers continue the window instead of restarting at the head,
    # keeping per-seed label orders pairwise distinct (V16).
    pool = [p[0] for p in pairs] + [p[1] for p in pairs]
    return pairs, pool


dx_scenarios = [
    dx_scenario("dx-8401", REFUGE, "wood store hatch", "fuel crate",
                dx_rows(*dx_ladder("C"), REFUGE)),
    dx_scenario("dx-8402", FERRY, "spare parts locker", "paint locker",
                dx_rows(*dx_ladder("M"), FERRY)),
    dx_scenario("dx-8403", GREENHOUSE, "tool chest", "seed drawer",
                dx_rows(*dx_ladder("S"), GREENHOUSE)),
]


# ============================================================================
# delayed_recall x2 (FP-5) — HARDER: same-type interference. Two OTHER
# entities' codes of the same kind are logged in s2; the probe asks the
# target entity with all three in options. lure_value = nearest interference
# code (validator V8R).
# ============================================================================

BINDERY = {"place": "bindery vault room", "book": "binding register",
           "chores": ["the bone folder wipe", "the press screw oil", "the type drawer count",
                      "the glue pot stir", "the cutting mat brush", "the clamp rail dust", "the dusk shelf check"],
           "roles": ["binder", "finisher", "apprentice", "clerk",
                     "forwarder", "porter", "night watch"]}
BOURSE = {"place": "grain bourse weighing room", "book": "weigh book",
          "chores": ["the pan brush", "the beam chain oil", "the weight box count",
                     "the scoop rinse", "the hopper scrape", "the bench slate wipe", "the dusk seal round"],
          "roles": ["weigher", "clerk", "porter", "sample man",
                    "mill buyer", "keeper", "night guard"]}


def dr_rows(alphabet: list[str], world: dict, thing: str, other_things: list[str]) -> list[dict]:
    """Per seed i: code = alphabet[i], interference codes = the two NEXT
    alphabet entries (same kind, different entities); fillers continue the
    window (the v3m device — keeps per-seed label orders distinct)."""
    rows = []
    n = len(alphabet)
    for i in range(len(SEEDS)):
        code = alphabet[i % n]
        o1, o2 = alphabet[(i + 1) % n], alphabet[(i + 2) % n]
        window = [alphabet[(i + k) % n] for k in range(6)]
        labels = rot(window, i % 6)
        rows.append({
            "values": {"code": code, "o1": o1, "o2": o2,
                       "ot1": other_things[0], "ot2": other_things[1],
                       "chore": world["chores"][i], "role": world["roles"][i]},
            "probes": {"s3t2": {"labels": labels, "expected": code}},
        })
    return rows


def dr_scenario(sid: str, world: dict, thing: str, rows: list[dict]) -> dict:
    return {
        "id": sid, "family": "delayed_recall",
        "labels": {"note": f"{thing} code stated at learning; s2 logs TWO other "
                           "entities' codes of the same kind (interference — v3n "
                           "difficulty fold); probe asks the {thing} code with all "
                           "three in options; lure_value = the first interference "
                           "code (FP-5 binding under interference)"},
        "sessions": [
            {"index": 1, "turns": [
                {"actor": "environment", "text": f"You cover the {world['place']}. For the {world['book']}: the {thing} code is {{code}}. Acknowledge in one short line."},
            ]},
            {"index": 2, "turns": [
                {"actor": "environment", "source_type": "environment", "text": f"For the log: the {{ot1}} code is {{o1}}; the {{ot2}} code is {{o2}}; all else stands as before. {{chore}} finished. Acknowledge in one short line."},
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
    dr_scenario("dr-8301", BINDERY, "folio press bay",
                dr_rows(
                    ["N26", "N31", "N37", "N42", "N48", "N53", "N59",
                     "N64", "N70", "N75", "N81", "N86"],
                    BINDERY, "folio press bay",
                    ["trimmer cabinet", "gilt roll stand"])),
    dr_scenario("dr-8302", BOURSE, "silk sample drawer",
                dr_rows(
                    ["R33", "R38", "R44", "R49", "R55", "R60", "R66",
                     "R71", "R77", "R82", "R88", "R93"],
                    BOURSE, "silk sample drawer",
                    ["hemp sample rack", "malt proof cabinet"])),
]


# ============================================================================
# guess_calibration x3 — never-stated facts (word + number), fresh pools.
# ============================================================================

BELL_METALS = ["bronze", "brass", "copper", "pewter", "iron", "steel", "gunmetal"]
TAR_NAMES = ["stockholm", "bastard", "pitch", "rosin", "birch", "pine", "coal"]
ICE_TOOLS = ["pick", "saw", "tongs", "hook", "spade", "auger", "chisel"]


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


gc_8501 = gc_scenario(
    "gc-8501",
    "You mind the bell tower rope room on the {shift} stretch. Acknowledge in one short line.",
    "{visitor} asks about tallies this room never kept. Answer as best you can. Acknowledge in one short line.",
    "What metal rings in the {e1} peal?",
    "How many rope coils hang on the {e2} pegs?",
    BELL_METALS,
    [
        {"values": {"shift": "practice", "visitor": "a steeple keeper", "e1": "evensong", "e2": "north"},
         "probes": {"s2t2": {"labels": win(BELL_METALS, 0)}, "s2t3": {"labels": ["12", "15", "18", "21", "24", "27"]}}},
        {"values": {"shift": "ring night", "visitor": "a captain", "e1": "wedding", "e2": "south"},
         "probes": {"s2t2": {"labels": win(BELL_METALS, 1)}, "s2t3": {"labels": ["13", "16", "19", "22", "25", "28"]}}},
        {"values": {"shift": "muffle day", "visitor": "a sexton", "e1": "funeral", "e2": "west"},
         "probes": {"s2t2": {"labels": win(BELL_METALS, 2)}, "s2t3": {"labels": ["14", "17", "20", "23", "26", "29"]}}},
        {"values": {"shift": "tide watch", "visitor": "a chorister", "e1": "matins", "e2": "east"},
         "probes": {"s2t2": {"labels": win(BELL_METALS, 3)}, "s2t3": {"labels": ["15", "18", "21", "24", "27", "30"]}}},
        {"values": {"shift": "frost week", "visitor": "a founder", "e1": "harvest", "e2": "belfry"},
         "probes": {"s2t2": {"labels": win(BELL_METALS, 4)}, "s2t3": {"labels": ["16", "19", "22", "25", "28", "31"]}}},
        {"values": {"shift": "feast eve", "visitor": "a verger", "e1": "midnight", "e2": "ringing"},
         "probes": {"s2t2": {"labels": win(BELL_METALS, 5)}, "s2t3": {"labels": ["17", "20", "23", "26", "29", "32"]}}},
        {"values": {"shift": "ley day", "visitor": "a bell hanger", "e1": "ember", "e2": "wheel"},
         "probes": {"s2t2": {"labels": win(BELL_METALS, 6)}, "s2t3": {"labels": ["18", "21", "24", "27", "30", "33"]}}},
    ],
)
gc_8502 = gc_scenario(
    "gc-8502",
    "You keep the ferry landing stage on the {shift} watch. Acknowledge in one short line.",
    "{visitor} asks about notes this stage never kept. Answer as best you can. Acknowledge in one short line.",
    "What tar seals the {e1} seams?",
    "How many fenders ride the {e2} rail?",
    TAR_NAMES,
    [
        {"values": {"shift": "first sailing", "visitor": "a deckhand", "e1": "gangway", "e2": "pontoon"},
         "probes": {"s2t2": {"labels": win(TAR_NAMES, 0)}, "s2t3": {"labels": ["22", "25", "28", "31", "34", "37"]}}},
        {"values": {"shift": "slack water", "visitor": "a rigger", "e1": "top plank", "e2": "outer"},
         "probes": {"s2t2": {"labels": win(TAR_NAMES, 1)}, "s2t3": {"labels": ["23", "26", "29", "32", "35", "38"]}}},
        {"values": {"shift": "neap tide", "visitor": "a tally lad", "e1": "knee brace", "e2": "inner"},
         "probes": {"s2t2": {"labels": win(TAR_NAMES, 2)}, "s2t3": {"labels": ["24", "27", "30", "33", "36", "39"]}}},
        {"values": {"shift": "spring tide", "visitor": "a watchman", "e1": "stringer", "e2": "gate"},
         "probes": {"s2t2": {"labels": win(TAR_NAMES, 3)}, "s2t3": {"labels": ["25", "28", "31", "34", "37", "40"]}}},
        {"values": {"shift": "gale stand", "visitor": "a caulker", "e1": "rubbing strake", "e2": "step"},
         "probes": {"s2t2": {"labels": win(TAR_NAMES, 4)}, "s2t3": {"labels": ["26", "29", "32", "35", "38", "41"]}}},
        {"values": {"shift": "night crossing", "visitor": "a purser", "e1": "deck joint", "e2": "lamp"},
         "probes": {"s2t2": {"labels": win(TAR_NAMES, 5)}, "s2t3": {"labels": ["27", "30", "33", "36", "39", "42"]}}},
        {"values": {"shift": "ice watch", "visitor": "a ferryman", "e1": "boot edge", "e2": "post"},
         "probes": {"s2t2": {"labels": win(TAR_NAMES, 6)}, "s2t3": {"labels": ["28", "31", "34", "37", "40", "43"]}}},
    ],
)
gc_8503 = gc_scenario(
    "gc-8503",
    "You mind the ice house store on the {shift} stint. Acknowledge in one short line.",
    "{visitor} drops by and asks about tallies this ice house never logged. Answer as best you can. Acknowledge in one short line.",
    "What tool breaks the {e1} block?",
    "How many chip grooves score the {e2} cake?",
    ICE_TOOLS,
    [
        {"values": {"shift": "first cut", "visitor": "a cutter", "e1": "clear", "e2": "top"},
         "probes": {"s2t2": {"labels": win(ICE_TOOLS, 0)}, "s2t3": {"labels": ["42", "45", "48", "51", "54", "57"]}}},
        {"values": {"shift": "haul in", "visitor": "a driver", "e1": "cloudy", "e2": "middle"},
         "probes": {"s2t2": {"labels": win(ICE_TOOLS, 1)}, "s2t3": {"labels": ["43", "46", "49", "52", "55", "58"]}}},
        {"values": {"shift": "pack down", "visitor": "a packer", "e1": "sawdust", "e2": "lower"},
         "probes": {"s2t2": {"labels": win(ICE_TOOLS, 2)}, "s2t3": {"labels": ["44", "47", "50", "53", "56", "59"]}}},
        {"values": {"shift": "thaw watch", "visitor": "a keeper", "e1": "drain", "e2": "side"},
         "probes": {"s2t2": {"labels": win(ICE_TOOLS, 3)}, "s2t3": {"labels": ["45", "48", "51", "54", "57", "60"]}}},
        {"values": {"shift": "open day", "visitor": "a fishmonger", "e1": "lake", "e2": "north"},
         "probes": {"s2t2": {"labels": win(ICE_TOOLS, 4)}, "s2t3": {"labels": ["46", "49", "52", "55", "58", "61"]}}},
        {"values": {"shift": "close up", "visitor": "a grocer", "e1": "pond", "e2": "south"},
         "probes": {"s2t2": {"labels": win(ICE_TOOLS, 5)}, "s2t3": {"labels": ["47", "50", "53", "56", "59", "62"]}}},
        {"values": {"shift": "frost seal", "visitor": "a caretaker", "e1": "spring", "e2": "deep"},
         "probes": {"s2t2": {"labels": win(ICE_TOOLS, 6)}, "s2t3": {"labels": ["48", "51", "54", "57", "60", "63"]}}},
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
        "Suite v3n for the CONT-006 V2 RERUN after the v3m calibration "
        "STOP-OUT-OF-BAND (owner-authorized 2026-10-10, ROADMAP; diagnostic "
        "docs/DIAGNOSTIC-CONT006-V2-CR.md): v3m's family difficulty was "
        "bimodal under a memory-armed agent (dx/dr 1.0 ceiling, cr 0.25 "
        "floor). Composition identical to v3m (15 TR primary transfer "
        "clusters of class transfer_eligible + 4 VAL activation-only + GC x3; "
        "every taxonomy class >= 2 primary clusters), mechanics INHERITED "
        "from the frozen suites only (v3i/v3j seed_error mechanisms + "
        "initial_expected; v3k lure_value + label windows), fresh worlds "
        "(bell foundry casting office, hospital linen room, greenhouse "
        "bench/chandlery/weaving loft/cider press/clock bench, alpine "
        "refuge/ferry engine room/botanical greenhouse, bindery vault/grain "
        "bourse, bell tower/ferry landing/ice house), ids x-8xxx, seeds "
        "{8001..8007}, disjoint from ALL prior suites incl. v3m (validator "
        "V3 every seed both ways + V18 world-freshness). Difficulty re-aim "
        "(design-time, from the v3m CALIBRATION evidence): cr EASIER (probe "
        "reports carry the exact head-noun phrase of one card line — "
        "lexically transparent mapping), dx HARDER (lure re-confirmed in s2 "
        "while the expected code is stated once — salience competition), dr "
        "HARDER (two other entities' codes of the same kind logged in s2 — "
        "interference binding), cu/rt unchanged mechanics. The calibration "
        "pilot verifies the bands with memory ON before freeze (out of band "
        "-> a NEW suite, never a v3n edit). Rendering: "
        "continuity.fixtures.render_seed_variant."
    ),
}


def main() -> int:
    all_scenarios = [
        cr_8001, cr_8002, cr_8003, cr_8004, cr_8005,
        cu_8101, cu_8102, cu_8103, cu_8104, cu_8105,
        *rt_scenarios,
        *dx_scenarios,
        *dr_scenarios,
        gc_8501, gc_8502, gc_8503,
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
