"""Chain multiple formatters together, applying each in sequence to transform log entries."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional


class FormatterChainError(Exception):
    """Raised when the formatter chain is misconfigured."""


@dataclass
class ChainedEntry:
    raw: str
    transformed: str
    stages: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "raw": self.raw,
            "transformed": self.transformed,
            "stages": self.stages,
        }


FormatterFn = Callable[[str], Optional[str]]


@dataclass
class FormatterStep:
    name: str
    fn: FormatterFn

    def __post_init__(self) -> None:
        if not self.name or not self.name.strip():
            raise FormatterChainError("FormatterStep name must not be empty.")
        if not callable(self.fn):
            raise FormatterChainError("FormatterStep fn must be callable.")


class LogEntryFormatterChain:
    """Applies a sequence of transformation functions to each log line."""

    def __init__(self, steps: List[FormatterStep], skip_on_none: bool = True) -> None:
        if not steps:
            raise FormatterChainError("At least one FormatterStep is required.")
        self._steps = steps
        self._skip_on_none = skip_on_none

    def apply(self, line: str) -> Optional[ChainedEntry]:
        """Apply all steps to *line*. Returns None if any step returns None and skip_on_none is True."""
        current = line
        stages: List[str] = []
        for step in self._steps:
            result = step.fn(current)
            if result is None:
                if self._skip_on_none:
                    return None
                # keep current value unchanged when not skipping
            else:
                current = result
            stages.append(step.name)
        return ChainedEntry(raw=line, transformed=current, stages=stages)

    def apply_all(self, lines: List[str]) -> List[ChainedEntry]:
        """Apply the chain to every line, dropping entries that resolve to None."""
        results: List[ChainedEntry] = []
        for line in lines:
            entry = self.apply(line)
            if entry is not None:
                results.append(entry)
        return results
