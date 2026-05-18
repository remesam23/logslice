from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import re


class EntryClassifierError(Exception):
    pass


@dataclass
class ClassifiedEntry:
    raw: str
    category: Optional[str]
    confidence: float  # 0.0 – 1.0
    matched_rule: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "raw": self.raw,
            "category": self.category,
            "confidence": self.confidence,
            "matched_rule": self.matched_rule,
        }


@dataclass
class ClassifierRule:
    name: str
    pattern: str
    category: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        if not self.name:
            raise EntryClassifierError("Rule name must not be empty.")
        if not self.pattern:
            raise EntryClassifierError("Rule pattern must not be empty.")
        if not self.category:
            raise EntryClassifierError("Rule category must not be empty.")
        if not (0.0 <= self.confidence <= 1.0):
            raise EntryClassifierError("Confidence must be between 0.0 and 1.0.")
        try:
            re.compile(self.pattern)
        except re.error as exc:
            raise EntryClassifierError(f"Invalid regex pattern '{self.pattern}': {exc}") from exc


class LogEntryClassifier:
    """Classifies log lines against an ordered list of regex rules.

    The first matching rule wins.  Lines that match no rule receive
    category=None and confidence=0.0.
    """

    def __init__(self, rules: List[ClassifierRule]) -> None:
        if not rules:
            raise EntryClassifierError("At least one ClassifierRule is required.")
        self._rules = rules
        self._compiled = [(r, re.compile(r.pattern)) for r in rules]

    def classify(self, line: str) -> ClassifiedEntry:
        for rule, regex in self._compiled:
            if regex.search(line):
                return ClassifiedEntry(
                    raw=line,
                    category=rule.category,
                    confidence=rule.confidence,
                    matched_rule=rule.name,
                )
        return ClassifiedEntry(raw=line, category=None, confidence=0.0, matched_rule=None)

    def classify_lines(self, lines: List[str]) -> List[ClassifiedEntry]:
        return [self.classify(line) for line in lines]

    def category_counts(self, lines: List[str]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for entry in self.classify_lines(lines):
            key = entry.category or "__unclassified__"
            counts[key] = counts.get(key, 0) + 1
        return counts
