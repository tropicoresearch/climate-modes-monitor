#!/bin/bash

# ============================================================
# TRÓPICO Climate Modes Monitor
# Monthly Update and GitHub Publication
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
# ============================================================

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python}"
cd "$ROOT"

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
    echo "ERROR: Python interpreter not found: $PYTHON_BIN"
    exit 1
}

git rev-parse --is-inside-work-tree >/dev/null 2>&1 || {
    echo "ERROR: Not a Git repository."
    exit 1
}

git remote get-url origin >/dev/null 2>&1 || {
    echo "ERROR: Git remote 'origin' is missing."
    exit 1
}

BRANCH="$(git branch --show-current)"
if [ -z "$BRANCH" ]; then
    echo "ERROR: No active Git branch."
    exit 1
fi

SCRIPTS=(
    # ENSO
    "scripts/01_download_enso_indices.py"
    "scripts/02_plot_enso_current_conditions.py"
    "scripts/03_plot_enso_historical_evolution.py"
    "scripts/04_plot_enso_roni_vs_oni.py"
    "scripts/05_export_enso_web_data.py"

    # QBO
    "scripts/06_download_qbo_indices.py"
    "scripts/07_plot_qbo_current_conditions.py"
    "scripts/08_plot_qbo_historical_evolution.py"
    "scripts/09_plot_qbo_time_height.py"
    "scripts/10_export_qbo_web_data.py"

    # PDO
    "scripts/11_download_pdo_index.py"
    "scripts/12_plot_pdo_current_conditions.py"
    "scripts/13_plot_pdo_historical_evolution.py"
    "scripts/14_plot_pdo_spatial_pattern.py"
    "scripts/15_export_pdo_web_data.py"

    # AMV
    "scripts/16_download_amv_index.py"
    "scripts/17_plot_amv_current_conditions.py"
    "scripts/18_plot_amv_historical_evolution.py"
    "scripts/19_plot_amv_sst_anomalies.py"
    "scripts/20_export_amv_web_data.py"
)

TOTAL=${#SCRIPTS[@]}

echo ""
echo "============================================================"
echo " TRÓPICO | CLIMATE MODES MONITOR"
echo " Monthly Update and GitHub Publication"
echo "============================================================"
echo "Repository: $ROOT"
echo "Branch:     $BRANCH"
echo "Python:     $PYTHON_BIN"
echo ""

for i in "${!SCRIPTS[@]}"; do
    SCRIPT="${SCRIPTS[$i]}"
    echo ""
    echo "============================================================"
    echo " [$((i + 1))/$TOTAL] $SCRIPT"
    echo "============================================================"
    if [ ! -f "$SCRIPT" ]; then
        echo "ERROR: Missing script: $SCRIPT"
        exit 1
    fi
    "$PYTHON_BIN" "$SCRIPT"
done

# Never publish incomplete dashboard assets.
for FILE in \
    docs/data/enso_status.json \
    docs/data/qbo_status.json \
    docs/data/pdo_status.json \
    docs/data/amv_status.json; do
    if [ ! -s "$FILE" ]; then
        echo "ERROR: Missing or empty dashboard data: $FILE"
        exit 1
    fi
done

echo ""
echo "============================================================"
echo " GitHub | Preparing publication"
echo "============================================================"

git add -A

git status --short

# Prevent accidental publication of large raw ERSST caches.
if git diff --cached --name-only | grep -Eq '^data/(amv|pdo)/raw/ersst_v6/'; then
    echo "ERROR: Raw ERSST NetCDF files are staged for GitHub."
    echo "Add data/amv/raw/ersst_v6/ and data/pdo/raw/ersst_v6/ to .gitignore."
    exit 1
fi

if git diff --cached --quiet; then
    echo "No new changes to commit."
else
    git commit -m "Update Climate Modes Monitor - $(date +%Y-%m-%d)"
fi

echo ""
echo "============================================================"
echo " GitHub | Publishing"
echo "============================================================"

git push -u origin "$BRANCH"

echo ""
echo "============================================================"
echo " Update completed successfully"
echo "============================================================"
echo "https://tropicoresearch.github.io/climate-modes-monitor/"
echo ""
