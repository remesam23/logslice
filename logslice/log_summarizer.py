from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from collections import Counter

from logslice.parser import LogParser


@dataclass
class SummaryResult:
    total_lines: int = 0
    matched_lines: int = 0
    severity_counts: Dict[str, int] = field(default_factory=dict)
    top_messages: List[tuple] = field(default_factory=list)
    first_timestamp: Optional[str] = None
    last_timestamp: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "severity_counts": self.severity_counts,
            "top_messages": [{"message": m, "count": c} for m, c in self.top_messages],
            "first_timestamp": self.first_timestamp,
            "last_timestamp": self.last_timestamp,
        }

    def summary(self) -> str:
        lines = [
            f"Total lines   : {self.total_lines}",
            f"Matched lines : {self.matched_lines}",
            f"First entry   : {self.first_timestamp or 'N/A'}",
            f"Last entry    : {self.last_timestamp or 'N/A'}",
            "Severity breakdown:",
        ]
        for sev, cnt in sorted(self.severity_counts.items()):
            lines.append(f"  {sev:<10}: {cnt}")
        lines.append("Top messages:")
        for msg, cnt in self.top_messages:
            lines.append(f"  [{cnt:>4}] {msg}")
        return "\n".join(lines)


SEVERITY_KEYWORDS = ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]


class LogSummarizer:
    def __init__(
        self,
        timestamp_formats: Optional[List[str]] = None,
        top_n: int = 5,
    ) -> None:
        self._parser = LogParser(formats=timestamp_formats)
        self._top_n = top_n

    def summarize(self, lines: List[str]) -> SummaryResult:
        result = SummaryResult()
        severity_counter: Counter = Counter()
        message_counter: Counter = Counter()

        for raw in lines:
            result.total_lines += 1
            line = raw.rstrip()
            if not line:
                continue
            ts = self._parser.extract_timestamp(line)
            if ts is None:
                continue
            result.matched_lines += 1
            ts_str = ts.isoformat()
            if result.first_timestamp is None:
                result.first_timestamp = ts_str
            result.last_timestamp = ts_str

            upper = line.upper()
            for sev in SEVERITY_KEYWORDS:
                if sev in upper:
                    severity_counter[sev] += 1
                    break

            # Use text after timestamp as message key (truncated)
            msg = line[20:].strip()[:80]
            if msg:
                message_counter[msg] += 1

        result.severity_counts = dict(severity_counter)
        result.top_messages = message_counter.most_common(self._top_n)
        return result

    def summarize_file(self, path: str) -> SummaryResult:
        with open(path, "r", errors="replace") as fh:
            return self.summarize(fh.readlines())
