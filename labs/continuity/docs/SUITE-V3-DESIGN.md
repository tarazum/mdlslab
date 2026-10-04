# Suite v3 design — fixture families for the CONT-005 cycle

Status: **design document, pre-implementation** (zero GPU). Owner-approved direction
(ROADMAP "Owner decisions" 2026-10-04, item 3 + "Next work package"). Nothing here
touches frozen v1/v2 artifacts or `docs/EVALUATION-PREP.md`. Power numbers quote
`experiments/suite-v3/power-results.json` (script `power_calc.py`, seed 20261004).

## 1. What v2 got wrong — the four diagnosed flaws this design fixes

| # | Flaw (evidence) | Fix in v3 (section) |
| --- | --- | --- |
| F1 | Strict RM lost construct validity: probes carry no label options, so they measure vocabulary+rubric recall; loose RM = 1.0 in every arm; arm A's strict 0.0 reflects *drifting* wrong answers, not error avoidance (`docs/REVIEW-FABLE.md` §2; ARC-REPORT §3.2 sensitivities) | Label-form probes with the label set present at probe time (§3) |
| F2 | 7-cluster bootstrap was structurally weak: with arm A pinned at 0, the observed effect shape (2/7 clusters) had **power ≈ 0.30** (power-results.json, R1) — quantifies the Fable critique | ≥12–15 primary clusters with a design-phase power calculation (§6) |
| F3 | RM eligibility was endogenous to the arm: on rt-0005/rt-0008 arms A/B answered the initial turn correctly (0 eligible) while C/D/E answered wrongly via the injected self-model (5 eligible) — denominators 20 vs 30 compare different scenario mixes (`REVIEW-FABLE.md` finding 1) | Structural eligibility: a scripted seed error identical in all arms (§5) |
| F4 | `correction_reuse` — the family added specifically for CN-007/008 — floored at 0.0 in every arm and diluted the primary denominator while measuring nothing (`REVIEW-FABLE.md` §3c) | CR redesigned as the *primary* family around typed corrections per the CONT-005 proposal (§4.1) |

## 2. Design center: the CONT-005 proposal

Per `docs/research-proposal.md` §CONT-005 (inspirer-authored, frozen): arms T0 (flat
episodic baseline) / T1 (+source-type & timestamp annotations) / T2 (+deterministic
supersession graph, conflict-aware resolution) / T3 (+validated trust policy,
evidence-backed reflection proposals). The suite must contain deliberately unreliable
environmental statements, erroneous user corrections, and later retractions, so that
no arm can win by hard-coding an absolute source ranking. Primary endpoint family:
correction-and-reuse. The proposal's entry gate ("a new fixture version and a pilot
sufficient to establish headroom/variance") is satisfied by this design + the v3 pilot.

## 3. Probe format — label-form with options at probe time

- Every probe presents the full label set in the prompt (`k = 6 ± 2`), e.g.
  `billing | bug | account | data | sync | permissions — reply with the label only`,
  and is scored by deterministic exact match. The vocabulary-recall confound (F1)
  disappears; the task at probe time is purely memory/rubric application.
- **Guessing baseline becomes measurable and the no-memory arm un-pins from 0**:
  with `k` options, a no-knowledge arm sits near `1/k` instead of a degenerate 0, so
  the primary contrast is no longer structurally one-sided (F2) and arm A / T0
  provides its own in-run guessing control.
- Anti-leakage rules (successors of the v2 E8 no-options ban; CN-004 lesson):
  the correct label must not be inferable from surface form — E9–E13 in §9.

## 4. Families and cluster counts (24 scenarios; 1 scenario = 1 bootstrap cluster)

### 4.1 Primary — RM endpoint, 14 clusters

**correction_reuse (CR, 8 clusters).** A seed error is recorded, a typed correction
arrives, then label-form reuse probes in later sessions. Sub-types (2 clusters each,
sourceType per the CONT-005 claim schema):

- **valid correction** (environment / tool / verified reference): the correction is
  authoritative; reuse probes must reflect it.
- **erroneous user correction**: a user "corrects" a fact that verified environment
  evidence supports — blind obedience is the failure (counter-hypothesis arm check).
- **retraction**: a correction is itself later retracted; the original value returns.
- **conflicting sources**: two source types disagree; the pre-registered trust policy
  decides; no arm can win by ranking alone (both orders appear across clusters).

**repeated_task (RM, 6 clusters).** Session-1 records the agent's earlier
classification as a scripted environment statement (identical bytes in every arm),
a rubric correction follows, session-2+ probes reuse. **Construct shift, documented:**
v3 primary measures *propagation of a recorded own-error* (the CN-007 anchoring
mechanism), not an emergent own-error. Emergent initial errors remain interesting
(they were a real harm signal, REVIEW-FABLE finding 1) and stay recorded — as a
secondary metric with per-arm denominators, explicitly labeled (§5).

