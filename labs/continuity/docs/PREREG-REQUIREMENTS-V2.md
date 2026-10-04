# Pre-registration requirements v2 — binding template for all future confirmatory runs

Owner-adopted 2026-10-04 (ROADMAP "Owner decisions" item 6). Every confirmatory
pre-registration in this lab (CONT-005 and later; CONT-002 behavioral when unblocked)
MUST satisfy this template in addition to everything v1 required
(`docs/EVALUATION-PREP.md` remains the frozen CONT-001 record; it is not edited).

## 1. Frozen analysis code (amendment a)

The freeze manifest records digests for fixtures, seeds, calibration data, the
pre-registration document, **and every analysis/scoring script the results pass
through**. Post-freeze edits to frozen paths are prohibited; infrastructure fixes
(runner, telemetry) follow §3. Analysis-logic changes after freeze = protocol
violation, recorded as such, verdict void.

## 2. Pre-registered infrastructure clause (lesson of `c679547`)

The pre-registration enumerates the *classes* of mid-run infrastructure failure that
may be fixed in place (e.g. telemetry aggregation over nullable fields, path
prefixes) and requires for each: a same-commit LOG entry, both attempt artifacts
preserved, and frozen-content digests re-verified. Anything outside the enumerated
classes — including any tolerance added to a halt-gate — goes to the non-executor
gate session (§4) before results are read, and is surfaced in the run record header,
not buried in a commit message.

## 3. Multi-rev execution must be pre-declared as a possibility

If a run legitimately spans >1 git revision (resume after crash), the resume manifest
records every rev, and the final verdict artifact carries the full rev list in its
header. "Both attempts" phrasing is banned; attempt counts and revs are stated
exactly.

## 4. Non-executor gates (amendment d)

Freeze verification, fixture validation (E-checks), and contamination/independence
checks are executed by a **fresh session that is not the run executor**, with its own
verdict file committed before any results summary is trusted. Executor self-attested
gate passes are recorded but never count as the gate (lesson: the resume manifest is
written by the same process it vouches for).

## 5. Wall-time and aggregate consistency (amendment e)

Run-record aggregates must reconcile: per-seed wall time summed **across all
attempts**, per-arm totals equal the sum of their seeds, and the run total equals the
sum of arms; offline-rebuilt summaries are flagged `summary_rebuilt_offline`. The
validator fails the record on any mismatch. Budget compliance is judged on the
reconciled totals (CN-002: wall clock is the GPU metric).

## 6. Power section mandatory (amendment c)

Every pre-registration states: cluster count, within-cluster observation count, the
design-phase power calculation artifact (method as in
`experiments/suite-v3/power_calc.py` or stronger), MME, and the power at MME. A run
whose MME is below its own detectable effect at ~80% power fails template review.

## 7. Droppable-secondary clause

Scenarios are ordered primary-first. If a budget cap forces trimming, only
pre-declared secondary clusters may be dropped, the trim is recorded in the run
record with the reason, and the primary set is untouchable. No silent reductions,
ever (v2 §scope rule, restated as a template requirement).

## 8. Carried-over review notes

Every non-blocking note a pre-registration review (PR-REVIEW-style) attaches to the
plan must re-appear, addressed or explicitly acknowledged, in the final run record —
notes do not evaporate (lesson: PR-REVIEW note 1's fixture-authoring exposure
statement never reached `results-summary.md`).

## 9. Guessing baseline reporting (amendment b, for label-form suites)

Label-form families report the empirical guess rate (guess-calibration subset,
validator E14) next to every family-level number, and the MME must clear the guessing
band (MME ≥ 0.15 or ≥ 2× the measured |guess − 1/k| deviation, whichever is larger).
