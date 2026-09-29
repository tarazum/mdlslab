# Laya Lab

## Status

Planned. Exact upstream model/project identity must be verified before implementation.

## Why this lab exists

Laya was identified as a candidate for local/open AI experimentation. Before building tests around it, mdlslab will first establish the exact upstream project, artifacts, license, architecture, supported runtimes, and intended workload.

This lab intentionally keeps uncertain details out of the permanent technical record.

## Research questions

1. Which exact project/model does the name Laya refer to?
2. Who publishes and maintains it?
3. Are weights and source available, and under which licenses?
4. What problem is it designed to solve?
5. What hardware is realistically required for local use?
6. Which inference runtimes are supported?
7. What makes it materially different from the other mdlslab subjects?
8. Which project-shaped workloads would provide a fair evaluation?

## Planned experiments

### LAYA-000: Source verification

Pin the canonical upstream repository/model page, documentation, license, model versions, architecture, and supported execution path.

### LAYA-001: Reproducible smoke test

Run the smallest meaningful upstream workflow and capture environment, configuration, resource use, and output.

### LAYA-002: Hardware feasibility

Measure local RAM/VRAM use, startup time, throughput, and stability on available hardware.

### LAYA-003: Capability-specific evaluation

Define this only after LAYA-000 establishes what the system is actually designed to do.

## Evidence rule

Do not fill missing facts from similarly named models, social-media summaries, or assumptions. Update this document once the canonical upstream identity is confirmed.
