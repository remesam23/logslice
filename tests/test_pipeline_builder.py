"""Tests for the PipelineBuilder fluent interface."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.pipeline import Pipeline
from logslice.pipeline_builder import PipelineBuilder


START = datetime(2024, 3, 1, 8, 0, tzinfo=timezone.utc)
END = datetime(2024, 3, 1, 18, 0, tzinfo=timezone.utc)


def test_builder_returns_pipeline():
    pipeline = (
        PipelineBuilder()
        .with_start(START)
        .with_end(END)
        .build()
    )
    assert isinstance(pipeline, Pipeline)


def test_builder_accepts_string_datetimes():
    pipeline = (
        PipelineBuilder()
        .with_start("2024-03-01T08:00:00")
        .with_end("2024-03-01T18:00:00")
        .build()
    )
    assert isinstance(pipeline, Pipeline)


def test_builder_missing_start_raises():
    with pytest.raises(ValueError, match="start"):
        PipelineBuilder().with_end(END).build()


def test_builder_missing_end_raises():
    with pytest.raises(ValueError, match="end"):
        PipelineBuilder().with_start(START).build()


def test_builder_custom_output_format():
    pipeline = (
        PipelineBuilder()
        .with_start(START)
        .with_end(END)
        .with_output_format("json")
        .build()
    )
    assert pipeline.config.output_format == "json"


def test_builder_invalid_format_raises():
    with pytest.raises(Exception):
        (
            PipelineBuilder()
            .with_start(START)
            .with_end(END)
            .with_output_format("xml")
            .build()
        )


def test_builder_with_output_path(tmp_path):
    out = str(tmp_path / "result.log")
    pipeline = (
        PipelineBuilder()
        .with_start(START)
        .with_end(END)
        .with_output_path(out)
        .build()
    )
    assert pipeline.config.output_path == out
