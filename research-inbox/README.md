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
| RI-001 | Gradium Phonon | Small, low-latency text-to-speech | MARTA, voice UX | Newsletter lead; primary source pending | Quality, Ukrainian support, CPU latency and licensing? | captured |
| RI-002 | Voxtral 3 | Speech/audio models | MARTA | Newsletter lead; primary source pending | Which speech tasks, language support and deployment footprint? | captured |
| RI-003 | Cohere Rerank 5 | Search result reranking | VERPLANN, TSE | Newsletter lead; primary source pending | Does reranking improve useful-source precision per unit cost? | captured |
| RI-004 | Exa 3.0 | Web search/retrieval | VERPLANN, TSE | Newsletter lead; primary source pending | Compare relevance, freshness, provenance, duplication and price against existing providers | captured |
| RI-005 | Durable agent harnesses (including Vercel durable-harness) | Resumable agent execution | VERPLANN, Agent Pool | Newsletter lead; primary source pending | Can interrupted jobs resume without duplicate side effects? | captured |
| RI-006 | Microsoft-Decision-1 | Decision-oriented model | IDENN, decision systems | Newsletter lead; primary source pending | Is decision quality measurably better than an established baseline? | captured |
| RI-007 | Drex 1.5 | Candidate model for decision/reasoning tasks | mdlslab | Newsletter lead; primary source pending | What reproducible task and baseline justify evaluation? | captured |
| RI-008 | TimesFM | Time-series foundation model | IDENN, TSE | Existing lab topic; verify upstream/version | Does it outperform simple forecasting baselines on relevant data? | captured |
| RI-009 | Consensus MCP | Scientific literature verification | mdlslab, research agents | Newsletter lead; primary source pending | Can it improve traceable, correctly supported claims? | captured |
| RI-010 | JOLT | Model training/distillation efficiency | mdlslab | Newsletter lead; primary source pending | Are the claimed efficiency gains reproducible in a small setup? | captured |
| RI-011 | OmniParseBench | Document parsing evaluation | research agents | Newsletter lead; primary source pending | Is the benchmark relevant to document extraction failures? | captured |
| RI-012 | Sakana AI peer-review research | Automated research critique | mdlslab | Newsletter lead; primary source pending | Can critiques identify real methodological issues better than baseline review? | captured |
| RI-013 | Recursive Flint | Sparse MoE coding model | mdlslab | Newsletter lead; primary source pending | Can constrained local hardware run a useful configuration? | captured |

## Triage policy

1. Batch ingest weekly or on demand; avoid daily proposal spam.
2. One row per distinct candidate; merge repeated newsletter mentions.
3. Prefer public upstream documentation/papers/repos; record publication date and license.
4. Evaluate fit using a **concrete question**, feasibility and cost; do not infer product integration from a newsletter.
5. Promote only a small number of candidates when work resumes, with baseline, metrics, budget and stop criteria.

**Provenance:** This initial set is a sanitized collection of leads mentioned in previous email-digest discussions. Names and product tags are hypotheses, not verified specifications or private project requirements.
