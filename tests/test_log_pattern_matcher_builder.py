"""Tests for LogPatternMatcherBuilder and PatternMatchReporter."""
import io
import json

import pytest

from logslice.log_pattern_matcher_builder import (
    LogPatternMatcherBuilder,
    LogPatternMatcherBuilderError,
)
from logslice.pattern_match_reporter import PatternMatchReporter, PatternMatchReporterError
from logslice.log_pattern_matcher import MatchedEntry


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------

class TestLogPatternMatcherBuilder:
    def test_returns_matcher(self):
        matcher = LogPatternMatcherBuilder().add_regex(r"ERROR").build()
        assert matcher is not None

    def test_no_rules_raises(self):
        with pytest.raises(LogPatternMatcherBuilderError):
            LogPatternMatcherBuilder().build()

    def test_invalid_regex_raises(self):
        with pytest.raises(LogPatternMatcherBuilderError):
            LogPatternMatcherBuilder().add_regex("[bad").build()

    def test_literal_rule_works(self):
        matcher = LogPatternMatcherBuilder().add_literal("WARN").build()
        assert matcher.match_line("WARN: low memory") is not None

    def test_group_propagated(self):
        matcher = LogPatternMatcherBuilder().add_regex(r"ERROR", group="err").build()
        entry = matcher.match_line("ERROR occurred")
        assert entry is not None
        assert entry.group == "err"

    def test_multiple_rules(self):
        matcher = (
            LogPatternMatcherBuilder()
            .add_regex(r"ERROR", group="err")
            .add_literal("WARN", group="warn")
            .build()
        )
        lines = ["ERROR x", "WARN y", "INFO z"]
        results = matcher.match_lines(lines)
        assert len(results) == 2


# ---------------------------------------------------------------------------
# Reporter
# ---------------------------------------------------------------------------

ENTRIES = [
    MatchedEntry(line="ERROR: disk full", pattern=r"ERROR", group="errors"),
    MatchedEntry(line="WARN: low mem", pattern=r"WARN", group="warnings"),
]


class TestPatternMatchReporter:
    def test_invalid_format_raises(self):
        with pytest.raises(PatternMatchReporterError):
            PatternMatchReporter(fmt="xml")

    def test_plain_output_contains_lines(self):
        buf = io.StringIO()
        PatternMatchReporter(fmt="plain").report(ENTRIES, out=buf)
        text = buf.getvalue()
        assert "ERROR: disk full" in text
        assert "WARN: low mem" in text

    def test_plain_empty_message(self):
        buf = io.StringIO()
        PatternMatchReporter(fmt="plain").report([], out=buf)
        assert "No matches" in buf.getvalue()

    def test_json_output_is_valid(self):
        buf = io.StringIO()
        PatternMatchReporter(fmt="json").report(ENTRIES, out=buf)
        data = json.loads(buf.getvalue())
        assert len(data) == 2
        assert data[0]["group"] == "errors"

    def test_report_to_file(self, tmp_path):
        path = str(tmp_path / "out.txt")
        PatternMatchReporter(fmt="plain").report_to_file(ENTRIES, path)
        with open(path) as fh:
            content = fh.read()
        assert "ERROR: disk full" in content
