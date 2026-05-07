"""Builder for LogAnnotator with a fluent interface."""

from typing import Dict, List, Optional

from logslice.log_annotator import LogAnnotator


class LogAnnotatorBuilderError(Exception):
    pass


class LogAnnotatorBuilder:
    """Fluent builder for constructing a LogAnnotator."""

    def __init__(self) -> None:
        self._rules: Dict[str, List[str]] = {}
        self._source: Optional[str] = None

    def add_rule(self, tag: str, keywords: List[str]) -> "LogAnnotatorBuilder":
        """Add or extend a tag rule with the given keywords."""
        if not tag:
            raise LogAnnotatorBuilderError("Tag name must not be empty.")
        if not keywords:
            raise LogAnnotatorBuilderError(
                f"Keyword list for tag '{tag}' must not be empty."
            )
        existing = self._rules.get(tag, [])
        self._rules[tag] = existing + list(keywords)
        return self

    def with_source(self, source: str) -> "LogAnnotatorBuilder":
        """Set the source label for annotated entries."""
        self._source = source
        return self

    def build(self) -> LogAnnotator:
        """Build and return a configured LogAnnotator."""
        if not self._rules:
            raise LogAnnotatorBuilderError(
                "At least one annotation rule must be defined before building."
            )
        return LogAnnotator(rules=dict(self._rules), source=self._source)
