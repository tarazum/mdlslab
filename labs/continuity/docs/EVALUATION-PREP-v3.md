# EVALUATION-PREP-v3 — CONT-005 cycle-2 pre-registration (DRAFT, not frozen)

Status: **DRAFT for review.** Binding template: `docs/PREREG-REQUIREMENTS-V2.md`
(owner-adopted 2026-10-04; all 9 items — mapping in §10-§12 below). Design
basis: `docs/NEXT-CYCLE-NOTES.md` (owner-accepted 2026-10-06), the cycle-1
confirmatory record (`results/CONT-005-CONFIRMATORY/...123917/`), the Fable
audit (`docs/REVIEW-FABLE-RESULTS.md`), and `docs/EVALUATION-PREP-v2.md` as
the structural template. Requires an independent pre-registration review
(PR-REVIEW-v3, non-executor session) with verdict GO before FREEZE-A; the
non-executor gate before the confirmatory run is a Fable session (owner
directive 2026-10-05).

## 1. Experiment and arms

CONT-005 "Memory Trust Hierarchy", cycle 2: **does provenance metadata alone
(per-episode source/verification annotations) reduce repeated label errors?**
Primary candidate per the cycle-1 label-level re-analysis (T1 = the only
0/90 trap-repeat arm; tied-top overall score 0.45 with T3). Cycle-1 fixes
carried in: prose-parenthetical annotations (no bracket/pipe markup) and R5
numeric supersession (`claims.py` at 73f1d96+; gates re-run PASS).

| Arm | Memory behavior | Role |
| --- | --- | --- |
| A | none (session-local context only) | sanity anchor, not primary |
| T0 | flat episodic memory (arm-B renderer, byte-identical) | **primary baseline** |
| T1 | T0 + source/verification annotations | **primary treatment** |
| T2 | T1 + deterministic supersession + conflict resolution | secondary (post-fix) |
| T3 | T2 + trust-policy header + per-episode trust rank | secondary (post-fix) |

Fixed config: `granite-code:8b` pinned by digest prefix `36c3c3b9683b` (CN-001);
temperature 0.0; `num_ctx` 4096; `num_predict` 256 (CN-011); sampling options
in every request (PB-071); one warm process per arm-seed (PB-070); wall clock
is the GPU metric (CN-002); shared GPU lock held per run.

## 2. Two-stage design: pilot (suite v3i, frozen at FREEZE-A) -> confirmatory (held-out v3j, frozen at FREEZE-B)

**Stage 1 — headroom/spread pilot on `fixtures/v3i`** (authored, validator
V1-V16 PASS, assembly gate G1-G6 PASS with committed per-seed verdict files
for all five seeds at this draft), 27 scenarios, 128 turns/seed, primary
CR(8)+CU(4)=12 clusters. The v3i protocol extension — a predeclared per-seed
variant table (values, codes, probe label orders, names; seeds {2001..2005}
in the manifest) rendered by `continuity.fixtures.render_seed_variant` — makes
temperature-0.0 seeds true replicates (cycle-1 Fable audit: byte-identical
prompts made five seeds one run). CR sub-types are rebalanced toward T1's
source/verification surface (valid_environment 2, valid_tool 1,
erroneous_user 2, source_conflict 2, retraction 1); corrections explicitly
negate the superseded routing (the cycle-1 CR floor: both arms at 1.0 error
on 6/8 clusters); CU keeps the R5 supersession pattern with near-miss option
sets. Design note: the variant key and the sampler seed are the same integer
by design — at temp 0.0 the sampler seed is inert and both arms share the
rendered content, so content-vs-sampler effects cannot be separated in this
design and do not affect the paired contrast (PR-REVIEW-v3 N2).

Predeclared pilot GO/NO-GO for the confirmatory stage (all four required,
computed by the FROZEN pilot analysis script `analyze_pilot_v3.py` — in the
FREEZE-A manifest per template §1, not ad-hoc):
1. **Headroom, PER FAMILY (not pooled — a pooled mean passed the exact
   cycle-1 pathology: T0 pooled 0.50 = 6/8 CR at 1.0 + 4/4 CU at 0.0):** the
   CR family-mean (8 clusters) AND the CU family-mean (4 clusters) primary
   error strictly inside (0.15, 0.85) in BOTH primary arms. A floored or
   ceilinged FAMILY at pilot -> that family is rebalanced in v3j at FREEZE-B
   (declared openly, as the v2 cycle did) — never silently.
