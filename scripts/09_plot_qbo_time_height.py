
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 09: QBO Time-Height Evolution
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: Karlsruhe Institute of Technology (KIT)
#         FU Berlin / KIT QBO radiosonde data series
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

from matplotlib.colors import LinearSegmentedColormap
from matplotlib.ticker import FixedLocator, FuncFormatter


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "qbo"
RAW = DATA / "raw"
OUTPUT = ROOT / "docs" / "figures"

RAW.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)

URL = "https://www.atmohub.kit.edu/data/singapore.dat"

RAW_FILE = RAW / "singapore.dat"
CSV_FILE = DATA / "qbo_vertical_profiles.csv"


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

MONTHS = 96

PRESSURES = [
    10, 12, 15, 20, 25,
    30, 35, 40, 45, 50,
    60, 70, 80, 90, 100
]

BLUE = "#24658A"
RED = "#C54B48"
DARK = "#17324D"
GRAY = "#657587"
LIGHT = "#E5EAF0"

CMAP = LinearSegmentedColormap.from_list(
    "tropico_qbo",
    [
        "#194F75",
        "#467D9E",
        "#94B8CB",
        "#F7F8FA",
        "#E9B0AA",
        "#CA6964",
        "#A9363C",
    ],
    N=256
)

LEVELS = np.arange(-40, 45, 5)

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
# Read KIT ASCII format
# ------------------------------------------------------------

def parse_singapore(text):

    if "Monthly mean zonal wind" not in text:
        raise ValueError("Unrecognized KIT data format")

    if "0.1 m/s" not in text:
        raise ValueError("Unexpected wind units")

    records = {}
    year = None
    previous_year = None
    levels_by_year = {}

    for line in text.splitlines():

        line = line.strip()

        if not line:
            continue

        # Each year begins with a four-digit year
        if re.fullmatch(r"(19|20)\d{2}", line):

            year = int(line)

            if not 1987 <= year <= 2100:
                raise ValueError(f"Invalid year: {year}")

            if previous_year is not None:
                if year <= previous_year:
                    raise ValueError(
                        "Duplicate or unordered years"
                    )

            previous_year = year
            levels_by_year[year] = set()
            continue

        if year is None:
            continue

        if line.lower().startswith("hpa"):
            continue

        parts = line.split()

        try:
            pressure = int(parts[0])
        except (ValueError, IndexError):
            continue

        if pressure not in PRESSURES:
            continue

        if pressure in levels_by_year[year]:
            raise ValueError(
                f"Duplicate pressure {pressure} in {year}"
            )

        levels_by_year[year].add(pressure)

        values = parts[1:]

        # The latest year may contain fewer than 12 months
        if not 1 <= len(values) <= 12:
            raise ValueError(
                f"Invalid month count for "
                f"{year}, {pressure} hPa"
            )

        for month, token in enumerate(values, start=1):

            if token in ("---", "NaN", "nan", "****"):
                continue

            try:
                raw_value = int(token)
            except ValueError as error:
                raise ValueError(
                    f"Unexpected value in {year}-{month:02d}, "
                    f"{pressure} hPa: {token}"
                ) from error

            # Missing-value codes or unrealistic wind speeds
            if abs(raw_value) >= 900:
                continue

            # KIT data are supplied in tenths of m/s
            value = raw_value / 10.0

            date = pd.Timestamp(
                year=year,
                month=month,
                day=1
            )

            key = (date, pressure)

            if key in records:
                raise ValueError(
                    f"Duplicate observation: {key}"
                )

            records[key] = value

    if not records:
        raise ValueError("No QBO observations found")

    series = pd.Series(
        records,
        dtype=float,
        name="zonal_wind"
    )

    series.index = pd.MultiIndex.from_tuples(
        series.index,
        names=["date", "pressure"]
    )

    table = series.unstack("pressure")

    table = table.reindex(
        columns=PRESSURES
    ).sort_index()

    calendar = pd.date_range(
        table.index.min(),
        table.index.max(),
        freq="MS"
    )

    table = table.reindex(calendar)
    table.index.name = "date"

    if len(table) < 450:
        raise ValueError(
            "Unexpectedly short Singapore record"
        )

    if table.notna().sum(axis=1).max() < 12:
        raise ValueError(
            "Insufficient vertical coverage"
        )

    return table


# ------------------------------------------------------------
# Download data
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("QBO | Time-Height Evolution\n")

print("Checking KIT Singapore radiosonde data ...")

