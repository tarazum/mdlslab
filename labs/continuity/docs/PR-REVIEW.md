# CONT-001 pre-registration review — M6b (GO/NO-GO)

- **Reviewer:** fresh M6b session (independent of the M6 author session; this
  review is the reviewer's only authored artifact besides LOG/ROADMAP status).
- **Document under review:** `docs/EVALUATION-PREP.md` — pre-registration v1,
  frozen at commit `a845fc5` (2026-10-02 00:29:28 +0300). Verified: `git diff
  a845fc5 HEAD -- …EVALUATION-PREP.md` is empty — the document is untouched
  since the freeze; commit order was exploratory results (`29df09e`) then
  pre-registration (`a845fc5`), with no held-out fixture v2 content in the
  repo (none exists yet — `fixtures/` contains only `v1`).
- **Method:** read the ROADMAP M6b brief, the pre-registration, the proposal's
  CONT-001/CONT-002 sections and CR discipline, LOG M6 entries, FINDINGS
  (CN-003/004/007/008/009/010), the exploratory artifacts
  (`cross-arm-table.{md,json}`, `repeated-mistake-analysis.{md,json}`,
  `pilot-consistency.json`), and the harness code itself
  (`src/continuity/runner.py`, `src/continuity/fixtures.py`,
  `experiments/CONT-001/analyze_repeated_mistakes.py`). Zero inference run.
- **Time check:** review completed 2026-10-02 ~00:45 FLEDT; arc deadline
  2026-10-02 11:30 FLEDT → **~10 h 45 min remaining**, comfortably above the
  2 h M7 margin. M7's time condition is currently satisfiable; the GO/NO-GO
  below is therefore the only remaining M7 gate.

## Verdict: **GO**

The pre-registration is executable by a fresh session without further design
decisions, its decision rule is symmetric and falsifiable, and it does not
reverse-engineer the exploratory result into guaranteed success. Three
non-blocking notes are recorded below; none requires changing the frozen plan.

## Checklist findings

### (a) Primary endpoint measurable; operationalization precise — PASS

- §1.1 gives a fully mechanical definition: initial answer = normalized reply
  to the session-1 first task turn (`s1t1`); initial error = answer !=
  `initial_expected`; eligible = initial error occurred (per-arm denominator);
  strict repeated mistake = eligible AND probe incorrect AND probe answer ==
  the agent's own initial answer (normalized); RM rate = strict repeats /
  eligible probes pooled over seeds x RM-eligible scenarios; loose and
  common-eligible variants pre-declared as sensitivities, not primaries.
- The harness implements every step deterministically and arm-blind. Verified
  in code, not just claimed: `runner.score_probe`
  (`src/continuity/runner.py:93-107`) normalizes (strip/lower/whitespace-
  collapse) and scores `exact_match`/`contains` against the fixture's expected
  string — it never reads the arm field; `analyze_repeated_mistakes.py`
  already performs the identical computation on v1 (its JSON rows expose
  `initial_answer`, `initial_expected`, `initial_error`, `eligible`,
  `repeated_mistake_strict/loose`), so a fresh executor scores identically by
  construction. The v2 deltas (select probes by `probe.class = "rm_eligible"`,
  read `initial_expected` from the fixture instead of the v1 hard-coded
  mapping) are mechanical edits specified by §6.3–6.4.
- Additive fixture fields are feasible: `fixtures._validate_scenario` checks
  required fields only and ignores unknown keys — the plan's "v1 validator
  accepts extra fields" claim re-verified independently.

### (b) Contrast / MME / thresholds falsifiable and not reverse-engineered;
direction honesty — PASS (the brief's emphasis case)

- Primary contrast fixed ex ante: RM(E) − RM(A), **two-sided** (§3), with
  secondaries enumerated and barred from promotion. Decision rule (§4):
  claim iff the 95% paired bootstrap CI excludes 0 AND |Δ̂| >= 0.15;
  otherwise "no confirmatory difference established". One primary, no
  multiplicity fudge, no post-hoc switching.
- **Direction honesty is explicit and correct.** §1.2/§2 record that the
  exploratory RM rate favors arm A (0.500 vs 1.000 for B–E), that this means
  persistent memory WORSENED strict repeated mistakes (anchoring), and that
  arm A's edge is partly the CN-004 leakage artifact — numbers cross-checked
  against `repeated-mistake-analysis.md` (A 5/10 = 0.500; B–E 10/10 = 1.000;
  identical in the JSON). §3 defines "success" as the symmetric rule and
  labels both outcomes in advance: benefit (RM(E) < RM(A)) or harm
  (RM(E) > RM(A)) — a negative-for-memory result is a legitimate confirmatory
  claim, not a failure to be spun.
- **Not reverse-engineered.** The MME 0.15 is derived from the v2 denominator
  granularity (just above 1/7 = 0.143, one probe per seed), explicitly NOT
  from the exploratory delta (0.5, measured on the confounded 2-scenario
  denominator). The rule cannot be tilted toward a memory-favorable outcome:
  removing the CN-004 leakage mechanically raises arm A's expected RM rate
  (leakage was letting A pass probes it would otherwise fail), which shrinks
  Δ toward 0 — the v2 design makes the memory-harm direction HARDER to keep,
  not easier. The mechanism-targeted correction-and-reuse family is openly
  declared as targeting CN-007/008 and is scored under the same symmetric
  rule. An underpowered guard (either arm's pooled eligible denominator < 10 →
  inconclusive, no claim) is pre-declared.
- Proposal compliance: this satisfies the CONT-001 requirement ("specify the
  primary contrast and minimum meaningful improvement … rather than selecting
  a favorable pair after observing outcomes") and the CR-2 primary-endpoint
  discipline; the endpoint text is quoted verbatim and operationalized, not
  redefined.

### (c) Aggregation and missing/failed-run handling fully defined — PASS

- §5: per-arm pooling with per-arm denominators, per-seed rates + range
  reported, Δ = RM(E) − RM(A); 10,000-resample percentile bootstrap, RNG seed
  20261002 pre-declared, paired over the SAME resampled scenario set; empty-
  eligible resamples redrawn, with a 5%-of-10,000 degeneracy halt.
- Bootstrap-unit choice is justified with measurement, not convenience: seed
  spread 0.000 on every family and arm across all runs to date (M1 arm A,
  M2–M5 pilots, 25 M6 seed-runs; `cross-arm-table.json` brackets all 0.000;
  CN-003 drift is token-level only — arm D/E seeds 44/55 +38 tokens, zero
  outcome changes). Seed-level resampling would yield degenerate zero-width
  CIs; scenario-level clustering is the unit that actually varies. Seeds are
  replicates pooled within scenario, with the caveat that any v2 outcome-level
  seed flip would surface in the reported per-seed spread and the redraw
  counter. Sound and stated.
- §8 covers every failure mode the brief lists: budget stop, trace-validation
  failure, or missing probe results → seed-run excluded and REPORTED (no
  replacement, no threshold re-derivation); > 1 excluded seed-run in any arm,
  or any single scenario missing in >= 3/5 seeds of any arm → analysis HALTS
  as inconclusive-with-cause; infrastructure failure BEFORE the first
  evaluation request → exactly one re-run, both attempts recorded;
  contamination (post-freeze fixture edit, calibration/evaluation overlap,
  wrong self-model provenance) → halt, no claim. §6.9 adds the GPU-cap stop
  rule (stop and record; no silent seed reduction).

### (d) Held-out plan disjoint from M6; M7 executable without further design
decisions — PASS

- Disjointness: confirmatory seeds {101,202,303,404,505} vs {11,22,33,44,55}
  and smoke 42; all scenario ids disjoint from v1; calibration scenarios
  disjoint from both evaluation scenarios and v1 (§6.1, §6.8).
- CN-004 → §6.5: NO closed option lists on probe turns, free-form
  exact/contains scoring; mechanical check that probe-turn text does not
  enumerate label candidates. Reviewer note: the v1 leakage is broader than
  rt-0003 alone — rt-0002's probe turn also carries an option list
  (`billing | bug | account`) with the expected answer among the options —
  so the blanket no-options rule is the correct fix, and it is what §6.5
  specifies.
- CN-010 → §6.6 (every RM-eligible probe preceded by >= 1 non-probe turn in
  the same session, mechanically enforced) and §6.7 (ex-ante expectation:
  >= 1 physical policy injection per seed, counted from traces; a
  zero-actuation outcome is pre-declared as "actuation-inert" with a
  null-increment E−D report — an outcome, not a hole in the plan). Fixture
  topology, not harness constraints, caused v1's inertness, so non-first-turn
  probes require no runner redesign.
- CN-009 → §6.8: revision-1' estimated ONLY from >= 3 designated calibration
  scenarios with provenance recorded in the self-model store; in-run
  capability updates stay disabled; failure-pattern rendering stays
  observed-answers-only; §8 halts on provenance violations.
- CN-007/008 → §6.2: >= 2 scenarios of a new correction-and-reuse family
  (own initial answer corrected by the environment; later task reuses the
  corrected knowledge on NEW content; probe scored against the corrected
  value), included in the >= 7 RM-eligible probes per seed.
- Executability: suite composition (>= 13 scenarios: >= 5 repeated-task-type
  + >= 2 correction-and-reuse + >= 2 each recall family), seeds, run config
  (§7 — model/digest/temperature/context identical to M6), MME, bootstrap,
  decision rule, missing-run policy, freeze discipline and the pre-inference
  mechanical validator for §6.1–6.6 are all pinned. What remains for M7 is
  content generation inside fixed templates, not design decisions.

### (e) "Exploratory data already seen" labeling; residual leakage — PASS
with one note

- Labeling is exemplary: the document header declares the author saw ALL
  exploratory evidence; §2 enumerates it (M1–M5 pilots + the M6 run) as
  context, not re-estimation inputs; every exploratory artifact and the
  cross-arm table are labeled EXPLORATORY, NOT confirmatory; the freeze/
  amend protocol (NO-GO → author v2 before confirmatory data exists) is
  stated.
- Known leakage channels are each closed and mechanically checked: CN-004
  (§6.5), CN-009 (§6.8 + provenance halt), calibration/evaluation id overlap
  (§8), post-freeze edits (§6.9). Numbers in the plan match the artifacts
  (RM table, family means, spread 0.000, pilot consistency 170/170).
- Residual leakage not fully eliminated (see note 1) — inherent to the
  agent-pre-registered setting, bounded by the symmetric rule and the owner
  acceptance gate.

## Non-blocking notes (no change to the frozen plan required)

1. **Fixture-authoring exposure (residual, unstated in the plan).** Whoever
   authors fixture v2 in M7 will have read the exploratory results; content
   selection could unconsciously favor the expected effect direction. This
   risk is not explicitly named in the plan. It is accepted here because the
   decision rule is symmetric (either direction is a claim), the mechanical
   validator blocks the known leakage channels, freeze discipline blocks
   post-hoc edits, and the owner acceptance gate sits on top. Recommended:
   the M7 run record should state this residual explicitly.
2. **Strict-RM comparator under free-form probes.** "Probe reply equals the
   agent's own initial answer (normalized)" is full-string equality after
   strip/lower/whitespace-collapse. With probe options removed (correctly),
   v2 probe prompts should elicit concise label-form answers (as v1's do) or
   strict equality will under-count category repetitions. Not a validity
   defect: the loose variant (any incorrect probe answer) is pre-declared as
   sensitivity (a), so degradation would be visible, never silent.
3. **Pin "initial task turn = s1t1" in the validator.** §1.1 defines the
   initial answer at s1t1 and §6.3 puts `initial_expected` "on the initial
   task turn"; the natural (and only consistent) reading is that they are the
   same turn. The M7 fixture validator — which the plan already requires —
   should enforce that the `initial_expected`-bearing turn is exactly
   session 1 turn 1 of every RM-eligible scenario.

## M7 conditions (recorded per the brief)

- M6b verdict GO: yes (this document).
- Time: as of review completion (~00:45 FLEDT, 2026-10-02) ≈ 10 h 45 min
  remain before the 11:30 FLEDT arc deadline — the ">= 2 h before deadline"
  condition holds with large margin. **M7 is currently satisfiable and may
  proceed** under its own brief (frozen protocol, held-out fixture v2,
  "agent-pre-registered, pending owner acceptance" labels).
