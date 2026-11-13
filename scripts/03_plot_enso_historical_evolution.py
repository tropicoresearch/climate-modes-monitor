
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 03: ENSO Historical Evolution
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Data source: NOAA Climate Prediction Center (ERSSTv6)
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Patch
from matplotlib.ticker import MultipleLocator, FuncFormatter


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "enso" / "enso_indices.csv"
OUTPUT = ROOT / "docs" / "figures"
OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

RECENT_YEARS = 20
THRESHOLD = 0.5

BLUE = "#24658A"
RED = "#C54B48"
DARK = "#17324D"
GRAY = "#657587"
NEUTRAL = "#A8B3BE"
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
# Read and validate RONI
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("ENSO | Historical Evolution\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 01_download_enso_indices.py first."
    )

df = pd.read_csv(INPUT, parse_dates=["date"])

if "roni" not in df.columns:
    raise ValueError("Missing column: roni")

if df["date"].isna().any() or df["date"].duplicated().any():
    raise ValueError("Invalid or duplicate dates")

df["roni"] = pd.to_numeric(
    df["roni"],
    errors="coerce"
)

roni = (
    df.set_index("date")["roni"]
    .sort_index()
    .dropna()
)

if len(roni) < 600:
    raise ValueError("RONI series is unexpectedly short")

if (roni.index.day != 1).any():
    raise ValueError(
        "Expected dates at the first day of each month"
    )

# Preserve missing seasons as NaN.
calendar = pd.date_range(
    roni.index.min(),
    roni.index.max(),
    freq="MS"
)

roni = roni.reindex(calendar)

print(
    f"Record: {roni.index.min():%Y-%m} "
    f"to {roni.index.max():%Y-%m}"
)
print(f"Valid RONI seasons: {roni.notna().sum()}")
print(f"Missing seasons: {roni.isna().sum()}")


# ------------------------------------------------------------
# Latest observation
# ------------------------------------------------------------

last_date = roni.last_valid_index()
last_value = float(roni.loc[last_date])

seasons = {
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

last_season = (
    f"{seasons[last_date.month]} {last_date.year}"
)

print(
    f"Latest RONI: {last_value:+.2f} °C "
    f"({last_season})"
)


# ------------------------------------------------------------
# Threshold-based colors
# ------------------------------------------------------------

# These colors represent individual seasonal index
# conditions, not officially classified ENSO events.

warm = roni >= THRESHOLD
cold = roni <= -THRESHOLD

colors = np.where(
    warm,
    RED,
    np.where(cold, BLUE, NEUTRAL)
)

peak = np.nanmax(
    np.abs(roni.to_numpy(dtype=float))
)

y_limit = max(
    2.0,
    np.ceil((peak + 0.3) * 2) / 2
)


# ------------------------------------------------------------
# Select recent record
# ------------------------------------------------------------

recent_start = max(
    roni.index[0],
    last_date
    - pd.DateOffset(years=RECENT_YEARS)
    + pd.DateOffset(months=1)
)

recent = roni.loc[recent_start:last_date]

recent_colors = np.where(
    recent >= THRESHOLD,
    RED,
    np.where(
        recent <= -THRESHOLD,
        BLUE,
        NEUTRAL
    )
)


# ------------------------------------------------------------
# Create figure
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14, 9.0),
    facecolor="white"
)

gs = fig.add_gridspec(
    nrows=2,
    ncols=1,
    left=0.085,
    right=0.955,
    bottom=0.205,
    top=0.790,
    hspace=0.38,
    height_ratios=[1.35, 1.0]
)

ax_history = fig.add_subplot(gs[0])
ax_recent = fig.add_subplot(gs[1])


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

