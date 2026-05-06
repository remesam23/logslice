"""Fluent builder for constructing a LogWatcher instance."""

from datetime import datetime
from typing import Optional

from logslice.parser import LogParser
from logslice.slicer import LogSlicer
from logslice.validator import parse_datetime_arg, validate_time_range
from logslice.watcher import LogWatcher

_DEFAULT_FORMATS = [
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%b %d %H:%M:%S",
]


class WatcherBuilder:
    """Build a LogWatcher with a fluent interface."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._start: Optional[datetime] = None
        self._end: Optional[datetime] = None
        self._formats = _DEFAULT_FORMATS
        self._poll_interval: float = 0.5
        self._max_idle: Optional[float] = None

    def with_start(self, value) -> "WatcherBuilder":
        self._start = parse_datetime_arg(value) if isinstance(value, str) else value
        return self

    def with_end(self, value) -> "WatcherBuilder":
        self._end = parse_datetime_arg(value) if isinstance(value, str) else value
        return self

    def with_timestamp_formats(self, formats: list) -> "WatcherBuilder":
        self._formats = formats
        return self

    def with_poll_interval(self, seconds: float) -> "WatcherBuilder":
        self._poll_interval = seconds
        return self

    def with_max_idle(self, seconds: float) -> "WatcherBuilder":
        self._max_idle = seconds
        return self

    def build(self) -> LogWatcher:
        if self._start is None:
            raise ValueError("start datetime is required")
        if self._end is None:
            raise ValueError("end datetime is required")
        validate_time_range(self._start, self._end)
        parser = LogParser(timestamp_formats=self._formats)
        slicer = LogSlicer(start=self._start, end=self._end, parser=parser)
        return LogWatcher(
            path=self._path,
            slicer=slicer,
            parser=parser,
            poll_interval=self._poll_interval,
            max_idle=self._max_idle,
        )
