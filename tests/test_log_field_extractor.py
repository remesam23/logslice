import pytest
from logslice.log_field_extractor import (
    ExtractedEntry,
    FieldExtractorError,
    FieldRule,
    LogFieldExtractor,
)


# ---------------------------------------------------------------------------
# ExtractedEntry
# ---------------------------------------------------------------------------

class TestExtractedEntry:
    def test_to_dict_keys(self):
        entry = ExtractedEntry(raw="some line", fields={"level": "ERROR"})
        assert set(entry.to_dict().keys()) == {"raw", "fields"}

    def test_to_dict_values(self):
        entry = ExtractedEntry(raw="msg", fields={"ip": "127.0.0.1"})
        d = entry.to_dict()
        assert d["raw"] == "msg"
        assert d["fields"]["ip"] == "127.0.0.1"

    def test_empty_fields(self):
        entry = ExtractedEntry(raw="no match", fields={})
        assert entry.to_dict()["fields"] == {}


# ---------------------------------------------------------------------------
# FieldRule
# ---------------------------------------------------------------------------

class TestFieldRule:
    def test_from_regex_valid(self):
        rule = FieldRule.from_regex("level", r"(?P<value>ERROR|WARN|INFO)")
        assert rule.name == "level"

    def test_from_regex_invalid_raises(self):
        with pytest.raises(FieldExtractorError, match="Invalid regex"):
            FieldRule.from_regex("bad", r"(?P<unclosed")


# ---------------------------------------------------------------------------
# LogFieldExtractor
# ---------------------------------------------------------------------------

@pytest.fixture()
def extractor():
    ex = LogFieldExtractor()
    ex.add_rule(FieldRule.from_regex("level", r"(?P<value>ERROR|WARN|INFO)"))
    ex.add_rule(FieldRule.from_regex("ip", r"(?P<value>\d{1,3}(?:\.\d{1,3}){3})"))
    return ex


class TestLogFieldExtractor:
    def test_extract_known_fields(self, extractor):
        entry = extractor.extract("2024-01-01 ERROR 192.168.1.1 something failed")
        assert entry.fields["level"] == "ERROR"
        assert entry.fields["ip"] == "192.168.1.1"

    def test_extract_missing_field_absent(self, extractor):
        entry = extractor.extract("2024-01-01 INFO no ip here")
        assert entry.fields["level"] == "INFO"
        assert "ip" not in entry.fields

    def test_extract_raw_preserved(self, extractor):
        line = "2024-01-01 WARN 10.0.0.1 disk full"
        entry = extractor.extract(line)
        assert entry.raw == line

    def test_extract_all_returns_list(self, extractor):
        lines = [
            "2024-01-01 ERROR 1.2.3.4 oops",
            "2024-01-01 INFO no ip",
        ]
        results = extractor.extract_all(lines)
        assert len(results) == 2
        assert results[0].fields["level"] == "ERROR"
        assert results[1].fields["level"] == "INFO"

    def test_no_rules_returns_empty_fields(self):
        ex = LogFieldExtractor()
        entry = ex.extract("some line")
        assert entry.fields == {}

    def test_extract_all_empty_input(self, extractor):
        assert extractor.extract_all([]) == []
