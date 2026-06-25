"""Take a real screenshot of the running web map (for the study docs)."""
from playwright.sync_api import sync_playwright

URL = "http://127.0.0.1:8000/app/"
OUT = "docs/images/phase5-map.png"

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1400, "height": 820})
    page.goto(URL, wait_until="networkidle", timeout=60000)
    page.wait_for_timeout(4500)          # let map tiles + all markers finish drawing
    page.screenshot(path=OUT)
    browser.close()
    print("Saved", OUT)
