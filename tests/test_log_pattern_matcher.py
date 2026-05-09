"""Tests for LogPatternMatcher and MatchedEntry."""
import pytest

from logslice.log_pattern_matcher import (
    LogPatternMatcher,
    MatchedEntry,
    PatternMatcherError,
    PatternRule,
)


# ---------------------------------------------------------------------------
# MatchedEntry
# ---------------------------------------------------------------------------

class TestMatchedEntry:
    def test_to_dict_keys(self):
        entry = MatchedEntry(line="hello", pattern=r"hel+o", group="grp")
        assert set(entry.to_dict().keys()) == {"line", "pattern", "group"}

    def test_to_dict_values(self):
        entry = MatchedEntry(line="hello", pattern=r"hel+o", group="grp")
        d = entry.to_dict()
        assert d["line"] == "hello"
        assert d["group"] == "grp"

    def test_to_dict_none_group(self):
        entry = MatchedEntry(line="x", pattern="x")
        assert entry.to_dict()["group"] is None


# ---------------------------------------------------------------------------
# PatternRule
# ---------------------------------------------------------------------------

class TestPatternRule:
    def test_regex_matches(self):
        rule = PatternRule(pattern=r"ERROR", is_regex=True)
        assert rule.matches("2024-01-01 ERROR something broke")

    def test_regex_no_match(self):
        rule = PatternRule(pattern=r"ERROR", is_regex=True)
        assert not rule.matches("INFO all good")

    def test_literal_matches(self):
        rule = PatternRule(pattern="WARN", is_regex=False)
        assert rule.matches("WARN disk space low")

    def test_invalid_regex_raises(self):
        with pytest.raises(PatternMatcherError):
            PatternRule(pattern="[invalid", is_regex=True)


# ---------------------------------------------------------------------------
# LogPatternMatcher
# ---------------------------------------------------------------------------

@pytest.fixture()
def matcher():
    m = LogPatternMatcher()
    m.add_rule(r"ERROR", group="errors")
    m.add_rule(r"WARN", group="warnings")
    return m


class TestLogPatternMatcher:
    def test_match_line_returns_entry(self, matcher):
        entry = matcher.match_line("ERROR: disk full")
        assert entry is not None
        assert entry.group == "errors"

    def test_match_line_returns_none_on_no_match(self, matcher):
        assert matcher.match_line("INFO: all good") is None

    def test_match_lines_filters_correctly(self, matcher):
        lines = ["INFO ok", "ERROR boom", "WARN low", "DEBUG trace"]
        results = matcher.match_lines(lines)
        assert len(results) == 2

    def test_match_file(self, tmp_path, matcher):
        log = tmp_path / "app.log"
        log.write_text("INFO start\nERROR crash\nWARN slow\n")
        results = matcher.match_file(str(log))
        assert len(results) == 2

    def test_entry_line_stripped(self, matcher):
        entry = matcher.match_line("ERROR: newline\n")
        assert entry is not None
        assert not entry.line.endswith("\n")

    def test_literal_rule(self):
        m = LogPatternMatcher()
        m.add_rule("CRITICAL", is_regex=False)
        assert m.match_line("CRITICAL failure") is not None
        assert m.match_line("ERROR other") is None
