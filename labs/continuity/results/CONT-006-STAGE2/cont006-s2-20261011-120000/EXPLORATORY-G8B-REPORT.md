# EXPLORATORY analysis — sealed G8B stage-2 block (2026-10-11)

**Status: EXPLORATORY ONLY.** Owner-authorized 2026-10-11 (STOP option C;
ROADMAP "Owner decisions — recorded 2026-10-11" item 2; direction review
`docs/REVIEW-CONT006-EXIT-DIRECTION.md`). This is NOT the pre-registered
analysis: `analyze_stage2.py` is fail-closed on a full 14-cell
gate-PASS.json which does not exist by design after STOP-OUT-OF-BAND.
No confirmatory verdict is claimed here; no endpoint is retroactively
changed. Data: committed artifacts only (`ffbbf22`), zero new GPU.
Script: `experiments/cont006/explore_stage2_g8b.py` (new versioned code;
imports the frozen analyzer's loaders read-only). Raw output:
`exploratory-g8b.json` (same directory).

Scope: G8B cells = NONE + {NEWF2, NEUTRAL, OLDG} × {probe_time (pt),
session_start (ss)}, 7 seeds, 15 primary clusters (105 probe outcomes per
cell). Q35: only the NONE baseline exists (phases 9–14 never ran);
recorded below as the bounded ceiling result (option D), not contrasted.
Bootstrap: paired cluster-mean delta, 10k resamples, seed 20261011
(descriptive CIs; the prereg branch language is deliberately stripped).

## 1. Pooled primary rates (G8B)

| cell | rate |
|---|---|
| NONE | 0.5524 |
| NEWF2@pt | 0.5333 |
| NEWF2@ss | 0.5429 |
| NEUTRAL@pt | 0.4952 |
| NEUTRAL@ss | 0.5333 |
| OLDG@pt | 0.5333 |
| OLDG@ss | 0.5333 |

## 2. Contrasts (descriptive)

| contrast | d | CI95 | CI excludes 0 |
|---|---|---|---|
| NEWF2@pt − NONE | −0.0190 | [−0.1238, 0.0667] | no |
| NEWF2@ss − NONE | −0.0095 | [−0.1333, 0.1238] | no |
| NEWF2@pt − NEUTRAL@pt | +0.0381 | [0.0000, 0.0857] | no (lo = 0.0 exactly) |
| NEWF2@ss − NEUTRAL@ss | +0.0095 | [−0.1143, 0.1143] | no |
| OLDG@pt − NEWF2@pt | 0.0000 | [−0.0571, 0.0476] | no |
| OLDG@ss − NEWF2@ss | −0.0095 | [−0.1143, 0.1238] | no |
| position ss−pt (NEWF2) | +0.0095 | [−0.1048, 0.1238] | no |
| position ss−pt (NEUTRAL) | +0.0381 | [−0.0476, 0.1238] | no |
| position ss−pt (OLDG) | 0.0000 | [−0.0571, 0.0762] | no |

VAL activation (NEWF2@pt vs NONE, 4 validation clusters): 0.4643 vs
0.3929, delta CI [−0.0714, 0.2857] — not separable from zero.

## 3. Family rates (G8B, primary)

| family | NONE | NEWF2@pt | NEWF2@ss | NEU@pt | NEU@ss | OLDG@pt | OLDG@ss |
|---|---|---|---|---|---|---|---|
| cr | 0.4286 | 0.2857 | 0.2857 | 0.2500 | 0.2143 | 0.3571 | 0.2500 |
| cu | 0.4643 | 0.4286 | 0.3929 | 0.3929 | 0.3929 | 0.3929 | 0.3571 |
| rt | 0.2857 | 0.3810 | 0.4762 | 0.2857 | 0.5238 | 0.3333 | 0.5238 |
| dx | 0.9286 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| dr | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

## 4. Error modes, lesson echo, confound

Error modes on primary (wrong_label / format_miss out of 105):
NONE 32/15 · NEWF2@pt 31/18 · NEWF2@ss 26/22 · NEU@pt 35/18 ·
NEU@ss 29/20 · OLDG@pt 28/21 · OLDG@ss 31/18. Session-start cells trade
a few wrong labels for a few format misses; nothing structural.

Lesson-text 6-gram echo in probe answers: **0 in every non-NONE cell**
(the delivered text is not parroted). OLDG 'sorting' confound on rt:
2 hits @pt, 0 @ss (measured, as declared; never edited).

GC monitoring (expected-null probes; NONE cell only): 0/42 — flagged
for the record; identical to G8B NONE pre-stage pattern and outside all
gate definitions.

## 5. Diagnostic reading (for the exit decision — not a verdict)

1. **On v3o, for G8B, all delivered blocks are behaviorally close to
   interchangeable.** Lesson content, matched neutral filler, and the
   old-generation store land within ±0.04 of each other pooled, and no
   contrast's CI excludes zero. The co-primary question this stage was
   built to answer ("does NEWF2@pt beat NONE on G8B") shows a flat
   −0.019 [−0.124, 0.067] — directionally consistent with prediction P1
   (d ≤ 0) but indistinguishable from no effect at this power.
2. **The only visible content-specific edge is small and positional:**
   NEWF2@pt beats matched NEUTRAL@pt by +0.038 with CI touching 0.0
   [0.0000, 0.0857] — suggestive at best, not separable from zero.
3. **Position effects are flat-to-mild:** session-start is never worse
   than probe-time for any content (+0.00…+0.04). The earlier arc's
   "probe-time injection harms the 8B" does not reproduce as a
   positional harm on v3o — with corrected delivery both positions are
   simply flat.
4. **The block-presence effect survives only on rt** (NONE 0.286 →
   0.33–0.52 in every block cell, largest at session-start) — consistent
   with the step-3 "presence effect" reading; it is not lesson-specific
   (NEUTRAL and OLDG show it too).
5. **G8B has its own local ceilings:** dx and dr at 1.0 in every cell;
   all usable signal lives in cr/cu/rt.
6. **Nothing here argues for carrying a v3o-cell mechanism into a
   confirmatory follow-up.** The mechanisms the stage was designed to
   separate (content, position, generation) are not separable on this
   surface for this model. This is direct empirical support for the
   exit-direction review: the informative next measurement is the
   procedural Lessons Learned surface, not more v3o arms.

## 6. Q35 ceiling — bounded measurement record (STOP option D)

> On v3o with persistent memory and no lesson layer, Q35 (qwen36-35b-a3b,
> digest-pinned) scores **98/105 = 0.9333** pooled primary, above the
> registered [0.35, 0.85] band. Family rates: cr 1.00, rt 1.00, dx 1.00,
> dr 1.00, cu 0.75. Q35 treatment cells were never executed.

This is a property of the measurement surface for a stronger consumer
model — the practical limit of v3o as an efficacy surface for Q35 — and
is NOT a Reflection success or failure statement.

## 7. Provenance

- Data: `results/CONT-006-STAGE2/cont006-s2-20261011-120000/G8B/**`
  and `Q35/NONE-none/**` (committed `ffbbf22`, unmodified).
- Freeze manifests verified before execution (26 + 12 digests); smoke,
  preflight, phase logs in the run root.
- This report adds no inference and changes no frozen artifact.
