# GATE-CONT006-CONTAMINATION — contamination / store-freeze gate verdict (BEFORE Phase V)

- **Gate session:** local **GLM 5.3 Flash** (ZCode CLI), fresh non-executor
  context. **THIRD position of the standing reviewer queue**
  (Fable → Opus → local GLM 5.3 Flash). **SUBSTITUTION DECLARED (GATE-V3B /
  GATE-CONT006 / GATE-CONT006-POSTW precedent): Fable AND Opus were
  session-limit-blocked at gate time; the third-position reviewer executed
  this gate.** Python execution EXPECTED and performed live: every number
  below was recomputed by this gate's OWN code from the committed evidence
  (independent re-implementation, nothing copied from the executor).
- **Date:** 2026-10-08, evening UTC (after commit `8991027`, the Phases
  W+G / POSTW-fix commit; HEAD at gate time; working tree clean).
- **Scope (prereg §12 "Contamination gate (before Phase V)" + §8 "R3 blind
  gold-lesson protocol"):** verify (1) no v3l content in any lesson text
  (independent mechanical re-run of §7.1d), (2) the R3 authoring session's
  blindness, (3) the worker prompt's input set, (4) store-freeze ordering
  readiness (§7.2: ACTIVE stores cannot exist yet; VAL/PILOT/CONFIRMATORY
  must not exist), (5) chain integrity (taxonomy nesting, provenance,
  freeze-manifest re-hash), (6) counterfactual-arm isolation.
- **Verdict: GO** for launching Phase V (behavioral inference — R0/R2/R3 on
  the 4 validation clusters, seeds {6001..6007}) and, on its completion, the
  V-activate store freeze.

Side effects of this gate session: this file only. Nothing committed (the
executor commits), no frozen path touched, no inference of any kind
performed, no file under `labs/continuity/` modified.

---

## Check 1 — NO v3l CONTENT IN ANY LESSON TEXT — PASS (0 hits)

**Targets scanned (canonical Phase-V inputs + the blind authoring file):**

| File | Lessons | v3l scenario-id anywhere in file |
| --- | --- | --- |
| `results/CONT-006-WORKER/cont006-worker-20261008-215103-v2/r2-store-evidence-validated.json` | 4 (LL-W-001/012/022/034) | 0 |
| `results/CONT-006-WORKER/cont006-worker-20261008-215103-v2/r3-store-evidence-validated.json` | 8 (LL-G-001..008) | 0 |
| `experiments/cont006/counterfactual-lessons.json` | 2 (CF-BAD-001, CF-GOLD-001) | 0 |
| `experiments/cont006/r3-candidates.json` (bonus — the R3 store's source) | 8 | 0 |

**Blocked-token set built by THIS gate, mechanically from `fixtures/v3l/**`
(own extraction code, not the frozen `_blocked_vocab`):**

- 22 scenario ids (whole-file regex scan of every target: pattern
  `cr-60xx|cu-61xx|rt-62xx|dr-63xx|dx-64xx|gc-65xx`, all fields incl.
  evidence/provenance — **0 matches in all four files**).
- Label tokens: every per-seed variant-table probe label + `expected` value,
  real `seed_error` values, and `initial_expected` values (walked at every
  nesting depth) — 187 single-word tokens (incl. the closed-list labels
  `berthing cargo crewing fueling safety tickets storage …`, color/word
  gc-labels `clover grenadine isabella …`, codes `f14–s83`, numerals) plus
  the multi-word label phrases. Word-boundary, case-insensitive.
- World content: all 437 multi-word variant `values` strings (phrase
  substring match) + the 11 world phrases mechanically extracted from the
  v3l manifest description parenthetical (`city ferry terminal`, `campus
  equipment cage`, `greenhouse`, `kiln`, `aquarium`, `print-shop`,
  `cheese-cave`, `ski patrol cache`, `harbor chandlery`, `bell foundry`,
  `seed vault`) + single-word variant values (codes, weekday fills, gc
  option words, numerals) matched at word boundaries.
- **Template-token carve-out (FIX-C, GATE-CONT006-POSTW-approved, adopted
  here identically):** v3l `seed_error` values `{old}`/`{new}` are pure
  fixture authoring syntax, never rendered label values — excluded
  (`{alt}` exists only in v3j). No other carve-out applied.

**Scan scope per lesson (broader than the frozen §7.1d validator, which
checks title/lesson/recommendedBehavior/applicability): this gate also
scanned `context` and `observation`.** **Result: 0 hits across all 22
lessons × 6 fields** — no v3l-unique token, no shared token (70 of the 187
blocked single tokens also occur in v3i/v3j corpus vocabulary; even those
have 0 hits, so the corpus-overlap qualification is moot), no world phrase,
no scenario id.

Protocol honesty note: this gate's first pass reported 22 substring hits of
the single-word v3l value `pro` (a gc-6501 option word) inside ordinary
English ("provide", "prose", "process…") — a matcher artifact of THIS
gate's phrase matcher, not contamination; single-word values were re-matched
at word boundaries and the final count is 0. The distinction is recorded so
the raw first-pass numbers cannot be misread later.

Transparency note (not a hit): R2 lesson LL-W-034's title contains "FP-1" —
that is FROZEN TAXONOMY vocabulary (`docs/CONT006-TAXONOMY.md`), a declared
authoring input for both stores (embedded verbatim in the frozen worker
prompt), not suite vocabulary.

## Check 2 — R3 BLINDNESS AUDIT — PASS (one observation recorded)

- **Content derivable from corpus only:** all 8 lessons in
  `experiments/cont006/r3-candidates.json` cite 28 evidence refs; every ref
  resolves to a corpus manifest trace key (`RUN|ARM|seed-N[|SCENARIO|TURN]`
  with the RUN|ARM|seed triple ∈ the 50 committed CONT-005-C2 traces — 0
  unresolved); the 20 distinct scenario ids referenced are ALL v3i/v3j ids
  (cr-3001…, cu-3101…, rt-3201…, dx-3401…, cr-4001…, cu-4101…, rt-4201…,
  dx-4401…); 0 v3l ids (check 1's whole-file scan). Lesson vocabulary is
  corpus-legitimate; check 1's zero-v3l-token scan covers the transfer
  vocabulary dimension.
- **Git history:** `git log --follow` on
  `labs/continuity/experiments/cont006/r3-candidates.json` shows EXACTLY ONE
  commit — `8991027` (2026-10-08 22:45:50 +0300, "Phases W+G complete …
  blind R3 8/8") — and no edit since (HEAD == 8991027; working tree clean;
  `git diff HEAD` on the file empty). Within the gate instruction's
  allowance ("created in ONE commit (8991027 or earlier by the blind
  authoring session), never edited after").
- **No other file records v3l as an R3 authoring input:** the declared
  input set is consistent everywhere it is written — design §8 ("a SEPARATE
  session that sees: the frozen taxonomy, the corpus manifest + the
  experience traces, and the lesson-schema/validator contract. It must NOT
  see: v3l fixtures (any seed), the transfer scenarios, or worker output"),
  prereg §8, SESSION-BRIEF-CONT006 ("experience-set only"), LOG
  ("blind R3 authoring subagent … isolated inputs; touches none of the
  frozen paths"). Repo-wide search finds NO record of the authoring session
  reading v3l; GATE-CONT006 (pre-W) separately verified no R3 candidates
  file existed before Phase W.
- **Observation (non-blocking, recorded for the run record):** the R3
  candidates file landed in the SAME commit as the Phase-W artifacts and
  the POSTW gate fixes — there is no separate git commit isolating the
  authoring session, so blindness rests on (a) the declared isolated-input
  protocol (above), and (b) the mechanical zero-v3l-content evidence of
  check 1, not on commit topology. This is the acknowledged one-commit
  landing pattern (prereg §12 freeze-gate note, PR-REVIEW-CONT006 N-7).
  The gate judges the combination sufficient: the file's content is fully
  derivable from corpus + taxonomy inputs, and no byte of it names any v3l
  id, label, value or world.

## Check 3 — WORKER PROMPT INPUT SET — PASS

`src/continuity/reflection_v2.py` (freeze-manifest digest
`7c8dc548c2a1…`, byte-verified in check 5):

- Case-insensitive `v3l` occurrences in the module: **0**. v3l scenario-id
  pattern occurrences: **0**. Suite names referenced: **{v3i, v3j} only**
  (`_scenario_classes` reads exactly `fixtures/v3i` and `fixtures/v3j`).
- `REFLECTION_PROMPT_TEMPLATE`: taxonomy vocabulary (FP-1…FP-6 definitions)
  + generic task framing only; no suite ids, labels, worlds or fixture
  values.
- `build_bundle` reads `trace["trace"]` paths from the corpus manifest: all
  50/50 traces live under `results/CONT-005-C2-PILOT|CONFIRMATORY/…`
  (mechanically verified). No other data source is referenced by the worker
  path (no `results/` literal appears in the module — paths come solely
  from the frozen corpus manifest).

## Check 4 — STORE-FREEZE READINESS (prereg §7.2 ordering) — PASS

- `results/CONT-006-VAL`, `results/CONT-006-PILOT`,
  `results/CONT-006-CONFIRMATORY`: **do NOT exist** (verified live;
  `results/` contains exactly the pre-CONT-006 run dirs + CONT-006-WORKER).
  Zero behavioral/transfer inference has run.
- No `active-store-*.json` exists ANYWHERE under `labs/continuity`
  (recursive scan) — Phase V-activate has not run; no store can have been
  regenerated after hidden inference.
- The canonical evidence-validated v2 stores exist and are digested:
  `…-215103-v2/` holds `candidates-v2.json`, `provenance.json`,
  `r2-store-evidence-validated.json` (4 lessons),
  `r3-store-evidence-validated.json` (8 lessons), `r3-validation-v2.json`;
  both stores' embedded `store_sha256` verifies under this gate's own
  digest re-implementation (canonical `json.dumps(sort_keys=True,
  ensure_ascii=True, indent=1)` over the payload minus the digest field)
  and equals the digests recorded in `provenance.json`.

## Check 5 — CHAIN INTEGRITY — PASS

- **Taxonomy nesting:** sha256 of `docs/CONT006-TAXONOMY.md` recomputed =
  `c93088bfb697bef39a4859e053300dbdbfd50ccebf0e91ad62b36abf8bd30a81` ==
  `taxonomy.sha256` embedded in
  `experiments/cont006/experience-corpus-manifest.json` (taxonomy-before-
  authoring ordering proven by digest nesting, per §12).
- **Store provenance:** both v2 stores embed the GATE-CONT006-POSTW
  provenance block (FIX-A/B/C, zero-new-inference, single-shot,
  originals-untouched declarations); `provenance.json` names
  `docs/GATE-CONT006-POSTW.md` and binds both store digests — all verified
  byte-level by this gate's own code.
- **Freeze manifest re-hash: 37/37.** All 37 entries of
  `experiments/suite-v3/frozen-config-cont006.json` re-hashed with this
  gate's OWN code: plain sha256 for the 29 file entries; for
  `fixtures/v3l_suite` the gate's own directory-digest (relative posix path
  + bytes over sorted files); for the 7 `fixtures/v3l_rendered_seedNNNN`
  entries the gate's OWN independent re-implementation of the frozen render
  rule (deepcopy → drop variants → per-seed `{token}` substitution → probe
  labels/expected materialization from the per-seed spec, `{options}` →
  ` | `-joined labels, fail-closed on unbound/stray tokens → sha256 over
  sorted-by-id `json.dumps(sort_keys=True)` scenario stream). **0
  mismatches.** (Entry count 37 = the POSTW refresh adding
  `revalidate_stores.py` over the freeze-time 36 — consistent with the
  POSTW gate record.)

## Check 6 — COUNTERFACTUAL ISOLATION — PASS

- `experiments/suite-v3/run_cont006.py :: lesson_channel_for` (read +
  mechanical branch scan): the **RBAD** and **RGOLD** branches load ONLY
  `experiments/cont006/counterfactual-lessons.json` (`CF_LESSONS`,
  digest-frozen in the manifest) and construct single-lesson stores from
  `payload["lessons"]["BAD"|"GOLD-TRIV"]`; the **R2/R3** branches read
  store files (`{arm}-store-evidence-validated.json` for Phase V /
  `active-store-{arm}.json` for P/C) and contain no reference to the
  counterfactual file; R0/R1 get no channel.
- `experiments/cont006/counterfactual-lessons.json`: both lessons carry
  `bypasses_evidence_validation: true` and evidence
  `SYNTHETIC-BY-DECLARATION (counterfactual pilot object; bypasses prereg
  7.1 evidence validation by design)` — the design-declared §11 fold of
  PR-REVIEW RC-3; the file's digest `cdc53a4d…` is freeze-manifest-pinned
  (verified in the 37/37 re-hash).

---

## Verdict

**GO.** All six checks pass on live recomputation. The Phase-V inputs (the
two v2 evidence-validated stores) are free of v3l content at token, phrase,
id and world level (broader field scope than the frozen validator), the R3
authoring chain is mechanically corpus-derivable with a clean single-commit
history and a consistent declared blind input set, the worker's prompt
input set touches only corpus traces + v3i/v3j fixtures + taxonomy, no
behavioral inference has run (no VAL/PILOT/CONFIRMATORY dirs, no active
stores), the freeze chain re-verifies end-to-end (taxonomy nesting,
37/37 digests, POSTW provenance), and the counterfactual arms are isolated
to their declared synthetic objects.

Phase V (R0/R2/R3 × 7 seeds × 4 validation clusters) and the subsequent
V-activate store freeze may launch. Conditions: none beyond the prereg's
own — the freeze gate (§12) still must verify the store-freeze ORDERING on
real Phase-V output (active-store digests recorded before the first
transfer request), which is outside this gate's pre-inference scope.
