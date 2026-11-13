
#!/bin/bash

# ============================================================
# TRÓPICO Climate Modes Monitor
# Monthly Update and GitHub Publication
#
# Author: Alejandro Jaramillo-Moreno
# ORCID: 0000-0002-4175-7726
# TRÓPICO Research Group | ICAyCC, UNAM
#
# Climate Modes:
#   ENSO - El Niño-Southern Oscillation
#   QBO  - Quasi-Biennial Oscillation
#   PDO  - Pacific Decadal Oscillation
#   AMV  - Atlantic Multidecadal Variability
#   IOD  - Indian Ocean Dipole
#
# Usage:
#   bash update_github.sh
# ============================================================

set -euo pipefail


# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PYTHON_BIN="${PYTHON:-python}"

cd "$ROOT"


# ------------------------------------------------------------
# Introduction
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo "              TRÓPICO RESEARCH GROUP"
echo "============================================================"
echo ""
echo "              CLIMATE MODES MONITOR"
echo ""
echo "         Monthly Update and Publication"
echo ""
echo "============================================================"
echo ""


# ------------------------------------------------------------
# Verify Python
# ------------------------------------------------------------

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then

    echo "ERROR: Python interpreter not found."
    echo "Activate your Conda environment and try again."

    exit 1

fi


# ------------------------------------------------------------
# Verify Git repository
# ------------------------------------------------------------

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then

    echo "ERROR: This directory is not a Git repository."

    exit 1

fi


# ------------------------------------------------------------
# Verify GitHub remote
# ------------------------------------------------------------

if ! git remote get-url origin >/dev/null 2>&1; then

    echo "ERROR: Git remote 'origin' is missing."

    exit 1

fi


# ------------------------------------------------------------
# Identify current branch
# ------------------------------------------------------------

BRANCH="$(git branch --show-current)"

if [ -z "$BRANCH" ]; then

    echo "ERROR: No active Git branch."

    exit 1

fi


echo "Repository: $ROOT"
echo "Branch:     $BRANCH"
echo "Python:     $PYTHON_BIN"
echo ""


# ------------------------------------------------------------
# Verify Git exclusions for scientific NetCDF data
# ------------------------------------------------------------

IGNORED_DIRECTORIES=(

    "data/pdo/raw/ersst_v6"
    "data/amv/raw/ersst_v6"
    "data/iod/raw/ersst_v6"

)

echo "Checking scientific data exclusions ..."
echo ""

for DIRECTORY in "${IGNORED_DIRECTORIES[@]}"; do

    if ! git check-ignore -q -- "$DIRECTORY/__check__.nc"; then

        echo "ERROR: Missing Git exclusion for:"
        echo "  $DIRECTORY/"
        echo ""
        echo "Add this directory to .gitignore before continuing."

        exit 1

    fi

    # Ignoring files does not untrack previously committed files.
    if [ -n "$(git ls-files -- "$DIRECTORY/")" ]; then

        echo "ERROR: NetCDF cache contains Git-tracked files:"
        echo "  $DIRECTORY/"
        echo ""
        echo "Remove these files from Git tracking before publishing."

        exit 1

    fi

    echo "  OK: $DIRECTORY/"

done


# ------------------------------------------------------------
# Processing pipeline
# ------------------------------------------------------------

SCRIPTS=(

    # --------------------------------------------------------
    # ENSO
    # --------------------------------------------------------

    "scripts/01_download_enso_indices.py"
    "scripts/02_plot_enso_current_conditions.py"
    "scripts/03_plot_enso_historical_evolution.py"
    "scripts/04_plot_enso_roni_vs_oni.py"
    "scripts/05_export_enso_web_data.py"


    # --------------------------------------------------------
    # QBO
    # --------------------------------------------------------

    "scripts/06_download_qbo_indices.py"
    "scripts/07_plot_qbo_current_conditions.py"
    "scripts/08_plot_qbo_historical_evolution.py"
    "scripts/09_plot_qbo_time_height.py"
    "scripts/10_export_qbo_web_data.py"


    # --------------------------------------------------------
    # PDO
    # --------------------------------------------------------

    "scripts/11_download_pdo_index.py"
    "scripts/12_plot_pdo_current_conditions.py"
    "scripts/13_plot_pdo_historical_evolution.py"
    "scripts/14_plot_pdo_spatial_pattern.py"
    "scripts/15_export_pdo_web_data.py"


    # --------------------------------------------------------
    # AMV
    # --------------------------------------------------------

    "scripts/16_download_amv_index.py"
    "scripts/17_plot_amv_current_conditions.py"
    "scripts/18_plot_amv_historical_evolution.py"
    "scripts/19_plot_amv_sst_anomalies.py"
    "scripts/20_export_amv_web_data.py"


    # --------------------------------------------------------
    # IOD
    # --------------------------------------------------------

    "scripts/21_download_iod_indices.py"
    "scripts/22_plot_iod_current_conditions.py"
    "scripts/23_plot_iod_historical_evolution.py"
    "scripts/24_plot_iod_sst_anomalies.py"
    "scripts/25_export_iod_web_data.py"

)


# ------------------------------------------------------------
# Verify all Python scripts exist
# ------------------------------------------------------------

