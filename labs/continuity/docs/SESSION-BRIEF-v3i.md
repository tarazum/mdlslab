# Session brief — suite v3i authoring + pre-registration draft (CONT-005 cycle 2)

For the NEXT working session (fresh context). This brief + the repo are the
complete state carrier; no conversation history is needed. House process:
`labs/continuity/PROCESS.md`; conventions and lessons: `LOG.md` tail.

## Entry conditions (all met at 73f1d96, verify `git status` clean on main)

- CONT-005 cycle 1 CLOSED: confirmatory accepted ("no confirmatory difference";
  CI upper bound 0 excludes the pre-registered >=0.25 effect); audit
  `docs/REVIEW-FABLE-RESULTS.md`; owner decisions in `LOG.md` 2026-10-06.
- Fixes landed: prose render annotations + R5 numeric supersession
  (`src/continuity/claims.py`); assembly gate expectations updated; all gates PASS.

## Scope (one milestone, zero GPU until the pilot)

1. **Author suite v3i** per `docs/NEXT-CYCLE-NOTES.md`:
   - fixture protocol v3i adds a **predeclared per-seed variant table**
     (values, codes, label orders, names per seed) so temp-0 seeds are true
     replicates (the cycle-1 lesson: identical prompts -> identical answers,
     effective n = 1). Extend `validate_fixtures_v3.py` with variant checks
     (V-namespace continues); extend the runner to render the per-seed variant.
   - Primary set with headroom in BOTH arms (cycle-1 CR floored both arms);
   - Primary candidate contrast: **T1 vs T0** (T1 = annotations-only, the only
     0/90 label-trap-repeat arm in cycle 1). Design the families so T1's
     treatment surface (source annotations) is exercised by most primary
     clusters.
2. **Draft the pre-registration v3** (EVALUATION-PREP-v3.md) per
   `docs/PREREG-REQUIREMENTS-V2.md` (all 9 items; power calc with the NEW
   between-seed spread assumption; frozen wordings; T2/T3 as secondaries).
3. **Power calculation artifact** (extend `power_calc_v2.py` pattern).

## Non-goals

- No inference/GPU in this milestone (the pilot is the NEXT milestone after
  Fable reviews the prereg).
- Do not touch frozen cycle-1 artifacts or `frozen-config-v2.json`.
- Do not edit `docs/research-proposal.md` (inspirer-owned).

## Exit artifacts

`fixtures/v3i/` (+ manifest with variant table), validator V-checks PASS on
v3i AND regression PASS on v3/v3h, `docs/EVALUATION-PREP-v3.md` draft,
power artifact, LOG start+result notes, commit+push, Mnemosyne note. Then the
chain continues: Fable PR-REVIEW-v3 -> freeze -> Fable gate -> pilot -> T1
confirmatory.

## Budget

<= 110 min wall, 0 GPU. Fresh session reads: this brief, PROCESS.md,
NEXT-CYCLE-NOTES.md, LOG.md tail (last 3 entries), SUITE-V3-DESIGN.md section 3
(scoring rule), EVALUATION-PREP-v2.md as the template example.

## Owner checkpoints in this milestone

None required mid-milestone (owner accepted the direction 2026-10-06); Fable
review comes after the draft, per the standing-reviewer directive.
