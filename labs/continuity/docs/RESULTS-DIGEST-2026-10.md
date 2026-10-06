# Continuity Lab — results digest (2026-10-06)

Prepared for evaluating an external agent-memory architecture (owner's OCL
project). Everything below is backed by committed artifacts in this repo;
paths given per item. Phone-format: short lines, numbers first.

## What the lab is

Synthetic-world harness around a local LLM (granite-code:8b @ temp 0.0,
Ollama): multi-session scenarios where the agent keeps records, corrections
and retractions arrive, and later sessions probe reuse. Five memory configs:
A = no memory (session-local only); T0 = flat episodic memory (verbatim
record of every exchange, keyword retrieval, top-8 injection); T1 = T0 +
per-record source/verification annotations; T2 = T1 + supersession/conflict
resolution; T3 = T2 + trust-policy header. Pre-registered, frozen analyses,
independent (non-executor) gates throughout.

## Proven results (numbers -> artifact)

1. **Plain episodic memory is a large, replicable win.** Cycle-2 pilot
   (per-family pass rate, 5 seeds): delayed_recall A 0.13 -> T0 1.00;
   distractor_recall A 0.07 -> T0 1.00; contradiction_update A 0.40 ->
   T0 0.95; correction reuse A 0.35 -> T0 0.33 (that family measures error
   propagation, not recall - see 3). Cost: ~2.2x prompt tokens (A ~14.1k vs
   T0 ~31.2k tokens per arm-seed).
   `results/CONT-005-C2-PILOT/pilot-c2-20261006-093202/aggregate.json`

2. **The trust MACHINERY did not beat plain memory - confirmed twice.**
   Cycle-1 confirmatory: T0 vs T2 primary delta -0.100, 95% CI
   [-0.283, 0.000], "no confirmatory difference established" (CI upper bound
   excludes the pre-registered >=0.25 effect).
   `results/CONT-005-CONFIRMATORY/cont005-confirmatory-20261005-123917/results-summary.json`
   Cycle-2 pilot: on contradiction_update T2 scored 0.50 vs T0 0.95 - the
   supersession FLAGS actively hurt. Working hypothesis (both cycles):
   **anchoring-by-flagging** - marking a record as superseded/untrusted makes
   it MORE salient to the model, not less.

3. **Source annotations alone (T1) are the one promising signal.** Cycle-1
   label-level re-analysis: trap repeats A 25/90 > T0 15/90 > T2=T3 10/90 >
   **T1 0/90** - the only config that never repeated a recorded mistake;
   tied-top overall (0.45). Cycle-2 was designed to test exactly this
   (primary contrast T0 vs T1); its pilot surfaced test-material problems
   (see 7) and the confirmatory on rebalanced fixtures is the next step.

4. **The agent's own earlier wrong answer is sticky (anchoring).** Storing
   the agent's own initial misclassification propagates the error through
   memory; self-model summaries, post-session reflection, and a world model
   all FAILED to cure it (CONT-001 arc, `docs/ARC-REPORT.md`).

## Engineering lessons for any memory architecture

5. **Injected markup leaks into answers.** Square-bracket/pipe metadata in
   memory blocks was echoed by the model into its replies, producing invalid
   outputs. Fix: render all injected metadata as clean prose parentheses
   ("(recorded in session N; source: X; verification: Y)"). Residual: even
   "[RESOLVED: ...]" verdict flags leak (~5% of trust-arm replies in the
   cycle-2 pilot) - being moved to plain "NOTE:" prose.
   `src/continuity/claims.py`

6. **Temperature-0 "replicates" are fake unless content varies.** Identical
   prompts -> identical answers (five seeds were effectively one run; one
   flip in 350 requests). Fix: predeclared per-seed variant tables (values,
   codes, probe option orders, names) so each seed runs different content;
   verified working in the cycle-2 pilot (per-seed primary means 0.33-0.58,
   sd 0.095). Power calculations must model between-seed spread.
   `src/continuity/fixtures.py` (render_seed_variant),
   `experiments/suite-v3/validate_fixtures_v3.py` (checks V14-V16)

7. **Test-surface design is load-bearing.** A pooled mean hid a fully
   bimodal surface (cycle-1: T0 pooled 0.50 = 6/8 clusters floored at 1.0
   error + 4/4 ceilinged at 0.0). Pre-declared per-family and per-cluster
   headroom gates caught it in the cycle-2 pilot (0/12 "live" clusters ->
   fixtures rebalanced before the confirmatory, owner-signed).
   `experiments/suite-v3/analyze_pilot_v3.py`

8. **Superseded values must stay in the option set** to measure regression
   (trap-in-labels), and near-miss numeric distractors were still not enough
   to keep the update family hard for flat memory.

## Where OCL-relevant decisions stand

- If OCL has (or plans) conflict-resolution/supersession layers on top of
  flat records: our evidence says do not expect accuracy wins from the
  resolution MACHINERY itself; flags can hurt by salience.
- Cheap per-record provenance metadata is the unconfirmed-but-promising
  middle: zero trap repeats in cycle 1; the proper confirmatory test
  (rebalanced fixtures, prose flags, true seed replicates) runs next.
- Render everything injected into context as prose; keep syntax out.
- Store the agent's own wrong answers carefully - they anchor future errors
  harder than environment facts.

## Status of the T1 test (why "next step")

Cycle-2 pilot GO/NO-GO (frozen rulebook) routed: CU family too easy (both
arms 0.05 error), CR bimodal at cluster level (0/12 live), bracket echo
confirmed. All three fixes go into the held-out confirmatory suite (v3j) at
FREEZE-B (owner sign-off received 2026-10-06); then Fable gate; then the
confirmatory run. `docs/EVALUATION-PREP-v3.md`, `docs/PR-REVIEW-v3.md`,
`docs/GATE-V3A.md`, LOG.md tail.
