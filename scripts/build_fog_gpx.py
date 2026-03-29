#!/usr/bin/env python3
"""Build a Fog of World compatible GPX track from photo metadata."""

from __future__ import annotations

import argparse
import json
import locale
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Callable, Iterable
from zoneinfo import ZoneInfo


SUPPORTED_EXTENSIONS = ("jpg", "jpeg", "heic", "png")
EXIF_DATE_FORMAT = "%Y:%m:%d %H:%M:%S"
GPX_NAMESPACE = "http://www.topografix.com/GPX/1/1"
XSI_NAMESPACE = "http://www.w3.org/2001/XMLSchema-instance"
SCHEMA_LOCATION = (
    "http://www.topografix.com/GPX/1/1 "
    "http://www.topografix.com/GPX/1/1/gpx.xsd"
)
YEAR_DIR_PATTERN = re.compile(r"^\d{4}$")
SPLIT_SCAN_THRESHOLD = 1000


@dataclass
class TrackPoint:
    source_file: str
    capture_time_local: datetime
    capture_time_utc: datetime
    latitude: float
    longitude: float
    altitude: float | None


@dataclass
class ConversionResult:
    input_dir: Path
    output_path: Path | None
    track_points: list[TrackPoint]
    skipped_count: int
    warning_text: str | None


@dataclass
class RunOptions:
    input_dir: Path
    output: Path | None = None
    timezone_name: str | None = None
    track_name: str | None = None
    reuse_existing_child_gpx: bool = False
    skip_existing_output: bool = False


@dataclass
class RunSummary:
    mode: str
    input_dir: Path
    output_path: Path | None
    track_points: int
    skipped_files: int
    timezone_name: str
    warning_text: str | None
    detail_lines: list[str]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a GPX track from geotagged photos for Fog of World."
    )
    parser.add_argument("input_dir", help="Folder containing photos to scan")
    parser.add_argument(
        "-o",
        "--output",
        help=(
            "Output GPX file path. Defaults to "
            "<input_dir>/<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx"
        ),
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
        help="Track name written into the GPX file. Defaults to the input folder name.",
    )
    parser.add_argument(
        "--reuse-existing-child-gpx",
        action="store_true",
        help=(
            "For yearly folders, reuse the newest child-directory GPX when present "
            "instead of rescanning that child directory."
        ),
    )
    parser.add_argument(
        "--skip-existing-output",
        action="store_true",
        help=(
            "Skip writing a new GPX when the target directory already contains a "
            "matching Fog of World GPX output. Useful for resumable long-running scans."
        ),
    )
    return parser.parse_args()


def slugify_folder_name(name: str) -> str:
    normalized = re.sub(r"\s+", "-", name.strip())
    normalized = re.sub(r'[<>:"/\\|?*]+', "-", normalized)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-.")
    return normalized or "photo-folder"


