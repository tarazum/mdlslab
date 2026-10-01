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



