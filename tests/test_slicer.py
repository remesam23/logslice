"""Tests for logslice.slicer."""

from datetime import datetime

import pytest

from logslice.slicer import LogSlicer

SAMPLE_LINES = [
    '2024-03-10 07:00:00 DEBUG early message\n',
    '2024-03-10 08:00:00 INFO within range start\n',
    '2024-03-10 09:30:00 WARN midpoint\n',
    '2024-03-10 10:00:00 INFO within range end\n',
    '2024-03-10 11:00:00 ERROR after range\n',
    'no timestamp line\n',
]

START = datetime(2024, 3, 10, 8, 0, 0)
END = datetime(2024, 3, 10, 10, 0, 0)


@pytest.fixture
def slicer():
    return LogSlicer(start=START, end=END)


class TestLogSlicer:
    def test_filters_within_range(self, slicer):
        results = list(slicer.filter_lines(SAMPLE_LINES))
        timestamps = [r['timestamp'] for r in results]
        assert datetime(2024, 3, 10, 8, 0, 0) in timestamps
        assert datetime(2024, 3, 10, 10, 0, 0) in timestamps
        assert datetime(2024, 3, 10, 9, 30, 0) in timestamps

    def test_excludes_before_start(self, slicer):
        results = list(slicer.filter_lines(SAMPLE_LINES))
        timestamps = [r['timestamp'] for r in results]
        assert datetime(2024, 3, 10, 7, 0, 0) not in timestamps

    def test_excludes_after_end(self, slicer):
        results = list(slicer.filter_lines(SAMPLE_LINES))
        timestamps = [r['timestamp'] for r in results]
        assert datetime(2024, 3, 10, 11, 0, 0) not in timestamps

    def test_exclude_unparsed_by_default(self, slicer):
        results = list(slicer.filter_lines(SAMPLE_LINES))
        assert all(r['parsed'] for r in results)

    def test_include_unparsed_flag(self):
        s = LogSlicer(start=START, end=END, include_unparsed=True)
        results = list(s.filter_lines(SAMPLE_LINES))
        unparsed = [r for r in results if not r['parsed']]
        assert len(unparsed) == 1

    def test_no_bounds_returns_all_parsed(self):
        s = LogSlicer()
        results = list(s.filter_lines(SAMPLE_LINES))
        assert len(results) == 5  # 5 lines with timestamps

    def test_only_start_bound(self):
        s = LogSlicer(start=START)
        results = list(s.filter_lines(SAMPLE_LINES))
        timestamps = [r['timestamp'] for r in results]
        assert datetime(2024, 3, 10, 7, 0, 0) not in timestamps
        assert datetime(2024, 3, 10, 11, 0, 0) in timestamps
