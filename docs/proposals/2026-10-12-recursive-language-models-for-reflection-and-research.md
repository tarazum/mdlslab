# Proposal: Recursive Language Models for reflection and repository research

Date: 2026-10-12  
Status: **Exploratory proposal only. Do not reprioritize or expand the current experiment queue automatically.**

## Trigger

An upcoming Research Lab session on **“Recursive Language Models in Practice: Architecture, Tradeoffs, and Evidence”** highlighted a pattern that may be relevant to mdlslab, especially the Continuity / Reflection-v2 work.

The useful interpretation of **Recursive Language Models (RLMs)** here is not “a new neural architecture” comparable to Transformer/Mamba. It is an **inference / agent-harness pattern** built around an ordinary LLM:

- keep a large evidence corpus in an external workspace instead of placing all of it into one prompt;
- let a root model inspect/search/slice that workspace;
- recursively invoke focused model calls over smaller relevant subsets;
- combine the partial analyses into a final answer or action.

Conceptually:

```text
large task / long evidence history
            |
            v
         root LLM
            |
            v
 external workspace / REPL
      /       |       \
 focused   focused   focused
 subcall   subcall   subcall
      \       |       /
        synthesis
```

This is closer to adaptive evidence navigation than to ordinary fixed top-k RAG.

Primary leads to verify/use:
- Recursive Language Models paper: https://arxiv.org/abs/2512.24601
- reference implementation: https://github.com/alexzhang13/rlm
- Recursive Agent Harness follow-on direction: https://arxiv.org/abs/2606.13643

## Why this is interesting for mdlslab

### 1. Reflection-v2 / Lessons Learned extraction

The original Reflection-v2 idea is:

> a separate process reviews completed work and extracts reusable lessons from experience.

That becomes increasingly difficult once the evidence is:
- tens or hundreds of sessions;
- tool calls;
- failures and corrections;
- reviews;
- previous lessons;
- contradictory evidence.

A single “read the entire history and extract lessons” prompt is exactly the kind of workload where an RLM-style worker may help.

Possible workflow:

```text
session/event history
        |
        v
find corrections / failures / rollbacks / retries
        |
        +--> analyze failure cluster A
        +--> analyze failure cluster B
        +--> search for counterexamples
        +--> compare with existing lessons
        |
        v
candidate generalized lesson
```

This is substantially closer to the intended Reflection mechanism than the earlier deterministic session-summary MVP.

Potential advantage: the reflector can reason over a much larger evidence base without forcing every raw event into one context window.

### 2. Deep repository / project-history research

mdlslab now contains a growing amount of:
- findings;
- experiment logs;
- preregistrations;
- reviews;
- results;
- code;
- corrections and invalidations.

Questions such as:

> “Why did this class of experimental failure recur, and what general process rule would have prevented it?”

often require evidence from multiple documents and commits.

An RLM-style researcher could recursively inspect the repository, delegate focused analyses, and synthesize an evidence-backed answer instead of relying on one-shot repository retrieval.

This may also be useful outside Continuity for long-lived projects such as IDENN.

### 3. Multi-document evidence synthesis

RLMs may be more appropriate than ordinary RAG when the task is not “find the relevant paragraph” but:

- compare changes across many documents;
- trace a decision over time;
- reconcile contradictory sources;
- identify missing evidence;
- synthesize several dependent sub-questions.

Examples:
- broker statements + decision logs + market notes;
- government/bond documents across periods;
- scientific-paper review across methods/results/appendices;
- large technical repositories and architecture histories.

For simple lookup, conventional retrieval remains preferable.

## Important caution

RLM should not be treated as automatically better because it is recursive.

The likely tradeoffs are:
- more calls;
- higher latency;
- higher token/API cost;
- more operational failure modes;
- more opportunities for a wrong sub-analysis to propagate upward.

The relevant question is not:

> “Does recursion sound intelligent?”

It is:

> “Does adaptive recursive evidence navigation improve grounded task quality enough to justify its cost and complexity?”