TOTAL=${#SCRIPTS[@]}

echo ""
echo "Checking processing scripts ..."
echo ""

for SCRIPT in "${SCRIPTS[@]}"; do

    if [ ! -f "$SCRIPT" ]; then

        echo "ERROR: Missing script:"
        echo "  $SCRIPT"

        exit 1

    fi

done

echo "All $TOTAL Python scripts found."
echo ""


# ------------------------------------------------------------
# Execute processing pipeline
# ------------------------------------------------------------

for i in "${!SCRIPTS[@]}"; do

    SCRIPT="${SCRIPTS[$i]}"

    COUNT=$((i + 1))

    echo ""
    echo "============================================================"
    echo " PROCESSING [$COUNT/$TOTAL]"
    echo "============================================================"
    echo ""
    echo "$SCRIPT"
    echo ""

    "$PYTHON_BIN" "$SCRIPT"

    echo ""
    echo "Completed: $SCRIPT"
    echo ""

done


# ------------------------------------------------------------
# Verify website data
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " VERIFYING WEBSITE DATA"
echo "============================================================"
echo ""

JSON_FILES=(

    "docs/data/enso_status.json"
    "docs/data/qbo_status.json"
    "docs/data/pdo_status.json"
    "docs/data/amv_status.json"
    "docs/data/iod_status.json"

)

for FILE in "${JSON_FILES[@]}"; do

    if [ ! -s "$FILE" ]; then

        echo "ERROR: Missing or empty JSON file:"
        echo "  $FILE"

        exit 1

    fi

    "$PYTHON_BIN" -m json.tool "$FILE" >/dev/null

    echo "  OK: $FILE"

done


# ------------------------------------------------------------
# Verify all scientific figures
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " VERIFYING SCIENTIFIC FIGURES"
echo "============================================================"
echo ""

FIGURES=(

    # ENSO

    "enso_current_conditions"
    "enso_historical_evolution"
    "enso_roni_vs_oni"

    # QBO

    "qbo_current_conditions"
    "qbo_historical_evolution"
    "qbo_time_height"

    # PDO

    "pdo_current_conditions"
    "pdo_historical_evolution"
    "pdo_spatial_pattern"

    # AMV

    "amv_current_conditions"
    "amv_historical_evolution"
    "amv_sst_anomalies"

    # IOD

    "iod_current_conditions"
    "iod_historical_evolution"
    "iod_sst_anomalies"

)

for FIGURE in "${FIGURES[@]}"; do

    for EXTENSION in png svg; do

        FILE="docs/figures/${FIGURE}.${EXTENSION}"

        if [ ! -s "$FILE" ]; then

            echo "ERROR: Missing or empty figure:"
            echo "  $FILE"

            exit 1

        fi

    done

    echo "  OK: $FIGURE"

done


# ------------------------------------------------------------
# Verify website HTML
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " VERIFYING WEBSITE"
echo "============================================================"
echo ""

if [ ! -s "docs/index.html" ]; then

    echo "ERROR: docs/index.html is missing or empty."

    exit 1

fi

echo "  OK: docs/index.html"
echo ""
echo "All five climate modes have been processed."
echo "All JSON files and figures are present."
echo ""


# ------------------------------------------------------------
# GitHub publication
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " GITHUB | PREPARING PUBLICATION"
echo "============================================================"
echo ""

git add -A


# ------------------------------------------------------------
# Prevent accidental publication of cached NetCDF fields
# ------------------------------------------------------------

STAGED_FILES="$(git diff --cached --name-only --diff-filter=ACMR)"

if echo "$STAGED_FILES" | grep -Eq \
    '^data/(pdo|amv|iod)/raw/ersst_v6/'; then

    echo "ERROR: Cached NetCDF files were staged."
    echo "Publication has been stopped."

    exit 1

fi


# ------------------------------------------------------------
# Show changes
# ------------------------------------------------------------

git status --short

echo ""


# ------------------------------------------------------------
# Commit changes
# ------------------------------------------------------------

if git diff --cached --quiet; then

    echo "No new changes to commit."

else

    COMMIT_MESSAGE="Update Climate Modes Monitor - $(date +%Y-%m-%d)"

    echo "Creating commit:"
    echo "$COMMIT_MESSAGE"
    echo ""

    git commit -m "$COMMIT_MESSAGE"

fi


# ------------------------------------------------------------
# Push to GitHub
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " GITHUB | PUBLISHING"
echo "============================================================"
echo ""

git push -u origin "$BRANCH"


# ------------------------------------------------------------
# Final summary
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo "              TRÓPICO RESEARCH GROUP"
echo "============================================================"
echo ""
echo "         CLIMATE MODES MONITOR UPDATED"
echo ""
echo "   ENSO  : Completed"
echo "   QBO   : Completed"
echo "   PDO   : Completed"
echo "   AMV   : Completed"
echo "   IOD   : Completed"
echo ""
echo "   Climate modes      : 5"
echo "   Scientific figures : 15"
echo "   Python scripts     : 25"
echo ""
echo "============================================================"
echo ""
echo "GitHub publication completed successfully."
echo ""
echo "Website:"
echo "https://tropicoresearch.github.io/climate-modes-monitor/"
echo ""
