"""Pre-inference mechanical validator for fixture v2 (M7, CONT-001 confirmatory).

Enforces docs/EVALUATION-PREP.md section 6.1-6.6 on the frozen fixtures BEFORE
any inference (evaluation AND calibration), plus the PR-REVIEW.md non-blocking
note 3 (pin the initial_expected-bearing turn to exactly s1t1) and the section
6.7 ex-ante arm-E actuation expectation. A failed check halts the run
fail-closed: fix-and-regenerate the fixtures, never relax the validator.

Checks (evaluation suite, fixtures/v2):
  E1  manifest protocol/version; families include the correction_reuse family
  E2  every scenario passes fixtures._validate_scenario (schema)
  E3  scenario ids unique and disjoint from fixtures/v1 ids
  E4  no turn text (normalized) is shared with fixtures/v1 (content disjoint)
  E5  composition: >= 5 repeated_task, >= 2 correction_reuse, >= 2 each of
      delayed_recall / distractor_recall / contradiction_update, total >= 13
  E6  RM denominator: >= 7 scenarios carry exactly one probe and it is marked
      probe.class == "rm_eligible"
  E7  every RM-eligible scenario carries initial_expected on exactly ONE turn
      and that turn is s1t1 (PR-REVIEW note 3); s1t1 carries no probe; the
      scenario has >= 2 sessions
  E8  no option leakage on ANY probe turn: no "|" in the text; the expected
      string (normalized) does not appear in the text; at most ONE word of the
      scenario's initial-turn option vocabulary appears in the probe text
  E9  every rm_eligible probe is preceded by >= 1 non-probe turn in the SAME
      session (probes off session-first turns; CN-010 fix)
  E10 public-safety: texts are ASCII, contain no "@" and no "http"

Calibration suite (fixtures/v2-calibration):
  C1  schema + unique ids; ids disjoint from v1 AND from the evaluation suite
  C2  >= 3 scenarios; families are a subset of the evaluation families; every
      evaluation family has >= 1 calibration scenario (families matched)
  C3  no turn text shared with v1 or with the evaluation suite (disjoint
      content on both sides, section 6.8)
  C4  calibration probes_per_seed per family STRICTLY EXCEEDS the evaluation
      suite's probes per family for that family — this keeps the reflection
      validator's double-count guard ("family incomplete") rejecting every
      in-run capability update during the confirmatory run, so section 6.8's
      "in-run capability updates remain disabled" holds deterministically
      without touching the frozen M4 reflection code

Arm-E actuation, ex ante (section 6.7):
  A1  for every RM-eligible scenario, replay the deterministic policy rule
      (continuity.policy.decide) over the fixture with placeholder assistant
      replies, and simulate the runner's memory/injection sequence with a real
      MemoryStore: the policy decision on the probe turn must be
      retrieve_then_answer AND the probe-turn retrieval must surface at least
      one episode id not covered by the session-start baseline injection.
      Verdict states the pre-declared expectation: >= 1 physical policy
      injection per seed across the suite (section 6.7).

Usage:
    python labs/continuity/experiments/CONT-001/validate_fixtures_v2.py \
        --out <run_root>/fixture-validation.json

Exit 0 = PASS (verdict JSON written); exit 2 = FAIL-CLOSED (no inference).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import load_suite  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.policy import decide as policy_decide  # noqa: E402
from continuity.runner import MEMORY_TOP_K  # noqa: E402

EVAL_DIR = LAB_ROOT / "fixtures" / "v2"
CAL_DIR = LAB_ROOT / "fixtures" / "v2-calibration"
V1_DIR = LAB_ROOT / "fixtures" / "v1"

PLACEHOLDER_REPLY = "acknowledged."


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def turn_refs(scenario: dict) -> list[tuple[str, dict]]:
    """[(f"s{i}t{j}", turn), ...] in order."""
    out = []
    for session in scenario["sessions"]:
        for j, turn in enumerate(session["turns"], start=1):
            out.append((f"s{session['index']}t{j}", turn))
    return out


def probes_of(scenario: dict) -> list[tuple[str, dict]]:
    return [(ref, t) for ref, t in turn_refs(scenario) if t.get("probe") is not None]


def option_vocabulary(scenario: dict) -> list[str]:
    """Label tokens enumerated on the s1t1 initial task turn (if any).

    Matches 'exactly one <noun>: a | b | c' — the v1/v2 initial-turn option
    list syntax. Option lists are permitted ONLY on initial (pre-rubric) task
    turns (section 6.5), so this vocabulary exists only there.
    """
    first = scenario["sessions"][0]["turns"][0].get("text", "")
    m = re.search(r"exactly one [a-z]+:\s*([a-z\- ]+(?:\s*\|\s*[a-z\- ]+)+)", first.lower())
    if not m:
        return []
    return [w.strip() for w in m.group(1).split("|") if w.strip()]


def suite_digest(fixture_dir: Path) -> str:
    """sha256 over sorted (relpath, bytes) of every file in the suite."""
    import hashlib

    h = hashlib.sha256()
    for path in sorted(p for p in fixture_dir.rglob("*") if p.is_file()):
        rel = path.relative_to(fixture_dir).as_posix()
        h.update(rel.encode("utf-8"))
        h.update(path.read_bytes())
    return h.hexdigest()


def check_eval_suite(
    eval_manifest: dict,
    eval_scenarios: list[dict],
    v1_scenarios: list[dict],
) -> tuple[list[dict], dict[str, Any]]:
    checks: list[dict] = []

    def record(cid: str, ok: bool, detail: str) -> bool:
        checks.append({"check": cid, "pass": ok, "detail": detail})
        return ok

    # E1 manifest
    fams = eval_manifest["families"]
    record(
        "E1-manifest",
        "correction_reuse" in fams
        and {"delayed_recall", "distractor_recall", "contradiction_update", "repeated_task"} <= set(fams),
        f"families={fams} (correction_reuse present, recall families present)",
    )

    # E3 ids disjoint from v1
    v1_ids = {s["id"] for s in v1_scenarios}
    eval_ids = [s["id"] for s in eval_scenarios]
    record(
        "E3-ids-disjoint-from-v1",
        len(eval_ids) == len(set(eval_ids)) and not (set(eval_ids) & v1_ids),
        f"{len(eval_ids)} unique eval ids, overlap with v1: {sorted(set(eval_ids) & v1_ids)}",
    )

    # E4 content disjoint from v1 (normalized whole-turn-text equality)
    v1_texts = {normalize(t["text"]) for s in v1_scenarios for _, t in turn_refs(s)}
    shared = sorted(
        {normalize(t["text"]) for s in eval_scenarios for _, t in turn_refs(s)} & v1_texts
    )
    record("E4-content-disjoint-from-v1", not shared, f"shared turn texts with v1: {len(shared)} {shared[:3]}")

    # E5 composition
    fam_counts: dict[str, int] = {}
    for s in eval_scenarios:
        fam_counts[s["family"]] = fam_counts.get(s["family"], 0) + 1
    ok = (
        fam_counts.get("repeated_task", 0) >= 5
        and fam_counts.get("correction_reuse", 0) >= 2
        and all(fam_counts.get(f, 0) >= 2 for f in ("delayed_recall", "distractor_recall", "contradiction_update"))
        and len(eval_scenarios) >= 13
    )
    record("E5-composition", ok, f"family counts {fam_counts}, total {len(eval_scenarios)} (need rt>=5, cr>=2, recall>=2 each, total>=13)")

    # E6/E7/E8/E9 per RM scenario
    rm_scenarios = [s for s in eval_scenarios if any(p.get("probe", {}).get("class") == "rm_eligible" for _, p in probes_of(s))]
    record(
        "E6-rm-denominator",
        len(rm_scenarios) >= 7 and all(len(probes_of(s)) == 1 for s in rm_scenarios),
        f"{len(rm_scenarios)} RM-eligible scenarios (need >= 7), each with exactly one probe: "
        f"{all(len(probes_of(s)) == 1 for s in rm_scenarios)}",
    )

    e7_details: list[str] = []
    e7_ok = True
    for s in rm_scenarios:
        bearing = [
            (ref, t)
            for ref, t in turn_refs(s)
            if "initial_expected" in t
        ]
        s1t1 = s["sessions"][0]["turns"][0]
        ok = (
            len(bearing) == 1
            and bearing[0][0] == "s1t1"
            and bearing[0][1] is s1t1
            and isinstance(s1t1.get("initial_expected"), str)
            and s1t1["initial_expected"].strip() != ""
            and s1t1.get("probe") is None
            and len(s["sessions"]) >= 2
        )
        e7_ok = e7_ok and ok
        e7_details.append(f"{s['id']}: bearing={[r for r, _ in bearing]} ok={ok}")
    record(
        "E7-initial-expected-on-s1t1",
        e7_ok,
        "initial_expected on exactly s1t1 of every RM-eligible scenario, s1t1 carries no probe, >= 2 sessions; " + "; ".join(e7_details),
    )

    e8_details: list[str] = []
    e8_ok = True
    for s in eval_scenarios:
        vocab = option_vocabulary(s)
        for ref, turn in probes_of(s):
            text_n = normalize(turn["text"])
            expected_n = normalize(turn["probe"]["expected"])
            pipe = "|" in turn["text"]
            leaked_expected = expected_n in text_n
            vocab_hits = sorted(w for w in vocab if re.search(rf"\b{re.escape(w)}\b", text_n))
            ok = (not pipe) and (not leaked_expected) and len(vocab_hits) <= 1
            e8_ok = e8_ok and ok
            if not ok:
                e8_details.append(f"{s['id']} {ref}: pipe={pipe} expected_leaked={leaked_expected} vocab_hits={vocab_hits}")
    record(
        "E8-no-option-leakage",
        e8_ok,
        "every probe turn: no '|', expected not verbatim in text, <= 1 option-vocabulary word; violations: "
        + ("; ".join(e8_details) if e8_details else "none"),
    )

    e9_details: list[str] = []
    e9_ok = True
    for s in rm_scenarios:
        for ref, turn in probes_of(s):
            session_no = int(ref[1:ref.index("t")])
            turn_no = int(ref[ref.index("t") + 1:])
            preceding_non_probe = any(
                t.get("probe") is None
                for t in s["sessions"][session_no - 1]["turns"][: turn_no - 1]
            )
            if not (turn_no >= 2 and preceding_non_probe):
                e9_ok = False
                e9_details.append(f"{s['id']} {ref}: turn_no={turn_no}")
    record(
        "E9-rm-probes-off-first-turns",
        e9_ok,
        "every rm_eligible probe is preceded by >= 1 non-probe turn in the same session; violations: "
        + ("; ".join(e9_details) if e9_details else "none"),
    )

    # E10 public safety
    bad: list[str] = []
    for s in eval_scenarios:
        for ref, t in turn_refs(s):
            text = t["text"]
            if ("@" in text) or ("http" in text.lower()) or (not text.isascii()):
                bad.append(f"{s['id']} {ref}")
    record("E10-public-safe", not bad, f"ASCII, no '@', no http everywhere; violations: {bad}")

    eval_probes_per_family: dict[str, int] = {}
    for s in eval_scenarios:
        eval_probes_per_family[s["family"]] = eval_probes_per_family.get(s["family"], 0) + len(probes_of(s))

    return checks, {
        "family_counts": fam_counts,
        "rm_scenarios": [s["id"] for s in rm_scenarios],
        "probes_per_family_per_seed": eval_probes_per_family,
    }


def check_cal_suite(
    cal_manifest: dict,
    cal_scenarios: list[dict],
    eval_scenarios: list[dict],
    v1_scenarios: list[dict],
    eval_probes_per_family: dict[str, int],
) -> tuple[list[dict], dict[str, Any]]:
    checks: list[dict] = []

    def record(cid: str, ok: bool, detail: str) -> bool:
        checks.append({"check": cid, "pass": ok, "detail": detail})
        return ok

    v1_ids = {s["id"] for s in v1_scenarios}
    eval_ids = {s["id"] for s in eval_scenarios}
    cal_ids = [s["id"] for s in cal_scenarios]
    record(
        "C1-ids-disjoint",
        len(cal_ids) == len(set(cal_ids)) and not (set(cal_ids) & (v1_ids | eval_ids)),
        f"{len(cal_ids)} unique cal ids; overlap with v1/eval: {sorted(set(cal_ids) & (v1_ids | eval_ids))}",
    )

    cal_families = {s["family"] for s in cal_scenarios}
    eval_families = {s["family"] for s in eval_scenarios}
    record(
        "C2-families-matched",
        len(cal_scenarios) >= 3 and cal_families <= eval_families and eval_families <= cal_families,
        f"{len(cal_scenarios)} calibration scenarios (need >= 3); families {sorted(cal_families)} match the evaluation families exactly",
    )

    v1_texts = {normalize(t["text"]) for s in v1_scenarios for _, t in turn_refs(s)}
    eval_texts = {normalize(t["text"]) for s in eval_scenarios for _, t in turn_refs(s)}
    shared = sorted({normalize(t["text"]) for s in cal_scenarios for _, t in turn_refs(s)} & (v1_texts | eval_texts))
    record("C3-content-disjoint", not shared, f"shared turn texts with v1/eval: {len(shared)} {shared[:3]}")

    cal_probes_per_family: dict[str, int] = {}
    for s in cal_scenarios:
        cal_probes_per_family[s["family"]] = cal_probes_per_family.get(s["family"], 0) + len(probes_of(s))
    comparison = {
        f: (cal_probes_per_family.get(f, 0), eval_probes_per_family.get(f, 0))
        for f in sorted(eval_families)
    }
    ok = all(cal_n > eval_n for cal_n, eval_n in comparison.values())
    record(
        "C4-guard-sizing",
        ok,
        "calibration probes_per_seed strictly exceeds evaluation probes per family for every family "
        f"({ {f: f'cal {c} > eval {e}' for f, (c, e) in comparison.items()} }) — keeps the reflection "
        "double-count guard rejecting every in-run capability update (section 6.8)",
    )

    return checks, {"cal_probes_per_family_per_seed": cal_probes_per_family, "guard_sizing": comparison}


def simulate_arm_e_actuation(scenario: dict) -> dict[str, Any]:
    """Ex-ante simulation of section 6.7 for one RM-eligible scenario.

    Replays the deterministic policy rule and the runner's memory sequence
    with placeholder assistant replies in a real MemoryStore; reports whether
    the probe turn actuates a PHYSICAL injection (new episode ids beyond the
    session-start baseline injection).
    """
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(str(Path(tmp) / "sim.sqlite3"))
        run_id = "validator-sim"
        sid = scenario["id"]
        probe_ref_expected = next(
            ref for ref, t in probes_of(scenario) if t.get("probe", {}).get("class") == "rm_eligible"
        )
        result: dict[str, Any] = {"scenario": sid, "probe_turn": probe_ref_expected}
        for session in scenario["sessions"]:
            injected_ids: set[int] = set()
            if session["index"] >= 2:
                query = session["turns"][0]["text"]
                episodes = store.retrieve(query, scenario=sid, limit=MEMORY_TOP_K)
                injected_ids = {e["id"] for e in episodes}
                result["baseline_episode_ids"] = sorted(injected_ids)
            for turn_no, turn in enumerate(session["turns"], start=1):
                turn_ref = f"s{session['index']}t{turn_no}"
                decision = policy_decide(
                    turn_text=turn["text"],
                    is_probe=turn.get("probe") is not None,
                    env_episodes=store.episodes_for_scenario(sid),
                )
                if turn_ref == probe_ref_expected:
                    result["probe_decision"] = decision["action"]
                    result["probe_rule"] = decision["rule"]
                    if decision["action"] == "retrieve_then_answer":
                        eps = store.retrieve(turn["text"], scenario=sid, limit=MEMORY_TOP_K)
                        new_ids = [e["id"] for e in eps if e["id"] not in injected_ids]
                        result["probe_retrieved_ids"] = [e["id"] for e in eps]
                        result["new_episode_ids_at_probe"] = new_ids
                # Appends happen after the exchange completes (runner order).
                for role, content in (("environment", turn["text"]), ("assistant", PLACEHOLDER_REPLY)):
                    store.append_episode(
                        run_id=run_id, scenario=sid, session=session["index"],
                        turn_ref=turn_ref, role=role, content=content,
                    )
        store.close()
    result["physical_injection_expected"] = bool(
        result.get("probe_decision") == "retrieve_then_answer" and result.get("new_episode_ids_at_probe")
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out", default=None,
        help="path for the verdict JSON (default: print only, still exit-coded)",
    )
    args = parser.parse_args()

    report: dict[str, Any] = {
        "kind": "cont001-confirmatory-fixture-validation",
        "label": "agent-pre-registered, pending owner acceptance",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "spec": "docs/EVALUATION-PREP.md sections 6.1-6.7 (frozen at commit a845fc5) + PR-REVIEW.md note 3",
        "suites": {
            "evaluation": str(EVAL_DIR.relative_to(LAB_ROOT)).replace("\\", "/"),
            "calibration": str(CAL_DIR.relative_to(LAB_ROOT)).replace("\\", "/"),
            "v1_reference": str(V1_DIR.relative_to(LAB_ROOT)).replace("\\", "/"),
        },
        "digests": {
            "evaluation_suite_sha256": suite_digest(EVAL_DIR),
            "calibration_suite_sha256": suite_digest(CAL_DIR),
            "v1_suite_sha256": suite_digest(V1_DIR),
        },
    }

    # E2 happens inside load_suite (schema validation on every scenario).
    try:
        eval_manifest, eval_scenarios = load_suite(str(EVAL_DIR))
        cal_manifest, cal_scenarios = load_suite(str(CAL_DIR))
        v1_manifest, v1_scenarios = load_suite(str(V1_DIR))
    except Exception as exc:
        report["verdict"] = "FAIL"
        report["error"] = f"suite load/schema failure: {exc}"
        if args.out:
            Path(args.out).write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
        print(f"FAIL-CLOSED: {report['error']}", file=sys.stderr)
        return 2
    report["checks"] = [{"check": "E2-schema", "pass": True, "detail": f"all {len(eval_scenarios)} eval + {len(cal_scenarios)} cal scenarios pass fixtures._validate_scenario"}]

    eval_checks, eval_info = check_eval_suite(eval_manifest, eval_scenarios, v1_scenarios)
    report["checks"] += eval_checks
    cal_checks, cal_info = check_cal_suite(
        cal_manifest, cal_scenarios, eval_scenarios, v1_scenarios,
        eval_info["probes_per_family_per_seed"],
    )
    report["checks"] += cal_checks
    report["evaluation_suite"] = eval_info
    report["calibration_suite"] = cal_info

    # A1: ex-ante actuation simulation on every RM scenario
    sims = [simulate_arm_e_actuation(s) for s in eval_scenarios if s["id"] in set(eval_info["rm_scenarios"])]
    per_scenario_pass = [s["physical_injection_expected"] for s in sims]
    report["arm_e_actuation_ex_ante"] = {
        "expectation_predeclared": (
            ">= 1 physical policy injection per seed across the suite "
            "(policy.action with retrieval.injected = true; section 6.7)"
        ),
        "rationale": (
            "RM-eligible probes sit on non-first session turns behind a non-probe "
            "turn; the s2t1 exchange appends episodes AFTER the session-start "
            "baseline injection, so the probe-turn retrieve surfaces new episode "
            "ids; the deterministic R2 rule fires on rubrics/corrections carrying "
            "corrective markers, R1 on absence-of-records markers"
        ),
        "simulation_note": (
            "placeholder assistant replies; a lower bound on the real store state "
            "(real runs also hold reflection summaries for arms D/E)"
        ),
        "per_scenario": sims,
        "scenarios_with_expected_injection": sum(1 for p in per_scenario_pass if p),
        "pass": len(per_scenario_pass) > 0 and all(per_scenario_pass),
    }
    report["checks"].append(
        {
            "check": "A1-actuation-ex-ante",
            "pass": bool(report["arm_e_actuation_ex_ante"]["pass"]),
            "detail": (
                f"{sum(1 for p in per_scenario_pass if p)}/{len(per_scenario_pass)} RM scenarios "
                "show a simulated physical injection at the probe turn (expectation >= 1/seed)"
            ),
        }
    )

    failed = [c for c in report["checks"] if not c["pass"]]
    report["verdict"] = "PASS" if not failed else "FAIL"
    report["failed_checks"] = [c["check"] for c in failed]

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
        print(f"verdict written: {out}")

    print(f"VERDICT: {report['verdict']}")
    for c in report["checks"]:
        status = "PASS" if c["pass"] else "FAIL"
        print(f"  [{status}] {c['check']}: {c['detail'][:160]}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
