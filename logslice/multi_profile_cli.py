"""CLI entry point for running multiple filter profiles against a log file."""

from __future__ import annotations

import argparse
import json
import sys

from logslice.multi_profile_runner import MultiProfileRunner, MultiProfileError


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="logslice-multi",
        description="Apply multiple time-range profiles to a log file.",
    )
    parser.add_argument("log_file", help="Path to the log file to slice.")
    parser.add_argument(
        "profiles_file",
        help="Path to a JSON file containing an array of profile definitions.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format for the summary (default: text).",
    )
    parser.add_argument(
        "--output",
        default=None,
        metavar="FILE",
        help="Write summary to FILE instead of stdout.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        runner = MultiProfileRunner.from_json_file(args.log_file, args.profiles_file)
        summary = runner.summary()
    except MultiProfileError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if args.output_format == "json":
        output = json.dumps(summary, indent=2)
    else:
        lines = []
        for entry in summary:
            lines.append(
                f"[{entry['profile']}] matched={entry.get('matched', 0)} "
                f"skipped={entry.get('skipped', 0)} "
                f"match_rate={entry.get('match_rate', 0.0):.1%}"
            )
        output = "\n".join(lines)

    if args.output:
        try:
            with open(args.output, "w") as fh:
                fh.write(output + "\n")
        except OSError as exc:
            print(f"Error writing output: {exc}", file=sys.stderr)
            return 1
    else:
        print(output)

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
