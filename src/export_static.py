"""
Export the data the web map needs into static JSON files.

Why: historical earthquakes don't change, so the map doesn't need a live backend.
By baking the data into JSON, the map becomes a plain static website we can host
for free on GitHub Pages — no server to keep running.

Run it with:   .venv/bin/python src/export_static.py
"""

import json
from pathlib import Path

from sqlalchemy import text

from db import get_engine

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "web" / "data"
MIN_MAG = 5.0   # quakes shown on the map (smaller ones are too many for a web page)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    engine = get_engine()
    with engine.connect() as conn:
        quakes = conn.execute(text("""
            SELECT id,
                   round(magnitude, 1)::float  AS mag,
                   round(latitude, 3)::float   AS lat,
                   round(longitude, 3)::float  AS lon,
                   round(depth_km, 1)::float   AS depth,
                   place,
                   tsunami,
                   to_char(event_time AT TIME ZONE 'UTC',
                           'YYYY-MM-DD"T"HH24:MI:SS"Z"')  AS time
            FROM staging.events
            WHERE magnitude >= :m
            ORDER BY magnitude ASC          -- big quakes drawn last, so they sit on top
        """), {"m": MIN_MAG}).mappings().all()

        zones = conn.execute(text("""
            SELECT top_region, risk_score, n_events,
                   max_magnitude::float AS max_magnitude,
                   centroid_lat::float  AS lat,
                   centroid_lon::float  AS lon
            FROM analytics.zone_risk
            ORDER BY risk_score DESC
            LIMIT 30
        """)).mappings().all()

    (OUT / "quakes.json").write_text(json.dumps([dict(r) for r in quakes]))
    (OUT / "zones.json").write_text(json.dumps([dict(r) for r in zones]))

    size_mb = (OUT / "quakes.json").stat().st_size / 1e6
    print(f"quakes (M{MIN_MAG}+): {len(quakes):,}  ->  web/data/quakes.json ({size_mb:.1f} MB)")
    print(f"zones:           {len(zones)}  ->  web/data/zones.json")


if __name__ == "__main__":
    main()
