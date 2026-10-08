# EVALUATION-PREP-CONT006 — CONT-006 lesson-extraction pre-registration (DRAFT, not frozen)

Status: **DRAFT for review.** Binding template: `docs/PREREG-REQUIREMENTS-V2.md`
(owner-adopted 2026-10-04; all 9 items — mapping in §11–§13). Design basis:
`docs/CONT-006-DESIGN.md`, `docs/REFLECTION-V2-PROPOSAL.md` (both reviews
folded), `docs/CONT006-TAXONOMY.md` (FROZEN 2026-10-08),
`experiments/cont006/experience-corpus-manifest.json` (sha256 e8e863b7…),
suite `fixtures/v3l` (validator PASS 18/18 + regressions v3..v3k PASS ×5),
`experiments/suite-v3/power-results-cont006.json`. Requires an independent
pre-registration review (PR-REVIEW-CONT006, fresh non-executor session from
the standing queue **Fable → Opus → local GLM 5.3 Flash**, owner directive
2026-10-07) with verdict GO before FREEZE; non-executor gates before each
inference stage use the same queue. **No inference of any kind is EVER
AUTONOMOUS** (ROADMAP never-autonomous clause): the owner accepts this
pre-registration before the worker pass, the validation phase, or any
transfer run.

## 1. Experiment, arms, phases

CONT-006 "Reflection as Lesson Extraction": **do evidence-validated lessons
from an asynchronous reflection worker improve held-out transfer on novel
scenarios with the same underlying failure patterns?** Arms (design §2):
R0 (persistent memory, no lessons), R1 (deterministic MVP
`src/continuity/reflection.py`, byte-stable), R2 (worker store through the
lesson channel), R3 (blind-authored gold lessons through the SAME
machinery). Working core granite-code:8b (`36c3c3b9683b…`, CN-001); R2
reflector qwen36-35b-a3b:mdlslab (`8a0fd5da454e…`, M2b), temp 0.0,
top-level `"think": false` pin in every request (inherited from
`OllamaProvider`; the owner-approved CONT-002 fix), sampling options in
every request (PB-071), `num_ctx` 4096, `num_predict` 256 (CN-011), one
warm process per core per seed batch (PB-070), wall clock is the GPU metric
(CN-002), shared GPU lock held per run.

Phases (each owner-visible; order is binding):

```
Phase W  worker pass (one batch over the frozen corpus) + evidence
         validation → evidence-validated stores; raw worker log committed
Phase G  R3 blind gold-lesson authoring (independent session, §8)
Phase V  activation: R0/R2/R3 on the 4 VALIDATION clusters, seeds
         {6001..6007} → frozen activation rule (§7.2) → ACTIVE stores
         committed + digested (store freeze — BEFORE any TR inference)
Phase P  pilot: seeds {6001,6002}; all four arms on TR+GC; plus the two
         counterfactual arms BAD and GOLD-TRIV on a predeclared subset
         (critical test 3); GO/NO-GO per §9
Phase C  confirmatory: all four arms, all 7 seeds, TR+GC; frozen analysis
```

## 2. Suite v3l, data split, two-phase rule

`fixtures/v3l` (authored BEFORE any CONT-006 inference; validator V1–V17
PASS at this draft; `fixture-validation-v3l.json` committed): 22 scenarios
— **15 primary transfer clusters** (CR×4 + CU×4 + RT×3 + DX×2 + DR×2,
class `transfer_eligible`, ids x-6xxx, fresh worlds, texts disjoint from
all prior suites — V3, every seed both ways) + **4 validation clusters**
(cr-6005, cu-6105, rt-6204, dx-6403; V17-pinned; activation decisions only,
never in the primary endpoint) + GC×3 (6 never-stated probes). Seeds
{6001..6007} predeclared (fresh); 103 turns/seed; per-seed variant tables
(label-form probes, k=6; scoring SUITE-V3-DESIGN §3,
`continuity.runner.extract_label`, digest at freeze). Experience corpus =
the 50 committed CONT-005-C2 arm-seed traces (v3i pilot 25 + v3j
confirmatory 25; digests + taxonomy labels in the corpus manifest).
**Two-phase rule:** no lesson injection during experience accumulation
(satisfied — corpus pre-committed; binding for any fresh supplement);
all arms share identical experience traces; no lesson is evaluated on its
generating scenario (fresh suite, mechanical disjointness).

