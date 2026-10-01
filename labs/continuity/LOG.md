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



