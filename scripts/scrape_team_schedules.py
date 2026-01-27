#!/usr/bin/env python3
"""
Scrape NBA team schedules for the current season.

This script scrapes the full season schedule for all 30 NBA teams
and saves it to a single CSV file for local caching.

Since schedules are fixed at the start of the season, this only
needs to be run once per season (or when games are postponed).

Usage:
    python scripts/scrape_team_schedules.py
    python scripts/scrape_team_schedules.py --season 2025-26
"""

import sys
import time
import random
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

import pandas as pd

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
SCHEDULE_DIR = Path("data/schedules")
DELAY_MIN = 3
DELAY_MAX = 6
DELAY_BETWEEN_TEAMS = 10

# Team mapping
TEAM_ID_TO_ABBREV = {
    1610612737: 'ATL', 1610612738: 'BOS', 1610612751: 'BKN',
    1610612766: 'CHA', 1610612741: 'CHI', 1610612739: 'CLE',
    1610612742: 'DAL', 1610612743: 'DEN', 1610612765: 'DET',
    1610612744: 'GSW', 1610612745: 'HOU', 1610612754: 'IND',
    1610612746: 'LAC', 1610612747: 'LAL', 1610612763: 'MEM',
    1610612748: 'MIA', 1610612749: 'MIL', 1610612750: 'MIN',
    1610612740: 'NOP', 1610612752: 'NYK', 1610612760: 'OKC',
    1610612753: 'ORL', 1610612755: 'PHI', 1610612756: 'PHX',
    1610612757: 'POR', 1610612758: 'SAC', 1610612759: 'SAS',
    1610612761: 'TOR', 1610612762: 'UTA', 1610612764: 'WAS'
}

ALL_TEAM_IDS = list(TEAM_ID_TO_ABBREV.keys())


def random_delay(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    """Sleep for random duration."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def scrape_team_schedule(team_id: int, season: str, scraper) -> Optional[pd.DataFrame]:
    """
    Scrape a single team's schedule.

    Args:
        team_id: NBA team ID
        season: Season string (e.g., "2025-26")
        scraper: Page scraper instance

    Returns:
        DataFrame with schedule data, or None if failed.
    """
    abbrev = TEAM_ID_TO_ABBREV.get(team_id, 'UNK')
    url = f"https://www.nba.com/team/{team_id}/schedule?season={season}"

    try:
        scraper.go_to_url(url)
        time.sleep(3)  # Wait for page to load

        # Get the page source and parse schedule table
        # The schedule page typically has game cards with date, opponent, result
        # This is a simplified approach - actual implementation may need
        # to handle dynamic content loading

        # Try to find schedule elements
        games = []

        # Look for schedule items
        try:
            schedule_items = scraper.get_elements_by_class("ScheduleLeagueNextGame_slng__ubADo")
            if not schedule_items:
                schedule_items = scraper.get_elements_by_class("Schedule")
        except:
            pass

        # Alternative: Use NBA API endpoint directly
        # The schedule data might be better obtained via stats.nba.com API

        return None  # Placeholder - needs actual implementation

    except Exception as e:
        print(f"    Error scraping {abbrev}: {e}")
        return None


def scrape_schedule_via_api(season: str) -> Optional[pd.DataFrame]:
    """
    Scrape schedule data via NBA.com Stats API.

    The NBA Stats API provides schedule data at:
    https://stats.nba.com/stats/leaguegamefinder

    Args:
        season: Season string (e.g., "2025-26")

    Returns:
        DataFrame with all games, or None if failed.
    """
    import requests

    # Convert season format: "2025-26" -> "2025-26"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://www.nba.com'
    }

    # Use the leaguegamefinder endpoint
    url = "https://stats.nba.com/stats/leaguegamefinder"
    params = {
        "Season": season,
        "SeasonType": "Regular Season",
        "LeagueID": "00"
    }

    try:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Parse the response
        result_sets = data.get('resultSets', [])
        if not result_sets:
            return None

        headers = result_sets[0].get('headers', [])
        rows = result_sets[0].get('rowSet', [])

        if not headers or not rows:
            return None

        df = pd.DataFrame(rows, columns=headers)

        # Select relevant columns
        columns = ['TEAM_ID', 'TEAM_ABBREVIATION', 'GAME_ID', 'GAME_DATE', 'MATCHUP', 'WL']
        df = df[[c for c in columns if c in df.columns]]

        # Determine home/away from MATCHUP
        df['IS_HOME'] = df['MATCHUP'].str.contains(' vs. ')

        return df

    except Exception as e:
        print(f"Error fetching schedule via API: {e}")
        return None


def create_schedule_from_boxscores(season_dir: str = "2025_26") -> Optional[pd.DataFrame]:
    """
    Alternative: Create schedule from existing scraped data.

    If we have team_advanced data for multiple months, we can infer
    games played from the cumulative W-L records.

    Args:
        season_dir: Season directory name

    Returns:
        DataFrame with inferred schedule info, or None.
    """
    # This is a fallback method using existing data
    return None


def main():
    parser = argparse.ArgumentParser(description='Scrape NBA team schedules')
    parser.add_argument('--season', type=str, default='2025-26',
                        help='Season to scrape (e.g., 2025-26)')

    args = parser.parse_args()

    print("=" * 70)
    print("NBA Team Schedule Scraper")
    print("=" * 70)
    print(f"Season: {args.season}")
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)

    # Try API method first
    print("Attempting to fetch schedule via NBA Stats API...")
    schedule_df = scrape_schedule_via_api(args.season)

    if schedule_df is not None and not schedule_df.empty:
        # Save to file
        season_clean = args.season.replace('-', '_')
        output_file = SCHEDULE_DIR / f"schedule_{season_clean}.csv"
        schedule_df.to_csv(output_file, index=False)

        print(f"\nSuccess! Saved {len(schedule_df)} game records to {output_file}")

        # Show sample
        print("\nSample data:")
        print(schedule_df.head(10).to_string())

        return 0
    else:
        print("API method failed.")
        print("\nNote: The NBA Stats API may require additional authentication")
        print("or the schedule data may not be available through this endpoint.")
        print("\nAlternative approaches:")
        print("1. Manually download schedule CSV from basketball-reference.com")
        print("2. Use nba_api Python package")
        print("3. Scrape individual team pages with Selenium")

        return 1


if __name__ == "__main__":
    sys.exit(main())
