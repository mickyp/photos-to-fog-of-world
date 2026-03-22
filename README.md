# Photos to Fog of World

Convert a folder of geotagged photos into a Fog of World compatible `GPX` track.

This skill scans photos recursively, extracts timestamps and GPS coordinates from EXIF metadata, sorts all usable points by capture time, and writes a `GPX` file that Fog of World can import.

Traditional Chinese documentation:

- [README.zh-TW.md](README.zh-TW.md)

## Supported Photo Types

- `jpg`
- `jpeg`
- `heic`
- `png`

## Requirements

- Python 3
- `exiftool`

## Output

The script creates a `GPX` track file.

Default output path:

- `<input-folder>/fog_of_world_import.gpx`

## How It Works

The conversion uses these rules:

- Read photos recursively
- Use `DateTimeOriginal` first and fall back to `CreateDate`
- Keep only files that have both timestamp and GPS coordinates
- Sort all retained points by capture time ascending
- Convert GPX timestamps to UTC
- Preserve altitude when available

## Command

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" --timezone "Asia/Taipei"
```

Optional output override:

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\fog_of_world_import.gpx" --timezone "Asia/Taipei"
```

## Example Codex Prompt

```text
Use $photos-to-fog-of-world to convert C:\path\to\photos into a Fog of World GPX file.
```

## Repository Layout

- `SKILL.md`: Skill definition and usage instructions
- `agents/openai.yaml`: UI metadata
- `scripts/build_fog_gpx.py`: Conversion script

## Notes

- Photos without GPS coordinates are skipped
- If timestamps do not include an offset, the provided `--timezone` value is used as the local timezone assumption
- Fog of World supports importing existing tracks via `GPX` or `KML`
