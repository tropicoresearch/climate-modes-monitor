
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 17: AMV Current Conditions
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Data source: NOAA NCEI / ERSSTv6
#
# Observed North Atlantic SST anomalies.
# Not an estimate of internally generated AMV.
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

INPUT = (
    ROOT / "data" / "amv" /
    "north_atlantic_ssta.csv"
)

OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

MONTHS = 60
HISTORICAL_START = "1900-01-01"

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
print("AMV | Current Conditions\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 16_download_amv_index.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
).sort_index()

required = [
    "na_ssta",
    "na_ssta_12m",
    "na_ssta_120m"
]

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError("Invalid observation dates")

for column in required:

    if column not in df.columns:
        raise ValueError(
            f"Missing column: {column}"
        )

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

    if df[column].dropna().empty:
        raise ValueError(
            f"No valid data in {column}"
        )


# ------------------------------------------------------------
# Observation periods
# ------------------------------------------------------------

latest_date = df["na_ssta"].last_valid_index()

recent_start = latest_date - pd.DateOffset(
    months=MONTHS - 1
)

recent = df.loc[
    recent_start:latest_date
]

historical = df.loc[
    HISTORICAL_START:latest_date
]

if recent["na_ssta"].notna().sum() < 36:
    raise ValueError(
        "Insufficient recent observations"
    )

if historical["na_ssta_120m"].notna().sum() < 500:
    raise ValueError(
        "Insufficient multidecadal observations"
    )


# ------------------------------------------------------------
# Latest values
# ------------------------------------------------------------

latest_monthly = df["na_ssta"].dropna()
latest_12m = df["na_ssta_12m"].dropna()
latest_120m = df["na_ssta_120m"].dropna()

monthly_date = latest_monthly.index[-1]
monthly_value = float(latest_monthly.iloc[-1])

mean12_date = latest_12m.index[-1]
mean12_value = float(latest_12m.iloc[-1])

mean120_date = latest_120m.index[-1]
mean120_value = float(latest_120m.iloc[-1])

print(
    f"Monthly: {monthly_value:+.2f} °C "
    f"({monthly_date:%b %Y})"
)

print(
    f"12-month: {mean12_value:+.2f} °C "
    f"({mean12_date:%b %Y})"
)

print(
    f"120-month: {mean120_value:+.2f} °C "
    f"({mean120_date:%b %Y})"
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
    hspace=0.41,
    wspace=0.06,
    width_ratios=[5.2, 1.15]
)

ax_recent = fig.add_subplot(gs[0, 0])
ax_history = fig.add_subplot(gs[1, 0])

side_recent = fig.add_subplot(gs[0, 1])
side_history = fig.add_subplot(gs[1, 1])

side_recent.axis("off")
side_history.axis("off")


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
    "AMV | Current Conditions",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Observed North Atlantic sea surface "
    "temperature variability",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Shared axes style
# ------------------------------------------------------------

for ax in [ax_recent, ax_history]:

    ax.set_facecolor("white")

    ax.axhline(
        0,
        color=GRAY,
        linewidth=1.0,
        zorder=4
    )

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

    ax.set_ylabel(
        "SST anomaly (°C)",
        color=GRAY,
        labelpad=10
    )


# ------------------------------------------------------------
# Panel 1: Recent SST anomalies
# ------------------------------------------------------------

x = recent.index
y = recent["na_ssta"].to_numpy(dtype=float)

finite = np.isfinite(y)

ax_recent.fill_between(
    x,
    0,
    y,
    where=finite & (y > 0),
    interpolate=True,
    color=RED,
    alpha=0.20,
    zorder=2
)

ax_recent.fill_between(
    x,
    0,
    y,
    where=finite & (y < 0),
    interpolate=True,
    color=BLUE,
    alpha=0.21,
    zorder=2
)

ax_recent.plot(
    x,
    y,
    color=DARK,
    linewidth=2.0,
    label="Monthly SSTA",
    zorder=4
)

ax_recent.plot(
    x,
    recent["na_ssta_12m"],
    color=RED,
    linewidth=1.6,
    linestyle=(0, (5, 3)),
    label="12-month mean",
    zorder=5
)

monthly_color = (
    RED if monthly_value > 0
    else BLUE if monthly_value < 0
    else GRAY
)

ax_recent.scatter(
    [monthly_date],
    [monthly_value],
    s=65,
    color=monthly_color,
    edgecolor="white",
    linewidth=1.4,
    zorder=7
)

recent_extreme = np.nanmax(
    np.abs(
        recent[
            ["na_ssta", "na_ssta_12m"]
        ].to_numpy(dtype=float)
    )
)

recent_limit = max(
    0.5,
    np.ceil(
        (recent_extreme + 0.15) * 4
    ) / 4
)

ax_recent.set_ylim(
    -recent_limit,
    recent_limit
)

ax_recent.set_xlim(
    x[0] - pd.DateOffset(months=1),
    x[-1] + pd.DateOffset(months=1)
)

