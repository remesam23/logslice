"""Tests for OutputRouter and OutputRouterBuilder."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from logslice.output_router import OutputRouter, OutputRouterError
from logslice.output_router_builder import OutputRouterBuilder
from logslice.formatter import PlainFormatter, JSONFormatter

SAMPLE_ENTRIES = [
    {"timestamp": "2024-01-01 10:00:00", "raw": "line one"},
    {"timestamp": "2024-01-01 10:01:00", "raw": "line two"},
]


# ---------------------------------------------------------------------------
# OutputRouter – stdout routing
# ---------------------------------------------------------------------------

class TestOutputRouterStdout:
    def test_write_plain_to_stdout(self, capsys):
        router = OutputRouter(formatter=PlainFormatter())
        router.write(SAMPLE_ENTRIES)
        captured = capsys.readouterr()
        assert "line one" in captured.out
        assert "line two" in captured.out

    def test_write_json_to_stdout(self, capsys):
        router = OutputRouter(formatter=JSONFormatter())
        router.write(SAMPLE_ENTRIES)
        captured = capsys.readouterr()
        data = json.loads(captured.out.strip())
        assert isinstance(data, list)
        assert len(data) == 2

    def test_write_empty_entries(self, capsys):
        router = OutputRouter()
        router.write([])
        captured = capsys.readouterr()
        assert captured.out is not None


# ---------------------------------------------------------------------------
# OutputRouter – file routing
# ---------------------------------------------------------------------------

class TestOutputRouterFile:
    def test_write_plain_to_file(self, tmp_path):
        out = tmp_path / "out.log"
        router = OutputRouter(formatter=PlainFormatter(), output_file=out)
        with router:
            router.write(SAMPLE_ENTRIES)
        assert "line one" in out.read_text()

    def test_write_json_to_file(self, tmp_path):
        out = tmp_path / "out.json"
        router = OutputRouter(formatter=JSONFormatter(), output_file=out)
        with router:
            router.write(SAMPLE_ENTRIES)
        data = json.loads(out.read_text())
        assert len(data) == 2

    def test_also_stdout_flag(self, tmp_path, capsys):
        out = tmp_path / "out.log"
        router = OutputRouter(formatter=PlainFormatter(), output_file=out, also_stdout=True)
        with router:
            router.write(SAMPLE_ENTRIES)
        captured = capsys.readouterr()
        assert "line one" in captured.out
        assert "line one" in out.read_text()

    def test_write_without_open_raises(self, tmp_path):
        out = tmp_path / "out.log"
        router = OutputRouter(output_file=out)
        with pytest.raises(OutputRouterError, match="open\(\)"):
            router.write(SAMPLE_ENTRIES)

    def test_invalid_path_raises(self, tmp_path):
        bad = tmp_path / "no_dir" / "out.log"
        router = OutputRouter(output_file=bad)
        with pytest.raises(OutputRouterError, match="Cannot open"):
            router.open()


# ---------------------------------------------------------------------------
# OutputRouterBuilder
# ---------------------------------------------------------------------------

class TestOutputRouterBuilder:
    def test_builds_default_router(self):
        router = OutputRouterBuilder().build()
        assert isinstance(router, OutputRouter)
        assert isinstance(router.formatter, PlainFormatter)

    def test_with_json_format(self):
        router = OutputRouterBuilder().with_format("json").build()
        assert isinstance(router.formatter, JSONFormatter)

    def test_with_plain_format(self):
        router = OutputRouterBuilder().with_format("plain").build()
        assert isinstance(router.formatter, PlainFormatter)

    def test_invalid_format_raises(self):
        from logslice.validator import ValidationError
        with pytest.raises(ValidationError):
            OutputRouterBuilder().with_format("xml")

    def test_with_output_file(self, tmp_path):
        out = tmp_path / "result.log"
        router = OutputRouterBuilder().with_output_file(str(out)).build()
        assert router.output_file == out

    def test_with_also_stdout(self):
        router = OutputRouterBuilder().with_also_stdout().build()
        assert router.also_stdout is True
