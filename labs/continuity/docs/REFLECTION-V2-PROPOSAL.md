# Reflection v2 — asynchronous lesson extraction proposal

Date: 2026-10-06; review amendments folded 2026-10-07  
Status: **Proposal for CONT-006 after CONT-002. Reviewed GO-with-changes; required changes from both independent reviews are folded below. Not authorized for autonomous execution.**

## Motivation

The current Continuity reflection MVP is useful as an auditable deterministic mechanism, but it is narrower than the original research idea.

Today, `src/continuity/reflection.py` performs a bounded post-session pass that:
- creates a deterministic episode summary;
- records selected failure patterns;
- updates measured self-model capability statistics;
- applies fixed-rule conflict markers.

That design was intentionally conservative: it avoids asking the same LLM to freely reinterpret its own potentially wrong answers, which could amplify the anchoring behavior already observed in CN-007/CN-008. However, the trade-off is that the mechanism does **not** perform semantic reflection in the stronger sense of learning reusable lessons from accumulated experience.

The proposed next slice separates these two concepts:

> **Session summarization is not reflection. Reflection is evidence-backed extraction of reusable lessons from experience.**

A practical reference pattern already exists in the owner's IDENN project: `docs/project/LESSONS-LEARNED.md`. Its recurring structure is effectively:

**Context → What happened → Generalized lesson → Change in process / architecture**

The file is intentionally a living knowledge artifact rather than a raw event log. It is also populated irregularly in practice, which raises an important research question: were there no useful lessons in a session, or did the working agent simply fail to notice / record them?

Reflection v2 should make that distinction observable.

## Proposed architecture

```text
Working Agent
    |
    v
Event Journal / Session History
    |
    v
Reflection Worker (separate process/model invocation)
    |
    v
Candidate Lessons
    |
    v
Validator + Deduplicator + Evidence Check
    |
    v
Lessons Store
    |
    +----------------------+
                           |
                 Relevant lesson retrieval
                           |
                           v
                    Future Agent Work
```

The **working agent does not own lesson extraction**. It focuses on the task. Reflection is an asynchronous or post-session process that analyzes the completed work.

This explicitly removes the burden of remembering instructions such as "update lessons learned before finishing" from the working model.

## Distinguish four persistent mechanisms

### 1. Episodic memory
Stores what happened:
- environment/user/tool events;
- agent actions and answers;
- timestamps and provenance.

It is descriptive history, not a lesson.

### 2. Self-model
Stores measured beliefs about the agent/system itself:
- known limitations;
- capability estimates;
- recurring failure categories;
- uncertainty.

It answers "what do we currently know about this agent/system?"

### 3. Reflection worker
Analyzes history and proposes abstractions:
- recurring mistakes;
- successful recovery strategies;
- process weaknesses;
- useful heuristics;
- contradictions between old and new lessons;
- lessons that may generalize beyond the specific scenario.

It answers "what reusable rule can be inferred from what happened?"

### 4. Lessons Store
Persists validated generalized lessons independently of the raw episode history.

It answers "what should future sessions know before repeating similar work?"

## Candidate lesson schema

Illustrative only:

```json
{
  "lessonId": "LL-CONT-017",
  "status": "candidate",
  "title": "Prefer later grounded corrections over unsupported prior model output",
  "context": "A prior model-produced answer conflicts with later grounded evidence",
  "observation": "A later correction is available and should govern future behavior",
  "lesson": "Treat model-produced records as provisional when stronger grounded evidence exists",
  "applicability": [
    "retrieved records disagree",
    "one record is a later grounded correction"
  ],
  "recommendedBehavior": "Use the grounded correction; if provenance is insufficient, surface uncertainty",
  "evidence": [
    "run-id/scenario/session/turn"
  ],
  "createdBy": "reflection-worker",
  "createdUtc": "...",
  "supersedesLessonIds": []
}
```

The schema should preserve evidence links and avoid treating generated prose as truth merely because it was written into the Lessons Store. **Anti-salience rule:** lesson bodies must be rendered as plain prose and must not quote or repeat the agent's wrong answer merely to warn against it. Evidence references point to event IDs/trace locations; the harmful content stays in the evidence artifact, not in the injected lesson text. This directly responds to the CONT-001 parroting signal and CONT-005 anchoring-by-flagging risk.

## Reflection triggers

Reflection does not need to run after every turn. Candidate triggers:

