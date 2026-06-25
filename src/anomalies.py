"""
Phase 3, Method D — anomaly detection (two complementary views).

Plain-English idea:
    "Anomaly" = something that stands out from the usual pattern. We look two ways:
    1) Per-quake (Isolation Forest): given each quake's magnitude, depth and location,
       which individual quakes are weird combinations (e.g. very deep, or large in an
       unusual place)? Isolation Forest flags points that are "easy to isolate".
    2) Per-month (z-score): which whole months had far more quakes than normal? A
       z-score says how many standard deviations above average a month is; >2.5 is rare.

Run it with:   .venv/bin/python src/anomalies.py
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.ensemble import IsolationForest

from db import load_events, get_engine


def main() -> None:
    df = load_events()

    # --- D1: per-quake anomalies with Isolation Forest ---
    features = df[["magnitude", "depth_km", "latitude", "longitude"]].copy()
    features = features.fillna(features.median())
    forest = IsolationForest(contamination=0.01, n_estimators=200, random_state=42)
    forest.fit(features)
    df["anomaly_score"] = -forest.score_samples(features)     # higher = more unusual
    df["is_anomaly"] = forest.predict(features) == -1

    n_anom = int(df.is_anomaly.sum())
    print(f"Isolation Forest flagged {n_anom:,} unusual quakes ({n_anom / len(df) * 100:.1f}%).")
    print("\nThe 8 most unusual quakes:")
    cols = ["event_time", "magnitude", "depth_km", "place"]
    print(df.sort_values("anomaly_score", ascending=False).head(8)[cols].to_string(index=False))

    df[["id", "anomaly_score", "is_anomaly"]].to_sql(
        "event_anomalies", get_engine(), schema="analytics", if_exists="replace", index=False)

    # --- D2: per-month anomalies with z-scores ---
    monthly = df.set_index("event_time").resample("MS").size()
    mean, std = monthly.mean(), monthly.std()
    z = (monthly - mean) / std
    spikes = monthly[z > 2.5]
    print(f"\nUnusually busy months (z > 2.5): {len(spikes)}")
    for month, count in spikes.items():
        print(f"  {month:%Y-%m}: {count:,} quakes  (z = {(count - mean) / std:.1f})")

    _plot_map(df)
    _plot_monthly(monthly, mean, std, z)


def _plot_map(df) -> None:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    normal, anom = df[~df.is_anomaly], df[df.is_anomaly]
    ax.scatter(normal.longitude, normal.latitude, s=1, c="lightgray", alpha=0.4)
    ax.scatter(anom.longitude, anom.latitude, s=9, c="red", alpha=0.6, label="flagged unusual")
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Unusual quakes flagged by Isolation Forest (magnitude + depth + location)")
    ax.legend()
    fig.tight_layout()
    fig.savefig("docs/images/phase3-anomalies-map.png", dpi=130)
    print("Saved chart -> docs/images/phase3-anomalies-map.png")


def _plot_monthly(monthly, mean, std, z) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    ax.plot(monthly.index, monthly.values, color="#4285f4", lw=1)
    spikes = monthly[z > 2.5]
    ax.scatter(spikes.index, spikes.values, color="red", zorder=5, label="unusual month (z > 2.5)")
    ax.axhline(mean, color="gray", ls="--", lw=1, label="average month")
    ax.axhline(mean + 2.5 * std, color="orange", ls=":", lw=1, label="z = 2.5 threshold")
    ax.set_xlabel("Month")
    ax.set_ylabel("M4.5+ quakes per month")
    ax.set_title("Monthly counts — spikes are major aftershock sequences")
    ax.legend()
    fig.tight_layout()
    fig.savefig("docs/images/phase3-anomalies-monthly.png", dpi=130)
    print("Saved chart -> docs/images/phase3-anomalies-monthly.png")


if __name__ == "__main__":
    main()