### 4.2 Secondary — 10 clusters

- **contradiction_update (CU, 4):** keep the v2 3-session structure (it discriminates:
  B 1.0 vs C/D/E 0.5 in confirmatory); probes become label-form old-vs-new value
  choice; doubles as the superseded-fact-usage secondary of CONT-005.
- **delayed_recall (3) / distractor_recall (3):** memory-presence anchors; probes
  become label-form. Their job is sanity/headroom, not the primary.

## 5. Eligibility and denominators

- **Primary RM eligibility is structural**: every CR/RM scenario contains the scripted
  seed error, so the eligible scenario set and denominator are identical in all arms.
  The common-eligible analysis — a sensitivity in v2 — becomes the primary analysis.
- Emergent initial errors (arm's own first answer wrong) are recorded per arm as the
  **secondary** "initial-error rate" (with the F3 caveat printed next to it), never
  pooled into the primary denominator.

## 6. Power (from `experiments/suite-v3/power-results.json`)

| Configuration | Power (two-sided 95% cluster bootstrap) |
| --- | --- |
| R1: K=7, A pinned at 0, effect in 2/7 clusters (v2 retrospective) | **0.304** |
| R2: K=14, uniform Δ=0.40 (0.60 vs 0.20) | 1.000 |
| R2: K=14, uniform Δ=0.30 | 1.000 |
| R2: K=14, uniform Δ=0.20 | 0.934 |
| R2: K=14, uniform Δ=0.10 | 0.453 |
| R3: K=14, effect concentrated in 8/14 clusters (avg Δ≈0.24) | 0.982 |
| R3: K=14, effect concentrated in 5/14 clusters | 0.610 |

Conclusions: (i) the retrospective row quantifies flaw F2 — v2's frozen test had
~30% power for the effect shape it actually observed; (ii) at K=14 the detectable
effect at ~80% power interpolates to Δ≈0.13–0.15, which **justifies keeping
MME = 0.15** as the pre-registered minimum; (iii) sparse concentration (5/14) is
underpowered → **design guardrail E12:** no trust-inert filler in the primary set —
every CR/RM cluster must be one the trust intervention can plausibly move.

## 7. Budget arithmetic (zero GPU; wall-clock per CN-002 / SIZING.md)

Confirmatory v2 measured 1125 requests ≈ 2752 s of arm wall (≈2.45 s/request across
memory arms). v3 ≈ 140 turns/seed (CR 56 + RM 36 + CU 24 + DR 12 + DX 12) →
≈ 343 s/seed/arm → 4 arms × 5 seeds ≈ **114 min GPU**, inside the 3 h cap with
headroom for warmup and retries. Execution order is primary-first (CR+RM), so a
budget overrun trims secondary clusters only, and any such trim must be recorded,
never silent (pre-registered droppable-secondary clause; see
`docs/PREREG-REQUIREMENTS-V2.md` §7).

## 8. What does not change

Append-only event journal + trace validation; deterministic runner with budgets; the
arm-flag mechanism (T0–T3 replace A–E); sampling parameters in every request (PB-071)
and multi-seed spread reporting (CN-003); CN-002 wall-clock budgeting. The fixture
schema extends, not breaks: probes gain a `labels` field, scenarios gain a
`seed_error` block and a `sub_type` tag.

## 9. New validator checks (extend `validate_fixtures_v2.py`)

- **E9** every probe declares ≥5 labels and the label set appears in the probe text.
- **E10** correct-label position rotates across scenarios (no positional pattern).
- **E11** no label string appears verbatim in the stimulus text.
- **E12** exactly 14 primary clusters; every primary scenario declares a sub-type and
  passes the non-inert checklist item at gate review.
- **E13** every primary scenario contains the scripted seed error (structural
  eligibility).
- **E14** a guess-calibration subset exists (≥6 probes about never-stated facts) to
  measure the empirical guess rate and position bias in-run.

## 10. Open questions routed to the CONT-005 review cycle (inspirer-owned proposal)

1. Acceptability of the scripted-own-answer construct for RM (vs emergent-only).
2. Whether CU stays secondary or joins the primary set (its B-vs-C/D/E discrimination
   is the strongest existing signal for trust/supersession).
3. T1 budget-matching mechanics when annotations consume context (proposal requires a
   budget-matched T0 control).
4. Whether the guess-calibration subset doubles as the CONT-002 probe battery
   (deferred with CONT-002 until label-form elicitation exists — this suite is it).
