# Continuity Lab Journal

Append-only working journal. Facts, numbers, and decisions only — interpretation lives in experiment docs; universal lessons are promoted to the machine playbook the same day they are learned. English only (public repository).

## 2026-10-01 — start-note: P0a (CONT-000 foundation)

- Contract: `docs/research-proposal.md` @ `1a75746` + implementing-agent review CR-1..CR-4 (integrated). Owner start word received.
- Process adopted from house rules (IDENN AGENTS.md / playbook PB-NNN): start-note before long chains; results proven by artifact in `results/`, not exit codes (PB-067); sampling parameters travel in every request (PB-071); persistent warm process for latency-relevant runs (PB-070); findings recorded immediately as CN-NNN in `docs/FINDINGS.md`; lessons same day; commit+push after each completed stage.
- Environment before start: Ollama 0.34.2 (server up), Python 3.12.10, local models include `granite-code:8b` (4.6 GB, fits 8 GB VRAM) — chosen as the compact arm-A core for the smoke, zero new downloads.
- Plan for P0a: fixture protocol v1 (manifest + scenario families `delayed_recall`, `repeated_task`), append-only event journal with trace validation, deterministic runner with seed/budget/stop controls, Ollama inference provider with per-request sampling params and telemetry, no-memory agent (arm A: session-local context only), single-scenario smoke producing a replayable schema-valid trace in `results/CONT-000/`.
- P0b (variance/headroom pilot, seed set, sizing) is the next stage and is NOT part of this session's claim.

## 2026-10-01 — P0a smoke result

Artifacts: `results/CONT-000/cont000-smoke-dr-0001-20261001-220047/` (cold) and
`results/CONT-000/cont000-smoke-dr-0001-20261001-220201/` (warm rerun after CN-001 fix).

- Scenario `dr-0001` (delayed_recall, 2 sessions, 2 turns), arm A (no persistent memory),
  `granite-code:8b`, temperature 0.0, seed 42, num_ctx 4096, Ollama 0.34.2, Python 3.12.10.
- CONT-000 feasibility endpoint: completed=true, trace_schema_valid=true, no budget stop,
  in both runs.
- Probe `s2t1` (contains "7"): FAILED both runs — the agent answered "the verdin isle
  lighthouse is not mentioned in any of my records". This is the expected arm-A behavior
  and demonstrates headroom for the delayed_recall family: the fact exists only in the
  session-1 context, which arm A does not carry across sessions.
- Determinism data point: both runs produced identical normalized answers and identical
  token counts (209); warm run 4.9 s vs cold run 26.8 s (model load). PB-071 caveat stands
  (greedy+seed is not a cross-backend guarantee).
- Model pinned via `/api/ps` (CN-001): digest `36c3c3b9683b…`, fully in VRAM (5.31 GB).
- One harness bug found and fixed during the smoke (wrong `parents[]` index in
  `run_smoke.py`); CN-001 (digest via `/api/ps`) found and closed same day.

Next stage (P0b, separate session/owner gate): predeclare the seed set, run arm A over
the full fixture suite, measure spread of candidate endpoints, size CONT-001.

## 2026-10-01 22:30 — arc start-note: autonomous 12h window (owner authorized)

