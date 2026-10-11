# PREREG-CONT006-PLT — Procedural Lessons Transfer (CONT-006 final experiment 1)

Status: PRE-REGISTERED rev 2 (review-folded; verify-pass
`docs/REVIEW-OPUS-CONT006-PLT-PREREG.md` — GO-with-changes, V-1..V-12
all folded here). Owner accepted the design rev 2 in chat 2026-10-11
(«ок»); ROADMAP records the exit direction and the accept. Power
artifact computed BEFORE this freeze:
`experiments/cont006/power-results-plt.json` (v3 — conjunctive decision
rule). Experiment 1 of the hard cap (max 1–2, then FREEZE CONT-006).

## 1. Research question and arms

Can a reflection worker extract a procedural lesson from completed
project work that reduces recurrence of the same failure class in
surface-different, structurally related work?

- Consumer: granite-code:8b (pin 36c3c3b9683b), **temperature 0.3**
  (seed variation mechanism, R-3/V-5). Worker: qwen36-35b-a3b (pin
  8a0fd5da454e), **temperature 0.2**. Both pinned in the freeze.
- Stage 1 arms: **A** (task only) / **L** (worker lessons only) /
  **GOLD-L** (hand-authored lessons) / **NEUTRAL-L** (length-matched
  procedural note, linted).
- Stage 2 (conditional, criterion in §6.4): **M** (episodic history) /
  **M+L**.
- Failure classes FC-1..FC-5 (design §3; FC-6 declared out). Cluster =
  (class, instance): 5 × 5 = 25 clusters × 7 seeds. **Pilot classes:
  FC-1 and FC-3** (fixed now — the choice is not a post-hoc degree of
  freedom; cleanest journal-equality checkers).
- Q35-as-consumer appears ONLY in the pilot on GOLD-L (§6.1b).

## 2. Endpoints (frozen)

- **Primary (the only confirmatory contrast):** recurrence rate of the
  target failure class, **L − A**, on trigger-eligible episodes only
  (an episode counts only if its trigger opportunity occurred).
- **Estimator:** the unweighted mean of the 25 per-cluster deltas
  d_c = mean_eligible_seeds(L) − mean_eligible_seeds(A). NOT the
  pooled episode rate (unequal eligibility across clusters would make
  the two differ; the power artifact models exactly the cluster mean).
  Pairing is at CLUSTER level (the same (class, instance) in every
  arm); seeds are NOT paired across arms.
- **Benefit-established (compound decision rule, V-1):** ALL of
  (i) CI95 of L − A entirely below 0; (ii) point |d̂| ≥ 0.20; (iii)
  EVERY leave-one-class-out drop (5 datasets) keeps CI95 entirely
  below 0; (iv) the two-level (class → instance) bootstrap CI95
  entirely below 0. Failing (i) → "no difference established"; CI
  entirely above 0 → interference-harm branch (same compound logic
  mirrored). Conclusions that pass (i) but fail (ii)/(iii)/(iv) are
  **directional** (the downgrade rule).
- **Task-success co-endpoint (V-2):** a positive L claim is BLOCKED
  only by PROVEN harm — task-success CI95 (L − A) entirely below
  −0.10. The non-inferiority margin −0.10 is reported descriptively
  (a soft-NI gate at −0.10 would be a coin flip at this CI width —
  power artifact, review V-2 analysis). Paralysis rate
  (trigger-absent episode share) per arm is a secondary.
- **Secondary contrasts (directional/descriptive, no MME machinery):**
  GOLD-L − A, NEUTRAL-L − A, L − GOLD-L, (stage 2) M − A, M+L − A,
  L − M; lesson-quality rubric (worker lesson vs gold class rule:
  correct/partial/wrong/vague).
- **Lesson-quality rubric mechanics (V-7):** executed BETWEEN the
  L-store freeze and the first consumer episode (blind-to-outcome is a
  property of the order, not a declaration); rater = non-executor
  agent + adjudication, recorded in an artifact.
- **Delivery-failure accounting (V-3):** a lesson rejected by the
  consumption gate is NEVER delivered; that class's L-episodes stay in
  the primary (conservative — L−A dilutes toward 0, which IS the
  result "extraction/delivery failed for this class"); a per-class
  delivery-status table is mandatory in the close-out; the
  localization matrix gains the cell "lesson not delivered → delivery
  failure ≠ abstraction failure".
