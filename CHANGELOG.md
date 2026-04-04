# Changelog

## [Unreleased]

### Added

- `README.md` / `README.zh-TW.md`：於開頭加入 GitHub Pages 官網連結 [https://mickyp.github.io/photos-to-fog-of-world/](https://mickyp.github.io/photos-to-fog-of-world/)。
- `index.html`：首頁新增「兩點之間貼道路線」示範區塊（中英說明），搭配 `images/map-auto-road.png`（Web GPX 編輯器 Road 模式 demo 截圖）。

### Changed

- `README.md` / `README.zh-TW.md`：雙語互連結文字改為「正體中文版」與「English Version」。
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
