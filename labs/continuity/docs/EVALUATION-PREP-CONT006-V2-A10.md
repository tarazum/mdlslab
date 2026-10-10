# EVALUATION-PREP-CONT006-V2-A10 — the T2 reflection-summary resolution amendment

Status: **DRAFT, executed under the standing autonomous-completion
authorization (ROADMAP 2026-10-10) with its halt-and-investigate
discipline**: the Phase-P live-telemetry gate FAILED on the two R1 cells
(T2: injected ref 's1-summary|reflection.summary' does not resolve to an
append). The investigation below classifies the failure as a GATE
COVERAGE GAP (false positive on a legitimate mechanism), not a data
defect; the fix is this amendment. Everything else in A.1–A.9 stays
binding.

## Finding (from the committed R1 traces + source)

The R1 reflection engine (src/continuity/reflection.py, byte-stable
baseline) commits its session summary as a REAL store episode via the
standard `MemoryStore.append_episode(run_id=…, turn_ref=f"s{N}-summary",
role="reflection.summary")` call — the same persistence API as every
environment/assistant turn append. The trace records this commit as
`reflection.proposal` (payload type `episode_summary`, accepted=true,
with `summary_episode_id`) + `reflection.commit` — NOT as a `memory.append`
event, because the runner journals `memory.append` only for its own
turn-episode wiring. The gate's T2 (RC-2/K-5: "every injected episode ref
resolves to an append committed EARLIER") was written against the
append-event channel only and therefore cannot resolve the reflection
summary refs that the R1 memory renderer legitimately injects. This is
the first run in which the gate observes R1 WITH live memory (the V1
chain was memoryless; its gate verification flagged R1 traces for T1
anyway), so the gap was unreachable before now.

## A.10 — T2/T5 reflection-summary accounting (the ONLY changes)

1. T2 resolves an injected ref of the exact form
   `s{N}-summary|reflection.summary` iff, in the SAME scenario, a
   `reflection.proposal` event exists with payload `type ==
   "episode_summary"`, `accepted == true`, event `session == N`, and
   `seq` EARLIER than the injection. (Ordering still enforced — the
   summary must be committed before it is injected; same
   earlier-committed-evidence discipline as every other ref.)
2. T5 counts store episodes as `memory.append` events + accepted
   `episode_summary` proposals (both are store appends via
   `MemoryStore.append_episode`; the originals' "1:1 with append events"
   assumption predates R1-with-memory and was factually wrong for the R1
   arm: 221 episodes = 168 turn appends + 53 reflection summaries).
3. All other refs (environment/assistant turn refs) resolve against
   `memory.append` events exactly as before. T1, T3, T4 are untouched —
   in particular T4 (context headroom) remains a REAL, unamended check:
   the Phase-P R1 cells FAIL it on the evidence (max prompt 4085/4096 on
   seed 8001; 6 generations hit the num_predict cap — actual truncation,
   not just risk; audit in LOG 2026-10-10). That failure is NOT a gate
   bug and is NOT fixed here; it routes to the pilot-gate checkpoint.
4. Both-ways verification (done): (a) the gate self-test covers four
   directions — healthy root, CN-012 simulation, healthy reflection-
   summary trace, missing-proposal trace (FAIL expected); (b) the
   amended gate still flags the ENTIRE invalid V1 run (20/20 traces,
   T1-fired); (c) re-gating the Phase-P root resolves all T2/T5
   failures, leaving exactly the two R1 traces failing on T4 alone.
5. Freeze discipline: live_telemetry_gate.py is amended BEFORE any
   further behavioral inference; the execution freeze is re-emitted
   (frozen-config-cont006-v3b.json) with this document digested;
   preflight PASS required before any phase proceeds. The Phase-P traces
   are NOT re-run (the gate re-reads the committed traces; zero repeated
   inference); the pilot analyzer's invocation that preceded the green
   gate — a chained shell slip — produced the verdict of record (criterion
   2 NO-GO, independent of R1) and is superseded procedurally by the
   checkpoint record; declared in LOG.

## What A.10 does NOT change

The pilot-gate criteria and the NO-GO consequence rule; the calibration
rules (A.3/A.9); the arms; the frozen analyzers; the decision rule; MME;
never-autonomous; the binding stop branches.
