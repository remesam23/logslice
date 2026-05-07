"""Compare two log slices and report added, removed, and common lines."""

from dataclasses import dataclass, field
from typing import List, Sequence


@dataclass
class DiffResult:
    added: List[str] = field(default_factory=list)
    removed: List[str] = field(default_factory=list)
    common: List[str] = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed)

    def to_dict(self) -> dict:
        return {
            "added": len(self.added),
            "removed": len(self.removed),
            "common": len(self.common),
            "has_changes": self.has_changes,
        }

    def summary(self) -> str:
        return (
            f"+{len(self.added)} added, "
            f"-{len(self.removed)} removed, "
            f"={len(self.common)} common"
        )


class LogDiffer:
    """Diff two sequences of log lines, preserving order context."""

    def __init__(self, strip_whitespace: bool = True):
        self._strip = strip_whitespace

    def _normalize(self, line: str) -> str:
        return line.strip() if self._strip else line

    def diff(self, baseline: Sequence[str], current: Sequence[str]) -> DiffResult:
        """Return lines added, removed, and common between baseline and current."""
        baseline_set = set(self._normalize(l) for l in baseline)
        current_set = set(self._normalize(l) for l in current)

        common = sorted(baseline_set & current_set)
        removed = sorted(baseline_set - current_set)
        added = sorted(current_set - baseline_set)

        return DiffResult(added=added, removed=removed, common=common)

    def diff_files(self, baseline_path: str, current_path: str) -> DiffResult:
        """Read two log files and diff their contents."""
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = f.readlines()
        with open(current_path, "r", encoding="utf-8") as f:
            current = f.readlines()
        return self.diff(baseline, current)
