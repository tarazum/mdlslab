# CONT-006 design — Reflection as Lesson Extraction (R0/R1/R2/R3 on suite v3l)

Status: DESIGN for pre-registration. Behavioral and worker runs are **never
autonomous** (ROADMAP); they start only after the owner accepts
`docs/EVALUATION-PREP-CONT006.md` (which itself requires an independent
PR-REVIEW pass first). Zero GPU in this milestone. Basis:
`docs/REFLECTION-V2-PROPOSAL.md` (both reviews folded: RC-1..RC-5 +
RC-1..RC-4), `docs/CONT006-TAXONOMY.md` (FROZEN),
`experiments/cont006/experience-corpus-manifest.json`, suite v3l
(`fixtures/v3l`, builder `build_v3l.py`, validator PASS 19/19 +
regressions v3..v3k PASS ×5), power artifact
`experiments/suite-v3/power-results-cont006.json`.

## 1. Research question

Does an asynchronous evidence-backed reflection worker, analyzing ALREADY
COMMITTED experience traces, produce validated lessons that improve the
working agent's performance on **novel but structurally related tasks**
(same failure patterns, different surface wording), compared with no
lessons — and is any improvement attributable to the LESSON CHANNEL
(manual gold lessons through the identical machinery) versus the WORKER's
extraction quality?

**Primary endpoint (candidate, binding text in the prereg):** the
label-form pass-rate delta **Δ = S(R2) − S(R0)** over the 15 v3l primary
transfer clusters (7 seeds each), where S(arm) = mean probe pass rate of the
arm; cluster bootstrap two-sided 95% CI; MME **0.20** absolute (power
artifact: the smallest 0.05-step effect detectable at ≥ 0.80 on the
conservative row — 0.15 gives only 0.660; effects below 0.20 are not
claimable at this design's power, declared limitation; 0.20 also clears the
template §9 guessing-band floor).

## 2. Arms

| Arm | Working config | Lesson source | Reflection |
| --- | --- | --- | --- |
| R0 | granite-code:8b (`36c3c3b9683b…`, CN-001), persistent episodic memory (the existing runner arm-B behavior), think-pinned provider | none | none |
| R1 | same as R0 | none | current deterministic MVP `src/continuity/reflection.py` — **byte-stable historical baseline**; in-run summaries render into later sessions (the CONT-001 arm-D behavior) |
| R2 | same as R0 | **worker-generated**: async reflection worker over the frozen experience corpus → deterministic evidence validator + dedup → generalization activation (§6) → ACTIVE store injected through the lesson channel | separate process |
| R3 | same as R0 | **manually authored gold lessons** (blind protocol §8) through the SAME activation rule | none |

**R3 inherits ALL of R2's delivery machinery** (proposal RC-1): the same
lesson retrieval code, prompt slot, prose renderer, token budget, validator
contract and lifecycle. ONLY the lesson source differs. Manual lessons pass
the same evidence/schema/scope validator as worker lessons — the authoring
session must cite corpus evidence the same way.

**Interpretation grid (pre-declared):** R2 helps ≈ R3 → the worker does
useful semantic work. R3 helps but R2 does not → the channel is viable,
automatic extraction is weak. Neither helps → do NOT attribute the null to
worker quality: the delivery channel itself may be ineffective (R3 is the
channel control; the pilot's trivially-useful gold lesson is the
manipulation check that the channel can move behavior at all). R1 ≤ R0 is
declared ex ante as the expected REPLICATION of the CONT-001 parroting
signal (D−C = +0.5015; ARC-REPORT §3.4/§4.2) — a minus for R1 reads as
replication, not anomaly (review waitlist item).

Pilot-only counterfactual arms (never in the primary analysis): **BAD** =
one plausible-but-wrong lesson injected through the normal channel (safety
check: no blind parroting; challenge/supersede path observable) and
**GOLD-TRIV** = one trivially-useful gold lesson (manipulation check:
delivery can influence behavior at all) — critical test 3, assigned to the
pilot.

## 3. Data split and the two-phase rule

1. **Experience set (frozen, committed):** ALL 50 CONT-005-C2 arm-seed
   traces (suite v3i pilot 25 + v3j confirmatory 25), selected + digested +
   taxonomy-labeled by `select_experience_corpus.py`
   (`experiments/cont006/experience-corpus-manifest.json`; sha256 6f8f885a… (re-emitted at the
   PR-REVIEW fold, N-4);
   pooled failure classes FP-1 118, FP-2 226, FP-3a 129, FP-3b 103, FP-4 27,
   FP-5 26, FP-6 271 — every class covered; the fresh-supplement rule does
   not fire). Reserve NOT selected: CONT-001-confirmatory (v2 free-form
   probes; PR-REVIEW note-2 label-form caveat — cited as taxonomy evidence,
   not worker input).
