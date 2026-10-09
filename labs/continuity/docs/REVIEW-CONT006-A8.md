# REVIEW — CONT-006 A.8 diff-pass (2026-10-10)

Model substitution DECLARED: Fable and Opus were both session-limit-blocked
(reset 2:30am Kyiv); the review ran on GLM 5.3 via a ZCode subagent — the
house review queue (Fable -> Opus -> GLM) with the 4th+ GLM substitution
(precedents: D-1, D-PW-7, VF-3, and the GATE-V2B-era substitutions).
Scope: diff-pass per Fable's closing note on the V2 review (machinery
unchanged; only the suite swaps). Reviewer commands: 69 tool uses; the
validator was re-run live by the reviewer (v3n PASS 20/20, regressions x7).

## Verdict: GO-WITH-CHANGES (K-1 critical + K-2..K-6; ALL folded same session — fold log below)

### Fold log (implementer, same session)
- K-1 (critical) FOLDED: check_counterfactual_lessons.py suites map now
  includes v3n {8001..8007} (re-run PASS: 0 shared 4-grams across
  v3l+v3m+v3n, every seed; the print string updated to name all three).
- K-2 (minor) FOLDED: the V3 freeze manifest prereg string now cites the
  ROADMAP owner entry instead of asserting a bare acceptance date.
- K-3 (minor) FOLDED: docs/SESSION-BRIEF-CONT006-V2A-EXEC.md written (v3n
  ground truth: suite sha 9201d710…, seeds 8001..8007, stores REUSED from
  the W2 dir, W2/R3-recap steps SKIPPED per A.8, CF_SUBSET x-8xxx).
- K-4 (minor/observation) FOLDED: carried as a declared reading note in
  A.8 §2 (3/35 cr probe reports carry modifier-position stems from other
  card lines; the head-noun claim holds as worded).
- K-5 (minor) FOLDED: consolidated regression artifact
  experiments/suite-v3/regressions-v3n.json (all 8 suites, verdicts +
  suite shas, committed).
- K-6 (minor) FOLDED: the ported execution files committed BEFORE the
  freeze emission (see the fold commit).

## Raw review (verbatim)

INDEPENDENT REVIEW — EVALUATION-PREP-CONT006-V2-A8 (the v3n amendment), DIFF-PASS scope
Reviewer: GLM (standing house queue Fable -> Opus -> GLM; SUBSTITUTION DECLARED:
Fable and Opus are session-limit-blocked — docs/_fable_a8_review_raw.txt carries
the tombstone "You've hit your session limit"; this review runs in their place).
Date: 2026-10-09/10. Repo: C:\projects\mdlslab. Review-only: no repo file was
edited, created, or deleted by this review (this file excepted). All validator
re-runs were executed WITHOUT --out (no artifact writes).

==============================================================================
TASK 1 — MECHANICAL VERIFICATION
==============================================================================

1(a) Composition. CONFIRMED.
- fixtures/v3n holds exactly 22 scenarios: correction_reuse x5 (cr-8001..8005),
  contradiction_update x5 (cu-8101..8105), repeated_task x4 (rt-8201..8204),
  distractor_recall x3 (dx-8401..8403), delayed_recall x2 (dr-8301..8302),
  guess_calibration x3 (gc-8501..8503) — identical shape to fixtures/v3m
  (cr-7001.. etc.). 15 TR after subtracting the 4 VAL clusters
  (cr-8005/cu-8105/rt-8204/dx-8403, declared in fixtures/v3n/manifest.json
  "validation_cluster_ids" and validator VALIDATION_IDS["v3n"]). ids are all
  x-8xxx; manifest variant_seeds = [8001..8007]. Validator V7-composition PASS:
  family counts {'cr':5,'cu':5,'rt':4,'dx':3,'dr':2,'gc':3}, cr sub-types
  {vce:1, vct:1, euc:1, sc:2} — identical to v3m's plan (CR_SUBTYPES["v3n"] ==
  CR_SUBTYPES["v3m"], validate_fixtures_v3.py lines 145-159).

