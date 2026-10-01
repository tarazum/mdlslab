# CONT-001 evaluation prep — pre-registration v1 (M6)

**Status: pre-registration v1 — exploratory data already seen by the author (M6);
confirmatory run uses only fresh held-out data per this plan.**

- Author: the M6 executor session (2026-10-01/02). The author has seen and
  committed ALL exploratory evidence cited in section 2 (M1–M5 mini-pilots and
  the M6 exploratory run). No confirmatory (held-out) data exists at the time
  of this commit, and none is generated in M6.
- Review: M6b (fresh session, `docs/PR-REVIEW.md`, GO/NO-GO) checks this plan
  against a fixed checklist BEFORE any confirmatory data exists.
- Execution: M7 (conditional on M6b GO) generates the held-out fixture v2 per
  section 6 and runs exactly this protocol. Every M7 artifact and LOG entry is
  labeled "agent-pre-registered, pending owner acceptance".
- This document is FROZEN at commit. If M6b demands a fix, M6b records a
  required change and verdict NO-GO; the author may then commit v2 of this
  plan before any confirmatory data exists.

## 1. Primary endpoint — repeated-mistake (RM) rate

Construct (verbatim from `docs/research-proposal.md` CONT-001): *"repeated-
mistake rate on task families previously encountered during the learning
sessions. Define a mistake as a repeated occurrence of an independently
labelled error category on a subsequent eligible task; denominator is the
number of eligible subsequent tasks, scored by a fixed evaluator blind to arm
identity where practical."*

### 1.1 Mechanical operationalization (defines the confirmatory computation)

For every RM-eligible scenario (fixture v2 marks them explicitly, see 6.2–6.4;
on the current v1 suite this maps to the `repeated_task` family):

1. **Initial answer** = the agent's normalized reply to the session-1 FIRST
   task turn (`s1t1`), which precedes the rubric/correction record.
2. **Initial error** = initial answer != `initial_expected` (the independently
   labelled correct category for that initial task; a fixture field in v2).
3. **Eligible subsequent task** = the scenario's probe, ONLY IF an initial
   error occurred. An agent that did not err cannot repeat its own mistake;
   the denominator is therefore **per-arm** (each arm's own eligible tasks),
   exactly as the proposal defines it.
4. **Repeated mistake (primary, strict)** = eligible AND the probe reply is
   incorrect AND the probe reply equals the agent's own initial answer
   (normalized) — the same independently labelled error category recurring.
5. **RM rate (arm)** = pooled strict repeated mistakes / pooled eligible
   subsequent tasks, over seeds x RM-eligible scenarios.
6. **Sensitivity (pre-declared, not primary)**: (a) loose variant — eligible
   AND probe incorrect, regardless of which wrong label; (b) common-eligible
   subset — only scenarios where BOTH contrasted arms erred initially.

Evaluator blindness: probe scoring and the RM classifier are deterministic
string comparisons in the committed harness (`runner.score_probe`,
`analyze_repeated_mistakes.py`); neither reads the arm field. Fixed and
arm-blind by construction.

### 1.2 Mapping on the current v1 suite (exploratory, stated for the record)

The v1 `repeated_task` family implements the schema above, except that
`initial_expected` is not a fixture field; it is derived from each scenario's
rubric sentence (author-derived, recorded once in
`analyze_repeated_mistakes.py`): rt-0001 `bug` (crash on export), rt-0002
`billing` (wrong VAT on invoice), rt-0003 `perf` (slow but working).

Measured in the M6 exploratory run (5 seeds/arm; strict RM, per-arm
denominators; `repeated-mistake-analysis.{json,md}` in the run dir):

| arm | eligible (pooled over 5 seeds) | repeated (strict) | RM rate |
| --- | --- | --- | --- |
| A | 10 | 5 | 0.500 |
| B | 10 | 10 | 1.000 |
| C | 10 | 10 | 1.000 |
| D | 10 | 10 | 1.000 |
| E | 10 | 10 | 1.000 |

### 1.3 Limits of the v1-suite operationalization (why the confirmatory run
needs fixture v2)

