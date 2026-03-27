# Repository Description

## Suggested GitHub repo name

`photos-to-fog-of-world`

## Suggested short description

Convert geotagged photos and year-folder photo libraries into Fog of World importable GPX tracks.

## Suggested topics

- `codex-skill`
- `fog-of-world`
- `gpx`
- `exif`
- `exiftool`
- `geotagged-photos`
- `heic`
- `jpeg`
- `png`
- `travel`

## Suggested first release note

Initial release of the `photos-to-fog-of-world` Codex skill.

Includes:

- recursive photo scanning
- year-folder processing by first-level child directory
- automatic deeper splitting when a first-level child directory's immediate child directories contain more than 1000 supported photos in total
- merged yearly GPX output that can include year-root photos when metadata is usable
- EXIF timestamp and GPS extraction
- support for `jpg`, `jpeg`, `heic`, and `png`
- time-ordered GPX export for Fog of World
- timezone fallback handling for photos without embedded offsets
- optional reuse of existing child-directory GPX files during yearly merges
