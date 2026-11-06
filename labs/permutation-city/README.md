# Permutation City — computation, identity, and artificial worlds

Status: **planned / parked**. No experiment, issue, model download, or scheduled work is authorized.

## Motivation
Greg Egan's *Permutation City* (1994) raises questions about substrate independence, subjective continuity, and artificial worlds. The novel's Dust Theory is a speculative philosophical thesis, **not** an established physical or computational result. This track separates testable engineering properties from claims about consciousness.

## Research questions
1. Which properties of a deterministic computation survive reordering of independent evaluation steps?
2. How do checkpoint, restore, fork, and merge affect a software agent's state identity, history, and behavior?
3. Can simple local rules produce persistent structures, replication, adaptation, and memory in an artificial world?
4. What assumptions would be needed to infer conscious experience from a functional simulation, and which are currently untestable?
5. What are the objections to Dust Theory: causation, arbitrary mappings, observer measure, and falsifiability?

## Proposed experiments (not started)
### PC-001 — Permuted computation
- Implement a small deterministic state-transition model with explicit dependency graph, event log, and canonical state hashes.
- Compare chronological execution with valid alternative topological schedules and replay from checkpoints.
- Measure state equivalence, reproducibility, causal dependencies, and failure modes.
- **Limit:** out-of-order execution of independent steps does not demonstrate consciousness or the Dust Theory.

### PC-002 — Agent identity fork
- Snapshot and fork a deterministic agent with memory, goals, and an auditable event history; give branches different inputs.
- Compare behavioral divergence, replay consistency, and merge conflicts; define identity as an operational equivalence relation rather than subjective personal identity.
- Optional LLM variant only after deterministic baseline; record stochasticity and model version.
- **Limit:** matching memory or behavior is not evidence of shared subjective experience.

### PC-003 — Mini Autoverse
- Build a minimal cellular-automaton / artificial-life environment with fixed rules and seeds.
- Track persistence, replication, complexity proxies, and robustness across seeds and perturbations.
- Include null models and negative controls.
- **Limit:** emergence, complexity, and adaptation are not evidence of consciousness.

## Prerequisites / promotion gates
- Review Egan's official novel page and Dust Theory FAQ; distinguish fictional mechanisms from author commentary.
- Write explicit hypotheses, baseline, measurable acceptance criteria, failure criteria, and reproducibility plan before coding.
- Keep any work public-safe; no private conversations, credentials, proprietary data, or corporate material.
- Owner must explicitly approve promotion from parked research to an active experiment.
- Suggested sequence: PC-001 → PC-002 → PC-003; no deadline.

## Primary references
- Greg Egan, *Permutation City* (1994): https://www.gregegan.net/PERMUTATION/Permutation.html
- Greg Egan, Dust Theory FAQ (contains spoilers): https://www.gregegan.net/PERMUTATION/FAQ/FAQ.html

## Related mdlslab work
- [Continuity](../continuity/) — behavioral continuity and memory; coordinate rather than duplicate its experiments.
