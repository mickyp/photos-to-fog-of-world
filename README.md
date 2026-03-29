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

If you want to share this with Windows users who do not have Python or a local coding agent, this repo now also includes:

- `scripts/fog_gpx_cli.py`: a friendlier command-line entry point
- `scripts/fog_gpx_gui.py`: a simple desktop window for choosing a folder
- `scripts/build_windows_exe.ps1`: a packaging script that builds single-file Windows `.exe` files and bundles `exiftool.exe`

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

Windows-friendly CLI wrapper:

```powershell
py scripts/fog_gpx_cli.py --input "C:\path\to\photos" --timezone "Asia/Taipei"
```

Optional output override:

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\trip_fog_of_world_20260322-120000.gpx" --timezone "Asia/Taipei"
```

Optional yearly merge that reuses existing child-directory GPX files:

```powershell
py scripts/build_fog_gpx.py "C:\path\to\2015" --timezone "Asia/Taipei" --reuse-existing-child-gpx
```

## GUI Usage

Launch the simple desktop app:

```powershell
py scripts/fog_gpx_gui.py
```

Then:

1. Choose the photo folder.
2. Optionally choose a GPX output path.
3. Click `Export GPX`.

The app shows progress and alerts you when the file is ready.

The GUI can switch between English and Traditional Chinese from the language selector at the top of the window.

### GUI Field Guide

- `Photo folder`: The folder that will be scanned. This is the main required field.
- `Output GPX (optional)`: Where to save the GPX file. If left blank, the app creates a timestamped GPX inside the selected photo folder.
- `Timezone`: Used only when photo timestamps do not already include timezone information. `Asia/Taipei` is a good default for photos taken in Taiwan.
- `Track name (optional)`: The name stored inside the GPX track itself. This is what some apps may show after import. If left blank, the selected folder name is used.
- `Reuse existing child GPX for yearly folders`: Useful when the selected folder is a year folder such as `2019` and some child folders have already been exported before. The app will reuse those child GPX files instead of rescanning everything.
- `Skip writing a new GPX when one already exists`: If a matching GPX already exists in the target folder, reuse it instead of creating another new file.

### GUI Filling Tips

- For most normal cases, fill only `Photo folder` and leave the rest at their defaults.
- Fill `Output GPX` only if you want the GPX saved somewhere else or under a specific filename.
- Fill `Track name` only if you want a nicer display name after importing into Fog of World or another map app.
- Turn on the two checkboxes mainly for large or repeated scans.
- Use the language selector at the top if the user prefers English or Traditional Chinese.

## Build Windows EXEs

Build both the CLI and GUI executables:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```

By default this creates:

- `dist\photos-to-gpx-cli.exe`
- `dist\photos-to-gpx-gui.exe`

The packaging script bundles `exiftool.exe` inside each executable, so the recipient only needs a single downloaded `.exe`.

## Example Codex Prompt

```text
Use $photos-to-fog-of-world to convert C:\path\to\photos into Fog of World GPX files.
```

## Repository Layout

- `SKILL.md`: Skill definition and usage instructions
- `agents/openai.yaml`: UI metadata
- `scripts/build_fog_gpx.py`: Conversion script
- `scripts/fog_gpx_cli.py`: CLI wrapper for end users
- `scripts/fog_gpx_gui.py`: GUI wrapper for end users
- `scripts/build_windows_exe.ps1`: Windows packaging helper

## Notes

- Photos without GPS coordinates are skipped
- If timestamps do not include an offset, the provided `--timezone` value is used as the local timezone assumption
- If the input is a year bucket, the script processes every first-level child directory and then creates a merged year track
- Large first-level child directories are automatically split one level deeper when their immediate child directories contain more than `1000` supported photos in total
- When a year-root photo does not contain both timestamp and GPS metadata, it is skipped from the merged year track
- Fog of World supports importing existing tracks via `GPX` or `KML`