2. **Spread:** per-arm sd of the 5 per-seed primary means is reported with
   its n=5 (df=4) confidence interval, not a point estimate. If any primary
   arm's sd exceeds 0.25, the stress row (P4) of the power artifact governs
   and the owner signs off before FREEZE-B.
3. **Concentration:** the per-cluster report counts LIVE clusters (both
   primary arms' cluster error strictly inside (0.10, 0.90)). If fewer than
   8 of 12 are live, the P5 row of the power artifact (0.705 at 8/12, 0.578
   at 6/12) governs and the owner signs off before FREEZE-B — the P1/P3
   power claim assumes the effect is not concentrated below ~8 effective
   clusters.
4. **Residual echo:** no `[RESOLVED` substring in any T2/T3 answer and the
   per-arm invalid-format rate is reported; if the bracket flags echo
   (NEXT-CYCLE-NOTES residual risk), flags move to plain "NOTE:" prose at
   FREEZE-B (pre-authorized fix class, recorded in the run record).

**Stage 2 — confirmatory on held-out `fixtures/v3j`**: fresh content authored
at FREEZE-B under the v3i protocol (same family composition, same variant-table
mechanics, NEW predeclared seeds {3001..3005}; ids x-4xxx; texts disjoint from
v1/v2/v2-cal/v3/v3h/v3i — validator V3 covers rendered texts of every seed;
V15 identical-across-seeds turn share targeted at <= 0.45 — v3i sits at the
0.50 limit and a one-word edit must not flip the gate). Difficulty
calibration MAY use pilot per-sub-type rates (fixture-authoring exposure
acknowledged per template §8; mitigation = fresh content + independent gate
review incl. the arm-neutrality check of §12). FREEZE-B order (cycle-1
checklist): 1) analysis script FIRST, 2) author v3j, 3) validator
`--suite v3j` + assembly gate per seed, 4) digest manifest, 5) Fable
non-executor gate, 6) confirmatory run.

## 3. Primary endpoint

**Label-form error rate** (1 − pass, v3 extraction scoring per
SUITE-V3-DESIGN §3) over the 12 primary clusters (CR x8 + CU x4). Eligibility
is structural (identical denominators in every arm by construction). Per
cluster: mean error over its 5 seed-variant observations (5 seeds x 1 probe;
each seed renders different content per the variant table).

## 4. Primary contrast

**T0 − T1** (positive = annotations reduce errors). Direction pre-declared
two-sided; no post-hoc switch. Cycle-1 context declared: on v3h T1's primary
error was 0.60 vs T0 0.50 (T1 WORSE, leaky markup era) while T1 had zero
label-level trap repeats — the cycle-2 hypothesis is that the prose-annotation
fix plus the redesign flips the error-rate direction; the frozen wording below
covers both directions.

## 5. Minimum meaningful effect

**MME = 0.25.** Power artifact: `experiments/suite-v3/power-results-v3.json`
(`power_calc_v3.py`, seed 20261006; K=12, 5 obs/cluster, T0 fixed at the
design target 0.50; two-sided 95% cluster percentile bootstrap, REPS 3000 x
BOOT 4000). The NEW between-seed spread model (per arm a, cluster c, seed s):
p = clip(base + eps_s + eta[a,s]), eps_s = shared variant difficulty (same
rendered content in both arms — cancels in the paired delta; P2 confirms:
power 0.855 at delta 0.25, ~= binomial 0.844), eta = arm-specific variant
response (does NOT cancel — the power killer):

| Row | (sig_shared, sig_int) | delta 0.20 | delta 0.25 | delta 0.30 |
| --- | --- | --- | --- | --- |
 | P1 binomial-equivalent | (0, 0) | 0.655 | 0.844 | 0.939 |
 | P3 conservative (grounds MME) | (0.20, 0.10) | 0.670 | **0.842** | 0.930 |
 | P4 stress | (0.20, 0.15) | — | 0.810 | 0.919 |

