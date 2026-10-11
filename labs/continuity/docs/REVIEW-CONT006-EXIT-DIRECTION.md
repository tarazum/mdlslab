# Review — CONT-006 exit direction after Stage-2 STOP-OUT-OF-BAND

Date: 2026-10-11  
Reviewer role: proposal co-owner / independent research observer  
Reviewed through: `ffbbf22` plus current HEAD context  
Status: **Direction review. Recommendation: do not continue benchmark escalation on v3o/v3p as the default path. Allow at most 1–2 bounded follow-up experiments, then freeze CONT-006.**

## Executive view

CONT-006 has produced useful engineering and methodological findings, but the research program is now showing diminishing returns.

The latest STOP-OUT-OF-BAND is not another negative result for Reflection-v2. It is evidence that the current synthetic transfer surface is reaching the limit of its usefulness:

- G8B baseline is well calibrated: 58/105 = 0.5524.
- Q35 baseline is at 98/105 = 0.9333, above the registered ceiling guard.
- Q35 is perfect on correction_reuse, repeated_task, distractor_recall and delayed_recall; only contradiction_update retains meaningful headroom.

The pre-registered halt behaved correctly. The important question is what to do with that signal.

My recommendation is **not** to make "author v3p until Q35 is mid-band" the default continuation. Repeatedly making synthetic puzzles harder risks optimizing the benchmark around a particular model rather than testing the original Reflection hypothesis.

## What the arc has already taught us

The work is not empty despite the lack of a satisfying positive endpoint.

### 1. Persistent episodic memory is genuinely useful

Earlier Continuity experiments established strong delayed-recall/state-transfer effects. CONT-002 additionally showed that learned persistent state can transfer across different cores.

That component has survived multiple redesigns.

### 2. Lesson delivery is behaviorally powerful

CONT-006 repeatedly showed that lesson/system blocks materially change the working model:

- format compliance can improve sharply;
- neutral blocks can also move behavior;
- deliberately bad active lessons can be followed/parroted;
- the effect can be harmful, beneficial on isolated clusters, or simply interference.

So "the lesson channel is inert" has been ruled out.

### 3. The hard part is not writing text into the context

The unresolved problem is whether the extracted lesson contains a useful abstraction and whether the consumer can apply that abstraction to a genuinely new situation.

Several diagnostics showed that:
- G8B is sensitive to extra blocks and often degrades;
- Q35 is much more robust to injected context;
- on the tested surfaces Q35 is frequently at ceiling, so positive lesson value is unmeasurable;
- no tested worker-authored lesson set has yet produced a convincing end-to-end transfer benefit.

### 4. Many failures were experimental-system failures, not hypothesis failures

The arc caught substantial issues:
- CN-012 memory append omission invalidated an entire behavioral chain;
- delivery mechanics mattered;
- validator lexical collisions selected lesson coverage;
- fixture underspecification contaminated repeated-task probes;
- neutral controls carried unintended workflow content;
- store-generation pipelines differed in more dimensions than originally claimed;
- strong-model ceiling repeatedly removed headroom.

These are valuable lessons, but they also show that further synthetic work has a high probability of spending more effort on harness correction than on the underlying research question.

## Reading the Stage-2 STOP

The correct interpretation of `STOP-OUT-OF-BAND.md` is:

> v3o is an informative surface for G8B, but not an informative efficacy surface for Q35.

This is a property of the measurement surface, not evidence that Q35 does or does not benefit from Reflection.

The declared option A ("author v3p with harder Q35-tier levers") is methodologically legitimate, but I do **not** recommend it as the default next step.

Why:

1. Q35 already solves four of five primary families at or near ceiling.
2. Any new suite would need to be deliberately engineered to make Q35 fail.
3. Repeating this loop creates benchmark-chasing risk.
4. The resulting harder puzzles may drift even farther from the original "Lessons Learned from real work" concept.
5. A still-stronger hosted model would likely recreate the same ceiling problem on another synthetic suite.

## Recommended immediate action: C + D from the STOP record

### C — authorize exploratory analysis of the sealed G8B block

The G8B Stage-2 block is complete:
- NONE;
- NEWF2 / NEUTRAL / OLDG;
- probe-time / session-start;
- 7 seeds;
- baseline in the registered headroom band;
- no invalid cells.

This data should be inspected **exploratorily only**, with no confirmatory verdict and no retroactive endpoint change.

Questions worth answering:
- NEWF2 vs NONE;
- NEWF2 vs matched NEUTRAL;
- session-start vs probe-time;
- OLDG vs NEWF2;
- family-level error-mode decomposition.

The purpose is diagnostic: decide whether any mechanism is worth carrying into one final transfer experiment.

### D — record the Q35 ceiling as a real result

The Q35 finding is itself useful:

> On v3o with persistent memory and no lesson layer, Q35 scores 93.3% overall and reaches 100% on four of five primary families.

This marks the practical limit of the current synthetic surface for a stronger consumer model.

Do not describe it as a Reflection success or failure.

## Recommended final direction: return to the original Reflection concept

The initial idea behind Reflection-v2 was closer to project `LESSONS-LEARNED.md` than to classification-memory puzzles.

The desired abstraction is:

