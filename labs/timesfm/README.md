# TimesFM Lab

## Status

Active research runs in a private playground repository because the evaluation data comes from non-public projects. This public lab records the direction; sanitized methodology and results will be published here once the evaluation reaches its verdict.

## Why this lab exists

Evaluate Google's TimesFM family for practical time-series forecasting and determine where a pretrained foundation model adds value over simple statistical and domain-specific baselines.

## Upstream snapshot

- Publisher: Google Research
- Family: TimesFM
- Purpose: zero-shot time-series forecasting
- Main track: TimesFM 2.5 (200M) — code and pretrained weights under Apache 2.0; the only practical-use candidate in this lab.
- Reference track: TimesFM 3.0 (330M) — adds native multivariate forecasting and covariates, but its pretrained weights use a separate non-commercial license; research reference only.
- Dropped: TimesFM 2.0 — superseded by 2.5 for this lab's purposes.
- Source code: Apache 2.0
- Licensing must be checked per version before any production or commercial use.

Official references:
- https://github.com/google-research/timesfm
- https://www.research.google/blog/timesfm-3-a-zero-shot-foundation-model-for-multivariate-forecasting/

## Research questions

1. How well does TimesFM perform zero-shot on datasets relevant to our projects?
2. How much do multivariate inputs and covariates improve useful forecasts?
3. How does it compare with simple baselines that are cheap and explainable?
4. How sensitive are results to horizon, history length, missing data, regime changes, and irregular observations?
5. Are probabilistic/quantile forecasts calibrated enough to be useful?
6. What compute and latency are required locally?
7. Where does fine-tuning improve results enough to justify its complexity?
8. Can forecasting output be integrated safely as evidence for downstream systems without presenting forecasts as certainty?

## Planned experiments

### TF-001: Reproducible local baseline

Install the current supported release, record environment and hardware, run an upstream example, and preserve a minimal reproducible result.

### TF-002: Baseline comparison

Compare against naive last-value, seasonal naive, moving-average and other appropriate simple baselines. TimesFM should earn its complexity.

### TF-003: Horizon sensitivity

Evaluate multiple forecast horizons on the same series and track error degradation.

### TF-004: Multivariate and covariate value

Where the dataset supports it, compare univariate forecasts with TimesFM 3.0 multivariate/covariate configurations.

### TF-005: Regime changes and shocks

Use historical windows containing abrupt changes. Record failure modes rather than averaging them away.

### TF-006: Probabilistic forecast quality

Evaluate quantile coverage/calibration where supported and useful.

### TF-007: Project-shaped datasets

Create sanitized experiments resembling real project workloads without publishing private financial, personal, or proprietary data.

## Metrics

Metrics depend on the series and objective. Candidate measures include MAE, RMSE, MASE, sMAPE, quantile loss, coverage, latency, and memory use. No single metric should be treated as universally sufficient.

## Publication note

This lab can document TimesFM 3.0 research while respecting the checkpoint's current non-commercial terms. Do not copy model weights into mdlslab.
