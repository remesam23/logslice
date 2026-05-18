"""Fluent builder for LogSessionSplitter."""
from __future__ import annotations

from datetime import timedelta
from typing import List, Optional

from logslice.log_session_splitter import LogSessionSplitter, SessionSplitterError


class LogSessionSplitterBuilderError(Exception):
    """Raised when the builder is misconfigured."""


class LogSessionSplitterBuilder:
    """Build a :class:`LogSessionSplitter` with a fluent interface."""

    def __init__(self) -> None:
        self._gap_seconds: Optional[float] = None
        self._formats: List[str] = []

    def with_gap_seconds(self, seconds: float) -> "LogSessionSplitterBuilder":
        """Set the inactivity gap in seconds that defines a new session."""
        if seconds <= 0:
            raise LogSessionSplitterBuilderError(
                "gap_seconds must be greater than zero"
            )
        self._gap_seconds = seconds
        return self

    def with_timestamp_formats(self, formats: List[str]) -> "LogSessionSplitterBuilder":
        """Provide custom timestamp format strings for the underlying parser."""
        self._formats = list(formats)
        return self

    def build(self) -> LogSessionSplitter:
        """Return a configured :class:`LogSessionSplitter`."""
        if self._gap_seconds is None:
            raise LogSessionSplitterBuilderError(
                "gap_seconds is required; call with_gap_seconds() before build()"
            )
        try:
            return LogSessionSplitter(
                gap=timedelta(seconds=self._gap_seconds),
                timestamp_formats=self._formats or None,
            )
        except SessionSplitterError as exc:
            raise LogSessionSplitterBuilderError(str(exc)) from exc
