
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 18: AMV Historical Evolution
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Observed North Atlantic SST anomalies (NOAA NCEI ERSSTv6)
# This series does not isolate internal AMV.
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator


# ------------------------------------------------------------
# Directories and configuration
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT / "data" / "amv" /
    "north_atlantic_ssta.csv"
)

OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)

MODERN_START = "1950-01-01"

BLUE = "#24658A"
RED = "#C54B48"
DARK = "#17324D"
GRAY = "#657587"
LIGHT = "#E5EAF0"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
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
print("AMV | Historical Evolution\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing {INPUT}. Run script 16 first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
)

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError(
        "Missing or duplicated dates in AMV data"
    )

if (df.index.day != 1).any():
    raise ValueError(
        "Expected first-of-month timestamps"
    )

if "na_ssta" not in df.columns:
    raise ValueError(
        "Column na_ssta is missing"
    )

monthly = pd.to_numeric(
    df["na_ssta"],
    errors="coerce"
).sort_index()

monthly = monthly.replace(
    [np.inf, -np.inf],
    np.nan
)

if monthly.notna().sum() < 1800:
    raise ValueError(
        "Unexpectedly short North Atlantic SST record"
    )

if (monthly.dropna().abs() > 10).any():
    raise ValueError(
        "Unrealistic SST anomaly detected"
    )


# ------------------------------------------------------------
# Preserve complete monthly calendar
# ------------------------------------------------------------

calendar = pd.date_range(
    monthly.index.min(),
    monthly.index.max(),
    freq="MS"
)

monthly = monthly.reindex(calendar)

last_date = monthly.last_valid_index()

monthly = monthly.loc[:last_date]


# ------------------------------------------------------------
# Calculate running means
# ------------------------------------------------------------

series = pd.DataFrame({
    "na_ssta": monthly
})

series["na_ssta_12m"] = (
    monthly
    .rolling(12, min_periods=12)
    .mean()
)

series["na_ssta_120m"] = (
    monthly
    .rolling(120, min_periods=120)
    .mean()
)

modern = series.loc[
    MODERN_START:last_date
]

if modern["na_ssta"].notna().sum() < 600:
    raise ValueError(
        "Incomplete modern record"
    )


# ------------------------------------------------------------
# Latest observations
# ------------------------------------------------------------

summary = []

for column in [
    "na_ssta",
    "na_ssta_12m",
    "na_ssta_120m"
]:

    valid = series[column].dropna()

    if valid.empty:
        raise ValueError(
            f"No valid values for {column}"
        )

    date = valid.index[-1]
    value = float(valid.iloc[-1])

    summary.append((date, value))

    print(
        f"{column:16s} "
        f"{date:%Y-%m} "
        f"{value:+.3f} °C"
    )

print(
    f"Record: {monthly.index[0]:%Y-%m} "
    f"to {last_date:%Y-%m}"
)


# ------------------------------------------------------------
# Figure layout
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.2, 10.2),
    facecolor="white"
)

gs = fig.add_gridspec(
    nrows=3,
    ncols=2,
    left=0.09,
    right=0.955,
    bottom=0.195,
    top=0.785,
    hspace=0.58,
    wspace=0.06,
    height_ratios=[1.0, 1.0, 0.92],
    width_ratios=[5.2, 1.15],
)

axes = [
    fig.add_subplot(gs[i, 0])
    for i in range(3)
]

sides = [
    fig.add_subplot(gs[i, 1])
    for i in range(3)
]


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

fig.text(
    0.09, 0.955,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    fontsize=9,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.09, 0.909,
    "AMV | Historical Evolution",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.867,
    "Observed North Atlantic SST anomalies | "
    "Monthly to multidecadal variability",
    fontsize=10.5,
    color=GRAY
)


# ------------------------------------------------------------
# Panel definitions
# ------------------------------------------------------------

PANELS = [
    {
        "data": series,
        "title": "Full Historical Record",
        "description": (
            "Monthly SST anomalies and 12-month "
            "trailing mean | 1850–present"
        ),
        "field": "na_ssta_12m",
        "monthly": True,
        "years": 25,
    },
    {
        "data": modern,
        "title": "Modern Record | Since 1950",
        "description": (
            "Monthly SST anomalies and "
            "12-month trailing mean"
        ),
        "field": "na_ssta_12m",
        "monthly": True,
        "years": 10,
    },
    {
        "data": series,
        "title": "Multidecadal Perspective",
        "description": (
            "120-month trailing mean | "
            "Descriptive low-frequency variation"
        ),
        "field": "na_ssta_120m",
        "monthly": False,
        "years": 25,
    },
]


# ------------------------------------------------------------
# Draw panels
# ------------------------------------------------------------

