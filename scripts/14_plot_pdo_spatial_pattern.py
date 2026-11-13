
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 14: PDO Spatial Regression Pattern
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Data: NOAA NCEI ERSSTv6 and PDO index
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd
import xarray as xr
import matplotlib.pyplot as plt

from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
from matplotlib.ticker import FixedLocator

import cartopy.crs as ccrs
import cartopy.feature as cfeature

from cartopy.mpl.gridliner import (
    LATITUDE_FORMATTER,
    LONGITUDE_FORMATTER,
)


# ------------------------------------------------------------
# Paths and configuration
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INDEX_FILE = ROOT / "data" / "pdo" / "pdo_indices.csv"

CACHE = ROOT / "data" / "pdo" / "raw" / "ersst_v6"

PRODUCT = (
    ROOT / "data" / "pdo" /
    "pdo_spatial_regression_1991_2020.csv"
)

OUTPUT = ROOT / "docs" / "figures"

CACHE.mkdir(parents=True, exist_ok=True)
OUTPUT.mkdir(parents=True, exist_ok=True)

BASE_URL = (
    "https://www.ncei.noaa.gov/pub/data/cmb/"
    "ersst/v5/v6"
)

START_YEAR = 1991
END_YEAR = 2020

MIN_VALID_MONTHS = 300
FORCE_REBUILD = False


# ------------------------------------------------------------
# Colors
# ------------------------------------------------------------

BLUE = "#24658A"
DARK = "#17324D"
GRAY = "#657587"
LIGHT = "#E2E8EE"
LAND = "#F0F2F4"