- **3-probe family**: rt-0001 is ineligible for every arm observed so far (no
  initial error), so the effective per-seed denominator is <= 2 scenarios.
  Five seeds give at most 10 eligible observations per arm — too coarse for a
  confirmatory claim. Fixture v2 raises the RM-eligible denominator to >= 7
  probes per seed (6.2).
- **CN-004 (rt-0003 option leakage)**: the probe turn lists `perf` among the
  label options, which is the expected answer; arm A passed it 5/5 with no
  memory of the rubric. This simultaneously inflates arm A and understates
  the memory arms' relative RM — the v1 exploratory contrast is CONFOUNDED in
  arm A's favor. Fixture v2 forbids option lists on probe turns (6.5).
- **Author-derived `initial_expected`** on v1 (v2 makes it a fixture field).
- **Own-answer anchoring (CN-007)** is the dominant observed mechanism behind
  B–E's RM = 1.000; the correction-and-reuse family (6.2) targets it and
  CN-008 directly.

## 2. Exploratory evidence the author has already seen (context, not inputs
to be re-estimated)

- M6 exploratory run `cont001-exploratory-20261002-000048` (arms A–E x seeds
  {11,22,33,44,55}, 650 requests, all seeds completed, spread 0.000 on every
  family and every arm; pilot consistency 170/170 outcome vectors identical
  to the M1–M5 pilots). Cross-arm per-family means: delayed_recall
  0/1/1/1/1; distractor_recall 0/1/1/1/1; contradiction_update 0/0.5/1/1/1;
  repeated_task 0.667/0.333/0.333/0.333/0.333; overall 0.2/0.7/0.8/0.8/0.8.
- RM rates (1.2): A 0.500 vs B–E 1.000 — on this leakaged, 2-scenario-
  denominator suite, persistent memory WORSENED strict repeated mistakes
  (anchoring), while arm A's advantage is an artifact of CN-004.
- CN-009: arm C–E self-model revision 1 was estimated on this same suite
  (arm-B pilot) — the confirmatory self-model must come from disjoint
  calibration scenarios (6.6).
- CN-010: arm E's policy never physically actuated on v1 (all probes are
  session-first turns; 24/24 retrieves were dedup no-ops; E ran token-identical
  to D) — fixture v2 moves probes off first turns and pre-declares the
  expected actuation count (6.5, 6.7).

## 3. Primary contrast and hypotheses

- **Primary contrast: RM(arm E) − RM(arm A)** on the held-out fixture v2
  suite. Arm E is the full continuity stack (memory + self-model +
  reflection + policy); arm A is the no-persistent-memory ablation. This is
  the proposal's "does Continuity matter" question in its strongest form.
- **Two-sided.** The exploratory phase showed the effect can plausibly go
  either direction (recall gains vs anchoring harm); a one-sided test would
  presume an answer the evidence does not support.
- H0: RM(E) = RM(A). The confirmatory claim is about the DIRECTION observed,
  reported as benefit (RM(E) < RM(A)) or harm (RM(E) > RM(A)).
- **Secondary contrasts (pre-declared, mechanism attribution, never
  promotable to primary claims)**: B−A, C−B, D−C, E−D on RM rate; delayed-
  recall and contradiction-update family pass rates for E−A and C−B; token
  cost per arm; arm-E policy actuation count vs expectation (6.7).

## 4. Minimum meaningful effect, thresholds, decision rule

- **Minimum meaningful effect (MME): |ΔRM| >= 0.15** (absolute). Rationale:
  the v2 RM-eligible denominator is >= 7 probes/seed (>= 35 pooled
  observations per arm over 5 seeds); 0.15 is just above one probe per seed
  (1/7 = 0.143) — the smallest difference that would mean anything at the
  per-run level rather than a single marginal probe flip. It is deliberately
  NOT the exploratory delta (0.5, measured on a confounded 2-scenario
  denominator).
- **Decision rule (frozen)**: the primary claim is supported iff BOTH
  (i) the two-sided 95% percentile bootstrap CI of RM(E) − RM(A) excludes 0,
  and (ii) |point estimate| >= MME. Otherwise: "no confirmatory difference
  established" — reported as such, whatever the direction of the point
  estimate. Alpha 0.05 (two-sided), single pre-declared primary contrast; no
  multiplicity correction is applied to the primary (there is exactly one);
  secondaries are reported with CIs and labeled exploratory-attribution, no
  threshold claims.