- Owner set the global goal and authorized an unattended 10–12h run ("давай ставити велику
  глобальну ціль… без мене"), with fresh sessions per milestone to avoid context distortion.
- Mechanism: `docs/ROADMAP.md` (M1–M7 briefs, executor protocol, deadline 2026-10-02 10:30
  FLEDT) + a recurring 2h automation that executes the next open milestone from repo state
  (fail-closed on entry conditions; GPU lock around inference; 110-min checkpoint budget).
- M1 (P0b pilot) launched immediately as a background agent; the automation covers M2+.
- Confirmatory CONT-001, CONT-002 work, external actions stay owner-gated per ROADMAP.

## 2026-10-01 22:33 — start-note: M1 / P0b (fixture suite v2 + arm A pilot + sizing)

- Contract: `docs/ROADMAP.md` M1 brief (P0b). Entry verified: repo clean on `origin/main`
  (HEAD `50de659`), smoke artifacts under `results/CONT-000/`, Ollama 0.34.2 up,
  `granite-code:8b` present (digest prefix `36c3c3b9683b`).
- **Predeclared seed set (before any pilot run): {11, 22, 33, 44, 55}** — fixed in
  `experiments/CONT-000/run_pilot_arm_a.py` (`SEEDS` constant); the full seed list travels
  in every `run.start` trace event and in the aggregate. Temperature 0.0, num_ctx 4096,
  per-request sampling options (PB-071), one warm process for the whole suite x seeds
  (PB-070).
- Plan: extend `fixtures/v1` from 3 to 10 scenarios (new families `distractor_recall`,
  `contradiction_update`; manifest updated); pilot script reusing fixtures/provider/
  runner/events; one warmup request before the measured runs so latency stats are warm;
  GPU lock held around the pilot; then `docs/SIZING.md`, README/ROADMAP state updates,
  commit+push.
- Budget: <= 90 min wall clock, <= 60 min GPU. Fail-closed if Ollama is unreachable or the
  model/digest mismatches.

## 2026-10-01 22:35 — arc amendment (owner): owner work moved to arc end

- Owner directive: nothing in the chain may wait on the owner; all owner work is
  consolidated in the ROADMAP "Owner morning list" at the end of the arc.
- De-gated per owner delegation: the confirmatory CONT-001 execution is now autonomous
  via M6b (independent pre-registration review by a fresh session) + conditional M7
  (frozen protocol, fresh held-out data, labels "agent-pre-registered, pending owner
  acceptance"). The owner only accepts/rejects in the morning.
- Deadline extended to 2026-10-02 11:30 FLEDT; status legend gained SKIPPED; the
  2h automation prompt was updated to match (conditional milestones, no hardcoded time).

## 2026-10-01 22:37 — M1 / P0b result: fixture suite v2 + arm A pilot + sizing

Artifacts: `results/CONT-000/pilot-armA-20261001-222950/` (5 x trace.jsonl/summary.json/
env.json + aggregate.json); `docs/SIZING.md`; fixtures `fixtures/v1/{distractor_recall,
contradiction_update}/` + dr-0003, rt-0002, rt-0003 (10 scenarios, 4 families).

- Fixture suite v2: 10 scenarios / 26 turns / 10 probes per seed — delayed_recall 3
  (incl. 3-session interference variant), distractor_recall 2, contradiction_update 2
  (corrected-value probes), repeated_task 3. All synthetic; manifest updated.
- Pilot (arm A, granite-code:8b, digest `36c3c3b9683b…a18dd`, temp 0.0, num_ctx 4096,
  predeclared seeds {11,22,33,44,55}, one warm process, warmup 2.2 s excluded): all 5
  seeds completed, all traces re-validate from disk, 0 budget stops, exit 0 under the
  shared GPU lock. Wall 22:29:41–22:34:58 (~5 min GPU total, budget <= 60 min).
- Endpoints: delayed_recall 0/3, distractor_recall 0/2, contradiction_update 0/2,
  repeated_task 2/3 — identical on every seed (spread 0.000; overall arm-A pass 2/10).
  rt-0001 5/5 (intuitive), rt-0002 0/5 (rubric-dependent; arm A answers `bug`),
  rt-0003 5/5 (CN-004: `perf` option leaks the rubric answer).
- Tokens: prompt 10,865 + eval 1,520 = 12,385 total (per request: 83.6 prompt / 11.7
  eval). Warm inference latency: mean 265.5 ms, p95 527.3 ms; effective wall ~2.3 s per
  request, ~60 s per seed (CN-002 records the gap).
- Findings opened this stage: CN-002 (total_duration vs wall gap), CN-003 (temp-0 seed
  drift: 4/26 answers differ between seeds 11 vs 55, outcomes unchanged), CN-004
  (rt-0003 option leakage), CN-005 (GPU idle threshold cannot distinguish residency
  from activity; pilot ran under the lock with the ollama attribution snapshot in
  aggregate.json — flagged for the shared tooling owner).
- Sizing recommendation for CONT-001 (SIZING.md): 5 seeds; keep the 10-scenario,
  2–3-session suite; scale scenarios (not seeds) if more power is needed.
- M1 exit artifacts complete; ROADMAP M1 marked DONE. Next: M2 (arm B, SQLite
  persistent memory) per ROADMAP.

## 2026-10-01 22:42 — start-note: M2 / P1a arm B (SQLite persistent memory)

- Contract: `docs/ROADMAP.md` M2 brief. Entry verified: M1 DONE, `docs/SIZING.md`
  exists, repo clean on `origin/main` (HEAD `b187c7a` after the IN_PROGRESS
  marker commit). Ollama preflight and digest pin happen fail-closed in the
  smoke/pilot scripts (CN-001 method).
- Open findings re-read before starting: CN-002 OPEN (budgets sized by wall
  clock, not `total_duration`), CN-003 OPEN (temp-0 seed drift — will watch for
  marginal probe flips in arm B), CN-004 OPEN (rt-0003 option leakage — NOT
  fixed, fixture untouched), CN-005 OPEN (GPU lock held without
  `--require-idle-gpu` when the only resident model is the run's own target;
  attribution snapshot recorded). CN-006 closed. This stage declares all four
  open cases out of scope except as monitoring rules.
- Plan: `src/continuity/memory.py` (SQLite episodes, keyword/substring
  retrieval, portable JSON export/import — the future CONT-002 state carrier);
  runner gains `arm=A|B` with arm B = arm A + fixed-rule memory injection at
  session start (query = session's first env turn, top-K=8 keyword-scored
  episodes of the SAME scenario, injected as one extra system message; base
  system prompt byte-identical; episodes appended after each exchange). Arm-A
  code path unchanged. New journal events `memory.append` / `memory.injected`.
  Memory scope decision (recorded): one SQLite store per seed run, retrieval
  scoped to the current scenario — cross-scenario contamination would confound
  the A-vs-B contrast. Smoke dr-0001 arm B must PASS probe s2t1 (the point of
  memory) and re-validate; mini-pilot 10 scenarios x seeds {11,22,33} under
  `results/CONT-000/pilot-armB-<run_id>/`; A-vs-B delayed_recall comparison
  artifact + LOG numbers.
- Budget: <= 110 min wall clock, <= 30 min GPU (arm A was ~60 s wall/seed;
  3 seeds + smoke fits comfortably). GPU lock via
  `shared/tooling/agent-resource-coordination/lock.py run gpu`.

## 2026-10-01 22:50 — M2 / P1a result: arm B (SQLite persistent memory)

Artifacts: `results/CONT-000/cont000-smoke-armB-dr-0001-20261001-224558/`
(smoke), `results/CONT-000/pilot-armB-20261001-224636/` (mini-pilot: 3 seeds x
trace.jsonl/summary.json/env.json/memory.sqlite3/memory-export.json +
aggregate.json + `armA-vs-armB-delayed_recall.{json,md}`); new
`src/continuity/memory.py`, runner arm flag, `run_smoke_arm_b.py`,
`run_pilot_arm_b.py`.

- **Smoke gate PASSED**: dr-0001 arm B (seed 42, granite-code:8b, digest
  `36c3c3b9683b…a18dd`, temp 0.0, num_ctx 4096): probe s2t1 expected "7" →
  observed "the lighthouse on verdin isle flashes every 7 minutes." (arm A
  failed this probe 5/5 in M1). Trace re-validates, no budget stop, 4 memory
  episodes, exit 0 under the shared GPU lock.
- **Mini-pilot (arm B, predeclared seeds {11,22,33}, one warm process,
  warmup 2.3 s excluded)**: all 3 seeds completed, all traces re-validate,
  0 budget stops, 78 requests, wall ~58-60 s per seed, total GPU wall ~3 min
  (budget <= 30 min).
- **A vs B — delayed_recall family (the M2 headline)**: arm A 0/3 probes on
  every seed (5 seeds, mean 0.000); arm B 3/3 on every seed (3 seeds, mean
  1.000). Delta mean pass rate **+1.000**. Per scenario: dr-0001 0/5 → 3/3,
  dr-0002 0/5 → 3/3, dr-0003 0/5 → 3/3 (incl. the 3-session interference
  variant). Artifact: `armA-vs-armB-delayed_recall.{json,md}`.
- Other families (exploratory, arm A 5-seed vs arm B 3-seed): distractor_recall
  0.000 → 1.000 (dx-0001, dx-0002 all pass — same mechanism as delayed_recall);
  contradiction_update 0.000 → 0.500 (cu-0002 green 3/3; cu-0001 still answers
  the superseded "12" — CN-008); repeated_task 0.667 → 0.333 (rt-0001 bug 3/3
  unchanged; rt-0002 account 0/3 unchanged; rt-0003 perf 0/3 — own-answer
  anchoring, CN-007, while arm A's 5/5 there was CN-004 option leakage).
  Overall arm B probes 7/10 per seed vs arm A 2/10.
- Tokens (78 requests): prompt 11,331 + eval 631 = 11,962 total (per request:
  145.0 prompt / 8.1 eval; arm A was 83.6 / 11.7 — memory injection raises
  prompt tokens ~74%, lowers eval verbosity). Warm latency mean 202.6 ms,
  p95 445.8 ms. CN-002 planning rule applied: budgets sized by wall (~60
  s/seed), `total_duration` reported for relative comparison only.
- Memory evidence: 52 episodes per seed (26 turns x 2 sides); retrieval
  deterministic and identical across seeds; `memory.injected` events show
  e.g. cu-0001 s3 ranked the correction episode first (harness correct,
  model failed — CN-008). Portable export `memory-export.json`
  (continuity-memory-export v1, model-neutral) written per seed — the
  CONT-002 state carrier; round-trip import verified by the offline selftest
  (`python labs/continuity/src/continuity/memory.py`).
- Findings opened: CN-007 (own-answer anchoring propagates early mistakes —
  repeated-mistake endpoint signal), CN-008 (no supersession semantics in
  keyword memory; correction ranked first yet model keeps superseded value).
  CN-003 monitoring: arm B answers byte-identical across seeds 11/22/33 — no
  seed drift observed this stage. CN-004 untouched (no fixture changes).
- Arm-A comparability preserved: arm-A runner path, prompts, and trace
  payloads unchanged; all five M1 arm-A traces re-validate with the extended
  event-type set (verified before the runs).
- Mid-run roadmap amendment (owner, while M2 executed): M2b "CONT-002 mechanics
  smoke" inserted after M2 — import the M2 state export onto a second core,
  plumbing only. M2's `memory-export.json` (continuity-memory-export v1) is
  exactly the state carrier M2b consumes; no M2 change needed for it.
- M2 exit artifacts complete; ROADMAP M2 marked DONE. Next: M2b (conditional)
  then M3 (arm C, validated self-model) per ROADMAP.

## 2026-10-01 22:54 — start-note: M2b / CONT-002 mechanics smoke (owner-ordered)

- Contract: `docs/ROADMAP.md` M2b brief. Entry verified: M2 DONE; local GGUF
  `C:\Models\qwen36_Q4_K_M\Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` present; ~12.5 h to
  the arc deadline (>= 45 min condition met); Ollama 0.34.2 up; GPU lock free;
  no tag collision for the planned import name `qwen36-35b-a3b:mdlslab`
  (checked `/api/tags`).
- Open findings re-read before starting: CN-002 OPEN (budget by wall clock —
  applied: 22 GB core-B load sized by wall, `total_duration` relative only),
  CN-003 OPEN (temp-0 seed drift — monitoring only, single seed 11), CN-004
  OPEN (fixture untouched), CN-005 OPEN (GPU attribution snapshot will be
  recorded in the checklist), CN-007/CN-008 OPEN (arm-B behavior findings,
  out of scope for a mechanics smoke). This stage is mechanics-only: zero
  behavioral claims, no R ratio, no model-quality judgments.
- Plan: one script `experiments/CONT-000/run_cont002_mechanics.py` under the
  shared GPU lock (single `lock.py run gpu` hold): (1) `ollama create
  qwen36-35b-a3b:mdlslab` from a Modelfile with only `FROM <local GGUF>` (local
  import, not a download); (2) core A `granite-code:8b` (digest pinned
  `36c3c3b9683b…`) runs the dr-0001 LEARNING session only (session 1, seed 11,
  arm B) and exports `memory-export.json` (continuity-memory-export v1); (3)
  export imported into a fresh core-B store, round-trip compared; (4) core B
  runs the dr-0001 HELD-OUT probe session only (session 2) twice — imported
  state then clean state — sampling options per request (temp 0.0, seed 11,
  num_ctx 4096, PB-071), keep_alive 45m so the 22 GB load happens once; (5)
  checklist JSON: import+digest, schema-valid round-trip, `memory.injected`
  visible in the core-B trace, both traces re-validate from disk, no
  cross-core errors. Session slicing happens in-script on the validated
  fixture dict — the fixture file itself is untouched. Probe outcome under
  B+state, if any, is recorded as an observation only. Garbage core-B output
  (possible chat-template mismatch) → new CN-NNN; plumbing checks 2-5 can
  still pass.
- Budget: <= 45 min wall clock, <= 30 min GPU. Fail-closed: GGUF missing or
  Ollama unreachable → LOG note, status back to TODO, stop.

## 2026-10-01 23:02 — M2b result: CONT-002 mechanics smoke — ALL 5 CHECKS PASS

Artifacts: `results/CONT-000/cont002-mechanics-20261001-225738/` (Modelfile,
model-digests.json, checklist.json, coreA/{trace,summary,memory-export.json,
memory.sqlite3}, coreB-state/…, coreB-clean/…); script
`experiments/CONT-000/run_cont002_mechanics.py`. Exit 0 under the shared GPU
lock (held ~2.5 min; released clean).

- **Check 1 — Modelfile import PASS**: `ollama create qwen36-35b-a3b:mdlslab`
  from `FROM C:/Models/qwen36_Q4_K_M/Qwen3.6-35B-A3B-UD-Q4_K_M.gguf` (local
  import, no download), wall 48.5 s (disk only). Digest pinned via `/api/ps`
  after loading (CN-001 method): `8a0fd5da454e…d0c50c7`. `/api/show`: chat
  template present (8057 chars), families `[qwen35moe]`, parameter size 34.7B.
  The imported model remains in Ollama for the owner's CONT-002 decision
  (morning list item 3).
- **Check 2 — export schema-valid round-trip PASS**: core A exported 2
  episodes (`continuity-memory-export` v1) after the dr-0001 learning session
  (session 1 only, seed 11, arm B, digest `36c3c3b9683b…a18dd`, 1 request);
  fresh-store import 2/2 error-free, re-export byte-equal, retrieval on the
  probe query deterministic.
- **Check 3 — state renders into core B's context PASS**: the core-B-state
  trace's `memory.injected` event shows injected=true, episode_count=1,
  episode_ids=[1] (`s1t1|environment` — the lighthouse fact learned on core
  A), ids a subset of the export; the clean run's event shows injected=false.
- **Check 4 — traces re-validate PASS**: all three traces (coreA, coreB-state,
  coreB-clean) re-validate from disk (re-verified independently after the
  run); 0 budget stops.
- **Check 5 — no cross-core errors PASS**: no provider/HTTP/import errors in
  any cross-core phase. Core-B warmup reply was "ready" — no chat-template
  garbage, so no new CN-NNN for template mismatch.
- **Observations ONLY (no transfer claims, single seed, mechanics smoke)**:
  the held-out probe (dr-0001 s2t1, expected "7") PASSED under core
  B+imported state (observed exactly "7", 318 tokens) and FAILED under core
  B+clean state ("i don't have records of this lighthouse.", 2726 tokens —
  Qwen3.6 reasons at length without the record). Recorded as plumbing-run
  by-products; the R ratio and any CONT-002 conclusion remain owner-gated.
- Mechanics: core-B requests carried their own sampling options
  (temperature 0.0, seed 11, num_ctx 4096 — PB-071, visible in each
  `agent.response.options`); the 22 GB MoE loaded with 6.18 GB in VRAM
  (partial offload, expected on the 8 GB card). CN-005 attribution snapshot
  recorded: at lock time nvidia-smi 6009 MiB, ollama `/api/ps` attributed
  5310 MiB to granite-code:8b (the run's own core-A target, no foreign
  compute). CN-002 rule applied (budgets by wall). CN-003: single seed — not
  exercised. No fixture changes.
- M2b exit artifacts complete; ROADMAP M2b marked DONE. Next: M3 (arm C,
  validated self-model) per ROADMAP.

## 2026-10-01 23:07 — start-note: M3 / P1a arm C (validated self-model)

- Contract: `docs/ROADMAP.md` M3 brief. Entry verified: M2 DONE (M2b also
  DONE, not an M3 dependency); repo clean on `origin/main` (HEAD `aab8deb`
  after the IN_PROGRESS marker commit); arm-B pilot aggregate exists at
  `results/CONT-000/pilot-armB-20261001-224636/aggregate.json` — the
  self-model estimate source. Ollama preflight + digest pin
  (`36c3c3b9683b…`) happen fail-closed inside the smoke/pilot scripts.
- Open findings re-read before starting: CN-002 OPEN (budgets by wall clock —
  applied), CN-003 OPEN (temp-0 seed drift — monitoring; arm C re-runs seeds
  {11,22,33}), CN-004 OPEN (rt-0003 option leakage — fixture untouched, but
  directly relevant to interpreting arm C's repeated_task numbers since the
  self-model failure patterns mention rt-0003), CN-005 OPEN (GPU attribution
  snapshot under the lock), CN-007 OPEN (own-answer anchoring — SEEDS the
  self-model's known-failure-patterns per the brief), CN-008 OPEN (no
  supersession — likewise). This stage embeds CN-007/CN-008 as self-model
  content with FINDINGS/LOG references; it does not close them.
- Plan: (1) `src/continuity/selfmodel.py` — versioned JSON self-model store,
  stdlib only: schema {agentId, revision, capabilities[per-family pass rates
  with counts + Wilson 95% + binomial SD], knownFailurePatterns[CN-007/CN-008
  with evidence refs], lastConsolidation, provenance per estimate}; estimates
  built ONLY from the arm-B aggregate artifact (never self-declared);
  deterministic `commit()` that validates (schema, revision = old+1,
  provenance on every estimate) and rejects otherwise; offline selftest.
  (2) Runner arm=C = arm B (SQLite memory, unchanged injection rule) + the
  self-model summary as ONE extra system message after the base prompt in
  every session; new trace event `selfmodel.injected` (revision + sha256).
  Arm A/B code paths unchanged — verified by re-validating one M1 and one M2
  trace from disk after the change. (3) Canonical store built at
  `state/selfmodel.json` (revision 1, provenance = pilot-armB aggregate);
  each run dir gets a copy + hash for reproducibility. (4) Smoke: dr-0001
  arm C, seed 42 — gate: probe passes, `selfmodel.injected` visible in the
  trace, trace re-validates. (5) Mini-pilot: arm C, 10 scenarios x seeds
  {11,22,33}, one warm process, `results/CONT-000/pilot-armC-<run_id>/`
  (same layout as arm B) + A-vs-B-vs-C per-family comparison artifact.
  (6) FINDINGS: expected new CN for estimate/evaluation fixture overlap
  (self-model measured on the same suite arm C is evaluated on — mini-pilot
  caveat, CONT-001 design input). No LLM-proposed revisions (M4), no
  reflection, no world model.
- Budget: <= 110 min wall clock, <= 30 min GPU (arm B was ~60 s/seed; arm C
  adds only prompt tokens). GPU lock via `shared/tooling/agent-resource-coordination/lock.py run gpu`.

## 2026-10-01 23:16 — M3 / P1a result: arm C (validated self-model)

Artifacts: `results/CONT-000/cont000-smoke-armC-dr-0001-20261001-230926/`
(smoke) and `results/CONT-000/pilot-armC-20261001-231050/` (mini-pilot: 3
seeds x trace.jsonl/summary.json/env.json/memory.sqlite3/memory-export.json
+ selfmodel.json + aggregate.json + `armA-vs-armB-vs-armC.{json,md}`);
new `src/continuity/selfmodel.py`, runner arm-C wiring + new
`selfmodel.injected` event type, `run_smoke_arm_c.py`, `run_pilot_arm_c.py`;
canonical store `state/selfmodel.json` (revision 1, sha256 `67054c3f8cc9…`).

- **Self-model store** (`continuity-selfmodel` v1, stdlib, JSON):
  agentId `continuity/granite-code:8b@36c3c3b9683b`; capabilities
  recomputed from the arm-B pilot aggregate (never self-declared):
  contradiction_update 3/6 rate 0.500 Wilson95 [0.188, 0.812];
  delayed_recall 9/9 1.000 [0.701, 1.000]; distractor_recall 6/6 1.000
  [0.610, 1.000]; repeated_task 3/9 0.333 [0.121, 0.646]. Known failure
  patterns seeded from CN-007/CN-008 evidence with FINDINGS/LOG refs and
  per-scenario numbers pulled from the aggregate. `lastConsolidation` null
  (M4). Deterministic `commit()` validates schema, requires revision =
  previous + 1, and provenance on every estimate; the offline selftest
  proves tamper-rejection (self-declared rate, missing provenance, and
  skipped revisions are all refused, nothing written).
- **Runner arm C = arm B + self-model summary**: `render_summary` block
  (1,257 chars) as ONE system message immediately after the base system
  prompt in every session; new `selfmodel.injected` trace event carries
  revision + sha256. Arm A/B behavior-identity verified: M1 seed-11 and M2
  seed-11 traces re-validate under the extended event set, the arm-B
  `session.context_reset` reason string is byte-identical, and the arm-A
  branch is untouched.
- **Smoke gate PASSED**: dr-0001 arm C (seed 42, granite-code:8b, digest
  `36c3c3b9683b…a18dd`, temp 0.0, num_ctx 4096): probe s2t1 expected "7" →
  observed "7"; `selfmodel.injected` visible in 2/2 sessions (revision 1);
  trace re-validates; exit 0 under the shared GPU lock.
- **Mini-pilot (arm C, predeclared seeds {11,22,33}, one warm process,
  warmup 2.2 s)**: all 3 seeds completed, all traces re-validate from disk,
  0 budget stops, 78 requests, wall 60.0–69.5 s per seed (total GPU wall
  ~3.2 min, budget <= 30 min). CN-005 attribution at lock time: only
  granite-code:8b resident (5,064.6 of 5,982 MiB) — the run's own target.
- **A/B/C per family (mean pass rates; A 5 seeds, B/C 3 seeds)**:
  delayed_recall 0.000 / 1.000 / 1.000; distractor_recall 0.000 / 1.000 /
  1.000; contradiction_update 0.000 / 0.500 / **1.000**; repeated_task
  0.667 / 0.333 / 0.333. Overall probes per seed: A 2/10, B 7/10, C 8/10.
  Identical across seeds within each arm (spread 0.000) — no CN-003 seed
  drift. Artifact: `armA-vs-armB-vs-armC.{json,md}`.
- **M3 headline**: cu-0001 flipped to PASS 3/3 (answered "18"; arm B
  answered the superseded "12") — the CN-008 no-supersession pattern
  recorded in the self-model describes exactly that failure and the model
  applied the correction. rt-0002 and rt-0003 are UNCHANGED ("bug" 3/3):
  the CN-007 own-answer-anchoring note did not break anchoring —
  self-knowledge alone was insufficient there (direct input for M4's
  reflection/consolidation design). CN-009 opened: the self-model was
  estimated on the same suite arm C is evaluated on, so the cu-0001 gain
  partly reflects "told which recorded failure to avoid" — CONT-001 design
  input.
- Tokens (78 requests): prompt 41,991 + eval 693 = 42,684 (per request:
  538.4 prompt / 8.9 eval; arm B was 145.3 / 8.1 — the 1,257-char
  self-model block raises per-request prompt tokens ~3.7x; eval verbosity
  unchanged). Warm latency mean 373.3 ms, p95 851.2 ms (CN-002 rule:
  budgets sized by wall; `total_duration` relative only).
- Memory evidence: 52 episodes per seed, injection counts per scenario
  identical to arm B (same harness rule; arm C changes only the prompt).
- M3 exit artifacts complete; ROADMAP M3 marked DONE. Next: M4 (arm D,
  reflection/consolidation) per ROADMAP.

## 2026-10-01 23:21 — start-note: M4 / P1a arm D (reflection/consolidation)

- Contract: `docs/ROADMAP.md` M4 brief. Entry verified: M3 DONE; repo clean on
  `origin/main` (HEAD `2fdb15c` after the IN_PROGRESS marker commit); arm-C
  pilot aggregate exists (`results/CONT-000/pilot-armC-20261001-231050/`);
  Ollama 0.34.2 up; GPU lock free.
- Open findings re-read before starting: CN-002 OPEN (budgets by wall clock —
  applied), CN-003 OPEN (seed drift — monitoring, seeds {11,22,33} re-run),
  CN-004 OPEN (fixture untouched), CN-005 OPEN (attribution snapshot under the
  lock), CN-007 OPEN (own-answer anchoring — THE M4 design input: arm C's
  self-knowledge note did not cure rt-0003), CN-008 OPEN (no supersession —
  second M4 design input), CN-009 OPEN (estimate/evaluation overlap — see the
  CN-009 exposure decision below). This stage is the M4 mitigation attempt for
  CN-007/CN-008 (mechanism + measurement); it does not pre-declare them closed.
- **Deterministic-MVP decision (recorded)**: the one bounded post-session
  reflection pass is DETERMINISTIC, not an LLM call. Reasons: (a) full
  reproducibility and zero GPU overhead inside the 40-min budget; (b) an LLM
  reflecting on its own wrong answers is itself exposed to the CN-007
  anchoring mechanism it is meant to cure; (c) the M4 question is whether
  bounded, evidence-gated consolidation moves behavior — a deterministic pass
  isolates that question. Same pinned core/params still govern all inference
  requests (PB-071); reflection adds none.
- Plan: (1) `src/continuity/reflection.py` — `ReflectionEngine.reflect_session`
  runs ONCE after each non-stopped session and produces PROPOSALS only:
  (a) `episode_summary` — one compact summary episode of the session's
  episodes (environment records verbatim + own answers + a fixed-rule conflict
  review: an assistant answer followed by a later same-session environment
  record containing a fixed corrective marker ("do not use", "instead of",
  "is now", "correction", …) is juxtaposed with that corrective record and the
  corrective record is marked authoritative — deterministic supersession
  semantics aimed at CN-007/CN-008); (b) `selfmodel_capability_update` —
  cumulative probe-count increment, accepted only when the family's per-seed
  probe count is complete (keeps the selfmodel arithmetic invariant); (c)
  `selfmodel_failure_pattern` — in-run failure entry citing the failed probe,
  deduplicated. A deterministic validator re-derives every proposal's evidence
  from the episode store / probe outcomes — no evidence or mismatched
  evidence -> reject. Accepted summaries commit as NEW episodes
  (role `reflection.summary`; immutable events never rewritten); accepted
  self-model proposals commit through `selfmodel.commit()` (fail-closed,
  revision +1) into a per-run COPY of `state/selfmodel.json` — the canonical
  store stays revision 1. Accept/reject telemetry: new trace events
  `reflection.start` / `reflection.proposal` / `reflection.commit` + run
  summary + aggregate counts. (2) Runner arm D = arm C wiring + the pass after
  each session; accepted outputs feed subsequent sessions (summaries via the
  existing memory injection surface, self-model via the rendered block).
  Arms A/B/C paths untouched — verified by re-validating one M1/M2/M3 trace
  per arm from disk after the change. (3) Smoke dr-0001 arm D (probe passes,
  reflection events visible, validator decisions recorded incl. at least one
  rejection — expected: capability update rejected, family incomplete, trace
  re-validates). (4) Mini-pilot 10 scenarios x seeds {11,22,33}, one warm
  process, `results/CONT-000/pilot-armD-<run_id>/` (same layout as arm C) +
  A/B/C/D per-family comparison. (5) repeated_task (CN-007 family, B 0.333 /
  C 0.333) examined per scenario; any accepted-proposal drift (degradation vs
  C or contradiction of evidence) -> CN-NNN immediately.
- **CN-009 exposure decision (explicit, not silent)**: arm D's self-model
  revisions are estimated from in-run probe outcomes and DO render into later
  sessions of the same run — the estimate/evaluation overlap CN-009 documents
  becomes dynamic and larger under arm D. Mitigations recorded: every
  reflection-derived revision carries `provenance.method: "reflection…"` and
  in-run trace refs (auditable exposure), failure-pattern text renders
  observed answers but never expected answers, and the comparison artifact
  states the caveat. CN-009 will be annotated with the M4 amplification.
- Budget: <= 110 min wall clock, <= 40 min GPU (arm C was ~3.2 min GPU wall;
  reflection is CPU-only; +smoke). GPU lock via
  `shared/tooling/agent-resource-coordination/lock.py run gpu`. Fail-closed on
  Ollama/digest mismatch (same preflight as M2/M3).

## 2026-10-01 23:38 — M4 / P1a result: arm D (reflection/consolidation)

Artifacts: `results/CONT-000/cont000-smoke-armD-dr-0001-20261001-232508/`
(first smoke — FAILED the gate, kept as evidence of the gate catching a wiring
bug, see lesson 1), `…-232535/` and `…-233142/` (passing smokes; the latter
after the marker-sentence fix), `results/CONT-000/pilot-armD-20261001-232723/`
(first pilot, pre-fix, kept as evidence) and
`results/CONT-000/pilot-armD-20261001-233203/` (pilot of record); new
`src/continuity/reflection.py` (engine + validator + offline selftest),
`run_smoke_arm_d.py`, `run_pilot_arm_d.py`; runner arm-D wiring + 3 new trace
event types; `memory.episodes_for` read helper.

- **Smoke gate PASSED** (run `…-233142`): dr-0001 arm D (seed 42,
  granite-code:8b, digest `36c3c3b9683b…a18dd`, temp 0.0, num_ctx 4096):
  probe s2t1 expected "7" -> observed "7"; 3 reflection proposals (2 episode
  summaries ACCEPTED, 1 capability update REJECTED "family incomplete");
  trace re-validates; exit 0 under the shared GPU lock.
- **Mini-pilot (arm D, predeclared seeds {11,22,33}, one warm process,
  warmup 2.5 s)**: all 3 seeds completed, byte-identical answers across
  seeds (tokens 17,124 per seed — no CN-003 drift), 78 requests, wall
  60.7-61.6 s per seed, 0 budget stops, all traces re-validate from disk
  (re-verified independently after the run). Total GPU wall for the stage
  (2 smokes-fail+pass, 2 pilots, 1 fixed smoke) ~8 min (budget <= 40 min);
  wall clock ~55 min (budget <= 110 min). CN-005 attribution at lock time:
  nvidia-smi 5,842 MiB, `/api/ps` attributes 5,064.6 MiB to granite-code:8b
  (the run's own target); snapshot recorded in aggregate.json.
- **Reflection mechanism (per seed, identical on all 3)**: 43 proposals ->
  25 accepted / 18 rejected. Accepted: 23 episode summaries (one per
  session; appended as NEW episodes role `reflection.summary`, never
  rewriting events) + 2 self-model failure patterns (REF-0038 rt-0002,
  REF-0043 rt-0003) committed through the fail-closed store; per-run
  `selfmodel-run.json` revision 1 -> 3; canonical `state/selfmodel.json`
  untouched (still revision 1, verified). Rejected: all 18 capability-update
  proposals with reason "seed already counted" — the revision-1 estimates
  already cover seeds {11,22,33} (M2 pilot), and the validator's
  double-count guard fired; capability numbers therefore never drifted
  in-run (a stricter CN-009 bound than designed, by honest mechanism).
- **A/B/C/D per family (mean pass rates; A 5 seeds, B/C/D 3 seeds)**:
  delayed_recall 0.000 / 1.000 / 1.000 / 1.000; distractor_recall 0.000 /
  1.000 / 1.000 / 1.000; contradiction_update 0.000 / 0.500 / 1.000 /
  1.000; repeated_task 0.667 / 0.333 / 0.333 / 0.333. D - C = 0.000 on
  every family and every scenario. Overall probes per seed: A 2/10, B 7/10,
  C 8/10, D 8/10. Artifact: `armA-vs-armB-vs-armC-vs-armD.{json,md}`.
- **repeated_task (CN-007 family): reflection did NOT move it — recorded
  plainly.** rt-0003 still answers "bug" on 3/3 seeds even though the
  conflict-review summary (injected ranked FIRST into session 2) quotes the
  corrective sentence verbatim ("slowness without a crash gets the label
  perf — do not use bug for slow-but-working behavior"), juxtaposes the
  agent's own s1t1 answer 'bug', and declares the corrective record
  authoritative. rt-0002 unchanged ("bug", expected "account" — its rubric
  carries no corrective marker, so no conflict review fired, by design);
  rt-0001 unchanged (passes). Deterministic evidence-juxtaposition
  consolidation did not break own-answer anchoring in granite-code:8b;
  CN-007 stays OPEN with the M4 negative result appended. **No reflection
  drift observed**: no accepted proposal degraded behavior or contradicted
  evidence (D >= C everywhere), so no new CN-NNN for drift.
- CN-009 annotated (not silently): in-run failure patterns DID render into
  later sessions (rt-0002's pattern visible in rt-0003's prompt at revision
  2) — the exposure is larger than arm C's static block; rendered pattern
  text shows observed answers only ("bug"), never expected answers;
  everything carries provenance.method starting with "reflection" and trace
  refs. Capability updates never committed in-run (double-count guard).
- Tokens (78 requests): prompt 50,757 + eval 615 = 51,372 total (per
  request: 650.7 prompt / 7.9 eval; arm C was 538.4 / 8.9 — the injected
  summaries add ~21% prompt tokens). Warm latency mean 301.3 ms, p95
  618.2 ms (CN-002 rule: budgets sized by wall; `total_duration` relative
  only).
- Same-day lessons (Context -> What happened -> Lesson -> Change):
  1. First arm D smoke failed with 0 memory episodes — the runner's
     episode-append arm set still read `arm in ("B", "C")` after the arm D
     branch was added, so arm D silently ran without memory. Lesson: when an
     arm is defined as "previous arm + X", grep for every arm-set literal in
     the runner before running; the smoke gate caught it exactly as
     designed. Change: arm set now ("B", "C", "D"); bug + failed run kept as
     evidence.
  2. The first pilot's conflict review quoted the FIRST sentence of a
     corrective record instead of the sentence containing the marker —
     `_marker_sentence`'s `or (… and marker in lowered)` clause matched
     every sentence once the marker appeared anywhere in the content.
     Lesson: inspect the actually-injected prompt content, not just the
     event stream, before accepting a mechanism result; a boolean clause
     over the whole haystack defeats sentence selection. Change: match the
     marker per sentence only; selftest now asserts the quoted sentence is
     the corrective one; pre-fix pilot kept as evidence, post-fix pilot is
     the run of record.
- M4 exit artifacts complete; ROADMAP M4 marked DONE. Next: M5 (arm E,
  world model + bounded policy) per ROADMAP.

## 2026-10-01 23:41 — start-note: M5 / P1a arm E (world model + bounded policy)

- Contract: `docs/ROADMAP.md` M5 brief + executor task instructions. Entry
  verified: M4 DONE; repo clean on `origin/main` (HEAD `6e98573` after the
  IN_PROGRESS marker commit); arm-D pilot aggregate exists
  (`results/CONT-000/pilot-armD-20261001-233203/`); Ollama preflight +
  digest pin (`36c3c3b9683b…`) fail-closed inside the smoke/pilot scripts.
- Open findings re-read before starting: CN-002 OPEN (budgets by wall clock —
  applied), CN-003 OPEN (seed drift — monitoring, seeds {11,22,33}),
  CN-004 OPEN (fixture untouched), CN-005 OPEN (attribution snapshot under
  the lock), CN-007 OPEN (**the M5 design input**: arm D's evidence
  juxtaposition did not cure own-answer anchoring; the FINDINGS update
  names "policy-level handling" as a candidate — but only a BOUNDED
  {answer_direct, retrieve_then_answer} action set is in M5 scope; no
  retrieval weighting/filtering, which is the owner-gated CONT-005
  trust-hierarchy proposal — NOT implemented here), CN-008 OPEN (no
  supersession — R2 rule below re-surfaces corrective records, an MVP-level
  acknowledgment, not new memory semantics), CN-009 OPEN (self-model
  leakage: arm E's predictions derive confidence from the same revision-1
  family rates estimated on this suite — calibration numbers are partly
  circular and will be reported with that caveat, not as clean calibration).
- Plan: (1) `src/continuity/worldmodel.py` — deterministic ex-ante
  predictions BEFORE each probe turn is answered (predicted pass/fail +
  confidence from exactly two signals: the self-model's current per-family
  pass-rate estimate; whether the store holds episodes for the scenario),
  outcome attached after scoring, bucketed calibration counters
  (predicted-pass rate vs actual per bucket high/medium/low). Predictions
  are trace events (`worldmodel.prediction` / `worldmodel.outcome`) and
  NEVER alter prompts or the answer path. (2) `src/continuity/policy.py` —
  pure deterministic decision over the FIXED set {answer_direct,
  retrieve_then_answer}: R1 retrieve when the environment turn carries a
  fixed absence-of-records marker ("not at hand", "no logbook", "no
  paperwork", "no papers", "no timetable", "from your own records");
  R2 retrieve when the turn is a probe and the scenario's stored
  environment episodes contain a corrective marker (reusing
  `reflection.CORRECTIVE_MARKERS`); otherwise answer_direct. Actuation is
  ONLY a per-turn memory refresh/extension using the SAME renderer, SAME
  retrieval rule and top-k as the arm-B baseline injection (query = the
  current turn), with a dedup no-op when the retrieved ids are already
  covered by this session's baseline injection; the no-op is recorded, not
  hidden. The MVP policy does NOT consume world-model predictions
  (recorded decision — keeps predictions non-behavioral). (3) Runner arm E
  = arm D wiring + worldmodel + policy; 3 new event types; arms A/B/C/D
  paths untouched, verified by re-validating one trace per arm from disk
  after the change + the M4 lesson applied (every arm-set literal extended
  deliberately). (4) Smoke dr-0001 arm E: probe passes, prediction + policy
  events visible, trace re-validates. (5) Mini-pilot arm E, 10 scenarios x
  seeds {11,22,33}, one warm process, `results/CONT-000/pilot-armE-<run_id>/`
  (same layout as arm D) + calibration summary and policy action
  distribution in the aggregate + A/B/C/D/E comparison artifact. (6) LOG
  result entry states plainly whether repeated_task moved (flat 0.333 since
  arm B) and what the policy actually did.
- Budget: <= 110 min wall clock, <= 40 min GPU (arm D was ~8 min GPU wall
  for the whole stage; arm E adds no inference calls). GPU lock via
  `shared/tooling/agent-resource-coordination/lock.py run gpu`. Fail-closed
  on Ollama/digest mismatch.

## 2026-10-01 23:54 — M5 / P1a result: arm E (world model + bounded policy)

Artifacts: `results/CONT-000/cont000-smoke-armE-dr-0001-20261001-234641/`
(smoke) and `results/CONT-000/pilot-armE-20261001-234851/` (mini-pilot: 3
seeds x trace.jsonl/summary.json/env.json/memory.sqlite3/memory-export.json
+ selfmodel-run.json + aggregate.json +
`armA-vs-armB-vs-armC-vs-armD-vs-armE.{json,md}`); new
`src/continuity/worldmodel.py`, `src/continuity/policy.py`, runner arm-E
wiring + 3 new trace event types (`worldmodel.prediction`,
`worldmodel.outcome`, `policy.action`), `memory.episodes_for_scenario` read
helper, `run_smoke_arm_e.py`, `run_pilot_arm_e.py`.

- **Smoke gate PASSED**: dr-0001 arm E (seed 42, granite-code:8b, digest
  `36c3c3b9683b…a18dd`, temp 0.0, num_ctx 4096): probe s2t1 expected "7" ->
  observed "7"; 1 prediction recorded BEFORE the answer (predicted pass,
  confidence 1.0, bucket high, family_rate 1.0, 3 stored episodes) + 1
  outcome attached after scoring (correct); 2 policy actions (s1t1
  answer_direct; s2t1 retrieve_then_answer via R1 "no logbook" — dedup
  no-op, recorded); reflection events intact (3 proposals, revision 1->1);
  trace re-validates; exit 0 under the shared GPU lock.
- **Mini-pilot (arm E, predeclared seeds {11,22,33}, one warm process,
  warmup 2.4 s)**: all 3 seeds completed, byte-identical answers across
  seeds (tokens 17,124 per seed — identical to arm D; no CN-003 drift), 78
  requests, wall 60.2-60.7 s per seed, 0 budget stops, all traces
  re-validate from disk. 75 memory episodes per seed (52 exchange episodes
  + 23 accepted reflection summaries). Total GPU for the stage ~4.5 min
  (smoke + pilot; budget <= 40 min); wall clock ~75 min (budget <= 110).
  CN-005 attribution at lock time: nvidia-smi 5,876 MiB, `/api/ps` attributes
  5,064.6 MiB to granite-code:8b (the run's own target); snapshot in
  aggregate.json.
- **A/B/C/D/E per family (mean pass rates; A 5 seeds, B/C/D/E 3 seeds)**:
  delayed_recall 0.000 / 1.000 / 1.000 / 1.000 / 1.000; distractor_recall
  0.000 / 1.000 / 1.000 / 1.000 / 1.000; contradiction_update 0.000 / 0.500
  / 1.000 / 1.000 / 1.000; repeated_task 0.667 / 0.333 / 0.333 / 0.333 /
  **0.333**. E - D = 0.000 on every family and every scenario. Overall
  probes per seed: A 2/10, B 7/10, C 8/10, D 8/10, E 8/10. Artifact:
  `armA-vs-armB-vs-armC-vs-armD-vs-armE.{json,md}`.
- **repeated_task did NOT move — stated plainly.** It has been flat at
  0.333 since arm B: rt-0001 passes 3/3, rt-0002 answers "bug" (expected
  "account") 0/3, rt-0003 answers "bug" (expected "perf") 0/3. The M5
  policy's R2 retrieve fired on rt-0003's probe but was a recorded no-op
  (CN-010), so arm E tested the policy's plumbing, not a new mitigation
  mechanism for CN-007 — the anchoring result stands unchanged through
  arms B/C/D/E.
- **What the world model did (30 predictions / 30 outcomes attached)**:
  overall predicted-pass rate 0.700 vs actual 0.800; pass/fail call accuracy
  0.900 (27/30; the 3 misses are rt-0001 — predicted fail at the 0.333
  family rate, actually passes); mean confidence 0.700. Buckets: high n=15
  (mean confidence 1.000, actual pass 1.000); medium n=6 (confidence 0.500,
  actual 1.000 — the contradiction_update probes, UNDERCONFIDENT because
  revision-1 rates are arm-B measurements, cu 0.500 there vs 1.000 achieved
  under C/D/E — CN-009 M5 annotation: predictions are B-anchored); low n=9
  (confidence 0.333, actual 0.333 — the repeated_task probes, calibrated in
  aggregate). Calibration numbers are exploratory only (CN-009 circularity
  + staleness).
- **What the policy actually did (78 turn decisions pooled over 3 seeds)**:
  answer_direct 54, retrieve_then_answer 24 (R1 absence-of-records 21 — one
  per dr/dx/cu probe, identical per seed; R2 corrected-fact-probe 3 —
  rt-0003 only). **All 24 retrieves were dedup no-ops** ("already covered
  by this session's injections"), 0 physical injections: every probe in
  this suite is the FIRST turn of its session, so the baseline session-start
  injection (query = that same turn) had already retrieved the identical
  episode set against the identical store state. Consequence: arm E's
  prompts were byte-identical to arm D's — which the identical token counts
  (17,124/seed) and E-D = 0.000 independently confirm. Recorded as **CN-010**
  (empty actuation surface on this fixture topology; CONT-001 needs probes
  on non-first turns or mid-session store growth to measure policy
  actuation, not just policy decisions).
- **Reflection under arm E (unchanged arm-D semantics)**: 129 proposals
  across seeds -> 75 accepted (69 episode summaries + 6 failure patterns,
  2 per seed: rt-0002, rt-0003) / 54 rejected (all capability updates,
  "seed already counted" double-count guard); per-run selfmodel revision
  1 -> 3 per seed; canonical `state/selfmodel.json` untouched (revision 1,
  verified).
- **Tokens (78 requests)**: prompt 50,757 + eval 615 = 51,372 total —
  byte-identical to arm D (0 physical policy injections => 0 extra prompt
  tokens). Warm latency mean 272.7 ms, p95 556.2 ms (CN-002 rule: budgets
  sized by wall; `total_duration` relative only).
- Arms A/B/C/D behavior-identity verified: the runner diff touches only
  arm-set literals (extended to "E") plus arm-E-guarded branches; a
  world-model argument is REJECTED for arms != "E" (identity guard); one
  M1/M2/M3/M4 trace per arm re-validated from disk after the change; all
  offline selftests pass (worldmodel, policy, memory, selfmodel,
  reflection).
- Findings this stage: CN-010 opened (empty policy actuation surface);
  CN-007 and CN-009 annotated with the M5 results. No new drift anywhere
  (E >= D everywhere, trivially, since prompts were identical).
- Same-day lesson (Context -> What happened -> Lesson -> Change): the
  pilot's per-scenario policy breakdown first showed impossible counts
  (dx-0002 "answer_direct 7" for a 2-turn scenario) — `parse_policy_events`
  used `dict(by_action)` (the RUNNING global totals) as the per-scenario
  template. Lesson: when a by-group breakdown's counts cannot exceed the
  group size, that invariant is a free assertion — the impossible number
  was visible in the artifact before any deeper check. Change: template
  starts from zeros; aggregate + comparison rebuilt from the on-disk traces
  (traces are the primary evidence; no re-run needed).
- M5 exit artifacts complete; ROADMAP M5 marked DONE. Next: M6
  (exploratory CONT-001 pass over all arms + pre-registration v1) per
  ROADMAP.

## 2026-10-01 23:57 — start-note: M6 / exploratory CONT-001 (all arms) + pre-registration v1

- Contract: `docs/ROADMAP.md` M6 brief + executor task instructions. Entry
  verified: M1–M5 all DONE; repo clean on `origin/main` (HEAD `56ca3dd`
  after the IN_PROGRESS marker commit); Ollama 0.34.2 up with
  `granite-code:8b` resident at digest `36c3c3b9683b411ee20ba5c6c6858df…`
  (prefix pin OK); shared GPU lock free at 23:57; ~11.5 h to the arc
  deadline.
- Open findings re-read before starting: CN-002 OPEN (budgets by wall
  clock — applied), CN-003 OPEN (temp-0 seed drift — 5 seeds re-run, watch
  marginal flips), CN-004 OPEN (rt-0003 option leakage — fixture NOT
  touched, belongs in the pre-registration's held-out plan), CN-005 OPEN
  (GPU attribution snapshot under the lock), CN-007 OPEN (own-answer
  anchoring, flat 0.333 since arm B — the repeated-mistake endpoint's
  target phenomenon), CN-008 OPEN (no supersession semantics), CN-009 OPEN
  (self-model estimated on the evaluation suite — the canonical store
  revision 1 derives from the arm-B pilot on THIS suite; exploratory-only
  here, held-out plan must fix), CN-010 OPEN (empty policy actuation
  surface, session-first-turn probes — held-out plan must fix). None is
  fixed silently in this stage; all map into EVALUATION-PREP.md.
- Seed count per `docs/SIZING.md`: **5 seeds {11, 22, 33, 44, 55}**
  (SIZING recommendation, matches the expected count). GPU estimate by the
  CN-002 wall rule: ~60 s/seed/arm x 25 seed-runs ≈ 25–30 min GPU — far
  inside the 3 h hard cap, no reduction anticipated.
- Plan: (1) new script `experiments/CONT-001/run_exploratory_abcde.py` —
  one warm process for the whole batch (single preflight warmup,
  keep_alive 30m, continuous inference keeps the model resident; PB-070),
  arms run in order A,B,C,D,E x seeds {11,22,33,44,55}; per seed: fresh
  MemoryStore + per-run selfmodel copy + ReflectionEngine/WorldModel as
  the arm requires; per-request sampling options temp 0.0 / seed / num_ctx
  4096 (PB-071); fail-closed preflight on Ollama/digest/self-model
  validation; fixtures untouched. (2) Artifacts under
  `results/CONT-001-exploratory/<run_id>/arm-<X>/seed-<n>/…` + per-arm
  aggregates + a normalized cross-arm table `cross-arm-table.{json,md}`
  (per-family + overall pass rates with cross-seed spread, token counts,
  wall/GPU time). (3) Consistency check against the M1–M5 pilot artifacts
  (same fixtures/code path: arm A 5 seeds should reproduce M1; B/C/D/E
  seeds {11,22,33} should match the pilots). (4) `docs/EVALUATION-PREP.md`
  pre-registration v1 (primary endpoint = repeated-mistake rate on
  previously encountered task families per the proposal's CONT-001
  definition, operationalized on the repeated_task family probes with its
  3-probe limits stated; contrast, minimum meaningful effect, thresholds,
  aggregation, missing-run handling, bootstrap unit, held-out fixture v2
  requirements targeting CN-004/007/008/009/010) — committed BEFORE any
  held-out fixture v2 content exists. (5) LOG result entry + ROADMAP M6
  DONE + commit/push + Mnemosyne note.
- Budget: <= 150 min wall clock, <= 180 min GPU; shared GPU lock held
  around the whole run (`lock.py run gpu`). Fixture edits: NONE (M1–M5
  comparability is the point). No confirmatory execution, no held-out
  fixture generation, no CONT-002/CONT-005 work (non-goals).

## 2026-10-02 00:29 — M6 result: exploratory CONT-001 (all arms) + pre-registration v1

Artifacts: `results/CONT-001-exploratory/cont001-exploratory-20261002-000048/`
(per-arm `arm-<X>/seed-<n>/` traces+summaries+stores, per-arm
`aggregate-arm-<X>.json`, `cross-arm-table.{json,md}`,
`pilot-consistency.json`, `repeated-mistake-analysis.{json,md}`); new
scripts `experiments/CONT-001/run_exploratory_abcde.py` (multi-arm runner,
aggregation offline-validated against the M1/M5 pilot artifacts BEFORE any
inference) and `experiments/CONT-001/analyze_repeated_mistakes.py`;
`docs/EVALUATION-PREP.md` (pre-registration v1, commit `a845fc5`).

- **Run**: arms A–E x predeclared seeds {11,22,33,44,55} (SIZING.md count,
  no reduction needed) x 10 scenarios = 650 requests, one warm process
  (preflight warmup 2.4 s, keep_alive 30m), all 25 seed-runs completed, 0
  budget stops, all traces re-validate from disk. GPU wall under the shared
  lock 1,543 s (~25.7 min; budget <= 180 min); stage wall clock ~32 min
  (budget <= 150 min). Model `granite-code:8b`, digest `36c3c3b9683b…a18dd`
  pinned; temp 0.0, num_ctx 4096, options in every request (PB-071). CN-005
  attribution snapshot at lock time: nvidia-smi 5,876 MiB, ollama `/api/ps`
  attributes 5,064.6 MiB to granite-code:8b (the run's own target).
- **Cross-arm table (mean pass rate, cross-seed spread in brackets — 0.000
  on every family and arm; per-seed outcomes IDENTICAL within each arm)**:

  | family (probes/seed) | A | B | C | D | E |
  | --- | --- | --- | --- | --- | --- |
  | delayed_recall (3) | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
  | distractor_recall (2) | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
  | contradiction_update (2) | 0.000 | 0.500 | 1.000 | 1.000 | 1.000 |
  | repeated_task (3) | 0.667 | 0.333 | 0.333 | 0.333 | 0.333 |
  | **overall (10)** | **0.200** | **0.700** | **0.800** | **0.800** | **0.800** |

  Per scenario: dr/dx/cu-0002 all 5/5 for B–E (cu-0001 0/5 for B — CN-008;
  5/5 for C–E); rt-0001 5/5 everywhere; rt-0002 0/5 everywhere; rt-0003
  5/5 (A, CN-004 leakage) vs 0/5 (B–E, CN-007 anchoring).
- **Repeated-mistake rate (primary-endpoint operationalization, strict, own
  eligible denominators; artifact `repeated-mistake-analysis.*`)**: arm A
  5/10 = 0.500; arms B/C/D/E 10/10 = 1.000 each. On this suite persistent
  memory WORSENED repeated mistakes (own-answer anchoring), and arm A's
  advantage is the CN-004 option-leakage artifact — the v1 contrast is
  confounded, which is exactly what the pre-registration's fixture v2
  requirements remove.
- **Pilot consistency**: 170/170 per-seed per-scenario probe outcome vectors
  identical to the M1–M5 pilot artifacts on overlapping seeds (arm A 50/50
  over 5 seeds; B/C/D/E 30/30 each over 3) — deterministic reproduction of
  every pilot at the outcome level; CN-003 stays token-level only (arm D/E
  seeds 44/55 +38 tokens, arm A seed 55 −5 tokens, zero outcome changes).
- **Cost per arm (5 seeds, 130 requests each)**: tokens A 12,385 / B 19,936
  / C 71,140 / D 85,696 / E 85,696 (E byte-identical to D — CN-010 inert
  policy actuation, 0 physical injections suite-wide); wall 58–61 s/seed,
  arm walls 295–300 s. Warm latency (`total_duration`, relative only per
  CN-002): means A 268.6 / B 215.9 / C 244.6 / D 234.9 / E 242.9 ms (p95
  465–570 ms).
- **Pre-registration v1 committed (`a845fc5`) BEFORE any held-out fixture
  v2 content exists** (none generated in M6): primary endpoint = RM rate per
  the proposal's definition, mechanically operationalized (initial answer /
  initial error / own-eligible denominator / strict same-answer recurrence,
  deterministic arm-blind scoring); primary contrast E−A two-sided; MME
  |Δ| >= 0.15; decision rule = 95% paired cluster bootstrap over scenarios
  (10,000 resamples, RNG seed 20261002) excluding 0 AND |Δ̂| >= MME;
  uncertainty unit justified by the measured 0.000 seed spread; held-out
  plan: fresh scenarios + fresh seeds {101,202,303,404,505}, RM denominator
  >= 7/seed incl. a new correction-and-reuse family (CN-007/008), explicit
  `initial_expected` + `probe.class` fixture fields, no option lists on
  probe turns (CN-004), probes off session-first turns with expected
  arm-E actuation >= 1 physical injection/seed stated ex ante (CN-010),
  self-model estimated only on disjoint calibration scenarios (CN-009),
  freeze discipline + fail-closed missing-run handling.
- Open findings disposition this stage: CN-002/003/005 monitoring rules
  applied (no escalation); CN-004/007/009/010 each annotated with the M6
  disposition and mapped into EVALUATION-PREP.md (none silently fixed; v1
  fixtures untouched). No new CN cases (no anomaly: every number reproduced
  its pilot).
- Repo note: an independent observer commit (`9591be1`, OBSERVER-NOTES.md)
  landed mid-run; rebased cleanly, no interaction with M6 scope.
- M6 exit artifacts complete; ROADMAP M6 marked DONE. Next: M6b
  (independent pre-registration review, GO/NO-GO) per ROADMAP.

## 2026-10-02 00:52 — M6b result: independent pre-registration review — verdict GO

Artifacts: `docs/PR-REVIEW.md` (the review; `docs/EVALUATION-PREP.md` NOT
modified — frozen at `a845fc5`, verified untouched: `git diff a845fc5 HEAD`
on the file is empty). Fresh-session review (M6 author session did not
participate). Zero inference; wall ~20 min (budget <= 30 min).

- **Checklist (all PASS)**: (a) primary endpoint mechanically operationalized
  (s1t1 initial answer / initial_expected / per-arm eligible denominator /
  strict same-answer recurrence) and implemented deterministically and
  arm-blind in the committed harness (`runner.score_probe` re-read in code;
  `analyze_repeated_mistakes.py` performs the identical computation);
  additive v2 fixture fields feasible (validator ignores unknown keys —
  re-verified). (b) E−A two-sided, MME |Δ| >= 0.15 derived from the v2
  denominator granularity (1/7 = 0.143), NOT the exploratory delta; decision
  rule symmetric — direction honesty explicit (exploratory favored arm A
  0.500 vs 1.000; plan states memory WORSENED RM and labels arm A's edge a
  CN-004 artifact; a harm-direction result is a legitimate claim);
  underpowered guard pre-declared. (c) aggregation, paired scenario-cluster
  bootstrap (unit justified by the measured 0.000 seed spread), redraw
  degeneracy halt, and complete missing/failed-run policy (exclusions
  reported, halt thresholds, single infra re-run, contamination halts,
  GPU-cap stop rule). (d) held-out plan disjoint (seeds {101,202,303,404,505},
  fresh scenario ids, disjoint self-model calibration) with fixture v2
  requirements covering CN-004/007/008/009/010 and a pre-inference mechanical
  validator — M7 executable without further design decisions. (e) exploratory
  data-seen labeling thorough; known leakage channels closed and checked.
- **Non-blocking notes recorded in PR-REVIEW.md**: (1) fixture-authoring
  exposure (v2 author has seen exploratory results) is a residual risk the
  plan does not name — accepted given the symmetric rule, mechanical checks
  and the owner acceptance gate; (2) strict-RM comparator needs concise
  label-form probe prompts under free-form scoring (loose sensitivity
  pre-declared, so degradation is visible); (3) M7 validator should pin
  "initial task turn = s1t1" explicitly.
- **M7 conditions**: GO granted; ~10 h 45 min remained before the 11:30 FLEDT
  arc deadline at review time — the >= 2 h margin holds. M7 may proceed per
  its brief (frozen protocol, held-out fixture v2, "agent-pre-registered,
  pending owner acceptance" labels).
- ROADMAP M6b marked DONE. Next: M7 (confirmatory CONT-001) per ROADMAP.

## 2026-10-02 00:58 — start-note: M7 / confirmatory CONT-001 (agent-pre-registered)

- Contract: `docs/ROADMAP.md` M7 brief + `docs/EVALUATION-PREP.md` (FROZEN at
  `a845fc5`; verified byte-identical to that commit at 00:37 — sha256
  5910789afeea1576316105cc59d1e0b3b8c8fd65 both sides). M6b verdict GO
  (PR-REVIEW.md); time check 00:37 FLEDT vs 11:30 deadline → ~10 h 53 min
  remain, >= 2 h condition holds. Every artifact this stage is labeled
  "agent-pre-registered, pending owner acceptance".
- PR-REVIEW non-blocking notes, incorporated ONLY where the frozen plan
  already allows: (1) fixture-authoring exposure — stated explicitly in the
  run record (the plan's freeze discipline + owner gate bound it); (2)
  label-form probe prompts — v2 probes ask "Reply with the label/tier/class
  only." (concise label-form elicitation is consistent with §6.5 free-form
  scoring; loose sensitivity still covers degradation); (3) validator pins
  the `initial_expected`-bearing turn to exactly s1t1 (§1.1/§6.3 consistency
  check the plan already requires mechanically).
- Plan: (1) author held-out fixture v2 (`fixtures/v2/`, 14 scenarios: 3 dr +
  2 dx + 2 cu + 5 rt + 2 correction_reuse = 7 RM-eligible probes/seed,
  `initial_expected` fixture fields, `probe.class="rm_eligible"` markers, no
  option lists on ANY probe turn, RM probes on s2t2 behind a non-probe s2t1)
  + disjoint calibration suite `fixtures/v2-calibration/` (5 scenarios,
  cal-* ids, seeds {11,22,33}); calibration probes_per_seed per family
  EXCEEDS the evaluation suite's (dr 4>3, dx 3>2, cu 3>2, rt 6>5, cr 3>2) so
  the reflection double-count guard rejects every in-run capability update —
  §6.8 "in-run capability updates remain disabled" holds deterministically
  without touching the frozen M4 reflection code. (2) Pre-inference
  mechanical validator `validate_fixtures_v2.py` enforces §6.1–6.6 + the
  s1t1 pin + an ex-ante arm-E actuation simulation (R2 corrective markers
  fire on rt-0004/rt-0006/cr-0001/cr-0002 probes; mid-session store growth
  from the s2t1 exchange yields new episode ids at the probe-turn retrieve —
  expected >= 1 physical injection per seed, stated ex ante per §6.7).
  (3) Calibration arm-B run (v1 calibration seeds 11/22/33 — disjoint from
  the confirmatory seeds, which are never used for calibration per §6.1) →
  self-model revision 1' built ONLY from the calibration aggregate
  (`build_from_calibration_aggregate`, mirroring the M3 builder with
  parameterized CN-007/CN-008 evidence scenarios cal-RT1/cal-CU1;
  provenance.derived_from points at the calibration artifact — §6.8/§8).
  (4) Freeze commit: fixtures + calibration artifact + self-model 1' +
  frozen-config.json (git rev, sha256s, seeds {101,202,303,404,505}, model
  granite-code:8b digest prefix 36c3c3b9683b, temp 0.0, num_ctx 4096,
  MME 0.15, bootstrap seed 20261002 / 10,000 resamples) BEFORE the first
  confirmatory inference request (§6.9). (5) Confirmatory run
  `run_confirmatory_abcde.py` — the M6 multi-arm runner semantics carried
  over unchanged (same run_one_seed logic, budgets, injection rules, one
  warm process, options in every request) with labeled deltas only:
  confirmatory kind/labels, v2 fixtures, fresh seeds, calibration self-model,
  freeze verification at start. (6) `analyze_confirmatory.py` executes the
  pre-registered analysis exactly: RM rate per §1.1 (probe selection by
  fixture marker, initial_expected from the fixture), primary contrast E−A
  two-sided, MME 0.15, paired cluster bootstrap over scenarios (10,000
  resamples, RNG seed 20261002, redraw cap 5%), decision rule per §4,
  underpowered guard, secondaries as listed in §3 (exploratory-attribution),
  missing-run handling per §8, contamination halts per §8. (7) Results under
  results/CONT-001-confirmatory/<run_id>/ + results-summary.md with the
  plain confirmatory outcome (benefit / harm / no difference / inconclusive
  — whatever the data shows).
- Budget: <= 150 min wall, <= 180 min GPU (calibration ~4 min + confirmatory
  ~50 min estimated at M6's measured ~2.4 s/request × 1,206 requests);
  shared GPU lock around all inference; stop-and-record on overrun, no
  silent seed reduction.




## 2026-10-02 02:12 — M7 result: confirmatory CONT-001 (agent-pre-registered, pending owner acceptance)

Artifacts: `results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711/`
(fixture-validation.json PASS; frozen-config.json + freeze-verification{,-attempt1}.json;
calibration/ + selfmodel-v2-calibration.json (revision 1', sha 2ce516bd7402...);
arm-{A..E}/seed-{101,202,303,404,505}/ traces+summaries+stores; aggregate-arm-<X>.json;
cross-arm-table.{json,md}; repeated-mistake-analysis.{json,md}; secondary-analyses.json;
results-summary.md; resume-manifest.json). New scripts:
`experiments/CONT-001/{validate_fixtures_v2,run_calibration_v2,run_confirmatory_abcde,analyze_confirmatory}.py`;
new held-out suites `fixtures/v2/` (14 scenarios) and `fixtures/v2-calibration/` (5).
**Every artifact and number in this entry is labeled: agent-pre-registered, pending
owner acceptance.**

- **Protocol integrity**: EVALUATION-PREP.md verified byte-identical to the frozen
  commit `a845fc5` before anything ran (sha256 5910789afeea... both sides). PR-REVIEW
  verdict GO; ~10 h 53 m remained before the arc deadline at start. Frozen-content
  digests (fixtures v2, v2-calibration, protocol doc, self-model 1') recorded in
  frozen-config.json at the freeze commit and re-verified at run start and at
  analysis time; no drift.
- **Fixture v2** (held-out; mechanical validator PASS pre-inference, 15 checks
  E1-E10/C1-C4/A1): 14 scenarios (3 dr + 2 dx + 2 cu + 5 rt + 2 correction_reuse),
  7 RM-eligible probes/seed (`probe.class="rm_eligible"`, `initial_expected` pinned
  to exactly s1t1 per PR note 3), NO option lists on any probe turn (CN-004 fix;
  probes elicit concise label-form answers per PR note 2), every RM probe on s2t2
  behind a non-probe s2t1 (CN-010 fix), ids/content disjoint from v1 (validated).
  Two validator FAILs during authoring were fixed by regenerating fixtures
  (em-dash ASCII; actuation phrasing), never by relaxing the validator.
- **Calibration (CN-009 fix executed)**: arm B on the disjoint calibration suite
  (seeds {11,22,33} — the confirmatory seeds {101,202,303,404,505} were never used
  for calibration), 81 requests, wall 205 s. Revision 1' rates: delayed_recall
  0.750, distractor_recall 1.000, contradiction_update 1.000, correction_reuse
  1.000, repeated_task 0.000 (0/18 — granite finds the cal-RT rubric hard; an
  honest estimate). Provenance.derived_from points at the calibration aggregate
  only; analysis re-verifies. Guard sizing (cal probes_per_seed > eval per family:
  4>3, 3>2, 3>2, 6>5, 3>2) kept the reflection double-count guard active: **0
  in-run capability updates accepted in every D/E seed-run** (6.8 satisfied
  deterministically, frozen M4 code untouched).
- **Run**: arms A-E x seeds {101,202,303,404,505} x 45 turns = 1,125 requests,
  14 probes/seed, one warm process per attempt, temp 0.0 / num_ctx 4096 /
  options in every request, digest 36c3c3b9683b...a18dd pinned, all 25 seed-runs
  completed, 0 budget stops, all traces re-validate, 0 exclusions (8.1 clean).
  GPU total across the four lock sessions (calibration + attempt 1 + resume 1 +
  resume 2) ~3,080 s measured arm walls + calibration + warmups ≈ **~55 min**
  (cap 180); stage wall clock ~100 min (cap 150).
- **Execution incident (recorded, fail-closed path worked)**: attempt 1 (rev
  66eefc8) crashed in the executor's OWN post-inference instrumentation
  (`sum()` over an int telemetry counter) after arm C and arm D seed 101's
  inference completed; arms D(202-505)/E had issued zero evaluation requests.
  Recovery per 8's infrastructure clause + the M5 traces-are-primary lesson:
  one-line fix + None-tolerant aggregation (commits c679547, 4e425ea, recorded),
  arm D seed 101's summary REBUILT offline from its complete attempt-1 trace
  (zero inference repeated anywhere), never-started seeds ran as their first
  run, both attempts + revs recorded in resume-manifest.json and
  freeze-verification-attempt1.json. Frozen content digests unchanged throughout.
- **PRIMARY RESULT (pre-registered rule, exactly as frozen)**: strict RM rate
  (per-arm eligible denominators) — A 0/20 = 0.000; B 0/20 = 0.000; C 0/30 =
  0.000; D 15/30 = 0.500; E 10/30 = 0.333. Primary contrast **RM(E)-RM(A) =
  +0.333 (harm direction), 95% CI [0.000, 0.750]** (paired cluster bootstrap over
  7 scenarios, 10,000 resamples, RNG seed 20261002, 18 redraws < 500 limit).
  CI does NOT exclude 0 (lower bound exactly 0.0) although |0.333| >= MME 0.15 →
  **verdict: NO CONFIRMATORY DIFFERENCE ESTABLISHED** (both criteria required by
  the frozen rule; one failed). Underpowered guard not triggered (denominators
  20/30 >= 10). Sensitivity (a) loose RM = 1.000 for EVERY arm (all eligible
  probes incorrect everywhere — free-form probes are brutally hard for
  granite-code:8b without option lists); sensitivity (b) common-eligible E-A =
  +0.247 CI [0.0, 0.75] — same shape as the primary. Reported plainly: the
  point estimate leans toward memory-arm harm (arm E repeats its own initial
  wrong answers more than arm A), but the pre-registered uncertainty rule does
  not certify it.
- **Per-seed spread**: RM rate range 0.000 on A/B/C, 0.500 on D, 0.333 on E —
  zero within-arm seed variation on the primary endpoint EXCEPT one probe
  elsewhere: arm B rt-0008 seed 101 failed (0) vs passed (1) on seeds
  202-505 — the run's single outcome-level seed flip → **CN-003 ESCALATED**
  (see FINDINGS).
- **Mechanism observations (secondary, exploratory-attribution — never
  promotable)**: (i) strict RM appears exactly at arm D (D-C = +0.50, CI
  [0.143, 0.857]) and persists at E (E-D = -0.169, CI [-0.714, 0.400]); the
  strict repeats are VERBATIM copies of the agent's own earlier degenerate
  answers (granite parrots its prior reply, and reflection summaries re-inject
  it) — anchoring-by-parroting, the CN-007 phenomenon surfacing with reflection
  summaries in context. (ii) delayed_recall E-A = +1.000 CI [1.0, 1.0]: with
  option leakage removed, arm A passes NOTHING on the whole suite (0/14) while
  B-E pass all recall probes — persistent memory's recall benefit is unambiguous.
  (iii) contradiction_update C-B = -0.500 (B 5/5 -> C/D/E 0/5 on cu-0003, the
  superseded-value trap: with the calibration self-model block in context, C-E
  answer the superseded value) — a self-model-interference signal, small-n.
  (iv) correction_reuse 0/5 everywhere: the new family defeats every arm.
  (v) token cost/arm: A 26,329 / B 46,540 / C 152,320 / D 272,795 / E 278,805.
- **Arm-E policy actuation (CN-010 fix executed, 6.7)**: **7 physical policy
  injections per seed** (one per RM scenario, exactly matching the ex-ante
  simulation), 13 retrieve actions/seed, expectation >= 1/seed MET on every
  seed; arm E is NOT actuation-inert on v2 — E tokens 278,805 vs D 272,795
  (+1,202/seed from the injected blocks). No policy-level claim beyond
  actuation (E-D RM CI spans 0).
- **PR-REVIEW note 1 (fixture-authoring exposure)** stated in frozen-config.json
  exactly as the reviewer recommended; the symmetric rule + mechanical validator
  + freeze + owner gate bound it. The harm-leaning point estimate is reported
  as plainly as a benefit-leaning one would have been.
- Same-day lessons (Context -> What happened -> Lesson -> Change):
  1. Attempt 1 crashed post-inference on `sum(int)`; attempt 2's aggregate then
     crashed on `wall_s=None` from the offline-rebuilt summary. Lesson: when a
     resume path introduces Nullable fields, grep every consumer of those fields
     in the same PR — the second crash was the first crash's shadow. Change:
     None-tolerant aggregation; offline summary rebuild marked
     `summary_rebuilt_offline`; resume manifest records both attempts.
  2. The pre-freeze offline smoke of verify_freeze caught two record/verifier
     mismatches (key name, provenance path prefix) with zero GPU spent. Lesson:
     smoke the freeze verifier against the real record BEFORE the run, exactly
     like the fixture validator. Change: fail-closed exits kept; the smoke
     steps are recorded here for M8.
- Open findings disposition this stage: CN-003 ESCALATED (arm B rt-0008 seed
  101 failed vs passed on seeds 202-505 — the run's single outcome-level seed
  flip; numbers above); CN-004 CLOSED (v2 has no option lists on probe turns;
  on the rt-0006 analogue arm A went 5/5 (v1, leaked) -> 0/5 (v2) — leakage
  gone by construction, validator-enforced); CN-007 annotated (strict RM at
  D/E via verbatim own-answer parroting; loose RM 1.000 everywhere — the
  strict/loose gap shows PR note 2's label-form caveat materialized on
  free-form probes); CN-009 CLOSED (calibration-only self-model executed with
  provenance; 0 in-run capability updates in every D/E seed-run); CN-010
  CLOSED (7 physical policy injections per seed, expectation >= 1/seed met;
  arm E no longer token-identical to D, +1,202 tokens/seed). CN-002/005
  monitoring rules applied (attribution snapshots in aggregates; wall-clock
  budgets per CN-002).
- M7 exit artifacts complete; ROADMAP M7 marked DONE. Next: M8 (housekeeping,
  arc report, owner morning list) per ROADMAP. The owner accepts or rejects
  this agent-pre-registered result in the morning list.

## 2026-10-02 02:21 — M8 result: arc closed — ARC-REPORT, CN triage, owner morning list, arc COMPLETE

Artifacts: `docs/ARC-REPORT.md` (the arc's closing document); ROADMAP header
gained "**Arc status:** COMPLETE (2026-10-02 02:21 FLEDT)"; lab README Status
and the root README labs-table row updated to the final state; M8 DONE. Zero
inference, zero GPU this stage. IN_PROGRESS marker commit `9d5a268`.

- **Entry**: no earlier milestone open (M1–M7 + M2b/M6b all DONE); well before
  the 11:30 FLEDT deadline.
- **CN triage at arc end** (full lines in FINDINGS.md / ARC-REPORT §5):
  CLOSED — CN-001, CN-004 (fixture v2, validator E8; arm A 5/5 -> 0/5 on the
  rt-0006 analogue), CN-006, CN-009 (calibration-only self-model 1'), CN-010
  (7 physical policy injections/seed). OPEN — CN-002 (latency-understatement
  planning rule; budgeting only), **CN-003 ESCALATED** (the confirmatory run's
  single outcome-level seed flip: arm B rt-0008 seed 101 failed vs passed on
  seeds 202-505 — temp-0 does not fully determinize outcomes on this backend;
  flip is outside the primary endpoint, verdict unchanged), CN-005 (shared GPU
  attribution; owner decision, morning list item 5), CN-007 (anchoring uncured
  by C/D/E mechanisms; strict form = verbatim parroting at D/E, D-C CI
  [0.143, 0.857] secondary; CONT-005 `c8176c9` is the mitigation proposal —
  owner-gated), CN-008 (no supersession; cu-0003 secondary B 5/5 vs C/D/E 0/5
  self-model-interference observation).
- **Deferred Mnemosyne consolidation retried once** (`mnemosyne_sleep`,
  all_sessions=true): completed cleanly — status `no_op`, "No old working
  memories to consolidate", 0 sessions scanned, 0 consolidated, 0 errors.
  Nothing eligible; recorded in ARC-REPORT §8.
- **ARC-REPORT.md** (per the M8 brief): planned-vs-ran with per-milestone
  commit hashes; the numbers that matter — exploratory A-E table (overall
  0.200/0.700/0.800/0.800/0.800, spread 0.000), confirmatory outcome stated
  exactly as pre-registered ("no confirmatory difference established": E-A
  +0.3333, 95% CI [0.0, 0.75], criterion (i) CI-excludes-0 failed, criterion
  (ii) MME passed), delayed_recall E-A +1.000 CI [1.0, 1.0], D-C +0.5015 CI
  [0.1429, 0.8571], M2b mechanics 5/5, arm-E actuation 7 injections/seed;
  failures and negative results (M4 null, reflection-associated verbatim
  parroting, instrumentation crash + clean recovery, CN-003 flip); explicit
  PENDING OWNER ACCEPTANCE section mirroring the morning list with file
  pointers; explicit NOT-claimed list (no M2b transfer claims, no M6
  confirmatory claims, no consciousness adjacency, CONT-005 untouched).
- **READMEs**: lab Status = autonomous arc COMPLETE (2026-10-02), pending
  owner acceptance, with the headline numbers and pointers; root labs-table
  Continuity row = "Autonomous arc complete: exploratory + confirmatory
  CONT-001 done, pending owner acceptance".
- Nothing autonomous remains: the chain is closed; everything open is owner
  work in the ROADMAP morning list (accept/reject the confirmatory result,
  CONT-002 program, CN-005 tooling decision, CONT-005 proposal, external/
  publication/scope decisions).
- M8 exit artifacts complete; ROADMAP M8 marked DONE; arc marked COMPLETE.
  Final commit + push follows this entry.


## 2026-10-04 — Suite v3 + protocol amendments: start-note (post-acceptance work package)

Owner accepted the arc record + Fable recommendations 2026-10-04 (ROADMAP "Owner
decisions", commit 4bbac40). This session starts the approved zero-GPU package that
gates the CONT-005 arc:

1. `docs/SUITE-V3-DESIGN.md` — fixture family redesign: label-form probes (kills the
   free-form floor and un-pins arm A from degenerate 0 to a measurable guessing
   baseline), structural RM eligibility (scripted initial error, common denominators
   across arms — fixes the endogeneity where the self-model itself created the
   eligible mistakes), >= 12-15 RM clusters, leakage controls replacing the v2
   no-options ban (E8) with balanced label sets + empirical guessing baseline.
2. Power calculation by simulation (cluster percentile bootstrap; K=7 retrospectively
   vs K=12/14/15 prospectively) — script + JSON artifact, no GPU.
3. `docs/PREREG-REQUIREMENTS-V2.md` — owner-adopted amendments (a)/(d)/(e) as concrete
   pre-registration template requirements: analysis code frozen by digest, gates run by
   a non-executor session, consistent wall-time accounting across resume attempts.
4. `docs/OWNER-BRIEF-TEMPLATE.md` — phone-first arc report skeleton (Fable format).

Non-goals: touching frozen v1/v2 artifacts or EVALUATION-PREP.md; any inference;
authoring CONT-005 experiment proposals (inspirer's file); arc planning (after the
review cycle).

## 2026-10-04 — Suite v3 + protocol amendments: DONE (zero GPU, zero inference)

Artifacts: `docs/SUITE-V3-DESIGN.md` (the design doc), `docs/PREREG-REQUIREMENTS-V2.md`
(binding template per Owner decisions item 6), `docs/OWNER-BRIEF-TEMPLATE.md`
(phone-first report skeleton, Flash+Fable format), `experiments/suite-v3/power_calc.py`
+ `power-results.json` (seed 20261004; 3000 Monte-Carlo reps x 4000 bootstrap
resamples per configuration).

- **Power headline numbers** (read from power-results.json): v2 retrospective shape
  (K=7, A pinned at 0, effect in 2/7 clusters) power **0.304** — the frozen test
  quantitatively underpowered for what it observed; K=14 uniform delta 0.20 -> 0.934,
  delta 0.10 -> 0.453, so ~80% power at delta ~0.13-0.15 -> **MME 0.15 stands**;
  concentration 8/14 -> 0.982, 5/14 -> 0.610 -> validator E12 bans trust-inert
  primary filler.
- **Suite v3 shape**: 24 scenarios = 14 primary RM clusters (CR 8 with typed
  corrections incl. erroneous-user-correction/retraction/conflict per the CONT-005
  proposal; RM 6 with scripted seed error = structural eligibility, fixes the
  endogeneity) + 10 secondary (CU 4, DR 3, DX 3). Label-form probes with options at
  probe time (kills the vocabulary floor, un-pins no-memory arm to ~1/k). Budget
  arithmetic from v2 evidence: ~140 turns/seed, ~343 s/seed/arm, 4 arms x 5 seeds
  ~ **114 min GPU** — inside the 3 h cap; primary-first execution with droppable-
  secondary clause.
- Construct shift documented: primary RM now measures propagation of a *recorded*
  own-error (the CN-007 mechanism); emergent initial errors demoted to labeled
  secondary with per-arm denominators.
- Open questions routed to the CONT-005 review cycle (SUITE-V3-DESIGN §10):
  scripted-own-answer acceptability, CU primary-vs-secondary, T1 budget-matching,
  guess-calibration doubling as the CONT-002 battery.
- Next: fixture v3 authoring + validator E9-E14 (zero GPU), T0-T3 arm
  implementation, headroom pilot (GPU, small), then the CONT-005 proposal review
  cycle and a fresh arc plan.

## 2026-10-04 — Fixtures v3 authored + validator PASS (zero GPU, zero inference)

Artifacts: `fixtures/v3/` (27 scenarios: correction_reuse x8 with typed sub-types,
repeated_task x6 scripted_own_answer, contradiction_update x4, delayed_recall x3,
distractor_recall x3, guess_calibration x3 / 6 never-stated probes; manifest v3) and
`experiments/suite-v3/validate_fixtures_v3.py` (V1-V13, V-namespace; design-doc
E9-E14 = V4-V9) + `experiments/suite-v3/fixture-validation-v3.json`.

- **VERDICT: PASS, 13/13 checks.** Highlights: 24 scored label-form probes, correct
  positions perfectly uniform across 6 slots (max share 0.17 vs the 0.50 rule);
  zero session-scoped label leakage; ids and turn texts fully disjoint from
  fixtures/v1, v2, v2-calibration; every primary scenario carries a structural
  seed_error whose trap value is a probe label, differs from expected, and is
  stated pre-probe.
- Trap map (primary): cr valid-env(bug), valid-tool(account), erroneous-user
  (billing, data), retraction(sync, sync), conflict(bug, data); rt scripted
  (offline, maintenance, standby, bug, billing, permissions).
- Authoring slips caught by tooling, not by eye: 1 heredoc truncation (cr-1004) and
  4 missing `]` closers (cu-1004, dx-1003, gc-1002, gc-1003) — JSON parse found all
  five before the validator ran; validator's own error path initially swallowed the
  JSONDecodeError detail (prints it now via the written JSON).
- Next in the chain: extend the runner/loader for the v3 schema (probe.labels,
  seed_error, source_type, guess_calibration) and implement arms T0-T3 (flat
  baseline / +annotations / +supersession resolution / +trust policy), then the
  headroom pilot (GPU, small) and the CONT-005 review cycle.

## 2026-10-04 — T-arms implemented + assembly gate PASS (zero GPU, zero inference)

Artifacts: `src/continuity/claims.py` (trust-policy/v1: source ranks
environment/tool 2, user 1, agent_answer 0; "verified" bump to 3, "unreviewed"
demote to 1; retraction chains; T1/T2/T3 renderers), runner T0-T3 arm wiring
(T0 flat = byte-identical arm-B renderer; T1 annotations; T2 resolution flags +
trust demotion ordering; T3 + policy-version header and per-episode trust rank),
fixtures.py v3 kinds (guess_calibration null-expected, probe.labels), guess-probe
aggregation in score_probe, `experiments/suite-v3/assembly_gate.py` +
`assembly-gate.json`.

- **ASSEMBLY GATE: PASS 7/7.** G3 resolution counts exactly as designed across
  the 14 primary scenarios: erroneous_user flagged x2, source_conflict exactly
  one side flagged x2, retraction superseded x2, scripted own-answer flagged x6,
  valid corrections clean x2 (only the agent_answer seed flag, which is by
  policy). Flagged episodes demoted after unflagged; policy header T3-only;
  assembly deterministic (byte-identical second pass); guess_calibration clean.
- Fixtures amended after validation (revalidated PASS 13/13): the eight
  seed-record turns typed `source_type: agent_answer` (the CN-007 semantics:
  the agent's own earlier answer is a first-class lowest-trust source); the
  verified-token contract tightened in cr-1003/cr-1004 ("verified" now appears
  in a turn iff the turn itself is verified evidence — the desk's own evidence
  notes no longer use the token inside unverified user turns). The assembly
  gate caught the contract break ex ante (G3), which is the gate doing its job.
- Regression: frozen v2 fixture validator still PASS; fixtures/v1, v2,
  v2-calibration load unchanged through the extended fixtures.py.
- Design property recorded: the trust treatment surface covers CR (typed
  corrections) and RT (agent_answer seeds); CU/DR/DX secondaries are
  near-controls for the T-arms (their corrections are untyped plain
  statements) - documented, not hidden.
- Next: headroom pilot (GPU, small: arm A vs T0 vs T2 on the primary set to
  confirm floor removal and guessing baseline ~1/k), then the CONT-005
  pre-registration v2 per docs/PREREG-REQUIREMENTS-V2.md and the review cycle.

## 2026-10-05 — CONT-005 headroom pilot: start-note (first GPU touch of suite v3)

Arms A / T0 / T2 x predeclared seeds {11, 22, 33} over the full fixtures/v3
(27 scenarios, ~130 turns/seed, ~1170 requests total). Model pinned
granite-code:8b digest 36c3c3b9683b (CN-001), temperature 0.0, options in every
request (PB-071), one warm process per arm-seed (PB-070), shared GPU lock held
for the whole run; wall clock is the GPU metric (CN-002). Script:
experiments/suite-v3/pilot_headroom.py; artifacts under
results/CONT-005-PILOT/pilot-headroom-<ts>/.

EX-ANTE expectations (declared before any v3 inference; exploratory headroom,
not confirmation):
- X1 guess_calibration: valid-label fraction >= 0.9, max position share <= 0.5,
  equal across arms (the facts were never stated - no arm can have an edge).
- X2 the v2 floor pathology is gone: no scored family at 0.000 in every arm.
- X3 delayed_recall / distractor_recall: arm A low, T0/T2 clearly higher.
- X4 directional only: strict repeated-mistake (reply == scripted trap) higher
  for T0 than T2 on the policy-targeted CR sub-types.
Guard: no new arm-seed starts after 50 min wall.

Run-2 failure + fix (same-day, PB-075 pattern): run 2 crashed AFTER arm T0
seed-11's inference completed - the pilot's own telemetry called
MemoryStore.count_episodes(), which does not exist (the API is count()). No
data lost for arm A (3/3 seeds completed with summaries); T0/seed-11's trace
is complete in the aborted root but its summary was never written, so that
arm-seed re-runs. Fix: count(); plus --resume support (completed arm-seeds
copied into the new root with zero repeated inference, resume recorded in the
aggregate). Run 3 resumes A x3 from pilot-headroom-20261005-071700 and runs
T0 x3 + T2 x3.

## 2026-10-05 — Run 3 post-mortem: two root causes found same day; run 4 clean

Run 3 (T0/T2 executed, A resumed) completed all inference but exposed two real
defects, both proven from the traces:

1. **RC1 - T-arms never wrote memory.** All 53 memory.injected events in T0/seed-11
   have episode_count=0; token totals byte-equal to arm A (13607/13711 pattern).
   Root cause: runner.py gated episode appends on `arm in ("B","C","D","E")` - the
   T-arms were never added, so they degenerated to no-memory runs. Fixed (gate now
   includes T0-T3).
2. **RC2 - label-form replies are prose, not bare labels.** Probe observations like
   "the cost of a season membership is 55." (CORRECT answer, exact_match FAIL) and
   '"20"' (quoted superseded value). Declared the v3 scoring rule in
   SUITE-V3-DESIGN.md section 3 BEFORE run 4: extract standalone option labels
   (word-boundary); pass iff exactly one distinct label and it is the expected one.
   Implemented in runner.score_probe/extract_label (unit sanity 6/6); applies to
   guess_calibration aggregation too. v1/v2 probes (no labels field) take the
   unchanged legacy path.
3. Aggregate crash (max() over empty positions) guarded - same post-inference
   wrapper-crash family as PB-075, third instance this pilot.

Same-day lesson (candidate playbook promotion): the assembly gate validated the
trust RENDERER with its own store-fill simulation, so it could not catch RC1 -
the runner's append gating was never exercised. Ex-ante gates must drive the
PRODUCTION runner path (a dry-run mode or trace-replay), not a parallel
reimplementation of it. To be promoted as PB-077 after the pilot completes.

Run 3 artifacts kept as evidence (pilot-headroom-20261005-073940; aborted run 2
root pilot-headroom-20261005-071700; aborted run 1
aborted-partial-20261005-071210-wallguard-fix). Run 4 = full clean 9 arm-seeds,
no resume (arm A re-runs too: its run-3 scores used the legacy scorer).

Run-4 post-mortem: arm A x3 COMPLETED under the declared v3 label-scoring rule -
**5/24 scored probes per seed (~0.21, chance level for k~6; the v2-style 0-floor
is gone at the very bottom too)**. T0/seed-11 died mid-run on a single hung
Ollama request (provider timeout 300 s at rt-1004 s3t2; server healthy
immediately after - transient). Hardening: bounded fresh-arm-seed retry (2
attempts, partials preserved as seed-N-attemptK-failed, never silent); run 5
resumes A x3 from run 4 and runs T0 x3 + T2 x3.

Run-5 post-mortem (same day): T0/seed-11 timed out AGAIN at the same turn - not
transient: the provider never set num_predict, so a memory-injected repetition
loop could generate past the 300 s request timeout (CN-011 in FINDINGS.md,
closed same day: num_predict=256 now travels in every request, provider default).
Second bug: the retry handler renamed a directory whose journal handle was still
open (no finally-close) -> Windows PermissionError. Fixes: attempt-scoped seed
dirs (seed-N / seed-N-a2, no renames), try/finally closing journal+store,
provider num_predict, resume accepts a2 dirs. Run 6 resumes A x3 from run 5 and
runs T0 x3 + T2 x3 under the hardened loop.

## 2026-10-05 — CONT-005 headroom pilot RUN 6 COMPLETE (exit 0, all 9 arm-seeds)

Run of record: results/CONT-005-PILOT/pilot-headroom-20261005-084818 (A x3 resumed
from run-5 root, zero repeated inference; T0 x3 + T2 x3 fresh under num_predict=256).
Aggregate: aggregate.json in the run root. Model granite-code:8b @ 36c3c3b9683b,
temp 0.0, options in every request incl. num_predict=256 (CN-011). Wall: A ~307 s,
T0 ~345 s, T2 ~365 s per seed; tokens/seed: A 13.6k, T0 30.8k, T2 37.3k.

Per-family mean pass rate (3 seeds each):

| family (probes/seed) | A | T0 | T2 |
| --- | --- | --- | --- |
| contradiction_update (4) | 0.250 | 0.250 | **1.000** |
| correction_reuse (8) | 0.375 | 0.417 | **0.583** |
| delayed_recall (3) | 0.000 | 0.000 | 0.000 |
| distractor_recall (3) | 0.000 | 0.333 | **0.667** |
| repeated_task (6) | 0.167 | 0.333 | 0.333 |
| overall scored (24) | 5/24 | 7-8/24 | **12-13/24** |

RM primary (42 eligible/arm): strict trap-repeat A 3/42 (0.071), T0 0/42, T2 0/42;
error rate A 0.714 > T0 0.619 > T2 0.524 (monotone). Guess probes (18/arm):
valid-label A 1.0 / T0 0.667 / T2 1.0; max position share 0.333 / 0.278 / 0.667.

EX-ANTE VERDICTS:
- X1 MET (mostly): guessing measurable; A/T2 valid 1.0; T2 position share 0.667
  (n=18, noisy) and T0 valid 0.667 - guess aggregation goes into the prereg as a
  mandatory per-arm report, not a gate.
- X2 MET: the v2 floor pathology is gone - A sits at ~chance (0.208 overall),
  arms separate cleanly upward.
- X3 PARTIAL: dx confirmed (0 -> 0.667 with memory); **dr = 0.000 in ALL arms** -
  inspection needed (suspect: replies echo BOTH key codes -> two distinct labels
  -> extraction rule counts a miss). Design input, not a memory failure.
- X4 NOT MET AS STATED, replaced by a better signal: strict scripted-trap repeats
  are ~zero in T0/T2 (granite rarely lands verbatim on the trap), so the strict-RM
  primary has NO headroom on v3; the trust effect manifests as the monotone ERROR
  RATE reduction (0.714 / 0.619 / 0.524) and family-level separation (CU 1.0 vs
  0.25 is the strongest single result of the pilot).

THREE DESIGN INPUTS for the CONT-005 pre-registration (PREREG-REQUIREMENTS-V2):
1. Primary endpoint candidate: label-form error rate on policy-targeted families
   (CR+CU), not verbatim-trap strict RM (no headroom).
2. Fix the delayed_recall extraction artifact (multi-label replies) or reword the
   DR probes ("reply with the code only" enforcement) before freezing.
3. Guess calibration reported per arm; investigate T2's position concentration
   (0.667) before trusting label-position invariance.

## 2026-10-05 — Pilot design inputs applied; EVALUATION-PREP-v2 DRAFT (zero GPU)

- DR fix (design input #2): the three delayed_recall scenarios now pair each
  code/color with a NON-label companion fact (harbor closes at six / relief at
  eight / kettle is steel), so an echo-both reply contains at most one option
  label. Validator re-run: PASS 13/13 (suite v3 digest changed accordingly).
- Power calc v2 for the new primary (experiments/suite-v3/power_calc_v2.py +
  power-results-v2.json, seed 20261005): error-rate endpoint, K=12 (CR+CU),
  5 obs/cluster, T0=0.64. delta 0.36 -> 0.983; delta 0.25 -> 0.812;
  delta 0.20 -> 0.641 (rejected); concentration 8/12 -> 0.893. **MME = 0.25.**
- docs/EVALUATION-PREP-v2.md (DRAFT, not frozen): primary = label-form error
  rate on 12 CR+CU clusters; contrast T0 - T2; MME 0.25; two-sided 95% cluster
  bootstrap; completeness guard (no substitution); held-out suite v3h plan
  (fresh content, v3 protocol + DR fix); freeze manifest includes analysis code
  (template 1); non-executor gates; wall-time reconciliation; droppable
  secondary; execution ~150 min GPU primary-first. Next: independent
  PR-REVIEW-v2 (fresh session), then freeze (author v3h + digests).

## 2026-10-05 — PR-REVIEW-v2 launched (independent pre-registration review)

Reviewer: Fable (claude --model fable -p, fresh context, read-only) — the same
independent-model pattern as the arc review (REVIEW-FABLE.md) and the M6b
author/reviewer separation. Checklist: measurability, falsifiability incl. an
MME-defensibility challenge (0.25 vs pilot 0.36), aggregation/missing-run
handling, held-out isolation of v3h, reverse-engineering risk, template coverage
(all 9 PREREG-REQUIREMENTS-V2 items), and the single-author mitigations. Verdict
GO -> freeze (author v3h + digest manifest); NO-GO -> fold required changes
first. Output will be curated (claims verified against the repo) and saved as
docs/PR-REVIEW-v2.md.

## 2026-10-05 — PR-REVIEW-v2: NO-GO verdict folded same day (zero GPU)

Independent review (Fable, fresh context, read-only; full text + disposition in
docs/PR-REVIEW-v2.md): verdict NO-GO with 5 required changes, all document/
validator. All folded the same session: (1) validator suite-parameterized
(--suite v3h; disjointness now includes the v3 pilot suite; v3 regression PASS),
(2) the pilot-informed primary deviation (RM->secondary, CU->primary) declared
openly in the prereg, (3) SUITE-V3-DESIGN.md added to the freeze manifest (the
scoring rule is frozen by reference), (4) guess-band rule operationalized
(|guess-1/k| per arm, caveat if primary delta < 2x max band) + mandatory
wrong-label vs invalid-format error decomposition, (5) review-notes-reappear
clause. Non-blocking notes 1-4 folded; note 5 (v3h turn arithmetic) is a
freeze-time checklist item. Next: Fable verify-pass on the diff, then freeze
(author suite v3h + analysis script + digest manifest), then the confirmatory
run.

Fable verify-pass on the folded changes: **GO** (all 5 SATISFIED, non-blocking
folded; full table appended to docs/PR-REVIEW-v2.md). Its cosmetic note (validator
report hardcoded the suite name) fixed immediately; v3 regression PASS. Review
cycle complete: prereg is GO for freeze. Freeze checklist (next session):
1) write the analysis script FIRST (digest partner), 2) author suite v3h (fresh
content, v3 protocol + DR fix, validator --suite v3h PASS), 3) freeze manifest
digests (v3h, EVALUATION-PREP-v2, SUITE-V3-DESIGN.md, seeds {1001..1005},
analysis script, validator/claims/runner/provider), 4) non-executor gate
session, 5) confirmatory run (~150 min GPU, primary-first T0/T2 then A/T1/T3).

## 2026-10-05 — Freeze execution started (owner directive: Fable = standing reviewer)

Owner directive recorded: keep consulting Fable at key checkpoints; the
non-executor gate session before the confirmatory run will be a Fable review
(read-only, fresh context). Freeze order per the checklist: 1) analysis script
FIRST (digest partner), 2) suite v3h authoring, 3) freeze manifest, 4) Fable
gate, 5) confirmatory run.

## 2026-10-05 — FREEZE COMPLETE (before any v3h inference)

- Suite v3h authored (27 scenarios: CR x8 with typed sub-types incl. BOTH
  source-conflict orders, RT x6 scripted, CU x4 with superseded_value traps,
  DR x3 with non-label companions, DX x3, GC x3) in fresh worlds (library
  circulation desk, tram depot board). Validator --suite v3h: PASS 13/13
  (positions max share 0.21; zero shared texts with v1/v2/v2-cal/v3 after
  rewording four boilerplate lines). v3 regression PASS.
- Assembly gate --suite v3h: PASS 7/7 (resolution counts exactly as designed:
  user 2, conflict 2, superseded 2, valid-clean 2, CU-clean 4).
- Analysis script analyze_confirmatory_v2.py (frozen constants: seeds
  {1001..1005}, MME 0.25, bootstrap 10k RNG 20261005, verbatim verdict
  wordings, error decomposition, guess-band); dry smoke on the pilot root
  returns "incomplete" cleanly. Run script run_confirmatory_v2.py (arms
  T0,T2,A,T1,T3 primary-first, suite v3h, transient-retry hardened).
- frozen-config-v2.json: sha256 digests for all prereg-designated paths
  (incl. SUITE-V3-DESIGN.md per PR-REVIEW-v2 RC3) + v3h suite digest +
  validation/gate artifacts; recorded BEFORE any v3h inference.
- Authoring slips caught by tooling, not by eye: 1 Python-expression-in-JSON
  (rt-2004), 2 CU scenarios missing their superseded value in the options
  (cu-2003/cu-2004 — the validator's trap-in-labels check), 4 verbatim
  boilerplate texts shared with v3, vocab regex missing underscores
  (on_time). All fixed; final verdicts PASS.
- NEXT: non-executor gate session (Fable per owner directive) -> confirmatory
  run (~150 min GPU) -> analyze with the frozen script -> owner brief.

FREEZE CORRECTION (pre-inference, before first use): run_confirmatory_v2.py
inherited the pilot's 75-min wall guard; the frozen execution plan
(EVALUATION-PREP-v2 section 13) requires ~150 min for 25 arm-seeds inside the
3-h cap. Raised to 170 min; the run script's digest in frozen-config-v2.json
refreshed. No v3h inference has occurred at the moment of this correction; the
Fable gate session below validates the FINAL frozen state.

## 2026-10-05 — GATE-V2 PASS (Fable, non-executor) -> CONFIRMATORY RUN LAUNCHED

Fable gate: GO (6/6 checks passed; digests re-hashed independently; the guard
correction ruled a legitimate pre-inference fix; full verdict in docs/GATE-V2.md).
Its sandbox condition (executor re-runs the zero-inference confirmations
pre-launch) executed: validator exit 0, assembly gate exit 0, GPU free. The
confirmatory run (arms T0,T2,A,T1,T3 x seeds 1001-1005 over suite v3h, ~150 min
GPU under the exclusive lock) launched via run_confirmatory_v2.py. Cosmetic
post-run note from the gate: run_confirmatory_v2.py docstring still carries
pilot-era wording - to be cleaned AFTER the run, outside the frozen digests
never.

## 2026-10-05 — CONT-005 CONFIRMATORY RUN COMPLETE + frozen analysis verdict

Run: results/CONT-005-CONFIRMATORY/cont005-confirmatory-20261005-123917 — all 25
arm-seeds completed (T0/T2/A/T1/T3 x seeds 1001-1005), zero retries needed,
~150 min GPU under the exclusive lock, wall per arm-seed ~305-360 s.

Analysis-script hotfix BEFORE any results were read (crash prevented output):
TypeError in the SECONDARY t1_t3_exploratory_overall block (fmean over lists);
primary logic untouched; recorded in frozen-config-v2.json post_freeze_hotfixes
(M7 c679547 pattern; flagged for owner acceptance).

**FROZEN VERDICT: "no confirmatory difference established"**
- Primary delta (T0 - T2) = **-0.1000**, 95% CI [-0.2833, 0.0000] (cluster
  percentile bootstrap, 10k, RNG 20261005). The CI includes 0; criterion (i)
  failed; direction is NEGATIVE (T2 errors HIGHER than T0 on the held-out
  primary) - the opposite of the pilot's +0.36. Guess-band caveat fired
  (max band 0.333).
- The pilot's T2 advantage did not replicate on held-out fixtures. Per Fable's
  pre-registration note, regression toward the mean from the CU ceiling was the
  named risk; the landing zone proved even less favorable.
- Where the numbers did hold: A at 0.208 overall (guessing level, exactly the
  pilot value); memory arms recover delayed_recall 0.6-0.67 (the non-label
  companion fix worked; was 0.0 in the pilot); CU memory benefit real
  (A 0.00 vs T0 pass 1.0 on 3/4 CU clusters).
- NEW exploratory signals for the next cycle: (1) **T2 and T3 each repeat the
  scripted/superseded TRAP 5/60 times while A/T0/T1 have ZERO** - trust-layer
  annotations may increase trap salience (anchoring-by-flagging hypothesis);
  (2) T1 (annotations only) 0.45 and T3 0.45 beat T2 0.35 overall -
  metadata helps, resolution/policy hurts on this suite; (3) T2 failed cu-2004
  in all 5 seeds (T0 perfect) - the single cluster carrying most of the delta.
- Owner decisions next: accept/reject this confirmatory result; next-cycle
  direction (trap-salience study vs CONT-005 closure); the analysis-script
  hotfix acceptance.

## 2026-10-05 — Fable post-result audit + free label-level re-analysis

Owner requested a second look before acceptance. Fable audit
(docs/REVIEW-FABLE-RESULTS.md): verdict **SOLID WITH CAVEATS** - primary
independently recounted from traces (exact match); the frozen wording is the
only correct reading, and the result is STRONGER than it sounds (CI upper
bound 0.000 excludes the pre-registered effect >= 0.25). Corrections to the
owner brief: the "T2/T3-only trap-repeats" claim was a strict-normalization
artifact (all 5 = cu-2004; A repeated the same trap in quotes; T0 in
sentences); seeds at temp 0.0 are degenerate (effective n ~ 12 binary
observations); one cluster carries 83% of the delta. Hotfix re-verified clean
(2 lines, secondary block, digests match).

Free label-level re-analysis run immediately after (zero GPU): A 25/90 >
T0 15/90 > T2 = T3 10/90 > **T1 0/90** - annotations-only is the only arm
with zero label-level trap repeats. Exploratory; recorded in the audit
appendix. Next-cycle design inputs: fix T2/T3 render-markup leakage into
answers (invalid_format source), supersession on numeric conflicts, and vary
content/positions across seeds (temp-0 seeds do not replicate).

## 2026-10-06 — Owner decisions on the CONT-005 confirmatory result (all defaults accepted)

1. CONFIRMATORY RESULT ACCEPTED ("no confirmatory difference established";
   the CI upper bound excludes the pre-registered >=0.25 effect).
2. ANALYSIS HOTFIX ACCEPTED (secondary-block crash, pre-read, digests recorded).
3. NEXT-CYCLE DIRECTION ACCEPTED: (a) fix the T2/T3 render-markup leakage into
   answers, (b) supersession on numeric corrections, (c) require per-seed
   content variation in the next suite design (temp-0 seeds do not replicate);
   then test the T1-annotations finding properly. The frozen v3h artifacts and
   frozen-config-v2.json remain the untouched record of THIS run; claims.py
   evolves from here for the NEXT cycle (post-acceptance development).

## 2026-10-06 — Next-cycle fixes implemented (zero GPU, per owner defaults)

- claims.py: (1) prose-parenthetical injection annotations (no bracket/pipe
  markup - closes the render-leakage/invalid-format channel seen in v3h);
  (2) R5 numeric supersession ("correction for the records" marker supersedes
  the prior plain statement - closes the cu-2004 gap). Assembly gate CU
  expectations updated (R5 supersession); unit-verified on cu-2001; gates
  re-run: v3h PASS (superseded 2+4), v3 regression PASS, validator PASS.
- docs/NEXT-CYCLE-NOTES.md: next suite requirements (MANDATORY per-seed
  content variation - temp-0 seeds were degenerate; primary with headroom in
  both arms; T1-vs-T0 as the candidate primary contrast; watch residual flag
  bracket echo).

## 2026-10-06 — Session handoff: cycle-2 milestone brief committed

Session boundary per the house pattern (fresh session per milestone; repo as
the state carrier). docs/SESSION-BRIEF-v3i.md = the complete brief for the
next session (suite v3i with per-seed variant tables + EVALUATION-PREP-v3
draft + power artifact; zero GPU; entry conditions verified at 73f1d96; chain
continues Fable PR-REVIEW-v3 -> freeze -> gate -> pilot). Closure state clean:
working tree clean, origin/main synced, no GPU locks, no active automations.

## 2026-10-06 — CYCLE 2 START: suite v3i authoring + prereg v3 draft (zero GPU)

Plan per docs/SESSION-BRIEF-v3i.md (entry conditions verified: main clean at
2a419a0). One milestone, zero GPU: (1) fixtures/v3i with a predeclared
per-seed variant table (values/codes/label-orders/names per seed — the Fable
audit lesson: temp-0 seeds on byte-identical prompts are one run, not five);
(2) validator extended with variant checks (V-namespace continues), runner-side
render in fixtures.py; (3) power_calc_v3 with the NEW between-seed spread
model (shared variant difficulty cancels in the paired T0-T1 delta; arm-variant
interaction is the power killer — scanned explicitly); (4) EVALUATION-PREP-v3
draft: primary contrast T1 vs T0, T2/T3 secondaries after the two claims.py
fixes. Primary set keeps CR(8, sub-types rebalanced toward T1's source/verification
surface)+CU(4)=12 clusters, headroom aimed mid-scale in both arms (explicit
negation in corrections — the v3h CR floor driver). Next command: write
fixtures.py render_seed_variant, then build_v3i.py emitting the suite.

## 2026-10-06 — CYCLE 2 MILESTONE COMPLETE: suite v3i + prereg v3 draft (zero GPU)

- **fixtures/v3i** (27 scenarios, 128 turns/seed, fresh worlds: aquatic
  center, fire brigade roster, theater box office, refuge post, botanical
  garden; ids x-3xxx): predeclared per-seed variant table per scenario
  (values/codes/names + probe label orders; manifest.variant_seeds
  {2001..2005}), emitted deterministically by the committed builder
  (experiments/suite-v3/build_v3i.py). Primary CR(8, sub-types rebalanced to
  T1's source/verification surface: valid_env 2, valid_tool 1, erroneous_user
  2, source_conflict 2, retraction 1) + CU(4, R5, near-miss options) = 12;
  headroom lever: every correction explicitly negates the superseded routing
  (cycle-1 CR floored both arms on 6/8).
- **Render single-definition:** continuity.fixtures.render_seed_variant +
  load_suite_for_seed; loader relaxed for variant scenarios (expected
  materializes at render). Runner unchanged (renders upstream in run scripts);
  validator and assembly gate IMPORT the same function (no divergence).
- **Validator extended** (validate_fixtures_v3.py): --suite v3i; per-suite CR
  sub-type tables; per-scenario checks run on the RENDERED multiset (all 135
  instances); new V14-variant-table (+V14b token closure), V15-seed-variation
  (probe texts distinct per seed; identical-across-seeds turn share <= 0.50),
  V16-label-order-varies (pairwise-distinct orders; expected position >= 3
  distinct slots). Authoring slips caught by tooling, not by eye: 1 label leak
  (pq 'tanker'), 1 leak ('patrol set'), validator V3 dup-id false-positive
  fixed (count over base scenarios). v3i PASS 16/16; v3 + v3h regressions PASS.
- **Assembly gate extended** (--suite v3i [--seed]): v3i PASS 7/7 on ALL five
  seeds (resolutions exactly as designed: user 2, conflict 2, superseded
  4 CU-R5 + 1 retraction, clean 3); G2 annotation counter fixed for prose
  render ("source: " not "|source: "); v3 + v3h regressions PASS. Artifacts:
  fixture-validation-v3i.json, assembly-gate-v3i.json.
- **Power calc v3** (power_calc_v3.py / power-results-v3.json, seed 20261006):
  NEW between-seed spread model — shared variant difficulty eps_s cancels in
  the paired T0-T1 delta (P2 0.855 ~ binomial 0.844 at delta 0.25);
  arm-variant interaction is the power killer. MME 0.25: power 0.842
  (conservative 0.20/0.10), 0.810 (stress 0.20/0.15); delta 0.20 rejected
  (0.670); concentration 8/12 -> 0.705 (caveat; pilot per-cluster report
  covers it); T0 sensitivity 0.40-0.64 -> 0.814-0.834.
- **docs/EVALUATION-PREP-v3.md DRAFT** (all 9 PREREG-REQUIREMENTS-V2 items):
  primary contrast T0 - T1 two-sided with pre-declared harm-direction wording;
  two-stage design — pilot on v3i at FREEZE-A (GO/NO-GO: headroom (0.15,0.85)
  both arms; per-seed spread sd <= 0.25 else stress row + owner sign-off;
  residual bracket-echo check with pre-authorized NOTE: fix), confirmatory on
  held-out v3j authored at FREEZE-B (fresh content, same protocol, seeds
  {3001..3005}, analysis script first); variant-integrity guard (per-seed
  rendered digests frozen); T1 budget-matching declared as limitation.
- Frozen cycle-1 artifacts and frozen-config-v2.json untouched; validator/
  assembly-gate/fixtures digests recorded there are the cycle-1 record —
  superseded for cycle 2 per the post-acceptance development pattern (73f1d96).
- NEXT: Fable PR-REVIEW-v3 on this draft (standing-reviewer directive) ->
  fold -> FREEZE-A -> Fable gate -> pilot (~150 min GPU).

## 2026-10-06 — PR-REVIEW-v3 LAUNCHED (independent pre-registration review, cycle 2)

Next chain step per SESSION-BRIEF-v3i: Fable reviews the EVALUATION-PREP-v3
draft (standing-reviewer directive) BEFORE FREEZE-A. Same pattern as
PR-REVIEW-v2: claude --model fable -p, fresh context, read-only, repo root,
numbered-task prompt, raw output to temp then curated into
docs/PR-REVIEW-v3.md with claim verification. Checklist adds cycle-2 angles:
paired-delta power argument (eps_s cancellation), two-freeze design
(FREEZE-A pilot v3i -> FREEZE-B v3j pilot-informed calibration), per-seed
variant mechanics (V14-V16, render single-definition, seed doubling as
sampler+variant key), CU T0-ceiling risk (cycle-1 CU err 0.0), MME 0.25
defensibility for the cheap T1 intervention. Verdict GO -> FREEZE-A; NO-GO ->
fold required changes same session + Fable verify-pass on the diff.

## 2026-10-06 — PR-REVIEW-v3 COMPLETE: NO-GO folded same day -> verify-pass GO (zero GPU)

- Fable verdict on the EVALUATION-PREP-v3 draft: **NO-GO with 5 required
  changes** (all document/validator/artifact). Full text + disposition +
  verify-pass: docs/PR-REVIEW-v3.md. All load-bearing review claims re-verified
  by the implementing agent before folding (4/4 exact: bimodal T0 pooled 0.50
  passing the pooled gate; T1/T3 0.45 tie; single-seed gate artifact +
  hardcoded "14 primary"; ~15% clip-floor probability).
- The substantive catch: the pilot headroom gate was pooled-mean and would
  have passed the EXACT cycle-1 pathology (T0 pooled 0.50 = 6/8 CR floored +
  4/4 CU ceilinged). Folded as per-family headroom (CR and CU family means
  each strictly inside (0.15, 0.85) in both primary arms) + a live-cluster
  concentration rule (<8/12 live -> P5 power row governs + owner sign-off).
- All 5 required changes folded + 8 non-blocking notes folded (incl.
  arm-neutrality gate check for v3j corrections, variant-seed=sampler-seed
  confound sentence, sd CI reporting, power-model clipping/shared-eps caveats
  recorded in power_calc_v3.py, per-seed gate artifacts seed2001..2005
  committed, dynamic G3 count). Fable verify-pass on the diff: **GO for
  FREEZE-A**, one execution condition: analyze_pilot_v3.py must be written and
  digested AT FREEZE-A (it does not exist yet - that is the freeze work item).
- NEXT (fresh session per house pattern): FREEZE-A - write analyze_pilot_v3.py
  + the pilot run script FIRST, digest manifest (this doc, v3i suite +
  per-seed rendered digests, validator, gate, claims/runner/provider/fixtures,
  seeds {2001..2005}), Fable non-executor gate, then the pilot (~150 min GPU).

## 2026-10-06 — FREEZE-A EXECUTION (before any v3i inference)

Order per EVALUATION-PREP-v3 §10 (amended by PR-REVIEW-v3 RC2): 1) analysis
script FIRST — analyze_pilot_v3.py written and functionally smoked on
synthetic data (clause 1 per-family headroom, clause 2 sd with df=4 CI
[0.6x/2.9x multipliers verified], clause 3 live clusters, clause 4 echo scan;
incomplete-root dry smoke returns cleanly — the v2 analysis-hotfix lesson
applied pre-freeze); 2) run_pilot_v3.py written (arms T0,T1,A,T2,T3
primary-first, per-seed variant rendering via load_suite_for_seed, wall guard
170 min, transient retry, resume); 3) zero-inference confirmations re-run:
validator v3i PASS 16/16 (+ v3/v3h regressions PASS), assembly gate PASS 7/7
x all five seeds (fresh artifacts); 4) frozen-config-v3a.json digest manifest
(next commit, records the frozen-content rev); 5) Fable non-executor gate;
6) pilot launch.

## 2026-10-06 — GATE-V3A PASS (Fable, non-executor) -> PILOT LAUNCHED

- Fable gate: **GO** (6/6 checks; 19/25 digests re-hashed independently; the 6
  computed digests verified by chain via fixture-validation-v3i.json's
  suite_sha256; full verdict in docs/GATE-V3A.md).
- Sandbox condition executed by the executor pre-launch (all byte-match):
  fixtures/v3i_suite f5c0f5a9bab7...; rendered seeds 2001-2005
  4527d3a2a51a..., 56cf3b1743ae..., 148618c35212..., 6ff9468295f2...,
  2d7f3eee242a... **Rendered-digest recipe (GATE-V3A condition b, fixed as
  the run-record reference): sha256 over the concatenation of
  json.dumps(scenario, sort_keys=True, ensure_ascii=True) for the seed's
  rendered scenarios sorted by id, rendering = continuity.fixtures.
  render_seed_variant (the same code path run_pilot_v3.py uses).**
- Gate conditions (a) done, (b) recorded above, (c) binding: post-run numbers
  come ONLY from the frozen analyze_pilot_v3.py.
- Pilot launched via run_pilot_v3.py (arms T0,T1,A,T2,T3 x seeds
  {2001..2005}, per-seed variants, ~140-160 min GPU expected under the shared
  lock; wall clock the GPU metric per CN-002).

## 2026-10-06 — CYCLE-2 PILOT COMPLETE: 25/25 arm-seeds, frozen GO/NO-GO verdict

Run of record: results/CONT-005-C2-PILOT/pilot-c2-20261006-093202 — all 25
arm-seeds (T0,T1,A,T2,T3 x seeds 2001-2005) completed, zero retries, ~128 min
GPU (09:32-11:45), 3200 requests, wall/arm-seed ~296-345 s. Analysis from the
FROZEN analyze_pilot_v3.py only (GATE-V3A condition c); pilot-go-nogo.json
committed with the run.

**Per-seed variants WORK**: per-seed primary means genuinely differ (T0
0.333-0.583, sd 0.095 CI [0.057, 0.273]) — the cycle-1 degeneracy (identical
answers everywhere) is gone; clause 2 PASS.

**GO/NO-GO verdict: REBALANCE (CU) | OWNER SIGN-OFF (concentration) | ECHO
FIX — all three routed actions at FREEZE-B, none silent:**
- Clause 1 (per-family headroom): CR PASS both arms (T0 0.675, T1 0.700
  error — mid-scale as designed); CU FAIL both arms (0.050 error — the
  ceiling risk Fable named as the biggest design risk materialized: near-miss
  options did not make CU hard) -> CU rebalanced in v3j.
- Clause 3 (live clusters): 0/12. The surface is bimodal at cluster level:
  cr-3001/3003/3004/3008 both arms floored at 1.0; cr-3005/3006/3007 both at
  0.0 (the explicit-negation lever made the erroneous-user/conflict clusters
  easy for everyone); cr-3002 T0 0.0 vs T1 1.0 (discriminates, both pinned);
  CU all 0.0. The T1-vs-T0 delta on this surface (raw -0.017) is
  uninformative — the pre-registered guardrail correctly refuses to treat it
  as evidence. P5 row (0.705 at 8/12) governs + owner sign-off required.
- Clause 4 (echo): [RESOLVED brackets present in 31/640 T2 and 39/640 T3
  replies (NEXT-CYCLE-NOTES residual risk confirmed) -> flags move to plain
  NOTE: prose at FREEZE-B (pre-authorized fix class).

Exploratory secondaries (no verdicts): T2 CU pass 0.50 vs T0 0.95 — the R5
supersession flags HURT T2 on CU this pilot; T2/T3 guess valid-label 0.80/
0.733 vs 1.0 elsewhere (trust arms produce messier answers); DR/DX 1.0 for
all memory arms (anchors saturated); RT T1 0.433 vs T0 0.333.

NEXT: owner sign-off (clause-3 routing) -> FREEZE-B: author v3j with CU
harder AND CR un-bimodalized (mid-difficulty clusters where arms can differ),
NOTE: prose flags, fresh seeds {3001..3005}, analysis script FIRST, Fable
gate, confirmatory run.

## 2026-10-06 — Owner sign-off received (FREEZE-B authorized) + results digest

- Owner: "я ок" — clause-3 routing satisfied; FREEZE-B (v3j: CU harder, CR
  un-bimodalized, NOTE: prose flags, seeds {3001..3005}, analysis script
  FIRST, Fable gate, confirmatory) is authorized to proceed.
- docs/RESULTS-DIGEST-2026-10.md: cross-project results digest (proven
  findings + engineering lessons + artifact pointers) for the owner's
  evaluation of his other memory project (OCL). Pushed so a GitHub link can
  be shared.

## 2026-10-06 — FREEZE-B EXECUTION (before any v3j inference)

Order per EVALUATION-PREP-v3 §10: 1) analysis script FIRST —
analyze_confirmatory_v3.py written and functionally smoked on synthetic run
roots built from the real rendered v3j (all four frozen verdict paths hit
their exact wording: established / reverse-established / sub-MME boundary
checked / no-difference / incomplete; decomposition, label-level trap repeat,
echo scan ([RESOLVED must-be-zero + NOTE: echo rate), guess-band caveat,
between-seed sd with df=4 CI, T0-T2/T0-T3 secondary bootstraps, CU
superseded-value share all verified on synthetic data — the v2 analysis-hotfix
lesson applied pre-freeze); 2) run_confirmatory_v3.py written (arms
T0,T1,A,T2,T3 primary-first; seeds {3001..3005}; per-seed rendering; the
GATE-V3A condition-b recipe institutionalized: preflight re-verifies the
suite + 5 rendered digests fail-closed against the freeze manifest before
any inference); 3) NOTE: prose fix in claims.py (pilot clause-4,
pre-authorized class — gate-matched substrings kept); 4) suite v3j authored
via build_v3j.py (27 scenarios, fresh worlds museum/marina/bakery/airport,
ids x-4xxx, 130 turns/seed): CU recency-defeat redesign (cu-4101
retracted_correction, cu-4102/4103 user_override vs verified evidence,
cu-4104 v3i anchor), CR sub-types IDENTICAL to v3i with wording levers only
(indirect counter-evidence, trap-surface probe cases, withdrawal restating
the rule with its label, both conflict orders across cr-4006/4007); 5)
validator --suite v3j PASS 16/16 + regressions v3/v3h/v3i PASS; assembly
gate v3j PASS 7/7 x all five seeds (fresh artifacts committed), v3i
regression PASS; 6) frozen-config-v3b.json digest manifest (25 digests,
incl. per-seed rendered); cross-check vs FREEZE-A: untouched paths
byte-identical, exactly the 3 declared changes (claims.py NOTE: fix,
validator v3j registration, gate v3j registration + CU-mechanism branches +
G3b un-vacuated); manifest self-verified against the run script's own
digest-verification code path. NEXT: Fable non-executor gate → confirmatory
run (~2.5 h GPU).

