
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

echo ""
echo "============================================================"
echo " TRÓPICO CLIMATE MODES MONITOR"
echo " Monthly Update and GitHub Publication"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# Verify environment
# ------------------------------------------------------------

command -v "$PYTHON_BIN" >/dev/null 2>&1 || {
    echo "ERROR: Python interpreter not found."
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

echo "Repository: $ROOT"
echo "Python:     $PYTHON_BIN"
echo "Branch:     $BRANCH"
echo ""

# ------------------------------------------------------------
# Processing pipeline
# ------------------------------------------------------------

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
)

TOTAL=${#SCRIPTS[@]}
COUNT=0

for SCRIPT in "${SCRIPTS[@]}"; do

    COUNT=$((COUNT + 1))

    echo ""
    echo "============================================================"
    echo " [$COUNT/$TOTAL] $SCRIPT"
    echo "============================================================"
    echo ""

    if [ ! -f "$SCRIPT" ]; then
        echo "ERROR: Missing script: $SCRIPT"
        exit 1
    fi

    "$PYTHON_BIN" "$SCRIPT"

done

# ------------------------------------------------------------
# GitHub publication
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " Preparing GitHub publication"
echo "============================================================"
echo ""

git add -A
git status --short

if git diff --cached --quiet; then

    echo ""
    echo "No new changes to commit."

else

    COMMIT_MESSAGE="Update Climate Modes Monitor - $(date +%Y-%m-%d)"

    git commit -m "$COMMIT_MESSAGE"

fi

echo ""
echo "============================================================"
echo " Publishing to GitHub"
echo "============================================================"
echo ""

git push -u origin "$BRANCH"

echo ""
echo "============================================================"
echo " TRÓPICO CLIMATE MODES MONITOR"
echo " Update completed successfully"
echo "============================================================"
echo ""
echo "https://tropicoresearch.github.io/climate-modes-monitor/"
echo ""
