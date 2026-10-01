# Arm A vs arm B vs arm C vs arm D — per family (M4 mini-pilot)

- arm A source: `results/CONT-000/pilot-armA-20261001-222950/aggregate.json` (seeds [11, 22, 33, 44, 55])
- arm B source: `results/CONT-000/pilot-armB-20261001-224636/aggregate.json` (seeds [11, 22, 33])
- arm C source: `results/CONT-000/pilot-armC-20261001-231050/aggregate.json` (seeds [11, 22, 33])
- arm D source: `aggregate.json (this directory)` (seeds [11, 22, 33])
- model granite-code:8b, digest `36c3c3b9683b…`, temp 0.0, num_ctx 4096
- arm D = arm C + one deterministic post-session reflection pass (episode summaries with conflict review; evidence-gated self-model revisions through the fail-closed store)

| family | A mean | B mean | C mean | D mean | D - C |
| --- | --- | --- | --- | --- | --- |
| contradiction_update | 0.0 | 0.5 | 1.0 | 1.0 | +0.000 |
| delayed_recall | 0.0 | 1.0 | 1.0 | 1.0 | +0.000 |
| distractor_recall | 0.0 | 1.0 | 1.0 | 1.0 | +0.000 |
| repeated_task | 0.667 | 0.333 | 0.333 | 0.333 | +0.000 |

Per-scenario pass counts (passed probes / seeds x 1 probe):

| scenario | arm A | arm B | arm C | arm D |
| --- | --- | --- | --- | --- |
| dr-0001 | 0/5 | 3/3 | 3/3 | 3/3 |
| dr-0002 | 0/5 | 3/3 | 3/3 | 3/3 |
| dr-0003 | 0/5 | 3/3 | 3/3 | 3/3 |
| dx-0001 | 0/5 | 3/3 | 3/3 | 3/3 |
| dx-0002 | 0/5 | 3/3 | 3/3 | 3/3 |
| cu-0001 | 0/5 | 0/3 | 3/3 | 3/3 |
| cu-0002 | 0/5 | 3/3 | 3/3 | 3/3 |
| rt-0001 | 5/5 | 3/3 | 3/3 | 3/3 |
| rt-0002 | 0/5 | 0/3 | 0/3 | 0/3 |
| rt-0003 | 5/5 | 0/3 | 0/3 | 0/3 |

Exploratory mini-pilot numbers only. Caveats: CN-009 (the arm-C/D self-model was estimated on this same fixture suite from the arm-B pilot, and under arm D additionally evolves in-run from probe outcomes that render into later sessions); CN-004 (rt-0003 option leakage inflates arm A there). Not the confirmatory CONT-001 contrast.
