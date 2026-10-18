"""Download a pinned public Kaggle dataset; do not extract arbitrary archive paths."""
from pathlib import Path
import hashlib, io, json, urllib.request, zipfile

ROOT = Path(__file__).resolve().parents[1]
REF = 'naiyakhalid/flood-prediction-dataset'
URL = f'https://www.kaggle.com/api/v1/datasets/download/{REF}?datasetVersionNumber=1'

def main():
    target = ROOT / 'data'
    target.mkdir(exist_ok=True)
    with urllib.request.urlopen(URL, timeout=180) as response:
        raw = response.read()
    archive = zipfile.ZipFile(io.BytesIO(raw))
    members = [x for x in archive.namelist() if x.lower().endswith('.csv')]
    print('CSV members:', members)
    if len(members) != 1:
        raise ValueError('Expected exactly one CSV; inspect dataset before proceeding')
    content = archive.read(members[0])
    (target / 'flood.csv').write_bytes(content)
    with urllib.request.urlopen('https://www.kaggle.com/api/v1/datasets/list?search=flood-prediction-dataset', timeout=60) as response:
        listing = json.load(response)
    metadata = next(x for x in listing if x['ref'] == REF)
    (target / 'source.json').write_text(json.dumps({'ref':REF,'url':f'https://www.kaggle.com/datasets/{REF}', 'download_url':URL,'version':1,'retrieved':'2026-10-18','archive_member':members[0],'sha256':hashlib.sha256(content).hexdigest(),'license':metadata.get('licenseName'),'metadata':metadata}, ensure_ascii=False, indent=2), encoding='utf-8')
    print('Downloaded bytes:',len(content),'sha256:',hashlib.sha256(content).hexdigest())

if __name__ == '__main__':
    main()
