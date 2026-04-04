# Photos to Fog of World

Convert a folder of geotagged photos into Fog of World compatible `GPX` tracks.

The project scans photos recursively, extracts timestamps and GPS coordinates from EXIF metadata, sorts usable points by capture time, and writes `GPX` files that Fog of World can import.

**Website (GitHub Pages):** [https://mickyp.github.io/photos-to-fog-of-world/](https://mickyp.github.io/photos-to-fog-of-world/)

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

The repository includes three user-facing entry points:

- `scripts/build_fog_gpx.py`: the core conversion script
- `scripts/fog_gpx_cli.py`: a Windows-friendly command-line wrapper
- `scripts/fog_gpx_gui.py`: a simple desktop window for selecting folders and exporting GPX

## Install `exiftool` on Windows

If `exiftool` is not already available on `PATH`, install it with Scoop:

```powershell
scoop install exiftool
```

If you only want the packaged Windows build, download the release artifact from GitHub Releases instead.

## Output

The tool creates one or more `GPX` track files.

Default output paths:

- Single folder: `<input-folder>/<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- Year folder named like `2015`
  - Child directory GPX: `<input-folder>/<child>/<child>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
  - Yearly merged GPX: `<input-folder>/<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`

Every default output filename includes a timestamp down to seconds. The core script, CLI, and GUI all follow the same naming rule when the output path is not supplied manually.

## Folder Selection

In normal use, choose the highest folder that represents the trip, month, or year you want to export. Do not drill down to the deepest leaf folder unless you intentionally want only that one leaf exported.

Recommended folder selection:

```text
[Choose this folder]
2024
├─ 01 Taipei Trip
│  ├─ Day 1
│  │  ├─ IMG_0001.JPG
│  │  └─ IMG_0002.JPG
│  └─ Day 2
│     └─ IMG_0003.JPG
└─ 02 Tainan Trip
   └─ Day 1
      └─ IMG_0100.JPG
```

If you choose `2024`, the tool scans downward recursively, processes each child folder, and writes a merged GPX back into `2024`.

Typical results:

```text
2024
├─ 01 Taipei Trip
│  ├─ Day 1
│  ├─ Day 2
│  └─ 01-Taipei-Trip_fog_of_world_20260329-130501.gpx
├─ 02 Tainan Trip
│  ├─ Day 1
│  └─ 02-Tainan-Trip_fog_of_world_20260329-130508.gpx
└─ 2024_fog_of_world_20260329-130520.gpx
```

Common wrong selection:

```text
2024
└─ 01 Taipei Trip
   └─ [Chosen by mistake] Day 1
      ├─ IMG_0001.JPG
      └─ IMG_0002.JPG
```

If you choose `Day 1`, the tool only exports that leaf folder. It will not automatically infer that you wanted a merged `2024` result.

## Conversion Rules

- Read photos recursively from the selected folder down to the deepest supported-photo folders
- When the input folder name looks like a year such as `2015`, process each first-level child directory independently and then merge them into a yearly GPX
- Before scanning a large first-level child directory, count supported photos in its immediate child directories; if their subtotal is greater than `1000`, scan those immediate child directories first and then merge them
- Use `DateTimeOriginal` first and fall back to `CreateDate`
- Keep only files that have both a timestamp and GPS coordinates
- Ask `exiftool` to pre-filter files missing GPS or timestamps
- Include supported photos stored directly at the year root when building the yearly merged GPX
- Sort all retained points by capture time ascending
- Convert GPX timestamps to UTC
- Preserve altitude when available
- Optionally reuse the latest child-directory `GPX` file with `--reuse-existing-child-gpx`

## Core Script

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" --timezone "Asia/Taipei"
```

Specify a custom output path:

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\trip_fog_of_world_20260322-120000.gpx" --timezone "Asia/Taipei"
```

Reuse existing child GPX files for a year folder:

```powershell
py scripts/build_fog_gpx.py "C:\path\to\2015" --timezone "Asia/Taipei" --reuse-existing-child-gpx
```

## CLI Wrapper

```powershell
py scripts/fog_gpx_cli.py --input "C:\path\to\photos" --timezone "Asia/Taipei"
```

Optional output override:

```powershell
py scripts/fog_gpx_cli.py --input "C:\path\to\photos" -o "C:\path\to\output\trip.gpx"
```

## GUI

Launch the desktop app:

```powershell
py scripts/fog_gpx_gui.py
```

Typical workflow:

1. Choose the photo folder.
2. Optionally choose a GPX output path.
3. Click `Export GPX`.

The app shows progress while scanning and alerts you when the export is complete.

### GUI Field Guide

- `Photo folder`: the top-level folder that should be scanned
- `Output GPX (optional)`: where to save the GPX file; if left blank, a timestamped file is created in the selected photo folder
- `Timezone`: used only when timestamps do not already include timezone data
- `Track name (optional)`: the name written into the GPX metadata
- `Reuse existing child GPX for yearly folders`: useful when rerunning a year-folder export
- `Skip writing a new GPX when one already exists`: reuse the newest matching GPX in the folder instead of creating another file

## Web Editor

The repository also contains a browser-based GPX editor:

- `scripts/gpx_editor.html`: standalone editor page (single self-contained HTML file)

See [GPX_EDITOR.md](GPX_EDITOR.md) for usage notes.

## Build Windows EXEs

Build both the CLI and GUI executables:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```

By default this creates:

- `dist\photos-to-gpx-cli.exe`
- `dist\photos-to-gpx-gui.exe`

Each packaged executable already includes `exiftool.exe`, so the downloaded `.exe` can be used directly without a separate `exiftool` installation.

The version number comes from the repository-root `VERSION` file. Update that file before each release. The GUI shows the version in the window title, and the CLI shows it with `--version`.

## Repository Layout

- `SKILL.md`: skill definition and usage notes
- `agents/openai.yaml`: metadata for the skill UI
- `scripts/build_fog_gpx.py`: core conversion logic
- `scripts/fog_gpx_cli.py`: end-user CLI wrapper
- `scripts/fog_gpx_gui.py`: end-user GUI wrapper
- `scripts/gpx_editor.html`: browser-based GPX editor
- `scripts/build_windows_exe.ps1`: packaging helper for Windows builds

## Notes

- Photos without GPS coordinates are skipped
- When timestamps do not include an offset, the provided `--timezone` value is used as the local timezone assumption
- Year folders are processed child-by-child and then merged back into a single yearly GPX
- Large child folders are automatically split one level deeper before merging
- Fog of World can import existing tracks from `GPX` or `KML`
