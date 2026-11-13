
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 01: Download and prepare ENSO indices
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen
import pandas as pd

# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "enso"
RAW = DATA / "raw"

RAW.mkdir(parents=True, exist_ok=True)

# ------------------------------------------------------------
# NOAA CPC data sources
# ------------------------------------------------------------

BASE_URL = "https://www.cpc.ncep.noaa.gov/data/indices"

SOURCES = {
    "RONI.ascii.txt": f"{BASE_URL}/RONI.ascii.txt",
    "Rnino34.ascii.txt": f"{BASE_URL}/Rnino34.ascii.txt",
    "detrend.nino34.ascii.txt":
        f"{BASE_URL}/detrend.nino34.ascii.txt",
    "oni.ascii.txt": f"{BASE_URL}/oni.ascii.txt",
}

# ------------------------------------------------------------
# Download and cache original files
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("ENSO indices | NOAA CPC\n")

for filename, url in SOURCES.items():

    destination = RAW / filename

    print(f"Checking {filename} ...")

    try:
        request = Request(
            url,
            headers={"User-Agent": "TROPICO-Climate-Modes-Monitor"}
        )

        with urlopen(request, timeout=30) as response:
            content = response.read()

        if len(content) < 100:
            raise ValueError("Unexpectedly small download")

        # Detect an unchanged source without rewriting the file.
        if destination.exists():
            if destination.read_bytes() == content:
                print("  Unchanged")
                continue

        destination.write_bytes(content)
        print("  Downloaded / updated")

    except Exception as error:

        if destination.exists():
            print(f"  WARNING: {error}")
            print("  Using the local cached version")
        else:
            raise RuntimeError(
                f"Unable to download {filename}: {error}"
            ) from error

# ------------------------------------------------------------
# Seasonal labels and central months
# ------------------------------------------------------------

SEASON_MONTH = {
    "DJF": 1,
    "JFM": 2,
    "FMA": 3,
    "MAM": 4,
    "AMJ": 5,
    "MJJ": 6,
    "JJA": 7,
    "JAS": 8,
    "ASO": 9,
    "SON": 10,
    "OND": 11,
    "NDJ": 12,
}

# ------------------------------------------------------------
# RONI: seasonal three-month running mean
# ------------------------------------------------------------

roni = pd.read_csv(
    RAW / "RONI.ascii.txt",
    sep=r"\s+"
)

roni["date"] = pd.to_datetime({
    "year": roni["YR"],
    "month": roni["SEAS"].map(SEASON_MONTH),
    "day": 1,
})

roni = (
    roni.set_index("date")[["ANOM"]]
    .rename(columns={"ANOM": "roni"})
)

# ------------------------------------------------------------
# Relative Niño 3.4: monthly
# ------------------------------------------------------------

relative = pd.read_csv(
    RAW / "Rnino34.ascii.txt",
    sep=r"\s+"
)

relative["date"] = pd.to_datetime({
    "year": relative["YR"],
    "month": relative["MTH"],
    "day": 1,
})

relative = (
    relative.set_index("date")[["ANOM"]]
    .rename(columns={"ANOM": "relative_nino34"})
)

# ------------------------------------------------------------
# Conventional Niño 3.4: monthly ERSSTv6
# ------------------------------------------------------------

nino34 = pd.read_csv(
    RAW / "detrend.nino34.ascii.txt",
    sep=r"\s+"
)

nino34["date"] = pd.to_datetime({
    "year": nino34["YR"],
    "month": nino34["MON"],
    "day": 1,
})

nino34 = (
    nino34.set_index("date")[["ANOM"]]
    .rename(columns={"ANOM": "nino34"})
)

# ------------------------------------------------------------
# ONI: seasonal three-month running mean
# ------------------------------------------------------------

oni = pd.read_csv(
    RAW / "oni.ascii.txt",
    sep=r"\s+"
)

oni["date"] = pd.to_datetime({
    "year": oni["YR"],
    "month": oni["SEAS"].map(SEASON_MONTH),
    "day": 1,
})

oni = (
    oni.set_index("date")[["ANOM"]]
    .rename(columns={"ANOM": "oni"})
)

# ------------------------------------------------------------
# Basic validation
# ------------------------------------------------------------

series = {
    "roni": roni,
    "relative_nino34": relative,
    "nino34": nino34,
    "oni": oni,
}

for name, frame in series.items():

    if frame.index.has_duplicates:
        raise ValueError(f"Duplicate dates in {name}")

    if not frame.index.is_monotonic_increasing:
        raise ValueError(f"Non-chronological dates in {name}")

    if frame.empty or frame.isna().any().any():
        raise ValueError(f"Missing or invalid data in {name}")

    if len(frame) < 600:
        raise ValueError(f"Unexpectedly short series: {name}")

# ------------------------------------------------------------
# Merge all indices on the central month
# ------------------------------------------------------------

enso = pd.concat(
    [roni, relative, nino34, oni],
    axis=1,
    sort=True
).sort_index()

# ------------------------------------------------------------
# Save consolidated monthly dataset
# ------------------------------------------------------------

output = DATA / "enso_indices.csv"

content = enso.to_csv(
    index_label="date",
    float_format="%.2f"
).encode("utf-8")

if output.exists() and output.read_bytes() == content:
    print("\nConsolidated dataset unchanged")
else:
    output.write_bytes(content)
    print("\nConsolidated dataset updated")

# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("\nLatest available observations")
print("-" * 55)

for name in enso.columns:

    valid = enso[name].dropna()

    latest_date = valid.index[-1]
    latest_value = valid.iloc[-1]

    if name in ("roni", "oni"):
        season = list(SEASON_MONTH.keys())[
            latest_date.month - 1
        ]
        period = f"{season} {latest_date.year}"
    else:
        period = latest_date.strftime("%Y-%m")

    print(
        f"{name:20s} "
        f"{period:12s} "
        f"{latest_value:+6.2f} °C"
    )

print("-" * 55)
print(f"\nSaved: {output}")
print("ENSO data preparation completed.\n")
