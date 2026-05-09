"""Analyzes log entry rates over time windows within a slice."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from logslice.parser import LogParser


@dataclass
class RateBucket:
    window_start: datetime
    window_end: datetime
    count: int = 0

    def to_dict(self) -> dict:
        return {
            "window_start": self.window_start.isoformat(),
            "window_end": self.window_end.isoformat(),
            "count": self.count,
        }


@dataclass
class RateResult:
    bucket_seconds: int
    buckets: List[RateBucket] = field(default_factory=list)

    @property
    def peak_bucket(self) -> Optional[RateBucket]:
        return max(self.buckets, key=lambda b: b.count, default=None)

    @property
    def total_entries(self) -> int:
        return sum(b.count for b in self.buckets)

    def to_dict(self) -> dict:
        return {
            "bucket_seconds": self.bucket_seconds,
            "total_entries": self.total_entries,
            "peak": self.peak_bucket.to_dict() if self.peak_bucket else None,
            "buckets": [b.to_dict() for b in self.buckets],
        }

    def summary(self) -> str:
        peak = self.peak_bucket
        peak_str = f"{peak.window_start.isoformat()} ({peak.count} entries)" if peak else "n/a"
        return (
            f"Total entries : {self.total_entries}\n"
            f"Bucket size   : {self.bucket_seconds}s\n"
            f"Buckets       : {len(self.buckets)}\n"
            f"Peak window   : {peak_str}"
        )


class LogRateAnalyzer:
    """Counts log entries per fixed-size time bucket."""

    def __init__(
        self,
        bucket_seconds: int = 60,
        timestamp_formats: Optional[List[str]] = None,
    ) -> None:
        if bucket_seconds <= 0:
            raise ValueError("bucket_seconds must be a positive integer")
        self.bucket_seconds = bucket_seconds
        self._parser = LogParser(formats=timestamp_formats)

    def analyze(self, lines: List[str]) -> RateResult:
        result = RateResult(bucket_seconds=self.bucket_seconds)
        buckets: Dict[datetime, RateBucket] = {}
        delta = timedelta(seconds=self.bucket_seconds)

        for line in lines:
            ts = self._parser.extract_timestamp(line)
            if ts is None:
                continue
            bucket_start = datetime(
                ts.year, ts.month, ts.day,
                ts.hour, ts.minute,
                (ts.second // self.bucket_seconds) * self.bucket_seconds,
            )
            if bucket_start not in buckets:
                buckets[bucket_start] = RateBucket(
                    window_start=bucket_start,
                    window_end=bucket_start + delta,
                )
            buckets[bucket_start].count += 1

        result.buckets = [buckets[k] for k in sorted(buckets)]
        return result

    def analyze_file(self, path: str) -> RateResult:
        with open(path, "r", errors="replace") as fh:
            return self.analyze(fh.readlines())
