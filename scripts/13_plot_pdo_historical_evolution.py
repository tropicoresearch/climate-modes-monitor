
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 13: PDO Historical Evolution
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Data source: NOAA NCEI / ERSSTv6
# ============================================================

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "pdo" / "pdo_indices.csv"
OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

MODERN_START = "1950-01-01"
DECADAL_MONTHS = 120

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
print("PDO | Historical Evolution\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 11_download_pdo_index.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
).sort_index()

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError("Invalid or duplicate PDO dates")

if (df.index.day != 1).any():
    raise ValueError(
        "Expected monthly first-of-month timestamps"
    )

if "pdo" not in df.columns or "pdo_12m" not in df.columns:
    raise ValueError(
        "Expected pdo and pdo_12m columns"
    )

for column in ["pdo", "pdo_12m"]:

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

    if (df[column].dropna().abs() > 20).any():
        raise ValueError(
            f"Unrealistic values in {column}"
        )

if df["pdo"].notna().sum() < 1500:
    raise ValueError(
        "PDO historical record is unexpectedly short"
    )


# ------------------------------------------------------------
# Preserve monthly calendar
# ------------------------------------------------------------

calendar = pd.date_range(
    df.index.min(),
    df.index.max(),
    freq="MS"
)

df = df.reindex(calendar)
df.index.name = "date"


# ------------------------------------------------------------
# Calculate running means
# ------------------------------------------------------------

# Complete calendar windows are required.
# Missing months are never interpolated.

df["pdo_12m"] = (
    df["pdo"]
    .rolling(
        window=12,
        min_periods=12
    )
    .mean()
)

df["pdo_120m"] = (
    df["pdo"]
    .rolling(
        window=DECADAL_MONTHS,
        min_periods=DECADAL_MONTHS
    )
    .mean()
)


# ------------------------------------------------------------
# Latest observations
# ------------------------------------------------------------

last_month = df["pdo"].last_valid_index()
last_12m = df["pdo_12m"].last_valid_index()
last_120m = df["pdo_120m"].last_valid_index()

if last_12m is None or last_120m is None:
    raise ValueError(
        "Not enough complete months for smoothing"
    )

latest_pdo = float(df.loc[last_month, "pdo"])
latest_12m = float(df.loc[last_12m, "pdo_12m"])
latest_120m = float(df.loc[last_120m, "pdo_120m"])

print(
    f"Record: {df.index.min():%Y-%m} "
    f"to {last_month:%Y-%m}"
)

print(
    f"Latest monthly: {latest_pdo:+.2f} "
    f"({last_month:%b %Y})"
)

print(
    f"Latest 12-month: {latest_12m:+.2f} "
    f"({last_12m:%b %Y})"
)

print(
    f"Latest 120-month: {latest_120m:+.2f} "
    f"({last_120m:%b %Y})"
)


# ------------------------------------------------------------
# Modern record
# ------------------------------------------------------------

modern = df.loc[MODERN_START:last_month]

if modern["pdo"].notna().sum() < 500:
    raise ValueError(
        "Insufficient post-1950 observations"
    )


# ------------------------------------------------------------
# Figure layout
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.2, 10.1),
    facecolor="white"
)

gs = fig.add_gridspec(
    nrows=3,
    ncols=2,
    left=0.09,
    right=0.955,
    bottom=0.188,
    top=0.787,
    hspace=0.62,
    wspace=0.06,
    height_ratios=[1.0, 1.0, 0.90],
    width_ratios=[5.2, 1.15]
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
    0.09, 0.954,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    fontsize=9,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.09, 0.909,
    "PDO | Historical Evolution",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.868,
    "Pacific Decadal Oscillation | "
    "Monthly, annual-scale, and decadal perspectives",
    fontsize=10.5,
    color=GRAY
)


# ------------------------------------------------------------
# Panel definitions
# ------------------------------------------------------------

PANELS = [
    {
        "axis": axes[0],
        "data": df.loc[:last_month],
        "title": "Full Historical Record",
        "description": "Monthly PDO and 12-month running mean",
        "line": "pdo_12m",
        "year_step": 25,
        "show_monthly": True,
    },
    {
        "axis": axes[1],
        "data": modern,
        "title": "Modern Record | Since 1950",
        "description": "Monthly PDO and 12-month running mean",
        "line": "pdo_12m",
        "year_step": 10,
        "show_monthly": True,
    },
    {
        "axis": axes[2],
        "data": df.loc[:last_120m],
        "title": "Decadal Perspective",
        "description": "120-month trailing running mean",
        "line": "pdo_120m",
        "year_step": 25,
        "show_monthly": False,
    },
]


# ------------------------------------------------------------
# Draw panels
# ------------------------------------------------------------

