"""
Phase 3, Method C2 — Omori's law: how aftershocks fade after a big quake.

Plain-English idea:
    After a large earthquake, the ground keeps shaking with aftershocks — frequent at
    first, then fewer and fewer. Omori's law says that fade follows a smooth curve:
    the rate drops in proportion to 1 / time^p, where p is usually about 1.
    On a log-log chart that curve becomes a straight line, whose steepness is p.

    We test it on the 2011 M9.1 Tōhoku mainshock — quakes within 400 km, for 1 year.

Run it with:   .venv/bin/python src/omori.py
"""

import numpy as np
import pandas as pd
from scipy import stats
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from db import load_events

TOHOKU_LAT, TOHOKU_LON = 38.297, 142.373
MAINSHOCK = pd.Timestamp("2011-03-11 05:46:24", tz="UTC")
RADIUS_KM, WINDOW_DAYS = 400.0, 365


def haversine_km(lat1, lon1, lat2, lon2):
    R = 6371.0
    p1, p2 = np.radians(lat1), np.radians(lat2)
    dphi, dl = np.radians(lat2 - lat1), np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 2 * R * np.arcsin(np.sqrt(a))


def main() -> None:
    df = load_events()
    df = df.assign(dist=haversine_km(TOHOKU_LAT, TOHOKU_LON,
                                     df.latitude.to_numpy(), df.longitude.to_numpy()))
    df["days"] = (df.event_time - MAINSHOCK).dt.total_seconds() / 86400.0
    after = df[(df.dist <= RADIUS_KM) & (df.days > 0) & (df.days <= WINDOW_DAYS)]
    print(f"{len(after):,} aftershocks within {RADIUS_KM:.0f} km in the year after Tōhoku.")

    day = np.floor(after.days).astype(int) + 1
    per_day = after.groupby(day).size()
    d, rate = per_day.index.to_numpy(), per_day.to_numpy()
    keep = rate > 0
    slope, intercept, r, pv, se = stats.linregress(np.log10(d[keep]), np.log10(rate[keep]))
    p_omori = -slope
    print(f"Omori p-exponent = {p_omori:.2f}  (typically ~1).  fit R² = {r**2:.2f}")

    fig, ax = plt.subplots(figsize=(9, 6))
    ax.scatter(d, rate, s=14, color="#4285f4", label="aftershocks per day")
    xfit = np.array([d[keep].min(), d[keep].max()])
    ax.plot(xfit, 10 ** (intercept + slope * np.log10(xfit)), "r-", lw=2,
            label=f"Omori fit:  rate ∝ t^(−{p_omori:.2f})")
    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel("Days since the M9.1 mainshock  (log scale)")
    ax.set_ylabel("Aftershocks per day  (log scale)")
    ax.set_title("Omori's law — Tōhoku aftershocks fading through 2011")
    ax.legend()
    fig.tight_layout()
    fig.savefig("docs/images/phase3-omori.png", dpi=130)
    print("Saved chart -> docs/images/phase3-omori.png")


if __name__ == "__main__":
    main()
