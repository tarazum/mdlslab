# Continuity arc report — closing document (M8)

Arc: "from smoke to first ablation signal" — armed 2026-10-01 22:30 FLEDT, deadline
2026-10-02 11:30 FLEDT. This report closes the arc. All results are reproducible from
the committed artifacts under `results/`; every claim below carries a file pointer.

## 1. What was planned

Per `docs/ROADMAP.md`: complete P0b (fixture suite v2 + arm-A variance/headroom pilot +
sizing, M1), build arms B–E as MVPs (M2 SQLite memory, M3 validated self-model, M4
reflection/consolidation, M5 world model + bounded policy), with an owner-ordered M2b
CONT-002 mechanics smoke inserted mid-arc, then run a first **exploratory** CONT-001
multi-arm pass (M6), pre-register the confirmatory analysis before any confirmatory data
exists (committed in M6, independently reviewed in M6b), execute the confirmatory run
autonomously under the frozen protocol labeled "agent-pre-registered, pending owner
acceptance" (M7), and close with this report (M8). All owner decisions were consolidated
at arc end into the ROADMAP Owner morning list; no milestone waited on the owner.

## 2. What ran, milestone by milestone

Every milestone in the status table ran to DONE; none was SKIPPED or BLOCKED.

| Milestone | What ran | Result commit(s) |
| --- | --- | --- |
| M1 | Fixture suite v2 (10 scenarios, 4 families), arm-A pilot x 5 predeclared seeds {11,22,33,44,55}, `docs/SIZING.md` | `441fdfc` |
| M2 | Arm B: `src/continuity/memory.py` (SQLite store, keyword retrieval, portable export), runner arm flag, smoke + 3-seed mini-pilot | `79f2889` |
| M2b | CONT-002 mechanics smoke (owner-ordered): local GGUF import into Ollama, cross-core state export/import, 5 plumbing checks | `4098172` (insertion), `a38aabe` (result) |
| M3 | Arm C: `src/continuity/selfmodel.py` (versioned store, evidence-derived estimates, fail-closed commit), smoke + 3-seed mini-pilot | `1e2dee5` |
| M4 | Arm D: `src/continuity/reflection.py` (deterministic proposals + validator), smoke + 3-seed mini-pilot; reflection negative result recorded | `eb1cba7`, `95303fd` |
| M5 | Arm E: `src/continuity/worldmodel.py` + `src/continuity/policy.py`, smoke + 3-seed mini-pilot; CN-010 opened | `2e78931`, `7e1c58f` |
| M6 | Exploratory CONT-001: arms A–E x 5 seeds x 10 scenarios (650 requests); cross-arm table; pilot consistency 170/170; pre-registration v1 (`docs/EVALUATION-PREP.md`) committed before any held-out data | `29df09e` (run), `a845fc5` (pre-registration, frozen), `b804ba4` (result/DONE) |
| M6b | Independent pre-registration review, fresh session, zero inference | `d2dd004` (verdict GO) |
| M7 | Confirmatory CONT-001: held-out fixture v2 (14 scenarios) + disjoint calibration suite, pre-inference validator, freeze, arms A–E x fresh seeds {101,202,303,404,505} (1,125 requests), analysis exactly as frozen | `437294a`, `a7394b3`, `313b957` (FREEZE), `66eefc8` (attempt 1 rev), `c679547`, `4e425ea` (resume fixes), `c8a830f` (DONE) |
| M8 | This report, CN triage, consolidation retry, owner morning list, arc closure | `9d5a268` (IN_PROGRESS) + this commit |

Mid-arc owner/observer commits: `c8176c9` (CONT-005 Memory Trust Hierarchy next-cycle
proposal), `aa34b74` (morning-list pointer to it), `9591be1` (independent observer
notes). Arc infrastructure: `50de659` (roadmap), `11a853c` (owner amendment: all owner
work at arc end, deadline 11:30 FLEDT).

## 3. The numbers that matter

### 3.1 Exploratory CONT-001 cross-arm table (M6)

`results/CONT-001-exploratory/cont001-exploratory-20261002-000048/cross-arm-table.{md,json}`
— arms A–E x seeds {11,22,33,44,55}, 10 scenarios, mean pass rate per seed; cross-seed
spread 0.000 on every family and arm:

