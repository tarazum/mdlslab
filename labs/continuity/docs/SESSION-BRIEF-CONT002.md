# Session brief — CONT-002 design + pre-registration draft (state transfer across cores)

For the NEXT working session (fresh context). This brief + the repo are the
complete state carrier; no conversation history is needed. House process:
`labs/continuity/PROCESS.md`; conventions and lessons: `LOG.md` tail.

## Entry conditions (verify `git status` clean on main at the current HEAD)

- CONT-005 CLOSED and accepted 2026-10-07 (ROADMAP "Owner decisions —
  recorded 2026-10-07"); CONT-006 proposal review cycle artifacts exist
  (`docs/review-reflection-v2-implementing-agent.md`,
  `docs/REVIEW-CONT006-PROPOSAL.md` — context only, NOT this milestone).
- Owner sequence decided 2026-10-07: **CONT-002 is the next arc**.
- The 2026-10-04 deferral condition ("label-form probes") is SATISFIED by
  the closed v3-protocol work (label-form probes, per-seed variant tables,
  headroom gates — all battle-tested in cycles 1-2).
- CONT-002 mechanics proven at M2b (5/5): core-A state export → import into
  core B (Qwen3.6-35B-A3B, already imported in Ollama) → renders into B's
  context; traces valid. `results/CONT-000/cont002-mechanics-*`.

## Scope (one milestone, ZERO GPU)

1. **Design doc `docs/CONT-002-DESIGN.md`**: the 2×2 — {core A
   (granite-code:8b, pinned), core B (Qwen3.6-35B-A3B)} × {state learned on
   A imported, clean}. Primary endpoint: **retained-benefit ratio
   R = ΔB/ΔA** (ΔA = memory benefit on core A = (A+state) − (A+clean); ΔB =
   imported-state benefit on core B = (B+state) − (B+clean)), with the
   inspirer's non-estimable clause verbatim (if ΔA ≈ 0, report deltas only,
   no denominator cherry-picking). Reading grid: R ≈ 1 → state fully
   portable; R ≈ 0 → no transfer; ΔB < 0 → state actively hurts core B.
   Address: which families are PRIMARY (candidates: delayed_recall /
   distractor_recall — cycle 2 showed the cleanest, largest memory benefit
   (1.0 vs 0.13-0.15); correction/anchoring families showed memory can
   HURT, which is a different question — declare the choice and why).
2. **Author suite v3k** (fixture protocol v3i as-is: per-seed variant
   tables, label-form probes, ids x-5xxx, fresh worlds, disjoint from all
   prior suites): learning-phase scenarios + held-out probe scenarios sized
   for the 2×2 (the state is learned ONCE per seed on core A, then the SAME
   state is probed on both cores — seeds vary content per the cycle-2
   lesson). Validator extension (`--suite v3k`) + regressions.
3. **Draft `docs/EVALUATION-PREP-CONT002.md`** per
   `docs/PREREG-REQUIREMENTS-V2.md` — all 9 items, ALL FIVE 2026-10-04
   amendments (frozen analysis code first, label-form probes, ≥12-15
   clusters, non-executor gates from the reviewer queue, wall-time
   accounting). Bootstrap design for R's CI over clusters (power calc
   artifact, extend the `power_calc_v3.py` pattern; model the paired
   structure explicitly).
4. **B-core feasibility note**: wall-clock per request on Qwen3.6-35B-A3B
   offload (from M2b traces), GPU budget per cell, and the B+clean capability
   baseline (the 2×2 tolerates intrinsic capability differences by design —
   state the assumption).

## Non-goals

- **No inference/GPU, no behavioral measurements** — CONT-002 behavioral
  runs are NEVER AUTONOMOUS (ROADMAP); they start only after the owner
  accepts the pre-registration.
- Do not touch frozen CONT-005 artifacts, frozen-config-v2/v3a/v3b, or the
  closed suites.
- Do not edit `docs/REFLECTION-V2-PROPOSAL.md` or its review files
  (CONT-006 line, owner/co-owner owned).

## Exit artifacts

`docs/CONT-002-DESIGN.md`, `fixtures/v3k/` (+ manifest), validator PASS
v3k + regressions v3/v3h/v3i/v3j, `docs/EVALUATION-PREP-CONT002.md` draft,
power artifact, LOG start+result notes, commit+push, Mnemosyne note.

## Budget

<= 110 min wall, 0 GPU. Fresh-session reading: this brief, PROCESS.md,
ROADMAP.md (M2b scope + Owner decisions), LOG.md tail (last 3 entries),
`docs/SESSION-BRIEF-v3i.md` (suite-authoring precedent),
`experiments/suite-v3/build_v3j.py` (builder pattern),
`results/CONT-000/cont002-mechanics-*` (what M2b proved).

## Chain after this milestone

Independent PR-REVIEW of EVALUATION-PREP-CONT002 (reviewer queue: Fable →
Opus → local GLM 5.3 Flash, per the 2026-10-07 directive) → fold → owner
gate (explicit go for the behavioral run) → freeze → gate → pilot →
confirmatory. Every GPU step owner-visible.

## Owner checkpoints

One: after the PR-REVIEW fold, the owner approves the pre-registration
before ANY behavioral run (never-autonomous clause).
