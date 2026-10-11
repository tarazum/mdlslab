# DESIGN (rev 2, review-folded) — CONT-006 final experiment 1: Procedural Lessons Transfer (PLT)

Status: DRAFT rev 2. Rev 1 reviewed by Opus (doc-level, GO-with-changes,
R-1..R-19; `docs/REVIEW-OPUS-CONT006-PLT.md`, curation 4/4 confirmed);
all findings folded below. Fable limit-blocked that day (queue: Fable →
Opus → Astra → Flash). Zero GPU so far. Nothing frozen; execution starts
only after owner accept (never-autonomous).

Direction basis: `docs/REVIEW-CONT006-EXIT-DIRECTION.md` (owner, 3b62e9a)
+ ROADMAP "Owner decisions — recorded 2026-10-11". Experiment 1 of the
hard cap (max 1–2, then freeze CONT-006).

## 1. Research question

Can an independent reflection process extract a **procedural lesson**
from completed project work, such that delivering that lesson reduces
recurrence of the same **failure class** in later, surface-different but
structurally related work — without access to the original task's
surface details?

Returns CONT-006 to the original Reflection-v2 motivation
(`LESSONS-LEARNED.md`): project-style work where headroom is natural —
a strong model cannot know a project's conventions from pretraining.

## 2. Abstraction pipeline under test

```text
experience:  completed sandbox-project sessions with a recorded,
             objectively detectable failure of class FC-x (the failure
             is DERIVABLE from the log and never named — R-7 standard)
                 ↓ (no access to any transfer task)
reflection:  worker model reads evidence/history only
                 ↓
lesson:      short procedural rule ("after X, do Y before Z")
                 ↓
transfer:    new project — different names, domain text, identifiers,
             concrete failure instance; SAME latent procedural rule
                 ↓
endpoint:    recurrence of failure class FC-x (deterministic checker),
             counted ONLY on episodes where the trigger opportunity
             occurred (R-2), with task-success as co-endpoint
```

## 3. Failure classes (small, high-quality, deterministic checkers)

| id | failure class | trap (experience) | checker (transfer) |
|---|---|---|---|
| FC-1 | stale-revision edit | edit applied to an artifact revision that is not the latest shared revision | edited base revision ≠ latest at edit time (journal equality) |
| FC-2 | persistence/schema change without dependent validation | schema changed; required dependent check skipped | required validation action absent between change event and completion |
| FC-3 | focused change without smallest relevant test | code/config edited; the one relevant local check not run | test action absent between edit and "done" |
| FC-4 | stale generated artifact after source mutation | source changed; generated artifact consumed without regeneration | artifact digest ≠ regenerate(source digest at use time) |
| FC-5 | invalid retry after evidence change | same failed approach retried after evidence invalidating it | ≥2 retries with IDENTICAL action-signature after invalidation marker (exact journal equality — R-14) |

FC-6 (authority error) — **declared OUT** (Opus R-14/§B-11.2: semantic,
non-deterministic checker; 6th class buys no decision-relevant power).
Budget goes to instances, not classes. No taxonomy growth.

## 4. Surface

- **Experience phase (deterministic, zero GPU):** pre-authored sandbox
  project histories (action logs + artifacts) in which each failure
  occurs and is evident from evidence. **Explicitness standard (R-7):**
  the failure must be derivable from the journal and NEVER named;
  automatic lint bans class-name lexicon and imperative rule forms in
  histories; human spot-check ≥5 histories/class, recorded in an
  artifact. Declared limitation (scope, not defect): lessons are
  extracted from canonically-readable histories; ecological validity
  of live-failing experience is not tested.
- **Transfer phase (live model):** new project per class instance —
  different filenames, domain text, identifiers, failure instance;
  same latent rule. Consumer works in a bounded file/command sandbox;
  every action journaled. Instance-vs-instance independence enforced
  by an automatic identifier/name disjointness matrix across ALL
  instances of a class (R-17).

## 5. Arms — staged (R-5)

| stage | arm | context delivered at transfer | role |
|---|---|---|---|
| 1 | A | current task only | baseline |
| 1 | L | validated lessons only | **decisive: portable abstraction?** |
| 1 | GOLD-L | hand-authored high-quality lesson per class | lesson-channel viability vs extraction quality |
| 1 | NEUTRAL-L | procedural note, length-matched (±25%), no rule | generic-interference control |
| 2 (conditional) | M | relevant episodic/project history only | memory-only reference |
| 2 (conditional) | M+L | episodic history + validated lessons | complementarity (directional) |

