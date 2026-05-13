from __future__ import annotations

from typing import List, Optional

from logslice.log_threshold_alert import (
    LogThresholdAlert,
    ThresholdAlertError,
    ThresholdRule,
)


class LogThresholdAlertBuilderError(Exception):
    pass


class LogThresholdAlertBuilder:
    """Fluent builder for LogThresholdAlert."""

    def __init__(self) -> None:
        self._rules: List[ThresholdRule] = []

    def add_rule(
        self,
        name: str,
        pattern: str,
        threshold: int,
    ) -> "LogThresholdAlertBuilder":
        try:
            rule = ThresholdRule(name=name, pattern=pattern, threshold=threshold)
        except ThresholdAlertError as exc:
            raise LogThresholdAlertBuilderError(str(exc)) from exc
        self._rules.append(rule)
        return self

    def build(self) -> LogThresholdAlert:
        if not self._rules:
            raise LogThresholdAlertBuilderError(
                "At least one rule must be added before building"
            )
        return LogThresholdAlert(rules=self._rules)
