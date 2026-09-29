# mdlslab

Experimental lab for evaluating AI models, architectures, agents, memory systems, forecasting models, and inference runtimes on real-world workloads.

The lab is intentionally heterogeneous. A forecasting foundation model, a local agentic LLM, a decision model, and an external memory system do not need one artificial benchmark. The common unit is a reproducible **experiment**.

## Labs

| Lab | Focus | State |
| --- | --- | --- |
| [Muse Glimmer](labs/muse-glimmer/) | Local multimodal agent model, tool use, long tasks, constrained hardware | Planned |
| [TimesFM](labs/timesfm/) | Time-series foundation models and forecasting | Planned |
| [Jev](labs/jev/) | Decision-oriented model evaluation | Source verification |
| [Laya](labs/laya/) | Candidate local/open model | Source verification |
| [TencentDB Agent Memory](labs/tencentdb-agent-memory/) | Persistent agent memory and retrieval behavior | Planned |
| [Colibri](labs/colibri/) | Existing public playground | External lab |
| [Mamba](labs/mamba/) | Existing public playground | External lab |

## Principles

- Use evaluation methods appropriate to each subject.
- Preserve environment, configuration, procedure, and evidence.
- Compare systems only when they solve compatible problems.
- Treat vendor benchmarks as context, not as lab findings.
- Record failures and negative results.
- Keep the repository public-safe by design.
- Prefer primary upstream sources and pin versions used by experiments.

See [Architecture](docs/architecture.md) for the repository model, experiment contract, publication policy, and migration strategy.

## Public repository

Do not commit credentials, private datasets, personal conversations, corporate code, proprietary logs, or restricted model artifacts. Experiments requiring private material should stay outside this repository; only sanitized methodology and results may be published here.

## Existing playgrounds

Existing public playgrounds are linked from mdlslab rather than immediately migrated. This preserves their history and URLs while the new lab structure proves itself. A future migration should be deliberate, not a prerequisite for using mdlslab.
