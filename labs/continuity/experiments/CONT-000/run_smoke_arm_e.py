"""CONT-000 smoke, arm E: one scenario (dr-0001), memory + self-model +
reflection + world model + bounded policy.

Usage (from anywhere; take the shared GPU lock around this, see
shared/tooling/agent-resource-coordination/PROTOCOL.md):

    python labs/continuity/experiments/CONT-000/run_smoke_arm_e.py

Arm E = arm D + ex-ante world-model predictions on probe turns + the bounded
deterministic policy {answer_direct, retrieve_then_answer} (M5). The M5 smoke
gate: (1) the delayed-recall probe (dr-0001 s2t1, expected "7") still PASSES,
(2) world-model events are visible (`worldmodel.prediction` BEFORE the probe
is answered + `worldmodel.outcome` after scoring, attached to each other),
(3) policy events are visible (`policy.action` on every turn, including at
least one retrieve_then_answer — expected here: dr-0001 s2t1 carries the
absence marker "no logbook"), (4) reflection events still visible (arm D
semantics preserved), (5) the trace re-validates from disk — plus completion
and no budget stop. The per-run self-model copy (`selfmodel-run.json`)
evolves only through the fail-closed `selfmodel.commit()`; the canonical
`state/selfmodel.json` is never touched.

Fail-closed: if Ollama is unreachable, the model is missing, the resident
digest does not match EXPECTED_DIGEST_PREFIX, or the self-model store does
not validate, nothing runs and the script exits 2.
"""

from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]  # labs/continuity
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity import PROTOCOL_VERSION  # noqa: E402
from continuity.events import EventJournal, validate_trace  # noqa: E402
from continuity.fixtures import load_scenario  # noqa: E402
from continuity.memory import MemoryStore  # noqa: E402
from continuity.policy import ACTION_SET  # noqa: E402
from continuity.provider import OllamaProvider  # noqa: E402
from continuity.reflection import ReflectionEngine  # noqa: E402
from continuity.runner import MEMORY_TOP_K, Budget, run_scenario  # noqa: E402
from continuity.selfmodel import load as load_selfmodel  # noqa: E402
from continuity.selfmodel import selfmodel_sha256  # noqa: E402
from continuity.worldmodel import WorldModel  # noqa: E402

MODEL = "granite-code:8b"
EXPECTED_DIGEST_PREFIX = "36c3c3b9683b"  # pinned since the P0a smoke (CN-001)
SEED = 42  # same seed as the arm-A/B/C/D smokes for direct comparison
TEMPERATURE = 0.0
NUM_CTX = 4096
DEFAULT_SELFMODEL = LAB_ROOT / "state" / "selfmodel.json"

POLICY_CONFIG = {
    "action_set": ["answer_direct", "retrieve_then_answer"],
    "rules": (
        "R1 retrieve when the environment turn carries a fixed "
        "absence-of-records marker; R2 retrieve when the turn is a probe and "
        "the scenario's stored environment episodes contain a corrective "
        "marker (reflection.CORRECTIVE_MARKERS); otherwise answer_direct"
    ),
    "actuation": (
        "per-turn memory refresh/extension only: SAME renderer, SAME keyword "
        "retrieval rule and top_k as the arm-B baseline injection, query = the "
        "CURRENT turn; dedup no-op recorded when the retrieved ids are already "
        "covered by this session's injections; no new tools, no prompt changes"
    ),
    "consumes_predictions": False,
}

WORLDMODEL_CONFIG = {
    "prediction": (
        "before each probe turn is answered: predicted pass/fail + confidence "
        "= self-model current family pass-rate estimate (0.5 default prior), "
        "capped at 0.25 when the store holds no episodes for the scenario"
    ),
    "buckets": "high >=0.75 | medium [0.5,0.75) | low <0.5 (threshold 0.5)",
    "non_behavioral": (
        "predictions are trace events only; they never alter the prompt or "
        "the answer path (the M5 policy acts on environment/memory signals)"
    ),
}


def git_rev() -> str:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=str(LAB_ROOT), stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return "unknown"


