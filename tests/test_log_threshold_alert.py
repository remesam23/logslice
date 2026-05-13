import pytest
from logslice.log_threshold_alert import (
    AlertResult,
    LogThresholdAlert,
    ThresholdAlertError,
    ThresholdRule,
)


# ---------------------------------------------------------------------------
# AlertResult
# ---------------------------------------------------------------------------

class TestAlertResult:
    def test_to_dict_keys(self):
        result = AlertResult(
            rule_name="errors",
            threshold=3,
            matched_count=5,
            triggered=True,
            matching_lines=["line1", "line2"],
        )
        keys = set(result.to_dict().keys())
        assert keys == {"rule_name", "threshold", "matched_count", "triggered", "matching_lines"}

    def test_summary_triggered(self):
        result = AlertResult("errors", 3, 5, True)
        assert "TRIGGERED" in result.summary()
        assert "errors" in result.summary()

    def test_summary_ok(self):
        result = AlertResult("warnings", 10, 2, False)
        assert "OK" in result.summary()


# ---------------------------------------------------------------------------
# ThresholdRule validation
# ---------------------------------------------------------------------------

class TestThresholdRule:
    def test_invalid_threshold_raises(self):
        with pytest.raises(ThresholdAlertError, match="Threshold"):
            ThresholdRule(name="r", pattern="ERROR", threshold=0)

    def test_empty_pattern_raises(self):
        with pytest.raises(ThresholdAlertError, match="Pattern"):
            ThresholdRule(name="r", pattern="", threshold=1)

    def test_valid_rule(self):
        rule = ThresholdRule(name="r", pattern="ERROR", threshold=1)
        assert rule.name == "r"


# ---------------------------------------------------------------------------
# LogThresholdAlert.evaluate
# ---------------------------------------------------------------------------

@pytest.fixture()
def lines():
    return [
        "2024-01-01 10:00:00 ERROR disk full",
        "2024-01-01 10:01:00 INFO all good",
        "2024-01-01 10:02:00 ERROR timeout",
        "2024-01-01 10:03:00 WARN high load",
        "2024-01-01 10:04:00 ERROR connection refused",
    ]


class TestLogThresholdAlert:
    def test_no_rules_raises(self):
        with pytest.raises(ThresholdAlertError):
            LogThresholdAlert(rules=[])

    def test_triggered_when_count_meets_threshold(self, lines):
        alert = LogThresholdAlert([
            ThresholdRule(name="errors", pattern="ERROR", threshold=3),
        ])
        results = alert.evaluate(lines)
        assert results[0].triggered is True
        assert results[0].matched_count == 3

    def test_not_triggered_below_threshold(self, lines):
        alert = LogThresholdAlert([
            ThresholdRule(name="warns", pattern="WARN", threshold=5),
        ])
        results = alert.evaluate(lines)
        assert results[0].triggered is False

    def test_matching_lines_captured(self, lines):
        alert = LogThresholdAlert([
            ThresholdRule(name="errors", pattern="ERROR", threshold=1),
        ])
        results = alert.evaluate(lines)
        assert len(results[0].matching_lines) == 3

    def test_multiple_rules_evaluated_independently(self, lines):
        alert = LogThresholdAlert([
            ThresholdRule(name="errors", pattern="ERROR", threshold=2),
            ThresholdRule(name="info", pattern="INFO", threshold=2),
        ])
        results = alert.evaluate(lines)
        assert results[0].triggered is True
        assert results[1].triggered is False

    def test_empty_lines_returns_untriggered(self):
        alert = LogThresholdAlert([
            ThresholdRule(name="errors", pattern="ERROR", threshold=1),
        ])
        results = alert.evaluate([])
        assert results[0].triggered is False
        assert results[0].matched_count == 0
