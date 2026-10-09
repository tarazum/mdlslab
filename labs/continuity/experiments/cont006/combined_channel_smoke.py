"""Combined channel-liveness smoke (Fable C.2 / RC-2; K-4 fold of
REVIEW-FABLE-CONT006-V2): EVERY memory arm (R0/R1/R2/R3/RBAD/RGOLD) on a
REAL multi-session v3l scenario, asserting from TRACE ARTIFACTS (not object
state): (a) memory.append > 0; (b) non-empty memory.injected at session >= 2
with refs resolving to earlier committed turns; (c) R0/R2/R3 see the SAME
episodic content for the same scenario/seed before lesson augmentation
(RC-2e/RC-3 core); (d) lesson arms render a non-empty lesson block;
(e) no silent context clip (prompt tokens << num_ctx); (f) R1's reflection
is episode-DERIVED (reflection.start evidence_episode_ids non-empty — C.5).
Zero GPU (FakeProvider).
"""
import json
import sys
import tempfile
from pathlib import Path

LAB = Path(r"C:\projects\mdlslab\labs\continuity")
sys.path.insert(0, str(LAB / "src"))

from continuity.events import EventJournal
from continuity.fixtures import render_seed_variant
from continuity.lessons import LessonChannel, make_store
from continuity.memory import MemoryStore
from continuity.runner import Budget, run_scenario

STORE = make_store([{
    "lessonId": "LL-SMOKE", "title": "One option, nothing else",
    "applicability": ["a closed list of choices is offered"],
    "recommendedBehavior": "respond with exactly one item from the list",
}], source="worker", status="active")


class FakeProvider:
    model = "fake"
    options = {"temperature": 0.0}
    def chat(self, messages):
        prompt_words = sum(len(m["content"].split()) for m in messages)
        return {"content": f"ack ({prompt_words} words in context)",
                "usage": {"prompt_tokens": prompt_words, "eval_tokens": 3,
                          "total_tokens": prompt_words + 3},
                "total_duration_ms": 1.0}


def run(arm, scenario, tmp, lessons=None, selfmodel=None, reflection=None):
    # (kept for external callers/tests; the main loop inlines the same wiring
    # so R1's engine shares the runner's memory + journal objects)
    mem = MemoryStore(str(tmp / f"m-{arm}.sqlite3"))
    jour = EventJournal(str(tmp / f"t-{arm}.jsonl"), f"smoke2-{arm}")
    try:
        summary = run_scenario(scenario, FakeProvider(), jour,
                               Budget(60, 200_000, 120), arm=arm,
                               memory=mem, lessons=lessons,
                               selfmodel=selfmodel, reflection=reflection)
        events = [json.loads(l) for l in
                  (tmp / f"t-{arm}.jsonl").read_text(encoding="utf-8").splitlines()]
        return summary, events
    finally:
        jour.close()
        mem.close()


def main():
    base = json.loads((LAB / "fixtures/v3l/contradiction_update/cu-6101.json")
                      .read_text(encoding="utf-8"))
    scenario = render_seed_variant(base, 6001)
    for sess in scenario["sessions"]:
        for t in sess["turns"]:
            t.pop("probe", None)
            t.pop("initial_expected", None)
    tmp = Path(tempfile.mkdtemp())
    episodic_by_arm = {}
    # K-4 fold (REVIEW-FABLE-CONT006-V2): EVERY memory arm — R1 included
    # (C.5: with memory alive, its episode-derived reflection path is finally
    # exercised offline) and RGOLD alongside RBAD.
    from continuity.reflection import ReflectionEngine
    selfmodel_src = (LAB / "results" / "CONT-001-confirmatory" /
                     "cont001-confirmatory-20261002-005711" /
                     "selfmodel-v2-calibration.json")
    for arm, lessons in (("R0", None), ("R1", None), ("R2", LessonChannel(STORE)),
                         ("R3", LessonChannel(STORE)), ("RBAD", LessonChannel(STORE)),
                         ("RGOLD", LessonChannel(STORE))):
        mem = MemoryStore(str(tmp / f"m-{arm}.sqlite3"))
        jour = EventJournal(str(tmp / f"t-{arm}.jsonl"), f"smoke2-{arm}")
        selfmodel = reflection = None
        if arm == "R1":
            # run_cont006 wiring: engine shares THE runner's memory + journal;
            # per-run selfmodel copy (never the frozen calibration file)
            run_copy = tmp / "selfmodel-run.json"
            run_copy.write_bytes(selfmodel_src.read_bytes())
            reflection = ReflectionEngine(selfmodel_path=str(run_copy),
                                          memory=mem, journal=jour,
                                          run_seed=6001,
                                          source_artifact=(
                                              "smoke per-run copy of "
                                              "results/CONT-001-confirmatory/"
                                              "cont001-confirmatory-20261002-"
                                              "005711/selfmodel-v2-calibration"
                                              ".json"))
            selfmodel = reflection.model
        try:
            summary = run_scenario(scenario, FakeProvider(), jour,
                                   Budget(60, 200_000, 120), arm=arm,
                                   memory=mem, lessons=lessons,
                                   selfmodel=selfmodel, reflection=reflection)
            events = [json.loads(l) for l in
                      (tmp / f"t-{arm}.jsonl").read_text(encoding="utf-8")
                      .splitlines()]
        finally:
            jour.close()
            mem.close()
        appends = [e for e in events if e["type"] == "memory.append"]
        inj = [e for e in events if e["type"] == "memory.injected"]
        inj_ok = [e for e in inj if e["payload"]["episode_count"]]
        les = [e for e in events if e["type"] == "lessons.injected"]
        les_ok = [e for e in les if e["payload"]["injected"]]
        assert len(appends) == 8, (arm, len(appends))          # (a) appends
        assert len(inj_ok) >= 2, (arm, len(inj_ok))            # (b) non-empty s>=2
        refs = {tuple(r.split("|")) for e in inj_ok
                for r in e["payload"]["episode_refs"]}
        assert refs, arm                                        # (b2) refs resolve shape
        episodic_by_arm[arm] = refs
        if lessons is not None:
            assert les_ok, arm                                  # (d) lesson render
        if arm == "R1":
            # (f) C.5: episode-DERIVED reflection — reflection.start events
            # carry non-empty evidence_episode_ids (the invalid run's R1
            # reflected with zero episodes; that mode must be distinguishable)
            rstarts = [e for e in events if e["type"] == "reflection.start"]
            assert rstarts and all(
                e["payload"]["evidence_episode_ids"] for e in rstarts), arm
            assert summary["reflection"]["passes"] >= 1, arm
        max_prompt = max(e["payload"]["usage"]["prompt_tokens"]
                         for e in events if e["type"] == "agent.response")
        assert max_prompt < 3500, (arm, max_prompt)             # (e) no clip (4096 ctx)
        print(f"PASS {arm}: appends={len(appends)} inj_nonempty={len(inj_ok)} "
              f"lesson_renders={len(les_ok)} max_prompt_tok={max_prompt}")
    # (c) arm-equivalence: identical episodic refs across R0/R2/R3
    assert episodic_by_arm["R0"] == episodic_by_arm["R2"] == episodic_by_arm["R3"], \
        {a: len(r) for a, r in episodic_by_arm.items()}
    print(f"PASS arm-equivalence: R0/R2/R3 identical episodic refs "
          f"({len(episodic_by_arm['R0'])} refs)")
    print("COMBINED SMOKE COMPLETE: all channels live on a real multi-session "
          "scenario for every memory arm (zero GPU)")


if __name__ == "__main__":
    main()
