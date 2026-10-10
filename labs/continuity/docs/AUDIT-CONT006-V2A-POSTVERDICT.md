# Post-verdict audit — why the registered negative clashes with the owner's 2-year lesson experience

Origin: the owner REJECTS provisional acceptance (chat, 2026-10-10):
"не приймаю поки акцепт. пошукай сам проблеми, чому так сталося. бо ти сам
використовуєш вивчені уроки, пишеш їх і бачиш що вони працюють. і весь мій
2 річний досвід, де я юзаю вивчені уроки говорить про інше. може справа в
 тому що малі і локальні моделі, які не можуть адекватно сприймати уроки."

The registered numbers STAND (frozen analyzer, single-freeze dataset;
nothing here re-litigates them). This audit asks what the run actually
measured, where the construct breaks, and what would reconcile it with
the working reality of agent lessons. Independent review: GPT-6 Astra
(docs/REVIEW-ASTRA-CONT006-V2A.md; Fable/Opus were session-limit-blocked;
codex CLI updated 0.148.0 -> 0.162.1 to enable gpt-6-astra).

## A. What the run measured vs what "lessons" means for the owner

| dimension | this experiment | owner's working lessons (mine too) |
|---|---|---|
| author | mined by a 35B reflector from an 8B's own failure corpus (+ one blind human store) | written/curated during real work by frontier-class agents + human |
| content | blunt output prescriptions ("Always treat the latest explicit correction as ground truth… Output ONLY the corrected label") | mechanism-level, host/tool-specific ("heredocs silently truncate on this host → write a temp .py via Write and run it") |
| scope | always-on applicability; injected at essentially every turn (retrieval top-3 keyed on turn text) | narrowly condition-scoped; retrieved when the condition fires |
| consumer | granite-code:8b (4.6 GB, local) | frontier models (GPT-6/Claude class) |
| task | psychometric probes under adversarial distractors; scoring = exact label match | workflow decisions (how to work), graded by outcome |
| corpus coverage | the mined SELECTION lost the evidence (see correction below): the source corpus DOES contain inference tasks (Astra counterexample: v3j rt-4201 card->novel probe), but the bundle digest strips source types, corrections and card texts, leaving fragments + answer keys; 97/108 selected runs came from the NO-MEMORY arm | lessons accumulate across the actual work distribution |

The registered claim is about THIS row-left construct. Read literally,
"lessons do not improve transfer" IS what was tested and found; read as
a claim about lesson-memory as the owner uses it, the experiment never
touched it. The owner's rejection is justified at the construct level.

## B. The mechanism, decomposed from the data (all pulls verified)

1. **The channel works on the 8B.** V1's (invalid, memoryless) run:
   worker lessons erased format-miss 0.162 → 0.0095. This run: VAL
   activation +0.214; rt-8204 0.143 → 0.857 (R2 and R3 alike); RGOLD
   changed behavior strongly (in the wrong direction). A model that
   "cannot perceive lessons" could not produce these.
2. **The one big win and the harm are THE SAME PUSH.** At rt-8204, R0's
   failure mode is deflection — it answers 'Acknowledged.' at the probe
   (verified in trace) — while R2/R3, pushed by the lessons to answer
   decisively from the standing card, reply 'Collection.' and pass. On
   cr-8003/8004 and dx-8401/8402 the same push lands on a conflict: the
   lesson says "output the explicitly-stated/corrected value, do not
   infer", the probe demands inference from memory — and the 8B
   degenerates (5 of R2's 6 harm-cluster errors are format-misses:
   'Acknowledged.' or whole-list echoes; R0 on the same clusters: 3
   wrong-label, ZERO format-miss). Lessons shift the model's operating
   point from "hesitant inference" to "decisive literalism"; that helps
   where literalism is the answer, hurts where it is the trap.
3. **Where the help and harm landed (per-cluster deltas vs R0, 7 seeds):**
   R2: cr-8001 +0.143, rt-8203 +0.143, rt-8204(VAL) +0.714 — versus
   cr-8004 −0.286, cu-8104 −0.286, dx-8402 −0.286, cr-8003/dx-8401/
   cr-8002 −0.143. R3 (human gold, the most prescriptive store) hurts
   most and significantly: cr-8003 −0.429, dx-8401 −0.429, pooled
   −0.105 CI excluding 0 down. Harm concentrates exactly on the
   instruction-vs-memory classes (FP-3b/FP-4) — the corpus-coverage
   prediction from DIAGNOSTIC-CONT006-V2-CR, confirmed at scale.