| family (probes/seed) | A | B | C | D | E |
| --- | --- | --- | --- | --- | --- |
| delayed_recall (3) | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| distractor_recall (2) | 0.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| contradiction_update (2) | 0.000 | 0.500 | 1.000 | 1.000 | 1.000 |
| repeated_task (3) | 0.667 | 0.333 | 0.333 | 0.333 | 0.333 |
| **overall (10)** | **0.200** | **0.700** | **0.800** | **0.800** | **0.800** |

EXPLORATORY only — input to the pre-registration, not a confirmatory result. Arm A's
repeated_task 0.667 includes the CN-004 option-leakage artifact (rt-0003 5/5), removed by
construction in fixture v2. Token cost per arm (5 seeds): A 12,385 / B 19,936 / C 71,140
/ D 85,696 / E 85,696 (E byte-identical to D — CN-010 inert actuation on v1 topology).

### 3.2 Confirmatory outcome (M7) — exactly as pre-registered

`results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711/results-summary.md`
(labeled agent-pre-registered, pending owner acceptance). Pre-registration frozen at
`a845fc5`, independent review GO (`docs/PR-REVIEW.md`). Held-out fixture v2, fresh seeds
{101,202,303,404,505}, strict repeated-mistake rate on per-arm eligible denominators:
A 0/20 = 0.000; B 0/20 = 0.000; C 0/30 = 0.000; D 15/30 = 0.500; E 10/30 = 0.3333.

- Primary contrast: **RM(E) − RM(A) = +0.3333 (harm direction), 95% CI [0.0, 0.75]**
  (paired cluster bootstrap over 7 scenarios, 10,000 resamples, RNG seed 20261002,
  18 redraws < 500 limit).
- Frozen decision rule requires BOTH (i) the two-sided 95% CI excludes 0 AND (ii)
  |point estimate| >= MME 0.15. Outcome: **"no confirmatory difference established"** —
  criterion (ii) passed (0.3333 >= 0.15), criterion (i) failed (the CI lower bound is
  exactly 0.0, so the CI does not exclude 0).
- Underpowered guard not triggered (eligible denominators 20/30 >= 10); 0 exclusions;
  frozen-content digests verified unchanged throughout.
- Sensitivities: loose RM = 1.000 for every arm (all eligible probes incorrect
  everywhere — free-form probes without option lists are hard for granite-code:8b);
  common-eligible E−A = +0.247, CI [0.0, 0.75] — same shape as the primary.

Reported plainly: the point estimate leans toward memory-arm harm (arm E repeats its own
initial wrong answers more than arm A), but the pre-registered uncertainty rule does not
certify it.

### 3.3 delayed_recall secondary — unambiguous memory benefit

With option leakage removed (fixture v2), arm A passes nothing suite-wide (0/14 probes)
while arms B–E pass all recall probes: **delayed_recall E−A = +1.000, 95% CI [1.0, 1.0]**
(secondary, exploratory-attribution; `secondary-analyses.json` in the confirmatory run).

### 3.4 D−C strict-RM observation (secondary)

Strict RM appears exactly at arm D and persists at E: **D−C = +0.5015, 95% CI
[0.1429, 0.8571]**; E−D = −0.169, CI [−0.7143, 0.4] (spans 0). The strict repeats at
D/E are verbatim copies of the agent's own earlier degenerate answers — the model parrots
its prior reply, and reflection summaries re-inject it (anchoring-by-parroting; CN-007
M7 disposition). Exploratory-attribution, not promotable to a claim.

### 3.5 M2b CONT-002 mechanics — all 5 checks pass

`results/CONT-000/cont002-mechanics-20261001-225738/checklist.json`: (1) local GGUF
import into Ollama (`qwen36-35b-a3b:mdlslab`, digest `8a0fd5da454e…d0c50c7`, no
download); (2) memory-export schema-valid round-trip, byte-equal re-export; (3) imported
state renders into core B's context (`memory.injected` event); (4) all three traces
re-validate from disk; (5) zero cross-core errors. Observations recorded WITHOUT claims:
held-out probe passed under B+imported state ("7"), failed under B+clean. No transfer
claims (plumbing proof only; single seed).

### 3.6 Arm-E policy actuation (CN-010 fix executed)

Fixture v2 places every RM-eligible probe on s2t2 behind a non-probe s2t1: **7 physical
policy injections per seed** (one per RM scenario, exactly matching the ex-ante
validator simulation), 13 retrieve actions/seed, expectation >= 1/seed met on every
seed; arm E no longer token-identical to arm D (278,805 vs 272,795 tokens/arm, +1,202
tokens/seed). Actuation measured; no policy-level behavioral claim (E−D RM CI spans 0).