- **Underpowered guard**: if either arm's pooled eligible denominator is
  < 10, the primary analysis is reported as inconclusive (no claim), because
  the MME cannot be distinguished from probe granularity.
- **No post-hoc metric switching, no secondary promotion, no threshold
  adjustment after seeing held-out data.**

## 5. Aggregation and uncertainty

- **Point estimate**: per arm, RM rate pooled over seeds x RM-eligible
  scenarios (per-arm denominators per 1.1). Per-seed rates and their range
  are reported alongside. Δ = RM(E) − RM(A).
- **Uncertainty: paired cluster bootstrap over scenarios** (the exchangeable
  sampling unit), 10,000 resamples, percentile 95% CI, RNG seed 20261002
  (pre-declared). For each resample: draw n RM-eligible scenarios with
  replacement (n = number in the suite), recompute both arms' pooled RM
  rates on the SAME resampled scenario set (pairing preserves the
  matched-fixture design), Δ_b = RM_b(E) − RM_b(A). If a resample yields an
  empty eligible set for either arm, redraw it (redraws counted; if redraws
  exceed 5% of 10,000, eligibility is degenerate — reported, analysis
  halts).
- **Why scenarios (clusters) and not seeds as the resampling unit**: within-
  arm seed outcome spread was 0.000 on every family in every run measured to
  date — M1 arm A (5 seeds), M2–M5 mini-pilots, and the M6 exploratory run
  (25 seed-runs, spread 0.000 everywhere; `cross-arm-table.json`). Seed-level
  variation exists only at the token level (CN-003: e.g. arm D seeds 44/55
  differ by 38 tokens with identical outcomes). Bootstrapping over seeds
  would therefore produce degenerate zero-width intervals and fake
  precision; the scenario is the unit that actually varies. Seeds are
  replicates pooled within scenario (with 0.000 observed spread, pooling is
  exact to date; any outcome-affecting seed flip under v2 would show up in
  the reported per-seed spread and the redraw counter).

## 6. Held-out data plan for M7 (fixture v2 — REQUIRED properties)

M7 generates fixture v2 and the confirmatory run per this section. A
mechanical validation script (part of the M7 run scripts, committed BEFORE
any inference) enforces 6.1–6.6 on the frozen fixtures and writes its
verdict into the run artifacts; a failed check halts the run fail-closed.

1. **Fresh scenarios, fresh seeds** (never used in M1–M6, never used for any
   calibration): confirmatory seeds {101, 202, 303, 404, 505} (5, per
   docs/SIZING.md; disjoint from {11,22,33,44,55} and smoke seed 42). All
   scenario ids disjoint from v1. Synthetic, public-safe, manifest schema
   unchanged apart from the additive fields below (the v1 validator accepts
   extra fields — verified in M6).
2. **RM-eligible denominator >= 7 probes per seed**: >= 5 repeated-task-type
   scenarios AND >= 2 scenarios of a NEW **correction-and-reuse** family
   targeting the CN-007/CN-008 phenomena (agent's own initial answer is
   corrected by the environment; a later task requires REUSING the corrected
   knowledge on new content; probe scored against the corrected value).
   Recall families (delayed_recall, distractor_recall, contradiction_update)
   are included with >= 2 scenarios each so secondary endpoints remain
   computable; total suite >= 13 scenarios.
3. **`initial_expected` is an explicit fixture field** on the initial task
   turn of every RM-eligible scenario (independently labelled at
   authoring time; no author-derived mapping at analysis time).
4. **`probe.class = "rm_eligible"` marker** on RM probes (additive; the
   analysis selects probes by this marker, not by family name).
5. **No option leakage (CN-004)**: probe turns present NO closed label-option
   list (free-form answers, exact/contains scoring on normalized text).
   Option lists are permitted only on initial (pre-rubric) task turns.
   Mechanical check: probe-turn text must not enumerate label candidates.
