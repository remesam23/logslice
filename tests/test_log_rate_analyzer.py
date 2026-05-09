"""Tests for LogRateAnalyzer and related dataclasses."""

import pytest
from datetime import datetime

from logslice.log_rate_analyzer import LogRateAnalyzer, RateBucket, RateResult


LINES = [
    "2024-01-15T10:00:05 INFO  request received\n",
    "2024-01-15T10:00:45 INFO  request completed\n",
    "2024-01-15T10:01:10 ERROR timeout\n",
    "2024-01-15T10:01:55 WARN  slow query\n",
    "2024-01-15T10:02:30 INFO  healthcheck\n",
    "not a log line\n",
]


@pytest.fixture
def analyzer():
    return LogRateAnalyzer(bucket_seconds=60)


class TestRateBucket:
    def test_to_dict_keys(self):
        b = RateBucket(
            window_start=datetime(2024, 1, 15, 10, 0, 0),
            window_end=datetime(2024, 1, 15, 10, 1, 0),
            count=3,
        )
        d = b.to_dict()
        assert set(d.keys()) == {"window_start", "window_end", "count"}

    def test_to_dict_count(self):
        b = RateBucket(
            window_start=datetime(2024, 1, 15, 10, 0, 0),
            window_end=datetime(2024, 1, 15, 10, 1, 0),
            count=7,
        )
        assert b.to_dict()["count"] == 7


class TestRateResult:
    def test_total_entries(self):
        r = RateResult(bucket_seconds=60)
        r.buckets = [
            RateBucket(datetime(2024, 1, 15, 10, 0), datetime(2024, 1, 15, 10, 1), count=3),
            RateBucket(datetime(2024, 1, 15, 10, 1), datetime(2024, 1, 15, 10, 2), count=5),
        ]
        assert r.total_entries == 8

    def test_peak_bucket(self):
        r = RateResult(bucket_seconds=60)
        r.buckets = [
            RateBucket(datetime(2024, 1, 15, 10, 0), datetime(2024, 1, 15, 10, 1), count=2),
            RateBucket(datetime(2024, 1, 15, 10, 1), datetime(2024, 1, 15, 10, 2), count=9),
        ]
        assert r.peak_bucket.count == 9

    def test_peak_bucket_none_when_empty(self):
        r = RateResult(bucket_seconds=60)
        assert r.peak_bucket is None

    def test_to_dict_keys(self):
        r = RateResult(bucket_seconds=60)
        d = r.to_dict()
        assert set(d.keys()) == {"bucket_seconds", "total_entries", "peak", "buckets"}

    def test_summary_contains_totals(self):
        r = RateResult(bucket_seconds=60)
        r.buckets = [
            RateBucket(datetime(2024, 1, 15, 10, 0), datetime(2024, 1, 15, 10, 1), count=4),
        ]
        s = r.summary()
        assert "4" in s
        assert "60" in s


class TestLogRateAnalyzer:
    def test_invalid_bucket_raises(self):
        with pytest.raises(ValueError):
            LogRateAnalyzer(bucket_seconds=0)

    def test_bucket_count(self, analyzer):
        result = analyzer.analyze(LINES)
        assert len(result.buckets) == 3

    def test_first_bucket_has_two_entries(self, analyzer):
        result = analyzer.analyze(LINES)
        assert result.buckets[0].count == 2

    def test_skips_unparseable_lines(self, analyzer):
        result = analyzer.analyze(LINES)
        assert result.total_entries == 5

    def test_analyze_file(self, analyzer, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("".join(LINES))
        result = analyzer.analyze_file(str(log))
        assert result.total_entries == 5

    def test_empty_input(self, analyzer):
        result = analyzer.analyze([])
        assert result.total_entries == 0
        assert result.peak_bucket is None
