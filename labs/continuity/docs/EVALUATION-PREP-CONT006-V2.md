# EVALUATION-PREP-CONT006-V2 — CONT-006 rethink pre-registration (DRAFT, supersedes V1 for the rerun)

Status: **DRAFT for the RC-6 review chain** (implementer self-review →
Fable → co-owner → owner acceptance). Binding template:
docs/PREREG-REQUIREMENTS-V2.md (all 9 items + the five 2026-10-04
amendments; the V1 mapping carries over — see EVALUATION-PREP-CONT006.md
§10–§13 — except where amended below). Basis: docs/CONT-006-DESIGN-V2.md
(the rethink addendum), the CN-012 invalidation record, both independent
reviews, the owner decisions of 2026-10-09. **Behavioral inference remains
NEVER-AUTONOMOUS**: the owner accepts this V2 pre-registration before the
worker pass, calibration pilot, or any transfer run.

## Amendments to the V1 pre-registration (binding text)

### A.1 — Suite: fixtures/v3m (replaces v3l for every behavioral phase)

`fixtures/v3m` (builder `build_v3m.py`, deterministic; validator
`--suite v3m` PASS 20/20 + regressions v3/v3h/v3i/v3j/v3k/v3l PASS ×6;
fixture-validation-v3m.json committed; suite sha256 6c82a3710158fea9…).
Composition identical to V1's v3l description (15 TR + 4 VAL cr-7005/
cu-7105/rt-7204/dx-7403 + GC×3; ids x-7xxx; seeds {7001..7007} pre-
declared; texts disjoint from ALL prior suites incl. v3l — V3 every seed
both ways + V18 world-freshness, added at the RC-6 Fable fold: no v3m
scenario shares ≥4 rare content words or an opening 5-gram with ANY
prior-suite scenario; the first cut reused the planetarium (v3h) and
pottery-kiln (v3l) worlds — cu-7101/cu-7104 re-worlded to ropewalk/
tannery, cr-7005 decorations re-worded; the check is verified BOTH ways:
FAIL on the old fixtures naming all three collisions, PASS on the new). v3l and the entire invalid-chain record stay committed and
untouched; the invalid run is labeled (run-record header) as an
unregistered lessons-only ablation.

### A.2 — Memory discipline (CN-012 class killers; all mechanical, all live)

1. Single source of truth: `continuity.runner.MEMORY_ARMS`; the append
   branch and the run-script memory guard derive from it (no parallel arm
   lists — F-1/F-2/RC-1 folded; regression-tested by
   experiments/cont006/combined_channel_smoke.py, PASS ×5).
