from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


class EntryRouterError(Exception):
    """Raised when the entry router is misconfigured."""


@dataclass
class RouteRule:
    """A named rule that maps a regex pattern to a destination label."""

    name: str
    pattern: str
    destination: str
    _compiled: re.Pattern = field(init=False, repr=False)

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise EntryRouterError("RouteRule name must not be empty.")
        if not self.destination.strip():
            raise EntryRouterError("RouteRule destination must not be empty.")
        try:
            self._compiled = re.compile(self.pattern)
        except re.error as exc:
            raise EntryRouterError(f"Invalid regex pattern '{self.pattern}': {exc}") from exc

    def matches(self, line: str) -> bool:
        return bool(self._compiled.search(line))


@dataclass
class RoutedEntry:
    """A log line paired with the destination it was routed to."""

    line: str
    destination: str
    rule_name: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "line": self.line,
            "destination": self.destination,
            "rule_name": self.rule_name,
        }


class LogEntryRouter:
    """Routes log lines to named destinations based on ordered regex rules.

    Lines that match no rule are routed to *default_destination*.
    Rules are evaluated in insertion order; the first match wins.
    """

    def __init__(
        self,
        rules: List[RouteRule],
        default_destination: str = "unmatched",
    ) -> None:
        if not rules:
            raise EntryRouterError("At least one RouteRule is required.")
        self._rules = rules
        self._default = default_destination

    def route(self, line: str) -> RoutedEntry:
        """Return a RoutedEntry for *line*."""
        for rule in self._rules:
            if rule.matches(line):
                return RoutedEntry(line=line, destination=rule.destination, rule_name=rule.name)
        return RoutedEntry(line=line, destination=self._default, rule_name=None)

    def route_lines(
        self,
        lines: List[str],
        on_route: Optional[Callable[[RoutedEntry], None]] = None,
    ) -> Dict[str, List[RoutedEntry]]:
        """Route all *lines* and return a dict keyed by destination label."""
        buckets: Dict[str, List[RoutedEntry]] = {}
        for line in lines:
            entry = self.route(line)
            buckets.setdefault(entry.destination, []).append(entry)
            if on_route:
                on_route(entry)
        return buckets
