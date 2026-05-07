"""Format and write DiffResult output to a stream or file."""

import json
import sys
from typing import IO

from logslice.log_differ import DiffResult


class DiffReporterError(ValueError):
    pass


SUPPORTED_FORMATS = ("plain", "json")


class DiffReporter:
    """Render a DiffResult in plain-text or JSON format."""

    def __init__(self, fmt: str = "plain"):
        if fmt not in SUPPORTED_FORMATS:
            raise DiffReporterError(
                f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}"
            )
        self._fmt = fmt

    def report(self, result: DiffResult, stream: IO[str] | None = None) -> None:
        """Write the diff report to *stream* (defaults to stdout)."""
        out = stream or sys.stdout
        if self._fmt == "json":
            self._write_json(result, out)
        else:
            self._write_plain(result, out)

    def report_to_file(self, result: DiffResult, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            self.report(result, stream=f)

    def _write_plain(self, result: DiffResult, out: IO[str]) -> None:
        out.write(f"Summary: {result.summary()}\n")
        if result.removed:
            out.write("--- removed ---\n")
            for line in result.removed:
                out.write(f"  - {line}\n")
        if result.added:
            out.write("+++ added +++\n")
            for line in result.added:
                out.write(f"  + {line}\n")
        if not result.has_changes:
            out.write("No differences found.\n")

    def _write_json(self, result: DiffResult, out: IO[str]) -> None:
        payload = {
            "summary": result.to_dict(),
            "added": result.added,
            "removed": result.removed,
            "common": result.common,
        }
        json.dump(payload, out, indent=2)
        out.write("\n")
