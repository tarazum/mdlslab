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

Create synthetic multi-session tasks with verifiable facts, contradictions, tool failures, predictions, repeated task families and delayed recall; define dataset splits and leakage checks. Define the fixture suite as a **lab-agnostic workload protocol** with versioned scenario fixtures, expected observations/labels, metric definitions, a runner contract, and a reproducible configuration manifest. A consumer receives fixtures and emits a normalized trace and result regardless of whether it is Continuity, TencentDB Agent Memory (TAM-002–TAM-007), or a private OCL implementation. Do not couple fixture semantics to Continuity's internal self-model or memory APIs. Keep this package inside `labs/continuity/` until a second real consumer demonstrates reuse; only then consider extraction to `shared/` under the root repository policy. Public fixtures and traces must be synthetic and safe to publish.

Implement minimal event store, replay, metrics, reproducible configs and a compact local core. Do a single-session smoke test and **early variance/headroom pilot** before building arms B–E: run arm A with pinned decoding settings over a predeclared seed set, estimate spread of candidate endpoints, and inspect failure rates across scenario families. If A is at ceiling or results are dominated by noise, adjust fixtures or sample size using pilot data *before freezing the confirmatory suite*. Reserve held-out scenarios that are not used for calibration. Greedy decoding alone does not guarantee bit-identical outputs across batch sizes or inference backends.

**Primary endpoint for CONT-000 (feasibility):** proportion of predeclared pilot runs that complete and produce a replayable, schema-valid trace under the configured budget. Variance, headroom, latency, tokens, and calibration of scenario difficulty are secondary diagnostic outputs. Pin the exact pass criterion in the run plan before executing this pilot.

### CONT-001: Does Continuity Matter?

Run ablations using the *same* base model and identical tasks:

| Arm | Configuration |
| --- | --- |
| A | LLM, no persistent memory |
| B | A + persistent memory |
| C | B + validated self-model |
| D | C + reflection/consolidation |
| E | D + bounded drive/policy and world model |

**Primary endpoint (to pre-register before confirmatory runs): repeated-mistake rate** on task families previously encountered during the learning sessions. Define a mistake as a repeated occurrence of an independently labelled error category on a subsequent eligible task; denominator is the number of eligible subsequent tasks, scored by a fixed evaluator blind to arm identity where practical. Specify the primary contrast and minimum meaningful improvement between arms A–E in the pre-registration, rather than selecting a favorable pair after observing outcomes.

**Secondary/exploratory outcomes:** task completion, retrieval correctness/false recall, stale contradiction rate, feedback adaptation, prediction calibration, restart robustness, tool calls, latency, compute/tokens and storage growth. Do not promote secondary metrics into retrospective primary success claims.

Compare repeated seeded runs using the variance/headroom pilot from CONT-000 to choose seed count and session count. Control inference budget, tool availability, context size, initial knowledge, prompt length and exposure; where one arm requires extra tokens/cycles include budget-matched controls. Rotate scenarios to reduce order effects. Report effect sizes and uncertainty, including failures and null results, not just best runs. An improvement in arm E cannot automatically be attributed to a single component without further ablations.

### CONT-002: Identity Persistence

After a pilot-justified number of controlled synthetic learning sessions (the earlier "~100" is a sizing hypothesis, not a fixed requirement), pause the agent and clear volatile process/context state. Evaluate the **full 2×2 factorial design**, with the same held-out tasks and the same predeclared number of matched seeds in all four cells:

| Cognitive core | Restored learning state | Clean state |
| --- | --- | --- |
| Core A (training core) | A + restored | A + clean |
| Core B (compatible replacement) | B + restored | B + clean |

State export/import must have a documented compatibility contract. Clean controls must preserve identical fixed instructions, initial permissions, tools and test budget; they differ only in the learned persistent state. Match evaluation prompts and context budgets as closely as the model adapters allow.

Let `S(X, state)` be a predeclared, independently scored held-out behavioral performance measure (higher is better). Define `ΔA = S(A, restored) − S(A, clean)` and `ΔB = S(B, restored) − S(B, clean)`. **Primary endpoint: retained-benefit ratio `R = ΔB / ΔA`**, estimating the share of measured learned-state benefit that survives core replacement. Pre-register aggregation, minimum meaningful `ΔA`, target ratio/uncertainty criterion and treatment of negative values. If `ΔA` is zero or too close to zero to support a stable ratio, label the primary endpoint non-estimable and report the two deltas with uncertainty as diagnostics; do not cherry-pick another denominator or claim successful transfer.