1(b) Difficulty mechanics in the emitted fixtures. CONFIRMED, per rendered seed.
  (Scripts re-rendered every scenario via continuity.fixtures.render_seed_variant.)

  cr EASIER — "probe reports carry the exact head-noun phrase of one card line":
  the card (BELL_CARD, build_v3n.py lines 84-88) has 6 mutually-exclusive lines
  ("loam builds and cope ramming are moulding; metal taps and ladle melts are
  pouring; ..."). I extracted the s3t2 probe report string for ALL 5 cr scenarios
  x ALL 7 seeds (35 cells) and matched each report against every card line's
  head-noun phrases (plural and singular forms, word-boundary anchored):
  35/35 reports contain a head-noun phrase of EXACTLY the expected card line and
  of no other line (cr-8001/8002 keep the learning report's head noun; same for
  cr-8003/8004/8005). ZERO mapping violations. Residual noise found: 3/35 reports
  carry a MODIFIER-position word whose stem belongs to another line/label —
  see finding K-4 (does not break the claim as worded; the claim is about the
  head-noun phrase).

  dx HARDER — "lure re-confirmed in s2 while the expected is stated once;
  transposition-confusable pairs": verified for all 3 scenarios x 7 seeds
  (21 cells). Rendered counts: expected code appears exactly once in s1 and
  0 times in s2/s3-pre; the lure appears once in s1 AND once in s2
  ("Reminder from the {fuel depot|yard office|estate store}: the {lure_thing}
  code {lure} was re-confirmed this morning and still stands." — build_v3n.py
  line 519) and the s3 opener names the lure's holder ("A {role} arrives from
  the fuel depot run", line 522). Every (code, lure) pair is a true digit
  transposition with a shared prefix (C17/C71 ... C38/C83; M-, S- likewise;
  dx_ladder digits = [(17,71),(23,32),(45,54),(68,86),(19,91),(26,62),(38,83)],
  line 535); lure is always among the probe options; V8R PASS.

  dr HARDER — "two other entities' codes of the same kind logged in s2;
  lure_value = the first interference code": verified for both scenarios x 7
  seeds (14 cells). s2 = "For the log: the {ot1} code is {o1}; the {ot2} code
  is {o2}; all else stands as before. {chore} finished." (build_v3n.py line
  606) with o1/o2 = the two NEXT alphabet entries (same N-/R- code kind,
  different entities — trimmer cabinet / gilt roll stand; hemp sample rack /
  malt proof cabinet). The expected code is stated exactly once (s1), absent
  from s2; "lure_value": "{o1}" (line 613) = the FIRST interference code;
  expected + o1 + o2 all present among the 6 probe options.

  cu/rt/gc mechanics unchanged: confirmed structurally (Task 2) — same
  constructors, same trap mechanisms, new worlds/values only (cu old/new pairs
  47/6, 21/7, 38/5, 14/6, 29/8; rt linen-room card; gc BELL_METALS/TAR_NAMES/
  ICE_TOOLS windows with the same win() arithmetic).

1(c) Validator extension soundness. CONFIRMED. v3n is wired into EVERY suite
  table in validate_fixtures_v3.py: EXPECTED_PRIMARY (line 78), FAMILY_PLANS
  (100), CR_SUBTYPES (154-159), PROBE_CLASS (172, transfer_eligible),
  VALIDATION_IDS (179), the other_suites disjointness map (278), the V1
  variant-seed check (304), and the V18 gate (767: `if suite in ("v3m","v3n")`).
  check_world_freshness's all_suites tuple (line 830) = ("v3","v3h","v3i","v3j",
  "v3k","v3l","v3m","v3n") — the suite under test is compared against EVERY
  other suite, so --suite v3n checks v3n vs v3m (and all earlier), and
  --suite v3m now also checks v3m vs v3n. "--suite" choices derive from
  EXPECTED_PRIMARY keys, so v3n is selectable. The committed artifact
  experiments/suite-v3/fixture-validation-v3n.json: verdict PASS, 20 checks
  (V1,V14,V2,V3,V4,V5,V6,V7,V8,V8R,V9,V10,V11,V12,V13,V14b,V15,V16,V17,V18),
  scenario_count 22, instance_count 154, suite_sha256
  9201d71026451f58189dcbdf3b2740b256d88df2945ac87ae462912ff18323e9 — matching
  the A.8 "PASS 20/20" and "sha256 9201d710...".

