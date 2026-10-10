You are GPT-6 Astra, engaged as an INDEPENDENT reviewer for the Continuity lab (mdlslab repo; your cwd is the repo root — verify every load-bearing claim against the files; read-only review, do not edit anything).

# Context

The CONT-006 arc just completed a fully pre-registered confirmatory run and produced a NEGATIVE result. The OWNER (a researcher with 2 years of daily experience using agent-learned lessons — curated memory files that agents write and reuse across sessions — where they clearly WORK, including for the coding agents he uses daily) REJECTS provisional acceptance and challenges the result:

> "не приймаю поки акцепт. пошукай сам проблеми, чому так сталося. бо ти сам використовуєш вивчені уроки, пишеш їх і бачиш що вони працюють. і весь мій 2 річний досвід, де я юзаю вивчені уроки говорить про інше. може справа в тому що малі і локальні моделі, які не можуть адекватно сприймати уроки. треба вдоль і впоперек пройтися по експерименту, викликати незалежних агентів."

Your job: independently audit whether the experiment's negative result is (a) an artifact of experimental design/construct mismatch, (b) genuinely about "lessons" as a mechanism, (c) about model capacity, or a mix — and say what would discriminate.

# The registered result (verify from artifacts)

- Verdict artifact: labs/continuity/results/CONT-006-CONFIRMATORY/cont006-c-20261010-144817/results-summary-cont006.json
- Primary: delta = S(R2)-S(R0) = -0.0667, 95% CI [-0.1333, 0.0000], MME 0.20 -> "no confirmatory difference established" (15 TR clusters x 7 seeds; R2 = agent memory + worker-mined lessons through a lesson channel; R0 = memory only).
- Secondary: R3-R0 (blind human-authored "gold" lessons) = -0.1048, CI [-0.1905, -0.0286] — excludes 0 downward (significant HARM).
- Working core: granite-code:8b (a 4.6GB local model). Reflector: qwen36-35b-a3b (local MoE).
- Chain of the night (all pre-registered, all committed): suite v3n authored after a first calibration STOP (dx/dr ceiling); amendments A.8-A.11 (owner-accepted); both lesson stores ACTIVATED on validation clusters (+0.2143 each); pilot NO-GO overridden by owner (RGOLD phenomenon: a trivially-benign format lesson DEGRADED format 0.143->0.357 via list-echoing); Phase C 15/15 cells, live-telemetry gate PASS.

# The implementer's own audit (verify these numbers yourself; they are pulls, not registered claims)

From labs/continuity results (Phase V root cont006-v-20261010-130154; Phase P root cont006-p-20261010-132230; Phase C root cont006-c-20261010-144817):

1. The +0.214 activation is almost entirely rt-8204 (R0 0.143 -> R2 0.857) + cu-8105 (0.857 -> 1.0); cr-8005 = 0.0 for ALL arms; dx-8403 = 1.0 flat. I.e., where a probe's answer is derivable from the explicit instruction, lessons help enormously.
2. On the harm classes (cr-8003/8004 = FP-3b, dx-8401/8402 = FP-4): R0 errors = 3 wrong-label, ZERO format-miss; R2 = 4 wrong-label + 5 FORMAT-MISS (the degeneration signature: the model replies 'Acknowledged.' or echoes the whole option list — see the CAL diagnostic labs/continuity/docs/DIAGNOSTIC-CONT006-V2-CR.md).
3. The 5 worker lessons (labs/continuity/results/CONT-006-WORKER/cont006-worker-v2-20261010-000332/r2-store-v2.json) are all blunt output prescriptions ("Always treat the latest explicit correction as ground truth... Output ONLY the corrected label") mined from a corpus (CONT-005-C2 traces of the same 8B model) that contains NO transfer-inference tasks — a corpus-coverage bias.
4. In-run evidence the 8B DOES follow injected lessons: V1's invalidated run showed lessons erasing format-miss (0.162 -> 0.0095); RGOLD changed behavior strongly (wrong direction); rt-8204 +0.714. The channel moves the model; what fails is CONDITIONAL application on inference-demanding probes.

# Your tasks (numbered; answer each with evidence)

1. VERIFY the registered numbers and the audit pulls from the artifacts (results-summary JSONs; per-cluster tables you compute yourself from the summary.json files under the three run roots).
2. CONSTRUCT VALIDITY: the owner's working lessons are mechanism-level, narrowly condition-scoped, curated, and consumed by frontier-class models in workflow tasks. The experiment's lessons are output-prescriptions mined from an 8B's own failure corpus and injected at psychometric probes. Is the registered claim "lessons do not improve transfer" overbroad relative to what was tested? Where exactly does the construct break?
3. MODEL CAPACITY: evaluate the owner's small-model hypothesis against the in-run evidence (item 4 above + the RGOLD list-echo + R1 context overflow 4085/4096). What specific signature would distinguish "8B can't absorb lessons conditionally" from "lessons of this generation are anti-transfer by content"?
4. ARTIFACT HUNT: look for experimental artifacts the implementer may have missed — scoring (exact_match), lesson retrieval/applicability matching (does it inject at every probe?), the activation surface (4 VAL clusters only), the A.9 dx/dr ceiling exemption (4/15 clusters unmeasurable for improvement), single-suite/single-model scope, anything else.
5. DISCRIMINATING EXPERIMENTS: propose the minimal set that would settle the owner's challenge (e.g., capacity ladder on the same frozen suite with a stronger local model; a hand-curated "lessons-that-work" arm in the owner's style; applicability-gated injection; Stage B hosted replication). Rank by cost/information.
6. VERDICT: one paragraph — what does this run actually establish, what does it NOT, and is the owner's rejection justified?

Output: plain text, sections per task, verdict at the end. Be ruthless and specific; cite file paths and numbers you verified.
