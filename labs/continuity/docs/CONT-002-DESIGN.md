# CONT-002 design — state transfer across cores (2×2, R = ΔB/ΔA)

Status: DESIGN for pre-registration. Behavioral runs are **never autonomous**
(ROADMAP); they start only after the owner accepts
`docs/EVALUATION-PREP-CONT002.md`. Mechanics proven at M2b (5/5 checks,
`results/CONT-000/cont002-mechanics-20261001-225738/`): core-A learning →
state export (`continuity-memory-export` v1) → import into core B
(Qwen3.6-35B-A3B via local GGUF Modelfile, digest 8a0fd5da…) → renders into
B's context → traces re-validate. This design turns that plumbing into a
pre-registerable measurement.

## 1. Research question

When an agent's persistent state (episodic memory) is learned on core A and
imported into a different core B, **how much of the measured memory benefit
survives the core replacement?** Primary endpoint (inspirer's wording,
`docs/research-proposal.md:126`, verbatim):

> Let `S(X, state)` be a predeclared, independently scored held-out
> behavioral performance measure (higher is better). Define
> `ΔA = S(A, restored) − S(A, clean)` and
> `ΔB = S(B, restored) − S(B, clean)`. **Primary endpoint:
> retained-benefit ratio `R = ΔB / ΔA`**, estimating the share of measured
> learned-state benefit that survives core replacement. Pre-register
> aggregation, minimum meaningful `ΔA`, target ratio/uncertainty criterion
> and treatment of negative values. If `ΔA` is zero or too close to zero to
> support a stable ratio, label the primary endpoint non-estimable and report
> the two deltas with uncertainty as diagnostics; do not cherry-pick another
> denominator or claim successful transfer.

Operationalization: S(X, cell) = mean label-form probe **pass rate** over the
primary clusters × seeds in that cell (scoring rule frozen by reference:
SUITE-V3-DESIGN §3, `continuity.runner.extract_label`). Four cells per
cluster-seed:

| Cell | Core | Store at probe | Meaning |
| --- | --- | --- | --- |
| A+restored | granite-code:8b | own learned state, export→import round-trip | benefit on the learning core |
| A+clean | granite-code:8b | empty | A's no-memory baseline (guess band) |
| B+restored | Qwen3.6-35B-A3B | state imported from A | **transfer cell** |
| B+clean | Qwen3.6-35B-A3B | empty | B's no-memory baseline |

ΔA = S(A+restored) − S(A+clean); ΔB = S(B+restored) − S(B+clean); R = ΔB/ΔA.

**Symmetry decision:** A+restored uses the state **after an export→import
round-trip into a fresh store and fresh process**, not a continuous
continuation of the learning run. Both cores then receive the state through
the identical pipeline, so the contrast isolates the core, not the portability
machinery (matches the inspirer's "restored" wording; costs one extra process
spin-up per cluster-seed, zero extra learning passes).

**Execution shape (learn once, probe four ways):** per cluster c, seed s: the
learning sessions (sessions 1..k−1) run ONCE on core A, arm B (memory on);
the state is exported between session k−1 and session k; the held-out probe
session (session k, never seen during learning) runs in all four cells. Seeds
vary content via the predeclared per-seed variant table (cycle-2 lesson:
temp-0 seeds on byte-identical prompts are one observation; here every seed
renders different facts/codes, and the SAME learned state is probed on both
cores). Harness deltas needed at freeze time (additive, none this milestone):
session-subset execution (learn phase vs probe phase), probe-run store
preload from an export JSON, per-run model pinning (provider already takes a
model; M2b exercised it).

**Reading grid (pre-declared):** R ≈ 1 → state fully portable; R ≈ 0 → no
transfer; ΔB < 0 (R < 0) → state actively hurts core B. Negative values are
reported as-is, never clamped; the harm branch is a verdict of its own.

## 2. Family choice: delayed_recall + distractor_recall PRIMARY

Primary = **DR ×7 + DX ×8 = 15 clusters** (suite v3k, §3; sizing grounded in
the power artifact, §4). Declared choice
and why:

1. **Largest, cleanest memory benefit on core A — the denominator must be
   estimable.** Cycles 1–2 measured DR/DX pass ≈ 1.0 with memory vs 0.13–0.15
   without (arm-A sanity: error 0.82 without vs ~0.53–0.60 with on
   correction families — a benefit of ~0.25 vs ~0.85 here). The
   non-estimable clause is the design's main failure mode; DR/DX is the
   family pair that keeps ΔA far from zero by construction.
2. **The probe tests storage, not policy.** DR/DX probe = "which code did you
   log" — retrieving a stated fact. Correction/anchoring families (CR/CU)
   additionally exercise conflict-resolution behavior, where cycles 1–2
   showed memory can HURT (parroting D−C=+0.5015 cycle 1; anchoring
   persists on cr-clusters in cycle 2). Transferring harmful state, or
   transferring a conflict-resolution policy, is a different question —
   declared out of scope for the CONT-002 primary.
