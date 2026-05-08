import pytest
from logslice.log_severity_filter import (
    FilteredEntry,
    LogSeverityFilter,
    SeverityFilterError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def lines():
    return [
        "2024-01-01T10:00:00 DEBUG starting up",
        "2024-01-01T10:00:01 INFO  service ready",
        "2024-01-01T10:00:02 WARNING disk usage high",
        "2024-01-01T10:00:03 ERROR  connection refused",
        "2024-01-01T10:00:04 CRITICAL out of memory",
        "2024-01-01T10:00:05 no level token here",
    ]


# ---------------------------------------------------------------------------
# FilteredEntry
# ---------------------------------------------------------------------------


class TestFilteredEntry:
    def test_to_dict_keys(self):
        entry = FilteredEntry(line="some line", severity="ERROR")
        assert set(entry.to_dict().keys()) == {"line", "severity"}

    def test_to_dict_values(self):
        entry = FilteredEntry(line="msg", severity="INFO")
        d = entry.to_dict()
        assert d["line"] == "msg"
        assert d["severity"] == "INFO"

    def test_none_severity(self):
        entry = FilteredEntry(line="raw", severity=None)
        assert entry.to_dict()["severity"] is None


# ---------------------------------------------------------------------------
# LogSeverityFilter construction
# ---------------------------------------------------------------------------


class TestLogSeverityFilterInit:
    def test_invalid_level_raises(self):
        with pytest.raises(SeverityFilterError, match="VERBOSE"):
            LogSeverityFilter(levels=["VERBOSE"])

    def test_valid_levels_accepted(self):
        f = LogSeverityFilter(levels=["error", "WARNING"])
        assert "ERROR" in f.levels
        assert "WARNING" in f.levels

    def test_empty_levels_accepted(self):
        f = LogSeverityFilter()
        assert f.levels == []


# ---------------------------------------------------------------------------
# extract_severity
# ---------------------------------------------------------------------------


class TestExtractSeverity:
    def test_extracts_error(self):
        assert LogSeverityFilter.extract_severity("ERROR something") == "ERROR"

    def test_normalises_warn_to_warning(self):
        assert LogSeverityFilter.extract_severity("WARN low disk") == "WARNING"

    def test_normalises_fatal_to_critical(self):
        assert LogSeverityFilter.extract_severity("FATAL crash") == "CRITICAL"

    def test_returns_none_when_absent(self):
        assert LogSeverityFilter.extract_severity("no level here") is None

    def test_case_insensitive(self):
        assert LogSeverityFilter.extract_severity("info startup") == "INFO"


# ---------------------------------------------------------------------------
# matches / filter
# ---------------------------------------------------------------------------


class TestFilter:
    def test_filter_by_error_only(self, lines):
        f = LogSeverityFilter(levels=["ERROR"])
        results = f.filter(lines)
        assert len(results) == 1
        assert results[0].severity == "ERROR"

    def test_filter_multiple_levels(self, lines):
        f = LogSeverityFilter(levels=["ERROR", "CRITICAL"])
        results = f.filter(lines)
        assert {r.severity for r in results} == {"ERROR", "CRITICAL"}

    def test_empty_levels_returns_all(self, lines):
        f = LogSeverityFilter()
        results = f.filter(lines)
        assert len(results) == len(lines)

    def test_no_level_line_excluded_when_filter_set(self, lines):
        f = LogSeverityFilter(levels=["INFO"])
        raw_lines = [r.line for r in f.filter(lines)]
        assert "2024-01-01T10:00:05 no level token here" not in raw_lines

    def test_matches_returns_true_for_matching_line(self):
        f = LogSeverityFilter(levels=["WARNING"])
        assert f.matches("WARNING disk almost full") is True

    def test_matches_returns_false_for_non_matching_line(self):
        f = LogSeverityFilter(levels=["ERROR"])
        assert f.matches("INFO all good") is False
