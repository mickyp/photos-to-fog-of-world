# Changelog

本檔案記錄每個版本的重要變更。

## [Unreleased]

### Added

- `gpx_editor.html`：新增地點與門牌搜尋框（使用 OpenStreetMap Nominatim API），點擊結果後可將畫面飛向定位點並顯示臨時標記。
- `.cursorrules`：加入專案特定的開發指令與 commit 中文撰寫規範。
- `gpx_editor.html`：於介面上方顯示目前載入的 GPX 檔名。
- `gpx_editor.html`：在「平移」模式點擊節點時，顯示包含時間、高度與座標的資訊視窗。

### Changed

- `gpx_editor.html`：放大左側工具列的按鈕圖示與標籤字體大小，提升閱讀舒適度。
- `gpx_editor.html`：整體視覺對比度提升，包含拉大背景不透明度、亮化次要文字顏色。
- `gpx_editor.html`：搜尋結果清單改為深色不透明背景，以改善可讀性。
- `gpx_editor.html`：搜尋標記由文字提示改為包含「新增為軌跡節點」按鈕的選單。
- `gpx_editor.html`：「道路快貼」功能（Snap Mode）在選擇多個中介點時，不再刪除中間節點，改為分別請求每一段相鄰節點的道路路線。
- `gpx_editor.html`：優化 GPX 匯出邏輯，僅針對人工標記的「道路路線」以每 5 公尺為單位補點，原始軌跡與直線維持原狀。
- `gpx_editor.html`：預設以原始檔名附加 `_enhanced.gpx` 匯出，移除手動輸入檔名欄位。
- `gpx_editor.html`：放大節點標記圖示（20px 改為 24px）以支援完整顯示三位數字。

### Fixed

- `gpx_editor.html`：修正取消道路路線模式時，原節點上標記數字消失的問題。
- `gpx_editor.html`：修正平移模式下點擊節點顯示資訊視窗後，無法連續重複開啟或關閉的問題。

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
