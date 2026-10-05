# Next-cycle design notes — post-CONT-005-confirmatory (2026-10-06)

Owner-accepted direction (ROADMAP LOG 2026-10-06). Inputs: the confirmatory
run (`results/CONT-005-CONFIRMATORY/cont005-confirmatory-20261005-123917/`),
the Fable audit + label-level re-analysis (`docs/REVIEW-FABLE-RESULTS.md`).

## What the confirmatory cycle established

- The pilot's T2 advantage did not replicate (primary T0−T2 = −0.100, CI upper
  bound 0.000 EXCLUDES the pre-registered ≥0.25 effect).
- Memory itself works (A→arms on CU 0→~1.0; DR 0→0.67 after the companion fix;
  A sits at guessing level).
- At label level, trap repeats: A 25/90 > T0 15 > T2 = T3 10 > **T1 0**.

## Fixes implemented (2026-10-06, zero GPU, post-acceptance development)

1. **Render-markup leakage (claims.py):** T1/T2/T3 injections now use prose
   parenthetical annotations `(recorded in session N; source: X; verification:
   Y[; trust: Z])` — no square brackets or pipes anywhere in the line prefix
   (the v3h run showed the old bracket markup echoing into answers and causing
   invalid-format errors). Resolution flags keep their wording.
2. **Numeric supersession (claims.py R5):** an environment turn carrying the
   protocol marker "correction for the records" now supersedes the closest
   prior plain statement (the CU s1 fact). Closes the cu-2004 gap where the
   trust layer had no typed sources to act on. Assembly gate expectations
   updated (v3h G3: superseded = 2 retractions + 4 CU); all gates re-run PASS.

## Design requirements for the next suite/protocol (v3i candidate)

1. **Per-seed content variation (MANDATORY):** at temperature 0.0 with
   byte-identical prompts, seeds produced identical answers everywhere except
   one deviation — five "seeds" were effectively one run (Fable audit).
   The next fixture protocol predeclares a per-seed variant table (values,
   codes, label orders, names) so each seed is a true replicate. The
   power calculation must then use the measured between-seed spread.
2. **Primary endpoint candidate:** label-form error rate on a primary set
   where BOTH arms have headroom (the v3h CR set floored both arms at 1.0 on
   6/8 clusters — only 2 clusters discriminated).
3. **The T1 hypothesis to test properly:** annotations-only produced ZERO
   label-level trap repeats and the top overall score (0.45). Candidate
   primary contrast for the next cycle: T1 vs T0 (does provenance metadata
   alone reduce repeated mistakes?), with T2/T3 as secondary after the two
   fixes above.
4. Residual echo risk: resolution flags still carry `[RESOLVED: ...]` brackets
   on flagged lines only — watch in the next pilot; move to plain "NOTE:" prose
   if they echo.
