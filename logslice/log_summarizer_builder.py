from __future__ import annotations

from typing import List, Optional

from logslice.log_summarizer import LogSummarizer


class LogSummarizerBuilderError(ValueError):
    pass


class LogSummarizerBuilder:
    """Fluent builder for :class:`LogSummarizer`."""

    def __init__(self) -> None:
        self._timestamp_formats: Optional[List[str]] = None
        self._top_n: int = 5

    def with_timestamp_formats(self, formats: List[str]) -> "LogSummarizerBuilder":
        """Override the timestamp formats used during parsing."""
        if not formats:
            raise LogSummarizerBuilderError("formats list must not be empty")
        self._timestamp_formats = list(formats)
        return self

    def with_top_n(self, n: int) -> "LogSummarizerBuilder":
        """Set how many top messages to include in the summary."""
        if n < 1:
            raise LogSummarizerBuilderError("top_n must be at least 1")
        self._top_n = n
        return self

    def build(self) -> LogSummarizer:
        """Construct and return a configured :class:`LogSummarizer`."""
        return LogSummarizer(
            timestamp_formats=self._timestamp_formats,
            top_n=self._top_n,
        )
