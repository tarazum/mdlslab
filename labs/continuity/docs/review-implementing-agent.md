# Review: Continuity research proposal — implementing agent

- Reviewer: the agent expected to implement CONT-000 and later stages (ZCode session).
- Date: 2026-10-01.
- Subject: `labs/continuity/docs/research-proposal.md` as of commit `4bd51b0`.
- Verdict: direction approved; the proposal is methodologically sound and consistent with the repository's principles. Four change requests below — CR-1 and CR-2 should be folded in before P0 starts; CR-3 is editorial; CR-4 is strategic. No blockers.
- Scope note: this file is input for the proposal author. The reviewer deliberately did not edit `research-proposal.md` itself.

## Change requests

### CR-1: CONT-002 needs the fourth cell of the 2×2 (must fix before P0)

The three comparison conditions in CONT-002 give:

1. core A + restored state
2. core A + clean state
3. core B + restored state

Cell 4 — **core B + clean state** — is implied ("control transfer effects caused by different models' intrinsic capabilities") but not listed. Without it, "the state transferred to B" cannot be separated from "B is intrinsically different from A".

Request: state the design as an explicit 2×2, {core A, core B} × {restored, clean}, same held-out tasks and seed count per cell, and define the quantity of interest as the interaction: does the state effect on B, Δ(B+state − B+clean), preserve a meaningful fraction of the state effect on A, Δ(A+state − A+clean)? Adding the cell costs one more run configuration and removes the main confound of the experiment the owner cares most about.

### CR-2: one primary endpoint per experiment (must fix before CONT-001 pre-registration)

CONT-001 currently evaluates roughly ten measures with no hierarchy. With repeated seeded runs and many metrics, some metric will always move — post-hoc selection among them is HARKing.

Request: each CONT-NNN names exactly one pre-registered primary endpoint (the acceptance condition), with everything else explicitly secondary/exploratory. Implementer's proposals, for the author/owner to confirm or replace:

- CONT-001 primary: repeated-mistake rate on task families encountered in earlier sessions (arm-vs-arm A→E).
- CONT-002 primary: retained-benefit ratio on held-out tasks, i.e. Δ(B+state − B+clean) relative to Δ(A+state − A+clean).

### CR-3: editorial — duplicate stage label in the backlog

Section 5 contains two `P1:` lines (build arms; then execute CONT-001). Relabel the second as its own stage or merge, so the staging stays unambiguous.

### CR-4: one fixture suite, three consumers (strategic)

CONT-004 overlaps TAM-002…TAM-007 by a large margin, and the memory-behavior workload is also the intended comparison vehicle for the private OCL side. The risk is two half-built harnesses measuring slightly different things.

Request: design the CONT-000 synthetic scenario package from the start as a lab-agnostic workload protocol — fixtures, metric definitions, and a runner contract — so the TencentDB Agent Memory lab (and OCL, running it privately elsewhere) can execute the identical package. Until a second consumer actually exists, keep it lab-local per the repository's shared-assets rule, but design for extraction rather than for Continuity-specific coupling.

## Feasibility notes (advisory, not change requests)

1. **Effect size vs variance is the central scientific risk.** Small quantized cores have high run-to-run variance; the state/memory effect can drown in noise. Recommend an early variance baseline inside CONT-000: run one arm across N seeds and measure the spread of candidate endpoints before investing in arms B–E. The "~100 sessions" figure should be justified by this baseline, not assumed. Fix decoding parameters; note in the experiment record that greedy decoding does not guarantee bit-identical outputs across batch sizes.
2. **Task calibration headroom.** Scenario families must sit between the noise floor and the base model's ceiling: pilot arm A (no memory) on the full suite; if A is at ceiling, redesign tasks until accumulated experience has room to matter.
3. **Compute arithmetic.** A 100-session run × ~3 turns × ~2–3k tokens ≈ 0.6–0.9M tokens per arm-set; × 5 arms × ≥3 seeds ≈ 10–15M tokens — days of wall-clock at local speeds on the 8 GB reference machine. Plan overnight batches and take the `shared/tooling/agent-resource-coordination` lock when the GPU is contended.
4. **Sequencing.** JEV-001 and TAM-001 are cheap, already unblocked, and de-risk Continuity's optional adapters (Jev policy adapter, TencentDB backend). They should not be frozen while Continuity starts.

## What the reviewer commits to

Treat proposal + this review as the implementation contract: start CONT-000 inside the first-implementation boundary (compact local core, SQLite event store, synthetic-only data, explicit stop/budget), do the variance baseline before building further arms, and expand scope only by owner decision.
