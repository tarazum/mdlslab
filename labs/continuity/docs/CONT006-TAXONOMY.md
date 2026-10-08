# CONT-006 failure-pattern taxonomy — FROZEN

Status: **FROZEN for authoring purposes 2026-10-08** (CONT-006 design
milestone, before ANY lesson authoring and before ANY transfer-fixture
authoring — the ex-ante contamination protocol of REFLECTION-V2-PROPOSAL
"Contamination and artifact-freeze protocol" and RC-3 of both reviews). The
freeze manifest at FREEZE time re-digests this file; lesson authors and
transfer-fixture authors work FROM this document only. Edits after lesson or
fixture authoring begins = protocol violation.

Authoring basis (all pre-existing, committed evidence; no new inference):

- the CONT-005-C2 trace corpus (suite v3j; `results/CONT-005-C2-PILOT/
  pilot-c2-20261006-093202` + `results/CONT-005-C2-CONFIRMATORY/
  confirm-c2-20261006-230445`; 50 arm-seed traces; per-class instance counts
  in `experiments/cont006/experience-corpus-manifest.json`);
- `docs/FINDINGS.md` CN-007 (own-answer anchoring; M7 verbatim-parroting
  disposition), CN-008 (supersession semantics absent), CN-003 (temp-0 does
  not fully determinize);
- `docs/ARC-REPORT.md` §3.4/§4.2 (D−C = +0.5015 parroting when reflection
  summaries enter context) and the cycle-2 anchoring-by-flagging risk
  (`docs/RESULTS-DIGEST-2026-10.md`);
- pooled C2 probe outcomes by family (fail rate over all 50 arm-seeds,
  guess probes excluded): correction_reuse **0.695** (278/400),
  repeated_task **0.753** (226/300), contradiction_update **0.360** (72/200),
  distractor_recall **0.180** (27/150), delayed_recall **0.173** (26/150);
  format-miss share of failures: cr 132/278, rt 134/226, cu 3/72, dx 2/27,
  dr 0/26.

## Classes

Each class: **definition** (what the working agent did wrong), **evidence
base** (where it is observed), **lesson hypothesis** (the shape of a good
lesson for it — hypothesis for the reflection worker / gold author, never a
guarantee), **transfer signature** (how a held-out scenario may re-instantiate
the SAME underlying pattern with different surface wording).

### FP-0 — NO_LESSON-heavy (no failure instance)

- **Definition:** a session (or scenario-run) in which no FP-1..FP-6 instance
  occurs: acknowledged facts, chores executed, probes passed or
  legitimately-unanswerable guess probes. The correct reflection output for
  such material is `NO_LESSON`.
- **Evidence base:** the majority of probe-passing turns across the corpus;
  guess_calibration scenarios (300/300 expected-null probes); chore turns.
- **Lesson hypothesis:** none — the class exists so the worker's NO_LESSON
  rate is measurable against material that genuinely has nothing to learn
  (telemetry: sessions_analyzed vs no_lesson_sessions; the proposal's
  "missing lessons" ambiguity).
- **Transfer signature:** none — FP-0 material is never a transfer scenario;
  it appears in the corpus and in the worker input only.

### FP-1 — supersession-resolution miss

- **Definition:** a value was stated, then superseded (corrected, withdrawn,
  or retracted); at probe time the agent asserts the outdated or retracted
  value instead of the governing one.
- **Evidence base:** CN-008 (cu-0001 answered superseded "12" on 3/3 seeds);
  v3j contradiction_update family (fail 0.360 pooled; both mechanisms:
  `superseded_value` — probe expects the NEW value, trap is the old; and
  `retracted_correction` — probe expects the ORIGINAL value, trap is the
  withdrawn correction).
- **Lesson hypothesis:** provenance-aware recency behavior — "when a later
  correction or withdrawal exists in the records, answer with the governing
  value, not the one you recorded first" — WITHOUT quoting the specific
  superseded value (anti-salience).
- **Transfer signature:** a fresh domain states a setting, then amends or
  withdraws it; the probe offers old/new/never-stated options.

### FP-2 — own-answer anchoring

- **Definition:** the agent's own earlier answer (often wrong, seeded by the
  environment) persists at probe time against a standing rule or verified
  correction; the probe answer repeats the agent's prior label.
- **Evidence base:** CN-007 (rt-0003 "bug" 3/3 through arm B/C/D/E; M7:
  strict repeats are VERBATIM copies of the agent's own degenerate answers,
  surfacing when reflection summaries enter context — D−C = +0.5015);
  v3j repeated_task family (fail 0.753 pooled; `scripted_own_answer`
  mechanism) and cr scenarios with `scripted_agent_answer` seeds.
- **Lesson hypothesis:** self-distrust with re-derivation — "your earlier
  classification of an item is provisional; when a standing rule or verified
  notice re-routes it, re-derive the label from the rule instead of
  repeating what you first said."
- **Transfer signature:** a fresh classification task where the agent's first
  (seeded wrong) answer is later contradicted by a rule card; the probe
  re-asks the classification.

### FP-3a — correction-application miss

- **Definition:** a VERIFIED, authoritative correction exists and should
  govern; the agent fails to apply it (answers a pre-correction value or a
  non-correction label).
- **Evidence base:** v3j cr sub-types `valid_correction_environment` /
  `valid_correction_tool` (a verified bulletin/tool output re-routes an item;
  probe expects the corrected label).