3. **Both cores stay on-task.** A label-form 6-option recall probe is
   core-agnostic; no core is asked to reproduce a granite-specific
   formatting habit.

CR/CU/RT are therefore NOT in v3k at all (lean suite, budget discipline);
guess_calibration stays (3 scenarios, 6 probes) because template §9 makes the
empirical guess rate mandatory next to family-level numbers — here it is
measured on BOTH cores (the two no-memory baselines are per-core
constructs). B+clean doubles as B's in-run guessing control for ΔB.

## 3. Suite v3k (protocol v3i as-is)

`fixtures/v3k/`, builder `experiments/suite-v3/build_v3k.py` (deterministic,
re-runs byte-identical). Fixture protocol v3i carried unchanged: label-form
probes with options (k=6), per-seed variant tables (values, codes, label
orders), validator V1–V16, fresh worlds, ids x-5xxx, predeclared seeds
{5001..5007}, texts disjoint from v1/v2/v2-cal/v3/v3h/v3i/v3j (validator V3
covers rendered texts of every seed).

- **dr-5301..5307** (delayed_recall ×7): learning s1 states a code + a
  NON-label companion fact (anti-echo, cycle-1 fix kept); s2 a chore turn;
  s3 ack + label-form probe (options k=6, expected = the code). Worlds:
  mountain cable-car stations, university chemistry stockroom.
- **dx-5401..5408** (distractor_recall ×8): learning s1 states two codes
  (target + lure); s2 chore; s3 probe the target with the lure in options.
  Worlds: theater props loft, quarry weighbridge office.
