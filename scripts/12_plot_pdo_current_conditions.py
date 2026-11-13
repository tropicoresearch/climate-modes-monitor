
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 12: PDO Current Conditions
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

from matplotlib.ticker import MultipleLocator


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "pdo" / "pdo_indices.csv"
OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

MONTHS = 36
RECENT_YEARS = 20

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
# Read dataset
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("PDO | Current Conditions\n")

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

required = ["pdo", "pdo_12m"]

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError("Invalid PDO dates")

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
            f"No valid data in {column}"
        )


# ------------------------------------------------------------
# Select observation periods
# ------------------------------------------------------------

latest_date = df["pdo"].last_valid_index()

monthly_start = latest_date - pd.DateOffset(
    months=MONTHS - 1
)

recent_start = latest_date - pd.DateOffset(
    years=RECENT_YEARS
)

monthly = df.loc[
    monthly_start:latest_date,
    "pdo"
]

smoothed = df.loc[
    recent_start:latest_date,
    "pdo_12m"
]

if monthly.notna().sum() < 24:
    raise ValueError("Insufficient monthly PDO data")

if smoothed.notna().sum() < 120:
    raise ValueError("Insufficient smoothed PDO data")


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
    "PDO | Current Conditions",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Recent evolution of the Pacific Decadal "
    "Oscillation index",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Panel definitions
# ------------------------------------------------------------

PANELS = [
    {
        "series": monthly,
        "title": "Monthly PDO Index",
        "description": "Last 36 months",
        "summary": "Latest monthly value",
        "type": "monthly",
    },
    {
        "series": smoothed,
        "title": "PDO | 12-Month Running Mean",
        "description": "Last 20 years",
        "summary": "Latest 12-month mean",
        "type": "smoothed",
    },
]


# ------------------------------------------------------------
# Draw panels
# ------------------------------------------------------------

for i, panel in enumerate(PANELS):

    ax = fig.add_subplot(gs[i, 0])
    side = fig.add_subplot(gs[i, 1])

    side.axis("off")

    series = panel["series"]

    x = series.index
    y = series.to_numpy(dtype=float)

    valid = series.dropna()

    last_date = valid.index[-1]
    last_value = float(valid.iloc[-1])

    # Positive PDO
    ax.fill_between(
        x,
        0,
        y,
        where=np.isfinite(y) & (y > 0),
        interpolate=True,
        color=RED,
        alpha=0.21,
        zorder=2
    )

    # Negative PDO
    ax.fill_between(
        x,
        0,
        y,
        where=np.isfinite(y) & (y < 0),
        interpolate=True,
        color=BLUE,
        alpha=0.23,
        zorder=2
    )

    # Main curve
    ax.plot(
        x,
        y,
        color=DARK,
        linewidth=2.1,
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

    # Latest observation color
    if last_value > 0:
        phase = "POSITIVE"
        marker_color = RED
    elif last_value < 0:
        phase = "NEGATIVE"
        marker_color = BLUE
    else:
        phase = "ZERO"
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

    # Dynamic symmetric vertical scale
    finite = y[np.isfinite(y)]

    limit = max(
        1.0,
        np.ceil((np.max(np.abs(finite)) + 0.3) * 2) / 2
    )

    ax.set_ylim(-limit, limit)

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
        0.0,
        1.025,
        panel["description"],
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=GRAY
    )

    # Axes
    ax.set_ylabel(
        "PDO index",
        color=GRAY,
        labelpad=10
    )

    ax.set_xlim(
        x[0] - pd.DateOffset(months=2),
        x[-1] + pd.DateOffset(months=1)
    )

    if panel["type"] == "monthly":

        ax.xaxis.set_major_locator(
            mdates.MonthLocator(bymonth=[1, 7])
        )

        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%b %Y")
        )

        ax.yaxis.set_major_locator(
            MultipleLocator(1.0)
        )

    else:

        ax.xaxis.set_major_locator(
            mdates.YearLocator(4)
        )

        ax.xaxis.set_major_formatter(
            mdates.DateFormatter("%Y")
        )

        ax.yaxis.set_major_locator(
            MultipleLocator(0.5)
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
        f"{last_value:+.2f}",
        transform=side.transAxes,
        ha="left",
        va="top",
        fontsize=19,
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
        f"{panel['title']}: "
        f"{last_value:+.2f} "
        f"({last_date:%Y-%m})"
    )


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.117,
    "Positive and negative values describe the sign "
    "of the PDO index, not SST anomalies at individual locations.",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.09, 0.089,
    "The 12-month running mean is descriptive smoothing; "
    "it does not define an official PDO phase transition.",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.09, 0.046,
    "Data: NOAA NCEI | PDO derived from ERSSTv6",
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

png_file = OUTPUT / "pdo_current_conditions.png"
svg_file = OUTPUT / "pdo_current_conditions.svg"

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

print("\nPDO Current Conditions completed.\n")
