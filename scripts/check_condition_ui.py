"""Browser check against the running synthetic preview on port 8517."""
from pathlib import Path
import json
import atexit
import subprocess
import sys
import time
from urllib.request import urlopen
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
server = subprocess.Popen(
    [sys.executable, '-m', 'streamlit', 'run', 'scripts/preview_condition_ui.py',
     '--global.developmentMode=false', '--server.port=8517', '--server.address=127.0.0.1',
     '--server.headless=true', '--browser.gatherUsageStats=false'],
    cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
)
atexit.register(server.terminate)
for attempt in range(30):
    try:
        with urlopen('http://127.0.0.1:8517/_stcore/health', timeout=1):
            break
    except OSError:
        time.sleep(1)
else:
    raise RuntimeError('Preview server did not start')
with sync_playwright() as p:
    browser = p.chromium.launch(channel='chrome', headless=True)
    page = browser.new_page(viewport={'width': 1536, 'height': 960})
    page.goto('http://127.0.0.1:8517')
    page.locator('.pa-condition-description').nth(11).wait_for()
    page.wait_for_timeout(500)
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    page.get_by_role('button', name='Borrower', exact=True).first.click()
    page.get_by_text('Co-Borrower', exact=True).wait_for(state='visible')
    page.get_by_text('Title', exact=True).click()
    page.get_by_role('button', name='Borrower +1', exact=True).wait_for()
    page.keyboard.press('Escape')
    for theme in ['light', 'dark']:
        page.evaluate('(theme) => document.documentElement.dataset.theme = theme', theme)
        sizes = page.evaluate('''() => {
            const descriptions = [...document.querySelectorAll('.pa-condition-description')];
            const button = [...document.querySelectorAll('button')].find(b => b.innerText.includes('Borrower +1'));
            return {buttonHeight: button.getBoundingClientRect().height,
                    buttonBackground: getComputedStyle(button).backgroundColor,
                    rowPitch: descriptions[1].getBoundingClientRect().top - descriptions[0].getBoundingClientRect().top};
        }''')
        print(theme, json.dumps(sizes))
        if sizes['rowPitch'] > 36:
            print(page.locator('.pa-condition-description').first.evaluate('''el => [...el.closest('[data-testid="stHorizontalBlock"]').querySelectorAll('*')].filter(n => n.getBoundingClientRect().height > 30).map(n => ({tag:n.tagName, testid:n.dataset.testid, base:n.dataset.baseweb, cls:n.className, height:n.getBoundingClientRect().height, min:getComputedStyle(n).minHeight, padding:getComputedStyle(n).padding, margin:getComputedStyle(n).margin}))'''))
            print(page.locator('.pa-condition-description').first.evaluate('''el => {
                const result = [];
                for (let n = el; n && n !== document.body; n = n.parentElement) {
                    const s = getComputedStyle(n);
                    result.push({tag: n.tagName, testid: n.dataset.testid, cls: n.className,
                        height: n.getBoundingClientRect().height, gap: s.gap, padding: s.padding, margin: s.margin});
                }
                return result;
            }'''))
        assert sizes['buttonHeight'] <= 28, sizes
        assert sizes['rowPitch'] <= 36, sizes
        page.screenshot(path=str(ROOT / 'screenshots' / f'compact-controls-{theme}.png'))
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    page.get_by_role('button', name='Borrower +1', exact=True).click()
    page.get_by_text('Co-Borrower', exact=True).wait_for(state='visible')
    page.screenshot(path=str(ROOT / 'screenshots' / 'party-checklist.png'))
    browser.close()
