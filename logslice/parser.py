"""Core log line parser for extracting timestamps from log entries."""

import re
from datetime import datetime
from typing import Optional

# Common log timestamp patterns
TIMESTAMP_PATTERNS = [
    # ISO 8601: 2024-01-15T13:45:00 or 2024-01-15 13:45:00
    (r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:?\d{2})?)', '%Y-%m-%dT%H:%M:%S'),
    (r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}(?:\.\d+)?)', '%Y-%m-%d %H:%M:%S'),
    # Common syslog: Jan 15 13:45:00
    (r'([A-Z][a-z]{2} +\d{1,2} \d{2}:\d{2}:\d{2})', '%b %d %H:%M:%S'),
    # Apache/nginx: 15/Jan/2024:13:45:00
    (r'(\d{2}/[A-Z][a-z]{2}/\d{4}:\d{2}:\d{2}:\d{2})', '%d/%b/%Y:%H:%M:%S'),
]


class LogParser:
    """Parses log lines and extracts structured timestamp information."""

    def __init__(self, pattern: Optional[str] = None, fmt: Optional[str] = None):
        """
        Args:
            pattern: Custom regex pattern with one capture group for the timestamp.
            fmt: Custom strptime format string matching the captured timestamp.
        """
        if pattern and fmt:
            self._patterns = [(pattern, fmt)]
        else:
            self._patterns = TIMESTAMP_PATTERNS

    def extract_timestamp(self, line: str) -> Optional[datetime]:
        """Extract and parse the first timestamp found in a log line."""
        for pattern, fmt in self._patterns:
            match = re.search(pattern, line)
            if match:
                raw = match.group(1)
                # Normalize ISO 8601 variants
                raw = raw.rstrip('Z').replace('T', ' ')
                # Strip sub-seconds for parsing
                raw = re.sub(r'\.\d+', '', raw)
                try:
                    return datetime.strptime(raw, fmt)
                except ValueError:
                    continue
        return None

    def parse_line(self, line: str) -> dict:
        """Return a dict with timestamp and raw line content."""
        ts = self.extract_timestamp(line)
        return {
            'timestamp': ts,
            'line': line.rstrip('\n'),
            'parsed': ts is not None,
        }
