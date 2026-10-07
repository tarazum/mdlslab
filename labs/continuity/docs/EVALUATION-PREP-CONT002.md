# EVALUATION-PREP-CONT002 — CONT-002 state-transfer pre-registration (DRAFT, not frozen)

Status: **DRAFT for review.** Binding template: `docs/PREREG-REQUIREMENTS-V2.md`
(owner-adopted 2026-10-04; all 9 items — mapping in §10–§12). Design basis:
`docs/CONT-002-DESIGN.md`, the inspirer's clause (`docs/research-proposal.md`
CONT-002 section, quoted verbatim in the design §1), the M2b mechanics proof
(`results/CONT-000/cont002-mechanics-20261001-225738/`), and
`docs/EVALUATION-PREP-v3.md` as the structural template. Requires an
independent pre-registration review (PR-REVIEW-CONT002, non-executor session
from the standing queue: **Fable → Opus → local GLM 5.3 Flash**, owner
directive 2026-10-07) with verdict GO before FREEZE; the non-executor gates
before each inference stage use the same queue. **Behavioral runs are NEVER
AUTONOMOUS** (ROADMAP): the owner accepts this pre-registration before ANY
inference (the sole gate; after owner acceptance, pilot and confirmatory run
under the normal gate chain).

## 1. Experiment and cells

