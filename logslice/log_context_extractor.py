"""Extract surrounding context lines around matched log entries."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


class ContextExtractorError(Exception):
    """Raised for invalid ContextExtractor configuration."""


@dataclass
class ContextEntry:
    """A matched line together with its surrounding context."""

    line_number: int
    matched_line: str
    before: List[str] = field(default_factory=list)
    after: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "line_number": self.line_number,
            "matched_line": self.matched_line,
            "before": self.before,
            "after": self.after,
        }

    def formatted_block(self) -> str:
        """Return a human-readable block with context markers."""
        parts = []
        for ln in self.before:
            parts.append(f"  {ln}")
        parts.append(f"> {self.matched_line}")
        for ln in self.after:
            parts.append(f"  {ln}")
        return "\n".join(parts)


class LogContextExtractor:
    """Extract *before* / *after* context lines for lines matching a predicate."""

    def __init__(self, before: int = 2, after: int = 2) -> None:
        if before < 0 or after < 0:
            raise ContextExtractorError(
                "'before' and 'after' must be non-negative integers."
            )
        self.before = before
        self.after = after

    def extract(self, lines: List[str], predicate) -> List[ContextEntry]:
        """Return ContextEntry objects for every line where predicate(line) is True.

        Args:
            lines: All log lines (already loaded into memory).
            predicate: Callable[[str], bool] – returns True for lines of interest.
        """
        results: List[ContextEntry] = []
        total = len(lines)
        for idx, line in enumerate(lines):
            if not predicate(line):
                continue
            before_lines = lines[max(0, idx - self.before): idx]
            after_lines = lines[idx + 1: min(total, idx + 1 + self.after)]
            results.append(
                ContextEntry(
                    line_number=idx + 1,  # 1-based
                    matched_line=line.rstrip("\n"),
                    before=[l.rstrip("\n") for l in before_lines],
                    after=[l.rstrip("\n") for l in after_lines],
                )
            )
        return results

    def extract_from_file(self, path: str, predicate) -> List[ContextEntry]:
        """Convenience wrapper that reads *path* and calls extract()."""
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        return self.extract(lines, predicate)
