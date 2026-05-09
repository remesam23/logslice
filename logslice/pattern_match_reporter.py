"""Reports pattern match results as plain text or JSON."""
from __future__ import annotations

import json
import sys
from typing import IO, List

from logslice.log_pattern_matcher import MatchedEntry


class PatternMatchReporterError(Exception):
    """Raised on unsupported output format."""


SUPPORTED_FORMATS = ("plain", "json")


class PatternMatchReporter:
    def __init__(self, fmt: str = "plain") -> None:
        if fmt not in SUPPORTED_FORMATS:
            raise PatternMatchReporterError(
                f"Unsupported format '{fmt}'. Choose from: {SUPPORTED_FORMATS}"
            )
        self.fmt = fmt

    def report(self, entries: List[MatchedEntry], out: IO[str] = sys.stdout) -> None:
        if self.fmt == "json":
            self._write_json(entries, out)
        else:
            self._write_plain(entries, out)

    def report_to_file(self, entries: List[MatchedEntry], path: str) -> None:
        with open(path, "w", encoding="utf-8") as fh:
            self.report(entries, out=fh)

    def _write_plain(self, entries: List[MatchedEntry], out: IO[str]) -> None:
        if not entries:
            out.write("No matches found.\n")
            return
        for entry in entries:
            group_tag = f" [{entry.group}]" if entry.group else ""
            out.write(f"{group_tag} {entry.line}\n".lstrip())

    def _write_json(self, entries: List[MatchedEntry], out: IO[str]) -> None:
        json.dump([e.to_dict() for e in entries], out, indent=2)
        out.write("\n")