## 2026-10-06 — GATE-V3B: GO (Opus substitution, declared) -> confirmatory launch

- **Fable limit-blocked at gate time** ("You've reached your Fable 5 limit",
  verified twice). The non-executor gate ran on **Opus** (claude --model opus
  -p, fresh context, read-only) with the substitution declared up front in
  the prompt and in docs/GATE-V3B.md; the owner may re-bind the gate to Fable
  (standing directive 05.10 names Fable for gates).
- Verdict **GO** (docs/GATE-V3B.md): completeness §10 PASS (2 pilot scripts
  absent from the v3b manifest — byte-identical to FREEZE-A, no protocol
  harm); 19/19 file digests re-hashed independently; analysis script
  implements §3-§9/§12 verbatim (χ² df=4 multipliers checked; sub-MME wording
  confirmed); run script predeclared + the new freeze-digest preflight gate
  verified to run BEFORE any inference; exactly the 3 declared changes vs
  FREEZE-A, all additive/tightening (claims.py = purely the 5 flag strings;
  G3b confirmed to have been VACUOUS pre-fix); no v3j inference anywhere.
- Executor curation of the gate's claims: PASS (pilot digests, gate
  artifacts, verdict wordings via import, digest triple-check) — appendix in
  docs/GATE-V3B.md.
