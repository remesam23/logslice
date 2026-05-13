from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class ThresholdAlertError(Exception):
    pass


@dataclass
class AlertResult:
    rule_name: str
    threshold: int
    matched_count: int
    triggered: bool
    matching_lines: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "rule_name": self.rule_name,
            "threshold": self.threshold,
            "matched_count": self.matched_count,
            "triggered": self.triggered,
            "matching_lines": self.matching_lines,
        }

    def summary(self) -> str:
        status = "TRIGGERED" if self.triggered else "OK"
        return (
            f"[{status}] {self.rule_name}: "
            f"{self.matched_count}/{self.threshold} matches"
        )


@dataclass
class ThresholdRule:
    name: str
    pattern: str
    threshold: int

    def __post_init__(self) -> None:
        if self.threshold < 1:
            raise ThresholdAlertError(
                f"Threshold must be >= 1, got {self.threshold}"
            )
        if not self.pattern:
            raise ThresholdAlertError("Pattern must not be empty")


class LogThresholdAlert:
    """Scans log lines and fires alerts when pattern counts exceed a threshold."""

    def __init__(self, rules: List[ThresholdRule]) -> None:
        if not rules:
            raise ThresholdAlertError("At least one rule is required")
        self._rules = rules

    def evaluate(self, lines: List[str]) -> List[AlertResult]:
        results: List[AlertResult] = []
        for rule in self._rules:
            matching = [ln for ln in lines if rule.pattern in ln]
            count = len(matching)
            results.append(
                AlertResult(
                    rule_name=rule.name,
                    threshold=rule.threshold,
                    matched_count=count,
                    triggered=count >= rule.threshold,
                    matching_lines=matching,
                )
            )
        return results
