"""Builder for LogDeduplicator with a fluent API."""

from typing import List, Optional

from logslice.log_deduplicator import LogDeduplicator


class LogDeduplicatorBuilderError(ValueError):
    pass


class LogDeduplicatorBuilder:
    """Fluent builder for constructing a LogDeduplicator."""

    _DEFAULT_WINDOW = 60

    def __init__(self) -> None:
        self._window_seconds: int = self._DEFAULT_WINDOW
        self._timestamp_formats: Optional[List[str]] = None

    def with_window(self, seconds: int) -> "LogDeduplicatorBuilder":
        """Set the deduplication time window in seconds."""
        if seconds <= 0:
            raise LogDeduplicatorBuilderError(
                f"window_seconds must be positive, got {seconds}"
            )
        self._window_seconds = seconds
        return self

    def with_timestamp_formats(self, formats: List[str]) -> "LogDeduplicatorBuilder":
        """Override the timestamp formats used for parsing."""
        if not formats:
            raise LogDeduplicatorBuilderError("formats list must not be empty")
        self._timestamp_formats = formats
        return self

    def build(self) -> LogDeduplicator:
        """Construct and return the configured LogDeduplicator."""
        return LogDeduplicator(
            window_seconds=self._window_seconds,
            timestamp_formats=self._timestamp_formats,
        )