- Gate conditions A-E accepted: (A) run WITHOUT --skip-digest-verify + fresh
  validator/gate passes into tmp before the run; (B) the flag is banned;
  (C) execution revs recorded (manifest records the pre-freeze rev 10fb461,
  frozen content lives at 10f2a8d — FREEZE-A convention); (D) run record
  carries decomposition beside the delta (T0-only bracket asymmetry noted —
  post-fix T0 is the only arm with bracket markup in its memory block;
  pilot baseline invalid-format T0 16/60 vs T1 14/60), bracket_hits_total,
  the SIGNED guess-caveat comparison, and the P5 row (0.705) governing the
  power claim; (E) two informative notes (pilot scripts outside the v3b
  manifest; comment-only χ² rounding) recorded in GATE-V3B.md.
- Confirmatory launched per condition A: fresh validator PASS 16/16 + gate
  PASS 7/7 x 5 seeds into tmp (byte-comparable details, committed artifacts
  untouched), then run_confirmatory_v3.py WITHOUT --skip-digest-verify
  ("freeze digests verified ... byte-match" printed before preflight ok).

## 2026-10-07 — CONFIRMATORY COMPLETE 25/25: frozen verdict "no confirmatory difference established"

Run of record: results/CONT-005-C2-CONFIRMATORY/confirm-c2-20261006-230445 —
all 25 arm-seeds completed (23:04-01:20, ~2h16m wall/GPU, 3250 requests, zero
retries, single execution rev bb515ff, digest preflight line present before
preflight ok). Analysis from the FROZEN analyze_confirmatory_v3.py only.

