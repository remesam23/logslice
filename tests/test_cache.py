"""Tests for logslice.cache module."""

import json
import os
import pytest
from datetime import datetime
from unittest.mock import patch

from logslice.cache import LogCache, _file_fingerprint


@pytest.fixture
def tmp_cache(tmp_path):
    return LogCache(cache_dir=str(tmp_path / "cache"))


@pytest.fixture
def sample_log(tmp_path):
    log = tmp_path / "app.log"
    log.write_text("2024-01-01T00:00:00 INFO started\n")
    return str(log)


class TestLogCache:
    def test_get_returns_none_for_missing_file(self, tmp_cache):
        result = tmp_cache.get("/nonexistent/file.log")
        assert result is None

    def test_get_returns_none_when_no_cache(self, tmp_cache, sample_log):
        result = tmp_cache.get(sample_log)
        assert result is None

    def test_set_and_get_roundtrip(self, tmp_cache, sample_log):
        metadata = {"line_count": 42, "format": "iso8601"}
        tmp_cache.set(sample_log, metadata)
        result = tmp_cache.get(sample_log)
        assert result == metadata

    def test_set_serializes_datetime(self, tmp_cache, sample_log):
        dt = datetime(2024, 1, 15, 10, 30, 0)
        metadata = {"first_ts": dt, "line_count": 10}
        tmp_cache.set(sample_log, metadata)
        result = tmp_cache.get(sample_log)
        assert result["first_ts"] == "2024-01-15T10:30:00"
        assert result["line_count"] == 10

    def test_invalidate_removes_entry(self, tmp_cache, sample_log):
        tmp_cache.set(sample_log, {"line_count": 5})
        removed = tmp_cache.invalidate(sample_log)
        assert removed is True
        assert tmp_cache.get(sample_log) is None

    def test_invalidate_returns_false_if_no_entry(self, tmp_cache, sample_log):
        result = tmp_cache.invalidate(sample_log)
        assert result is False

    def test_invalidate_missing_file_returns_false(self, tmp_cache):
        result = tmp_cache.invalidate("/does/not/exist.log")
        assert result is False

    def test_clear_removes_all_entries(self, tmp_cache, tmp_path):
        for i in range(3):
            log = tmp_path / f"log{i}.log"
            log.write_text(f"line {i}\n")
            tmp_cache.set(str(log), {"index": i})
        count = tmp_cache.clear()
        assert count == 3
        cache_files = os.listdir(tmp_cache.cache_dir)
        assert len(cache_files) == 0

    def test_cache_invalidated_after_file_change(self, tmp_cache, sample_log):
        tmp_cache.set(sample_log, {"line_count": 1})
        # Overwrite file to change mtime/size
        with open(sample_log, "a") as f:
            f.write("2024-01-01T00:01:00 INFO new line\n")
        # Fingerprint changes, so old cache entry is not found
        result = tmp_cache.get(sample_log)
        assert result is None

    def test_fingerprint_changes_with_content(self, tmp_path):
        log = tmp_path / "test.log"
        log.write_text("original\n")
        fp1 = _file_fingerprint(str(log))
        log.write_text("original\nmore content\n")
        fp2 = _file_fingerprint(str(log))
        assert fp1 != fp2
