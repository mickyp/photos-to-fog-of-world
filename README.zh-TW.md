# Photos to Fog of World

把含有拍攝時間與位置資訊的照片資料夾轉成可匯入 Fog of World 的 `GPX` 軌跡檔。

這個 skill 會掃描照片、讀取 EXIF 內的拍攝時間與 GPS 座標、依時間排序，最後輸出 Fog of World 可匯入的 `GPX` 檔案。

英文說明：
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

如果系統裡還沒有 `exiftool`，可以用 Scoop 安裝：

```powershell
scoop install exiftool
```

## 輸出方式

腳本會產生一個或多個 `GPX` 檔案。

預設輸出位置：

- 單一資料夾：`<input-folder>/<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- 年度資料夾（例如 `2015`）：
- 第一層子資料夾 GPX：`<input-folder>/<child>/<child>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`
- 年度整合 GPX：`<input-folder>/<folder-name>_fog_of_world_<YYYYMMDD-HHMMSS>.gpx`

## 處理規則

- 一般資料夾會遞迴掃描照片
- 年度資料夾會先處理每個第一層子資料夾，再整合成年度 GPX
- 如果某個第一層子資料夾底下「各直接子資料夾」的支援照片總數超過 `1000` 張，會自動再往下一層拆分掃描
- 拆分掃描時，會先在那些直接子資料夾各自產生 GPX，再回收整合成該第一層子資料夾自己的 GPX
- 優先使用 `DateTimeOriginal`，沒有時改用 `CreateDate`
- 只保留同時具備拍攝時間與 GPS 座標的照片
- 會先讓 `exiftool` 過濾缺少時間或 GPS 的照片
- 年度整合時，也會把年度根目錄本身的支援照片納入判斷
- 所有可用軌跡點都會依拍攝時間由早到晚排序
- GPX 內時間會轉成 UTC
- 若有高度資訊，會一併保留
- 若加上 `--reuse-existing-child-gpx`，年度整合時可以沿用已存在的第一層子資料夾 GPX

## 指令

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" --timezone "Asia/Taipei"
```

指定輸出檔案：

```powershell
py scripts/build_fog_gpx.py "C:\path\to\photos" -o "C:\path\to\output\trip_fog_of_world_20260322-120000.gpx" --timezone "Asia/Taipei"
```

年度整合時沿用已存在的第一層子資料夾 GPX：

```powershell
py scripts/build_fog_gpx.py "C:\path\to\2015" --timezone "Asia/Taipei" --reuse-existing-child-gpx
```

## Codex 範例提示詞

```text
Use $photos-to-fog-of-world to convert C:\path\to\photos into Fog of World GPX files.
```

## 倉庫內容

- `SKILL.md`：skill 流程與操作說明
- `agents/openai.yaml`：介面顯示設定
- `scripts/build_fog_gpx.py`：實際轉換腳本

## 補充

- 沒有 GPS 的照片會被略過
- 如果照片時間沒有時區資訊，會使用 `--timezone` 提供的時區當作判斷基準
- 如果年度根目錄照片缺少時間或 GPS，就不會被放進年度 GPX
- Fog of World 可匯入 `GPX` 或 `KML`
