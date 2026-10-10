"""W3 driver: the faithful-bundle worker pass (run_worker_v2 over
worker_v3_bundles.json), reflector warm-then-pinned per CN-001 order.

Declared deviation vs the frozen WORKER_OPTIONS (carried in the run
record): num_ctx 8192 -> 16384 via a custom provider — the faithful
digests are ~10.1k prompt tokens (the frozen 8192 rejects them:
exceed_context_size_error n_prompt_tokens=10146). Everything else
identical (temperature 0.0, seed 42, num_predict 768, think:false,
keep_alive 30m). Selection/grouping/cap stay byte-identical to W2.
"""
import json
import sys
import time
from pathlib import Path

LAB = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB / "src"))

from continuity.provider import OllamaProvider
from continuity.reflection_v2 import (
    REFLECTOR_DIGEST_PREFIX, REFLECTOR_MODEL, WORKER_OPTIONS, run_worker_v2)

BUNDLES = LAB / "experiments" / "cont006" / "worker_v3_bundles.json"
CORPUS = LAB / "experiments" / "cont006" / "experience-corpus-manifest.json"
BASE = "http://localhost:11434"
NUM_CTX_V3 = 16384

ts = time.strftime("%Y%m%d-%H%M%S")
out = LAB / "results" / "CONT-006-WORKER" / f"cont006-worker-v3-{ts}"
out.mkdir(parents=True, exist_ok=True)

warm = OllamaProvider(base_url=BASE, model=REFLECTOR_MODEL, temperature=0.0,
                      seed=0, num_ctx=NUM_CTX_V3, keep_alive="30m",
                      timeout_s=900)
t0 = time.monotonic()
warm.chat([{"role": "user", "content": "Reply with the single word: ready."}])
print(f"reflector warm {time.monotonic()-t0:.1f}s", flush=True)
info = OllamaProvider(base_url=BASE, model=REFLECTOR_MODEL).model_info()
if not info.get("digest", "").startswith(REFLECTOR_DIGEST_PREFIX):
    raise SystemExit(f"FAIL-CLOSED: reflector digest {info.get('digest')!r}")
print("reflector pinned:", info["digest"], flush=True)

worker = OllamaProvider(
    base_url=BASE, model=REFLECTOR_MODEL,
    temperature=WORKER_OPTIONS["temperature"], seed=WORKER_OPTIONS["seed"],
    num_ctx=NUM_CTX_V3, num_predict=WORKER_OPTIONS["num_predict"],
    keep_alive="30m", timeout_s=900)

tel = run_worker_v2(bundles_path=BUNDLES, out_dir=out,
                    corpus_manifest=CORPUS, base_url=BASE, provider=worker)
tel["declared_deviation"] = {
    "worker_num_ctx": f"8192 (frozen WORKER_OPTIONS) -> {NUM_CTX_V3} via "
                      "custom provider; faithful digests are ~10.1k prompt "
                      "tokens and the frozen ctx rejects them "
                      "(exceed_context_size_error); all else identical"}
(LAB / "results" / "CONT-006-WORKER" / f"cont006-worker-v3-{ts}"
 / "telemetry-v2.json").write_text(
    json.dumps(tel, indent=1, ensure_ascii=True) + "\n", encoding="utf-8")
print(json.dumps(tel, indent=1), flush=True)
print(f"W3 complete: {out}")
