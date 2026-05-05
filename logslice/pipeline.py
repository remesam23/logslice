"""Pipeline orchestrator that wires together parsing, slicing, and exporting."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from logslice.config import SliceConfig
from logslice.exporter import LogExporter
from logslice.parser import LogParser
from logslice.slicer import LogSlicer
from logslice.stats import SliceStats
from logslice.stats_reporter import StatsReporter
from logslice.validator import validate_time_range, validate_output_format


class Pipeline:
    """End-to-end processing pipeline for a single log slice operation."""

    def __init__(self, config: SliceConfig) -> None:
        self.config = config
        validate_time_range(config.start, config.end)
        validate_output_format(config.output_format)

        self.parser = LogParser(fmt=config.timestamp_format)
        self.slicer = LogSlicer(
            parser=self.parser,
            start=config.start,
            end=config.end,
        )
        self.exporter = LogExporter(
            output_format=config.output_format,
            output_path=config.output_path,
        )
        self.stats = SliceStats()

    # ------------------------------------------------------------------
    def run(self, log_path: str | Path) -> SliceStats:
        """Execute the pipeline against *log_path* and return statistics."""
        log_path = Path(log_path)
        entries = []

        for entry in self.slicer.filter_file(log_path):
            entries.append(entry)
            self.stats.record_match()

        # Count skipped lines (total lines minus matched entries)
        total_lines = self._count_lines(log_path)
        skipped = total_lines - len(entries)
        for _ in range(max(skipped, 0)):
            self.stats.record_skip()

        self.exporter.export(entries)
        return self.stats

    # ------------------------------------------------------------------
    def run_with_report(
        self,
        log_path: str | Path,
        report_format: str = "text",
        report_path: Optional[str] = None,
    ) -> SliceStats:
        """Run the pipeline and emit a stats report."""
        stats = self.run(log_path)
        reporter = StatsReporter(stats, output_format=report_format, output_path=report_path)
        reporter.report()
        return stats

    # ------------------------------------------------------------------
    @staticmethod
    def _count_lines(path: Path) -> int:
        try:
            with path.open("r", errors="replace") as fh:
                return sum(1 for _ in fh)
        except OSError:
            return 0