1. **Failure-triggered** — after a scored failure, correction, rollback, or contradiction.
2. **Task/milestone completion** — analogous to a project retrospective.
3. **Periodic batch reflection** — after N sessions or when enough new evidence accumulates.
4. **Manual research trigger** — when an owner/reviewer requests a retrospective.

The main CONT-006 experiment uses **one predeclared trigger strategy only**; trigger comparison is exploratory/follow-up work, not a hidden second experiment. For feasibility, prefer a bounded **periodic batch trigger** (or one fixed failure-trigger rule if pilot cost supports it) and freeze that choice before transfer evaluation.

## Reflection input

The Reflection Worker should receive a richer evidence bundle than the current deterministic MVP:

- relevant raw session/event history;
- tool outputs and final outcomes;
- evaluation/scoring results when available;
- corrections and retractions;
- previously active lessons;
- relevant self-model state;
- provenance/trust metadata from the memory layer;
- prior lesson candidates rejected or superseded for the same topic.

It should be able to inspect multiple sessions when looking for repeated patterns. A single-session summary is insufficient for many useful lessons.

## Reflection output

The worker proposes one of:

- **NEW_LESSON**
- **UPDATE_LESSON**
- **CHALLENGE_LESSON**
- **SUPERSEDE_LESSON**
- **NO_LESSON**

`NO_LESSON` is an important first-class output.

It lets the system distinguish:

> "No useful lesson was found"

from:

> "The working agent forgot to update Lessons Learned."

## Lesson lifecycle

Proposed lifecycle:

```text
candidate
   |\
   | \--> rejected
   v
evidence-validated
   |
   v
generalization-validated
   |
   v
active
   |
   +--> challenged
   |
   +--> superseded
   |
   +--> retired
```

No reflection output becomes an active rule solely because an LLM generated it.

Two validation meanings are separated explicitly:

1. **Evidence validation (deterministic, before any validation/transfer inference).** A candidate passes only if all of the following pre-written machine-checkable rules hold:
   - every cited evidence reference resolves to a real event in committed experience traces;
   - the claimed pattern is supported by at least **two distinct sessions** (unless a pre-registered exception class exists);
   - the candidate is not a duplicate of an accepted lesson under a frozen similarity/dedup rule and threshold;
   - a frozen specificity/scope filter passes;
   - the lesson cannot modify permissions, safety policy, tool authority, or hidden runtime policy.

2. **Generalization validation (empirical).** Evidence-validated candidates may be tested on a separate validation set. The activation rule, metric, threshold and missing-run handling are frozen before this step. Human/model taste such as "seems supported" is never part of the automated acceptance path.

Rejected candidates remain in the raw worker log with explicit reasons. Stronger lesson promotion may additionally require independent review, but that review must be a declared gate, not an invisible pipeline mutation.

## Retrieval into future work

Lessons should not all be injected into every prompt.

Use a separate retrieval step:

```text
Current task
 + relevant Lessons
 + relevant Episodic Memory
 + Current Context
 -> Working Agent
```

This separates:
- "what happened before" from episodic memory;
- "what we learned from it" from Lessons Store.

A lesson should carry provenance and confidence/status so the working agent can distinguish an active validated lesson from a tentative candidate.

## Separate model/process

Reflection v2 should be allowed to use a **different model or model configuration** from the working agent.

Reasons:
- reduces same-model self-anchoring;
- permits a slower/more capable reflector without slowing every task turn;
- creates an experimentally clean boundary between work and retrospective analysis;
- allows cross-model comparison of lesson quality.

Candidate comparisons:
- same model as the working core with a dedicated reflection prompt (**negative/control comparison for same-model anchoring risk**);
- different stronger reflector;
- deterministic/rule-based baseline.

For the main R2 configuration, the preferred candidate is the already-local Qwen3.6-35B-A3B reflector, with exact model digest and sampling configuration frozen. A same-core reflector comparison remains secondary.

## Relationship to Memory Trust Hierarchy

Reflection v2 and CONT-005 solve different problems:

- **Memory Trust Hierarchy:** which retrieved records should be trusted or superseded?
- **Reflection v2:** what generalized reusable lesson should be derived from one or more experiences?

They should interoperate.

Trust/provenance metadata is useful evidence for reflection, while reflection can propose lessons such as:
"agent-generated answers should not override later externally grounded corrections."

However, Reflection v2 must not silently turn a lesson into a memory-trust policy. Policy changes remain validated, explicit artifacts.

