# Photos to Fog of World

Convert a folder of geotagged photos into Fog of World compatible `GPX` tracks.

This skill scans photos recursively, extracts timestamps and GPS coordinates from EXIF metadata, sorts usable points by capture time, and writes `GPX` files that Fog of World can import.

Traditional Chinese README:
- [README.zh-TW.md](README.zh-TW.md)

## Supported Photo Types

- `jpg`
- `jpeg`
- `heic`
- `png`

## Requirements

- Python 3
- `exiftool`

### Install `exiftool` on Windows

If `exiftool` is not already available on `PATH`, install it with Scoop:

```powershell
scoop install exiftool
```

## Output

The script creates one or more `GPX` track files.

Default output paths:

- Single folder: `<input-folder>/<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- Year folder named like `2015`:
- Child directory GPX: `<input-folder>/<child>/<child>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- Yearly merged: `<input-folder>/<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`

## How It Works

The conversion uses these rules:

- Read photos recursively
- For year folders, process each first-level child directory independently and then merge them
- Before scanning a first-level child directory, count supported photos in its immediate child directories; if their subtotal is greater than `1000`, scan those immediate child directories individually first and then merge them into the first-level child directory GPX
- Use `DateTimeOriginal` first and fall back to `CreateDate`
- Keep only files that have both timestamp and GPS coordinates
- Ask `exiftool` to pre-filter files that are missing GPS or timestamps
- Include supported photos stored directly at the year root when building the yearly merged GPX
- Sort all retained points by capture time ascending
- Convert GPX timestamps to UTC
- Preserve altitude when available
- Optionally reuse the latest child-directory `GPX` file with `--reuse-existing-child-gpx` when a year-folder merge is rerun

## Command

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" --timezone "Asia/Taipei"
```

Optional output override:

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\trip_fog_of_world_20260322-120000.gpx" --timezone "Asia/Taipei"
```

Optional yearly merge that reuses existing child-directory GPX files:

```powershell
py scripts/build_fog_gpx.py "C:\path\to\2015" --timezone "Asia/Taipei" --reuse-existing-child-gpx
```

## Example Codex Prompt

```text
Use $photos-to-fog-of-world to convert C:\path\to\photos into Fog of World GPX files.
```

## Repository Layout

- `SKILL.md`: Skill definition and usage instructions
- `agents/openai.yaml`: UI metadata
- `scripts/build_fog_gpx.py`: Conversion script

## Notes

- Photos without GPS coordinates are skipped
- If timestamps do not include an offset, the provided `--timezone` value is used as the local timezone assumption
- If the input is a year bucket, the script processes every first-level child directory and then creates a merged year track
- Large first-level child directories are automatically split one level deeper when their immediate child directories contain more than `1000` supported photos in total
- When a year-root photo does not contain both timestamp and GPS metadata, it is skipped from the merged year track
- Fog of World supports importing existing tracks via `GPX` or `KML`
