# mdlslab Architecture

## Purpose

mdlslab is a public experimental laboratory for evaluating AI models, model architectures, agent systems, memory layers, forecasting models, and inference runtimes on real-world hardware and workloads.

The repository is intentionally broader than an LLM benchmark suite. Its subjects can have very different interfaces, goals, and evaluation methods. A time-series foundation model, an agentic LLM, a state-space architecture, and an agent-memory framework should not be forced into one artificial benchmark.

The common unit is the **experiment**, not the benchmark.

## Goals

- Keep related AI experiments in one discoverable laboratory instead of creating a new playground repository for every technology.
- Preserve enough environment, configuration, procedure, and raw evidence to reproduce useful results later.
- Allow each lab to use evaluation methods appropriate to its subject.
- Make successful and unsuccessful experiments equally useful as engineering evidence.
- Keep the repository safe to publish by design.
- Enable cross-lab experiments when two technologies naturally interact.

## Non-goals

mdlslab is not intended to:

- rank unrelated models using a single score;
- impose one runtime, language, or framework on every lab;
- mirror upstream projects;
- store large model weights or datasets in Git;
- contain credentials, private data, corporate code, or confidential material;
- turn exploratory observations into claims that the evidence does not support.

## Repository model

```text
mdlslab/
├── README.md
├── docs/
│   ├── architecture.md
│   ├── hardware.md
│   ├── experiment-format.md
│   └── results-index.md
├── labs/
│   ├── <subject>/
│   │   ├── README.md
│   │   ├── experiments/
│   │   └── results/
│   └── ...
├── shared/
│   ├── datasets/
│   ├── prompts/
│   ├── scripts/
│   └── tooling/
└── reports/
    ├── comparison/
    └── findings/
```

This is a target structure, not a requirement to create empty directories. Directories should appear when an experiment needs them.

## Labs

A lab is an isolated research area for one model, architecture, runtime, framework, or closely related family.

Candidate labs currently include:

- Colibri
- Mamba
- TimesFM
- Jev
- Laya
- Muse Glimmer
- TencentDB Agent Memory

This list is a research backlog, not a statement that every subject has already been evaluated or accepted.

Each lab owns its methodology. For example:

- an inference-oriented LLM lab may measure VRAM/RAM use, quantization effects, throughput, tool calling, long-running agent behavior, and failure recovery;
- TimesFM may use historical datasets, forecast horizons, backtesting, and forecast-error metrics;
- an agent-memory lab may study recall, retention, false recall, memory lifecycle, latency, storage growth, and token cost;
- an architecture experiment may focus on runtime feasibility, hardware constraints, and behavior rather than application-level quality.

Cross-lab comparisons should exist only where the compared systems actually solve the same problem under compatible conditions.

## Minimum experiment contract

Experiments do not need identical implementations, but a durable experiment should capture these concepts:

### Goal

What question is the experiment trying to answer?

### Subject and version

Record the model/framework/runtime version, revision, checkpoint, quantization, or upstream commit where relevant.

### Environment

Record relevant operating system, runtime, libraries, drivers, and other dependencies.

### Hardware

Record hardware that materially affects the result, especially CPU, GPU, VRAM, RAM, and storage when relevant.

Shared machine descriptions may live in `docs/hardware.md` and be referenced by experiments.

### Configuration

Record parameters that can materially change the outcome.

### Procedure

Describe the steps required to reproduce the experiment.

### Raw results

Preserve machine-readable or minimally processed evidence where practical.

### Observations

Record what happened without overstating what the evidence proves.

### Conclusion

Answer the experiment's original question and identify unresolved questions or useful next experiments.

Not every exploratory spike needs all sections immediately. Once a result is used in a report or comparison, however, it should satisfy this contract closely enough to be independently understood.

## Reproducibility levels

Experiments can naturally mature through three informal stages:

1. **Exploration** — early investigation; setup and observations may still change.
2. **Reproducible** — configuration and procedure are sufficient to repeat the experiment.
3. **Reported** — evidence has been reviewed and is used in a finding or comparison.

These are descriptive stages, not approval labels.

## Shared assets

The `shared/` area exists only for assets genuinely reused by multiple labs.

Examples include:

- small redistributable datasets or dataset-generation scripts;
- reusable prompt suites;
- hardware/inference measurement helpers;
- result normalization or reporting tools.

Lab-specific code should stay inside its lab until reuse is demonstrated. Premature shared abstractions make experimental repositories harder to change.

## Results and reports

A **result** belongs to an experiment and records what happened.

A **report** interprets one or more results.

This distinction matters: raw measurements should remain available even if later interpretation changes.

Cross-model reports must document enough methodology to make differences meaningful. A table containing numbers produced under incompatible settings is not a comparison.

## Public-by-design policy

mdlslab is a public repository. Everything committed to it must be safe for public disclosure.

Do not commit:

- API keys, tokens, passwords, cookies, or connection strings;
- proprietary or corporate source code;
- private prompts, logs, conversations, or documents;
- personal or sensitive datasets;
- model files whose licenses do not permit redistribution;
- generated artifacts that accidentally contain local paths, credentials, or private input.

Use environment variables and ignored local configuration for credentials. Example configuration files should contain placeholders only.

If an experiment cannot be performed safely in public, keep its private working material outside mdlslab and publish only sanitized code, methodology, and results when appropriate.

## Upstream projects and licensing

Each lab should identify its upstream project, model source, and applicable license.

mdlslab's repository license applies to original material in this repository. It does not replace or override licenses for upstream models, datasets, copied code, model weights, or other third-party assets.

Prefer references and setup/download scripts over committing third-party binaries or model weights.

## Existing playground repositories

Existing playground repositories should not be deleted or migrated blindly.

A safe migration sequence is:

1. establish mdlslab conventions using new experiments;
2. select one existing playground as a migration pilot;
3. preserve its useful Git history where practical;
4. verify that links, documentation, and reproducibility survive the move;
5. archive the old public repository with a clear pointer to its new location;
6. migrate additional playgrounds only if the structure proved useful.

Migration and publication are separate decisions. Private experiments must not become public merely because mdlslab is public.

## Candidate migration strategy

Mamba is a reasonable pilot because it is already a bounded playground.

Colibri can follow after the migration pattern is validated.

TimesFM should be considered separately because repository consolidation must not implicitly decide whether unfinished private work is ready for publication.

## Cross-lab experiments

The monorepo becomes especially useful when technologies interact.

Examples:

- compare memory behavior across compatible agent models;
- attach an external memory system to an agentic model and measure the effect;
- compare inference runtimes for the same model and quantization;
- reuse one hardware measurement harness across otherwise unrelated labs.

Cross-lab experiments should reference the participating labs rather than duplicating their setup and documentation.

## Evolution

The structure is deliberately lightweight. Conventions should be added when repeated experiments demonstrate a need for them.

The laboratory should optimize for:

**evidence over impressions, reproducibility over ceremony, and useful experiments over uniformity.**
