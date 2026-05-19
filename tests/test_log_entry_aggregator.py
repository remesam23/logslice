import pytest

from logslice.log_entry_aggregator import (
    AggregatedGroup,
    AggregationResult,
    EntryAggregatorError,
    LogEntryAggregator,
)

LOG_LINES = [
    "2024-01-01 INFO service=auth user logged in\n",
    "2024-01-01 ERROR service=db connection refused\n",
    "2024-01-01 INFO service=auth token refreshed\n",
    "2024-01-01 WARN service=cache eviction triggered\n",
    "2024-01-01 ERROR service=auth invalid token\n",
    "no-match line without service tag\n",
]


@pytest.fixture
def aggregator():
    return LogEntryAggregator(pattern=r"service=(\w+)", group=1, keep_lines=True)


class TestAggregatedGroup:
    def test_to_dict_keys(self):
        grp = AggregatedGroup(key="auth", count=2, lines=["a", "b"], first_line="a", last_line="b")
        d = grp.to_dict()
        assert set(d.keys()) == {"key", "count", "first_line", "last_line", "lines"}

    def test_summary_format(self):
        grp = AggregatedGroup(key="db", count=5, lines=[])
        assert "db" in grp.summary()
        assert "5" in grp.summary()


class TestAggregationResult:
    def test_to_dict_keys(self):
        result = AggregationResult()
        d = result.to_dict()
        assert "total_lines" in d
        assert "unmatched_lines" in d
        assert "groups" in d

    def test_summary_contains_totals(self):
        result = AggregationResult(total_lines=10, unmatched_lines=2)
        s = result.summary()
        assert "10" in s
        assert "2" in s


class TestLogEntryAggregator:
    def test_group_counts(self, aggregator):
        result = aggregator.aggregate(LOG_LINES)
        assert result.groups["auth"].count == 3
        assert result.groups["db"].count == 1
        assert result.groups["cache"].count == 1

    def test_total_lines(self, aggregator):
        result = aggregator.aggregate(LOG_LINES)
        assert result.total_lines == len(LOG_LINES)

    def test_unmatched_lines(self, aggregator):
        result = aggregator.aggregate(LOG_LINES)
        assert result.unmatched_lines == 1

    def test_first_and_last_line(self, aggregator):
        result = aggregator.aggregate(LOG_LINES)
        auth = result.groups["auth"]
        assert "logged in" in auth.first_line
        assert "invalid token" in auth.last_line

    def test_keep_lines_false_does_not_store(self):
        agg = LogEntryAggregator(pattern=r"service=(\w+)", group=1, keep_lines=False)
        result = agg.aggregate(LOG_LINES)
        assert result.groups["auth"].lines == []

    def test_keep_lines_true_stores_all(self, aggregator):
        result = aggregator.aggregate(LOG_LINES)
        assert len(result.groups["auth"].lines) == 3

    def test_empty_pattern_raises(self):
        with pytest.raises(EntryAggregatorError, match="pattern"):
            LogEntryAggregator(pattern="")

    def test_invalid_regex_raises(self):
        with pytest.raises(EntryAggregatorError, match="invalid regex"):
            LogEntryAggregator(pattern="[unclosed")

    def test_invalid_group_index_raises(self):
        with pytest.raises(EntryAggregatorError, match="group"):
            LogEntryAggregator(pattern=r"(\w+)", group=0)

    def test_empty_lines_returns_zero_totals(self, aggregator):
        result = aggregator.aggregate([])
        assert result.total_lines == 0
        assert result.groups == {}
