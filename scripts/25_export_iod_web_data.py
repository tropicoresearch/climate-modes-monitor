
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 25: Export IOD Data for the Website
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA Climate Prediction Center / ERSSTv6
#
# Published indices:
#   DMI   : Dipole Mode Index
#   WTIO  : Western Tropical Indian Ocean SSTA
#   SETIO : Southeastern Tropical Indian Ocean SSTA
# ============================================================

from pathlib import Path
import json

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Directories
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "iod" / "iod_indices.csv"

OUTPUT = ROOT / "docs" / "data" / "iod_status.json"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

HISTORY_MONTHS = 60

INDICES = {
    "dmi": {
        "name": "Dipole Mode Index",
        "description": (
            "Western minus southeastern tropical "
            "Indian Ocean SST anomalies"
        ),
    },
    "wtio": {
        "name": "Western Tropical Indian Ocean",
        "description": (
            "SST anomaly in the western IOD region"
        ),
    },
    "setio": {
        "name": "Southeastern Tropical Indian Ocean",
        "description": (
            "SST anomaly in the southeastern IOD region"
        ),
    },
}


# ------------------------------------------------------------
# Read observations
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("IOD | Exporting Website Data\n")

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
    raise ValueError(
        "Invalid or duplicate IOD observation dates"
    )

if (df.index.day != 1).any():
    raise ValueError(
        "Expected monthly first-of-month timestamps"
    )


# ------------------------------------------------------------
# Validate indices
# ------------------------------------------------------------

for name in INDICES:

    if name not in df.columns:
        raise ValueError(
            f"Missing column: {name}"
        )

    df[name] = pd.to_numeric(
        df[name],
        errors="coerce"
    ).replace(
        [np.inf, -np.inf],
        np.nan
    )

    valid = df[name].dropna()

    if len(valid) < 700:
        raise ValueError(
            f"Unexpectedly short series: {name}"
        )

    if (valid.abs() > 15).any():
        raise ValueError(
            f"Unrealistic values in {name}"
        )


# ------------------------------------------------------------
# Check index consistency
# ------------------------------------------------------------

common = df[
    ["dmi", "wtio", "setio"]
].dropna()

if common.empty:
    raise ValueError(
        "No common IOD observations"
    )

difference = (
    common["wtio"]
    - common["setio"]
    - common["dmi"]
).abs()

if (difference > 0.06).any():

    date = difference.idxmax()

    raise ValueError(
        f"Inconsistent published DMI at {date:%Y-%m}"
    )


# ------------------------------------------------------------
# Latest common observation
# ------------------------------------------------------------

latest_date = common.index[-1]

print(
    f"Latest common observation: "
    f"{latest_date:%B %Y}"
)

# Preserve complete monthly calendar
calendar = pd.date_range(
    df.index.min(),
    latest_date,
    freq="MS"
)

df = df.reindex(calendar)
df.index.name = "date"


# ------------------------------------------------------------
# Export metrics
# ------------------------------------------------------------

metrics = {}

for key, config in INDICES.items():

    series = df[key]

    value = float(series.loc[latest_date])

    start_date = (
        latest_date
        - pd.DateOffset(months=HISTORY_MONTHS - 1)
    )

    history_calendar = pd.date_range(
        start=start_date,
        end=latest_date,
        freq="MS"
    )

    history = series.reindex(history_calendar)

    if value > 0:
        sign = "Positive"
    elif value < 0:
        sign = "Negative"
    else:
        sign = "Zero"

    metrics[key] = {
        "name": config["name"],
        "description": config["description"],
        "value": round(value, 2),
        "unit": "°C",
        "date": latest_date.strftime("%Y-%m-%d"),
        "period": latest_date.strftime("%b %Y"),
        "sign": sign,
        "history": [
            {
                "date": date.strftime("%Y-%m-%d"),
                "value": (
                    round(float(item), 2)
                    if pd.notna(item)
                    else None
                ),
            }
            for date, item in history.items()
        ],
    }

    print(
        f"{key.upper():8s} "
        f"{value:+.2f} °C "
        f"({sign})"
    )


# ------------------------------------------------------------
# Assemble JSON
# ------------------------------------------------------------

payload = {
    "mode": "IOD",
    "name": "Indian Ocean Dipole",
    "indicator": "Dipole Mode Index",
    "source": "NOAA Climate Prediction Center",
    "dataset": "ERSSTv6",
    "climatology": "1991–2020",
    "source_url": (
        "https://www.cpc.ncep.noaa.gov/products/"
        "international/ocean_monitoring/indian/IODMI/"
        "mnth.ersstv6.clim19912020.dmi_current.txt"
    ),
    "last_observation": latest_date.strftime("%Y-%m-%d"),
    "definition": "DMI = WTIO - SETIO",
    "regions": {
        "wtio": {
            "name": "Western Tropical Indian Ocean",
            "longitude": [50, 70],
            "latitude": [-10, 10],
        },
        "setio": {
            "name": "Southeastern Tropical Indian Ocean",
            "longitude": [90, 110],
            "latitude": [-10, 0],
        },
    },
    "metrics": metrics,
    "interpretation": (
        "The sign of a monthly DMI observation describes "
        "the zonal SST anomaly gradient. A persistent "
        "IOD event cannot be diagnosed from one month alone."
    ),
}


# ------------------------------------------------------------
# Save JSON
# ------------------------------------------------------------

content = (
    json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        allow_nan=False
    )
    + "\n"
)

if (
    OUTPUT.exists()
    and OUTPUT.read_text(encoding="utf-8") == content
):

    print("\nWeb JSON unchanged")

else:

    OUTPUT.write_text(
        content,
        encoding="utf-8"
    )

    print("\nWeb JSON updated")


# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

print("\n" + "-" * 60)
print(f"Saved: {OUTPUT}")
print("-" * 60)

print("\nIOD website data export completed.\n")
