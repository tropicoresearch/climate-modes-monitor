
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 21: Download IOD Indices
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA Climate Prediction Center / ERSSTv6
#
# Published indices:
#   WTIO : Western Tropical Indian Ocean SSTA
#   SETIO: Southeastern Tropical Indian Ocean SSTA
#   DMI  : Dipole Mode Index
#
# No independent climate indices are calculated.
# ============================================================

from pathlib import Path
from urllib.request import Request, urlopen
import re

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

DATA = ROOT / "data" / "iod"
RAW = DATA / "raw"

RAW.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# NOAA data source
# ------------------------------------------------------------

URL = (
    "https://www.cpc.ncep.noaa.gov/products/"
    "international/ocean_monitoring/indian/IODMI/"
    "mnth.ersstv6.clim19912020.dmi_current.txt"
)

RAW_FILE = RAW / "mnth.ersstv6.clim19912020.dmi_current.txt"
OUTPUT = DATA / "iod_indices.csv"


# ------------------------------------------------------------
# Parse NOAA monthly indices
# ------------------------------------------------------------

def parse_iod(text):

    if not all(
        name in text.upper()
        for name in ["WTIO", "SETIO", "DMI"]
    ):
        raise ValueError(
            "Unexpected NOAA IOD data structure"
        )

    records = {}

    for line in text.splitlines():

        parts = line.split()

        if len(parts) < 2:
            continue

        # Expected data rows:
        # Year Month WTIO SETIO DMI

        if not re.fullmatch(r"(19|20)\d{2}", parts[0]):
            continue

        if not re.fullmatch(r"\d{1,2}", parts[1]):
            continue

        year = int(parts[0])
        month = int(parts[1])

        if not 1950 <= year <= 2100:
            continue

        if not 1 <= month <= 12:
            raise ValueError(
                f"Invalid month: {year}-{month}"
            )

        if len(parts) != 5:
            raise ValueError(
                f"Invalid NOAA row: {line}"
            )

        try:
            values = [
                float(token)
                for token in parts[2:]
            ]
        except ValueError as error:
            raise ValueError(
                f"Invalid numerical values: {line}"
            ) from error

        cleaned = []

        for value in values:

            if not np.isfinite(value) or abs(value) >= 90:
                cleaned.append(np.nan)

            elif abs(value) > 15:
                raise ValueError(
                    f"Unrealistic SST anomaly: {value}"
                )

            else:
                cleaned.append(value)

        date = pd.Timestamp(
            year=year,
            month=month,
            day=1
        )

        if date in records:
            raise ValueError(
                f"Duplicate observation: {date}"
            )

        records[date] = {
            "wtio": cleaned[0],
            "setio": cleaned[1],
            "dmi": cleaned[2],
        }

    if not records:
        raise ValueError(
            "No monthly IOD observations found"
        )

    df = pd.DataFrame.from_dict(
        records,
        orient="index"
    ).sort_index()

    df.index.name = "date"

    # --------------------------------------------------------
    # Validate published DMI
    # --------------------------------------------------------

    paired = df.dropna(
        subset=["wtio", "setio", "dmi"]
    )

    if len(paired) < 800:
        raise ValueError(
            "Unexpectedly short IOD record"
        )

    difference = (
        paired["wtio"]
        - paired["setio"]
        - paired["dmi"]
    ).abs()

    # Allow differences due to decimal rounding.
    if (difference > 0.06).any():

        bad_date = difference.idxmax()

        raise ValueError(
            "Published DMI does not match "
            f"WTIO - SETIO at {bad_date:%Y-%m}"
        )

    if df.index.min().year > 1950:
        raise ValueError(
            "Historical record starts unexpectedly late"
        )

    # --------------------------------------------------------
    # Preserve monthly calendar
    # --------------------------------------------------------

    calendar = pd.date_range(
        start=df.index.min(),
        end=df.index.max(),
        freq="MS"
    )

    df = df.reindex(calendar)
    df.index.name = "date"

    last_date = df["dmi"].last_valid_index()

    if last_date is None:
        raise ValueError(
            "No valid DMI observations"
        )

    return df.loc[:last_date]


# ------------------------------------------------------------
# Download
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("IOD | Downloading NOAA CPC indices\n")

try:

    request = Request(
        URL,
        headers={
            "User-Agent": "Mozilla/5.0 TROPICO-Climate-Monitor"
        }
    )

    with urlopen(request, timeout=60) as response:
        content = response.read()

    if len(content) < 10000:
        raise ValueError(
            "Unexpectedly small NOAA download"
        )

    text = content.decode(
        "utf-8",
        errors="replace"
    )

    # Validate before updating the local source.
    df = parse_iod(text)

    if (
        RAW_FILE.exists()
        and RAW_FILE.read_bytes() == content
    ):

        print("Original NOAA source unchanged")

    else:

        temporary = RAW_FILE.with_suffix(
            ".txt.part"
        )

        temporary.write_bytes(content)
        temporary.replace(RAW_FILE)

        print("Original NOAA source downloaded / updated")

except Exception as error:

    if not RAW_FILE.exists():
        raise RuntimeError(
            f"Unable to obtain NOAA DMI: {error}"
        ) from error

    print(f"WARNING: {error}")
    print("Using locally cached NOAA data")

    text = RAW_FILE.read_text(
        encoding="utf-8",
        errors="replace"
    )

    df = parse_iod(text)


# ------------------------------------------------------------
# Export CSV
# ------------------------------------------------------------

csv_content = df.to_csv(
    index_label="date",
    float_format="%.2f"
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

print("\nLatest available observations")
print("-" * 60)

for name in ["dmi", "wtio", "setio"]:

    valid = df[name].dropna()

    date = valid.index[-1]
    value = float(valid.iloc[-1])

    print(
        f"{name.upper():8s} "
        f"{date:%Y-%m} "
        f"{value:+.2f} °C"
    )

print("-" * 60)

print(
    f"Record: {df.index.min():%Y-%m} "
    f"to {df.index.max():%Y-%m}"
)

print(f"Valid DMI months: {df['dmi'].notna().sum()}")
print(f"Missing DMI months: {df['dmi'].isna().sum()}")

print(f"\nSaved: {OUTPUT}")
print("\nIOD data preparation completed.\n")
