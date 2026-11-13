
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 11: Download PDO Index
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA NCEI / ERSSTv6
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "pdo"
RAW = DATA / "raw"

RAW.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Data source
# ------------------------------------------------------------

URL = (
    "https://www.ncei.noaa.gov/pub/data/cmb/"
    "ersst/v5/v6/index/ersst.v6.pdo.dat"
)

RAW_FILE = RAW / "ersst.v6.pdo.dat"
OUTPUT = DATA / "pdo_indices.csv"


# ------------------------------------------------------------
# Introduction
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("PDO | Monthly Index")
print("Source: NOAA NCEI / ERSSTv6\n")


# ------------------------------------------------------------
# Download original data
# ------------------------------------------------------------

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
        raise ValueError(
            "Unexpectedly small download"
        )

    text = content.decode(
        "utf-8",
        errors="replace"
    )

    # Basic source format validation
    if "ERSST PDO Index" not in text:
        raise ValueError(
            "Unexpected NOAA PDO data format"
        )

    print("NOAA source downloaded")

except Exception as error:

    if not RAW_FILE.exists():
        raise RuntimeError(
            f"Unable to download PDO data: {error}"
        ) from error

    print(f"WARNING: {error}")
    print("Using locally cached PDO data")

    content = RAW_FILE.read_bytes()

    text = content.decode(
        "utf-8",
        errors="replace"
    )


# ------------------------------------------------------------
# Parse monthly PDO values
# ------------------------------------------------------------

records = {}
years = set()

for line in text.splitlines():

    parts = line.split()

    if not parts:
        continue

    # NOAA format:
    # Year Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec

    if not (
        len(parts[0]) == 4
        and parts[0].isdigit()
    ):
        continue

    year = int(parts[0])

    if not 1850 <= year <= 2100:
        continue

    if year in years:
        raise ValueError(
            f"Duplicate year: {year}"
        )

    years.add(year)

    values = parts[1:]

    if len(values) != 12:
        raise ValueError(
            f"Expected 12 monthly values for {year}, "
            f"found {len(values)}"
        )

    for month, token in enumerate(values, start=1):

        value = float(token)

        # NOAA uses 99.99 for missing observations.
        if abs(value) >= 90:
            value = np.nan

        elif not np.isfinite(value) or abs(value) > 20:
            raise ValueError(
                f"Invalid PDO value: "
                f"{year}-{month:02d}: {value}"
            )

        date = pd.Timestamp(
            year=year,
            month=month,
            day=1
        )

        records[date] = value


# ------------------------------------------------------------
# Validate observations
# ------------------------------------------------------------

pdo = pd.Series(
    records,
    name="pdo",
    dtype=float
).sort_index()

if pdo.notna().sum() < 1500:
    raise ValueError(
        "PDO historical record is unexpectedly short"
    )

calendar = pd.date_range(
    start=pdo.index.min(),
    end=pdo.index.max(),
    freq="MS"
)

pdo = pdo.reindex(calendar)

# Remove trailing months without observations
last_date = pdo.last_valid_index()

if last_date is None:
    raise ValueError("No valid PDO observations")

pdo = pdo.loc[:last_date]

if pdo.index.has_duplicates:
    raise ValueError("Duplicate monthly dates")


# ------------------------------------------------------------
# Calculate 12-month running mean
# ------------------------------------------------------------

df = pd.DataFrame({
    "pdo": pdo
})

df["pdo_12m"] = (
    df["pdo"]
    .rolling(
        window=12,
        min_periods=12
    )
    .mean()
)

df.index.name = "date"


# ------------------------------------------------------------
# Cache original source
# ------------------------------------------------------------

if (
    RAW_FILE.exists()
    and RAW_FILE.read_bytes() == content
):
    print("Original source unchanged")
else:
    RAW_FILE.write_bytes(content)
    print("Original source updated")


# ------------------------------------------------------------
# Save processed dataset
# ------------------------------------------------------------

csv_content = df.to_csv(
    index_label="date",
    float_format="%.3f"
).encode("utf-8")

if (
    OUTPUT.exists()
    and OUTPUT.read_bytes() == csv_content
):
    print("Processed dataset unchanged")
else:
    OUTPUT.write_bytes(csv_content)
    print("Processed dataset updated")


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

latest = df.loc[last_date]

pdo_value = float(latest["pdo"])

smoothed = df["pdo_12m"].dropna()

if smoothed.empty:
    raise ValueError(
        "No complete 12-month average available"
    )

smooth_date = smoothed.index[-1]
smooth_value = float(smoothed.iloc[-1])

if pdo_value > 0:
    state = "Positive"
elif pdo_value < 0:
    state = "Negative"
else:
    state = "Zero"

print("\nPDO data summary")
print("-" * 55)

print(
    f"Historical record: "
    f"{df.index.min():%Y-%m} to {last_date:%Y-%m}"
)

print(
    f"Valid monthly values: "
    f"{df['pdo'].notna().sum()}"
)

print(
    f"Latest PDO: "
    f"{pdo_value:+.2f} ({last_date:%b %Y})"
)

print(f"Index sign: {state}")

print(
    f"12-month mean: "
    f"{smooth_value:+.2f} ({smooth_date:%b %Y})"
)

print("-" * 55)

print(f"\nSaved: {OUTPUT}")
print("PDO data preparation completed.\n")
