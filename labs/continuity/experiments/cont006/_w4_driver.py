"""W4 driver: the BALANCED faithful-bundle worker pass with the AUDITED
validator V2 (stage-2 brief §3). Same frozen machinery as W3 (run_worker_v2
over a pre-computed bundle file; reflector warm-then-pinned per CN-001),
with exactly two declared substitutions:

1. bundles = worker_v4_bundles.json (faithful v3 rendering + the BALANCED
   selection: per-arm cap 3, total 12; repairs audit defect 2);
2. validator = lessons_v2.validate_candidate_v2 (the pre-registered V2
   anti-salience rule: C1 structural digits + C2 expected-null option
   words exempted; frozen lessons.py untouched) — substituted into the
   frozen reflection_v2 namespace BEFORE the pass, recorded in telemetry
   with the collision-report digest.

Declared deviation vs the frozen WORKER_OPTIONS (carried in the run
record, same as W3): num_ctx 8192 -> 16384 via a custom provider (the
faithful digests are ~7k prompt tokens; identical rationale to W3's
10.1k digests). Everything else identical (temperature 0.0, seed 42,
num_predict 768, think:false, keep_alive 30m).

After the pass: the CONSUMPTION GATE (prereg validator-V2 §4) — every
lesson of the frozen worker store is matched against the v3o answer
vocabulary (all fields, no C1/C2 exemptions); ANY hit excludes the lesson
(fail-closed). The post-gate store is the stage-2 NEWF-v2 store; the
exclusions are reported. Zero consumer inference happens in this driver.
"""

import hashlib
import json
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB / "src"))
sys.path.insert(0, str(LAB / "experiments" / "cont006"))

from continuity.provider import OllamaProvider
from continuity import reflection_v2
from continuity.reflection_v2 import (
    REFLECTOR_DIGEST_PREFIX, REFLECTOR_MODEL, WORKER_OPTIONS, run_worker_v2)
from continuity.lessons import make_store, save_store
from lessons_v2 import build_vocab_report, v2_blocked_tokens
from lessons_v2 import consumption_vocab, consumption_gate

BUNDLES = LAB / "experiments" / "cont006" / "worker_v4_bundles.json"
CORPUS = LAB / "experiments" / "cont006" / "experience-corpus-manifest.json"
V3O = LAB / "fixtures" / "v3o"
BASE = "http://localhost:11434"
NUM_CTX_V4 = 16384

ts = time.strftime("%Y%m%d-%H%M%S")
out = LAB / "results" / "CONT-006-WORKER" / f"cont006-worker-v4-{ts}"
out.mkdir(parents=True, exist_ok=True)

warm = OllamaProvider(base_url=BASE, model=REFLECTOR_MODEL, temperature=0.0,
                      seed=0, num_ctx=NUM_CTX_V4, keep_alive="30m",
                      timeout_s=900)
t0 = time.monotonic()
warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
print(f"reflector warm {time.monotonic()-t0:.1f}s", flush=True)
info = OllamaProvider(base_url=BASE, model=REFLECTOR_MODEL).model_info()
if not info.get("digest", "").startswith(REFLECTOR_DIGEST_PREFIX):
    raise SystemExit(f"FAIL-CLOSED: reflector digest {info.get('digest')!r}")
print("reflector pinned:", info["digest"], flush=True)

# --- substitution 2: the audited validator V2 into the frozen namespace ---
report = build_vocab_report()
BLOCKED = v2_blocked_tokens(report)
report_sha = hashlib.sha256(json.dumps(
    report, sort_keys=True).encode("utf-8")).hexdigest()
_frozen_validate = reflection_v2.validate_candidate


def validate_candidate_v2_adapter(lesson, corpus, accepted):
    # mirrors the frozen signature; imports the v2 implementation lazily to
    # keep the frozen module byte-untouched
    from lessons_v2 import validate_candidate_v2
    return validate_candidate_v2(lesson, corpus, accepted, BLOCKED)


reflection_v2.validate_candidate = validate_candidate_v2_adapter
print(f"validator V2 substituted: {len(report['c1_structural_digits'])} C1 + "
      f"{len(report['c2_expected_null_option_words'])} C2 exemptions; "
      f"v2 tokens {len(BLOCKED)} (v1 {report['v1_blocked_tokens']}); "
      f"collision-report sha {report_sha[:12]}", flush=True)

worker = OllamaProvider(
    base_url=BASE, model=REFLECTOR_MODEL,
    temperature=WORKER_OPTIONS["temperature"], seed=WORKER_OPTIONS["seed"],
    num_ctx=NUM_CTX_V4, num_predict=WORKER_OPTIONS["num_predict"],
    keep_alive="30m", timeout_s=900)

try:
    tel = run_worker_v2(bundles_path=BUNDLES, out_dir=out,
                        corpus_manifest=CORPUS, base_url=BASE, provider=worker)
finally:
    reflection_v2.validate_candidate = _frozen_validate

tel["declared_deviation"] = {
    "worker_num_ctx": f"8192 (frozen WORKER_OPTIONS) -> {NUM_CTX_V4} via "
                      "custom provider; faithful v4 digests are ~7k prompt "
                      "tokens (same rationale as W3); all else identical",
    "validator": "audited V2 substituted into the frozen reflection_v2 "
                 "namespace (prereg docs/PREREG-CONT006-VALIDATOR-V2.md; "
                 f"collision-report sha256 {report_sha}); frozen "
                 "src/continuity/lessons.py untouched",
    "bundles": "worker_v4_bundles.json — balanced selection (per-arm cap 3, "
               "total 12; arm A 27% vs ~90% in the executed v3 selection)",
}
(out / "telemetry-v2.json").write_text(
    json.dumps(tel, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
print(json.dumps(tel, indent=1), flush=True)

# --- consumption gate over v3o (prereg validator-V2 §4) ---
store = json.loads((out / "r2-store-v2.json").read_text(encoding="utf-8"))
vocab = consumption_vocab([V3O])
excluded, kept = consumption_gate(store["lessons"], vocab)
gate_report = {
    "kind": "cont006-stage2-consumption-gate",
    "suite": "fixtures/v3o",
    "vocab_tokens": len(vocab["tokens"]),
    "vocab_phrases": len(vocab["phrases"]),
    "pre_gate_lessons": len(store["lessons"]),
    "excluded": excluded,
    "kept": len(kept),
}
(out / "consumption-gate.json").write_text(
    json.dumps(gate_report, indent=1, ensure_ascii=True) + "\n",
    encoding="utf-8")
post = make_store(
    kept, source="worker", status="evidence-validated",
    provenance=("W4 balanced faithful pass (worker_v4_bundles.json; audited "
                "validator V2 per docs/PREREG-CONT006-VALIDATOR-V2.md) + the "
                "v3o consumption gate (any answer-vocabulary hit excludes "
                "the lesson; report in consumption-gate.json of this run)"))
digest = save_store(post, out / "newf2-store-postgate.json")
print(f"consumption gate: kept {len(kept)}/{len(store['lessons'])}, "
      f"excluded {len(excluded)}; post-gate store sha {digest}", flush=True)
if excluded:
    print("EXCLUSIONS:", json.dumps(excluded, indent=1), flush=True)
print(f"W4 complete: {out}")
