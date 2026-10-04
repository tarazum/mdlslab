# mdlslab

Experimental lab for evaluating AI models, architectures, agents, memory systems, forecasting models, and inference runtimes on real-world workloads.

The lab is intentionally heterogeneous. A forecasting foundation model, a local agentic LLM, a decision model, and an external memory system do not need one artificial benchmark. The common unit is a reproducible **experiment**.

## Labs

| Lab | Focus | State |
| --- | --- | --- |
| [Muse Glimmer](labs/muse-glimmer/) | Local multimodal agent model, tool use, long tasks, constrained hardware | Planned |
| [TimesFM](labs/timesfm/) | Time-series foundation models and forecasting | In progress (private playground) |
| [Jev](labs/jev/) | Decision-oriented model evaluation | Upstream verified; experiments pending |
| [Laya](labs/laya/) | Candidate local/open model | Source verification |
| [TencentDB Agent Memory](labs/tencentdb-agent-memory/) | Persistent agent memory and retrieval behavior | Upstream verified; experiments pending |
| [Continuity (Project C)](labs/continuity/) | Behavioral continuity through memory, self-model, feedback and reflection | Autonomous arc complete: exploratory + confirmatory CONT-001 done; result owner-accepted 2026-10-04 with caveats; next arc CONT-005 gated on suite v3 redesign |
| [CLI-Anything](labs/cli-anything/) | Agent tooling and CLI-based software control | Planned |
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

## Shared tooling

- [Agent resource coordination](shared/tooling/agent-resource-coordination/) — binding protocol + `lock.py` for concurrent agents sharing one machine's GPU/downloads; enforcement research tracked there.

## Public repository

Do not commit credentials, private datasets, personal conversations, corporate code, proprietary logs, or restricted model artifacts. Experiments requiring private material should stay outside this repository; only sanitized methodology and results may be published here.

## Existing playgrounds

Existing public playgrounds are linked from mdlslab rather than immediately migrated. This preserves their history and URLs while the new lab structure proves itself. A future migration should be deliberate, not a prerequisite for using mdlslab.
