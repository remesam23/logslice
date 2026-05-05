"""Input validation utilities for logslice."""

from datetime import datetime
from typing import Optional, Tuple


SUPPORTED_FORMATS = ("plain", "json", "csv")

SUPPORTED_TIMESTAMP_PATTERNS = (
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
    "%b %d %H:%M:%S",
    "%d/%b/%Y:%H:%M:%S",
)


class ValidationError(ValueError):
    """Raised when input validation fails."""
    pass


def parse_datetime_arg(value: str) -> datetime:
    """Parse a datetime string from CLI or config input.

    Tries multiple common formats. Raises ValidationError if none match.
    """
    for fmt in SUPPORTED_TIMESTAMP_PATTERNS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise ValidationError(
        f"Cannot parse datetime {value!r}. "
        f"Supported formats: {', '.join(SUPPORTED_TIMESTAMP_PATTERNS)}"
    )


def validate_time_range(
    start: Optional[datetime], end: Optional[datetime]
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Validate that start is before end if both are provided."""
    if start is not None and end is not None:
        if start >= end:
            raise ValidationError(
                f"start time {start.isoformat()} must be before "
                f"end time {end.isoformat()}"
            )
    return start, end


def validate_output_format(fmt: str) -> str:
    """Validate the requested output format."""
    fmt = fmt.lower().strip()
    if fmt not in SUPPORTED_FORMATS:
        raise ValidationError(
            f"Unsupported format {fmt!r}. Choose from: {', '.join(SUPPORTED_FORMATS)}"
        )
    return fmt
