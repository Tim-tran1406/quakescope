"""
Phase 1 — Ingest earthquake data from the USGS.

Plain-English idea:
    Ask the USGS website for every earthquake in a range of years, one year at a
    time, and save each year's answer to a file on disk. We save the data exactly
    as it arrives ("raw"), so we never have to re-download it, and so we always
    have an untouched original to go back to.

Run it (from the project folder) with:
    .venv/bin/python src/ingest.py
"""

import json
import time
from pathlib import Path

import requests

# ---------------------------------------------------------------------------
# SETTINGS — change these to pull more or less data.
# ---------------------------------------------------------------------------
USGS_URL = "https://earthquake.usgs.gov/fdsnws/event/1/query"
START_YEAR = 2010          # first year to download
END_YEAR = 2026            # last year to download (this year)
MIN_MAGNITUDE = 4.5        # only quakes at least this strong (see note below)

# Why magnitude 4.5? The USGS reliably records EVERY quake this size or bigger,
# anywhere on Earth. Smaller quakes are only well-recorded near sensors (mostly
# the USA), which would bias a "global" study. 4.5+ gives a fair worldwide picture.

# Where downloaded files are saved. (data/raw is gitignored — big & re-downloadable.)
RAW_DIR = Path(__file__).resolve().parent.parent / "data" / "raw"


def fetch_one_year(year: int, max_tries: int = 4) -> dict:
    """Ask the USGS for all earthquakes in a single year and return the answer.

    Networks are flaky, so if a request times out or fails, we wait a moment and
    try again (up to `max_tries` times) before giving up.
    """
    params = {
        "format": "geojson",               # ask for the answer as GeoJSON
        "starttime": f"{year}-01-01",      # from the 1st of January...
        "endtime": f"{year + 1}-01-01",    # ...up to (not including) next Jan 1st
        "minmagnitude": MIN_MAGNITUDE,
        "orderby": "time-asc",             # oldest first (valid values: time, time-asc, magnitude, magnitude-asc)
    }
    for attempt in range(1, max_tries + 1):
        try:
            response = requests.get(USGS_URL, params=params, timeout=180)
            response.raise_for_status()    # if the request failed, raise an error
            return response.json()         # success: turn the text answer into Python data
        except requests.exceptions.RequestException as error:
            if attempt == max_tries:
                raise                       # out of tries — give up and stop loudly
            wait = 5 * attempt              # wait longer after each failure
            print(f"      attempt {attempt} failed ({type(error).__name__}); retrying in {wait}s...")
            time.sleep(wait)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)   # make the folder if it's missing

    total = 0
    print(f"Downloading global quakes (magnitude >= {MIN_MAGNITUDE}), {START_YEAR}-{END_YEAR}\n")

    for year in range(START_YEAR, END_YEAR + 1):
        out_file = RAW_DIR / f"earthquakes_{year}.geojson"

        # RESUME: if we already downloaded this year, skip it (don't waste a request)
        if out_file.exists():
            existing = json.loads(out_file.read_text())["features"]
            print(f"  {year}: {len(existing):>6,} earthquakes  (already downloaded, skipping)")
            total += len(existing)
            continue

        data = fetch_one_year(year)
        quakes = data["features"]          # the list of earthquakes is under "features"
        out_file.write_text(json.dumps(data))   # save this year's raw answer to its own file

        print(f"  {year}: {len(quakes):>6,} earthquakes  ->  data/raw/{out_file.name}")
        total += len(quakes)
        time.sleep(0.5)                    # be polite: a short pause between requests

    print(f"\nDone. {total:,} earthquakes saved to data/raw/")


if __name__ == "__main__":
    main()
