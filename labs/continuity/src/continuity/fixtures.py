"""Fixture protocol v1: versioned synthetic scenarios, labels, probes.

A fixture suite is a directory with a `manifest.json` and one JSON file per
scenario. The suite is consumer-neutral: it describes environment turns and
expected observations, not Continuity-internal APIs. See
labs/continuity/docs/research-proposal.md (CONT-000).
"""

from __future__ import annotations

import json
import os

PROBE_KINDS = frozenset({"exact_match", "contains"})
TURN_ACTORS = frozenset({"environment"})


def load_manifest(fixture_dir: str) -> dict:
    with open(os.path.join(fixture_dir, "manifest.json"), "r", encoding="utf-8") as fh:
        manifest = json.load(fh)
    if manifest.get("protocol") != "continuity-workload":
        raise ValueError("manifest.protocol must be 'continuity-workload'")
    if not isinstance(manifest.get("version"), int):
        raise ValueError("manifest.version must be an integer")
    return manifest


def load_scenario(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as fh:
        scenario = json.load(fh)
    _validate_scenario(scenario)
    return scenario


def load_suite(fixture_dir: str) -> tuple[dict, list[dict]]:
    """Load the manifest and every scenario file it lists."""
    manifest = load_manifest(fixture_dir)
    scenarios = []
    seen_ids: set[str] = set()
    for family in manifest["families"]:
        family_dir = os.path.join(fixture_dir, family)
        for name in sorted(os.listdir(family_dir)):
            if not name.endswith(".json"):
                continue
            scenario = load_scenario(os.path.join(family_dir, name))
            if scenario["id"] in seen_ids:
                raise ValueError(f"duplicate scenario id: {scenario['id']}")
            seen_ids.add(scenario["id"])
            scenarios.append(scenario)
    return manifest, scenarios


def _validate_scenario(scenario: dict) -> None:
    for field in ("id", "family", "sessions"):
        if field not in scenario:
            raise ValueError(f"scenario missing field: {field}")
    if not isinstance(scenario["sessions"], list) or not scenario["sessions"]:
        raise ValueError(f"{scenario['id']}: sessions must be a non-empty list")
    for i, session in enumerate(scenario["sessions"], start=1):
        if session.get("index") != i:
            raise ValueError(f"{scenario['id']}: session indices must be 1..n contiguous")
        turns = session.get("turns")
        if not isinstance(turns, list) or not turns:
            raise ValueError(f"{scenario['id']} session {i}: turns must be a non-empty list")
        for j, turn in enumerate(turns, start=1):
            if turn.get("actor") not in TURN_ACTORS:
                raise ValueError(
                    f"{scenario['id']} s{i}t{j}: actor must be one of {sorted(TURN_ACTORS)}"
                )
            if not isinstance(turn.get("text"), str) or not turn["text"].strip():
                raise ValueError(f"{scenario['id']} s{i}t{j}: text must be non-empty")
            probe = turn.get("probe")
            if probe is not None:
                if probe.get("kind") not in PROBE_KINDS:
                    raise ValueError(
                        f"{scenario['id']} s{i}t{j}: probe.kind must be one of {sorted(PROBE_KINDS)}"
                    )
                if not isinstance(probe.get("expected"), str) or not probe["expected"].strip():
                    raise ValueError(f"{scenario['id']} s{i}t{j}: probe.expected must be non-empty")
