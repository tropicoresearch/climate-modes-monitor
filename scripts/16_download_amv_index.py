
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 16: Download North Atlantic SST Index
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA NCEI / ERSSTv6
#
# Note:
# This is a North Atlantic SST anomaly series.
# It does not isolate internally generated AMV.
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "amv"
RAW = DATA / "raw"

RAW.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Source
# ------------------------------------------------------------

URL = (
    "https://www.ncei.noaa.gov/pub/data/cmb/"
    "ersst/v5/v6/index/ersst.v6.amo.dat"
)

RAW_FILE = RAW / "ersst.v6.amo.dat"
OUTPUT = DATA / "north_atlantic_ssta.csv"


# ------------------------------------------------------------
# Parse NOAA monthly data
# ------------------------------------------------------------

def parse_amv_source(text):

    records = {}

    for line in text.splitlines():

        parts = line.split()

        # Expected format:
        # Year Month SSTA

        if len(parts) != 3:
            continue

        try:
            year = int(parts[0])
            month = int(parts[1])
            value = float(parts[2])
        except ValueError:
            continue

        if not 1850 <= year <= 2100:
            continue

        if not 1 <= month <= 12:
            raise ValueError(
                f"Invalid month in NOAA data: {month}"
            )

        # Missing-value sentinels
        if not np.isfinite(value) or abs(value) >= 90:
            value = np.nan

        elif abs(value) > 10:
            raise ValueError(
                f"Unrealistic SST anomaly: "
                f"{year}-{month:02d} = {value}"
            )

        date = pd.Timestamp(
            year=year,
            month=month,
            day=1
        )

        if date in records:
            raise ValueError(
                f"Duplicate observation: {date}"
            )

        records[date] = value

    series = pd.Series(
        records,
        dtype=float,
        name="na_ssta"
    ).sort_index()

    if series.notna().sum() < 2000:
        raise ValueError(
            "Unexpectedly short North Atlantic SST record"
        )

    if series.index.min().year > 1850:
        raise ValueError(
            "Historical NOAA record starts too late"
        )

    # Preserve missing months as NaN
    calendar = pd.date_range(
        series.index.min(),
        series.index.max(),
        freq="MS"
    )

    series = series.reindex(calendar)
    series.index.name = "date"

    # Exclude any trailing missing values
    last_date = series.last_valid_index()

    if last_date is None:
        raise ValueError("No valid SST observations")

    return series.loc[:last_date]


# ------------------------------------------------------------
# Download and validate
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("AMV | North Atlantic SST Anomalies")
print("Source: NOAA NCEI / ERSSTv6\n")

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

    text = content.decode("utf-8")

    if "ERSST AMO" not in text:
        raise ValueError(
            "Unexpected NOAA file header"
        )

    # Validate downloaded data before saving
    series = parse_amv_source(text)

    if (
        RAW_FILE.exists()
        and RAW_FILE.read_bytes() == content
    ):
        print("Original source unchanged")

    else:

        temporary = RAW_FILE.with_suffix(
            ".dat.part"
        )

        temporary.write_bytes(content)
        temporary.replace(RAW_FILE)

        print("Original source downloaded / updated")

except Exception as error:

    if not RAW_FILE.exists():
        raise RuntimeError(
            f"Unable to obtain NOAA AMV data: {error}"
        ) from error

    print(f"WARNING: {error}")
    print("Using locally cached source")

    text = RAW_FILE.read_text(
        encoding="utf-8"
    )

    series = parse_amv_source(text)


# ------------------------------------------------------------
# Monthly and low-frequency indicators
# ------------------------------------------------------------

df = pd.DataFrame({
    "na_ssta": series
})

df["na_ssta_12m"] = (
    df["na_ssta"]
    .rolling(
        window=12,
        min_periods=12
    )
    .mean()
)

df["na_ssta_120m"] = (
    df["na_ssta"]
    .rolling(
        window=120,
        min_periods=120
    )
    .mean()
)


# ------------------------------------------------------------
# Save processed data
# ------------------------------------------------------------

content = df.to_csv(
    index_label="date",
    float_format="%.4f"
).encode("utf-8")

if (
    OUTPUT.exists()
    and OUTPUT.read_bytes() == content
):
    print("Processed dataset unchanged")

else:

    OUTPUT.write_bytes(content)

    print("Processed dataset updated")


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("\nNorth Atlantic SST data summary")
print("-" * 58)

print(
    f"Historical record: "
    f"{df.index.min():%Y-%m} "
    f"to {df.index.max():%Y-%m}"
)

print(
    f"Valid monthly observations: "
    f"{df['na_ssta'].notna().sum()}"
)

print(
    f"Missing months: "
    f"{df['na_ssta'].isna().sum()}"
)

for column in df.columns:

    valid = df[column].dropna()

    latest_date = valid.index[-1]
    latest_value = float(valid.iloc[-1])

    print(
        f"{column:16s} "
        f"{latest_date:%Y-%m} "
        f"{latest_value:+.3f} °C"
    )

print("-" * 58)

print(f"\nSaved: {OUTPUT}")

print(
    "\nNote: This dataset contains observed North Atlantic "
    "SST anomalies, including forced climate variability."
)

print("\nAMV data preparation completed.\n")