**Primary (T0 - T1): delta -0.0167, 95% CI [-0.1667, 0.1000] -> "no
confirmatory difference established."** The CI is tight (+-0.13) and excludes
the pre-registered MME 0.25 in BOTH directions — an informative null:
provenance annotations neither reduce nor increase label-form errors on the
rebalanced mid-difficulty surface. Guess-band caveat fired (max arm band
0.20; signed comparison per GATE-V3B condition D). Secondary contrasts also
null: T0-T2 -0.0667 CI [-0.2667, 0.1500]; T0-T3 -0.0167 CI [-0.1667, 0.1667]
— the heavier trust machineries show no post-fix effect either.

Design targets hit: CU family error 0.05 (pilot) -> T0 0.35 / T1 0.30
(rebalance worked; both families mid-scale); per-seed spread tight (T0 sd
0.070, T1 sd 0.075); per-cluster surface mostly live (cr-4001 floored 1.0/1.0
— anchoring persists on the own-answer cluster; cr-4007 + cu-4103/4104 zeroed
— cu-4103 means BOTH arms solved the verified-correction-vs-user-push
recency-defeat).

Echo fix verified in the wild: bracket echo 0 replies (pilot 31+39); residual
NOTE: prose echo 19/650 (T2) and 52/650 (T3); invalid-format T1 4/60, T2
7/60, T3 12/60 vs T0 11/60 — no format blow-up from the NOTE flags (the
gate's T0-only bracket-asymmetry concern did not materialize into a delta).

Cycle-1 label-level finding NOT replicated: trap repeats T1 8/60 vs T0 7/60
(cycle 1: T1 0/90 vs T0 15/90) — T1's earlier cleanliness was a surface
artifact, not an annotation effect. A-arm sanity: error 0.82 without memory
vs ~0.53-0.60 with — the memory effect itself replicates strongly. Token
cost: T1 +5.6% vs T0 (cycle 1: +21%); T3 +37%.

Owner brief: docs/OWNER-BRIEF-CONT005-C2-CONFIRMATORY.md (decisions: accept
result + close direction; accept Opus gate substitution; annotate the results
digest; next thread CONT-002). CONT-005 closes either way per the
pre-registered plan.

## 2026-10-07 — Owner acceptance recorded; CONT-005 CLOSED; next-direction consultation

- Owner: "все так" — decisions 1-3 of the brief accepted (result + close;
  Opus substitution; digest annotation). Recorded in ROADMAP "Owner decisions
  — recorded 2026-10-07"; RESULTS-DIGEST-2026-10.md annotated (T1's cycle-1
  0/90 signal reclassified as a surface artifact: 8/60 vs T0 7/60).
