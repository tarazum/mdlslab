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



