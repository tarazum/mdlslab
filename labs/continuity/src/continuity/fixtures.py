"""Fixture protocol: versioned synthetic scenarios, labels, probes.

A fixture suite is a directory with a `manifest.json` and one JSON file per
scenario. The suite is consumer-neutral: it describes environment turns and
expected observations, not Continuity-internal APIs. See
labs/continuity/docs/research-proposal.md (CONT-000).

Fixture protocol v3i (CONT-005 cycle 2): a scenario may carry a `variants`
table — a predeclared per-seed binding (values, per-probe label lists with
their display order, per-probe expected answers) so every seed runs genuinely
different content (the cycle-1 Fable audit: at temperature 0.0 byte-identical
prompts produce identical answers — five seeds were effectively one run).
Variant scenarios store turn texts with `{token}` placeholders; the concrete
scenario for a seed is produced by `render_seed_variant`. The reserved token
`{options}` is only valid on probe turns and renders to the probe's label
list joined with " | ".
"""

from __future__ import annotations

import copy
import json
import os
import re

PROBE_KINDS = frozenset({"exact_match", "contains", "guess_calibration"})
TURN_ACTORS = frozenset({"environment"})

_TOKEN_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")
_OPTIONS_TOKEN = "options"


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


def variant_seed_list(manifest: dict) -> list[int]:
    """Predeclared variant seeds of a v3i suite (manifest.variant_seeds)."""
    seeds = manifest.get("variant_seeds")
    if not isinstance(seeds, list) or not seeds or not all(
        isinstance(s, int) and not isinstance(s, bool) for s in seeds
    ):
        raise ValueError("manifest.variant_seeds must be a non-empty list of ints")
    return list(seeds)


def load_suite_for_seed(fixture_dir: str, seed: int) -> tuple[dict, list[dict]]:
    """Load a v3i suite fully rendered for one seed (fail-closed)."""
    manifest, scenarios = load_suite(fixture_dir)
    if seed not in variant_seed_list(manifest):
        raise ValueError(
            f"seed {seed} is not in manifest.variant_seeds "
            f"{variant_seed_list(manifest)} (suite {fixture_dir})"
        )
    return manifest, [render_seed_variant(s, seed) for s in scenarios]


def render_seed_variant(scenario: dict, seed: int) -> dict:
    """Render the concrete scenario for one seed from its variant table.

    Substitutes `{token}` placeholders in every turn text, in
    seed_error.value and in initial_expected; materializes each probe's
    labels/expected from the per-seed table. Fail-closed on any unknown or
    unbound token, any probe turn without a per-seed spec, and any spec for a
    turn that is not a probe. This function is the single render definition
    shared by the runner, the validator and the assembly gate (digest-frozen
    at freeze time).
    """
    sid = scenario.get("id", "?")
    table = scenario.get("variants")
    if not isinstance(table, dict):
        raise ValueError(f"{sid}: no variants table (suite requires per-seed variants)")
    key = str(seed)
    if key not in table:
        raise ValueError(f"{sid}: no variant for seed {seed} (have {sorted(table)})")
    var = table[key]
    values = var.get("values")
    probe_specs = var.get("probes")
    if not isinstance(values, dict) or not isinstance(probe_specs, dict):
        raise ValueError(f"{sid} seed {seed}: variant needs 'values' and 'probes' objects")

    def substitute(text: str, extra: dict[str, str] | None, where: str) -> str:
        def repl(match: re.Match) -> str:
            token = match.group(1)
            if token == _OPTIONS_TOKEN:
                if extra is None or _OPTIONS_TOKEN not in extra:
                    raise ValueError(f"{sid} seed {seed}: {{{token}}} used outside a probe turn ({where})")
                return extra[_OPTIONS_TOKEN]
            if token not in values:
                raise ValueError(f"{sid} seed {seed}: unbound token {{{token}}} in {where}")
            return values[token]

        return _TOKEN_RE.sub(repl, text)

    out = copy.deepcopy(scenario)
    out.pop("variants", None)
    seen_probe_refs: set[str] = set()
    for session in out["sessions"]:
        for turn_no, turn in enumerate(session["turns"], start=1):
            ref = f"s{session['index']}t{turn_no}"
            probe = turn.get("probe")
            extra: dict[str, str] | None = None
            if probe is not None:
                spec = probe_specs.get(ref)
                if spec is None:
                    raise ValueError(f"{sid} seed {seed}: probe turn {ref} has no per-seed spec")
                labels = spec.get("labels")
                if not isinstance(labels, list) or not labels:
                    raise ValueError(f"{sid} seed {seed}: probe {ref} spec needs a labels list")
                extra = {_OPTIONS_TOKEN: " | ".join(labels)}
                probe["labels"] = list(labels)
                if probe.get("kind") == "guess_calibration":
                    probe["expected"] = None
                else:
                    expected = spec.get("expected")
                    if not isinstance(expected, str) or not expected.strip():
                        raise ValueError(f"{sid} seed {seed}: probe {ref} spec needs 'expected'")
                    if expected not in labels:
                        raise ValueError(
                            f"{sid} seed {seed}: probe {ref} expected {expected!r} not in its labels"
                        )
                    probe["expected"] = expected
                seen_probe_refs.add(ref)
            turn["text"] = substitute(turn["text"], extra, ref)
    stray = set(probe_specs) - seen_probe_refs
    if stray:
        raise ValueError(f"{sid} seed {seed}: probe specs for non-probe turns: {sorted(stray)}")
    if isinstance(out.get("seed_error"), dict) and isinstance(out["seed_error"].get("value"), str):
        out["seed_error"]["value"] = substitute(out["seed_error"]["value"], None, "seed_error.value")
    if isinstance(out.get("initial_expected"), str):
        out["initial_expected"] = substitute(out["initial_expected"], None, "initial_expected")
    leftovers = [
        f"s{sess['index']}t{k}"
        for sess in out["sessions"]
        for k, t in enumerate(sess["turns"], start=1)
        if _TOKEN_RE.search(t["text"])
    ]
    if leftovers:
        raise ValueError(f"{sid} seed {seed}: unresolved tokens remain in turns {leftovers}")
    return out


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
                if probe.get("kind") == "guess_calibration":
                    # Suite v3: never-stated fact; expected is null by design and
                    # the reply is aggregated for the empirical guess rate.
                    if probe.get("expected") is not None:
                        raise ValueError(
                            f"{scenario['id']} s{i}t{j}: guess_calibration expects null"
                        )
                elif "variants" in scenario:
                    # Suite v3i: expected/labels materialize per seed at render
                    # time (render_seed_variant); the base file may omit them.
                    pass
                elif not isinstance(probe.get("expected"), str) or not probe["expected"].strip():
                    raise ValueError(f"{scenario['id']} s{i}t{j}: probe.expected must be non-empty")
                labels = probe.get("labels")
                if labels is not None and (
                    not isinstance(labels, list)
                    or not labels
                    or any(not isinstance(x, str) or not x.strip() for x in labels)
                ):
                    raise ValueError(
                        f"{scenario['id']} s{i}t{j}: probe.labels must be a non-empty list of strings"
                    )
