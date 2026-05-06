"""Pipeline variant that uses OutputRouter for flexible output destinations."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from logslice.config import SliceConfig
from logslice.output_router import OutputRouter
from logslice.output_router_builder import OutputRouterBuilder
from logslice.parser import LogParser
from logslice.slicer import LogSlicer
from logslice.stats import SliceStats


class RoutedPipeline:
    """Filters a log file and routes output via an OutputRouter."""

    def __init__(self, config: SliceConfig, router: OutputRouter) -> None:
        self.config = config
        self.router = router

    # ------------------------------------------------------------------
    # Factory helpers
    # ------------------------------------------------------------------

    @classmethod
    def to_stdout(cls, config: SliceConfig, fmt: str = "plain") -> "RoutedPipeline":
        """Create a pipeline that writes to stdout."""
        router = OutputRouterBuilder().with_format(fmt).build()
        return cls(config, router)

    @classmethod
    def to_file(
        cls,
        config: SliceConfig,
        path: str,
        fmt: str = "plain",
        also_stdout: bool = False,
    ) -> "RoutedPipeline":
        """Create a pipeline that writes to *path*."""
        router = (
            OutputRouterBuilder()
            .with_format(fmt)
            .with_output_file(path)
            .with_also_stdout(also_stdout)
            .build()
        )
        return cls(config, router)

    # ------------------------------------------------------------------
    # Execution
    # ------------------------------------------------------------------

    def run(self) -> SliceStats:
        """Execute the pipeline and return statistics."""
        cfg = self.config
        parser = LogParser(timestamp_formats=cfg.timestamp_formats)
        slicer = LogSlicer(start=cfg.start, end=cfg.end)
        stats = SliceStats()

        entries = []
        with open(cfg.log_file, "r", encoding="utf-8", errors="replace") as fh:
            for raw_line in fh:
                line = raw_line.rstrip("\n")
                parsed = parser.parse_line(line)
                if parsed and slicer._in_range(parsed["timestamp"]):
                    entries.append(parsed)
                    stats.record_match()
                else:
                    stats.record_skip(reason="out_of_range")

        with self.router:
            self.router.write(entries)

        return stats
