"""Tests for logslice.filter_profile."""

import json
import pytest
from pathlib import Path

from logslice.filter_profile import FilterProfile, FilterProfileError


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MINIMAL = {
    "name": "morning",
    "start": "2024-01-01T08:00:00",
    "end": "2024-01-01T12:00:00",
}

FULL = {
    "name": "debug-window",
    "start": "2024-06-01T00:00:00",
    "end": "2024-06-01T23:59:59",
    "timestamp_format": "%Y-%m-%dT%H:%M:%S",
    "output_format": "json",
    "tags": ["debug", "prod"],
}


# ---------------------------------------------------------------------------
# from_dict
# ---------------------------------------------------------------------------

class TestFromDict:
    def test_minimal_fields(self):
        fp = FilterProfile.from_dict(MINIMAL)
        assert fp.name == "morning"
        assert fp.output_format == "plain"
        assert fp.tags == []
        assert fp.timestamp_format is None

    def test_full_fields(self):
        fp = FilterProfile.from_dict(FULL)
        assert fp.output_format == "json"
        assert fp.tags == ["debug", "prod"]
        assert fp.timestamp_format == "%Y-%m-%dT%H:%M:%S"

    def test_missing_name_raises(self):
        data = {"start": "2024-01-01T00:00:00", "end": "2024-01-01T01:00:00"}
        with pytest.raises(FilterProfileError, match="name"):
            FilterProfile.from_dict(data)

    def test_missing_start_raises(self):
        data = {"name": "x", "end": "2024-01-01T01:00:00"}
        with pytest.raises(FilterProfileError, match="start"):
            FilterProfile.from_dict(data)

    def test_missing_end_raises(self):
        data = {"name": "x", "start": "2024-01-01T00:00:00"}
        with pytest.raises(FilterProfileError, match="end"):
            FilterProfile.from_dict(data)


# ---------------------------------------------------------------------------
# to_dict round-trip
# ---------------------------------------------------------------------------

def test_to_dict_round_trip():
    fp = FilterProfile.from_dict(FULL)
    d = fp.to_dict()
    assert d["name"] == FULL["name"]
    assert d["tags"] == FULL["tags"]
    fp2 = FilterProfile.from_dict(d)
    assert fp2 == fp


# ---------------------------------------------------------------------------
# from_json_file / save
# ---------------------------------------------------------------------------

def test_save_and_load(tmp_path):
    fp = FilterProfile.from_dict(FULL)
    dest = tmp_path / "profile.json"
    fp.save(dest)
    loaded = FilterProfile.from_json_file(dest)
    assert loaded == fp


def test_missing_file_raises(tmp_path):
    with pytest.raises(FilterProfileError, match="not found"):
        FilterProfile.from_json_file(tmp_path / "nonexistent.json")


def test_invalid_json_raises(tmp_path):
    bad = tmp_path / "bad.json"
    bad.write_text("not-json{{{")
    with pytest.raises(FilterProfileError, match="Invalid JSON"):
        FilterProfile.from_json_file(bad)