fig.text(
    0.085, 0.955,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    fontsize=9,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.085, 0.911,
    "ENSO | Historical Evolution",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.085, 0.870,
    "Relative Oceanic Niño Index (RONI) | "
    "NOAA CPC, 1950–present",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Latest RONI value
# ------------------------------------------------------------

if last_value >= THRESHOLD:
    latest_color = RED
elif last_value <= -THRESHOLD:
    latest_color = BLUE
else:
    latest_color = GRAY

fig.text(
    0.955, 0.948,
    f"LATEST · {last_season}",
    ha="right",
    fontsize=9,
    fontweight="bold",
    color=GRAY
)

fig.text(
    0.955, 0.904,
    f"{last_value:+.2f} °C",
    ha="right",
    fontsize=19,
    fontweight="bold",
    color=latest_color
)


# ------------------------------------------------------------
# Draw historical and recent panels
# ------------------------------------------------------------

panels = [
    (
        ax_history,
        roni,
        colors,
        "Full historical record",
        1.0
    ),
    (
        ax_recent,
        recent,
        recent_colors,
        "Last 20 years",
        1.5
    ),
]

for ax, data, bar_colors, heading, linewidth in panels:

    ax.set_facecolor("white")

    # Neutral reference band
    ax.axhspan(
        -THRESHOLD,
        THRESHOLD,
        color=LIGHT,
        alpha=0.30,
        zorder=0
    )

    # One bar per overlapping three-month season
    ax.bar(
        data.index,
        data.to_numpy(dtype=float),
        width=27,
        color=bar_colors,
        edgecolor="none",
        alpha=0.75,
        zorder=2
    )

    # RONI time series
    ax.plot(
        data.index,
        data.to_numpy(dtype=float),
        color=DARK,
        linewidth=linewidth,
        alpha=0.90,
        zorder=3
    )

    # Zero reference
    ax.axhline(
        0,
        color=GRAY,
        linewidth=0.85,
        zorder=4
    )

    # Warm threshold
    ax.axhline(
        THRESHOLD,
        color=RED,
        linestyle=(0, (5, 4)),
        linewidth=0.9,
        alpha=0.65,
        zorder=1
    )

    # Cold threshold
    ax.axhline(
        -THRESHOLD,
        color=BLUE,
        linestyle=(0, (5, 4)),
        linewidth=0.9,
        alpha=0.65,
        zorder=1
    )

    # Y axis
    ax.set_ylim(-y_limit, y_limit)

    ax.yaxis.set_major_locator(
        MultipleLocator(1.0)
    )

    ax.yaxis.set_major_formatter(
        FuncFormatter(
            lambda value, pos:
            f"{value:+.0f}" if value != 0 else "0"
        )
    )

    ax.set_ylabel(
        "RONI (°C)",
        color=GRAY,
        labelpad=11
    )

    # Panel title
    ax.set_title(
        heading,
        loc="left",
        fontsize=12.5,
        fontweight="bold",
        color=DARK,
        pad=14
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
# Historical time axis
# ------------------------------------------------------------

ax_history.set_xlim(
    roni.index.min() - pd.DateOffset(months=4),
    roni.index.max() + pd.DateOffset(months=4)
)

ax_history.xaxis.set_major_locator(
    mdates.YearLocator(10)
)

ax_history.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)


# ------------------------------------------------------------
# Recent time axis
# ------------------------------------------------------------

ax_recent.set_xlim(
    recent.index.min() - pd.DateOffset(months=2),
    recent.index.max() + pd.DateOffset(months=2)
)

ax_recent.xaxis.set_major_locator(
    mdates.YearLocator(2)
)

ax_recent.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

# Highlight latest observation
ax_recent.scatter(
    [last_date],
    [last_value],
    s=46,
    color=latest_color,
    edgecolor="white",
    linewidth=1.3,
    zorder=5
)


# ------------------------------------------------------------
# Legend
# ------------------------------------------------------------

handles = [
    Patch(
        facecolor=RED,
        alpha=0.75,
        label="RONI ≥ +0.5 °C"
    ),
    Patch(
        facecolor=BLUE,
        alpha=0.75,
        label="RONI ≤ −0.5 °C"
    ),
    Patch(
        facecolor=NEUTRAL,
        alpha=0.75,
        label="Between thresholds"
    ),
]

fig.legend(
    handles=handles,
    ncol=3,
    loc="lower left",
    bbox_to_anchor=(0.085, 0.151),
    frameon=False,
    fontsize=9,
    labelcolor=DARK,
    handlelength=1.5,
    columnspacing=2.2,
    borderaxespad=0
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.085, 0.123,
    "Colors show individual three-month RONI "
    "conditions, not officially classified ENSO episodes.",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.085, 0.098,
    "ENSO episodes require persistence across at least "
    "five overlapping seasons and supporting "
    "ocean–atmosphere evidence.",
    fontsize=8.5,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.085, 0.050,
    "Data: NOAA Climate Prediction Center | "
    "RONI based on ERSSTv6",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.955, 0.050,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.5,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "enso_historical_evolution.png"
svg_file = OUTPUT / "enso_historical_evolution.svg"

fig.savefig(
    png_file,
    dpi=250,
    facecolor="white"
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

print("\nENSO Historical Evolution completed.\n")
