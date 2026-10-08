# Independent review — CONT-006 CN-012 invalidation and rerun plan

Date: 2026-10-09  
Reviewer role: proposal co-owner / independent research observer  
Reviewed HEAD: `a8c7c97`  
Status: **REVIEW. The previous CONT-006 primary verdict is invalid as a test of the registered R0–R3 configuration. This is NOT a hypothesis-level NO-GO. A repaired rerun is warranted after independent review and protocol hardening.**

## Executive verdict

I agree with CN-012 and with the decision to invalidate the first CONT-006 confirmatory verdict.

The failed run did **not** execute the registered R0–R3 arms:

- R0 was intended to be persistent episodic memory with no lessons, but ran with no appended episodic memory.
- R2/R3 were intended to test lessons on top of the same persistent memory, but instead tested lessons on top of a memoryless worker.
- R1's deterministic reflection baseline had no episodic history to reflect over.

Therefore the frozen result

> R2 − R0 = +0.019, CI [−0.076, +0.114]

is not evidence that Reflection-v2 fails when combined with persistent memory.

It is better interpreted as an **accidental lessons-without-episodic-memory ablation**.

That accidental ablation is still useful:
- the lesson channel strongly changed behavior;
- format misses collapsed (R0 0.162 -> R2 0.0095; R3 0.0286);
- semantic accuracy did not materially improve;
- the BAD lesson demonstrated high behavioral salience of an active poisoned lesson.

But none of those observations rescues the registered primary claim.

## Root cause

The runner declared R0–R3 as memory arms for retrieval, but the append path used a separate hard-coded arm tuple that omitted them.

The result was structurally asymmetric:

```text
memory retrieval path: R0/R1/R2/R3 enabled
memory append path:    R0/R1/R2/R3 omitted
```

So retrieval correctly ran against an empty store.

The traces corroborate the code defect:
- zero `memory.append` events across the affected v3l R-arm runs;
- `memory.injected.injection = false` / empty episodes throughout;
- `memory_episodes = 0` in summaries.

This is a configuration-integrity failure, not a statistical ambiguity.

## What remains valid

The following artifacts/results remain useful and should not be discarded:

1. **Worker authoring artifacts and evidence-validated lesson stores.**
2. **Blind R3 gold lessons.**
3. **v3l fixture suite and taxonomy**, subject to the new review chain.
4. **Lesson-channel liveness observation:** lessons materially alter generated behavior.
5. **BAD lesson containment finding:** an active poisoned lesson can be followed/parroted.
6. **Accidental no-memory ablation:** generalized lessons alone mainly improved response discipline, not semantic correctness.

The old run should remain committed and explicitly labeled INVALID for the registered primary question rather than deleted.

## Required changes before rerun

### RC-1 — one source of truth for memory-arm membership

The current fix includes the missing R-arms in the append tuple, but the implementation should go one step further.

Do **not** maintain a second hard-coded arm list in the append path.

Use the already-defined `memory_arms` source of truth directly:

```python
if arm in memory_arms:
    ...
```

The exact CN-012 failure happened because two arm-membership lists drifted. Repeating the full tuple, even with the correct members today, preserves the failure mode.

Add a regression test asserting that every declared memory arm exercises both:
- append;
- subsequent retrieval/injection on a known multi-session scenario.

### RC-2 — pre-inference live memory invariant

Before any pilot or confirmatory dataset is allowed to accumulate, run a mandatory multi-session smoke for every behavioral arm that declares memory.

The gate must verify from trace artifacts, not only object state:

- `memory.append > 0`;
- store count > 0 after session 1;
- at least one session >= 2 has a non-empty `memory.injected`;
- injected episode refs resolve to earlier committed turns;
- R0/R2/R3 see the same episodic content for the same scenario/seed before lesson augmentation.

A single-session lesson-channel smoke is insufficient.

### RC-3 — paired arm-equivalence audit

For R0 vs R2 vs R3, everything except the lesson source/channel must be mechanically equivalent.

Add a pre-run audit that compares:
- model + provider config;
- memory implementation;
- retrieval top-k and renderer;
- fixture rendering;
- session reset behavior;
- seed;
- episodic store semantics.

The only permitted differences should be:
- R0: no lesson store;
- R2: worker lesson store;
- R3: gold lesson store.

This should be emitted as an artifact and independently reviewed.

### RC-4 — retrieval/content review before rerun

The invalid run still exposed a second likely weakness worth addressing before spending more compute.

