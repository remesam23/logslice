import pytest

from logslice.log_entry_router import (
    EntryRouterError,
    LogEntryRouter,
    RouteRule,
    RoutedEntry,
)


# ---------------------------------------------------------------------------
# RouteRule
# ---------------------------------------------------------------------------


class TestRouteRule:
    def test_matches_returns_true_for_matching_line(self):
        rule = RouteRule(name="errors", pattern=r"ERROR", destination="error_sink")
        assert rule.matches("2024-01-01 ERROR something broke")

    def test_matches_returns_false_for_non_matching_line(self):
        rule = RouteRule(name="errors", pattern=r"ERROR", destination="error_sink")
        assert not rule.matches("2024-01-01 INFO all good")

    def test_empty_name_raises(self):
        with pytest.raises(EntryRouterError, match="name"):
            RouteRule(name="  ", pattern=r"ERROR", destination="sink")

    def test_empty_destination_raises(self):
        with pytest.raises(EntryRouterError, match="destination"):
            RouteRule(name="r", pattern=r"ERROR", destination="")

    def test_invalid_regex_raises(self):
        with pytest.raises(EntryRouterError, match="Invalid regex"):
            RouteRule(name="bad", pattern=r"[", destination="sink")


# ---------------------------------------------------------------------------
# RoutedEntry
# ---------------------------------------------------------------------------


class TestRoutedEntry:
    def test_to_dict_keys(self):
        entry = RoutedEntry(line="hello", destination="errors", rule_name="err_rule")
        assert set(entry.to_dict().keys()) == {"line", "destination", "rule_name"}

    def test_to_dict_values(self):
        entry = RoutedEntry(line="msg", destination="warnings", rule_name="warn")
        d = entry.to_dict()
        assert d["line"] == "msg"
        assert d["destination"] == "warnings"
        assert d["rule_name"] == "warn"

    def test_to_dict_none_rule_name(self):
        entry = RoutedEntry(line="x", destination="unmatched", rule_name=None)
        assert entry.to_dict()["rule_name"] is None


# ---------------------------------------------------------------------------
# LogEntryRouter
# ---------------------------------------------------------------------------


@pytest.fixture()
def router():
    rules = [
        RouteRule(name="errors", pattern=r"ERROR", destination="error_sink"),
        RouteRule(name="warnings", pattern=r"WARN", destination="warn_sink"),
    ]
    return LogEntryRouter(rules=rules, default_destination="default_sink")


class TestLogEntryRouter:
    def test_no_rules_raises(self):
        with pytest.raises(EntryRouterError):
            LogEntryRouter(rules=[])

    def test_route_matches_first_rule(self, router):
        entry = router.route("2024-01-01 ERROR disk full")
        assert entry.destination == "error_sink"
        assert entry.rule_name == "errors"

    def test_route_matches_second_rule(self, router):
        entry = router.route("2024-01-01 WARN low memory")
        assert entry.destination == "warn_sink"
        assert entry.rule_name == "warnings"

    def test_route_unmatched_goes_to_default(self, router):
        entry = router.route("2024-01-01 INFO startup complete")
        assert entry.destination == "default_sink"
        assert entry.rule_name is None

    def test_route_lines_groups_by_destination(self, router):
        lines = [
            "ERROR one",
            "WARN two",
            "ERROR three",
            "INFO four",
        ]
        buckets = router.route_lines(lines)
        assert len(buckets["error_sink"]) == 2
        assert len(buckets["warn_sink"]) == 1
        assert len(buckets["default_sink"]) == 1

    def test_route_lines_calls_on_route_callback(self, router):
        seen = []
        router.route_lines(["ERROR x", "INFO y"], on_route=seen.append)
        assert len(seen) == 2
        assert all(isinstance(e, RoutedEntry) for e in seen)

    def test_first_matching_rule_wins(self):
        rules = [
            RouteRule(name="both", pattern=r"ERROR", destination="first"),
            RouteRule(name="also", pattern=r"ERROR", destination="second"),
        ]
        r = LogEntryRouter(rules=rules)
        entry = r.route("ERROR collision")
        assert entry.destination == "first"