CMAP = LinearSegmentedColormap.from_list(
    "tropico_pdo",
    [
        "#163C63",
        "#296A9D",
        "#79A8C7",
        "#C9DCE7",
        "#F7F8FA",
        "#F0C9C1",
        "#D97E75",
        "#B6414C",
        "#771A36",
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
# Read PDO index
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("PDO | Spatial Regression Pattern\n")

if not INDEX_FILE.exists():
    raise FileNotFoundError(
        "Run 11_download_pdo_index.py first."
    )

index_df = pd.read_csv(
    INDEX_FILE,
    parse_dates=["date"]
)

if (
    index_df["date"].isna().any()
    or index_df["date"].duplicated().any()
):
    raise ValueError("Invalid or duplicate PDO dates")

index = pd.to_numeric(
    index_df.set_index("date")["pdo"],
    errors="coerce"
).sort_index()

months = pd.date_range(
    f"{START_YEAR}-01-01",
    f"{END_YEAR}-12-01",
    freq="MS"
)

index = index.reindex(months)

if index.isna().any():
    raise ValueError(
        "Missing PDO index values in regression period"
    )


# ------------------------------------------------------------
# Load saved regression
# ------------------------------------------------------------

if PRODUCT.exists() and not FORCE_REBUILD:

    print("Using cached spatial regression coefficients")

    table = pd.read_csv(PRODUCT)

    if not {"lat", "lon", "beta"}.issubset(table.columns):
        raise ValueError(
            "Invalid regression CSV columns"
        )

    if table.duplicated(["lat", "lon"]).any():
        raise ValueError(
            "Duplicate grid cells in regression CSV"
        )

    matrix = table.pivot(
        index="lat",
        columns="lon",
        values="beta"
    )

    matrix = (
        matrix.sort_index()
        .sort_index(axis=1)
    )

    latitudes = matrix.index.to_numpy(dtype=float)
    longitudes = matrix.columns.to_numpy(dtype=float)

    regression = matrix.to_numpy(dtype=float)


# ------------------------------------------------------------
# Rebuild regression if needed
# ------------------------------------------------------------

else:

    fields = []

    latitudes = None
    longitudes = None

    for number, date in enumerate(months, start=1):

        filename = f"ersst.v6.{date:%Y%m}.nc"
        filepath = CACHE / filename

        if not filepath.exists():

            print(
                f"[{number}/{len(months)}] "
                f"Downloading {filename}"
            )

            url = f"{BASE_URL}/{filename}"

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
                    f"Unexpected file size: {filename}"
                )

            temporary = filepath.with_suffix(".nc.part")

            temporary.write_bytes(content)
            temporary.replace(filepath)

        with xr.open_dataset(filepath) as ds:

            if "ssta" not in ds:
                raise ValueError(
                    f"Missing ssta in {filename}"
                )

            field = (
                ds["ssta"]
                .squeeze(drop=True)
                .sel(
                    lat=slice(20, 70),
                    lon=slice(110, 260)
                )
                .transpose("lat", "lon")
                .load()
            )

            this_lat = field["lat"].to_numpy()
            this_lon = field["lon"].to_numpy()

            if latitudes is None:

                latitudes = this_lat
                longitudes = this_lon

            elif not (
                np.array_equal(latitudes, this_lat)
                and np.array_equal(longitudes, this_lon)
            ):

                raise ValueError(
                    f"SST grid changed in {filename}"
                )

            fields.append(
                field.to_numpy().astype(np.float64)
            )

    # --------------------------------------------------------
    # Vectorized linear regression
    # --------------------------------------------------------

    sst = np.stack(fields, axis=0)

    x = index.to_numpy(
        dtype=float
    )[:, None, None]

    valid = np.isfinite(sst)

    count = valid.sum(axis=0)

    x_valid = np.where(valid, x, 0.0)
    y_valid = np.where(valid, sst, 0.0)

    sx = x_valid.sum(axis=0)
    sy = y_valid.sum(axis=0)

    sxx = (x_valid * x_valid).sum(axis=0)
    sxy = (x_valid * y_valid).sum(axis=0)

    denominator = (
        sxx - sx * sx / np.maximum(count, 1)
    )

    numerator = (
        sxy - sx * sy / np.maximum(count, 1)
    )

    regression = np.divide(
        numerator,
        denominator,
        out=np.full_like(numerator, np.nan),
        where=(
            (count >= MIN_VALID_MONTHS)
            & (denominator > 1e-8)
        )
    )

    # --------------------------------------------------------
    # Save regression coefficients
    # --------------------------------------------------------

    table = pd.DataFrame({
        "lat": np.repeat(
            latitudes,
            len(longitudes)
        ),
        "lon": np.tile(
            longitudes,
            len(latitudes)
        ),
        "beta": regression.ravel(),
    })

    table.to_csv(
        PRODUCT,
        index=False,
        float_format="%.5f"
    )

    print(f"Saved: {PRODUCT}")


# ------------------------------------------------------------
# Validate regression
# ------------------------------------------------------------

if regression.shape != (
    len(latitudes),
    len(longitudes)
):
    raise ValueError(
        "Invalid regression matrix shape"
    )

if not np.isfinite(regression).any():
    raise ValueError(
        "No valid regression coefficients"
    )

# Symmetric color range
scale = max(
    0.2,
    np.ceil(
        np.nanpercentile(
            np.abs(regression), 99
        ) * 10
    ) / 10
)

levels = np.linspace(
    -scale,
    scale,
    33
)

print(
    f"Regression period: {START_YEAR}–{END_YEAR}"
)

print(
    f"Grid: {len(latitudes)} x {len(longitudes)}"
)

print(
    f"Color range: {-scale:+.1f} to {scale:+.1f}"
)


# ------------------------------------------------------------
# Create figure
# ------------------------------------------------------------

fig = plt.figure(
    figsize=(14.2, 7.1),
    facecolor="white"
)


# ------------------------------------------------------------
# Header
# ------------------------------------------------------------

fig.text(
    0.065, 0.952,
    "TRÓPICO  /  CLIMATE MODES MONITOR",
    color=BLUE,
    fontsize=9,
    fontweight="bold"
)

fig.text(
    0.065, 0.894,
    "PDO | Spatial Regression Pattern",
    color=DARK,
    fontsize=23,
    fontweight="bold"
)

fig.text(
    0.065, 0.849,
    "North Pacific SST anomalies associated with "
    "PDO variability | 1991–2020",
    color=GRAY,
    fontsize=10.5
)


# ------------------------------------------------------------
# North Pacific map
# ------------------------------------------------------------

projection = ccrs.PlateCarree(
    central_longitude=180
)

ax = fig.add_axes(
    [0.065, 0.255, 0.72, 0.52],
    projection=projection
)

ax.set_facecolor("#EAF2F7")


# ------------------------------------------------------------
# Smooth filled contours
# ------------------------------------------------------------

# Contours interpolate the existing spatial grid
# for display only. Native ERSSTv6 data are unchanged.

field = ax.contourf(
    longitudes,
    latitudes,
    np.ma.masked_invalid(regression),
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

field.set_rasterized(True)


# ------------------------------------------------------------
# Land and coastlines
# ------------------------------------------------------------

ax.add_feature(
    cfeature.LAND.with_scale("50m"),
    facecolor=LAND,
    edgecolor="none",
    zorder=5
)

ax.coastlines(
    resolution="50m",
    color="#566A7B",
    linewidth=0.65,
    zorder=6
)

ax.set_extent(
    [110, 260, 20, 70],
    crs=ccrs.PlateCarree()
)

ax.set_title(
    "SST regression onto monthly PDO index",
    loc="left",
    color=DARK,
    fontsize=12.5,
    fontweight="bold",
    pad=13
)


# ------------------------------------------------------------
# Geographic grid
# ------------------------------------------------------------

grid = ax.gridlines(
    draw_labels=True,
    linewidth=0.5,
    color=GRAY,
    alpha=0.35,
    linestyle=(0, (3, 3)),
    x_inline=False,
    y_inline=False
)

grid.top_labels = False
grid.right_labels = False

grid.xlocator = FixedLocator([
    120, 150, 180, 210, 240
])

grid.ylocator = FixedLocator([
    20, 30, 40, 50, 60, 70
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

ax.spines["geo"].set_edgecolor("#AAB9C5")
ax.spines["geo"].set_linewidth(0.65)


# ------------------------------------------------------------
# Right information panel
# ------------------------------------------------------------

info = fig.add_axes(
    [0.810, 0.280, 0.165, 0.44]
)

info.set_axis_off()

info.text(
    0, 0.98,
    "HOW TO READ THE MAP",
    fontsize=9,
    fontweight="bold",
    color=GRAY,
    va="top"
)

info.text(
    0, 0.81,
    "SST association with a\n"
    "+1 PDO index unit",
    fontsize=11,
    fontweight="bold",
    color=DARK,
    va="top",
    linespacing=1.55
)

info.text(
    0, 0.57,
    "RED  /  Positive SST\n"
    "BLUE  /  Negative SST",
    fontsize=9.5,
    color=GRAY,
    va="top",
    linespacing=1.8
)

info.plot(
    [0, 1],
    [0.39, 0.39],
    color=LIGHT,
    linewidth=1,
)

# Keep the information panel in normalized coordinates
info.set_xlim(0, 1)
info.set_ylim(0, 1)

info.text(
    0, 0.29,
    "Statistical regression,\n"
    "not a causal response\n"
    "and not the defining\n"
    "PDO EOF pattern.",
    fontsize=9.2,
    color=GRAY,
    va="top",
    linespacing=1.5
)


# ------------------------------------------------------------
# Colorbar
# ------------------------------------------------------------

cax = fig.add_axes([
    0.092, 0.167, 0.67, 0.024
])

bar = fig.colorbar(
    field,
    cax=cax,
    orientation="horizontal"
)

bar.outline.set_visible(False)

bar.ax.tick_params(
    labelsize=9,
    colors=GRAY,
    length=0,
    pad=5
)

bar.set_label(
    "SST regression coefficient "
    "(°C per PDO index unit)",
    fontsize=9,
    color=GRAY,
    labelpad=7
)


# ------------------------------------------------------------
# Scientific notes
# ------------------------------------------------------------

fig.text(
    0.065, 0.077,
    "Monthly ERSSTv6 SST anomalies regressed onto "
    "NOAA NCEI PDO (1991–2020). "
    "Filled contours interpolate the native grid for display.",
    fontsize=8.1,
    color=GRAY
)


# ------------------------------------------------------------
# Footer
# ------------------------------------------------------------

fig.text(
    0.065, 0.037,
    "Data: NOAA NCEI | ERSSTv6 and PDO index",
    fontsize=8.3,
    color=GRAY
)

fig.text(
    0.975, 0.037,
    "TRÓPICO Research Group | ICAyCC, UNAM",
    ha="right",
    fontsize=8.3,
    color=DARK
)


# ------------------------------------------------------------
# Export
# ------------------------------------------------------------

png_file = OUTPUT / "pdo_spatial_pattern.png"
svg_file = OUTPUT / "pdo_spatial_pattern.svg"

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

print(f"\nSaved: {png_file}")
print(f"Saved: {svg_file}")

print("\nPDO spatial regression figure completed.\n")