## 4. Failures and negative results

1. **M4 null result.** Arm D's deterministic reflection/consolidation moved nothing:
   D−C = 0.000 on every family and every scenario in the mini-pilot. The conflict-review
   summary quoted the corrective sentence verbatim, juxtaposed the agent's own wrong
   answer, and declared the corrective record authoritative — rt-0003 still answered
   "bug" 3/3 (`results/CONT-000/pilot-armD-20261001-233203/`). Evidence juxtaposition
   alone did not break own-answer anchoring in granite-code:8b.
2. **Reflection-caused verbatim parroting (confirmatory).** The M7 secondary D−C
   +0.5015 CI [0.1429, 0.8571] shows strict repeated mistakes appearing exactly when
   reflection summaries enter the context: arm D/E repeat their own earlier degenerate
   answers verbatim. The mechanism built to cure anchoring (CN-007) is implicated in
   surfacing it on held-out data. Secondary, exploratory-attribution.
3. **Instrumentation crash, clean recovery (M7).** Attempt 1 (rev `66eefc8`) crashed in
   the executor's own post-inference instrumentation (`sum()` over an int telemetry
   counter) after arm C and arm D seed 101's inference completed; arms D(202–505)/E had
   issued zero evaluation requests. Recovery per the frozen §8 infrastructure clause:
   one-line fix + None-tolerant aggregation (`c679547`, `4e425ea`), arm D seed 101's
   summary rebuilt offline from its complete attempt-1 trace, zero inference requests
   repeated for any seed, both attempts recorded in `resume-manifest.json` and
   `freeze-verification-attempt1.json`; frozen-content digests verified unchanged.
   Fail-closed path worked as designed.
4. **CN-003 seed flip (escalated).** See the factual summary in §5.
5. **M6 primary-endpoint confound (design, not execution, failure).** The exploratory
   strict-RM contrast (A 0.500 vs B–E 1.000) was confounded by the CN-004 option-leakage
   artifact; recorded as such and removed by construction in fixture v2 rather than
   argued away.
6. **Two caught harness bugs, kept as evidence:** arm-D first smoke failed the gate with
   0 memory episodes (stale arm-set literal; the gate caught it — `eb1cba7` entry);
   `_marker_sentence` matched the first sentence of a corrective record instead of the
   marker sentence (pre-fix pilot kept as evidence, post-fix is the run of record).

## 5. CN case triage at arc end (`docs/FINDINGS.md`)

Closed: CN-001 (digest pinning via `/api/ps`), CN-004 (option leakage; closed by
fixture v2 + validator E8; arm A 5/5 -> 0/5 on the rt-0006 analogue), CN-006 (README
staleness), CN-009 (estimate/evaluation overlap; closed by the calibration-only
self-model 1' with mechanical provenance checks), CN-010 (empty actuation surface;
closed by fixture v2 topology, 7 physical injections/seed).

Open cases, each with its owner-relevant implication:

- **CN-002 — Ollama `total_duration` understates effective latency** (~265 ms reported
  vs ~2.3 s wall per request; root cause unidentified). Standing planning rule applied
  all arc: budgets by wall clock. Implication: budgeting-only; matters if this harness
  is reused for timing claims.
