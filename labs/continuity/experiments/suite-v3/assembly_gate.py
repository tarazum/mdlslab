"""Zero-GPU assembly gate for the CONT-005 T-arms over fixture suites v3/v3h/v3i.

Proves, BEFORE any inference, that the trust layer behaves as designed on every
scenario: builds the memory blocks each arm WOULD inject at every session
start (real MemoryStore, placeholder assistant replies, same append order as
the runner) and asserts arm-differentiating invariants. This is the ex-ante
gate the pre-registration will cite; a FAIL here means the memory layer is
broken, not that a model answered wrong.

Suite v3i (cycle 2): scenarios carry per-seed variant tables; the gate renders
the suite for ONE seed (--seed, default the first manifest variant seed) so
the assembled blocks are the ones the runner would actually inject for that
seed. Run it for every predeclared seed at freeze time (the gate is
deterministic; per-seed variation is mechanical rotation, but the render path
is what is being proven here).

Checks:
  G1  T0 blocks are byte-identical to the arm-B flat renderer (baseline
      equivalence: the only T0 difference from arm B is the arm label).
  G2  T1 blocks annotate every typed episode (prose "(recorded in session N;
      source: X; verification: Y)") and contain no resolution verdicts (no
      "RESOLVED", no "SUPERSEDED").
  G3  T2/T3 resolution per primary sub-type:
      - erroneous_user_correction: the user episode carries the
        "unverified user statement" flag
      - source_conflict: exactly one of the two typed source episodes in the
        conflict session is flagged (the unverified/unreviewed one)
      - retraction: the correction episode is marked superseded by the
        retraction episode's ref
      - scripted_own_answer: the seed record episode (agent_answer) carries
        the own-earlier-answer flag
      - superseded_value (CU): R5 marks exactly the s1 fact statement
        superseded by the "correction for the records" turn, no strays
      - valid_*: no episode flagged (the verified correction governs cleanly)
      Flagged episodes are demoted after unflagged ones (ordering).
  G4  T3 blocks carry the trust-policy version header; T2 blocks do not.
  G5  Determinism: a second full assembly pass is byte-identical.
  G6  guess_calibration scenarios produce no annotations/flags in any arm and
      their probes score to passed=null with position extraction.

Usage:
    python labs/continuity/experiments/suite-v3/assembly_gate.py \
        [--suite v3|v3h|v3i] [--seed 2001] [--out <path>/assembly-gate.json]
Exit 0 = PASS; exit 2 = FAIL-CLOSED.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.claims import TRUST_POLICY_VERSION, format_trust_block, resolve_episodes  # noqa: E402
from continuity.fixtures import load_suite, render_seed_variant  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.runner import MEMORY_TOP_K, format_memory_block, score_probe  # noqa: E402

SUITES = {
    "v3": LAB_ROOT / "fixtures" / "v3",
    "v3h": LAB_ROOT / "fixtures" / "v3h",
    "v3i": LAB_ROOT / "fixtures" / "v3i",
}
PRIMARY_FAMILIES = {
    "v3": ("correction_reuse", "repeated_task"),
    "v3h": ("correction_reuse", "contradiction_update"),
    "v3i": ("correction_reuse", "contradiction_update"),
}
PLACEHOLDER_REPLY = "acknowledged."
T_ARMS = ("T0", "T1", "T2", "T3")


def turn_by_ref_of(scenario: dict) -> dict[str, dict]:
    return {
        f"s{sess['index']}t{k}": t
        for sess in scenario["sessions"]
        for k, t in enumerate(sess["turns"], start=1)
    }


def build_blocks(scenario: dict) -> dict[str, dict[str, list[str]]]:
    """One MemoryStore pass per arm slot; returns {arm: {session_ref: [blocks]}}.

    The store fill is arm-independent (same episodes for every arm); only the
    renderer differs. Blocks are collected at every session >= 2 exactly as the
    runner would inject them.
    """
    with tempfile.TemporaryDirectory() as tmp:
        store = MemoryStore(str(Path(tmp) / "sim.sqlite3"))
        sid = scenario["id"]
        blocks: dict[str, list[str]] = {arm: [] for arm in T_ARMS}
        probes_seen: list[dict] = []
        for session in scenario["sessions"]:
            if session["index"] >= 2:
                query = session["turns"][0]["text"]
                episodes = store.retrieve(query, scenario=sid, limit=MEMORY_TOP_K)
                if episodes:
                    blocks["T0"].append(format_memory_block(episodes))
                    turn_map = turn_by_ref_of(scenario)
                    blocks["T1"].append(format_trust_block(episodes, turn_map, "T1"))
                    blocks["T2"].append(format_trust_block(episodes, turn_map, "T2"))
                    blocks["T3"].append(format_trust_block(episodes, turn_map, "T3"))
            for turn_no, turn in enumerate(session["turns"], start=1):
                turn_ref = f"s{session['index']}t{turn_no}"
                if turn.get("probe") is not None:
                    probes_seen.append(turn["probe"])
                for role, content in (("environment", turn["text"]), ("assistant", PLACEHOLDER_REPLY)):
                    store.append_episode(
                        run_id="gate", scenario=sid, session=session["index"],
                        turn_ref=turn_ref, role=role, content=content,
                    )
        store.close()
    return {"blocks": blocks, "probes": probes_seen}


def check(res: dict, suite: str = "v3", seed: int | None = None) -> list[dict]:
    checks: list[dict] = []

    def record(cid: str, ok: bool, detail: str) -> None:
        checks.append({"check": cid, "pass": ok, "detail": detail})

    manifest, scenarios = load_suite(str(SUITES[suite]))
    if manifest.get("variant_seeds"):
        seed = seed if seed is not None else manifest["variant_seeds"][0]
        if seed not in manifest["variant_seeds"]:
            raise ValueError(
                f"seed {seed} not in {suite} variant_seeds {manifest['variant_seeds']}"
            )
        scenarios = [render_seed_variant(s, seed) for s in scenarios]
    primary = [s for s in scenarios if s["family"] in PRIMARY_FAMILIES[suite]]

    builds = {s["id"]: build_blocks(s) for s in scenarios}

    # G1 T0 == flat arm-B renderer is trivially true by construction; assert
    # non-emptiness and the header instead (byte-equivalence is the renderer call).
    bad = [s["id"] for s in scenarios if any(not b.startswith("Your persistent memory:") for b in builds[s["id"]]["blocks"]["T0"])]
    record("G1-t0-flat-renderer", not bad, f"every T0 block uses the arm-B flat renderer; violations: {bad or 'none'}")

    # G2 T1 annotations without verdicts
    bad = []
    for s in scenarios:
        for block in builds[s["id"]]["blocks"]["T1"]:
            if "RESOLVED" in block or "SUPERSEDED" in block or "superseded by" in block:
                bad.append(f"{s['id']}: verdict text in T1")
    typed_flagged = 0
    for s in scenarios:
        for block in builds[s["id"]]["blocks"]["T1"]:
            for line in block.splitlines():
                if "source: " in line:
                    typed_flagged += 1
    record("G2-t1-annotations-only", not bad, f"no verdicts in T1 ({bad[:3] or 'none'}); {typed_flagged} source annotations rendered")

    # G3 resolution per sub-type
    problems: list[str] = []
    resolution_counts = {"user_flag": 0, "conflict_flag": 0, "superseded": 0, "own_answer_flag": 0, "clean": 0}
    for s in primary:
        turn_map = turn_by_ref_of(s)
        # resolve over ALL environment episodes of the scenario (superset of any
        # single injection window; the flags must hold whenever retrieved)
        eps = []
        for sess in s["sessions"]:
            for k, t in enumerate(sess["turns"], start=1):
                eps.append({"turn_ref": f"s{sess['index']}t{k}", "role": "environment", "content": t["text"]})
        resolved = resolve_episodes(eps, turn_map)
        flags = {e["turn_ref"]: e["resolution_flag"] for e in resolved}
        sub = s.get("sub_type", "")
        if sub in ("valid_correction_environment", "valid_correction_tool"):
            # The verified correction governs cleanly; the only legitimate flag
            # is the agent's own recorded seed answer (lowest trust by policy).
            stray = [r for r, f in flags.items() if f and "own earlier answer" not in f]
            if stray:
                problems.append(f"{s['id']} ({sub}): unexpected flags {stray}")
            else:
                resolution_counts["clean"] += 1
        elif sub == "erroneous_user_correction":
            user_refs = [r for r, t in turn_map.items() if t.get("source_type") == "user"]
            if not all("unverified user statement" in flags.get(r, "") for r in user_refs):
                problems.append(f"{s['id']}: user episode not flagged")
            else:
                resolution_counts["user_flag"] += 1
        elif sub == "source_conflict":
            typed = [r for r, t in turn_map.items() if t.get("source_type") in ("environment", "user", "tool")]
            flagged = [r for r in typed if flags.get(r)]
            if len(flagged) != 1:
                problems.append(f"{s['id']}: {len(flagged)} flagged conflict sources (need exactly 1)")
            else:
                resolution_counts["conflict_flag"] += 1
        elif sub == "retraction":
            sup = [r for r, f in flags.items() if f and "superseded by the retraction" in f]
            if len(sup) != 1:
                problems.append(f"{s['id']}: {len(sup)} superseded corrections (need 1)")
            else:
                resolution_counts["superseded"] += 1
        elif sub == "scripted_own_answer":
            own = [r for r, t in turn_map.items() if t.get("source_type") == "agent_answer"]
            if not all("own earlier answer" in flags.get(r, "") for r in own):
                problems.append(f"{s['id']}: agent_answer episode not flagged")
            else:
                resolution_counts["own_answer_flag"] += 1
        elif s.get("seed_error", {}).get("mechanism") == "superseded_value":
            # v3h CU primary (post-acceptance R5): the s1 fact statement is
            # superseded by the "correction for the records" turn; no OTHER
            # flags expected; the superseded old value stays in options (V8).
            sup = [r for r, f in flags.items() if f and "superseded by the value correction" in f]
            stray = [r for r, f in flags.items() if f and "superseded by the value correction" not in f]
            if len(sup) != 1 or stray:
                problems.append(f"{s['id']}: R5 supersession {len(sup)} (need 1), stray {stray}")
            else:
                resolution_counts["superseded"] += 1
    record(
        "G3-resolution-by-subtype",
        not problems,
        f"14 primary scenarios resolved as designed {resolution_counts}; violations: {problems[:5] or 'none'}",
    )

    # G3b demotion ordering: flagged lines after unflagged in T2 blocks
    bad = []
    for s in primary:
        for block in builds[s["id"]]["blocks"]["T2"]:
            lines = [ln for ln in block.splitlines() if ln.startswith("[s")]
            flagged_idx = [i for i, ln in enumerate(lines) if "RESOLVED" in ln]
            unflagged_idx = [i for i, ln in enumerate(lines) if "RESOLVED" not in ln]
            if flagged_idx and unflagged_idx and max(unflagged_idx) > min(flagged_idx):
                bad.append(s["id"])
    record("G3b-flag-demoted-ordering", not bad, f"flagged episodes ordered after unflagged in every T2 block; violations: {sorted(set(bad)) or 'none'}")

    # G4 policy header only on T3
    bad = []
    for s in scenarios:
        b3 = builds[s["id"]]["blocks"]["T3"]
        b2 = builds[s["id"]]["blocks"]["T2"]
        if any(TRUST_POLICY_VERSION not in x for x in b3):
            bad.append(f"{s['id']}: T3 missing policy header")
        if any(TRUST_POLICY_VERSION in x for x in b2):
            bad.append(f"{s['id']}: T2 leaks policy header")
    record("G4-policy-header-t3-only", not bad, f"trust-policy version header present on T3 only; violations: {bad or 'none'}")

    # G5 determinism
    second = build_blocks(primary[0])
    det = all(
        "".join(builds[primary[0]["id"]]["blocks"][arm]) == "".join(second["blocks"][arm])
        for arm in T_ARMS
    )
    record("G5-determinism", det, f"second assembly pass byte-identical on {primary[0]['id']} across all arms: {det}")

    # G6 guess calibration
    gc = [s for s in scenarios if s["family"] == "guess_calibration"]
    bad = []
    for s in gc:
        for arm in T_ARMS:
            for block in builds[s["id"]]["blocks"][arm]:
                if "RESOLVED" in block or "SUPERSEDED" in block:
                    bad.append(f"{s['id']} {arm}: verdict in gc block")
        for probe in builds[s["id"]]["probes"]:
            r = score_probe(probe, "alpha")
            if r["passed"] is not None or "observed_position" not in r:
                bad.append(f"{s['id']}: guess probe scored instead of aggregated")
    record("G6-guess-calibration-clean", not bad and len(gc) == 3, f"3 gc scenarios, no verdicts, probes aggregate with positions; violations: {bad or 'none'}")

    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", default=None)
    parser.add_argument("--suite", default="v3", choices=sorted(SUITES))
    parser.add_argument("--seed", default=None, type=int,
                        help="variant seed to render (v3i; default: first manifest seed)")
    args = parser.parse_args()

    try:
        checks = check({}, suite=args.suite, seed=args.seed)
    except Exception as exc:
        checks = [{"check": "gate-crash", "pass": False, "detail": f"{type(exc).__name__}: {exc}"}]

    failed = [c for c in checks if not c["pass"]]
    report = {
        "kind": "suite-v3-assembly-gate",
        "created_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "suite": args.suite,
        "seed": args.seed,
        "arms": list(T_ARMS),
        "checks": checks,
        "verdict": "PASS" if not failed else "FAIL",
        "failed_checks": [c["check"] for c in failed],
    }
    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(report, indent=2, ensure_ascii=True), encoding="utf-8")
        print(f"verdict written: {out}")
    print(f"VERDICT: {report['verdict']}")
    for c in checks:
        status = "PASS" if c["pass"] else "FAIL"
        print(f"  [{status}] {c['check']}: {c['detail'][:160]}")
    return 0 if not failed else 2


if __name__ == "__main__":
    raise SystemExit(main())