CONT-002 "state transfer across cores": **how much of a measured learned-state
benefit survives replacing the core the state was learned on?** Primary
endpoint (inspirer's wording, verbatim in design §1):
**R = ΔB/ΔA**, ΔA = S(A, restored) − S(A, clean), ΔB = S(B, restored) −
S(B, clean), S = mean label-form probe pass rate over the v3k primary set.

| Cell | Core | Store at probe |
| --- | --- | --- |
| A+restored | granite-code:8b (digest `36c3c3b9683b…`, CN-001) | own learned state via export→import into a fresh store/process |
| A+clean | granite-code:8b | empty |
| B+restored | Qwen3.6-35B-A3B `qwen36-35b-a3b:mdlslab` (digest `8a0fd5da454e…`, M2b) | state imported from A |
| B+clean | Qwen3.6-35B-A3B | empty |

Symmetry: BOTH restored cells receive the state through the identical
export→import pipeline (the contrast isolates the core, not the machinery).
Per cluster-seed: learning sessions (s1+s2) run ONCE on core A, arm B; state
exported between s2 and s3; the held-out probe session (s3) runs in all four
cells; the SAME state is probed on both cores. Seeds render different
content per the v3k variant table (cycle-2 lesson).

Fixed config: temperature 0.0; `num_ctx` 4096; `num_predict` 256 (CN-011);
sampling options in every request (PB-071); one warm process per core per
seed batch (PB-070); wall clock is the GPU metric (CN-002); shared GPU lock
held per run. Harness deltas (additive, frozen at FREEZE, before any v3k
inference): session-subset execution (learn phase / probe phase), probe-run
store preload from an export JSON, per-run model pinning.

## 2. Two-stage design: pilot (2 seeds) → confirmatory (7 seeds), ONE suite

Suite `fixtures/v3k` (authored BEFORE any CONT-002 inference; validator
V1–V16 PASS at this draft; committed `fixture-validation-v3k.json`): 18
scenarios — DR ×7 + DX ×8 = **15 primary clusters** (class
`transfer_eligible`) + GC ×3 (6 never-stated probes, measured clean on BOTH
cores). Seeds {5001..5007} predeclared; ids x-5xxx; fresh worlds; rendered
texts disjoint from all prior suites (V3). Family rationale and the 2×2
scenario shape: design §2–§3.

**Stage 1 — feasibility pilot on seeds {5001, 5002}** (all 15 clusters, all
four cells + GC on both cores). Predeclared GO/NO-GO (computed by the FROZEN
pilot analysis script, in the freeze manifest per template §1):

1. **B label-form compliance:** invalid-format share on B cells (both
   restored and clean) < 0.30 per cell. **Definition (frozen here, not in a
   script body):** invalid-format share = the share of probes whose reply
   yields ZERO or MORE-THAN-ONE distinct standalone label under
   `extract_label` (the format-miss category of the §8 decomposition);
   denominator 15 clusters × 2 pilot seeds = 30 probes per cell. A
   non-compliant B floors B+restored and voids the ratio's meaning → NO-GO
   to the owner gate (the prompt-template class of fixes is a declared
   owner-gate decision, never an in-place edit after inference).
2. **Wall-time feasibility:** extrapolated 7-seed total (per-cell means ×
   remaining seeds, reconciled per template §5) within the 5.5 h GPU cap;
   else the declared trims (GC-B to seeds {5001..5004}) are applied at the
   gate, or NO-GO. **Worst case, stated plainly (PR-REVIEW-CONT002 N-3):**
   if every no-record B turn rambles to the token cap (~42 turns/seed ×
   73.5 s), the B side alone reaches ~6.3 h — the cap is then exceeded and
   the GC-B trim (~40–45 min) does NOT close the gap; the backstop for the
   pathological worst case is NO-GO at this criterion, the trim covers only
   a moderate overrun.
3. **ΔA denominator size:** pilot ΔA ≥ 0.45 (n = 2 seeds, reported with its
   wide uncertainty) is the pilot GO floor for proceeding to the
   confirmatory at all (a feasibility judgement); ΔA < 0.30 additionally
   triggers the non-estimable risk declaration to the owner BEFORE the
   confirmatory (the run may still proceed for the diagnostic deltas —
   owner decision, recorded either way). **Threshold ladder, stated once:**
   0.30 = the pre-registered estimability-gate floor (§4); 0.45 = the pilot
   GO floor (run/no-run); 0.60 = the MME re-derivation trigger (§5). Every
   pilot-dependent adjustment executes at the **pilot-gate checkpoint** —
   after the frozen pilot analysis, before any confirmatory inference,
   owner-visible — never "at freeze" (the single FREEZE precedes the pilot;
   its parameters are immutable, PR-REVIEW-CONT002 RC-1).
4. **Spread report:** per-cell sd over the 2 pilot seeds is REPORTED, not
   gated (n=2 gates nothing); the freeze-time power re-check (§5) must clear
   the conservative row with the measured between-seed spread; if measured
   spread exceeds the stress rows, owner sign-off before the confirmatory
   (cycle-2 clause-2 pattern).

**Stage 2 — confirmatory on all 7 seeds {5001..5007}** (the 2 pilot seeds
are part of the final dataset — analysis code frozen before any inference,
so pilot data cannot contaminate the analysis; a NO-GO at stage 1 stops the
arc at the owner gate and never triggers re-authoring of v3k). NO post-pilot
fixture edits: any difficulty rebalance = a NEW suite + fresh review, never
a v3k edit (fixture-authoring exposure acknowledged per template §8;
mitigation = fresh worlds, disjointness V3, independent gate review).

## 3. Primary endpoint

**R = ΔB/ΔA** over the 15 primary clusters, label-form pass rate (1 − error;
v3 scoring per SUITE-V3-DESIGN §3, `continuity.runner.extract_label`,
digest recorded at freeze). Per cell: cluster mean over its 7 seed-variant
probes. ΔA_c = P(A+restored,c) − P(A+clean,c); ΔB_c = P(B+restored,c) −
P(B+clean,c); ΔA, ΔB = cluster means; R = ΔB/ΔA (ratio of cluster means,
never a mean of per-cluster ratios).

## 4. Primary contrast + estimability gate (the inspirer's clause)

ΔB vs ΔA is not an arm-vs-arm test; the pre-registered sequence is:

1. **Estimability gate:** ΔA point ≥ **0.30** (pre-registered minimum
   meaningful ΔA) AND the two-sided 95% cluster-bootstrap CI of ΔA excludes
   0 → proceed; otherwise the primary endpoint is **"non-estimable"** —
   report ΔA and ΔB with CIs as diagnostics; no ratio, no transfer claim, no
   alternative denominator (verbatim intent of the inspirer's clause).
2. If estimable: **R with a two-sided 95% cluster percentile bootstrap**
   over the 15 clusters (resample clusters with replacement; same resample
   indices reused for the ΔA CI and the R CI; RNG seed recorded at freeze;
   degenerate draws with |ΔA*| ≤ 0.05 counted — if >10% of draws the R CI
   carries an "unstable-denominator" flag and no "established" verdict is
   issued). **Degenerate-draw handling in the frozen script (N-4):** R* is
   computed for every draw with ΔA* ≠ 0; non-finite draws (ΔA* = 0) are
   excluded from the percentiles AND their count recorded in the run
   record; any occurrence is reported.

Direction pre-declared two-sided (R > 0 retention, R < 0 harm); no post-hoc
switch; negative values reported as-is, never clamped.

## 5. Minimum meaningful effect + power (template §6)

**MME on R = 0.25** (a quarter of the measured benefit is the smallest
fraction that justifies importing state as the default over re-telling the
facts inline; the 0.25 house convention). Power artifact:
`experiments/suite-v3/power-results-cont002.json` (`power_calc_cont002.py`,
sim RNG seed 20261007; K=15, 7 obs/cluster/cell; four-cell paired model:
eps shared per cluster-seed cancels within ΔA/ΔB and correlates them; eta
per cell is the power killer; bases bAs 0.90 / bAc 0.15 / bBc 0.17 →
latent ΔA 0.75; clip [0.02, 0.98]):

| Row | (sig_shared; sig_int) | detection power at R 0.25 |
| --- | --- | --- |
| binomial-equivalent | (0; 0) | 0.877 |
| **conservative (grounds MME)** | (0.20; 0.10) | **0.801** |
| stress all cells | (0.20; 0.15) | 0.767 |
| B-side stress | (0.20; A .10 / B .20) | 0.720 |

Sizing table (recorded): K12×5 = 0.604 (undersized), K15×5 = 0.692, K12×7 =
0.735, K15×7 = 0.801 — the design sits at the amendment-(c) cluster ceiling
with seeds carrying the rest. The "established" verdict additionally requires
the point estimate ≥ MME, bounding that branch near 0.5 at exactly the MME
(0.477 in the artifact) — declared openly (cycle-2 precedent; at R ≥ 0.5 the
branch rate is 1.000). False positive at R = 0: detection 0.033 /
established 0.002. Harm branch at R = −0.25: 0.697. Sensitivity: stronger B
baseline (bBc 0.30) 0.819; weaker ΔA 0.60 → 0.617 (declared limitation; the
pilot measures actual ΔA). **Pilot-gate power re-check (mandatory; runs at
the pilot-gate checkpoint, not at freeze — RC-1):** with the pilot-measured
ΔA and per-cell between-seed spread, the conservative row must still clear
0.75 detection at MME, else owner sign-off before the confirmatory
(stress-row governance, cycle-2 clause-2 pattern). Guess-band coupling
(template §9): MME-clearance is checked on the ΔB scale: implied ΔB at MME
= 0.25 × ΔA_measured must be ≥ 0.15 or ≥ 2× the larger core's measured
|guess − 1/6| deviation; at the design ΔA 0.85 → 0.21 ✓. **MME
re-derivation (pre-declared adjustment path, executes at the pilot-gate
checkpoint):** if the pilot-measured ΔA < 0.60, R_MME is re-derived by the
frozen formula
`R_MME' = max(0.25, max(0.15, 2 × band_max) / ΔA_measured)`
— the MME may move ONLY UPWARD (raising the bar is conservative; lowering
it on pilot data is prohibited and would void the verdict). Owner-visible,
pre-declared here with a fixed formula — not post-hoc flexibility
(PR-REVIEW-CONT002 RC-1).

## 6. Decision rule (frozen wording)

Evaluated in order; delta-freeze at FREEZE, no edits after any inference:
1. Estimability gate fails → **"primary endpoint non-estimable; deltas
   reported as diagnostics; no transfer claim"**.
2. R CI excludes 0 upward AND R ≥ 0.25 → **"retained benefit established
   (R = [point], 95% CI [lo, hi]): a quarter or more of the core-A memory
   benefit survives the core replacement"**.
3. R CI excludes 0 upward AND R < 0.25 → **"directional retention below the
   minimum meaningful effect; transfer detected but not established as
   meaningful"**.
4. R CI excludes 0 downward → **"state actively hurts core B (R = [point],
   95% CI [lo, hi])"**.
5. R CI includes 0 → **"no confirmatory transfer difference established"**.

Secondaries never promoted; direction stated plainly whichever way it points.

## 7. Aggregation, guards, missing-run handling

- Cluster = scenario (1 probe per cluster-seed per cell; 15 clusters × 7
  seeds × 4 cells = 420 primary probes). Seed-variant identity is part of
  the denominator: exactly the seeds {5001..5007} rendered by v3k, no
  re-draws.
- **Completeness guard:** all 15 × 7 × 4 primary cell-probes present; any
  missing cluster-seed-cell → verdict "incomplete" (no substitution).
  GC cells follow the droppable-secondary clause (§2 trims; incompleteness
  reported, never voids the primary).
- **State-integrity guard:** for every cluster-seed, the export digest
  imported into A+restored and B+restored must be byte-identical (recorded
  per run record; the SAME state file feeds both restored cells), and the
  export must contain zero probe-session content (learning sessions only —
  verified structurally by the gate session).
- **Variant-integrity guard:** `render_seed_variant` digest recorded at
  freeze; per-seed rendered suite digests recorded alongside the suite
  digest (every cell's exact prompt content reproducible from the manifest).
- Resume per the PB-075 pattern (zero repeated inference for completed
  cluster-seed-cells; every rev recorded). Exclusions: none, unless a
  fixture is proven invalid by the gate session (recorded with proof before
  results are read).

## 8. Secondaries (exploratory, not promotable)

- Per-family R (DR-only vs DX-only) and per-cluster Δ table — **ratios are
  computed and reported ONLY if the pooled estimability gate (§4) passed;
  in the non-estimable branch NO ratio of any kind is computed or reported,
  including per-family R** (the inspirer's clause bans alternative
  denominators — an R_DR published over a failed pooled gate is exactly
  that backdoor; PR-REVIEW-CONT002 RC-2). Per-cluster ΔA/ΔB tables are
  always reported (deltas, not ratios).
- ΔA and ΔB with their own CIs (always reported — they are the diagnostics
  of the non-estimable branch and the substance behind R).
- Invalid-format decomposition per cell (wrong-answer vs format-miss; the
  cycle-1 lesson that format non-compliance is not wrong memory).
- Empirical guess rate + position distribution per CORE (GC run clean;
  k = 6); B+clean vs the 1/6 band (is B's no-record behavior guessing or
  something else).
- Token cost per cell (the restored block is longer than clean context —
  the same budget-matching declaration as cycle 2: no length-matched control
  this cycle); wall-time per cell (feasibility follow-through, template §5).
- Harness telemetry: retrieval hits per restored cell (was the state
  actually rendered into context — the M2b check, at scale).

## 9. Scoring rule (frozen by reference)

The v3 label-extraction rule declared in SUITE-V3-DESIGN §3 on 2026-10-05
(standalone-label extraction; pass iff exactly one distinct label and it is
expected). Implementation `continuity.runner.extract_label`; digest recorded
at FREEZE.

## 10. Freeze manifest (template §1)

- **FREEZE (single freeze; the two stages share it — the pilot is not a
  separate freeze because its data is part of the final dataset and NO
  protocol parameter depends on pilot outcomes except the declared
  trim/re-derivation paths):** this document, `docs/CONT-002-DESIGN.md`,
  `fixtures/v3k` (suite digest + per-seed rendered digests),
  `validate_fixtures_v3.py` (v3k-extended), `build_v3k.py`, the run script
  (authoring at freeze: learn/probe split, store preload, per-cell model
  pinning, budget stops, wall-time accounting), the pilot GO/NO-GO analysis
  script AND the confirmatory analysis script (written FIRST, before any
  v3k inference — every analysis script the numbers pass through),
  `runner.py`, `provider.py`, `memory.py`, `fixtures.py`, predeclared seeds
  {5001..5007} + pilot subset {5001, 5002}. **Environment pin (N-5):** the
  Ollama version (M2b baseline: 0.34.2) and the core-B offload
  configuration are recorded in the freeze manifest and repeated in every
  run record — wall-time conclusions and ramble behavior are sensitive to
  them.
- Post-freeze edits to any frozen path = protocol violation, verdict void.
  The CONT-005 frozen artifacts and `frozen-config-v2/v3a/v3b.json` stay
  untouched as the historical record.

## 11. Infrastructure clause (template §2–§3, the c679547 lesson)

Enumerated in-place hotfix classes ONLY: provider telemetry aggregation over
nullable fields; path/argument prefixes; attempt-directory bookkeeping; the
bounded transient-retry wrapper. Rendering-related fixes (render function,
variant tables, run-script wiring) are legal ONLY before any inference of
the affected stage, with same-commit LOG entry and digest refresh. ANY
relaxation of a halt-gate or validator goes to the non-executor gate session
before results are read, and appears in the run record header. Multi-rev
execution pre-declared: every git rev of execution appears in the final
artifact header; "attempt counts and revs stated exactly"; per-cell wall
times reconcile across attempts (template §5) — cell totals = sum over
attempts, cluster totals = sum of cells, run total = sum of clusters per
core; offline-rebuilt summaries flagged `summary_rebuilt_offline`.

## 12. Gates (template §4), accounting (template §5), guessing band (template §9)

Fixture validation, freeze verification, contamination/independence checks,
and the state-integrity guard of §7: fresh non-executor sessions from the
standing queue (Fable → Opus → local GLM 5.3 Flash), verdict files committed
before any results summary is trusted. Concrete gate instructions:
re-run `validate_fixtures_v3.py --suite v3k` (V1–V16 incl. V8R and
rendered-text disjointness from ALL prior suites), verify freeze digests
independently, confirm the four-cell wiring (same export digest into both
restored cells; zero probe-session content in exports), confirm E10/V16
position rotation, and the **core-neutrality check** (the v3k analogue of
the cycle-2 arm-neutrality check): fixture texts must not reference either
core, the memory block format is the existing arm-B renderer byte-identical
for both cores, and no wording advantage can accrue to the core that
authored the state (the companion/lure facts are core-neutral). Two
additions per PR-REVIEW-CONT002 RC-4:
- **(a) Regression artifact, not self-attestation:** the gate session
  re-runs `validate_fixtures_v3.py --suite v3|v3h|v3i|v3j` with the
  v3k-extended validator and commits a NEW consolidated regression-verdict
  artifact (e.g. `fixture-validation-regressions-post-v3k.json`); the
  frozen per-suite `fixture-validation-*.json` records are never
  overwritten — executor-logged regression passes do not count as the gate
  (template §4; the committed pre-v3k verdicts predate the validator
  extension).
- **(b) Script verification:** the gate verifies that the frozen pilot
  GO/NO-GO and confirmatory analysis scripts implement §2/§4–§6 — minimum
  bar: a dry-run on synthetic input with a known answer (the v2-hotfix
  lesson) — and that the run script starts the A+clean and B+clean cells
  from a verified-empty store (cell isolation).
Wall-time
aggregates reconcile per §11. Guess band: empirical rate next to every
family-level number; the ΔB-scale MME clearance rule of §5; in-run caveat
"ΔB does not clear the guessing band" if ΔB < 2× max-core band — reported,
never used to move the MME. Every PR-REVIEW-CONT002 note reappears
(addressed or acknowledged) in the final run record (template §8);
explicitly carried: **N-1** (power-model caveats: ceiling compression of
the realized ΔA at bAs 0.90; shared-eps-across-cores assumption narrows
R's CI) beside every power number, and **N-2** (the pilot GO condition
ΔA ≥ 0.45 on seeds that stay in the final dataset induces a small upward
selection bias on ΔA — conservative for R, anti-conservative for the
estimability gate) in the run-record header.

## 13. Execution plan

Stage 0 (after owner acceptance + freeze + gate): pilot — seeds {5001,
5002}, primary-first order (A learn → A+restored → A+clean → B+restored →
B+clean → GC-A → GC-B), ~45–85 min GPU; pilot analysis (frozen script);
GO/NO-GO per §2 + freeze-time power re-check per §5. Stage 1: confirmatory —
remaining seeds {5003..5007} then the full-dataset analysis (frozen
script); est. 2–4.5 h GPU, cap 5.5 h, wall guard; artifacts under
`results/CONT-002-PILOT/` and `results/CONT-002-CONFIRMATORY/`. Budget stop
conditions per PROCESS.md rule 6; shared GPU lock held per run.

## 14. What this pre-registration does NOT claim

No CONT-005 reinterpretation (its record is closed); no claims beyond the
two pinned cores @ temp 0.0 on synthetic v3k content; no B-relearned
control (out of scope, recorded as an open question — a fifth cell, not a
promise); no claim that R generalizes to other core pairs (one pair is one
data point for the protocol, the same scope discipline as every lab
verdict); determinism caveat PB-071/CN-003 travels with every number; no
consciousness adjacency (README purpose clause); the T1-style budget-matching
limitation of §8 stands.
