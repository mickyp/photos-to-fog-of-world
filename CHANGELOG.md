# Changelog

## [Unreleased]

### Changed

- Removed unused `scripts/gpx_editor/*` stubs (CSS, app/core modules, tests); the web editor is implemented entirely in `scripts/gpx_editor.html`.
- Added explanatory comments to the adaptive conversion flow in `scripts/build_fog_gpx.py`.
- Rewrote the English and Traditional Chinese READMEs so they match the current CLI, GUI, and web editor structure.
- Rewrote `GPX_EDITOR.md` to describe the current editor workflow and file layout more clearly.
- Cleaned up `index.html` copy so the public landing page is readable again.

## [1.0.0] - 2026-03-29

### Added

- Initial release of the photo-to-GPX conversion workflow
- Windows CLI and GUI entry points
- Packaging flow for standalone Windows executables
- Fog of World skill and project documentation
