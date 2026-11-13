
#!/usr/bin/env python3

# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 15: Export PDO indicators for the website
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
# ============================================================

from pathlib import Path
import json

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / "data" / "pdo" / "pdo_indices.csv"
OUTPUT = ROOT / "docs" / "data" / "pdo_status.json"

print("\nTRÓPICO Climate Modes Monitor")
print("PDO | Exporting website data\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing data: {INPUT}\n"
        "Run 11_download_pdo_index.py first."
    )

df = pd.read_csv(INPUT, parse_dates=["date"])

if df["date"].isna().any() or df["date"].duplicated().any():
    raise ValueError("Invalid or duplicate PDO dates")

if (df["date"].dt.day != 1).any():
    raise ValueError("Expected monthly dates on the first day")

if "pdo" not in df.columns:
    raise ValueError("Missing pdo column")

df = df.set_index("date").sort_index()

raw = pd.to_numeric(
    df["pdo"],
    errors="coerce"
).replace([np.inf, -np.inf], np.nan)

if raw.notna().sum() < 1000 or (raw.dropna().abs() > 20).any():
    raise ValueError("Unexpected PDO series or invalid values")

calendar = pd.date_range(
    raw.index.min(),
    raw.index.max(),
    freq="MS"
)

monthly = raw.reindex(calendar)
monthly.index.name = "date"

# Trailing windows, with no interpolation.
mean_12m = monthly.rolling(
    12,
    min_periods=12
).mean()

mean_120m = monthly.rolling(
    120,
    min_periods=120
).mean()

series = {
    "pdo": ("Monthly PDO index", monthly),
    "pdo_12m": ("12-month trailing mean", mean_12m),
    "pdo_120m": ("120-month trailing mean", mean_120m),
}

metrics = {}

for key, (name, values) in series.items():

    valid = values.dropna()

    if valid.empty:
        raise ValueError(f"No valid values for {key}")

    latest_date = valid.index[-1]
    latest_value = float(valid.iloc[-1])

    start = latest_date - pd.DateOffset(months=35)

    history = values.reindex(
        pd.date_range(start, latest_date, freq="MS")
    )

    metrics[key] = {
        "name": name,
        "value": round(latest_value, 2),
        "date": latest_date.strftime("%Y-%m-%d"),
        "period": latest_date.strftime("%b %Y"),
        "unit": "index units",
        "sign": (
            "Positive" if latest_value > 0 else
            "Negative" if latest_value < 0 else "Zero"
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
        f"  {key:9s} "
        f"{latest_date:%Y-%m} "
        f"{latest_value:+.2f}"
    )

payload = {
    "mode": "PDO",
    "name": "Pacific Decadal Oscillation",
    "source": "NOAA NCEI / ERSSTv6",
    "source_url": (
        "https://www.ncei.noaa.gov/pub/data/cmb/ersst/"
        "v5/v6/index/ersst.v6.pdo.dat"
    ),
    "metrics": metrics,
}

OUTPUT.parent.mkdir(parents=True, exist_ok=True)

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
    OUTPUT.write_text(content, encoding="utf-8")
    print("\nWeb JSON updated")

print(f"Saved: {OUTPUT}")
print("PDO export completed.\n")
