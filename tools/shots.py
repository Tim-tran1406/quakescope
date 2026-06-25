"""Screenshot each view of the site for a quick visual check."""
import sys
from playwright.sync_api import sync_playwright

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8002/"

with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 860})
    pg.goto(BASE, wait_until="networkidle", timeout=60000)
    pg.wait_for_timeout(1200)
    pg.screenshot(path="/tmp/home.png")

    pg.click("#nav .links a[data-view='map']")
    pg.wait_for_timeout(8000)                      # data + tiles + markers
    pg.screenshot(path="/tmp/map.png")
    pg.screenshot(path="docs/images/phase5-map.png")   # refresh the README hero

    pg.click("#nav .links a[data-view='findings']")
    pg.wait_for_timeout(2500)
    pg.screenshot(path="/tmp/findings.png")

    pg.click("#nav .links a[data-view='about']")
    pg.wait_for_timeout(1000)
    pg.screenshot(path="/tmp/about.png")
    b.close()
    print("done")
