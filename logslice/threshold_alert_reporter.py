from __future__ import annotations

import json
from typing import List, TextIO
import sys

from logslice.log_threshold_alert import AlertResult


class ThresholdAlertReporterError(Exception):
    pass


class ThresholdAlertReporter:
    """Writes AlertResult lists as plain-text or JSON."""

    def __init__(self, fmt: str = "plain") -> None:
        if fmt not in ("plain", "json"):
            raise ThresholdAlertReporterError(
                f"Unsupported format: {fmt!r}. Use 'plain' or 'json'."
            )
        self._fmt = fmt

    def report(self, results: List[AlertResult], stream: TextIO = sys.stdout) -> None:
        if self._fmt == "json":
            self._write_json(results, stream)
        else:
            self._write_plain(results, stream)

    def report_to_file(self, results: List[AlertResult], path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            self.report(results, fh)

    def _write_plain(self, results: List[AlertResult], stream: TextIO) -> None:
        for result in results:
            stream.write(result.summary() + "\n")
            if result.triggered:
                for line in result.matching_lines:
                    stream.write(f"  > {line}\n")

    def _write_json(self, results: List[AlertResult], stream: TextIO) -> None:
        payload = [r.to_dict() for r in results]
        stream.write(json.dumps(payload, indent=2) + "\n")
