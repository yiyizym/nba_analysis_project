#!/bin/bash
# Run all player data scrapers in sequence
# Usage: ./scripts/run_all_player_scrapers.sh

set -e

cd "$(dirname "$0")/.."
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

echo "=========================================="
echo "NBA Player Data Scraping Pipeline"
echo "=========================================="
echo "Started: $(date)"
echo ""

# 1. Player Stats (Traditional + Advanced)
echo "[1/6] Player Stats (Traditional + Advanced)..."
python scripts/scrape_player_stats_monthly.py
echo ""

# 2. Player Bio
echo "[2/6] Player Bio..."
python scripts/scrape_player_bio.py
echo ""

# 3. Player Tracking (Touches)
echo "[3/6] Player Tracking (Touches)..."
python scripts/scrape_player_tracking_monthly.py
echo ""

# 4. Player PlayType (11 categories)
echo "[4/6] Player PlayType (11 categories)..."
python scripts/scrape_player_playtype_monthly.py
echo ""

# 5. Player Shooting
echo "[5/6] Player Shooting..."
python scripts/scrape_player_shooting_monthly.py
echo ""

# 6. Player Defense
echo "[6/6] Player Defense..."
python scripts/scrape_player_defense_monthly.py
echo ""

echo "=========================================="
echo "ALL SCRAPING COMPLETE"
echo "=========================================="
echo "Finished: $(date)"
echo ""

# Build features and classify
echo "Building player features..."
python scripts/build_player_features_monthly.py
echo ""

echo "Classifying players..."
python scripts/classify_players.py
echo ""

echo "=========================================="
echo "PIPELINE COMPLETE"
echo "=========================================="
