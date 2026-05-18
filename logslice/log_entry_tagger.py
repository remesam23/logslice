from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class EntryTaggerError(Exception):
    """Raised when tagging configuration is invalid."""


@dataclass
class TaggedEntry:
    line: str
    tags: List[str]
    timestamp: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "line": self.line,
            "tags": self.tags,
            "timestamp": self.timestamp,
        }


@dataclass
class TagRule:
    tag: str
    pattern: str
    case_sensitive: bool = False

    def __post_init__(self) -> None:
        if not self.tag or not self.tag.strip():
            raise EntryTaggerError("Tag name must not be empty.")
        if not self.pattern or not self.pattern.strip():
            raise EntryTaggerError("Tag pattern must not be empty.")
        flags = 0 if self.case_sensitive else re.IGNORECASE
        try:
            self._regex = re.compile(self.pattern, flags)
        except re.error as exc:
            raise EntryTaggerError(f"Invalid regex pattern '{self.pattern}': {exc}") from exc

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class LogEntryTagger:
    rules: List[TagRule]
    timestamp_formats: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.rules:
            raise EntryTaggerError("At least one TagRule is required.")

    def tag_line(self, line: str) -> TaggedEntry:
        matched_tags = [rule.tag for rule in self.rules if rule.matches(line)]
        timestamp = self._extract_timestamp(line)
        return TaggedEntry(line=line.rstrip("\n"), tags=matched_tags, timestamp=timestamp)

    def tag_lines(self, lines: List[str]) -> List[TaggedEntry]:
        return [self.tag_line(line) for line in lines if line.strip()]

    def _extract_timestamp(self, line: str) -> Optional[str]:
        for fmt in self.timestamp_formats:
            try:
                match = re.search(fmt, line)
                if match:
                    return match.group(0)
            except re.error:
                continue
        return None
