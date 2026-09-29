# Muse Glimmer Lab

## Why this lab exists

Evaluate Meta Muse Glimmer as a local agentic model, with emphasis on whether a 30B multimodal agent model is practically useful on constrained consumer hardware.

## Upstream snapshot

- Publisher: Meta
- Model: Muse Glimmer
- Size: 30B parameters
- Architecture: dense decoder-only multimodal transformer
- Inputs: text and images
- Output: text
- Default context: 128K tokens
- License: Apache 2.0
- Intended use: local agents, tool use, coding, long-running tasks, failure recovery
- Candidate runtimes: llama.cpp first; other supported runtimes can be evaluated later

Official references:
- https://research.meta.ai/blog/introducing-muse-glimmer-open-agentic-model
- https://dev.meta.ai/models/muse-glimmer
- https://dev.meta.ai/docs/muse-glimmer

## Research questions

1. Can a useful quantized build run on the lab's 8 GB VRAM machine using CPU/GPU offload?
2. What RAM, VRAM, startup time, prompt-processing speed, and generation speed are observed?
3. Which quantization gives the best quality/performance trade-off on this hardware?
4. How reliable is structured tool calling?
5. Can the model sustain multi-step tool loops without losing task state?
6. How does it recover from tool failures and invalid results?
7. How useful is its multimodal input for screenshots and technical documents?
8. How well does it handle coding and Ukrainian-language tasks?
9. What happens as context and agent-session length increase?
10. Is local operation practically useful rather than merely technically possible?

## Planned experiments

### MG-001: Local feasibility

Start with a GGUF build and llama.cpp. Measure installation friction, model footprint, RAM/VRAM usage, load time, tokens per second, and stability under partial GPU offload.

### MG-002: Quantization sweep

Compare a small set of realistic quantizations under identical prompts and hardware settings. Record speed, memory use, and obvious quality regressions.

### MG-003: Tool calling

Use deterministic local tools with known expected calls. Measure argument correctness, unnecessary calls, malformed calls, and completion after tool results.

### MG-004: Long-horizon agent loop

Give the model a task requiring many sequential operations. Record state loss, repetition, recovery, completion rate, and context growth.

### MG-005: Failure recovery

Inject missing files, failed commands, invalid tool responses, and recoverable environmental errors. Observe whether the model diagnoses and adapts instead of looping.

### MG-006: Multimodal technical input

Test screenshots, diagrams, and UI captures where the expected facts are independently known.

### MG-007: Coding workload

Use bounded repository tasks with tests or other objective verification. Separate code quality from scaffold/tooling quality.

### MG-008: Ukrainian

Test instruction following, technical Ukrainian, summarization, and mixed Ukrainian/English engineering workflows.

## Evidence policy

Vendor benchmark results are useful context, not local findings. Results in this lab must come from recorded experiments and identify the exact artifact, runtime, configuration, and hardware used.
