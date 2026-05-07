"""Deduplicates log entries based on message content within a time window."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional

from logslice.parser import LogParser


@dataclass
class DeduplicatedEntry:
    raw: str
    timestamp: Optional[datetime]
    count: int = 1
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "count": self.count,
            "first_seen": self.first_seen.isoformat() if self.first_seen else None,
            "last_seen": self.last_seen.isoformat() if self.last_seen else None,
        }


class LogDeduplicator:
    """Collapses repeated log lines that occur within a configurable time window."""

    def __init__(
        self,
        window_seconds: int = 60,
        timestamp_formats: Optional[List[str]] = None,
    ) -> None:
        self.window = timedelta(seconds=window_seconds)
        self._parser = LogParser(formats=timestamp_formats)
        self._seen: dict = {}  # message -> DeduplicatedEntry

    def _message_key(self, raw: str) -> str:
        """Strip the timestamp prefix to get a stable message key."""
        ts = self._parser.extract_timestamp(raw)
        if ts is None:
            return raw.strip()
        ts_str = ts.isoformat()
        return raw.replace(ts_str, "", 1).strip()

    def feed(self, lines: List[str]) -> List[DeduplicatedEntry]:
        """Process lines and return deduplicated entries."""
        results: List[DeduplicatedEntry] = []
        for line in lines:
            line = line.rstrip("\n")
            if not line:
                continue
            ts = self._parser.extract_timestamp(line)
            key = self._message_key(line)

            if key in self._seen:
                entry = self._seen[key]
                if ts and entry.last_seen and (ts - entry.last_seen) <= self.window:
                    entry.count += 1
                    entry.last_seen = ts
                    continue
                else:
                    results.append(self._seen.pop(key))

            new_entry = DeduplicatedEntry(
                raw=line,
                timestamp=ts,
                count=1,
                first_seen=ts,
                last_seen=ts,
            )
            self._seen[key] = new_entry

        return results

    def flush(self) -> List[DeduplicatedEntry]:
        """Return all buffered entries and clear internal state."""
        remaining = list(self._seen.values())
        self._seen.clear()
        return remaining

    def process(self, lines: List[str]) -> List[DeduplicatedEntry]:
        """Feed lines then flush; returns complete deduplicated result."""
        partial = self.feed(lines)
        return partial + self.flush()
