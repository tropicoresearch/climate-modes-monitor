
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 06: Download QBO indices
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA Climate Prediction Center (CORe)
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

DATA = ROOT / "data" / "qbo"
RAW = DATA / "raw"

RAW.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Sources
# ------------------------------------------------------------

BASE_URL = "https://www.cpc.ncep.noaa.gov/data/indices"

SOURCES = {
    "qbo_u30": f"{BASE_URL}/qbo.u30.index",
    "qbo_u50": f"{BASE_URL}/qbo.u50.index",
}


# ------------------------------------------------------------
# Read original monthly wind data
# ------------------------------------------------------------

def parse_qbo(text, name):

    lines = text.splitlines()

    # Locate ORIGINAL DATA section
    section = next(
        (
            i for i, line in enumerate(lines)
            if re.search(
                r"\bORIGINAL\s+DATA\b",
                line,
                re.IGNORECASE
            )
        ),
        None
    )

    if section is None:
        raise ValueError(
            f"ORIGINAL DATA section not found: {name}"
        )

    # Locate monthly header
    header = next(
        (
            i for i in range(section + 1, len(lines))
            if re.match(
                r"^\s*YEAR\s+JAN\s+FEB\b",
                lines[i]
            )
        ),
        None
    )

    if header is None:
        raise ValueError(
            f"Monthly header not found: {name}"
        )

    observations = {}

    for line in lines[header + 1:]:

        # Stop before the next section
        if re.search(
            r"\bANOMALY\b|\bSTANDARDIZED\b",
            line,
            re.IGNORECASE
        ):
            break

        match = re.match(
            r"^\s*(\d{4})(.*)$",
            line
        )

        if match is None:
            continue

        year = int(match.group(1))

        if year < 1979 or year > 2100:
            continue

        # Values may be concatenated, e.g.
        # 15.91-999.90-999.90
        tokens = re.findall(
            r"[+-]?\d+(?:\.\d+)?",
            match.group(2)
        )

        if len(tokens) != 12:
            raise ValueError(
                f"{name}: expected 12 months "
                f"for year {year}, found {len(tokens)}"
            )

        for month, token in enumerate(tokens, start=1):

            value = float(token)

            # NOAA missing-value sentinel
            if not np.isfinite(value) or value <= -900:
                continue

            if abs(value) > 100:
                raise ValueError(
                    f"Unrealistic wind in {name}: "
                    f"{year}-{month:02d} = {value}"
                )

            date = pd.Timestamp(
                year=year,
                month=month,
                day=1
            )

            if date in observations:
                raise ValueError(
                    f"Duplicate observation: {date}"
                )

            observations[date] = value

    series = pd.Series(
        observations,
        name=name,
        dtype=float
    ).sort_index()

    if len(series) < 400:
        raise ValueError(
            f"Unexpectedly short QBO record: {name}"
        )

    return series


# ------------------------------------------------------------
# Download and validate
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("QBO | Downloading monthly zonal winds\n")

series = {}

for name, url in SOURCES.items():

    filename = url.rsplit("/", 1)[-1]
    destination = RAW / filename

    print(f"Checking {filename} ...")

    try:

        request = Request(
            url,
            headers={
                "User-Agent":
                "TROPICO-Climate-Modes-Monitor"
            }
        )

        with urlopen(request, timeout=40) as response:
            content = response.read()

        if len(content) < 1000:
            raise ValueError(
                "Unexpectedly small download"
            )

        # Validate before saving
        text = content.decode(
            "utf-8",
            errors="replace"
        )

        parsed = parse_qbo(text, name)

        if (
            destination.exists()
            and destination.read_bytes() == content
        ):
            print("  Unchanged")
        else:
            destination.write_bytes(content)
            print("  Downloaded / updated")

    except Exception as error:

        if not destination.exists():
            raise RuntimeError(
                f"Unable to obtain {filename}: {error}"
            ) from error

        print(f"  WARNING: {error}")
        print("  Using cached local data")

        text = destination.read_text(
            encoding="utf-8",
            errors="replace"
        )

        parsed = parse_qbo(text, name)

    series[name] = parsed

    print(
        f"  {len(parsed)} monthly observations"
    )


# ------------------------------------------------------------
# Consolidate series
# ------------------------------------------------------------

qbo = pd.concat(
    [series["qbo_u30"], series["qbo_u50"]],
    axis=1,
    sort=True
).sort_index()

calendar = pd.date_range(
    start=qbo.index.min(),
    end=qbo.index.max(),
    freq="MS"
)

qbo = qbo.reindex(calendar)
qbo.index.name = "date"

if qbo.index.has_duplicates:
    raise ValueError(
        "Duplicate dates in consolidated QBO data"
    )


# ------------------------------------------------------------
# Save CSV
# ------------------------------------------------------------

output = DATA / "qbo_indices.csv"

content = qbo.to_csv(
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
print("-" * 58)

for name in qbo.columns:

    valid = qbo[name].dropna()

    date = valid.index[-1]
    value = float(valid.iloc[-1])

    if value > 0:
        phase = "Westerly"
    elif value < 0:
        phase = "Easterly"
    else:
        phase = "Zero wind"

    print(
        f"{name:12s} "
        f"{date:%Y-%m} "
        f"{value:+8.2f} m/s "
        f"{phase}"
    )

print("-" * 58)

print(f"\nSaved: {output}")
print("QBO data preparation completed.\n")
