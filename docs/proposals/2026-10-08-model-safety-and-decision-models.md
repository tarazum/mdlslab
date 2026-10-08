# Proposal: model-safety checkpoints and compact decision models — 2026-10-08

## Status and provenance

Exploratory research proposal derived from a Marktechpost newsletter digest (8 October 2026). Names, versions, licenses, availability and capabilities below are **unverified leads**, not validated upstream facts. This document neither approves work nor changes existing experiment priorities.

## A. Unsloth Studio: pre-execution model safety checkpoints (highest interest)

**Question:** Can a repeatable, lightweight preflight reduce the risk of running untrusted model artifacts locally?

Investigate what Unsloth Studio actually checks and whether those checks can be reproduced independently. Candidate preflight controls:

- Pin model repository, revision, files, hashes and provenance.
- Inspect artifact formats; prefer data-only formats where feasible.
- Flag custom/remote code, deserialization and executable dependencies.
- Check license and download provenance.
- Run isolated smoke tests with constrained filesystem, network and resource access.
- Record explicit pass/fail/unknown findings with evidence, not a blanket “safe” verdict.

**Evaluation idea:** construct a benign fixture suite with known safe and intentionally suspicious packaging characteristics; measure detection coverage, false positives, reproducibility, overhead and bypass limitations. Do not execute malicious payloads. Compare the product's actual protections with a minimal independent checklist.

**Potential home:** shared tooling, but only if more than one lab needs it. Avoid blocking existing experiments on a new security framework.

## B. Liquid AI d1-3B / d1-omni-600M: compact decision-oriented models (high interest)

**Question:** Do small specialized decision models offer a useful quality/latency/cost tradeoff against deterministic policies and general-purpose LLMs?

First verify the exact model IDs, official releases, licenses, runtime interfaces and whether “decision model” is an accurate description. Do not assume the newsletter's names or numbers are correct.

If confirmed, propose a bounded comparison with the existing `labs/jev/` direction:

- controlled classification and action-selection tasks;
- abstention and uncertainty handling;
- contradictory instructions and misleading context;
- stability across repeated runs;
- latency, memory/VRAM footprint and inference cost;
- simple rule-based baseline plus an appropriately sized LLM baseline.

Use matched tasks and inputs; avoid ranking incompatible models with a single score. Start with a feasibility spike on available hardware, then decide whether a reproducible experiment is warranted.

## C. Perplexity pplx-embed-v2-late: retrieval candidate (medium interest)

Verify official availability, embedding interface, dimensions, late-interaction semantics, pricing/license and hosting requirements.

If feasible, compare against existing or simpler embedding baselines on synthetic/public corpora: English/Ukrainian retrieval, near-duplicate discrimination, false recall, latency and indexing/storage cost. Possible relevance to Continuity and TencentDB Agent Memory; no migration implied.

## D. Claude Haiku 5.5: reference model watchlist

Verify that this exact version exists and obtain official model/API documentation, pricing and limits. If confirmed, consider it only as a reference baseline for compatible small-agent tasks. No dedicated lab or benchmark is proposed from a newsletter mention alone.

## Candidate ordering and gates

1. **Unsloth preflight investigation** — identify concrete upstream checks, threat model and reusable fixture suite.
2. **Liquid decision-model verification** — resolve exact artifacts, then assess Jev overlap and local feasibility.
3. **Perplexity embedding verification** — assess relevance to memory/retrieval tests.
4. **Claude Haiku version verification** — watchlist only.

**Before implementation:** attach primary-source URLs, pin versions, check licenses, establish a falsifiable research question and success/failure criteria, and follow `docs/architecture.md` experiment contract. Keep the public repository free of private emails, account data, tokens, model binaries and unsafe payloads.

## Related material

- [Previous newsletter-derived proposal](2026-10-07-newsletter-research-candidates.md)
- [Jev lab](../../labs/jev/)
- [Continuity lab](../../labs/continuity/)
- [TencentDB Agent Memory lab](../../labs/tencentdb-agent-memory/)
