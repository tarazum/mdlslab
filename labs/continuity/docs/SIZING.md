# CONT-000 sizing — arm A variance/headroom pilot (P0b, milestone M1)

Source of truth: `results/CONT-000/pilot-armA-20261001-222950/` (per-seed `trace.jsonl`,
`summary.json`, `env.json` + `aggregate.json`). All numbers below are read from those
artifacts, not from console output (PB-067).

## Run configuration

| Field | Value |
| --- | --- |
| Model | `granite-code:8b`, digest `36c3c3b9683b…a18dd` (pinned via `/api/ps`, CN-001) |
| Backend | Ollama 0.34.2, `http://localhost:11434`, Python 3.12.10 |
| Sampling | temperature 0.0, num_ctx 4096, seed per run, options in every request (PB-071) |
| Seeds | predeclared {11, 22, 33, 44, 55} — all run, none skipped |
| Process model | one warm process, suite loaded once, warmup 2.2 s excluded from stats (PB-070) |
| Suite | 10 scenarios, 4 families, 26 turns and 10 probes per seed, 130 requests total |
| GPU | exclusive shared lock held for the run (see CN-005 for the idle-threshold caveat) |

## Per-family pass-rate spread across seeds (arm A)

| Family | Probes/seed | Pass rate per seed (11/22/33/44/55) | Spread (range) | Mean |
| --- | --- | --- | --- | --- |
| delayed_recall | 3 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.000 | 0.000 |
| distractor_recall | 2 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.000 | 0.000 |
| contradiction_update | 2 | 0.000 / 0.000 / 0.000 / 0.000 / 0.000 | 0.000 | 0.000 |
| repeated_task | 3 | 0.667 / 0.667 / 0.667 / 0.667 / 0.667 | 0.000 | 0.667 |

Per-scenario detail (pass count over 5 seeds): dr-0001 0/5, dr-0002 0/5, dr-0003 0/5,
dx-0001 0/5, dx-0002 0/5, cu-0001 0/5, cu-0002 0/5, rt-0001 5/5, rt-0002 0/5, rt-0003 5/5.

Reading (exploratory, arm A only):

- The three memory-dependent families sit at a stable 0.000 floor — the arm-A agent
  cannot carry facts across sessions and hallucinates plausible values instead
  (e.g. "1634" for the 1783 sundial; "20"/"200" passengers where the corrected value is
  18). This is exactly the headroom CONT-001's memory arms must clear.
- `repeated_task` mixes an intuitive sub-case (rt-0001, "crash → bug": 5/5 without
  memory) with rubric-dependent ones (rt-0002: 0/5 — arm A answers `bug` where the
  rubric says `account`; rt-0003: 5/5, but see CN-004 — the `perf` option leaks).
- Outcome variance across seeds is 0.000 on every family; token-level output drift
  across seeds does exist at temperature 0.0 (CN-003), so zero spread is a property of
  these particular probes, not a guarantee.

## Token and latency statistics (warm, 130 measured requests)

| Metric | Value |
| --- | --- |
| Inference latency, Ollama `total_duration` | mean 265.5 ms · median 180.3 ms · p90 467.8 ms · p95 527.3 ms · max 571.2 ms |
| Effective wall per request (trace `env.turn` → `agent.response`) | mean ≈ 2.3 s (2–3 s at 1 s timestamp resolution) — see CN-002 |
| Wall per full seed (26 requests) | ≈ 60 s (59.7–60.2 s) |
| Tokens per request | prompt mean 83.6 · eval mean 11.7 |
| Tokens, whole pilot | prompt 10,865 · eval 1,520 · total 12,385 (~2,476 per seed) |
| Pilot GPU occupancy | ≈ 5 min wall including warmup (22:29:41 → 22:34:58), far inside the 60 min budget |

For planning, use the wall numbers (~2.3 s/request, ~60 s/seed-arm), not `total_duration`
(CN-002: the reported duration excludes ~2 s per request of unexplained overhead).

## Recommended CONT-001 sizing

- **Seeds: 5.** Seed-to-seed outcome spread measured at 0.000 makes more seeds
  statistically redundant, but seed-only output drift is real (CN-003: 4/26 responses
  differed between seeds at temperature 0.0), and at ~60 s GPU per seed the extra
  insurance against a marginal probe flip costs about 2 minutes per arm.
- **Scenarios/sessions: keep the 10-scenario suite with its 2–3 sessions per scenario
  (26 turns, 10 probes).** A full arm at 5 seeds costs ~5 min GPU by the wall metric, so
  the suite fits the M6 hard cap (3 h GPU) with ~30x headroom even for all five arms,
  and the 3-session horizon in `contradiction_update` is what separates encoding from
  correction — shortening it would collapse the family's construct.
- **Do not add seeds to gain power; add scenarios if power is lacking.** With an
  arm-A floor of 0/7 on all memory-dependent probes, the binding constraint for
  CONT-001 is discrimination between arms B–E, not tighter bounds on arm A, and probe
  count scales linearly with scenarios at negligible GPU cost.