def preflight(base_url: str) -> dict:
    probe = OllamaProvider(base_url=base_url, model=MODEL)
    try:
        version = probe.version()
    except Exception as exc:
        print(f"FAIL-CLOSED: Ollama unreachable at {base_url}: {exc}", file=sys.stderr)
        raise SystemExit(2)
    warm = OllamaProvider(
        base_url=base_url, model=MODEL, temperature=TEMPERATURE, seed=0, num_ctx=NUM_CTX
    )
    warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
    pinned = probe.model_info()
    digest = pinned.get("digest", "")
    if not digest.startswith(EXPECTED_DIGEST_PREFIX):
        print(
            f"FAIL-CLOSED: resident digest {digest!r} does not match pinned prefix "
            f"{EXPECTED_DIGEST_PREFIX!r}",
            file=sys.stderr,
        )
        raise SystemExit(2)
    return {"ollama_version": version, "digest": digest, "size_vram": pinned.get("size_vram", 0)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--base-url", default="http://localhost:11434")
    parser.add_argument("--scenario", default="dr-0001")
    parser.add_argument("--seed", type=int, default=SEED)
    parser.add_argument("--selfmodel", default=str(DEFAULT_SELFMODEL))
    args = parser.parse_args()

    env = preflight(args.base_url)
    scenario = load_scenario(
        str(LAB_ROOT / "fixtures" / "v1" / "delayed_recall" / f"{args.scenario}.json")
    )
    try:
        base_model = load_selfmodel(args.selfmodel)
    except Exception as exc:
        print(f"FAIL-CLOSED: self-model store invalid: {exc}", file=sys.stderr)
        raise SystemExit(2)
    base_sha = selfmodel_sha256(base_model)

    run_id = time.strftime(f"cont000-smoke-armE-{args.scenario}-%Y%m%d-%H%M%S")
    out_dir = LAB_ROOT / "results" / "CONT-000" / run_id
    out_dir.mkdir(parents=True, exist_ok=True)
    # Per-run copy: the canonical store never evolves from a smoke/pilot run.
    selfmodel_run_path = out_dir / "selfmodel-run.json"
    shutil.copyfile(args.selfmodel, selfmodel_run_path)

    provider = OllamaProvider(
        base_url=args.base_url,
        model=MODEL,
        temperature=TEMPERATURE,
        seed=args.seed,
        num_ctx=NUM_CTX,
    )
    memory = MemoryStore(str(out_dir / "memory.sqlite3"))
    journal = EventJournal(str(out_dir / "trace.jsonl"), run_id)
    journal.emit(
        "run.start",
        {
            "protocol_version": PROTOCOL_VERSION,
            "kind": "smoke-armE",
            "arm": "E",
            "scenario": scenario["id"],
            "model": MODEL,
            "seed": args.seed,
            "temperature": TEMPERATURE,
            "num_ctx": NUM_CTX,
            "memory": {
                "backend": "sqlite",
                "db": "memory.sqlite3",
                "retrieval": "keyword/substring, same-scenario scope",
                "top_k": MEMORY_TOP_K,
                "injection": "one system message at session start (index >= 2)",
            },
            "selfmodel": {
                "store": "selfmodel-run.json (per-run copy in this run dir)",
                "source": str(Path(args.selfmodel).relative_to(LAB_ROOT)).replace("\\", "/"),
                "agent_id": base_model["agentId"],
                "revision": base_model["revision"],
                "sha256": base_sha,
                "injection": "one system message after the base prompt in every session",
            },
            "reflection": {
                "engine": "deterministic MVP (no LLM call)",
                "pass": "one per non-stopped session",
                "proposal_types": [
                    "episode_summary",
                    "selfmodel_capability_update",
                    "selfmodel_failure_pattern",
                ],
                "validator": "schema + evidence re-derivation; no evidence -> reject",
                "commits": (
                    "summaries as new episodes (role reflection.summary); self-model "
                    "via fail-closed selfmodel.commit into selfmodel-run.json"
                ),
            },
            "worldmodel": dict(WORLDMODEL_CONFIG),
            "policy": dict(POLICY_CONFIG),
            "git_rev": git_rev(),
        },
    )
    env_snapshot = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "ollama_version": env["ollama_version"],
        "model": MODEL,
        "model_digest": env["digest"],
        "seed": args.seed,
        "arm": "E",
        "determinism_caveat": (
            "greedy+seed does not guarantee identical outputs across batch "
            "sizes or backends (PB-071)"
        ),
    }
    journal.emit("env.snapshot", env_snapshot)
    (out_dir / "env.json").write_text(
        json.dumps(env_snapshot, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    engine = ReflectionEngine(
        selfmodel_path=str(selfmodel_run_path),
        memory=memory,
        journal=journal,
        run_seed=args.seed,
        source_artifact=f"{run_id}/summary.json",
    )
    worldmodel = WorldModel(journal)
    budget = Budget(max_turns=40, max_total_tokens=100_000, wall_clock_s=600)
    summary = run_scenario(
        scenario, provider, journal, budget, arm="E",
        memory=memory, selfmodel=engine.model, reflection=engine,
        worldmodel=worldmodel,
    )

    pinned = provider.model_info()
    journal.emit("env.model_pinned", dict(pinned))
    summary["model_digest"] = pinned["digest"]

    memory_export = memory.export_json(str(out_dir / "memory-export.json"))
    summary["memory_episodes_total"] = memory_export["episode_count"]
    summary["reflection_telemetry"] = engine.telemetry
    summary["selfmodel_revision_final"] = engine.model["revision"]
    summary["selfmodel_sha256_final"] = selfmodel_sha256(engine.model)
    summary["worldmodel_calibration"] = worldmodel.calibration()
    memory.close()

    trace_ok, trace_errors = validate_trace(str(out_dir / "trace.jsonl"))
    summary["run_id"] = run_id
    summary["trace_schema_valid"] = trace_ok
    summary["trace_validation_errors"] = trace_errors
    summary["completed"] = (not summary["stopped"]) and trace_ok
    probes_passed = summary["probes_passed"] == summary["probes_total"] and summary["probes_total"] > 0
    summary["all_probes_passed"] = probes_passed

    # World-model visibility gates: each prediction must PRECEDE the answer
    # of its OWN turn, and its outcome must follow that turn's probe result.
    prediction_events: list[dict] = []
    outcome_events: list[dict] = []
    policy_events: list[dict] = []
    reflection_events: list[dict] = []
    prediction_seq: dict[str, int] = {}
    outcome_seq: dict[str, int] = {}
    scored_seq: dict[str, int] = {}
    with open(out_dir / "trace.jsonl", "r", encoding="utf-8") as fh:
        response_seq: dict[str, int] = {}
        for line in fh:
            line = line.strip()
            if not line:
                continue
            record = json.loads(line)
            rtype = record.get("type")
            payload = record.get("payload", {})
            turn_ref = payload.get("turn_ref")
            if rtype == "worldmodel.prediction":
                prediction_events.append(payload)
                prediction_seq[turn_ref] = record["seq"]
            elif rtype == "worldmodel.outcome":
                outcome_events.append(payload)
                outcome_seq[turn_ref] = record["seq"]
            elif rtype == "agent.response":
                response_seq[turn_ref] = record["seq"]
            elif rtype == "probe.result":
                scored_seq[turn_ref] = record["seq"]
            elif rtype == "policy.action":
                policy_events.append(payload)
            elif rtype == "reflection.proposal":
                reflection_events.append(payload)
    prediction_pre_answer = bool(prediction_seq) and all(
        prediction_seq[t] < response_seq[t] for t in prediction_seq if t in response_seq
    )
    outcomes_attached = bool(outcome_seq) and set(outcome_seq) == set(prediction_seq) and all(
        scored_seq[t] < outcome_seq[t] for t in outcome_seq if t in scored_seq
    )
    summary["worldmodel_prediction_events"] = len(prediction_events)
    summary["worldmodel_outcome_events"] = len(outcome_events)
    summary["policy_action_events"] = len(policy_events)
    summary["policy_actions_by_action"] = {
        a: sum(1 for p in policy_events if p["action"] == a) for a in sorted(ACTION_SET)
    }
    summary["policy_retrieve_injections"] = sum(
        1 for p in policy_events if p.get("retrieval", {}) and p["retrieval"].get("injected")
    )
    summary["policy_retrieve_noops"] = sum(
        1
        for p in policy_events
        if p["action"] == "retrieve_then_answer" and not p["retrieval"]["injected"]
    )
    summary["reflection_proposal_events"] = len(reflection_events)

    worldmodel_visible = (
        bool(prediction_events)
        and bool(outcome_events)
        and prediction_pre_answer
        and outcomes_attached
    )
    summary["worldmodel_visible_in_trace"] = worldmodel_visible

    policy_visible = bool(policy_events) and any(
        p["action"] == "retrieve_then_answer" for p in policy_events
    )
    summary["policy_visible_in_trace"] = policy_visible
    reflection_visible = bool(reflection_events) and any(p["accepted"] for p in reflection_events)
    summary["reflection_visible_in_trace"] = reflection_visible

    journal.emit(
        "run.end",
        {
            "completed": summary["completed"],
            "trace_schema_valid": trace_ok,
            "probes_passed": summary["probes_passed"],
            "probes_total": summary["probes_total"],
            "all_probes_passed": probes_passed,
            "worldmodel_visible_in_trace": worldmodel_visible,
            "policy_visible_in_trace": policy_visible,
            "reflection_visible_in_trace": reflection_visible,
        },
    )
    journal.close()
    (out_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=True), encoding="utf-8"
    )

    print(f"run_id: {run_id}")
    print(f"completed: {summary['completed']} stopped: {summary['stopped']}")
    print(
        f"probes: {summary['probes_passed']}/{summary['probes_total']} passed; "
        f"turns: {summary['turns']}; tokens: {summary['tokens_total']}; "
        f"memory episodes: {summary['memory_episodes_total']}"
    )
    for probe in summary["probes"]:
        print(
            f"  {probe['turn_ref']} {probe['kind']} expected={probe['expected']!r} "
            f"passed={probe['passed']} observed={probe['observed_normalized'][:80]!r}"
        )
    print(
        f"worldmodel: {summary['worldmodel_prediction_events']} predictions / "
        f"{summary['worldmodel_outcome_events']} outcomes attached; calibration "
        f"{json.dumps(summary['worldmodel_calibration']['overall'])}"
    )
    for p in prediction_events:
        print(
            f"  prediction {p['prediction_id']} {p['turn_ref']}: predicted={p['predicted']} "
            f"confidence={p['confidence']} bucket={p['bucket']} "
            f"(family_rate={p['family_rate']}, episodes={p['episodes_for_scenario']})"
        )
    print(
        f"policy: {summary['policy_action_events']} actions "
        f"{summary['policy_actions_by_action']}; injections "
        f"{summary['policy_retrieve_injections']}, no-ops {summary['policy_retrieve_noops']}"
    )
    for p in policy_events:
        retrieval = p.get("retrieval")
        r_str = (
            "n/a"
            if retrieval is None
            else (
                f"injected {len(retrieval['episode_ids'])} episodes"
                if retrieval.get("injected")
                else retrieval.get("reason", "no-op")
            )
        )
        print(
            f"  policy {p['turn_ref']}: {p['action']} ({p['rule']}; "
            f"signals={p['signals']}) -> {r_str}"
        )
    print(
        f"reflection: {summary['reflection_proposal_events']} proposals; self-model revision "
        f"{base_model['revision']} -> {summary['selfmodel_revision_final']}"
    )
    print(f"artifacts: {out_dir}")
    ok = summary["completed"] and probes_passed and worldmodel_visible and policy_visible and reflection_visible
    print(
        "M5 smoke gate (probe passes + prediction/policy/reflection events visible "
        f"+ trace valid): {ok}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
