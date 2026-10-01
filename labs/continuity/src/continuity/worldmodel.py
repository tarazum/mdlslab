"""Ex-ante world model: probe predictions + calibration counters (arm E MVP, stdlib only).

M5 contract (docs/ROADMAP.md): BEFORE each PROBE turn is answered, record an
ex-ante prediction of the probe outcome (pass/fail) plus a simple confidence;
after the outcome is scored, attach it and maintain bucketed calibration
counters (predicted-pass rate vs actual pass rate). Predictions are trace
events (`worldmodel.prediction` / `worldmodel.outcome`) and NEVER alter the
prompt or the answer path — the M5 policy acts on environment/memory signals,
not on predictions, so the world model stays purely observational in this MVP.

Prediction basis (deterministic; deliberately tiny and blind to the expected
answer):
1. c = the self-model's CURRENT pass-rate estimate for the probe's family
   (measured, provenance-carrying; 0.5 default prior when the family is
   unknown to the store). CN-009 caveat applies: the revision-1 estimates
   were measured on the same fixture suite the predictions are scored on,
   so "calibration" here is partly circular — reported as an exploratory
   number, never as clean calibration.
2. If the memory store holds no episodes for the scenario (nothing to
   recall from), c = min(c, NO_RECORDS_CAP): without records the family
   estimate does not apply.

Predicted outcome = pass iff c >= DECISION_THRESHOLD. Confidence bucket:
high (c >= 0.75) / medium (0.5 <= c < 0.75) / low (c < 0.5).

Calibration counters are telemetry only: per bucket n, predicted-pass rate,
actual pass rate, mean confidence; overall accuracy of the pass/fail call.
"""

from __future__ import annotations

from typing import Any

from .events import EventJournal

BUCKETS = ("high", "medium", "low")
BUCKET_BOUNDS = {"high": 0.75, "medium": 0.50}  # low: anything below "medium"
DECISION_THRESHOLD = 0.50  # predicted pass iff confidence >= threshold
NO_RECORDS_CAP = 0.25  # records absent -> confidence cannot exceed this
DEFAULT_PRIOR = 0.50  # family unknown to the self-model


def bucket_of(confidence: float) -> str:
    if confidence >= BUCKET_BOUNDS["high"]:
        return "high"
    if confidence >= BUCKET_BOUNDS["medium"]:
        return "medium"
    return "low"


def family_rate(selfmodel: dict[str, Any] | None, family: str) -> float | None:
    """Current self-model pass-rate estimate for `family` (None if absent)."""
    if not selfmodel:
        return None
    for cap in selfmodel.get("capabilities", []):
        if cap.get("family") == family:
            return float(cap["rate"])
    return None


