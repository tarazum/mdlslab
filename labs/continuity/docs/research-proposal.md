# Continuity: research and architecture proposal

Date: 2026-10-01  
Status: Proposed; no implementation or experimental evidence yet.

## 1. Motivation and scope

Study *behavioral continuity* in a persistent agent: an agent that tracks interactions and decisions, makes testable predictions, updates its own operating model after feedback, and can be restored after process/context loss. A useful result may be positive, negative or mixed. The experiment must neither assume nor purport to establish consciousness, a soul, feelings, moral status, or a subjective self. Anthropomorphic labels (e.g. dream, curiosity, identity) are shorthand for observable and operational mechanisms.

The core question is not whether retrieval improves factual answers alone, but whether experience changes future choices in a reliable, auditable and generalizable way without updating model weights.

## 2. Proposed architecture

```text
Human / synthetic environment / sandboxed tools
                 |       ^
                 v       |
        Interaction / Orchestrator
                 |       ^
                 v       |
           Cognitive Core (LLM)
           /      |       \
          v       v        v
    Self-Model   Memory   World Model
          \       |        /
           \      v       /
          Drive / Policy (bounded)
                 |       ^
                 v       |
       Actions + predictions + observations
                 |
                 v
        Feedback / Reflection Engine
                 |
                 v
     Proposed state and memory revisions
                 |
                 v
      Validation / Commit / Event Journal
                 |
                 +----> next cognitive cycle
```

Every state transition is traceable to an event. Reflection must not silently rewrite prior history.

### Cognitive Core

Swappable text-capable LLM inference adapter. Start with a compact model that runs comfortably within the available hardware (reference machine has 8 GB VRAM); record runtime, quantization, context window, sampling, prompt templates, token counts and latency. Muse Glimmer is a candidate for a later feasibility-gated variant, not a compulsory starting point. Colibri/Mamba may provide architecture alternatives only after task/interface equivalence is established.

### Memory System

Separate working memory, episodic event history, semantic summaries and autobiographical consolidation. MVP: append-only SQLite event journal and basic retrieval/summarization. Candidate TencentDB Agent Memory adapter should use an identical external contract and be evaluated independently against no-memory, fixed-summary and basic retrieval baselines. Track provenance, timestamp, revisions, contradictions, stale recall, deletion behavior, latency, storage and token overhead. Maintain immutable source events; corrections supersede earlier claims rather than deleting their provenance.

### Self-Model

Structured, versioned operational description: `agentId`, `revision`, measured capabilities and uncertainty, active goals, known failure patterns, applicable constraints, and consolidation metadata. A suggested schema (numbers are illustrative, not benchmark findings):

```json
{
  "agentId": "continuity-001",
  "revision": 42,
  "capabilities": {"codeReasoning": 0.81, "visualRecognition": 0.64},
  "goals": ["improve task completion", "reduce repeated mistakes"],
  "uncertainties": ["poor estimation of complex task duration"],
  "lastConsolidation": "2026-10-01T18:00:00Z"
}
```

The agent proposes revisions; deterministic validation decides which changes are committed. Scores must be tied to documented metrics, not self-declared competence. Separate configurable goals from mutable learned estimates.

### World Model

Store explicit, falsifiable predictions before tool execution (expected outcome, confidence where suitable, assumptions and deadline). Compare actual outcomes to predictions. Track calibration/error and whether subsequent strategy updates reduce repeated mistakes.

### Drive / Policy

Initially deterministic and budgeted. Candidate signals: information gain / curiosity, uncertainty, prediction error, goal progress and unproductive repetition. Distinguish signals from simulated emotional experience. Choose among explicit bounded actions (continue, retrieve, inspect, try alternative, ask, stop). Jev/System One is a later adapter to compare decision latency, action quality, option-order robustness and calibration under the *same* candidate action space. Do not equate API confidence with calibrated correctness.

### Reflection and Consolidation (informal nickname: 'sleep')

A scheduled or manually triggered bounded pass reviews episodes, failures, forecast errors and contradictory claims; proposes semantic summaries and self-model revisions with evidence references; passes them through validation; emits immutable records. Compare the task LLM with a separate reflector later. Never permit reflection to modify policies, permissions, tools or immutable events on its own.

### Orchestrator, observability and execution safety

Event-driven state machine with run ID, trace ID, versioned prompt/policy/model fingerprints, tool I/O references, stop conditions, budget counters, deterministic seed when available, and checkpoints. Local sandbox, explicit tool allowlist, human approval for external effects, immediate kill switch, maximum cycles/time/tokens/cost, no unrestricted network or autonomous self-replication. Integrate existing `shared/tooling/agent-resource-coordination` when multiple agents share the GPU. Use Python initially for inference adapters; contracts should remain language-neutral so a C# orchestrator can be tried.

## 3. Experimental program

### CONT-000: foundation

Create synthetic multi-session tasks with verifiable facts, contradictions, tool failures, predictions, repeated task families and delayed recall; define dataset splits and leakage checks. Implement minimal event store, replay, metrics, reproducible configs and a compact local core. Do a single-session smoke test before longitudinal trials.