4. **Model capacity IS implicated — in the failure MODE, not the
   channel.** The 8B degenerates under instruction stacking (echo/
   acknowledge; R1 overflowed its 4096 context outright). A frontier
   model given "output only X" + "infer from memory" resolves the
   conflict; granite-8b collapses. So: strong models can hold both
   constraints and apply lessons conditionally — the owner's experience;
   the 8B cannot — this run.

## B2. Independent review findings folded (docs/REVIEW-ASTRA-CONT006-V2A.md)

GPT-6 Astra (codex CLI; Fable/Opus limit-blocked) reproduced both CIs,
rescored 473 responses with zero discrepancies, and found delivery-side
defects beyond this audit: (1) retrieval is lexical token-overlap keyed
on the SESSION'S FIRST TURN (an acknowledge request), never refreshed at
the probe — both lesson arms received lessons at ALL 105 probes, i.e.
zero conditional application; (2) the renderer omits the lesson FIELD
itself (title+applicability+behavior only) and its 165-word greedy
budget dropped the retrieved-and-relevant G005 at exactly the harm
clusters (cr-8003/8004); (3) the full LINEN_CARD constant is never used
— rt-8203 AND the main activation driver rt-8204 expect categories whose
rules are never supplied (partly-underspecified probes); (4) the
aggregate negative is predominantly wrong-label (29->35->38), not format;
(5) fresh-seeds-only sensitivity: R2 delta -0.053, R3 delta -0.133 — the
negative is not a reused-pilot artifact; (6) the A.9 "power ~0.79-0.80 at
K11" figure was bracketed from the K12 row, not computed — flagged as
overstated. Curation appendix in the review doc (one Astra sub-claim
refuted: G001/G002 ARE injected at cu probes).

## C. The honest reading of the registered verdict

Corrected reading (post-Astra): on this surface (one 4.6 GB model, one
synthetic suite with two underspecified rt probes, lessons mined from
evidence-stripped fragments of a 90%-no-memory sample, delivered by
lexical first-turn retrieval that never checks conditions and a renderer
that drops the field carrying the rule): the executed lesson pipeline
did not improve novel-task transfer, and the gold pipeline significantly
harmed it. The numbers are real FOR THIS IMPLEMENTATION. What is NOT
established: that lessons generally fail; that properly-delivered
conditional lessons fail; that small-model capacity is the cause. The
owner's rejection of broad acceptance is justified. Three design levers
the next iteration must move: FAITHFUL mining evidence, CONDITIONAL
delivery (route at the probe, check applicability, render the rule
field), and lesson QUALITY (mechanism-level, narrowly scoped).

## D. What would discriminate (proposals to the owner; Astra's list folds in when its review lands)

Adopted from the Astra ranking (cost/information), amended with the
capacity-ladder idea:

1. **Corrected DELIVERY on the existing 8B** (cheapest, tests the
   strongest demonstrated defect): same gold wording, independent
   applicability annotation, deliver ONLY the relevant lesson AT THE
   PROBE, no budget dropping; probe-level diagnostic on recorded memory
   inputs + end-to-end check. If this works, weak model capacity is not
   needed to explain the original failure.
2. **Faithful worker evidence + fixed fixtures**: complete evidence in
   the bundles (cards, corrections, source identity, novel query),
   balanced memory-condition sampling; repair the rt mappings in a NEW
   named suite (the executed run stays as-is, never retrofitted).
3. **Capacity x content comparison** (the owner's small-model
   hypothesis, properly isolated): 8B vs a stronger local
   instruction-follower, memory-only vs original-worker vs curated
   conditional lessons, fixed routing; measure the lesson-minus-baseline
   INTERACTION per model, not the baseline.
4. **Stage B / the owner's actual construct** (deferred, owner-gated):
   curated workflow lessons, applicable/inapplicable task pairs,
   frontier consumer, objective task outcomes.

Recommended order: 1 -> 2 -> 3, then 4 when external access opens.
