# Changelog

本檔案記錄每個版本的重要變更。

## [Unreleased]

### Added

- `.cursorrules`：加入專案特定的開發指令與 commit 中文撰寫規範。
- `gpx_editor.html`：於介面上方顯示目前載入的 GPX 檔名。
- `gpx_editor.html`：在「平移」模式點擊節點時，顯示包含時間、高度與座標的資訊視窗。

### Changed

- `gpx_editor.html`：優化 GPX 匯出邏輯，僅針對人工標記的「道路路線」以每 5 公尺為單位補點，原始軌跡與直線維持原狀。
- `gpx_editor.html`：預設以原始檔名附加 `_enhanced.gpx` 匯出，移除手動輸入檔名欄位。
- `gpx_editor.html`：放大節點標記圖示（20px 改為 24px）以支援完整顯示三位數字。

## [1.0.0] - 2026-03-29

### Changes

- 讓 GUI 視窗標題顯示目前版本號
- 新增可自動產生 CHANGELOG.md 的腳本
- 建立版本規則並讓打包檔名自動帶版號
- 為 GUI 訊息區加入捲軸
- 隱藏 ExifTool 視窗並改為單檔 EXE 封裝
- 調整 GUI 版面並改為浮動提示說明
- 修正 GUI 輸出路徑同步並忽略打包產物
- 補充 GUI 欄位與雙語操作說明
- 新增可切換中英文的 GUI 匯出介面
- 新增 Windows 封裝流程與命令列匯出工具
- Update Fog of World skill workflow and docs
- Update README for Traditional Chinese documentation
- Initial skill release
