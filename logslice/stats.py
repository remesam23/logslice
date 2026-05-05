"""Statistics collector for log slicing operations."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SliceStats:
    """Holds statistics gathered during a log slicing operation."""

    total_lines: int = 0
    matched_lines: int = 0
    skipped_before: int = 0
    skipped_after: int = 0
    unparseable_lines: int = 0
    first_matched_ts: Optional[datetime] = None
    last_matched_ts: Optional[datetime] = None
    _extra: dict = field(default_factory=dict)

    def record_match(self, ts: Optional[datetime]) -> None:
        """Record a matched log line with its timestamp."""
        self.matched_lines += 1
        if ts is not None:
            if self.first_matched_ts is None or ts < self.first_matched_ts:
                self.first_matched_ts = ts
            if self.last_matched_ts is None or ts > self.last_matched_ts:
                self.last_matched_ts = ts

    def record_skip(self, reason: str) -> None:
        """Record a skipped line with a reason ('before', 'after', 'unparseable')."""
        if reason == "before":
            self.skipped_before += 1
        elif reason == "after":
            self.skipped_after += 1
        else:
            self.unparseable_lines += 1

    @property
    def match_rate(self) -> float:
        """Fraction of total lines that matched the time range."""
        if self.total_lines == 0:
            return 0.0
        return self.matched_lines / self.total_lines

    def to_dict(self) -> dict:
        """Serialize stats to a plain dictionary."""
        return {
            "total_lines": self.total_lines,
            "matched_lines": self.matched_lines,
            "skipped_before": self.skipped_before,
            "skipped_after": self.skipped_after,
            "unparseable_lines": self.unparseable_lines,
            "match_rate": round(self.match_rate, 4),
            "first_matched_ts": self.first_matched_ts.isoformat() if self.first_matched_ts else None,
            "last_matched_ts": self.last_matched_ts.isoformat() if self.last_matched_ts else None,
        }

    def summary(self) -> str:
        """Return a human-readable summary string."""
        return (
            f"Processed {self.total_lines} lines: "
            f"{self.matched_lines} matched ({self.match_rate:.1%}), "
            f"{self.skipped_before} before range, "
            f"{self.skipped_after} after range, "
            f"{self.unparseable_lines} unparseable."
        )
