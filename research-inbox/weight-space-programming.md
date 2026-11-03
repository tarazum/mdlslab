# Weight-Space Programming and Modular Capability Adapters

Status: research proposal only; no experiment authorized or started.
Date captured: 2026-11-04
Repository: mdlslab / Research Inbox

## Primary evidence

- MIT CSAIL, Takehi et al. (2026-11-02): https://rikiyat.github.io/blog/weight-space-programming/
- Published logs and evaluation artifacts: https://github.com/RikiyaT/lm_understand-logs
- Published Qwen patch/checkpoint: https://huggingface.co/RikiyaT/Qwen3.5-0.8B-weight-space-programming

Author-reported findings: small game-playing policies generated directly without gradient descent; a targeted change to 0.016% of Qwen3.5-0.8B weights improved MATH-500 from 7.9% to 48.1%, primarily by addressing reasoning loops. This is early research, not evidence that an LLM can construct a general-purpose language model from scratch. Experiments on larger language models used Python inspection and limited forward passes. The Gemma 3 270M follow-up did not show a comparable gain. Independent replication and evaluation leakage controls remain important.

## Research questions

1. Can an LLM identify the function of specific weights or attention heads from weight inspection better than chance and simple structural heuristics?
2. Can it generate a small, useful network from scratch without training or feedback, and outperform deterministic hand-coded and conventionally trained baselines?
3. Can it repair a reproducible failure by editing a tiny fraction of weights while preserving unrelated capabilities?
4. Can it directly synthesize a low-rank adapter (LoRA-like A and B matrices) from a natural-language capability specification, without gradient descent?
5. Do dynamically loaded adapters improve specialized behavior without unacceptable interference, latency, or reliability loss?

## Proposed experimental tracks (not approved for execution)

### WSP-001: Read weights and localize a circuit
- Start with tiny controlled MLP/Transformer tasks with known causal mechanisms and multiple random seeds.
- Provide only allowed weight slices, architecture, and an explicit specification of available tools.
- Ask a reasoning LLM to predict behavior and locate responsible components.
- Baselines: chance, simple heuristics, shuffled weights, and mechanistic interpretability probes.
- Metrics: prediction accuracy, localization precision, intervention effect, tokens/cost and runtime.
- Controls: blind task labels, held-out seeds, independent evaluator, no test answers in prompts.

### WSP-002: Synthesize a network from scratch
- Choose deterministic toy control, arithmetic or finite-state tasks before any language-model claim.
- Ask the LLM to emit tensor values or a deterministic generator script; prohibit training loops, optimizers, and gradient steps.
- Compare against analytical hand-built solutions, random weights, and conventional training at matched inference budgets.
- Metrics: held-out task success, generalization to unseen inputs, weight count, synthesis cost, and reproducibility.
- Stop criterion: no consistent advantage over simple baselines or evidence of benchmark-specific memorization.
- Boundary: constructing a general-purpose LLM from scratch is not currently supported by this evidence.

### WSP-003: Targeted model repair
- Reproduce a known small-model failure and inspect the MIT Qwen experiment's published patch methodology.
- Compare original, published patch, random same-size patch, activation steering, and optionally conventional fine-tuning.
- Use disjoint diagnostic and final evaluation sets, multiple seeds and equal generation settings.
- Metrics: target failure rate, held-out task quality, instruction following, unrelated-task regressions, patch sparsity and cost.
- Never claim that removing an obstruction proves acquisition of new knowledge.

### WSP-004: Synthesized modular adapters
- Base model remains immutable. Represent each module as an isolated low-rank delta, W' = W + scale * B * A, with versioned metadata.
- Hypothesis A: reasoning LLM can synthesize useful A/B matrices directly without gradient descent.
- Hypothesis B: traditional LoRA training provides a stronger baseline at acceptable cost.
- Hypothesis C: a router can activate a relevant adapter per request without catastrophic interference.
- Baselines: no adapter, RAG-only, trained LoRA, prompt-only, and (where supported) adapter composition.
- Evaluate new task behavior, factual reliability, forgetting/interference, conflicting adapters, latency, memory, and cost.
- Separate procedural capability from factual knowledge: adapters are not a trustworthy mutable fact store; use RAG for auditable, updatable facts.
- Possible adjacent techniques to review: PEFT/LoRA, multi-adapter serving, adapter fusion, model merging, and modular Mixture-of-Experts. These are not equivalent approaches.

## Suggested execution order and gates

1. Literature and artifact audit; pin upstream commits, licenses, environment, model revisions and benchmark definitions.
2. WSP-001 on tiny models, CPU-first.
3. WSP-002 on constrained deterministic tasks.
4. WSP-003 only after clean baseline replication.
5. WSP-004 only if the preceding work shows credible causal control over weights.

No downloads, GPU jobs, repository migrations, issue creation or experiments are authorized by this proposal.

## Safety, provenance and reproducibility

- Public sources only; no private datasets, correspondence, credentials, or corporate artifacts.
- Treat generated tensor-editing code as untrusted; sandbox it with no network and strict filesystem scope.
- Keep immutable base checkpoints, explicit sparse diffs, tensor hashes, evaluation logs, negative results, and rollback procedures.
- Prevent test-set leakage and report both success and failures.
- Any future implementation must follow mdlslab experiment contract and require explicit owner approval.

## Initial assessment

Small network synthesis: demonstrated for selected constrained tasks, with generalization still to test.
Direct generation of a general-purpose LLM: speculative and currently impractical.
Modular capability adapters: technically established via trained LoRA; direct LLM synthesis of useful adapters without training remains an open hypothesis.
For fresh factual knowledge, RAG remains the practical default; adapters are better candidates for skills, behaviors, and domain-specific transformations.