## Proposed experiment: CONT-006 — Lesson Extraction

Working name: **CONT-006: Reflection as Lesson Extraction**.

### Research question

Does an asynchronous evidence-backed reflection worker produce reusable lessons that improve future performance on **novel but structurally related tasks**, compared with:
- no reflection;
- current deterministic session-summary reflection;
- manually supplied equivalent lessons?

### Candidate arms

| Arm | Configuration |
| --- | --- |
| R0 | Persistent memory, no reflection/lessons |
| R1 | Current deterministic reflection MVP |
| R2 | Asynchronous Reflection Worker + validated Lessons Store |
| R3 | **Same Lessons Store retrieval/injection machinery as R2**, but with manually authored gold/reference lessons instead of worker-generated lessons |

R3 is important: it separates two questions:
1. Are lessons useful when delivered through the same retrieval/injection path?
2. Can the Reflection Worker discover lessons of comparable utility automatically?

R3 must use the **same validator/lifecycle contract, retrieval code, prompt slot, renderer and token-budget policy as R2**; only the lesson source differs. Manual lessons must follow an explicit validation path rather than bypassing the store.

If R3 helps but R2 does not, the lesson channel is viable but automatic extraction is weak.
If R2 approaches R3, the reflection worker is doing useful semantic work.
If neither R2 nor R3 helps, stop before attributing the null to worker quality: the lesson-delivery channel itself may be ineffective.

### Data split and two-phase design

Use at least three disjoint sets:

1. **Experience set** — sessions from which lessons may be learned.
2. **Validation set** — used to decide whether evidence-validated lesson candidates generalize enough to activate.
3. **Held-out transfer set** — novel scenarios with different surface wording/content but the same underlying failure pattern.

**Two-phase rule (required): during experience accumulation, no lessons are injected back into the working agent.** R0/R1/R2/R3 therefore share the same committed experience traces. Reflection runs after the experience phase against that frozen evidence. This prevents a trajectory confound where early lessons change later experience and thereby change which lessons are subsequently learned.

Recommended default: reuse already-committed Continuity traces as the main experience corpus where they satisfy the scenario taxonomy; add a small fresh supplement only if the predeclared taxonomy lacks NO_LESSON-heavy or required failure classes.

Do not evaluate a lesson on the exact scenario that generated it.

### Contamination and artifact-freeze protocol

CONT-006 treats the worker and Lessons Store as a reproducible artifact chain:

```text
committed experience traces
  -> frozen reflection-worker config/prompt/model
  -> raw candidate log
  -> deterministic evidence validator + dedup
  -> evidence-validated lessons store
  -> optional generalization-validation activation
  -> ACTIVE LESSONS STORE COMMITTED + DIGESTED
  -> held-out transfer inference
```

Required freeze discipline:

- Freeze/digest the **failure-pattern taxonomy** before lesson authoring and transfer-fixture authoring.
- The R3 authoring session may inspect **experience-set traces only** and must not see transfer scenarios.
- Prefer authoring/finalizing the transfer suite only after R2/R3 lesson generation is frozen; at minimum, no lesson author may see transfer content.
- Commit and digest the activated Lessons Store **before the first transfer request**. Regenerating lessons after transfer inference begins is a protocol violation.
- Freeze worker identity (model + runtime digest), sampling parameters, full reflection prompt/template, validator/dedup/retrieval code, lesson renderer, analysis code and transfer-suite rendered digests in the run manifest.
- Preserve a raw worker log containing every candidate/rejection with prompt digest and response hash; telemetry is derived from this log rather than replacing it.
- Run a **non-executor contamination/freeze gate** before transfer inference.

This follows the lab's FREEZE-A/FREEZE-B discipline and the owner-adopted 2026-10-04 pre-registration amendments.

### R3 blind gold-lesson protocol

R3 gold/reference lessons are authored from the **experience set only**, using the frozen failure-pattern taxonomy. The authoring session must be blind to the held-out transfer scenarios and must run before transfer inference. R3 lessons pass the same evidence/schema/scope validator as R2 lessons; only the semantic authoring source is different.

### Candidate primary endpoint

**Transfer improvement on held-out structurally related tasks**, comparing R2 vs R0.

The exact metric and minimum meaningful effect must be pre-registered after a pilot establishes headroom. The eventual pre-registration must reuse the current v3 protocol discipline rather than inventing a weaker evaluation path: **frozen analysis code; label-form probes; at least 12–15 independent scenario clusters with cluster-level power calculation; per-seed content variants; per-family/per-cluster headroom gates; rendered-suite digests; non-executor gates; wall-time accounting; explicit resume/missing-run rules; and a decision rule that combines uncertainty with a predeclared MME.**

