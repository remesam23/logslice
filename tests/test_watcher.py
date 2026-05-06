"""Tests for LogWatcher and WatcherBuilder."""

import os
import pytest
from datetime import datetime

from logslice.watcher_builder import WatcherBuilder
from logslice.watcher import LogWatcher


LOG_LINES = [
    "2024-03-10T10:00:01 INFO  service started\n",
    "2024-03-10T10:00:05 DEBUG heartbeat\n",
    "2024-03-10T10:00:09 ERROR disk full\n",
    "2024-03-10T10:00:15 INFO  recovered\n",
]


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text("".join(LOG_LINES), encoding="utf-8")
    return str(p)


def _build(log_file, start="2024-03-10T10:00:00", end="2024-03-10T10:00:10", max_idle=0.1):
    return (
        WatcherBuilder(log_file)
        .with_start(start)
        .with_end(end)
        .with_max_idle(max_idle)
        .build()
    )


class TestWatcherBuilder:
    def test_returns_log_watcher(self, log_file):
        watcher = _build(log_file)
        assert isinstance(watcher, LogWatcher)

    def test_missing_start_raises(self, log_file):
        with pytest.raises(ValueError, match="start"):
            WatcherBuilder(log_file).with_end("2024-03-10T10:00:10").build()

    def test_missing_end_raises(self, log_file):
        with pytest.raises(ValueError, match="end"):
            WatcherBuilder(log_file).with_start("2024-03-10T10:00:00").build()

    def test_inverted_range_raises(self, log_file):
        with pytest.raises(Exception):
            _build(log_file, start="2024-03-10T10:00:10", end="2024-03-10T10:00:00")


class TestLogWatcher:
    def test_watch_yields_nothing_from_empty_tail(self, log_file):
        # File already written; watcher seeks to end, so no new lines.
        watcher = _build(log_file, max_idle=0.1)
        results = list(watcher.watch())
        assert results == []

    def test_watch_yields_appended_lines(self, tmp_path):
        p = tmp_path / "live.log"
        p.write_text("", encoding="utf-8")
        watcher = _build(str(p), max_idle=0.3)

        import threading

        def _append():
            import time
            time.sleep(0.05)
            with open(str(p), "a", encoding="utf-8") as fh:
                fh.write("2024-03-10T10:00:03 INFO  hello\n")
                fh.write("2024-03-10T10:00:20 INFO  outside range\n")

        t = threading.Thread(target=_append, daemon=True)
        t.start()
        results = list(watcher.watch())
        t.join()

        assert len(results) == 1
        assert results[0]["message"].strip().endswith("hello")
