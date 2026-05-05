"""Pipeline wrapper that uses LogCache to skip re-parsing unchanged files."""

from typing import Optional

from logslice.cache import LogCache
from logslice.config import SliceConfig
from logslice.pipeline import Pipeline
from logslice.stats import SliceStats


class CachedPipeline:
    """Wraps Pipeline with a caching layer to avoid redundant processing.

    On first run, metadata (match count, skip count) is stored in the cache.
    On subsequent runs with an unchanged file, cached stats are returned
    without re-parsing the file.
    """

    def __init__(self, config: SliceConfig, cache: Optional[LogCache] = None):
        self.config = config
        self.cache = cache or LogCache()
        self._pipeline = Pipeline(config)

    def run(self, use_cache: bool = True) -> SliceStats:
        """Run the pipeline, returning cached stats if available.

        Args:
            use_cache: If False, bypass cache and always re-process.

        Returns:
            SliceStats from either cache or a fresh pipeline run.
        """
        filepath = self.config.input_file

        if use_cache and filepath:
            cached = self.cache.get(filepath)
            if cached is not None:
                return self._stats_from_cache(cached)

        stats = self._pipeline.run()

        if filepath:
            self.cache.set(filepath, self._stats_to_cache(stats))

        return stats

    def invalidate(self) -> bool:
        """Invalidate the cache entry for the configured input file."""
        if self.config.input_file:
            return self.cache.invalidate(self.config.input_file)
        return False

    @staticmethod
    def _stats_to_cache(stats: SliceStats) -> dict:
        return {
            "matched": stats.matched,
            "skipped_before": stats.skipped_before,
            "skipped_after": stats.skipped_after,
            "unparseable": stats.unparseable,
            "total_lines": stats.total_lines,
        }

    @staticmethod
    def _stats_from_cache(data: dict) -> SliceStats:
        stats = SliceStats()
        for _ in range(data.get("matched", 0)):
            stats.record_match()
        for _ in range(data.get("skipped_before", 0)):
            stats.record_skip("before")
        for _ in range(data.get("skipped_after", 0)):
            stats.record_skip("after")
        for _ in range(data.get("unparseable", 0)):
            stats.record_skip("unparseable")
        return stats
