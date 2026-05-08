from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, Sequence

KNOWN_LEVELS = ["DEBUG", "INFO", "WARNING", "WARN", "ERROR", "CRITICAL", "FATAL"]

_LEVEL_PATTERN = re.compile(
    r"\b(DEBUG|INFO|WARNING|WARN|ERROR|CRITICAL|FATAL)\b", re.IGNORECASE
)


class SeverityFilterError(ValueError):
    """Raised when the severity filter is misconfigured."""


@dataclass
class FilteredEntry:
    line: str
    severity: Optional[str]

    def to_dict(self) -> dict:
        return {"line": self.line, "severity": self.severity}


@dataclass
class LogSeverityFilter:
    """Filters log lines by one or more severity levels."""

    levels: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        normalised = [lvl.upper() for lvl in self.levels]
        invalid = [lvl for lvl in normalised if lvl not in KNOWN_LEVELS]
        if invalid:
            raise SeverityFilterError(
                f"Unknown severity level(s): {invalid}. "
                f"Valid levels: {KNOWN_LEVELS}"
            )
        self.levels = normalised

    @staticmethod
    def extract_severity(line: str) -> Optional[str]:
        """Return the first severity token found in *line*, or None."""
        match = _LEVEL_PATTERN.search(line)
        if match:
            token = match.group(1).upper()
            # Normalise WARN -> WARNING, FATAL -> CRITICAL
            return {"WARN": "WARNING", "FATAL": "CRITICAL"}.get(token, token)
        return None

    def matches(self, line: str) -> bool:
        """Return True if *line* contains one of the configured severity levels."""
        if not self.levels:
            return True
        severity = self.extract_severity(line)
        return severity in self.levels

    def filter(self, lines: Sequence[str]) -> List[FilteredEntry]:
        """Return FilteredEntry objects for lines that pass the severity filter."""
        results: List[FilteredEntry] = []
        for line in lines:
            severity = self.extract_severity(line)
            normalised = {"WARN": "WARNING", "FATAL": "CRITICAL"}.get(
                severity or "", severity
            )
            if not self.levels or normalised in self.levels:
                results.append(FilteredEntry(line=line, severity=normalised))
        return results
