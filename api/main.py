"""
Phase 4 — QuakeScope's web API (FastAPI).

Plain-English idea:
    A web API is a set of URLs that hand back data (as JSON) when something asks. Our
    Phase 5 map website — and anyone on the internet — will call these URLs to get
    earthquakes, risk scores, clusters and anomalies, read live from PostgreSQL.

    Each function below becomes one URL ("endpoint"). FastAPI also builds clickable,
    interactive documentation for free at  /docs.

Run it (from the project folder):
    .venv/bin/uvicorn api.main:app --reload
Then open  http://127.0.0.1:8000/docs
"""

import os
from pathlib import Path

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def make_engine():
    """Build the connection to PostgreSQL from our .env settings."""
    user = os.environ["DB_USER"]
    password = os.environ.get("DB_PASSWORD") or ""
    host, port, name = os.environ["DB_HOST"], os.environ["DB_PORT"], os.environ["DB_NAME"]
    auth = f"{user}:{password}@" if password else f"{user}@"
    return create_engine(f"postgresql+psycopg://{auth}{host}:{port}/{name}")


engine = make_engine()

app = FastAPI(
    title="QuakeScope API",
    description="Serves earthquake data and analysis from the QuakeScope database.",
    version="1.0",
)

# Let a browser-based website (Phase 5) call this API from another address.
app.add_middleware(CORSMiddleware, allow_origins=["*"],
                   allow_methods=["*"], allow_headers=["*"])


def run_query(sql: str, **params):
    """Run a read-only SQL query safely (parameters are bound, never glued in)."""
    with engine.connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()
    return [dict(r) for r in rows]


@app.get("/")
def root():
    """A friendly index of what this API offers."""
    return {
        "name": "QuakeScope API",
        "try": ["/quakes?min_magnitude=7&limit=5", "/zones/risk", "/clusters",
                "/anomalies", "/stats/yearly"],
        "interactive_docs": "/docs",
    }


@app.get("/quakes")
def list_quakes(
    min_magnitude: float = Query(4.5, ge=0, le=10),
    start: str | None = Query(None, description="ISO date, e.g. 2023-01-01"),
    end: str | None = Query(None, description="ISO date (exclusive)"),
    region: str | None = Query(None, description="text match on place, e.g. Japan"),
    limit: int = Query(200, ge=1, le=20000),
):
    """Earthquakes from staging.events, with optional filters."""
    sql = [
        "SELECT id, event_time, magnitude::float AS magnitude, depth_km::float AS depth_km,",
        "       latitude::float AS latitude, longitude::float AS longitude, place, tsunami",
        "FROM staging.events WHERE magnitude >= :minmag",
    ]
    params = {"minmag": min_magnitude, "limit": limit}
    if start:
        sql.append("AND event_time >= :start"); params["start"] = start
    if end:
        sql.append("AND event_time < :end"); params["end"] = end
    if region:
        sql.append("AND place ILIKE :region"); params["region"] = f"%{region}%"
    sql.append("ORDER BY event_time DESC LIMIT :limit")
    return run_query(" ".join(sql), **params)


@app.get("/quakes/{quake_id}")
def get_quake(quake_id: str):
    """One earthquake by its USGS id."""
    rows = run_query("SELECT * FROM staging.events WHERE id = :id", id=quake_id)
    if not rows:
        raise HTTPException(status_code=404, detail="earthquake not found")
    return rows[0]


@app.get("/stats/yearly")
def yearly_counts():
    """How many quakes per year (the trend data)."""
    return run_query(
        "SELECT date_part('year', event_time AT TIME ZONE 'UTC')::int AS year, "
        "count(*) AS quakes FROM staging.events GROUP BY year ORDER BY year"
    )


@app.get("/zones/risk")
def riskiest_zones(limit: int = Query(20, ge=1, le=207)):
    """Seismic zones ranked by our risk score (Method E)."""
    return run_query(
        "SELECT cluster_id, top_region, n_events, max_magnitude::float AS max_magnitude, "
        "centroid_lat::float AS centroid_lat, centroid_lon::float AS centroid_lon, "
        "total_energy_j, risk_score FROM analytics.zone_risk "
        "ORDER BY risk_score DESC LIMIT :limit", limit=limit)


@app.get("/clusters")
def list_clusters(limit: int = Query(50, ge=1, le=207)):
    """Seismic zones found by DBSCAN (Method A), biggest first."""
    return run_query(
        "SELECT cluster_id, top_region, n_events, centroid_lat::float AS centroid_lat, "
        "centroid_lon::float AS centroid_lon, max_magnitude::float AS max_magnitude "
        "FROM analytics.clusters ORDER BY n_events DESC LIMIT :limit", limit=limit)


@app.get("/anomalies")
def list_anomalies(limit: int = Query(50, ge=1, le=500)):
    """The most unusual quakes (Method D), with their details."""
    return run_query(
        "SELECT e.id, e.event_time, e.magnitude::float AS magnitude, "
        "e.depth_km::float AS depth_km, e.place, a.anomaly_score "
        "FROM analytics.event_anomalies a "
        "JOIN staging.events e ON e.id = a.id "
        "WHERE a.is_anomaly = true "
        "ORDER BY a.anomaly_score DESC LIMIT :limit", limit=limit)


# Serve the Phase 5 map website (web/index.html) at /app.
# Mounted last so it never shadows the API routes above.
app.mount("/app", StaticFiles(directory=str(ROOT / "web"), html=True), name="web")
