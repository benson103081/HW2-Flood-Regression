from pathlib import Path
import functools,http.server,json,threading
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args):pass
server=http.server.ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(ROOT/'site')))
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
base=f'http://127.0.0.1:{server.server_port}'
checks=[];errors=[]
try:
    with sync_playwright() as p:
        browser=p.chromium.launch(channel='chrome',headless=True)
        page=browser.new_page(viewport={'width':1440,'height':1050},device_scale_factor=1)
        page.on('pageerror',lambda e:errors.append(str(e)))
        response=page.goto(base);assert response.status==200
        page.wait_for_function("document.getElementById('prediction-value').textContent.includes('%')")
        assert page.locator('#inputs input[type=number]').count()==20
        assert '50,000' in page.locator('#finding').inner_text()
        assert '退化' in page.locator('#prediction-interval').inner_text()
        checks.append('initial load, 20 inputs, deterministic-target explanation, no misleading interval')
        initial=page.locator('#prediction-value').inner_text()
        page.locator('#n0').fill('6');page.locator('#n0').dispatch_event('input')
        values=page.locator('#inputs input[type=number]').evaluate_all('(els)=>els.map(e=>Number(e.value))')
        assert abs(float(page.locator('#prediction-value').inner_text().strip('%'))-sum(values)/2)<.006
        page.locator('#n0').fill('');page.locator('#n0').dispatch_event('input');assert page.locator('#prediction-value').inner_text()=='—'
        page.locator('#n0').fill('999');page.locator('#n0').dispatch_event('input');assert '外推' in page.locator('#prediction-message').inner_text()
        page.locator('#reset').click();assert page.locator('#prediction-value').inner_text()==initial
        checks.append('prediction matches independent sum/200, blank validation, extrapolation, reset')
        for name in ['Ridge','Lasso','SelectKBest + OLS','RFE + OLS','OLS']:
            page.locator('#model-select').select_option(name)
            assert '%' in page.locator('#prediction-value').inner_text()
        page.locator('[data-preset=high]').click();hi=page.locator('#prediction-value').inner_text()
        page.locator('[data-preset=low]').click();lo=page.locator('#prediction-value').inner_text()
        assert float(hi.strip('%'))>float(lo.strip('%'))
        page.locator('#reset').click();checks.append('all exported models and presets')
        for href in page.locator('#downloads a').evaluate_all('(els)=>els.map(e=>e.getAttribute("href"))'):
            if not href.startswith('http'):assert page.request.get(base+'/'+href).status==200,href
        assert page.request.get(base+'/downloads/7114056126_hw2_report.pdf').body().startswith(b'%PDF')
        checks.append('local download links and PDF signature')
        page.screenshot(path=str(ROOT/'reports/browser-desktop.png'),full_page=True)
        for width in [390,320]:
            page.set_viewport_size({'width':width,'height':844})
            assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),width
            page.locator('#n0').fill('7');page.locator('#n0').dispatch_event('input')
            assert '%' in page.locator('#prediction-value').inner_text()
            page.screenshot(path=str(ROOT/f'reports/browser-mobile-{width}.png'),full_page=True)
        checks.append('390px and 320px layout without horizontal page overflow')
        assert not errors,errors
        browser.close()
    (ROOT/'reports/browser-verification.json').write_text(json.dumps({'passed':True,'checks':checks,'page_errors':errors},ensure_ascii=False,indent=2),encoding='utf8')
    print('PASS:',len(checks),'browser groups')
finally:
    server.shutdown();server.server_close()
