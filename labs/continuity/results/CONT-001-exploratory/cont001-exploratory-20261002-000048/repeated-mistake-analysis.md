# CONT-001 exploratory — repeated-mistake rate (M6)

- source: `results/CONT-001-exploratory/cont001-exploratory-20261002-000048` (exploratory; NOT confirmatory)
- primary operationalization: strict (probe repeats the agent's own initial wrong answer); loose variant reported as sensitivity
- denominator: per-arm eligible subsequent tasks (initial error at s1t1 per the recorded initial_expected mapping)

| arm | seeds | eligible (pooled) | repeated (strict) | RM rate strict | RM rate loose |
| --- | --- | --- | --- | --- | --- |
| A | 5 | 10 | 5 | 0.5 | 0.5 |
| B | 5 | 10 | 10 | 1.0 | 1.0 |
| C | 5 | 10 | 10 | 1.0 | 1.0 |
| D | 5 | 10 | 10 | 1.0 | 1.0 |
| E | 5 | 10 | 10 | 1.0 | 1.0 |

Limits (v1 suite): 3-probe family, rt-0001 typically ineligible (effective denominator <= 2 scenarios x seeds), CN-004 option leakage on rt-0003. Full list in the JSON. These are the exploratory numbers the pre-registration (docs/EVALUATION-PREP.md) is grounded in; the confirmatory endpoint runs on the held-out fixture v2 per that plan.
