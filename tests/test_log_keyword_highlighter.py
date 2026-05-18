import pytest

from logslice.log_keyword_highlighter import (
    HighlightedEntry,
    KeywordHighlighterError,
    KeywordRule,
    LogKeywordHighlighter,
)
from logslice.log_keyword_highlighter_builder import (
    LogKeywordHighlighterBuilder,
    LogKeywordHighlighterBuilderError,
)


# ---------------------------------------------------------------------------
# HighlightedEntry
# ---------------------------------------------------------------------------

class TestHighlightedEntry:
    def test_to_dict_keys(self):
        entry = HighlightedEntry(raw="line", matched_keywords=["error"], highlighted=">>>error<<<", source="f.log")
        assert set(entry.to_dict().keys()) == {"raw", "matched_keywords", "highlighted", "source"}

    def test_to_dict_values(self):
        entry = HighlightedEntry(raw="an error occurred", matched_keywords=["error"], highlighted="an >>>error<<< occurred", source=None)
        d = entry.to_dict()
        assert d["source"] is None
        assert d["matched_keywords"] == ["error"]


# ---------------------------------------------------------------------------
# KeywordRule
# ---------------------------------------------------------------------------

class TestKeywordRule:
    def test_empty_keyword_raises(self):
        with pytest.raises(KeywordHighlighterError):
            KeywordRule(keyword="")

    def test_matches_case_insensitive(self):
        rule = KeywordRule(keyword="ERROR")
        assert rule.matches("An error occurred")

    def test_matches_case_sensitive(self):
        rule = KeywordRule(keyword="ERROR", case_sensitive=True)
        assert not rule.matches("An error occurred")
        assert rule.matches("An ERROR occurred")

    def test_apply_wraps_keyword(self):
        rule = KeywordRule(keyword="fail", marker_open="[", marker_close="]")
        result = rule.apply("system fail detected")
        assert result == "system [fail] detected"


# ---------------------------------------------------------------------------
# LogKeywordHighlighter
# ---------------------------------------------------------------------------

@pytest.fixture
def highlighter():
    rules = [KeywordRule(keyword="error"), KeywordRule(keyword="timeout")]
    return LogKeywordHighlighter(rules=rules)


class TestLogKeywordHighlighter:
    def test_no_rules_raises(self):
        with pytest.raises(KeywordHighlighterError):
            LogKeywordHighlighter(rules=[])

    def test_non_matching_line_returns_none(self, highlighter):
        assert highlighter.highlight_line("everything is fine") is None

    def test_matching_line_returns_entry(self, highlighter):
        entry = highlighter.highlight_line("connection timeout reached")
        assert entry is not None
        assert "timeout" in entry.matched_keywords

    def test_multiple_keywords_matched(self, highlighter):
        entry = highlighter.highlight_line("error and timeout both present")
        assert "error" in entry.matched_keywords
        assert "timeout" in entry.matched_keywords

    def test_highlight_file(self, tmp_path, highlighter):
        log = tmp_path / "app.log"
        log.write_text("all ok\nerror connecting\ntimeout waiting\nfinished\n")
        results = highlighter.highlight_file(str(log))
        assert len(results) == 2
        assert results[0].source == str(log)


# ---------------------------------------------------------------------------
# LogKeywordHighlighterBuilder
# ---------------------------------------------------------------------------

class TestLogKeywordHighlighterBuilder:
    def test_build_returns_highlighter(self):
        h = LogKeywordHighlighterBuilder().add_keyword("error").build()
        assert isinstance(h, LogKeywordHighlighter)

    def test_no_keywords_raises(self):
        with pytest.raises(LogKeywordHighlighterBuilderError):
            LogKeywordHighlighterBuilder().build()

    def test_empty_keyword_raises(self):
        with pytest.raises(LogKeywordHighlighterBuilderError):
            LogKeywordHighlighterBuilder().add_keyword("")

    def test_custom_markers(self):
        h = LogKeywordHighlighterBuilder().with_markers("**", "**").add_keyword("warn").build()
        entry = h.highlight_line("warn: low disk")
        assert "**warn**" in entry.highlighted

    def test_add_keywords_bulk(self):
        h = LogKeywordHighlighterBuilder().add_keywords(["error", "critical"]).build()
        entry = h.highlight_line("critical failure")
        assert "critical" in entry.matched_keywords
