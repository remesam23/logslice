"""Tests for LogDeduplicator and LogDeduplicatorBuilder."""

import pytest

from logslice.log_deduplicator import DeduplicatedEntry, LogDeduplicator
from logslice.log_deduplicator_builder import (
    LogDeduplicatorBuilder,
    LogDeduplicatorBuilderError,
)


LINE_A = "2024-01-01T10:00:00 ERROR disk full"
LINE_A2 = "2024-01-01T10:00:30 ERROR disk full"
LINE_A3 = "2024-01-01T10:02:00 ERROR disk full"  # outside 60s window from A
LINE_B = "2024-01-01T10:00:05 INFO  heartbeat ok"
LINE_B2 = "2024-01-01T10:00:10 INFO  heartbeat ok"


@pytest.fixture
def dedup() -> LogDeduplicator:
    return LogDeduplicator(window_seconds=60)


class TestDeduplicatedEntry:
    def test_to_dict_keys(self):
        from datetime import datetime
        entry = DeduplicatedEntry(
            raw=LINE_A,
            timestamp=datetime(2024, 1, 1, 10, 0, 0),
            count=3,
            first_seen=datetime(2024, 1, 1, 10, 0, 0),
            last_seen=datetime(2024, 1, 1, 10, 0, 30),
        )
        d = entry.to_dict()
        assert set(d.keys()) == {"raw", "timestamp", "count", "first_seen", "last_seen"}

    def test_to_dict_count(self):
        from datetime import datetime
        entry = DeduplicatedEntry(raw=LINE_A, timestamp=None, count=5)
        assert entry.to_dict()["count"] == 5

    def test_to_dict_none_timestamp(self):
        entry = DeduplicatedEntry(raw="no timestamp line", timestamp=None)
        assert entry.to_dict()["timestamp"] is None


class TestLogDeduplicator:
    def test_unique_lines_all_returned(self, dedup):
        results = dedup.process([LINE_A, LINE_B])
        assert len(results) == 2

    def test_duplicate_within_window_collapsed(self, dedup):
        results = dedup.process([LINE_A, LINE_A2])
        assert len(results) == 1
        assert results[0].count == 2

    def test_duplicate_outside_window_not_collapsed(self, dedup):
        results = dedup.process([LINE_A, LINE_A3])
        assert len(results) == 2
        assert results[0].count == 1
        assert results[1].count == 1

    def test_count_accumulates_correctly(self, dedup):
        results = dedup.process([LINE_B, LINE_B2])
        assert results[0].count == 2

    def test_flush_clears_state(self, dedup):
        dedup.feed([LINE_A])
        flushed = dedup.flush()
        assert len(flushed) == 1
        assert len(dedup._seen) == 0

    def test_empty_input_returns_empty(self, dedup):
        assert dedup.process([]) == []

    def test_blank_lines_skipped(self, dedup):
        results = dedup.process(["", "   ", "\n"])
        assert results == []

    def test_first_and_last_seen_set(self, dedup):
        results = dedup.process([LINE_A, LINE_A2])
        entry = results[0]
        assert entry.first_seen is not None
        assert entry.last_seen is not None
        assert entry.last_seen >= entry.first_seen


class TestLogDeduplicatorBuilder:
    def test_build_returns_deduplicator(self):
        d = LogDeduplicatorBuilder().build()
        assert isinstance(d, LogDeduplicator)

    def test_custom_window(self):
        d = LogDeduplicatorBuilder().with_window(120).build()
        from datetime import timedelta
        assert d.window == timedelta(seconds=120)

    def test_zero_window_raises(self):
        with pytest.raises(LogDeduplicatorBuilderError):
            LogDeduplicatorBuilder().with_window(0)

    def test_negative_window_raises(self):
        with pytest.raises(LogDeduplicatorBuilderError):
            LogDeduplicatorBuilder().with_window(-5)

    def test_empty_formats_raises(self):
        with pytest.raises(LogDeduplicatorBuilderError):
            LogDeduplicatorBuilder().with_timestamp_formats([])

    def test_custom_formats_applied(self):
        fmt = ["%Y-%m-%dT%H:%M:%S"]
        d = LogDeduplicatorBuilder().with_timestamp_formats(fmt).build()
        assert d._parser is not None
