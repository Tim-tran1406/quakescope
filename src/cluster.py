"""
Phase 3, Method A — find seismic zones with DBSCAN clustering.

Plain-English idea:
    DBSCAN looks at where quakes are dense on the globe and groups those dense
    patches into "clusters" (seismic zones). Lonely quakes in empty areas are left
    out as "noise". We never tell it where the zones are — it finds them itself.

We measure distance the correct way for a globe (great-circle / haversine), not as
if the Earth were a flat sheet.

Run it with:   .venv/bin/python src/cluster.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")          # draw to a file, no pop-up window
import matplotlib.pyplot as plt
from sklearn.cluster import DBSCAN

from db import load_events, get_engine

EARTH_RADIUS_KM = 6371.0
EPS_KM = 50.0                  # quakes within ~50 km can belong to the same zone
MIN_SAMPLES = 40               # a zone needs at least this many quakes to count


def main() -> None:
    df = load_events()

    # DBSCAN with haversine wants coordinates in radians, as (latitude, longitude).
    coords = np.radians(df[["latitude", "longitude"]].to_numpy())
    model = DBSCAN(
        eps=EPS_KM / EARTH_RADIUS_KM,   # convert km into the radians haversine uses
        min_samples=MIN_SAMPLES,
        metric="haversine",
        algorithm="ball_tree",
    ).fit(coords)
    df["cluster_id"] = model.labels_     # -1 means "noise" (not in any zone)

    n_clusters = df.loc[df.cluster_id != -1, "cluster_id"].nunique()
    n_noise = int((df.cluster_id == -1).sum())
    print(f"Found {n_clusters} seismic zones. "
          f"{len(df) - n_noise:,} quakes fell into a zone, {n_noise:,} were scattered noise.\n")

    # A readable region label = the text after the last comma in "place".
    df["region"] = df["place"].str.split(",").str[-1].str.strip()

    summary = (
        df[df.cluster_id != -1]
        .groupby("cluster_id")
        .agg(
            n_events=("id", "size"),
            centroid_lat=("latitude", "mean"),
            centroid_lon=("longitude", "mean"),
            max_magnitude=("magnitude", "max"),
            top_region=("region", lambda s: s.mode().iat[0] if not s.mode().empty else ""),
        )
        .reset_index()
        .sort_values("n_events", ascending=False)
    )
    print("Top 10 seismic zones by number of quakes:")
    print(summary.head(10).to_string(index=False))

    # Save results into the analytics schema (for the dashboards later).
    engine = get_engine()
    df[["id", "cluster_id"]].to_sql("event_clusters", engine, schema="analytics",
                                    if_exists="replace", index=False)
    summary.to_sql("clusters", engine, schema="analytics",
                   if_exists="replace", index=False)
    print("\nWrote analytics.event_clusters and analytics.clusters.")

    _plot(df)


def _plot(df) -> None:
    fig, ax = plt.subplots(figsize=(13, 6.5))
    noise = df[df.cluster_id == -1]
    zoned = df[df.cluster_id != -1]
    ax.scatter(noise.longitude, noise.latitude, s=1, c="lightgray", alpha=0.4)
    ax.scatter(zoned.longitude, zoned.latitude, s=2,
               c=zoned.cluster_id % 20, cmap="tab20", alpha=0.6)
    ax.set_xlim(-180, 180)
    ax.set_ylim(-90, 90)
    ax.set_aspect("equal")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title("Seismic zones found automatically by DBSCAN  (M4.5+, 2010–2026)")
    fig.tight_layout()
    fig.savefig("docs/images/phase3-clusters.png", dpi=130)
    print("Saved chart -> docs/images/phase3-clusters.png")


if __name__ == "__main__":
    main()
