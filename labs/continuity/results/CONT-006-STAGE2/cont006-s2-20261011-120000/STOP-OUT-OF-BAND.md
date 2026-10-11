# STOP-OUT-OF-BAND — CONT-006 stage-2 execution halt (2026-10-11)

Pre-registered STOP branch fired. Owner decision required before any
further stage-2 work. This file is the halt record; the analyzer was
NOT run (it is fail-closed on gate-PASS.json, which was NOT written —
correct behavior under the stop).

## What ran (all under stage2-exec-freeze, digests verified at preflight)

- SMOKE PASS; PREFLIGHT PASS (26+12 digests, model pins 36c3c3b9683b /
  8a0fd5da454e, ollama 0.34.2, Q35 latency probes 3.3s / 2.9s).
- Phase 1 (G8B NONE, full scope): 7/7 seeds, 0 invalid.
  Baseline gate G8B: pooled primary 58/105 = 0.5524 ∈ [0.15, 0.85] — PASS.
- Phases 2–7 (G8B NEWF2/NEUTRAL/OLDG × probe_time/session_start): all
  7 cells × 7 seeds, 0 invalid, no wall-guard trips.
- Phase 8 (Q35 NONE, full scope): 7/7 seeds, 0 invalid.
  Baseline gate Q35: pooled primary **98/105 = 0.9333 > 0.85 — FAIL**.
  Formal re-invocation (--baseline-gate Q35) recorded in
  baseline-gate-Q35-STOP.json — same numbers, ok=false.
- Phases 9–14: NOT STARTED (halt per prereg §3 P0 / §5 step 4).
- --gate: NOT run (meaningless over an incomplete run by design).
- analyze_stage2.py: NOT run. stage2-results.json does not exist.

## The gate numbers (from summary.json per seed; data, not narrative)

Q35 NONE, pooled over 7 seeds, by family (all probes incl. VAL/GC):

| family                | G8B NONE | Q35 NONE |
|-----------------------|----------|----------|
| correction_reuse (cr) | 0.40     | **1.00** |
| repeated_task (rt)    | 0.32     | **1.00** |
| distractor_recall(dx) | 0.90     | 1.00     |
| delayed_recall (dr)   | 1.00     | 1.00     |
| contradiction_upd(cu) | 0.57     | 0.80     |
| guess_calibration(GC) | 0.00     | 0.00     |

PRIMARY pooled: G8B 58/105 = 0.5524 (in band); Q35 98/105 = 0.9333
(out of band, ceiling side). Q35 is at PERFECT 35/35 on cr and 28/28 on
rt across all seeds (temperature 0); only cu (0.80) retains any headroom.
GC pass 0/42 on BOTH models at NONE is a monitoring number (expected-null
probes), not a gate input — flagged here for the record.

## Why this fired (reading)

The v3o difficulty levers were calibrated to separate mid-band behavior
on the 8B (they do: G8B 0.32–0.90 across families, pooled 0.55). The
35B MoE solves the same v3o probes at ceiling on 4 of 5 primary
families. This is the pre-registered ceiling branch: with baseline at
0.93, lesson-induced DEGRADATION (the co-primary d_m = NEWF2@pt − NONE)
would be measurable in principle, but the band [0.35, 0.85] was declared
exactly to keep the NONE anchor away from ceiling/floor regimes; 0.9333
is far outside it. Per prereg §3 P0: "the v3o difficulty levers failed
(ceiling or floor); the stage halts; a NEW suite is authored, never a
v3o edit (v3m precedent, branch A.3)."

## What is salvageable / sealed

- The G8B block (phases 1–7) is complete and internally valid, and stays
  sealed: the frozen analyzer requires gate-PASS over the full run root
  (all 14 cells), so NO G8B-only analysis was performed. Whether to
  authorize a clearly-labeled exploratory G8B-only look (or keep sealed
  until a new Q35 suite completes the design) is an owner decision, not
  a default.
- No frozen file, verdict, or committed artifact was modified. Run
  artifacts (this root) committed as-is at halt.

## Options for the owner (not decisions — the branch is owner-gated)

A. Declared branch: author a NEW suite (v3p) with harder Q35-tier
   levers (cr/rt/cu need it; dr is ceiling on both models), re-prereg
   Q35 cells, keep G8B v3o cells as already executed or re-run all on
   v3p for a single-suite design.
B. Drop the Q35 arm of stage-2 (keep the arc 8B-only), analyze the
   completed G8B block under a prereg addendum.
C. Exploratory-only G8B analysis now (labeled, no verdict), Q35
   deferred to A.
D. Stop the stage here and fold the ceiling finding as a result
   ("v3o does not tax a 35B MoE at baseline" is itself a measured fact).

## Chain of custody

- run root: results/CONT-006-STAGE2/cont006-s2-20261011-120000
- console logs: phase-01-console.log, phases-02-07-console.log,
  phase-08-console.log; gate JSON: baseline-gate-Q35-STOP.json
- freeze manifests verified pre-run: stage2-freeze.json (26),
  stage2-exec-freeze.json (12)
