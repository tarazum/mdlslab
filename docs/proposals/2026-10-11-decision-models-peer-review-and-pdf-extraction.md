# Proposal: verify decision models, AI peer review, and PDF extraction benchmark — 2026-10-11

## Status and provenance

Exploratory candidates from a Marktechpost newsletter summary dated 2026-10-11. **Names, releases, metrics and capabilities have not been independently verified.** This is a request to investigate primary sources, not approval to start new experiments or reprioritize existing work.

## Candidates to verify

### 1. Drex 1.5 — decision-model candidate (first research priority)

Newsletter claim: open 9B-parameter decision model. Verify the exact name, publisher, model card, weights, license, architecture, supported tasks and hardware footprint. Assess whether the model is meaningfully comparable to [Jev](../../labs/jev/) and the previously noted Liquid AI decision-model leads.

If confirmed, outline a small, reproducible feasibility evaluation: action selection, conflicting evidence, abstention, stability across runs, latency and memory usage, with deterministic and general-purpose LLM baselines. Do not schedule the experiment yet.

### 2. Sakana AI Peer Review — scientific claim-checking (first research priority)

Newsletter claim: detection of 73% of deliberately inserted errors in key claims. Verify the primary paper or project, exact experimental setup, denominator, error types, baseline, confidence intervals and whether the quoted metric means what the newsletter suggests.

Potential connection to [full-text research verification proposal](2026-10-10-agent-spending-and-fulltext-research.md): compare AI-assisted review against grounded passage-level evidence, assess false positives, missed methodological problems, hallucinated citations and reproducibility. Prefer openly licensed papers and controlled injected-error fixtures.

### 3. Microsoft-Decision-1 — decision-model candidate

Newsletter claims a model for evaluating options with median latency of 85 ms. First establish whether this exact product/model exists, who published it, its interface, benchmark task, hardware, batch size and definition of latency. Compare conceptual overlap with Drex/Jev only after validating those facts.

### 4. OmniExtractBench — PDF structured-extraction benchmark

Newsletter claims a dataset of 620 documents. Verify upstream repository/paper, document count, licensing, annotation quality, task definitions and availability. Evaluate relevance to extracting tables, figures, citations and methods from scientific PDFs. Possible shared evidence-ingestion benchmark, but avoid creating another independent lab until reuse is demonstrated.

## Suggested next step

Conduct a **primary-source fact-check and feasibility note** for all four leads. Focus first on **Drex 1.5** and **Sakana AI Peer Review**, then decide whether either merits a bounded experiment. Record official URLs, version pins, licensing, reproduction constraints and explicit reasons to proceed or drop each lead.

## Boundaries

- Preserve the current mdlslab experiment queue.
- Vendor/newsletter numbers are hypotheses to verify, not lab findings.
- Do not add proprietary papers, model weights, unsafe artifacts or private correspondence to the public repository.

## Related proposals

- [Earlier decision-model and model-safety candidates](2026-10-08-model-safety-and-decision-models.md)
- [Full-text scientific verification](2026-10-10-agent-spending-and-fulltext-research.md)
