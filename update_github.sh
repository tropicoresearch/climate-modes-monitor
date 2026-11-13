
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

# ------------------------------------------------------------
# Configuration
# ------------------------------------------------------------

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON:-python}"

cd "$ROOT"

echo ""
echo "============================================================"
echo " TRÓPICO | CLIMATE MODES MONITOR"
echo " Monthly Update and GitHub Publication"
echo "============================================================"
echo ""

# ------------------------------------------------------------
# Verify environment
# ------------------------------------------------------------

if ! command -v "$PYTHON_BIN" >/dev/null 2>&1; then
    echo "ERROR: Python interpreter not found: $PYTHON_BIN"
    exit 1
fi

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "ERROR: This directory is not a Git repository."
    exit 1
fi

if ! git remote get-url origin >/dev/null 2>&1; then
    echo "ERROR: Git remote 'origin' is not configured."
    exit 1
fi

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
# ENSO | Download and prepare indices
# ------------------------------------------------------------

echo "============================================================"
echo "[1/5] ENSO | Downloading indices"
echo "============================================================"

"$PYTHON_BIN" scripts/01_download_enso_indices.py

# ------------------------------------------------------------
# ENSO | Current conditions
# ------------------------------------------------------------

echo "============================================================"
echo "[2/5] ENSO | Current conditions"
echo "============================================================"

"$PYTHON_BIN" scripts/02_plot_enso_current_conditions.py

# ------------------------------------------------------------
# ENSO | Historical evolution
# ------------------------------------------------------------

echo "============================================================"
echo "[3/5] ENSO | Historical evolution"
echo "============================================================"

"$PYTHON_BIN" scripts/03_plot_enso_historical_evolution.py

# ------------------------------------------------------------
# ENSO | RONI vs. ONI
# ------------------------------------------------------------

echo "============================================================"
echo "[4/5] ENSO | RONI vs. ONI"
echo "============================================================"

"$PYTHON_BIN" scripts/04_plot_enso_roni_vs_oni.py

# ------------------------------------------------------------
# ENSO | Export web data
# ------------------------------------------------------------

echo "============================================================"
echo "[5/5] ENSO | Exporting website data"
echo "============================================================"

"$PYTHON_BIN" scripts/05_export_enso_web_data.py

# ------------------------------------------------------------
# GitHub | Stage all changes
# ------------------------------------------------------------

echo "============================================================"
echo " GitHub | Preparing publication"
echo "============================================================"

git add -A

echo ""
git status --short
echo ""

# ------------------------------------------------------------
# GitHub | Commit changes
# ------------------------------------------------------------

if git diff --cached --quiet; then

    echo "No new changes to commit."

else

    COMMIT_MESSAGE="Update Climate Modes Monitor - $(date +%Y-%m-%d)"

    git commit -m "$COMMIT_MESSAGE"

fi

# ------------------------------------------------------------
# GitHub | Push
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " GitHub | Pushing changes"
echo "============================================================"

git push -u origin "$BRANCH"

# ------------------------------------------------------------
# Completed
# ------------------------------------------------------------

echo ""
echo "============================================================"
echo " TRÓPICO CLIMATE MODES MONITOR"
echo " Update completed successfully!"
echo "============================================================"
echo ""
echo "Website:"
echo "https://tropicoresearch.github.io/climate-modes-monitor/"
echo ""
