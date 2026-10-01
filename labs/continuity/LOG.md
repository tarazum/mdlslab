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



