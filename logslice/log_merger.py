"""Merge and sort log entries from multiple files by timestamp."""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogParser


@dataclass(order=True)
class _HeapEntry:
    timestamp: datetime
    source: str = field(compare=False)
    line: str = field(compare=False)


@dataclass
class MergedEntry:
    timestamp: Optional[datetime]
    source: str
    line: str

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "source": self.source,
            "line": self.line.rstrip("\n"),
        }


class LogMerger:
    """Merge log lines from multiple files, yielding them in timestamp order."""

    def __init__(
        self,
        paths: List[Path],
        timestamp_formats: Optional[List[str]] = None,
    ) -> None:
        self.paths = [Path(p) for p in paths]
        self._parser = LogParser(formats=timestamp_formats)

    def _iter_file(self, path: Path) -> Iterator[_HeapEntry]:
        with path.open("r", errors="replace") as fh:
            for line in fh:
                ts = self._parser.extract_timestamp(line)
                if ts is not None:
                    yield _HeapEntry(timestamp=ts, source=str(path), line=line)

    def merge(self) -> Iterable[MergedEntry]:
        """Yield MergedEntry objects sorted by timestamp across all files."""
        iterators = [self._iter_file(p) for p in self.paths]
        for heap_entry in heapq.merge(*iterators):
            yield MergedEntry(
                timestamp=heap_entry.timestamp,
                source=heap_entry.source,
                line=heap_entry.line,
            )
