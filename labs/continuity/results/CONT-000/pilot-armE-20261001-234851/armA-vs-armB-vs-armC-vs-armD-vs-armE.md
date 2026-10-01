# Arm A vs arm B vs arm C vs arm D vs arm E — per family (M5 mini-pilot)

- arm A source: `results/CONT-000/pilot-armA-20261001-222950/aggregate.json` (seeds [11, 22, 33, 44, 55])
- arm B source: `results/CONT-000/pilot-armB-20261001-224636/aggregate.json` (seeds [11, 22, 33])
- arm C source: `results/CONT-000/pilot-armC-20261001-231050/aggregate.json` (seeds [11, 22, 33])
- arm D source: `results/CONT-000/pilot-armD-20261001-233203/aggregate.json` (seeds [11, 22, 33])
- arm E source: `aggregate.json (this directory)` (seeds [11, 22, 33])
- model granite-code:8b, digest `36c3c3b9683b…`, temp 0.0, num_ctx 4096
- arm E = arm D + ex-ante world-model predictions on probe turns (non-behavioral, trace events) + bounded policy {answer_direct, retrieve_then_answer} (actuation: per-turn memory refresh/extension only)

| family | A mean | B mean | C mean | D mean | E mean | E - D |
| --- | --- | --- | --- | --- | --- | --- |
| contradiction_update | 0.0 | 0.5 | 1.0 | 1.0 | 1.0 | +0.000 |
| delayed_recall | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | +0.000 |
| distractor_recall | 0.0 | 1.0 | 1.0 | 1.0 | 1.0 | +0.000 |
| repeated_task | 0.667 | 0.333 | 0.333 | 0.333 | 0.333 | +0.000 |

Per-scenario pass counts (passed probes / seeds x 1 probe):

| scenario | arm A | arm B | arm C | arm D | arm E |
| --- | --- | --- | --- | --- | --- |
| dr-0001 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| dr-0002 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| dr-0003 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| dx-0001 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| dx-0002 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| cu-0001 | 0/5 | 0/3 | 3/3 | 3/3 | 3/3 |
| cu-0002 | 0/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| rt-0001 | 5/5 | 3/3 | 3/3 | 3/3 | 3/3 |
| rt-0002 | 0/5 | 0/3 | 0/3 | 0/3 | 0/3 |
| rt-0003 | 5/5 | 0/3 | 0/3 | 0/3 | 0/3 |

## Arm E world-model calibration (pooled over 30 predictions / 30 outcomes)

- overall: predicted-pass rate 0.700 vs actual 0.800; pass/fail accuracy 0.900; mean confidence 0.700

| bucket | n | predicted-pass rate | actual pass rate | mean confidence |
| --- | --- | --- | --- | --- |
| high | 15 | 1.000 | 1.000 | 1.000 |
| medium | 6 | 1.000 | 1.000 | 0.500 |
| low | 9 | 0.000 | 0.333 | 0.333 |

CN-009 caveat: confidence derives from self-model family rates estimated on this same fixture suite — exploratory calibration, partly circular.

## Arm E policy action distribution (pooled over 78 turn decisions)

| action / rule | count |
| --- | --- |
| action: answer_direct | 54 |
| action: retrieve_then_answer | 24 |
| rule fired: R1-absence-of-records | 21 |
| rule fired: R2-corrected-fact-probe | 3 |
| rule fired: default | 54 |
| retrieve_then_answer -> physical injection | 0 |
| retrieve_then_answer -> no-op (no-op: retrieved episodes already covered by this session's injections) | 24 |

Exploratory mini-pilot numbers only. Caveats: CN-009 (self-model estimated on this same fixture suite; predictions partly circular); CN-004 (rt-0003 option leakage inflates arm A there). Not the confirmatory CONT-001 contrast.
