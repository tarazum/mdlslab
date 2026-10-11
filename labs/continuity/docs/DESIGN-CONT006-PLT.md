# DESIGN (draft) — CONT-006 final experiment 1: Procedural Lessons Transfer (PLT)

Status: DRAFT for the review chain (Fable → codex fallback) and the owner
gate. Zero GPU so far. Nothing here is frozen; execution starts only
after PR review + owner accept (never-autonomous).

Direction basis: `docs/REVIEW-CONT006-EXIT-DIRECTION.md` (owner, 3b62e9a)
+ ROADMAP "Owner decisions — recorded 2026-10-11". This is experiment 1
of the hard cap (max 1–2, then freeze CONT-006).

## 1. Research question

Can an independent reflection process extract a **procedural lesson**
from completed project work, such that delivering that lesson reduces
recurrence of the same **failure class** in later, surface-different but
structurally related work — without access to the original task's
surface details?

This returns CONT-006 to the original Reflection-v2 motivation
(`LESSONS-LEARNED.md`), replacing label-accuracy puzzles with
project-style work where headroom is natural: a strong model cannot
know a project's conventions from pretraining.

## 2. Abstraction pipeline under test

```text
experience:  completed sandbox-project sessions with a recorded,
             objectively detectable failure of class FC-x
                 ↓ (no access to any transfer task)
reflection:  worker model reads evidence/history only
                 ↓
lesson:      short procedural rule ("after X, do Y before Z")
                 ↓
transfer:    new project — different names, domain text, identifiers,
             concrete failure instance; SAME latent procedural rule
                 ↓
endpoint:    recurrence of failure class FC-x (deterministic checker)
```

## 3. Failure classes (small and high-quality, per the review)

Each class must have (a) a deterministic checker over the action log /
resulting sandbox state, and (b) natural headroom: the safe behavior is
project-convention-driven, not pretrain-guessable.

| id | failure class | trap (experience) | checker (transfer) |
|---|---|---|---|
| FC-1 | stale-revision edit | agent edits artifact from an outdated revision although a newer shared revision exists | edit applied to base ≠ latest revision at edit time |
| FC-2 | persistence/schema change without dependent validation | schema/persistence changed; dependent check deferred/skipped | required validation action absent after change event |
| FC-3 | focused change without smallest relevant test | code/config edited; the one relevant local check not run | test action absent between edit and "done" |
| FC-4 | stale generated artifact after source mutation | source changed; generated artifact consumed without regeneration | artifact digest ≠ regenerate(source digest at use time) |
| FC-5 | invalid retry after evidence change | same failed approach retried after the evidence invalidating it | ≥2 identical-method retries post-invalidation marker |
| FC-6 (candidate) | authority error: treating a superseded own/external answer as evidence | prior output quoted as ground truth after external correction supersedes it | superseded token used as justification in a later decision |

Default: FC-1..FC-5 (5 classes). FC-6 optional if authoring budget
allows; NOT more (no new taxonomy).

## 4. Surface

- **Experience phase (deterministic, zero GPU):** pre-authored sandbox
  project histories (action logs + artifacts) in which the failure
  occurs and is evident from the evidence. Authored by a deterministic
  simulator module (scripted project world), NOT by the consumer model.
  Why: fixed reflection input → lessons comparable across arms; the
  failure's presence is guaranteed; no GPU spent manufacturing traps.
  Declared alternative (not default): live consumer works the
  experience task and naturally falls into the trap — ecological but
  non-deterministic occurrence; revisit only at review.
- **Transfer phase (live model):** new project per class instance:
  different filenames, domain text, identifiers, failure instance;
  same latent rule. The consumer works the task in a bounded file/command
  sandbox; every action journaled.

## 5. Arms

| arm | context delivered at transfer | role |
|---|---|---|
| A | current task only | baseline |
| M | relevant episodic/project history only | memory-only reference |
| L | validated lessons only | **decisive: portable abstraction?** |
| M+L | episodic history + validated lessons | combined |
| GOLD-L (control) | hand-authored high-quality lesson per class | lesson-channel viability vs extraction quality |
| NEUTRAL-L (control) | procedural note, length-matched, no rule | generic-interference control |

