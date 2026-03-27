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
4. If the target is a yearly folder named like `2015`, let the script process each first-level child directory independently, write one GPX into that child directory, and then write a merged yearly GPX into the year folder.
5. Before scanning a first-level child directory, count the supported photos inside its immediate child directories. If that subtotal is greater than `1000`, scan one level deeper: write GPX files inside those immediate child directories first, then merge them back into a GPX at the first-level child directory.
6. The merged yearly GPX must include both the points from every first-level child directory GPX and any supported photos stored directly at the year root.
7. If photo timestamps do not include an offset, pass `--timezone` using the user's locale timezone when it is known.
8. Return the output GPX path and summarize how many files became track points versus how many were skipped.
9. When the yearly folder already has valid child-directory GPX files and a full rescan would take too long, it is acceptable to reuse the latest GPX in each child directory and only rescan child directories that do not have one yet.

## Command

Run:

```powershell
py C:\Users\micky\.codex\skills\photos-to-fog-of-world\scripts\build_fog_gpx.py "<input-folder>" --timezone "<IANA timezone>"
```

Use `-o "<output-file>"` to override the default yearly or single-folder output path. The default output file is `<input-folder>\<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`.
Use `--reuse-existing-child-gpx` when a yearly folder already contains child GPX files that should be merged without rescanning those child directories.

## Conversion Rules

- Read photos recursively for normal folders and for each first-level child directory inside a yearly folder.
- Accept `jpg`, `jpeg`, `heic`, and `png`.
- Use `DateTimeOriginal` first and fall back to `CreateDate`.
- Use only files that have both timestamp and GPS coordinates.
- Let `exiftool` pre-filter files that are missing GPS or timestamps when scanning large folders.
- When the input folder is a year bucket like `2015`, process every first-level child directory independently before producing the merged yearly GPX.
- Before scanning a first-level child directory, total the supported photos across its immediate child directories. If that subtotal is greater than `1000`, process those immediate child directories individually first and then merge them back into the first-level child directory GPX.
- Include supported photos stored directly at the yearly root in the merged yearly GPX.
- When scanning a yearly folder, rescan every first-level child directory so the child GPX files and yearly GPX are produced from the same run.
- If `--reuse-existing-child-gpx` is passed, reuse the latest GPX in each first-level child directory and only rescan child directories that do not already have one.
- Sort all retained points by capture time ascending.
- Convert GPX times to UTC.
- Preserve altitude when present.

## Output Expectations

- Produce a `.gpx` file that Fog of World can import.
- Prefer the default timestamped filename so repeated exports from different folders remain distinguishable.
- For year-bucket inputs, leave each child-directory GPX beside the corresponding photos and write the merged yearly GPX at the year root.
- Mention the timezone assumption when timestamps lacked an embedded offset.
- Call out skipped files when they were missing GPS or timestamps.

## Script

Use [scripts/build_fog_gpx.py](C:\Users\micky\.codex\skills\photos-to-fog-of-world\scripts\build_fog_gpx.py) for the conversion. Prefer running the script instead of rebuilding GPX logic manually.