for ax, panel in zip(axes, PANELS):

    data = panel["data"]

    smooth = data[panel["field"]]

    x = smooth.index
    y = smooth.to_numpy(dtype=float)

    good = np.isfinite(y)

    ax.set_facecolor("white")

    # Positive values
    ax.fill_between(
        x, 0, y,
        where=good & (y >= 0),
        interpolate=True,
        color=RED,
        alpha=0.18,
        zorder=2
    )

    # Negative values
    ax.fill_between(
        x, 0, y,
        where=good & (y < 0),
        interpolate=True,
        color=BLUE,
        alpha=0.21,
        zorder=2
    )

    # Monthly SST anomalies
    if panel["monthly"]:

        ax.plot(
            data.index,
            data["na_ssta"],
            color=GRAY,
            linewidth=0.70,
            alpha=0.38,
            zorder=3
        )

    # Smoothed time series
    ax.plot(
        x, y,
        color=DARK,
        linewidth=(
            1.85 if panel["monthly"] else 2.3
        ),
        zorder=4
    )

    # Zero reference
    ax.axhline(
        0,
        color=GRAY,
        linewidth=0.95,
        zorder=5
    )

    # Symmetric vertical scale
    if panel["monthly"]:
        extent_data = data["na_ssta"]
    else:
        extent_data = smooth

    extreme = float(
        extent_data.abs().max()
    )

    limit = max(
        0.5,
        np.ceil((extreme + 0.12) * 4) / 4
    )

    ax.set_ylim(-limit, limit)

    ax.yaxis.set_major_locator(
        MultipleLocator(
            0.5 if limit > 1.5 else 0.25
        )
    )

    ax.set_ylabel(
        "SST anomaly (°C)",
        color=GRAY,
        labelpad=10
    )

    # Time axis
    ax.set_xlim(
        x[0] - pd.DateOffset(months=8),
        x[-1] + pd.DateOffset(months=8)
    )

    ax.xaxis.set_major_locator(
        mdates.YearLocator(panel["years"])
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    # Titles
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
        va="bottom",
        fontsize=9,
        color=GRAY
    )

    # Grid
    ax.grid(
        axis="y",
        color=LIGHT,
        linewidth=0.8
    )

    ax.grid(
        axis="x",
        color=LIGHT,
        linewidth=0.55,
        alpha=0.7
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
# Latest observations: right-side panels
# ------------------------------------------------------------

SIDE_LABELS = [
    (
        "LATEST MONTHLY SSTA",
        "Monthly observation"
    ),
    (
        "LATEST 12-MONTH MEAN",
        "Trailing mean"
    ),
    (
        "LATEST 10-YEAR MEAN",
        "Trailing mean"
    ),
]

for side, (date, value), (label, note) in zip(
    sides,
    summary,
    SIDE_LABELS
):

    side.axis("off")

    if value > 0:
        color = RED
    elif value < 0:
        color = BLUE
    else:
        color = GRAY

    side.plot(
        [0.02, 0.02],
        [0.10, 0.84],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.2
    )

    side.text(
        0.13, 0.80,
        label,
        transform=side.transAxes,
        fontsize=8,
        fontweight="bold",
        va="top",
        color=GRAY
    )

    side.text(
        0.13, 0.58,
        f"{value:+.2f} °C",
        transform=side.transAxes,
        fontsize=17,
        fontweight="bold",
        va="top",
        color=color
    )

    side.text(
        0.13, 0.39,
        date.strftime("%b %Y"),
        transform=side.transAxes,
        fontsize=10,
        va="top",
        color=DARK
    )

    side.text(
        0.13, 0.23,
        note,
        transform=side.transAxes,
        fontsize=9,
        va="top",
        color=GRAY
    )


# ------------------------------------------------------------
# Legend
# ------------------------------------------------------------

handles = [
    Line2D(
        [0], [0],
        color=GRAY,
        linewidth=1.0,
        alpha=0.65,
        label="Monthly North Atlantic SSTA"
    ),
    Line2D(
        [0], [0],
        color=DARK,
        linewidth=2.0,
        label="Trailing mean (12 or 120 months)"
    ),
]

fig.legend(
    handles=handles,
    loc="lower left",
    bbox_to_anchor=(0.09, 0.150),
    ncol=2,
    frameon=False,
    fontsize=9,
    labelcolor=DARK,
    handlelength=2.5,
    columnspacing=2.0,
    borderaxespad=0
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.09, 0.118,
    "Observed North Atlantic SST anomalies combine "
    "internally generated variability and "
    "externally forced changes.",
    fontsize=8.2,
    color=GRAY
)

fig.text(
    0.09, 0.093,
    "The 10-year trailing mean is descriptive smoothing, "
    "not an isolated index of internally generated AMV.",
    fontsize=8.2,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.047,
    "Data: NOAA NCEI | North Atlantic SST "
    "anomaly index (ERSSTv6)",
    fontsize=8.2,
    color=GRAY
)

fig.text(
    0.955, 0.047,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.2,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "amv_historical_evolution.png"
svg_file = OUTPUT / "amv_historical_evolution.svg"

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

print("\nAMV Historical Evolution completed.\n")
