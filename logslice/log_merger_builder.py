"""Fluent builder for LogMerger."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from logslice.log_merger import LogMerger


class LogMergerBuilderError(ValueError):
    pass


class LogMergerBuilder:
    """Build a LogMerger using a fluent interface."""

    def __init__(self) -> None:
        self._paths: List[Path] = []
        self._timestamp_formats: Optional[List[str]] = None

    def add_file(self, path: str) -> "LogMergerBuilder":
        """Add a log file to merge."""
        resolved = Path(path)
        if not resolved.exists():
            raise LogMergerBuilderError(f"File not found: {path}")
        self._paths.append(resolved)
        return self

    def add_files(self, paths: List[str]) -> "LogMergerBuilder":
        """Add multiple log files to merge."""
        for p in paths:
            self.add_file(p)
        return self

    def with_timestamp_formats(self, formats: List[str]) -> "LogMergerBuilder":
        """Override the timestamp formats used for parsing."""
        self._timestamp_formats = list(formats)
        return self

    def build(self) -> LogMerger:
        """Build and return the LogMerger."""
        if not self._paths:
            raise LogMergerBuilderError("At least one log file must be added.")
        return LogMerger(
            paths=self._paths,
            timestamp_formats=self._timestamp_formats,
        )
