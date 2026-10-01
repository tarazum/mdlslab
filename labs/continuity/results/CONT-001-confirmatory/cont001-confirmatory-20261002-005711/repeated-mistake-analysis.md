# CONT-001 confirmatory — repeated-mistake rate (primary endpoint, M7)

**agent-pre-registered, pending owner acceptance**

- source: `results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711` (held-out fixture v2)
- primary operationalization: strict (probe repeats the agent's own initial wrong answer, both at s1t1 / probe normalized); denominator: per-arm eligible subsequent tasks (initial error vs the fixture's initial_expected)
- primary contrast: RM(E) - RM(A), two-sided; MME 0.15; decision rule: 95% paired cluster bootstrap CI excludes 0 AND |delta| >= MME

| arm | seeds | eligible (pooled) | repeated (strict) | RM rate strict | RM rate loose |
| --- | --- | --- | --- | --- | --- |
| A | 5 | 20 | 0 | 0.0 | 1.0 |
| B | 5 | 20 | 0 | 0.0 | 1.0 |
| C | 5 | 30 | 0 | 0.0 | 1.0 |
| D | 5 | 30 | 15 | 0.5 | 1.0 |
| E | 5 | 30 | 10 | 0.3333 | 1.0 |

**Primary contrast RM(E) - RM(A): point 0.3333, 95% CI [0.0, 0.75] (paired cluster bootstrap over scenarios, 10,000 resamples, RNG seed 20261002, 18 redraws).**

**Decision rule verdict: NO CONFIRMATORY DIFFERENCE ESTABLISHED** (CI [0.0, 0.75] excludes 0: False; |0.3333| >= MME 0.15: True)