## 3. Primary endpoint

**Δ = S(R2) − S(R0)** = difference of mean label-form probe pass rates over
the 15 primary transfer clusters (7 seed-variant probes per cluster per
arm; 15 × 7 × 2 = 210 primary probes). Per cluster c: Δ_c = mean-s S(R2,c)
− mean-s S(R0,c); Δ = mean-c Δ_c. The SAME rendered content is presented to
both arms per seed (paired at the cluster-seed level).

## 4. Decision rule (frozen wording)

Evaluated in order; two-sided 95% cluster percentile bootstrap over the 15
clusters (10,000-equivalent draws, RNG seed recorded at freeze; the same
resample indices used for any secondary CI computed in the same run
record):

1. CI of Δ excludes 0 upward AND Δ ≥ 0.20 → **"lesson transfer established
   (Δ = [point], 95% CI [lo, hi]): evidence-validated worker lessons
   improve held-out transfer by at least the minimum meaningful effect"**.
2. CI excludes 0 upward AND Δ < 0.20 → **"directional improvement below
   the minimum meaningful effect"**.
3. CI excludes 0 downward → **"lessons actively hurt transfer (Δ = [point],
   95% CI [lo, hi])"**.
4. CI includes 0 → **"no confirmatory difference established"**.

Direction pre-declared two-sided; negative values reported as-is, never
clamped; secondaries never promoted. R1 expectation declared ex ante:
R1 ≤ R0 replicates the CONT-001 parroting signal (secondary contrast; a
null R1−R0 is informative, not anomalous).

## 5. MME + power (template §6, §9)

**MME on Δ = 0.20 absolute pass-rate points.** Rationale (design §1):
effects smaller than 0.20 are not claimable at this design's power —
the MME ladder was sized at design time (zero GPU, before any inference):
Δ 0.15 → detection 0.650, 0.175 → 0.775, **0.20 → 0.862** (conservative
row, grounds the MME; undersized/record rows in the artifact). 0.20 also
clears the template §9 floor (MME ≥ 0.15). Power artifact:
`experiments/suite-v3/power-results-cont006.json` (`power_calc_cont006.py`,
sim RNG seed 20261008; K=15, 7 obs/cluster/arm; paired two-arm model:
eps shared per cluster-seed cancels inside Δ; eta per arm is the power
killer; b0 = 0.42 = the C2 T-arm pooled pass on primary families; clip
[0.02, 0.98]):

| Row | (sig_shared; sig_arm) | detection power at Δ 0.20 |
| --- | --- | --- |
| binomial-equivalent | (0; 0) | 0.845 |
| **conservative (grounds MME)** | (0.20; 0.10) | **0.862** |
| stress arm noise | (0.20; 0.15) | 0.848 |
| headroom edge (b0 0.75) | (0.20; 0.10) | 0.819 |

Sizing rows kept for the record: K15×5 = 0.763, K12×7 = 0.801 (both
under 0.862 — the K15×7 design stands at the amendment-(c) cluster ceiling
with seeds carrying the rest). Established-branch rate AT exactly the MME
≈ 0.45 (the branch additionally requires the point estimate ≥ MME —
bounded near 0.5 by construction, cycle-2/CONT-002 precedent, declared
openly; at Δ 0.30 — the gold-channel scale — 0.921). False positive at
Δ = 0: detection 0.038 / established 0.001. Harm at Δ = −0.15: 0.652.
Base sensitivities: b0 0.30 → 0.879, b0 0.55 → 0.869. **Pilot-gate power
re-check (mandatory; runs at the pilot-gate checkpoint with the
pilot-measured R0 base and per-arm spread):** the conservative row must
still clear 0.75 detection at the MME, else owner sign-off before the
confirmatory (stress-row governance, cycle-2 clause-2 pattern). **Headroom
stop (declared):** if pilot R0 pass on TR clusters > 0.75, an 0.20 delta
may be structurally unreachable → owner decision before the confirmatory
(no parameter moves automatically). **Guessing band (template §9):** the
empirical guess rate (GC run per arm; k = 6) is reported next to every
family-level number; MME 0.20 ≥ 0.15 floor ✓ and ≥ 2× any plausible band
deviation; in-run caveat "Δ does not clear the guessing band" is reported,
never used to move the MME.

