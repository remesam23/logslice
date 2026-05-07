"""Runs a Pipeline using a FilterProfile as configuration source."""

from pathlib import Path
from typing import Optional, Union

from logslice.filter_profile import FilterProfile, FilterProfileError
from logslice.pipeline_builder import PipelineBuilder
from logslice.stats import SliceStats


class ProfileRunner:
    """Executes a log slice pipeline driven by a FilterProfile."""

    def __init__(self, profile: FilterProfile) -> None:
        self._profile = profile

    @classmethod
    def from_json_file(cls, path: Union[str, Path]) -> "ProfileRunner":
        """Convenience constructor — load a profile from disk and return a runner."""
        profile = FilterProfile.from_json_file(path)
        return cls(profile)

    def run(
        self,
        log_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
    ) -> SliceStats:
        """Run the pipeline for *log_path* using the loaded profile.

        Parameters
        ----------
        log_path:
            Path to the log file to slice.
        output_path:
            Optional destination file.  When *None* output goes to stdout.

        Returns
        -------
        SliceStats
            Statistics collected during the run.

        Raises
        ------
        FileNotFoundError
            If *log_path* does not exist or is not a file.
        """
        log_path = Path(log_path)
        if not log_path.exists():
            raise FileNotFoundError(f"Log file not found: {log_path}")
        if not log_path.is_file():
            raise FileNotFoundError(f"Log path is not a file: {log_path}")

        p = self._profile

        builder = (
            PipelineBuilder()
            .with_start(p.start)
            .with_end(p.end)
        )

        if p.timestamp_formats:
            builder = builder.with_timestamp_formats(p.timestamp_formats)

        if p.output_format:
            builder = builder.with_output_format(p.output_format)

        if output_path is not None:
            builder = builder.with_output_path(output_path)

        pipeline = builder.build()
        stats = pipeline.run(log_path)
        return stats
