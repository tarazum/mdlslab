# Session brief — CONT-006 V2 EXECUTION CHAIN (post-accept; the rerun)

For the NEXT working session (fresh context). This brief + the repo are the
complete state carrier; no conversation history is needed. House process:
`labs/continuity/PROCESS.md`; conventions and lessons: `LOG.md` tail
(especially the 2026-10-09 RC-6 entries).

## Entry conditions (verify ALL before any work)

- `git status` clean on `main` at HEAD ≥ the commit carrying this brief;
  ROADMAP contains **"Owner decisions — recorded 2026-10-09 (CONT-006 V2
  pre-registration ACCEPTED; rerun UNBLOCKED; co-owner review step
  WAIVED)"**. That entry is the never-autonomous gate: if it is absent at
  your HEAD, STOP — do not run any inference.
- Binding protocol: `docs/EVALUATION-PREP-CONT006-V2.md` (amendments
  A.1–A.7 + the V2 freeze-manifest list). Design traceability:
  `docs/CONT-006-DESIGN-V2.md` (§Chain is the canonical order).
- Review record (context, all findings already folded — do NOT reopen):
  `docs/SELF-REVIEW-CONT006-V2.md` (SR-1..SR-9), `docs/REVIEW-FABLE-CONT006-V2.md`
  (K-1..K-5, Б-1..Б-7; folded at commits 7450b08 + fa44fd6).
- GPU prerequisites: Ollama 0.34.x up; `granite-code:8b` (working core) and
  `qwen36-35b-a3b:mdlslab` (reflector, digest prefix 8a0fd5da454e) present.
  Budget: ~2.5–3.5 h GPU wall total. If any phase exceeds ~2× the V1 wall
  for the equivalent work, STOP and report.
- v3m ground truth: suite sha256 starts `6c82a3710158fea9`; validator
  `--suite v3m` PASS 20/20 (incl. V18 world-freshness); seeds {7001..7007};
  ids: TR = cr-7001..7004, cu-7101..7104, rt-7201..7203, dx-7401..7402,
  dr-7301..7302 (15); VAL = cr-7005, cu-7105, rt-7204, dx-7403; GC =
  gc-7501..7503.

## Scope (ONE milestone: the V2 execution chain, in the frozen order)

### Step 0 — preflight (zero inference)

`python experiments/suite-v3/run_cont006.py --phase preflight` — env,
warmups, model digest pins must pass. Then re-run the zero-GPU battery and
confirm green: validator v3m + 6 regressions, combined_channel_smoke (6
arms), live_telemetry_gate --self-test, recap_r3_v2 (byte-identical,
r3-store-v2.json sha256 starts 48064a02), check_counterfactual_lessons
(PASS), power_calc_cont006_v2 (exit 0), arm_equivalence_audit (PASS).

### Step 1 — FREEZE V2 (zero GPU; scripts FIRST, then manifest, then commit)

1. Port the run machinery to V2 in `experiments/suite-v3/run_cont006.py`
   (V1 constants → V2; V1's frozen digests are NOT touched by editing the
   current file — the V1 freeze record stays committed in git history and
   in frozen-config-cont006.json):
   - SUITE_DIR → `fixtures/v3m`; ALL_SEEDS → [7001..7007]; PILOT_SEEDS →
     [7001, 7002]; TR/VAL ids per the ground-truth list above; CF_SUBSET →
     positional v3m equivalents [cr-7001, cr-7003, rt-7201, rt-7202,
     cu-7101, dx-7401, dr-7301, gc-7501]; FREEZE_MANIFEST →
     `frozen-config-cont006-v2.json`.
   - NEW phase `W2` (worker v2): mirror the V1 `--phase W` block — warm the
     reflector, digest-pin (8a0fd5da454e), then call
     `continuity.reflection_v2.run_worker_v2(bundles_path=
     experiments/cont006/worker_v2_bundles.json, out_dir=
     results/CONT-006-WORKER/cont006-worker-v2-<ts>, corpus_manifest=
     CORPUS_MANIFEST, base_url=…)`. Outputs: raw-worker-log-v2.jsonl,
     candidates-v2.json, telemetry-v2.json, r2-store-v2.json.
   - NEW phase `CAL` (calibration pilot): R0+R2 × seeds {7001,7002} over
     the full v3m set (TR+VAL+GC), memory ON; R2 store = the W2 output
     `r2-store-v2.json` (pass the W2 dir via `--worker-dir`); run root
     `results/CONT-006-CAL/cont006-cal-<ts>`; reuse run_arm_seed as-is.
