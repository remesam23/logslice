"""Exporter module for writing filtered log output to files or stdout."""

import sys
import json
from pathlib import Path
from typing import Iterable, Union, Optional

from logslice.formatter import BaseFormatter, PlainFormatter, JSONFormatter


class LogExporter:
    """Exports filtered log entries using a formatter to a file or stdout."""

    FORMATS = {
        "plain": PlainFormatter,
        "json": JSONFormatter,
    }

    def __init__(
        self,
        fmt: str = "plain",
        output_path: Optional[Union[str, Path]] = None,
    ):
        """
        Initialize the exporter.

        :param fmt: Output format, one of 'plain' or 'json'.
        :param output_path: Path to write output. If None, writes to stdout.
        """
        if fmt not in self.FORMATS:
            raise ValueError(f"Unsupported format '{fmt}'. Choose from: {list(self.FORMATS)}.")

        self.formatter: BaseFormatter = self.FORMATS[fmt]()
        self.output_path = Path(output_path) if output_path else None

    def export(self, entries: Iterable[dict]) -> int:
        """
        Export log entries.

        :param entries: Iterable of parsed log entry dicts.
        :returns: Number of entries exported.
        """
        lines = [self.formatter.format(entry) for entry in entries]
        count = len(lines)

        if self.output_path:
            self.output_path.parent.mkdir(parents=True, exist_ok=True)
            with self.output_path.open("w", encoding="utf-8") as fh:
                fh.write("\n".join(lines))
                if lines:
                    fh.write("\n")
        else:
            for line in lines:
                sys.stdout.write(line + "\n")

        return count
