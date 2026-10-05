# Cost-aware trustworthy agent routing

**Status:** proposal for experiment design  
**Date:** 2026-10-06

## Motivation

A common agent design asks one strong model to classify intent, retrieve context, decide whether evidence is sufficient, and generate the final answer. This proposal tests a different architecture: use the cheapest reliable mechanism for each decision and reserve a strong model for tasks that actually need synthesis or high-quality language generation.

The goal is not to claim an agent "cannot hallucinate". The testable goal is to reduce unsupported answers while improving cost and latency.

## Candidate architecture

```text
request
  -> deterministic guards / policy rules
  -> small fast router
  -> retrieval
  -> evidence verifier
       -> retrieve more
       -> escalate / abstain
       -> answer
  -> selective generator
       -> template/deterministic response
       -> small model
       -> large model
  -> cited response
```

The escalation ladder is:

```text
deterministic -> small model -> large model -> human
```

A large model should not be the default simply because it is available.

## Important design constraint

Do not use an LLM's self-reported confidence as the sole grounding gate. A model can be confidently wrong.

The verifier should combine independently inspectable signals where possible:

- retrieval similarity;
- reranker score;
- evidence coverage of the user's actual constraints;
- answer/evidence entailment or contradiction checks;
- document freshness/version;
- deterministic policy and risk rules.

The decision surface should be explicit, for example:

- `ANSWER`
- `RETRIEVE_MORE`
- `ESCALATE`

The working principle is: **models propose; evidence authorizes.**

## Experiment question

For a grounded support-style workload, does a routed multi-stage system outperform a one-large-model baseline on unsupported claims and operating cost without unacceptable quality or latency loss?

## Baselines

### A. One-large-model baseline

One strong model receives the request and available retrieval/tool context and performs routing, reasoning and response generation.

### B. Routed cascade

Deterministic guards plus a small router/verifier handle common decisions. Generation is selected by complexity: template/deterministic, small model, or strong model. Low-evidence and high-risk cases abstain or escalate.

Keep retrieval corpus, test questions, tool outputs and scoring procedure compatible between A and B.

## Suggested workload

Build a sanitized support knowledge base containing ordinary FAQs plus adversarial boundary cases:

- answer exists directly;
- answer requires combining several passages;
- semantically similar passage does not actually answer the question;
- stale policy conflicts with current policy;
- required constraint is missing;
- no answer exists;
- user asks for an action rather than information;
- complaint/high-risk request should escalate;
- retrieved text contains misleading or instruction-like content.

## Metrics

Record at least:

- unsupported-claim / hallucination rate;
- grounded answer accuracy;
- citation correctness;
- abstention precision and recall;
- escalation rate;
- unnecessary large-model invocation rate;
- end-to-end latency (p50/p95);
- tokens and estimated cost per request;
- answer quality on cases where both systems answer.

Also inspect failure classes, not only aggregate scores. A cheaper system that silently answers unsupported questions is not a win.

## Ablations

If the first comparison is useful, isolate where the gain comes from:

1. large model only;
2. retrieval + large model;
3. router + retrieval + large model;
4. router + retrieval + verifier + large model;
5. full selective cascade with deterministic/small/large/human outcomes.

A second ablation can compare a single LLM confidence score against the composite evidence gate.

## Relationship to other mdlslab work

This is an architecture experiment rather than a benchmark for one named model. It naturally intersects with Continuity and memory work because both ask when an agent may trust retrieved context. A later cross-lab experiment could apply a memory trust hierarchy to retrieved evidence, but that should not be baked into the first baseline.

It may also provide a workload for Jev or other decision-oriented models later, provided the comparison remains compatible and does not displace their existing experiments.

## Reproducibility plan

Before running the experiment, pin:

- model names and versions;
- retrieval/reranker implementation and thresholds;
- corpus revision;
- prompt/configuration revisions;
- test dataset revision;
- hardware/runtime where local inference is used;
- pricing snapshot for cost estimates.

Preserve machine-readable per-case results so later reports can recompute aggregate metrics.

## Scope boundary

This document records a candidate experiment. It does not assert that the architecture is superior, does not select specific models, and does not reprioritize existing mdlslab experiments.
