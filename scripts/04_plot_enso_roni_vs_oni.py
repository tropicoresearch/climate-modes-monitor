
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 04: ENSO | RONI vs. ONI
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

from matplotlib.ticker import MultipleLocator, FuncFormatter
from matplotlib.lines import Line2D


# ------------------------------------------------------------
# Paths and settings
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "enso" / "enso_indices.csv"
OUTPUT = ROOT / "docs" / "figures"

OUTPUT.mkdir(parents=True, exist_ok=True)

RECENT_YEARS = 20
THRESHOLD = 0.5

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
# Read and align overlapping seasonal indices
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("ENSO | RONI vs. ONI\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 01_download_enso_indices.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
)

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError(
        "Missing or duplicate dates in ENSO dataset"
    )

for column in ["roni", "oni"]:

    if column not in df.columns:
        raise ValueError(f"Missing column: {column}")

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )

# Both indices represent overlapping three-month seasons.
# Dates correspond to the central month of each season.

shared = (
    df[["roni", "oni"]]
    .sort_index()
    .dropna()
)

if len(shared) < 600:
    raise ValueError(
        "Insufficient paired RONI/ONI observations"
    )

if (shared.index.day != 1).any():
    raise ValueError(
        "Expected first-of-month timestamps"
    )

# Preserve missing periods as gaps.

calendar = pd.date_range(
    shared.index.min(),
    shared.index.max(),
    freq="MS"
)

comparison = shared.reindex(calendar)
comparison.index.name = "date"

comparison["difference"] = (
    comparison["roni"] - comparison["oni"]
)


# ------------------------------------------------------------
# Latest common observation
# ------------------------------------------------------------

last_date = shared.index.max()

last_roni = float(shared.loc[last_date, "roni"])
last_oni = float(shared.loc[last_date, "oni"])

last_diff = last_roni - last_oni

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

last_season = (
    f"{SEASONS[last_date.month]} {last_date.year}"
)


# ------------------------------------------------------------
# Historical statistics
# ------------------------------------------------------------

correlation = shared["roni"].corr(
    shared["oni"]
)

differences = shared["roni"] - shared["oni"]

mean_difference = differences.mean()
mean_absolute_difference = differences.abs().mean()

recent_start = (
    last_date
    - pd.DateOffset(years=RECENT_YEARS)
    + pd.DateOffset(months=1)
)

recent = comparison.loc[recent_start:last_date]

print(
    f"Common record: "
    f"{shared.index.min():%Y-%m} to {last_date:%Y-%m}"
)

print(f"Paired seasons: {len(shared)}")

print(
    f"Missing seasons: "
    f"{comparison['roni'].isna().sum()}"
)

print(f"Latest shared season: {last_season}")

print(f"RONI: {last_roni:+.2f} °C")
print(f"ONI:  {last_oni:+.2f} °C")
print(f"RONI - ONI: {last_diff:+.2f} °C")

print(f"Pearson correlation: {correlation:.3f}")

print(
    f"Mean difference: "
    f"{mean_difference:+.3f} °C"
)

print(
    f"Mean absolute difference: "
    f"{mean_absolute_difference:.3f} °C"
)


# ------------------------------------------------------------
# Axis limits
# ------------------------------------------------------------

extreme = np.nanmax(
    np.abs(
        comparison[["roni", "oni"]].to_numpy()
    )
)

index_limit = max(
    2.0,
    np.ceil((extreme + 0.3) * 2) / 2
)

diff_extreme = np.nanmax(
    np.abs(
        comparison["difference"].to_numpy()
    )
)

diff_limit = max(
    0.5,
    np.ceil((diff_extreme + 0.1) * 4) / 4
)


# ------------------------------------------------------------
# Figure layout
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.3, 10.4),
    facecolor="white"
)

gs = fig.add_gridspec(
    nrows=3,
    ncols=2,
    left=0.087,
    right=0.957,
    bottom=0.177,
    top=0.761,
    height_ratios=[1.1, 1.1, 0.95],
    width_ratios=[5.25, 1.18],
    hspace=0.60,
    wspace=0.06,
)

axes = [
    fig.add_subplot(gs[i, 0])
    for i in range(3)
]

side_axes = [
    fig.add_subplot(gs[i, 1])
    for i in range(3)
]


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

