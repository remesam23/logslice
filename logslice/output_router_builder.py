"""Fluent builder for OutputRouter instances."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from logslice.formatter import BaseFormatter, JSONFormatter, PlainFormatter
from logslice.output_router import OutputRouter
from logslice.validator import validate_output_format


class OutputRouterBuilder:
    """Builds an OutputRouter with a fluent interface."""

    def __init__(self) -> None:
        self._formatter: Optional[BaseFormatter] = None
        self._output_file: Optional[Path] = None
        self._also_stdout: bool = False

    def with_format(self, fmt: str) -> "OutputRouterBuilder":
        """Set the output format ('plain' or 'json')."""
        validate_output_format(fmt)
        self._formatter = JSONFormatter() if fmt == "json" else PlainFormatter()
        return self

    def with_output_file(self, path: str) -> "OutputRouterBuilder":
        """Write output to *path*."""
        self._output_file = Path(path)
        return self

    def with_also_stdout(self, enabled: bool = True) -> "OutputRouterBuilder":
        """Also echo output to stdout even when a file is configured."""
        self._also_stdout = enabled
        return self

    def build(self) -> OutputRouter:
        """Return the configured OutputRouter."""
        return OutputRouter(
            formatter=self._formatter,
            output_file=self._output_file,
            also_stdout=self._also_stdout,
        )
