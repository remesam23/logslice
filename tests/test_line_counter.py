"""Tests for logslice.line_counter."""

import pytest
from datetime import datetime, timezone
from pathlib import Path

from logslice.parser import LogParser
from logslice.slicer import LogSlicer
from logslice.line_counter import LineCounter, LineCountResult


START = datetime(2024, 1, 10, 8, 0, 0, tzinfo=timezone.utc)
END = datetime(2024, 1, 10, 10, 0, 0, tzinfo=timezone.utc)

LOG_LINES = [
    "2024-01-10T07:59:00Z DEBUG too early",
    "2024-01-10T08:00:00Z INFO  start boundary",
    "2024-01-10T09:00:00Z INFO  within range",
    "2024-01-10T10:00:00Z INFO  end boundary",
    "2024-01-10T10:01:00Z WARN  too late",
    "no timestamp here at all",
]


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "sample.log"
    p.write_text("\n".join(LOG_LINES) + "\n")
    return str(p)


@pytest.fixture
def counter():
    parser = LogParser(timestamp_formats=["%Y-%m-%dT%H:%M:%SZ"])
    slicer = LogSlicer(start=START, end=END)
    return LineCounter(slicer=slicer, parser=parser)


class TestLineCountResult:
    def test_skipped_sum(self):
        r = LineCountResult(skipped_before=2, skipped_after=3, unparseable=1)
        assert r.skipped == 6

    def test_to_dict_keys(self):
        r = LineCountResult(total=10, matched=5)
        d = r.to_dict()
        assert set(d.keys()) == {
            "total", "matched", "skipped_before",
            "skipped_after", "unparseable", "skipped",
        }

    def test_summary_contains_counts(self):
        r = LineCountResult(total=6, matched=3, skipped_before=1, skipped_after=1, unparseable=1)
        s = r.summary()
        assert "6" in s
        assert "3" in s


class TestLineCounter:
    def test_total_count(self, counter, log_file):
        result = counter.count_file(log_file)
        assert result.total == len(LOG_LINES)

    def test_matched_count(self, counter, log_file):
        result = counter.count_file(log_file)
        assert result.matched == 3  # 08:00, 09:00, 10:00

    def test_skipped_before(self, counter, log_file):
        result = counter.count_file(log_file)
        assert result.skipped_before == 1

    def test_skipped_after(self, counter, log_file):
        result = counter.count_file(log_file)
        assert result.skipped_after == 1

    def test_unparseable(self, counter, log_file):
        result = counter.count_file(log_file)
        assert result.unparseable == 1

    def test_skipped_total(self, counter, log_file):
        result = counter.count_file(log_file)
        assert result.skipped == result.skipped_before + result.skipped_after + result.unparseable
