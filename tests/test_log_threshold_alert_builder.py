import pytest
from logslice.log_threshold_alert import LogThresholdAlert
from logslice.log_threshold_alert_builder import (
    LogThresholdAlertBuilder,
    LogThresholdAlertBuilderError,
)


class TestLogThresholdAlertBuilder:
    def test_returns_alert_instance(self):
        alert = (
            LogThresholdAlertBuilder()
            .add_rule("errors", "ERROR", 3)
            .build()
        )
        assert isinstance(alert, LogThresholdAlert)

    def test_build_with_no_rules_raises(self):
        with pytest.raises(LogThresholdAlertBuilderError, match="rule"):
            LogThresholdAlertBuilder().build()

    def test_invalid_threshold_raises(self):
        with pytest.raises(LogThresholdAlertBuilderError):
            LogThresholdAlertBuilder().add_rule("r", "ERROR", 0)

    def test_empty_pattern_raises(self):
        with pytest.raises(LogThresholdAlertBuilderError):
            LogThresholdAlertBuilder().add_rule("r", "", 1)

    def test_multiple_rules_accepted(self):
        alert = (
            LogThresholdAlertBuilder()
            .add_rule("errors", "ERROR", 2)
            .add_rule("warns", "WARN", 5)
            .build()
        )
        lines = [
            "ERROR something",
            "ERROR again",
            "WARN minor",
        ]
        results = alert.evaluate(lines)
        assert len(results) == 2
        assert results[0].triggered is True
        assert results[1].triggered is False

    def test_chaining_returns_builder(self):
        builder = LogThresholdAlertBuilder()
        returned = builder.add_rule("r", "ERROR", 1)
        assert returned is builder
