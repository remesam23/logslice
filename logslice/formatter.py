"""Output formatters for filtered log results."""

import csv
import io
import json
from typing import Iterable


class BaseFormatter:
    """Abstract base for output formatters."""

    def format(self, records: Iterable[dict]) -> str:
        raise NotImplementedError


class PlainFormatter(BaseFormatter):
    """Outputs raw log lines, one per line."""

    def format(self, records: Iterable[dict]) -> str:
        return '\n'.join(r['line'] for r in records)


class JSONFormatter(BaseFormatter):
    """Outputs each record as a JSON object (newline-delimited)."""

    def format(self, records: Iterable[dict]) -> str:
        lines = []
        for r in records:
            obj = {
                'timestamp': r['timestamp'].isoformat() if r['timestamp'] else None,
                'line': r['line'],
            }
            lines.append(json.dumps(obj))
        return '\n'.join(lines)


class CSVFormatter(BaseFormatter):
    """Outputs records as CSV with timestamp and line columns."""

    def format(self, records: Iterable[dict]) -> str:
        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(['timestamp', 'line'])
        for r in records:
            ts = r['timestamp'].isoformat() if r['timestamp'] else ''
            writer.writerow([ts, r['line']])
        return buf.getvalue().rstrip('\r\n')


FORMATTERS = {
    'plain': PlainFormatter,
    'json': JSONFormatter,
    'csv': CSVFormatter,
}


def get_formatter(name: str) -> BaseFormatter:
    """Return a formatter instance by name."""
    cls = FORMATTERS.get(name.lower())
    if cls is None:
        raise ValueError(f"Unknown formatter '{name}'. Choose from: {list(FORMATTERS)}.")
    return cls()