- **Trigger-absent vs invalid (V-3/R-2c):** trigger-absent episodes
  are NOT invalid — they feed the paralysis secondary. "Invalid" =
  per-episode invariant violations only (journal completeness, sandbox
  state, budget overrun); invalid episodes are logged with cause,
  never silently re-run; >10% invalid in a cell → halt + owner gate.
- **Cluster eligibility minimum:** a cluster needs ≥3 trigger-eligible
  episodes per arm; otherwise the cluster is declared-out of the
  primary (recorded in a coverage table; never re-run, never re-tuned).
- **Analysis mechanics:** cluster percentile bootstrap 10k resamples,
  RNG seed 20261011 (the power artifact approximates at BOOT 4k —
  declared); sensitivity variants per the compound rule.

## 3. Sizing (power-results-plt.json v3, conservative row)

- CI-only reference (NOT the power of the decision): d .20 → 0.918;
  d .15 → 0.738; FP(d=0) 0.062.
- **The compound decision rule (claim threshold m = 0.20):** true
  effect 0.30 → conjunctive power **0.899**; 0.25 → 0.733; 0.20 →
  0.472 (the threshold is a median event at the MME — structural, not
  a bug); FP(d=0) → **0.002**. **MME = 0.30** (smallest 0.05-step
  true effect with conjunctive power ≥ 0.80).
- **Declared honest limitation:** effects in [0.20, 0.30) will usually
  resolve as directional, not established — that is the price of the
  claim discipline + class structure (two-level bootstrap CI width
  0.27 vs 0.19 flat). No design change can remove this without more
  classes (banned: taxonomy growth) or difficulty tuning (banned:
  escalation).
- Honesty rows: no effect heterogeneity lifts d .25 to 0.818
  (heterogeneity costs ~0.09); band-edge bases .30/.90 at d .15 →
  0.688/0.750; LOO-single-drop approx K20 d .20 → 0.858; rev-1 K15
  geometry d .20 → 0.792 (rejected); seed cut n=4 → 0.757 (**7 seeds
  required**). Planning base A-recurrence 0.60; pilot verifies the
  [0.3, 0.9] band per class.
- **Seed-variation check (operational, V-5):** if in >70% of pilot
  cluster-arm cells all 5 seeds give identical recurrence outcomes,
  effective-n is recomputed at cluster level and MME/power re-issued
  BEFORE the full run (owner-visible amendment).

## 4. Authoring phases (zero GPU) and freeze ORDER (binding)

1. **A1** harness (bounded file/command sandbox, journaled actions,
   per-episode invariants fail-closed) + experience simulator +
   experience histories: **≥3 per class (15+ total)**; failure
   derivable from the journal, never named; auto-lint bans class-name
   lexicon and imperative rule forms; human spot-check ≥3 histories
   per class recorded in an artifact.
2. **A2** deterministic checkers FC-1..FC-5 (journal-equality
   semantics) + dev validation: ≥20 labeled traces per class, labeler-1
   = implementer, labeler-2 = fresh non-executor agent, 100% agreement
   on class-defining events (or ≥0.95 + recorded error analysis); dev
   traces held out; checker code digested at freeze.
3. **A3** GOLD-L lessons authored from class rules; committed and
   digested **BEFORE any transfer instance exists** (own commit; the
   manifest order is the blindness proof).
4. **A4** transfer instances (5/class; different filenames, domain,
   identifiers, failure instance; same latent rule) + identifier
   disjointness matrix (automatic, all instances of a class) +
   NEUTRAL-L mechanical composition (length ±25%, imperative ban-list
   lint) + **experience↔transfer 6-gram contamination gate** (V-9).
5. **A5** analyzer FIRST among execution artifacts (self-test PASS;
   fail-closed on gate records; implements the compound rule,
   sensitivity variants, localization matrix, delivery-status and
   coverage tables) + run wrapper (per-episode budget: max_turns 80,
   max_total_tokens 250k, wall 1800 s; per-cell wall guard 4 h;
   resumable cell-seed dirs; invalid logging per §2).
   **A5-bis (V-9):** stub-consumer dry-run of the whole chain (all
   arms × classes: positional context delivery, journaling, checkers,
   analyzer end-to-end) + per-class synthetic known-answer traces
   (recurrence true/false; checker must match exactly).
6. **F** single EXEC FREEZE: digests of everything above + this prereg
   + the power artifact + the worker prompt + the consumption-gate
   module + dry-run/known-answer artifacts. Any post-start fix = halt
   + owner gate. "Cheap repair" bounded NOW: ≤1 session, no new
   module, no freeze-surface change.
7. **G** non-executor gate session (reviewer queue) before any GPU.

