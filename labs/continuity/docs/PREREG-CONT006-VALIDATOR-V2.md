# PREREG — CONT-006 validator V2 (anti-salience collision resolution)

Stage-2 task 1 (SESSION-BRIEF-CONT006-STAGE2.md §1). Written and committed
BEFORE the collision report is generated and BEFORE the W3 disposition
re-run. Zero GPU throughout; deterministic re-derivation from committed
artifacts only. Frozen `src/continuity/lessons.py` is NEVER edited — the
V2 semantics live in NEW versioned code (`experiments/cont006/lessons_v2.py`).

## 1. What is being audited and why

REVIEW-ASTRA-CONT006-CAPACITY-CONTENT finding 3 + RESULTS Addendum A: the
frozen anti-salience check (`anti_salience_violations`) rejected 5/9 W3
worker candidates on **lexical collisions**, and that rejection selected
NEWF's cr-only coverage as much as the evidence did. This prereg fixes the
V2 rule BEFORE looking at per-candidate outcomes under it, so the re-run
cannot be tuned to a desired disposition.

## 2. Enumeration procedure (mechanical, from committed fixtures)

Re-walk EXACTLY the frozen `_blocked_vocab()` sources — suites v3i/v3j/v3l,
fields: scenario `id`, `seed_error.value` (rendered, template tokens
skipped as in FIX-C), `initial_expected`, per-variant probe `labels` and
`expected` — recording per vocabulary entry its full provenance
(suite, fixture id, field kind, and for label-derived entries whether the
probe spec carries a non-null `expected` = "answerable", or `expected`
null/absent = "expected-null by design", e.g. the guess_calibration
battery). Then classify every single-word blocked TOKEN:

- **C1 structural digit**: the token is a standalone digit 0–9.
- **C2 expected-null option word**: EVERY provenance entry of the token is
  a label of an expected-null probe.
- **C3 retained**: everything else (id words, rendered seed_error /
  initial_expected words, words of answerable probes' options or expected
  answers, world phrases, multi-digit numerals, code-like tokens).

The collision report lists C1 ∪ C2 with provenance (the "colliders" —
ordinary English and structural digits the frozen rule blocks) and C3
counts, plus which C1 tokens are ALSO an expected answer of some
answerable probe variant (declared residual risk, §4).

## 3. V2 rule (pre-registered semantics)

`anti_salience_violations_v2` = the frozen §7.1(d) checks with exactly two
exemptions on the blocked-TOKEN set:

1. **C1 exemption**: standalone digits 0–9 are never blocked as tokens.
2. **C2 exemption**: tokens whose ENTIRE label provenance is expected-null
   probe options are not blocked.

Everything else is byte-identical to the frozen validator: world-phrase
blocks, id/seed_error/initial_expected token blocks, answerable-option
word blocks, `CODE_RE` (`[A-Z]\d{2,4}`), `NUM_RE` (standalone 2+-digit
numerals), and all NON-anti-salience §7.1 logic (evidence refs, ≥2
sessions / ≥2 traces, dedup jaccard ≥ 0.70, lesson length 1–60 words,
applicability, recommendedBehavior, policy denylist) plus the worker-side
class-tag fail-closed and the FP-6 store cap.

## 4. Declared residual risks and the V2 consumption gate

- **C1 residual**: a lesson digit could coincide with a single-digit
  expected answer of an answerable CORPUS probe (the cu-family numeric
  corrections). The corpus-side validator is OVERFIT protection for the
  mining surface; consumption-surface protection was and is a separate
  check — which v1 never did (the capacity-content lessons were validated
  against v3i/v3j/v3l vocabulary but consumed on v3n: declared gap).
- **V2 consumption gate (new, fail-closed, closes that gap)**: before any
  store freeze for consumption, every lesson's checked text
  (title + lesson + recommendedBehavior + applicability) is matched
  against the CONSUMPTION suite's answer vocabulary — rendered variant
  label values and expected answers, scenario ids, world-name phrases
  (same collection procedure as §2 over the consumption suite, all fields,
  no C1/C2 exemptions). ANY hit excludes the lesson from the store
  (reported, not silently). For stage 2 the consumption suite is v3o.

## 5. Re-run procedure (the audited W3 dispositions)

Re-validate the 9 recorded candidates (candidates-v2.json of the frozen
run cont006-worker-v3-20261010-203420, original record order) under
`validate_candidate_v2` with a fresh sequential accepted-list (dedup and
order semantics identical to run_worker_v2), CorpusIndex over the same
experience-corpus-manifest.json. Report per candidate: v1 disposition,
v2 disposition, v2 reasons. Report the would-be store composition under
V2 (class coverage, FP-6 cap application) WITHOUT rewriting any frozen
artifact — the actual stage-2 store comes from the W4 pass (task 3), not
from re-mining W3.

## 6. Non-goals

No change to any frozen file or committed run artifact; no retroactive
re-classification of the W3 store (its 4 lessons stand as executed); no
GPU; no redesign of the multi-word-label phrase semantics (noted as a
future option in the report if the enumeration shows it matters — not
implemented here); the W4 worker prompt and options stay frozen.
