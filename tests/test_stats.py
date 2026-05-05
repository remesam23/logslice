"""Tests for SliceStats and StatsReporter."""

import json
from datetime import datetime
from io import StringIO

import pytest

from logslice.stats import SliceStats
from logslice.stats_reporter import StatsReporter


@pytest.fixture
def populated_stats() -> SliceStats:
    s = SliceStats(total_lines=100)
    s.record_match(datetime(2024, 1, 1, 10, 0, 0))
    s.record_match(datetime(2024, 1, 1, 10, 5, 0))
    s.record_match(datetime(2024, 1, 1, 9, 55, 0))  # earlier — becomes first
    s.record_skip("before")
    s.record_skip("before")
    s.record_skip("after")
    s.record_skip("unparseable")
    return s


class TestSliceStats:
    def test_initial_state(self):
        s = SliceStats()
        assert s.total_lines == 0
        assert s.matched_lines == 0
        assert s.match_rate == 0.0

    def test_match_rate(self, populated_stats):
        assert populated_stats.matched_lines == 3
        assert populated_stats.match_rate == pytest.approx(0.03)

    def test_skip_counters(self, populated_stats):
        assert populated_stats.skipped_before == 2
        assert populated_stats.skipped_after == 1
        assert populated_stats.unparseable_lines == 1

    def test_first_last_timestamps(self, populated_stats):
        assert populated_stats.first_matched_ts == datetime(2024, 1, 1, 9, 55, 0)
        assert populated_stats.last_matched_ts == datetime(2024, 1, 1, 10, 5, 0)

    def test_to_dict_keys(self, populated_stats):
        d = populated_stats.to_dict()
        for key in ("total_lines", "matched_lines", "skipped_before",
                    "skipped_after", "unparseable_lines", "match_rate",
                    "first_matched_ts", "last_matched_ts"):
            assert key in d

    def test_to_dict_no_timestamps(self):
        s = SliceStats(total_lines=5)
        d = s.to_dict()
        assert d["first_matched_ts"] is None
        assert d["last_matched_ts"] is None

    def test_summary_contains_counts(self, populated_stats):
        summary = populated_stats.summary()
        assert "100" in summary
        assert "3" in summary


class TestStatsReporter:
    def test_invalid_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported stats format"):
            StatsReporter(fmt="xml")

    def test_text_report(self, populated_stats):
        buf = StringIO()
        reporter = StatsReporter(fmt="text", output=buf)
        reporter.report(populated_stats)
        output = buf.getvalue()
        assert "Processed" in output
        assert "matched" in output

    def test_json_report(self, populated_stats):
        buf = StringIO()
        reporter = StatsReporter(fmt="json", output=buf)
        reporter.report(populated_stats)
        data = json.loads(buf.getvalue())
        assert data["matched_lines"] == 3
        assert data["skipped_before"] == 2

    def test_report_to_string_text(self, populated_stats):
        reporter = StatsReporter(fmt="text")
        result = reporter.report_to_string(populated_stats)
        assert isinstance(result, str)
        assert "Processed" in result

    def test_report_to_string_json(self, populated_stats):
        reporter = StatsReporter(fmt="json")
        result = reporter.report_to_string(populated_stats)
        data = json.loads(result)
        assert "match_rate" in data
