"""Report session-split results as plain text or JSON."""
from __future__ import annotations

import json
from typing import List, TextIO

from logslice.log_session_splitter import LogSession


class SessionSplitReporterError(Exception):
    """Raised on invalid reporter configuration."""


class SessionSplitReporter:
    """Write a human-readable or machine-readable summary of log sessions."""

    FORMATS = ("text", "json")

    def __init__(self, fmt: str = "text") -> None:
        if fmt not in self.FORMATS:
            raise SessionSplitReporterError(
                f"Unknown format '{fmt}'. Choose from: {self.FORMATS}"
            )
        self._fmt = fmt

    def report(self, sessions: List[LogSession], stream: TextIO) -> None:
        """Write session summary to *stream*."""
        if self._fmt == "json":
            self._write_json(sessions, stream)
        else:
            self._write_text(sessions, stream)

    def report_to_file(self, sessions: List[LogSession], path: str) -> None:
        """Write session summary to a file at *path*."""
        try:
            with open(path, "w", encoding="utf-8") as fh:
                self.report(sessions, fh)
        except OSError as exc:
            raise SessionSplitReporterError(
                f"Cannot write report to '{path}'"
            ) from exc

    # ------------------------------------------------------------------
    # private helpers
    # ------------------------------------------------------------------

    def _write_text(self, sessions: List[LogSession], stream: TextIO) -> None:
        stream.write(f"Sessions found: {len(sessions)}\n")
        for s in sessions:
            d = s.to_dict()
            dur = (
                f"{d['duration_seconds']:.1f}s"
                if d["duration_seconds"] is not None
                else "unknown"
            )
            stream.write(
                f"  [{d['index']}] entries={d['entry_count']}  "
                f"start={d['start']}  end={d['end']}  duration={dur}\n"
            )

    def _write_json(self, sessions: List[LogSession], stream: TextIO) -> None:
        payload = {
            "session_count": len(sessions),
            "sessions": [s.to_dict() for s in sessions],
        }
        json.dump(payload, stream, indent=2)
        stream.write("\n")