Template §6 satisfied: power at MME = 0.842 (conservative), 0.810 (stress);
delta 0.20 rejected (0.670). Sensitivity: T0 0.64 -> 0.834; T0 0.40 -> 0.814.
Concentration caveat (P5): effect in 8/12 clusters -> 0.705, 6/12 -> 0.578 —
the power claim assumes the effect is not concentrated below ~8 effective
clusters; pilot GO/NO-GO clause 3 (live-cluster count) attaches the
pre-declared action to this caveat (P5 row governs + owner sign-off).
Substantive grounds: annotations are the cheapest trust intervention, but
adoption still changes the memory renderer for every future session; a
quarter fewer label errors on correction-bearing work is the smallest
difference that justifies that default. The spread values are DESIGN-PHASE
ASSUMPTIONS (zero v3i inference at drafting); the pilot measures them and
clause §2.2 governs the outcome.

## 6. Decision rule

Two-sided 95% cluster percentile bootstrap over the 12 clusters, 10,000
resamples, RNG seed recorded at FREEZE-B. Frozen wording (delta = T0 − T1):
- CI excludes 0 AND delta >= 0.25 → **"confirmatory difference established
  (annotations reduce errors)"**;
- CI excludes 0 AND delta <= −0.25 → **"confirmatory difference established
  in the reverse direction (annotations increase errors)"**;
- CI excludes 0 otherwise → **"directional difference below the minimum
  meaningful effect; not established as meaningful"**;
- CI includes 0 → **"no confirmatory difference established"**.
No promotion of secondaries; direction stated plainly whichever way it points.

## 7. Aggregation, guards, missing-run handling

- Cluster = scenario; per-arm-cluster error = mean over its 5 seed-variant
  probes. Seed-variant identity is part of the denominator: cluster c
  contributes exactly the observations rendered for seeds {3001..3005} in
  v3j, no re-draws.
- **Completeness guard:** all 12 clusters x 5 seeds in BOTH primary arms;
  any missing cluster-seed → verdict "incomplete" (no substitution). A/T2/T3
  and secondary families follow the droppable-secondary clause: their
  incompleteness is REPORTED and excludes them from secondary analysis, never
  voids the primary.
- **Variant-integrity guard (new):** the render function
  (`fixtures.render_seed_variant`) is frozen at FREEZE-B and its digest
  recorded; the per-seed rendered suite digests are recorded alongside the
  suite digest, so the exact prompt content of every arm-seed is reproducible
  from the manifest.
- Resume per the PB-075 pattern (zero repeated inference for completed
  arm-seeds; every rev recorded). Exclusions: none, unless a fixture is
  proven invalid by the gate session (recorded with proof before results are
  read).

## 8. Secondaries (exploratory-attribution, not promotable)

- **T2 vs T0 and T3 vs T0** after the two cycle-1 fixes (prose annotations;
  R5 supersession) — the cycle-1 primary contrast, re-measured post-fix.
- **Mandatory error decomposition on the primary set:** wrong-label vs
  invalid-format per arm (cycle 1: T0 13/60 invalid-format — format
  non-compliance is not wrong memory).
- **Label-level scripted-trap repeat rate** per arm (reply == the trap
  label; the cycle-1 T1 0/90 vs T0 15/90 finding this cycle tests properly).
- Between-seed spread report (per-arm sd of the 5 per-seed primary means,
  with its n=5/df=4 confidence interval) at BOTH stages — the measurement
  the power model assumed.
- DR/DX/RT family pass rates; per-arm guess rate and position distribution
  (the variant rotation should spread position; v3h's T0 max share 0.5 is the
  named risk being addressed); token cost per arm; CU superseded-value choice
  share inside options.
- **T1 budget-matching limitation, declared:** T1's annotated block is longer
  than T0's flat block (cycle-1 pilot: +21% prompt tokens for trust arms);
  a length-matched T0 control is OUT OF SCOPE this cycle (open question
  SUITE-V3-DESIGN §10.3). Token cost per arm is reported with every contrast.

## 9. Scoring rule (frozen by reference)

The v3 label-extraction rule declared in SUITE-V3-DESIGN §3 on 2026-10-05
(standalone-label extraction; pass iff exactly one distinct label and it is
expected). Implementation `continuity.runner.extract_label`; digest recorded
at FREEZE-B.

## 10. Freeze manifest (template §1)

- **FREEZE-A (before any v3i inference):** this document, `fixtures/v3i`
  (suite digest + per-seed rendered digests), `SUITE-V3-DESIGN.md`,
  `validate_fixtures_v3.py`, `assembly_gate.py`, `claims.py`, `runner.py`,
  `provider.py`, `fixtures.py`, the pilot run script AND the pilot GO/NO-GO
  analysis script `analyze_pilot_v3.py` (template §1: every analysis script
  the pilot numbers pass through is frozen with them), predeclared pilot
  seeds {2001..2005}.