def existing_output_path(input_dir: Path) -> Path | None:
    candidates = sorted(
        input_dir.glob(f"{slugify_folder_name(input_dir.name)}_fog_of_world_*.gpx"),
        key=lambda path: path.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def default_output_path(input_dir: Path, now: datetime | None = None) -> Path:
    timestamp = (now or datetime.now()).strftime("%Y%m%d-%H%M%S")
    folder_name = slugify_folder_name(input_dir.name)
    return input_dir / f"{folder_name}_fog_of_world_{timestamp}.gpx"


def normalize_cli_path(path_value: str) -> Path:
    expanded = os.path.expanduser(path_value)
    return Path(os.path.abspath(expanded))


def prepare_windows_long_path(path_value: Path) -> str:
    resolved = str(path_value)
    if os.name != "nt":
        return resolved
    normalized = resolved.replace("/", "\\")
    if normalized.startswith("\\\\?\\"):
        return normalized
    if normalized.startswith("\\\\"):
        return "\\\\?\\UNC\\" + normalized.lstrip("\\")
    return "\\\\?\\" + normalized


def resolve_default_timezone(tz_name: str | None) -> ZoneInfo | timezone:
    if tz_name:
        return ZoneInfo(tz_name)
    return datetime.now().astimezone().tzinfo or timezone.utc


def find_exiftool() -> str:
    discovered = shutil.which("exiftool")
    if discovered:
        return discovered

    bundled_base_dirs: list[Path] = []
    if getattr(sys, "frozen", False):
        bundled_base_dirs.append(Path(sys.executable).resolve().parent)
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled_base_dirs.append(Path(meipass))

    bundled_base_dirs.extend(
        [
            Path(__file__).resolve().parent,
            Path(__file__).resolve().parent.parent,
        ]
    )

    bundled_names = [
        "exiftool.exe",
        "ExifTool.exe",
        "tools/exiftool.exe",
        "tools/ExifTool.exe",
    ]
    for base_dir in bundled_base_dirs:
        for bundled_name in bundled_names:
            candidate = base_dir / bundled_name
            if candidate.exists():
                return str(candidate)

    local_app_data = os.environ.get("LOCALAPPDATA")
    candidates = [
        Path(r"C:\Users\micky\AppData\Local\Programs\ExifTool\ExifTool.exe"),
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


def count_supported_files(input_dir: Path) -> int:
    total = 0
    for path in input_dir.rglob("*"):
        if path.is_file() and path.suffix.lower().lstrip(".") in SUPPORTED_EXTENSIONS:
            total += 1
    return total


def count_supported_files_non_recursive(input_dir: Path) -> int:
    total = 0
    for path in input_dir.iterdir():
        if path.is_file() and path.suffix.lower().lstrip(".") in SUPPORTED_EXTENSIONS:
            total += 1
    return total


def count_supported_files_in_immediate_child_dirs(input_dir: Path) -> list[tuple[Path, int]]:
    child_counts: list[tuple[Path, int]] = []
    for child in input_dir.iterdir():
        if child.is_dir():
            child_counts.append((child, count_supported_files(child)))
    return child_counts


def exiftool_filename_charset() -> str:
    if os.name == "nt":
        encoding = locale.getpreferredencoding(False).lower()
        if encoding in {"cp950", "ms950", "big5"}:
            return "cp950"
    return "utf8"


def normalize_exiftool_warning_text(warning_text: str | None) -> str | None:
    if not warning_text:
        return None

    filtered_lines: list[str] = []
    for line in warning_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("Invalid Charset cp950"):
            continue
        if stripped.startswith("FileName encoding not specified."):
            continue
        filtered_lines.append(stripped)

    if not filtered_lines:
        return None
    return "\n".join(filtered_lines)


def read_photo_metadata(input_dir: Path, exiftool_cmd: str) -> tuple[list[dict], str | None]:
    command = [
        exiftool_cmd,
        "-n",
        "-json",
        "-charset",
        f"filename={exiftool_filename_charset()}",
        "-if",
        "($gpslatitude and $gpslongitude) and ($datetimeoriginal or $createdate)",
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

    result = subprocess.run(command, capture_output=True, check=False)
    stdout_text = result.stdout.decode("utf-8", errors="replace")
    stderr_text = normalize_exiftool_warning_text(
        result.stderr.decode("utf-8", errors="replace").strip() or None
    )

    if not stdout_text.strip():
        if result.returncode != 0 and not stderr_text:
            raise SystemExit("exiftool failed without producing metadata")
        return [], stderr_text

    return json.loads(stdout_text), stderr_text


def read_photo_metadata_non_recursive(
    input_dir: Path, exiftool_cmd: str
) -> tuple[list[dict], str | None]:
    command = [
        exiftool_cmd,
        "-n",
        "-json",
        "-charset",
        f"filename={exiftool_filename_charset()}",
        "-if",
        "($gpslatitude and $gpslongitude) and ($datetimeoriginal or $createdate)",
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

    result = subprocess.run(command, capture_output=True, check=False)
    stdout_text = result.stdout.decode("utf-8", errors="replace")
    stderr_text = normalize_exiftool_warning_text(
        result.stderr.decode("utf-8", errors="replace").strip() or None
    )

    if not stdout_text.strip():
        if result.returncode != 0 and not stderr_text:
            raise SystemExit("exiftool failed without producing metadata")
        return [], stderr_text

    return json.loads(stdout_text), stderr_text


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


def parse_flexible_exif_datetime(timestamp_text: str) -> datetime | None:
    normalized = " ".join(timestamp_text.strip().split())
    normalized = normalized.replace("\u4e0a\u5348", "AM").replace("\u4e0b\u5348", "PM")

    for candidate in {
        normalized,
        re.sub(r"\b(AM|PM)\b\s*", "", normalized).strip(),
        re.sub(r"\s*(AM|PM)\s*$", lambda m: f" {m.group(1)}", normalized).strip(),
    }:
        for fmt in (EXIF_DATE_FORMAT, "%Y:%m:%d %I:%M:%S %p", "%Y:%m:%d %p %I:%M:%S"):
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
    return None


def parse_exif_datetime(timestamp_text: str) -> datetime | None:
    normalized = " ".join(timestamp_text.strip().split())
    normalized = normalized.replace("上午", "AM").replace("下午", "PM")

    for candidate in {
        normalized,
        re.sub(r"\b(AM|PM)\b\s*", "", normalized).strip(),
        re.sub(r"\s*(AM|PM)\s*$", lambda m: f" {m.group(1)}", normalized).strip(),
    }:
        for fmt in (EXIF_DATE_FORMAT, "%Y:%m:%d %I:%M:%S %p", "%Y:%m:%d %p %I:%M:%S"):
            try:
                return datetime.strptime(candidate, fmt)
            except ValueError:
                continue
    return None


def pick_capture_time(entry: dict) -> str | None:
    return entry.get("DateTimeOriginal") or entry.get("CreateDate")


def build_track_points(
    metadata_rows: Iterable[dict], fallback_tz: ZoneInfo | timezone
) -> list[TrackPoint]:
    track_points: list[TrackPoint] = []

    for entry in metadata_rows:
        source_file = entry.get("SourceFile") or entry.get("FileName") or "<unknown>"
        timestamp_text = pick_capture_time(entry)
        latitude = entry.get("GPSLatitude")
        longitude = entry.get("GPSLongitude")
        altitude = entry.get("GPSAltitude")

        if not timestamp_text or latitude is None or longitude is None:
            continue

        naive_time = parse_flexible_exif_datetime(timestamp_text)
        if naive_time is None:
            continue
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
    return track_points


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
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(prepare_windows_long_path(output_path), "wb") as handle:
        tree.write(handle, encoding="utf-8", xml_declaration=True)


def find_child_dirs(input_dir: Path) -> list[Path]:
    child_dirs = [
        child
        for child in input_dir.iterdir()
        if child.is_dir()
    ]
    return sorted(child_dirs, key=lambda path: path.name)


def find_latest_child_gpx(child_dir: Path) -> Path | None:
    candidates = sorted(
        child_dir.glob("*_fog_of_world_*.gpx"),
        key=lambda path: path.stat().st_mtime,
    )
    return candidates[-1] if candidates else None


def build_default_track_name(input_dir: Path) -> str:
    return input_dir.name


def read_track_points_from_gpx(gpx_path: Path) -> list[TrackPoint]:
    tree = ET.parse(gpx_path)
    root = tree.getroot()
    namespace = {"gpx": GPX_NAMESPACE}
    track_points: list[TrackPoint] = []

    for point_el in root.findall(".//gpx:trkpt", namespace):
        lat = point_el.attrib.get("lat")
        lon = point_el.attrib.get("lon")
        time_el = point_el.find("gpx:time", namespace)
        ele_el = point_el.find("gpx:ele", namespace)
        if lat is None or lon is None or time_el is None or not time_el.text:
            continue
        capture_time_utc = datetime.fromisoformat(time_el.text.replace("Z", "+00:00"))
        track_points.append(
            TrackPoint(
                source_file=str(gpx_path),
                capture_time_local=capture_time_utc,
                capture_time_utc=capture_time_utc,
                latitude=float(lat),
                longitude=float(lon),
                altitude=float(ele_el.text) if ele_el is not None and ele_el.text else None,
            )
        )

    track_points.sort(key=lambda item: item.capture_time_utc)
    return track_points


def convert_directory(
    input_dir: Path,
    exiftool_cmd: str,
    fallback_tz: ZoneInfo | timezone,
    output_path: Path | None = None,
    track_name: str | None = None,
    skip_existing_output: bool = False,
) -> ConversionResult:
    existing_output = None
    if skip_existing_output and output_path is None:
        existing_output = existing_output_path(input_dir)
        if existing_output is not None:
            reused_points = read_track_points_from_gpx(existing_output)
            return ConversionResult(
                input_dir=input_dir,
                output_path=existing_output,
                track_points=reused_points,
                skipped_count=0,
                warning_text="reused existing output GPX",
            )

    supported_file_count = count_supported_files(input_dir)
    metadata_rows, warning_text = read_photo_metadata(input_dir, exiftool_cmd)
    track_points = build_track_points(metadata_rows, fallback_tz)

    resolved_output = output_path or default_output_path(input_dir)
    if track_points:
        gpx_root = build_gpx(track_points, track_name or build_default_track_name(input_dir))
        write_gpx(resolved_output, gpx_root)
    else:
        resolved_output = None

    return ConversionResult(
        input_dir=input_dir,
        output_path=resolved_output,
        track_points=track_points,
        skipped_count=max(supported_file_count - len(track_points), 0),
        warning_text=warning_text,
    )


def merge_warning_texts(warning_texts: list[str | None]) -> str | None:
    normalized = [text.strip() for text in warning_texts if text and text.strip()]
    if not normalized:
        return None
    return "\n".join(dict.fromkeys(normalized))


def preferred_output_encoding() -> str:
    for stream in (sys.stdout, sys.stderr):
        encoding = getattr(stream, "encoding", None)
        if encoding:
            return encoding
    return "utf-8"


def convert_directory_non_recursive(
    input_dir: Path,
    exiftool_cmd: str,
    fallback_tz: ZoneInfo | timezone,
    output_path: Path | None = None,
    track_name: str | None = None,
    skip_existing_output: bool = False,
) -> ConversionResult:
    existing_output = None
    if skip_existing_output and output_path is None:
        existing_output = existing_output_path(input_dir)
        if existing_output is not None:
            reused_points = read_track_points_from_gpx(existing_output)
            return ConversionResult(
                input_dir=input_dir,
                output_path=existing_output,
                track_points=reused_points,
                skipped_count=0,
                warning_text="reused existing output GPX",
            )

    supported_file_count = count_supported_files_non_recursive(input_dir)
    metadata_rows, warning_text = read_photo_metadata_non_recursive(input_dir, exiftool_cmd)
    track_points = build_track_points(metadata_rows, fallback_tz)

    resolved_output = output_path or default_output_path(input_dir)
    if track_points:
        gpx_root = build_gpx(track_points, track_name or build_default_track_name(input_dir))
        write_gpx(resolved_output, gpx_root)
    else:
        resolved_output = None

    return ConversionResult(
        input_dir=input_dir,
        output_path=resolved_output,
        track_points=track_points,
        skipped_count=max(supported_file_count - len(track_points), 0),
        warning_text=warning_text,
    )


def convert_directory_adaptive(
    input_dir: Path,
    exiftool_cmd: str,
    fallback_tz: ZoneInfo | timezone,
    output_path: Path | None = None,
    track_name: str | None = None,
    split_threshold: int = SPLIT_SCAN_THRESHOLD,
    skip_existing_output: bool = False,
    line_printer: Callable[[str], None] | None = None,
) -> ConversionResult:
    child_counts = count_supported_files_in_immediate_child_dirs(input_dir)
    total_child_supported_files = sum(count for _, count in child_counts)
    child_dirs_with_supported_files = [child for child, count in child_counts if count > 0]

    if child_dirs_with_supported_files and total_child_supported_files > split_threshold:
        merged_points: list[TrackPoint] = []
        child_skipped_total = 0
        child_warning_texts: list[str | None] = []

        for child_dir in child_dirs_with_supported_files:
            child_result = convert_directory_adaptive(
                child_dir,
                exiftool_cmd,
                fallback_tz,
                split_threshold=split_threshold,
                skip_existing_output=skip_existing_output,
                line_printer=line_printer,
            )
            if line_printer:
                for line in format_conversion_summary(child_result, fallback_tz, label=child_dir.name):
                    line_printer(line)
            merged_points.extend(child_result.track_points)
            child_skipped_total += child_result.skipped_count
            child_warning_texts.append(child_result.warning_text)

        root_result = convert_directory_non_recursive(
            input_dir,
            exiftool_cmd,
            fallback_tz,
            skip_existing_output=skip_existing_output,
        )
        if line_printer:
            for line in format_conversion_summary(root_result, fallback_tz, label=f"{input_dir.name} ROOT"):
                line_printer(line)
        merged_points.extend(root_result.track_points)
        merged_points.sort(key=lambda item: item.capture_time_utc)

        resolved_output = output_path or default_output_path(input_dir)
        if merged_points:
            gpx_root = build_gpx(merged_points, track_name or build_default_track_name(input_dir))
            write_gpx(resolved_output, gpx_root)
        else:
            resolved_output = None

        return ConversionResult(
            input_dir=input_dir,
            output_path=resolved_output,
            track_points=merged_points,
            skipped_count=child_skipped_total + root_result.skipped_count,
            warning_text=merge_warning_texts(child_warning_texts + [root_result.warning_text]),
        )

    return convert_directory(
        input_dir,
        exiftool_cmd,
        fallback_tz,
        output_path=output_path,
        track_name=track_name,
        skip_existing_output=skip_existing_output,
    )


def format_conversion_summary(
    result: ConversionResult, fallback_tz: ZoneInfo | timezone, label: str | None = None
) -> list[str]:
    prefix = f"{label}: " if label else ""
    lines: list[str] = []
    if result.output_path:
        lines.append(f"{prefix}Wrote GPX: {result.output_path}")
    else:
        lines.append(f"{prefix}No photos with both timestamp and GPS coordinates were found")
    lines.append(f"{prefix}Track points: {len(result.track_points)}")
    lines.append(f"{prefix}Skipped files: {result.skipped_count}")
    if result.warning_text:
        output_encoding = preferred_output_encoding()
        safe_warning_text = result.warning_text.encode(
            output_encoding, errors="replace"
        ).decode(output_encoding, errors="replace")
        lines.append(f"{prefix}ExifTool warnings: {safe_warning_text}")
    lines.append(
        f"{prefix}Timezone assumption: "
        f"{getattr(fallback_tz, 'key', str(fallback_tz))} for timestamps without offsets"
    )
    return lines


def print_conversion_summary(
    result: ConversionResult, fallback_tz: ZoneInfo | timezone, label: str | None = None
) -> None:
    for line in format_conversion_summary(result, fallback_tz, label=label):
        print(line)


def run_conversion(options: RunOptions, line_printer: Callable[[str], None] | None = None) -> RunSummary:
    input_dir = options.input_dir
    if not input_dir.exists() or not input_dir.is_dir():
        raise SystemExit(f"Input directory does not exist: {input_dir}")

    exiftool_cmd = find_exiftool()
    ensure_exiftool_available(exiftool_cmd)
    fallback_tz = resolve_default_timezone(options.timezone_name)
    timezone_name = getattr(fallback_tz, "key", str(fallback_tz))
    child_dirs = find_child_dirs(input_dir) if YEAR_DIR_PATTERN.fullmatch(input_dir.name) else []

    detail_lines: list[str] = []

    if child_dirs:
        yearly_points: list[TrackPoint] = []
        saw_warning = False
        total_skipped_files = 0
        yearly_output_path = options.output or default_output_path(input_dir)

        for child_dir in child_dirs:
            existing_child_gpx = (
                find_latest_child_gpx(child_dir)
                if options.reuse_existing_child_gpx
                else None
            )
            if existing_child_gpx:
                child_points = read_track_points_from_gpx(existing_child_gpx)
                child_result = ConversionResult(
                    input_dir=child_dir,
                    output_path=existing_child_gpx,
                    track_points=child_points,
                    skipped_count=0,
                    warning_text="reused existing child-directory GPX",
                )
            else:
                child_result = convert_directory_adaptive(
                    child_dir,
                    exiftool_cmd,
                    fallback_tz,
                    skip_existing_output=options.skip_existing_output,
                    line_printer=line_printer,
                )

            child_lines = format_conversion_summary(child_result, fallback_tz, label=child_dir.name)
            detail_lines.extend(child_lines)
            if line_printer:
                for line in child_lines:
                    line_printer(line)
            yearly_points.extend(child_result.track_points)
            total_skipped_files += child_result.skipped_count
            saw_warning = saw_warning or bool(child_result.warning_text)

        root_result = convert_directory_non_recursive(
            input_dir,
            exiftool_cmd,
            fallback_tz,
            skip_existing_output=options.skip_existing_output,
        )
        root_lines = format_conversion_summary(root_result, fallback_tz, label="ROOT")
        detail_lines.extend(root_lines)
        if line_printer:
            for line in root_lines:
                line_printer(line)
        yearly_points.extend(root_result.track_points)
        total_skipped_files += root_result.skipped_count
        saw_warning = saw_warning or bool(root_result.warning_text)

        yearly_points.sort(key=lambda item: item.capture_time_utc)
        if not yearly_points:
            return RunSummary(
                mode="year",
                input_dir=input_dir,
                output_path=None,
                track_points=0,
                skipped_files=total_skipped_files,
                timezone_name=timezone_name,
                warning_text="No photos with both timestamp and GPS coordinates were found",
                detail_lines=detail_lines,
            )

        yearly_gpx_root = build_gpx(
            yearly_points, options.track_name or build_default_track_name(input_dir)
        )
        write_gpx(yearly_output_path, yearly_gpx_root)
        detail_lines.extend(
            [
                f"YEAR: Wrote GPX: {yearly_output_path}",
                f"YEAR: Track points: {len(yearly_points)}",
                f"YEAR: Skipped files: {total_skipped_files}",
            ]
        )
        if saw_warning:
            detail_lines.append(
                "YEAR: Completed with one or more ExifTool warnings during monthly scans"
            )
        if line_printer:
            for line in detail_lines[-(4 if saw_warning else 3):]:
                line_printer(line)

        return RunSummary(
            mode="year",
            input_dir=input_dir,
            output_path=yearly_output_path,
            track_points=len(yearly_points),
            skipped_files=total_skipped_files,
            timezone_name=timezone_name,
            warning_text=(
                "Completed with one or more ExifTool warnings during monthly scans"
                if saw_warning
                else None
            ),
            detail_lines=detail_lines,
        )

    single_result = convert_directory_adaptive(
        input_dir,
        exiftool_cmd,
        fallback_tz,
        output_path=options.output,
        track_name=options.track_name,
        skip_existing_output=options.skip_existing_output,
        line_printer=None,
    )
    detail_lines = format_conversion_summary(single_result, fallback_tz)
    if line_printer:
        for line in detail_lines:
            line_printer(line)
    return RunSummary(
        mode="single",
        input_dir=input_dir,
        output_path=single_result.output_path,
        track_points=len(single_result.track_points),
        skipped_files=single_result.skipped_count,
        timezone_name=timezone_name,
        warning_text=single_result.warning_text,
        detail_lines=detail_lines,
    )


def main() -> int:
    args = parse_args()
    summary = run_conversion(
        RunOptions(
            input_dir=normalize_cli_path(args.input_dir),
            output=normalize_cli_path(args.output) if args.output else None,
            timezone_name=args.timezone,
            track_name=args.name,
            reuse_existing_child_gpx=args.reuse_existing_child_gpx,
            skip_existing_output=args.skip_existing_output,
        ),
        line_printer=print,
    )
    return 0 if summary.track_points else 1


if __name__ == "__main__":
    sys.exit(main())
