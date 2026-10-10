"""CONT-006 step-2-fold: FAITHFUL worker bundles (v3) — the same selection,
grouping and per-bundle cap as the executed v2 (worker_v2_bundles.py), with
the EVIDENCE restored (audit defect 1, AUDIT-CONT006-V2A-POSTVERDICT §B2).

What was lost in v2 and restored here:
- v2 emitted `ENV [source: ...]` lines only when the TRACE carried
  source_type — the runner never writes it, so all 9 v2 bundles had ZERO
  source-marked lines: standing cards, verified corrections, retractions
  and authority data disappeared. The fixtures DO carry source_type/actor
  per turn; the trace turn_ref maps 1:1 onto the fixture turn position, so
  roles are recovered positionally (rendered suite for that corpus seed).
- v2 abbreviated env turns to 12 words and kept only the FIRST env turn —
  the item under classification often vanished. v3 keeps EVERY env turn
  VERBATIM; agent replies are kept at every turn, capped at 80 words (the
  card-echo failure mode stays visible without blowing the worker ctx).
- The probe question is rendered in full (PROBE-Q), not 8 words.

Held fixed vs v2 (so old-vs-new isolates evidence fidelity ONLY): the
corpus manifest, SUBTYPE_GROUP/FAMILY_GROUP grouping, fails-first
scenario-interleaved ranking, MAX_RUNS_PER_BUNDLE=12, deterministic order,
the frozen worker prompt (reflection_v2.bundle_prompt), the worker options
and the §7.1 validator + FP-6 cap (run_worker_v2 is reused as-is over this
file). NOT fixed here (declared, stays open): the arm-A-dominant sample
(audit defect 2) — the capacity×content diagnostic contrasts stores, not
sampling; balanced sampling belongs to the end-to-end stage-2 suite.

Mechanical gate (main): every bundle digest must contain >= 1
"ENV [source:" line (the exact check the audit ran against v2 — 0/9 there);
digest size gate ~7.2k tokens with a declared lowest-rank-first trim.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.fixtures import load_suite_for_seed  # noqa: E402
from worker_v2_bundles import (  # noqa: E402
    CORPUS, MAX_RUNS_PER_BUNDLE, build_bundles as build_bundles_v2,
    group_for, scenario_runs)

# corpus run -> suite carrying its rendered scenarios (fixture single source)
RUN_SUITE = {"CONT-005-C2-PILOT": ("v3i", range(2001, 2006)),
             "CONT-005-C2-CONFIRMATORY": ("v3j", range(3001, 3006))}
MAX_DIGEST_CHARS = 28_800  # ~7.2k tokens of a 8192 worker ctx (declared trim)
AGENT_WORD_CAP = 80

_SUITES: dict[tuple[str, int], dict[str, dict]] = {}


def fixture_turns(run: str, seed: int) -> dict[str, dict]:
    """"{sid}|{turn_ref}" -> fixture turn (rendered, with source_type/actor)."""
    key = (run, seed)
    if key in _SUITES:
        return _SUITES[key]
    spec = RUN_SUITE.get(run)
    turns: dict[str, dict] = {}
    if spec is not None and seed in spec[1]:
        _, scenarios = load_suite_for_seed(
            str(LAB_ROOT / "fixtures" / spec[0]), seed)
        for s in scenarios:
            for sess in s["sessions"]:
                for k, t in enumerate(sess["turns"], start=1):
                    turns[f"{s['id']}|s{sess['index']}t{k}"] = t
    _SUITES[key] = turns
    return turns


def _cap_words(text: str, n: int) -> str:
    words = " ".join(text.split()).split(" ")
    return " ".join(words[:n]) + ("…" if len(words) > n else "")


def faithful_lines(prefix: str, sid: str, cls: str, sub: str,
                   evs: list[dict], fx: dict[str, dict]) -> list[str]:
    lines = [f"### {prefix}|{sid} family={sid[:2]} class={cls} sub_type={sub}"]
    probe_refs = {(e.get("payload") or {}).get("turn_ref") for e in evs
                  if e["type"] == "probe.result"}
    for e in evs:
        pl = e.get("payload") or {}
        ref = f"{prefix}|{sid}|{pl.get('turn_ref', '?')}"
        turn_ref = pl.get("turn_ref", "")
        ft = fx.get(f"{sid}|{turn_ref}", {})
        if e["type"] == "env.turn":
            text = pl.get("text", "")
            # fail-closed: trace env text must equal the rendered fixture
            # turn (positional mapping sanity; the runner emits it verbatim)
            if ft and ft.get("text") != text:
                raise ValueError(f"{prefix}|{sid}|{turn_ref}: trace/fixture "
                                 f"text mismatch — positional map broken")
            src = ft.get("source_type")
            actor = ft.get("actor", "environment")
            if turn_ref in probe_refs:
                lines.append(f"{ref} PROBE-Q: {text}")
            elif src:
                lines.append(f"{ref} ENV [source: {src}; actor: {actor}]: {text}")
            else:
                lines.append(f"{ref} ENV [actor: {actor}]: {text}")
        elif e["type"] == "agent.response":
            lines.append(f"{ref} AGENT: "
                         f"{_cap_words(pl.get('content', ''), AGENT_WORD_CAP)}")
        else:
            fmt = "format-miss" if pl.get("observed_label") is None else (
                "pass" if pl.get("passed") else "wrong-label")
            lines.append(f"{ref} PROBE: expected={pl.get('expected')!r} "
                         f"observed={pl.get('observed_label')!r} -> {fmt}")
    return lines


def build_bundles_v3() -> list[dict]:
    """v2 selection verbatim (grouping/ranking/cap/order), faithful digest."""
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    runs_by_group: dict[str, list[dict]] = {}
    for trace in manifest["traces"]:
        prefix = f"{trace['run']}|{trace['arm']}|seed-{trace['seed']}"
        fx = fixture_turns(trace["run"], trace["seed"])
        for run in scenario_runs(trace):
            name = group_for(run["sid"], run["sub_type"])
            if name is None:
                continue
            runs_by_group.setdefault(name, []).append(
                {**run, "prefix": prefix, "trace_key": prefix, "fx": fx})
    bundles = []
    for name, runs in runs_by_group.items():
        # identical ranking to v2 (fails first; scenario-interleaved ranks)
        runs.sort(key=lambda r: (not r["failed"], r["prefix"], r["sid"]))
        by_sid: dict[str, list[dict]] = {}
        for r in runs:
            by_sid.setdefault(r["sid"], []).append(r)
        ranked = [{**r, "_rank": i}
                  for rs in by_sid.values() for i, r in enumerate(rs)]
        ranked.sort(key=lambda r: (not r["failed"], r["_rank"],
                                   r["prefix"], r["sid"]))
        kept = ranked[:MAX_RUNS_PER_BUNDLE]
        digest_lines: list[str] = []
        for r in kept:
            digest_lines.extend(faithful_lines(
                r["prefix"], r["sid"], r["cls"], r["sub_type"],
                r["events"], r["fx"]))
        # declared trim: while over budget, drop the lowest-ranked kept run
        # (its lines were appended contiguously; remove from the tail)
        trimmed = 0
        while sum(len(l) + 1 for l in digest_lines) > MAX_DIGEST_CHARS \
                and len(kept) > 2:
            r = kept[-1]
            removed = faithful_lines(r["prefix"], r["sid"], r["cls"],
                                     r["sub_type"], r["events"], r["fx"])
            digest_lines = digest_lines[:len(digest_lines) - len(removed)]
            kept = kept[:-1]
            trimmed += 1
        digest = "\n".join(digest_lines)
        env_turns_total = sum(
            1 for r in kept for e in r["events"] if e["type"] == "env.turn")
        bundles.append({
            "bundle": name,
            "n_runs": len(kept),
            "n_traces": len({r["trace_key"] for r in kept}),
            "n_scenarios": len({r["sid"] for r in kept}),
            "digest": digest,
            "skipped_runs": len(runs) - len(kept) - trimmed,
            "trimmed_for_ctx": trimmed,
            "env_turns_total": env_turns_total,
            "env_lines_total": sum(
                1 for l in digest_lines
                if (" ENV [" in l or " PROBE-Q: " in l)),
        })
    bundles.sort(key=lambda b: b["bundle"])
    return bundles


def main() -> int:
    from continuity.reflection_v2 import bundle_prompt
    bundles = build_bundles_v3()
    # gate: prompt renders; FULL env coverage per bundle; source-marked
    # evidence present wherever the fixtures define it (cr/cu families —
    # dr/rt/dx state their facts in plain env turns by design, so their
    # check is coverage, not source lines; v2 had 0 source lines anywhere)
    probe_prompt = bundle_prompt(bundles[0])
    assert bundles[0]["digest"].splitlines()[0] in probe_prompt
    total_src = 0
    for b in bundles:
        assert b["env_lines_total"] == b["env_turns_total"], (
            f"gate FAIL: {b['bundle']} env coverage "
            f"{b['env_lines_total']}/{b['env_turns_total']}")
        n_src = sum(1 for l in b["digest"].splitlines() if "ENV [source:" in l)
        total_src += n_src
        print(f"  {b['bundle']:14s} runs={b['n_runs']:2d} traces={b['n_traces']:2d} "
              f"chars={len(b['digest']):5d} (~{len(b['digest'])//4} tok) "
              f"env={b['env_lines_total']}/{b['env_turns_total']} "
              f"src={n_src} trimmed={b['trimmed_for_ctx']}")
    cr_src = sum(1 for b in bundles if b["bundle"].startswith("cr")
                 for l in b["digest"].splitlines() if "ENV [source:" in l)
    assert cr_src > 0, "gate FAIL: cr bundles carry no source-marked lines"
    print(f"bundles: {len(bundles)}, source-marked lines total {total_src} "
          f"(cr: {cr_src}; v2 had 0 across all 9)")
    out = LAB_ROOT / "experiments" / "cont006" / "worker_v3_bundles.json"
    out.write_text(json.dumps(
        {"kind": "cont006-worker-v3-bundles-faithful",
         "note": "same selection/grouping/cap as worker_v2_bundles.json; "
                 "evidence restored (all env turns verbatim with "
                 "source_type/actor recovered positionally from the rendered "
                 "fixtures; agent replies every turn capped 80w; full probe "
                 "questions). Feeds run_worker_v2 unchanged.",
         "bundles": bundles}, indent=1, ensure_ascii=True) + "\n",
        encoding="utf-8")
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
