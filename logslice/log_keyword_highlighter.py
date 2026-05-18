from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Dict
import re


class KeywordHighlighterError(Exception):
    pass


@dataclass
class HighlightedEntry:
    raw: str
    matched_keywords: List[str]
    highlighted: str
    source: Optional[str] = None

    def to_dict(self) -> Dict:
        return {
            "raw": self.raw,
            "matched_keywords": self.matched_keywords,
            "highlighted": self.highlighted,
            "source": self.source,
        }


@dataclass
class KeywordRule:
    keyword: str
    case_sensitive: bool = False
    marker_open: str = ">>>"
    marker_close: str = "<<<"

    def __post_init__(self) -> None:
        if not self.keyword or not self.keyword.strip():
            raise KeywordHighlighterError("Keyword must not be empty.")
        flags = 0 if self.case_sensitive else re.IGNORECASE
        self._pattern = re.compile(re.escape(self.keyword), flags)

    def apply(self, text: str) -> str:
        return self._pattern.sub(
            lambda m: f"{self.marker_open}{m.group()}{self.marker_close}", text
        )

    def matches(self, text: str) -> bool:
        return bool(self._pattern.search(text))


class LogKeywordHighlighter:
    def __init__(self, rules: List[KeywordRule]) -> None:
        if not rules:
            raise KeywordHighlighterError("At least one keyword rule is required.")
        self._rules = rules

    def highlight_line(self, line: str, source: Optional[str] = None) -> Optional[HighlightedEntry]:
        matched: List[str] = [r.keyword for r in self._rules if r.matches(line)]
        if not matched:
            return None
        highlighted = line
        for rule in self._rules:
            highlighted = rule.apply(highlighted)
        return HighlightedEntry(
            raw=line,
            matched_keywords=matched,
            highlighted=highlighted.rstrip("\n"),
            source=source,
        )

    def highlight_lines(self, lines: List[str], source: Optional[str] = None) -> List[HighlightedEntry]:
        results = []
        for line in lines:
            entry = self.highlight_line(line, source=source)
            if entry is not None:
                results.append(entry)
        return results

    def highlight_file(self, path: str) -> List[HighlightedEntry]:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            lines = fh.readlines()
        return self.highlight_lines(lines, source=path)
