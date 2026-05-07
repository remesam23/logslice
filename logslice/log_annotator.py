"""Annotates log entries with metadata tags based on keyword rules."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class AnnotatedEntry:
    raw_line: str
    timestamp: Optional[str]
    tags: List[str] = field(default_factory=list)
    source: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "raw_line": self.raw_line,
            "timestamp": self.timestamp,
            "tags": self.tags,
            "source": self.source,
        }


class LogAnnotator:
    """Applies keyword-based tag rules to parsed log entries."""

    def __init__(self, rules: Dict[str, List[str]], source: Optional[str] = None):
        """
        Args:
            rules: Mapping of tag name to list of keywords that trigger it.
            source: Optional label for the log source (e.g. filename).
        """
        self.rules = rules
        self.source = source

    def annotate(self, line: str, timestamp: Optional[str] = None) -> AnnotatedEntry:
        """Return an AnnotatedEntry with all matching tags applied."""
        tags = [
            tag
            for tag, keywords in self.rules.items()
            if any(kw.lower() in line.lower() for kw in keywords)
        ]
        return AnnotatedEntry(
            raw_line=line,
            timestamp=timestamp,
            tags=tags,
            source=self.source,
        )

    def annotate_many(
        self, lines: List[str], timestamps: Optional[List[Optional[str]]] = None
    ) -> List[AnnotatedEntry]:
        """Annotate a list of lines, optionally pairing each with a timestamp."""
        if timestamps is None:
            timestamps = [None] * len(lines)
        return [self.annotate(line, ts) for line, ts in zip(lines, timestamps)]
