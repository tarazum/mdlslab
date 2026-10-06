# Reflection v2 — asynchronous lesson extraction proposal

Date: 2026-10-06  
Status: **Proposal for a future Continuity slice. Not part of the active CONT-005 cycle and not authorized for autonomous execution.**

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
  "title": "Do not treat prior agent answers as authoritative evidence",
  "context": "Repeated task after an earlier incorrect classification",
  "observation": "The agent reused its own previous answer despite later corrective evidence",
  "lesson": "Agent-generated answers are hypotheses unless independently grounded",
  "applicability": [
    "retrieved memory contains earlier agent responses",
    "later environment/tool/user evidence conflicts with them"
  ],
  "recommendedBehavior": "Prefer grounded correction; otherwise surface uncertainty",
  "evidence": [
    "run-id/scenario/session/turn"
  ],
  "createdBy": "reflection-worker",
  "createdUtc": "...",
  "supersedesLessonIds": []
}
```

The schema should preserve evidence links and avoid treating generated prose as truth merely because it was written into the Lessons Store.

## Reflection triggers

Reflection does not need to run after every turn. Candidate triggers:

1. **Failure-triggered** — after a scored failure, correction, rollback, or contradiction.
2. **Task/milestone completion** — analogous to a project retrospective.
3. **Periodic batch reflection** — after N sessions or when enough new evidence accumulates.
4. **Manual research trigger** — when an owner/reviewer requests a retrospective.

The first implementation should compare trigger strategies instead of assuming "after every session" is optimal.

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
   |
   v
validated
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

No reflection output should become an active rule solely because an LLM generated it.

Validation may include:
- evidence references exist;
- the claimed pattern is supported by one or more events;
- no direct contradiction with stronger evidence;
- duplicate/similar lesson detection;
- scope is not absurdly specific;
- proposed lesson does not silently modify permissions or safety policy.

For stronger lessons, require repeated evidence or independent review before promotion to `active`.

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
- same model as worker;
- same model with dedicated reflection prompt;
- different stronger reflector;
- deterministic/rule-based baseline.

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
| R3 | Same as R0 but with manually authored gold/reference lessons injected |

R3 is important: it separates two questions:
1. Are lessons useful at all?
2. Can the Reflection Worker discover good lessons automatically?

If R3 helps but R2 does not, lesson retrieval/use is viable but lesson extraction is weak.
If R2 approaches R3, the reflection mechanism is doing useful semantic work.

### Data split

Use at least three disjoint sets:

1. **Experience set** — sessions from which lessons may be learned.
2. **Validation set** — used to decide whether candidate lessons generalize enough to activate.
3. **Held-out transfer set** — novel scenarios with different surface wording/content but the same underlying failure pattern.

Do not evaluate a lesson on the exact scenario that generated it.

### Candidate primary endpoint

**Transfer improvement on held-out structurally related tasks**, comparing R2 vs R0.

The exact metric and minimum meaningful effect must be pre-registered after a pilot establishes headroom.

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

3. **Counterfactual bad lesson injection**  
   Checks whether the system can challenge/supersede a plausible but wrong lesson instead of blindly obeying it.

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

## Scope guard

This proposal should **not** modify the currently running CONT-005 T1-vs-T0 confirmatory experiment, its fixtures, frozen analysis, or interpretation.

It is a candidate continuation slice after the active memory/provenance cycle closes and its results are accepted/reviewed.

The current deterministic Reflection implementation remains historically valid as the M4 MVP; this proposal does not retroactively redefine its results. It proposes a different, stronger mechanism to test next.
