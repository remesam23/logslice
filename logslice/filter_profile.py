"""Filter profile: named, reusable filter configurations for log slicing."""

from __future__ import annotations

import json
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional


class FilterProfileError(Exception):
    """Raised when a filter profile is invalid or cannot be loaded."""


@dataclass
class FilterProfile:
    """A named, reusable set of filter parameters for log slicing."""

    name: str
    start: str
    end: str
    timestamp_format: Optional[str] = None
    output_format: str = "plain"
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "FilterProfile":
        required = {"name", "start", "end"}
        missing = required - data.keys()
        if missing:
            raise FilterProfileError(
                f"FilterProfile missing required fields: {', '.join(sorted(missing))}"
            )
        return cls(
            name=data["name"],
            start=data["start"],
            end=data["end"],
            timestamp_format=data.get("timestamp_format"),
            output_format=data.get("output_format", "plain"),
            tags=data.get("tags", []),
        )

    @classmethod
    def from_json_file(cls, path: str | Path) -> "FilterProfile":
        p = Path(path)
        if not p.exists():
            raise FilterProfileError(f"Profile file not found: {path}")
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError as exc:
            raise FilterProfileError(f"Invalid JSON in profile file: {exc}") from exc
        return cls.from_dict(data)

    def save(self, path: str | Path) -> None:
        Path(path).write_text(json.dumps(self.to_dict(), indent=2))
