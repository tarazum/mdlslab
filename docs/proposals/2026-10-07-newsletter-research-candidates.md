# Proposal: candidates from AI/newsletter review — 2026-10-07

## Status

Exploratory proposal only. This document preserves candidates for future research and does not change the priority or state of existing experiments.

## Context

A review of recent AI/engineering newsletters surfaced several items that may be useful for `mdlslab`. The goal is not to start new experiments immediately, but to preserve potentially valuable candidates without disrupting the current experiment queue.

Anything derived from newsletter summaries should be re-verified against primary upstream sources before implementation or publication as a technical claim.

## 1. Forecasting with adversarial traps — high priority

A Towards Data Science article described an evaluation setup where a forecasting task intentionally contains several traps and multiple AI assistants are tested against them.

### Why this matters

This is especially relevant to the lab's falsification/evaluation work.

Instead of asking only:

> Can the model produce a forecast?

the benchmark can ask:

> Can the model detect that the apparent predictive signal is misleading, insufficient, contaminated, or structurally invalid?

This would test whether a model:

- blindly extrapolates patterns;
- notices leakage or misleading correlations;
- distinguishes signal from artefact;
- questions invalid assumptions;
- refuses to overclaim when evidence is weak;
- detects dataset-construction traps;
- changes its conclusion when contradictory evidence is introduced.

### Proposed direction

Create a small `forecasting-traps` benchmark with deliberately constructed cases.

Candidate trap classes:

1. **Temporal leakage**
   - Future information accidentally appears in training features.

2. **Spurious correlation**
   - A variable predicts the target in training data but has no causal or stable relationship.

3. **Regime shift**
   - Training and evaluation periods follow different dynamics.

4. **Misleading trend**
   - A strong recent trend tempts extrapolation despite longer-term evidence against it.

5. **Insufficient evidence**
   - The dataset is too short or noisy for the requested confidence level.

6. **Contradictory indicators**
   - Different signals imply incompatible forecasts.

### What to measure

Compare systems not only by forecast error but also by:

- trap-detection rate;
- false-confidence rate;
- calibration;
- whether the system explicitly identifies the problematic assumption;
- whether it requests additional evidence;
- whether its conclusion changes after a counterexample is introduced.

This could become a bridge between falsification work and future TimesFM/time-series experiments.

**Candidate priority:** High.

---

## 2. AgentEnv — environment-level evaluation for agents

AgentEnv may be interesting as infrastructure for evaluating agents inside controlled environments.

### Research questions

- Can it provide reproducible environments for agent experiments?
- Can we define controlled failure conditions and hidden traps?
- Does it support deterministic reruns sufficiently well for benchmark comparison?
- Can it help separate:
  - model capability,
  - agent-harness behavior,
  - environment/tool effects?

### Possible use

If suitable, AgentEnv could become infrastructure for several existing lab tracks rather than a standalone playground.

**Candidate priority:** Medium-high.

---

## 3. Personal Agent Protocol

Investigate the Personal Agent Protocol as a possible interoperability layer for agent systems.

### Questions to answer

- What exactly does the protocol standardize?
- Does it overlap with MCP, ACP, A2A, or other agent protocols?
- Is it designed for tool interaction, agent identity, context transfer, delegation, or personal-agent portability?
- Could it help with continuity/memory experiments?

Potentially relevant to the Continuity lab if it enables state or context transfer between different agent implementations.

**Candidate priority:** Medium.

---

## 4. TinyFish / TinySearch / TinyFetch / TinyBrowser

This tool family appears to target lightweight web-agent workflows and MCP-style integration.

Rather than testing each component independently, evaluate the stack as one candidate **web research harness**.

### Possible comparison

Compare against the current approach on a small research benchmark:

- search;
- page retrieval;
- structured extraction;
- navigation;
- evidence collection;
- final answer quality.

Measure:

- latency;
- token usage;
- number of tool calls;
- retrieval accuracy;
- failure modes;
- resistance to irrelevant page content.

Potentially useful for agents that do not require a full browser environment.

**Candidate priority:** Medium.

---

## 5. Mistral Large 4 / “Le Chonk”

Track the announced open-weight multimodal MoE model once weights are actually available.

Reported characteristics are interesting primarily because of the ratio between total and active parameters and the claimed large context window.

### Do not benchmark yet

Wait for:

- official weights;
- license;
- hardware requirements;
- verified context limits;
- inference support in common runtimes.

Once available, evaluate whether it is practical for local or rented-GPU experimentation.

Possible relevance:

- agent reasoning;
- long-context experiments;
- multimodal tasks;
- comparison against other open-weight frontier candidates.

**Candidate priority:** Watchlist.

---

## 6. EmbeddingGemma 2

Evaluate as a possible embedding-model candidate rather than as a general model experiment.

Potential use cases:

- memory retrieval;
- semantic search;
- Continuity experiments;
- repository/document retrieval;
- comparison with current embedding approaches.

A compact benchmark may be sufficient:

- retrieval precision;
- recall;
- semantic near-duplicate discrimination;
- delayed-recall cases;
- multilingual Ukrainian/English retrieval.

**Candidate priority:** Medium.

---

## 7. Meta Rebalancer

Keep as a research candidate until its mechanism and applicability are clearer.

The interesting question is whether it can improve model/data balancing, evaluation robustness, or inference behavior in a way relevant to existing lab experiments.

Do not create a dedicated experiment yet.

**Candidate priority:** Watchlist.

---

## Suggested ordering

Recommended ordering without displacing existing work:

1. **Forecasting adversarial traps**
2. **AgentEnv investigation**
3. **Personal Agent Protocol**
4. **Tiny web-agent stack**
5. **EmbeddingGemma 2**
6. **Mistral Large 4 when weights become available**
7. **Meta Rebalancer investigation**

The forecasting-trap idea is the strongest candidate because it naturally extends existing falsification work instead of opening an unrelated research branch.

## Relationship to existing mdlslab work

The proposal is intentionally cross-lab:

- forecasting traps can complement `labs/timesfm/`;
- AgentEnv and the web-agent stack may become shared evaluation infrastructure if reuse is demonstrated;
- Personal Agent Protocol may be relevant to `labs/continuity/`;
- EmbeddingGemma 2 may be relevant to continuity/memory and retrieval experiments;
- Mistral Large 4 remains a model watchlist candidate until primary-source verification and runtime feasibility are available.

Per the repository architecture, these remain research backlog candidates rather than findings or accepted decisions.
