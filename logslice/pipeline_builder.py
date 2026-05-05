"""Fluent builder for constructing a Pipeline from individual arguments."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from logslice.config import SliceConfig
from logslice.pipeline import Pipeline
from logslice.validator import parse_datetime_arg


class PipelineBuilder:
    """Fluent interface to construct a :class:`Pipeline` step by step."""

    def __init__(self) -> None:
        self._start: Optional[datetime] = None
        self._end: Optional[datetime] = None
        self._fmt: Optional[str] = None
        self._output_format: str = "plain"
        self._output_path: Optional[str] = None

    # ------------------------------------------------------------------
    def with_start(self, value: str | datetime) -> "PipelineBuilder":
        self._start = parse_datetime_arg(value) if isinstance(value, str) else value
        return self

    def with_end(self, value: str | datetime) -> "PipelineBuilder":
        self._end = parse_datetime_arg(value) if isinstance(value, str) else value
        return self

    def with_timestamp_format(self, fmt: str) -> "PipelineBuilder":
        self._fmt = fmt
        return self

    def with_output_format(self, fmt: str) -> "PipelineBuilder":
        self._output_format = fmt
        return self

    def with_output_path(self, path: str) -> "PipelineBuilder":
        self._output_path = path
        return self

    # ------------------------------------------------------------------
    def build(self) -> Pipeline:
        """Validate collected options and return a ready :class:`Pipeline`."""
        if self._start is None or self._end is None:
            raise ValueError("Both 'start' and 'end' datetimes are required.")

        config_data: dict = {
            "start": self._start,
            "end": self._end,
            "output_format": self._output_format,
        }
        if self._fmt:
            config_data["timestamp_format"] = self._fmt
        if self._output_path:
            config_data["output_path"] = self._output_path

        config = SliceConfig.from_dict(config_data)
        return Pipeline(config)