2. Port the analyzers to V2: `analyze_pilot_cont006.py` /
   `analyze_confirmatory_cont006.py` — v3l ids/seeds → v3m/7001..7007;
   **MME = 0.20 absolute, band = caveat-only (never moves the MME)**;
   primary unchanged: Δ = S(R2) − S(R0) over the 15 TR clusters; four-branch
   decision rule wording untouched. Change NOTHING else.
3. Write `analyze_calibration.py` (frozen check of prereg A.3; deterministic,
   reads the CAL run root): (1) per-family headroom — every TR family mean
   pass ∈ (0.15, 0.85) for BOTH R0 and R2 (families cr/cu/rt/dx/dr; means
   over both seeds' probes; exact_match probes only, gc excluded);
   (2) anchor — |R0 pooled TR pass − 0.525| ≤ 0.15; (3) live-gate verdict
   file present and PASS; (4) invalid-share (observed_label is None) < 0.30
   per arm; wall feasibility note. Verdict GO / STOP-OUT-OF-BAND with the
   offending numbers. Include `--self-test` on a synthetic run root
   covering: in-band GO, family-band breach, anchor breach (RC-4b
   discipline: self-test BEFORE digesting).
4. Self-test + dry-run every frozen script; then emit
   `frozen-config-cont006-v2.json` digesting the FULL V2 manifest list
   from EVALUATION-PREP-CONT006-V2.md §"Freeze manifest additions (V2)"
   (includes: build_v3m.py, fixtures/v3m + 7 rendered seed digests +
   suite sha, fixture-validation-v3m.json, worker_v2_bundles.py/.json,
   src/continuity/reflection_v2.py, gold-lesson-classes.json,
   recap_r3_v2.py + r3-validation-v3.json + r3-store-v2.json,
   live_telemetry_gate.py, arm_equivalence_audit.py/.json,
   combined_channel_smoke.py, check_counterfactual_lessons.py,
   power_calc_cont006_v2.py/.json, run_cont006.py, both analyzers,
   analyze_calibration.py, counterfactual-lessons.json, the prereg + design
   docs). Commit the freeze as its own commit BEFORE any inference.

### Step 2 — worker v2 pass (GPU, reflector; ~9 calls, expect 10–25 min)

`--phase W2` after `verify_freeze_digests()` passes. Sanity-read
telemetry-v2.json: parse_error_calls explained or 0; class_coverage_store
recorded; dropped_by_fp6_cap ≤ the cap allows. Commit artifacts.

### Step 3 — R3 recap verify (zero GPU)

Re-run `experiments/cont006/recap_r3_v2.py`: r3-store-v2.json must be
byte-identical (sha 48064a02…; inputs unchanged since fa44fd6). If it
differs — STOP, investigate before anything else.

### Step 4 — contamination gate (zero GPU)

4-gram scan of ALL lesson texts (title + lesson + recommendedBehavior) in
r2-store-v2.json AND r3-store-v2.json vs EVERY rendered v3m turn text (all
7 seeds): 0 shared 4-grams required (reuse the tokens/ngrams functions from
check_counterfactual_lessons.py; the counterfactual lessons themselves are
already covered by that script). Commit the verdict artifact.

### Step 5 — calibration pilot (GPU ~15 min) — OWNER CHECKPOINT ARMED

`--phase CAL` → live_telemetry_gate over the CAL root (must exit 0 BEFORE
analyze_calibration.py runs) → frozen calibration verdict:
- **Out of band** (family band or anchor): the chain STOPS. Commit the
  record, write the owner brief, NO v3m edits, NO parameter moves. A NEW
  suite is authored only after the owner decides.
- **In band**: the 4 calibration cells (R0/R2 × 7001/7002) are PART OF THE
  FINAL DATASET (single freeze; CONT-002 pattern). Continue.

### Step 6 — Phase V activation (GPU)

Per V1 machinery on v3m: VAL scenarios, evidence-validated stores
(R2 = W2 output; R3 = r3-store-v2.json); anchor check per A.6
(|S0 − expected memory base| > 0.15 → halt & investigate); activation rule
+0.05 store-level, fail-closed; V-activate produces the ACTIVE stores
(active-store-r2/r3.json) which Phase P/C inject. LIVE GATE over the V root
before anything reads it. Commit.

### Step 7 — Phase P pilot (GPU) — includes counterfactual arms

Pilot seeds {7001, 7002}: R1/R3/RBAD/RGOLD run fresh; R0/R2 cells REUSE
the calibration arm-seeds (single-freeze dataset — resume semantics, never
re-run inference for an existing healthy cell). RBAD/RGOLD inject the
reused counterfactual texts (digest cdc53a4d…; the 4-gram re-check already
PASSes on v3m). LIVE GATE → frozen pilot analyzer → pilot-gate checkpoint:
**OWNER-VISIBLE decision point** (GO / NO-GO / owner-override — prereg §9;
the V1 precedent is the parroting NO-GO that the owner overrode). Do not
start Phase C without the checkpoint outcome.

### Step 8 — Phase C confirmatory (GPU ~1–1.5 h)

Seeds {7003..7007} × all four arms (+ completes any pilot-arm cells the
prereg requires for the final dataset). LIVE GATE → frozen confirmatory
analyzer → verdict. Run record header MUST carry: the CN-012 invalidation
note; the accidental-ablation label of the V1 chain; the PW-OVERRIDE
history; the V2 amendment list (A.1–A.7).

### Step 9 — close-out

Plain-language owner brief (OWNER-BRIEF-TEMPLATE pattern: direct
"підтвердилось / не підтвердилось / стоп" first, math second); LOG entry;
commit; safety scan; push.

## Hard rules (a violation = halt, log, report)

1. LIVE GATE BEFORE EVERY ANALYZER — exit 0 or the analyzer does not run.
2. No v3m edits, no parameter moves, no MME moves (0.20; band caveat-only).
3. Anchor-divergence or family-band breach → halt & investigate; owner
   decides; never "fix" by re-tuning.
4. Freeze-digest guard trips → restore from git, halt, log (PB-075).
5. Memory arms MUST append (T1); run-script guard marks cells invalid
   otherwise — an invalid cell is a STOP, not a skip.
6. Commit per phase; declare any model/tool substitution openly in LOG and
   the run record.
7. Zero behavioral inference before verifying the ROADMAP accept entry at
   your HEAD; zero v3l reuse in any V2 store or surface.

## Non-goals

- Stage B (hosted models) — a separate future experiment, owner-gated.
- V1 artifacts stay frozen as the invalidated chain's record.
- No new review rounds mid-chain unless a gate fires (then: owner routes;
  Fable diff-pass is sufficient per its closing note).

## Deliverables (exit state)

frozen-config-cont006-v2.json + V2-ported run/analyze scripts (digested);
W2 outputs + telemetry; recap verification; contamination verdict;
calibration run + live-gate + frozen verdict (or the STOP record);
Phase V activation + active stores; Phase P run + pilot analysis +
checkpoint outcome; Phase C run + confirmatory verdict + run record;
owner brief; LOG entries; everything pushed.

## Kickoff (paste into the fresh session)

"Прочитай labs/continuity/docs/SESSION-BRIEF-CONT006-V2-EXEC.md і виконай
milestone згідно бріфа. Перевір entry-умови до будь-яких дій."