## 6. Lesson-pipeline freeze discipline (proposal readiness checklist)

Everything below is digested in the freeze manifest BEFORE the phase that
uses it, and post-freeze edits to frozen paths = protocol violation
(template §1):

- **Taxonomy**: `docs/CONT006-TAXONOMY.md` frozen 2026-10-08 BEFORE lesson
  authoring and transfer-fixture authoring (ordering evidence: the corpus
  manifest embeds the taxonomy digest; V-manifest references it).
- **Experience corpus**: the corpus manifest (50 trace digests + class
  labels) committed before Phase W.
- **Worker (Phase W)**: reflector identity (model + runtime digest),
  temperature/sampling config, the FULL reflection prompt/template, the
  session-bundle assembly code; ONE batch pass; raw candidate log format
  (every candidate + rejection, prompt digest + response hash per call)
  committed before validation/transfer inference; telemetry DERIVED from
  the log (sessions_analyzed, sessions_with_candidates, candidate_lessons,
  accepted/duplicate/rejected breakdown, no_lesson_sessions).
- **Evidence validator + dedup + retrieval + renderer (code digests)**:
  the §7.1 rules implemented as a deterministic module; the renderer
  (prose block, ≤ 220 tokens) and the retrieval query rule; the anti-
  salience mechanical check (§7.1d).
- **Trigger strategy (frozen)**: post-experience single batch; comparisons
  are exploratory.
- **Active stores (store freeze, end of Phase V)**: R2-active and R3-active
  lesson stores COMMITTED + DIGESTED before the first transfer request;
  regeneration after transfer inference begins = protocol violation.
  Store-integrity guard: per arm, the store digest is byte-identical
  across all seeds and runs of that arm (recorded per run record).
- **Analysis code**: `analyze_pilot_cont006.py` (§9 GO/NO-GO) and
  `analyze_confirmatory_cont006.py` (§3–§4 verdict machinery) written
  FIRST, before any CONT-006 inference, with `--self-test` synthetic
  dry-runs (RC-4b pattern); digests in the freeze manifest.
- **Environment pin**: Ollama version (0.34.2 baseline) + reflector
  offload configuration recorded in the manifest and every run record
  (N-5 precedent).

## 7. Validation of lessons — the two meanings (design §5–§6)

### 7.1 Evidence validation (deterministic, pre-inference; applies to R2 AND R3 identically)

A candidate becomes `evidence-validated` iff ALL hold (machine-checkable,
pre-written): (a) every evidence ref resolves to a real event in a
committed corpus trace; (b) support ≥ 2 distinct sessions in ≥ 2 distinct
arm-seed traces; (c) dedup: Jaccard word-overlap < 0.70 vs every accepted
lesson (title + lesson text); (d) specificity/scope: ≤ 60 words, states an
applicability condition and a recommended behavior, and does NOT name
specific scenarios, ids, codes, label values or worlds (anti-salience +
anti-overfit; enforced mechanically by token checks against the suite
vocabularies and corpus label sets); (e) policy boundary: no permission,
safety, tool-authority or hidden-runtime changes. Rejected candidates stay
in the raw log with reasons. Human/model taste ("seems supported") is
never part of the automated path.

### 7.2 Generalization validation (frozen activation rule, Phase V)

Store-level, per source (R2 store and R3 store activated independently by
the SAME rule): S0 = R0 mean pass on the 4 validation clusters (7 seeds,
28 probes); SX = same for the lesson-carrying arm on identical rendered
content. Activate iff **SX − S0 ≥ +0.05** AND no validation probe is
missing or invalid (fail-closed missing-run handling). Do not activate on
SX − S0 < +0.05; record an active-harm signal if SX − S0 ≤ −0.05. If not
activated, the arm still runs the primary with an EMPTY active store
(declared branch; the honest verdict fires; §1 interpretation grid
carries the reading). Threshold is a weak directional bar BY DESIGN —
activation is a generalization/safety check, not a second endpoint.

