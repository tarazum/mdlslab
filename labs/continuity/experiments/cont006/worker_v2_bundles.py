"""CONT-006 rethink: multi-trace worker bundles (REVIEW-FABLE-CONT006 C.3 —
FIX-A/B become design; REVIEW-CONT006-CN012-RERUN Stage A).

The invalid run's per-trace bundles made §7.1(b) (>=2 distinct traces)
structurally unsatisfiable: the worker could only cite one trace per call,
so cross-trace support existed only as a post-hoc validator merge. v2
bundles are grouped by SCENARIO FAMILY across the whole corpus: every
bundle carries the condensed scenario-runs of ONE family (or sub-type)
from MULTIPLE arms/seeds, so the worker sees the repeated pattern and
cites cross-trace refs natively. One ref format only (5-part
RUN|ARM|seed-N|SCENARIO|TURN), pinned by a worked example in the prompt.

Bundle budget: each family bundle is capped at the 12 most informative
scenario-runs (fails first, then passes; deterministic order by
run/arm/seed) to fit worker num_ctx 8192 with the 768 output budget.

FP-6 store cap (C.4): the lesson pipeline applies a per-class cap of ONE
format-discipline lesson (FP-6 is cross-cutting by taxonomy — three
near-copies crowded out retrieval in the invalid run). Declared ex ante in
the V2 prereg; class-coverage telemetry reports the composition.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity.reflection_v2 import (  # noqa: E402
    CR_SUBTYPE_CLASS, FAMILY_CLASS, _abbreviate)

CORPUS = LAB_ROOT / "experiments" / "cont006" / "experience-corpus-manifest.json"

FAMILY_GROUPS = [
    # (group name, scenario filter): one bundle per group
    ("cu-FP1", lambda sid: sid[:2] == "cu"),
    ("rt-FP2", lambda sid: sid[:2] == "rt"),
    ("cr-FP3a-vce", lambda sid: sid[:2] == "cr" and sid.endswith(("7001", "3001", "4001", "6001")) or (sid[:2] == "cr" and sid[3] in "37" and sid.endswith("01"))),
    ("cr-FP3a-vct", lambda sid: sid[:2] == "cr" and sid.endswith(("02",))),
    ("cr-FP3b-euc", lambda sid: sid[:2] == "cr" and sid.endswith(("03",))),
    ("cr-FP3b-sc", lambda sid: sid[:2] == "cr" and sid.endswith(("04", "05", "06", "07", "08"))),
    ("dx-FP4", lambda sid: sid[:2] == "dx"),
    ("dr-FP5", lambda sid: sid[:2] == "dr"),
]

MAX_RUNS_PER_BUNDLE = 12

# The V2 prompt template + bundle_prompt() live in src/continuity/
# reflection_v2.py (single source; RC-6 self-review fold — this file earlier
# carried a stale copy and a broken @@-token prompt_for).


def scenario_runs(trace: dict) -> list[dict]:
    """(sid, class, lines[]) per non-gc scenario of one trace."""
    path = LAB_ROOT / trace["trace"]
    events: dict[str, list[dict]] = {}
    order: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        e = json.loads(line)
        sid = e.get("scenario")
        if not sid or sid[:2] == "gc":
            continue
        if e.get("type") in ("env.turn", "agent.response", "probe.result"):
            if sid not in events:
                order.append(sid)
            events.setdefault(sid, []).append(e)
    out = []
    classes = _scenario_classes()
    for sid in order:
        evs = events[sid]
        failed = any(e["type"] == "probe.result" and not e["payload"].get("passed")
                     for e in evs)
        out.append({"sid": sid, "cls": classes.get(sid, "?"), "events": evs,
                    "failed": failed})
    return out


_CLASSES_CACHE: dict[str, str] | None = None


def _scenario_classes() -> dict[str, str]:
    global _CLASSES_CACHE
    if _CLASSES_CACHE is None:
        out: dict[str, str] = {}
        for suite in ("v3i", "v3j"):
            for path in sorted((LAB_ROOT / "fixtures" / suite).rglob("*.json")):
                if path.name == "manifest.json":
                    continue
                s_ = json.loads(path.read_text(encoding="utf-8"))
                fam = s_["id"][:2]
                out[s_["id"]] = (CR_SUBTYPE_CLASS.get(s_.get("sub_type", ""), "?")
                                 if fam == "cr" else FAMILY_CLASS.get(fam, "?"))
        _CLASSES_CACHE = out
    return _CLASSES_CACHE


def _scenario_lines(prefix: str, sid: str, cls: str, evs: list[dict]) -> list[str]:
    lines = [f"### {prefix}|{sid} family={sid[:2]} class={cls}"]
    probe_refs = {(e.get("payload") or {}).get("turn_ref") for e in evs
                  if e["type"] == "probe.result"}
    first_env_seen = False
    for e in evs:
        pl = e.get("payload") or {}
        ref = f"{prefix}|{sid}|{pl.get('turn_ref', '?')}"
        turn_ref = pl.get("turn_ref", "")
        if e["type"] == "env.turn":
            src = pl.get("source_type")
            if src:
                lines.append(f"{ref} ENV [source: {src}]: {_abbreviate(pl.get('text', ''), 12)}")
            elif turn_ref in probe_refs:
                lines.append(f"{ref} PROBE-Q: {_abbreviate(pl.get('text', ''), 8)}")
            elif not first_env_seen:
                first_env_seen = True
                lines.append(f"{ref} ENV: {_abbreviate(pl.get('text', ''), 12)}")
        elif e["type"] == "agent.response":
            if (turn_ref.startswith("s1") and turn_ref.endswith("t1")) or turn_ref in probe_refs:
                lines.append(f"{ref} AGENT: {_abbreviate(pl.get('content', ''), 6)}")
        else:
            fmt = "format-miss" if pl.get("observed_label") is None else (
                "pass" if pl.get("passed") else "wrong-label")
            lines.append(f"{ref} PROBE: expected={pl.get('expected')!r} "
                         f"observed={pl.get('observed_label')!r} -> {fmt}")
    return lines


def build_bundles() -> list[dict]:
    """One bundle per family group; scenario-runs ranked fails-first within
    the per-bundle cap; deterministic order (run, arm, seed, sid)."""
    manifest = json.loads(CORPUS.read_text(encoding="utf-8"))
    runs_by_group: dict[str, list[dict]] = {name: [] for name, _ in FAMILY_GROUPS}
    for trace in manifest["traces"]:
        prefix = f"{trace['run']}|{trace['arm']}|seed-{trace['seed']}"
        for run in scenario_runs(trace):
            for name, keep in FAMILY_GROUPS:
                if keep(run["sid"]):
                    runs_by_group[name].append({**run, "prefix": prefix,
                                                "trace_key": prefix})
    bundles = []
    for name, runs in runs_by_group.items():
        runs.sort(key=lambda r: (not r["failed"], r["prefix"], r["sid"]))
        kept = runs[:MAX_RUNS_PER_BUNDLE]
        digest_lines: list[str] = []
        for r in kept:
            digest_lines.extend(_scenario_lines(r["prefix"], r["sid"], r["cls"], r["events"]))
        bundles.append({
            "bundle": name,
            "n_runs": len(kept),
            "n_traces": len({r["trace_key"] for r in kept}),
            "digest": "\n".join(digest_lines),
            "skipped_runs": len(runs) - len(kept),
        })
    return bundles


def main() -> int:
    from continuity.reflection_v2 import bundle_prompt  # single source (src)
    bundles = build_bundles()
    # sanity: the src template renders against a real bundle (format fields
    # resolve; no unbalanced-brace leak into the digest block)
    probe_prompt = bundle_prompt(bundles[0])
    assert bundles[0]["digest"].splitlines()[0] in probe_prompt
    sizes = [(b["bundle"], b["n_runs"], b["n_traces"], len(b["digest"])) for b in bundles]
    for row in sizes:
        print(f"  {row[0]:14s} runs={row[1]:2d} traces={row[2]:2d} chars={row[3]:5d} (~{row[3]//4} tok)")
    total = sum(row[3] for row in sizes)
    print(f"bundles: {len(bundles)}, total digest chars {total} (~{total//4} tokens)")
    out = LAB_ROOT / "experiments" / "cont006" / "worker_v2_bundles.json"
    out.write_text(json.dumps(
        {"kind": "cont006-worker-v2-bundles",
         "note": "pre-computed multi-trace bundles (design artifact of the V2 "
                 "prereg; the worker pass itself is owner-gated after the "
                 "review chain)",
         "bundles": [{k: v for k, v in b.items()} for b in bundles]},
        indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
    print("written:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