try:

    request = Request(
        URL,
        headers={
            "User-Agent": "TROPICO-Climate-Modes-Monitor"
        }
    )

    with urlopen(request, timeout=45) as response:
        content = response.read()

    if len(content) < 10000:
        raise ValueError("Unexpectedly small download")

    text = content.decode(
        "utf-8",
        errors="replace"
    )

    # Validate before modifying the cached file
    wind = parse_singapore(text)

    if (
        RAW_FILE.exists()
        and RAW_FILE.read_bytes() == content
    ):
        print("  Source unchanged")
    else:
        RAW_FILE.write_bytes(content)
        print("  Source downloaded / updated")

except Exception as error:

    if not RAW_FILE.exists():
        raise RuntimeError(
            f"Unable to obtain KIT QBO data: {error}"
        ) from error

    print(f"  WARNING: {error}")
    print("  Using validated cached data")

    text = RAW_FILE.read_text(
        encoding="utf-8",
        errors="replace"
    )

    wind = parse_singapore(text)


# ------------------------------------------------------------
# Save processed data
# ------------------------------------------------------------

csv_content = wind.to_csv(
    index_label="date",
    float_format="%.2f"
).encode("utf-8")

if (
    CSV_FILE.exists()
    and CSV_FILE.read_bytes() == csv_content
):
    print("  Processed CSV unchanged")
else:
    CSV_FILE.write_bytes(csv_content)
    print("  Processed CSV updated")


# ------------------------------------------------------------
# Select period with adequate vertical observations
# ------------------------------------------------------------

valid_months = wind.notna().sum(axis=1)

eligible = valid_months[valid_months >= 10]

if eligible.empty:
    raise ValueError(
        "No months have sufficient vertical observations"
    )

latest_date = eligible.index[-1]

start_date = latest_date - pd.DateOffset(
    months=MONTHS - 1
)

calendar = pd.date_range(
    start=start_date,
    end=latest_date,
    freq="MS"
)

recent = wind.reindex(calendar)

pressure = np.array(PRESSURES, dtype=float)

# Rows: pressure; columns: time
values = recent[PRESSURES].to_numpy(dtype=float).T

masked = np.ma.masked_invalid(values)

if masked.count() < 100:
    raise ValueError(
        "Not enough valid data for the time-height plot"
    )

print(
    f"Full dataset: {wind.index.min():%Y-%m} "
    f"to {wind.index.max():%Y-%m}"
)

print(
    f"Figure period: {start_date:%Y-%m} "
    f"to {latest_date:%Y-%m}"
)

print(f"Pressure levels: {len(PRESSURES)}")
print(f"Valid observations: {masked.count()}")


# ------------------------------------------------------------
# Latest vertical profile
# ------------------------------------------------------------

profile = wind.loc[latest_date, PRESSURES]

profile_values = profile.to_numpy(dtype=float)

valid_profile = np.isfinite(profile_values)

if valid_profile.sum() < 10:
    raise ValueError(
        "Insufficient data in latest vertical profile"
    )


# ------------------------------------------------------------
# Create figure
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.3, 8.1),
    facecolor="white"
)

gs = fig.add_gridspec(
    nrows=1,
    ncols=2,
    left=0.09,
    right=0.95,
    bottom=0.22,
    top=0.79,
    width_ratios=[5.1, 1.25],
    wspace=0.15
)

ax = fig.add_subplot(gs[0, 0])
ax_profile = fig.add_subplot(gs[0, 1], sharey=ax)


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
    "QBO | Time–Height Evolution",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.09, 0.866,
    "Observed equatorial stratospheric zonal winds "
    "| Singapore radiosondes",
    fontsize=11,
    color=GRAY
)


# ------------------------------------------------------------
# Time-height diagram
# ------------------------------------------------------------

time = mdates.date2num(recent.index.to_pydatetime())

X, P = np.meshgrid(time, pressure)

contours = ax.contourf(
    X,
    P,
    masked,
    levels=LEVELS,
    cmap=CMAP,
    extend="both",
    zorder=2
)

# Zero-wind contour
ax.contour(
    X,
    P,
    masked,
    levels=[0],
    colors=[DARK],
    linewidths=1.15,
    zorder=4
)

# Additional contours
ax.contour(
    X,
    P,
    masked,
    levels=[-20, -10, 10, 20],
    colors=DARK,
    linewidths=0.45,
    alpha=0.40,
    zorder=3
)

ax.set_yscale("log")
ax.set_ylim(100, 10)

ax.set_xlim(
    time[0],
    time[-1]
)

ax.set_title(
    "Vertical propagation of QBO wind regimes",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=17
)

ax.text(
    0,
    1.018,
    "Monthly zonal wind | 10–100 hPa",
    transform=ax.transAxes,
    fontsize=9,
    color=GRAY
)