- Standing reviewer queue (owner directive): Fable → Opus → local GLM 5.3
  Flash, in that order of availability.
- Commit 6f2d974 (docs/REFLECTION-V2-PROPOSAL.md, 366 lines, authored under
  the owner's git identity during the confirmatory run) reviewed by the
  implementing agent: it is the owner's idea retold by the co-owner advisor
  model — CONT-006 "Reflection as Lesson Extraction" (arms R0-R3 incl. the
  manual-gold-lessons control R3; 3-way data split; 4 critical causal tests;
  telemetry-first "NO_LESSON is first-class" design). Quality: strong — the
  R3 arm directly de-risks the main threat (the core may simply ignore
  injected lessons, the shared failure mode of both CONT-005 nulls).
- Implementing-agent recommendation for sequencing (owner to confirm):
  (1) CONT-006 proposal review cycle NOW (zero GPU, author/reviewer split —
  review file first, then an independent reviewer from the queue);
  (2) CONT-002 next arc — its 2026-10-04 deferral condition (label-form
  probes) is satisfied by the v3 suite work, mechanics proven at M2b,
  Qwen3.6-35B-A3B already imported in Ollama, and it tests a different axis
  (state portability) after two nulls on the metadata axis;
  (3) CONT-006 build AFTER CONT-002 — its critical test 4 (cross-model
  lesson transfer) reuses exactly the CONT-002 A/B-core machinery, so the
  sequencing is synergistic rather than competitive.
- Milestone answer: the proposal does not slot into any M1-M8 entry (arc
  COMPLETE); it opens a NEW milestone line — "CONT-006 proposal review"
  (zero GPU) — and then CONT-006 becomes the next-next arc.

## 2026-10-07 — Owner "ок": direction DECIDED + CONT-006 review cycle COMPLETE (GO-with-changes)

- Owner confirmed the sequence: (1) CONT-006 proposal review NOW; (2) CONT-002
  next arc; (3) CONT-006 build after. ROADMAP decision 4 updated; SESSION
  brief for the CONT-002 design milestone authored
  (`docs/SESSION-BRIEF-CONT002.md`, zero GPU, behavioral run owner-gated).
- **Reviewer queue exercised end-to-end for the first time:** Fable
  weekly-limited ("resets 8pm Europe/Kyiv"), Opus weekly-limited too →
  **local GLM 5.3 Flash** ran the independent proposal review (fresh-context
  agent, read-only, proposal-first, explicitly barred from reading the
  implementing-agent review). Both substitution steps declared in the review
  doc header.
- Implementing-agent review: `docs/review-reflection-v2-implementing-agent.md`
  (RC-1 freeze the lessons-store artifact chain; RC-2 deterministic
  lesson-acceptance rule ex ante; RC-3 blind+protocol-timed R3 authoring;
  RC-4 import the five 2026-10-04 amendments + v3 protocol machinery;
  RN-1..RN-5 incl. experience set from the ~50 existing committed arm-seed
  traces — zero GPU — and granite-first reflector).
- Independent review: `docs/REVIEW-CONT006-PROPOSAL.md` — verdict
  **GO-with-changes**: RC-1 R3 must inherit R2's retrieval/injection
  machinery (the proposal's "Same as R0" wording confounds source with
  delivery channel); RC-2 two-phase design (lessons NOT injected during
  experience accumulation — removes the trajectory confound and keeps the
  GPU budget at one shared experience pass); RC-3 ex-ante contamination
  protocol (frozen failure taxonomy, blind gold-lesson authors,
  digest-frozen Lessons Store before the first transfer request,
  non-executor contamination gate); RC-4 prose + anti-salience lesson
  authoring (LL-CONT-017 as written is an anchoring-by-flagging risk;
  D−C=+0.5015 parroting is the proven harm channel); RC-5 fill the
  pre-registration fields. Executor curation: 7/7 load-bearing claims
  reproduced (appendix in the review doc).
- Convergence between the two independent reviews: freeze/digest discipline
  for the LLM chain, blind R3 authoring, anti-salience prose lessons, the
  five amendments, empty prereg fields, scope guard OK. Divergent finds
  recorded in both docs (R3 confound + experience-loop = Flash; existing
  traces as experience + deterministic acceptance rule = implementing
  agent).
- NEXT: co-owner folds RC-1..RC-5 (+ the implementing-agent set) into
  `docs/REFLECTION-V2-PROPOSAL.md`; fresh session opens
  `docs/SESSION-BRIEF-CONT002.md` (CONT-002 design + pre-registration, zero
  GPU).

## 2026-10-07 — CONT-002 design milestone START (per docs/SESSION-BRIEF-CONT002.md)

- Plan: (1) `docs/CONT-002-DESIGN.md` — the 2×2 {core A granite-code:8b,
  core B Qwen3.6-35B-A3B} × {state learned on A imported, clean}, primary
  endpoint R = ΔB/ΔA with the inspirer's non-estimable clause verbatim
  (research-proposal.md:126), family choice declared (DR/DX primary);
  (2) suite v3k authoring (protocol v3i as-is, ids x-5xxx, fresh worlds,
  seeds {5001..5005}) + validator `--suite v3k` extension + regressions
  v3/v3h/v3i/v3j; (3) power artifact for R's cluster bootstrap (paired
  4-cell model); (4) `docs/EVALUATION-PREP-CONT002.md` draft (9 template
  items + all five 2026-10-04 amendments); (5) B-core feasibility note from
  M2b traces inside the design doc.
