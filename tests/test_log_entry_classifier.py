import pytest

from logslice.log_entry_classifier import (
    ClassifiedEntry,
    ClassifierRule,
    EntryClassifierError,
    LogEntryClassifier,
)
from logslice.log_entry_classifier_builder import (
    LogEntryClassifierBuilder,
    LogEntryClassifierBuilderError,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def classifier():
    return (
        LogEntryClassifierBuilder()
        .add_rule("error_rule", r"ERROR", "error", confidence=1.0)
        .add_rule("warn_rule", r"WARN", "warning", confidence=0.9)
        .add_rule("info_rule", r"INFO", "info", confidence=0.8)
        .build()
    )


# ---------------------------------------------------------------------------
# ClassifiedEntry
# ---------------------------------------------------------------------------

class TestClassifiedEntry:
    def test_to_dict_keys(self):
        entry = ClassifiedEntry(raw="line", category="error", confidence=1.0, matched_rule="r")
        assert set(entry.to_dict().keys()) == {"raw", "category", "confidence", "matched_rule"}

    def test_to_dict_values(self):
        entry = ClassifiedEntry(raw="boom", category="error", confidence=0.95, matched_rule="err")
        d = entry.to_dict()
        assert d["raw"] == "boom"
        assert d["category"] == "error"
        assert d["confidence"] == 0.95
        assert d["matched_rule"] == "err"

    def test_unmatched_entry_none_category(self):
        entry = ClassifiedEntry(raw="noop", category=None, confidence=0.0, matched_rule=None)
        assert entry.to_dict()["category"] is None


# ---------------------------------------------------------------------------
# ClassifierRule validation
# ---------------------------------------------------------------------------

class TestClassifierRule:
    def test_empty_name_raises(self):
        with pytest.raises(EntryClassifierError, match="name"):
            ClassifierRule(name="", pattern=r"x", category="c")

    def test_empty_pattern_raises(self):
        with pytest.raises(EntryClassifierError, match="pattern"):
            ClassifierRule(name="r", pattern="", category="c")

    def test_empty_category_raises(self):
        with pytest.raises(EntryClassifierError, match="category"):
            ClassifierRule(name="r", pattern=r"x", category="")

    def test_invalid_confidence_raises(self):
        with pytest.raises(EntryClassifierError, match="[Cc]onfidence"):
            ClassifierRule(name="r", pattern=r"x", category="c", confidence=1.5)

    def test_invalid_regex_raises(self):
        with pytest.raises(EntryClassifierError, match="[Ii]nvalid regex"):
            ClassifierRule(name="r", pattern=r"[", category="c")


# ---------------------------------------------------------------------------
# LogEntryClassifier
# ---------------------------------------------------------------------------

class TestLogEntryClassifier:
    def test_no_rules_raises(self):
        with pytest.raises(EntryClassifierError):
            LogEntryClassifier(rules=[])

    def test_classifies_error_line(self, classifier):
        entry = classifier.classify("2024-01-01 ERROR something broke")
        assert entry.category == "error"
        assert entry.matched_rule == "error_rule"
        assert entry.confidence == 1.0

    def test_classifies_warn_line(self, classifier):
        entry = classifier.classify("2024-01-01 WARN disk almost full")
        assert entry.category == "warning"

    def test_classifies_info_line(self, classifier):
        entry = classifier.classify("2024-01-01 INFO server started")
        assert entry.category == "info"

    def test_unclassified_line(self, classifier):
        entry = classifier.classify("some random line with no keywords")
        assert entry.category is None
        assert entry.confidence == 0.0
        assert entry.matched_rule is None

    def test_first_rule_wins(self, classifier):
        # A line that matches both ERROR and WARN patterns — error_rule comes first
        entry = classifier.classify("ERROR WARN mixed")
        assert entry.category == "error"

    def test_classify_lines_returns_list(self, classifier):
        lines = ["ERROR a", "WARN b", "INFO c", "other"]
        results = classifier.classify_lines(lines)
        assert len(results) == 4
        assert results[0].category == "error"
        assert results[3].category is None

    def test_category_counts(self, classifier):
        lines = ["ERROR a", "ERROR b", "WARN c", "other"]
        counts = classifier.category_counts(lines)
        assert counts["error"] == 2
        assert counts["warning"] == 1
        assert counts["__unclassified__"] == 1


# ---------------------------------------------------------------------------
# LogEntryClassifierBuilder
# ---------------------------------------------------------------------------

class TestLogEntryClassifierBuilder:
    def test_returns_classifier(self):
        c = (
            LogEntryClassifierBuilder()
            .add_rule("r", r"ERROR", "error")
            .build()
        )
        assert isinstance(c, LogEntryClassifier)

    def test_no_rules_raises(self):
        with pytest.raises(LogEntryClassifierBuilderError):
            LogEntryClassifierBuilder().build()

    def test_invalid_regex_raises(self):
        with pytest.raises(LogEntryClassifierBuilderError):
            LogEntryClassifierBuilder().add_rule("r", r"[", "c")

    def test_add_rules_bulk(self):
        rules = [
            ClassifierRule(name="r1", pattern=r"ERROR", category="error"),
            ClassifierRule(name="r2", pattern=r"INFO", category="info"),
        ]
        c = LogEntryClassifierBuilder().add_rules(rules).build()
        assert c.classify("INFO msg").category == "info"