- **CN-003 — temp-0 seed drift, ESCALATED (M7).** Factual summary: in 350 confirmatory
  seed-scenario outcomes there was exactly ONE outcome-level seed flip — arm B,
  scenario rt-0008, seed 101 answered incorrectly while seeds 202/303/404/505 passed
  (seed 101 overall 7/14 vs 8/14). Visible in
  `results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711/repeated-mistake-analysis.{json,md}`
  per-seed rows. The pre-registered escalation clause ("any marginal probe flip caused
  by seed-only variation escalates this case") fired. What it means for determinism
  claims: temperature 0.0 + fixed seed does NOT fully determinize outcomes on this
  backend (Ollama 0.34.2 / granite-code:8b) — PB-071's caveat is confirmed at the
  outcome level, not just token level. The flip is OUTSIDE the primary endpoint (RM
  rows were seed-stable in every arm) and does not change the confirmatory verdict;
  single-probe margins of one seed are within temp-0 noise here. Any future
  seed-sensitive conclusion needs the multi-seed spread reported, as done throughout.
- **CN-005 — shared GPU idle threshold cannot attribute residency-only load.** Awaits
  an explicit owner decision on the shared tooling direction
  (`shared/tooling/agent-resource-coordination/`; morning list item 5). Every run this
  arc held the exclusive lock and recorded an attribution snapshot in its aggregate.
- **CN-007 — own-answer anchoring, OPEN with a full arc of evidence.** Not cured by
  self-knowledge (M3), evidence juxtaposition (M4), or bounded retrieval policy (M5);
  M7 surfaced its strict form as verbatim parroting at D/E with the D−C CI excluding 0
  (secondary). Mitigation via retrieval weighting/filtering is the owner-gated CONT-005
  proposal (`c8176c9`) — not implemented in this arc.
- **CN-008 — no supersession semantics in keyword memory, OPEN.** Owner-relevant
  observation: the confirmatory cu-0003 secondary (B 5/5 -> C/D/E 0/5, the superseded-
  value trap with the self-model block in context) suggests self-model interference on
  contradiction-update probes — small-n, an observation, not a closed question.

## 6. PENDING OWNER ACCEPTANCE

Everything below is owner work per the ROADMAP Owner morning list (`docs/ROADMAP.md`);
the chain stops here and waits.

1. **Read the arc record:** `docs/ARC-REPORT.md` (this file), `docs/SIZING.md`,
   `docs/PR-REVIEW.md`, and the confirmatory
   `results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711/results-summary.md`.
2. **Accept or reject the agent-pre-registered confirmatory result** — accept / re-run
   with amendments / discard. The result is "no confirmatory difference established"
   (E−A +0.3333, CI [0.0, 0.75]); acceptance is the owner's, per the labels on every M7
   artifact.
3. **Decide the CONT-002 program.** Mechanics are de-risked: all 5 M2b checks pass, the
   storage format (`continuity-memory-export` v1) is in place, and
   `qwen36-35b-a3b:mdlslab` remains imported in Ollama. No download is required — local
   core-B candidates are listed in ROADMAP item 3. Behavioral experiments (the R ratio)
   remain never-autonomous.
4. **External actions, publication decisions, any scope change to the roadmap.**
5. **CN-005 owner decision** on the shared GPU tooling direction
   (`shared/tooling/agent-resource-coordination/`).
6. **CONT-005 "Memory Trust Hierarchy" next-cycle proposal** (owner-added, `c8176c9`):
   scope, priority, and whether it becomes the next arc. The arc's CN-007 evidence
   (anchoring uncured by C/D/E mechanisms; strict form = verbatim parroting) is the
   strongest input for that decision.

## 7. What is explicitly NOT claimed

- **No transfer claims from M2b.** The mechanics smoke proved export/import plumbing
  only; the single-seed probe outcomes under core B are recorded as observations, not
  evidence. The R ratio and any CONT-002 conclusion are owner-gated.
- **No confirmatory claims from M6.** The exploratory pass and its table are input to
  the pre-registration, explicitly labeled exploratory.
- **No confirmatory memory-harm (or benefit) claim from M7 beyond the frozen wording.**
  The pre-registered verdict is "no confirmatory difference established." The
  harm-direction point estimate, the D−C parroting contrast, the delayed_recall +1.000,
  and every other M7 secondary are exploratory-attribution and not promotable.
- **No consciousness adjacency.** This lab studies behavioral continuity engineering;
  the README's purpose statement bars claims about consciousness or subjective
  experience, and nothing in this arc touches that boundary.
- **CONT-005 untouched.** The Memory Trust Hierarchy exists as a proposal document
  only; none of it was implemented or run.
- **Scope bounds of every number:** synthetic public-safe fixtures, one core model
  (granite-code:8b) at temperature 0.0, the v1/v2 suite families; no external-validity
  claims beyond that; PB-071/CN-003 determinism caveat travels with every number.

## 8. Housekeeping record (M8)

- Deferred Mnemosyne consolidation retried once (M8 instruction): `mnemosyne_sleep`
  with `all_sessions=true` completed cleanly — status `no_op`, "No old working memories
  to consolidate", 0 sessions scanned, 0 consolidated, 0 errors. Nothing was eligible;
  no timeout, no error, no further retry.
- Repo state at closure: all milestones DONE, arc marked COMPLETE in `docs/ROADMAP.md`,
  README statuses updated, final LOG.md entry written, everything committed and pushed.