**GPU budget estimate (V-5/R-5):** pilot ≈ 90 episodes (G8B 60 + Q35
30) ≈ 2–5 h wall; stage 1 = 700 episodes ≈ 20–40 h wall; stage 2
conditional +350 ≈ 10–20 h. Resumable; may span sessions; re-estimated
at preflight from measured pilot latency (stage-2 convention).

## 5. Consumption gate (procedural, redefined — review R-6)

Every delivered lesson (worker AND gold) must pass: (i) surface-leak
ban — no identifier/filename/domain of ANY transfer instance (exact +
normalized, automatic); (ii) generic procedural lexicon explicitly
PERMITTED by design; (iii) no imperatives specific to a concrete
transfer step. Worker lessons additionally pass the frozen validator
(class-tagged; multi-trace support over the ≥3 histories of the
class). Fail-closed: a rejected lesson is never delivered (accounting
per §2 delivery-failure rule).

## 6. Execution phases (GPU) and gates

1. **Pilot (first GPU):** classes **FC-1, FC-3** × 3 instances × 5
   seeds; arms {A, GOLD-L} on G8B; screening criterion (NOT
   inference): baseline ∈ [0.3, 0.9] per class AND GOLD-L strictly
   lower in ≥1 class with **≥2 of the 15 class-episodes** (3
   instances × 5 seeds) flipping to non-recurrence. Pilot data
   EXCLUDED from primary (declared). Out-of-band pilot class →
   declared-out of the full run (class never edited); <3 classes in
   band → STOP (typology endpoint 3/5, reported). **Max ONE pilot
   repeat, only after owner gate, only for a diagnosed harness bug;
   any difficulty/class change = freeze CONT-006 outright.**
   **1b. Q35 consumer-selection branch (V-4):** GOLD-L on Q35, same
   geometry. If GOLD-L is dead on G8B (fails screening) AND alive on
   Q35 (passes the same screening) → **STOP before the full run +
   owner gate**: the result is consumer-capacity localization; the cap
   is spent on ~90 episodes, not 700. (This is a PRE-run stop, not a
   mid-run switch.)
2. **Worker pass (after pilot GO):** Q35 reflection over each class's
   experience histories (no access to transfer instances) → validator
   + consumption gate → **L-store frozen BEFORE any consumer episode**
   (digest manifest). The lesson-quality rubric runs between this
   freeze and the first consumer episode.
3. **Stage-1 run:** arms {A, L, GOLD-L, NEUTRAL-L} × 25 clusters × 7
   seeds = 700 episodes. **Per-class baseline band gate [0.3, 0.9] on
   the completed arm-A phase (V-6): ≥4 classes in band, else the
   primary is reported directional-only; ≤3 in band → STOP.**
   Out-of-band class → excluded from primary with declaration, never
   edited. Analyzer fail-closed on the gate record. Live telemetry
   gate before the analyzer.
4. **Stage-2 (mechanical criterion, V-11):** run iff (L − A) OR
   (GOLD-L − A) has CI95 entirely off zero in EITHER direction;
   **NEUTRAL-L − A does not trigger** (the arc's presence effect on
   neutral blocks must not open stage 2 without a live lesson
   channel). Criterion failed → no stage 2; stage-1 analysis stands.
5. **Analysis:** frozen analyzer only; verdicts per §2; exploratory
   tables labeled.
6. **Close-out (binding artifacts):** final synthesis; claims table
   (established / directional / unresolved / falsified-on-tested-
   scope); typology mapping observed-pattern → owner-review endpoints
   1–5; reusable-infrastructure inventory. Then freeze/archive per the
   exit criteria.

## 7. Non-goals (binding)

No v3p/v3q; no difficulty escalation anywhere (pilot, out-of-band, and
harness-fix branches included); no hosted models (experiment 2 is a
separate optional owner-gated replication); no taxonomy growth; no
confirmatory claims from the exploratory stage-2 report; no post-hoc
endpoint changes; consumer never switched mid-run; MME/MME-related
rules never re-derived after data.

## 8. Predictions registered (diagnostic branches)

Localization experiment: each outcome pattern maps to a pre-registered
conclusion (design §6 matrix + the delivery-failure cell). The single
direction that would claim the arc's original idea works: L−A benefit
meeting the compound rule with no proven task-success harm. Its
absence with a live GOLD channel localizes the failure to extraction;
with a dead GOLD channel (mid-band consumer, live delivery) it
falsifies the lessons idea on the tested scope. All five typology
endpoints are valid closings.
