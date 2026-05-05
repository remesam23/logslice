"""Tests for logslice.exporter.LogExporter."""

import json
import pytest
from pathlib import Path
from unittest.mock import patch
import io

from logslice.exporter import LogExporter


SAMPLE_ENTRIES = [
    {"timestamp": "2024-01-15T10:00:00", "level": "INFO", "message": "Service started"},
    {"timestamp": "2024-01-15T10:05:00", "level": "WARNING", "message": "High memory usage"},
    {"timestamp": "2024-01-15T10:10:00", "level": "ERROR", "message": "Connection refused"},
]


def test_invalid_format_raises():
    with pytest.raises(ValueError, match="Unsupported format"):
        LogExporter(fmt="xml")


def test_export_plain_to_stdout(capsys):
    exporter = LogExporter(fmt="plain")
    count = exporter.export(SAMPLE_ENTRIES)
    captured = capsys.readouterr()
    assert count == 3
    assert "Service started" in captured.out
    assert "High memory usage" in captured.out
    assert "Connection refused" in captured.out


def test_export_json_to_stdout(capsys):
    exporter = LogExporter(fmt="json")
    count = exporter.export(SAMPLE_ENTRIES)
    captured = capsys.readouterr()
    assert count == 3
    lines = [l for l in captured.out.strip().splitlines() if l]
    parsed = [json.loads(line) for line in lines]
    assert parsed[0]["level"] == "INFO"
    assert parsed[2]["message"] == "Connection refused"


def test_export_empty_entries(capsys):
    exporter = LogExporter(fmt="plain")
    count = exporter.export([])
    assert count == 0
    captured = capsys.readouterr()
    assert captured.out == ""


def test_export_plain_to_file(tmp_path):
    out_file = tmp_path / "output.log"
    exporter = LogExporter(fmt="plain", output_path=out_file)
    count = exporter.export(SAMPLE_ENTRIES)
    assert count == 3
    assert out_file.exists()
    content = out_file.read_text()
    assert "Service started" in content
    assert "Connection refused" in content


def test_export_json_to_file(tmp_path):
    out_file = tmp_path / "output.jsonl"
    exporter = LogExporter(fmt="json", output_path=out_file)
    count = exporter.export(SAMPLE_ENTRIES)
    assert count == 3
    lines = [l for l in out_file.read_text().strip().splitlines() if l]
    assert len(lines) == 3
    assert json.loads(lines[1])["level"] == "WARNING"


def test_export_creates_nested_output_dir(tmp_path):
    out_file = tmp_path / "nested" / "deep" / "output.log"
    exporter = LogExporter(fmt="plain", output_path=out_file)
    exporter.export(SAMPLE_ENTRIES)
    assert out_file.exists()
