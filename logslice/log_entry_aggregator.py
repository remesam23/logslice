from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


class EntryAggregatorError(Exception):
    """Raised for invalid aggregator configuration."""


@dataclass
class AggregatedGroup:
    key: str
    count: int
    lines: List[str]
    first_line: Optional[str] = None
    last_line: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "key": self.key,
            "count": self.count,
            "first_line": self.first_line,
            "last_line": self.last_line,
            "lines": self.lines,
        }

    def summary(self) -> str:
        return f"[{self.key}] {self.count} entries"


@dataclass
class AggregationResult:
    groups: Dict[str, AggregatedGroup] = field(default_factory=dict)
    total_lines: int = 0
    unmatched_lines: int = 0

    def to_dict(self) -> dict:
        return {
            "total_lines": self.total_lines,
            "unmatched_lines": self.unmatched_lines,
            "groups": {k: v.to_dict() for k, v in self.groups.items()},
        }

    def summary(self) -> str:
        lines = [f"Total lines: {self.total_lines}", f"Unmatched: {self.unmatched_lines}"]
        for group in self.groups.values():
            lines.append(group.summary())
        return "\n".join(lines)


class LogEntryAggregator:
    """Groups log lines by a extracted key using a regex capture group."""

    def __init__(self, pattern: str, group: int = 1, keep_lines: bool = False) -> None:
        import re

        if not pattern:
            raise EntryAggregatorError("pattern must not be empty")
        try:
            self._regex = re.compile(pattern)
        except re.error as exc:
            raise EntryAggregatorError(f"invalid regex pattern: {exc}") from exc
        if group < 1:
            raise EntryAggregatorError("group index must be >= 1")
        self._group = group
        self._keep_lines = keep_lines

    def aggregate(self, lines: List[str]) -> AggregationResult:
        result = AggregationResult()
        for raw in lines:
            line = raw.rstrip("\n")
            result.total_lines += 1
            match = self._regex.search(line)
            if not match:
                result.unmatched_lines += 1
                continue
            try:
                key = match.group(self._group)
            except IndexError:
                result.unmatched_lines += 1
                continue
            if key not in result.groups:
                result.groups[key] = AggregatedGroup(
                    key=key, count=0, lines=[], first_line=line
                )
            grp = result.groups[key]
            grp.count += 1
            grp.last_line = line
            if self._keep_lines:
                grp.lines.append(line)
        return result
