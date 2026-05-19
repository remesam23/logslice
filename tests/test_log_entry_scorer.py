import pytest

from logslice.log_entry_scorer import (
    EntryScorerError,
    LogEntryScorer,
    ScoredEntry,
    ScoringRule,
)
from logslice.log_entry_scorer_builder import (
    LogEntryScorerBuilder,
    LogEntryScorerBuilderError,
)


# ---------------------------------------------------------------------------
# ScoringRule
# ---------------------------------------------------------------------------


class TestScoringRule:
    def test_empty_name_raises(self):
        with pytest.raises(EntryScorerError, match="name"):
            ScoringRule(name="", pattern="error", score=1.0)

    def test_empty_pattern_raises(self):
        with pytest.raises(EntryScorerError, match="pattern"):
            ScoringRule(name="r", pattern="", score=1.0)

    def test_invalid_regex_raises(self):
        with pytest.raises(EntryScorerError, match="Invalid regex"):
            ScoringRule(name="r", pattern="[unclosed", score=1.0)

    def test_matches_true(self):
        rule = ScoringRule(name="err", pattern=r"ERROR", score=5.0)
        assert rule.matches("2024-01-01 ERROR something broke")

    def test_matches_false(self):
        rule = ScoringRule(name="err", pattern=r"ERROR", score=5.0)
        assert not rule.matches("2024-01-01 INFO all good")


# ---------------------------------------------------------------------------
# ScoredEntry
# ---------------------------------------------------------------------------


class TestScoredEntry:
    def test_to_dict_keys(self):
        entry = ScoredEntry(line="foo", total_score=3.0, matched_rules=["a"])
        assert set(entry.to_dict().keys()) == {"line", "total_score", "matched_rules"}

    def test_to_dict_values(self):
        entry = ScoredEntry(line="bar", total_score=7.5, matched_rules=["x", "y"])
        d = entry.to_dict()
        assert d["total_score"] == 7.5
        assert d["matched_rules"] == ["x", "y"]


# ---------------------------------------------------------------------------
# LogEntryScorer
# ---------------------------------------------------------------------------


@pytest.fixture()
def scorer():
    rules = [
        ScoringRule(name="error", pattern=r"ERROR", score=10.0),
        ScoringRule(name="timeout", pattern=r"timeout", score=5.0),
    ]
    return LogEntryScorer(rules=rules)


class TestLogEntryScorer:
    def test_no_rules_raises(self):
        with pytest.raises(EntryScorerError):
            LogEntryScorer(rules=[])

    def test_score_line_no_match(self, scorer):
        entry = scorer.score_line("INFO everything fine")
        assert entry.total_score == 0.0
        assert entry.matched_rules == []

    def test_score_line_single_match(self, scorer):
        entry = scorer.score_line("ERROR disk full")
        assert entry.total_score == 10.0
        assert "error" in entry.matched_rules

    def test_score_line_multiple_matches(self, scorer):
        entry = scorer.score_line("ERROR connection timeout")
        assert entry.total_score == 15.0
        assert set(entry.matched_rules) == {"error", "timeout"}

    def test_score_lines_no_threshold(self, scorer):
        lines = ["INFO ok", "ERROR boom", "WARN timeout"]
        results = scorer.score_lines(lines)
        assert len(results) == 3

    def test_score_lines_with_threshold(self):
        rules = [ScoringRule(name="e", pattern="ERROR", score=10.0)]
        s = LogEntryScorer(rules=rules, threshold=5.0)
        lines = ["INFO ok", "ERROR boom"]
        results = s.score_lines(lines)
        assert len(results) == 1
        assert results[0].total_score == 10.0


# ---------------------------------------------------------------------------
# LogEntryScorerBuilder
# ---------------------------------------------------------------------------


class TestLogEntryScorerBuilder:
    def test_returns_scorer(self):
        scorer = (
            LogEntryScorerBuilder()
            .add_rule("err", r"ERROR", 10.0)
            .build()
        )
        assert isinstance(scorer, LogEntryScorer)

    def test_no_rules_raises(self):
        with pytest.raises(LogEntryScorerBuilderError, match="no rules"):
            LogEntryScorerBuilder().build()

    def test_invalid_regex_raises(self):
        with pytest.raises(LogEntryScorerBuilderError):
            LogEntryScorerBuilder().add_rule("bad", "[open", 1.0)

    def test_with_threshold_sets_value(self):
        scorer = (
            LogEntryScorerBuilder()
            .add_rule("e", "ERROR", 5.0)
            .with_threshold(3.0)
            .build()
        )
        assert scorer.threshold == 3.0

    def test_invalid_threshold_raises(self):
        with pytest.raises(LogEntryScorerBuilderError, match="numeric"):
            LogEntryScorerBuilder().with_threshold("high")  # type: ignore
