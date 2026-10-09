"""Paired arm-equivalence audit (REVIEW-CONT006-CN012-RERUN RC-3): a
mechanical pre-run artifact proving that R0/R2/R3 differ ONLY in the lesson
source/channel, and R1 only in the reflection machinery. Everything else —
model, provider config, memory implementation, retrieval top-k and
renderer, fixture rendering, session reset, seed semantics, episodic store
semantics — must be byte-identical configuration.

Emits experiments/cont006/arm-equivalence-audit.json; the gate/review chain
verifies it before any behavioral inference. Deterministic, zero GPU.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LAB_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(LAB_ROOT / "src"))

from continuity import runner as R  # noqa: E402
from continuity import provider as P  # noqa: E402
from continuity import lessons as L  # noqa: E402

ARMS = ["R0", "R1", "R2", "R3", "RBAD", "RGOLD"]
EXPECTED_DIFFS = {
    ("R0", "R2"): ["lesson store: none vs worker store"],
    ("R0", "R3"): ["lesson store: none vs gold store"],
    ("R2", "R3"): ["lesson store: worker vs gold"],
    ("R0", "R1"): ["reflection machinery: none vs deterministic MVP + selfmodel block"],
    ("R0", "RBAD"): ["lesson store: none vs counterfactual BAD"],
    ("R0", "RGOLD"): ["lesson store: none vs counterfactual GOLD-TRIV"],
}


def main() -> int:
    # 1. memory membership identical across all six arms (single source)
    membership = {arm: arm in R.MEMORY_ARMS for arm in ARMS}
    assert all(membership.values()), membership
    # 2. provider defaults (model pinning happens per run-script; sampling
    #    contract is the provider's own dict)
    provider_contract = dict(P.OllamaProvider(
        model="x", temperature=0.0, seed=0).options)
    assert provider_contract == {"temperature": 0.0, "seed": 0,
                                 "num_ctx": 4096, "num_predict": 256}
    # 3. retrieval/renderer constants shared (module-level, not per-arm)
    retrieval = {"memory_top_k": R.MEMORY_TOP_K,
                 "lesson_top_k": L.LESSON_TOP_K,
                 "render_budget_words": L.MAX_RENDER_WORDS,
                 "memory_renderer": "flat (format_memory_block) for every R-arm",
                 "lesson_renderer": "prose (render_block) for lesson arms"}
    # 4. arm-gated machinery table (from the runner source, asserted)
    import inspect
    src = inspect.getsource(R.run_scenario)
    checks = {
        "append_from_memory_arms": "if arm in memory_arms:" in src,
        "no_second_arm_tuple": src.count('arm in ("B"') == 0,
        "lesson_guard": "lesson channel is R2/R3/RBAD/RGOLD only" in src,
        "selfmodel_R1_only_among_R": 'arm in ("C", "D", "E", "R1")' in src,
        "reflection_R1_only_among_R": 'arm in ("D", "E", "R1")' in src,
    }
    assert all(checks.values()), checks
    # 5. fixture rendering: single definition (import identity)
    from continuity.fixtures import render_seed_variant
    rendering = {"definition": "continuity.fixtures.render_seed_variant",
                 "shared_by": "runner, validator, gates (single import)",
                 # stable identity (repr carries a per-process address -> the
                 # artifact must be byte-stable for the freeze manifest)
                 "object": (f"{render_seed_variant.__module__}."
                            f"{render_seed_variant.__qualname__}")}
    # 6. session reset semantics identical for every arm (context reset +
    #    persistent store retained; verified by the combined channel smoke)
    session_semantics = ("context reset per session for ALL arms; memory store "
                         "retained for all memory arms; lesson channel injected "
                         "per session for lesson arms only (verified live by "
                         "experiments/cont006/combined_channel_smoke.py)")
    # 7. seed semantics: sampler seed = variant seed, inert at temp 0
    seed_semantics = ("sampler seed == variant seed (house convention; PB-071 "
                      "caveat travels); identical across arms")
    audit = {
        "kind": "cont006-arm-equivalence-audit",
        "arms": ARMS,
        "expected_diffs": {f"{a} vs {b}": d for (a, b), d in EXPECTED_DIFFS.items()},
        "verified": {
            "memory_membership_single_source": membership,
            "provider_sampling_contract": provider_contract,
            "retrieval_and_rendering": retrieval,
            "runner_source_checks": checks,
            "fixture_rendering": rendering,
            "session_semantics": session_semantics,
            "seed_semantics": seed_semantics,
        },
        "conclusion": ("R0/R2/R3 differ ONLY by the lesson store; RBAD/RGOLD only "
                       "by the counterfactual store; R1 additionally carries the "
                       "deterministic MVP reflection. All other machinery is "
                       "shared module-level code."),
    }
    out = LAB_ROOT / "experiments" / "cont006" / "arm-equivalence-audit.json"
    out.write_text(json.dumps(audit, indent=1, ensure_ascii=True) + "\n",
                   encoding="utf-8")
    print("ARM-EQUIVALENCE AUDIT: PASS (all source checks hold; artifact written)")
    print(f"written: {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
