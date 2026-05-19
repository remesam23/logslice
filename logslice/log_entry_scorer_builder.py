from __future__ import annotations

from typing import List, Optional

from logslice.log_entry_scorer import EntryScorerError, LogEntryScorer, ScoringRule


class LogEntryScorerBuilderError(ValueError):
    pass


class LogEntryScorerBuilder:
    def __init__(self) -> None:
        self._rules: List[ScoringRule] = []
        self._threshold: Optional[float] = None

    def add_rule(self, name: str, pattern: str, score: float) -> "LogEntryScorerBuilder":
        try:
            rule = ScoringRule(name=name, pattern=pattern, score=score)
        except EntryScorerError as exc:
            raise LogEntryScorerBuilderError(str(exc)) from exc
        self._rules.append(rule)
        return self

    def with_threshold(self, threshold: float) -> "LogEntryScorerBuilder":
        if not isinstance(threshold, (int, float)):
            raise LogEntryScorerBuilderError("Threshold must be a numeric value")
        self._threshold = float(threshold)
        return self

    def build(self) -> LogEntryScorer:
        if not self._rules:
            raise LogEntryScorerBuilderError(
                "Cannot build LogEntryScorer: no rules have been added"
            )
        return LogEntryScorer(rules=list(self._rules), threshold=self._threshold)
