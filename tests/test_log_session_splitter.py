"""Tests for LogSessionSplitter and LogSessionSplitterBuilder."""
from __future__ import annotations

import os
import textwrap
from datetime import timedelta

import pytest

from logslice.log_session_splitter import (
    LogSession,
    LogSessionSplitter,
    SessionSplitterError,
)
from logslice.log_session_splitter_builder import (
    LogSessionSplitterBuilder,
    LogSessionSplitterBuilderError,
)


LINES_TWO_SESSIONS = [
    "2024-01-01 10:00:00 INFO  login user=alice\n",
    "2024-01-01 10:00:05 INFO  request GET /api\n",
    "2024-01-01 10:05:00 INFO  request GET /api\n",  # > 60 s gap → new session
    "2024-01-01 10:05:10 INFO  logout user=alice\n",
]

LINES_ONE_SESSION = [
    "2024-01-01 09:00:00 INFO  start\n",
    "2024-01-01 09:00:30 INFO  middle\n",
    "2024-01-01 09:00:59 INFO  end\n",
]


@pytest.fixture
def splitter() -> LogSessionSplitter:
    return LogSessionSplitter(gap=timedelta(seconds=60))


class TestLogSession:
    def test_to_dict_keys(self):
        s = LogSession(index=0)
        keys = s.to_dict().keys()
        assert {"index", "entry_count", "start", "end", "duration_seconds"} == set(keys)

    def test_duration_none_when_no_timestamps(self):
        s = LogSession(index=0)
        assert s.duration is None

    def test_duration_computed(self):
        from datetime import datetime
        s = LogSession(
            index=0,
            start=datetime(2024, 1, 1, 10, 0, 0),
            end=datetime(2024, 1, 1, 10, 0, 30),
        )
        assert s.duration == timedelta(seconds=30)


class TestLogSessionSplitter:
    def test_splits_into_two_sessions(self, splitter):
        sessions = splitter.split(LINES_TWO_SESSIONS)
        assert len(sessions) == 2

    def test_single_session_when_no_gap(self, splitter):
        sessions = splitter.split(LINES_ONE_SESSION)
        assert len(sessions) == 1

    def test_entry_counts_correct(self, splitter):
        sessions = splitter.split(LINES_TWO_SESSIONS)
        assert sessions[0].entry_count == 2  # LogSession has no entry_count attr; use len
        # use to_dict for entry_count
        assert sessions[0].to_dict()["entry_count"] == 2
        assert sessions[1].to_dict()["entry_count"] == 2

    def test_empty_lines_ignored(self, splitter):
        sessions = splitter.split(["\n", "  \n", "\n"])
        assert sessions == []

    def test_session_indices_sequential(self, splitter):
        sessions = splitter.split(LINES_TWO_SESSIONS)
        assert [s.index for s in sessions] == [0, 1]

    def test_negative_gap_raises(self):
        with pytest.raises(SessionSplitterError):
            LogSessionSplitter(gap=timedelta(seconds=-1))

    def test_split_file_missing_raises(self, splitter):
        with pytest.raises(SessionSplitterError):
            splitter.split_file("/nonexistent/path/file.log")

    def test_split_file_reads_correctly(self, splitter, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("".join(LINES_TWO_SESSIONS), encoding="utf-8")
        sessions = splitter.split_file(str(log))
        assert len(sessions) == 2


class TestLogSessionSplitterBuilder:
    def test_missing_gap_raises(self):
        with pytest.raises(LogSessionSplitterBuilderError):
            LogSessionSplitterBuilder().build()

    def test_zero_gap_raises(self):
        with pytest.raises(LogSessionSplitterBuilderError):
            LogSessionSplitterBuilder().with_gap_seconds(0)

    def test_returns_splitter_instance(self):
        splitter = LogSessionSplitterBuilder().with_gap_seconds(30).build()
        assert isinstance(splitter, LogSessionSplitter)

    def test_custom_formats_accepted(self):
        splitter = (
            LogSessionSplitterBuilder()
            .with_gap_seconds(60)
            .with_timestamp_formats(["%Y-%m-%d %H:%M:%S"])
            .build()
        )
        assert isinstance(splitter, LogSessionSplitter)