GOLD authoring is blind to transfer instances (rule-level text only).
Worker lessons pass the consumption gate (answer-vocabulary check
against the transfer surface) — the v1 gap stays closed.

Models (local, pinned): consumer = granite-code:8b (mid-band on this
kind of surface; the arc's workhorse); reflection worker =
qwen36-35b-a3b (the arc's reflector). No hosted models in experiment 1.

## 6. Endpoints

- **Primary:** recurrence rate of the target failure class at transfer,
  L − A (paired cluster bootstrap over classes; the existing machinery).
- Decision contrasts (pre-registered, all reported): M − A, M+L − A,
  L − M, GOLD-L − A, NEUTRAL-L − A.
- **Localization matrix** (the review's closure logic):
  - GOLD-L helps, L does not → extraction is the bottleneck;
  - L ≈ NEUTRAL-L, both ≠ A → generic block interference, not content;
  - M helps, L does not (and GOLD-L helps) → abstraction missing from
    history-alone retrieval;
  - nothing helps incl. GOLD-L on a mid-band consumer with a live
    channel → the lessons idea itself fails on tested scope;
  - M+L > max(M, L) → complementarity.
- Sizing at prereg (declared): K = 5 classes × 3 transfer instances ×
  7 seeds (105 binary outcomes per arm per contrast scope); MME 0.20
  target, directional-below-MME reported as directional. Power artifact
  REQUIRED before freeze (learned from stage-2: interaction-scale
  effects need explicit sizing).

## 7. Gates and stop branches (binding)

1. **Headroom pilot (tiny, first GPU):** 2 classes × 2 seeds × {A,
   GOLD-L}. PASS requires: baseline recurrence mid-band (0.3–0.9 per
   class) AND GOLD-L moves recurrence by ≥ MME 0.20 on at least one
   class (channel alive). FAIL → stop; report as endpoint (3)/(5) of
   the success typology — do NOT escalate difficulty (no v3p-logic).
2. Deterministic checkers validated against hand-labeled traces
   (checker ≡ label on a labeled dev set) before freeze.
3. Consumption gate over the transfer surface for every delivered
   lesson (worker AND gold).
4. Contamination: experience and transfer surfaces share no 6-gram
   content; lesson text shares no transfer answer vocabulary.
5. Freeze discipline unchanged: prereg → digests → review gate → owner
   accept → execution; live telemetry gate before the analyzer;
   analyzer fail-closed.

## 8. Harness delta (declared, bounded)

New, versioned: sandbox task harness (bounded file/command sandbox with
a journaled action log + deterministic per-class checkers) and the
simulator that authors experience histories. Reused as-is: SQLite
memory store, lesson delivery channel, model pins, freeze/gate/review
discipline, bootstrap analysis machinery. No new UI/tools.

## 9. Non-goals

- No v3p/v3q, no synthetic-suite difficulty chasing.
- No hosted models in experiment 1 (experiment 2 = optional replication,
  only on signal or a diagnosed consumer-capacity limit; tiny headroom
  pilot first — never a v3o ceiling re-run).
- No taxonomy growth beyond FC-1..FC-6.
- No confirmatory claims from the exploratory G8B stage-2 report.

## 10. Exit criteria (binding, from the owner direction)

After this experiment: positive → optional hosted replication
(experiment 2, the last); mixed-but-diagnostic → at most one targeted
replication of the identified bottleneck; null-with-valid-controls →
freeze CONT-006; major harness invalidation → repair only if cheap,
else freeze and document. Then: final synthesis, claims classified
(established / directional / unresolved / falsified-on-tested-scope),
archive, reusable infra retained.

## 11. Open questions for the reviewer

1. Experience phase determinism (scripted histories) vs ecological
   validity (live consumer failing naturally) — default scripted; is
   the tradeoff accepted?
2. FC-6 in or out (budget vs coverage)?
3. 3 transfer instances per class enough for the M+L complementarity
   read, or drop M+L-specific claims to directional?
4. GOLD-L arm at full 7 seeds or reduced (budget) — reduced weakens the
   localization matrix's anchor; default full.
5. Consumer = G8B only in experiment 1 (Q35 replication folded into
   experiment 2) — accepted?
