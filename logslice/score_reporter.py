from __future__ import annotations

import json
from typing import IO, List

from logslice.log_entry_scorer import ScoredEntry


class ScoreReporterError(ValueError):
    pass


class ScoreReporter:
    def __init__(self, entries: List[ScoredEntry]) -> None:
        self._entries = entries

    def report(self, fmt: str = "text", stream: IO[str] | None = None) -> None:
        import sys

        out = stream or sys.stdout
        if fmt == "json":
            self._write_json(out)
        elif fmt == "text":
            self._write_text(out)
        else:
            raise ScoreReporterError(f"Unsupported format: '{fmt}'. Use 'text' or 'json'.")

    def report_to_file(self, path: str, fmt: str = "text") -> None:
        with open(path, "w", encoding="utf-8") as fh:
            self.report(fmt=fmt, stream=fh)

    def _write_text(self, out: IO[str]) -> None:
        if not self._entries:
            out.write("No scored entries.\n")
            return
        for entry in self._entries:
            rules = ", ".join(entry.matched_rules) if entry.matched_rules else "none"
            out.write(
                f"[score={entry.total_score:.2f}] [rules={rules}] {entry.line}\n"
            )

    def _write_json(self, out: IO[str]) -> None:
        json.dump([e.to_dict() for e in self._entries], out, indent=2)
        out.write("\n")