```text
work session(s)
    -> evidence/history
    -> independent reflection process
    -> generalized procedural lesson
    -> later, structurally related but surface-different work
```

Examples of the target lesson level:

- Fetch the latest shared artifact/revision immediately before modifying it.
- After a persistence/schema change, run the smallest relevant validation immediately rather than deferring all checks.
- Treat generated artifacts as stale after their source changes.
- When an external correction supersedes prior model output, do not treat the model's prior answer as authoritative evidence.

These are procedural/project lessons, not stored answers.

A strong model cannot solve this simply from pretrained world knowledge if the rule arises from the history or conventions of a specific synthetic project.

That creates **natural headroom** without making riddles artificially harder.

## Final experiment candidate 1 — Procedural Lessons Transfer

This should be the preferred last major CONT-006 experiment.

### Core question

Can a Reflection Worker extract a procedural lesson from completed project work and reduce recurrence of the same **failure class** in a different task/project where the surface details have changed?

### Suggested arms

| Arm | Context |
| --- | --- |
| A | Current task only |
| M | Relevant episodic/project history only |
| L | Relevant validated Lessons Learned only |
| M+L | Episodic/project history + validated lessons |

The important new arm is **L**.

If L transfers, Reflection has extracted a portable abstraction rather than merely helping retrieval.

### Experience phase

Use small sandbox/project workflows with objectively detectable mistakes, for example:
- editing an artifact based on a stale revision;
- changing a schema without validating dependent code;
- failing to run the smallest relevant test after a focused change;
- using a stale generated artifact after source mutation;
- repeating an invalid retry/process pattern after the evidence already changed.

Reflection runs after completed work, not inside the task loop.

### Transfer phase

Use a new project/task with:
- different filenames;
- different domain text;
- different identifiers;
- different concrete failure instance;
- the same latent procedural rule.

Primary endpoint:

> recurrence of the target failure class.

This maps much more directly to the original "Lessons Learned" intuition than label accuracy does.

### Important controls

- gold/manual lesson arm if affordable, to separate lesson-channel viability from extraction quality;
- neutral procedural note of comparable length;
- no access to transfer task during lesson extraction;
- deterministic outcome checker whenever possible;
- small number of high-quality failure classes rather than another large taxonomy.

## Final experiment candidate 2 — strong-model / hosted replication

Only run this if experiment 1 has a meaningful signal or a clearly diagnosed consumer-capacity limitation.

Use a stronger hosted working model and preferably a different model family for the Reflection Worker.

Purpose:

> test external validity of the architecture, not rescue a failed local result.

Do **not** run a stronger hosted model on v3o merely to repeat the ceiling.

The procedural surface should be used because project-specific lessons retain headroom even for strong models.

Before full execution, use a tiny headroom pilot. If the baseline already solves nearly every procedural failure class, stop rather than escalating difficulty again.

## Explicit exit criteria

CONT-006 should not become an open-ended benchmark-development project.

I recommend the following hard cap:

### Experiment 1
Run the procedural Lessons Learned transfer experiment.

Then:

- **Clear positive transfer:** optionally run one hosted/model-family replication.
- **Mixed but diagnostic result:** at most one tightly targeted replication addressing the identified bottleneck.
- **Null with valid gold/control channel:** freeze CONT-006.
- **Another major harness/design invalidation:** repair only if cheap; otherwise freeze and document the limitation.

### Experiment 2
If authorized, this is the **last planned CONT-006 experiment**.

After it:
- write a final synthesis;
- classify each claim as established / directional / unresolved / falsified-on-tested-scope;
- archive/freeze the Continuity experimental arc;
- retain reusable infrastructure and lessons for future labs;
- do not create v3p/v3q merely because another model needs a different difficulty band.

Any work beyond this point should require a **new research question**, not "one more CONT-006 fix."

## What success should mean before freeze

A satisfying outcome does not require proving that Reflection universally improves agents.

A useful final result could be any of:

1. **Positive:** validated procedural lessons reduce recurrence on held-out project-style tasks.
2. **Conditional:** lessons help only a sufficiently capable consumer / only in M+L.
3. **Negative:** even gold procedural lessons do not improve recurrence under a clean delivery channel.
4. **Extraction failure:** gold lessons help, worker lessons do not — Reflection Worker quality is the bottleneck.
5. **Interference finding:** lessons are behaviorally salient but the costs exceed transfer gains on the tested architecture.

All five are scientifically cleaner endpoints than continuing to tune a synthetic suite until a desired mid-band appears.

## Recommendation / owner decision suggested

Recommended path:

1. **Authorize exploratory-only analysis of the existing sealed G8B Stage-2 block.**
2. **Record Q35 v3o ceiling as a bounded measurement result.**
3. **Do not author v3p as the default continuation.**
4. **Design one project/procedural Lessons Learned transfer experiment aligned with the original Reflection-v2 motivation.**
5. **Reserve one optional hosted/strong-model replication as the final experiment.**
6. **Freeze CONT-006 after those 1–2 experiments and write a final synthesis.**

This recommendation explicitly incorporates the owner's concern that the arc has consumed disproportionate tokens/iteration effort relative to the clarity of its final result. The goal of the remaining work should be **closure**, not expansion.