- State: repo clean on main @ 31962bc; entry conditions verified (CONT-005
  CLOSED + accepted; CONT-002 next arc per owner "ок" 2026-10-07; deferral
  condition satisfied by v3 label-form work; mechanics 5/5 at M2b).
- Zero GPU; no behavioral runs (never-autonomous clause stands; behavioral
  work starts only after owner accepts the pre-registration).

## 2026-10-07 — CONT-002 design milestone COMPLETE (design + suite v3k + prereg draft + power)

Zero GPU; all exit artifacts of docs/SESSION-BRIEF-CONT002.md delivered.

- `docs/CONT-002-DESIGN.md`: the 2x2 {granite-code:8b, Qwen3.6-35B-A3B} x
  {restored, clean} with the inspirer's R = dB/dA clause verbatim
  (research-proposal.md:126); A+restored deliberately uses the SAME
  export->import pipeline as B+restored (core is the only difference);
  family choice declared: DR/DX primary (largest cleanest memory benefit,
  ~0.85 -> the R denominator stays estimable), CR/CU/RT absent
  (memory-can-hurt transfer is a different question); B-core feasibility
  note from M2b traces (B+state 8.9 s vs B+clean ramble 73.5 s/turn; total
  est 2.5-5 h GPU, cap 5.5 h, pilot measures first).
