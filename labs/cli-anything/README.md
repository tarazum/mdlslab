# CLI-Anything Lab

## Status

Planned. Upstream reviewed 2026-09-30; no mdlslab experiments run yet.

## Why this lab exists

Evaluate CLI-Anything as an agent-tooling layer: can AI agents operate existing software more reliably through purpose-built command-line harnesses than through GUI automation or ad-hoc integrations?

This is not a model lab. It belongs in mdlslab because the common unit is the reproducible experiment, and CLI-Anything gives us a useful way to study how different agents interact with the same external tool.

## Upstream snapshot

Reviewed 2026-09-30.

- Publisher: HKUDS
- Upstream repository: https://github.com/HKUDS/CLI-Anything
- CLI-Hub: https://clianything.cc/
- License: Apache-2.0
- Purpose: expose software to AI agents through structured, composable CLI harnesses.
- CLI-Hub installs and manages existing harnesses with `pip install cli-anything-hub`.
- Existing harnesses include LibreOffice, Blender, GIMP, Inkscape, Audacity, OBS Studio, QGIS, FreeCAD, Draw.io, n8n, Ollama, and others.
- Agent integrations/skills exist for multiple ecosystems, including Claude Code, Codex, Cursor, Pi, OpenCode and others.
- Generated harnesses are intended to expose structured output and agent-facing skill documentation rather than require screen interpretation.

Upstream capabilities and claims are context only until reproduced locally.

## Research questions

1. How reliably can an agent discover and use an existing CLI-Anything harness?
2. Does structured CLI control reduce retries and failures compared with GUI/computer-use automation?
3. Can different agents execute the same task through the same harness without agent-specific rewrites?
4. How much agent context is required to learn a harness from its help and skill documentation?
5. Are generated artifacts equivalent to artifacts produced through native application workflows?
6. How deterministic are repeated runs of the same task?
7. What failure modes occur when the underlying application version changes?
8. How portable are harnesses across Windows, WSL/Linux, and other environments relevant to the lab?
9. How good is the harness generator on software that does not already have a CLI-Anything integration?
10. When is CLI preferable to MCP, native APIs, direct libraries, or GUI automation?

## Planned experiments

### CLA-001: CLI-Hub smoke test

Install CLI-Hub, inspect the registry, install one existing harness, and execute a minimal end-to-end task. Record exact versions, environment, commands, outputs, failures, and cleanup steps.

### CLA-002: Artifact-producing workflow

Use a mature harness such as LibreOffice, Draw.io, GIMP, or Inkscape for a non-trivial task that produces an inspectable artifact. Verify the artifact independently rather than accepting successful command execution as success.

### CLA-003: Cross-agent reproducibility

Give at least two compatible agents the same task, harness, inputs, and acceptance criteria. Compare task completion, tool calls, retries, elapsed time, and artifact quality. Do not turn this into a general model ranking; measure behavior for the defined task.

Candidate agents include Codex, Claude Code, Cursor, Copilot CLI, Pi, or other supported agents available in the test environment.

### CLA-004: CLI versus GUI automation

Run a compatible task once through CLI-Anything and once through GUI/computer-use automation. Compare reliability, number of interaction steps, recovery from errors, runtime, and observability.

### CLA-005: CLI versus direct integration

For software with a usable native API, library, MCP server, or existing CLI, compare the CLI-Anything path with the direct path. Identify what abstraction is gained and what complexity or capability is lost.

### CLA-006: Harness generation

Choose an open-source application not already well served by CLI-Hub. Run the CLI-Anything harness-generation workflow against a pinned source revision. Review the generated command surface, tests, skill documentation, and safety boundaries before execution.

### CLA-007: Version drift

Run a validated harness against its known-good application version and then against a newer compatible candidate. Record breakage, silent behavioral changes, and the effort needed to repair the harness.

### CLA-008: Agent-generated lab artifact

Use CLI-Anything as infrastructure for another mdlslab experiment. A candidate example is generating a report, diagram, or presentation from TimesFM experiment results. This tests whether the tool layer is useful beyond a synthetic demo.

## Evaluation dimensions

Record at least:

- task success against explicit acceptance criteria;
- number of agent/tool interactions;
- retries and recoveries;
- elapsed time;
- deterministic versus variable outputs;
- structured-output quality;
- artifact validity;
- setup and maintenance effort;
- portability;
- application-version sensitivity;
- token/context overhead where measurable.

## First experiment recommendation

Start with an existing mature harness rather than generating a new one. LibreOffice or Draw.io are attractive because they create artifacts that can be inspected independently and are relevant to normal agent workflows.

The first goal is deliberately small: determine whether CLI-Anything provides a stable, observable agent-to-application boundary in our environment. Only then invest in custom harness generation.

## Relationship to mdlslab

CLI-Anything is categorized as **agent tooling / agent-computer interface**, not as a model. It can also become shared experimental infrastructure: the same harness and task can be presented to multiple agents, reducing one source of variation in cross-agent experiments.

This lab should remain independent from model-specific conclusions. A failed task can be caused by the agent, the harness, the application, the environment, or their interaction; experiment notes must preserve enough evidence to distinguish them.

## Safety and publication

Use public or synthetic inputs only. Do not expose credentials, private documents, corporate applications, or proprietary source code to generated harnesses or public experiment artifacts. Pin upstream versions used by experiments and preserve exact acceptance criteria and evidence.
