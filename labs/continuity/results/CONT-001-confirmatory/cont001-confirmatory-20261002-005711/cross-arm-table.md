# CONT-001 confirmatory — cross-arm table (M7)

**agent-pre-registered, pending owner acceptance**

- run `cont001-confirmatory-20261002-005711` (confirmatory; pre-registration frozen at `a845fc5`)
- model `granite-code:8b`, digest `36c3c3b9683b…`, temp 0.0, num_ctx 4096
- seeds [101, 202, 303, 404, 505] (fresh, EVALUATION-PREP.md 6.1), arms ['A', 'B', 'C', 'D', 'E'], 14 scenarios / 45 turns / 14 probes per seed, one warm process
- fixture validation verdict: PASS; freeze verification passed: True
- GPU wall 602.2 s under the shared lock (cap 180 min); script wall 602.2 s (cap 150 min)

Pass rates are mean over seeds; brackets show the cross-seed range (min-max).

| family (probes/seed) | arm A | arm B | arm C | arm D | arm E |
| --- | --- | --- | --- | --- | --- |
| contradiction_update (2) | 0.000 [0.000] | 1.000 [0.000] | 0.500 [0.000] | 0.500 [0.000] | 0.500 [0.000] |
| correction_reuse (2) | 0.000 [0.000] | 0.000 [0.000] | 0.000 [0.000] | 0.000 [0.000] | 0.000 [0.000] |
| delayed_recall (3) | 0.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] |
| distractor_recall (2) | 0.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] | 1.000 [0.000] |
| repeated_task (5) | 0.000 [0.000] | 0.160 [0.200] | 0.000 [0.000] | 0.000 [0.000] | 0.000 [0.000] |
| **overall (14)** | **0.000 [0.000]** | **0.557 [0.071]** | **0.429 [0.000]** | **0.429 [0.000]** | **0.429 [0.000]** |

Per-scenario pass counts (passed probes / seeds run x 1 probe):

| scenario | arm A | arm B | arm C | arm D | arm E |
| --- | --- | --- | --- | --- | --- |
| dr-0004 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dr-0005 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dr-0006 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dx-0003 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| dx-0004 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| cu-0003 | 0/5 | 5/5 | 0/5 | 0/5 | 0/5 |
| cu-0004 | 0/5 | 5/5 | 5/5 | 5/5 | 5/5 |
| rt-0004 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| rt-0005 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| rt-0006 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| rt-0007 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| rt-0008 | 0/5 | 4/5 | 0/5 | 0/5 | 0/5 |
| cr-0001 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |
| cr-0002 | 0/5 | 0/5 | 0/5 | 0/5 | 0/5 |

Cost (tokens are per-request sums over the whole arm; wall per CN-002 rule):

| arm | seeds run | requests | prompt tok | eval tok | total tok | wall/seed s (min-max) | arm wall s |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A | 5 | 225 | 21,814 | 4,515 | 26,329 | 111-112 | 555.1 |
| B | 5 | 225 | 42,018 | 4,522 | 46,540 | 110-114 | 559.5 |
| C | 5 | 225 | 146,820 | 5,500 | 152,320 | 116-117 | 582.7 |
| D | 5 | 225 | 267,200 | 5,595 | 272,795 | 116-116 | 464.0 |
| E | 5 | 225 | 272,360 | 6,445 | 278,805 | 118-119 | 591.3 |

The confirmatory claim is decided ONLY by the pre-registered primary analysis (`repeated-mistake-analysis.md`): RM(E) - RM(A), two-sided 95% paired cluster bootstrap over scenarios, MME 0.15. This table is descriptive. agent-pre-registered, pending owner acceptance.
