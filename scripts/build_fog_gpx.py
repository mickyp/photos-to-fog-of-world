#!/usr/bin/env python3
"""Build a Fog of World compatible GPX track from photo metadata."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


SUPPORTED_EXTENSIONS = ("jpg", "jpeg", "heic", "png")
EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = (
    "http://www.topografix.com/GPX/1/1 "
    "http://www.topografix.com/GPX/1/1/gpx.xsd"
)


@dataclass
class TrackPoint:
    source_file: str
    capture_time_local: datetime
    capture_time_utc: datetime
    latitude: float
    longitude: float
    altitude: float | None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a GPX track from geotagged photos for Fog of World."
    )
    parser.add_argument("input_dir", help="Folder containing photos to scan")
    parser.add_argument(
        "-o",
        "--output",
        help="Output GPX file path. Defaults to <input_dir>/fog_of_world_import.gpx",
    )
    parser.add_argument(
        "--timezone",
        help=(
            "IANA timezone for photo timestamps without embedded offsets, "
            "for example Asia/Taipei"
        ),
    )
    parser.add_argument(
        "--name",
        default="photo import",
        help="Track name written into the GPX file",
    )
    return parser.parse_args()


def resolve_default_timezone(tz_name: str | None) -> ZoneInfo | timezone:
    if tz_name:
        return ZoneInfo(tz_name)
    return datetime.now().astimezone().tzinfo or timezone.utc


def find_exiftool() -> str:
    discovered = shutil.which("exiftool")
    if discovered:
        return discovered

    local_app_data = os.environ.get("LOCALAPPDATA")
    candidates = [
        Path(r"C:\Users\169896\AppData\Local\Programs\ExifTool\ExifTool.exe"),
    ]
    if local_app_data:
        candidates.append(Path(local_app_data) / "Programs" / "ExifTool" / "ExifTool.exe")

    for candidate in candidates:
        if candidate.exists():
            return str(candidate)

    raise SystemExit("exiftool is not installed or not on PATH")


def ensure_exiftool_available(exiftool_cmd: str) -> None:
    try:
        subprocess.run(
            [exiftool_cmd, "-ver"],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError as exc:
        raise SystemExit("exiftool is not installed or not on PATH") from exc
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"Unable to run exiftool: {exc.stderr.strip()}") from exc


def read_photo_metadata(input_dir: Path, exiftool_cmd: str) -> list[dict]:
    command = [
        exiftool_cmd,
        "-n",
        "-json",
        "-r",
        "-FileName",
        "-Directory",
        "-DateTimeOriginal",
        "-CreateDate",
        "-OffsetTimeOriginal",
        "-OffsetTime",
        "-GPSLatitude",
        "-GPSLongitude",
        "-GPSAltitude",
    ]
    for extension in SUPPORTED_EXTENSIONS:
        command.extend(["-ext", extension])
    command.append(str(input_dir))

    result = subprocess.run(command, capture_output=True, text=True, check=True)
    return json.loads(result.stdout)


def parse_offset(offset_value: str | None) -> timezone | None:
    if not offset_value:
        return None
    sign = 1
    raw = offset_value.strip()
    if raw.startswith("-"):
        sign = -1
        raw = raw[1:]
    elif raw.startswith("+"):
        raw = raw[1:]
    try:
        hours_str, minutes_str = raw.split(":", 1)
        delta = timedelta(hours=int(hours_str), minutes=int(minutes_str))
    except ValueError:
        return None
    return timezone(sign * delta)


def pick_capture_time(entry: dict) -> str | None:
    return entry.get("DateTimeOriginal") or entry.get("CreateDate")


def build_track_points(
    metadata_rows: Iterable[dict], fallback_tz: ZoneInfo | timezone
) -> tuple[list[TrackPoint], list[str]]:
    track_points: list[TrackPoint] = []
    skipped: list[str] = []

    for entry in metadata_rows:
        source_file = entry.get("SourceFile") or entry.get("FileName") or "<unknown>"
        timestamp_text = pick_capture_time(entry)
        latitude = entry.get("GPSLatitude")
        longitude = entry.get("GPSLongitude")
        altitude = entry.get("GPSAltitude")

        if not timestamp_text or latitude is None or longitude is None:
            skipped.append(source_file)
            continue

        naive_time = datetime.strptime(timestamp_text, EXIF_DATE_FORMAT)
        offset = parse_offset(entry.get("OffsetTimeOriginal")) or parse_offset(
            entry.get("OffsetTime")
        )
        if offset is not None:
            capture_time_local = naive_time.replace(tzinfo=offset)
        else:
            capture_time_local = naive_time.replace(tzinfo=fallback_tz)

        capture_time_utc = capture_time_local.astimezone(timezone.utc)
        track_points.append(
            TrackPoint(
                source_file=source_file,
                capture_time_local=capture_time_local,
                capture_time_utc=capture_time_utc,
                latitude=float(latitude),
                longitude=float(longitude),
                altitude=float(altitude) if altitude is not None else None,
            )
        )

    track_points.sort(key=lambda item: item.capture_time_utc)
    return track_points, skipped


def build_gpx(track_points: list[TrackPoint], track_name: str) -> ET.Element:
    ET.register_namespace("", GPX_NAMESPACE)
    ET.register_namespace("xsi", XSI_NAMESPACE)

    root = ET.Element(
        f"{{{GPX_NAMESPACE}}}gpx",
        {
            "version": "1.1",
            "creator": "photos-to-fog-of-world",
            f"{{{XSI_NAMESPACE}}}schemaLocation": SCHEMA_LOCATION,
        },
    )
    metadata_el = ET.SubElement(root, f"{{{GPX_NAMESPACE}}}metadata")
    ET.SubElement(metadata_el, f"{{{GPX_NAMESPACE}}}name").text = track_name
    ET.SubElement(
        metadata_el, f"{{{GPX_NAMESPACE}}}desc"
    ).text = "Track generated from photo EXIF metadata for Fog of World import."
    ET.SubElement(metadata_el, f"{{{GPX_NAMESPACE}}}time").text = format_gpx_time(
        track_points[0].capture_time_utc
    )

    track_el = ET.SubElement(root, f"{{{GPX_NAMESPACE}}}trk")
    ET.SubElement(track_el, f"{{{GPX_NAMESPACE}}}name").text = track_name
    segment_el = ET.SubElement(track_el, f"{{{GPX_NAMESPACE}}}trkseg")

    for point in track_points:
        point_el = ET.SubElement(
            segment_el,
            f"{{{GPX_NAMESPACE}}}trkpt",
            {"lat": f"{point.latitude:.10f}", "lon": f"{point.longitude:.10f}"},
        )
        if point.altitude is not None:
            ET.SubElement(point_el, f"{{{GPX_NAMESPACE}}}ele").text = (
                f"{point.altitude:.8f}"
            )
        ET.SubElement(point_el, f"{{{GPX_NAMESPACE}}}time").text = format_gpx_time(
            point.capture_time_utc
        )

    return root


def format_gpx_time(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace(
        "+00:00", "Z"
    )


def indent_xml(element: ET.Element) -> None:
    ET.indent(element, space="  ")


def write_gpx(output_path: Path, gpx_root: ET.Element) -> None:
    indent_xml(gpx_root)
    tree = ET.ElementTree(gpx_root)
    tree.write(output_path, encoding="utf-8", xml_declaration=True)


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir).expanduser().resolve()
    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else input_dir / "fog_of_world_import.gpx"
    )

    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    exiftool_cmd = find_exiftool()
    ensure_exiftool_available(exiftool_cmd)
    fallback_tz = resolve_default_timezone(args.timezone)
    metadata_rows = read_photo_metadata(input_dir, exiftool_cmd)
    track_points, skipped = build_track_points(metadata_rows, fallback_tz)

    if not track_points:
        raise SystemExit("No photos with both timestamp and GPS coordinates were found")

    gpx_root = build_gpx(track_points, args.name)
    write_gpx(output_path, gpx_root)

    print(f"Wrote GPX: {output_path}")
    print(f"Track points: {len(track_points)}")
    print(f"Skipped files: {len(skipped)}")
    if skipped:
        for item in skipped:
            print(f"  skipped: {item}")
    print(
        "Timezone assumption: "
        f"{getattr(fallback_tz, 'key', str(fallback_tz))} for timestamps without offsets"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
