"""Pre-inference mechanical validator for fixture suites v3/v3h/v3i/v3j/v3k.

Enforces docs/SUITE-V3-DESIGN.md on fixtures/v3 BEFORE any inference. Fail-closed:
a failed check means fix-and-regenerate the fixtures, never relax the validator.

Check namespaces: the frozen v2 validator owns E1..E10 (see
experiments/CONT-001/validate_fixtures_v2.py). This validator uses V1..V16; the
design doc's check ids map as: design E9 -> V4, E10 -> V5, E11 -> V6, E12 -> V7,
E13 -> V8, E14 -> V9. Inherited v2 semantics: V3 (id/content disjointness, was
E3/E4), V10 (probes off first turns, was E9), V11 (RM denominator shape, was
E6/E7), V12 (public safety, was E10), V13 (initial_expected on s1t1, was E7).

Suite v3i (cycle 2): scenarios carry a predeclared per-seed variant table; the
validator renders EVERY seed via continuity.fixtures.render_seed_variant (the
single render definition shared with the runner — importing it here is
deliberate, so validator and runner cannot diverge on rendering) and runs the
per-scenario checks (V2, V4-V6, V8-V13) on the rendered multiset, plus three
variant-specific checks:
  V14-variant-table   table structure, token closure, render success per seed
  V15-seed-variation  probe texts pairwise distinct per seed; identical-across-
                      all-seeds turn share <= 0.5 (true replicates, not echoes)
  V16-label-order-varies  per-seed label orders pairwise distinct; expected
                      label position spread >= 3 distinct positions per scenario

Suite v3k (CONT-002 state transfer): PRIMARY = delayed_recall x6 +
distractor_recall x6 (12 recall clusters, probe class transfer_eligible); no
CR/CU/RT scenarios at all, so the per-suite FAMILY_PLANS replace the
CONT-005-hardcoded layout in V1/V7, and recall primaries take the V8R
structural-eligibility check (learned-fact + lure structure) instead of the
V8 trap/seed_error check that does not apply to recall probes.

Usage:
    python labs/continuity/experiments/suite-v3/validate_fixtures_v3.py \
        [--suite v3|v3h|v3i|v3j|v3k] [--out <path>/fixture-validation-<suite>.json]

Exit 0 = PASS; exit 2 = FAIL-CLOSED.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import render_seed_variant  # noqa: E402

# Primary-set expectations per suite (PR-REVIEW-v2 required change 1: the
# validator is suite-parameterized; v3 keeps CR+RT=14, the held-out v3h uses
# the pilot-informed CR+CU=12, cycle-2 v3i keeps CR+CU=12 with CR sub-types
# rebalanced toward T1's source/verification surface, CONT-002 v3k uses the
# recall pair DR+DX=12 per docs/CONT-002-DESIGN.md section 2).
EXPECTED_PRIMARY = {
    "v3": {"correction_reuse": 8, "repeated_task": 6},
    "v3h": {"correction_reuse": 8, "contradiction_update": 4},
    "v3i": {"correction_reuse": 8, "contradiction_update": 4},
    "v3j": {"correction_reuse": 8, "contradiction_update": 4},
    "v3k": {"delayed_recall": 7, "distractor_recall": 8},
}
# Complete per-suite family plans (scenario BASE counts, not multiplied by
# seeds). v3-v3j layouts are exactly what the pre-v3k V1/V7 checks enforced;
# v3k drops the CONT-005 correction families entirely (lean transfer suite).
FAMILY_PLANS = {
    "v3": {"correction_reuse": 8, "repeated_task": 6, "contradiction_update": 4,
           "delayed_recall": 3, "distractor_recall": 3, "guess_calibration": 3},
    "v3h": {"correction_reuse": 8, "contradiction_update": 4, "repeated_task": 6,
            "delayed_recall": 3, "distractor_recall": 3, "guess_calibration": 3},
    "v3i": {"correction_reuse": 8, "contradiction_update": 4, "repeated_task": 6,
            "delayed_recall": 3, "distractor_recall": 3, "guess_calibration": 3},
    "v3j": {"correction_reuse": 8, "contradiction_update": 4, "repeated_task": 6,
            "delayed_recall": 3, "distractor_recall": 3, "guess_calibration": 3},
    "v3k": {"delayed_recall": 7, "distractor_recall": 8, "guess_calibration": 3},
}
CR_SUBTYPES = {
    "v3": {
        "valid_correction_environment": 1,
        "valid_correction_tool": 1,
        "erroneous_user_correction": 2,
        "retraction": 2,
        "source_conflict": 2,
    },
    "v3h": {
        "valid_correction_environment": 1,
        "valid_correction_tool": 1,
        "erroneous_user_correction": 2,
        "retraction": 2,
        "source_conflict": 2,
    },
    "v3i": {
        "valid_correction_environment": 2,
        "valid_correction_tool": 1,
        "erroneous_user_correction": 2,
        "source_conflict": 2,
        "retraction": 1,
    },
    # v3j (FREEZE-B): sub-type composition deliberately IDENTICAL to v3i
    # (no post-pilot sub-type cherry-picking); difficulty is re-aimed mid-scale
    # via wording levers only (pilot-informed calibration, EVALUATION-PREP-v3
    # section 2 stage 2).
    "v3j": {
        "valid_correction_environment": 2,
        "valid_correction_tool": 1,
        "erroneous_user_correction": 2,
        "source_conflict": 2,
        "retraction": 1,
    },
    # v3k: no correction_reuse scenarios; the expectation is the empty map.
    "v3k": {},
}
# Primary probe class per suite: rm_eligible = repeated-mistake endpoint
# (CONT-001/CONT-005); transfer_eligible = the CONT-002 R = dB/dA analogue.
PROBE_CLASS = {
    "v3": "rm_eligible",
    "v3h": "rm_eligible",
    "v3i": "rm_eligible",
    "v3j": "rm_eligible",
    "v3k": "transfer_eligible",
}
# Families whose primaries carry the trap/seed_error structure checked by V8.
TRAP_PRIMARY_FAMILIES = {"correction_reuse", "contradiction_update", "repeated_task"}
SECONDARY_COUNTS = {"delayed_recall": 3, "distractor_recall": 3, "guess_calibration": 3}
SEED_MECHANISMS = {
    "scripted_agent_answer", "user_override", "retracted_correction", "source_conflict",
    "superseded_value",  # v3h: CU primary — the superseded old value is the trap
}
_TOKEN_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")

INITIAL_VOCAB_RE = re.compile(r"exactly one [a-z]+:\s*([a-z\-_ ]+(?:\s*\|\s*[a-z\-_ ]+)+)")


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def load_scenarios(fixture_dir: Path) -> tuple[dict, list[dict]]:
    manifest = json.loads((fixture_dir / "manifest.json").read_text(encoding="utf-8"))
    scenarios: list[dict] = []
    for path in sorted(fixture_dir.rglob("*.json")):
        if path.name == "manifest.json":
            continue
        scenarios.append(json.loads(path.read_text(encoding="utf-8")))
    return manifest, scenarios


def turn_refs(scenario: dict) -> list[tuple[int, int, dict]]:
    out = []
    for session in scenario["sessions"]:
        for j, turn in enumerate(session["turns"], start=1):
            out.append((session["index"], j, turn))
    return out


def probes_of(scenario: dict) -> list[tuple[int, int, dict]]:
    return [(s, j, t) for s, j, t in turn_refs(scenario) if t.get("probe") is not None]


def strip_options(text: str) -> str:
    idx = text.find("Options:")
    return text[:idx] if idx >= 0 else text


def label_word_hit(label: str, text: str) -> bool:
    return re.search(rf"(?<![A-Za-z0-9]){re.escape(label.lower())}(?![A-Za-z0-9])", text.lower()) is not None


def suite_digest(fixture_dir: Path) -> str:
    h = hashlib.sha256()
    for path in sorted(p for p in fixture_dir.rglob("*") if p.is_file()):
        h.update(path.relative_to(fixture_dir).as_posix().encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def suite_texts(fixture_dir: Path) -> tuple[set[str], set[str]]:
    """Ids and normalized turn texts of a suite (rendered for EVERY variant seed
    when the suite carries a variant table, so disjointness covers all seeds)."""
    manifest, scenarios = load_scenarios(fixture_dir)
    ids = {s["id"] for s in scenarios}
    seeds = manifest.get("variant_seeds")
    if seeds:
        texts: set[str] = set()
        for s in scenarios:
            for sd in seeds:
                texts |= {normalize(t["text"]) for _, _, t in turn_refs(render_seed_variant(s, sd))}
    else:
        texts = {normalize(t["text"]) for s in scenarios for _, _, t in turn_refs(s)}
    return ids, texts


def validate(fixtures_root: Path, suite: str = "v3") -> dict:
    checks: list[dict] = []

    def record(cid: str, ok: bool, detail: str) -> None:
        checks.append({"check": cid, "pass": ok, "detail": detail})

    expected_primary = EXPECTED_PRIMARY.get(suite)
    if expected_primary is None:
        raise ValueError(f"no primary-set expectation for suite {suite!r}; extend EXPECTED_PRIMARY")
    cr_subtypes_expected = CR_SUBTYPES[suite]
    primary_families = set(expected_primary)
    primary_total = sum(expected_primary.values())
    # Disjointness set (PR-REVIEW-v2 required change 1a): every OTHER suite,
    # including the v3 pilot suite when validating v3h (or any future suite).
    other_suites = [
        p for name, p in {
            "v1": fixtures_root / "v1",
            "v2": fixtures_root / "v2",
            "v2-calibration": fixtures_root / "v2-calibration",
            "v3": fixtures_root / "v3",
            "v3h": fixtures_root / "v3h",
            "v3i": fixtures_root / "v3i",
            "v3j": fixtures_root / "v3j",
            "v3k": fixtures_root / "v3k",
        }.items()
        if name != suite and p.exists()
    ]

    v3_dir = fixtures_root / suite
    manifest, scenarios = load_scenarios(v3_dir)
    variant_seeds = manifest.get("variant_seeds")

    # V1 manifest
    fams = set(manifest.get("families", []))
    declared_primary = set(manifest.get("primary_families", primary_families))
    expected_families = set(FAMILY_PLANS[suite])
    seeds_ok = (
        isinstance(variant_seeds, list)
        and len(variant_seeds) >= 2
        and len(set(variant_seeds)) == len(variant_seeds)
        and all(isinstance(x, int) and not isinstance(x, bool) for x in variant_seeds)
    )
    ok = (
        manifest.get("protocol") == "continuity-workload"
        and manifest.get("version") == 3
        and expected_families <= fams
        and fams == expected_families
        and declared_primary == primary_families
        and manifest.get("primary_cluster_count") == primary_total
        and (seeds_ok if suite in ("v3i", "v3j", "v3k") else True)
    )
    record("V1-manifest", ok,
           f"suite={suite}; protocol/version ok; families={sorted(fams)}; primary={sorted(declared_primary)} "
           f"x{primary_total} (expected {sorted(primary_families)} x{primary_total}); "
           f"variant_seeds={variant_seeds if variant_seeds else 'none'}")

    # Variant suites: render every seed; per-scenario checks run on the
    # rendered multiset so every invariant is verified for EVERY seed's content.
    render_errors: list[str] = []
    flat: list[dict] = list(scenarios)
    if variant_seeds:
        flat = []
        for s in scenarios:
            for sd in variant_seeds:
                try:
                    flat.append(render_seed_variant(s, sd))
                except Exception as exc:
                    render_errors.append(f"{s.get('id')} seed {sd}: {type(exc).__name__}: {exc}")
        record("V14-variant-table", not render_errors,
               f"{len(scenarios)} scenarios x {len(variant_seeds)} seeds render; "
               f"fail-closed errors: {render_errors[:4] or 'none'}")
    else:
        record("V14-variant-table", True, "no variant table (pre-v3i suite); check skipped")

    # V2 schema (rendered: probes are complete only after rendering)
    problems: list[str] = []
    ids = []
    for s in flat:
        ids.append(s.get("id"))
        if not isinstance(s.get("id"), str) or not isinstance(s.get("family"), str):
            problems.append(f"{s.get('id')}: id/family types")
        if not isinstance(s.get("sessions"), list) or len(s["sessions"]) < 1:
            problems.append(f"{s.get('id')}: sessions")
            continue
        for k, session in enumerate(s["sessions"], start=1):
            if session.get("index") != k:
                problems.append(f"{s.get('id')}: session index {session.get('index')} != {k}")
            for turn in session["turns"]:
                if turn.get("actor") != "environment":
                    problems.append(f"{s.get('id')}: non-environment actor {turn.get('actor')!r}")
                if not isinstance(turn.get("text"), str) or not turn["text"].strip():
                    problems.append(f"{s.get('id')}: empty turn text")
                probe = turn.get("probe")
                if probe is None:
                    continue
                labels = probe.get("labels")
                expected = probe.get("expected")
                if not isinstance(labels, list) or len(set(labels)) != len(labels) or any(not isinstance(x, str) or not x.strip() for x in labels):
                    problems.append(f"{s.get('id')}: bad probe.labels {labels!r}")
                if probe.get("kind") == "guess_calibration":
                    if expected is not None or probe.get("class") != "guess_cal":
                        problems.append(f"{s.get('id')}: guess probe must have expected null + class guess_cal")
                else:
                    if probe.get("kind") != "exact_match" or not isinstance(expected, str):
                        problems.append(f"{s.get('id')}: probe kind/expected {probe.get('kind')}/{expected!r}")
                    elif isinstance(labels, list) and expected not in labels:
                        problems.append(f"{s.get('id')}: expected {expected!r} not in labels")
    record("V2-schema", not problems, f"{len(flat)} scenario-instances; violations: {problems[:5] or 'none'}")

    # V3 disjointness from every other suite (incl. the v3 pilot for v3h; for
    # v3i the check covers the rendered texts of every seed both ways)
    other_ids: set[str] = set()
    other_texts: set[str] = set()
    for other in other_suites:
        o_ids, o_texts = suite_texts(other)
        other_ids |= o_ids
        other_texts |= o_texts
    dup_ids = [i for i in ids if ids.count(i) > 1] if not variant_seeds else []
    if variant_seeds:
        base_ids = [s["id"] for s in scenarios]
        dup_ids = [i for i in base_ids if base_ids.count(i) > 1]
        ids = base_ids  # cross-suite id overlap is a base-scenario property
    id_overlap = sorted(set(ids) & other_ids)
    own_texts = {normalize(t["text"]) for s in flat for _, _, t in turn_refs(s)}
    text_overlap = sorted(own_texts & other_texts)
    record(
        "V3-disjoint-from-v1-v2",
        not dup_ids and not id_overlap and not text_overlap,
        f"dup ids {dup_ids}; id overlap {id_overlap}; shared turn texts {len(text_overlap)} {text_overlap[:2]}",
    )

    # V4 (design E9): label-form probes with options present
    bad: list[str] = []
    for s in flat:
        for _, _, turn in probes_of(s):
            probe = turn["probe"]
            labels = probe.get("labels", [])
            segment = turn["text"][turn["text"].find("Options:"):] if "Options:" in turn["text"] else ""
            if len(labels) < 5:
                bad.append(f"{s['id']}: k={len(labels)} < 5")
            if not segment:
                bad.append(f"{s['id']}: no Options: segment")
            else:
                for label in labels:
                    if label not in segment:
                        bad.append(f"{s['id']}: label {label!r} missing from options text")
            if "reply with the" not in turn["text"]:
                bad.append(f"{s['id']}: no deterministic reply instruction")
    record("V4-label-form", not bad, f"every probe: >=5 labels, options verbatim in text, reply instruction; violations: {bad[:5] or 'none'}")

    # V5 (design E10): correct-label position rotation (over every seed instance)
    positions = []
    for s in flat:
        for _, _, turn in probes_of(s):
            probe = turn["probe"]
            if probe.get("expected") is not None and isinstance(probe.get("labels"), list):
                positions.append(probe["labels"].index(probe["expected"]))
    distinct = sorted(set(positions))
    max_share = max(positions.count(p) for p in distinct) / len(positions) if positions else 1.0
    record(
        "V5-position-rotation",
        len(distinct) >= 3 and max_share <= 0.5,
        f"{len(positions)} scored probes; distinct positions {distinct}; max share {max_share:.2f} (need >=3 distinct, <=0.50)",
    )

    # V6 (design E11): session-scoped anti-leakage
    bad = []
    for s in flat:
        for sess_idx, _, turn in probes_of(s):
            session_texts = [
                strip_options(t["text"]) if t is turn else t["text"]
                for t in next(x for x in s["sessions"] if x["index"] == sess_idx)["turns"]
            ]
            for label in turn["probe"].get("labels", []):
                for text in session_texts:
                    if label_word_hit(label, text):
                        bad.append(f"{s['id']} s{sess_idx}: label {label!r} leaks in {text[:60]!r}")
                        break
    record("V6-no-session-leak", not bad, f"no label word in any probe-session text (options segment stripped); violations: {bad[:5] or 'none'}")

    # V7 (design E12): composition (BASE scenarios — counts do not multiply by seeds)
    fam_counts: dict[str, int] = {}
    cr_subs: dict[str, int] = {}
    rt_subs: set[str] = set()
    gc_probes = 0
    for s in flat:
        fam_counts[s["family"]] = fam_counts.get(s["family"], 0) + 1
    for s in scenarios:
        if s["family"] == "correction_reuse":
            cr_subs[s.get("sub_type", "?")] = cr_subs.get(s.get("sub_type", "?"), 0) + 1
        if s["family"] == "repeated_task":
            rt_subs.add(s.get("sub_type", "?"))
    for s in flat:
        gc_probes += sum(1 for _, _, t in probes_of(s) if t["probe"].get("kind") == "guess_calibration")
    if variant_seeds:
        gc_probes = gc_probes // len(variant_seeds)
        fam_counts = {f: (n // len(variant_seeds)) for f, n in fam_counts.items()}
    family_plan = FAMILY_PLANS[suite]
    ok = (
        all(fam_counts.get(f) == n for f, n in expected_primary.items())
        and fam_counts == family_plan
        and cr_subs == cr_subtypes_expected
        and ("repeated_task" not in primary_families or rt_subs == {"scripted_own_answer"})
        and gc_probes >= 6
    )
    record(
        "V7-composition",
        ok,
        f"suite={suite}; family counts {fam_counts}; family plan {family_plan}; "
        f"primary expectation {expected_primary}; "
        f"cr sub-types {cr_subs} (need {cr_subtypes_expected}); rt sub-type {rt_subs}; gc probes {gc_probes}",
    )

    # V8 (design E13): structural eligibility (primary set per suite, EVERY
    # seed). Trap primaries (CR/CU/RT) carry the seed_error/trap structure;
    # recall primaries (DR/DX in v3k) instead carry the learned-fact/lure
    # structure checked by V8R.
    bad = []
    primary = [s for s in flat if s["family"] in primary_families]
    if primary_families <= TRAP_PRIMARY_FAMILIES:
        for s in primary:
            seed = s.get("seed_error")
            probe_turns = probes_of(s)
            if not isinstance(seed, dict) or seed.get("mechanism") not in SEED_MECHANISMS or not isinstance(seed.get("value"), str):
                bad.append(f"{s['id']}: seed_error {seed!r}")
                continue
            if len(probe_turns) != 1:
                bad.append(f"{s['id']}: {len(probe_turns)} probes, need exactly 1")
                continue
            sess_idx, _, turn = probe_turns[0]
            labels = turn["probe"].get("labels", [])
            if seed["value"] not in labels:
                bad.append(f"{s['id']}: seed value {seed['value']!r} not a probe label")
            if seed["value"] == turn["probe"].get("expected"):
                bad.append(f"{s['id']}: seed value equals expected (no trap)")
            earlier = " ".join(
                t["text"] for si, _, t in turn_refs(s) if si < sess_idx
            )
            if not label_word_hit(seed["value"], earlier):
                bad.append(f"{s['id']}: seed value never stated before the probe session")
        record("V8-structural-eligibility", not bad, f"every primary scenario-instance: seed_error valid, trap in labels, trap != expected, trap stated pre-probe; violations: {bad[:5] or 'none'}")
    else:
        # V8R (v3k recall primaries): the probe's expected value must be a
        # standalone token in a pre-probe LEARNING turn (the fact the state
        # must carry); a declared lure_value (DX) must be in labels, stated
        # pre-probe, and differ from expected; exactly one probe, last
        # session. lure_value is a {token} template resolved per seed from
        # the base variant table (render_seed_variant does not touch it).
        for s_base in scenarios:
            if s_base["family"] not in primary_families:
                continue
            for sd in variant_seeds or [None]:
                s = render_seed_variant(s_base, sd) if sd is not None else s_base
                probe_turns = probes_of(s)
                if len(probe_turns) != 1 or probe_turns[0][0] != s["sessions"][-1]["index"]:
                    bad.append(f"{s['id']}: need exactly 1 probe in the last session")
                    continue
                sess_idx, _, turn = probe_turns[0]
                expected = turn["probe"].get("expected")
                labels = turn["probe"].get("labels", [])
                earlier = " ".join(
                    t["text"] for si, _, t in turn_refs(s) if si < sess_idx
                )
                if not isinstance(expected, str) or expected not in labels:
                    bad.append(f"{s['id']}: expected {expected!r} not a probe label")
                elif not label_word_hit(expected, earlier):
                    bad.append(f"{s['id']}: expected {expected!r} never stated in a learning turn")
                lure_tmpl = s_base.get("lure_value")
                if lure_tmpl is not None:
                    values = s_base["variants"][str(sd)]["values"]
                    lure = _TOKEN_RE.sub(lambda m: values[m.group(1)], lure_tmpl)
                    if lure not in labels:
                        bad.append(f"{s['id']}: lure {lure!r} not in probe labels")
                    elif not label_word_hit(lure, earlier):
                        bad.append(f"{s['id']}: lure {lure!r} never stated in a learning turn")
                    elif lure == expected:
                        bad.append(f"{s['id']}: lure equals expected")
        record("V8R-recall-eligibility", not bad, f"every recall primary (every seed): expected stated in a learning turn; lure (when declared) in labels, stated pre-probe, != expected; 1 probe in last session; violations: {bad[:5] or 'none'}")

    # V9 (design E14): guess calibration
    gc_scenarios = [s for s in flat if s["family"] == "guess_calibration"]
    gc_scenario_base = {s["id"] for s in scenarios if s["family"] == "guess_calibration"}
    ok = len(gc_scenario_base) >= 3 and gc_probes >= 6 and all(
        all(t["probe"].get("kind") == "guess_calibration" and t["probe"].get("expected") is None for _, _, t in probes_of(s))
        for s in gc_scenarios
    )
    record("V9-guess-calibration", ok, f"{len(gc_scenario_base)} gc scenarios, {gc_probes} never-stated probes (all seeds), all expected null")

    # V10 probes off first turns (v2 E9 inherited)
    bad = []
    for s in flat:
        for sess_idx, turn_no, _ in probes_of(s):
            session = next(x for x in s["sessions"] if x["index"] == sess_idx)
            if turn_no < 2 or not any(t.get("probe") is None for t in session["turns"][: turn_no - 1]):
                bad.append(f"{s['id']} s{sess_idx}t{turn_no}")
    record("V10-probes-off-first-turns", not bad, f"every probe preceded by a non-probe turn in its session; violations: {bad or 'none'}")

    # V11 primary shape
    bad = []
    for s in primary:
        probe_turns = probes_of(s)
        last_session = s["sessions"][-1]["index"]
        if len(s["sessions"]) < 2 or len(probe_turns) != 1 or probe_turns[0][0] != last_session:
            bad.append(s["id"])
        elif probe_turns[0][2]["probe"].get("class") != PROBE_CLASS[suite]:
            bad.append(f"{s['id']}: probe class")
    record("V11-primary-shape", not bad, f"primary: >=2 sessions, exactly 1 probe, in the LAST session, class {PROBE_CLASS[suite]}; violations: {bad or 'none'}")

    # V12 public safety
    bad = []
    for s in flat:
        for _, _, t in turn_refs(s):
            text = t["text"]
            if "@" in text or "http" in text.lower() or not text.isascii():
                bad.append(f"{s['id']}: unsafe turn")
    record("V12-public-safe", not bad, "ASCII, no '@', no http everywhere (all seed instances)")

    # V13 initial_expected on s1t1 of primary CLASSIFICATION scenarios (CR/RT);
    # value-correction primaries (CU in v3h/v3i) state facts, they have no option-
    # vocabulary initial task - their structural trap is seed_error(superseded_value).
    bad = []
    for s in primary:
        if s["family"] not in ("correction_reuse", "repeated_task"):
            continue
        s1t1 = s["sessions"][0]["turns"][0]
        m = INITIAL_VOCAB_RE.search(s1t1.get("text", "").lower())
        vocab = [w.strip() for w in m.group(1).split("|")] if m else []
        if s1t1.get("probe") is not None:
            bad.append(f"{s['id']}: probe on s1t1")
        elif s1t1.get("initial_expected") not in vocab:
            bad.append(f"{s['id']}: initial_expected {s1t1.get('initial_expected')!r} not in s1t1 vocabulary")
    record("V13-initial-expected", not bad, f"initial_expected on s1t1 of every primary classification scenario (CR/RT), drawn from its option vocabulary; violations: {bad or 'none'}")

    if variant_seeds:
        # V14b token closure: every declared value token is used, every used
        # token is declared (the {options} token is reserved for probe turns).
        bad: list[str] = []
        for s in scenarios:
            used: set[str] = set()
            for _, _, t in turn_refs(s):
                used |= set(_TOKEN_RE.findall(t["text"]))
            for field in (s.get("seed_error", {}).get("value"), s.get("initial_expected")):
                if isinstance(field, str):
                    used |= set(_TOKEN_RE.findall(field))
            for sd_key, var in s.get("variants", {}).items():
                declared = set(var.get("values", {}))
                missing = used - declared - {"options"}
                dead = declared - used
                if missing:
                    bad.append(f"{s['id']} seed {sd_key}: unbound {sorted(missing)}")
                if dead:
                    bad.append(f"{s['id']} seed {sd_key}: dead tokens {sorted(dead)}")
        record("V14b-token-closure", not bad, f"values declared == tokens used in every variant; violations: {bad[:5] or 'none'}")

        # V15 seed variation: probe texts pairwise distinct per seed; the share
        # of turns identical across ALL seeds is bounded (true replicates).
        bad = []
        identical_shares = []
        for s in scenarios:
            rendered = [render_seed_variant(s, sd) for sd in variant_seeds]
            probe_slots = [
                (si, j) for si, j, t in turn_refs(s) if t.get("probe") is not None
            ]
            for si, j in probe_slots:
                texts = {
                    next(x for x in r["sessions"] if x["index"] == si)["turns"][j - 1]["text"]
                    for r in rendered
                }
                if len(texts) != len(rendered):
                    bad.append(f"{s['id']} s{si}t{j}: probe text not distinct across seeds")
            n_turns = len(turn_refs(s))
            fixed = sum(
                1
                for slot in range(n_turns)
                if len({
                    turn_refs(r)[slot][2]["text"] for r in rendered
                }) == 1
            )
            share = fixed / n_turns if n_turns else 1.0
            identical_shares.append(round(share, 2))
            if share > 0.5:
                bad.append(f"{s['id']}: {fixed}/{n_turns} turns identical across all seeds")
        record("V15-seed-variation", not bad,
               f"probe texts distinct per seed; identical-across-seeds turn share "
               f"max {max(identical_shares) if identical_shares else 0} (need <= 0.50); violations: {bad[:5] or 'none'}")

        # V16 label orders vary per seed: pairwise-distinct orders, expected
        # label sits at >= 3 distinct positions across the seeds.
        bad = []
        for s in scenarios:
            rendered = [render_seed_variant(s, sd) for sd in variant_seeds]
            for si, j in [
                (si, j) for si, j, t in turn_refs(s) if t.get("probe") is not None
            ]:
                orders = [
                    tuple(next(x for x in r["sessions"] if x["index"] == si)["turns"][j - 1]["probe"]["labels"])
                    for r in rendered
                ]
                if len(set(orders)) != len(orders):
                    bad.append(f"{s['id']} s{si}t{j}: duplicate label order across seeds")
                positions = [
                    order.index(next(x for x in r["sessions"] if x["index"] == si)["turns"][j - 1]["probe"]["expected"])
                    for r, order in zip(rendered, orders)
                    if next(x for x in r["sessions"] if x["index"] == si)["turns"][j - 1]["probe"]["expected"] is not None
                ]
                if positions and (len(set(positions)) < 3 or max(positions.count(p) for p in set(positions)) / len(positions) > 0.6):
                    bad.append(f"{s['id']} s{si}t{j}: expected position spread {sorted(set(positions))} too concentrated")
        record("V16-label-order-varies", not bad,
               f"per-seed label orders pairwise distinct; expected position >= 3 distinct slots per scenario; violations: {bad[:5] or 'none'}")

    failed = [c for c in checks if not c["pass"]]
    return {
        "kind": "suite-v3-fixture-validation",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spec": "docs/SUITE-V3-DESIGN.md sections 3-9 (design check ids E9-E14 implemented as V4-V9 here); v3i adds V14-V16 (variant table)",
        "suite": f"fixtures/{suite}",
        "suite_sha256": suite_digest(v3_dir),
        "variant_seeds": variant_seeds,
        "scenario_count": len(scenarios),
        "scenario_instance_count": len(flat),
        "checks": checks,
        "verdict": "PASS" if not failed else "FAIL",
        "failed_checks": [c["check"] for c in failed],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=None)
    parser.add_argument("--suite", default="v3", choices=sorted(EXPECTED_PRIMARY),
                        help="fixture suite to validate (default v3; v3h = held-out CR+CU primary)")
    args = parser.parse_args()

    try:
        report = validate(LAB_ROOT / "fixtures", suite=args.suite)
    except Exception as exc:  # fail-closed on any structural error
        report = {"verdict": "FAIL", "error": f"{type(exc).__name__}: {exc}", "checks": []}

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
        print(f"verdict written: {out}")

    print(f"VERDICT: {report['verdict']}")
    for c in report.get("checks", []):
        status = "PASS" if c["pass"] else "FAIL"
        print(f"  [{status}] {c['check']}: {c['detail'][:150]}")
    return 0 if report["verdict"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