Stage 2 runs ONLY if stage 1 shows a live channel (GOLD-L or L moves
recurrence); protects the decisive contrasts within the same budget.
M/M+L stay in the design — deferred, not dropped.

**Blind gold, mechanized (R-9):** GOLD-L texts are committed and
digested BEFORE any transfer instance exists (binding freeze-ordering
requirement; proof by commit order + digest manifest).
**NEUTRAL-L lint (C.4):** no procedural imperatives (ban-list), no
class vocabulary, length-matched ±25%.
**Consumption gate, redefined for procedural lessons (R-6):**
(i) surface-leak ban — no identifier/filename/domain of ANY transfer
instance in lesson text (exact + normalized match, automatic);
(ii) declared-permitted generic procedural lexicon ("run the smallest
relevant check …") — explicitly allowed by design, else the gate would
cut exactly the target abstraction level; (iii) no imperatives specific
to a concrete transfer step.

Models (local, pinned): consumer = granite-code:8b; reflection worker =
qwen36-35b-a3b. **Q35 as consumer appears ONLY in the pilot, ONLY on
GOLD-L (R-13): consumer selection before the main spend, not a
replication.** Hosted models = experiment 2 only, per the exit criteria.

## 6. Endpoints, sizing, inference

- **Primary (the only confirmatory contrast):** recurrence rate of the
  target failure class, **L − A**. All other contrasts are
  secondary/descriptive without MME machinery (R-15); no multiplicity
  correction needed (single test).
- **Episode eligibility (R-2):** an episode enters the primary only if
  its trigger opportunity occurred (edit made / schema changed /
  artifact consumed / …). **Task-success co-endpoint** (deterministic
  checker of task completion) is mandatorily reported next to
  recurrence; a positive L claim additionally requires non-inferior
  task-success. **Paralysis rate** (episodes without trigger event) is
  a per-arm secondary — "cautious do-nothing" cannot masquerade as
  lesson benefit.
- **Geometry (R-1):** cluster = (class, instance). Default 5 classes ×
  **5 instances** × 7 seeds = 25 clusters × 7 = 175 episodes/arm;
  stage-1 arms 4 → 700 episodes total ≈ rev-1 budget (630) with
  materially higher primary power. Stage 2 (+M, +M+L conditional)
  ≈ +350.
- **Power artifact computed BEFORE the prereg freeze** (not "at prereg"):
  MDE for L−A at 25×7 under the stage-2 artifact's planning model
  (sig_shared/sig_cell rows), binary recurrence delta. Declared
  honesty caveat: instances within a class share the latent rule →
  25-cluster bootstrap understates between-class variation. Therefore
  MANDATORY sensitivity, pre-registered: leave-one-class-out and
  two-level (class → instance) bootstrap; if the sign/conclusion does
  not survive LOO → classified directional, not established.
  Class-level generalization is NOT inferred; scope claim = "on the 5
  tested classes".
- **Seed semantics (R-3), declared:** a seed varies (a) sampling
  temperature > 0 for the consumer, (b) instance-irrelevant sandbox
  detail order, (c) memory/episode tie-breaks — never the latent rule
  or checker. Pilot gate: if within-cluster seed variation ≈ 0 in the
  pilot, effective-n is recomputed at cluster level and MME/power are
  re-issued BEFORE the full run (prereg amendment, owner-visible).
- **Decision contrasts (secondary, all reported):** GOLD-L − A,
  NEUTRAL-L − A, (stage 2) M − A, M+L − A, L − M. **Localization
  matrix (complete — R-16):**
  - GOLD-L helps, L does not → extraction is the bottleneck;
  - L ≈ NEUTRAL-L ≠ A → generic block interference, not content;
  - M helps, L does not (GOLD-L helps) → abstraction missing from
    history-alone retrieval;
  - nothing helps incl. GOLD-L, mid-band consumer, live channel →
    the lessons idea fails on tested scope (consumer-scoped claim);
  - M+L > max(M, L) → complementarity (directional only — declared);
  - M+L < max(M, L) → interference-dominant combination;
  - L helps but GOLD-L does not → harness artifact suspicion —
    investigate branch, NO claim.
- **Lesson-quality rubric (R-8, prereg secondary):** blind rating of
  each worker lesson vs the class's gold rule (correct / partial /
  wrong / vague), rater + adjudication, blind to arm and transfer
  outcome. Makes "extraction is the bottleneck" a measured statement.

## 7. Gates and stop branches (binding)

