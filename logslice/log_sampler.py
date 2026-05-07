"""LogSampler: extract a representative sample of log entries within a time range."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogParser
from logslice.slicer import LogSlicer


@dataclass
class SampleResult:
    entries: List[dict] = field(default_factory=list)
    total_matched: int = 0
    sample_size: int = 0
    step: int = 1

    @property
    def is_exact(self) -> bool:
        """True when the sample contains every matched entry."""
        return self.total_matched <= self.sample_size

    def to_dict(self) -> dict:
        return {
            "total_matched": self.total_matched,
            "sample_size": self.sample_size,
            "step": self.step,
            "is_exact": self.is_exact,
            "entries": self.entries,
        }


class LogSampler:
    """Filters a log file by time range and returns an evenly-spaced sample."""

    def __init__(
        self,
        slicer: LogSlicer,
        parser: LogParser,
        max_samples: int = 100,
    ) -> None:
        if max_samples < 1:
            raise ValueError("max_samples must be >= 1")
        self.slicer = slicer
        self.parser = parser
        self.max_samples = max_samples

    def sample_file(self, path: str) -> SampleResult:
        """Read *path*, filter by range, and return a sampled SampleResult."""
        matched: List[dict] = []
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.rstrip("\n")
                parsed = self.parser.parse_line(line)
                if parsed and self.slicer._in_range(parsed["timestamp"]):
                    matched.append(parsed)

        total = len(matched)
        if total == 0:
            return SampleResult(entries=[], total_matched=0, sample_size=0, step=1)

        step = max(1, math.ceil(total / self.max_samples))
        sampled = matched[::step]

        return SampleResult(
            entries=sampled,
            total_matched=total,
            sample_size=len(sampled),
            step=step,
        )

    def sample_lines(self, lines: List[str]) -> SampleResult:
        """Filter and sample an already-loaded list of raw log lines.

        Useful when the caller has already read the file into memory or is
        working with in-memory log data (e.g. from a stream or test fixture).
        """
        matched: List[dict] = []
        for line in lines:
            line = line.rstrip("\n")
            parsed = self.parser.parse_line(line)
            if parsed and self.slicer._in_range(parsed["timestamp"]):
                matched.append(parsed)

        total = len(matched)
        if total == 0:
            return SampleResult(entries=[], total_matched=0, sample_size=0, step=1)

        step = max(1, math.ceil(total / self.max_samples))
        sampled = matched[::step]

        return SampleResult(
            entries=sampled,
            total_matched=total,
            sample_size=len(sampled),
            step=step,
        )
