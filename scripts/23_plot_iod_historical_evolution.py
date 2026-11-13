
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 23: IOD Historical Evolution
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA Climate Prediction Center / ERSSTv6
# Monthly Dipole Mode Index (DMI)
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.ticker import MultipleLocator


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "iod" / "iod_indices.csv"
OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

RECENT_YEARS = 25

BLUE = "#24658A"
RED = "#C54B48"
DARK = "#17324D"
GRAY = "#657587"
LIGHT = "#E5EAF0"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "axes.titlesize": 12,
    "axes.labelsize": 10,
    "axes.edgecolor": LIGHT,
    "axes.linewidth": 0.8,
    "xtick.color": GRAY,
    "ytick.color": GRAY,
    "xtick.labelsize": 9,
    "ytick.labelsize": 9,
    "savefig.facecolor": "white",
    "svg.fonttype": "none",
    "svg.hashsalt": "tropico-climate-modes-monitor",
})


# ------------------------------------------------------------
# Read and validate data
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("IOD | Historical Evolution\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 21_download_iod_indices.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
).sort_index()

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError("Invalid or duplicate observation dates")

if (df.index.day != 1).any():
    raise ValueError(
        "Expected monthly first-of-month timestamps"
    )

if "dmi" not in df.columns:
    raise ValueError("Missing DMI column")

df["dmi"] = pd.to_numeric(
    df["dmi"],
    errors="coerce"
).replace([np.inf, -np.inf], np.nan)

if df["dmi"].notna().sum() < 700:
    raise ValueError(
        "Insufficient historical DMI observations"
    )

if (df["dmi"].dropna().abs() > 10).any():
    raise ValueError(
        "Unrealistic DMI values detected"
    )


# ------------------------------------------------------------
# Preserve complete monthly calendar
# ------------------------------------------------------------

calendar = pd.date_range(
    start=df.index.min(),
    end=df.index.max(),
    freq="MS"
)

dmi = df["dmi"].reindex(calendar)
dmi.index.name = "date"

latest_date = dmi.last_valid_index()

if latest_date is None:
    raise ValueError("No valid DMI observations")

dmi = dmi.loc[:latest_date]

latest_value = float(dmi.loc[latest_date])


# ------------------------------------------------------------
# Recent historical period
# ------------------------------------------------------------

recent_start = (
    latest_date
    - pd.DateOffset(years=RECENT_YEARS)
    + pd.DateOffset(months=1)
)

recent = dmi.loc[recent_start:latest_date]

if recent.notna().sum() < 200:
    raise ValueError(
        "Insufficient recent DMI observations"
    )


# ------------------------------------------------------------
# Historical statistics
# ------------------------------------------------------------

valid = dmi.dropna()

maximum_date = valid.idxmax()
minimum_date = valid.idxmin()

maximum_value = float(valid.max())
minimum_value = float(valid.min())

print(
    f"Record: {valid.index.min():%Y-%m} "
    f"to {valid.index.max():%Y-%m}"
)

print(f"Valid observations: {len(valid)}")

print(
    f"Latest DMI: {latest_value:+.2f} °C "
    f"({latest_date:%b %Y})"
)

print(
    f"Historical maximum: {maximum_value:+.2f} °C "
    f"({maximum_date:%b %Y})"
)

print(
    f"Historical minimum: {minimum_value:+.2f} °C "
    f"({minimum_date:%b %Y})"
)


# ------------------------------------------------------------
# Figure layout
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(13.4, 8.4),
    facecolor="white"
)

gs = fig.add_gridspec(
    nrows=2,
    ncols=2,
    left=0.09,
    right=0.95,
    bottom=0.18,
    top=0.79,
    hspace=0.42,
    wspace=0.06,
    width_ratios=[5.2, 1.15]
)

axes = [
    fig.add_subplot(gs[i, 0])
    for i in range(2)
]

sides = [
    fig.add_subplot(gs[i, 1])
    for i in range(2)
]


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

