"""Create a UTF-8 HTML report, printable PDF and handoff documents from actual results."""
from pathlib import Path
import json, html, shutil, os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak

ROOT=Path(__file__).resolve().parents[1]

def main():
    d=json.loads((ROOT/'reports/results.json').read_text(encoding='utf8'))
    notebook=json.loads((ROOT/'reports/notebooklm_summary.json').read_text(encoding='utf8'))
    font=Path(os.environ.get('HW2_CJK_FONT','C:/Windows/Fonts/msjh.ttc'))
    if not font.exists():
        raise RuntimeError('Set HW2_CJK_FONT to a Traditional Chinese TrueType font (.ttf/.ttc) to generate the PDF.')
    pdfmetrics.registerFont(TTFont('MSung-Light',str(font),subfontIndex=0))
    normal=ParagraphStyle('body',fontName='MSung-Light',fontSize=10,leading=17,wordWrap='CJK',spaceAfter=9)
    heading=ParagraphStyle('heading',parent=normal,fontSize=16,leading=23,textColor=colors.HexColor('#177f74'),spaceBefore=16)
    small=ParagraphStyle('small',parent=normal,fontSize=8,leading=12)
    story=[]; web=[]
    def para(text,title=False):
        story.append(Paragraph(html.escape(text),heading if title else normal))
        web.append(f'<h2>{html.escape(text)}</h2>' if title else f'<p>{html.escape(text)}</p>')
    def figure(name,caption):
        from PIL import Image as PILImage
        path=ROOT/f'site/assets/{name}.png'; w,h=PILImage.open(path).size
        story.append(Image(str(path),width=470,height=470*h/w));para(caption)
        web.append(f'<img src="../site/assets/{name}.png" alt="{html.escape(caption)}">')
    def table(rows,widths):
        items=[[Paragraph(html.escape(str(c)),small) for c in row] for row in rows]
        t=Table(items,colWidths=widths,repeatRows=1,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e5eee6')),('VALIGN',(0,0),(-1,-1),'TOP'),('GRID',(0,0),(-1,-1),.3,colors.HexColor('#ccd7ce')),('BOTTOMPADDING',(0,0),(-1,-1),7)]));story.append(t);story.append(Spacer(1,12))
        web.append('<table>'+''.join('<tr>'+''.join(f'<td>{html.escape(str(c))}</td>' for c in row)+'</tr>' for row in rows)+'</table>')
    def num(x): return f'{x:.6g}'
    para('HW2 多元線性迴歸：洪水機率資料的確定性規則與特徵選擇',True)
    para('學號：7114056126｜GitHub：benson103081｜分析日期：2026-10-18')
    para('版本狀態：分析、程式、圖表、網站及使用者提供的 NotebookLM 研究摘要已整合；完整 GPT 對話 PDF 尚待補上。此報告不是已齊備所有必交附件的最終版本。')
    para('摘要',True)
    para('本研究使用 Kaggle Flood Prediction Dataset 版本 1 的 50,000 筆資料與 20 個數值特徵，依 CRISP-DM 建立可重現的多元線性迴歸流程。資料以固定亂數種子切為 40,000 筆訓練與 10,000 筆測試，前處理和特徵選擇均在交叉驗證訓練折內完成。完整 OLS 的測試 R² 為 1；事後以十進位精確運算核對發現，全部目標都等於 20 個輸入分數加總除以 200。研究價值在於揭露資料的確定性規則、解釋刪除特徵的誤差，以及避免將完美擬合誤認為真實災害預測能力。')
    para('1. Business Understanding｜商業理解',True)
    para('情境：若取得環境與社會因素評分，能否預測 FloodProbability？能否用較少欄位維持表現？主要比較標準為訓練集五折 CV RMSE，測試集用於最終評估。將預測訓練平均值設為最低基準，並比較解釋性較高的線性模型與非線性樹模型。資料沒有真實時空識別、感測器量測或事件標籤證據，因此成果定位為分析教學，不作預警、保險定價或因果政策建議。')
    para('2. Data Understanding｜資料理解',True)
    para('來源：Naiya Khalid，Flood Prediction Dataset，https://www.kaggle.com/datasets/naiyakhalid/flood-prediction-dataset 。下載固定 datasetVersionNumber=1 的 flood.csv；查詢當日公開中繼資料為版本 2，但本研究固定使用版本 1，避免無聲改變資料。公開 listing 標示 CC0: Public Domain，並保留 source.json 作來源紀錄。資料不是後來百萬筆的 Playground 競賽衍生資料。')
    para('SHA-256：'+d['source']['sha256'])
    para(f"實際檢查：{d['initial_rows']:,} 筆、21 欄（20 個輸入 + 1 個目標）；缺值合計 {sum(d['missing'].values())}，完全重複列 {d['duplicates_removed']}。全部欄位為數值型；目標介於 0 與 1。除原始檔品質檢查外，特徵分布與相關性僅由訓練資料計算。")
    labels=['季風強度','地形排水','河川管理','森林砍伐','都市化','氣候變遷','水壩品質','淤積','農業活動','土地侵占','災害準備不足','排水系統','海岸脆弱度','山崩','集水區','基礎設施劣化','人口分數','濕地流失','規劃不足','政治因素']
    table([['欄位（原始名稱）','中文輔助標籤','訓練最小–最大','訓練平均']]+[[f,labels[i],f"{d['feature_summary'][f]['min']:g}–{d['feature_summary'][f]['max']:g}",f"{d['feature_summary'][f]['mean']:.3f}"] for i,f in enumerate(d['features'])],[190,100,90,90])
    para('中文名稱是欄位翻譯，不補造來源未提供的單位或分數方向。例如 DamsQuality 的正係數不能解讀為「水壩品質越好越會淹水」。')
    para('3. Data Preparation｜資料準備',True)
    para(f"先移除完全重複列與缺少目標列，再使用 train_test_split(test_size=0.2, random_state={d['seed']})。訓練資料內以 KFold(5, shuffle=True, random_state={d['seed']}) 建立共用折。每折的 SimpleImputer(median)、StandardScaler、特徵選擇與模型都置於 Pipeline；不以驗證或測試資料擬合。資料沒有類別欄，因此不需要 one-hot encoding。未刪除極端值，以免任意改變分布。原始 CSV 列號及每折驗證位置保存在 reports/splits.json。")
    para('4. Modeling｜建模與特徵選擇',True)
    para('完整 OLS 含截距，最小化殘差平方和。Ridge 使用 L2 懲罰，alpha = 0.01、1、100、1000；Lasso 使用 L1 懲罰，alpha = 10^-6、10^-5、10^-4、10^-3、10^-2，max_iter=20000、tol=10^-9。StandardScaler 只標準化 X，未標準化 y；兩種模型的 alpha 定義不同，不直接比較其數字大小。')
    para('SelectKBest 用訓練折內的單變量 f_regression 分數選欄；RFE 以標準化後的線性係數遞迴剔除，每次移除 1 欄。兩者均測試 k=5、10、14、16、18、20，之後擬合 OLS。額外的 Histogram Gradient Boosting 設 max_iter=200、max_leaf_nodes=15 或 31、early_stopping=True，只在訓練折內早停。七個方法共用相同五折；GridSearchCV 依平均 CV RMSE 選參數。')
    para('預測模型在讀取測試成績前依 CV 鎖定。完整 OLS 與選滿 20 欄的選擇器本質上是同一模型；近乎零的誤差差異只反映浮點運算，不宣稱存在實質優劣。CV 參與調參，最佳 CV 分數仍有選擇偏差；測試資料才是留出評估。')
    table([['方法','最佳參數','CV RMSE','測試 RMSE','測試 R²']]+[[r['name'],str(r['params']),num(r['cv_rmse']),num(r['test']['rmse']),num(r['test']['r2'])] for r in d['models']],[100,130,80,80,80])
    table([['方法','測試 MAE','測試 MSE','訓練 Adjusted R²']]+[[r['name'],num(r['test']['mae']),num(r['test']['mse']),num(r['adjusted_train_r2']) if r.get('adjusted_train_r2') is not None else '不適用'] for r in d['models']],[140,110,110,110])
    para('RMSE=sqrt(mean((y−ŷ)^2))，MAE=mean(|y−ŷ|)，MSE=mean((y−ŷ)^2)，R²=1−SSE/SST。Adjusted R²=1−(1−R²)(n−1)/(n−p−1)，只呈現非正則化 OLS 的訓練描述值；特徵選擇後的此數字不作未經調整的統計推論。')
    figure('selection','圖 1：特徵選擇曲線，誤差棒為五折分數標準差；並非信賴區間。')
    table([['選擇方法','保留 14 欄的 CV RMSE','保留 20 欄的 CV RMSE']]+[[name,num(next(r['rmse'] for r in d['cv_candidates'] if r['name']==name and list(r['params'].values())==[14])),num(next(r['rmse'] for r in d['cv_candidates'] if r['name']==name and list(r['params'].values())==[20]))] for name in ['SelectKBest + OLS','RFE + OLS']],[190,140,140])
    para('5. Evaluation｜評估與結果解釋',True)
    para('重要發現：訓練完成後，使用 Python Decimal 以 CSV 原始十進位字串逐筆核對：FloodProbability = (MonsoonIntensity + … + PoliticalFactors) / 200。50,000 / 50,000 筆完全相等，最大十進位誤差為 0。此稽核沒有用來訓練或調參，只用於解釋異常高分。這支持「所提供資料存在確定性目標公式」，但不能單憑公式斷言作者如何收集或生成資料。')
    para('因此每個輸入分數的原始尺度 OLS 係數約為 0.005，截距約為 0。完整模型重建公式，R²=1 與近零 RMSE 是合理數值結果；刪掉任何有變動的因素就失去公式資訊，故兩種選擇器都選滿 20 欄。沒有為了展示「特徵選擇成功」而強制保留較少欄位。')
    figure('comparison','圖 2：獨立測試集誤差；樹模型沒有優於本資料的確定性線性公式。')
    figure('predictions','圖 3：實際值／預測值及殘差；殘差尺度接近機器精度，不代表測量誤差如此小。')
    para('五項假設診斷',True)
    para(f"線性：逐筆精確公式及圖形支持本表內的線性關係。共線性：完整 OLS 最大 VIF = {d['diagnostics']['max_vif']:.6f}，沒有顯著共線性跡象。獨立性：缺乏時間、地點或群組資訊，無法確認，不能用打亂順序後的 Durbin–Watson 宣稱通過。")
    para('等變異與殘差常態：完整模型殘差只剩浮點運算誤差；RESET、Breusch–Pagan、Jarque–Bera 與 Durbin–Watson 的數值無法作為有意義的統計證據，結果欄設為不適用。原始計算值只保存在 numerical_only_do_not_interpret 供稽核。一般 OLS 預測區間會退化為近乎零寬，故網站與報告不提供誤導性的 95% 區間；題目要求的預測圖已完整提供。')
    figure('diagnostics','圖 4：Q-Q 與殘差分布只展示浮點誤差形狀，不進行常態推論。')
    para('網路主流或更優方法的比較',True)
    para('依 scikit-learn 官方線性模型與特徵選擇說明，Ridge、Lasso、單變量篩選及 RFE 是本研究比較的方法；Lasso 可產生稀疏係數，Ridge 通常不會精確歸零。另依官方 ensemble 文件，直方圖梯度提升可擬合表格資料的非線性。本研究已在相同切分實跑該方法，其測試 RMSE 約 0.00877、R² 約 0.969，未超越完整 OLS。這只適用本次參數網格及資料，不代表線性模型普遍優於 boosting。未引用他人的 Kaggle 排名或把不同資料上的成績當作公平比較。')
    para('可行的下一步是取得有地點、時間與真實觀測定義的獨立資料，再評估時間／區域外推與機率校準；若確有非線性，可擴大樹模型調參範圍或比較其他方法。對現有確定性資料，追求更複雜模型不能改善實際科學效度。沒有參加 Kaggle 競賽，因此沒有名次；不提供虛構排名。')
    para('6. Deployment｜部署與重現',True)
    para('主程式：7114056126_hw2.py。安裝 requirements.txt 後執行主程式，產生模型比較、切分列號、測試預測及圖表，再執行 python scripts/build_report.py 建立報告。網站使用 JSON 中的原始尺度係數，計算 ŷ = intercept + Σ coefficient_i × input_i；20 個輸入支援滑桿與數字、模型切換、重設與示範情境。超出訓練範圍時提醒外推，空白或非法輸入不計算。')
    para('數值驗證：以 statsmodels 獨立 OLS 對照 scikit-learn 預測；所有匯出的線性係數以原始測試列重算，要求絕對誤差小於 10^-12。另以 Decimal 核對確定性公式。網站瀏覽器測試和最終部署狀態請見 reports/browser-verification.json 與 README；未完成的連線或人工附件會另列，不把預計網址視為已成功部署。')
    para('7. GPT 輔助內容',True)
    para('本作業由使用者提出需求並提供學號與繳交規格，GPT/Codex 協助閱讀題目、查詢來源、撰寫程式、設計分析流程、製作網站、查核數值及整理報告。全部模型分數由實際下載資料執行產生，未將範例成績抄入報告。使用者需審閱結論並理解程式；AI 協助不取代資料來源可信度或個人責任。')
    para('待附：完整 GPT 對話 PDF。必須由使用者從聊天介面匯出此次作業的所有對話；不能以本節摘要冒充完整對話紀錄。')
    para('8. NotebookLM 研究摘要',True)
    para(notebook['provenance'])
    para('NotebookLM 摘要（依使用者提供內容校訂，超過 100 字）：')
    para(notebook['summary'])
    para('內容校訂與證據界線',True)
    for correction in notebook['corrections']: para(correction)
    para('9. 參考來源',True)
    sources=[('Kaggle 資料來源','https://www.kaggle.com/datasets/naiyakhalid/flood-prediction-dataset'),('scikit-learn：Linear Models','https://scikit-learn.org/stable/modules/linear_model.html'),('scikit-learn：Feature selection','https://scikit-learn.org/stable/modules/feature_selection.html'),('scikit-learn：Common pitfalls / leakage','https://scikit-learn.org/stable/common_pitfalls.html'),('scikit-learn：Histogram-based gradient boosting','https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting'),('statsmodels：Regression diagnostics','https://www.statsmodels.org/stable/diagnostic.html')]
    for title,url in sources:para(title+'：'+url)
    para('來源查閱日期：2026-10-18。方法介紹採官方文件；資料生成規則為本次實測發現，未宣稱由 Kaggle 作者確認。')
    out=ROOT/'reports/7114056126_hw2_report.pdf'
    def footer(canvas,doc):
        canvas.setFont('MSung-Light',8);canvas.drawString(48,27,'7114056126 | HW2 | 完整 GPT 對話附件待補');canvas.drawRightString(545,27,str(doc.page))
    SimpleDocTemplate(str(out),pagesize=(595,842),rightMargin=48,leftMargin=48,topMargin=40,bottomMargin=48).build(story,onFirstPage=footer,onLaterPages=footer)
    (ROOT/'reports/report.html').write_text('<!doctype html><html lang="zh-Hant"><meta charset="utf-8"><title>HW2 分析報告</title><style>body{font:16px/1.8 sans-serif;max-width:1000px;margin:40px auto;padding:24px;color:#173f36}h2{margin-top:35px}img{max-width:100%}table{border-collapse:collapse;width:100%}td{border:1px solid #ccd7ce;padding:8px;font-size:13px}p{overflow-wrap:anywhere}@media print{body{margin:0;font-size:11pt}h2{break-after:avoid}img,table{break-inside:avoid}}</style>'+''.join(web)+'</html>',encoding='utf8')
    shutil.copy2(out,ROOT/'site/downloads'/out.name)
    shutil.copy2(ROOT/'7114056126_hw2.py',ROOT/'site/downloads/7114056126_hw2.py')
    shutil.copy2(ROOT/'reports/test_predictions.csv',ROOT/'site/downloads/test_predictions.csv')
    # Keep the site wording consistent with the observed deterministic target.
    p=ROOT/'site/index.html';s=p.read_text(encoding='utf8')
    s=s.replace('報告已標示尚待補上的 NotebookLM 研究與完整 GPT 對話附件。','NotebookLM 研究摘要已整合；完整 GPT 對話 PDF 附件仍待補。')
    for a,b in [('完整 OLS 的 95% 預測區間','預測不確定性'),('僅在選擇 OLS 時顯示。這是新觀測值的區間，依賴線性、常態與等變異等假設；並非實際災害機率的校準保證。','全部目標符合輸入分數總和除以 200。殘差僅為浮點誤差，無法合理估計真實預測區間，因此不顯示虛假的精密區間。'),('以及 OLS 預測區間覆蓋率','；殘差退化時停用推論與區間'),('測試集預測與區間 CSV','測試集預測 CSV'),('大樣本中的小偏離可能達統計顯著；p 值不能單獨證明模型可用。','本資料殘差退化，故不解讀 RESET、常態與等變異檢定 p 值。')]: s=s.replace(a,b)
    p.write_text(s,encoding='utf8')
    p=ROOT/'site/app.js';s=p.read_text(encoding='utf8').replace("'請切換至 OLS'","'殘差退化，不提供區間'").replace("'?????????'","'不適用（殘差退化）'").replace('特徵選擇實驗顯示，保留完整 20 欄的誤差最低；精簡欄位在這份資料中犧牲了預測資訊。','全部 50,000 筆目標皆等於 20 個輸入分數總和 ÷ 200，因此 R² = 1 反映確定性公式，並非真實洪水預測能力。精簡特徵會丟失公式所需資訊。')
    p.write_text(s,encoding='utf8')
    print('Report written:',out.name)

if __name__=='__main__':main()