## 8. R3 blind gold-lesson protocol

R3 lessons are authored in a separate session whose inputs are: the frozen
taxonomy, the corpus manifest + experience traces, the lesson schema and
the §7.1 validator contract. The authoring session must NOT see v3l
fixtures (any seed), transfer scenarios, or worker output; authoring
completes before the store freeze; the NON-EXECUTOR contamination gate
(§12) verifies the authoring session's input set. R3 lessons pass §7.1
and §7.2 identically.

## 9. Two-stage design: pilot (2 seeds) → confirmatory (7 seeds), ONE freeze

**Stage 1 — pilot, seeds {6001, 6002}.** All four arms on TR+GC (these
cells are part of the final dataset — analysis frozen before any
inference), plus counterfactual arms (excluded from the primary by
design): **BAD** = one plausible-but-wrong lesson (authored against the
taxonomy's FP-6 vector: a wrong formatting directive) injected through the
normal channel; **GOLD-TRIV** = one trivially-useful gold lesson (the
format-discipline rule) — both on the predeclared pilot subset
{cr-6001, cr-6003, rt-6201, rt-6202, cu-6101, dx-6401, dr-6301, gc-6501}
(format-heavy on purpose), seeds {6001, 6002}. Predeclared GO/NO-GO
(computed by the FROZEN pilot analysis script):

1. **BAD-lesson safety check (critical test 3a):** (i) NO probe reply in
   the BAD arm contains any verbatim contiguous ≥ 4-word span of the
   injected bad-lesson text (**parroting check** — definition frozen HERE,
   not in a script body: a "word" is a whitespace token, spans compared
   after lowercasing and stripping punctuation); AND (ii) BAD-arm pass
   rate on the pilot subset ≥ R0-subset pass − 0.10 (no catastrophic
   channel capture). Violation of (i) or (ii) → the channel's harm
   containment is questionable → NO-GO to the owner gate.
2. **GOLD-TRIV manipulation check (critical test 3b):** invalid-format
   share on the pilot subset improves by ≥ 0.10 absolute vs R0
   (invalid-format share = probes whose reply yields ZERO or MORE-THAN-ONE
   distinct standalone label under `extract_label`, the §14 decomposition;
   denominator = subset clusters × 2 pilot seeds). Failure → the delivery
   channel may be dead → owner gate BEFORE the confirmatory; combined
   stop: if BOTH stores failed activation (§7.2) AND this check fails,
   the confirmatory transfer run does NOT launch (channel-dead branch;
   owner decision recorded either way).
3. **Wall-time feasibility:** extrapolated 7-seed, 4-arm total (per-cell
   means × remaining seeds, reconciled per template §5) within the 5 h GPU
   cap, else the pre-declared GC trim (GC to seeds {6001..6004}) applies
   at the gate, or NO-GO. Worst case stated plainly: if every no-record
   turn rambles to the num_predict cap, granite-side walls grow ~2×;
   the backstop is NO-GO at this criterion, the trim covers only a
   moderate overrun (N-3 precedent).
4. **R0 headroom on TR:** pilot R0 pass ≤ 0.75 (else §5 headroom stop —
   owner decision, no automatic parameter move).
5. **Spread report:** per-arm sd over the 2 pilot seeds REPORTED, not
   gated; the §5 pilot-gate power re-check must clear 0.75 with the
   measured spread, else owner sign-off (stress-row governance).
6. **Label-form compliance:** invalid-format share < 0.30 per arm-cell
   (granite precedent: expected ~0.05–0.20 on classification probes).

NO post-pilot fixture edits: any difficulty rebalance = a NEW suite +
fresh review, never a v3l edit (fixture-authoring exposure acknowledged
per template §8; mitigation: fresh worlds, V3 disjointness, independent
gate review — the v3l author saw the taxonomy and the C2 corpus OUTCOME
RATES (pooled per-family fails) but no v3l authoring input derived from
any working-arm behavior on v3l itself).

**Stage 2 — confirmatory, seeds {6003..6007} ∪ pilot seeds = all 7**
(single freeze; the analysis is frozen before any inference so pilot data
cannot contaminate it).

## 10. Aggregation, guards, missing-run handling

- Cluster = scenario (1 probe per cluster-seed per arm). Completeness
  guard: all 15 × 7 × 4 primary cell-probes present; any missing
  cluster-seed-arm → verdict "incomplete" (no substitution). VAL probes:
  any missing → activation fail-closed (§7.2). GC follows the
  droppable-secondary clause (§9 trim; incompleteness reported, never
  voids the primary).
- **Store-integrity guard** (§6): per-arm store digest byte-identical
  across seeds/runs; retrieval telemetry per probe (was a lesson block
  rendered — the M2b check, at scale). For R2/R3 with an EMPTY store the
  telemetry must show zero rendered lesson blocks (mechanical).
- **Variant-integrity guard:** `render_seed_variant` digest at freeze;
  per-seed rendered suite digests in the manifest.
- Resume per PB-075 (zero repeated inference for completed
  cluster-seed-arms; every rev recorded). Exclusions: none, unless a
  fixture is proven invalid by the gate session (recorded with proof
  before results are read).

## 11. Freeze manifest (template §1–§3)

Single FREEZE before Phase W (the earliest inference of the experiment —
the worker pass), covering: this document, `docs/CONT-006-DESIGN.md`,
`docs/CONT006-TAXONOMY.md`, the corpus manifest + selector,
`fixtures/v3l` (suite digest + 7 rendered-seed digests),
`validate_fixtures_v3.py` (v3l-extended), `build_v3l.py`, the worker
module + prompt + session-bundle code, the evidence-validator/dedup/
retrieval/renderer module, the transfer run script (authoring at freeze:
arm configs, lesson-channel injection, store preload, budget stops,
wall-time accounting, per-arm store-digest pinning), BOTH analysis
scripts (with self-tests), `runner.py`, `provider.py`, `memory.py`,
`fixtures.py`, predeclared seeds {6001..6007} + pilot subset {6001,
6002} + the pilot counterfactual subset, `reflection.py` (R1 baseline —
byte-stability witness), environment pin. Post-freeze edits to frozen
paths = protocol violation, verdict void. Closed artifacts (CONT-001/
CONT-002/CONT-005, frozen-config-*, closed suites) stay untouched.
**Infrastructure clause (template §2):** enumerated in-place hotfix
classes ONLY (provider telemetry aggregation over nullable fields;
path/argument prefixes; attempt-directory bookkeeping; bounded
transient-retry wrapper); rendering-related fixes only before any
inference of the affected stage, with same-commit LOG entry + digest
refresh; ANY relaxation of a halt-gate or validator goes to the
non-executor gate session before results are read and appears in the run
record header. **Multi-rev (template §3):** every git rev of execution in
the final artifact header; attempt counts and revs stated exactly.

## 12. Gates (template §4), accounting (template §5), carried notes (template §8)

Non-executor sessions from the standing queue (Fable → Opus → local GLM
5.3 Flash), verdict files committed before any results summary is
trusted. Concrete gate instructions:

- **Fixture gate:** re-run `validate_fixtures_v3.py --suite v3l` AND the
  regressions `--suite v3|v3h|v3i|v3j|v3k` with the v3l-extended
  validator; commit a NEW consolidated regression-verdict artifact
  (frozen per-suite JSONs never overwritten; RC-4a precedent — the
  committed pre-v3l regression artifact predates the v3l extension).
- **Freeze gate:** independent digest re-hash of the whole manifest;
  verify the taxonomy digest embedded in the corpus manifest matches the
  committed taxonomy file; verify the store freeze ordering (store
  digests recorded before the first transfer request timestamp).
- **Contamination gate (before Phase V):** verify the R3 authoring
  session's inputs (experience-set only; no v3l content), the worker
  prompt's input set, and that no lesson text names v3l ids/labels
  (mechanical §7.1d check re-run independently).
- **Script verification (RC-4b):** the frozen pilot/confirmatory analysis
  scripts implement §4/§9 — minimum bar a dry-run on synthetic input with
  a known answer; the run script starts each arm from the pinned store
  digest (empty-store arms verified against a byte-empty store).
- **Wall-time reconciliation (template §5):** per-seed wall summed across
  all attempts; per-arm totals = sum of seeds; run total = sum of arms;
  offline-rebuilt summaries flagged `summary_rebuilt_offline`; budget
  compliance judged on reconciled totals.
- **Carried notes (template §8):** every PR-REVIEW-CONT006 note reappears
  addressed or acknowledged in the final run record. Pre-declared carried
  notes: **CN-A** power-model caveats (paired-eps assumption narrows Δ's
  CI; b0 anchored to C2 T-arms — if R0 behaves differently the realized
  power shifts; the pilot-gate re-check governs) beside every power
  number; **CN-B** the pilot GO criteria 1–2 condition the launch (not
  the estimate — no endpoint-value condition selects the dataset; the
  headroom criterion reads R0 only) — declared in the run-record header.

## 13. Execution plan

Phase 0 (after owner acceptance + freeze + fixture gate): **Phase W**
worker pass (~≤ 1 h GPU, qwen reflector) → raw log + telemetry; **Phase G**
R3 blind authoring (zero GPU); contamination gate. Phase 1: **Phase V**
validation/activation (R0/R2/R3 × 7 seeds × 4 VAL clusters, ~20 min) →
store freeze → freeze gate. Phase 2: **Phase P** pilot (seeds 6001, 6002;
4 arms TR+GC + BAD/GOLD-TRIV subsets; ~45–75 min) → frozen pilot analysis
→ pilot-gate checkpoint (GO/NO-GO + power re-check, owner-visible). Phase
3: **Phase C** confirmatory (remaining cells; est. 1.5–2.5 h GPU; cap 5 h
with wall guard) → frozen confirmatory analysis → verdict + run-record
header. Artifacts under `results/CONT-006-WORKER/`, `results/CONT-006-VAL/`,
`results/CONT-006-PILOT/`, `results/CONT-006-CONFIRMATORY/`. Budget stops
per PROCESS.md rule 6; shared GPU lock held per run. Bounded later stage
(critical test 4, separately gated): cross-model lesson transfer on the
CONT-002 four-cell machinery, predeclared subset (2 patterns × 2–3 seeds),
own budget, inspirer's non-estimable clause (ΔA gate, deltas-only in the
non-estimable branch).

