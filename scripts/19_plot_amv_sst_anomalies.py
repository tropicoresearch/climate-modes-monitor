
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 19: North Atlantic SST Anomalies
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Data source: NOAA NCEI / ERSSTv6
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from matplotlib.colors import (
    LinearSegmentedColormap,
    TwoSlopeNorm
)

from matplotlib.ticker import (
    FixedLocator,
    FuncFormatter
)

from cartopy.mpl.gridliner import (
    LATITUDE_FORMATTER,
    LONGITUDE_FORMATTER
)


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INDEX_FILE = (
    ROOT / "data" / "amv" /
    "north_atlantic_ssta.csv"
)

CACHE = ROOT / "data" / "amv" / "raw" / "ersst_v6"
OUTPUT = ROOT / "docs" / "figures"

CACHE.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

BASE_URL = (
    "https://www.ncei.noaa.gov/pub/data/cmb/"
    "ersst/v5/v6"
)

LON_MIN = -100
LON_MAX = 25

LAT_MIN = 0
LAT_MAX = 70

COAST_RESOLUTION = "10m"

BLUE = "#24658A"
RED = "#C54B48"
DARK = "#17324D"
GRAY = "#657587"
LAND = "#F0F2F4"
COAST = "#536A7D"

CMAP = LinearSegmentedColormap.from_list(
    "tropico_ssta",
    [
        "#153E64",
        "#2C6F9D",
        "#83B3D0",
        "#D0E2ED",
        "#F8F9FA",
        "#F0C7C0",
        "#DE8D80",
        "#BD4A52",
        "#7D203D",
    ],
    N=256
)

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "svg.fonttype": "none",
    "svg.hashsalt": "tropico-climate-modes-monitor",
})


# ------------------------------------------------------------
# Read North Atlantic SST index
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("AMV | North Atlantic SST Anomalies\n")

if not INDEX_FILE.exists():
    raise FileNotFoundError(
        "Run 16_download_amv_index.py first."
    )

index = pd.read_csv(
    INDEX_FILE,
    parse_dates=["date"]
)

if (
    index["date"].isna().any()
    or index["date"].duplicated().any()
):
    raise ValueError(
        "Invalid or duplicate observation dates"
    )

if "na_ssta" not in index.columns:
    raise ValueError("Missing na_ssta column")

index["na_ssta"] = pd.to_numeric(
    index["na_ssta"],
    errors="coerce"
)

index = (
    index.dropna(subset=["na_ssta"])
    .sort_values("date")
)

if index.empty:
    raise ValueError("No valid SST observations")

latest = index.iloc[-1]

date = pd.Timestamp(latest["date"])
index_value = float(latest["na_ssta"])

filename = f"ersst.v6.{date:%Y%m}.nc"
filepath = CACHE / filename

url = f"{BASE_URL}/{filename}"

print(f"Observation: {date:%B %Y}")
print(f"North Atlantic index: {index_value:+.2f} °C")


# ------------------------------------------------------------
# Download and cache monthly NetCDF
# ------------------------------------------------------------

try:

    request = Request(
        url,
        headers={
            "User-Agent":
            "TROPICO-Climate-Modes-Monitor"
        }
    )

    with urlopen(request, timeout=60) as response:
        content = response.read()

    if len(content) < 100000:
        raise ValueError(
            "Unexpectedly small NetCDF download"
        )

    if (
        filepath.exists()
        and filepath.read_bytes() == content
    ):

        print("Monthly NetCDF unchanged")

    else:

        temporary = CACHE / (filename + ".part")

        try:

            temporary.write_bytes(content)

            with xr.open_dataset(temporary) as test:

                if "ssta" not in test:
                    raise ValueError(
                        "Unexpected ERSSTv6 NetCDF structure"
                    )

                if not {"lat", "lon"}.issubset(test.coords):
                    raise ValueError(
                        "Missing geographic coordinates"
                    )

                if test["ssta"].size < 5000:
                    raise ValueError(
                        "Unexpectedly small SST field"
                    )

            temporary.replace(filepath)

        finally:

            if temporary.exists():
                temporary.unlink()

        print("Monthly NetCDF downloaded / updated")

except Exception as error:

    if not filepath.exists():
        raise RuntimeError(
            f"Unable to obtain {filename}: {error}"
        ) from error

    print(f"WARNING: {error}")
    print("Using locally cached NetCDF")


# ------------------------------------------------------------
# Read SST anomalies
# ------------------------------------------------------------

with xr.open_dataset(filepath) as ds:

    if "ssta" not in ds:
        raise ValueError(
            "Missing ssta variable"
        )

    ssta = ds["ssta"].squeeze(drop=True)

    if set(ssta.dims) != {"lat", "lon"}:
        raise ValueError(
            f"Unexpected dimensions: {ssta.dims}"
        )

    # Convert longitudes to -180 / +180.
    ssta = ssta.assign_coords(
        lon=((ssta["lon"] + 180) % 360) - 180
    )

    ssta = (
        ssta.sortby("lon")
        .sortby("lat")
        .sel(
            lon=slice(LON_MIN, LON_MAX),
            lat=slice(LAT_MIN, LAT_MAX)
        )
        .transpose("lat", "lon")
        .load()
    )


lons = ssta["lon"].to_numpy()
lats = ssta["lat"].to_numpy()

values = np.asarray(
    ssta.to_numpy(),
    dtype=float
).copy()

values[
    ~np.isfinite(values)
    | (np.abs(values) > 15)
] = np.nan

if np.isfinite(values).sum() < 300:
    raise ValueError(
        "Insufficient North Atlantic SST observations"
    )


