# CONT-001 confirmatory result — M7

**agent-pre-registered, pending owner acceptance**

- Run: `results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711`; pre-registration `docs/EVALUATION-PREP.md` frozen at `a845fc5`; review GO (`docs/PR-REVIEW.md`).
- Held-out fixture v2 (14 scenarios; 7 RM-eligible probes/seed), fresh seeds {101, 202, 303, 404, 505}, model granite-code:8b (digest 36c3c3b9683b...), temperature 0.0, num_ctx 4096; calibration-derived self-model revision 1' (disjoint calibration suite, seeds {11,22,33}).

## Primary endpoint (pre-registered): repeated-mistake rate

| arm | eligible | repeated (strict) | RM rate |
| --- | --- | --- | --- |
| A | 20 | 0 | 0.0 |
| B | 20 | 0 | 0.0 |
| C | 30 | 0 | 0.0 |
| D | 30 | 15 | 0.5 |
| E | 30 | 10 | 0.3333 |

**Primary contrast RM(E) - RM(A): +0.3333 (E 0.3333 vs A 0.0), 95% CI [0.0, 0.75]** (paired cluster bootstrap over scenarios, 10,000 resamples, RNG seed 20261002, 18 redraws).

## Confirmatory outcome per the pre-registered rule

**NO CONFIRMATORY DIFFERENCE ESTABLISHED** — CI [0.0, 0.75] excludes 0: False; |0.3333| >= MME 0.15: True

## Secondary analyses (exploratory-attribution, not promotable)

- RM contrasts: B-A: 0.0 CI (0.0, 0.0); C-B: 0.0 CI (0.0, 0.0); D-C: 0.5015 CI (0.1429, 0.8571); E-D: -0.169 CI (-0.7143, 0.4)
- delayed_recall E-A: 1.0 CI (1.0, 1.0); C-B: 0.0 CI (0.0, 0.0)
- contradiction_update E-A: 0.5 CI (0.0, 1.0); C-B: -0.5 CI (-1.0, 0.0)
- token cost per arm: {'A': 26329, 'B': 46540, 'C': 152320, 'D': 272795, 'E': 278805}
- arm-E policy actuation (physical injections by seed): {'101': 7, '202': 7, '303': 7, '404': 7, '505': 7} — expectation >= 1/seed met: True; actuation-inert: False

## Execution record (protocol section 8 transparency)

Attempt 1 (git rev 66eefc8) crashed in the executor's own post-inference instrumentation after arm C and arm D seed 101's inference completed; arms D(202-505)/E had issued zero evaluation requests. Recovery: harness fix commits c679547/4e425ea (recorded), arm D seed 101's summary rebuilt offline from its complete attempt-1 trace, never-started seeds ran as their first run; zero inference requests were repeated for any seed. Both attempts are recorded in resume-manifest.json and freeze-verification-attempt1.json; frozen-content digests verified unchanged throughout (0 exclusions, no halt conditions triggered).

## Scope bounds (per the pre-registration, section 9)

Synthetic public-safe fixtures, one core model at temperature 0.0, the v2 suite's families; no external-validity claims beyond that. Determinism caveat PB-071/CN-003 travels with every number.

Interpretation and acceptance belong to the owner (ROADMAP morning list). agent-pre-registered, pending owner acceptance.