class WorldModel:
    """One world model per run (per seed); predicts probe turns only.

    Emits `worldmodel.prediction` before the probe turn is answered and
    `worldmodel.outcome` after scoring; keeps running calibration counters.
    """

    def __init__(self, journal: EventJournal) -> None:
        self.journal = journal
        self._prediction_counter = 0
        self._pending: dict[tuple[str, str], dict[str, Any]] = {}
        self.counters: dict[str, Any] = {
            "predictions": 0,
            "outcomes": 0,
            "predicted_pass": 0,
            "actual_pass": 0,
            "correct_calls": 0,
            "confidence_sum": 0.0,
            "by_bucket": {
                b: {"n": 0, "predicted_pass": 0, "actual_pass": 0, "confidence_sum": 0.0}
                for b in BUCKETS
            },
        }

    # ---------------------------------------------------------------- predict

    def predict_probe(
        self,
        *,
        scenario: str,
        family: str,
        turn_ref: str,
        family_rate_value: float | None,
        episodes_for_scenario: int,
        session: int,
    ) -> dict[str, Any]:
        """Record the ex-ante prediction for one probe turn (before answering)."""
        self._prediction_counter += 1
        prediction_id = f"W-{self._prediction_counter:04d}"
        if family_rate_value is None:
            confidence = DEFAULT_PRIOR
        else:
            confidence = family_rate_value
        if episodes_for_scenario <= 0:
            confidence = min(confidence, NO_RECORDS_CAP)
        confidence = round(min(1.0, max(0.0, confidence)), 3)
        predicted = "pass" if confidence >= DECISION_THRESHOLD else "fail"
        record = {
            "prediction_id": prediction_id,
            "scenario": scenario,
            "family": family,
            "turn_ref": turn_ref,
            "family_rate": family_rate_value,
            "episodes_for_scenario": episodes_for_scenario,
            "confidence": confidence,
            "bucket": bucket_of(confidence),
            "predicted": predicted,
        }
        self._pending[(scenario, turn_ref)] = record
        self.counters["predictions"] += 1
        self.journal.emit(
            "worldmodel.prediction", dict(record), scenario=scenario, session=session
        )
        return record

    # ---------------------------------------------------------------- outcome

    def attach_outcome(
        self, *, scenario: str, turn_ref: str, passed: bool, session: int
    ) -> dict[str, Any] | None:
        """Attach the scored outcome to its prediction; update calibration."""
        key = (scenario, turn_ref)
        record = self._pending.pop(key, None)
        if record is None:
            return None  # no prediction was recorded for this probe turn
        correct = (record["predicted"] == "pass") == bool(passed)
        bucket = record["bucket"]
        slot = self.counters["by_bucket"][bucket]
        self.counters["outcomes"] += 1
        self.counters["predicted_pass"] += 1 if record["predicted"] == "pass" else 0
        self.counters["actual_pass"] += 1 if passed else 0
        self.counters["correct_calls"] += 1 if correct else 0
        self.counters["confidence_sum"] += record["confidence"]
        slot["n"] += 1
        slot["predicted_pass"] += 1 if record["predicted"] == "pass" else 0
        slot["actual_pass"] += 1 if passed else 0
        slot["confidence_sum"] += record["confidence"]
        outcome = {
            "prediction_id": record["prediction_id"],
            "turn_ref": turn_ref,
            "predicted": record["predicted"],
            "confidence": record["confidence"],
            "bucket": bucket,
            "actual_passed": bool(passed),
            "prediction_correct": correct,
        }
        self.journal.emit(
            "worldmodel.outcome", dict(outcome), scenario=scenario, session=session
        )
        return outcome

    # ------------------------------------------------------------ calibration

    def calibration(self) -> dict[str, Any]:
        """Bucketed calibration summary (predicted-pass rate vs actual)."""
        n = self.counters["outcomes"]

        def rate(num: int, den: int) -> float | None:
            return round(num / den, 3) if den else None

        by_bucket: dict[str, Any] = {}
        for bucket in BUCKETS:
            slot = self.counters["by_bucket"][bucket]
            by_bucket[bucket] = {
                "n": slot["n"],
                "predicted_pass_rate": rate(slot["predicted_pass"], slot["n"]),
                "actual_pass_rate": rate(slot["actual_pass"], slot["n"]),
                "mean_confidence": rate(slot["confidence_sum"], slot["n"]),
            }
        return {
            "predictions": self.counters["predictions"],
            "outcomes": n,
            "overall": {
                "predicted_pass_rate": rate(self.counters["predicted_pass"], n),
                "actual_pass_rate": rate(self.counters["actual_pass"], n),
                "accuracy": rate(self.counters["correct_calls"], n),
                "mean_confidence": rate(self.counters["confidence_sum"], n),
            },
            "by_bucket": by_bucket,
            "cn009_caveat": (
                "prediction confidence derives from self-model family rates "
                "estimated on the same fixture suite (CN-009) — exploratory "
                "calibration, not clean calibration"
            ),
        }


# --- offline selftest -------------------------------------------------------


