
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 22: IOD Current Conditions
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA Climate Prediction Center / ERSSTv6
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

INPUT = ROOT / "data" / "iod" / "iod_indices.csv"
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
print("IOD | Current Conditions\n")

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
    raise ValueError("Invalid observation dates")

if (df.index.day != 1).any():
    raise ValueError(
        "Expected first-of-month timestamps"
    )

required = ["dmi", "wtio", "setio"]

for name in required:

    if name not in df.columns:
        raise ValueError(f"Missing column: {name}")

    df[name] = pd.to_numeric(
        df[name],
        errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

    if df[name].dropna().empty:
        raise ValueError(
            f"No valid observations in {name}"
        )


# ------------------------------------------------------------
# Latest common observation
# ------------------------------------------------------------

common = df[required].dropna()

if common.empty:
    raise ValueError(
        "No common DMI and component observations"
    )

latest_date = common.index[-1]

start_date = latest_date - pd.DateOffset(
    months=MONTHS - 1
)

calendar = pd.date_range(
    start=start_date,
    end=latest_date,
    freq="MS"
)

recent = df.reindex(calendar)

if recent["dmi"].notna().sum() < 36:
    raise ValueError(
        "Insufficient recent DMI observations"
    )

latest = common.loc[latest_date]

dmi_value = float(latest["dmi"])
wtio_value = float(latest["wtio"])
setio_value = float(latest["setio"])

print(f"Latest common month: {latest_date:%b %Y}")
print(f"DMI:   {dmi_value:+.2f} °C")
print(f"WTIO:  {wtio_value:+.2f} °C")
print(f"SETIO: {setio_value:+.2f} °C")


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
    hspace=0.42,
    wspace=0.06,
    width_ratios=[5.2, 1.15]
)

ax_dmi = fig.add_subplot(gs[0, 0])
ax_poles = fig.add_subplot(gs[1, 0])

side_dmi = fig.add_subplot(gs[0, 1])
side_poles = fig.add_subplot(gs[1, 1])

side_dmi.axis("off")
side_poles.axis("off")


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
    "IOD | Current Conditions",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Recent evolution of the Indian Ocean Dipole "
    "and its regional SST anomalies",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Common axes configuration
# ------------------------------------------------------------

for ax in [ax_dmi, ax_poles]:

    ax.set_facecolor("white")

    ax.axhline(
        0,
        color=GRAY,
        linewidth=1.0,
        zorder=3
    )

    ax.set_xlim(
        start_date - pd.DateOffset(months=1),
        latest_date + pd.DateOffset(months=1)
    )

    ax.xaxis.set_major_locator(
        mdates.MonthLocator(bymonth=[1, 7])
    )

    ax.xaxis.set_major_formatter(
        mdates.DateFormatter("%b %Y")
    )

    ax.set_ylabel(
        "SST anomaly (°C)",
        color=GRAY,
        labelpad=10
    )

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


# ------------------------------------------------------------
# Panel 1: Dipole Mode Index
# ------------------------------------------------------------

x = recent.index
y = recent["dmi"].to_numpy(dtype=float)

finite = np.isfinite(y)

ax_dmi.fill_between(
    x, 0, y,
    where=finite & (y >= 0),
    interpolate=True,
    color=RED,
    alpha=0.21,
    zorder=2
)

ax_dmi.fill_between(
    x, 0, y,
    where=finite & (y < 0),
    interpolate=True,
    color=BLUE,
    alpha=0.23,
    zorder=2
)

ax_dmi.plot(
    x,
    y,
    color=DARK,
    linewidth=2.1,
    solid_capstyle="round",
    zorder=4
)

if dmi_value > 0:
    condition = "POSITIVE DMI"
    latest_color = RED
elif dmi_value < 0:
    condition = "NEGATIVE DMI"
    latest_color = BLUE
else:
    condition = "ZERO DMI"
    latest_color = GRAY

ax_dmi.scatter(
    [latest_date],
    [dmi_value],
    s=65,
    color=latest_color,
    edgecolor="white",
    linewidth=1.4,
    zorder=6
)

maximum = np.nanmax(np.abs(y))

limit = max(
    1.0,
    np.ceil((maximum + 0.25) * 2) / 2
)

ax_dmi.set_ylim(-limit, limit)

ax_dmi.yaxis.set_major_locator(
    MultipleLocator(0.5 if limit <= 2.5 else 1.0)
)

ax_dmi.set_title(
    "Dipole Mode Index (DMI)",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=18
)

ax_dmi.text(
    0,
    1.025,
    "Monthly SST anomaly difference | Last 60 months",
    transform=ax_dmi.transAxes,
    fontsize=9,
    color=GRAY,
    va="bottom"
)


