# TencentDB Agent Memory Lab

## Why this lab exists

Evaluate TencentDB Agent Memory as an external memory layer for agents, separately from the quality of the LLM using it.

The interesting question is not merely whether an agent can retrieve stored text. It is whether the memory system improves useful long-running behavior without introducing unacceptable false recall, latency, token cost, storage growth, privacy risk, or operational complexity.

## Research scope

This lab should cover the project's memory mechanisms and integrations using pinned upstream versions. It should also compare external memory with simpler baselines before attributing improvements to the framework.

Canonical upstream source must be recorded in experiment metadata before execution.

## Research questions

1. What information is written to memory and when?
2. How is information represented, indexed, consolidated, and retrieved?
3. How well does relevant memory survive long conversations and restarts?
4. How often is irrelevant or incorrect memory surfaced?
5. Can contradictory facts be updated cleanly?
6. What happens when memory becomes large?
7. What are the latency and token-cost effects?
8. How portable is stored memory across different LLMs?
9. How much behavior comes from the memory layer versus prompting/scaffolding?
10. Can it be useful as a reference point for an OCL-style cognitive/memory layer?

## Planned experiments

### TAM-001: Local reproducibility

Pin an upstream version and run the smallest local configuration. Record dependencies, storage backend, startup path, and resource use.

### TAM-002: Remember and retrieve

Insert controlled facts over multiple sessions and measure whether the correct facts are retrieved when needed.

### TAM-003: Distractor resistance

Populate memory with semantically related but irrelevant facts and measure false or noisy recall.

### TAM-004: Correction and contradiction

Change previously stored facts and determine whether stale information continues to influence answers.

### TAM-005: Longitudinal growth

Grow the memory store over many synthetic sessions and measure retrieval quality, latency, storage size, and context/token overhead.

### TAM-006: Cross-model portability

Use the same controlled memory dataset with multiple compatible LLMs and separate memory-system effects from base-model effects.

### TAM-007: Baseline comparison

Compare against simpler approaches such as no persistent memory, explicit summaries, and basic vector retrieval.

### TAM-008: OCL comparison

Document conceptual similarities and differences with an operation/cognitive-layer architecture. Keep this architectural: no corporate implementation details or proprietary artifacts belong in the public repository.

## Evaluation dimensions

Candidate measures include retrieval precision/recall on synthetic ground truth, stale-memory rate, contradiction handling, latency, tokens added to context, storage growth, restart persistence, and qualitative agent-task completion.

## Privacy

Memory experiments are especially likely to accumulate sensitive data. Use synthetic or explicitly public test data only. Never use exported personal conversations, corporate logs, credentials, or private documents in this public lab.
