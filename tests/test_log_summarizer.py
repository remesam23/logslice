import textwrap
from pathlib import Path

import pytest

from logslice.log_summarizer import LogSummarizer, SummaryResult
from logslice.log_summarizer_builder import LogSummarizerBuilder, LogSummarizerBuilderError


LOG_LINES = [
    "2024-01-15T08:00:01 INFO  Service started\n",
    "2024-01-15T08:00:02 DEBUG Loading config\n",
    "2024-01-15T08:00:03 INFO  Service started\n",
    "2024-01-15T08:00:04 ERROR Disk full\n",
    "2024-01-15T08:00:05 WARNING High memory usage\n",
    "2024-01-15T08:00:06 ERROR Disk full\n",
    "not a timestamped line\n",
    "",
]


@pytest.fixture()
def summarizer() -> LogSummarizer:
    return LogSummarizer(top_n=3)


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("".join(LOG_LINES))
    return p


# ---------------------------------------------------------------------------
# SummaryResult
# ---------------------------------------------------------------------------

class TestSummaryResult:
    def test_to_dict_keys(self):
        r = SummaryResult(total_lines=10, matched_lines=8)
        d = r.to_dict()
        assert set(d.keys()) == {
            "total_lines", "matched_lines", "severity_counts",
            "top_messages", "first_timestamp", "last_timestamp",
        }

    def test_summary_string_contains_totals(self):
        r = SummaryResult(total_lines=10, matched_lines=8)
        text = r.summary()
        assert "10" in text
        assert "8" in text


# ---------------------------------------------------------------------------
# LogSummarizer
# ---------------------------------------------------------------------------

class TestLogSummarizer:
    def test_total_lines(self, summarizer):
        result = summarizer.summarize(LOG_LINES)
        assert result.total_lines == len(LOG_LINES)

    def test_matched_lines_excludes_no_timestamp(self, summarizer):
        result = summarizer.summarize(LOG_LINES)
        # 6 lines have timestamps; blank line and plain text line are skipped
        assert result.matched_lines == 6

    def test_severity_counts_error(self, summarizer):
        result = summarizer.summarize(LOG_LINES)
        assert result.severity_counts.get("ERROR") == 2

    def test_severity_counts_info(self, summarizer):
        result = summarizer.summarize(LOG_LINES)
        assert result.severity_counts.get("INFO") == 2

    def test_first_and_last_timestamp(self, summarizer):
        result = summarizer.summarize(LOG_LINES)
        assert result.first_timestamp is not None
        assert result.last_timestamp is not None
        assert result.first_timestamp <= result.last_timestamp

    def test_top_messages_length(self, summarizer):
        result = summarizer.summarize(LOG_LINES)
        assert len(result.top_messages) <= 3

    def test_top_message_most_common(self, summarizer):
        result = summarizer.summarize(LOG_LINES)
        top_msg, top_count = result.top_messages[0]
        assert top_count >= 2  # "Disk full" or "Service started" appear twice

    def test_summarize_file(self, summarizer, log_file):
        result = summarizer.summarize_file(str(log_file))
        assert result.total_lines == len(LOG_LINES)

    def test_empty_input(self, summarizer):
        result = summarizer.summarize([])
        assert result.total_lines == 0
        assert result.matched_lines == 0
        assert result.first_timestamp is None


# ---------------------------------------------------------------------------
# LogSummarizerBuilder
# ---------------------------------------------------------------------------

class TestLogSummarizerBuilder:
    def test_build_returns_summarizer(self):
        s = LogSummarizerBuilder().build()
        assert isinstance(s, LogSummarizer)

    def test_custom_top_n(self):
        s = LogSummarizerBuilder().with_top_n(10).build()
        result = s.summarize(LOG_LINES)
        assert len(result.top_messages) <= 10

    def test_invalid_top_n_raises(self):
        with pytest.raises(LogSummarizerBuilderError):
            LogSummarizerBuilder().with_top_n(0)

    def test_empty_formats_raises(self):
        with pytest.raises(LogSummarizerBuilderError):
            LogSummarizerBuilder().with_timestamp_formats([])

    def test_custom_formats_accepted(self):
        s = (
            LogSummarizerBuilder()
            .with_timestamp_formats(["%Y-%m-%dT%H:%M:%S"])
            .build()
        )
        assert isinstance(s, LogSummarizer)
