# Continuity (Project C)

**Status:** Research proposal (2026-10-01). No implementation or experimental results yet.

## Purpose

Explore whether persistent autobiographical memory, an explicit self-model, recursive reflection, feedback, and a world model lead to measurable, durable adaptive behavior in an LLM-based agent. This is an engineering study of *behavioral continuity*, not a claim to have built, detected, disproved, or simulated consciousness or subjective experience.

Working nickname: the good-sense Frankenstein experiment.

## Research question

Compared with the same foundation model and a controlled interaction budget, what changes when an agent can accumulate experience, evaluate predicted against observed outcomes, revise a persistent self-description under validation, and resume after interruption? Which changes transfer when the base model is replaced?

See [research proposal](docs/research-proposal.md) for architecture, dependencies, controlled experiments, metrics, risks, and a proposed staged backlog.

## Relationship to other labs

Continuity is a cross-lab architecture experiment, not another model-specific playground. Reuse existing setups by reference rather than copying or migrating them.

| Existing lab | Potential contribution | Initial role |
| --- | --- | --- |
| TencentDB Agent Memory | Persistent memory, retrieval, consolidation | Candidate backend, tested against simple SQLite baseline |
| Muse Glimmer | Local agentic LLM | Candidate core after hardware feasibility |
| Jev / System One | Bounded action or policy decisions | Optional later comparison against deterministic policy |
| Colibri / Mamba | Alternative model architectures | Later core substitution experiments |
| CLI-Anything | Structured environment interaction | Later sandboxed tooling |
| TimesFM | Forecasting time-series state/metrics | Optional, only if useful after simpler forecasting |
| Shared agent-resource-coordination | GPU/download contention control | Reuse where concurrent local runs occur |

The upstream and local status of each candidate must be rechecked and versions pinned before integration. No untested feature is treated as demonstrated.

## Proposed research milestones

- CONT-000: lab-agnostic synthetic workload protocol, measurement harness, local baseline, early variance/headroom pilot.
- CONT-001: Does Continuity Matter? Controlled ablation of memory, self-model, reflection, drive, world model.
- CONT-002: Identity Persistence. Full 2×2 comparison of {core A, core B} × {restored, clean state}, using held-out tasks and a pre-registered retained-benefit endpoint.
- CONT-003 (candidate): reactive versus bounded continuous background cycles.
- CONT-004 (candidate): SQLite baseline versus TencentDB memory implementation.

## First implementation boundary

Start with one compact locally runnable LLM, deterministic tooling and policy, SQLite event store, synthetic-only data, and an explicit stop/budget mechanism. Do not make a 30B model or an external memory framework a prerequisite for the first result. Python is a pragmatic integration choice; the orchestration contract should allow a C# implementation.

## Evidence and publication

Follow the parent repository's [architecture and experiment contract](../../docs/architecture.md): retain environment, pinned artifacts, prompts, configuration, baseline, procedure, raw evidence, failures and limitations. Public repo only: **no personal chat histories**, identifying data, corporate code, private logs, credentials, or model weights without redistribution permission.

The design is a proposal to refine through experiments; do not present hypotheses as accepted decisions or positive experimental findings.