6. **Probes NOT on session-first turns (CN-010)**: every RM-eligible probe is
   preceded by >= 1 non-probe environment turn in the same session, so the
   session-start baseline injection (query = first turn) differs from the
   probe-turn query. Mechanical check enforced by the fixture validator.
7. **Arm-E policy actuation, expected count stated ex ante (CN-010's explicit
   ask)**: with 6.6 in place, R1/R2 retrieves on probe turns are expected to
   surface episode ids not covered by the session-start injection.
   Pre-declared expectation: **>= 1 physical policy injection per seed**
   (physical = a `policy.action` event with `retrieval.injected = true`)
   across the suite. The count is recorded from the traces. If the observed
   physical-injection count is 0 for every seed, arm E is declared
   "actuation-inert on fixture v2", the E−D contrast is reported as a null
   increment WITH that caveat, and no policy-level claim is made — this
   outcome is a finding about the policy, not a silently-dropped endpoint.
8. **Self-model estimates from designated calibration scenarios only
   (CN-009)**: >= 3 calibration scenarios (families matched to the
   evaluation suite, content disjoint from BOTH the evaluation scenarios and
   v1) are run first on the pinned core; arm C–E revision-1' is estimated
   ONLY from that calibration run artifact (provenance recorded in the
   self-model store). No M1–M6 or pilot aggregate feeds the confirmatory
   self-model. In-run capability updates remain disabled (the reflection
   validator's double-count guard stays active); in-run failure-pattern
   rendering stays observed-answers-only (never expected answers).
9. **Freeze discipline**: fixture v2, seeds, self-model calibration artifact
   and this document are committed and their git rev recorded BEFORE the
   first confirmatory inference request. Any edit after the freeze halts the
   run. Budget: <= 3 h GPU for the whole confirmatory pass; if exceeded, STOP
   and record — no silent seed reduction (M7 brief).

## 7. Run configuration (identical to the M6 exploratory pass unless stated)

Model `granite-code:8b` pinned by digest prefix `36c3c3b9683b` via
`/api/ps` (CN-001 method); Ollama at `http://localhost:11434`; fail-closed on
server/digest mismatch. Temperature 0.0, num_ctx 4096, seed per run,
sampling options in every request (PB-071), keep_alive 30m; one warm process
per arm batch (PB-070); per-seed fresh memory store and per-run self-model
copies; shared GPU lock held around all inference
(`shared/tooling/agent-resource-coordination/`); scenario budgets and runner
code path unchanged from M6 (`labs/continuity/experiments/CONT-001/`).
Determinism caveat (PB-071/CN-003) travels with every claim: greedy+seed is
not a cross-backend guarantee.

## 8. Missing / failed-run handling (frozen)

- A seed-run with ANY of: budget stop, trace validation failure, or missing
  probe results → excluded from analysis and reported (exclusion list in the
  analysis JSON). No seed replacement, no threshold re-derivation.
- If more than 1 seed-run is excluded in any arm, OR any single scenario is
  missing in >= 3 of 5 seeds of any arm → the confirmatory analysis HALTS
  and is reported as inconclusive-with-cause (the protocol did not execute;
  no claim).
- Infrastructure failure BEFORE the first evaluation request of a seed-run
  (e.g., preflight/digest failure at process start): the affected seed may
  be re-run ONCE, with both attempts recorded; this is the only re-run
  allowed.
- Any contamination detected (fixture edited after freeze, calibration set
  overlapping evaluation ids, self-model provenance pointing at a non-
  calibration artifact) → halt, report, no claim.

## 9. Reporting

Analysis produces, under `results/CONT-001-confirmatory/<run_id>/`: per-arm
traces/summaries/aggregates (same layout as M6), the RM analysis with
bootstrap CI and decision-rule verdict, the cross-arm table, the fixture-v2
validation verdict, policy actuation counts, and a LOG entry — all labeled
"agent-pre-registered, pending owner acceptance". Owner accepts/rejects in
the morning list (ROADMAP). Interpretation of a supported claim is bounded
by: synthetic public-safe fixtures, one core model at temperature 0.0, and
the v2 suite's families — no external-validity claims beyond that.
