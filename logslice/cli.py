"""Command-line interface for logslice."""

import argparse
import sys
from pathlib import Path

from logslice.slicer import LogSlicer
from logslice.exporter import LogExporter


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="logslice",
        description="Filter log files by time range and export structured output.",
    )
    p.add_argument("logfile", type=Path, help="Path to the log file to process.")
    p.add_argument("--start", metavar="DATETIME", default=None,
                   help="Start of time range (ISO 8601 or syslog format).")
    p.add_argument("--end", metavar="DATETIME", default=None,
                   help="End of time range (ISO 8601 or syslog format).")
    p.add_argument("--format", dest="fmt", choices=["plain", "json"], default="plain",
                   help="Output format (default: plain).")
    p.add_argument("--output", metavar="FILE", type=Path, default=None,
                   help="Write output to FILE instead of stdout.")
    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.logfile.exists():
        print(f"logslice: error: file not found: {args.logfile}", file=sys.stderr)
        return 2

    slicer = LogSlicer(start=args.start, end=args.end)
    exporter = LogExporter(fmt=args.fmt, output_path=args.output)

    entries = list(slicer.filter_file(args.logfile))
    count = exporter.export(entries)

    print(f"logslice: exported {count} log entries.", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
