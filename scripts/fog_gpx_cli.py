#!/usr/bin/env python3
"""Windows-friendly CLI wrapper for building Fog of World GPX files."""

from __future__ import annotations

import argparse
import sys

from app_version import APP_VERSION
from build_fog_gpx import RunOptions, normalize_cli_path, run_conversion


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a photo folder and export a Fog of World compatible GPX file."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s v{APP_VERSION}",
    )
    parser.add_argument(
        "input_dir",
        nargs="?",
        help="Photo folder to scan. If omitted, you must pass --input.",
    )
    parser.add_argument(
        "--input",
        dest="input_override",
        help="Photo folder to scan. Useful when paths contain special characters.",
    )
    parser.add_argument(
        "-o",
        "--output",
        help="Optional GPX output file path. Defaults to a timestamped file in the input folder.",
    )
    parser.add_argument(
        "--timezone",
        default="Asia/Taipei",
        help="Timezone to use when photo timestamps do not include an offset.",
    )
    parser.add_argument("--name", help="Optional track name written into the GPX.")
    parser.add_argument(
        "--reuse-existing-child-gpx",
        action="store_true",
        help="For yearly folders, reuse the newest child GPX when one already exists.",
    )
    parser.add_argument(
        "--skip-existing-output",
        action="store_true",
        help="Reuse the newest GPX in a folder instead of writing another copy.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_value = args.input_override or args.input_dir
    if not input_value:
        print("Please provide a folder path with INPUT_DIR or --input.", file=sys.stderr)
        return 2

    try:
        summary = run_conversion(
            RunOptions(
                input_dir=normalize_cli_path(input_value),
                output=normalize_cli_path(args.output) if args.output else None,
                timezone_name=args.timezone,
                track_name=args.name,
                reuse_existing_child_gpx=args.reuse_existing_child_gpx,
                skip_existing_output=args.skip_existing_output,
            ),
            line_printer=print,
        )
    except SystemExit as exc:
        message = str(exc)
        if message:
            print(message, file=sys.stderr)
        return 1
    except Exception as exc:  # pragma: no cover - defensive CLI error handling
        print(f"Unexpected error: {exc}", file=sys.stderr)
        return 1

    if summary.output_path:
        print(f"Done. Output GPX: {summary.output_path}")
        return 0

    print("No GPX was created because no photos had both capture time and GPS data.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
