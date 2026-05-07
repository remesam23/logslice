"""Tests for LogAnnotator and LogAnnotatorBuilder."""

import pytest

from logslice.log_annotator import AnnotatedEntry, LogAnnotator
from logslice.log_annotator_builder import LogAnnotatorBuilder, LogAnnotatorBuilderError


RULES = {
    "error": ["ERROR", "Exception"],
    "slow": ["timeout", "slow"],
    "auth": ["login", "logout", "unauthorized"],
}


@pytest.fixture
def annotator():
    return LogAnnotator(rules=RULES, source="app.log")


class TestAnnotatedEntry:
    def test_to_dict_keys(self):
        entry = AnnotatedEntry(raw_line="test", timestamp="2024-01-01", tags=["error"])
        d = entry.to_dict()
        assert set(d.keys()) == {"raw_line", "timestamp", "tags", "source"}

    def test_to_dict_values(self):
        entry = AnnotatedEntry(raw_line="msg", timestamp=None, tags=[], source="x")
        assert entry.to_dict()["source"] == "x"
        assert entry.to_dict()["tags"] == []


class TestLogAnnotator:
    def test_single_tag_matched(self, annotator):
        entry = annotator.annotate("2024-01-01 ERROR something failed")
        assert "error" in entry.tags

    def test_multiple_tags_matched(self, annotator):
        entry = annotator.annotate("2024-01-01 ERROR timeout reached")
        assert "error" in entry.tags
        assert "slow" in entry.tags

    def test_no_tags_when_no_match(self, annotator):
        entry = annotator.annotate("2024-01-01 INFO all systems nominal")
        assert entry.tags == []

    def test_case_insensitive_matching(self, annotator):
        entry = annotator.annotate("exception raised in module")
        assert "error" in entry.tags

    def test_source_is_set(self, annotator):
        entry = annotator.annotate("some line")
        assert entry.source == "app.log"

    def test_timestamp_passed_through(self, annotator):
        entry = annotator.annotate("ERROR", timestamp="2024-06-01T10:00:00")
        assert entry.timestamp == "2024-06-01T10:00:00"

    def test_annotate_many_length(self, annotator):
        lines = ["ERROR one", "INFO two", "timeout three"]
        entries = annotator.annotate_many(lines)
        assert len(entries) == 3

    def test_annotate_many_with_timestamps(self, annotator):
        lines = ["ERROR one", "INFO two"]
        ts = ["2024-01-01", "2024-01-02"]
        entries = annotator.annotate_many(lines, timestamps=ts)
        assert entries[0].timestamp == "2024-01-01"
        assert entries[1].timestamp == "2024-01-02"


class TestLogAnnotatorBuilder:
    def test_build_returns_annotator(self):
        ann = LogAnnotatorBuilder().add_rule("error", ["ERROR"]).build()
        assert isinstance(ann, LogAnnotator)

    def test_source_set_on_annotator(self):
        ann = (
            LogAnnotatorBuilder()
            .add_rule("error", ["ERROR"])
            .with_source("syslog")
            .build()
        )
        assert ann.source == "syslog"

    def test_add_rule_merges_keywords(self):
        ann = (
            LogAnnotatorBuilder()
            .add_rule("error", ["ERROR"])
            .add_rule("error", ["Exception"])
            .build()
        )
        assert "Exception" in ann.rules["error"]
        assert "ERROR" in ann.rules["error"]

    def test_empty_tag_raises(self):
        with pytest.raises(LogAnnotatorBuilderError, match="Tag name"):
            LogAnnotatorBuilder().add_rule("", ["ERROR"])

    def test_empty_keywords_raises(self):
        with pytest.raises(LogAnnotatorBuilderError, match="Keyword list"):
            LogAnnotatorBuilder().add_rule("error", [])

    def test_build_without_rules_raises(self):
        with pytest.raises(LogAnnotatorBuilderError, match="At least one"):
            LogAnnotatorBuilder().build()