fig.text(
    0.087, 0.955,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    fontsize=9,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.087, 0.910,
    "ENSO | RONI vs. ONI",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.087, 0.866,
    "Comparing relative and conventional "
    "tropical Pacific SST indices",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Legend
# ------------------------------------------------------------

legend_lines = [
    Line2D(
        [0], [0],
        color=BLUE,
        lw=2.5,
        label="RONI"
    ),
    Line2D(
        [0], [0],
        color=RED,
        lw=2.2,
        label="ONI"
    ),
]

fig.legend(
    handles=legend_lines,
    loc="upper left",
    bbox_to_anchor=(0.087, 0.828),
    frameon=False,
    ncol=2,
    fontsize=10,
    labelcolor=DARK,
    borderaxespad=0,
    handlelength=2.5,
    columnspacing=2.5,
)


# ------------------------------------------------------------
# Common axis styling
# ------------------------------------------------------------

for ax in axes:

    ax.set_facecolor("white")

    ax.grid(
        axis="y",
        color=LIGHT,
        linewidth=0.8,
        alpha=0.95
    )

    ax.grid(
        axis="x",
        color=LIGHT,
        linewidth=0.6,
        alpha=0.55
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
        "Anomaly (°C)",
        color=GRAY,
        labelpad=11
    )

    ax.yaxis.set_major_formatter(
        FuncFormatter(
            lambda value, pos:
            f"{value:+.1f}"
            if abs(value) > 0.001 else "0"
        )
    )


# ------------------------------------------------------------
# RONI and ONI comparisons
# ------------------------------------------------------------

panels = [
    (
        axes[0],
        comparison,
        "Historical comparison | 1950–present"
    ),
    (
        axes[1],
        recent,
        "Recent evolution | Last 20 years"
    ),
]

for ax, series, title in panels:

    # Neutral reference band
    ax.axhspan(
        -THRESHOLD,
        THRESHOLD,
        color=LIGHT,
        alpha=0.32,
        zorder=0
    )

    # Reference thresholds
    ax.axhline(
        THRESHOLD,
        color=GRAY,
        linestyle=(0, (4, 4)),
        linewidth=0.75,
        alpha=0.6
    )

    ax.axhline(
        -THRESHOLD,
        color=GRAY,
        linestyle=(0, (4, 4)),
        linewidth=0.75,
        alpha=0.6
    )

    ax.axhline(
        0,
        color=GRAY,
        linewidth=0.8
    )

    # RONI
    ax.plot(
        series.index,
        series["roni"],
        color=BLUE,
        linewidth=2.1,
        zorder=3
    )

    # ONI
    ax.plot(
        series.index,
        series["oni"],
        color=RED,
        linewidth=1.8,
        alpha=0.9,
        zorder=2
    )

    # Latest common observations
    ax.scatter(
        [last_date],
        [last_roni],
        s=46,
        color=BLUE,
        edgecolor="white",
        linewidth=1.0,
        zorder=5
    )

    ax.scatter(
        [last_date],
        [last_oni],
        s=46,
        color=RED,
        edgecolor="white",
        linewidth=1.0,
        zorder=5
    )

    ax.set_ylim(
        -index_limit,
        index_limit
    )

    ax.yaxis.set_major_locator(
        MultipleLocator(1.0)
    )

    ax.set_title(
        title,
        loc="left",
        fontsize=12.5,
        fontweight="bold",
        color=DARK,
        pad=12
    )


# ------------------------------------------------------------
# Historical time axis
# ------------------------------------------------------------

axes[0].set_xlim(
    comparison.index.min()
    - pd.DateOffset(months=4),

    comparison.index.max()
    + pd.DateOffset(months=4)
)

axes[0].xaxis.set_major_locator(
    mdates.YearLocator(10)
)

axes[0].xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)


# ------------------------------------------------------------
# Recent time axis
# ------------------------------------------------------------

axes[1].set_xlim(
    recent.index.min()
    - pd.DateOffset(months=2),

    last_date
    + pd.DateOffset(months=2)
)

axes[1].xaxis.set_major_locator(
    mdates.YearLocator(4)
)

axes[1].xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)


# ------------------------------------------------------------
# Historical difference: RONI minus ONI
# ------------------------------------------------------------

ax = axes[2]

delta = comparison["difference"]
delta_values = delta.to_numpy(dtype=float)

# Positive difference
ax.fill_between(
    delta.index,
    0,
    delta_values,
    where=(delta >= 0).fillna(False).to_numpy(),
    color=RED,
    alpha=0.29,
    interpolate=True,
    zorder=2
)

# Negative difference
ax.fill_between(
    delta.index,
    0,
    delta_values,
    where=(delta < 0).fillna(False).to_numpy(),
    color=BLUE,
    alpha=0.29,
    interpolate=True,
    zorder=2
)

