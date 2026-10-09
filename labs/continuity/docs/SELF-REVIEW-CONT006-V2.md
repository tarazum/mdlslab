# SELF-REVIEW-CONT006-V2 — implementer self-review of the V2 (rethink) package

- Date: 2026-10-09 (RC-6 chain, step 1 of 4: self-review → Fable → co-owner → owner accept)
- Reviewer: ZCode (the implementing agent) — self-review, so every claim below was re-executed or re-read from raw artifacts this session, not taken from the milestone LOG
- Scope: the RETHINK milestone package (commit 602cf62) — fixtures/v3m + builder/validator, memory discipline (MEMORY_ARMS, combined_channel_smoke, live_telemetry_gate, arm_equivalence_audit), worker v2 bundles, FP-6 cap, power V2, EVALUATION-PREP-CONT006-V2.md + CONT-006-DESIGN-V2.md
- Method per the co-owner's RC-6 requirement: **direct inspection of representative traces/artifacts, not only manifests/digests** — the invalid run's raw trace telemetry was re-read line-by-line; every mechanical gate was RE-RUN (zero GPU); determinism was re-verified by double execution
- Verdict: **GO for the package AFTER folding SR-1..SR-9 below — all nine folded and re-verified this session** (changes in this commit; nothing behavioral ran)

## A. Direct trace inspection (the RC-6 mandate)

**Invalid run, R2/seed-6003 raw trace (results/CONT-006-CONFIRMATORY/cont006-c-20261009-001720):**
- `memory.append` events: **0**. `memory.injected`: 35 events, **every one** with `episode_count: 0, episode_ids: [], injected: false`. `lessons.injected`: 53 events, every one non-empty (`injected: true`, resolved `lesson_ids`, pinned `store_sha256`). This is the CN-012 signature in the raw telemetry, exactly as the audit recorded it: the episodic channel dead, the lesson channel live.
- Arm-seed `summary.json`: `completed: true` with `memory_episodes: 0` — the historical (pre-fix) guard pass-through, now impossible under the run-script memory guard + gate T5.
- R2/seed-6003 `probes_passed: 3/21` — consistent with the recorded invalid anchor 0.267 vs the C2 memory-armed anchor 0.525 (the F-3 signal).

**Worker v2 bundle (cr-FP3a-vce, read directly):** 12 scenario-runs from **12 distinct traces**, fails-first, every digest line carrying the 5-part evidence ref; probe lines show expected/observed/wrong-label. The §7.1(b) ≥2-distinct-traces rule is now satisfiable natively (in the invalid chain only 4/58 candidates had cross-trace support post-hoc).

**Rendered v3m (cu-7101, seed 7001, rendered this session):** fresh world (planetarium), typed sources, R5 supersession markers present; composition matches the v3l plan (3 sessions, probe-in-last-session per validator).

## B. Re-executed verification battery (all zero GPU, this session)

| Check | Result |
|---|---|
| Validator `--suite v3m` | PASS 19/19 (exit 0) |
| Regressions v3/v3h/v3i/v3j/v3k/v3l | PASS ×6 (exit 0 each) |
| build_v3m.py re-run | byte-identical (git clean) |
| live gate on the invalid run | **FAIL 20/20, exit 2** (fail-closed re-confirmed) |
| combined_channel_smoke.py | PASS ×5 (R0/R2/R3/RBAD + identical episodic refs) |
| power_calc_cont006_v2.py re-run | byte-identical; MME 0.20; b0 0.525 (RC-1-corrected 252/480) |
| worker_v2_bundles.py re-run | byte-identical; 8 bundles, 52545 digest chars |
| arm-equivalence audit | PASS (but see SR-1 — artifact was NOT byte-stable) |
| 4-gram counterfactual check | PASS vs v3l (0 hits) — **but did not cover v3m** (SR-9) |

## C. Findings SR-1..SR-9 (all folded this session; re-verified after the fold)