2. **Validation set:** the 4 v3l VALIDATION clusters (cr-6005, cu-6105,
   rt-6204, dx-6403; validator V17). Activation decisions ONLY; never part
   of the primary endpoint; its seeds never enter the primary analysis.
3. **Held-out transfer set:** the 15 v3l PRIMARY clusters (CR×4 FP-3a/3b,
   CU×4 FP-1, RT×3 FP-2, DX×2 FP-4, DR×2 FP-5) + GC×3 (guess band).

**Two-phase rule (RC-2, binding):** NO lesson injection during experience
accumulation. Trivially satisfied here — the experience corpus is already
committed — and re-stated as the binding rule for any future fresh
supplement: all four arms share the SAME experience traces; arms differ
only at the transfer phases. No lesson is ever evaluated on the exact
scenario that generated it (v3l is a fresh suite, mechanically disjoint by
validator V3 from every prior suite, every seed both ways).

## 4. Reflection-worker architecture

- **Separate process, different core (preferred R2 configuration):**
  reflector `qwen36-35b-a3b:mdlslab` (digest `8a0fd5da454e…`, M2b/CN-001
  pin), temperature 0.0, top-level `"think": false` pin inherited from
  `OllamaProvider` (the CONT-002 owner-approved fix — hybrid reasoning cores
  otherwise return empty visible replies at num_predict 256), sampling
  options in every request (PB-071). Worker identity (model + runtime
  digest), full reflection prompt/template and sampling config are
  digest-frozen in the freeze manifest BEFORE the worker runs.
- **Same-core reflector** (granite as reflector) is a declared
  negative-control/comparison for same-model self-anchoring — exploratory
  only unless separately pre-registered (proposal; both reviews).
- **Trigger strategy (frozen, one only):** post-experience single batch.
  ONE worker pass over the whole frozen corpus (session-level evidence
  bundles grouped by scenario-run; one call per bundle; batch semantics:
  the worker may inspect MULTIPLE sessions when looking for repeated
  patterns). Trigger-strategy comparison is exploratory follow-up work.
- **Input bundle per session (proposal "Reflection input"):** the rendered
  environment turns, the agent's answers, probe results (expected vs
  observed, pass/fail, format validity), corrections/retractions with
  source types, the taxonomy class label of the scenario (from the corpus
  manifest), and provenance (run/arm/seed/scenario/turn ids). Previously
  active lessons: EMPTY at worker time (two-phase rule). Self-model state:
  not part of v1 worker input (declared; the deterministic self-model is R1
  machinery).
- **Outputs (first-class):** `NEW_LESSON` / `UPDATE_LESSON` /
  `CHALLENGE_LESSON` / `SUPERSEDE_LESSON` / **`NO_LESSON`** — NO_LESSON
  distinguishes "no useful lesson found" from "the agent forgot to update
  lessons learned" (the proposal's core observability claim; telemetry
  below).
- **Raw worker log (artifact, never replaced by telemetry):** every
  candidate and rejection recorded with prompt digest + response hash per
  call; telemetry is DERIVED from this log. The log is committed before any
  validation/transfer inference.

## 5. Lesson schema + lifecycle (two validation meanings)

Schema fields (proposal §"Candidate lesson schema", adapted): `lessonId`,
`status`, `title`, `context`, `observation`, `lesson`, `applicability`
(conditions), `recommendedBehavior`, `evidence` (trace refs: run/arm/seed/
scenario/turn — IDS ONLY, never quoted content), `createdBy`
(reflection-worker | gold-author), `createdUtc`, `supersedesLessonIds`.

Lifecycle: `candidate → rejected | evidence-validated → active | rejected`
(+ `challenged` / `superseded` / `retired` post-transfer, recorded but not
exercised by the main experiment). No reflection output becomes active
solely because an LLM generated it. The two validation meanings (review
finding; separated explicitly):

1. **Evidence validation — deterministic, pre-inference, zero GPU.** A
   candidate passes iff ALL pre-written machine-checkable rules hold:
   (a) every cited evidence ref resolves to a real event in a committed
   corpus trace; (b) the claimed pattern is supported by ≥ 2 distinct
   sessions in ≥ 2 distinct arm-seed traces; (c) dedup: no accepted lesson
   with Jaccard word-overlap ≥ **0.70** over (title + lesson) text; (d)
   specificity/scope: ≤ 60 words, states an applicability condition and a
   recommended behavior, and does NOT name specific scenarios, ids, codes,
   label values or worlds (surface-independence is what transfer tests —
   an overfit lesson is rejected here, not discovered later); (e) policy
   boundary: cannot modify permissions, safety policy, tool authority or
   hidden runtime policy. Rejections stay in the raw log with reasons.
2. **Generalization validation — empirical, frozen activation rule (§6),
   evaluated on the VALIDATION clusters BEFORE any transfer inference.**

