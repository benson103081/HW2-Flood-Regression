"""Publish this dedicated homework repo. Credentials stay in process memory only."""
from pathlib import Path
import os,subprocess,json,urllib.request,urllib.error,sys
ROOT=Path(__file__).resolve().parents[1]
OWNER='benson103081'; REPO='HW2-Flood-Regression'
def run(*args):return subprocess.run(args,cwd=ROOT,check=True,capture_output=True,text=True,encoding='utf8')
env=os.environ.copy();env['GIT_TERMINAL_PROMPT']='0';env['GCM_INTERACTIVE']='never'
proc=subprocess.run(['git','credential','fill'],input='protocol=https\nhost=github.com\nusername='+OWNER+'\n\n',capture_output=True,text=True,env=env)
if proc.returncode:raise SystemExit('No noninteractive GitHub credential available; user login required.')
cred=dict(line.split('=',1) for line in proc.stdout.splitlines() if '=' in line)
token=cred.get('password')
if not token:raise SystemExit('No GitHub credential returned.')
def api(path,method='GET',payload=None):
    req=urllib.request.Request('https://api.github.com'+path,data=json.dumps(payload).encode() if payload is not None else None,method=method,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'HW2-publication','Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(req,timeout=45) as r:return json.load(r) if r.status!=204 else {}
    except urllib.error.HTTPError as e:
        # Never print request headers or credentials.
        body=e.read().decode();raise RuntimeError(f'GitHub API {method} {path}: HTTP {e.code}: {body[:600]}') from None
user=api('/user')
assert user['login']==OWNER,'Authenticated account differs from homework owner'
print('Authenticated account:',user['login'])
mode=sys.argv[1] if len(sys.argv)>1 else 'probe'
if mode=='probe':sys.exit(0)
if mode=='publish':
    try:existing=api(f'/repos/{OWNER}/{REPO}')
    except RuntimeError as e:
        if 'HTTP 404' not in str(e):raise
        existing=api('/user/repos','POST',{'name':REPO,'description':'7114056126 HW2: reproducible flood regression, feature selection and CRISP-DM','private':False,'auto_init':False})
        print('Created public repository:',existing['html_url'])
    assert existing['owner']['login']==OWNER and not existing['private']
    # Existing nonempty repositories must have the expected local origin; never overwrite.
    if not (ROOT/'.git').exists():
        if existing['size']!=0:raise SystemExit('Existing nonempty repo; refusing automatic initialization.')
        run('git','init','-b','main');run('git','remote','add','origin',f'https://github.com/{OWNER}/{REPO}.git')
    assert run('git','remote','get-url','origin').stdout.strip()==f'https://github.com/{OWNER}/{REPO}.git'
    run('git','add','.gitignore','7114056126_hw2.py','README.md','requirements.txt','requirements-dev.txt','data','reports','scripts','site','.github','需要你完成的事項.txt')
    status=run('git','status','--porcelain').stdout
    if status.strip():run('git','commit','-m','Complete reproducible HW2 analysis, report and interactive site')
    result=run('git','push','-u','origin','main');print('Pushed main successfully')
    try:pages=api(f'/repos/{OWNER}/{REPO}/pages')
    except RuntimeError as e:
        if 'HTTP 404' not in str(e):raise
        pages=api(f'/repos/{OWNER}/{REPO}/pages','POST',{'build_type':'workflow','source':{'branch':'main','path':'/'}})
    print('Pages:',pages.get('html_url'),'status:',pages.get('status'))
elif mode=='status':
    data=api(f'/repos/{OWNER}/{REPO}/actions/runs?per_page=3')
    for r in data['workflow_runs']:print(json.dumps({k:r.get(k) for k in ['id','status','conclusion','html_url','head_sha']}))
    print('Pages metadata:',json.dumps({k:v for k,v in api(f'/repos/{OWNER}/{REPO}/pages').items() if k in ['html_url','status','build_type']}))
