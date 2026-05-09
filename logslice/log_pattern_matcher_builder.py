"""Fluent builder for LogPatternMatcher."""
from __future__ import annotations

from typing import List, Optional

from logslice.log_pattern_matcher import LogPatternMatcher, PatternMatcherError


class LogPatternMatcherBuilderError(Exception):
    """Raised when the builder is misconfigured."""


class LogPatternMatcherBuilder:
    def __init__(self) -> None:
        self._rules: List[dict] = []

    def add_regex(self, pattern: str, group: Optional[str] = None) -> "LogPatternMatcherBuilder":
        """Add a regex-based rule."""
        self._rules.append({"pattern": pattern, "group": group, "is_regex": True})
        return self

    def add_literal(self, pattern: str, group: Optional[str] = None) -> "LogPatternMatcherBuilder":
        """Add a literal substring rule."""
        self._rules.append({"pattern": pattern, "group": group, "is_regex": False})
        return self

    def build(self) -> LogPatternMatcher:
        if not self._rules:
            raise LogPatternMatcherBuilderError("At least one pattern rule is required.")
        matcher = LogPatternMatcher()
        for rule in self._rules:
            try:
                matcher.add_rule(
                    pattern=rule["pattern"],
                    group=rule["group"],
                    is_regex=rule["is_regex"],
                )
            except PatternMatcherError as exc:
                raise LogPatternMatcherBuilderError(str(exc)) from exc
        return matcher
