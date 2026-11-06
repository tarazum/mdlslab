# Case study: Perceived Utility vs Demonstrated Behavioral Transfer

**Status:** qualitative external observation; hypothesis-generating only.  
**Source:** Owner-supplied Fable assessment of a private work-project knowledge system (November 2026), paraphrased and sanitized for public publication. Original contains non-public project identifiers, operational schedules, incident details, and personal names; none are reproduced here.

## Observation

An agent acting as a consumer of a project knowledge system ranked a structured `lessons-learned.yaml` collection first for *anticipated utility per token*. Its rationale: compact entries organized as **problem → root cause → solution → key points** provide project-specific facts absent from the foundation model's prior knowledge. It also valued incident playbooks and a decisions log, and recommended section-level retrieval, distilled meeting notes, usefulness feedback, alias mappings, and freshness-aware scoring.

The agent used counterfactual language: such lessons **would have saved** substantial effort. This is an expectation, not measured task improvement. Its feedback was a design/consumer review, not a randomized A/B trial.

## Relation to Continuity experiments

- **CONT-001:** Persistent memory improves recall on tested synthetic tasks, but self-model/reflection can amplify anchoring on prior wrong answers. The confirmatory repeated-mistake contrast did not establish a difference; measurement-floor and power caveats apply. See `docs/REVIEW-FABLE.md`.
- **CONT-005:** Provenance/trust machinery did not improve label accuracy over plain episodic memory on the tested core and surfaces. See `docs/RESULTS-DIGEST-2026-10.md`.
- **CONT-006:** Tests whether reflection extracts **generalizable procedural lessons** and whether supplying them reduces recurrence of a failure class on surface-different tasks. See `docs/DESIGN-CONT006-PLT.md`. This is *not identical* to consuming curated, domain-specific troubleshooting entries in a live work project.

## Why this is not a contradiction

1. **Different endpoint:** perceived usefulness, retrieval convenience, and prior information gain vs observed reduction in repeated mistakes.
2. **Different treatment:** curated factual/project lessons vs independently extracted procedural rules.
3. **Different environment:** real project context and a capable reviewing agent vs bounded synthetic tasks and pinned local consumers.
4. **No measured counterfactual:** the review does not compare matched tasks with/without lessons.

The observation is therefore **compatible** with an inconclusive or negative behavioral experiment. It does, however, challenge any overgeneralization from the lab to the practical value of structured lessons.

## Falsifiable follow-up

On a privacy-safe synthetic project corpus, compare **no context**, **curated lessons**, **automatically extracted lessons**, and **length-matched neutral notes**, using the same tasks and controlled context budget. Measure task success, recurrence of target failure classes, token cost, and actual use of retrieved evidence. Include a gold-lesson control to separate extraction failures from consumer failures; score both retrieval and action outcomes. Do not treat citations or agent self-reports as proof of causal benefit.

**Decision:** Archive this as a qualitative contrast case, **not** as evidence overturning CONT-006 or as a new authorization to run experiments.
