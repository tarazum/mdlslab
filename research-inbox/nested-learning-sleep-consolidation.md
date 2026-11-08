# Nested Learning and Sleep-Inspired Memory Consolidation

- Date: 2026-11-09
- Status: captured
- Scope: research lead only; no experiments authorized
- Tags: continual learning, agent memory, OCL, OSL, memory consolidation, LoRA

## Idea
Investigate whether periodic offline consolidation of agent experience improves retention, reuse, task success, and cost compared with append-only external memory. Separately evaluate whether parameter-efficient adapters (e.g. LoRA) can consolidate knowledge without unacceptable forgetting.

## Research questions
1. How do Nested Learning / Hope and sleep-inspired LLM consolidation actually work according to primary papers?
2. Which mechanisms are architectural/training-time, and which can be approximated at the agent memory layer without weight updates?
3. What is the relationship to OCL and its existing memory/lesson lifecycle? Inspect OCL repository before assuming terminology or implementation.
4. Can an offline consolidation pass merge duplicates, resolve contradictions, retire obsolete lessons, and generate regression tests while retaining provenance?
5. How to prevent hallucinated lessons, feedback loops, contamination, and loss of useful minority cases?
6. Which baselines, metrics, controls and ablations would demonstrate incremental value?

## Candidate comparison (proposal only)
- A: no persistent memory
- B: append-only memory / lessons
- C: retrieval plus deduplication
- D: scheduled consolidation with provenance and validation
- E: synthetic replay (only if justified and leakage-safe)
Measure held-out task success, retention of old tasks, false-memory rate, retrieval precision, latency, token cost, and consolidation overhead. Keep task/model/tool budgets identical; separate offline costs from online costs.

## Sources to verify
- Nested Learning: The Illusion of Deep Learning Architectures (find exact primary paper and implementation)
- Language Models Need Sleep (verify exact publication, methods and availability)
- Google Research technical write-up on sleep-inspired continual learning (verify claims independently)
- Context: https://vt.tiktok.com/ZSpAJUNK4/ (secondary social-media lead, not evidence)

## Boundaries
No claim of benchmark improvement is accepted without matching original experimental setup. Do not conflate Hope with sleep-phase work or external-memory consolidation with weight learning. Do not copy private OCL internals into this public repository. Do not run tests, download models, modify OCL, or open issues without explicit owner approval.

## Next step
Ask an agent to perform a source-grounded OCL architecture review and produce a bounded experiment proposal with risks and go/no-go criteria.