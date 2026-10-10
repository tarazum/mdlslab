"""Post-verdict audit pulls (owner challenge 2026-10-10): zero GPU.
(1) VAL vs TR asymmetry per arm; (2) error composition on the harm classes;
(3) rendered lessons at failing Phase-C R2 probes + the actual replies."""
import json
from pathlib import Path

LAB = Path(".")
C = LAB / "results/CONT-006-CONFIRMATORY/cont006-c-20261010-144817"
P = LAB / "results/CONT-006-PILOT/cont006-p-20261010-132230"
V = LAB / "results/CONT-006-VAL/cont006-v-20261010-130154"

TR = ["cr-8001","cr-8002","cr-8003","cr-8004","cu-8101","cu-8102","cu-8103",
      "cu-8104","rt-8201","rt-8202","rt-8203","dx-8401","dx-8402","dr-8301","dr-8302"]
VAL = ["cr-8005","cu-8105","rt-8204","dx-8403"]
CLASS = {"cr-8001":"FP-3a","cr-8002":"FP-3a","cr-8003":"FP-3b","cr-8004":"FP-3b",
         "cu-8101":"FP-1","cu-8102":"FP-1","cu-8103":"FP-1","cu-8104":"FP-1",
         "rt-8201":"FP-2","rt-8202":"FP-2","rt-8203":"FP-2","dx-8401":"FP-4",
         "dx-8402":"FP-4","dr-8301":"FP-5","dr-8302":"FP-5"}

def load(root, arm, seeds):
    out = {}
    for sd in seeds:
        f = root / arm / f"seed-{sd}" / "summary.json"
        if f.exists():
            out[sd] = json.loads(f.read_text())["probes"]
    return out

print("=" * 70)
print("(1) VAL clusters per arm (Phase V, 7 seeds) — activation surface")
for arm in ("R0", "R2", "R3"):
    data = load(V, arm, range(8001, 8008))
    per = {}
    for sid in VAL:
        probes = [p for sd in data for p in data[sd]
                  if p.get("scenario") == sid and p.get("kind") != "guess_calibration"]
        per[sid] = round(sum(1 for p in probes if p.get("passed") is True) / len(probes), 3) if probes else None
    print(f"  {arm}: {per}")

print("=" * 70)
print("(2) TR clusters per arm (P+C dataset, 7 seeds) — endpoint surface")
for arm in ("R0", "R2", "R3"):
    data = {**load(P, arm, (8001, 8002)), **load(C, arm, range(8003, 8008))}
    per = {}
    for sid in TR:
        probes = [p for sd in data for p in data[sd]
                  if p.get("scenario") == sid and p.get("kind") != "guess_calibration"]
        per[sid] = round(sum(1 for p in probes if p.get("passed") is True) / len(probes), 3) if probes else None
    print(f"  {arm}: {per}")
    if arm == "R0":
        r0 = per
    else:
        deltas = {k: round(per[k] - r0[k], 3) for k in TR}
        print(f"     delta vs R0: {deltas}")

print("=" * 70)
print("(3) error composition on the harm classes (FP-3b cr-8003/8004, FP-4 dx-8401/8402)")
harm = ["cr-8003", "cr-8004", "dx-8401", "dx-8402"]
for arm in ("R0", "R2"):
    data = {**load(P, arm, (8001, 8002)), **load(C, arm, range(8003, 8008))}
    comp = {"pass": 0, "wrong_label": 0, "format_miss": 0}
    for sid in harm:
        for sd in data:
            for p in data[sd]:
                if p.get("scenario") == sid and p.get("kind") != "guess_calibration":
                    if p.get("passed") is True: comp["pass"] += 1
                    elif p.get("observed_label") is None: comp["format_miss"] += 1
                    else: comp["wrong_label"] += 1
    print(f"  {arm} on harm clusters: {comp}")

print("=" * 70)
print("(4) failing R2 probes in Phase C on harm clusters — reply + last lesson ids")
ev = [json.loads(l) for l in (C / "R2" / "seed-8004" / "trace.jsonl").read_text(encoding="utf-8").splitlines()]
shown = 0
for e in ev:
    if e["type"] != "probe.result" or e.get("scenario") not in harm:
        continue
    pl = e["payload"]
    if pl.get("passed") is True:
        continue
    reply = next((x["payload"]["content"] for x in ev
                  if x["type"] == "agent.response" and x.get("scenario") == e["scenario"]
                  and x["payload"]["turn_ref"] == pl["turn_ref"]), "?")
    lessons = [x for x in ev if x["type"] == "lessons.injected" and x.get("scenario") == e["scenario"]]
    lids = lessons[-1]["payload"]["lesson_ids"] if lessons else []
    print(f"  {e['scenario']}/{pl['turn_ref']} exp={pl.get('expected')!r} obs={pl.get('observed_label')!r}")
    print(f"    lessons: {lids}")
    print(f"    reply: {reply[:160]!r}")
    shown += 1
    if shown >= 5:
        break
