"""
Phase 2, Part 1 — Load the raw earthquake files into PostgreSQL.

Plain-English idea:
    Read the GeoJSON files we downloaded, and copy each earthquake into a database
    table called `raw.events`. We store each quake exactly as it arrived, in a single
    column of type JSONB (PostgreSQL's format for holding JSON). This is our "raw"
    layer inside the database — untouched, ready for SQL to clean up next.

Run it with:
    .venv/bin/python src/load_raw.py
"""

import json
import os
from pathlib import Path

import psycopg
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "raw"

# Read database settings from the .env file into the environment.
load_dotenv(ROOT / ".env")


def connection_string() -> str:
    """Build the 'how to reach the database' string from our .env settings."""
    parts = [
        f"host={os.environ['DB_HOST']}",
        f"port={os.environ['DB_PORT']}",
        f"dbname={os.environ['DB_NAME']}",
        f"user={os.environ['DB_USER']}",
    ]
    if os.environ.get("DB_PASSWORD"):          # only add a password if we set one
        parts.append(f"password={os.environ['DB_PASSWORD']}")
    return " ".join(parts)


def main() -> None:
    with psycopg.connect(connection_string()) as conn:   # open a connection
        with conn.cursor() as cur:                        # a cursor runs commands
            # 1) Create our three "layers" as schemas (areas inside the database).
            cur.execute("CREATE SCHEMA IF NOT EXISTS raw;")
            cur.execute("CREATE SCHEMA IF NOT EXISTS staging;")
            cur.execute("CREATE SCHEMA IF NOT EXISTS analytics;")

            # 2) Start the raw table fresh each time (so re-running is safe).
            cur.execute("DROP TABLE IF EXISTS raw.events;")
            cur.execute("CREATE TABLE raw.events (id text, raw jsonb);")

            # 3) Copy every earthquake from every file into raw.events.
            #    COPY is PostgreSQL's fastest way to bulk-load data.
            files = sorted(RAW_DIR.glob("earthquakes_*.geojson"))
            total = 0
            with cur.copy("COPY raw.events (id, raw) FROM STDIN") as copy:
                for f in files:
                    features = json.loads(f.read_text())["features"]
                    for feature in features:
                        copy.write_row((feature["id"], json.dumps(feature)))
                    total += len(features)
                    print(f"  loaded {f.name}: {len(features):,}")

        conn.commit()                                     # save the work

        # 4) Confirm what landed in the database.
        with conn.cursor() as cur:
            cur.execute("SELECT count(*) FROM raw.events;")
            print(f"\nraw.events now holds {cur.fetchone()[0]:,} earthquakes "
                  f"({total:,} read from disk).")


if __name__ == "__main__":
    main()
