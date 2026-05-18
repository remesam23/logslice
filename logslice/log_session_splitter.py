"""Split a log file into sessions based on inactivity gaps between entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from logslice.parser import LogParser


class SessionSplitterError(Exception):
    """Raised when session splitting cannot proceed."""


@dataclass
class LogSession:
    index: int
    entries: List[str] = field(default_factory=list)
    start: Optional[datetime] = None
    end: Optional[datetime] = None

    @property
    def duration(self) -> Optional[timedelta]:
        if self.start and self.end:
            return self.end - self.start
        return None

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "entry_count": len(self.entries),
            "start": self.start.isoformat() if self.start else None,
            "end": self.end.isoformat() if self.end else None,
            "duration_seconds": self.duration.total_seconds() if self.duration else None,
        }


class LogSessionSplitter:
    """Groups log lines into sessions separated by inactivity gaps."""

    def __init__(
        self,
        gap: timedelta,
        timestamp_formats: Optional[List[str]] = None,
    ) -> None:
        if gap.total_seconds() <= 0:
            raise SessionSplitterError("gap must be a positive timedelta")
        self._gap = gap
        self._parser = LogParser(formats=timestamp_formats)

    def split(self, lines: List[str]) -> List[LogSession]:
        sessions: List[LogSession] = []
        current: Optional[LogSession] = None
        last_ts: Optional[datetime] = None

        for line in lines:
            stripped = line.rstrip("\n")
            if not stripped:
                continue
            ts = self._parser.extract_timestamp(stripped)
            if current is None:
                current = LogSession(index=0, start=ts, end=ts)
            elif ts and last_ts and (ts - last_ts) > self._gap:
                sessions.append(current)
                current = LogSession(index=len(sessions), start=ts, end=ts)
            current.entries.append(stripped)
            if ts:
                if current.start is None:
                    current.start = ts
                current.end = ts
            last_ts = ts if ts else last_ts

        if current is not None:
            sessions.append(current)
        return sessions

    def split_file(self, path: str) -> List[LogSession]:
        try:
            with open(path, "r", encoding="utf-8", errors="replace") as fh:
                return self.split(fh.readlines())
        except OSError as exc:
            raise SessionSplitterError(f"Cannot read file: {path}") from exc