2. **Live-telemetry gate (binding order)**: before ANY analyzer reads a
   phase's results, `experiments/cont006/live_telemetry_gate.py --run-root
   <phase root>` must PASS (exit 0) over every canonical arm-seed trace:
   T1 appends > 0; T2 every injected episode ref resolves to an earlier
   append of the same scenario; T3 lesson arms render ≥ 1 block,
   non-lesson arms zero lessons.* events; T4 prompt_tokens ≤ num_ctx −
   512; T5 summary cross-check. Verified FAIL-CLOSED on the invalid run
   (20/20 traces flagged). The gate verdict file commits with the phase.
3. Arm-equivalence artifact (RC-3): experiments/cont006/
   arm-equivalence-audit.json (PASS) enters the freeze manifest; the
   review chain re-verifies its source checks.

### A.3 — Calibration pilot (new stage, before the store freeze and any transfer phase)

R0 + R2 × seeds {7001, 7002} on v3m WITH memory (~15 min GPU), after the
owner accepts this prereg and the worker v2 pass produces the R2 store
(the pilot's position in the chain: after worker v2 + R3 recap +
contamination gate, before Phase V — see A.6).
Pre-declared checks (computed by the frozen pilot machinery; GO required
for the transfer phases):
1. **Per-family headroom**: every TR family mean pass ∈ (0.15, 0.85) for
   BOTH R0 and R2 (cycle-2 discipline restored; V1's pooled-only ceiling
   gate is repealed).
2. **Anchor-divergence halt**: |R0 TR pass − 0.525| ≤ 0.15 (the C2
   memory-armed anchor; a larger divergence = halt & investigate — the
   invalid run printed 0.267 vs 0.525 with no criterion attached — F-3).
3. Live-telemetry gate PASS (A.2.2).
4. Label-form compliance < 0.30 invalid-share per arm; wall feasibility.
Out of band (1 or 2) → the chain STOPS; a NEW suite is authored (never a
v3m edit); owner consulted. In band → the calibration seeds are part of
the final dataset (single freeze; the analysis is frozen before the
confirmatory adds seeds — the CONT-002 pattern).

### A.4 — Worker v2 (multi-trace bundles; FIX-A/B become design)

Phase W re-runs over the SAME frozen corpus with bundles grouped by the
fixtures' ACTUAL family/sub-type (9 bundles × 12 scenario-runs —
cr-FP3a-vce/cr-FP3a-vct/cr-FP3b-euc/cr-FP3b-sc/cr-FP1-retraction/cu-FP1/
rt-FP2/dx-FP4/dr-FP5; fails-first with scenario-diversity interleave,
deterministic order; artifact experiments/cont006/worker_v2_bundles.json;
prompt = reflection_v2 WORKER_V2_PROMPT_TEMPLATE with the 5-part ref
format pinned by a worked example and an explicit preference for
substance over formatting lessons). Cross-trace support is cited by the
worker natively; §7.1(b) is satisfiable as designed (no post-hoc merge).
§7.1 rules otherwise unchanged; **FP-6 cap**: at most ONE format-
discipline lesson per store, keep-first in acceptance order (uniform for
R2 and R3; mechanically `continuity.reflection_v2.apply_class_cap`;
worker lessons carry a taxonomy `class` field REQUIRED by the prompt — a
candidate with a missing/invalid class is REJECTED as a schema violation,
fail-closed, so the cap cannot be bypassed by an untagged lesson; the cap
is mechanical over the worker's model-declared classification and is
declared as such; class-coverage telemetry is written with the store).
R3 gold lessons reused verbatim from the blind authoring
(protocol intact), capped 8 → 7 (declared classes in
experiments/cont006/gold-lesson-classes.json; recap artifact
experiments/cont006/r3-store-v2.json — LL-G-008 drops; the R3 candidate
list is in lessonId order, so list order == lessonId order there).

### A.5 — MME and the guessing band (V1 §5 amended)

**MME = 0.20 absolute** (restored; the 0.333 band re-derivation was a
small-n artifact of the invalid memoryless pilot). Power artifact:
experiments/suite-v3/power_calc_cont006_v2.py + power-results-cont006-
v2.json (seed 20261009; conservative row 0.871 at MME 0.20; sensitivity
b0 0.30/0.55/0.75 → 0.863/0.879/0.815; false-positive 0.040; ladder rows
kept). **Band reading (binding): caveat-only** — guess behavior is
arm-symmetric in the paired Δ contrast; the empirical band is reported
next to family numbers and NEVER moves the MME (no re-derivation
formula). Headroom-stop retained (calibration R0 > 0.75 pooled → owner).

### A.6 — Phases and gates (V1 §1/§12 amended)

Chain: owner accept V2 → freeze V2 (analysis scripts re-frozen for v3m
ids/seeds; live gate + audit + bundles + smoke in the manifest) → worker
v2 pass → R3 recap → contamination gate → calibration pilot (A.3) →
gate → Phase V (activation; S0 anchor-checked: |S0 − expected memory
base| > 0.15 → halt) → store freeze → Phase P pilot (BAD/GOLD-TRIV texts
reused; 4-gram check re-run against rendered v3m — PASS required) →
**live-telemetry gate** → frozen pilot analysis → pilot-gate checkpoint →
Phase C → **live-telemetry gate** → frozen confirmatory analysis →
verdict + run record (header carries: the CN-012 invalidation note, the
accidental-ablation label of the V1 chain, PW-OVERRIDE history, and the
V2 amendment list).

### A.7 — What V2 does NOT change

Arms R0/R1/R2/R3 and their definitions (R1 stays — with memory alive the
R1 ≤ R0 parroting-replication expectation is finally testable); the
primary endpoint Δ = S(R2) − S(R0) over 15 TR clusters; the four-branch
decision rule (frozen wording); §7.1 evidence-validation rules (except
the FP-6 cap); the activation rule (+0.05 store-level, fail-closed);
trigger strategy; R3 blind protocol; the counterfactual texts; template
items 1–9 and the five 2026-10-04 amendments (mapping per V1 §10–§13);
never-autonomous; Stage B (hosted models) = a separate future experiment,
out of scope here.

## Freeze manifest additions (V2)

Everything in V1's manifest PLUS: build_v3m.py, fixtures/v3m (+ 7 rendered
seed digests), fixture-validation-v3m.json, worker_v2_bundles.py +
worker_v2_bundles.json, src/continuity/reflection_v2.py (now carries the
V2 worker template, run_worker_v2, the class schema and apply_class_cap),
gold-lesson-classes.json, recap_r3_v2.py + r3-validation-v3.json +
r3-store-v2.json, live_telemetry_gate.py (incl. --self-test),
arm_equivalence_audit.py + .json, combined_channel_smoke.py,
check_counterfactual_lessons.py (v3l+v3m 4-gram scan),
power_calc_cont006_v2.py + power-results-cont006-v2.json, this document,
CONT-006-DESIGN-V2.md. V1's manifest stays untouched as the invalidated
chain's record.
