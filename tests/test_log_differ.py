"""Tests for LogDiffer and DiffResult."""

import pytest
from logslice.log_differ import LogDiffer, DiffResult
from logslice.log_differ_builder import LogDifferBuilder, LogDifferBuilderError


LINES_A = [
    "2024-01-01T10:00:00 INFO  service started\n",
    "2024-01-01T10:01:00 DEBUG heartbeat\n",
    "2024-01-01T10:02:00 ERROR disk full\n",
]

LINES_B = [
    "2024-01-01T10:00:00 INFO  service started\n",
    "2024-01-01T10:01:00 DEBUG heartbeat\n",
    "2024-01-01T10:03:00 WARN  memory high\n",
]


@pytest.fixture
def differ():
    return LogDiffer()


class TestDiffResult:
    def test_has_changes_when_diffs_exist(self):
        result = DiffResult(added=["x"], removed=[], common=[])
        assert result.has_changes is True

    def test_no_changes_when_identical(self):
        result = DiffResult(added=[], removed=[], common=["x"])
        assert result.has_changes is False

    def test_to_dict_keys(self):
        result = DiffResult(added=["a"], removed=["b"], common=["c"])
        d = result.to_dict()
        assert set(d.keys()) == {"added", "removed", "common", "has_changes"}

    def test_to_dict_counts(self):
        result = DiffResult(added=["a", "b"], removed=["c"], common=[])
        d = result.to_dict()
        assert d["added"] == 2
        assert d["removed"] == 1

    def test_summary_format(self):
        result = DiffResult(added=["a"], removed=["b", "c"], common=["d"])
        assert "+1 added" in result.summary()
        assert "-2 removed" in result.summary()
        assert "=1 common" in result.summary()


class TestLogDiffer:
    def test_added_lines(self, differ):
        result = differ.diff(LINES_A, LINES_B)
        assert any("WARN" in l for l in result.added)

    def test_removed_lines(self, differ):
        result = differ.diff(LINES_A, LINES_B)
        assert any("ERROR" in l for l in result.removed)

    def test_common_lines(self, differ):
        result = differ.diff(LINES_A, LINES_B)
        assert any("INFO" in l for l in result.common)
        assert any("DEBUG" in l for l in result.common)

    def test_identical_inputs_no_changes(self, differ):
        result = differ.diff(LINES_A, LINES_A)
        assert not result.has_changes
        assert len(result.common) == len(LINES_A)

    def test_empty_baseline(self, differ):
        result = differ.diff([], LINES_B)
        assert len(result.added) == len(LINES_B)
        assert result.removed == []

    def test_empty_current(self, differ):
        result = differ.diff(LINES_A, [])
        assert len(result.removed) == len(LINES_A)
        assert result.added == []

    def test_strip_whitespace_normalizes(self):
        d = LogDiffer(strip_whitespace=True)
        result = d.diff(["  hello\n"], ["hello"])
        assert not result.has_changes

    def test_no_strip_treats_differently(self):
        d = LogDiffer(strip_whitespace=False)
        result = d.diff(["  hello\n"], ["hello"])
        assert result.has_changes

    def test_diff_files(self, tmp_path, differ):
        f1 = tmp_path / "a.log"
        f2 = tmp_path / "b.log"
        f1.write_text("".join(LINES_A))
        f2.write_text("".join(LINES_B))
        result = differ.diff_files(str(f1), str(f2))
        assert result.has_changes


class TestLogDifferBuilder:
    def test_missing_baseline_raises(self):
        with pytest.raises(LogDifferBuilderError, match="baseline"):
            LogDifferBuilder().with_current("/tmp/b.log").run()

    def test_missing_current_raises(self):
        with pytest.raises(LogDifferBuilderError, match="current"):
            LogDifferBuilder().with_baseline("/tmp/a.log").run()

    def test_run_returns_diff_result(self, tmp_path):
        f1 = tmp_path / "a.log"
        f2 = tmp_path / "b.log"
        f1.write_text("".join(LINES_A))
        f2.write_text("".join(LINES_B))
        result = (
            LogDifferBuilder()
            .with_baseline(str(f1))
            .with_current(str(f2))
            .run()
        )
        assert isinstance(result, DiffResult)
        assert result.has_changes
