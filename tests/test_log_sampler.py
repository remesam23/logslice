"""Tests for LogSampler and LogSamplerBuilder."""

import os
import textwrap
from pathlib import Path

import pytest

from logslice.log_sampler import LogSampler, SampleResult
from logslice.log_sampler_builder import LogSamplerBuilder


@pytest.fixture()
def log_file(tmp_path: Path) -> str:
    content = textwrap.dedent("""\
        2024-01-01 08:00:00 startup complete
        2024-01-01 09:00:00 user login alice
        2024-01-01 10:00:00 user login bob
        2024-01-01 11:00:00 warning disk usage 80%
        2024-01-01 12:00:00 user logout alice
        2024-01-01 13:00:00 error connection refused
        2024-01-01 14:00:00 user login carol
        2024-01-01 15:00:00 shutdown initiated
    """)
    p = tmp_path / "app.log"
    p.write_text(content)
    return str(p)


def _builder(start: str, end: str, max_samples: int = 100) -> LogSampler:
    return (
        LogSamplerBuilder()
        .with_start(start)
        .with_end(end)
        .with_max_samples(max_samples)
        .build()
    )


class TestSampleResult:
    def test_is_exact_when_all_fit(self):
        r = SampleResult(entries=[{}, {}], total_matched=2, sample_size=2, step=1)
        assert r.is_exact is True

    def test_not_exact_when_sampled(self):
        r = SampleResult(entries=[{}], total_matched=10, sample_size=1, step=10)
        assert r.is_exact is False

    def test_to_dict_keys(self):
        r = SampleResult(entries=[], total_matched=0, sample_size=0, step=1)
        d = r.to_dict()
        assert set(d.keys()) == {"total_matched", "sample_size", "step", "is_exact", "entries"}


class TestLogSampler:
    def test_returns_all_when_within_max(self, log_file):
        sampler = _builder("2024-01-01 08:00:00", "2024-01-01 15:00:00", max_samples=100)
        result = sampler.sample_file(log_file)
        assert result.total_matched == 8
        assert result.sample_size == 8
        assert result.is_exact is True

    def test_samples_when_exceeds_max(self, log_file):
        sampler = _builder("2024-01-01 08:00:00", "2024-01-01 15:00:00", max_samples=3)
        result = sampler.sample_file(log_file)
        assert result.total_matched == 8
        assert result.sample_size <= 3
        assert result.step > 1

    def test_empty_result_outside_range(self, log_file):
        sampler = _builder("2023-01-01 00:00:00", "2023-01-01 01:00:00")
        result = sampler.sample_file(log_file)
        assert result.total_matched == 0
        assert result.entries == []

    def test_partial_range(self, log_file):
        sampler = _builder("2024-01-01 09:00:00", "2024-01-01 11:00:00")
        result = sampler.sample_file(log_file)
        assert result.total_matched == 3


class TestLogSamplerBuilder:
    def test_missing_start_raises(self):
        with pytest.raises(ValueError, match="start"):
            LogSamplerBuilder().with_end("2024-01-01 12:00:00").build()

    def test_missing_end_raises(self):
        with pytest.raises(ValueError, match="end"):
            LogSamplerBuilder().with_start("2024-01-01 08:00:00").build()

    def test_invalid_max_samples_raises(self):
        with pytest.raises(ValueError):
            LogSamplerBuilder().with_max_samples(0)

    def test_inverted_range_raises(self):
        with pytest.raises(Exception):
            LogSamplerBuilder()\
                .with_start("2024-01-01 12:00:00")\
                .with_end("2024-01-01 08:00:00")\
                .build()