- **FREEZE-B (before any v3j inference):** analysis script written FIRST,
  `fixtures/v3j` (+ per-seed rendered digests), predeclared confirmatory
  seeds {3001..3005}, refreshed digests of every frozen path above.
- Post-freeze edits to any frozen path = protocol violation, verdict void.
  The cycle-1 frozen artifacts and `frozen-config-v2.json` stay untouched as
  the historical record; cycle-2 freeze files are new artifacts.

## 11. Infrastructure clause (template §2-§3, the c679547 lesson)

Enumerated in-place hotfix classes ONLY: provider telemetry aggregation over
nullable fields; path/argument prefixes; attempt-directory bookkeeping; the
bounded transient-retry wrapper. Rendering-related fixes (render function,
variant tables) are legal ONLY before any inference of the affected stage,
with same-commit LOG entry and digest refresh. ANY relaxation of a halt-gate
or validator goes to the non-executor gate session before results are read,
and appears in the run record header. Multi-rev execution pre-declared: every
git rev of execution appears in the final artifact header; "attempt counts
and revs stated exactly".

## 12. Gates (template §4), accounting (template §5), guessing band (template §9)

Fixture validation, freeze verification, contamination/independence checks:
fresh non-executor sessions (Fable per owner directive), verdict files
committed before any results summary is trusted. Concrete gate instructions:
re-run `validate_fixtures_v3.py --suite v3j` (V1-V16, incl. variant checks
V14-V16 and rendered-text disjointness from ALL prior suites), assembly gate
per predeclared seed, verify freeze digests independently, confirm sub-type
balance and BOTH source-conflict orders, confirm E10/V16 position rotation,
and the **arm-neutrality check of v3j correction wordings** (the one channel
structural checks cannot catch): corrections must be phrased symmetrically
with respect to all arms' renderers — no wording that only an annotated
(T1+) memory block would surface (PR-REVIEW-v3 N1). Wall-time aggregates
reconcile across attempts (per-seed sums across all attempts; arm sums = run
total; `summary_rebuilt_offline` flags mandatory).
Guess-band rule (v2 operationalization, unchanged): in-run guess band per arm
= |guess_rate − 1/k| from that arm's guess-calibration probes (k = 6); if the
primary delta < 2 x max-arm band the verdict carries the caveat "primary
effect does not clear the guessing band" — reported, never used to move the
MME. **Design-time reading of template §9 (recorded per PR-REVIEW-v3 RC4):**
the template's baseline requirement "MME >= 0.15" is satisfied at design time
(0.25); its alternative arm "MME >= 2 x the measured deviation" is
operationalized per the v2 precedent (PR-REVIEW-v2 required change 4 ->
EVALUATION-PREP-v2 §12, accepted 2026-10-05) as a mandatory in-run caveat
rather than an MME veto — cycle 1's max-arm band was 0.333 (2x = 0.667,
inflated by degenerate seeds: 30 guess probes were effectively 6); the v3i
variant rotation is expected to compress it. Both facts travel into the final
run record; the owner may re-bind the template text at any time. Empirical
guess rate reported next to every family-level number. Every PR-REVIEW-v3
note reappears (addressed or acknowledged) in the final run record
(template §8).

## 13. Execution plan

Both stages: 5 arms x 5 seeds, primary-first order (T0 x5, T1 x5, then
A x5, T2 x5, T3 x5), full suite per arm-seed, ~128 turns/seed -> ~150 min
GPU per stage inside the 3 h cap with primary arms first so a budget overrun
can only trim secondary arms per the droppable-secondary clause. Budget stop
conditions per PROCESS.md rule 6; wall guard 170 min per stage. Pilot
artifacts under `results/CONT-005-C2-PILOT/`, confirmatory under
`results/CONT-005-C2-CONFIRMATORY/`.

## 14. What this pre-registration does NOT claim

No transfer claims (CONT-002 is separate, owner-gated); no claims beyond
granite-code:8b @ temp 0.0 on synthetic v3i/v3j content; determinism caveat
PB-071/CN-003 travels with every number; no consciousness adjacency (README
purpose clause); no T2/T3 claims (secondaries this cycle); the T1
budget-matching limitation of §8 stands.
