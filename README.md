# HW2｜洪水機率多元線性迴歸

學號 **7114056126** · GitHub **benson103081**

以 Kaggle 的 20 個數值特徵，完成 CRISP-DM、多元線性迴歸、特徵選擇、模型比較、殘差診斷及互動網站。

**核心發現：資料中全部 50,000 筆 `FloodProbability` 都精確等於 20 個輸入分數總和除以 200。** 完整 OLS 的 R²=1 是重建此公式，不代表真實洪水預測能力。資料原始蒐集與生成過程未獲獨立驗證，不把欄位名稱當作因果或實際量測定義。

## 繳交狀態

- 分析、Python 主程式、PDF 報告、互動網站與數值／瀏覽器驗證：完成。
- NotebookLM：使用者已貼回研究內容，已核對數值並整合超過 100 字的摘要；來源與校訂紀錄見 `reports/notebooklm_summary.json`。
- GPT 對話：已取得使用者原始匯出並轉為 72 頁 PDF，附於本機繳交 ZIP 的 `attachments/`，不公開對話內容。
- 正式要求是一個以學號命名的 ZIP，GitHub／網站網址為補充，不能取代必要附件。
- Repo：<https://github.com/benson103081/HW2-Flood-Regression>
- 已部署網站：<https://benson103081.github.io/HW2-Flood-Regression/>

請看 [需要你完成的事項.txt](需要你完成的事項.txt)。本機 `submission/7114056126_hw2.zip` 已包含必要文件與對話附件，可於使用者最終審閱後繳交。

## 快速重現

Python 3.12。在本資料夾 PowerShell 執行：

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe 7114056126_hw2.py
.\.venv\Scripts\python.exe scripts/verify.py
.\.venv\Scripts\python.exe scripts/build_report.py
.\.venv\Scripts\python.exe -m http.server 8000 --directory site
```

開啟 <http://localhost:8000>。不要直接以 file:// 開啟，網站需要 fetch JSON。單次分析會執行五折網格搜尋，時間依電腦而異；所有結果來自實際計算。原始資料已隨 repo 提供，重跑不需要 Kaggle 金鑰。

PDF 產生器在 Windows 使用系統 Microsoft JhengHei 並嵌入字型。其他系統請以 `HW2_CJK_FONT` 環境變數指定支援繁體中文的 TrueType `.ttf`／`.ttc`；分析與現有 PDF 閱讀不需要此設定。

若需重新取得原始資料，執行 `python scripts/download_data.py`。該程式固定下載版本 1，只接受單一 CSV，並產生 SHA-256 與來源中繼資料。

瀏覽器驗證需要已安裝 Chrome：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe scripts/browser_test.py
```

測試自行啟動並關閉本機 HTTP server；不修改 Chrome 個人資料。報告與網站不依賴外部字型、CDN 或後端服務。

## 資料與研究流程