This should be tested against strong non-recursive baselines.

## Bounded spike 1 — Long-history Reflection

### Question

Does an RLM-style Reflection Worker extract better grounded, reusable lessons from a long project/session history than a strong single-pass model?

### Candidate input

Use already committed Continuity history:
- session/event traces;
- findings;
- review docs;
- invalidated runs;
- accepted lessons.

No new behavioral experiment is needed for the first spike.

### Conditions

1. **LONG** — strong model receives as much directly supplied context as feasible.
2. **RAG** — ordinary retrieval + strong model.
3. **RLM** — root model recursively navigates the external evidence workspace.

### Task

Produce a small fixed number of candidate Lessons Learned.

Each lesson must include:
- generalized rule;
- applicability;
- recommended behavior;
- evidence references;
- counterexample/limitation if found.

### Evaluation

Blind review on:
- evidence grounding;
- unsupported claims;
- important events missed;
- overgeneralization;
- duplicate lessons;
- usefulness/actionability;
- calls/tokens/latency/cost.

This is a **research spike**, not a new CONT-006 confirmatory branch.

## Bounded spike 2 — Cross-document investigation

Use one question that genuinely requires evidence from many artifacts.

Example shape:

> “Across the Continuity arc, which recurring failure modes came from the model, which came from experiment/harness design, and which process changes actually prevented recurrence?”

Compare:
- long-context model;
- conventional RAG;
- RLM.

Require explicit source/evidence mapping for every major conclusion.

This tests the part of RLM that is most likely to matter in real mdlslab work: adaptive multi-hop evidence gathering.

## Relationship to CONT-006

RLM should **not** become another excuse to extend the synthetic CONT-006 benchmark series.

The current recommended Continuity exit direction remains:
- inspect the sealed G8B Stage-2 block exploratorily;
- record the Q35 ceiling;
- run at most 1–2 final procedural/project-style transfer experiments;
- freeze the arc.

RLM is potentially useful as **infrastructure for the Reflection Worker** in such a procedural experiment, because it changes how the worker reads history, not the transfer benchmark itself.

A clean separation would be:

```text
project history
     |
     v
RLM Reflection Worker
     |
     v
validated Lessons Store
     |
     v
future project-style task
```

Do not mix “RLM navigation works” and “Lessons Learned improve behavior” into one primary claim. They are separate questions.

## Recursive Agent Harness follow-on

A related recent direction, **Recursive Agent Harness (RAH)**, generalizes recursion from “LLM calls another LLM” to “an agent spawns focused sub-agents with tools/code/planning.”

This may eventually be more relevant to mdlslab than pure text-only RLM because repository research often requires:
- filesystem navigation;
- running code;
- comparing artifacts;
- computing metrics;
- checking provenance.

Do not start a separate RAH lab yet. First determine whether the simpler RLM pattern creates measurable value on the two bounded spikes above.

## Go / drop criteria

Proceed beyond the spikes only if RLM shows a clear benefit in at least one of:
- materially better evidence coverage;
- fewer unsupported conclusions;
- better cross-document reasoning;
- better lesson quality/actionability;

without an obviously disproportionate cost increase.

Drop/defer if:
- a strong long-context model performs equivalently;
- ordinary RAG performs equivalently at much lower cost;
- recursive calls mostly add latency and failure modes;
- gains depend on benchmark-specific prompt tuning.

## Recommended next action

1. Attend/watch the Research Lab session and capture any implementation details, especially:
   - architecture;
   - benchmark design;
   - where recursion helped;
   - where it did not;
   - latency/cost;
   - confounds they found.
2. Verify the primary paper/repository and pin a reproducible implementation/version.
3. Run **only the two bounded spikes above**.
4. Decide afterward whether RLM merits:
   - integration into Reflection-v2;
   - general mdlslab repository-research tooling;
   - or no further work.

The purpose is to test whether RLM can reduce context-management burden in real long-history work, not to create another open-ended experimental branch.