- **SR-1 (freeze-integrity): arm-equivalence-audit.json was not byte-stable.** It embedded `str(render_seed_variant)` — a per-process object address — so every re-run changed the sha256 of an artifact declared for the freeze manifest. After CN-012/F-1, a digest that "just needs re-hashing" on every verification is exactly the drift-accommodation vector this lab is killing. Fold: stable `module.qualname` identity; double-run byte-compare PASS.
- **SR-2 (declared-but-missing machinery): the FP-6 cap existed only in prose.** No lesson→class schema, no cap code, no class-coverage telemetry anywhere in the pipeline; `make_store` accepts any list. "Declared ex ante" without an executor is how V1's gates came to check manifests instead of reality. Fold: `class` field in the lesson schema (worker prompt instructs the tag; FP-6 restricted to reply-formatting lessons), `apply_class_cap` (deterministic keep-first, uniform R2/R3), `class_coverage` telemetry, all in src/continuity/reflection_v2.py; R3 recap now mechanical (SR-2b).
- **SR-2b (the 8→7 arithmetic had no recorded decision):** the R3 gold "capped 8 → 7" was asserted but nothing recorded WHICH lesson drops or why two are FP-6. Fold: gold-lesson-classes.json (all 8 annotated with rationale — LL-G-007 **and** LL-G-008 are FP-6: a bare acknowledgment is a prose reply under the operational definition); recap_r3_v2.py re-validates §7.1 (8/8) then caps (keep-first by lessonId → LL-G-008 drops); artifacts r3-validation-v3.json + r3-store-v2.json (7 lessons, sha 48064a02…, deterministic ×2).
- **SR-3 (missing V2 executor + dead-wrong helper): `run_worker_v2` did not exist** — reflection_v2.run_worker is still the V1 per-trace pass; the prereg's Phase-W-v2 step had no executable path. Worse, `worker_v2_bundles.prompt_for()` replaced @@-tokens that do not exist in the V2 template and left `{bundle}/{digest}` unsubstituted — a landmine returning the raw template. Fold: run_worker_v2(bundles → prompt → parse → §7.1 → cap → telemetry → R2 store) in src; template moved to src (single source); broken prompt_for deleted; bundles artifact byte-identical after the move. The pass itself remains owner-gated (zero inference run here).
- **SR-4 (three contradictory chain orders):** EVALUATION-PREP A.6 (freeze → worker → calibration), A.3 body (worker before calibration) vs A.3 title ("before freeze sign-off") vs DESIGN-V2 §Chain (**calibration BEFORE worker** — impossible: R2 needs the worker store). Fold: canonical order fixed in both docs (worker v2 + R3 recap + contamination gate → calibration pilot → Phase V); A.3 retitled "before the store freeze and any transfer phase"; the ambiguity source (the LOG's «ДО фризу» meaning the STORE freeze, not the protocol freeze) is now explicit.
- **SR-5 (gate verified in ONE direction only; T5 weaker than documented):** the live gate's FAIL direction was verified on the invalid run, but its PASS direction (T2 ref-resolution over real appends, the arm/seed glob, T5) had never executed over healthy traces — a gate that cannot PASS is as useless as one that cannot FAIL. Also the T5 docstring promised "summary memory_episodes matches append count / 2" while the code only checked zero — and the /2 ratio itself is wrong (episodes are 1:1 with append events). Fold: T5 implemented as the real equality (summary exists, completed, episodes == append count, > 0); missing summary = fail; `--self-test` added (FakeProvider healthy R0/R2 root → PASS; CN-012-simulated trace → FAIL; both directions verified, zero GPU).
- **SR-6 (residual parallel list):** `valid_arms` in run_scenario is a literal superset tuple — legitimate (name validity), but drift-silent. Fold: module assert `set(MEMORY_ARMS) <= set(valid_arms)` at every call.
- **SR-7 (checked, no change):** gate NUM_CTX=4096 matches the agent provider default (4096) and run_cont006; the reflector's 8192 is a different, correct context. No inconsistency.
- **SR-8 (stale prose in a freeze artifact):** the power V2 artifact declared its endpoint on "v3l … seeds 6001..6007" — the V2 surface is v3m/{7001..7007}. Same class as the V1 RC-3 lesson (re-grep prose after a rename). Fold: endpoint/notes now name v3m explicitly (design-sized before v3m authoring on the composition-identical plan); artifact regenerated, byte-stable, MME 0.20 unchanged.
- **SR-9 (missing required re-check):** the counterfactual 4-gram non-overlap check still scanned only v3l; V2 requires it against rendered v3m. Fold: script extended to v3l+v3m × all 14 seed-renderings; **run now: PASS, 0 shared 4-grams** (early evidence for the Phase P gate; the check re-runs as a frozen gate at Phase P).

## D. What I could NOT self-verify (honestly declared for the reviewers)

1. **run_worker_v2 executes only under a real provider** — its structure is V1-derived and unit-checked for prompt rendering/cap/telemetry, but no worker call has run under it (owner-gated). The first live execution is the chain's worker v2 pass, after owner accept.
2. **Calibration-pilot numbers** (headroom bands, anchor |R0−0.525|≤0.15) are predictions until the pilot runs; the anchor 0.525 is a CROSS-SUITE base (C2 surfaces, v3i/v3j family mix) — the 0.15 tolerance + halt-and-investigate semantics (never a parameter move) is the declared buffer; out-of-band → new suite, owner consulted.
3. **v3l fixtures reuse in the smoke/gate self-test** (cu-6101) is plumbing-only (FakeProvider, no behavioral inference) — no contamination path into the v3m behavioral phases.

## E. Residual risks I judge acceptable (for Fable/co-owner to challenge)

- The gold class annotation (SR-2b) is implementer-judged, not blind — mitigated: rationale recorded per lesson; the blind protocol applies to lesson TEXT (untouched), not to our classification of it; the cap rule is deterministic given the annotation.
- LL-G-008 (acknowledgment-vs-answer) dropping means the acknowledgment-subclass of FP-6 is uncovered in R3 — accepted consequence of the cap, now explicit instead of silent.
- The gate T4 headroom (512 under 4096) and the smoke's <3500 assertion are heuristics; real v3m prompts with memory+lessons could run hotter than v3l plumbing tests — the calibration pilot's live gate will catch it before any transfer phase.

## F. Chain state after this review

RC-6 step 1 (self-review) COMPLETE with folds SR-1..SR-9. Next: step 2 —
independent review from the standing queue (Fable preferred, then Opus,
then local GLM 5.3 Flash), then step 3 — co-owner review, then step 4 —
OWNER ACCEPT (never-autonomous; no behavioral inference before it).
