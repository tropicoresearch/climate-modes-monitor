
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 05: Export ENSO indicators for the website
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
# ============================================================

from pathlib import Path
import json

import numpy as np
import pandas as pd


# ------------------------------------------------------------
# Paths
# ------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[1]

INPUT = ROOT / "data" / "enso" / "enso_indices.csv"
OUTPUT = ROOT / "docs" / "data" / "enso_status.json"


# ------------------------------------------------------------
# Seasonal definitions
# ------------------------------------------------------------

SEASONS = {
    1: "DJF",
    2: "JFM",
    3: "FMA",
    4: "MAM",
    5: "AMJ",
    6: "MJJ",
    7: "JJA",
    8: "JAS",
    9: "ASO",
    10: "SON",
    11: "OND",
    12: "NDJ",
}


INDEX_CONFIG = {
    "roni": {
        "name": "Relative Oceanic Niño Index",
        "frequency": "3-month",
    },
    "nino34": {
        "name": "Niño 3.4 SST Anomaly",
        "frequency": "monthly",
    },
    "oni": {
        "name": "Oceanic Niño Index",
        "frequency": "3-month",
    },
}


# ------------------------------------------------------------
# Read data
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("ENSO | Exporting website data\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing {INPUT}. Run script 01 first."
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"]
)

if df["date"].isna().any() or df["date"].duplicated().any():
    raise ValueError("Invalid or duplicate observation dates")

df = df.set_index("date").sort_index()


# ------------------------------------------------------------
# Prepare observations
# ------------------------------------------------------------

metrics = {}

for key, config in INDEX_CONFIG.items():

    if key not in df.columns:
        raise ValueError(f"Missing index column: {key}")

    values = pd.to_numeric(
        df[key],
        errors="coerce"
    )

    values = (
        values.replace([np.inf, -np.inf], np.nan)
        .dropna()
    )

    if values.empty:
        raise ValueError(f"No valid values for {key}")

    latest_date = values.index[-1]
    latest_value = float(values.iloc[-1])

    if config["frequency"] == "3-month":
        period = (
            f"{SEASONS[latest_date.month]} "
            f"{latest_date.year}"
        )
    else:
        period = latest_date.strftime("%b %Y")

    metrics[key] = {
        "name": config["name"],
        "value": round(latest_value, 2),
        "date": latest_date.strftime("%Y-%m-%d"),
        "period": period,
        "frequency": config["frequency"],
        "unit": "°C",
        "history": [
            {
                "date": d.strftime("%Y-%m-%d"),
                "value": round(float(v), 2),
            }
            for d, v in values.tail(36).items()
        ],
    }

    print(
        f"  {key:8s} "
        f"{period:12s} "
        f"{latest_value:+.2f} °C"
    )


# ------------------------------------------------------------
# Export JSON
# ------------------------------------------------------------

payload = {
    "source": "NOAA Climate Prediction Center",
    "source_url": (
        "https://www.cpc.ncep.noaa.gov/data/indices/"
    ),
    "metrics": metrics,
}

OUTPUT.parent.mkdir(
    parents=True,
    exist_ok=True
)

content = (
    json.dumps(
        payload,
        ensure_ascii=False,
        indent=2
    ) + "\n"
)

if (
    OUTPUT.exists()
    and OUTPUT.read_text(encoding="utf-8") == content
):
    print("\nWeb data unchanged")
else:
    OUTPUT.write_text(
        content,
        encoding="utf-8"
    )
    print("\nWeb data updated")

print(f"Saved: {OUTPUT}")
print("\nENSO web data export completed.\n")
