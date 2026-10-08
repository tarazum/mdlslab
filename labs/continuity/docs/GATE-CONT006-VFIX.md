# GATE-CONT006-VFIX — non-executor gate verdict (Phase V validator/renderer fixes, BEFORE any result is used)

- **Gate session:** local **GLM 5.3 Flash** (ZCode CLI), fresh context, non-executor (the
  executor that ran Phase V and proposed the fixes is a different session). **THIRD
  position of the standing reviewer queue** (Fable → Opus → local GLM 5.3 Flash).
  **SUBSTITUTION DECLARED (GATE-V3B / GATE-CONT006 / GATE-CONT006-POSTW precedent):
  Fable AND Opus were session-limit-blocked at gate time; the third-position reviewer
  executed this gate.** Python execution EXPECTED and performed live: every number
  below was independently recomputed by this gate from the committed evidence, not
  copied from the executor's briefing (one briefing inaccuracy corrected, VF-6).
- **Date:** 2026-10-08, late UTC (evidence dir `results/CONT-006-VAL/cont006-v-20261008-225347`,
  R3 crash remnants timestamped 20:04:57Z, `total_wall_s` 630.8 in `cells.json`).
- **Scope (prereg §11 infrastructure clause):** two proposed changes to FROZEN
  validation/rendering paths AFTER two of three Phase-V arms completed and BEFORE any
  activation outcome or transfer inference is used. Per
  `docs/EVALUATION-PREP-CONT006.md` §11 — "rendering-related fixes only before any
  inference of the affected stage, with same-commit LOG entry + digest refresh; ANY
  relaxation of a halt-gate or validator goes to the non-executor gate session before
  results are read and appears in the run record header" — FIX-R enters under the
  rendering class, FIX-S under the halt-gate class; both land on this gate.
- **Verdict: GO-with-fixes — FIX-R GO, FIX-S GO, execution plan APPROVED with
  conditions 1–11.** Overall **GO** to: apply FIX-R (budget-fit renderer) + FIX-S
  (invalid-probe semantics), re-run `--phase V-activate` (deterministic, zero
  inference), and re-run the R3 arm-seeds under `--resume-root` (R0/R2 skipped
  verbatim — zero repeated inference), exactly as conditioned below.

Side effects of this gate session: this file only. Nothing committed (executor
commits), no frozen path touched, no inference of any kind performed (no provider
calls, no warm-ups — all verification is offline post-processing over the existing
artifacts).

---

## 1. Evidence verified live (gate's own recomputation)

Evidence: `results/CONT-006-VAL/cont006-v-20261008-225347/` (untracked on disk at
gate time — correct; the executor commits). Working tree `?? results/CONT-006-VAL/`
only; HEAD `b1e914b` (contamination gate GO, Phase V unblocked).

**R0/R2 complete, numbers recomputed from the summaries themselves:**

- R0: 7/7 seeds completed, each summary exactly **4 non-gc probes** (`kind
  exact_match`; no guess_calibration probes exist in VAL), **2/28 passed →
  s0 = 0.0714**. Matches `activation.json`.
