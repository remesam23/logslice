"""Live log file watcher that emits new lines as they are appended."""

import time
import os
from typing import Iterator, Optional
from datetime import datetime

from logslice.parser import LogParser
from logslice.slicer import LogSlicer


class LogWatcher:
    """Tail a log file and yield parsed entries matching a time range."""

    def __init__(
        self,
        path: str,
        slicer: LogSlicer,
        parser: LogParser,
        poll_interval: float = 0.5,
        max_idle: Optional[float] = None,
    ) -> None:
        self.path = path
        self.slicer = slicer
        self.parser = parser
        self.poll_interval = poll_interval
        self.max_idle = max_idle

    def _open_at_end(self):
        fh = open(self.path, "r", encoding="utf-8", errors="replace")
        fh.seek(0, os.SEEK_END)
        return fh

    def watch(self) -> Iterator[dict]:
        """Yield matching log entry dicts as new lines appear."""
        fh = self._open_at_end()
        idle_time = 0.0
        try:
            while True:
                line = fh.readline()
                if not line:
                    time.sleep(self.poll_interval)
                    idle_time += self.poll_interval
                    if self.max_idle is not None and idle_time >= self.max_idle:
                        break
                    continue
                idle_time = 0.0
                entry = self.parser.parse_line(line)
                if entry and self.slicer._in_range(entry["timestamp"]):
                    yield entry
        finally:
            fh.close()
