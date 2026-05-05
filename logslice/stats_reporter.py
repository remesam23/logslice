"""Formats and outputs SliceStats in various representations."""

import json
import sys
from typing import IO

from logslice.stats import SliceStats


class StatsReporter:
    """Renders a SliceStats object to a chosen output format and destination."""

    SUPPORTED_FORMATS = ("text", "json")

    def __init__(self, fmt: str = "text", output: IO = None) -> None:
        if fmt not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported stats format '{fmt}'. "
                f"Choose one of: {self.SUPPORTED_FORMATS}"
            )
        self.fmt = fmt
        self.output = output or sys.stderr

    def report(self, stats: SliceStats) -> None:
        """Write the stats report to the configured output stream."""
        if self.fmt == "json":
            self._write_json(stats)
        else:
            self._write_text(stats)

    def _write_text(self, stats: SliceStats) -> None:
        self.output.write(stats.summary() + "\n")

    def _write_json(self, stats: SliceStats) -> None:
        self.output.write(json.dumps(stats.to_dict(), indent=2) + "\n")

    def report_to_string(self, stats: SliceStats) -> str:
        """Return the stats report as a string without writing to any stream."""
        if self.fmt == "json":
            return json.dumps(stats.to_dict(), indent=2)
        return stats.summary()
