# Jev Lab

## Status

JEV-000 closed for the local track on 2026-10-01: primary sources pinned (see Upstream snapshot). The TypeSafe hosted API is pinned at surface level only; no experiments run yet.

## Why this lab exists

Jev represents a different experimental direction from general-purpose language models: decision-oriented inference rather than using free-form text generation as the core decision mechanism.

Current public reporting describes Jev as a model from TypeSafe AI that selects among candidate actions/choices probabilistically and is being explored for agent and control workflows. Because the ecosystem is new and changing quickly, this lab deliberately avoids freezing secondary-source claims into architecture facts until primary artifacts are recorded.

## Upstream snapshot

Verified 2026-10-01 against primary pages.

### TypeSafe Jev (origin of the API class)

- Publisher: TypeSafe AI, San Francisco ("machine-native intelligence infrastructure for automation").
- Jev is described as their first public "System One Model" — a model class returning typed decisions with calibrated probabilities, trained via RLCD (Reinforcement Learning for Calibrated Decisions).
- Delivery: hosted service (console.typesafe.ai, docs.typesafe.ai); no local runtime from TypeSafe. Pricing published as $42 per 1B input tokens. No model/SDK license stated on the site.
- Marketing claims ("238x cheaper than Claude Fable 5.1", "zero hallucinations", "193.6x faster") are context only, not lab findings.

### Ollama System One API (local path)

- Announced 2026-09-29 in the Ollama blog; requires Ollama >= 0.35.0 (v0.35.0 released 2026-09-28; v0.35.1-rc0 current as of verification).
- Endpoint: `POST /v1/systemone`, local only, no auth. Explicitly based on TypeSafe's Jev API. Cloud and MLX/Safetensors models are rejected; requires compatible GGUF weights.
- Contract, pinned from docs.ollama.com/api/systemone:
  - Request: `model`; `state` (nonempty string/object/array, serialized JSON — not chat input); `questions` — 1–64 named questions, each scored independently against the full state (answers are not chained).
  - Question types: `choice` (2–26 options keyed to descriptions), `noul` (yes/no, returns probability 0–1 of true — not a boolean), `score` (rubric of 2–26 levels, zero-based).
  - Response: per question `choice` + normalized `probabilities` + `confidence`; `noul` probability; `score` as probability-weighted index plus `legend`; `usage` with `input_tokens`/`output_tokens`.
  - `confidence` = 1 − H(p)/ln(N); the docs state explicitly it is "Not calibrated correctness" — this makes calibration a first-class lab question, not an assumption.
  - Limits: single JSON response (no streaming, tools, or images); request body <= 64 KiB; no input truncation.

### Local models

- `nimble` (Bespoke Labs): 9B, fine-tuned from Qwen3.5-9B, Apache 2.0, 9.5 GB, 256K context window (~8,192-token effective prompt). Vendor claim: answers under 100 ms on an M5 Max MacBook Pro.
- `tev1:4b` and `tev1:0.8b` (Together AI, labeled experimental): fine-tuned from Qwen3.5; 4.5 GB / 812 MB; 256K context window, runs internally at roughly 2,000 tokens. Dataset builders and training scripts are MIT; the model-weight license is not explicitly stated — verify before redistribution or product use.
- Hardware note for this lab's reference laptop (8 GB VRAM): nimble exceeds VRAM and will partially offload to RAM; tev1:0.8b fits entirely. Correctness experiments are unaffected; latency comparisons must state the offload state.

### Vendor benchmarks (context, not findings)

- Bespoke's 13 public datasets (3,880 decisions): nimble 9B 75.7% mean vs Jev 1.13 76.0% vs tev1 4B 73.3% vs tev1 0.8B 63.5%. Bespoke held-out set: 90.12% agreement for nimble vs 66.36% for base Qwen3.5-9B. Together dev numbers: 88% main decision set, 100% policy transfer.
- Upstream-stated caveats: prompt injection untested, non-English input untested, calibration untested, not intended as the sole decision-maker in high-stakes settings.

## Research questions

1. What exactly is Jev's public API and model contract?
2. Is it locally runnable, hosted, or both?
3. What parts are open source or open weight, and under what license?
4. How are candidate decisions represented and scored?
5. Where does a decision model outperform an LLM selecting an action through generated text?
6. What scaffold is required around the model?
7. How stable are decisions under reordered or semantically equivalent candidate choices?
8. Can it reduce latency/cost in routing, classification, control, or agent-policy workloads?
9. How should uncertainty and confidence be calibrated and consumed?

## Planned experiments

### JEV-000: Source verification

Locate and pin primary documentation, repository/model artifacts, license, API, version, and reproducible installation/invocation instructions.

### JEV-001: Minimal decision task

Build a deterministic decision dataset with known labels and measure accuracy, latency, cost, and confidence behavior. With nimble, tev1:4b, and tev1:0.8b all callable through the same local endpoint, model size becomes a cheap additional axis on one harness.

### JEV-002: Choice-order robustness

Shuffle equivalent candidate sets and measure whether output changes for irrelevant positional reasons.

### JEV-003: LLM comparison

Compare Jev with an LLM performing the same bounded selection task. Keep the surrounding scaffold identical where possible.

### JEV-004: Agent routing

Test model/tool/task routing where the action space is explicit and finite.

### JEV-005: Long-running control loop

If the API is suitable, evaluate repeated state/action decisions and identify loops, drift, and recovery behavior.

## Evidence rule

Until JEV-000 is complete, external demonstrations and media reports are leads, not verified specifications.