The R2 active store contained four lessons, three of which were near-duplicates about single-label formatting. In the invalid confirmatory run they dominated retrieval:
- LL-W-001: 265 injections;
- LL-W-012: 265;
- LL-W-022: 228;
- semantic supersession lesson LL-W-034: only 37.

That explains why format compliance improved dramatically while semantic accuracy did not.

Before rerun, review:
- dedup threshold/semantic dedup quality;
- whether retrieval against only the session's first turn is sufficient;
- whether applicability matching should be structured rather than raw keyword overlap;
- whether generic format lessons should have a capped quota so they cannot crowd out task-semantic lessons.

Do not silently tune these from the invalid outcome. Any change must produce a new prereg/freeze version and be reviewed as such.

### RC-5 — preserve the accidental ablation as a separate result

Do not overwrite the invalid run conceptually.

Label it explicitly as:

> exploratory accidental ablation: lessons without episodic memory

It gives a useful causal clue:
- lessons can teach **how to answer**;
- without episodic state they cannot reliably supply **what the answer should be**.

The repaired run can then test the intended composition:

> episodic facts + generalized lessons

### RC-6 — new review chain before GPU/API spend

Before rerun:
1. implementing-agent self-review;
2. independent reviewer from the established queue (Fable preferred, then Opus, then local GLM if unavailable);
3. proposal co-owner review;
4. owner acceptance of the amended/frozen protocol.

The previous formal gates missed CN-012. The new review must include direct inspection of representative traces, not only manifests/digests.

## Rerun strategy

### Stage A — repaired baseline replication

First rerun the corrected protocol with the **same working core and reflector** used in the invalid run.

Reason: changing both implementation and models at once creates a new confound. If the repaired run changes materially, we need to know whether that came from restoring episodic memory, not from a stronger model.

This rerun does not need to reproduce every historical arm if review agrees the question can be narrowed. The scientifically central cells are:

- R0: episodic memory, no lessons;
- R2: same episodic memory + worker lessons;
- R3: same episodic memory + blind gold lessons.

R1 is useful as a historical baseline but is not load-bearing for the Reflection-v2 primary question.

Use a small fresh pilot first and verify live memory invariants before confirmatory execution.

### Stage B — hosted-model replication

After Stage A, I support a second replication using **hosted non-local models**.

This should be a separate external-validity experiment, not a replacement for the repaired baseline.

Recommended structure:
- one strong hosted working model;
- preferably a different model/family as the reflection worker to reduce same-model self-anchoring;
- same frozen experience corpus / lesson schema / validation logic where portable;
- fresh held-out transfer content;
- a short headroom pilot before committing to the full run.

Why this is valuable:
- Granite may simply be too weak at applying abstract lessons to trap-heavy semantic tasks;
- the local Qwen reflector may extract lessons that are linguistically valid but not optimally actionable for the working core;
- a stronger hosted working model lets us test whether the architecture is sound but the local core is the bottleneck.

Caution: a much stronger model may create a **ceiling effect**. If R0 already solves almost everything, lessons cannot show improvement. Therefore headroom must be measured before a hosted confirmatory run.

## Model-change interpretation

Do not ask one run to answer two questions.

The repaired local baseline asks:

> Does Reflection-v2 help when the intended architecture is actually executed?

The hosted replication asks:

> Does the effect generalize when model capability changes?

Those are different questions and should remain different result records.

## Updated interpretation of the existing evidence

My current view is:

- **Persistent episodic memory:** previously demonstrated useful in earlier Continuity work.
- **Lesson delivery channel:** clearly live; the invalid CONT-006 run demonstrates strong behavioral influence.
- **Reflection Worker lesson quality:** unresolved.
- **Lessons + episodic memory interaction:** not tested by the invalid run.
- **Bad-lesson safety:** real downstream risk, but primarily an activation/validation problem.
- **Current CONT-006 hypothesis:** still open.

## Review verdict

**RERUN REQUIRED / HYPOTHESIS STILL OPEN.**

Not GO on the existing result.  
Not NO-GO on Reflection-v2.

The previous primary verdict is invalidated by CN-012. Proceed only after RC-1..RC-6 are addressed and independently reviewed.

If the repaired same-model run remains null while:
- memory is demonstrably active,
- semantic lessons are actually retrieved,
- R3 gold lessons also fail,

then a null result becomes genuinely informative.

If R3 works but R2 does not, the architecture/channel is viable and the Reflection Worker is the weak link.

If repaired local R2/R3 remain weak but a hosted-model replication works, model capability is likely the bottleneck rather than the architecture itself.
