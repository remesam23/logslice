"""Tests for logslice.parser."""

from datetime import datetime

import pytest

from logslice.parser import LogParser


@pytest.fixture
def parser():
    return LogParser()


class TestExtractTimestamp:
    def test_iso8601_T_separator(self, parser):
        line = '2024-03-10T08:22:01 INFO Server started'
        ts = parser.extract_timestamp(line)
        assert ts == datetime(2024, 3, 10, 8, 22, 1)

    def test_iso8601_space_separator(self, parser):
        line = '2024-03-10 08:22:01.123 ERROR Disk full'
        ts = parser.extract_timestamp(line)
        assert ts == datetime(2024, 3, 10, 8, 22, 1)

    def test_syslog_format(self, parser):
        line = 'Mar 10 08:22:01 myhost sshd[1234]: Accepted'
        ts = parser.extract_timestamp(line)
        assert ts is not None
        assert ts.month == 3
        assert ts.day == 10
        assert ts.hour == 8

    def test_apache_format(self, parser):
        line = '127.0.0.1 - - [10/Mar/2024:08:22:01 +0000] "GET / HTTP/1.1" 200'
        ts = parser.extract_timestamp(line)
        assert ts == datetime(2024, 3, 10, 8, 22, 1)

    def test_no_timestamp_returns_none(self, parser):
        line = 'This line has no timestamp at all'
        assert parser.extract_timestamp(line) is None

    def test_parse_line_returns_dict(self, parser):
        line = '2024-03-10 08:22:01 INFO hello'
        result = parser.parse_line(line)
        assert result['parsed'] is True
        assert result['line'] == line
        assert isinstance(result['timestamp'], datetime)

    def test_parse_line_unparsed(self, parser):
        result = parser.parse_line('no timestamp here')
        assert result['parsed'] is False
        assert result['timestamp'] is None

    def test_custom_pattern(self):
        custom = LogParser(pattern=r'(\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2})', fmt='%Y/%m/%d %H:%M:%S')
        ts = custom.extract_timestamp('2024/03/10 08:22:01 custom log entry')
        assert ts == datetime(2024, 3, 10, 8, 22, 1)