ax_recent.set_title(
    "North Atlantic SST Anomalies",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=18
)

ax_recent.text(
    0,
    1.025,
    "Monthly observations | Last 60 months",
    transform=ax_recent.transAxes,
    fontsize=9,
    color=GRAY,
    va="bottom"
)

ax_recent.xaxis.set_major_locator(
    mdates.YearLocator(1)
)

ax_recent.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

ax_recent.yaxis.set_major_locator(
    MultipleLocator(
        0.5 if recent_limit >= 1.5 else 0.25
    )
)

ax_recent.legend(
    loc="upper left",
    fontsize=8,
    frameon=False,
    ncol=2,
    labelcolor=GRAY
)


# ------------------------------------------------------------
# Panel 2: Multidecadal variability
# ------------------------------------------------------------

x = historical.index

y = historical[
    "na_ssta_120m"
].to_numpy(dtype=float)

finite = np.isfinite(y)

ax_history.fill_between(
    x,
    0,
    y,
    where=finite & (y > 0),
    interpolate=True,
    color=RED,
    alpha=0.20,
    zorder=2
)

ax_history.fill_between(
    x,
    0,
    y,
    where=finite & (y < 0),
    interpolate=True,
    color=BLUE,
    alpha=0.22,
    zorder=2
)

ax_history.plot(
    x,
    y,
    color=DARK,
    linewidth=2.1,
    zorder=4
)

history_color = (
    RED if mean120_value > 0
    else BLUE if mean120_value < 0
    else GRAY
)

ax_history.scatter(
    [mean120_date],
    [mean120_value],
    s=65,
    color=history_color,
    edgecolor="white",
    linewidth=1.4,
    zorder=6
)

history_extreme = np.nanmax(
    np.abs(y)
)

history_limit = max(
    0.5,
    np.ceil(
        (history_extreme + 0.10) * 4
    ) / 4
)

ax_history.set_ylim(
    -history_limit,
    history_limit
)

ax_history.set_xlim(
    x[0] - pd.DateOffset(years=2),
    x[-1] + pd.DateOffset(years=2)
)

ax_history.set_title(
    "Multidecadal Perspective",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=18
)

ax_history.text(
    0,
    1.025,
    "120-month trailing mean | Since 1900",
    transform=ax_history.transAxes,
    fontsize=9,
    color=GRAY,
    va="bottom"
)

ax_history.xaxis.set_major_locator(
    mdates.YearLocator(20)
)

ax_history.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

ax_history.yaxis.set_major_locator(
    MultipleLocator(0.25)
)


# ------------------------------------------------------------
# Right-side information
# ------------------------------------------------------------

for side in [side_recent, side_history]:

    side.plot(
        [0.02, 0.02],
        [0.12, 0.82],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.2
    )


# Recent indicator
side_recent.text(
    0.13, 0.80,
    "LATEST OBSERVATION",
    transform=side_recent.transAxes,
    fontsize=8,
    fontweight="bold",
    color=GRAY,
    va="top"
)

side_recent.text(
    0.13, 0.60,
    f"{monthly_value:+.2f} °C",
    transform=side_recent.transAxes,
    fontsize=17,
    fontweight="bold",
    color=monthly_color,
    va="top"
)

side_recent.text(
    0.13, 0.41,
    monthly_date.strftime("%b %Y"),
    transform=side_recent.transAxes,
    fontsize=10,
    color=DARK,
    va="top"
)

side_recent.text(
    0.13, 0.25,
    f"12-month: {mean12_value:+.2f} °C",
    transform=side_recent.transAxes,
    fontsize=8.5,
    color=GRAY,
    va="top"
)


# Multidecadal indicator
side_history.text(
    0.13, 0.80,
    "LATEST 10-YEAR MEAN",
    transform=side_history.transAxes,
    fontsize=8,
    fontweight="bold",
    color=GRAY,
    va="top"
)

side_history.text(
    0.13, 0.60,
    f"{mean120_value:+.2f} °C",
    transform=side_history.transAxes,
    fontsize=17,
    fontweight="bold",
    color=history_color,
    va="top"
)

side_history.text(
    0.13, 0.41,
    mean120_date.strftime("%b %Y"),
    transform=side_history.transAxes,
    fontsize=10,
    color=DARK,
    va="top"
)

side_history.text(
    0.13, 0.25,
    "Trailing average",
    transform=side_history.transAxes,
    fontsize=8.5,
    color=GRAY,
    va="top"
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.09, 0.117,
    "Positive and negative values represent North Atlantic "
    "SST anomalies, not independently diagnosed AMV phases.",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.09, 0.089,
    "Observed SST anomalies include externally forced "
    "changes. The trailing 10-year average is "
    "descriptive and lags transitions.",
    fontsize=8.4,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.046,
    "Data: NOAA NCEI | North Atlantic SSTA (ERSSTv6)",
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

png_file = OUTPUT / "amv_current_conditions.png"
svg_file = OUTPUT / "amv_current_conditions.svg"

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

print("\nAMV Current Conditions completed.\n")
