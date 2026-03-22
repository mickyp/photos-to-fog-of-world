# Photos to Fog of World

將資料夾中的地理標記照片轉換為 Fog of World 可匯入的 `GPX` 軌跡檔。

這個 skill 會遞迴掃描照片、從 EXIF 中擷取拍攝時間與 GPS 座標，依拍攝時間排序後輸出 `GPX` 檔案，供 Fog of World 匯入。

## 支援的照片格式

- `jpg`
- `jpeg`
- `heic`
- `png`

## 需求

- Python 3
- `exiftool`

## 輸出結果

腳本會建立一個 `GPX` 軌跡檔。

預設輸出路徑：

- `<input-folder>/fog_of_world_import.gpx`

## 轉換規則

轉換流程遵循以下規則：

- 遞迴掃描照片
- 優先使用 `DateTimeOriginal`，若沒有則退回 `CreateDate`
- 只保留同時具有拍攝時間與 GPS 座標的檔案
- 依拍攝時間由早到晚排序
- 將 GPX 時間統一轉為 UTC
- 若有高度資訊則一併保留

## 指令範例

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" --timezone "Asia/Taipei"
```

指定輸出檔案：

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\fog_of_world_import.gpx" --timezone "Asia/Taipei"
```

## Codex 使用範例

```text
Use $photos-to-fog-of-world to convert C:\path\to\photos into a Fog of World GPX file.
```

## 專案結構

- `SKILL.md`：skill 定義與使用說明
- `agents/openai.yaml`：UI metadata
- `scripts/build_fog_gpx.py`：轉換腳本

## 備註

- 沒有 GPS 座標的照片會被略過
- 如果照片時間沒有內嵌時區偏移，會使用 `--timezone` 作為當地時間假設
- Fog of World 支援匯入既有軌跡的 `GPX` 或 `KML`
