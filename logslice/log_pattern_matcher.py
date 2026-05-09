"""Pattern-based log line matcher supporting regex and literal string rules."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional


class PatternMatcherError(Exception):
    """Raised when pattern configuration is invalid."""


@dataclass
class MatchedEntry:
    line: str
    pattern: str
    group: Optional[str] = None

    def to_dict(self) -> dict:
        return {"line": self.line, "pattern": self.pattern, "group": self.group}


@dataclass
class PatternRule:
    pattern: str
    group: Optional[str] = None
    is_regex: bool = True

    def __post_init__(self) -> None:
        if self.is_regex:
            try:
                self._compiled = re.compile(self.pattern)
            except re.error as exc:
                raise PatternMatcherError(f"Invalid regex '{self.pattern}': {exc}") from exc
        else:
            self._compiled = None

    def matches(self, line: str) -> bool:
        if self.is_regex:
            return bool(self._compiled.search(line))  # type: ignore[union-attr]
        return self.pattern in line


@dataclass
class LogPatternMatcher:
    rules: List[PatternRule] = field(default_factory=list)

    def add_rule(self, pattern: str, group: Optional[str] = None, is_regex: bool = True) -> "LogPatternMatcher":
        self.rules.append(PatternRule(pattern=pattern, group=group, is_regex=is_regex))
        return self

    def match_line(self, line: str) -> Optional[MatchedEntry]:
        for rule in self.rules:
            if rule.matches(line):
                return MatchedEntry(line=line.rstrip("\n"), pattern=rule.pattern, group=rule.group)
        return None

    def match_lines(self, lines: List[str]) -> List[MatchedEntry]:
        results: List[MatchedEntry] = []
        for line in lines:
            entry = self.match_line(line)
            if entry is not None:
                results.append(entry)
        return results

    def match_file(self, path: str) -> List[MatchedEntry]:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            return self.match_lines(fh.readlines())
