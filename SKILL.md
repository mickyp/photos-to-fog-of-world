---
name: photos-to-fog-of-world
description: Convert a folder of photos into a Fog of World importable GPX track by extracting EXIF timestamps and GPS coordinates, sorting points by capture time, and writing a GPX file. Use when the user wants to turn geotagged JPG, JPEG, HEIC, or PNG photos into Fog of World track data, especially when they provide or mention a photo folder to scan.
---

# Photos To Fog Of World

## Overview

Convert geotagged photos into a Fog of World compatible GPX track. Run the bundled script against the target folder, keep only photos with timestamps and GPS, and tell the user what was included or skipped.

## Workflow

1. Confirm the target folder path. Assume the current workspace if the user clearly refers to it.
2. Check that `exiftool` is available. Install it if the user asks and the environment allows it.
3. Run `scripts/build_fog_gpx.py` with the folder path.
4. If photo timestamps do not include an offset, pass `--timezone` using the user's locale timezone when it is known.
5. Return the output GPX path and summarize how many files became track points versus how many were skipped.

## Command

Run:

```powershell
py C:\Users\169896\.codex\skills\photos-to-fog-of-world\scripts\build_fog_gpx.py "<input-folder>" --timezone "<IANA timezone>"
```

Use `-o "<output-file>"` to override the default output path. The default output file is `<input-folder>\fog_of_world_import.gpx`.

## Conversion Rules

- Read photos recursively.
- Accept `jpg`, `jpeg`, `heic`, and `png`.
- Use `DateTimeOriginal` first and fall back to `CreateDate`.
- Use only files that have both timestamp and GPS coordinates.
- Sort all retained points by capture time ascending.
- Convert GPX times to UTC.
- Preserve altitude when present.

## Output Expectations

- Produce a `.gpx` file that Fog of World can import.
- Mention the timezone assumption when timestamps lacked an embedded offset.
- Call out skipped files when they were missing GPS or timestamps.

## Script

Use [scripts/build_fog_gpx.py](C:\Users\169896\.codex\skills\photos-to-fog-of-world\scripts\build_fog_gpx.py) for the conversion. Prefer running the script instead of rebuilding GPX logic manually.
