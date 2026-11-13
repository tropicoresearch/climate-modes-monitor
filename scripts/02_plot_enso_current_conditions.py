
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 02: ENSO Current Conditions
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Data source: NOAA Climate Prediction Center
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.ticker import MultipleLocator, FuncFormatter


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "enso" / "enso_indices.csv"
OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Figure configuration
# ------------------------------------------------------------

MONTHS = 36

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
})


# ------------------------------------------------------------
# Read dataset
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("ENSO | Current Conditions\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 01_download_enso_indices.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
).sort_index()

required = ["roni", "nino34"]

if df.index.has_duplicates:
    raise ValueError("Duplicate dates in ENSO dataset")

for column in required:

    if column not in df.columns:
        raise ValueError(f"Missing column: {column}")

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    if df[column].dropna().empty:
        raise ValueError(f"No valid data in {column}")


# ------------------------------------------------------------
# Select last 36 calendar months
# ------------------------------------------------------------

latest_date = max(
    df[column].dropna().index.max()
    for column in required
)

start_date = latest_date - pd.DateOffset(
    months=MONTHS - 1
)

calendar = pd.date_range(
    start=start_date,
    end=latest_date,
    freq="MS"
)

recent = df.reindex(calendar)

print(
    f"Period: {start_date:%Y-%m} "
    f"to {latest_date:%Y-%m}"
)


# ------------------------------------------------------------
# Seasonal labels
# ------------------------------------------------------------

SEASONS = {
    1: "DJF",
    2: "JFM",
    3: "FMA",
    4: "MAM",
    5: "AMJ",
    6: "MJJ",
    7: "JJA",
    8: "JAS",
    9: "ASO",
    10: "SON",
    11: "OND",
    12: "NDJ",
}


# ------------------------------------------------------------
# Common vertical scale
# ------------------------------------------------------------

values = recent[required].to_numpy(dtype=float)
finite = values[np.isfinite(values)]

if finite.size == 0:
    raise ValueError("No valid ENSO observations")

maximum = np.max(np.abs(finite))

ylim = max(
    2.0,
    np.ceil((maximum + 0.4) * 2) / 2
)


# ------------------------------------------------------------
# Panel definitions
# ------------------------------------------------------------

PANELS = [
    {
        "column": "roni",
        "title": "Relative Oceanic Niño Index (RONI)",
        "description": "Three-month running mean",
        "frequency": "3-month season",
    },
    {
        "column": "nino34",
        "title": "Niño 3.4 SST Anomaly",
        "description": "Monthly sea surface temperature anomaly",
        "frequency": "Monthly value",
    },
]


# ------------------------------------------------------------
# Create figure
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(13.4, 8.4),
    facecolor="white"
)

# Two columns:
# Left: time series
# Right: latest observation

gs = fig.add_gridspec(
    nrows=2,
    ncols=2,
    left=0.09,
    right=0.95,
    bottom=0.18,
    top=0.79,
    hspace=0.40,
    wspace=0.06,
    width_ratios=[5.2, 1.15]
)


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
    "ENSO | Current Conditions",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Recent evolution of tropical Pacific sea surface "
    "temperature indices",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Draw panels
# ------------------------------------------------------------

