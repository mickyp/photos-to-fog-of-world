# Photos to Fog of World

把有 GPS 資訊的照片資料夾轉成 Fog of World 可匯入的 `GPX` 軌跡。

這個工具會遞迴掃描照片、讀取拍攝時間與座標，依照拍攝時間排序後輸出 `GPX`。現在除了原本的 Python 腳本，也另外提供比較適合一般 Windows 使用者的版本：

- `scripts/fog_gpx_cli.py`：命令列版
- `scripts/fog_gpx_gui.py`：小視窗版
- `scripts/build_windows_exe.ps1`：可打包成 `.exe` 的封裝腳本

英文說明請見：
- [README.md](README.md)

## 支援格式

- `jpg`
- `jpeg`
- `heic`
- `png`

## 需求

- Python 3
- `exiftool`

### Windows 安裝 `exiftool`

如果系統中還沒有 `exiftool`，可以用 Scoop 安裝：

```powershell
scoop install exiftool
```

如果你是要封裝給別人使用，可以直接跑內建的打包腳本；它會把 `exiftool.exe` 一起放進輸出資料夾。

## 輸出結果

預設會在輸入資料夾內產生帶時間戳記的 `GPX` 檔案：

- 一般資料夾：`<input-folder>\<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- 年度資料夾（例如 `2015`）：
- 子資料夾 GPX：`<input-folder>\<child>\<child>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- 年度合併 GPX：`<input-folder>\<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`

## 轉換規則

- 遞迴掃描照片
- 若輸入是像 `2015` 這種年度資料夾，會先處理第一層子資料夾，再合併成年度 GPX
- 若某個第一層子資料夾底下的下一層照片量總和超過 `1000`，會先切得更細再合併
- 先用 `DateTimeOriginal`，沒有的話改用 `CreateDate`
- 只保留同時有拍攝時間與 GPS 的照片
- 會請 `exiftool` 先過濾掉缺少必要資訊的檔案
- 年度資料夾根目錄中的照片也會一併納入合併
- 依拍攝時間排序
- GPX 時間會轉成 UTC
- 有高度資訊就保留
- 重新處理年度資料夾時，可用 `--reuse-existing-child-gpx` 重用既有子資料夾 GPX

## 原始腳本用法

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" --timezone "Asia/Taipei"
```

指定輸出檔：

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\trip_fog_of_world_20260322-120000.gpx" --timezone "Asia/Taipei"
```

年度資料夾重用既有子資料夾 GPX：

```powershell
py scripts/build_fog_gpx.py "C:\path\to\2015" --timezone "Asia/Taipei" --reuse-existing-child-gpx
```

## 命令列版

```powershell
py scripts/fog_gpx_cli.py --input "C:\path\to\photos" --timezone "Asia/Taipei"
```

也可以另外指定輸出位置：

```powershell
py scripts/fog_gpx_cli.py --input "C:\path\to\photos" -o "C:\path\to\output\trip.gpx"
```

## 小視窗版

啟動方式：

```powershell
py scripts/fog_gpx_gui.py
```

操作流程很簡單：

1. 選擇要掃描的照片資料夾。
2. 如果要自訂輸出位置，可以另外指定 GPX 檔案位置。
3. 按下 `Export GPX`。

畫面會顯示掃描進度，完成後也會跳出提示。

GUI 視窗最上方可以切換 `正體中文` 或 `English`。

### GUI 各欄位說明

- `Photo folder`：要掃描的照片資料夾。這是最主要、一定要填的欄位。
- `Output GPX (optional)`：GPX 要存到哪裡。若留白，程式會自動在你選的照片資料夾裡建立一個帶時間的 GPX 檔。
- `Timezone`：只有在照片時間裡沒有時區資訊時才會用到。若照片是在台灣拍的，`Asia/Taipei` 通常就可以。
- `Track name (optional)`：寫進 GPX 裡的軌跡名稱。之後匯入 Fog of World 或其他地圖工具時，可能會看到這個名字。若留白，通常會直接用資料夾名稱。
- `Reuse existing child GPX for yearly folders`：如果你選的是像 `2019` 這種年度資料夾，而且底下某些子資料夾之前已經做過 GPX，勾選後會直接重用那些結果，不必整包重掃。
- `Skip writing a new GPX when one already exists`：如果目標資料夾裡已經有符合條件的 GPX，勾選後會直接沿用，不再另外建立一個新的。

### GUI 填寫建議

- 一般情況下，只要填 `Photo folder` 就可以，其它欄位維持預設值通常就夠用。
- 只有在你想把 GPX 存到別的位置，或想指定檔名時，才需要填 `Output GPX`。
- 只有在你想讓匯入後顯示更好辨認的名稱時，才需要填 `Track name`。
- 兩個勾選選項比較適合大量照片或重複匯出的情境。
- 如果使用者比較習慣英文介面，可以用視窗最上方的語言選單切換成 `English`。

## 封裝成 Windows EXE

執行：

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build_windows_exe.ps1
```

完成後會得到：

- `dist\photos-to-gpx-cli\photos-to-gpx-cli.exe`
- `dist\photos-to-gpx-gui\photos-to-gpx-gui.exe`

這兩個資料夾內都會附上 `exiftool.exe`，所以交給別人時，不需要再另外安裝 `exiftool`。

## 專案內容

- `SKILL.md`：技能說明
- `agents/openai.yaml`：介面用設定
- `scripts/build_fog_gpx.py`：核心轉換邏輯
- `scripts/fog_gpx_cli.py`：命令列入口
- `scripts/fog_gpx_gui.py`：圖形介面入口
- `scripts/build_windows_exe.ps1`：Windows 封裝腳本

## 補充

- 沒有 GPS 的照片會被略過
- 如果照片時間沒有時區資訊，會套用你指定的時區
- Fog of World 可匯入 `GPX` 或 `KML`
