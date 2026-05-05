"""Tests for the Pipeline orchestrator."""

from __future__ import annotations

import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.pipeline import Pipeline
from logslice.config import SliceConfig


SAMPLE_LOG = textwrap.dedent("""\
    2024-01-15T08:00:00 INFO  startup complete
    2024-01-15T09:30:00 DEBUG request received
    2024-01-15T10:00:00 INFO  processing
    2024-01-15T11:00:00 ERROR something failed
    2024-01-15T12:00:00 INFO  shutdown
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text(SAMPLE_LOG)
    return p


@pytest.fixture()
def basic_config() -> SliceConfig:
    return SliceConfig.from_dict({
        "start": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        "end": datetime(2024, 1, 15, 11, 30, tzinfo=timezone.utc),
        "output_format": "plain",
    })


def test_pipeline_returns_stats(log_file, basic_config):
    pipeline = Pipeline(basic_config)
    stats = pipeline.run(log_file)
    assert stats.matched >= 0
    assert stats.skipped >= 0


def test_pipeline_match_count(log_file, basic_config, capsys):
    pipeline = Pipeline(basic_config)
    stats = pipeline.run(log_file)
    # Lines at 09:30, 10:00, 11:00 fall within [09:00, 11:30]
    assert stats.matched == 3


def test_pipeline_json_output(tmp_path, basic_config):
    log_file = tmp_path / "app.log"
    log_file.write_text(SAMPLE_LOG)
    out_file = tmp_path / "out.json"
    config = SliceConfig.from_dict({
        "start": datetime(2024, 1, 15, 9, 0, tzinfo=timezone.utc),
        "end": datetime(2024, 1, 15, 11, 30, tzinfo=timezone.utc),
        "output_format": "json",
        "output_path": str(out_file),
    })
    pipeline = Pipeline(config)
    pipeline.run(log_file)
    data = json.loads(out_file.read_text())
    assert isinstance(data, list)
    assert len(data) == 3


def test_pipeline_missing_file_raises(basic_config):
    pipeline = Pipeline(basic_config)
    with pytest.raises(Exception):
        pipeline.run("/nonexistent/path/app.log")


def test_pipeline_empty_log(tmp_path, basic_config):
    empty = tmp_path / "empty.log"
    empty.write_text("")
    pipeline = Pipeline(basic_config)
    stats = pipeline.run(empty)
    assert stats.matched == 0
