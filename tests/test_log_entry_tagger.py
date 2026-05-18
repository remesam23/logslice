import pytest
from logslice.log_entry_tagger import (
    EntryTaggerError,
    LogEntryTagger,
    TaggedEntry,
    TagRule,
)


# ---------------------------------------------------------------------------
# TaggedEntry
# ---------------------------------------------------------------------------

class TestTaggedEntry:
    def test_to_dict_keys(self):
        entry = TaggedEntry(line="some log line", tags=["error"], timestamp="2024-01-01")
        assert set(entry.to_dict().keys()) == {"line", "tags", "timestamp"}

    def test_to_dict_values(self):
        entry = TaggedEntry(line="hello", tags=["warn", "db"], timestamp=None)
        d = entry.to_dict()
        assert d["line"] == "hello"
        assert d["tags"] == ["warn", "db"]
        assert d["timestamp"] is None

    def test_empty_tags_list(self):
        entry = TaggedEntry(line="no match", tags=[])
        assert entry.to_dict()["tags"] == []


# ---------------------------------------------------------------------------
# TagRule
# ---------------------------------------------------------------------------

class TestTagRule:
    def test_empty_tag_raises(self):
        with pytest.raises(EntryTaggerError, match="Tag name"):
            TagRule(tag="", pattern="error")

    def test_empty_pattern_raises(self):
        with pytest.raises(EntryTaggerError, match="Tag pattern"):
            TagRule(tag="error", pattern="")

    def test_invalid_regex_raises(self):
        with pytest.raises(EntryTaggerError, match="Invalid regex"):
            TagRule(tag="bad", pattern="[unclosed")

    def test_case_insensitive_match(self):
        rule = TagRule(tag="error", pattern="ERROR", case_sensitive=False)
        assert rule.matches("2024-01-01 error: something failed")

    def test_case_sensitive_no_match(self):
        rule = TagRule(tag="error", pattern="ERROR", case_sensitive=True)
        assert not rule.matches("2024-01-01 error: lowercase only")

    def test_case_sensitive_match(self):
        rule = TagRule(tag="error", pattern="ERROR", case_sensitive=True)
        assert rule.matches("2024-01-01 ERROR: uppercase")


# ---------------------------------------------------------------------------
# LogEntryTagger
# ---------------------------------------------------------------------------

@pytest.fixture()
def tagger():
    rules = [
        TagRule(tag="error", pattern=r"error"),
        TagRule(tag="timeout", pattern=r"timeout"),
        TagRule(tag="db", pattern=r"database|db"),
    ]
    return LogEntryTagger(rules=rules)


class TestLogEntryTagger:
    def test_no_rules_raises(self):
        with pytest.raises(EntryTaggerError, match="At least one"):
            LogEntryTagger(rules=[])

    def test_single_tag_applied(self, tagger):
        entry = tagger.tag_line("2024-01-01 12:00:00 error: disk full")
        assert "error" in entry.tags
        assert "timeout" not in entry.tags

    def test_multiple_tags_applied(self, tagger):
        entry = tagger.tag_line("2024-01-01 12:00:00 error: database timeout")
        assert "error" in entry.tags
        assert "timeout" in entry.tags
        assert "db" in entry.tags

    def test_no_tags_when_no_match(self, tagger):
        entry = tagger.tag_line("2024-01-01 12:00:00 INFO: all systems nominal")
        assert entry.tags == []

    def test_tag_lines_skips_blank(self, tagger):
        lines = ["error: bad\n", "   \n", "timeout reached\n"]
        results = tagger.tag_lines(lines)
        assert len(results) == 2

    def test_line_stripped_of_newline(self, tagger):
        entry = tagger.tag_line("error: something\n")
        assert not entry.line.endswith("\n")

    def test_timestamp_extracted(self):
        rules = [TagRule(tag="error", pattern="error")]
        ts_fmt = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
        t = LogEntryTagger(rules=rules, timestamp_formats=[ts_fmt])
        entry = t.tag_line("2024-06-15 08:23:11 error: crash")
        assert entry.timestamp == "2024-06-15 08:23:11"

    def test_timestamp_none_when_no_format(self, tagger):
        entry = tagger.tag_line("error: no timestamp here")
        assert entry.timestamp is None
