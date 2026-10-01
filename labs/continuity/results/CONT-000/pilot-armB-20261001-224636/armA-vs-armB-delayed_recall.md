# Arm A vs arm B — delayed_recall family (M2 mini-pilot)

- arm A source: `results/CONT-000/pilot-armA-20261001-222950/aggregate.json` (seeds [11, 22, 33, 44, 55])
- arm B source: `aggregate.json (this directory)` (seeds [11, 22, 33])
- model granite-code:8b, digest `36c3c3b9683b…`, temp 0.0, num_ctx 4096

| arm | pass rate by seed | mean |
| --- | --- | --- |
| A (no persistent memory) | {'11': 0.0, '22': 0.0, '33': 0.0, '44': 0.0, '55': 0.0} | 0.0 |
| B (SQLite persistent memory) | {11: 1.0, 22: 1.0, 33: 1.0} | 1.0 |

Delta (B - A) mean pass rate: **+1.000**

Per-scenario pass counts (passed probes / seeds x 1 probe):

| scenario | arm A | arm B |
| --- | --- | --- |
| dr-0001 | 0/5 | 3/3 |
| dr-0002 | 0/5 | 3/3 |
| dr-0003 | 0/5 | 3/3 |

Exploratory mini-pilot numbers only; not the confirmatory CONT-001 contrast.
