# Proposal: agent spending controls and full-text research verification — 2026-10-10

## Status

Candidates for investigation only; no approval, implementation commitment, or change to existing experiment priorities. Derived from an email newsletter; vendor claims require verification against official documentation.

## 1. TinyFish stack — bounded spending by autonomous agents

**Lead:** TinySearch, TinyFetch, TinyBrowser, TinyAgent; claimed MCP integration, with a mix of free and paid operations. Verify exact product names, current pricing, API/tool interfaces and whether the “agent wallet” is a real payment mechanism or a metaphor for prepaid API credits.

**Research question:** How can an autonomous research agent use metered external tools without silently exceeding its budget, making unintended purchases or losing auditability?

Candidate controls:
- Hard per-run and per-day spending caps, plus per-tool limits.
- Explicit human approval before any payment or threshold crossing; default-deny for unknown prices.
- Pre-call cost estimate, post-call reconciliation, and handling of uncertain/failed charges.
- Idempotency keys, retry limits, cancellation and timeout behavior.
- Audit log linking user intent, tool call, authorization, billed amount and resulting evidence.
- Distinguish vendor API credits from real wallet/custodial payment authority.

**Evaluation:** Reproducible sandbox tests with mocked billing and adversarial cases: unexpected price changes, repeated calls, timeouts after charge, prompt-injection attempts to spend, and parallel agents racing against one shared budget. Measure overspend incidence, blocked legitimate tasks, accounting discrepancies, task success, latency and tool cost.

**Relation:** Extend the [existing Tiny web-agent stack proposal](2026-10-07-newsletter-research-candidates.md) rather than create a duplicate experiment. Potentially reusable agent-harness control if evidence supports it.

## 2. Consensus — full-text scientific evidence verification

**Lead:** Newsletter claims partnerships with Wiley, Taylor & Francis, Sage and ACS and full-text analysis beyond abstracts. Verify access scope, publisher terms, citation provenance, model behavior, and which content is genuinely available in full text.

**Research question:** Does access to full papers improve an AI research agent's ability to verify methodology, limitations and conclusions compared with abstract-only retrieval?

Suggested controlled benchmark:
- Select open-access papers with inspectable methods, figures, tables and limitations; respect publisher licenses.
- Prepare grounded questions where abstract-only answers are insufficient or misleading.
- Compare abstract-only, full-text retrieval, and manual expert/reference answers on the same questions.
- Score claim support, citation-to-passage correctness, methodology extraction, contradiction detection, abstention, retrieval completeness, token usage and latency.
- Explicitly test failures caused by PDF parsing, missing tables, paywalls and fabricated citations.

**Relation:** Could strengthen evidence-validation practices across `mdlslab`, especially Continuity and model-evaluation reports. Do not make a proprietary platform a prerequisite; compare with an open retrieval baseline.

## Suggested next step

Perform a short **primary-source feasibility review** for both leads, then decide whether either warrants a narrowly scoped benchmark. Preserve the current experiment queue; these are investigation candidates, not adopted designs.

## Publication and safety

No private emails, payment credentials, wallet secrets, proprietary PDFs or unlicensed full texts in the public repository. Use synthetic billing events and openly licensed papers.
