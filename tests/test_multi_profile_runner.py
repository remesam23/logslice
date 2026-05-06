"""Tests for MultiProfileRunner."""

import json
import textwrap
from pathlib import Path

import pytest

from logslice.multi_profile_runner import MultiProfileRunner, MultiProfileError
from logslice.filter_profile import FilterProfile


LOG_CONTENT = textwrap.dedent("""\
    2024-01-10T08:00:00 INFO  startup complete
    2024-01-10T09:15:00 ERROR disk full
    2024-01-10T10:30:00 INFO  request processed
    2024-01-10T11:45:00 WARN  high memory
    2024-01-10T13:00:00 INFO  shutdown
""")


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    p = tmp_path / "app.log"
    p.write_text(LOG_CONTENT)
    return str(p)


@pytest.fixture()
def profiles_file(tmp_path: Path) -> str:
    data = [
        {
            "name": "morning",
            "start": "2024-01-10T08:00:00",
            "end": "2024-01-10T10:00:00",
        },
        {
            "name": "afternoon",
            "start": "2024-01-10T10:00:00",
            "end": "2024-01-10T14:00:00",
        },
    ]
    p = tmp_path / "profiles.json"
    p.write_text(json.dumps(data))
    return str(p)


class TestMultiProfileRunner:
    def test_run_returns_dict_keyed_by_name(self, log_file, profiles_file):
        runner = MultiProfileRunner.from_json_file(log_file, profiles_file)
        results = runner.run()
        assert set(results.keys()) == {"morning", "afternoon"}

    def test_morning_profile_matches_two_lines(self, log_file, profiles_file):
        runner = MultiProfileRunner.from_json_file(log_file, profiles_file)
        results = runner.run()
        assert results["morning"].matched == 2

    def test_afternoon_profile_matches_three_lines(self, log_file, profiles_file):
        runner = MultiProfileRunner.from_json_file(log_file, profiles_file)
        results = runner.run()
        assert results["afternoon"].matched == 3

    def test_summary_includes_profile_key(self, log_file, profiles_file):
        runner = MultiProfileRunner.from_json_file(log_file, profiles_file)
        summary = runner.summary()
        assert len(summary) == 2
        assert all("profile" in entry for entry in summary)

    def test_empty_profiles_raises(self, log_file):
        with pytest.raises(MultiProfileError, match="At least one profile"):
            MultiProfileRunner(log_file, [])

    def test_missing_profiles_file_raises(self, log_file, tmp_path):
        with pytest.raises(MultiProfileError, match="not found"):
            MultiProfileRunner.from_json_file(log_file, str(tmp_path / "nope.json"))

    def test_invalid_json_raises(self, log_file, tmp_path):
        bad = tmp_path / "bad.json"
        bad.write_text("not json")
        with pytest.raises(MultiProfileError, match="Invalid JSON"):
            MultiProfileRunner.from_json_file(log_file, str(bad))

    def test_non_array_json_raises(self, log_file, tmp_path):
        bad = tmp_path / "obj.json"
        bad.write_text(json.dumps({"name": "x"}))
        with pytest.raises(MultiProfileError, match="JSON array"):
            MultiProfileRunner.from_json_file(log_file, str(bad))
