# EVALUATION-PREP-CONT006-V2-A11 — the pilot-override + R1-drop amendment

Status: **OWNER-ACCEPTED 2026-10-10** (ROADMAP "Owner decisions — recorded
2026-10-10 (CONT-006 A.11: pilot NO-GO OVERRIDDEN; R1 dropped from the
confirmatory)"; owner chat: "все по дефолту - ок. давай іти і доводити
експеримент до успіху"). Two changes; everything else in A.1–A.10 stays
binding.

## A.11.1 — Pilot NO-GO OVERRIDDEN (PW-OVERRIDE-2)

The pilot-gate NO-GO (criterion 2: RGOLD invalid-format 0.143 → 0.357 —
the trivially-benign format lesson degrades format via list-echoing) is
explicitly OVERRIDDEN by the owner. Legal per prereg §9 (the pilot-gate
checkpoint is an owner decision point; V1 precedent PW-OVERRIDE). The
primary R2−R0 endpoint is unaffected (counterfactual arms never enter
it); the RGOLD finding rides the run record as a HEADLINE SECONDARY
(its third independent appearance: worker lessons, the CAL suppression
signal, and now the CF manipulation check — lesson-prescribed output
behavior interacts badly with probe instructions on this model).

## A.11.2 — R1 dropped from the confirmatory

The R1 pilot cells are defective (A.10/T4: context overflow at the
18-scenario scale — max prompt 4085/4096, 6 of 168 generations truncated
at the num_predict cap; audit in LOG 2026-10-10). R1 is a SECONDARY arm;
the registered primary never involves it. Decisions:

1. The confirmatory dataset is R0/R2/R3 × 15 TR clusters × 7 seeds
   (completeness 15×7×3; the frozen analyzer's arm set and the Phase-C
   arm list are amended accordingly — the ONLY code changes under A.11).
2. The R1−R0 parroting-replication secondary is NOT ESTIMABLE this run;
   the analyzer reports it as such. The hypothesis stays OPEN (not
   refuted); the R1 pilot cells remain committed as flagged exploratory
   evidence.
3. The R1 pilot cells stay in the Phase-P root (evidence; the analyzer
   does not read them under the amended arm set).
4. No re-run of any healthy cell: CAL/V/P data are the single-freeze
   dataset (R1 included where it already ran, excluded where it did not).

## What A.11 does NOT change

The primary endpoint Δ = S(R2) − S(R0) over 15 TR clusters × 7 seeds; the
four-branch decision rule; MME 0.20 (band caveat-only); bootstrap/RNG;
the stores and activation decisions (both ACTIVE); the counterfactual
arm cells already collected; the A.2/A.10 gating (the Phase-C root must
pass the live gate before the analyzer — R0/R2/R3 prompts peak ~3.4k
tokens on the existing evidence, comfortably inside the 4096−512 pin);
never-autonomous.