1. **Headroom pilot (first GPU):** 2 classes × 3 instances × **5 seeds**
   arms {A, GOLD-L} on G8B **+ GOLD-L on Q35** (consumer selection,
   R-13). Screening criterion (R-11 — not an inference): baseline ∈
   [0.3, 0.9] per class AND GOLD-L strictly lower in ≥1 class with
   ≥2/5 flips. Pilot data status: **excluded from primary** (declared
   before the run). Out-of-band pilot class → declared-out of the full
   run (no class edits, no difficulty changes — the escalation ban
   covers this branch); <3 classes in band → STOP (primary loses
   clusters). **Max ONE pilot repeat, only after owner gate, only for
   a diagnosed harness bug (never difficulty); any difficulty/class
   change = freeze CONT-006 outright (E.3).**
2. **Full-run per-class baseline gate (R-4):** arm-A phase band check
   [0.3, 0.9] per class; out-of-band class → excluded from primary
   with a declaration (class never edited); analyzer fail-closed on
   the gate record.
3. **Harness self-test + dry-run BEFORE any GPU (C.1/C.3):** per-class
   synthetic traces with known answers (recurrence true / false) —
   checker must match; then a stub-consumer dry-run of the whole chain
   (all arms × classes: positional context delivery, journaling,
   checkers, analyzer end-to-end). Fail → no start.
4. **Checker validation with acceptance numbers (R-10):** ≥20 labeled
   dev traces/class, 2 independent labelers, 100% agreement required on
   class-defining events (or ≥0.95 + recorded error analysis); dev
   traces held out from the final run; checker code digested in EXEC
   FREEZE.
5. **Per-episode invariants, fail-closed (R-12):** journal completeness,
   trigger-event consistency, sandbox state consistency. Invalid
   episodes are NEVER silently re-run — each is logged with cause;
   >10% invalid in any cell → halt + owner gate.
6. **Single EXEC FREEZE (C.6):** harness + simulator + checkers + arms
   digested together before the first GPU episode; ANY post-start fix
   = halt + owner gate (no "quick repairs").
7. Contamination gates: experience ↔ transfer no shared 6-grams;
   lesson text surface-leak ban (§5); identifier disjointness matrix
   (§4).
8. Freeze discipline unchanged: prereg → digests → non-executor gate →
   owner accept → execution; live telemetry before the analyzer;
   analyzer fail-closed.

## 8. Harness delta (declared, bounded) + budget (R-5)

New, versioned: sandbox task harness (bounded file/command sandbox,
journaled action log), deterministic per-class checkers, experience
simulator, checker dev-set. Reused: SQLite memory store, lesson
delivery channel, model pins, freeze/gate/review discipline, bootstrap
machinery. No new UI/tools.
Budget per episode (turns / tokens / wall) + per-cell wall guard +
resumable cell-seed dirs + total GPU-hours estimate — all fixed in the
prereg before freeze (stage-2 V2A convention).

## 9. Non-goals

- No v3p/v3q; no difficulty escalation anywhere (incl. pilot and
  out-of-band branches).
- No hosted models in experiment 1 (Q35 pilot consumer-selection only);
  experiment 2 = optional hosted replication, gated on signal or a
  diagnosed consumer-capacity limit, tiny pilot first.
- No taxonomy growth (FC-6 declared out; nothing beyond FC-1..FC-5).
- No confirmatory claims from the exploratory G8B stage-2 report.

## 10. Exit criteria and REQUIRED closing artifacts (R-18/R-19)

After this experiment: positive → optional hosted replication
(experiment 2, the last); mixed-but-diagnostic → at most one targeted
replication of the identified bottleneck; null-with-valid-controls →
freeze; major harness invalidation → repair ONLY if cheap, defined
numerically NOW: ≤1 session, no new module, no freeze-surface change —
otherwise freeze and document.
Mandatory close-out files (binding, so exit does not depend on
post-run mood): final synthesis doc; claims table classified
(established / directional / unresolved / falsified-on-tested-scope);
typology mapping observed-pattern → endpoints 1–5 of the owner's
review; reusable-infrastructure inventory. Then archive/freeze.

## 11. Resolved questions (rev-1 §11 → Opus §B)

1. Scripted experience accepted (determinism, arm-comparability,
   zero-GPU) with the R-7 explicitness standard + limitation line.
2. FC-6 OUT (non-deterministic checker; instances > classes).
3. M+L claims directional-only, declared in advance.
4. GOLD-L at full seed count (anchor of the localization matrix);
   budget pressure cuts M (stage-2 staging), never GOLD-L.
5. Consumer G8B-only accepted with the Q35 GOLD-L pilot as consumer
   selection; a null is scoped "falsified-on-tested-scope for a
   mid-band 8B consumer", not for the architecture.
