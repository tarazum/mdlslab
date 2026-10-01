# CONT-001 exploratory — cross-arm table (M6)

- run `cont001-exploratory-20261002-000048` (exploratory; NOT confirmatory)
- model `granite-code:8b`, digest `36c3c3b9683b…`, temp 0.0, num_ctx 4096
- seeds [11, 22, 33, 44, 55] (SIZING.md), arms ['A', 'B', 'C', 'D', 'E'], 10 scenarios / 26 turns / 10 probes per seed, one warm process
- GPU wall 1543.5 s under the shared lock (cap 180 min); script wall 1543.5 s (cap 150 min)

Pass rates are mean over seeds; brackets show the cross-seed range (min-max). 'overall' = all probes of the suite per seed.

| family (probes/seed) | arm A | arm B | arm C | arm D | arm E |
| --- | --- | --- | --- | --- | --- |
| contradiction_update (2) | 0.000 [0.000] | 0.500 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] |
| delayed_recall (3) | 0.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] |
| distractor_recall (2) | 0.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] |
| repeated_task (3) | 0.667 [0.000] | 0.333 [0.000] | 0.333 [0.000] | 0.333 [0.000] | 0.333 [0.000] |
| **overall (10)** | **0.200 [0.000]** | **0.700 [0.000]** | **0.800 [0.000]** | **0.800 [0.000]** | **0.800 [0.000]** |

Per-scenario pass counts (passed probes / seeds run x 1 probe):

| scenario | arm A | arm B | arm C | arm D | arm E |
| --- | --- | --- | --- | --- | --- |
| dr-0001 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dr-0002 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dr-0003 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dx-0001 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dx-0002 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| cu-0001 | 0/5 | 0/5 | 5/5 | 5/5 | 5/5 |
| cu-0002 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| rt-0001 | 5/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| rt-0002 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| rt-0003 | 5/5 | 0/5 | 0/5 | 0/5 | 0/5 |

Cost (tokens are per-request sums over the whole arm; wall per CN-002 rule):

| arm | seeds run | requests | prompt tok | eval tok | total tok | wall/seed s (min-max) | arm wall s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 5 | 130 | 10,865 | 1,520 | 12,385 | 60-60 | 300.4 |
| B | 5 | 130 | 18,885 | 1,051 | 19,936 | 58-61 | 295.0 |
| C | 5 | 130 | 69,985 | 1,155 | 71,140 | 59-60 | 298.2 |
| D | 5 | 130 | 84,671 | 1,025 | 85,696 | 59-60 | 298.3 |
| E | 5 | 130 | 84,671 | 1,025 | 85,696 | 60-60 | 299.4 |

Notes: [EXPLORATORY only — input to docs/EVALUATION-PREP.md, not a confirmatory result.] [CN-004] [CN-007] [CN-009] [CN-010] [CN-003]

Caveats (see docs/FINDINGS.md): CN-003 (temp-0 seed drift), CN-004 (rt-0003 option leakage), CN-007 (own-answer anchoring), CN-009 (self-model estimated on this suite), CN-010 (empty policy actuation surface). Exploratory numbers only — the confirmatory contrast is defined in docs/EVALUATION-PREP.md.
