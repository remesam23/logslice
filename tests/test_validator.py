"""Tests for logslice.validator module."""

import pytest
from datetime import datetime

from logslice.validator import (
    parse_datetime_arg,
    validate_time_range,
    validate_output_format,
    ValidationError,
)


class TestParseDatetimeArg:
    def test_iso8601_T_separator(self):
        result = parse_datetime_arg("2024-03-15T10:30:00")
        assert result == datetime(2024, 3, 15, 10, 30, 0)

    def test_iso8601_space_separator(self):
        result = parse_datetime_arg("2024-03-15 10:30:00")
        assert result == datetime(2024, 3, 15, 10, 30, 0)

    def test_syslog_format(self):
        result = parse_datetime_arg("Mar 15 10:30:00")
        assert result.month == 3
        assert result.day == 15

    def test_apache_format(self):
        result = parse_datetime_arg("15/Mar/2024:10:30:00")
        assert result == datetime(2024, 3, 15, 10, 30, 0)

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError, match="Cannot parse datetime"):
            parse_datetime_arg("not-a-date")

    def test_partial_date_raises(self):
        with pytest.raises(ValidationError):
            parse_datetime_arg("2024-03-15")


class TestValidateTimeRange:
    def test_valid_range(self):
        start = datetime(2024, 1, 1, 0, 0, 0)
        end = datetime(2024, 1, 2, 0, 0, 0)
        s, e = validate_time_range(start, end)
        assert s == start
        assert e == end

    def test_none_values_allowed(self):
        assert validate_time_range(None, None) == (None, None)
        assert validate_time_range(datetime(2024, 1, 1), None)[1] is None

    def test_start_equal_to_end_raises(self):
        dt = datetime(2024, 1, 1, 12, 0, 0)
        with pytest.raises(ValidationError, match="must be before"):
            validate_time_range(dt, dt)

    def test_start_after_end_raises(self):
        start = datetime(2024, 1, 2)
        end = datetime(2024, 1, 1)
        with pytest.raises(ValidationError, match="must be before"):
            validate_time_range(start, end)


class TestValidateOutputFormat:
    def test_valid_formats(self):
        assert validate_output_format("plain") == "plain"
        assert validate_output_format("json") == "json"
        assert validate_output_format("csv") == "csv"

    def test_case_insensitive(self):
        assert validate_output_format("JSON") == "json"
        assert validate_output_format("Plain") == "plain"

    def test_invalid_format_raises(self):
        with pytest.raises(ValidationError, match="Unsupported format"):
            validate_output_format("xml")

    def test_whitespace_stripped(self):
        assert validate_output_format(" json ") == "json"
