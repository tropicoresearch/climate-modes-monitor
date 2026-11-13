
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 07: QBO Current Conditions
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA Climate Prediction Center (CORe)
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.ticker import MultipleLocator


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "qbo" / "qbo_indices.csv"
OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

MONTHS = 60

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
# Read data
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("QBO | Current Conditions\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 06_download_qbo_indices.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
).sort_index()

required = ["qbo_u30", "qbo_u50"]

if df.index.has_duplicates or df.index.hasnans:
    raise ValueError("Invalid dates in QBO dataset")

for column in required:

    if column not in df.columns:
        raise ValueError(f"Missing column: {column}")

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

    df[column] = df[column].replace(
        [np.inf, -np.inf],
        np.nan
    )

    if df[column].dropna().empty:
        raise ValueError(
            f"No valid observations for {column}"
        )


# ------------------------------------------------------------
# Select recent period
# ------------------------------------------------------------

latest_date = max(
    df[column].last_valid_index()
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
# Panel configuration
# ------------------------------------------------------------

PANELS = [
    {
        "column": "qbo_u30",
        "title": "Equatorial Zonal Wind | 30 hPa",
        "level": "30 hPa",
    },
    {
        "column": "qbo_u50",
        "title": "Equatorial Zonal Wind | 50 hPa",
        "level": "50 hPa",
    },
]


# ------------------------------------------------------------
# Create figure
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
    "QBO | Current Conditions",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Recent evolution of equatorial stratospheric "
    "zonal winds",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Draw panels
# ------------------------------------------------------------

for i, panel in enumerate(PANELS):

    column = panel["column"]
    series = recent[column]

    ax = fig.add_subplot(gs[i, 0])
    side = fig.add_subplot(gs[i, 1])

    side.axis("off")

    x = series.index
    y = series.to_numpy(dtype=float)

    valid = series.dropna()

    last_date = valid.index[-1]
    last_value = float(valid.iloc[-1])

    # Positive: eastward / westerly
    positive = np.isfinite(y) & (y >= 0)

    ax.fill_between(
        x,
        0,
        y,
        where=positive,
        interpolate=True,
        color=RED,
        alpha=0.22,
        zorder=2
    )

    # Negative: westward / easterly
    negative = np.isfinite(y) & (y < 0)

    ax.fill_between(
        x,
        0,
        y,
        where=negative,
        interpolate=True,
        color=BLUE,
        alpha=0.22,
        zorder=2
    )

    # Main wind series
    ax.plot(
        x,
        y,
        color=DARK,
        linewidth=2.1,
        solid_capstyle="round",
        zorder=4
    )

    # Zero wind
    ax.axhline(
        0,
        color=GRAY,
        linewidth=1.0,
        zorder=3
    )

    # Independent scale for each pressure level
    maximum = np.nanmax(np.abs(y))

    limit = max(
        10.0,
        np.ceil((maximum + 2.0) / 5.0) * 5.0
    )

    ax.set_ylim(-limit, limit)

    if last_value > 0:
        phase = "WESTERLY"
        marker_color = RED
    elif last_value < 0:
        phase = "EASTERLY"
        marker_color = BLUE
    else:
        phase = "ZERO WIND"
        marker_color = GRAY

    # Latest value marker
    ax.scatter(
        [last_date],
        [last_value],
        s=65,
        color=marker_color,
        edgecolor="white",
        linewidth=1.4,
        zorder=6
    )

    # Title
    ax.set_title(
        panel["title"],
        loc="left",
        fontsize=12.5,
        fontweight="bold",
        color=DARK,
        pad=18
    )

    ax.text(
        0.0,
        1.025,
        "Monthly mean zonal wind",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=GRAY
    )

    # Axes
    ax.set_ylabel(
        "Zonal wind (m/s)",
        color=GRAY,
        labelpad=10
    )

    ax.set_xlim(
        start_date - pd.Timedelta(days=12),
        latest_date + pd.DateOffset(months=1)
    )

    step = 10 if limit >= 25 else 5

    ax.yaxis.set_major_locator(
        MultipleLocator(step)
    )

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
    # Latest observation information
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
        f"{last_value:+.2f} m/s",
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=17,
        fontweight="bold",
        color=marker_color
    )

    side.text(
        0.13, 0.41,
        last_date.strftime("%b %Y"),
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=10,
        color=DARK
    )

    side.text(
        0.13, 0.25,
        phase,
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=8.5,
        fontweight="bold",
        color=marker_color
    )

    print(
        f"{column:10s} "
        f"{last_date:%Y-%m} "
        f"{last_value:+.2f} m/s "
        f"{phase}"
    )


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.117,
    "Positive winds indicate westerly (eastward) flow; "
    "negative winds indicate easterly (westward) flow.",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.09, 0.089,
    "Each pressure level has an independent vertical "
    "scale. Values represent zonal winds, not anomalies.",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.09, 0.046,
    "Data: NOAA Climate Prediction Center (CORe)",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.95, 0.046,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.5,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "qbo_current_conditions.png"
svg_file = OUTPUT / "qbo_current_conditions.svg"

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

print("\nQBO Current Conditions completed.\n")