## 14. Secondaries (exploratory, not promotable)

- R3 − R0 with CI (channel viability; the interpretation grid reads it
  together with the primary).
- R1 − R0 with CI (parroting replication expectation declared §4).
- Invalid-format decomposition per arm (wrong-answer vs format-miss; the
  cycle-1 lesson; the FP-6 window).
- Worker telemetry (candidates per session, accept/duplicate/reject
  breakdown, NO_LESSON rate; the "missing lessons" ambiguity made
  measurable).
- Per-taxonomy-class Δ table (FP-1/2/3a/3b/4/5 clusters; deltas, no
  ratio; class coverage 2–4 clusters each — descriptive only).
- Retrieval precision (lessons rendered per probe; rendered-but-ignored
  rate).
- Empirical guess rate + position distribution per arm (GC; k = 6).
- Token/latency cost of the lesson channel (budget-matching declaration:
  no length-matched control — the lesson block ADDS tokens; declared
  limitation, cycle-2 precedent).
- Activation-rule outcomes (§7.2 SX − S0 values; harm signals).

## 15. What this pre-registration does NOT claim

No reinterpretation of closed CONT-001/CONT-002/CONT-005 records; no
claims beyond the pinned cores @ temp 0.0 on synthetic v3l content and the
committed C2 experience corpus; no trigger-strategy, reflector-comparison
or broad cross-model claims (exploratory unless separately
pre-registered); no generalization of R2's raw-worker quality beyond what
the frozen evidence-validation rules operationalize; no claim that lessons
transfer across task domains beyond the taxonomy classes instantiated in
v3l; test 1 (lessons-only cell) not run; determinism caveat PB-071/CN-003
travels with every number; no consciousness adjacency (README purpose
clause).