# ------------------------------------------------------------
# Panel 2: SST anomalies in the two IOD regions
# ------------------------------------------------------------

west = recent["wtio"].to_numpy(dtype=float)
east = recent["setio"].to_numpy(dtype=float)

ax_poles.plot(
    recent.index,
    west,
    color=RED,
    linewidth=2.1,
    label="WTIO · Western Indian Ocean",
    zorder=4
)

ax_poles.plot(
    recent.index,
    east,
    color=BLUE,
    linewidth=2.1,
    label="SETIO · Southeastern Indian Ocean",
    zorder=4
)

ax_poles.scatter(
    [latest_date],
    [wtio_value],
    s=58,
    color=RED,
    edgecolor="white",
    linewidth=1.3,
    zorder=6
)

ax_poles.scatter(
    [latest_date],
    [setio_value],
    s=58,
    color=BLUE,
    edgecolor="white",
    linewidth=1.3,
    zorder=6
)

values = recent[
    ["wtio", "setio"]
].to_numpy(dtype=float)

maximum = np.nanmax(np.abs(values))

limit = max(
    1.0,
    np.ceil((maximum + 0.25) * 2) / 2
)

ax_poles.set_ylim(-limit, limit)

ax_poles.yaxis.set_major_locator(
    MultipleLocator(0.5 if limit <= 2.5 else 1.0)
)

ax_poles.set_title(
    "Western and Southeastern Indian Ocean",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=18
)

ax_poles.text(
    0,
    1.025,
    "Monthly regional SST anomalies | Last 60 months",
    transform=ax_poles.transAxes,
    fontsize=9,
    color=GRAY,
    va="bottom"
)

ax_poles.legend(
    loc="upper left",
    fontsize=8,
    frameon=False,
    ncol=2,
    labelcolor=GRAY,
    handlelength=2.3
)


# ------------------------------------------------------------
# Right-side information panels
# ------------------------------------------------------------

for side in [side_dmi, side_poles]:

    side.plot(
        [0.02, 0.02],
        [0.12, 0.82],
        transform=side.transAxes,
        color=LIGHT,
        linewidth=1.2
    )


# ------------------------------------------------------------
# Latest DMI
# ------------------------------------------------------------

side_dmi.text(
    0.13, 0.80,
    "LATEST OBSERVATION",
    transform=side_dmi.transAxes,
    va="top",
    fontsize=8,
    fontweight="bold",
    color=GRAY
)

side_dmi.text(
    0.13, 0.60,
    f"{dmi_value:+.2f} °C",
    transform=side_dmi.transAxes,
    va="top",
    fontsize=17,
    fontweight="bold",
    color=latest_color
)

side_dmi.text(
    0.13, 0.41,
    latest_date.strftime("%b %Y"),
    transform=side_dmi.transAxes,
    va="top",
    fontsize=10,
    color=DARK
)

side_dmi.text(
    0.13, 0.25,
    condition,
    transform=side_dmi.transAxes,
    va="top",
    fontsize=8.5,
    fontweight="bold",
    color=latest_color
)


# ------------------------------------------------------------
# Latest regional anomalies
# ------------------------------------------------------------

side_poles.text(
    0.13, 0.80,
    "REGIONAL ANOMALIES",
    transform=side_poles.transAxes,
    va="top",
    fontsize=8,
    fontweight="bold",
    color=GRAY
)

side_poles.text(
    0.13, 0.61,
    f"WTIO  {wtio_value:+.2f} °C",
    transform=side_poles.transAxes,
    va="top",
    fontsize=12,
    fontweight="bold",
    color=RED
)

side_poles.text(
    0.13, 0.44,
    f"SETIO {setio_value:+.2f} °C",
    transform=side_poles.transAxes,
    va="top",
    fontsize=12,
    fontweight="bold",
    color=BLUE
)

side_poles.text(
    0.13, 0.26,
    latest_date.strftime("%b %Y"),
    transform=side_poles.transAxes,
    va="top",
    fontsize=10,
    color=GRAY
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.09, 0.117,
    "DMI = WTIO − SETIO. Positive and negative "
    "monthly values indicate the sign of the "
    "Indian Ocean SST anomaly gradient.",
    fontsize=8.3,
    color=GRAY
)

fig.text(
    0.09, 0.089,
    "A single monthly DMI value does not establish "
    "a persistent IOD event. "
    "Recently published values may be revised.",
    fontsize=8.3,
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

png_file = OUTPUT / "iod_current_conditions.png"
svg_file = OUTPUT / "iod_current_conditions.svg"

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

print("\nIOD Current Conditions completed.\n")