**Secondary/exploratory outcomes:** recall, retention of corrected mistakes, policy/goal persistence, sensitivity to superficial wording, state import failures, run cost and latency. Use unseen held-out tasks, repeated matched seeds and (where feasible) more than one compatible model pair. This measures continuity of **observable learned behavior**, not metaphysical personal identity. The clean-state B cell is essential to distinguish transfer from B's intrinsic capability differences.

### CONT-003: Reactive versus continuous (candidate)

Compare wake-on-input agent, agent with bounded reflection while no user input arrives, and a compute-matched control with randomly selected permissible reflection operations. Strictly log every autonomous step and enforce cycle/budget caps. Investigate whether autonomous consolidation adds value beyond spending additional tokens. **Candidate primary endpoint:** repeated-mistake rate on held-out recurring task families after the idle period; finalize one endpoint and its primary contrast before this experiment is commissioned. Secondary diagnostics include compute, changes proposed/accepted, and trace quality.

### CONT-004: Memory backend (candidate)

Run the CONT-000 lab-agnostic fixture protocol against both the SQLite baseline and a pinned TencentDB Agent Memory release using compatible runner adapters, identical synthetic episodes, and the same evaluation rules. Reference TAM-001–TAM-008 for upstream setup and underlying memory-specific experiments; do not build a competing TAM harness. **Candidate primary endpoint:** correct delayed-recall rate on a pre-registered held-out question set, with the primary backend contrast specified in advance. Distractors, correction/conflict, storage growth, false recall, latency and cross-model portability are secondary/exploratory measures. The same protocol should be usable by an OCL implementation in a separate private environment; never publish corporate implementation details or real work data.

### CONT-005: Memory Trust Hierarchy (proposed next research cycle; owner-gated)

**Motivation (observations, not proof):** CN-007 records own-answer anchoring: an early incorrect agent answer is stored and later re-injected as if it were useful evidence. CN-008 records a different failure: retrieval surfaces a newer correction, yet the model answers with an older superseded value. CN-009 cautions that a self-model primed with the exact evaluated failure can improve a familiar fixture without showing generalizable learning. See `docs/FINDINGS.md` and the exploratory arm A/B/C results. These failures motivate a focused follow-up **after** the current M4–M7/CONT-001 arc; do not alter its running fixtures, memory injection, evaluation rules or pre-registration.

**Research hypothesis:** tracking provenance, verification status and supersession as first-class memory relations, and resolving conflicts at retrieval/assembly time, can reduce repeated mistakes and stale-fact answers compared with flat episode retrieval under equivalent information and compute budgets. A counter-hypothesis is that rigid source ranking will suppress valid user corrections, propagate falsely authoritative environmental inputs or introduce extra latency and overconfidence.

**Operational design proposal:** preserve an append-only event history and represent derived claims separately from source events. A claim records `claimId`, normalized proposition / subject and predicate, value, `sourceEventIds`, `sourceType` (environment observation, external verified reference, explicit user correction, tool result, agent-generated answer, reflection-derived hypothesis), `verificationStatus` (unverified / independently verified / contradicted / superseded), `observedAt`, `effectiveAt` if applicable, `supersedesClaimIds`, validation evidence and policy/version. Any trust score is a *policy-derived signal*, not a statement that a source is universally true; recency alone must not overrule provenance or explicit evidence. Never silently delete conflicting events or grant the agent's earlier answer the authority of the underlying environment. Reflection may propose claim links and status changes but must cite evidence; deterministic validation commits them. Missing/ambiguous evidence should remain visible as uncertainty, including the option to abstain or ask.

**Candidate controlled arms** (same LLM, fixtures, context/tool/token budget where feasible):

| Arm | Retrieval/assembly behavior |
| --- | --- |
| T0 | Current flat episodic memory (frozen baseline) |
| T1 | Flat memory with visible source-type and timestamp annotations only |
| T2 | T1 plus deterministic supersession graph and conflict-aware resolution |
| T3 | T2 plus validated, versioned trust policy and evidence-backed reflection proposals |

Ablate components rather than comparing only T0 vs T3: distinguish extra metadata/prompt hints from actual supersession logic. Provide budget-matched T0 controls when trust annotations consume additional context. Keep independently scored, unseen scenario templates apart from the pilot and any self-model training data; fix source policy before confirmatory runs. Include deliberately unreliable environmental statements, erroneous user corrections and later retractions to avoid simply hard-coding an absolute source ranking. Reuse CONT-000's lab-agnostic fixture/runner contract and cross-reference TAM-002–TAM-007 rather than building a separate benchmark.