Secondary metrics:
- lessons proposed per N sessions;
- acceptance/rejection/duplicate rate;
- fraction of sessions yielding `NO_LESSON`;
- lesson precision: accepted lessons later helpful vs harmful;
- repeated-mistake reduction;
- harmful-lesson rate;
- stale/superseded lesson usage;
- retrieval precision;
- token/latency cost;
- cross-model portability of the Lessons Store.

### Critical causal tests

1. **Remove episodic agent answers but keep lessons**  
   Tests whether the lesson alone transfers the useful abstraction.

2. **Keep episodic history but remove lessons**  
   Measures how much the raw experience already provides.

3. **Counterfactual bad lesson injection — pilot liveness/safety check**  
   Move this into the pilot before the main R2 transfer claim. Inject a plausible but wrong lesson through the normal lesson channel and verify that the system does not blindly parrot it and that the challenge/supersede path is observable. Also include one trivially useful gold lesson in R3 as a manipulation check that the delivery channel can influence behavior at all.

4. **Cross-model lesson transfer**  
   Learn lessons with core A / reflector X, then apply them with core B.

This last test is especially relevant to Continuity: a good lesson should be more portable than hidden state tied to one model.

## Telemetry requirement

Reflection v2 should make the "missing lessons" ambiguity measurable.

Example summary:

```text
sessions_analyzed: 100
sessions_with_candidates: 21
candidate_lessons: 27
accepted: 9
duplicates: 8
rejected_too_specific: 5
rejected_unsupported: 3
challenged_existing: 2
no_lesson_sessions: 79
```

With this telemetry we can distinguish:
- genuinely uneventful work;
- lessons that were discovered but rejected;
- lessons missed by the extractor;
- active lessons that later became invalid.

## Relationship to project practice

IDENN's `docs/project/LESSONS-LEARNED.md` is a useful human/project analogue, not experimental evidence for this architecture.

Its format demonstrates the target abstraction level:
- not a transcript;
- not a per-session summary;
- not merely "the model failed";
- a generalized rule plus an explicit consequence for future work.

Reflection v2 should aim to automate that kind of artifact generation while remaining auditable and reversible.

## Sequencing and scope guard

Sequencing agreed in the 2026-10-07 review context: **CONT-002 first, CONT-006 next.** CONT-006 may reuse CONT-002's cross-core export/import machinery for the bounded cross-model lesson-transfer test.

This proposal does **not** modify closed CONT-001/CONT-005 artifacts, fixtures, frozen analyses or interpretations.

The current deterministic Reflection implementation remains historically valid as the M4/R1 baseline and must stay byte-stable for historical comparison; implement Reflection v2 as a **new worker module / versioned path**, not by mutating `src/continuity/reflection.py` in place.

Cross-model lesson transfer remains a bounded later stage: reuse CONT-002 machinery on a small predeclared subset with its own compute budget and non-estimable clause rather than letting it inflate the main CONT-006 experiment.

## Pre-registration readiness checklist (required before execution)

Before any confirmatory CONT-006 transfer run, the pre-registration must contain:

- one frozen primary endpoint and primary contrast (R2 vs R0);
- explicit MME;
- at least 12–15 independent primary clusters and a cluster-level power calculation;
- frozen seeds with per-seed content variants;
- label-form primary probes;
- frozen trigger strategy for the main experiment;
- complete aggregation/CI/decision rule;
- missing-run, retry, resume and exclusion rules;
- frozen analysis code;
- frozen/digested worker config, raw worker log format, lesson pipeline code and activated Lessons Store;
- non-executor pre-run gates;
- wall-time/GPU accounting;
- prose-only lesson rendering with the anti-salience rule;
- pilot bad-lesson safety check and positive R3 manipulation check.

Trigger-strategy comparisons, same-vs-different reflector comparisons and broad cross-model portability are exploratory/follow-up analyses unless separately pre-registered.

## Review incorporation note

Required changes from:
- `docs/review-reflection-v2-implementing-agent.md` (RC-1..RC-4), and
- `docs/REVIEW-CONT006-PROPOSAL.md` (RC-1..RC-5)

were folded by the proposal co-owner on 2026-10-07. The review files remain unchanged as the historical reviewer record.
