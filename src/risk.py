"""
Phase 3, Method E — seismic energy and a regional risk score.

Plain-English idea:
    Counting quakes treats a M5 and a M9 the same, which is silly — a M9 releases
    about a MILLION times more energy. So we convert magnitude to energy
    (energy roughly = 10^(1.5 * magnitude + 4.8) joules) and add it up per seismic
    zone. Then we build a transparent 0–100 risk score blending three things a zone's
    danger depends on: total energy released, the strongest quake seen, and how often
    it shakes.

Run it with:   .venv/bin/python src/risk.py
"""

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from db import load_events, get_engine


def normalise(s: pd.Series) -> pd.Series:
    """Squeeze any column onto a 0–1 scale so we can fairly combine them."""
    return (s - s.min()) / (s.max() - s.min())


def main() -> None:
    engine = get_engine()
    df = load_events()
    df["energy_j"] = 10 ** (1.5 * df.magnitude + 4.8)         # magnitude -> joules

    total = df.energy_j.sum()
    biggest = df.loc[df.magnitude.idxmax()]
    n_m8 = int((df.magnitude >= 8).sum())
    print(f"Total seismic energy 2010–2026 : {total:.2e} joules")
    print(f"The single M{biggest.magnitude} (Tōhoku) alone = "
          f"{biggest.energy_j / total * 100:.0f}% of ALL that energy")
    print(f"The {n_m8} quakes of M8+ together = "
          f"{df[df.magnitude >= 8].energy_j.sum() / total * 100:.0f}% of all energy "
          f"(out of {len(df):,} quakes)")

    # Total energy per seismic zone, joined to the cluster summary from Method A.
    clusters = pd.read_sql("SELECT * FROM analytics.clusters", engine)
    ec = pd.read_sql("SELECT id, cluster_id FROM analytics.event_clusters", engine)
    energy = (df.merge(ec, on="id").query("cluster_id != -1")
                .groupby("cluster_id")["energy_j"].sum()
                .rename("total_energy_j").reset_index())
    risk = clusters.merge(energy, on="cluster_id")

    risk["risk_score"] = (100 * (
        0.5 * normalise(np.log10(risk.total_energy_j)) +
        0.3 * normalise(risk.max_magnitude) +
        0.2 * normalise(risk.n_events)
    )).round(1)
    risk = risk.sort_values("risk_score", ascending=False)
    risk.to_sql("zone_risk", engine, schema="analytics", if_exists="replace", index=False)

    print("\nTop 10 riskiest seismic zones:")
    show = risk.head(10)[["top_region", "n_events", "max_magnitude", "total_energy_j", "risk_score"]]
    print(show.to_string(index=False))

    _plot(risk.head(12).iloc[::-1])


def _plot(top) -> None:
    y = np.arange(len(top))
    fig, ax = plt.subplots(figsize=(10, 6.5))
    ax.barh(y, top.risk_score, color="#e8743b")
    ax.set_yticks(y)
    ax.set_yticklabels(top.top_region)
    ax.set_xlabel("Risk score (0–100)")
    ax.set_title("Riskiest seismic zones  =  energy + strongest quake + frequency")
    for yi, v in zip(y, top.risk_score):
        ax.text(v + 0.5, yi, f"{v:.0f}", va="center", fontsize=9)
    fig.tight_layout()
    fig.savefig("docs/images/phase3-risk.png", dpi=130)
    print("Saved chart -> docs/images/phase3-risk.png")


if __name__ == "__main__":
    main()
