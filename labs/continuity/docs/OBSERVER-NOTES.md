# Continuity — independent observer notes

Author-owned research observations. This file does not control the active autonomous arc. It must not modify or reinterpret the experiment protocol mid-run.

## 2026-10-01 23:59 Europe/Kyiv — observed `fccb85a`

### Measured observations

- M4 and M5 are DONE; M6 is IN_PROGRESS. Evidence: `docs/ROADMAP.md`, `LOG.md`, and committed M4/M5 pilot artifacts.
- Arm D (C + deterministic reflection) did not change any family pass rate relative to C in the 3-seed mini-pilot. In particular, `repeated_task` remained 0.333. The reflection layer produced conflict-review summaries but did not cure the rt-0003 own-answer anchoring described by CN-007. Primary artifact: `results/CONT-000/pilot-armD-20261001-233203/armA-vs-armB-vs-armC-vs-armD.md`.
- Arm E likewise did not change behavior relative to D: E-D = 0.000 for every family/scenario. This is not evidence that policy/world-model mechanisms are ineffective: all 24/24 `retrieve_then_answer` actions were deduplicated no-ops and produced zero physical retrieval injections because current probes occur on the first turn of each session (CN-010). Primary artifact: `results/CONT-000/pilot-armE-20261001-234851/armA-vs-armB-vs-armC-vs-armD-vs-armE.md`.
- The arm-E world model emitted 30 predictions with 27/30 pass/fail calls correct, but its confidence derives from arm-B family rates on the same fixture suite. The apparent 0.900 accuracy is therefore exploratory and partly circular/stale (CN-009), not clean evidence of calibrated self-prediction.
- Across B/C/D/E, the persistent failure pattern is now structurally clearer: delayed/distractor recall reaches 1.000, contradiction handling improves under C+, but repeated_task stays 0.333. The system can retain facts much more readily than it can revise an anchored task interpretation.

### Methodological cautions

- Do not interpret D=C as a null result for reflection. The current reflection mechanism adds evidence summaries, while the observed anchoring failure may require source authority/supersession or policy-level suppression. This is precisely the distinction CONT-005 should test later.
- Do not interpret E=D as a null result for bounded policy. CN-010 shows the current fixture topology provides no behavior-changing actuation surface. A confirmatory policy comparison needs non-first-turn probes or mid-session memory growth, pre-registered before data collection.
- M6 correctly leaves current fixtures untouched for exploratory comparability. Any fixes for CN-004/CN-009/CN-010 belong in the held-out confirmatory design, not this running batch.

### Next-cycle ideas / hypotheses

1. **Memory Trust Hierarchy gains a sharper causal target.** Split failure handling into (a) retrieval, (b) evidence authority/supersession, and (c) response policy. CN-007 shows that merely juxtaposing corrective evidence with the agent's own old answer can be insufficient; CN-008 shows retrieval can succeed while final conflict resolution fails.
2. **Counterfactual memory ablation.** For a held-out anchored-error scenario, replay the same state while selectively masking only prior `agent.response` episodes, then only corrective/environment episodes. This can quantify whether the harmful causal path is the stored own answer versus generic extra context. Keep it as a next-cycle experiment, not a current fixture change.
3. **Self-model provenance aging.** World-model confidence currently inherits stale arm-B capability rates after behavior changes under C+. A future design could version capability estimates by architecture/state revision and mark them stale when the architecture changes, rather than treating capability as a timeless property of the base model.
4. **Reflection needs an action contract, not only a summary contract.** A future ablation can compare evidence-only reflection against reflection that emits validated supersession/trust proposals. That would connect M4 directly to CONT-005 without allowing reflection to rewrite immutable history.

Next observer pass should focus on M6 exploratory cross-arm artifacts and `EVALUATION-PREP.md`, especially whether the held-out plan cleanly separates the repeated-mistake endpoint from CN-004 leakage and CN-009 exposure.


## 2026-10-02 04:28 Europe/Kyiv — final pass

Arc status: COMPLETE. Checked `docs/ARC-REPORT.md`, frozen `docs/EVALUATION-PREP.md`, `docs/PR-REVIEW.md`, and confirmatory artifacts under `results/CONT-001-confirmatory/cont001-confirmatory-20261002-005711/`.

### Observations

- Primary frozen verdict remains **no confirmatory difference established**: strict RM A=0.000, E=0.3333, delta +0.3333, 95% CI [0.0, 0.75].
- Delayed recall is a strong secondary signal: A=0.0, E=1.0, delta +1.0, CI [1.0, 1.0].
- Reflection is the most important next-cycle clue: strict RM C=0.000, D=0.500; D-C +0.5015, CI [0.1429, 0.8571] (secondary only). The artifacts associate this with verbatim reuse of earlier agent replies in reflection context.
- Arm E physically actuated on fixture v2 (7 injections and 13 retrieves per seed), so the earlier inert-policy confound is closed. E-D RM still spans zero.
- Token cost per arm: A 26,329; B 46,540; C 152,320; D 272,795; E 278,805.
- CONT-002 remains mechanics-only; no transfer-quality conclusion is warranted.

### Next-cycle ideas

1. Prioritize CONT-005 Memory Trust Hierarchy.
2. Add a reflection-causality ablation: no reflection; summary-only; mask prior reply text; mask corrective evidence; validated trust/supersession proposals.
3. Represent observations, derived claims, and agent replies as distinct memory objects with provenance rather than equal factual authority.
4. Mark capability estimates stale when the architecture revision changes and recalibrate them.
5. Run behavioral CONT-002 after memory semantics are cleaner, then replicate the key trust/reflection experiment on another instruct-capable core.

### Recommendation

Accept M7 as a valid execution of the frozen protocol with its stated null confirmatory verdict. Use the recall benefit and reflection-related repeated-error signal as secondary evidence to design the next cycle; do not promote them into the primary claim.
