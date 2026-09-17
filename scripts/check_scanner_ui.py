"""Inspect scanner contrast in desktop light/dark themes and on a narrow screen."""
import atexit
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
from urllib.request import urlopen

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
server = subprocess.Popen([sys.executable, "-m", "streamlit", "run", "scripts/preview_scanner_ui.py",
                           "--server.port=8518", "--server.address=127.0.0.1", "--server.headless=true",
                           "--browser.gatherUsageStats=false"], cwd=ROOT,
                          stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                          creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0)
atexit.register(server.terminate)
for attempt in range(30):
    try:
        urlopen("http://127.0.0.1:8518/_stcore/health", timeout=1).close()
        break
    except OSError:
        time.sleep(1)
else:
    raise RuntimeError("Preview did not start")
output = Path(tempfile.gettempdir()) / "processor-scanner-preview"
output.mkdir(exist_ok=True)
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", headless=True)
    page = browser.new_page(viewport={"width": 1536, "height": 960})
    page.goto("http://127.0.0.1:8518")
    page.get_by_role("heading", name="Scan documents").wait_for()
    page.get_by_role('link', name='Terms of Service', exact=True).wait_for()
    for theme in ("light", "dark"):
        page.evaluate("theme => document.documentElement.dataset.theme = theme", theme)
        page.wait_for_timeout(1000)
        page.get_by_role('button', name='Scanner', exact=True).wait_for(state='visible')
        page.locator('[data-testid="stFileUploader"]').wait_for(state='visible')
        colors = page.evaluate('''() => {
            const styles = el => { const s = getComputedStyle(el); return {color: s.color, background: s.backgroundColor}; };
            const uploader = document.querySelector('[data-testid="stFileUploader"]');
            const upload = uploader.querySelector('button');
            const scanner = [...document.querySelectorAll('[data-testid="stSidebar"] button')].find(el => el.innerText === 'Scanner');
            return {upload: {...styles(upload), color: getComputedStyle(upload.querySelector('span, p') || upload).color},
                    navigation: {...styles(scanner), color: getComputedStyle(scanner.querySelector('p') || scanner).color},
                    page: getComputedStyle(document.querySelector('.stApp')).backgroundColor,
                    intro: getComputedStyle(document.querySelector('.pa-scanner-heading p')).color,
                    uploadSurface: getComputedStyle(uploader).backgroundColor,
                    chips: [...document.querySelectorAll('.pa-pchip')].map(el => ({
                        color: getComputedStyle(el.querySelector('.pa-pchip-l')).color,
                        background: getComputedStyle(el).backgroundColor}))};
        }''')
        def luminance(rgb):
            values = [float(x) / 255 for x in rgb.removeprefix('rgb(').removesuffix(')').split(',')]
            linear = [x / 12.92 if x <= .04045 else ((x + .055) / 1.055) ** 2.4 for x in values]
            return sum(x * weight for x, weight in zip(linear, (.2126, .7152, .0722)))
        def contrast(a, b):
            x, y = sorted((luminance(a), luminance(b)))
            return (y + .05) / (x + .05)
        ratios = {name: round(contrast(colors[name]['color'], colors[name]['background']), 2)
                  for name in ('upload', 'navigation')}
        ratios['intro'] = round(contrast(colors['intro'], colors['page']), 2)
        ratios['pipeline'] = round(min(contrast(chip['color'], chip['background']) for chip in colors['chips']), 2)
        print(theme, json.dumps({"contrast": ratios, "colors": colors}))
        assert min(ratios.values()) >= 4.5, ratios
        page.screenshot(path=str(output / f"scanner-{theme}.png"))
    page.evaluate("document.documentElement.dataset.theme = 'light'")
    page.get_by_text("Privacy and data handling", exact=True).click()
    page.get_by_text("Built for GLBA compliance.", exact=False).wait_for(state="visible")
    page.get_by_text("Privacy and data handling", exact=True).click()
    page.set_viewport_size({"width": 768, "height": 1024})
    page.wait_for_timeout(1000)
    assert page.evaluate("document.querySelector('.pa-scanner-heading').getBoundingClientRect().top > document.querySelector('.pa-pipe-dash').getBoundingClientRect().bottom"), 'Heading obscured by pipeline header'
    page.screenshot(path=str(output / "scanner-narrow.png"))
    assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth"), 'Horizontal overflow'
    browser.close()
print("Screenshots:", output)
server.terminate()
