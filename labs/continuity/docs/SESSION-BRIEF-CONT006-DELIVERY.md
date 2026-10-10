# Session brief — CONT-006 DELIVERY: the corrected-lesson-delivery experiment (Astra/audit follow-up, step 1)

For the NEXT working session (fresh context). This brief + the repo are the
complete state carrier. House process: labs/continuity/PROCESS.md. Context
docs (read in this order): docs/AUDIT-CONT006-V2A-POSTVERDICT.md →
docs/REVIEW-ASTRA-CONT006-V2A.md (incl. the curation appendix) →
LOG.md 2026-10-10 (all three entries).

## Where things stand (do not re-litigate)

- The V2A confirmatory verdict is COMMITTED and stands as the record of
  the executed pipeline: primary "no confirmatory difference established"
  (Δ = −0.067, CI [−0.133, 0.000]); R3−R0 = −0.105, CI excludes 0 down.
  The owner REJECTED broad acceptance; the warranted conclusion (audit +
  GPT-6 Astra review concur): failure of THIS lesson generation + delivery
  implementation — NOT "lessons don't transfer", NOT "small models can't
  absorb lessons" (the channel demonstrably moves the 8B: V1 format
  0.162→0.0095; rt-8204 +0.71; RGOLD behavior flip).
- FIVE pipeline defects are documented and verified (audit doc §B2):
  (1) worker bundles lost all source-marked evidence (0 lines across 9
  bundles); (2) 97/108 mined runs from the no-memory arm A; (3) lesson
  retrieval is lexical, keyed on the session's FIRST turn, never
  refreshed at the probe — lessons at ALL 105 probes, zero conditional
  application; (4) the renderer omits the lesson FIELD and its greedy
  budget dropped the relevant G005 at the harm clusters cr-8003/8004;
  (5) rt-8203/rt-8204 (the main activation driver) are underspecified —
  the full LINEN_CARD constant is defined in build_v3n.py but never used.
- Owner decisions so far: all recorded in ROADMAP 2026-10-10 (A.8–A.11 +
  the rejection of provisional acceptance). The NEXT experiment was
  proposed and implicitly awaited the owner's word ("крок 1"); if the
  owner's kickoff says to run this brief, that is the authorization.

## Scope (ONE milestone: step 1 — corrected DELIVERY, same 8B model)

Goal: test whether the demonstrated delivery defects (not model capacity,
not lesson content) explain the negative result. Cheapest, highest
information (Astra ranking #1). Design discipline: pre-register BEFORE
any new inference (template §1); freeze manifest before the GPU part.

1. **Zero-GPU probe-level diagnostic (do FIRST)**: replay-from-traces —
   for a diagnostic subset of recorded probes (suggest: all cr-8003/8004,
   dx-8401/8402, rt-8203/8204 probes across seeds = the harm + driver
   clusters), reconstruct the EXACT memory inputs the agent saw (from the
   committed traces), and compare three prompt variants head-to-head:
   (a) as-executed (lessons as delivered — the baseline, already scored);
   (b) corrected delivery: route AT the probe (query = the probe turn
   text), strict applicability (independently annotated conditions per
   lesson; deliver ONLY matching lessons; if none match, deliver NONE),
   render the FULL lesson (title + when + RULE field + behavior), no
   budget drops;
   (c) memory-only (no lessons — the R0 equivalent prompt).
   This needs new inference (same model, same sampling pins) but zero new
   scenarios — a small GPU budget (~100–200 probes × 1 call).
2. **Pre-registered predictions** (write them BEFORE running): primary —
   corrected delivery ≥ as-executed on the harm clusters; secondary —
   corrected delivery does not lose the rt-8204-style gains; if corrected
   delivery ALSO underperforms memory-only, the capacity/content
   hypotheses gain (step 3 of the ranking becomes next).
3. **Fix class**: implement the corrected delivery as a SEPARATE,
   clearly-named mechanism (e.g. a delivery-v2 function in a new module
   or behind a flag); do NOT modify the executed chain's frozen files
   (the run record stays untouched). New freeze manifest for the
   diagnostic (digest the new code + this brief).
4. **Out of scope (non-goals)**: re-running the confirmatory; worker
   re-mining (step 2); fixture repair/new suite (step 2); capacity
   comparison (step 3); Stage B (step 4); ANY change to the registered
   verdict or the committed run artifacts.
5. **Review**: Fable if its limit has reset (2:30am Kyiv; check first) —
   else GPT-6 Astra via codex (CLI already updated to 0.162.1; invoke:
   `codex exec -m gpt-6-astra -c model_reasoning_effort='"high"' --sandbox
   read-only - < prompt.md`; note: gpt-6.1-sol is NOT account-supported).
   Diff-pass on the diagnostic design + results; fold; then owner gate.
6. **Close-out**: results doc + plain-language owner brief (the
   "підтвердилось/ні" first), LOG, safety scan, push. If corrected
   delivery WINS, the next brief is step 2 (faithful evidence + fixed
   fixtures in a new suite).

## Entry conditions (verify before any work)

- git clean on main at HEAD ≥ 93ec6c2; ROADMAP 2026-10-10 entries intact.
- Ollama 0.34.x up; granite-code:8b (36c3c3b9683b) present.
- The committed artifacts referenced above exist (audit doc, Astra
  review, run roots cont006-v-20261010-130154 / -p-20261010-132230 /
  -c-20261010-144817).
- The owner's kickoff word for THIS milestone (never-autonomous).

## Kickoff (paste into the fresh session)

"Прочитай labs/continuity/docs/SESSION-BRIEF-CONT006-DELIVERY.md і виконай
milestone згідно бріфа. Перевір entry-умови до будь-яких дій."
