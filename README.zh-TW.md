# Photos to Fog of World

把有 GPS 資訊的照片資料夾轉成 Fog of World 可匯入的 `GPX` 軌跡。

這個專案會遞迴掃描照片、讀取拍攝時間與座標、依照拍攝時間排序，最後輸出可匯入 Fog of World 的 `GPX`。除了核心 Python 腳本，專案也提供命令列包裝與桌面視窗版本。

**官網（GitHub Pages）：** [https://mickyp.github.io/photos-to-fog-of-world/](https://mickyp.github.io/photos-to-fog-of-world/)

- [English Version](README.md)

## 支援格式

- `jpg`
- `jpeg`
- `heic`
- `png`

## 需求

- Python 3
- `exiftool`

專案提供三個主要入口：

- `scripts/build_fog_gpx.py`：核心轉換腳本
- `scripts/fog_gpx_cli.py`：較適合 Windows 使用者的命令列入口
- `scripts/fog_gpx_gui.py`：可直接選資料夾匯出 GPX 的桌面工具

## Windows 安裝 `exiftool`

如果系統中還沒有 `exiftool`，可以用 Scoop 安裝：

```powershell
scoop install exiftool
```

如果你只想直接使用封裝好的 Windows 版，可以改從 GitHub Releases 下載現成執行檔。

## 輸出結果

工具會建立一個或多個 `GPX` 檔案。

預設輸出路徑：

- 一般資料夾：`<input-folder>\<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- 年度資料夾（例如 `2015`）
  - 子資料夾 GPX：`<input-folder>\<child>\<child>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
  - 年度合併 GPX：`<input-folder>\<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`

只要沒有手動指定輸出位置，核心腳本、CLI 和 GUI 都會用同一套帶秒數時間戳記的命名方式。

## 資料夾怎麼選

一般情況下，請直接選你要匯出的上層資料夾，例如旅行、月份或年份那一層。除非你只想匯出最後一小層，否則不要特地點到最深的葉節點資料夾。

建議這樣選：

```text
[請選這層]
2024
├─ 01 台北旅行
│  ├─ Day 1
│  │  ├─ IMG_0001.JPG
│  │  └─ IMG_0002.JPG
│  └─ Day 2
│     └─ IMG_0003.JPG
└─ 02 台南旅行
   └─ Day 1
      └─ IMG_0100.JPG
```

如果你選的是 `2024`，工具會一路往下掃描、視需要分批處理，再把結果合併回 `2024` 這層。

典型結果：

```text
2024
├─ 01 台北旅行
│  ├─ Day 1
│  ├─ Day 2
│  └─ 01-台北旅行_fog_of_world_20260329-130501.gpx
├─ 02 台南旅行
│  ├─ Day 1
│  └─ 02-台南旅行_fog_of_world_20260329-130508.gpx
└─ 2024_fog_of_world_20260329-130520.gpx
```

常見誤選方式：

```text
2024
└─ 01 台北旅行
   └─ [誤選] Day 1
      ├─ IMG_0001.JPG
      └─ IMG_0002.JPG
```

如果你選的是 `Day 1`，工具就只會輸出這一小層，不會自動推測你原本想要整個 `2024` 的合併結果。

## 轉換規則

- 從選定資料夾開始遞迴往下掃描所有支援格式的照片
- 如果輸入資料夾名稱看起來像年份，例如 `2015`，會先逐一處理第一層子資料夾，再合併成年度 GPX
- 若某個第一層子資料夾的下一層照片總量超過 `1000`，會先切成更小的批次處理，再往上合併
- 優先使用 `DateTimeOriginal`，沒有的話改用 `CreateDate`
- 只保留同時具備拍攝時間與 GPS 座標的照片
- 會先請 `exiftool` 過濾掉缺少必要資訊的檔案
- 年度資料夾根目錄中的照片也會納入年度合併
- 所有保留點位都會依拍攝時間排序
- GPX 時間會轉成 UTC
- 若有高度資訊則一併保留
- 可用 `--reuse-existing-child-gpx` 重用既有子資料夾 GPX

## 核心腳本

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" --timezone "Asia/Taipei"
```

指定自訂輸出檔：

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\trip_fog_of_world_20260322-120000.gpx" --timezone "Asia/Taipei"
```

重新處理年度資料夾並重用既有子資料夾 GPX：

```powershell
py scripts/build_fog_gpx.py "C:\path\to\2015" --timezone "Asia/Taipei" --reuse-existing-child-gpx
```

## 命令列版

```powershell
py scripts/fog_gpx_cli.py --input "C:\path\to\photos" --timezone "Asia/Taipei"
```

另外指定輸出位置：

```powershell
py scripts/fog_gpx_cli.py --input "C:\path\to\photos" -o "C:\path\to\output\trip.gpx"
```

## 桌面視窗版

啟動方式：

```powershell
py scripts/fog_gpx_gui.py
```

基本流程：

1. 選擇照片資料夾。
2. 視需要指定輸出位置。
3. 按下 `Export GPX`。

視窗會顯示掃描進度，完成後也會跳出提示。

### GUI 欄位說明

- `Photo folder`：要掃描的上層照片資料夾
- `Output GPX (optional)`：GPX 要存在哪裡；留白時會自動存回照片資料夾
- `Timezone`：只有在照片時間沒有時區資訊時才會用到
- `Track name (optional)`：寫進 GPX 內的軌跡名稱
- `Reuse existing child GPX for yearly folders`：重新處理年度資料夾時，可直接重用既有子資料夾 GPX
- `Skip writing a new GPX when one already exists`：若目標資料夾內已有符合命名規則的 GPX，直接沿用，不再另外寫一份新的

## Web 編輯器

專案也包含瀏覽器版 GPX 編輯器：

- `scripts/gpx_editor.html`：獨立的編輯器頁面（單一 HTML 自包含）

操作說明請見 [GPX_EDITOR.md](GPX_EDITOR.md)。

## 封裝成 Windows EXE

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```

預設會產生：

- `dist\photos-to-gpx-cli.exe`
- `dist\photos-to-gpx-gui.exe`

這兩個執行檔都已經包含 `exiftool.exe`，因此不需要額外安裝 `exiftool`。

版本號來自專案根目錄的 `VERSION` 檔案。GUI 會在視窗標題顯示版本，CLI 可用 `--version` 查看。

## 專案內容

- `SKILL.md`：技能說明
- `agents/openai.yaml`：技能介面設定
- `scripts/build_fog_gpx.py`：核心轉換邏輯
- `scripts/fog_gpx_cli.py`：給終端使用者的 CLI 包裝
- `scripts/fog_gpx_gui.py`：給終端使用者的 GUI 包裝
- `scripts/gpx_editor.html`：瀏覽器版 GPX 編輯器
- `scripts/build_windows_exe.ps1`：Windows 封裝腳本

## 補充說明

- 沒有 GPS 座標的照片會被略過
- 如果照片時間沒有包含時區偏移，就會使用 `--timezone` 指定的時區當成當地時間
- 年度資料夾會先逐一處理子資料夾，再合併成年度 GPX
- 大型子資料夾會自動拆成更小批次處理
- Fog of World 可匯入 `GPX` 或 `KML`
