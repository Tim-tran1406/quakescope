"""
Shared helper — load the clean staging table into a pandas DataFrame.

Every Phase 3 analysis script starts by calling load_events(). Keeping it in one
place means we connect to the database the same way everywhere.
"""

import os
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def get_engine():
    """Build a SQLAlchemy engine (the thing pandas uses to read/write Postgres)."""
    user = os.environ["DB_USER"]
    password = os.environ.get("DB_PASSWORD") or ""
    host, port, name = os.environ["DB_HOST"], os.environ["DB_PORT"], os.environ["DB_NAME"]
    auth = f"{user}:{password}@" if password else f"{user}@"
    return create_engine(f"postgresql+psycopg://{auth}{host}:{port}/{name}")


def load_events() -> pd.DataFrame:
    """Return all quakes as a DataFrame, with times standardised to UTC."""
    query = """
        SELECT id, event_time, magnitude, depth_km, latitude, longitude,
               place, tsunami, significance
        FROM staging.events
    """
    df = pd.read_sql(query, get_engine())
    # Standardise on UTC so year/month grouping is exact (no timezone surprises).
    df["event_time"] = pd.to_datetime(df["event_time"], utc=True)
    # numeric columns come back as Decimal from Postgres; make them plain floats.
    for col in ["magnitude", "latitude", "longitude", "depth_km"]:
        df[col] = df[col].astype(float)
    return df
