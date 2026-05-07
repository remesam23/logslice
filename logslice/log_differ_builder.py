"""Builder for LogDiffer with optional file path configuration."""

from logslice.log_differ import LogDiffer, DiffResult


class LogDifferBuilderError(ValueError):
    pass


class LogDifferBuilder:
    def __init__(self):
        self._baseline: str | None = None
        self._current: str | None = None
        self._strip_whitespace: bool = True

    def with_baseline(self, path: str) -> "LogDifferBuilder":
        self._baseline = path
        return self

    def with_current(self, path: str) -> "LogDifferBuilder":
        self._current = path
        return self

    def with_strip_whitespace(self, strip: bool) -> "LogDifferBuilder":
        self._strip_whitespace = strip
        return self

    def build(self) -> LogDiffer:
        return LogDiffer(strip_whitespace=self._strip_whitespace)

    def run(self) -> DiffResult:
        """Build and execute the diff immediately."""
        if not self._baseline:
            raise LogDifferBuilderError("baseline path is required")
        if not self._current:
            raise LogDifferBuilderError("current path is required")
        differ = self.build()
        return differ.diff_files(self._baseline, self._current)