# ------------------------------------------------------------
# Color scale
# ------------------------------------------------------------

scale = max(
    2.0,
    np.ceil(
        np.nanpercentile(
            np.abs(values),
            98
        ) * 2
    ) / 2
)

levels = np.linspace(
    -scale,
    scale,
    41
)

print(f"Grid: {len(lats)} x {len(lons)}")
print(f"Color range: ±{scale:.1f} °C")


# ------------------------------------------------------------
# Figure
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.2, 7.4),
    facecolor="white"
)


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

fig.text(
    0.075, 0.948,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    fontsize=9,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.075, 0.894,
    "AMV | North Atlantic SST Anomalies",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.075, 0.849,
    f"Observed sea surface temperature anomalies "
    f"| {date:%B %Y}",
    fontsize=11,
    color=GRAY
)

fig.text(
    0.925, 0.948,
    f"NORTH ATLANTIC INDEX  {index_value:+.2f} °C",
    ha="right",
    fontsize=9,
    fontweight="bold",
    color=RED if index_value > 0 else BLUE
)


# ------------------------------------------------------------
# Map
# ------------------------------------------------------------

projection = ccrs.PlateCarree(
    central_longitude=-35
)

ax = fig.add_axes(
    [0.075, 0.244, 0.85, 0.53],
    projection=projection
)

ax.set_facecolor("#EEF5F8")

ax.set_extent(
    [LON_MIN, LON_MAX, LAT_MIN, LAT_MAX],
    crs=ccrs.PlateCarree()
)


# ------------------------------------------------------------
# SST anomaly field
# ------------------------------------------------------------

# The field is displayed with filled contours.
# Do not rasterize the contour collection here.
# A high-resolution land layer will be drawn above it.

field = ax.contourf(
    lons,
    lats,
    np.ma.masked_invalid(values),
    levels=levels,
    cmap=CMAP,
    norm=TwoSlopeNorm(
        vmin=-scale,
        vcenter=0,
        vmax=scale
    ),
    extend="both",
    transform=ccrs.PlateCarree(),
    antialiased=True,
    zorder=2
)


# ------------------------------------------------------------
# Geographic grid
# ------------------------------------------------------------

grid = ax.gridlines(
    draw_labels=True,
    x_inline=False,
    y_inline=False,
    linewidth=0.5,
    color=GRAY,
    alpha=0.30,
    linestyle=(0, (3, 3)),
    zorder=3
)

grid.top_labels = False
grid.right_labels = False

grid.xlocator = FixedLocator([
    -90, -60, -30, 0
])

grid.ylocator = FixedLocator([
    0, 15, 30, 45, 60
])

grid.xformatter = LONGITUDE_FORMATTER
grid.yformatter = LATITUDE_FORMATTER

grid.xlabel_style = {
    "size": 9,
    "color": GRAY
}

grid.ylabel_style = {
    "size": 9,
    "color": GRAY
}


# ------------------------------------------------------------
# High-resolution land mask
# ------------------------------------------------------------

# IMPORTANT:
# Draw land AFTER the SST field and geographic grid.
# Natural Earth land polygons cover any contour
# interpolation extending beyond the real coastline.

land_feature = cfeature.NaturalEarthFeature(
    category="physical",
    name="land",
    scale=COAST_RESOLUTION,
    facecolor=LAND,
    edgecolor="none"
)

ax.add_feature(
    land_feature,
    zorder=20
)


# ------------------------------------------------------------
# Coastlines
# ------------------------------------------------------------

# Use the same Natural Earth resolution as the land mask
# to keep the coastline and land polygons consistent.

ax.coastlines(
    resolution=COAST_RESOLUTION,
    color=COAST,
    linewidth=0.65,
    zorder=21
)


# ------------------------------------------------------------
# Map title and frame
# ------------------------------------------------------------

ax.set_title(
    "Monthly SST anomaly | ERSSTv6",
    loc="left",
    pad=12,
    color=DARK,
    fontsize=12.5,
    fontweight="bold"
)

ax.spines["geo"].set_edgecolor("#AAB9C5")
ax.spines["geo"].set_linewidth(0.65)


# ------------------------------------------------------------
# Colorbar
# ------------------------------------------------------------

cax = fig.add_axes([
    0.10, 0.157, 0.80, 0.025
])

bar = fig.colorbar(
    field,
    cax=cax,
    orientation="horizontal"
)

bar.outline.set_visible(False)

# Clean, symmetric, integer tick labels.
tick_max = int(np.floor(scale))

bar.set_ticks(
    np.arange(
        -tick_max,
        tick_max + 1,
        1
    )
)

bar.ax.xaxis.set_major_formatter(
    FuncFormatter(
        lambda value, pos:
        "0" if abs(value) < 1e-8
        else f"{value:+.0f}"
    )
)

bar.set_label(
    "Sea surface temperature anomaly (°C)",
    fontsize=9,
    color=GRAY,
    labelpad=6
)

bar.ax.tick_params(
    colors=GRAY,
    labelsize=9,
    length=0,
    pad=5
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.075, 0.082,
    "ERSSTv6 anomalies relative to 1991–2020. "
    "Map shows observed SST anomalies, "
    "not an isolated internal AMV pattern.",
    fontsize=8.2,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.075, 0.042,
    "Data: NOAA NCEI | ERSSTv6 (2° × 2°)",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.925, 0.042,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.4,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "amv_sst_anomalies.png"
svg_file = OUTPUT / "amv_sst_anomalies.svg"

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

print("\nAMV SST anomaly map completed.\n")