1(d) Re-runs (this review, live, no --out). CONFIRMED.
    python experiments/suite-v3/validate_fixtures_v3.py --suite v3n
      -> VERDICT: PASS, exit 0, all 20 checks PASS.
    Regressions: --suite v3m, v3, v3h, v3i, v3j, v3k, v3l -> ALL "VERDICT: PASS"
    (7 regressions — exactly the A.8 "v3..v3m PASS x7"; the v3m run re-verifies
    V18 in the v3m-vs-v3n direction, so BOTH ways are confirmed by my own runs
    on the current tree). Independent digest recomputation reproduces
    9201d710... (v3n) and 6c82a371... (v3m, matching A.1's recorded v3m sha).
    Note (evidence trail): the x7 regression verdicts and the v3m-direction V18
    re-check are recorded only in the commit message of 203fcf0 and LOG.md, not
    as a committed consolidated artifact (the house precedent,
    fixture-validation-regressions-post-v3l.json, exists for v3l) — see K-5.

Basis documents cross-checked: the calibration verdict
results/CONT-006-CAL/cont006-cal-20261010-000940/calibration-verdict.json
matches every number quoted in the prompt/A.8 (family means R0 cr .25 / cu .5 /
rt .3333 / dx 1.0 / dr 1.0; R2 cr .0 ...; anchor PASS 0.5333 vs 0.525; invalid
R0 .1053 / R2 .2105; verdict STOP-OUT-OF-BAND). The diagnostic's trace evidence
is real: R2/seed-7001/trace.jsonl cr-7001 probe.result has
"observed_normalized": "acknowledged.", "passed": false, expected "signaling"
(the 'Acknowledged.' deflection), and 18 trace lines contain 'Acknowledged'.

==============================================================================
TASK 2 — FROZEN-MECHANICS PRESERVATION
==============================================================================

VERDICT: preserved. The difficulty re-aim breaks NO pre-registered structural
invariant; the only structural deltas are the two DECLARED difficulty folds.

Method: I compared the structural skeleton (family, sub_type, seed_error
mechanism, session/turn shapes incl. source_type and probe kind/class,
initial_expected positions, lure_value presence, probe slots/kinds/classes per
variant) of all 22 positional id pairs v3m->v3n (cr-7001->cr-8001 ...
gc-7503->gc-8503).
- cr / cu / rt / gc (16 pairs): structurally IDENTICAL — same sub_types, same
  seed_error mechanisms (scripted_agent_answer / user_override /
  source_conflict / retracted_correction / superseded_value / scripted_own_answer
  as before), same turn shapes, same initial_expected positions (cr_vce_vct s1t1
  = trap; cr_euc/cr_sc s1t1 = expected; rt s1t1 = trap), same probe slots.
- dx (3 pairs): s2 turn gains source_type "environment" (the lure re-confirmation
  reminder). No validator-checked invariant touches this field (V2 requires
  actor == "environment", unchanged). lure_value already present in v3m dx.
- dr (2 pairs): s2 gains source_type "environment" and the scenario gains a
  declared "lure_value" (absent in v3m dr). V8R explicitly supports optional
  declared lures for recall primaries ("a declared lure_value (DX) must be in
  labels, stated pre-probe, and differ from expected") and validates it per
  seed — PASS. This is the A.8-declared fold ("lure_value = the first
  interference code"), not an invariant break.

Invariant-by-invariant (from my --suite v3n re-run over the 154-instance
rendered multiset):
- Trap/seed_error structure (V8): every trap primary instance (CR/CU/RT, all
  seeds) — seed_error valid, trap in labels, trap != expected, trap stated
  pre-probe. PASS.
- V4 label form: >=5 labels, options verbatim in text, "reply with the"
  instruction, for every probe incl. the new dx/dr option sets. PASS.
- V6 no-session-leak: no probe-label word in any probe-session text (options
  stripped) — holds for the new dr s2 interference codes (they live in s2, the
  probe is s3) and for the dx s3 opener (names the holder, never a code).
  PASS.
- V10/V11 probe placement: probes off first turns, primaries >=2 sessions,
  exactly 1 probe, LAST session, class transfer_eligible everywhere. PASS.
- V13 initial_expected: on s1t1 of every primary CR/RT classification scenario,
  drawn from its option vocabulary (the new "For the foundry desk: file this
  report under exactly one label: ..." still matches INITIAL_VOCAB_RE).
  PASS.
- V15/V16 per-seed variation: probe texts pairwise distinct per seed;
  identical-turn share max 0.40 (<= 0.50); per-seed label orders pairwise
  distinct, expected position >=3 distinct slots (dx/dr window rotations
  verified: expected sits at positions {0..5} across seeds). PASS.
- transfer_eligible probe class: all primary probes carry it (V11 + PROBE_CLASS
  wiring). PASS.
- A.3 constants unchanged in the (uncommitted) analyze_calibration.py:
  FAMILY_LO/HI = 0.15/0.85 strict, ANCHOR 0.525, ANCHOR_TOL 0.15 — identical to
  the frozen v3m values; the v3m STOP used the same comparator.
- Counterfactual lesson texts, arms, endpoint, MME 0.20 (MME_D = 0.20 in
  analyze_confirmatory_cont006.py), power artifact (power-results-cont006-v2
  .json untouched per git status) — unchanged.

One design note (not an invariant): in dx the lure and the expected are BOTH
stated in s1 (the s1 learning turn states the target code and the lure-thing
code); "the expected code is stated once" in A.8 means once overall (verified:
exactly once, s1) while the lure is stated twice (s1+s2) plus the holder mention
in the s3 opener — the salience asymmetry is as declared.

==============================================================================
TASK 3 — SUITE-INDEPENDENCE OF THE STORES
==============================================================================

VERDICT: CONFIRMED. The W2 worker pass and the R3 recap never touched v3m/v3n.

- Corpus: experiments/cont006/experience-corpus-manifest.json selection_rule —
  "ALL committed CONT-005-C2 arm-seed traces (the C2 pilot ran suite v3i ids
  x-3xxx, the C2 confirmatory ran suite v3j ids x-4xxx; pilot 25 +
  confirmatory 25) are selected as the CONT-006 experience corpus" — 50 traces,
  none from v3m/v3n.
- Bundles: experiments/cont006/worker_v2_bundles.json — every x-#### token in
  the file is x-2xxx/x-3xxx/x-4xxx (cr/cu/rt/dx/dr/ed families of v3i/v3j-era
  suites); grep for "v3m"/"v3n" in the file: 0 hits.
- Worker class map: src/continuity/reflection_v2.py lines 96-99 —
  _scenario_classes() reads ONLY fixtures/v3i and fixtures/v3j ("id -> taxonomy
  class for every corpus scenario (v3i + v3j fixtures)"); comment line 78:
  "v3i/v3j families only — the corpus is frozen".
- Stores: results/CONT-006-WORKER/cont006-worker-v2-20261010-000332/
  r2-store-v2.json (sha256 66b2ba54..., 5 lessons: LL-W-002 FP-3a, LL-W-003
  FP-3a, LL-W-004 FP-3b, LL-W-005 FP-3b, LL-W-006 FP-1 — exactly the
  diagnostic's "5 lessons, FP-3a x2 / FP-3b x2 / FP-1 x1") and
  experiments/cont006/r3-store-v2.json (sha256 00fc09ca..., byte-identical to
  the V2 freeze manifest's digest "00fc09ca4ea69cdb" in
  frozen-config-cont006-v2.json — the reuse claim is mechanically anchored).
  Neither store text contains any v3m/v3n world vocabulary (tram/depot/
  pantography/foundry/loam/cope/linen/bell/... scan: none) nor any x-7xxx/x-8xxx
  id.
- Contamination, re-verified READ-ONLY by this review (I replicated the gate's
  exact 4-gram scan rather than running contamination_gate_v2.py, which writes
  its verdict file next to the store): against EVERY rendered v3n turn text,
  all 7 seeds — R2 store lessons: 0 shared 4-grams; R3 store lessons: 0;
  counterfactual BAD: 0; counterfactual GOLD-TRIV: 0. The A.8 "pre-checked:
  counterfactual lessons 0 shared 4-grams" claim reproduces, and the W2/R3
  store scan also passes pre-execution. (The wiring gap around WHICH script
  re-checks CF lessons vs v3n at execution time is finding K-1.)
- Byte-identical reuse going forward is tripwired: r3-store-v2.json is in
  FROZEN_PATHS (re-freeze digests it; every phase's preflight re-verifies),
  and the new manifest's R2_evidence string pins the exact worker dir
  (cont006-worker-v2-20261010-000332).

==============================================================================
TASK 4 — CHAIN COMPLETENESS vs A.1-A.7
==============================================================================

The A.8 execution plan is complete and contradiction-free in its declared
scope; three execution-side gaps found (K-1..K-3), none touching frozen
mechanics.

Verified in the (uncommitted) working tree — the v3m->v3n port implements
exactly what A.8 item 4 declares:
- run_cont006.py: SUITE_DIR -> fixtures/v3n; FREEZE_MANIFEST ->
  frozen-config-cont006-v3.json (new kind cont006-freeze-manifest-v3;
  supersedes both earlier manifests, which stay byte-untouched — verified:
  frozen-config-cont006-v2.json has an empty git diff and its r3-store digest
  still matches); ALL_SEEDS/PILOT_SEEDS -> {8001..8007}/{8001,8002}; TR_IDS/
  VAL_IDS/GC_IDS per v3n; CF_SUBSET -> [cr-8001, cr-8003, rt-8201, rt-8202,
  cu-8101, dx-8401, dr-8301, gc-8501] — a byte-for-byte positional match of
  v3m's [cr-7001, cr-7003, rt-7201, rt-7202, cu-7101, dx-7401, dr-7301,
  gc-7501] (sub-types verified pairwise: vce/euc/rt/cu-superseded/dx/dr/gc
  all line up); GC_TRIM_SEEDS -> (8001..8004); content_digests() tripwires
  v3l + v3m + v3n rendered seeds and suite digests; FROZEN_PATHS gains the A.8
  doc, the diagnostic, build_v3n.py, fixture-validation-v3n.json,
  contamination_gate_v2.py.
- contamination_gate_v2.py: --suite {v3m,v3n} parameterization (default v3n),
  seeds map 8001..8007 — "the W2/R3 store scan re-runs at execution" is wired.
- Calibration: analyze_calibration.py keeps A.3 verbatim ((0.15,0.85) strict
  both arms, 0.525 +/- 0.15, live-gate-first, invalid-share < 0.30, wall note);
  CAL phase = R0+R2 x {8001,8002} over TR+VAL+GC, memory ON, R2 = the W2 store.
- v3m CAL cells excluded from the v3n dataset: mechanically true — every
  analyzer/TR list is x-8xxx only, and both analyzers require an explicit
  --run-root (no glob that could silently pick
  cont006-cal-20261010-000940); Phase P's CAL-cell reuse is keyed to the NEW
  cal root via --resume-root (arm-seed resume semantics unchanged from V2).
- Phase V -> P -> C per A.6/A.7: code paths unchanged (same run_transfer_phase,
  same V-activate +0.05 fail-closed activation, same P/C store requirements);
  MME_D = 0.20; power artifact untouched; analyze_pilot CF_SUBSET without
  gc-8501 (RC-5 preserved); analyze_confirmatory CLASS_OF re-derived from v3n
  sub-types (cr-8001/8002 FP-3a, cr-8003/8004 FP-3b, cu FP-1, rt FP-2, dx
  FP-4, dr FP-5 — verified against the fixtures).
- A.8 item 5 (run-record additions): implemented — analyze_confirmatory's
  CARRIED gains "V3M-CAL-STOP" (verdict artifact path, family bands) and
  "CORPUS-COVERAGE" (the diagnostic's reading note, incl. the
  transfer-vs-suppression framing); run_cont006.py docstring carries the STOP
  context and the stores-reuse declaration.
- Routing (item 6): REVIEW-FABLE-CONT006-V2.md's closing note ("досить буде
  дифу фолдів" — a diff suffices instead of a full re-circle) is generalized
  to the suite swap by the recorded owner decision (ROADMAP 2026-10-10: "re-run
  chain (re-freeze on v3n -> Fable diff-pass per its closing note -> ...)");
  the owner gate before any v3n behavioral inference is explicit in the same
  entry. Routing claim stands.

Gaps (details in findings):
- K-1: check_counterfactual_lessons.py (the A.6 Phase P 4-gram gate for the
  CF/BAD/GOLD texts) still scans v3l+v3m only — not wired for v3n.
- K-2: the not-yet-emitted v3 freeze manifest's prereg string asserts
  "A.8 ... owner-accepted 2026-10-10" — anticipatory/false as of this review
  (A.8 is DRAFT; the 2026-10-10 decision authorized authoring, and the ROADMAP
  says behavioral inference "requires the next pre-registration acceptance").
- K-3: SESSION-BRIEF-CONT006-V2-EXEC.md is stale (v3m ground truth sha
  6c82a371..., seeds 7001..7007, v3m id lists, steps that re-run W2/R3 instead
  of reusing the stores). Nothing in A.8 replaces or annexes it for the v3n
  exec session.

==============================================================================
TASK 5 — VERDICT AND FINDINGS
==============================================================================

Prior on the cr-easier lever (explicitly requested): SUFFICIENT ON ITS FACE.
Reasoning: the v3m cr R0 failures were semantic, not format — the diagnostic
and the traces show ordinary wrong-label prose (R0) where the model had to map
a NOVEL paraphrase ("the pantograph round for the dusk trams") onto a
6-category card held in earlier-session memory. v3n removes exactly that
vocabulary gap: the probe report now contains the card line's own head-noun
phrase ("the loam build ...", "the cope ramming ..."), the 12 head-noun
phrases are mutually exclusive in vocabulary, and the remaining demands
(cross-session card recall, resisting the stale trap label, exact-match
format) are the same ones cu/rt already clear at 0.33-0.5. I therefore expect
R0 cr well above the 0.25 floor; in my judgment the more plausible out-of-band
direction is now from ABOVE (cr overshooting mid-scale toward 0.7+) rather
than a repeat floor — the K-4 modifier bleed (3/35 cells) marginally pushes
the other way but cannot re-floor the family. The calibration gate arbitrates
either way; this is design-time intent, correctly framed as such in A.8.

VERDICT: GO-WITH-CHANGES. The suite itself (composition, mechanics, validator
wiring, world freshness, determinism-of-record) is sound and fully verified;
the stores are suite-independent and byte-anchored; the frozen mechanics are
preserved. Every finding below is execution-chain wiring or record hygiene
with a one-file fold. K-1 must be folded before the exec session (a protective
gate scanning the stopped surface is vacuous for v3n); K-2/K-3 before or at
the re-freeze/owner-acceptance commit.

---------------------------------------------------------------------- K-1
K-1. SEVERITY: critical (gate covers the wrong surface; fold before the exec
     session; content itself verified clean today).
  EVIDENCE: experiments/cont006/check_counterfactual_lessons.py, the suites
  map at ~line 110: `suites = {"v3l": (6001..6007), "v3m": (7001..7007)}` —
  the script scans v3l+v3m rendered texts ONLY; its FAIL string still says
  "rendered v3l/v3m text". A.6 makes this script's check a binding Phase P
  gate ("4-gram check re-run against rendered v3m — PASS required"; surface
  now v3n per A.8), and contamination_gate_v2.py's own docstring defers CF
  lessons to it ("the counterfactual lessons themselves are already covered by
  that script") — the --suite v3n gate scans ONLY the R2/R3 stores. Net: at
  execution nobody mechanically re-verifies CF-lesson 4-gram disjointness
  against the live v3n surface; the gate would PASS while scanning the stopped
  chain's suite. (I reproduced the check read-only: 0 shared 4-grams CF-vs-v3n
  across all 7 seeds — the gap is wiring, not contamination.)
  MINIMAL FOLD: add `"v3n": (8001, ..., 8007)` to the suites map (and update
  the two prose strings) in check_counterfactual_lessons.py; alternatively
  extend contamination_gate_v2.py to scan the CF lessons alongside the stores
  for the --suite surface. Commit with the A.8 acceptance so the v3 re-freeze
  digests the extended script.

---------------------------------------------------------------------- K-2
K-2. SEVERITY: minor (record integrity; fold before the re-freeze is emitted).
  EVIDENCE: working-tree run_cont006.py, emit_freeze_manifest():
  `"prereg": "docs/EVALUATION-PREP-CONT006-V2.md (A.1-A.7) + A.8
  (EVALUATION-PREP-CONT006-V2-A8.md; owner-accepted 2026-10-10)"` and the
  module docstring "owner-accepted 2026-10-10, ROADMAP". False as of now: the
  ROADMAP entry of 2026-10-10 ("ок по дефолтах") authorized v3n AUTHORING +
  the diagnostic + arc-continuation and explicitly states "any behavioral
  inference on v3n requires the next pre-registration acceptance
  (never-autonomous clause unchanged)"; A.8's own header is "DRAFT for the
  next review pass + owner acceptance" with "the owner gate follows". If the
  v3 manifest is emitted with this string, its provenance record asserts an
  acceptance (and a date) that did not happen at emit time.
  MINIMAL FOLD: make the prereg string cite the acceptance event without
  hard-coding it ahead of time (e.g. "A.8 owner-accepted — see ROADMAP 'Owner
  decisions' entry for the acceptance record"), or set the actual date when
  the acceptance lands; same for the docstring. (Precedent: the V2 manifest's
  "owner-accepted 2026-10-09" was written after that acceptance.)

---------------------------------------------------------------------- K-3
K-3. SEVERITY: minor (operational; fold before the exec session).
  EVIDENCE: docs/SESSION-BRIEF-CONT006-V2-EXEC.md is the exec-session
  runbook the owner decision points at ("to run in a fresh session per
  SESSION-BRIEF-CONT006-V2-EXEC.md"), and it is entirely v3m-specific:
  ground truth "suite sha256 starts `6c82a3710158fea9`", "seeds {7001..7007}",
  v3m TR/VAL id lists (lines 25-28), re-freeze instructions with v3m ids
  (48-50), and steps 2-4 that re-run the worker pass / recap / contamination
  as NEW runs (92-110) — contradicting A.8's byte-identical store reuse with
  no new worker inference. A.8 provides no v3n replacement or annex; an exec
  session following the stale brief would verify the wrong sha (fail-closed
  confusion at best).
  MINIMAL FOLD: a short v3n annex (or refresh) of the brief: suite sha
  9201d710..., seeds 8001..8007, the v3n TR/VAL/GC lists, "NO W2/R3 phases —
  stores reused byte-identically (r2 66b2ba54..., r3 00fc09ca...)",
  "contamination gate --suite v3n", "CAL = the NEW cont006-cal-<ts> root
  (20261010-000940 is the stopped chain's record)", and the K-1 script fix in
  the confirm-green battery.

---------------------------------------------------------------------- K-4
K-4. SEVERITY: minor (observation; carry as a reading note — a fold would be
     a banned v3n edit).
  EVIDENCE: 3 of the 35 rendered cr probe reports carry a modifier-position
  word whose stem belongs to ANOTHER card line/label: cr-8001 seed 8002 "the
  cope ramming before the morning MELT" (melts -> pouring line); cr-8001 seed
  8007 "the loam build before the POUR" (pour -> the label 'pouring', which
  is also cr-8001's TRAP label); cr-8005 seed 8001 "the clapper store for the
  night CHECK" (checks -> tuning line). The A.8 claim (head-noun phrase of
  exactly one card line) holds in all 35 cells — verified; but the
  DIAGNOSTIC's stronger phrasing ("competing categories share no vocabulary
  with the report") does not hold in these 3 cells.
  MINIMAL FOLD: none to content (frozen; a v3n edit is banned). Record the
  3 cells in the calibration interpretation note so a seed-8007 cr-8001 miss
  pulling 'pouring' is read as residual lexical pull, not store suppression.

---------------------------------------------------------------------- K-5
K-5. SEVERITY: minor (evidence-trail hygiene; optional fold).
  EVIDENCE: the A.8 claims "regressions v3..v3m PASS x7" and "V18 verified
  BOTH ways", but the only committed records of those re-runs are the commit
  message of 203fcf0 and LOG.md — there is no committed consolidated
  regression artifact (house precedent: fixture-validation-regressions-
  post-v3l.json committed exactly this class of evidence for v3l). This
  review re-ran all 8 validations live: PASS, so the claims are true.
  MINIMAL FOLD: at the A.8 acceptance commit, add a one-file
  fixture-validation-regressions-post-v3n.json consolidating the 8 verdicts.

---------------------------------------------------------------------- K-6
K-6. SEVERITY: minor (process hygiene; fold at the acceptance commit).
  EVIDENCE: the five execution-machinery files implementing the swap
  (run_cont006.py, analyze_calibration.py, analyze_pilot_cont006.py,
  analyze_confirmatory_cont006.py, contamination_gate_v2.py) are uncommitted
  working-tree state (git status: 5 modified files). The re-freeze digests
  on-disk bytes regardless of git state, so an uncommitted-drift window
  would be frozen invisibly.
  MINIMAL FOLD: commit these files (with K-1's fix and the A.8/DRAFT->accepted
  status flip) BEFORE the re-freeze is emitted.

---------------------------------------------------------------------- END
Summary of the mechanical record this review independently reproduced:
validator --suite v3n PASS 20/20 (exit 0); regressions v3m/v3/v3h/v3i/v3j/
v3k/v3l ALL PASS; suite sha256 9201d710... matches; cr head-noun mapping
35/35; dx salience/transposition 21/21; dr interference/lure=o1 14/14;
structural skeleton delta = the two declared folds only; stores corpus-clean
(v3i/v3j only) and 0 shared 4-grams vs every rendered v3n text for R2/R3/CF;
A.3 constants and MME 0.20 unchanged; V2 freeze manifest untouched with its
r3-store digest still matching. GO-WITH-CHANGES per findings K-1..K-6 above.

