"""
Phase 3, Method B — the Gutenberg-Richter b-value.

Plain-English idea:
    Small earthquakes are common; big ones are rare. The Gutenberg-Richter law says
    that for every step up in magnitude, the number of quakes drops by a roughly
    CONSTANT factor. On a log scale, that's a straight line. Its slope is the
    "b-value", and it's almost always near 1.0 worldwide — so computing it is also a
    great check that our data is sound.

    b ≈ 1.0 means: each whole magnitude up = about 10× fewer quakes.

Run it with:   .venv/bin/python src/bvalue.py
"""

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from db import load_events

DM = 0.1                       # magnitudes are reported to the nearest 0.1
LOG10E = np.log10(np.e)        # 0.4343 — a constant in the b-value formula


def estimate_mc(mags: np.ndarray) -> float:
    """Magnitude of completeness: the smallest magnitude we reliably record.

    'Maximum curvature' method: the most common magnitude bin, plus a small
    standard correction of 0.2.
    """
    bins = np.arange(mags.min(), mags.max() + DM, DM)
    counts, edges = np.histogram(mags, bins=bins)
    peak_magnitude = edges[np.argmax(counts)]
    return round(peak_magnitude + 0.2, 1)


def aki_b_value(mags: np.ndarray, mc: float) -> float:
    """Aki (1965) maximum-likelihood estimate of the b-value."""
    above = mags[mags >= mc - 1e-9]
    return LOG10E / (above.mean() - (mc - DM / 2))


def main() -> None:
    mags = load_events()["magnitude"].to_numpy()
    mags = mags[~np.isnan(mags)]

    mc = estimate_mc(mags)
    b = aki_b_value(mags, mc)
    n_above = int((mags >= mc).sum())
    a = np.log10(n_above) + b * mc          # the line's intercept

    print(f"Magnitude of completeness (Mc) : {mc}")
    print(f"b-value (Aki MLE)              : {b:.3f}   (worldwide it should be ~1.0)")
    print(f"a-value (overall activity)     : {a:.2f}")
    print(f"Earthquakes at or above Mc     : {n_above:,}")

    _plot(mags, mc, b, a)


def _plot(mags: np.ndarray, mc: float, b: float, a: float) -> None:
    centers = np.arange(4.5, mags.max() + DM, DM)
    per_bin = np.array([((mags >= m - DM / 2) & (mags < m + DM / 2)).sum() for m in centers])
    cumulative = np.array([(mags >= m).sum() for m in centers])

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.bar(centers, per_bin, width=DM * 0.9, color="#cfe0fb", label="count in each 0.1 bin")
    ax.scatter(centers, cumulative, s=16, color="#4285f4", label="cumulative  N(≥ M)")
    mfit = np.linspace(mc, mags.max(), 50)
    ax.plot(mfit, 10 ** (a - b * mfit), "r-", lw=2, label=f"Gutenberg–Richter fit:  b = {b:.2f}")
    ax.axvline(mc, color="gray", ls="--", lw=1, label=f"Mc = {mc}")

    ax.set_yscale("log")
    ax.set_xlabel("Magnitude")
    ax.set_ylabel("Number of earthquakes  (log scale)")
    ax.set_title("Gutenberg–Richter law: quake frequency vs magnitude  (M4.5+, 2010–2026)")
    ax.legend()
    fig.tight_layout()
    fig.savefig("docs/images/phase3-bvalue.png", dpi=130)
    print("Saved chart -> docs/images/phase3-bvalue.png")


if __name__ == "__main__":
    main()
