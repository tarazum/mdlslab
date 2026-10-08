# Proposal: OmO agent orchestration and Herdr terminal runtime — 2026-10-08

## Scope and provenance

Exploratory candidate for `mdlslab`. This document preserves a review of [Oh My OpenAgent (OmO)](https://github.com/code-yeongyu/oh-my-openagent), [Herdr](https://github.com/herdrdev/herdr), and the optional third-party [OmO Herdr DAG](https://github.com/jc01rho/omo-herdr-dag) extension. Sources were reviewed on 2026-10-08; behaviors and integration compatibility are not yet verified locally.

**No existing experiment is displaced.** This is not an approval, an implementation order, a migration decision, or an experimental result. Do not modify Continuity's active plan or create new lab infrastructure until a bounded test is scheduled.

## Motivation and existing workflow

The working environment uses Windows and VS Code with Codex and Claude Code, plus a separate ZCode/GLM workflow. Three distinct questions should not be conflated:

1. **Agent quality / orchestration:** does OmO improve outcomes through model routing, delegated tasks, verification and memory compared with a conventional single-agent workflow?
2. **Workspace ergonomics:** does Herdr improve reliability and oversight for existing terminal-based coding agents, independent of model quality?
3. **Workflow observability:** does the optional OmO Herdr DAG viewer accurately expose dependencies and task progress without disrupting the underlying workflow?

VS Code remains the editor and debugging environment. Neither OmO nor Herdr is a drop-in replacement for its GUI or extensions. ZCode/GLM integration must be checked: Herdr owns CLI terminal sessions, not arbitrary IDE sidebars; OmO's support for GLM provider login does not establish compatibility with a particular ZCode account or tariff.

## A. Oh My OpenAgent (OmO): proposed evaluation

**Upstream:** https://github.com/code-yeongyu/oh-my-openagent

OmO 5.x provides a standalone `omo` edition using a Senpi/Pi-based engine and also documents OpenCode Ultimate and Codex CLI Light variants. The advertised capabilities include multi-model routing, `ulw` and `mass ulw` work modes, parallel task DAGs, selective skills, and Kibitzer memory stored in Git/Markdown.

The important research questions are:

- Does OmO produce measurably more correct, tested code than Codex-only or Claude-only execution on the *same fixed tasks and repository snapshots*?
- What is the wall-clock gain, if any, after including failed runs, retries, review and manual interventions?
- How much does parallelism increase total tokens, provider requests and spend?
- Is provider routing deterministic, explainable and reproducible across repeated tasks? How does it behave under model rate limits?
- Does Kibitzer reduce repeated mistakes and increase delayed recall compared with baseline session memory, without increasing false recall, contamination or token cost?
- How well does OmO recover after interruption, compaction, a failed tool call or session restart?

**Ablations:** (A0) existing direct Codex / Claude Code workflow, (A1) OmO Native single primary model with orchestration features minimized, (A2) OmO Native multi-model routing, (A3) OmO parallel-agent workflow for tasks that genuinely permit parallelism, (A4, later) OmO with and without Kibitzer under compatible memory fixtures.

**Evidence:** task success against predeclared acceptance criteria, build/test pass rate, code-review defect counts, human corrections, total model requests/tokens and estimated cost, p50/p95 and per-task wall time, interruption recovery, repeated-mistake rate, delayed recall, false memory use. Record raw per-run data and error classifications rather than only subjective impressions. Vendor claims, GitHub stars and demos are not evidence of a performance improvement.

**Risks:** OmO's SUL-1.0 license requires review before commercial redistribution/embedding; confirm exact scope for any intended deployment. The Codex Light install guide describes an optional autonomous profile with `approval_policy = "never"` and `sandbox_mode = "danger-full-access"`. Do **not** enable this for evaluation. Never use production credentials, private repositories, billing-sensitive resources or real customer data. Pin versions and audit install scripts and permissions before running.

**Suggested trial:** OmO Native in a disposable sandbox and on a sanitized public fixture repository, without replacing the existing Codex/Claude/ZCode configuration. Test provider authentication with zero unanticipated API billing before executing multi-agent work. Do not assume GLM access via ZCode equals OmO-compatible subscription access.

## B. Herdr: proposed evaluation

**Upstream:** https://github.com/herdrdev/herdr
**Reference release at review:** v0.9.3 (2026-09-29); Rust; Apache-2.0.

Herdr is a terminal multiplexer and persistent terminal runtime for coding agents, **not a model orchestrator**. It provides server-owned PTYs, workspaces/panes, SSH machine connections, process-aware agent states (working, blocked, done, idle), and CLI/socket controls such as starting an agent, sending a prompt, waiting, and reading output. A detached client leaves original processes alive. On server restart the original processes stop; the layout is restored and agent-conversation continuation depends on native session-restore support.

Current Windows documentation in the upstream repository says native Windows support is **generally available**, with stable recommended. It uses ConPTY. Remaining Windows-specific constraints include unsupported direct terminal attach, unsupported live server handoff, platform-specific terminal-keyboard/image behavior, partial live-CWD tracking, and preview-quality plugins. Note that older indexed/cached copies of the docs still describe Windows as beta; use the current repository source, not the stale cache.

**Benefits to test first:** keep independent Codex and Claude Code sessions in separate panes and quickly locate agents waiting for input. This adds value without changing prompts, models or APIs.

**Research questions:**

- How accurately are Codex and Claude Code classified (working / blocked / done / idle) on the target Windows Terminal + PowerShell setup?
- Can the agent state reliably trigger a wait/notification, especially across permission requests, compaction and long builds? How many false positives and missed blocked states?
- Do pane navigation, detach/reattach and optional session restore work without lost context?
- What is the additional CPU, memory and startup overhead with two/four concurrent panes?
- Is Git Bash detection reliable for the user's actual launch chain? Are API and clipboard behaviors adequate?
- Can a native GLM CLI be managed as a terminal, with meaningful state detection? If GLM is only accessible through a ZCode IDE extension, expect no native Herdr integration.

A Herdr screen manifest uses visible terminal state; it can misclassify unfamiliar UIs. Test actual behavior and inspect `herdr agent explain`; do not use the state label as authoritative evidence that the code task passed.

**Safety:** treat `pane run`, `agent prompt` and the socket API as command-execution surfaces; do not expose the control socket outside an appropriate trust boundary. Keep the test under an unprivileged account and avoid privileged Herdr sessions.

## C. Combined optional workflow: OmO + Herdr DAG

**Upstream:** https://github.com/jc01rho/omo-herdr-dag

This is a **third-party OmO extension**, not a built-in capability of Herdr. It uses OmO DAG updates to open a status viewer in another Herdr pane. It requires Node.js 24+, an OmO build emitting `omo.dag.updated`, and compatible Herdr pane APIs. Its README documents Windows PowerShell pane tests and a successful clean-install macOS integration; compatibility with each future OmO/Herdr release remains subject to verification.

It does **not** require Herdr's first-class OmO agent recognition: running `omo` inside an ordinary Herdr pane is sufficient for the extension's pane actions. Herdr's current supported-agent list does not include OmO by name; a community proposal for its first-class recognition exists, but must not be confused with merged official support.

Assess the viewer only after OmO and Herdr pass independent smoke tests. Measure graph fidelity (states, dependencies, failures, retries), responsiveness, extra resource use, snapshot correctness and behavior after disconnect/reload. The viewer is useful observability, **not** proof that work is correct.

## Trial sequence and stopping rules

1. **Herdr-only smoke test:** Windows Terminal/PowerShell; start existing Codex and Claude Code CLIs from Herdr; test wait/blocked/done, pane navigation and detach/reattach. No new model purchases.
2. **OmO Native smoke test:** isolated public repo fixture; one small implementation + validation task versus a matching direct-agent baseline. Record provider/auth behavior, tokens/cost, wall time and correctness. Disable full-access/autonomous permissions.
3. **Matched benchmark:** at least several repeatable tasks with frozen input commit and acceptance criteria; only enable multi-model parallelism where dependencies justify it.
4. **Optional memory experiment:** align with `labs/continuity/` and `labs/tencentdb-agent-memory/`, including repeated-mistake, delayed-recall and false-recall fixtures; do not quietly replace their existing methodology.
5. **Optional DAG integration:** only if independent runs establish a need for multi-agent observability; test `omo-herdr-dag` using pinned versions and collect screen/evidence of actual state transitions.

Stop or defer if provider permissions/costs cannot be bounded, on-screen status is persistently wrong, session recovery is unreliable, tasks cannot be scored objectively, or the harness requires installing untrusted hooks with unrestricted permissions.

## Reproducibility and integration boundaries

- Capture exact tool revisions, OS/terminal/shell, provider/model IDs, credential method (never credential values), configurations, prompt/task fixtures, build/test command results, timings and costs.
- Keep state/logs free of API keys, private prompts and user data. Only sanitized evidence belongs in this public repository.
- No production IDENN workload in the initial trial. Any later real-world trial must be sanitized and isolated.
- Avoid adding another permanent lab or changing `README.md` status tables until a selected experiment has been implemented and reviewed.
- Herdr's own utility must be judged separately from OmO's code quality; the combined workflow is a third, optional condition.

## Source references (primary)

- [OmO upstream and installation](https://github.com/code-yeongyu/oh-my-openagent)
- [OmO installation editions and permissions](https://github.com/code-yeongyu/oh-my-openagent/blob/dev/docs/guide/installation.md)
- [OmO license](https://github.com/code-yeongyu/oh-my-openagent/blob/dev/LICENSE.md)
- [Herdr upstream](https://github.com/herdrdev/herdr)
- [Herdr v0.9.3 release](https://github.com/herdrdev/herdr/releases/tag/v0.9.3)
- [Herdr current Windows support documentation (repository source)](https://github.com/herdrdev/herdr/blob/master/docs/next/website/src/content/docs/windows-beta.mdx)
- [Herdr supported agents](https://github.com/herdrdev/herdr/blob/master/docs/next/website/src/content/docs/agents.mdx)
- [Herdr session persistence](https://herdr.dev/docs/session-state/)
- [Herdr agent automation](https://herdr.dev/docs/agent-automation/)
- [Community OmO recognition discussion](https://github.com/herdrdev/herdr/discussions/2493)
- [OmO Herdr DAG extension](https://github.com/jc01rho/omo-herdr-dag)
- [mdlslab architecture and experiment contract](../architecture.md)
- [Continuity lab](../../labs/continuity/)
- [TencentDB Agent Memory lab](../../labs/tencentdb-agent-memory/)
