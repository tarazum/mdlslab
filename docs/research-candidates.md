# Research candidates

This page is a parking area for potentially useful technologies discovered while other mdlslab experiments are already queued or in progress.

Items listed here are **not part of the active experiment backlog**. Adding a candidate does not imply priority, approval, or a commitment to create a lab. Promotion into `labs/` should happen only when there is capacity and a concrete experiment question.

## Current candidates

### DeepSeek Harness v0.2

**Category:** agent runtime / orchestration  
**Candidate value:** high  
**Priority effect:** none; do not displace existing experiments

Why it may be worth evaluating:

- Open-source agent harness with Windows and macOS desktop applications.
- Plugin-oriented architecture, including the agent loop itself.
- Standard, Creator, PTC, and Minimal session modes.
- Creator mode can let an agent create and install plugins.
- Supports OpenAI-compatible endpoints, which makes model/runtime separation testable.
- Experimental Claude Code Mods compatibility creates a possible comparison point with coding-agent workflows.

Possible future questions:

- How much agent behavior comes from the harness versus the underlying model?
- Can the same model be compared across DeepSeek Harness and another coding-agent runtime?
- Does Creator mode improve long-running tasks or mainly increase failure surface?
- Could its plugin architecture inform mdlslab's continuity or agent-tooling experiments?

**Suggested relationship:** evaluate later alongside agent tooling such as CLI-Anything or as an execution environment for a model already selected for testing. Do not create a standalone experiment merely because the harness exists.

### OmniExtractBench

**Category:** document extraction benchmark  
**Candidate value:** high for document-heavy workloads  
**Priority effect:** none

Why it may be useful:

- Open benchmark focused on structured extraction from PDFs.
- Includes hundreds of documents from multiple sources, including long documents.
- Scoring distinguishes fabricated values and invented fields rather than treating all extraction errors alike.
- Table matching is designed to avoid one missing row cascading into many false mismatches.

Possible future questions:

- Can it provide a reusable evaluation layer for document-ingestion experiments?
- Which extraction pipeline fails least dangerously on financial statements, reports, and contracts?
- Can its error taxonomy be reused for sanitized domain-specific tests?

**Suggested relationship:** keep as shared evaluation infrastructure candidate rather than a new model lab. It becomes more valuable when mdlslab has a concrete PDF/document extraction experiment.

### Aleph Alpha Kolibri

**Category:** open-weight MoE model / architecture study  
**Candidate value:** medium-high as research; low for immediate local execution  
**Priority effect:** none

Why it is interesting:

- 78.1B-parameter English-German MoE with about 3.46B active parameters per token.
- Very long context and an architecture optimized around sparse expert activation.
- Apache 2.0 and positioned for sovereign / regulated deployment.
- Interesting case for cost-intelligence and active-parameter efficiency.

Practical constraint:

- The published FP8 checkpoint is far beyond the lab laptop's current 8 GB VRAM budget, so this is not an immediate local-playground candidate.
- Treat vendor benchmark claims as context until independently reproduced.

Possible future questions:

- What does Kolibri demonstrate about sparse MoE efficiency compared with smaller dense models?
- Is remote/cloud evaluation justified by a specific experiment?
- Are smaller quantized/community formats eventually available that make a constrained-hardware test meaningful?

**Suggested relationship:** architecture/research watch first. Promote only if accessible inference options or a compelling comparative experiment emerge.

### Qwen model-family evolution

**Category:** model-family research / possible future local candidate  
**Candidate value:** medium  
**Priority effect:** none

The recent Qwen history is useful mainly as context for how an open model family scales from small deployable models to very large MoE systems while changing the open/API boundary over time.

Possible future questions:

- Which Qwen generation and quantization is actually practical on the lab's constrained hardware?
- Is there a useful reasoning baseline for comparison with Jev or other decision-oriented systems?
- Which model provides the best capability-per-VRAM point rather than the best headline benchmark?

**Suggested relationship:** no separate lab yet. Revisit when a specific Qwen model answers an experiment need.

### OmO + Herdr: agent orchestration versus terminal runtime

**Category:** agent harness / persistent coding-agent workspace  
**Candidate value:** high for bounded comparisons; independent evaluation of both layers  
**Priority effect:** none; keep current experiments unchanged

[Evaluation proposal](proposals/2026-10-08-omo-herdr-agent-workspace-evaluation.md) records separate test questions for OmO's multi-model orchestration and memory (Kibitzer), Herdr's terminal persistence and agent-state visibility, and the optional third-party OmO Herdr DAG viewer.

Test Herdr first with existing Codex and Claude Code CLIs, then assess OmO independently on matched, sanitized tasks. ZCode/GLM IDE behavior does not automatically become a Herdr pane. Evaluate Windows support, provider/billing boundaries, security permissions, status accuracy, task correctness, token costs, and overlap with Continuity before scheduling a dedicated experiment.

**Suggested relationship:** cross-cutting candidate for agent tooling and Continuity, not a new lab or immediate migration.

## Promotion rule

A candidate should move from this page into `labs/` only when all of the following are true:

1. There is a concrete question worth testing.
2. The experiment adds information not already covered by an existing lab.
3. Required hardware, API access, data, and time are realistically available.
4. Higher-priority queued experiments are not displaced without an explicit reason.
5. A minimal reproducible experiment can be defined before implementation starts.

This keeps discoveries from being lost without turning every interesting release into another unfinished playground.
