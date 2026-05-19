"""Tests for LogEntryFormatterChain."""

import pytest

from logslice.log_entry_formatter_chain import (
    ChainedEntry,
    FormatterChainError,
    FormatterStep,
    LogEntryFormatterChain,
)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _upper(line: str):
    return line.upper()


def _strip(line: str):
    return line.strip()


def _drop_if_error(line: str):
    if "ERROR" in line:
        return None
    return line


# ---------------------------------------------------------------------------
# ChainedEntry
# ---------------------------------------------------------------------------

class TestChainedEntry:
    def test_to_dict_keys(self):
        entry = ChainedEntry(raw="hello", transformed="HELLO", stages=["upper"])
        assert set(entry.to_dict().keys()) == {"raw", "transformed", "stages"}

    def test_to_dict_values(self):
        entry = ChainedEntry(raw="hello", transformed="HELLO", stages=["upper"])
        d = entry.to_dict()
        assert d["raw"] == "hello"
        assert d["transformed"] == "HELLO"
        assert d["stages"] == ["upper"]


# ---------------------------------------------------------------------------
# FormatterStep
# ---------------------------------------------------------------------------

class TestFormatterStep:
    def test_empty_name_raises(self):
        with pytest.raises(FormatterChainError):
            FormatterStep(name="", fn=_upper)

    def test_non_callable_raises(self):
        with pytest.raises(FormatterChainError):
            FormatterStep(name="upper", fn="not_callable")  # type: ignore


# ---------------------------------------------------------------------------
# LogEntryFormatterChain
# ---------------------------------------------------------------------------

@pytest.fixture
def chain():
    steps = [
        FormatterStep(name="strip", fn=_strip),
        FormatterStep(name="upper", fn=_upper),
    ]
    return LogEntryFormatterChain(steps)


class TestLogEntryFormatterChain:
    def test_no_steps_raises(self):
        with pytest.raises(FormatterChainError):
            LogEntryFormatterChain(steps=[])

    def test_apply_transforms_line(self, chain):
        entry = chain.apply("  hello world  ")
        assert entry is not None
        assert entry.transformed == "HELLO WORLD"

    def test_apply_records_stages(self, chain):
        entry = chain.apply("test")
        assert entry.stages == ["strip", "upper"]

    def test_apply_returns_none_when_step_returns_none(self):
        steps = [FormatterStep(name="drop_errors", fn=_drop_if_error)]
        ch = LogEntryFormatterChain(steps, skip_on_none=True)
        assert ch.apply("2024-01-01 ERROR something") is None

    def test_apply_keeps_value_when_skip_on_none_false(self):
        steps = [FormatterStep(name="drop_errors", fn=_drop_if_error)]
        ch = LogEntryFormatterChain(steps, skip_on_none=False)
        entry = ch.apply("2024-01-01 ERROR something")
        assert entry is not None
        assert entry.transformed == "2024-01-01 ERROR something"

    def test_apply_all_filters_none_entries(self):
        steps = [FormatterStep(name="drop_errors", fn=_drop_if_error)]
        ch = LogEntryFormatterChain(steps)
        lines = ["INFO ok", "ERROR bad", "INFO also ok"]
        results = ch.apply_all(lines)
        assert len(results) == 2
        assert all("ERROR" not in e.transformed for e in results)

    def test_apply_all_empty_input(self, chain):
        assert chain.apply_all([]) == []
