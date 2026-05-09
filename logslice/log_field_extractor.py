from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class FieldExtractorError(Exception):
    """Raised when field extraction configuration is invalid."""


@dataclass
class ExtractedEntry:
    raw: str
    fields: Dict[str, str]

    def to_dict(self) -> dict:
        return {"raw": self.raw, "fields": self.fields}


@dataclass
class FieldRule:
    name: str
    pattern: re.Pattern
    group: str = "value"

    @classmethod
    def from_regex(cls, name: str, pattern: str, group: str = "value") -> "FieldRule":
        try:
            compiled = re.compile(pattern)
        except re.error as exc:
            raise FieldExtractorError(
                f"Invalid regex for rule '{name}': {exc}"
            ) from exc
        if group not in compiled.groupindex and not pattern.count("("):
            pass  # unnamed group fallback handled at match time
        return cls(name=name, pattern=compiled, group=group)


@dataclass
class LogFieldExtractor:
    rules: List[FieldRule] = field(default_factory=list)

    def add_rule(self, rule: FieldRule) -> None:
        self.rules.append(rule)

    def extract(self, line: str) -> ExtractedEntry:
        extracted: Dict[str, str] = {}
        for rule in self.rules:
            match = rule.pattern.search(line)
            if match:
                try:
                    extracted[rule.name] = match.group(rule.group)
                except IndexError:
                    # fallback: first capturing group
                    try:
                        extracted[rule.name] = match.group(1)
                    except IndexError:
                        extracted[rule.name] = match.group(0)
        return ExtractedEntry(raw=line, fields=extracted)

    def extract_all(self, lines: List[str]) -> List[ExtractedEntry]:
        return [self.extract(line) for line in lines]