## 6. Activation rule (generalization validation, frozen formula)

Store-level, per lesson SOURCE (the R2 worker store and the R3 gold store
are activated independently by the SAME rule): with S0 = mean label-form
pass rate of R0 on the 4 validation clusters (7 seeds) and SX = the same
for the lesson-carrying arm (R2 or R3) on the identical rendered content:

- **activate** iff SX − S0 ≥ **+0.05** (the store's lessons generalize
  enough to keep);
- **do not activate** iff SX − S0 < +0.05, or any validation probe is
  missing/invalid (fail-closed; missing-run handling), or SX − S0 ≤ −0.05
  (active harm signal on validation — recorded, store stays out of the
  primary).
- If not activated, the arm STILL RUNS the primary with an EMPTY active
  store (declared branch: the arm is then R0-equivalent by construction;
  the honest verdict "no confirmatory difference" fires; the R2-vs-R3
  comparison carries the extraction-vs-channel interpretation). Stores are
  frozen + digested immediately after activation, BEFORE the first transfer
  request (regeneration after transfer inference begins = protocol
  violation).

Threshold rationale: +0.05 on 28 validation probes is a weak directional
bar BY DESIGN — activation is a safety/generalization check, not a second
endpoint; the confirmatory claim remains the pre-registered TR-cluster
contrast at MME 0.20.

## 7. Retrieval, rendering, anti-salience (shared by R2/R3)

- **Retrieval (frozen code):** at session start of every transfer session,
  the active lessons are retrieved by keyword query against the session's
  first turn (the existing memory-retrieval interface pattern); per-session
  retrieval telemetry (which lessons rendered) is recorded per probe — the
  "was the lesson actually injected" check (M2b precedent).
- **Prompt slot + renderer (frozen digest):** one dedicated plain-prose
  block ("Lessons learned in earlier work") in the system/context prompt,
  budget ≤ **220 tokens** total (the memory-block budget discipline);
  lessons render as prose sentences — status + title + lesson +
  applicability condition. No JSON, no quoting.
- **Anti-salience rule (RC-4, binding for BOTH worker and gold lessons):**
  imperative behavioral form; the lesson text must NOT quote or repeat the
  agent's wrong answer, specific label values, or scenario content (same
  rule as evidence-validation (d) — enforced mechanically); evidence links
  are ids pointing into the corpus manifest; the harmful content stays in
  the evidence artifact, never in the injected text. This responds directly
  to the parroting channel (D−C = +0.5015) and anchoring-by-flagging risk:
  a lesson is a rule about BEHAVIOR, not a flag on specific answers.

## 8. R3 blind gold-lesson protocol (RC-3 of both reviews)

R3 gold lessons are authored in a SEPARATE session that sees: the frozen
taxonomy, the corpus manifest + the experience traces, and the lesson
schema/validator contract. It must NOT see: v3l fixtures (any seed), the
transfer scenarios, this design's v3l sections, or any worker output. R3
lessons pass the SAME evidence validation (§5.1) and the SAME activation
rule (§6). Ordering: R3 authoring may run before or after the worker pass
(they are independent) but MUST complete before the store freeze; the
non-executor contamination gate verifies the authoring session's inputs.

## 9. Suite v3l (authoring complete, validator PASS 19/19)