ax.set_ylabel(
    "Pressure (hPa)",
    color=GRAY,
    labelpad=12
)

ax.xaxis_date()

ax.xaxis.set_major_locator(
    mdates.YearLocator(1)
)

ax.xaxis.set_major_formatter(
    mdates.DateFormatter("%Y")
)

ax.yaxis.set_major_locator(
    FixedLocator([10, 15, 20, 30, 50, 70, 100])
)

ax.yaxis.set_major_formatter(
    FuncFormatter(
        lambda value, pos: f"{value:g}"
    )
)

ax.minorticks_off()

ax.tick_params(
    axis="both",
    length=0,
    pad=8
)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

ax.spines["left"].set_color(LIGHT)
ax.spines["bottom"].set_color(LIGHT)


# ------------------------------------------------------------
# Latest vertical profile
# ------------------------------------------------------------

ax_profile.set_yscale("log")
ax_profile.set_ylim(100, 10)

ax_profile.axvline(
    0,
    color=GRAY,
    linewidth=1.0,
    zorder=2
)

ax_profile.fill_betweenx(
    pressure,
    0,
    profile_values,
    where=valid_profile & (profile_values >= 0),
    color=RED,
    alpha=0.22,
    interpolate=True,
    zorder=1
)

ax_profile.fill_betweenx(
    pressure,
    0,
    profile_values,
    where=valid_profile & (profile_values < 0),
    color=BLUE,
    alpha=0.22,
    interpolate=True,
    zorder=1
)

ax_profile.plot(
    profile_values,
    pressure,
    color=DARK,
    linewidth=2.1,
    marker="o",
    markersize=3,
    zorder=4
)

profile_limit = max(
    20,
    np.ceil(
        (np.nanmax(np.abs(profile_values)) + 3) / 10
    ) * 10
)

ax_profile.set_xlim(
    -profile_limit,
    profile_limit
)

ax_profile.set_title(
    "Latest vertical profile",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=17
)

ax_profile.text(
    0,
    1.018,
    latest_date.strftime("%B %Y"),
    transform=ax_profile.transAxes,
    fontsize=9,
    color=GRAY
)

ax_profile.set_xlabel(
    "Zonal wind (m/s)",
    color=GRAY,
    labelpad=11
)

ax_profile.grid(
    axis="x",
    color=LIGHT,
    linewidth=0.8
)

ax_profile.spines["top"].set_visible(False)
ax_profile.spines["right"].set_visible(False)
ax_profile.spines["left"].set_visible(False)

ax_profile.spines["bottom"].set_color(LIGHT)

ax_profile.tick_params(
    axis="y",
    left=False,
    labelleft=False
)

ax_profile.tick_params(
    axis="x",
    length=0,
    pad=8
)

ax_profile.minorticks_off()

# ------------------------------------------------------------
# Explicit pressure labels on the shared logarithmic axis
# ------------------------------------------------------------

pressure_ticks = [10, 15, 20, 30, 50, 70, 100]

ax.yaxis.set_major_locator(
    FixedLocator(pressure_ticks)
)

ax.yaxis.set_major_formatter(
    FuncFormatter(
        lambda value, pos: f"{value:g}"
    )
)

ax.tick_params(
    axis="y",
    labelleft=True
)

ax_profile.tick_params(
    axis="y",
    left=False,
    labelleft=False
)

# ------------------------------------------------------------
# Horizontal colorbar
# ------------------------------------------------------------

cax = fig.add_axes([
    0.09, 0.143, 0.67, 0.022
])

cbar = fig.colorbar(
    contours,
    cax=cax,
    orientation="horizontal",
    ticks=np.arange(-40, 41, 10)
)

cbar.outline.set_visible(False)

cbar.ax.tick_params(
    labelsize=8.5,
    length=0,
    pad=5,
    colors=GRAY
)

fig.text(
    0.09,
    0.180,
    "EASTERLY (WESTWARD)",
    fontsize=8.5,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.76,
    0.180,
    "WESTERLY (EASTWARD)",
    ha="right",
    fontsize=8.5,
    fontweight="bold",
    color=RED
)

fig.text(
    0.425,
    0.106,
    "Zonal wind (m/s)",
    ha="center",
    fontsize=9,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.09, 0.069,
    "Monthly observations; contours interpolate "
    "between available levels and times. "
    "Missing observations are masked.",
    fontsize=8.2,
    color=GRAY
)

fig.text(
    0.09, 0.035,
    "Data: KIT / FU Berlin QBO radiosonde series",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.95, 0.035,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.5,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "qbo_time_height.png"
svg_file = OUTPUT / "qbo_time_height.svg"

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

print("\nQBO Time-Height Evolution completed.\n")
