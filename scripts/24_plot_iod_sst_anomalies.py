
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 24: Indian Ocean SST Anomalies
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Sources:
#   NOAA CPC  - IOD indices
#   NOAA NCEI - ERSSTv6 monthly SST anomalies
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from matplotlib.colors import (
    LinearSegmentedColormap,
    TwoSlopeNorm
)

from matplotlib.patches import Rectangle

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

INDEX_FILE = ROOT / "data" / "iod" / "iod_indices.csv"

CACHE = ROOT / "data" / "iod" / "raw" / "ersst_v6"

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

LON_MIN = 35
LON_MAX = 125

LAT_MIN = -25
LAT_MAX = 25

COAST_RESOLUTION = "10m"

BLUE = "#24658A"
RED = "#C54B48"
DARK = "#17324D"
GRAY = "#657587"
LAND = "#F0F2F4"
COAST = "#536A7D"

CMAP = LinearSegmentedColormap.from_list(
    "tropico_iod_ssta",
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
# Read published NOAA CPC indices
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("IOD | Indian Ocean SST Anomalies\n")

if not INDEX_FILE.exists():
    raise FileNotFoundError(
        "Run 21_download_iod_indices.py first."
    )

df = pd.read_csv(
    INDEX_FILE,
    parse_dates=["date"],
    index_col="date"
).sort_index()

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError("Invalid or duplicate dates")

for name in ["dmi", "wtio", "setio"]:

    if name not in df.columns:
        raise ValueError(f"Missing column: {name}")

    df[name] = pd.to_numeric(
        df[name],
        errors="coerce"
    )

common = df[["dmi", "wtio", "setio"]].dropna()

if common.empty:
    raise ValueError(
        "No common valid IOD observations"
    )

date = common.index[-1]
latest = common.loc[date]

dmi = float(latest["dmi"])
wtio = float(latest["wtio"])
setio = float(latest["setio"])

print(f"Latest common month: {date:%B %Y}")
print(f"DMI:   {dmi:+.2f} °C")
print(f"WTIO:  {wtio:+.2f} °C")
print(f"SETIO: {setio:+.2f} °C")


# ------------------------------------------------------------
# Monthly ERSSTv6 file
# ------------------------------------------------------------

filename = f"ersst.v6.{date:%Y%m}.nc"

filepath = CACHE / filename
url = f"{BASE_URL}/{filename}"

print(f"\nChecking {filename} ...")

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

            with xr.open_dataset(temporary) as ds:

                if "ssta" not in ds:
                    raise ValueError(
                        "Missing SSTA variable"
                    )

                if not {"lat", "lon"}.issubset(ds.coords):
                    raise ValueError(
                        "Missing geographic coordinates"
                    )

                if ds["ssta"].size < 5000:
                    raise ValueError(
                        "Unexpected NetCDF dimensions"
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
# Read the SST anomaly field
# ------------------------------------------------------------

with xr.open_dataset(filepath) as ds:

    ssta = ds["ssta"].squeeze(drop=True)

    if set(ssta.dims) != {"lat", "lon"}:
        raise ValueError(
            f"Unexpected dimensions: {ssta.dims}"
        )

    # Original ERSSTv6 longitudes: 0–360 degrees
    ssta = (
        ssta.sortby("lat")
        .sortby("lon")
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
        "Insufficient valid Indian Ocean SST data"
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
# Create figure
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.2, 8.0),
    facecolor="white"
)


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

fig.text(
    0.075, 0.950,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    fontsize=9,
    fontweight="bold",
    color=BLUE
)

fig.text(
    0.075, 0.895,
    "IOD | Indian Ocean SST Anomalies",
    fontsize=23,
    fontweight="bold",
    color=DARK
)

fig.text(
    0.075, 0.853,
    f"Observed sea surface temperature anomalies "
    f"| {date:%B %Y}",
    fontsize=11,
    color=GRAY
)

fig.text(
    0.925, 0.950,
    f"DMI  {dmi:+.2f} °C",
    ha="right",
    fontsize=11,
    fontweight="bold",
    color=RED if dmi > 0 else BLUE if dmi < 0 else GRAY
)


# ------------------------------------------------------------
# Indian Ocean map
# ------------------------------------------------------------

projection = ccrs.PlateCarree(
    central_longitude=80
)

ax = fig.add_axes(
    [0.13, 0.245, 0.74, 0.55],
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
    alpha=0.32,
    linestyle=(0, (3, 3)),
    zorder=3
)

grid.top_labels = False
grid.right_labels = False

grid.xlocator = FixedLocator([
    40, 60, 80, 100, 120
])

grid.ylocator = FixedLocator([
    -20, -10, 0, 10, 20
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

ax.coastlines(
    resolution=COAST_RESOLUTION,
    color=COAST,
    linewidth=0.65,
    zorder=21
)


# ------------------------------------------------------------
# IOD index regions
# ------------------------------------------------------------

REGIONS = [
    {
        "name": "WTIO",
        "lon": 50,
        "lat": -10,
        "width": 20,
        "height": 20,
    },
    {
        "name": "SETIO",
        "lon": 90,
        "lat": -10,
        "width": 20,
        "height": 10,
    },
]

for region in REGIONS:

    box = Rectangle(
        (
            region["lon"],
            region["lat"]
        ),
        region["width"],
        region["height"],
        facecolor="none",
        edgecolor=DARK,
        linewidth=2.0,
        transform=ccrs.PlateCarree(),
        zorder=30
    )

    # White outline improves contrast over SST colors.
    box.set_path_effects([
        pe.withStroke(
            linewidth=4,
            foreground="white"
        )
    ])

    ax.add_patch(box)

    ax.text(
        region["lon"] + region["width"] / 2,
        region["lat"] + region["height"] + 2.0,
        region["name"],
        transform=ccrs.PlateCarree(),
        fontsize=10,
        fontweight="bold",
        color=DARK,
        ha="center",
        va="bottom",
        zorder=32,
        bbox={
            "facecolor": "white",
            "edgecolor": "none",
            "alpha": 0.93,
            "pad": 2.5
        }
    )


# ------------------------------------------------------------
# Map title and frame
# ------------------------------------------------------------

ax.set_title(
    "Monthly SST anomaly | ERSSTv6",
    loc="left",
    fontsize=12.5,
    fontweight="bold",
    color=DARK,
    pad=12
)

ax.spines["geo"].set_edgecolor("#AAB9C5")
ax.spines["geo"].set_linewidth(0.65)


# ------------------------------------------------------------
# Colorbar
# ------------------------------------------------------------

cax = fig.add_axes([
    0.17, 0.153, 0.66, 0.024
])

bar = fig.colorbar(
    field,
    cax=cax,
    orientation="horizontal"
)

bar.outline.set_visible(False)

step = 1 if scale <= 3 else 2
tick_max = int(np.floor(scale / step)) * step

bar.set_ticks(
    np.arange(
        -tick_max,
        tick_max + step,
        step
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
    0.075, 0.087,
    "WTIO: 50°–70°E, 10°S–10°N. "
    "SETIO: 90°–110°E, 10°S–0°. "
    "DMI = WTIO − SETIO.",
    fontsize=8.5,
    color=GRAY
)

fig.text(
    0.075, 0.065,
    "ERSSTv6 SST anomalies relative to 1991–2020. "
    "Map depicts observed anomalies, not an IOD event classification.",
    fontsize=8.2,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.075, 0.031,
    "Data: NOAA NCEI ERSSTv6 | NOAA CPC DMI",
    fontsize=8.4,
    color=GRAY
)

fig.text(
    0.925, 0.031,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.4,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "iod_sst_anomalies.png"
svg_file = OUTPUT / "iod_sst_anomalies.svg"

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

print("\nIOD SST anomaly map completed.\n")
