# EVALUATION-PREP-v2 — CONT-005 confirmatory pre-registration (DRAFT, not frozen)

Status: **DRAFT for review.** To be frozen (digest manifest committed) BEFORE any
held-out inference; requires an independent pre-registration review
(PR-REVIEW-v2, non-executor session) with verdict GO before execution. Binding
template: `docs/PREREG-REQUIREMENTS-V2.md` (owner-adopted 2026-10-04). Design
basis: `docs/SUITE-V3-DESIGN.md` + the headroom pilot run of record
(`results/CONT-005-PILOT/pilot-headroom-20261005-084818/`).

## 1. Experiment and arms

CONT-005 "Memory Trust Hierarchy" (`docs/research-proposal.md`), suite v3
(label-form probes, options at probe time, structural seed errors).

| Arm | Memory behavior | Role |
| --- | --- | --- |
| A | none (session-local context only) | sanity anchor, not primary |
| T0 | flat episodic memory (arm-B renderer, byte-identical) | **primary baseline** |
| T1 | T0 + source/verification annotations | secondary (metadata-only ablation) |
| T2 | T1 + deterministic supersession + conflict resolution | **primary treatment** |
| T3 | T2 + trust-policy header + per-episode trust rank | secondary |

Fixed config: `granite-code:8b` pinned by digest prefix `36c3c3b9683b` (CN-001);
temperature 0.0; `num_ctx` 4096; `num_predict` 256 (CN-011); sampling options in
every request (PB-071); one warm process per arm-seed (PB-070); wall clock is the
GPU metric (CN-002); shared GPU lock held for the run.

## 2. Held-out suite v3h (authored at freeze, before any v3h inference)

Fresh content under the v3 protocol, disjoint from v1/v2/v3-pilot (validator V3
runs against all prior suites):

- **Primary set — 12 clusters:** correction_reuse x8 (sub-types: valid_environment
  1, valid_tool 1, erroneous_user 2, retraction 2, source_conflict 2) +
  contradiction_update x4. Every primary scenario carries a structural seed_error
  (trap is a probe label, differs from expected, stated pre-probe).
  **Pilot-informed deviation from `SUITE-V3-DESIGN.md` §4.1, declared openly:**
  the design doc's primary was CR(8)+RT(6)=14; the pilot demoted RT (T2−T0 effect
  zero, family rates 0.333 both) and promoted CU (T2 1.0 vs 0.25) — recorded as
  design input #1 (LOG 2026-10-05). The validator is suite-parameterized
  accordingly (`--suite v3h`, primary expectation CR+CU=12; PR-REVIEW-v2
  required change 1).
- **Secondary — droppable on budget (recorded, never silent):** repeated_task x6,
  delayed_recall x3 (with the non-label companion-fact fix), distractor_recall x3.
- **guess_calibration** x3 scenarios / 6 never-stated probes; per-arm guess rate
  and position distribution are a mandatory report (template §9).
- Fresh seeds, predeclared and frozen NOW (no "candidate" ambiguity): the five
  confirmatory seeds are **{1001, 1002, 1003, 1004, 1005}**, recorded in the
  freeze manifest.
