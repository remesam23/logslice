from __future__ import annotations

from typing import List, Optional

from logslice.log_entry_classifier import (
    ClassifierRule,
    EntryClassifierError,
    LogEntryClassifier,
)


class LogEntryClassifierBuilderError(Exception):
    pass


class LogEntryClassifierBuilder:
    """Fluent builder for :class:`LogEntryClassifier`."""

    def __init__(self) -> None:
        self._rules: List[ClassifierRule] = []

    def add_rule(
        self,
        name: str,
        pattern: str,
        category: str,
        confidence: float = 1.0,
    ) -> "LogEntryClassifierBuilder":
        """Append a classification rule.  Rules are evaluated in insertion order."""
        try:
            rule = ClassifierRule(
                name=name,
                pattern=pattern,
                category=category,
                confidence=confidence,
            )
        except EntryClassifierError as exc:
            raise LogEntryClassifierBuilderError(str(exc)) from exc
        self._rules.append(rule)
        return self

    def add_rules(self, rules: List[ClassifierRule]) -> "LogEntryClassifierBuilder":
        """Bulk-add pre-constructed :class:`ClassifierRule` objects."""
        for rule in rules:
            self._rules.append(rule)
        return self

    def build(self) -> LogEntryClassifier:
        if not self._rules:
            raise LogEntryClassifierBuilderError(
                "Cannot build a classifier with no rules."
            )
        return LogEntryClassifier(rules=self._rules)