fig.text(
    0.09, 0.954,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    fontsize=9,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.09, 0.908,
    "IOD | Historical Evolution",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Historical evolution of the Indian Ocean "
    "Dipole Mode Index",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Panel definitions
# ------------------------------------------------------------

PANELS = [
    {
        "series": dmi,
        "title": "Full Historical Record",
        "description": "Monthly DMI | 1950–present",
        "year_step": 10,
        "linewidth": 1.35,
    },
    {
        "series": recent,
        "title": "Recent Historical Evolution",
        "description": "Monthly DMI | Last 25 years",
        "year_step": 5,
        "linewidth": 2.0,
    },
]


# ------------------------------------------------------------
# Draw panels
# ------------------------------------------------------------

for ax, panel in zip(axes, PANELS):

    series = panel["series"]

    x = series.index
    y = series.to_numpy(dtype=float)

    finite = np.isfinite(y)

    # Positive DMI
    ax.fill_between(
        x,
        0,
        y,
        where=finite & (y > 0),
        interpolate=True,
        color=RED,
        alpha=0.21,
        zorder=2
    )

    # Negative DMI
    ax.fill_between(
        x,
        0,
        y,
        where=finite & (y < 0),
        interpolate=True,
        color=BLUE,
        alpha=0.23,
        zorder=2
    )

    # Main time series
    ax.plot(
        x,
        y,
        color=DARK,
        linewidth=panel["linewidth"],
        solid_capstyle="round",
        zorder=4
    )

    # Zero reference
    ax.axhline(
        0,
        color=GRAY,
        linewidth=1.0,
        zorder=3
    )

    # Dynamic symmetric scale
    maximum = np.nanmax(np.abs(y))

    limit = max(
        1.0,
        np.ceil((maximum + 0.2) * 2) / 2
    )

    ax.set_ylim(-limit, limit)

    ax.yaxis.set_major_locator(
        MultipleLocator(
            0.5 if limit <= 2.5 else 1.0
        )
    )

    ax.set_xlim(
        x.min() - pd.DateOffset(months=3),
        x.max() + pd.DateOffset(months=3)
    )

    ax.xaxis.set_major_locator(
        mdates.YearLocator(
            panel["year_step"]
        )
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    ax.set_ylabel(
        "DMI (°C)",
        color=GRAY,
        labelpad=11
    )

    ax.set_title(
        panel["title"],
        loc="left",
        fontsize=12.5,
        fontweight="bold",
        color=DARK,
        pad=18
    )

    ax.text(
        0,
        1.025,
        panel["description"],
        transform=ax.transAxes,
        fontsize=9,
        color=GRAY,
        va="bottom"
    )

    # Latest observation
    color = (
        RED if latest_value > 0
        else BLUE if latest_value < 0
        else GRAY
    )

    ax.scatter(
        [latest_date],
        [latest_value],
        s=62,
        color=color,
        edgecolor="white",
        linewidth=1.3,
        zorder=6
    )

    # Grid
    ax.grid(
        axis="y",
        color=LIGHT,
        linewidth=0.8,
        alpha=0.90
    )

    ax.grid(
        axis="x",
        color=LIGHT,
        linewidth=0.6,
        alpha=0.55
    )

    ax.set_axisbelow(True)

    # Borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_color(LIGHT)
    ax.spines["bottom"].set_color(LIGHT)

    ax.tick_params(
        axis="both",
        length=0,
        pad=8
    )


# ------------------------------------------------------------
# Side panels
# ------------------------------------------------------------

for side in sides:

    side.axis("off")

    side.plot(
        [0.02, 0.02],
        [0.12, 0.82],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.2
    )


# ------------------------------------------------------------
# Latest observation
# ------------------------------------------------------------

side = sides[0]

latest_color = (
    RED if latest_value > 0
    else BLUE if latest_value < 0
    else GRAY
)

side.text(
    0.13, 0.80,
    "LATEST OBSERVATION",
    transform=side.transAxes,
    fontsize=8,
    fontweight="bold",
    color=GRAY,
    va="top"
)

side.text(
    0.13, 0.60,
    f"{latest_value:+.2f} °C",
    transform=side.transAxes,
    fontsize=17,
    fontweight="bold",
    color=latest_color,
    va="top"
)

side.text(
    0.13, 0.41,
    latest_date.strftime("%b %Y"),
    transform=side.transAxes,
    fontsize=10,
    color=DARK,
    va="top"
)

side.text(
    0.13, 0.25,
    "POSITIVE DMI" if latest_value > 0
    else "NEGATIVE DMI" if latest_value < 0
    else "ZERO DMI",
    transform=side.transAxes,
    fontsize=8.5,
    fontweight="bold",
    color=latest_color,
    va="top"
)


# ------------------------------------------------------------
# Historical extremes
# ------------------------------------------------------------

side = sides[1]

side.text(
    0.13, 0.80,
    "MONTHLY EXTREMES",
    transform=side.transAxes,
    fontsize=8,
    fontweight="bold",
    color=GRAY,
    va="top"
)

side.text(
    0.13, 0.62,
    f"MAX  {maximum_value:+.2f} °C",
    transform=side.transAxes,
    fontsize=12,
    fontweight="bold",
    color=RED,
    va="top"
)

side.text(
    0.13, 0.48,
    maximum_date.strftime("%b %Y"),
    transform=side.transAxes,
    fontsize=9,
    color=GRAY,
    va="top"
)

side.text(
    0.13, 0.31,
    f"MIN  {minimum_value:+.2f} °C",
    transform=side.transAxes,
    fontsize=12,
    fontweight="bold",
    color=BLUE,
    va="top"
)

side.text(
    0.13, 0.17,
    minimum_date.strftime("%b %Y"),
    transform=side.transAxes,
    fontsize=9,
    color=GRAY,
    va="top"
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.09, 0.117,
    "Monthly DMI = western minus southeastern "
    "tropical Indian Ocean SST anomalies.",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.09, 0.089,
    "Monthly extremes and index sign are descriptive. "
    "Persistent IOD events require additional "
    "temporal criteria.",
    fontsize=8.4,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.046,
    "Data: NOAA CPC | ERSSTv6, climatology 1991–2020",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.95, 0.046,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.4,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "iod_historical_evolution.png"
svg_file = OUTPUT / "iod_historical_evolution.svg"

fig.savefig(
    png_file,
    dpi=250,
    facecolor="white",
    metadata={
        "Software": "TRÓPICO Climate Modes Monitor"
    }
)

fig.savefig(
    svg_file,
    facecolor="white",
    metadata={"Date": None}
)

plt.close(fig)

print("\nFigures saved:")
print(f"  {png_file}")
print(f"  {svg_file}")

print("\nIOD Historical Evolution completed.\n")
