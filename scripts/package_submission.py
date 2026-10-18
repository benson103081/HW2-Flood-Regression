from pathlib import Path
import json,zipfile,hashlib
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'submission';out.mkdir(exist_ok=True)
paths=[ROOT/n for n in ['7114056126_hw2.py','README.md','requirements.txt','requirements-dev.txt','需要你完成的事項.txt','.gitattributes','.gitignore']]
for folder in ['data','reports','site','scripts','attachments','.github']:
    if (ROOT/folder).exists():
        paths.extend(p for p in (ROOT/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts and not p.name.endswith('.log'))
verification=json.loads((ROOT/'attachments/transcript-verification.json').read_text(encoding='utf8'))
assert verification['verified']
assert hashlib.sha256((ROOT/'attachments/7114056126_hw2_GPT對話.pdf').read_bytes()).hexdigest()==verification['pdf_sha256']
assert hashlib.sha256((ROOT/'attachments/7114056126_hw2_對話.md').read_bytes()).hexdigest()==verification['source_sha256']
manifest={'student_id':'7114056126','status':'READY_FOR_SUBMISSION','completed':['Python analysis and report','User-provided NotebookLM summary reviewed and integrated','Actual exported GPT transcript PDF and source Markdown','GitHub repository and website'],'pending':[],'transcript_scope':verification['scope'],'note':'Submit this ZIP after your final review. Conversation attachments are included locally only.'}
target=out/'7114056126_hw2.zip'
with zipfile.ZipFile(target,'w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(set(paths)):z.write(p,Path('7114056126_hw2')/p.relative_to(ROOT))
    z.writestr('7114056126_hw2/SUBMISSION_STATUS.json',json.dumps(manifest,ensure_ascii=False,indent=2))
with zipfile.ZipFile(target) as z:assert z.testzip() is None
print('ZIP files:',len(paths),'bytes:',target.stat().st_size,'status:',manifest['status'])
