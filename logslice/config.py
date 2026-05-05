"""Configuration dataclass and loader for logslice."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from logslice.validator import (
    parse_datetime_arg,
    validate_output_format,
    validate_time_range,
)


@dataclass
class SliceConfig:
    """Holds all configuration for a logslice run."""

    start: Optional[datetime] = None
    end: Optional[datetime] = None
    output_format: str = "plain"
    output_file: Optional[str] = None
    timestamp_patterns: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> SliceConfig:
        """Build a SliceConfig from a plain dictionary (e.g. parsed JSON)."""
        start = parse_datetime_arg(data["start"]) if data.get("start") else None
        end = parse_datetime_arg(data["end"]) if data.get("end") else None
        validate_time_range(start, end)

        fmt = validate_output_format(data.get("output_format", "plain"))

        return cls(
            start=start,
            end=end,
            output_format=fmt,
            output_file=data.get("output_file"),
            timestamp_patterns=data.get("timestamp_patterns", []),
        )

    @classmethod
    def from_json_file(cls, path: str) -> SliceConfig:
        """Load configuration from a JSON file."""
        if not os.path.isfile(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        return cls.from_dict(data)

    def to_dict(self) -> dict:
        """Serialize config to a plain dictionary."""
        return {
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "output_format": self.output_format,
            "output_file": self.output_file,
            "timestamp_patterns": self.timestamp_patterns,
        }
