"""Tests for LogMerger and LogMergerBuilder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.log_merger import LogMerger, MergedEntry
from logslice.log_merger_builder import LogMergerBuilder, LogMergerBuilderError


@pytest.fixture()
def log_dir(tmp_path: Path) -> Path:
    return tmp_path


@pytest.fixture()
def file_a(log_dir: Path) -> Path:
    p = log_dir / "a.log"
    p.write_text(
        "2024-01-01T08:00:00 alpha first\n"
        "2024-01-01T10:00:00 alpha third\n"
    )
    return p


@pytest.fixture()
def file_b(log_dir: Path) -> Path:
    p = log_dir / "b.log"
    p.write_text(
        "2024-01-01T09:00:00 beta second\n"
        "2024-01-01T11:00:00 beta fourth\n"
    )
    return p


class TestLogMerger:
    def test_merge_returns_merged_entries(self, file_a, file_b):
        merger = LogMerger(paths=[file_a, file_b])
        results = list(merger.merge())
        assert all(isinstance(r, MergedEntry) for r in results)

    def test_merge_sorted_by_timestamp(self, file_a, file_b):
        merger = LogMerger(paths=[file_a, file_b])
        results = list(merger.merge())
        timestamps = [r.timestamp for r in results]
        assert timestamps == sorted(timestamps)

    def test_merge_correct_order(self, file_a, file_b):
        merger = LogMerger(paths=[file_a, file_b])
        lines = [r.line.strip() for r in merger.merge()]
        assert "alpha first" in lines[0]
        assert "beta second" in lines[1]
        assert "alpha third" in lines[2]
        assert "beta fourth" in lines[3]

    def test_source_reflects_filename(self, file_a, file_b):
        merger = LogMerger(paths=[file_a, file_b])
        sources = {r.source for r in merger.merge()}
        assert str(file_a) in sources
        assert str(file_b) in sources

    def test_to_dict_contains_expected_keys(self, file_a):
        merger = LogMerger(paths=[file_a])
        entry = next(iter(merger.merge()))
        d = entry.to_dict()
        assert set(d.keys()) == {"timestamp", "source", "line"}

    def test_to_dict_timestamp_is_iso(self, file_a):
        merger = LogMerger(paths=[file_a])
        entry = next(iter(merger.merge()))
        d = entry.to_dict()
        assert "2024-01-01" in d["timestamp"]


class TestLogMergerBuilder:
    def test_build_returns_log_merger(self, file_a):
        merger = LogMergerBuilder().add_file(str(file_a)).build()
        assert isinstance(merger, LogMerger)

    def test_missing_files_raises(self):
        with pytest.raises(LogMergerBuilderError, match="At least one"):
            LogMergerBuilder().build()

    def test_nonexistent_file_raises(self):
        with pytest.raises(LogMergerBuilderError, match="File not found"):
            LogMergerBuilder().add_file("/no/such/file.log")

    def test_add_files_bulk(self, file_a, file_b):
        merger = (
            LogMergerBuilder()
            .add_files([str(file_a), str(file_b)])
            .build()
        )
        assert len(merger.paths) == 2

    def test_with_timestamp_formats_propagates(self, file_a):
        fmt = ["%Y-%m-%dT%H:%M:%S"]
        merger = (
            LogMergerBuilder()
            .add_file(str(file_a))
            .with_timestamp_formats(fmt)
            .build()
        )
        assert merger._parser is not None
