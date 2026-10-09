# Session brief — CONT-006 V2A EXECUTION CHAIN (v3n surface; A.8 applied)

Supersedes SESSION-BRIEF-CONT006-V2-EXEC.md for the v3n rerun (the v3m
brief stays as the stopped chain's record). Basis: EVALUATION-PREP-
CONT006-V2.md (A.1–A.7) + EVALUATION-PREP-CONT006-V2-A8.md (A.8; ROADMAP
Owner decisions 2026-10-10) + REVIEW-CONT006-A8.md (GO-with-changes, all
folded).

## Ground truth (v3n)

- Suite: `fixtures/v3n`, sha256 starts `9201d710`; validator `--suite v3n`
  PASS 20/20; regressions v3..v3m PASS ×7 (artifact:
  experiments/suite-v3/regressions-v3n.json); seeds {8001..8007}; TR =
  cr-8001..8004, cu-8101..8104, rt-8201..8203, dx-8401..8402, dr-8301..8302
  (15); VAL = cr-8005, cu-8105, rt-8204, dx-8403; GC = gc-8501..8503;
  CF_SUBSET = [cr-8001, cr-8003, rt-8201, rt-8202, cu-8101, dx-8401,
  dr-8301, gc-8501].
- Stores (A.8.3, REUSED byte-identically — NO new worker inference):
  R2 = results/CONT-006-WORKER/cont006-worker-v2-20261010-000332/
  r2-store-v2.json (file sha 66b2ba54…; store content sha f82efc3f…);
  R3 = experiments/cont006/r3-store-v2.json (content sha 48064a02…).

## Chain (binding order; A.6 with the A.8 substitution)

1. FREEZE V3: the execution port (run_cont006.py + both analyzers +
   analyze_calibration.py on x-8xxx/8001..8007; contamination gate
   --suite v3n; CF check covers v3n) is committed BEFORE the manifest
   emission; emit frozen-config-cont006-v3.json (v3n digests + all V2A
   frozen paths); preflight must PASS. W2 and R3-recap steps are SKIPPED
   (stores reused per A.8).
2. Contamination gate: contamination_gate_v2.py --suite v3n over both
   stores (pre-checked 0 hits; re-run and commit the verdict).
3. Calibration pilot (A.3 unchanged): `--phase CAL --worker-dir <W2 dir>`;
   live_telemetry_gate FIRST; analyze_calibration.py verdict.
   In band → the v3n CAL cells are part of the final dataset; out of band
   → STOP, record, owner.
4. Phase V (`--phase V --worker-dir <W2 dir>`): VAL scenarios, both
   stores; operator-side anchor check |S0 − 0.525| ≤ 0.15 BEFORE
   V-activate; live gate; `--phase V-activate --val-root <V root>`.
5. Phase P: copy the four CAL cells (R0/R2 × 8001/8002) into the fresh P
   root (declared mechanical copy — single-freeze dataset, no re-inference),
   then `--phase P --active-dir <V root> --resume-root <P root>`; live
   gate; analyze_pilot_cont006.py; pilot-gate checkpoint (GO → continue;
   NO-GO → halt & report).
6. Phase C: `--phase C --active-dir <V root> --resume-root <C root>`
   (seeds 8003..8007 + any pilot-arm completions); live gate;
   analyze_confirmatory_cont006.py --pilot-root <P> --conf-root <C>.
7. Close-out: run record (header: CN-012 invalidation, accidental-ablation
   label, PW-OVERRIDE history, A.1–A.8 incl. the v3m CAL-STOP note +
   corpus-coverage caveat); owner brief; LOG; safety scan; push.

## Hard rules — unchanged from the V2 brief (all six) + A.8 additions

No v3n edits, no parameter moves, no MME moves; live gate before every
analyzer; anchor/family-band breach → halt; freeze-digest guard trips →
restore from git, halt, log; memory arms must append (invalid cell = STOP);
commit per phase; declare substitutions. W2 re-run is FORBIDDEN under A.8
(the committed stores are the frozen evidence).
