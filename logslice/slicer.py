"""Time-range filtering logic for log streams."""

from datetime import datetime
from typing import Iterator, Optional

from logslice.parser import LogParser


class LogSlicer:
    """Filters log lines by a start/end time range."""

    def __init__(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        parser: Optional[LogParser] = None,
        include_unparsed: bool = False,
    ):
        """
        Args:
            start: Inclusive start datetime. None means no lower bound.
            end: Inclusive end datetime. None means no upper bound.
            parser: LogParser instance. Defaults to auto-detection parser.
            include_unparsed: If True, lines without a timestamp are always included.
        """
        self.start = start
        self.end = end
        self.parser = parser or LogParser()
        self.include_unparsed = include_unparsed

    def _in_range(self, ts: Optional[datetime]) -> bool:
        """Return True if the timestamp falls within [start, end]."""
        if ts is None:
            return self.include_unparsed
        if self.start and ts < self.start:
            return False
        if self.end and ts > self.end:
            return False
        return True

    def filter_lines(self, lines: Iterator[str]) -> Iterator[dict]:
        """Yield parsed line dicts that fall within the configured time range."""
        for line in lines:
            parsed = self.parser.parse_line(line)
            if self._in_range(parsed['timestamp']):
                yield parsed

    def filter_file(self, filepath: str) -> Iterator[dict]:
        """Open a file and yield matching log line dicts."""
        with open(filepath, 'r', encoding='utf-8', errors='replace') as fh:
            yield from self.filter_lines(fh)
