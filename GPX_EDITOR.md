# GPX Editor

`scripts/gpx_editor.html` 是這個專案附帶的瀏覽器版 GPX 編輯器，用來把既有軌跡整理成更適合 Fog of World 匯入的版本。

它不需要額外安裝。直接用瀏覽器開啟 `scripts/gpx_editor.html` 即可使用。

## 主要用途

- 載入既有 GPX 軌跡
- 刪除不需要的點
- 補新的點位
- 把兩點之間改成貼道路線
- 搜尋地點後直接加入點位
- 匯出重新整理過的 GPX
- 儲存與載入編輯中的專案狀態

## 基本操作

1. 開啟 `scripts/gpx_editor.html`
2. 載入 GPX 檔案，或直接把檔案拖進頁面
3. 用左側工具列切換模式
4. 完成後按 `Export GPX`

## 工具列模式

- `Pan`：瀏覽地圖與查看點位資訊
- `Add`：在地圖上新增點位
- `Delete`：刪除點位
- `Road`：把選定區間改成貼道路線
- `Undo / Redo`：還原與重做

## 貼道路線

Road 模式會用 OSRM 公開路線服務取得道路幾何，再把該區段改成比較貼近實際道路的走法。

可選模式：

- `Car / motorcycle routing`
- `Bicycle routing`
- `Walking routing`
- `Straight line between points`

如果 OSRM 沒有成功回傳路線，該區段會退回直線連接。

## 匯出規則

- 匯出時會根據目前點位與道路幾何重新建立 GPX
- 直線區段保留原本節點
- 貼道路線區段會依固定步距補中間點，讓 Fog of World 匯入時更接近實際移動路線
- 如果原始資料有時間資訊，匯出時會沿著整條路徑重新分配時間

## 檔案結構

- `scripts/gpx_editor.html`：頁面入口
- `scripts/gpx_editor/gpx_editor_core.mjs`：距離計算、時間格式化、匯出路徑計算

## 限制

- 貼道路線仰賴外部 OSRM 服務，離線時無法使用
- 非道路區段仍會以直線連接
- 大型 GPX 匯入後，編輯器可能會先自動抽樣，避免瀏覽器一次載入過多點位