- R2: 7/7 completed, **8/28 passed → sx = 0.2857**; sx − s0 = **+0.2143 ≥ +0.05**.
  Per-cluster (gate's own table): cr-6005 2v0, cu-6105 1v0, rt-6204 3v2, dx-6403 2v0 —
  R2 ≥ R0 on **all four** VAL clusters; the signal is broad-based, not single-cluster.
- **Store-integrity guard (prereg §10) holds for R2:** all 7 R2 summaries record the
  identical `lesson_store_sha256` `a15d0206…`, equal to the payload digest of BOTH the
  VAL-dir `r2-store-evidence-validated.json` copy and the worker-v2 store under
  `results/CONT-006-WORKER/cont006-worker-20261008-215103-v2/` (digest chain
  re-hashed by the gate; POSTW condition 7 wiring verified in `env.json.store_dir`).
  R2 store = 4 lessons {LL-W-001, LL-W-012, LL-W-022, LL-W-034}; R3 store = 8 lessons
  {LL-G-001..008} — exactly the POSTW PW-3 verified sets.

**The one vetoing "invalid" R2 probe is a genuine scored reply — verified from the
trace, not the summary:**

- R2 seed-6003, cr-6005, session 3 turn 2: the model replied
  **"Understood. Acknowledged."** — `agent.response` event seq 24, `eval_tokens` 9 of
  num_predict 256 (complete, untruncated), granite-code:8b, temp 0.0, seed 6003.
  `extract_label` yields no standalone label → `observed_label: null`,
  `passed: false`. This is a textbook **FP-6 format-miss**: the agent acknowledged the
  correction without answering the probe. Lessons were injected in all 3 sessions of
  that scenario (telemetry present, store digest matches); the run is a normal,
  complete, scored observation.
- **The frozen code's own asymmetry (decisive for FIX-S):** R0 itself contains
  **EIGHT** observed_label-None probe records (cr-6005 on seeds 6001/6002/6005/6006/
  6007; rt-6204 on seeds 6001/6005/6007), every one **scored as a fail inside s0**,
  and `phase_v_activate`
  computes `inv0` for R0 but **never uses it** — R0's format-misses never veto
  anything. The same event class in R2 both depresses sx (as a fail) AND vetoes
  activation outright. The code treats one class of event as "scored fail" on one arm
  and "run-integrity veto" on the other.
- **Robustness of the activation outcome to the denominator treatment** (gate's
  computation): if format-misses were excluded from denominators instead of scored as
  fails, s0 = 2/20 = 0.100 and sx = 8/27 = 0.2963 → diff = **+0.1963**, still ≥ +0.05.
  The R2 activation decision is invariant to how format-misses are weighted — FIX-S
  is not outcome-engineered on that axis.

**R3 zero-inference — verified exhaustively:**

- All **14** R3 attempt dirs (7 seeds × attempts `seed-600N` + `seed-600N-a2`) contain
  exactly **3 trace events** — `scenario.start`, `session.start`,
  `session.context_reset` — all timestamped 20:04:57Z (both attempts within the same
  second: the crash is millisecond-fast render failure). **Zero** `env.turn`,
  `agent.response`, `probe.result`, `memory.injected`, or `lessons.injected` events.
  All 14 `memory.sqlite3` files contain 0 rows (`episodes` empty). No summary.json in
  any R3 dir. `cells.json`: 7/7 R3 cells `{"completed": false, "attempts": 3}` (the
  loop counter reads 3 after two executed attempts — see VF-5).
- **The crash point and numbers reproduced by simulation** (gate's own code over the
  frozen `retrieve`/`render_block`, real fixture queries): the frozen renderer raises
  on the FIRST session of the FIRST scenario in the plan (cr-6005) for every seed —
  rendered block **200 words** (seeds 6001/6003/6004/6005/6006) and **206 words**
  (seeds 6002/6007) vs budget 165 — exactly the executor's "200/206 words > budget
  165". Every other VAL first-session query also overflows (211 words). R3 top-3
  retrieval always selects 3 lessons (lines 60–70 words each; header 8 words) →
  198–213 words — the overflow is **structural for the R3 store**.
- **FIX-R safety, computed:** R2's max rendered block over all 84 VAL sessions
  (7 seeds × 4 scenarios × 3 sessions) is **138 words ≤ 165** — greedy-fit keeps all
  3 R2 lessons everywhere → **R2/R0 rendering is byte-identical before/after FIX-R**
  (R0 has no lesson channel at all). Greedy-fit on the R3 store keeps **exactly 2
  lessons in all 84 sessions** — never 0, never 3; the largest single R3 lesson line
  is 70 words (header + one lesson = 78 ≤ 165), so the single-lesson hard-error path
  never fires for either frozen store.
- Malformed-probe scan: **0** probe records missing kind/scenario/passed across
  R0+R2 (56 probe records); every seed exactly 4 non-gc probes; all 14 summaries
  `completed: true`, `stopped: false`, no budget violation.
- `activation.json` as written by the frozen code: R2 fail-closed
  ("1 invalid VAL probe(s)") with s0/sx as above; R3 fail-closed (runs incomplete),
  sx null. Active stores currently `status: empty`, 0 lessons; payload digests
  b59963ce… / 2205bc0a… re-verified by the gate through `load_store` (the
  D-PW-7 round-trip fix holds in production use).

## 2. Per-fix verdicts

### FIX-R (renderer budget-fit) — GO

The design's frozen text (§7) sets a budget, not a crash condition: "one dedicated
plain-prose block … budget ≤ 220 tokens total". A budget is enforced by fitting; the
frozen `render_block` instead raises ValueError whenever the top-3 block exceeds the
165-word proxy — which the R3 gold store (8 lessons, 60–70-word lines) triggers on
every possible query. The frozen implementation therefore makes the R3 arm
structurally unrunnable — the arm that design §2 declares the CHANNEL CONTROL for the
whole interpretation grid ("R3 inherits ALL of R2's delivery machinery"; "Neither
helps → do NOT attribute the null to worker quality" requires R3 to have run). This
is the same defect class as POSTW PW-1/D-PW-7: frozen code contradicting the frozen
text, discoverable only on execution. §11's enumerated hotfix class covers it exactly
("rendering-related fixes only before any inference of the affected stage") and the
precondition is verified: **zero R3 inference exists** (§1). The greedy-fit
implementation is deterministic (frozen retrieval score order, tie-break by lessonId
— unchanged), is provably byte-identical for the completed arms (max 138 ≤ 165), and
enforces the design's cap MORE faithfully than a crash. Conditions 1–3 pin the
predicate, the telemetry truthfulness, and the never-empty guarantee.

### FIX-S (activation invalid-probe semantics) — GO

The frozen rule text: "Activate iff SX − S0 ≥ +0.05 AND no validation probe is
missing or invalid **(fail-closed missing-run handling)**". The parenthetical names
MISSING-RUN handling, and prereg §10 repeats only "VAL probes: any missing →
activation fail-closed". Meanwhile the prereg's own framework classifies zero-label
replies as a SCORED observation category, not an invalid run: §14's "invalid-format
decomposition per arm (wrong-answer vs format-miss)" is a declared secondary, and
§9.2's GOLD-TRIV check defines "invalid-format share = probes whose reply yields
ZERO or MORE-THAN-ONE distinct standalone label under extract_label" — the identical
condition — as a measurable SHARE of scored probes whose improvement the experiment
is designed to detect. The frozen `invalid += 1 if observed_label is None` conflates
this reply-format class with run-integrity invalidity; the code's own structure
admits it (inv0 computed and ignored for R0 — §1). The steelman veto reading ("no
valid observation") collapses under its own weight: R0's eight format-misses would
void S0 itself, making the 28-probe denominator of design §6 ("+0.05 on 28
validation probes") a fiction and the activation rule dead on arrival with this
core's documented format-miss rate — not a reading a rule described as "a weak
directional bar BY DESIGN" can sustain. FIX-S restores the only self-consistent
reading: invalid = MISSING (run absent or probe count short) or MALFORMED (record
without required fields); a scored fail (observed_label None, passed False) is a
valid observation that already counts in the rate. The fail-closed intent is
preserved and slightly STRENGTHENED: the missing-run check gains an explicit
probe-count guard (condition 5) that the frozen code lacked (a short-but-present
summary would today compute a rate over a smaller denominator silently). Materiality
is stated plainly, POSTW FIX-B style: without FIX-S the R2 store does not activate on
a +0.2143 broad-based signal because of one prose acknowledgement — the primary
endpoint's R2 arm would then run the declared empty-store branch for a reason that
is a code/text semantics bug, not evidence. That the fix is experiment-preserving is
exactly why it required this gate. Robustness note: the activation decision is
invariant to the denominator treatment of format-misses (§1), so the fix's only
degree of freedom is the invalid/missing distinction itself.

## 3. Execution plan — APPROVED (conditions below)

Apply FIX-R to `src/continuity/lessons.py render_block` and FIX-S to
`experiments/suite-v3/run_cont006.py phase_v_activate` (plus the runner telemetry
truthfulness change, condition 2); refresh the freeze-manifest digests of every
touched frozen path; same-commit LOG entry naming this gate and each fix; snapshot
the evidence the re-run would destroy (condition 4); re-run `--phase V-activate`
over the SAME val_root (deterministic post-processing of the byte-identical R0/R2
summaries — no re-inference); then re-run the R3 arm-seeds with `--resume-root`
(completed R0/R2 arm-seeds are skipped verbatim by `arm_seed_complete` — zero
repeated inference; verified in the frozen resume code path), and re-run
`--phase V-activate` once more after R3 completes so the R3 activation decision is
taken on complete runs. The store freeze (prereg §6) re-fires at the final
V-activate: ACTIVE stores committed before any Phase P/C request.

Expected outcomes (gate's own computation, the executor's cross-check): R2 ACTIVATE
(sx − s0 = +0.2143; active-store-r2.json rewritten from empty to 4 lessons,
status active); R3 VAL behavior under the budget-fit renderer (2-lesson blocks) is
NOT predicted by this gate — it is the thing being measured; no expectation is
recorded.

## 4. Conditions (numbered, binding)

1. **FIX-R predicate pinned exactly:** `render_block(selected)` renders the header
   plus lesson lines GREEDILY in the order returned by the frozen `retrieve()`
   (score desc, lessonId asc — unchanged), including each next line iff
   `header_words + sum(included lines) + next_line_words <= MAX_RENDER_WORDS`
   (165); stop at the first misfit (drop the tail; do NOT skip-and-try-next);
   renumber 1..k. Hard error iff a single lesson line ALONE (header + that one
   line) exceeds the budget — the error predicate is BLOCK-level (header counts;
   design §7 caps the whole block), and it must also fire when `selected` is
   non-empty but NOTHING fits, so a header-only or empty render of a non-empty
   selection is impossible. Verified consequences for the frozen stores: R2 keeps 3
   everywhere (max 138), R3 keeps 2 in all 84 VAL sessions, the hard error never
   fires (max single lesson 70 + 8 = 78). Any deviation from this predicate = new
   gate.
2. **Telemetry truthfulness (runner.py, frozen path):** `lessons.injected` must
   report the RENDERED lesson ids (the kept subset), not the retrieved set — e.g.
   `lesson_ids` = kept, plus `retrieved_ids` and/or `dropped_ids` — and `chars`
   from the actually rendered block. The M2b "was the block actually rendered"
   check and the §14 retrieval-precision secondary read this telemetry; a
   retrieved-but-dropped id reported as injected would silently corrupt both.
3. **Digest + LOG discipline (prereg §11):** refresh the freeze-manifest digests of
   every touched frozen path (`src/continuity/lessons.py`,
   `experiments/suite-v3/run_cont006.py`, and `src/continuity/runner.py` if
   condition 2 is implemented there) in the same commit as the LOG entry naming
   GATE-CONT006-VFIX and defining FIX-R/FIX-S in one line each; the re-run's
   preflight must verify 100% (fail-closed) before any R3 arm-seed starts. Every
   git rev of Phase V execution (original + re-run) in the final artifact header
   (multi-rev clause).
4. **Evidence preserved before the re-run destroys it:** (a) the ORIGINAL
   `activation.json` (the frozen-code fail-closed outcome) is kept — copy to
   e.g. `activation-pre-vfix.json` before the re-run overwrites it; (b) the 14 R3
   crash-remnant dirs are snapshotted (e.g. moved/copied under
   `R3-attempts-pre-vfix/`) BEFORE the resume loop's `shutil.rmtree` deletes them —
   they are the evidence of the frozen-renderer crash (POSTW PW-4 pattern: aborted
   attempts are stated in the final header, not erased); (c) the original `env.json`
   is kept alongside the re-run's (the resume overwrites it with fresh warm-up
   values; derived, but keep the pair).
5. **FIX-S predicate pinned exactly:** for each arm (R0 for s0, and each lesson arm
   for sx — the SAME integrity check applies to R0, symmetrically): a VAL seed is
   VALID iff its `summary.json` exists AND `completed` is true AND its non-gc probe
   count equals the expected 4 (28 per arm per the prereg's "7 seeds, 28 probes")
   AND every probe record has kind/scenario/passed fields. INVALID = any seed
   missing/short/malformed → fail-closed, no activation for that arm (and for R0,
   SystemExit as today). A probe with `observed_label: null, passed: false` is a
   VALID scored fail. Record per-arm invalid/missing counts in `activation.json`
   for all three arms (R0 included, this time actually reported). Any further
   semantic widening = new gate.
6. **Single shot (POSTW condition-4 pattern):** after FIX-R lands, the R3 re-run
   uses the fixed renderer as-is; if R3 arm-seeds still fail, STOP — back to a
   non-executor gate (no further renderer/validator iteration on this evidence).
   The FIX-S V-activate re-run consumes the R0/R2 summaries byte-identically (no
   re-inference, no re-rendering of completed arms — FIX-R is provably a no-op for
   them); if any R0/R2 artifact changed during the re-run, that is a protocol
   violation and the activation is void (verify by digest before/after — condition
   9).
7. **Ordering and the store freeze:** Phase P/C may not launch until BOTH arms'
   final activation states are settled: (i) FIX-S V-activate re-run (settles R2;
   R3 stays fail-closed-incomplete), (ii) R3 arm-seed re-run under resume, (iii)
   final V-activate re-run (settles R3), (iv) ACTIVE stores committed + digested —
   then, and only then, the pilot (which still requires the owner + pilot gate per
   prereg §9/§13 — this gate authorizes nothing beyond Phase V completion). If R3
   completes but lands below −0.05, the active-harm branch fires honestly; if
   between −0.05 and +0.05, the empty-store branch fires — both recorded, neither
   re-litigated.
8. **Provenance embedded (POSTW condition-1 pattern):** the re-run `activation.json`
   carries a provenance block naming GATE-CONT006-VFIX, the two fixes (one line
   each), the pre-fix state (frozen-code outcome: R2 fail-closed on 1
   format-miss at sx−s0 = +0.2143; R3 incomplete on renderer crash; digests of the
   pre-vfix `activation.json` and the two pre-vfix active stores), and the
   pre/post digests of every frozen path touched.
9. **Zero repeated inference — mechanically checked:** the resume must skip R0/R2
   arm-seeds verbatim (`arm_seed_complete`); after the R3 re-run, the executor (or
   the next gate) verifies the 14 R0/R2 trace/summary/memory artifacts are
   byte-identical to the pre-re-run state (digest the trees before and after). The
   only new inference authorized by this gate: the 7 R3 VAL arm-seeds under the
   fixed renderer, plus the standard preflight warm-up calls (2, no arm content).
10. **Run-record notes carried:** (i) R2 renders 3 lessons per block, R3 renders 2
   (wordier lessons) under the same 165-word budget — a declared channel-content
   asymmetry the §2 interpretation grid must carry; (ii) R0's VAL format-miss count
   (8/28) and R2's (1/28) enter the §14 invalid-format decomposition verbatim — the
   FIX-S question was about ACTIVATION semantics only, the scored treatment of
   format-misses as fails is unchanged everywhere; (iii) `cells.json` R3
   `"attempts": 3` records the loop counter after TWO executed attempts — the final
   header states executed attempt counts exactly (template §5); (iv) the briefing's
   "R3 seed dirs contain no trace.jsonl / memory.sqlite3" was imprecise — they
   contain 3-event crash remnants and empty memory DBs (VF-6); the conclusion
   (zero inference) is unaffected and now evidence-backed.
11. **Nothing else moves:** the frozen 165-word constant, `LESSON_TOP_K = 3`, the
   retrieval scoring, the header text, the +0.05 threshold, the −0.05 harm branch,
   the VAL cluster set, and every closed artifact stay byte-identical. The two
   fixes are the complete authorized delta; anything further returns to gate.

## 5. Findings (GATE-CONT006 numbering continued; VF = validator-fix round)

- **VF-1 (root cause, blocking-class, resolved BY this gate's verdicts): the frozen
  renderer enforces the design §7 budget as a crash, making the R3 arm structurally
  unrunnable.** Every possible R3 block is 198–213 words vs the 165-word proxy; the
  crash reproduces on the first session of the first scenario for all 7 seeds (200w
  ×5, 206w ×2). Zero R3 inference existed at fix time (verified exhaustively — §1),
  which is what makes FIX-R legal under §11's rendering-hotfix class.
- **VF-2 (root cause, blocking-class, resolved BY this gate's verdicts): the frozen
  activation code conflates reply-format misses with run-integrity invalidity.**
  `observed_label is None` is the prereg's own FP-6/format-miss scored category
  (§14, §9.2), yet it vetoes activation — asymmetrically, since R0's eight
  format-misses never veto anything (inv0 unused). One prose acknowledgement
  ("Understood. Acknowledged.", 9 tokens, complete) blocked a +0.2143 broad-based
  signal (R2 ≥ R0 on all four VAL clusters).
- **VF-3 (latent guard gap, closed by condition 5): `phase_v_activate` had NO
  probe-count check.** A summary present-but-short (e.g. a budget-stopped arm-seed
  writing fewer probes) would silently compute sx over a smaller denominator. All
  current summaries carry exactly 4/4 non-gc probes, so the gap never fired — but
  FIX-S's MISSING definition must include the count guard, symmetrically for R0.
- **VF-4 (expected outcome, for the record):** post-fix V-activate re-run must show
  R2 s0 = 0.0714 (2/28), sx = 0.2857 (8/28), diff +0.2143 → ACTIVATE, active store =
  4 lessons LL-W-001/012/022/034, status active. Any mismatch with these numbers =
  back to gate. No expectation is recorded for R3.
- **VF-5 (bookkeeping, non-blocking):** `cells.json` attempt counts are loop-counter
  values (R3: "3" after 2 executed attempts; the attempt dirs `-a2` are the ground
  truth). Template §5 requires exact executed counts in the final header.
- **VF-6 (briefing correction, non-blocking):** the executor's briefing said R3 seed
  dirs "contain no trace.jsonl / memory.sqlite3, or only empty attempt remnants" —
  in fact every R3 attempt dir contains a 3-event trace.jsonl and a schema-only
  memory.sqlite3 (0 rows). The zero-inference conclusion was correct and is now
  proven by event-type census + row counts, not by absence of files.
- **VF-7 (observation, non-blocking):** the D-PW-7 store round-trip fix held in
  production — `load_store` verified every store this gate touched (2 evidence
  stores, 2 active stores, chain to the worker-v2 dir), and `activation.json`'s
  digests are payload digests (`store_digest`), not file-bytes digests; consistent
  convention, no integrity issue.

## 6. Verdict

**GO-with-fixes. FIX-R: GO. FIX-S: GO. Execution plan: APPROVED subject to
conditions 1–11.** The executor may implement the two bounded fixes, snapshot the
pre-fix evidence, re-run V-activate (deterministic; R2 expected ACTIVATE at
+0.2143), re-run the R3 arm-seeds under the resume protocol (zero repeated
inference), and take the final V-activate + store freeze. Phase P/C launch remains
gated by the owner and the pilot gate per the prereg — this gate authorizes Phase V
completion only. Any deviation from the pinned predicates, any additional relaxation,
any re-run that touches a completed arm's artifacts, or any mismatch with VF-4
returns to a non-executor gate before results are read.

---

# Appendix — full gate protocol (executed live, this session)

Sequential steps; every computation re-implemented by the gate (no executor numbers
trusted); all offline (zero provider calls, zero warm-ups, zero file writes outside
this verdict file).

1. **Read the frozen texts:** `docs/EVALUATION-PREP-CONT006.md` in full (§7.2
   activation wording, §10 missing-run handling, §14 invalid-format decomposition,
   §9.2 GOLD-TRIV share definition, §11 infrastructure clause); `docs/CONT-006-DESIGN.md`
   §6–§7 (activation formula, "budget ≤ 220 tokens total", "weak directional bar BY
   DESIGN", "28 validation probes"); `docs/GATE-CONT006-POSTW.md` in full (precedent:
   validator-relaxation gate mechanics, conditions patterns PW-1..6, D-PW-7, R-1/R-2).
2. **Results-tree census:** full `find` over
   `results/CONT-006-VAL/cont006-v-20261008-225347/` — R0/R2 7 seed dirs each with
   trace+summary+memory; R3 14 attempt dirs (7 seeds × 2 attempts) with trace+memory
   only, no summaries; top-level activation.json, active-store-r2/r3.json, cells.json,
   env.json, r2/r3-store-evidence-validated.json.
3. **R3 zero-inference proof:** read both attempt traces of seed-6001 in full (3
   lifecycle events each); event-type census over all 14 traces via sqlite/json scan
   (only scenario.start/session.start/session.context_reset present); sqlite row
   counts on 4 representative memory DBs (0 episodes everywhere); cross-checked
   cells.json R3 cells (7/7 incomplete).
4. **Numbers recomputation:** python pass over all 14 R0/R2 summaries — per-seed
   pass/probe counts, format-miss census (observed_label None), per-cluster R0-vs-R2
   table, totals 2/28 and 8/28; confirmed 4 non-gc probes per seed, zero malformed
   records, all completed.
5. **Format-miss forensic:** summary probe record for R2/seed-6003 cr-6005; trace
   `probe.result` payload; the two `agent.response` events of that session (s3t1,
   s3t2 — both "Understood. Acknowledged.", 9 eval tokens, complete); the three
   `lessons.injected` events with store digest match.
6. **Store chain:** `load_store` on both evidence stores and both active stores
   (VAL dir) — source/status/lesson counts (4 and 8, ids match POSTW PW-3); payload
   digests vs `activation.json` entries; VAL-dir copies vs the worker-v2 dir stores
   (identical payload digests); R2 store digest uniformity across the 7 seed
   summaries (store-integrity guard).
7. **Renderer simulation (gate's own code, frozen functions imported read-only):**
   fixture structure census for cr-6005 (3 sessions, turns); frozen `retrieve` +
   `render_block` on the real first-session first-turn query of every VAL scenario ×
   7 seeds — R3: 3 lessons selected everywhere, block 200/206/211 words → ValueError
   everywhere (crash precedes any provider call); R2: max block 138 words over all
   84 sessions (fits → FIX-R byte-identical for R2).
8. **FIX-R safety analysis:** per-lesson line word counts for both stores (R2
   40–47; R3 60–70; header 8); greedy-fit simulation over all 84 VAL sessions ×
   R3 → exactly 2 lessons kept in every session; single-lesson worst case 78 ≤ 165
   (hard-error path unreachable for the frozen stores; never-empty guarantee
   holds).
9. **Activation-robustness cross-check:** alternative-denominator computation
   (exclude format-misses): s0 2/20, sx 8/27, diff +0.1963 — activation decision
   invariant.
10. **Resume-mechanics read:** `run_transfer_phase` resume path (out_root reuse,
    `arm_seed_complete` skip, `shutil.rmtree` of attempt dirs — the evidence-loss
    hazard behind condition 4b), env/cells merge behavior, `cells.json`/`env.json`
    contents (store_kind evidence, store_dir = worker-v2 dir, gc_trim false, wall
    630.8 s, no wall-guard trip).
11. **Verdict written** to this file; nothing committed; no other file touched.

*End of gate record.*
