from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


class EntryScorerError(ValueError):
    pass


@dataclass
class ScoringRule:
    name: str
    pattern: str
    score: float

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise EntryScorerError("ScoringRule name must not be empty")
        if not self.pattern.strip():
            raise EntryScorerError("ScoringRule pattern must not be empty")
        try:
            self._regex = re.compile(self.pattern)
        except re.error as exc:
            raise EntryScorerError(f"Invalid regex pattern '{self.pattern}': {exc}") from exc

    def matches(self, line: str) -> bool:
        return bool(self._regex.search(line))


@dataclass
class ScoredEntry:
    line: str
    total_score: float
    matched_rules: List[str]

    def to_dict(self) -> dict:
        return {
            "line": self.line,
            "total_score": self.total_score,
            "matched_rules": self.matched_rules,
        }


@dataclass
class LogEntryScorer:
    rules: List[ScoringRule]
    threshold: Optional[float] = None

    def __post_init__(self) -> None:
        if not self.rules:
            raise EntryScorerError("At least one ScoringRule is required")

    def score_line(self, line: str) -> ScoredEntry:
        total = 0.0
        matched: List[str] = []
        for rule in self.rules:
            if rule.matches(line):
                total += rule.score
                matched.append(rule.name)
        return ScoredEntry(line=line, total_score=total, matched_rules=matched)

    def score_lines(self, lines: List[str]) -> List[ScoredEntry]:
        results = [self.score_line(ln) for ln in lines]
        if self.threshold is not None:
            results = [e for e in results if e.total_score >= self.threshold]
        return results
