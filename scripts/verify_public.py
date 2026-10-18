"""Read-only validation of the deployed public site and exact report bytes."""
from pathlib import Path
import hashlib,json,urllib.request
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
URL='https://benson103081.github.io/HW2-Flood-Regression/'
checks=[]
for rel in ['','assets/results.json','downloads/7114056126_hw2_report.pdf']:
    with urllib.request.urlopen(URL+rel,timeout=45) as r:
        assert r.status==200
        content=r.read()
    if rel:
        assert hashlib.sha256(content).hexdigest()==hashlib.sha256((ROOT/'site'/rel).read_bytes()).hexdigest(),rel
    checks.append('HTTP 200 and current artifact: '+(rel or 'index'))
with sync_playwright() as p:
    browser=p.chromium.launch(channel='chrome',headless=True)
    page=browser.new_page(viewport={'width':1280,'height':900});errors=[]
    page.on('pageerror',lambda e:errors.append(str(e)))
    page.goto(URL,wait_until='networkidle');page.wait_for_function("document.getElementById('prediction-value').textContent.includes('%')")
    assert page.locator('#prediction-value').inner_text()=='50.00%'
    page.locator('#n0').fill('7');page.locator('#n0').dispatch_event('input')
    assert page.locator('#prediction-value').inner_text()=='51.00%'
    assert not errors
    page.screenshot(path=str(ROOT/'reports/browser-public.png'),full_page=True)
    browser.close()
checks.append('public Chrome prediction 50.00% -> 51.00%, no JS exceptions')
result={'url':URL,'verified':True,'checks':checks}
(ROOT/'reports/public-verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(result,indent=2))
