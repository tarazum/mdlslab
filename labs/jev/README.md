# Jev Lab

## Status

Planned. Source identity and technical claims must be pinned to primary documentation before implementation.

## Why this lab exists

Jev represents a different experimental direction from general-purpose language models: decision-oriented inference rather than using free-form text generation as the core decision mechanism.

Current public reporting describes Jev as a model from TypeSafe AI that selects among candidate actions/choices probabilistically and is being explored for agent and control workflows. Because the ecosystem is new and changing quickly, this lab deliberately avoids freezing secondary-source claims into architecture facts until primary artifacts are recorded.

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

Build a deterministic decision dataset with known labels and measure accuracy, latency, cost, and confidence behavior.

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