**Candidate primary endpoint (freeze before confirmatory evaluation):** repeated-mistake rate on held-out correction-and-reuse task families, measured as independently adjudicated repeated errors per eligible subsequent task. Pre-register one primary contrast (suggested T2 vs T0), direction, minimum meaningful effect, sample sizing and uncertainty method. **Secondary/exploratory:** superseded-fact usage rate; correct correction acceptance; false override of valid older facts; provenance citation accuracy; retrieval vs answer-stage conflict failures; abstention calibration; memory pollution/anchoring; token cost, latency, storage growth and restart persistence. Record retrieval-ranked episodes separately from the final answer so a retrieval success cannot conceal a conflict-resolution failure.

**Entry and exit gates:** wait for the current CONT-001 arc and its owner review; freeze or version its dataset/results first. Begin CONT-005 with a new fixture version and a pilot sufficient to establish headroom/variance. The exit artifact is a reproducible, independent comparison with raw traces, error taxonomy, and an explicit go/no-go recommendation *for the architecture experiment*, not a claim about consciousness. This is a proposed backlog item, **not authorized work within the current autonomous ROADMAP deadline**.

## 4. Interfaces to define before implementation

- `IInferenceProvider`: generate with exact context and telemetry.
- `IMemoryProvider`: append episode, retrieve with provenance, consolidate, supersede/revise, export/import.
- `ISelfModelStore`: get revision, propose update, validate, commit with audit trail.
- `IWorldModel`: record ex-ante prediction and attach observed outcome.
- `IPolicy`: select from bounded actions based on explicit state signals.
- `IReflectionEngine`: produce evidence-backed proposals, not direct mutations.
- `IEnvironment`: synthetic fixtures and allowlisted observable actions.
- `IExperimentRunner`: pin config, replay, reset, ablate, score and export.
- `IWorkloadAdapter` (conceptual): accept versioned synthetic fixtures and publish standardized event traces, ground-truth labels, and metric inputs independent of the consuming lab. Keep its initial implementation lab-local.

Contract names are illustrative rather than an instruction to create interfaces before an MVP demonstrates a need.

## 5. Staged implementation backlog (suggested, not approved)

P0a: CONT-000 lab-agnostic synthetic fixture protocol, metric definitions and runner contract (kept lab-local), event schema, deterministic environment, no-memory baseline, minimal adapter, telemetry, basic replay and stop/budget controls.  
P0b: Early variance/headroom pilot with arm A; size confirmatory trials and document compute budget before implementing further arms. Pre-register a single primary endpoint per experiment and thresholds before confirmatory evaluation.  
P1a: SQLite memory and arm B; measured self-model and arm C; reflection proposals and arm D; explicit world predictions/policy and arm E.  
P1b: Execute CONT-001 repeatedly with held-out tests, data and analysis.  
P2a: CONT-002 complete 2×2 reset/restore/state export and alternative-core adaptation.  
P2b: Pinned TencentDB integration and direct comparison (CONT-004); candidate Jev policy adapter. TAM-001 and JEV-001 can proceed independently in parallel rather than blocking on Continuity.  
P3: Reactive/continuous trial with budget-matched random-reflection control (CONT-003); CLI-Anything sandbox, optional Muse Glimmer and other inference providers; TimesFM only with a demonstrated forecasting need.

**Compute feasibility note:** 100 sessions × ~3 turns × ~2–3k tokens is about 0.6–0.9M tokens per arm/seed; across five arms and three seeds, roughly 9–13.5M tokens before extra controls/retries. This is illustrative arithmetic, not a measured runtime estimate. Choose session count from P0b pilot variance and the practical inference throughput; log expected cost and schedule bounded batches. Acquire `shared/tooling/agent-resource-coordination` locks for contended GPU runs.

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

The existing root `docs/architecture.md` is authoritative for experiment contracts, evidence and status. Cross-lab inputs are references, not vendored code. The CONT-000 fixture protocol is intentionally consumer-neutral but remains in Continuity until another actual consumer demonstrates the need to move it into `shared/`. Keep the public repository free of real personal conversation exports, identifiers, confidential employment or project data, API credentials and private model artifacts. Use synthetic data and publish only sanitized evidence. Pin upstream licenses and versions. All code comments should be in English.

## 7. What would count as an informative outcome?

Evidence that persistent state lowers repeated errors, improves delayed adaptation or survives model substitution would justify further investigation of architectural behavioral continuity. Null or adverse results (false recall, reflection drift, unwarranted self-confidence, instability) are equally valuable. Neither positive nor negative outcomes settle whether AI systems have subjective experience.

This proposal should be revisited as the lab's baseline evidence accumulates.
