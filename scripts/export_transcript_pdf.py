"""Convert the user's actual exported Markdown verbatim to a private PDF attachment."""
from pathlib import Path
import hashlib, html, json, re, shutil
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
ROOT=Path(__file__).resolve().parents[1]
source=ROOT.parent/'7114056126_hw2_對話.md'
raw=source.read_bytes();text=raw.decode('utf-8-sig')
assert text.startswith('# Codex conversation')
assert '請幫我完成hw2' in text and '如何匯出對話紀錄' in text
assert 'NotebookLM' in text and '/export 7114056126_hw2_對話.md' in text
out=ROOT/'attachments';out.mkdir(exist_ok=True)
shutil.copy2(source,out/source.name)
pdfmetrics.registerFont(TTFont('TranscriptCJK','C:/Windows/Fonts/msjh.ttc',subfontIndex=0))
body=ParagraphStyle('body',fontName='TranscriptCJK',fontSize=8.5,leading=12,wordWrap='CJK',splitLongWords=True,spaceAfter=2)
heading=ParagraphStyle('heading',parent=body,fontSize=12,leading=17,spaceBefore=10,spaceAfter=6)
story=[Paragraph('7114056126 HW2｜GPT 完整對話匯出附件',heading),Paragraph('以下依使用者匯出的 Markdown 原文逐行排版，保留對話與活動紀錄；原始 Markdown 另附。紀錄截至匯出操作前的最後回覆，不包含匯出後的附件轉檔與打包作業。匯出檔中工具輸出若已有截斷或圖片未內嵌，PDF 保留原匯出內容，不自行補寫。',body),Spacer(1,10)]
for line in text.splitlines():
    if not line.strip():story.append(Spacer(1,4));continue
    story.append(Paragraph(html.escape(line).replace('\t','    '),heading if re.match(r'^#{1,2} ',line) else body))
target=out/'7114056126_hw2_GPT對話.pdf'
def footer(canvas,doc):
    canvas.setFont('TranscriptCJK',8);canvas.drawString(36,22,'7114056126 | GPT 對話原文匯出');canvas.drawRightString(559,22,str(doc.page))
SimpleDocTemplate(str(target),pagesize=(595,842),leftMargin=36,rightMargin=36,topMargin=32,bottomMargin=36).build(story,onFirstPage=footer,onLaterPages=footer)
import pymupdf
doc=pymupdf.open(target)
assert len(doc)>1
rendered=''.join(p.get_text() for p in doc)
assert '請幫我完成hw2' in rendered and '如何匯出對話紀錄' in rendered
doc[0].get_pixmap().save(out/'transcript-first-page.png')
doc[-1].get_pixmap().save(out/'transcript-last-page.png')
result={'verified':True,'source_sha256':hashlib.sha256(raw).hexdigest(),'pdf_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'source_bytes':len(raw),'source_lines':len(text.splitlines()),'user_messages':len(re.findall(r'^## User$',text,re.M)),'assistant_messages':len(re.findall(r'^## Assistant$',text,re.M)),'pdf_pages':len(doc),'scope':'Actual user export through export instructions; original tool truncations retained; subsequent packaging conversation excluded.'}
(out/'transcript-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