來源：[Naiya Khalid / Flood Prediction Dataset](https://www.kaggle.com/datasets/naiyakhalid/flood-prediction-dataset)。下載版本 1，50,000 列、20 個輸入、目標 `FloodProbability`。2026-10-18 查詢的公開 listing 標示 CC0；listing 已更新至版本 2，但本研究刻意保留固定版本 1。來源紀錄在 `data/source.json`。不是百萬列 Playground 競賽衍生資料。

資料檢查結果：零缺值、零完全重複列、全數數值型。程式仍提供中位數補值管線，以明確保留正確的訓練／測試邊界。沒有以測試資料的相關性選欄。

1. 定義連續目標與問題：預測分數、評估精簡欄位的代價。
2. 檢查來源、欄位型態、缺值與重複列；分布與相關性由訓練集計算。
3. seed `711405612`，80/20 隨機切分；40,000 筆訓練、10,000 筆測試。切分列號保存於 `reports/splits.json`。
4. 5 折 CV，補值／標準化／特徵選擇／模型皆在每一折重新擬合。
5. 依 CV RMSE 選參數並先鎖定推薦，再計算測試分數。沒有依測試成績回頭調模型。
6. 將線性模型係數還原原始尺度，匯出 JSON，網站即時計算預測。

## 方法與實測結果

| 方法 | 參數搜尋 | 測試 RMSE | 測試 R² |
|---|---|---:|---:|
| 訓練平均值基準 | 無 | 0.0498141 | -0.0001015 |
| 完整 OLS | 全部 20 欄、含截距 | 1.80e-16 | 1.000000 |
| Ridge | alpha=0.01, 1, 100, 1000 | 1.24e-8 | 約 1 |
| Lasso | alpha=1e-6, 1e-5, 1e-4, 1e-3, 1e-2 | 4.44e-6 | 約 1 |
| SelectKBest + OLS | k=5,10,14,16,18,20；選中20 | 1.80e-16 | 1.000000 |
| RFE + OLS | k=5,10,14,16,18,20；選中20 | 1.80e-16 | 1.000000 |
| Histogram boosting | max_leaf_nodes=15,31；max_iter=200 | 0.0087712 | 0.968993 |

完整 MAE、MSE、RMSE、R²、CV 各折分數、標準差、係數與原始尺度參數：`reports/results.json`。非正則化 OLS 額外提供訓練 Adjusted R²；選後值僅作描述，不作未調整推論。

兩種選擇器皆選滿 20 欄：確定性目標需要全部欄位資訊。網站與報告附完整 k 曲線，沒有將「必須選出更少欄」當作預設結論。Ridge 與 Lasso 的 alpha 定義不同；因目標尺度小，Lasso 使用較小 alpha。未標準化 y。

## 模型診斷與限制

主程式先依一般迴歸流程訓練，再用 `Decimal` 逐筆檢查原始字串，確認全部 50,000 筆精確滿足 `sum(features)/200`，最大誤差為 0。此事後稽核用於解釋高分，不參與模型選擇。

- 線性：本表內存在確定性線性公式。
- 共線性：完整模型最大 VIF 約 1.00077，無顯著共線性跡象。
- 常態／等變異：殘差只剩浮點誤差，相關 p 值不具合理推論意義。
- 獨立性：缺少時間、地點與群組資訊，不能確認；不以打亂後的 Durbin–Watson 宣稱通過。
- 不確定性：一般 OLS 預測區間會退化成零寬附近，因此停用。題目要求的預測圖、殘差圖及 Q-Q 圖已提供。
- 泛化：不能把資料內的高分推廣為真實洪水機率、感測器預測或政策因果效果。
- 競賽：使用公開 dataset，未參賽，沒有 Kaggle 排名。

`numerical_only_do_not_interpret` 僅保存失去意義的浮點診斷原值供稽核，網站不解讀它們。沒有添加隨機噪音讓結果看起來更真實，也沒有換 seed 挑選較漂亮的測試分數。

## 驗證

`scripts/verify.py` 檢查資料雜湊、切分不重疊且完整、五折覆蓋、目標未混入特徵、五個線性模型匯出係數的獨立預測、RMSE/MAE 重算、退化推論停用、50,000 筆精確十進位公式。主程式另用 statsmodels OLS 對照 sklearn 預測。

`scripts/browser_test.py` 已在 Chrome 通過：20 個欄位、預測對照獨立公式、空白檢查、外推提示、重設、模型切換、情境按鈕、下載連結、PDF 檔頭、390px／320px 無頁面水平溢位，且無 JavaScript 例外。詳見 `reports/verification.json`、`reports/browser-verification.json`。

GitHub Actions 執行數值／產物驗證後部署 `site/`。CI 不重新訓練或宣稱重跑本機瀏覽器；修改模型後需先重跑主程式與本機驗證並提交更新的產物。

## 檔案

```text
7114056126_hw2.py           主要 Python 程式
data/flood.csv             Kaggle 固定版本原始快照
data/source.json           來源、授權查詢與雜湊
reports/results.json       所有模型與交叉驗證結果
reports/splits.json        切分列號與每折驗證位置
reports/test_predictions.csv
reports/7114056126_hw2_report.pdf
reports/report.html        可閱讀／列印報告
site/                      GitHub Pages 靜態網站
scripts/                   下載、驗證、報告、打包與部署
需要你完成的事項.txt        NotebookLM 提問及附件操作步驟
submission/                本機 ZIP，不提交 repo
```

## AI 輔助與對話附件

GPT/Codex 協助需求理解、資料查詢、程式、分析流程、驗證、網站與文件。數值由真實執行產生。完整對話需由使用者從聊天介面匯出，不能以摘要替代。NotebookLM 摘要取自使用者在本次對話提供的研究內容，經實測數值校訂後納入報告；未直接連線 NotebookLM，亦未取得其筆記本網址或原始引用編號，不宣稱獨立驗證操作紀錄。

使用者實際匯出的 Markdown 與轉換後的 GPT 對話 PDF 已放在本機 `attachments/`；此目錄不提交 GitHub，只加入繳交 ZIP。紀錄涵蓋最初作業需求至匯出操作說明，不包含之後的附件轉檔與打包對話。原匯出中的工具輸出截斷或未內嵌圖片保留原樣，不補造內容。`transcript-verification.json` 保存原檔及 PDF 雜湊、頁數與驗證紀錄。公開 repo 不含私人對話附件，其他人僅 clone repo 不能產生具備私人附件的最終 ZIP；分析程式與網站仍可獨立重現。

## 方法來源

- [scikit-learn 線性模型](https://scikit-learn.org/stable/modules/linear_model.html)
- [特徵選擇](https://scikit-learn.org/stable/modules/feature_selection.html)
- [資料洩漏與 Pipeline](https://scikit-learn.org/stable/common_pitfalls.html)
- [Histogram gradient boosting](https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting)
- [statsmodels 迴歸診斷](https://www.statsmodels.org/stable/diagnostic.html)

## 部署紀錄

2026-10-18：GitHub Pages 已公開可用。[部署 run 39096069306](https://github.com/benson103081/HW2-Flood-Regression/actions/runs/39096069306) 已通過數值驗證並發布。早期兩次建置因 Git 自動轉換 CSV 換行造成來源雜湊不一致而停止；已用 `.gitattributes` 保留原始資料位元組，沒有放寬驗證門檻。

首次公開網站、結果 JSON、PDF 皆實際讀取 HTTP 200，並確認當時 JSON／PDF 與本機檔案雜湊一致。已在公開網站以 Chrome 實測：預設 50.00%，將季風強度由 5 改為 7 後顯示 51.00%，無 JavaScript 例外。驗證紀錄在 `reports/public-verification.json`。PDF 內嵌繁體中文字型，已檢視渲染及可搜尋文字。

本次更新已整合 NotebookLM 摘要、取得對話匯出附件並重新產生正式報告及本機 ZIP。ZIP 的 `SUBMISSION_STATUS.json` 為 `READY_FOR_SUBMISSION`，必要附件無待補項目；最後由使用者審閱並上傳課程平台。