for i, panel in enumerate(PANELS):

    column = panel["column"]

    ax = fig.add_subplot(gs[i, 0])
    side = fig.add_subplot(gs[i, 1])

    side.axis("off")

    series = recent[column]

    x = series.index
    y = series.to_numpy(dtype=float)

    # Positive anomalies
    ax.fill_between(
        x, 0, y,
        where=np.isfinite(y) & (y >= 0),
        interpolate=True,
        color=RED,
        alpha=0.18,
        zorder=2
    )

    # Negative anomalies
    ax.fill_between(
        x, 0, y,
        where=np.isfinite(y) & (y < 0),
        interpolate=True,
        color=BLUE,
        alpha=0.18,
        zorder=2
    )

    # Main time series
    ax.plot(
        x, y,
        color=DARK,
        linewidth=2.1,
        solid_capstyle="round",
        zorder=4
    )

    # Zero line
    ax.axhline(
        0,
        color=GRAY,
        linewidth=0.9,
        zorder=1
    )

    # Reference thresholds
    ax.axhline(
        0.5,
        color=RED,
        linewidth=1.0,
        linestyle=(0, (5, 4)),
        alpha=0.75,
        zorder=1
    )

    ax.axhline(
        -0.5,
        color=BLUE,
        linewidth=1.0,
        linestyle=(0, (5, 4)),
        alpha=0.75,
        zorder=1
    )

    # Latest valid observation
    valid = series.dropna()

    last_date = valid.index[-1]
    last_value = float(valid.iloc[-1])

    if last_value >= 0.5:
        marker_color = RED
    elif last_value <= -0.5:
        marker_color = BLUE
    else:
        marker_color = GRAY

    ax.scatter(
        [last_date],
        [last_value],
        s=65,
        color=marker_color,
        edgecolor="white",
        linewidth=1.4,
        zorder=6
    )

    # Observation period
    if column == "roni":
        period = (
            f"{SEASONS[last_date.month]} "
            f"{last_date.year}"
        )
    else:
        period = last_date.strftime("%b %Y")

    # Panel title
    ax.set_title(
        panel["title"],
        loc="left",
        fontsize=12.5,
        fontweight="bold",
        color=DARK,
        pad=18
    )

    ax.text(
        0.0, 1.025,
        panel["description"],
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=GRAY
    )

    # Axes limits
    ax.set_ylim(-ylim, ylim)

    ax.set_xlim(
        start_date - pd.Timedelta(days=12),
        latest_date + pd.DateOffset(months=1)
    )

    ax.set_ylabel(
        "Anomaly (°C)",
        color=GRAY,
        labelpad=10
    )

    # Y ticks
    ax.yaxis.set_major_locator(
        MultipleLocator(1.0)
    )

    ax.yaxis.set_major_formatter(
        FuncFormatter(
            lambda value, pos:
            f"{value:+.0f}" if value != 0 else "0"
        )
    )

    # X ticks
    ax.xaxis.set_major_locator(
        mdates.MonthLocator(bymonth=[1, 7])
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%b %Y")
    )

    # Grid
    ax.grid(
        axis="y",
        color=LIGHT,
        linewidth=0.8,
        alpha=0.85
    )

    ax.grid(
        axis="x",
        color=LIGHT,
        linewidth=0.6,
        alpha=0.5
    )

    ax.set_axisbelow(True)

    # Clean borders
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.spines["left"].set_color(LIGHT)
    ax.spines["bottom"].set_color(LIGHT)

    ax.tick_params(
        axis="both",
        which="major",
        length=0,
        pad=8
    )

    # --------------------------------------------------------
    # Latest observation: separate information column
    # --------------------------------------------------------

    side.plot(
        [0.02, 0.02],
        [0.12, 0.82],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.2
    )

    side.text(
        0.13, 0.80,
        "LATEST OBSERVATION",
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=8,
        fontweight="bold",
        color=GRAY
    )

    side.text(
        0.13, 0.60,
        f"{last_value:+.2f} °C",
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=marker_color
    )

    side.text(
        0.13, 0.42,
        period,
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color=DARK
    )

    side.text(
        0.13, 0.26,
        panel["frequency"],
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        color=GRAY
    )

    print(
        f"{column:10s} "
        f"{period:12s} "
        f"{last_value:+.2f} °C"
    )


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.117,
    "Dashed lines: ±0.5 °C reference thresholds. "
    "ENSO event identification also requires persistence "
    "and ocean–atmosphere coupling.",
    fontsize=8.3,
    color=GRAY
)

fig.text(
    0.09, 0.089,
    "RONI is placed at the central month of each "
    "three-month season; Niño 3.4 is monthly.",
    fontsize=8.3,
    color=GRAY
)

fig.text(
    0.09, 0.046,
    "Data: NOAA Climate Prediction Center (ERSSTv6)",
    fontsize=8.3,
    color=GRAY
)

fig.text(
    0.95, 0.046,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.3,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "enso_current_conditions.png"
svg_file = OUTPUT / "enso_current_conditions.svg"

fig.savefig(
    png_file,
    dpi=250,
    facecolor="white"
)

fig.savefig(
    svg_file,
    facecolor="white"
)

plt.close(fig)

print("\nFigures saved:")
print(f"  {png_file}")
print(f"  {svg_file}")

print("\nENSO Current Conditions completed.\n")