for panel in PANELS:

    ax = panel["axis"]
    subset = panel["data"]

    smooth = subset[panel["line"]]

    x = subset.index
    y = smooth.to_numpy(dtype=float)

    finite = np.isfinite(y)

    ax.set_facecolor("white")

    # Positive running mean
    ax.fill_between(
        x,
        0,
        y,
        where=finite & (y > 0),
        color=RED,
        alpha=0.19,
        interpolate=True,
        zorder=2
    )

    # Negative running mean
    ax.fill_between(
        x,
        0,
        y,
        where=finite & (y < 0),
        color=BLUE,
        alpha=0.21,
        interpolate=True,
        zorder=2
    )

    # Monthly series
    if panel["show_monthly"]:

        ax.plot(
            x,
            subset["pdo"],
            color=GRAY,
            linewidth=0.65,
            alpha=0.40,
            zorder=3
        )

    # Smoothed series
    ax.plot(
        x,
        smooth,
        color=DARK,
        linewidth=(
            1.65
            if panel["show_monthly"]
            else 2.15
        ),
        zorder=4
    )

    # Zero reference
    ax.axhline(
        0,
        color=GRAY,
        linewidth=0.9,
        zorder=5
    )

    # Independent symmetric vertical range
    if panel["show_monthly"]:
        limit_source = subset["pdo"]
    else:
        limit_source = smooth

    extreme = float(
        limit_source.abs().max()
    )

    limit = max(
        2.0 if panel["show_monthly"] else 0.5,
        np.ceil((extreme + 0.20) * 2) / 2
    )

    ax.set_ylim(-limit, limit)

    ax.yaxis.set_major_locator(
        MultipleLocator(
            0.5 if limit <= 2 else 1.0
        )
    )

    # Time axis
    ax.set_xlim(
        subset.index.min()
        - pd.DateOffset(months=5),

        subset.index.max()
        + pd.DateOffset(months=5)
    )

    ax.xaxis.set_major_locator(
        mdates.YearLocator(
            panel["year_step"]
        )
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    # Labels
    ax.set_ylabel(
        "PDO index",
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
# Right-side information panels
# ------------------------------------------------------------

for side in sides:

    side.axis("off")

    side.plot(
        [0.02, 0.02],
        [0.10, 0.86],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.2
    )


SUMMARY = [
    (
        "LATEST MONTHLY PDO",
        latest_pdo,
        last_month,
        "Monthly index"
    ),
    (
        "LATEST 12-MONTH MEAN",
        latest_12m,
        last_12m,
        "Trailing mean"
    ),
    (
        "LATEST 10-YEAR MEAN",
        latest_120m,
        last_120m,
        "Trailing mean"
    ),
]


for side, (label, value, date, note) in zip(
    sides, SUMMARY
):

    if value > 0:
        color = RED
    elif value < 0:
        color = BLUE
    else:
        color = GRAY

    side.text(
        0.13, 0.82,
        label,
        transform=side.transAxes,
        va="top",
        fontsize=8,
        fontweight="bold",
        color=GRAY
    )

    side.text(
        0.13, 0.59,
        f"{value:+.2f}",
        transform=side.transAxes,
        va="top",
        fontsize=20,
        fontweight="bold",
        color=color
    )

    side.text(
        0.13, 0.40,
        date.strftime("%b %Y"),
        transform=side.transAxes,
        va="top",
        fontsize=10,
        color=DARK
    )

    side.text(
        0.13, 0.23,
        note,
        transform=side.transAxes,
        va="top",
        fontsize=9,
        color=GRAY
    )


# ------------------------------------------------------------
# Legend
# ------------------------------------------------------------

handles = [
    Line2D(
        [0], [0],
        color=GRAY,
        alpha=0.6,
        linewidth=1,
        label="Monthly PDO"
    ),
    Line2D(
        [0], [0],
        color=DARK,
        linewidth=2.0,
        label="Running mean (12 or 120 months)"
    ),
]

fig.legend(
    handles=handles,
    loc="lower left",
    bbox_to_anchor=(0.09, 0.145),
    ncol=2,
    frameon=False,
    fontsize=9,
    labelcolor=DARK,
    handlelength=2.5,
    columnspacing=2,
    borderaxespad=0
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.09, 0.116,
    "Colored areas show the sign of each running mean; "
    "the 10-year curve is descriptive smoothing, "
    "not a separate PDO index.",
    fontsize=8.3,
    color=GRAY
)

fig.text(
    0.09, 0.089,
    "Early reconstructed SSTs have greater uncertainty; "
    "NOAA notes that ERSST is more reliable "
    "after the 1940s.",
    fontsize=8.3,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.044,
    "Data: NOAA NCEI | PDO derived from ERSSTv6",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.955, 0.044,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.4,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "pdo_historical_evolution.png"
svg_file = OUTPUT / "pdo_historical_evolution.svg"

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

print("\nPDO Historical Evolution completed.\n")
