# Diagnostic — the cr collapse at calibration (CONT-006 V2, 2026-10-10)

Owner decision #2 (ROADMAP "Owner decisions — recorded 2026-10-10"): a
zero-GPU read of the calibration traces explaining WHY the R2 lesson store
tanks correction_reuse (cr R0 0.25 → R2 0.0; invalid-format 0.105 → 0.211
concentrated on cr). Input to the v3n suite authoring (decision #1).

## Mechanism (verified from trace data, not interpretation)

At every cr probe turn the R2 arm retrieves and injects LL-W-005 + LL-W-002
+ LL-W-003 (the two FP-3a lessons + the FP-3b verification lesson; retrieval
is keyed on the turn text and cr probes match their correction-flavored
applicability conditions). Every accepted worker lesson is a variant of:

> "Output ONLY the [corrected/explicitly-stated] label from the current
> instruction. Do not re-evaluate or justify. Ignore context/distractors."

The cr probe requires the OPPOSITE cognitive act: a NOVEL report
("the pantograph round for the dusk trams") must be mapped to one of six
card categories where the card itself lives in EARLIER SESSIONS (episodic
memory), and the correct label is NOWHERE stated in the probe turn. The
lessons prescribe "resolve strictly from the explicit instruction; do not
infer from context" — which suppresses exactly the memory-based semantic
inference the probe tests. The model's observable failure modes:

- **Deflection**: replies `'Acknowledged.\n'` — no label (cr-7001/7002 R2).
- **Prompt-echo degeneration**: replies by repeating the probe question
  verbatim, twice (cr-7004/7005 seed 7001, cr-7001 seed 7002) — a
  granite-8b loop under instruction conflict.
- Same cells in R0 (no lessons) produce ordinary wrong-label prose answers
  ("The pantograph round … is a trackwork issue") — broken semantics but
  intact format; R0's cr misses are semantic, R2's are format collapses.

Contrast: on cu probes the answer IS a corrected value stated in a prior
turn — aligned with what the lessons prescribe — and R2 cu stays at R0's
level (0.5). dx/dr are at ceiling regardless (1.0 both arms).

## Two independent conclusions

1. **v3m difficulty defect (the STOP cause, suite-side)**: the family
   profile is bimodal — dx/dr trivially solvable by memory lookup of a
   stated value (1.0, no headroom), cr too hard for the granite baseline
   (R0 0.25: hold a 6-category card across sessions and map novel
   paraphrases onto it). The per-family gate caught exactly this.
   v3n direction: cr easier (report→category mapping lexically more
   transparent; competing categories share no vocabulary with the report),
   dx/dr harder (dx: lure stated later/more often than the expected —
   salience competition; dr: same-type values of OTHER entities stated
   between target and probe — interference), cu/rt unchanged mechanics.

2. **Corpus-coverage bias of worker lessons (store-side, carried as a
   declared caveat — NOT a code change)**: the experience corpus (CONT-005-
   C2 traces) contains only tasks whose correct answer is stated or
   corrected in some turn; the worker therefore generalizes
   "answer what the instruction states" and cannot emit transfer-supporting
   lessons. On probes that test beyond-corpus inference (cr), those
   prescriptions are anti-transfer. Consequence for the rerun design: the
   R2-vs-R0 contrast on v3n measures transfer of CORPUS-SHAPED lessons —
   a fair test of the registered hypothesis (the store is whatever the
   worker honestly learned), but the run record must carry this reading
   note; and cr clusters must be solvable at baseline so the lessons'
   suppressive pull is measurable rather than floor-masked.

## Evidence pointers

- Traces: results/CONT-006-CAL/cont006-cal-20261010-000940/{R0,R2}/seed-{7001,7002}/trace.jsonl
- Verdict: results/CONT-006-CAL/cont006-cal-20261010-000940/calibration-verdict.json
- Store: results/CONT-006-WORKER/cont006-worker-v2-20261010-000332/r2-store-v2.json (5 lessons, classes FP-3a×2/FP-3b×2/FP-1×1)