- **gc-5501..5503** (guess_calibration ×3): never-stated facts, 2 probes
  each (word + number), per-seed entities and per-seed 6-word option
  windows (7 seeds exceed 6 pure label rotations — the window keeps every
  seed's option set and order distinct); expected null. Worlds: orchard
  packing shed, brewery cellar, observatory dome. Run clean on both cores.

Scenario shape per primary cluster: 3 sessions, 4 turns (2 learning turns,
2 probe-session turns). 18 scenarios, 72 turns/seed. One probe per scenario,
last session, class `transfer_eligible` (the CONT-002 analogue of
`rm_eligible`; validator V11 extended per-suite).

Validator extension (`--suite v3k`): per-suite family plan (v3k has no
CR/CU/RT — V1/V7 expectations become suite-specific instead of the
CONT-005-hardcoded layout), CR-subtype expectation empty, and a recall-family
structural-eligibility check (V8R: expected value stated in a pre-probe
learning turn; DX lure in options; exactly one probe, last session) replacing
the trap/seed_error check that does not apply to recall primaries.
Regressions: v3/v3h/v3i/v3j must PASS byte-comparable verdicts after the
change.

## 4. Aggregation and decision rule (summary; binding text in the prereg)

- Unit: cluster = scenario. Per cell: cluster mean over its 7 seed-variant
  probes; ΔA_c, ΔB_c per cluster; ΔA, ΔB = cluster means; R = ΔB/ΔA.
- **Estimability gate (the inspirer's clause, numeric):** ΔA is estimable iff
  ΔA point estimate ≥ **0.30** (pre-registered minimum meaningful ΔA) AND its
  two-sided 95% cluster-bootstrap CI excludes 0. Otherwise the primary
  endpoint is **non-estimable** — report ΔA and ΔB with CIs as diagnostics,
  no ratio, no transfer claim, no alternative denominator.
- If estimable: R with two-sided 95% cluster percentile bootstrap
  (10,000-equivalent resamples over clusters, RNG seed frozen; degenerate
  draws with ΔA* ≤ 0.05 counted — if >10% of draws, the R CI carries an
  "unstable-denominator" flag). MME on R = **0.25** (a quarter of the
measured benefit is the smallest fraction that justifies importing state
as the default over re-telling the facts inline; same 0.25 convention as
the cycle-2 delta scale). **Power (artifact
`experiments/suite-v3/power-results-cont002.json`, `power_calc_cont002.py`,
seed 20261007):** at the conservative row (sig_shared 0.20, sig_int 0.10
both cores) detection power at MME = **0.801** (K15×7; the undersized
K12×5 alternative = 0.604, clusters-only K15×5 = 0.692, seeds-only
K12×7 = 0.735 — the sizing table is in the artifact). Stress rows: all-cell
si .15 → 0.767; B-side si .20 → 0.720 — the pilot GO/NO-GO attaches
pre-declared actions (spread re-check + owner sign-off) if measured spread
exceeds the conservative row. At true R the "established" branch
additionally requires the point estimate ≥ MME, bounding it near 0.5 AT
exactly the MME (0.477 in the artifact) — reported openly, never hidden
(cycle-2 house precedent). False-positive at R = 0: detection 0.033,
established 0.002. Harm at R = −0.25: 0.697. Guess-band coupling
(template §9): the implied ΔB at MME is R_MME × ΔA = 0.25 × 0.85 ≈ 0.21 >
0.15 at the design target ΔA ≈ 0.85; if the pilot-measured ΔA < 0.60, the
MME re-derivation executes at the pilot-gate checkpoint (after the frozen
pilot analysis, before any confirmatory inference, owner-visible) by the
frozen upward-only formula — see the prereg §5 (binding text; the freeze
itself precedes the pilot and is immutable).
- Verdict wording (frozen at freeze): retention established (CI > 0 and
  R ≥ 0.25) / retention below MME (CI > 0, R < 0.25) / harm established
  (CI < 0 — state actively hurts core B) / no confirmatory transfer
  difference established (CI includes 0) / non-estimable (gate fails).
  Two-sided, no post-hoc switch, secondaries never promoted.

## 5. B-core feasibility note (M2b traces, zero new inference)

Measured at M2b (`model-digests.json`, per-cell `summary.json`;
Qwen3.6-35B-A3B Q4_K_M, 22 GB, ~6.1 GB in VRAM under offload, Ollama 0.34.2):

| Quantity | M2b measurement |
| --- | --- |
| B model load + warmup | 39.6 s (once per process) |
| B+state probe turn (knows the answer, short reply) | 8.9 s (318 tokens) |
| B+clean probe turn (no record → rambles to the cap) | 73.5 s (2726 tokens ≈ num_predict 256 @ ~3.5 tok/s) |
| A learning session (1 turn) | 8.8 s incl. warm |
| A per-request (cycle-2 confirmatory, warm) | ~2.5 s avg |

Sizing the 2×2 (15 primary clusters × 7 seeds; A-side 102 turns/seed incl.
GC-A; B-side 72 turns/seed incl. GC-B):

- A-side (learn + A+restored + A+clean + GC-A): ~7–15 min/seed → **~50–105
  min GPU for 7 seeds**, one warm process per seed (PB-070).
- B-side: 504 turns total. The M2b 73.5 s ramble was a v1-era no-options
  "contains" probe; v3k probes are label-form WITH options, where an
  instruct-tuned core normally answers with one option (~10–20 s). Realistic
  mix: B+restored short replies, B+clean/GC-B compliant guesses with a
  minority of rambles to the cap → **~1.5–3 h typical**, ~4 h if no-record
  turns ramble to the cap half the time. Rambles are the honest no-record
  behavior of a verbose core under a fixed num_predict — data, not waste.
- Total estimate **~2.5–5 h GPU**; declared cap 5.5 h with wall guard; a
  pilot (2 seeds ≈ 45–85 min) measures the real wall-time before the full
  run. Primary-first execution order (A cells → B+restored → B+clean →
  GC-B); droppable-secondary order GC-B first (trimmable to seeds
  {5001..5004}, 24 probes, under budget pressure — pre-declared; further
  loss falls back to the design 1/k = 0.167 band with a caveat; the primary
  never depends on GC).

**Capability assumption (declared):** the 2×2 tolerates intrinsic capability
differences between cores BY DESIGN — R contrasts within-core deltas, so B
being slower/more verbose or intrinsically stronger/weaker shifts B+clean
but cancels in ΔB as long as the state, not the core, drives the delta. The
assumption B must satisfy is minimal: label-form compliance (reply with one
option) at a rate that does not floor B+restored; the pilot GO/NO-GO checks
exactly this (invalid-format decomposition on B cells). No assumption is
made about B's ability to LEARN (B never learns; it only reads imported
state) — a B-relearned control cell is out of scope (a fifth cell, ~+1 h
GPU; recorded as an open question, not a promise).

## 6. Contamination and independence stance

- Suite v3k is authored BEFORE any CONT-002 inference (this milestone,
  zero GPU); fixture-authoring exposure (the PR-REVIEW-v2 note-1 class) is
  acknowledged and mitigated the cycle-2 way: fresh worlds, independent gate
  review, no post-pilot fixture edits (any difficulty rebalance = a NEW
  suite + re-review, never a v3k edit).
- The pilot measures feasibility (wall-time, format compliance, ΔA size,
  spread); its 2 seeds {5001, 5002} are declared part of the final 7-seed
  dataset — the analysis code is frozen before any inference, so pilot data
  cannot contaminate the confirmatory analysis. The pilot GO/NO-GO criteria
  are frozen in the prereg; a NO-GO stops the arc at the owner gate, it does
  not trigger re-authoring.
- Non-executor gates (amendment d) use the standing reviewer queue
  (Fable → Opus → local GLM 5.3 Flash, owner directive 2026-10-07).

## 7. Out of scope (this milestone and the next)

No behavioral runs, no GPU (never-autonomous clause); no CONT-006 build (its
critical test 4 reuses this machinery AFTER CONT-002); no edits to frozen
CONT-005 artifacts, frozen-config-v2/v3a/v3b, closed suites, or
REFLECTION-V2-PROPOSAL.md and its review files.
