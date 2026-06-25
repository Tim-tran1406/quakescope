"""
Phase 3, Method C1 — Is seismic activity increasing? (Mann-Kendall trend test)

Plain-English idea:
    Looking at a wiggly line of yearly counts, our eyes are easily fooled. The
    Mann-Kendall test is the proper, neutral way to ask "is there a real upward (or
    downward) trend, or is this just random wobble?" It gives a p-value: if p < 0.05
    we'd call the trend real; otherwise we can't.
    Sen's slope then says how big the trend is (quakes per year).

Run it with:   .venv/bin/python src/trend.py
"""

import numpy as np
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from db import load_events


def mann_kendall(x: np.ndarray):
    """Return (S statistic, Z score, p-value) for a monotonic trend in x."""
    x = np.asarray(x, dtype=float)
    n = len(x)
    s = sum(np.sign(x[j] - x[i]) for i in range(n - 1) for j in range(i + 1, n))
    _, tie_counts = np.unique(x, return_counts=True)          # correct for tied values
    tie_term = sum(t * (t - 1) * (2 * t + 5) for t in tie_counts)
    var_s = (n * (n - 1) * (2 * n + 5) - tie_term) / 18.0
    if s > 0:
        z = (s - 1) / np.sqrt(var_s)
    elif s < 0:
        z = (s + 1) / np.sqrt(var_s)
    else:
        z = 0.0
    p = 2 * (1 - stats.norm.cdf(abs(z)))
    return s, z, p


def sens_slope(years: np.ndarray, counts: np.ndarray) -> float:
    """The trend's size: median of the slope between every pair of years."""
    n = len(years)
    slopes = [(counts[j] - counts[i]) / (years[j] - years[i])
              for i in range(n - 1) for j in range(i + 1, n)]
    return float(np.median(slopes))


def main() -> None:
    df = load_events()
    df["year"] = df["event_time"].dt.year
    by_year = df[df.year <= 2025].groupby("year").size()      # drop the partial 2026
    years, counts = by_year.index.to_numpy(), by_year.to_numpy()

    s, z, p = mann_kendall(counts)
    slope = sens_slope(years, counts)
    verdict = "a statistically significant trend" if p < 0.05 else "NO significant trend"
    print(f"Mann-Kendall:  S = {s:.0f},  Z = {z:.2f},  p = {p:.3f}")
    print(f"Sen's slope:   {slope:+.0f} quakes per year")
    print(f"Conclusion:    {verdict} in M4.5+ activity, 2010–2025.")

    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.bar(years, counts, color="#cfe0fb", edgecolor="#4285f4")
    mid_x, mid_y = np.median(years), np.median(counts)
    xline = np.array([years.min(), years.max()])
    ax.plot(xline, mid_y + slope * (xline - mid_x), "r-", lw=2,
            label=f"Sen's slope: {slope:+.0f}/yr")
    ax.set_xlabel("Year")
    ax.set_ylabel("M4.5+ earthquakes")
    ax.set_title(f"Is activity increasing?  Mann–Kendall p = {p:.2f}  →  {verdict}")
    ax.legend()
    fig.tight_layout()
    fig.savefig("docs/images/phase3-trend.png", dpi=130)
    print("Saved chart -> docs/images/phase3-trend.png")


if __name__ == "__main__":
    main()
