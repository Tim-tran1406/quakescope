"""Take a screenshot of the web map. Usage: screenshot_map.py [URL] [OUTPUT]"""
import sys
from playwright.sync_api import sync_playwright

URL = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/app/"
OUT = sys.argv[2] if len(sys.argv) > 2 else "docs/images/phase5-map.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 820})
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(5000)          # let tiles + all markers finish drawing
    page.screenshot(path=OUT)
    browser.close()
    print("Saved", OUT)
