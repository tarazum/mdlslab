# Arm A vs arm B vs arm C — per family (M3 mini-pilot)

- arm A source: `results/CONT-000/pilot-armA-20261001-222950/aggregate.json` (seeds [11, 22, 33, 44, 55])
- arm B source: `results/CONT-000/pilot-armB-20261001-224636/aggregate.json` (seeds [11, 22, 33])
- arm C source: `aggregate.json (this directory)` (seeds [11, 22, 33])
- model granite-code:8b, digest `36c3c3b9683b…`, temp 0.0, num_ctx 4096
- arm C = arm B + self-model summary (revision 1, sha `67054c3f8cc9…`) in the system prompt

| family | A mean | B mean | C mean | C - B |
| --- | --- | --- | --- | --- |
| contradiction_update | 0.0 | 0.5 | 1.0 | +0.500 |
| delayed_recall | 0.0 | 1.0 | 1.0 | +0.000 |
| distractor_recall | 0.0 | 1.0 | 1.0 | +0.000 |
| repeated_task | 0.667 | 0.333 | 0.333 | +0.000 |

Per-scenario pass counts (passed probes / seeds x 1 probe):

| scenario | arm A | arm B | arm C |
| --- | --- | --- | --- |
| dr-0001 | 0/5 | 3/3 | 3/3 |
| dr-0002 | 0/5 | 3/3 | 3/3 |
| dr-0003 | 0/5 | 3/3 | 3/3 |
| dx-0001 | 0/5 | 3/3 | 3/3 |
| dx-0002 | 0/5 | 3/3 | 3/3 |
| cu-0001 | 0/5 | 0/3 | 3/3 |
| cu-0002 | 0/5 | 3/3 | 3/3 |
| rt-0001 | 5/5 | 3/3 | 3/3 |
| rt-0002 | 0/5 | 0/3 | 0/3 |
| rt-0003 | 5/5 | 0/3 | 0/3 |

Exploratory mini-pilot numbers only (CN-009: the arm-C self-model was estimated on this same fixture suite from the arm-B pilot); not the confirmatory CONT-001 contrast.
