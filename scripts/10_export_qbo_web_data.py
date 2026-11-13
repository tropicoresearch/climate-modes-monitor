
# ============================================================
# TRÓPICO Climate Modes Monitor
# Script 10: Export QBO data for the website
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

INPUT = ROOT / "data" / "qbo" / "qbo_indices.csv"
PROFILE = ROOT / "data" / "qbo" / "qbo_vertical_profiles.csv"

OUTPUT = ROOT / "docs" / "data" / "qbo_status.json"

OUTPUT.parent.mkdir(parents=True, exist_ok=True)


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

HISTORY_MONTHS = 60

INDICES = {
    "qbo_u30": {
        "name": "Equatorial Zonal Wind at 30 hPa",
        "pressure_hpa": 30,
    },
    "qbo_u50": {
        "name": "Equatorial Zonal Wind at 50 hPa",
        "pressure_hpa": 50,
    },
}


# ------------------------------------------------------------
# Read NOAA data
# ------------------------------------------------------------

print("\nTRÓPICO Climate Modes Monitor")
print("QBO | Exporting website data\n")

if not INPUT.exists():
    raise FileNotFoundError(
        f"Missing QBO data: {INPUT}"
    )

df = pd.read_csv(
    INPUT,
    parse_dates=["date"],
    index_col="date"
).sort_index()

if df.index.hasnans or df.index.has_duplicates:
    raise ValueError("Invalid QBO observation dates")

metrics = {}

for key, config in INDICES.items():

    if key not in df.columns:
        raise ValueError(f"Missing column: {key}")

    series = pd.to_numeric(
        df[key],
        errors="coerce"
    ).replace([np.inf, -np.inf], np.nan)

    valid = series.dropna()

    if valid.empty:
        raise ValueError(f"No observations for {key}")

    if (valid.abs() > 100).any():
        raise ValueError(f"Unrealistic wind in {key}")

    latest_date = valid.index[-1]
    latest_value = float(valid.iloc[-1])

    if latest_value > 0:
        regime = "Westerly"
    elif latest_value < 0:
        regime = "Easterly"
    else:
        regime = "Zero wind"

    # Preserve the monthly calendar, including missing values.
    start = latest_date - pd.DateOffset(
        months=HISTORY_MONTHS - 1
    )

    calendar = pd.date_range(
        start=start,
        end=latest_date,
        freq="MS"
    )

    history = series.reindex(calendar)

    metrics[key] = {
        "name": config["name"],
        "pressure_hpa": config["pressure_hpa"],
        "value": round(latest_value, 2),
        "unit": "m/s",
        "date": latest_date.strftime("%Y-%m-%d"),
        "period": latest_date.strftime("%b %Y"),
        "wind_regime_at_level": regime,
        "history": [
            {
                "date": date.strftime("%Y-%m-%d"),
                "value": (
                    round(float(value), 2)
                    if pd.notna(value) else None
                ),
            }
            for date, value in history.items()
        ],
    }

    print(
        f"{key}: {latest_value:+.2f} m/s "
        f"({regime}, {latest_date:%Y-%m})"
    )


# ------------------------------------------------------------
# Read KIT vertical profiles
# ------------------------------------------------------------

if not PROFILE.exists():
    raise FileNotFoundError(
        f"Missing vertical profiles: {PROFILE}\n"
        "Run 09_plot_qbo_time_height.py first."
    )

profiles = pd.read_csv(
    PROFILE,
    parse_dates=["date"],
    index_col="date"
).sort_index()

if profiles.index.hasnans or profiles.index.has_duplicates:
    raise ValueError("Invalid profile dates")

pressure_columns = []

for column in profiles.columns:

    try:
        pressure = float(column)
    except ValueError:
        continue

    if 10 <= pressure <= 100:
        profiles[column] = pd.to_numeric(
            profiles[column],
            errors="coerce"
        )

        pressure_columns.append((pressure, column))

pressure_columns.sort()

if len(pressure_columns) < 10:
    raise ValueError("Insufficient pressure levels")

columns = [column for _, column in pressure_columns]

counts = profiles[columns].notna().sum(axis=1)

eligible = profiles.loc[counts >= 10]

if eligible.empty:
    raise ValueError("No sufficiently complete profile")

profile_date = eligible.index[-1]
profile = eligible.loc[profile_date]

levels = []

for pressure, column in pressure_columns:

    value = profile[column]

    levels.append({
        "pressure_hpa": pressure,
        "zonal_wind_ms": (
            round(float(value), 2)
            if pd.notna(value) else None
        ),
    })


# ------------------------------------------------------------
# Assemble JSON
# ------------------------------------------------------------

payload = {
    "mode": "QBO",
    "name": "Quasi-Biennial Oscillation",
    "index_source": "NOAA Climate Prediction Center",
    "profile_source": "KIT / FU Berlin Singapore radiosondes",
    "metrics": metrics,
    "vertical_profile": {
        "date": profile_date.strftime("%Y-%m-%d"),
        "period": profile_date.strftime("%b %Y"),
        "location": "Singapore",
        "levels": levels,
    },
}


# ------------------------------------------------------------
# Save only if content changed
# ------------------------------------------------------------

content = json.dumps(
    payload,
    indent=2,
    ensure_ascii=False,
    allow_nan=False
) + "\n"

if (
    OUTPUT.exists()
    and OUTPUT.read_text(encoding="utf-8") == content
):
    print("\nWeb JSON unchanged")
else:
    OUTPUT.write_text(content, encoding="utf-8")
    print("\nWeb JSON updated")

print(f"Saved: {OUTPUT}")
print("\nQBO web data export completed.\n")
