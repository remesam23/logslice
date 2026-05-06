"""Utility for counting and reporting lines in log files by match status."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from logslice.parser import LogParser
from logslice.slicer import LogSlicer


@dataclass
class LineCountResult:
    total: int = 0
    matched: int = 0
    skipped_before: int = 0
    skipped_after: int = 0
    unparseable: int = 0

    @property
    def skipped(self) -> int:
        return self.skipped_before + self.skipped_after + self.unparseable

    def to_dict(self) -> dict:
        return {
            "total": self.total,
            "matched": self.matched,
            "skipped_before": self.skipped_before,
            "skipped_after": self.skipped_after,
            "unparseable": self.unparseable,
            "skipped": self.skipped,
        }

    def summary(self) -> str:
        return (
            f"Total: {self.total} | Matched: {self.matched} | "
            f"Skipped before: {self.skipped_before} | "
            f"Skipped after: {self.skipped_after} | "
            f"Unparseable: {self.unparseable}"
        )


class LineCounter:
    """Counts log lines in a file, categorising each by match status."""

    def __init__(self, slicer: LogSlicer, parser: LogParser):
        self._slicer = slicer
        self._parser = parser

    def count_file(self, path: str) -> LineCountResult:
        result = LineCountResult()
        with open(path, "r", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.rstrip("\n")
                result.total += 1
                ts = self._parser.extract_timestamp(line)
                if ts is None:
                    result.unparseable += 1
                    continue
                if ts < self._slicer.start:
                    result.skipped_before += 1
                elif ts > self._slicer.end:
                    result.skipped_after += 1
                else:
                    result.matched += 1
        return result
