"""Tests for ProfileRunner."""

import json
import textwrap
from pathlib import Path

import pytest

from logslice.filter_profile import FilterProfile
from logslice.profile_runner import ProfileRunner
from logslice.stats import SliceStats


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    content = textwrap.dedent("""\
        2024-01-10T10:00:00 INFO  startup complete
        2024-01-10T11:00:00 DEBUG heartbeat
        2024-01-10T12:00:00 ERROR disk full
        2024-01-10T13:00:00 INFO  shutdown
    """)
    p = tmp_path / "app.log"
    p.write_text(content)
    return p


@pytest.fixture()
def profile_file(tmp_path: Path) -> Path:
    data = {
        "name": "midday",
        "start": "2024-01-10T10:30:00",
        "end": "2024-01-10T12:30:00",
    }
    p = tmp_path / "midday.json"
    p.write_text(json.dumps(data))
    return p


class TestProfileRunner:
    def test_run_returns_stats(self, log_file: Path, tmp_path: Path) -> None:
        profile = FilterProfile(
            name="test",
            start="2024-01-10T10:30:00",
            end="2024-01-10T12:30:00",
        )
        runner = ProfileRunner(profile)
        stats = runner.run(log_file)
        assert isinstance(stats, SliceStats)

    def test_run_matches_correct_lines(self, log_file: Path) -> None:
        profile = FilterProfile(
            name="test",
            start="2024-01-10T10:30:00",
            end="2024-01-10T12:30:00",
        )
        runner = ProfileRunner(profile)
        stats = runner.run(log_file)
        # Lines at 11:00 and 12:00 fall within the range
        assert stats.matched == 2

    def test_run_writes_output_file(self, log_file: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.txt"
        profile = FilterProfile(
            name="test",
            start="2024-01-10T10:30:00",
            end="2024-01-10T12:30:00",
        )
        runner = ProfileRunner(profile)
        runner.run(log_file, output_path=out)
        assert out.exists()
        assert out.stat().st_size > 0

    def test_from_json_file(self, log_file: Path, profile_file: Path) -> None:
        runner = ProfileRunner.from_json_file(profile_file)
        stats = runner.run(log_file)
        assert stats.matched == 2

    def test_run_with_json_output_format(self, log_file: Path, tmp_path: Path) -> None:
        out = tmp_path / "out.json"
        profile = FilterProfile(
            name="test",
            start="2024-01-10T10:30:00",
            end="2024-01-10T12:30:00",
            output_format="json",
        )
        runner = ProfileRunner(profile)
        runner.run(log_file, output_path=out)
        text = out.read_text()
        assert text.startswith("[")
