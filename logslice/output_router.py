"""Routes filtered log output to one or more destinations (stdout, file, or both)."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional, TextIO

from logslice.formatter import BaseFormatter, PlainFormatter


class OutputRouterError(Exception):
    """Raised when output routing fails."""


class OutputRouter:
    """Writes formatted log entries to configured destinations."""

    def __init__(
        self,
        formatter: Optional[BaseFormatter] = None,
        output_file: Optional[Path] = None,
        also_stdout: bool = False,
    ) -> None:
        self.formatter = formatter or PlainFormatter()
        self.output_file = output_file
        self.also_stdout = also_stdout
        self._file_handle: Optional[TextIO] = None

    def open(self) -> None:
        """Open the output file if one is configured."""
        if self.output_file is not None:
            try:
                self._file_handle = open(self.output_file, "w", encoding="utf-8")
            except OSError as exc:
                raise OutputRouterError(
                    f"Cannot open output file '{self.output_file}': {exc}"
                ) from exc

    def close(self) -> None:
        """Close the output file handle if open."""
        if self._file_handle is not None:
            self._file_handle.close()
            self._file_handle = None

    def write(self, entries: List[dict]) -> None:
        """Format and route *entries* to all configured destinations."""
        text = self.formatter.format(entries)
        if self.output_file is not None:
            if self._file_handle is None:
                raise OutputRouterError("OutputRouter.open() must be called before write().")
            self._file_handle.write(text)
            if not text.endswith("\n"):
                self._file_handle.write("\n")
        if self.output_file is None or self.also_stdout:
            sys.stdout.write(text)
            if not text.endswith("\n"):
                sys.stdout.write("\n")

    def __enter__(self) -> "OutputRouter":
        self.open()
        return self

    def __exit__(self, *_) -> None:
        self.close()
