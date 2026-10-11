# Session brief — CONT-006 PLT authoring half (phases A1–A5 + freeze prep)

For the NEXT working session (fresh context). This brief carries the
PLT (Procedural Lessons Transfer) authoring work. The design, prereg,
and both reviews are FROZEN INPUTS — read them, do not re-litigate.

Context docs to read, in order:
1. `docs/PREREG-CONT006-PLT.md` (the binding operational document —
   every pin in §1–§8 is executable specification)
2. `docs/DESIGN-CONT006-PLT.md` rev 2 (direction + rationale)
3. `docs/REVIEW-OPUS-CONT006-PLT.md` + `docs/REVIEW-OPUS-CONT006-PLT-PREREG.md`
   (both reviews; all findings folded — verify any doubt against these)
4. `experiments/cont006/power-results-plt.json` (MME + decision rule)
5. `docs/ROADMAP.md` — "Owner decisions — recorded 2026-10-11" + the
   accept record (owner «ок» 2026-10-11)
6. `LOG.md` — 2026-10-11 entries (STOP-OUT-OF-BAND → exit direction →
   exploratory G8B → PLT design/review/prereg)

## Scope of THIS session (zero GPU, authoring only)

Phases per prereg §4, in the binding order:

- **A1** sandbox harness (bounded file/command sandbox, journaled
  actions, per-episode invariants fail-closed) + experience simulator +
  experience histories: **≥3 per class, 15+ total** (failure derivable
  from the journal, never named; auto-lint bans class-name lexicon and
  imperative rule forms; human spot-check ≥3/class recorded in an
  artifact).
- **A2** deterministic checkers FC-1..FC-5 (journal-equality semantics
  per design §3) + dev validation: ≥20 labeled traces/class, labeler-1
  = implementer, labeler-2 = fresh non-executor agent, 100% agreement
  on class-defining events (or ≥0.95 + recorded error analysis); dev
  traces held out; checker code digested at freeze.
- **A3** GOLD-L lessons authored from class rules; committed and
  digested **BEFORE any transfer instance exists** (A3 must be its own
  commit; the digest manifest timestamp/order is the blindness proof).
- **A4** transfer instances 5/class (different filenames/domain/
  identifiers/failure instance, same latent rule) + identifier
  disjointness matrix (automatic) + NEUTRAL-L mechanical composition
  (length ±25%, imperative ban-list lint) + experience↔transfer 6-gram
  gate.
- **A5** analyzer FIRST among execution artifacts (self-test PASS,
  fail-closed on gate records, implements the conjunctive decision rule
  + sensitivity + localization matrix + delivery-status table) + run
  wrapper (per-episode budget 80 turns / 250k tokens / 1800 s; per-cell
  wall 4 h; resumable; invalid logged, never silently re-run) +
  **A5-bis**: stub-consumer dry-run of the whole chain (all arms ×
  classes, positional delivery, journaling, checkers, analyzer
  end-to-end) + per-class synthetic known-answer traces (recurrence
  true/false; checker must match).
- **F-prep** EXEC FREEZE manifest (digests of everything above + prereg
  + power artifact + worker prompt + consumption-gate module). The
  freeze COMMIT itself may land in this session; GPU does not.

## Hard rules

- Zero GPU in this session. The pilot (first GPU) runs only after the
  non-executor gate on the frozen artifacts AND the owner kickoff word
  (never-autonomous).
- No difficulty tuning, no class edits, no taxonomy growth (FC-6 stays
  out). Any temptation to "make the trap more likely" = freeze CONT-006
  (owner direction).
- Declared deviations get recorded in LOG + the run record (house
  convention). Anything that invalidates a prereg pin → STOP + owner
  brief, not a local fix.
- Budget note: authoring is the expensive human-time phase; instances
  are cheap, classes are not — the geometry is fixed at 5 × 5.

## Entry conditions (verify before any work)

- git clean on main at the PLT-prereg commit (see LOG for the sha).
- All PLT docs present: PREREG, DESIGN rev 2, both Opus reviews, power
  artifact.
- The owner's kickoff word for this authoring half.

## Kickoff (paste into the fresh session)

"Прочитай labs/continuity/docs/SESSION-BRIEF-CONT006-PLT-AUTHORING.md і
виконай authoring half згідно бріфа. Перевір entry-умови до будь-яких
дій."
