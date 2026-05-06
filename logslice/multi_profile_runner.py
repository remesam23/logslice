"""Run multiple filter profiles in sequence and collect aggregated results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from logslice.filter_profile import FilterProfile, FilterProfileError
from logslice.profile_runner import ProfileRunner
from logslice.stats import SliceStats


class MultiProfileError(Exception):
    """Raised when multi-profile execution encounters a fatal error."""


class MultiProfileRunner:
    """Execute multiple FilterProfiles against a log file and aggregate stats."""

    def __init__(self, log_path: str, profiles: List[FilterProfile]) -> None:
        if not profiles:
            raise MultiProfileError("At least one profile is required.")
        self.log_path = log_path
        self.profiles = profiles

    @classmethod
    def from_json_file(cls, log_path: str, profiles_path: str) -> "MultiProfileRunner":
        """Load a list of profile definitions from a JSON array file."""
        path = Path(profiles_path)
        if not path.exists():
            raise MultiProfileError(f"Profiles file not found: {profiles_path}")
        try:
            data = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            raise MultiProfileError(f"Invalid JSON in profiles file: {exc}") from exc
        if not isinstance(data, list):
            raise MultiProfileError("Profiles file must contain a JSON array.")
        profiles = [FilterProfile.from_dict(item) for item in data]
        return cls(log_path, profiles)

    def run(self) -> Dict[str, SliceStats]:
        """Run all profiles and return a mapping of profile name -> SliceStats."""
        results: Dict[str, SliceStats] = {}
        for profile in self.profiles:
            runner = ProfileRunner(self.log_path, profile)
            stats = runner.run()
            results[profile.name] = stats
        return results

    def summary(self) -> List[dict]:
        """Return a list of per-profile stat dicts suitable for serialisation."""
        results = self.run()
        return [
            {"profile": name, **stats.to_dict()}
            for name, stats in results.items()
        ]