### CONT-001: Does Continuity Matter?

Run ablations using the *same* base model and identical tasks:

| Arm | Configuration |
| --- | --- |
| A | LLM, no persistent memory |
| B | A + persistent memory |
| C | B + validated self-model |
| D | C + reflection/consolidation |
| E | D + bounded drive/policy and world model |

Pre-register acceptance conditions and compare across repeated seeded runs. Control inference budget, tool availability, context size, initial knowledge, prompt length and exposure; where one arm requires extra tokens/cycles include budget-matched controls. Rotate scenarios to reduce order effects. Evaluate task completion, retrieval correctness/false recall, stale contradiction rate, repetition of known mistakes, adaptation to feedback, prediction calibration, restart robustness, tool calls, latency, compute/tokens and storage growth. Report uncertainty and failures, not just best runs. An improvement in arm E cannot automatically be attributed to a single component without further ablations.

### CONT-002: Identity Persistence

After ~100 controlled synthetic sessions, pause the agent and clear volatile process/context state. Compare:

1. Same model restored with its prior persistent state.
2. Same model started with a clean persistent state.
3. Compatible different model restored with the previous state.

Use unseen held-out tasks, repeat with several seeds and model pairs, and test sensitivity to irrelevant changes in surface wording. Measure continuity of **observable learned behavior** (recall, policies, corrected mistakes, goal persistence), not metaphysical personal identity. Control transfer effects caused by different models' intrinsic capabilities, prompting and context handling.

### CONT-003: Reactive versus continuous (candidate)

Compare wake-on-input agent, agent with bounded reflection while no user input arrives, and a compute-matched control with randomly selected permissible reflection operations. Strictly log every autonomous step and enforce cycle/budget caps. Investigate whether autonomous consolidation adds value beyond spending additional tokens.

### CONT-004: Memory backend (candidate)

On identical synthetic episodes, compare SQLite baseline with pinned TencentDB Agent Memory release. Include delayed recall, distractors, correction/conflict, storage growth, false recall, latency and cross-model portability. Reuse and cross-reference the existing TencentDB lab's TAM-001 through TAM-008, avoiding duplicate vendor-specific setup.

## 4. Interfaces to define before implementation

- `IInferenceProvider`: generate with exact context and telemetry.
- `IMemoryProvider`: append episode, retrieve with provenance, consolidate, supersede/revise, export/import.
- `ISelfModelStore`: get revision, propose update, validate, commit with audit trail.
- `IWorldModel`: record ex-ante prediction and attach observed outcome.
- `IPolicy`: select from bounded actions based on explicit state signals.
- `IReflectionEngine`: produce evidence-backed proposals, not direct mutations.
- `IEnvironment`: synthetic fixtures and allowlisted observable actions.
- `IExperimentRunner`: pin config, replay, reset, ablate, score and export.

Contract names are illustrative rather than an instruction to create interfaces before an MVP demonstrates a need.

## 5. Staged implementation backlog (suggested, not approved)

P0: CONT-000 synthetic fixtures, event schema, deterministic environment, no-memory baseline, minimal adapter, telemetry, basic replay and stop/budget controls.  
P1: SQLite memory and arm B; measured self-model and arm C; reflection proposals and arm D; explicit world predictions/policy and arm E.  
P1: Execute CONT-001 repeatedly with held-out tests, data and analysis.  
P2: CONT-002 reset/restore/state export and alternative-core adaptation.  
P2: Pinned TencentDB integration and direct comparison (CONT-004); candidate Jev policy adapter.  
P3: Reactive/continuous trial with budget-matched random-reflection control (CONT-003); CLI-Anything sandbox, optional Muse Glimmer and other inference providers; TimesFM only with a demonstrated forecasting need.

Avoid creating empty directories or premature shared abstractions. Keep lab-local components until genuine cross-lab reuse appears.

## 6. Repository and publication policy

Proposed location:

```text
labs/continuity/
  README.md
  docs/
    research-proposal.md
    evaluation-plan.md          # when trials are designed
  src/                        # created only as needed
  experiments/CONT-000/       # created only as needed
  experiments/CONT-001/
  experiments/CONT-002/
  results/
```

The existing root `docs/architecture.md` is authoritative for experiment contracts, evidence and status. Cross-lab inputs are references, not vendored code. Keep the public repository free of real personal conversation exports, identifiers, confidential employment or project data, API credentials and private model artifacts. Use synthetic data and publish only sanitized evidence. Pin upstream licenses and versions. All code comments should be in English.

## 7. What would count as an informative outcome?

Evidence that persistent state lowers repeated errors, improves delayed adaptation or survives model substitution would justify further investigation of architectural behavioral continuity. Null or adverse results (false recall, reflection drift, unwarranted self-confidence, instability) are equally valuable. Neither positive nor negative outcomes settle whether AI systems have subjective experience.

This proposal should be revisited as the lab's baseline evidence accumulates.
