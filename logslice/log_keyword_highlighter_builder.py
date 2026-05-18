from __future__ import annotations

from typing import List, Optional

from logslice.log_keyword_highlighter import (
    KeywordHighlighterError,
    KeywordRule,
    LogKeywordHighlighter,
)


class LogKeywordHighlighterBuilderError(Exception):
    pass


class LogKeywordHighlighterBuilder:
    def __init__(self) -> None:
        self._rules: List[KeywordRule] = []
        self._default_marker_open: str = ">>>"
        self._default_marker_close: str = "<<<"
        self._case_sensitive: bool = False

    def with_markers(self, open_marker: str, close_marker: str) -> "LogKeywordHighlighterBuilder":
        if not open_marker or not close_marker:
            raise LogKeywordHighlighterBuilderError("Markers must not be empty.")
        self._default_marker_open = open_marker
        self._default_marker_close = close_marker
        return self

    def with_case_sensitive(self, value: bool = True) -> "LogKeywordHighlighterBuilder":
        self._case_sensitive = value
        return self

    def add_keyword(self, keyword: str, case_sensitive: Optional[bool] = None) -> "LogKeywordHighlighterBuilder":
        cs = case_sensitive if case_sensitive is not None else self._case_sensitive
        try:
            rule = KeywordRule(
                keyword=keyword,
                case_sensitive=cs,
                marker_open=self._default_marker_open,
                marker_close=self._default_marker_close,
            )
        except KeywordHighlighterError as exc:
            raise LogKeywordHighlighterBuilderError(str(exc)) from exc
        self._rules.append(rule)
        return self

    def add_keywords(self, keywords: List[str]) -> "LogKeywordHighlighterBuilder":
        for kw in keywords:
            self.add_keyword(kw)
        return self

    def build(self) -> LogKeywordHighlighter:
        if not self._rules:
            raise LogKeywordHighlighterBuilderError(
                "At least one keyword must be added before building."
            )
        return LogKeywordHighlighter(rules=self._rules)
