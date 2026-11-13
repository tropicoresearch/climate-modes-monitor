
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 08: QBO Historical Evolution
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Data source: NOAA Climate Prediction Center (CORe)
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
# Figure configuration
# ------------------------------------------------------------

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
print("QBO | Historical Evolution\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 06_download_qbo_indices.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
)

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError(
        "Missing or duplicate dates in QBO dataset"
    )

if (df.index.day != 1).any():
    raise ValueError(
        "Expected monthly timestamps on the first day"
    )

required = ["qbo_u30", "qbo_u50"]

for name in required:

    if name not in df.columns:
        raise ValueError(f"Missing column: {name}")

    df[name] = pd.to_numeric(
        df[name],
        errors="coerce"
    )

    df[name] = df[name].replace(
        [np.inf, -np.inf],
        np.nan
    )

    if df[name].notna().sum() < 400:
        raise ValueError(
            f"Insufficient valid observations in {name}"
        )

    if (df[name].dropna().abs() > 100).any():
        raise ValueError(
            f"Unrealistic zonal wind values in {name}"
        )

df = df.sort_index()

# Preserve missing months as gaps.
calendar = pd.date_range(
    df.index.min(),
    df.index.max(),
    freq="MS"
)

df = df.reindex(calendar)

first_date = df.index.min()

latest_date = max(
    df[name].last_valid_index()
    for name in required
)

print(
    f"Record: {first_date:%Y-%m} "
    f"to {latest_date:%Y-%m}"
)


# ------------------------------------------------------------
# Figure layout
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(13.4, 8.6),
    facecolor="white"
)

gs = fig.add_gridspec(
    nrows=2,
    ncols=2,
    left=0.09,
    right=0.95,
    bottom=0.18,
    top=0.79,
    hspace=0.39,
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
    "QBO | Historical Evolution",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Monthly equatorial zonal winds at "
    "30 and 50 hPa | 1979–present",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Panel definitions
# ------------------------------------------------------------

PANELS = [
    {
        "column": "qbo_u30",
        "title": "Equatorial Zonal Wind | 30 hPa",
    },
    {
        "column": "qbo_u50",
        "title": "Equatorial Zonal Wind | 50 hPa",
    },
]


# ------------------------------------------------------------
# Draw panels
# ------------------------------------------------------------

for i, panel in enumerate(PANELS):

    name = panel["column"]

    ax = fig.add_subplot(gs[i, 0])
    side = fig.add_subplot(gs[i, 1])

    side.axis("off")

    series = df[name]

    x = series.index
    y = series.to_numpy(dtype=float)

    valid = series.dropna()

    last_date = valid.index[-1]
    last_value = float(valid.iloc[-1])

    # Westerly winds
    ax.fill_between(
        x,
        0,
        y,
        where=np.isfinite(y) & (y > 0),
        interpolate=True,
        color=RED,
        alpha=0.19,
        zorder=2
    )

    # Easterly winds
    ax.fill_between(
        x,
        0,
        y,
        where=np.isfinite(y) & (y < 0),
        interpolate=True,
        color=BLUE,
        alpha=0.21,
        zorder=2
    )

    # Historical wind series
    ax.plot(
        x,
        y,
        color=DARK,
        linewidth=1.3,
        zorder=3
    )

    # Zero wind
    ax.axhline(
        0,
        color=GRAY,
        linewidth=0.9,
        zorder=4
    )

    # Independent vertical scale
    maximum = np.nanmax(np.abs(y))

    limit = max(
        10.0,
        np.ceil((maximum + 2.0) / 5.0) * 5.0
    )

    ax.set_ylim(-limit, limit)

    step = 10 if limit >= 25 else 5

    ax.yaxis.set_major_locator(
        MultipleLocator(step)
    )

    # Time axis
    ax.set_xlim(
        first_date - pd.DateOffset(months=6),
        latest_date + pd.DateOffset(months=6)
    )

    ax.xaxis.set_major_locator(
        mdates.YearLocator(5)
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%Y")
    )

    # Labels
    ax.set_ylabel(
        "Zonal wind (m/s)",
        color=GRAY,
        labelpad=10
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
        0.0,
        1.025,
        "Monthly mean zonal wind | Original data",
        transform=ax.transAxes,
        ha="left",
        va="bottom",
        fontsize=9,
        color=GRAY
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

    # Phase
    if last_value > 0:
        phase = "WESTERLY"
        phase_color = RED
    elif last_value < 0:
        phase = "EASTERLY"
        phase_color = BLUE
    else:
        phase = "ZERO WIND"
        phase_color = GRAY

    # Latest observation marker
    ax.scatter(
        [last_date],
        [last_value],
        s=55,
        color=phase_color,
        edgecolor="white",
        linewidth=1.2,
        zorder=5
    )

    # --------------------------------------------------------
    # Right information panel
    # --------------------------------------------------------

    side.plot(
        [0.02, 0.02],
        [0.12, 0.82],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.2
    )

    side.text(
        0.13,
        0.80,
        "LATEST OBSERVATION",
        transform=side.transAxes,
        va="top",
        fontsize=8,
        fontweight="bold",
        color=GRAY
    )

    side.text(
        0.13,
        0.60,
        f"{last_value:+.2f} m/s",
        transform=side.transAxes,
        va="top",
        fontsize=16,
        fontweight="bold",
        color=phase_color
    )

    side.text(
        0.13,
        0.42,
        last_date.strftime("%b %Y"),
        transform=side.transAxes,
        va="top",
        fontsize=10,
        color=DARK
    )

    side.text(
        0.13,
        0.26,
        phase,
        transform=side.transAxes,
        va="top",
        fontsize=8.5,
        fontweight="bold",
        color=phase_color
    )

    print(
        f"{name}: {len(valid)} months | "
        f"latest {last_date:%Y-%m}: "
        f"{last_value:+.2f} m/s ({phase})"
    )


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.09, 0.118,
    "Red: westerly (eastward) winds. "
    "Blue: easterly (westward) winds. "
    "Each pressure level uses an independent vertical scale.",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.09, 0.090,
    "Monthly mean winds, not anomalies. "
    "A wind sign at one level does not describe "
    "the complete vertical structure of the QBO.",
    fontsize=8.4,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

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

png_file = OUTPUT / "qbo_historical_evolution.png"
svg_file = OUTPUT / "qbo_historical_evolution.svg"

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

print("\nQBO Historical Evolution completed.\n")