- `fixtures/v3k` (builder `build_v3k.py`, deterministic re-run verified):
  18 scenarios = DR x7 + DX x8 (15 primary clusters, class
  transfer_eligible) + GC x3; seeds {5001..5007} predeclared; fresh worlds
  (cable-car stations, chemistry stockroom, theater props loft, quarry
  weighbridge office; gc: orchard shed, brewery cellar, observatory dome);
  72 turns/seed. Validator extended (--suite v3k: per-suite FAMILY_PLANS,
  V8R recall-eligibility incl. DX lure structure, per-suite V11 probe
  class): v3k PASS 16/16 + regressions v3/v3h/v3i/v3j PASS
  (fixture-validation-v3k.json committed; suite sha256 06b897f6e727a0cc...).
- SIZING FINDING (the milestone's real number): at the MME R = 0.25 the
  naive 12 clusters x 5 seeds gives detection power 0.604 — the binding
  constraint is per-observation binomial noise, not cluster spread (K15x5
  0.692, K12x7 0.735). Resized to K15x7 -> 0.801 on the conservative row
  (stress 0.767/0.720 govern via pilot clauses; false positive 0.033;
  "established"-branch near 0.5 AT exactly MME declared openly, cycle-2
  precedent). Power artifact: power_calc_cont002.py +
  power-results-cont002.json (seed 20261007, 15 rows incl. the undersized
  alternatives kept for the record).
- `docs/EVALUATION-PREP-CONT002.md` DRAFT: all 9 template items (frozen
  analysis code incl. pilot GO/NO-GO + confirmatory scripts; infrastructure
  clause; multi-rev; non-executor gates from the standing queue; wall-time
  reconciliation incl. per-cell sums; power section with freeze-time
  re-check; droppable-secondary with pre-declared GC-B trim; carried-over
  review notes; guessing band on BOTH cores + dB-scale MME clearance).
  Estimability gate numeric: dA >= 0.30 AND dA CI excludes 0, else
  "non-estimable, deltas as diagnostics, no alternative denominator".
  Two-stage: pilot {5001,5002} (feasibility GO/NO-GO: B label-form
  compliance < 0.30 invalid, wall-time, dA >= 0.45) -> confirmatory all 7
  seeds, single freeze, pilot data part of the final dataset (analysis
  frozen before any inference).
- NEXT: PR-REVIEW-CONT002 by a fresh non-executor session from the queue
  (Fable -> Opus -> GLM 5.3 Flash) -> fold -> OWNER GATE (explicit
  acceptance before ANY behavioral run; never-autonomous) -> freeze -> gate
  -> pilot -> confirmatory.

## 2026-10-07 — PR-REVIEW-CONT002 COMPLETE: Fable GO-with-changes (RC-1..5) -> folded -> verify-pass GO

- Reviewer: **Fable** (claude --model fable -p, fresh context, read-only,
  repo root) — first in the standing queue, no substitution needed (owner
  confirmed availability). Record: docs/PR-REVIEW-CONT002.md (raw review
  verbatim + executor curation appendix + disposition + verify-pass).
- Fable's summary: "дизайн і пререєстрація — найчистіші в лабораторії на
  сьогодні" (inspirer clause reproduced verbatim and operationalized
  honestly; 12x5 -> 15x7 sizing judged LEGITIMATE design-time sizing, not
  MME reverse-engineering; single-freeze contamination scheme almost
  closed). Template coverage 9/9 (2 stretch marks).
- Required changes, all executor-verified load-bearing and folded same
  session: RC-1 temporal contradiction (pilot-dependent MME re-derivation
  was anchored "at freeze" while the single freeze precedes the pilot;
  thresholds 0.45 vs 0.60 unexplained) -> pilot-gate checkpoint + threshold
  ladder 0.30/0.45/0.60 + frozen upward-only formula
  R_MME' = max(0.25, max(0.15, 2*band_max)/dA_measured); RC-2 per-family R
  backdoor (ratio reporting gated on the pooled estimability gate;
  non-estimable branch computes NO ratios at all); RC-3 stale validator
  docstring ("12" after the 15x7 resize — the resize missed the prose;
  fixed, suites re-PASS); RC-4 gate instructions extended ((a) non-executor
  regression artifact for v3/v3h/v3i/v3j — the committed verdicts predate
  the validator extension, so "regressions PASS" was executor
  self-attestation; (b) frozen-script dry-run verification + clean-cell
  empty-store isolation); RC-5 invalid-format share defined in the prereg
  text (stop criterion cannot live only in an unwritten script).
- Notes folded: N-1/N-2 carried-note obligations named in §12; N-3 worst
  case stated plainly (~6+ h B-side if every no-record turn rambles; NO-GO
  is the backstop, the GC-B trim covers only moderate overrun); N-4
  degenerate-bootstrap-draw handling specified; N-5 Ollama version +
  offload config pinned into the freeze manifest. N-6 (reviewer sandbox
  blocked execution) acknowledged and converted into mechanical gate
  checks via RC-4.
- Verify-pass: validator v3k + v3/v3h/v3i/v3j PASS x5 post-fold; no
  pilot-dependent "at freeze" remains; no frozen artifact touched
  (fixtures/v3k sha256 unchanged; old fixture-validation-*.json unmodified).
- NEXT: **owner gate** — explicit acceptance of EVALUATION-PREP-CONT002
  (with the folded RC) before ANY behavioral run (never-autonomous). After
  acceptance: FREEZE (run script + pilot/confirmatory analysis scripts
  FIRST, digests, environment pin) -> non-executor gate (incl. RC-4a
  regression artifact + RC-4b script dry-run) -> pilot {5001,5002} ->
  pilot-gate checkpoint -> confirmatory 7 seeds.
