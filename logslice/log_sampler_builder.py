"""Fluent builder for LogSampler."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from logslice.log_sampler import LogSampler
from logslice.parser import LogParser
from logslice.slicer import LogSlicer
from logslice.validator import parse_datetime_arg, validate_time_range


class LogSamplerBuilder:
    """Construct a :class:`LogSampler` with a fluent interface."""

    _DEFAULT_FORMATS: List[str] = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S",
        "%b %d %H:%M:%S",
        "%d/%b/%Y:%H:%M:%S",
    ]

    def __init__(self) -> None:
        self._start: Optional[datetime] = None
        self._end: Optional[datetime] = None
        self._formats: List[str] = list(self._DEFAULT_FORMATS)
        self._max_samples: int = 100

    def with_start(self, value: str | datetime) -> "LogSamplerBuilder":
        self._start = parse_datetime_arg(value) if isinstance(value, str) else value
        return self

    def with_end(self, value: str | datetime) -> "LogSamplerBuilder":
        self._end = parse_datetime_arg(value) if isinstance(value, str) else value
        return self

    def with_timestamp_formats(self, formats: List[str]) -> "LogSamplerBuilder":
        self._formats = formats
        return self

    def with_max_samples(self, n: int) -> "LogSamplerBuilder":
        if n < 1:
            raise ValueError("max_samples must be >= 1")
        self._max_samples = n
        return self

    def build(self) -> LogSampler:
        if self._start is None:
            raise ValueError("start datetime is required")
        if self._end is None:
            raise ValueError("end datetime is required")
        validate_time_range(self._start, self._end)
        parser = LogParser(timestamp_formats=self._formats)
        slicer = LogSlicer(start=self._start, end=self._end, parser=parser)
        return LogSampler(slicer=slicer, parser=parser, max_samples=self._max_samples)
