"""Tests for logslice.log_context_extractor."""
import pytest

from logslice.log_context_extractor import (
    ContextEntry,
    ContextExtractorError,
    LogContextExtractor,
)


LINES = [
    "2024-01-01 00:00:01 INFO  startup",
    "2024-01-01 00:00:02 DEBUG init db",
    "2024-01-01 00:00:03 ERROR disk full",
    "2024-01-01 00:00:04 INFO  retrying",
    "2024-01-01 00:00:05 WARN  slow query",
    "2024-01-01 00:00:06 ERROR timeout",
    "2024-01-01 00:00:07 INFO  done",
]


@pytest.fixture
def extractor():
    return LogContextExtractor(before=2, after=2)


class TestContextEntry:
    def test_to_dict_keys(self):
        entry = ContextEntry(line_number=3, matched_line="ERROR disk full",
                             before=["line1"], after=["line4"])
        d = entry.to_dict()
        assert set(d.keys()) == {"line_number", "matched_line", "before", "after"}

    def test_to_dict_values(self):
        entry = ContextEntry(line_number=3, matched_line="ERROR disk full",
                             before=["a", "b"], after=["c"])
        d = entry.to_dict()
        assert d["line_number"] == 3
        assert d["matched_line"] == "ERROR disk full"
        assert d["before"] == ["a", "b"]
        assert d["after"] == ["c"]

    def test_formatted_block_contains_marker(self):
        entry = ContextEntry(line_number=3, matched_line="ERROR disk full",
                             before=["prev"], after=["next"])
        block = entry.formatted_block()
        assert "> ERROR disk full" in block
        assert "  prev" in block
        assert "  next" in block


class TestLogContextExtractor:
    def test_negative_before_raises(self):
        with pytest.raises(ContextExtractorError):
            LogContextExtractor(before=-1, after=2)

    def test_negative_after_raises(self):
        with pytest.raises(ContextExtractorError):
            LogContextExtractor(before=2, after=-1)

    def test_no_matches_returns_empty(self, extractor):
        results = extractor.extract(LINES, lambda l: "CRITICAL" in l)
        assert results == []

    def test_single_match_line_number(self, extractor):
        results = extractor.extract(LINES, lambda l: "disk full" in l)
        assert len(results) == 1
        assert results[0].line_number == 3

    def test_before_context_clipped_at_start(self, extractor):
        # First line matched – no 'before' lines available
        results = extractor.extract(LINES, lambda l: "startup" in l)
        assert results[0].before == []

    def test_after_context_clipped_at_end(self, extractor):
        results = extractor.extract(LINES, lambda l: "done" in l)
        assert results[0].after == []

    def test_multiple_matches(self, extractor):
        results = extractor.extract(LINES, lambda l: "ERROR" in l)
        assert len(results) == 2
        assert results[0].matched_line.endswith("disk full")
        assert results[1].matched_line.endswith("timeout")

    def test_context_content_correct(self, extractor):
        results = extractor.extract(LINES, lambda l: "disk full" in l)
        entry = results[0]
        assert "DEBUG init db" in entry.before[-1]
        assert "retrying" in entry.after[0]

    def test_zero_context_windows(self):
        ext = LogContextExtractor(before=0, after=0)
        results = ext.extract(LINES, lambda l: "ERROR" in l)
        for entry in results:
            assert entry.before == []
            assert entry.after == []

    def test_extract_from_file(self, tmp_path, extractor):
        log = tmp_path / "sample.log"
        log.write_text("\n".join(LINES) + "\n", encoding="utf-8")
        results = extractor.extract_from_file(str(log), lambda l: "ERROR" in l)
        assert len(results) == 2
