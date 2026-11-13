
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 20: Export AMV data for the website
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Source: NOAA NCEI / ERSSTv6
#
# Observed North Atlantic SST anomalies.
# Not an isolated estimate of internal AMV.
# ============================================================

from pathlib import Path
import json

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = (
    ROOT / "data" / "amv" /
    "north_atlantic_ssta.csv"
)

OUTPUT = ROOT / "docs" / "data" / "amv_status.json"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

HISTORY_MONTHS = 60

INDICES = {
    "na_ssta": "North Atlantic SST Anomaly",
    "na_ssta_12m": "12-month trailing mean",
    "na_ssta_120m": "120-month trailing mean",
}


# ------------------------------------------------------------
# Read observations
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("AMV | Exporting website data\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing dataset: {INPUT}\n"
        "Run 16_download_amv_index.py first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
).sort_index()

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError("Invalid or duplicate dates")

if (df.index.day != 1).any():
    raise ValueError("Expected monthly timestamps")

for column in INDICES:

    if column not in df.columns:
        raise ValueError(f"Missing column: {column}")

    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

if df["na_ssta"].notna().sum() < 1800:
    raise ValueError("Unexpectedly short SST record")


# ------------------------------------------------------------
# Prepare indicators
# ------------------------------------------------------------

metrics = {}

for key, name in INDICES.items():

    series = df[key]
    valid = series.dropna()

    if valid.empty:
        raise ValueError(f"No valid observations: {key}")

    last_date = valid.index[-1]
    last_value = float(valid.iloc[-1])

    start_date = last_date - pd.DateOffset(
        months=HISTORY_MONTHS - 1
    )

    calendar = pd.date_range(
        start=start_date,
        end=last_date,
        freq="MS"
    )

    history = series.reindex(calendar)

    metrics[key] = {
        "name": name,
        "value": round(last_value, 3),
        "unit": "°C",
        "date": last_date.strftime("%Y-%m-%d"),
        "period": last_date.strftime("%b %Y"),
        "sign": (
            "Positive" if last_value > 0 else
            "Negative" if last_value < 0 else
            "Zero"
        ),
        "history": [
            {
                "date": date.strftime("%Y-%m-%d"),
                "value": (
                    round(float(value), 3)
                    if pd.notna(value) else None
                ),
            }
            for date, value in history.items()
        ],
    }

    print(
        f"{key:15s} "
        f"{last_date:%Y-%m} "
        f"{last_value:+.3f} °C"
    )


# ------------------------------------------------------------
# Assemble JSON
# ------------------------------------------------------------

payload = {
    "mode": "AMV",
    "name": "Atlantic Multidecadal Variability",
    "indicator": "Observed North Atlantic SST Anomaly",
    "region": "North Atlantic (0–60°N)",
    "source": "NOAA NCEI / ERSSTv6",
    "source_url": (
        "https://www.ncei.noaa.gov/pub/data/cmb/"
        "ersst/v5/v6/index/ersst.v6.amo.dat"
    ),
    "methodological_note": (
        "Observed North Atlantic SST anomalies include "
        "internal variability and externally forced changes. "
        "They are not an isolated internal AMV index."
    ),
    "metrics": metrics,
}


# ------------------------------------------------------------
# Export JSON
# ------------------------------------------------------------

content = (
    json.dumps(
        payload,
        ensure_ascii=False,
        indent=2,
        allow_nan=False
    ) + "\n"
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

print(f"\nSaved: {OUTPUT}")

print("\nAMV web data export completed.\n")
