"""Tests for RoutedPipeline."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

from logslice.config import SliceConfig
from logslice.routed_pipeline import RoutedPipeline

LOG_LINES = [
    "2024-01-01 09:00:00 startup complete",
    "2024-01-01 10:00:00 user login",
    "2024-01-01 10:30:00 request handled",
    "2024-01-01 11:00:00 user logout",
    "2024-01-01 12:00:00 shutdown",
]


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("\n".join(LOG_LINES) + "\n")
    return p


@pytest.fixture()
def basic_config(log_file: Path) -> SliceConfig:
    return SliceConfig.from_dict({
        "log_file": str(log_file),
        "start": "2024-01-01 10:00:00",
        "end": "2024-01-01 11:00:00",
    })


class TestRoutedPipelineStdout:
    def test_run_returns_stats(self, basic_config):
        pipeline = RoutedPipeline.to_stdout(basic_config)
        stats = pipeline.run()
        assert stats.total_matched >= 0

    def test_run_matches_correct_lines(self, basic_config, capsys):
        pipeline = RoutedPipeline.to_stdout(basic_config)
        pipeline.run()
        out = capsys.readouterr().out
        assert "user login" in out
        assert "request handled" in out
        assert "startup complete" not in out
        assert "shutdown" not in out

    def test_run_json_output(self, basic_config, capsys):
        pipeline = RoutedPipeline.to_stdout(basic_config, fmt="json")
        pipeline.run()
        out = capsys.readouterr().out
        data = json.loads(out.strip())
        assert isinstance(data, list)
        assert any("user login" in e.get("raw", "") for e in data)


class TestRoutedPipelineFile:
    def test_run_writes_to_file(self, basic_config, tmp_path):
        out = tmp_path / "result.log"
        pipeline = RoutedPipeline.to_file(basic_config, str(out))
        pipeline.run()
        content = out.read_text()
        assert "user login" in content

    def test_run_json_to_file(self, basic_config, tmp_path):
        out = tmp_path / "result.json"
        pipeline = RoutedPipeline.to_file(basic_config, str(out), fmt="json")
        pipeline.run()
        data = json.loads(out.read_text())
        assert isinstance(data, list)

    def test_also_stdout_writes_both(self, basic_config, tmp_path, capsys):
        out = tmp_path / "result.log"
        pipeline = RoutedPipeline.to_file(basic_config, str(out), also_stdout=True)
        pipeline.run()
        captured = capsys.readouterr()
        assert "user login" in captured.out
        assert "user login" in out.read_text()

    def test_match_count_correct(self, basic_config, tmp_path):
        out = tmp_path / "result.log"
        pipeline = RoutedPipeline.to_file(basic_config, str(out))
        stats = pipeline.run()
        # 10:00, 10:30, 11:00 → 3 matches
        assert stats.total_matched == 3
