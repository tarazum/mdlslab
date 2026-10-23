# Research Inbox (public-safe)

This is a **parking lot, not an experiment backlog**. The lab remains paused unless the owner explicitly restarts an experiment.

## Publication boundary

This repository is **public**. Never commit raw emails, private Gmail links or message IDs, recipient/sender addresses from private correspondence, account numbers, tokens, personal conversations, internal project specifications, proprietary datasets, corporate material, or unpublished commercial plans. Summarize only publicly discussable technologies and general use cases. Verify each external claim against a public primary source before promoting it into a research proposal. Vendor/newsletter claims are **unverified leads**, not lab results.

Keep source messages in Gmail. For a candidate, add a public upstream URL only when verified; otherwise write `source: newsletter lead; primary source pending`. Do not paste newsletter text or copyrighted content. Deduplicate by upstream project/model and version.

## Candidate schema

`ID | technology | general capability | possible application tags | source status | evaluation question | state`

States: `captured` → `source-verified` → `triaged` → `experiment-proposed` (only with explicit approval), or `discarded`. No automatic issues, experiments or model downloads.

## Initial candidates (historical digest leads; unverified)

| ID | Technology / topic | General capability | Possible tags | Source status | Evaluation question | State |
| --- | --- | --- | --- | --- | --- | --- |
| RI-001 | Gradium Phonon | Small, low-latency text-to-speech (published checkpoints do not list Ukrainian) | MARTA, voice UX | Primary source: [upstream](https://github.com/gradium-ai/xn-ptts); vendor benchmarks unverified | Quality, Ukrainian support, CPU latency and licensing? | source-verified |
| RI-002 | Voxtral 3 | Speech/audio models | MARTA | Newsletter lead; primary source pending | Which speech tasks, language support and deployment footprint? | captured |
| RI-003 | Cohere Rerank 5 | Search result reranking | VERPLANN, TSE | Newsletter lead; primary source pending | Does reranking improve useful-source precision per unit cost? | captured |
| RI-004 | Exa 3.0 | Web search/retrieval | VERPLANN, TSE | Newsletter lead; primary source pending | Compare relevance, freshness, provenance, duplication and price against existing providers | captured |
| RI-005 | Durable agent harnesses (including Vercel durable-harness) | Resumable agent execution | VERPLANN, Agent Pool | Newsletter lead; primary source pending | Can interrupted jobs resume without duplicate side effects? | captured |
| RI-006 | Microsoft-Decision-1 | Decision-oriented model | IDENN, decision systems | Newsletter lead; primary source pending | Is decision quality measurably better than an established baseline? | captured |
| RI-007 | Drex 1.5 | Candidate model for decision/reasoning tasks | mdlslab | Newsletter lead; primary source pending | What reproducible task and baseline justify evaluation? | captured |
| RI-008 | TimesFM | Time-series foundation model | IDENN, TSE | Primary source: [upstream](https://github.com/google-research/timesfm); vendor benchmarks unverified | Does it outperform simple forecasting baselines on relevant data? | source-verified |
| RI-009 | Consensus MCP | Scientific literature verification | mdlslab, research agents | Newsletter lead; primary source pending | Can it improve traceable, correctly supported claims? | captured |
| RI-010 | JOLT | Model training/distillation efficiency | mdlslab | Newsletter lead; primary source pending | Are the claimed efficiency gains reproducible in a small setup? | captured |
| RI-011 | OmniParseBench | Document parsing evaluation | research agents | Primary source: [upstream](https://www.datalab.to/blog/why-we-built-omniparsebench); vendor benchmarks unverified | Is the benchmark relevant to document extraction failures? | source-verified |
| RI-012 | Sakana AI peer-review research | Automated research critique | mdlslab | Newsletter lead; primary source pending | Can critiques identify real methodological issues better than baseline review? | captured |
| RI-013 | Recursive Flint | Sparse MoE coding model | mdlslab | Newsletter lead; primary source pending | Can constrained local hardware run a useful configuration? | captured |


## Additional September–October 2026 leads (source verification pending)

These are sanitized, deduplicated *newsletter leads*, not verified model specifications or experimental results. Public primary sources and licenses must be checked before promotion; no private email URLs or metadata are stored. Product tags indicate only generic potential applicability.

| ID | Technology / topic | General capability | Possible tags | Source status | Evaluation question | State |
| --- | --- | --- | --- | --- | --- | --- |
| RI-014 | GLiNER2.5-Decide | Schema-constrained text classification | VERPLANN, Agent Pool | Primary source: [upstream](https://huggingface.co/fastino/GLiNER2.5-Decide); vendor benchmarks unverified | Can calibrated classification reduce routing errors versus rules and a small LLM? | source-verified |
| RI-015 | CLM-8B | Candidate action scoring | Agent Pool, mdlslab | Primary source: [upstream](https://huggingface.co/Contrastive-LM/CLM-v0.1-8B); vendor benchmarks unverified | Does cached action scoring beat generative selection at equal accuracy and cost? | source-verified |
| RI-016 | Cloudflare Clef / Clef-flash | Decision scoring | Agent Pool, IDENN | Primary source: [upstream](https://clef-evals.workers-ai-mle.workers.dev/); vendor benchmarks unverified | Do scores stay calibrated on shifted decision tasks compared with Jev? | source-verified |
| RI-017 | Paper2Agent | Papers converted into callable research tools | mdlslab | Primary source: [upstream](https://github.com/jmiao24/Paper2Agent); vendor benchmarks unverified | Can generated tools reproduce cited results without unsupported operations? | source-verified |
| RI-018 | TabPFN-3.5 | Small-data tabular prediction | TSE, IDENN | Newsletter lead; primary source pending | Does it outperform logistic regression and gradient boosting under leakage-safe splits? | captured |
| RI-019 | EmbeddingGemma 2 | Text embedding and retrieval | VERPLANN, TSE | Newsletter lead; primary source pending | Does retrieval recall improve under equal memory and latency budgets? | captured |
| RI-020 | Meta Rebalancer | Training/data rebalancing | mdlslab | Newsletter lead; primary source pending | Which imbalanced-data metric improves versus weighted sampling? | captured |
| RI-021 | TorchTPU | PyTorch TPU execution backend | mdlslab | Newsletter lead; primary source pending | Is portability worth integration cost for accessible TPU workloads? | captured |
| RI-022 | llm-d (release/version must be pinned) | Distributed inference and cache-aware routing | Agent Pool | Primary source: [upstream](https://github.com/llm-d/llm-d); vendor benchmarks unverified | When does prefix-aware routing beat a simple load balancer? | source-verified |
| RI-023 | DeepInfer | Inference serving engine | Agent Pool | Newsletter lead; primary source pending | Which released components support reproducible throughput comparison? | captured |
| RI-024 | Mistral Timestral | Time-series forecasting | IDENN, TSE | Primary source: [upstream](https://huggingface.co/mistralai/Timestral-5M); vendor benchmarks unverified | Does it beat seasonal naive and TimesFM on identical rolling windows? | source-verified |
| RI-025 | Granite Speech 5.0 | Speech recognition (listed languages do not establish Ukrainian support) | MARTA | Primary source: [upstream](https://huggingface.co/ibm-granite/granite-speech-5.0-2b); vendor benchmarks unverified | What is Ukrainian WER and CPU real-time factor versus Whisper? | source-verified |
| RI-026 | Falcon-ASR | Arabic-focused speech recognition | MARTA | Newsletter lead; primary source pending | Is multilingual transfer relevant, or should this be discarded for Ukrainian speech? | captured |
| RI-027 | Liquid d1-Ultra | Low-latency reasoning model | Agent Pool | Newsletter lead; primary source pending | Can response latency be reproduced at fixed answer quality? | captured |
| RI-028 | Google Harness² | Agent harness optimization | VERPLANN, Agent Pool | Newsletter lead; primary source pending | Can harness-only changes improve task completion with model weights fixed? | captured |
| RI-029 | Perplexity SPACE | Computer-use agent research | VERPLANN | Newsletter lead; primary source pending | How often do actions remain recoverable and auditable after failure? | captured |
| RI-030 | TinyFish MCP | Web retrieval and browser actions | VERPLANN, TSE | Newsletter lead; primary source pending | Does provenance and extraction coverage improve against plain HTTP fetch? | captured |
| RI-031 | MiniMax M3.1 Flash | Agent-oriented hosted model | Agent Pool | Newsletter lead; primary source pending | What is verified task success per dollar compared with existing models? | captured |
| RI-032 | Mistral Large 4 | Large multimodal model | mdlslab | Newsletter lead; primary source pending | Are released weights, license and reproducible evaluation available? | captured |
| RI-033 | Personal Agent Protocol | Agent interoperability | Agent Pool | Newsletter lead; primary source pending | Can two heterogeneous agents exchange bounded capabilities safely? | captured |
| RI-034 | AgentEnv | Agent environment/evaluation tooling | Agent Pool, mdlslab | Newsletter lead; primary source pending | Does environment replay reproduce failures deterministically? | captured |
| RI-035 | GLiFormer | Lightweight classification architecture | VERPLANN | Newsletter lead; primary source pending | Can it reduce false-positive opportunity routing compared with rules? | captured |
| RI-036 | Nemotron 3 Diarization | Speaker diarization | MARTA | Primary source: [upstream](https://huggingface.co/nvidia/Nemotron-3-Diarization); vendor benchmarks unverified | What diarization error rate holds on Ukrainian multi-speaker audio? | source-verified |
| RI-038 | NVIDIA Run:ai | GPU resource scheduling | Agent Pool | Newsletter lead; primary source pending | Would GPU scheduling reduce idle time versus a simple lock-based allocator? | captured |

**Triage note:** Names, versions, claimed benchmark results, and availability are not independently confirmed. Existing RI-001–RI-013 and lab subjects were not re-added. Priority areas for later consideration: speech UX, calibrated decision/routing models, agent reliability, and provenance-aware retrieval. No experiment is authorized by this inventory.

## Triage policy

1. Batch ingest weekly or on demand; avoid daily proposal spam.
2. One row per distinct candidate; merge repeated newsletter mentions.
3. Prefer public upstream documentation/papers/repos; record publication date and license.
4. Evaluate fit using a **concrete question**, feasibility and cost; do not infer product integration from a newsletter.
5. Promote only a small number of candidates when work resumes, with baseline, metrics, budget and stop criteria.

**Provenance:** This initial set is a sanitized collection of leads mentioned in previous email-digest discussions. Names and product tags are hypotheses, not verified specifications or private project requirements.

## Source audit (2026-10-23; documentary only)

**Scope:** September–October 2026 newsletter triage, current Research Inbox, repository labs and public upstream checks. A source-verified state means the linked upstream project/model or benchmark is identifiable; it **does not** independently validate advertised accuracy, latency, model capability, license for all variants, or practical suitability. Do not treat a source link as an experiment.

- **Inventory integrity:** 37 actual rows, IDs RI-001–RI-036 and RI-038. RI-037 is absent (numbering gap, not a hidden candidate). No new row was created in this audit. Existing TimesFM lab is a related research subject, not a duplicate row; Jev remains a comparator, not a new proposal.
- **Public primary sources found for 11 records:** RI-001, RI-008, RI-011, RI-014, RI-015, RI-016, RI-017, RI-022, RI-024, RI-025, RI-036. All remaining 26 entries retain `captured` and need an exact upstream release/paper/repository match before promotion. The Clef link is the vendor's evaluation page, not independent validation of model weights; treat that link as a **partial** source check.
- **Repeated mentions collapsed by subject:** decision models (Jev, Clef, GLiNER, CLM), OmniParseBench, Phonon, Voxtral, DeepInfer and agent harnesses were mentioned in more than one issue. These are cross-issue repeats, **not** additional candidate rows. The number of all rejected newsletter mentions cannot be determined from the current 37-row inventory alone.
- **Misfit / deprioritization:** Phonon and Granite Speech published model descriptions do not establish Ukrainian-language support; Falcon-ASR targets Arabic, so do not assume Ukrainian ASR suitability. Distributed TPU/Kubernetes and Run:ai topics have higher infrastructure requirements than lightweight local experiments. Mistral Large 4 and Recursive Flint require feasibility screening before any local-model plan.
- **Vendor-claim quarantine:** reported leaderboard scores, claimed speedups, release timelines, API prices, licenses and third-party comparisons are unverified until exact upstream release, independent methodology and date are checked. For OmniParseBench, the publisher also sells a parser, creating a potential benchmark conflict; retain baseline and dataset provenance scrutiny.
- **Highest potential relevance (hypotheses):** MARTA: speech quality/latency/language coverage; VERPLANN and Agent Pool: typed decisions, durable execution, provenance-aware retrieval; IDENN and TSE: leakage-safe tabular/time-series forecasting and source verification; mdlslab: reproducibility and automated research critique. No product-specific architecture, private requirements or commercial data are included.
- **Future verification gates:** pin model/release/commit, check weights and exact license, independent metrics, applicable languages, reproducible baseline, operational cost and stop criterion. Nothing here authorizes experiments.

**Audit limitation:** A complete message-by-message reconciliation of *every* historical evening digest and *every* relevant September–October newsletter is not evidenced by this file. The counts above describe the 37 stored candidates, not an exhaustive census of all ideas in Gmail. The previous inventory should not have been described as fully deduplicated or fully sourced.