# Difference curve
ax.plot(
    delta.index,
    delta_values,
    color=DARK,
    linewidth=1.3,
    zorder=3
)

ax.axhline(
    0,
    color=GRAY,
    linewidth=0.85,
    zorder=4
)

# Latest difference
ax.scatter(
    [last_date],
    [last_diff],
    s=45,
    color=RED if last_diff >= 0 else BLUE,
    edgecolor="white",
    linewidth=1.0,
    zorder=5
)

ax.set_ylim(
    -diff_limit,
    diff_limit
)

ax.set_xlim(
    comparison.index.min()
    - pd.DateOffset(months=4),

    comparison.index.max()
    + pd.DateOffset(months=4)
)

ax.set_ylabel(
    "Difference (°C)",
    color=GRAY,
    labelpad=11
)

ax.set_title(
    "Historical difference | RONI − ONI",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=12
)

ax.xaxis.set_major_locator(
    mdates.YearLocator(10)
)

ax.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

ax.yaxis.set_major_locator(
    MultipleLocator(
        0.5 if diff_limit > 1.0 else 0.25
    )
)

ax.yaxis.set_major_formatter(
    FuncFormatter(
        lambda value, pos:
        f"{value:+.2f}"
        if abs(value) > 0.001 else "0"
    )
)


# ------------------------------------------------------------
# Side panels
# ------------------------------------------------------------

for side in side_axes:

    side.axis("off")

    side.plot(
        [0.03, 0.03],
        [0.03, 0.95],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.15
    )


# ------------------------------------------------------------
# Latest observations
# ------------------------------------------------------------

side = side_axes[0]

side.text(
    0.14, 0.94,
    "LATEST SHARED SEASON",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=8,
    fontweight="bold",
    color=GRAY
)

side.text(
    0.14, 0.72,
    last_season,
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=12,
    fontweight="bold",
    color=DARK
)

side.text(
    0.14, 0.51,
    f"RONI   {last_roni:+.2f} °C",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=10,
    fontweight="bold",
    color=BLUE
)

side.text(
    0.14, 0.33,
    f"ONI      {last_oni:+.2f} °C",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=10,
    fontweight="bold",
    color=RED
)

side.text(
    0.14, 0.15,
    f"Δ           {last_diff:+.2f} °C",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=10,
    fontweight="bold",
    color=DARK
)


# ------------------------------------------------------------
# Recent period information
# ------------------------------------------------------------

side = side_axes[1]

side.text(
    0.14, 0.94,
    "RECENT PERIOD",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=8,
    fontweight="bold",
    color=GRAY
)

side.text(
    0.14, 0.71,
    f"{recent.index.min().year}–{last_date.year}",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=12,
    fontweight="bold",
    color=DARK
)

side.text(
    0.14, 0.46,
    "Same overlapping\n"
    "three-month seasons\n"
    "for both indices",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=9,
    color=GRAY,
    linespacing=1.6
)


# ------------------------------------------------------------
# Historical statistics
# ------------------------------------------------------------

side = side_axes[2]

side.text(
    0.14, 0.94,
    "FULL-RECORD METRICS",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=8,
    fontweight="bold",
    color=GRAY
)

side.text(
    0.14, 0.70,
    f"Correlation    {correlation:.3f}",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=9.5,
    color=DARK
)

side.text(
    0.14, 0.48,
    f"Mean Δ         {mean_difference:+.2f} °C",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=9.5,
    color=DARK
)

side.text(
    0.14, 0.26,
    f"Mean |Δ|     {mean_absolute_difference:.2f} °C",
    transform=side.transAxes,
    ha="left",
    va="top",
    fontsize=9.5,
    color=DARK
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.087, 0.119,
    "RONI and ONI are overlapping three-month means, "
    "aligned by central month. "
    "The difference is RONI minus ONI.",
    fontsize=8.6,
    color=GRAY
)

fig.text(
    0.087, 0.092,
    "RONI uses a relative tropical-ocean SST baseline "
    "and variance adjustment; "
    "ONI uses centered 30-year climatologies.",
    fontsize=8.6,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.087, 0.048,
    "Data: NOAA Climate Prediction Center (ERSSTv6)",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.957, 0.048,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.5,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "enso_roni_vs_oni.png"
svg_file = OUTPUT / "enso_roni_vs_oni.svg"

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

print("\nENSO RONI vs. ONI completed.\n")
