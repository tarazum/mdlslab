# Review of REFLECTION-V2-PROPOSAL.md — implementing agent

Date: 2026-10-07. Reviewer: ZCode (implementing agent; separate file per the
author/reviewer split — the proposal text belongs to the owner/co-owner and
is not edited here). Basis: the proposal (commit 6f2d974), the closed
CONT-001/CONT-005 evidence base (`docs/ARC-REPORT.md`,
`docs/RESULTS-DIGEST-2026-10.md`, cycle-2 artifacts), and the owner-adopted
pre-registration amendments of 2026-10-04.

Overall: **strong proposal, GO-shape after required changes.** The R3
manual-gold-lessons control is the single best design decision in the
document — it directly de-risks the lab's dominant failure mode (two
consecutive nulls where richer injected context did not change answers).
The four-mechanism decomposition (episodic / self-model / worker / lessons)
and NO_LESSON-as-first-class are clean. The required changes below are all
about hardening the experiment against the specific ways this lab has
already been burned.

## Required changes

**RC-1 — Freeze the lessons store as an artifact chain.** The reflection
worker is an LLM step; its output must not be a moving input. Required
pipeline: experience-set traces (committed) → reflection worker runs ONCE
(model, temperature, prompt digested) → candidate lessons → deterministic
validator applies a PRE-WRITTEN acceptance rule → accepted lessons store
COMMITTED AND DIGESTED → only then is the transfer set authored/frozen and
run. The pre-registration covers the whole chain (worker config digest +
lessons-store digest + transfer suite digest + frozen analysis), mirroring
the FREEZE-A/FREEZE-B discipline. Without this, a mid-experiment lessons
regeneration is a protocol violation nobody can detect.

**RC-2 — Deterministic lesson-acceptance rule, written before the worker
runs.** "Validation may include…" is a menu, not a rule. Specify ex ante,
machine-checkable: e.g. a candidate becomes `validated` iff (a) every
evidence ref resolves to a real event in a committed trace, (b) the pattern
is supported by >= 2 distinct sessions, (c) no accepted lesson with
cosine/keyword similarity above a stated threshold (dedup rule), (d) scope
words pass a stated specificity filter. Anything softer (human taste,
"seems supported") moves to the review session, never the pipeline.

**RC-3 — R3 gold-lesson authoring must be blind and protocol-timed.** State
explicitly: R3 lessons are authored from the EXPERIENCE SET ONLY, by a
session that has not seen the transfer-set scenarios, BEFORE the transfer
suite is authored (or at minimum before any transfer inference). Otherwise
R3 silently becomes an oracle arm and the R2-vs-R3 comparison answers a
different question than intended.

**RC-4 — Incorporate the five 2026-10-04 pre-registration amendments by
reference and reuse the v3 protocol machinery.** The proposal predates the
closed cycle's tooling gains: (a) frozen analysis code; (b) label-form
probes; (c) cluster power calc with >= 12–15 clusters; (d) non-executor
gates; (e) wall-time accounting — all five apply. The transfer set should
be a v3-protocol suite (per-seed variant tables, label-form probes,
per-family/per-cluster headroom gates, rendered-digest freeze). Anchoring
note: a lesson like "do not treat prior agent answers as authoritative" is
itself a salience flag on own answers — the cycle-2 anchoring-by-flagging
finding (marking records makes them MORE salient) predicts this can
backfire; lessons must render as plain prose (digest lesson 5), and the
counterfactual bad-lesson test becomes the safety probe for exactly this.

## Recommended (non-blocking)

- **RN-1 — Experience set from existing traces.** The lab already holds
  ~50 committed arm-seed traces (v3i pilot + v3j confirmatory) dense in
  corrections, traps, anchoring failures. Use them as the experience set:
  zero new GPU for experience, and the evidence refs (RC-2a) point at
  already-frozen artifacts. A small fresh supplement is fine if the worker
  needs more NO_LESSON-heavy sessions.
- **RN-2 — Worker model for the main R2 config: a different local core
  (Qwen3.6-35B-A3B), not granite-code:8b.** The proposal's own rationale
  (same-model self-anchoring) points there; the host has it imported; R1
  already covers the deterministic baseline. Same-worker comparison stays a
  secondary.
- **RN-3 — One trigger strategy for the main experiment** (failure-triggered
  post-session), telemetry on the others; a trigger-strategy comparison is
  a separate follow-up, not a second experiment hidden inside the first.
- **RN-4 — Reuse the CONT-002 2×2 machinery for critical test 4** and its
  non-estimable clause (if ΔA ≈ 0, report deltas only). Sequencing (owner,
  2026-10-07): CONT-002 arc first; CONT-006 build reuses its A/B-core
  export/import.
- **RN-5 — Scope guard addition:** R2 implements a NEW worker module; the
  arm-D deterministic reflection (`src/continuity/reflection.py`) stays
  byte-stable as the historical R1 — version or fork, do not mutate.

## What the proposal gets right (for the record)

Session-summarization ≠ reflection, stated up front; NO_LESSON first-class;
lifecycle with challenge/supersede; "no reflection output becomes an active
rule solely because an LLM generated it"; the four critical causal tests
(especially #3 counterfactual bad lessons); explicit interop boundary with
the (now closed) trust work; scope guard against touching closed artifacts.