- **Lesson hypothesis:** "a verified correction from the authority channel
  amends the record immediately; answer from the amended record."
- **Transfer signature:** fresh domain, verified notice amends a routing; the
  probe asks the routing.

### FP-3b — unverified-source deference

- **Definition:** an UNVERIFIED or conflicting source (erroneous user
  correction, a second source of lower authority) contradicts the standing
  verified rule; the agent follows the unverified source instead of the
  standing rule.
- **Evidence base:** v3j cr sub-types `erroneous_user_correction` and
  `source_conflict`; the CONT-005 trust-hierarchy question this lab already
  studied (which retrieved records to trust) — here it is a FAILURE CLASS the
  working agent exhibits, not a policy to be learned silently.
- **Lesson hypothesis:** "an unverified correction does not override the
  standing verified rule; unless the verified channel confirms, keep the
  rule."
- **Transfer signature:** fresh domain where a casual remark or stale sheet
  contradicts the verified card; the probe asks the governed fact.

### FP-4 — distractor susceptibility

- **Definition:** two similar facts (target + lure) were stated together; at
  probe time the agent picks the lure though the target was explicitly given.
- **Evidence base:** v3j/v3k distractor_recall family (fail 0.180 pooled on
  v3j).
- **Lesson hypothesis:** binding discipline — "when two codes are logged for
  two different things, re-read which code belongs to which thing before
  answering."
- **Transfer signature:** fresh domain logs two codes; the probe asks for one
  with the other among the options.

### FP-5 — storage miss

- **Definition:** a plain stated fact is not retrievable at probe time (no
  correction, no conflict, no distractor — the memory channel simply did not
  carry it or the answer is invented).
- **Evidence base:** v3j/v3k delayed_recall family (fail 0.173 pooled on
  v3j); arm A (no memory) fails these by construction — the class is only
  lesson-relevant for memory-ON configurations.
- **Lesson hypothesis:** weakest lesson candidate — "acknowledge-and-log
  important codes when stated" is a behavior already required; a good worker
  may still emit NO_LESSON here (the failure is capacity/retrieval, not a
  learnable policy). Declared the class where NO_LESSON is often the RIGHT
  output despite visible failures.
- **Transfer signature:** fresh domain states a code; later probe asks it.

### FP-6 — format miss (cross-cutting)

- **Definition:** the reply yields ZERO or MORE-THAN-ONE distinct standalone
  label under the frozen `extract_label` rule — a format non-compliance, not
  a wrong memory (the cycle-1 decomposition lesson: format non-compliance is
  not wrong memory).
- **Evidence base:** empirically HEAVY on the classification families:
  132/278 cr failures and 134/226 rt failures in the pooled C2 corpus are
  format misses (the model replies prose or multiple labels instead of one
  option); recall families are nearly clean (dr 0, dx 2, cu 3).
- **Lesson hypothesis:** "answer closed-option questions with exactly one
  option label and nothing else" — a formatting lesson is a plausible,
  easily-validated, easily-transferred lesson; also the most likely
  BAD-lesson vector (a plausible-but-wrong formatting rule can corrupt every
  probe — the pilot safety check targets exactly this).
- **Transfer signature:** every label-form probe carries the format
  requirement; the class manifests in R0 replies, and a good lesson shows in
  the invalid-format decomposition, not only in pass rates.

## Mapping (family -> class; frozen for corpus labeling and fixture design)

| Suite family / mechanism | Class |
| --- | --- |
| contradiction_update (superseded_value, retracted_correction) | FP-1 |
| repeated_task (scripted_own_answer) | FP-2 |
| correction_reuse: valid_correction_environment / valid_correction_tool | FP-3a |
| correction_reuse: erroneous_user_correction / source_conflict | FP-3b |
| correction_reuse: scripted_agent_answer seeds | FP-2 |
| correction_reuse: retraction (withdrawn correction; original governs) | FP-1 |
| distractor_recall (lure chosen) | FP-4 |
| delayed_recall (fact not recalled) | FP-5 |
| any probe with observed_label null/ambiguous | FP-6 (co-counted, never exclusive) |
| sessions/scenario-runs with no FP-1..6 instance | FP-0 |

Probe fails that do not fit FP-1..FP-6 (e.g., a plain wrong-but-formatted
label on a cr scenario that is neither the seed value nor explainable by the
sub-type) are labeled `FP-X OTHER` in the corpus manifest and reported; the
class list above is closed — no new classes may be invented after lesson
authoring begins.

## Transfer-suite obligations (binding for fixtures/v3l authoring)

1. v3l primary clusters instantiate FP-1, FP-2, FP-3a, FP-3b, FP-4, FP-5
   with fresh surface wording and fresh worlds; every class has >= 2 primary
   clusters or is explicitly declared coverage-reduced in the design doc.
2. FP-6 is exercised by every label-form probe (the invalid-format
   decomposition is a prereg secondary; no separate FP-6 scenarios).
3. FP-0 appears in the experience corpus only; transfer scenarios are
   failure-bearing by construction.
4. Scenario mechanisms reuse ONLY the frozen v3i/v3j/v3k structural
   vocabulary (seed_error mechanisms, initial_expected, lure_value, probe
   kinds) — no new untested mechanics in v3l.