def _selftest() -> int:
    """Offline: prediction determinism, outcome attachment, counter arithmetic."""
    import tempfile
    from pathlib import Path

    journal_path = Path(tempfile.mkdtemp()) / "trace.jsonl"
    journal = EventJournal(str(journal_path), "selftest-run")

    wm = WorldModel(journal)
    # Prediction 1: known family rate 1.0 with records -> high/pass.
    p1 = wm.predict_probe(
        scenario="dr-x", family="delayed_recall", turn_ref="s2t1",
        family_rate_value=1.0, episodes_for_scenario=4, session=2,
    )
    assert p1["predicted"] == "pass" and p1["bucket"] == "high", p1
    # Prediction 2: unknown family -> default prior 0.5 -> medium/pass.
    p2 = wm.predict_probe(
        scenario="dx-x", family="unknown_family", turn_ref="s2t1",
        family_rate_value=None, episodes_for_scenario=3, session=2,
    )
    assert p2["confidence"] == 0.5 and p2["bucket"] == "medium", p2
    # Prediction 3: no records caps the confidence below the threshold.
    p3 = wm.predict_probe(
        scenario="dr-y", family="delayed_recall", turn_ref="s2t1",
        family_rate_value=1.0, episodes_for_scenario=0, session=2,
    )
    assert p3["confidence"] == 0.25 and p3["predicted"] == "fail", p3
    # Prediction 4: weak family rate -> low/fail.
    p4 = wm.predict_probe(
        scenario="rt-x", family="repeated_task", turn_ref="s2t1",
        family_rate_value=0.333, episodes_for_scenario=6, session=2,
    )
    assert p4["bucket"] == "low" and p4["predicted"] == "fail", p4

    o1 = wm.attach_outcome(scenario="dr-x", turn_ref="s2t1", passed=True, session=2)
    assert o1["prediction_correct"] is True, o1
    o2 = wm.attach_outcome(scenario="dx-x", turn_ref="s2t1", passed=False, session=2)
    assert o2["prediction_correct"] is False, o2
    o3 = wm.attach_outcome(scenario="dr-y", turn_ref="s2t1", passed=False, session=2)
    assert o3["prediction_correct"] is True, o3  # predicted fail, actually failed
    o4 = wm.attach_outcome(scenario="rt-x", turn_ref="s2t1", passed=False, session=2)
    assert o4["prediction_correct"] is True, o4
    # Unknown probe turn -> no outcome attached, no crash.
    assert wm.attach_outcome(scenario="zz", turn_ref="s9t9", passed=True, session=9) is None

    cal = wm.calibration()
    assert cal["predictions"] == 4 and cal["outcomes"] == 4, cal
    assert cal["overall"]["accuracy"] == 0.75, cal  # 3 of 4 calls correct
    assert cal["overall"]["actual_pass_rate"] == 0.25, cal
    assert cal["by_bucket"]["high"] == {
        "n": 1, "predicted_pass_rate": 1.0, "actual_pass_rate": 1.0,
        "mean_confidence": 1.0,
    }, cal
    assert cal["by_bucket"]["medium"]["actual_pass_rate"] == 0.0, cal
    assert cal["by_bucket"]["low"] == {
        "n": 2, "predicted_pass_rate": 0.0, "actual_pass_rate": 0.0,
        "mean_confidence": round((0.25 + 0.333) / 2, 3),
    }, cal

    journal.close()
    from .events import validate_trace

    ok, errors = validate_trace(str(journal_path))
    assert ok, errors
    text = journal_path.read_text(encoding="utf-8")
    assert '"type": "worldmodel.prediction"' in text
    assert '"type": "worldmodel.outcome"' in text

    # Determinism: same inputs -> byte-identical prediction records.
    journal2 = EventJournal(str(Path(tempfile.mkdtemp()) / "t2.jsonl"), "r2")
    wm2 = WorldModel(journal2)
    q1 = wm2.predict_probe(
        scenario="dr-x", family="delayed_recall", turn_ref="s2t1",
        family_rate_value=1.0, episodes_for_scenario=4, session=2,
    )
    assert q1 == p1, (q1, p1)
    journal2.close()
    print("worldmodel selftest ok: deterministic predictions, outcomes, calibration counters")
    return 0


if __name__ == "__main__":
    raise SystemExit(_selftest())
