"""Versioned self-model store (arm C MVP, stdlib only).

Scope: a JSON file holding MEASURED estimates of the agent's own
capabilities plus recorded known failure patterns. Two hard rules from the
M3 brief:

1. Estimates are always derived from committed result artifacts (pilot
   aggregates) with full provenance — never self-declared. `validate()`
   recomputes every rate/interval from the entry's own counts and rejects
   any mismatch, so a hand-edited "capability" number fails the commit.
2. Commits are deterministic and fail-closed: schema check, revision must
   increment by exactly 1 (or be 1 for a new store), and every estimate
   must carry provenance. Anything else raises `SelfModelError` and nothing
   is written.

The self-model deliberately contains ONLY measured facts and recorded
findings. LLM-proposed revisions, reflection, and consolidation are arm D /
M4 and are out of scope here (`lastConsolidation` is null until then).

Known caveat (CN-009): the revision-1 estimates come from the same fixture
suite on which arm C is evaluated (mini-pilot exposure). Recorded in
provenance so CONT-001 design can account for it.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

SELFMODEL_FORMAT = "continuity-selfmodel"
SCHEMA_VERSION = 1
Z95 = 1.959963984540054  # two-sided 95% normal quantile

_CAPABILITY_REQUIRED = (
    "family", "unit", "passed", "total", "seeds", "probes_per_seed",
    "rate", "wilson95", "binomial_sd", "provenance",
)
_PATTERN_REQUIRED = ("id", "title", "pattern", "evidence")


class SelfModelError(ValueError):
    """Deterministic validation failure — nothing is written when raised."""


def _utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def wilson_interval(passed: int, total: int, z: float = Z95) -> dict[str, float]:
    """Wilson score interval for a binomial proportion (bounded, behaves at 0/1)."""
    if total <= 0:
        raise ValueError("total must be > 0")
    if not 0 <= passed <= total:
        raise ValueError("passed must be within [0, total]")
    n = float(total)
    phat = passed / n
    denom = 1.0 + z * z / n
    center = (phat + z * z / (2.0 * n)) / denom
    half = (z / denom) * math.sqrt(phat * (1.0 - phat) / n + z * z / (4.0 * n * n))
    return {
        "low": round(max(0.0, center - half), 3),
        "high": round(min(1.0, center + half), 3),
    }


def binomial_sd(passed: int, total: int) -> float:
    """Plain binomial SD sqrt(p(1-p)/n) — 0 at the boundaries (caveat: Wilson
    is the primary uncertainty reported; SD is informational)."""
    if total <= 0:
        raise ValueError("total must be > 0")
    p = passed / total
    return round(math.sqrt(p * (1.0 - p) / total), 4)


def validate(model: dict[str, Any]) -> list[str]:
    """Deterministic schema + provenance + arithmetic checks. All errors returned."""
    errors: list[str] = []

    if not isinstance(model, dict):
        return ["model is not a JSON object"]
    if model.get("format") != SELFMODEL_FORMAT:
        errors.append(f"format must be {SELFMODEL_FORMAT!r}")
    if model.get("schemaVersion") != SCHEMA_VERSION:
        errors.append(f"schemaVersion must be {SCHEMA_VERSION}")
    if not isinstance(model.get("agentId"), str) or not model["agentId"].strip():
        errors.append("agentId must be a non-empty string")
    revision = model.get("revision")
    if not isinstance(revision, int) or isinstance(revision, bool) or revision < 1:
        errors.append("revision must be an integer >= 1")
    for field in ("createdUtc", "updatedUtc"):
        if not isinstance(model.get(field), str) or not model[field].strip():
            errors.append(f"{field} must be a non-empty ISO string")
    lc = model.get("lastConsolidation")
    if lc is not None and not (isinstance(lc, str) and lc.strip()):
        errors.append("lastConsolidation must be null or a non-empty ISO string")

    capabilities = model.get("capabilities")
    if not isinstance(capabilities, list) or not capabilities:
        errors.append("capabilities must be a non-empty list")
        capabilities = []
    seen_families: set[str] = set()
    for i, cap in enumerate(capabilities):
        where = f"capabilities[{i}]"
        if not isinstance(cap, dict):
            errors.append(f"{where}: entry is not an object")
            continue
        for field in _CAPABILITY_REQUIRED:
            if field not in cap:
                errors.append(f"{where}: missing field {field!r}")
        family = cap.get("family")
        if not isinstance(family, str) or not family.strip():
            errors.append(f"{where}: family must be a non-empty string")
        elif family in seen_families:
            errors.append(f"{where}: duplicate family {family!r}")
        else:
            seen_families.add(family)
        passed, total = cap.get("passed"), cap.get("total")
        if not isinstance(passed, int) or isinstance(passed, bool) or passed < 0:
            errors.append(f"{where}: passed must be an integer >= 0")
            passed = None
        if not isinstance(total, int) or isinstance(total, bool) or total <= 0:
            errors.append(f"{where}: total must be an integer > 0")
            total = None
        if passed is not None and total is not None:
            if passed > total:
                errors.append(f"{where}: passed > total")
            else:
                # The estimates are derived, not declared: recompute and compare.
                if cap.get("rate") != round(passed / total, 3):
                    errors.append(
                        f"{where}: rate {cap.get('rate')!r} != recomputed "
                        f"{round(passed / total, 3)}"
                    )
                wilson = wilson_interval(passed, total)
                if cap.get("wilson95") != wilson:
                    errors.append(
                        f"{where}: wilson95 {cap.get('wilson95')!r} != recomputed {wilson}"
                    )
                if cap.get("binomial_sd") != binomial_sd(passed, total):
                    errors.append(f"{where}: binomial_sd does not match recomputation")
        seeds = cap.get("seeds")
        if not isinstance(seeds, list) or not seeds:
            errors.append(f"{where}: seeds must be a non-empty list")
        pps = cap.get("probes_per_seed")
        if not isinstance(pps, int) or isinstance(pps, bool) or pps < 1:
            errors.append(f"{where}: probes_per_seed must be an integer >= 1")
        elif isinstance(seeds, list) and isinstance(total, int) and total != pps * len(seeds):
            errors.append(
                f"{where}: total {total} != probes_per_seed {pps} x seeds {len(seeds)}"
            )
        prov = cap.get("provenance")
        if not isinstance(prov, dict):
            errors.append(f"{where}: provenance must be an object")
        else:
            for field in ("source_artifact", "method", "numbers"):
                if field not in prov or prov[field] in (None, "", {}, []):
                    errors.append(f"{where}: provenance.{field} missing/empty")

    patterns = model.get("knownFailurePatterns")
    if not isinstance(patterns, list):
        errors.append("knownFailurePatterns must be a list")
        patterns = []
    for i, pat in enumerate(patterns):
        where = f"knownFailurePatterns[{i}]"
        if not isinstance(pat, dict):
            errors.append(f"{where}: entry is not an object")
            continue
        for field in _PATTERN_REQUIRED:
            if field not in pat or not str(pat.get(field, "")).strip():
                errors.append(f"{where}: missing/empty field {field!r}")
        evidence = pat.get("evidence")
        if not isinstance(evidence, dict) or not isinstance(evidence.get("refs"), list) or not evidence["refs"]:
            errors.append(f"{where}: evidence.refs must be a non-empty list")

    prov = model.get("provenance")
    if not isinstance(prov, dict):
        errors.append("top-level provenance must be an object")
    else:
        for field in ("derived_from", "method"):
            if field not in prov or not str(prov.get(field, "")).strip():
                errors.append(f"provenance.{field} missing/empty")
    return errors


def canonical_bytes(model: dict[str, Any]) -> bytes:
    return json.dumps(model, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("utf-8")


def selfmodel_sha256(model: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_bytes(model)).hexdigest()


def commit(path: str, candidate: dict[str, Any]) -> dict[str, Any]:
    """Validate + atomically write `candidate` as the next revision at `path`.

    Fail-closed rules: the candidate must pass `validate()`; its revision must
    be exactly (previous revision + 1), or exactly 1 when creating a new
    store. On any failure nothing is written and SelfModelError is raised.
    """
    errors = validate(candidate)
    if errors:
        raise SelfModelError("candidate rejected (validation): " + "; ".join(errors))
    store_path = Path(path)
    previous = None
    if store_path.exists():
        try:
            previous = json.loads(store_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as exc:
            raise SelfModelError(f"existing store unreadable: {exc}") from exc
        prev_errors = validate(previous)
        if prev_errors:
            raise SelfModelError(
                "existing store invalid (refusing to build on it): " + "; ".join(prev_errors)
            )
        prev_rev = previous.get("revision")
        expected = prev_rev + 1 if isinstance(prev_rev, int) else None
        if candidate["revision"] != expected:
            raise SelfModelError(
                f"revision must increment by exactly 1: candidate "
                f"{candidate['revision']} but store has {prev_rev!r}"
            )
    elif candidate["revision"] != 1:
        raise SelfModelError(f"new store must start at revision 1, got {candidate['revision']}")

    if previous is not None:
        history = list(previous.get("history", []))
        history.append(
            {
                "revision": previous["revision"],
                "updatedUtc": previous["updatedUtc"],
                "capabilities": {
                    c["family"]: {"passed": c["passed"], "total": c["total"]}
                    for c in previous.get("capabilities", [])
                },
            }
        )
        candidate = dict(candidate)
        candidate["history"] = history

    store_path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(
        dir=str(store_path.parent), prefix=store_path.name + ".", suffix=".tmp"
    )
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(json.dumps(candidate, indent=2, ensure_ascii=True, sort_keys=True) + "\n")
        os.replace(tmp_name, store_path)
    except BaseException:
        if os.path.exists(tmp_name):
            os.unlink(tmp_name)
        raise
    return candidate


def load(path: str) -> dict[str, Any]:
    model = json.loads(Path(path).read_text(encoding="utf-8"))
    errors = validate(model)
    if errors:
        raise SelfModelError("store invalid: " + "; ".join(errors))
    return model


# --- revision-1 builder: measured estimates from an arm-B pilot aggregate ---

def build_from_arm_b_aggregate(
    aggregate: dict[str, Any], *, agent_id: str, source_artifact: str,
    expected_arm: str = "B",
) -> dict[str, Any]:
    """Derive a self-model revision-1 candidate from a pilot aggregate dict.

    Every capability number is recomputed from the aggregate's per-family
    counts (never copied as a free-floating claim), and the known failure
    patterns are seeded from the CN-007/CN-008 evidence the aggregate itself
    contains (rt-0003 / cu-0001 per-scenario observations). Missing evidence
    fails closed: provenance must exist for everything.
    """
    pilot = aggregate.get("pilot", {})
    if pilot.get("arm") != expected_arm:
        raise SelfModelError(
            f"aggregate is arm {pilot.get('arm')!r}, expected {expected_arm!r}"
        )
    per_family = aggregate.get("per_family")
    per_scenario = aggregate.get("per_scenario", {})
    if not isinstance(per_family, dict) or not per_family:
        raise SelfModelError("aggregate has no per_family data")
    seeds_run = pilot.get("seeds_run")
    if not seeds_run:
        raise SelfModelError("aggregate has no seeds_run")

    capabilities: list[dict[str, Any]] = []
    for family in sorted(per_family):
        entry = per_family[family]
        passed_by_seed = entry.get("passed_by_seed", {})
        probes_per_seed = entry.get("probes_per_seed")
        if not passed_by_seed or not probes_per_seed:
            raise SelfModelError(f"{family}: missing passed_by_seed/probes_per_seed")
        # Fail closed if any declared seed is missing its counts.
        missing = [s for s in seeds_run if str(s) not in passed_by_seed]
        if missing:
            raise SelfModelError(f"{family}: no counts for seeds {missing}")
        passed = sum(int(passed_by_seed[str(s)]) for s in seeds_run)
        total = int(probes_per_seed) * len(seeds_run)
        capabilities.append(
            {
                "family": family,
                "unit": "probe pass rate",
                "passed": passed,
                "total": total,
                "seeds": list(seeds_run),
                "probes_per_seed": int(probes_per_seed),
                "rate": round(passed / total, 3),
                "wilson95": wilson_interval(passed, total),
                "binomial_sd": binomial_sd(passed, total),
                "provenance": {
                    "source_artifact": source_artifact,
                    "method": "sum of per-family probe pass counts across the aggregate's seeds_run",
                    "numbers": {
                        "passed_by_seed": {str(k): v for k, v in sorted(passed_by_seed.items())},
                        "probes_per_seed": probes_per_seed,
                        "model": pilot.get("model"),
                        "model_digest": pilot.get("model_digest"),
                        "temperature": pilot.get("temperature"),
                        "run_id": pilot.get("run_id"),
                    },
                },
            }
        )

    def scenario_evidence(sid: str, what: str) -> dict[str, Any]:
        slot = per_scenario.get(sid)
        if not slot:
            raise SelfModelError(f"cannot seed failure-pattern evidence: {sid} missing ({what})")
        observations: dict[str, list[dict[str, Any]]] = slot.get("observations_by_seed", {})
        observed = sorted(
            {o.get("observed_normalized", "") for obs in observations.values() for o in obs}
        )
        return {
            "scenario": sid,
            "family": slot.get("family"),
            "pass_count": slot.get("pass_count"),
            "seeds": len(observations),
            "observed_normalized": observed,
        }

    rt3 = scenario_evidence("rt-0003", "CN-007")
    cu1 = scenario_evidence("cu-0001", "CN-008")
    known_failure_patterns = [
        {
            "id": "CN-007",
            "title": "own-answer anchoring",
            "pattern": (
                "The agent's own early answers, once stored in persistent memory, "
                "anchor later answers even when a later session supplies the "
                "correcting rubric; an early misclassification can repeat across "
                "sessions instead of being revised."
            ),
            "evidence": {
                "refs": [
                    "labs/continuity/docs/FINDINGS.md#CN-007",
                    "labs/continuity/LOG.md (M2 result, 2026-10-01 22:50)",
                ],
                "numbers": rt3,
            },
        },
        {
            "id": "CN-008",
            "title": "no supersession of corrected facts",
            "pattern": (
                "When a later session corrects an earlier fact, keyword memory "
                "recalls both versions and the superseded value may be repeated "
                "even though the correction was retrieved first; conflict "
                "resolution is the gap."
            ),
            "evidence": {
                "refs": [
                    "labs/continuity/docs/FINDINGS.md#CN-008",
                    "labs/continuity/LOG.md (M2 result, 2026-10-01 22:50)",
                ],
                "numbers": cu1,
            },
        },
    ]

    now = _utc_now()
    return {
        "format": SELFMODEL_FORMAT,
        "schemaVersion": SCHEMA_VERSION,
        "agentId": agent_id,
        "revision": 1,
        "createdUtc": now,
        "updatedUtc": now,
        "lastConsolidation": None,
        "capabilities": capabilities,
        "knownFailurePatterns": known_failure_patterns,
        "provenance": {
            "derived_from": source_artifact,
            "method": (
                "capabilities recomputed from per-family probe counts; failure "
                "patterns seeded from CN-007/CN-008 evidence in the same aggregate"
            ),
            "note": (
                "measured on the same 10-scenario fixture suite on which arm C is "
                "evaluated (CN-009 estimate/evaluation overlap; exploratory "
                "mini-pilot caveat, CONT-001 design input)"
            ),
            "agent_id_basis": {
                "model": pilot.get("model"),
                "model_digest": pilot.get("model_digest"),
            },
        },
    }


# --- prompt-side rendering (the only behavioral surface of the self-model) ---

def render_summary(model: dict[str, Any]) -> str:
    """Compact factual block injected as one system message for arm C.

    Deterministic: same model -> byte-identical block. Numbers only, no
    self-improvement language; the guard sentence is fixed.
    """
    lines = [
        "SELF-MODEL — measured estimates of this agent's own capabilities "
        "and its recorded failure patterns (from its own prior evaluation "
        "runs; factual, not goals).",
        "Capabilities (task-family probe pass rates):",
    ]
    for cap in model["capabilities"]:
        w = cap["wilson95"]
        lines.append(
            f"- {cap['family']}: {cap['passed']}/{cap['total']} passed "
            f"(rate {cap['rate']:.3f}; Wilson 95% CI {w['low']:.3f}..{w['high']:.3f})"
        )
    lines.append("Known failure patterns (recorded findings):")
    for pat in model["knownFailurePatterns"]:
        numbers = pat["evidence"].get("numbers", {})
        scenario = numbers.get("scenario", "?")
        observed = numbers.get("observed_normalized", [])
        observed_str = f", observed {observed[0]!r}" if observed else ""
        lines.append(
            f"- {pat['id']} {pat['title']}: {pat['pattern']} "
            f"(evidence: {scenario}{observed_str}, "
            f"{numbers.get('pass_count', '?')} passes / {numbers.get('seeds', '?')} seeds)"
        )
    lines.append(
        "Treat this as background self-knowledge; it does not override what "
        "the current session or your records say."
    )
    return "\n".join(lines)


def _selftest() -> int:
    """Offline: build -> validate -> commit -> reload -> tamper-rejection."""
    aggregate = {
        "pilot": {
            "arm": "B",
            "run_id": "pilot-armB-selftest",
            "model": "granite-code:8b",
            "model_digest": "36c3c3b9683b",
            "temperature": 0.0,
            "seeds_run": [11, 22],
        },
        "per_family": {
            "delayed_recall": {
                "passed_by_seed": {"11": 3, "22": 3}, "probes_per_seed": 3,
            },
            "repeated_task": {
                "passed_by_seed": {"11": 1, "22": 0}, "probes_per_seed": 3,
            },
        },
        "per_scenario": {
            "rt-0003": {
                "family": "repeated_task", "pass_count": 0,
                "observations_by_seed": {
                    "11": [{"observed_normalized": "bug", "passed": False}],
                    "22": [{"observed_normalized": "bug", "passed": False}],
                },
            },
            "cu-0001": {
                "family": "contradiction_update", "pass_count": 0,
                "observations_by_seed": {
                    "11": [{"observed_normalized": "12", "passed": False}],
                    "22": [{"observed_normalized": "12", "passed": False}],
                },
            },
        },
    }
    model = build_from_arm_b_aggregate(
        aggregate, agent_id="continuity/selftest",
        source_artifact="results/CONT-000/selftest/aggregate.json",
    )
    assert not validate(model), validate(model)
    assert model["capabilities"][0]["rate"] == 1.0  # delayed_recall 6/6
    assert model["capabilities"][1]["rate"] == 0.167  # repeated_task 1/6

    with tempfile.TemporaryDirectory() as tmp:
        store = str(Path(tmp) / "selfmodel.json")
        committed = commit(store, model)
        assert committed["revision"] == 1
        reloaded = load(store)
        assert selfmodel_sha256(reloaded) == selfmodel_sha256(model)
        block = render_summary(reloaded)
        assert "delayed_recall: 6/6" in block and "CN-007" in block and "CN-008" in block

        # revision must increment by exactly 1
        rev2 = json.loads(json.dumps(reloaded))
        rev2["revision"] = 3
        rev2["updatedUtc"] = _utc_now()
        try:
            commit(store, rev2)
            raise AssertionError("bad revision accepted")
        except SelfModelError as exc:
            assert "increment by exactly 1" in str(exc)

        # self-declared (arithmetic-mismatched) estimate is rejected
        rev2["revision"] = 2
        rev2["capabilities"][0]["rate"] = 0.999
        try:
            commit(store, rev2)
            raise AssertionError("self-declared rate accepted")
        except SelfModelError as exc:
            assert "recomputed" in str(exc)

        # missing provenance is rejected
        rev2["capabilities"][0]["rate"] = 1.0
        rev2["capabilities"][0]["provenance"] = {}
        try:
            commit(store, rev2)
            raise AssertionError("missing provenance accepted")
        except SelfModelError as exc:
            assert "provenance.source_artifact" in str(exc)

        # a legitimate increment commits and keeps history
        rev2["capabilities"][0]["provenance"] = {
            "source_artifact": "results/CONT-000/selftest/aggregate.json",
            "method": "selftest increment", "numbers": {"n": 1},
        }
        rev2["updatedUtc"] = _utc_now()
        committed2 = commit(store, rev2)
        assert committed2["revision"] == 2
        assert committed2["history"][0]["revision"] == 1
    print("selfmodel selftest ok: build/validate/commit/reload/tamper-rejection deterministic")
    return 0


def _cli(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="continuity self-model store")
    sub = parser.add_subparsers(dest="cmd")
    build = sub.add_parser("build", help="build revision from an arm-B pilot aggregate")
    build.add_argument("--aggregate", required=True)
    build.add_argument("--out", required=True)
    build.add_argument("--agent-id", default=None)
    show = sub.add_parser("show", help="validate and summarize a store")
    show.add_argument("path")
    args = parser.parse_args(argv)

    if args.cmd == "build":
        aggregate = json.loads(Path(args.aggregate).read_text(encoding="utf-8"))
        pilot = aggregate.get("pilot", {})
        agent_id = args.agent_id or (
            f"continuity/{pilot.get('model', 'unknown')}@"
            f"{str(pilot.get('model_digest', ''))[:12]}"
        )
        candidate = build_from_arm_b_aggregate(
            aggregate, agent_id=agent_id, source_artifact=args.aggregate
        )
        committed = commit(args.out, candidate)
        print(
            f"committed {args.out}: agent {committed['agentId']}, revision "
            f"{committed['revision']}, {len(committed['capabilities'])} capability "
            f"estimates, {len(committed['knownFailurePatterns'])} failure patterns, "
            f"sha256 {selfmodel_sha256(committed)[:12]}..."
        )
        return 0
    if args.cmd == "show":
        model = load(args.path)
        print(f"{args.path}: revision {model['revision']}, agent {model['agentId']}")
        for cap in model["capabilities"]:
            print(f"  {cap['family']}: {cap['passed']}/{cap['total']} rate {cap['rate']}")
        print(render_summary(model))
        return 0
    return _selftest()


if __name__ == "__main__":
    raise SystemExit(_cli(sys.argv[1:]))