- Fixture-authoring exposure (the pilot's design inputs came from v3-pilot data):
  acknowledged per PR-REQUIREMENTS §8; mitigation = v3h content authored fresh,
  independent review of fixtures at the gate session.

## 3. Primary endpoint

**Label-form error rate** (1 − pass, v3 extraction scoring per
SUITE-V3-DESIGN §3) over the 12 primary clusters. Eligibility is structural
(identical denominators in every arm by construction — the v2 endogeneity flaw
does not exist here). Per cluster: mean error over its 5 seed-observations
(5 seeds x 1 probe).

## 4. Primary contrast

**T0 − T2** (positive = trust resolution reduces errors). Direction pre-declared
two-sided; no post-hoc switch.

## 5. Minimum meaningful effect

**MME = 0.25.** Power artifact: `experiments/suite-v3/power-results-v2.json`
(cluster percentile bootstrap, K=12, 5 obs/cluster, T0 error fixed at the pilot
estimate 0.64): delta 0.25 → power 0.812; delta 0.20 → 0.641 (rejected);
pilot-scale delta 0.36 → 0.983; effect concentrated in 8/12 clusters → 0.893.
Template §6 satisfied. Substantive grounds, not only power: a quarter fewer
errors on correction-bearing work is the smallest difference that would justify
adopting the trust-hierarchy machinery (its cost is real: +21% prompt tokens vs
T0 in the pilot); smaller improvements would not. Regression-to-the-mean risk is
acknowledged: the pilot delta 0.36 leans on a CU ceiling (T2 = 1.0 at n=12), so
an honest landing zone of 0.15–0.25 is plausible — the frozen wording below
covers it.

## 6. Decision rule

Two-sided 95% cluster percentile bootstrap over the 12 clusters, 10,000
resamples, RNG seed recorded at freeze. Verdict **"confirmatory difference
established"** iff BOTH (i) the CI excludes 0 AND (ii) the point estimate
delta >= MME 0.25. Frozen wording for every other landing zone: CI excludes 0
but delta < 0.25 → **"directional difference below the minimum meaningful
effect; not established as meaningful"**; CI includes 0 → "no confirmatory
difference established". No promotion of secondaries; direction stated plainly
whichever way it points.

## 7. Aggregation, guards, missing-run handling

- Cluster = scenario; per-arm-cluster error = mean over its 5 seed probes.
- **Completeness guard:** all 12 clusters x 5 seeds must contribute in BOTH
  primary arms; any missing cluster-seed → verdict "incomplete" (no substitution,
  no re-draw of seeds). Secondary arms (A/T1/T3) and secondary families follow
  the droppable-secondary clause instead: their incompleteness is REPORTED and
  excludes them from secondary analysis, but never voids the primary verdict.
- Resume per the PB-075 pattern is allowed (zero repeated inference for completed
  arm-seeds; every rev recorded).
- Exclusions: none, unless a fixture is proven invalid by the gate session
  (recorded with the proof before results are read).

## 8. Secondaries (exploratory-attribution, not promotable)

Strict scripted-trap repeat rate (pilot showed no headroom: 0/42 in T0/T2 —
reported for the record); **mandatory error decomposition on the primary set:
wrong-label vs invalid-format (zero or multiple labels) errors per arm** (the
pilot's T0 guess valid_fraction 0.667 means part of T0's "errors" may be format
non-compliance, not wrong memory — the decomposition must be in the run record);
DR/DX/RT family pass rates; T1 and T3 contrasts vs T0; per-arm guess rate and
position distribution (with the E10 rotation check of v3h at the fixture gate);
token cost per arm; the superseded-value choice share inside CU options.

## 9. Scoring rule (frozen by reference)

The v3 label-extraction rule declared in SUITE-V3-DESIGN §3 on 2026-10-05
(standalone-label extraction; pass iff exactly one distinct label and it is
expected). Implementation `continuity.runner.extract_label`; digest recorded at
freeze.

## 10. Freeze manifest (template §1)

Digests recorded at freeze for: fixtures v3h (suite digest), this document,
`docs/SUITE-V3-DESIGN.md` (the scoring rule lives in its §3 — frozen by
reference requires the referent frozen), predeclared seeds, the analysis script
(to be written before freeze and digested with it), `validate_fixtures_v3.py`,
`claims.py`, `runner.py`, `provider.py`. Post-freeze edits to any frozen path =
protocol violation, void verdict.

## 11. Infrastructure clause (template §2-§3, the c679547 lesson)

Enumerated in-place hotfix classes ONLY: provider telemetry aggregation over
nullable fields; path/argument prefixes; attempt-directory bookkeeping; the
bounded transient-retry wrapper. ANY relaxation of a halt-gate or validator goes
to the non-executor gate session before results are read, and appears in the run
record header. Multi-rev execution is pre-declared: every git rev of execution
appears in the final artifact header; "attempt counts and revs stated exactly".

## 12. Gates (template §4) and accounting (template §5)

Fixture validation, freeze verification, and contamination/independence checks
run by a fresh non-executor session with a committed verdict file BEFORE any
results summary is trusted. Concrete gate instructions (not "have a look"):
re-run `validate_fixtures_v3.py --suite v3h` (V1–V13 incl. disjointness from the
v3 pilot), verify the freeze digests, check sub-type balance and that BOTH
source-conflict orders appear in v3h, and confirm E10 position rotation. Every
PR-REVIEW-v2 note reappears (addressed or acknowledged) in the final run record
(template §8). Wall-time aggregates must reconcile across attempts (per-seed
sums across all attempts; arm sums = run total; `summary_rebuilt_offline` flags
mandatory).

**Guess-band rule (template §9, operationalized):** the in-run guess band per
arm is |guess_rate − 1/k| computed from that arm's own guess-calibration probes
(k = 6). If the PRIMARY delta < 2 x max-arm band, the verdict carries the
caveat "primary effect does not clear the guessing band" — reported, never used
to move the MME post hoc.

## 13. Execution plan

Primary-first order: T0 x5 seeds, T2 x5, then A x5, T1 x5, T3 x5 on the full
v3h (25 arm-seeds; ~130 turns/seed; ~2.45-3.8 s/request measured → ~150 min GPU,
inside the 3 h cap with primary arms first so a budget overrun can only trim
secondary arms per §2). Budget stop conditions per PROCESS.md rule 6; droppable
secondary clauses pre-declared.

## 14. What this pre-registration does NOT claim

No transfer claims (CONT-002 is a separate, owner-gated program); no claims
beyond granite-code:8b @ temp 0.0 on synthetic v3h content; determinism caveat
PB-071/CN-003 travels with every number; no consciousness adjacency (README
purpose clause).