`fixtures/v3l` (builder `build_v3l.py`, deterministic re-run verified;
validator `--suite v3l` PASS 19/19 (19 check records; V8 and V8R are
separate records — the milestone LOG's "18/18" was a miscount, corrected
at the PR-REVIEW fold, RC-4) incl. V8 mixed dispatch + V17 validation
split; regressions v3/v3h/v3i/v3j/v3k PASS ×5;
`fixture-validation-v3l.json` committed). 22 scenarios, 103 turns/seed,
seeds {6001..6007} predeclared, ids x-6xxx, fresh worlds, rendered texts
disjoint from ALL prior suites (V3, every seed both ways). Composition:
15 primary transfer clusters (class `transfer_eligible`) instantiating the
taxonomy classes with different surface wording — CR×4 (FP-3a ×2 via
valid-correction sub-types, FP-3b ×2 via erroneous-user/source-conflict),
CU×4 (FP-1: superseded ×2 + retracted ×2), RT×3 (FP-2), DX×2 (FP-4),
DR×2 (FP-5); every class has ≥ 2 primary clusters (taxonomy obligation).
4 validation clusters (same families, V17-pinned). GC×3 (6 never-stated
probes; the working core's guess band, template §9). FP-6 (format miss) is
exercised by every label-form probe; the invalid-format decomposition is a
prereg secondary. Structural vocabulary inherited from frozen suites only
(v3i/v3j mechanisms + initial_expected; v3k lure_value/windows; no new
mechanics).

## 10. Aggregation and decision rule (summary; binding text in the prereg)

Unit: cluster = scenario; per arm, cluster mean over its 7 seed-variant
probes; Δ_c = S(R2,c) − S(R0,c); Δ = cluster means. Two-sided 95% cluster
percentile bootstrap (10k-equivalent, RNG seed frozen at freeze). Verdict
branches (frozen wording): CI excludes 0 upward AND Δ ≥ 0.20 →
"lesson transfer established"; CI > 0 and Δ < 0.20 → "directional
improvement below the minimum meaningful effect"; CI excludes 0 downward →
"lessons actively hurt"; else → "no confirmatory difference established".
R3−R0 and R1−R0 with CIs are SECONDARY contrasts (never promoted; the
interpretation grid §2 reads them but the primary verdict is R2−R0 only).

## 11. Critical causal tests (placement)

1. **Remove episodic answers, keep lessons** — bounded follow-up cell
   (lessons-only config), exploratory unless separately pre-registered.
2. **Keep episodic, remove lessons** — this IS the R0 cell; the R2−R0
   primary measures exactly the lesson delta on top of memory.
3. **Bad-lesson injection + trivially-useful gold** — PILOT (BAD and
   GOLD-TRIV counterfactual arms, seeds {6001,6002}, excluded from the
   primary by design).
4. **Cross-model lesson transfer** — bounded later stage AFTER the
   confirmatory: reuse the PROVEN CONT-002 four-cell machinery (run_cont002
   pattern, export/import, digest pins) with core B = qwen36-35b-a3b as the
   working core; predeclared subset (2 patterns × 2–3 seeds), its own GPU
   budget, and the inspirer's non-estimable clause (ΔA gate; deltas-only
   reporting in the non-estimable branch). Never allowed to inflate the
   main experiment.

## 12. Feasibility (zero new inference; anchors from committed runs)

- Transfer phases: 4 arms × 7 seeds × 103 turns ≈ 2,884 requests; the C2
  confirmatory measured ~2h16m for a comparable 25 arm-seed × 130-turn
  load on granite → est. **~1.8–2.5 h GPU**; cap 5 h with wall guard
  (CONT-002 runner pattern).
- Validation phase: 3 arms × 7 seeds × 4 clusters (~19 turns) ≈ 400
  requests ≈ **~20 min**.
- Worker pass: ONE batch ≈ 50 session-bundles × 1–2k tokens on the qwen
  reflector ≈ **≤ 1 h** (batch trigger per review §6; a failure-per-session
  trigger would be 3+ h — rejected for v1).
- Pilot extras (BAD/GOLD-TRIV): 2 counterfactual arms × 2 seeds × a
  predeclared subset ≈ ≤ 30 min.
- R1 is free (deterministic MVP, already implemented).

## 13. Contamination and artifact-freeze protocol

The worker + stores are a reproducible artifact chain (proposal; FREEZE-A/
FREEZE-B discipline; the 2026-10-04 amendments):

```
frozen taxonomy (committed 2026-10-08, digest in corpus manifest)
  → frozen experience corpus (committed traces + digests)
  → worker pass (config/prompt/model digested) → raw candidate log
  → deterministic evidence validator + dedup (code digested)
  → evidence-validated stores (R2 worker; R3 blind-authored)
  → generalization activation on VAL clusters (frozen rule §6)
  → ACTIVE STORES COMMITTED + DIGESTED  ← store freeze
  → pilot (TR; bad-lesson + gold checks) → pilot-gate checkpoint
  → confirmatory (TR; all four arms)
```

Freeze discipline: the taxonomy was frozen BEFORE lesson authoring and
BEFORE transfer-fixture authoring (this milestone's authoring order; the
corpus manifest embeds the taxonomy digest as ordering evidence); R3
authors see experience-set material only; the transfer suite is committed
BEFORE any behavioral inference and no post-pilot fixture edits are allowed
(any rebalance = a NEW suite + fresh review); active stores are digested
before the first transfer request; worker identity, prompts, validator/
dedup/retrieval/renderer code, analysis code, and rendered-suite digests
all enter the freeze manifest; a NON-EXECUTOR contamination/freeze gate
runs before transfer inference (standing reviewer queue).

## 14. Out of scope (this milestone and the pre-registered experiment)

No inference of any kind (never-autonomous; owner gate first); no
`src/continuity/reflection.py` mutation (R1 stays byte-stable; Reflection
v2 is a NEW versioned module — RN-5); no edits to closed CONT-001/
CONT-002/CONT-005 artifacts, frozen configs, closed suites, or the proposal
and its review files; trigger-strategy comparison, same-vs-different
reflector comparison, tests 1 (lessons-only cell) and broad cross-model
portability are exploratory unless separately pre-registered; test 4 is a
bounded later stage with its own budget.
