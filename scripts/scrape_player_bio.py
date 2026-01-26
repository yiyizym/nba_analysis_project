#!/usr/bin/env python3
"""
Scrape NBA Player Bio data (Height, Weight, Position) for each season.

This script scrapes player physical attributes at season-level granularity.
Bio data doesn't change month to month, so we only need one per season.

URL pattern: https://www.nba.com/stats/players/bio?SeasonType=Regular+Season&Season={season}

Data includes:
- Height, Weight, Age
- Draft Year, Draft Round, Draft Number
- Country, School/College
"""

import sys
import time
import random
import json
import re
from pathlib import Path
from datetime import datetime
from io import StringIO

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer

# Configuration
DELAY_MIN = 10
DELAY_MAX = 15
MAX_RETRIES = 2

# Seasons to scrape
SEASONS = ["2021-22", "2022-23", "2023-24", "2024-25", "2025-26"]

OUTPUT_DIR = Path("data/newly_scraped/player_monthly")
PROGRESS_FILE = OUTPUT_DIR / "player_bio_progress.json"


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": []}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def random_delay(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def construct_bio_url(season, season_type="Regular+Season"):
    """Construct URL for NBA player bio page."""
    base_url = "https://www.nba.com/stats/players/bio"
    url = f"{base_url}?SeasonType={season_type}&Season={season}"
    return url


def extract_player_ids(data_table):
    """Extract player IDs from table links."""
    player_ids = []
    try:
        links = data_table.find_elements("css selector", "a[href*='/player/']")
        for link in links:
            href = link.get_attribute("href")
            if href:
                match = re.search(r'/player/(\d+)', href)
                if match:
                    player_ids.append(match.group(1))
    except Exception as e:
        print(f"    Warning: Could not extract player IDs: {e}")
    return player_ids


def fix_multi_level_header(df):
    """Fix multi-level headers by combining column levels."""
    if df.columns.nlevels > 1:
        new_cols = []
        for col in df.columns:
            if isinstance(col, tuple):
                parts = [str(c).strip() for c in col if str(c).strip() and 'Unnamed' not in str(c)]
                new_cols.append('_'.join(parts) if parts else col[0])
            else:
                new_cols.append(col)
        df.columns = new_cols

    # Clean column names
    df.columns = [
        re.sub(r'\s+', '_', str(c).strip())
        .replace('.', '')
        .replace('%', '_Pct')
        .replace("'", 'ft')
        .replace('"', 'in')
        for c in df.columns
    ]
    return df


def parse_height_to_inches(height_str):
    """Convert height string like '6-10' or '6'10\"' to inches."""
    if pd.isna(height_str) or height_str == '--':
        return None
    try:
        # Handle formats like "6-10" or "6'10"
        height_str = str(height_str).replace("'", "-").replace('"', '')
        parts = height_str.split('-')
        if len(parts) == 2:
            feet = int(parts[0])
            inches = int(parts[1])
            return feet * 12 + inches
    except:
        pass
    return None


def scrape_player_bio(page_scraper, config, url):
    """Scrape player bio from a URL and return DataFrame."""
    try:
        # Navigate to URL
        if not page_scraper.go_to_url(url):
            return None

        # Wait for table to load
        time.sleep(3)

        # Get the stats table
        table = page_scraper.scrape_page_table(
            url,
            config.table_class_name,
            config.pagination_class_name,
            config.dropdown_class_name
        )

        if table is None:
            return None

        # Convert table to DataFrame
        table_html = table.get_attribute('outerHTML')
        dfs = pd.read_html(StringIO(table_html), header=0)

        if not dfs:
            return None

        df = pd.concat(dfs, ignore_index=True)
        df = fix_multi_level_header(df)

        # Extract player IDs
        player_ids = extract_player_ids(table)
        if len(player_ids) == len(df):
            df['PLAYER_ID'] = player_ids
        else:
            print(f"    Warning: Player ID count mismatch ({len(player_ids)} vs {len(df)} rows)")

        # Convert height to inches for easier analysis
        height_col = [c for c in df.columns if 'HEIGHT' in c.upper()]
        if height_col:
            df['Height_Inches'] = df[height_col[0]].apply(parse_height_to_inches)

        return df

    except Exception as e:
        print(f"    Error scraping: {e}")
        return None


def scrape_with_retry(page_scraper, config, url, max_retries=MAX_RETRIES):
    """Scrape with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            df = scrape_player_bio(page_scraper, config, url)
            if df is not None and not df.empty:
                return df
            elif attempt < max_retries:
                wait_time = (attempt + 1) * 30
                print(f"    No data, retry {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
        except Exception as e:
            if attempt < max_retries:
                wait_time = (attempt + 1) * 30
                print(f"    Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise
    return None


def main():
    print("=" * 70)
    print("Player Bio Scraper (Height, Weight, Position)")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seasons: {SEASONS}")
    print()

    progress = load_progress()
    completed_tasks = set(progress["completed"])

    remaining_tasks = len(SEASONS) - len(completed_tasks)

    print(f"Total tasks: {len(SEASONS)}")
    print(f"Already completed: {len(completed_tasks)}")
    print(f"Remaining: {remaining_tasks}")

    if remaining_tasks == 0:
        print("All tasks already completed!")
        return 0

    # Estimated time
    avg_time = (DELAY_MIN + DELAY_MAX) / 2 + 5
    print(f"Estimated time: ~{remaining_tasks * avg_time / 60:.1f} minutes")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    container = DIContainer()
    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_player_bio.log")

        config = container.config()
        page_scraper = container.page_scraper()

        results = {"success": 0, "failed": 0, "skipped": 0}

        for season in SEASONS:
            if season in completed_tasks:
                print(f"  {season}: [skipped]")
                results["skipped"] += 1
                continue

            try:
                url = construct_bio_url(season)
                print(f"  {season}: Scraping...")

                df = scrape_with_retry(page_scraper, config, url)

                if df is not None and not df.empty:
                    df["Season"] = season

                    # Save to output directory
                    season_formatted = season.replace("-", "_")
                    filename = f"player_bio_{season_formatted}.csv"
                    df.to_csv(OUTPUT_DIR / filename, index=False)
                    print(f"  {season}: {len(df)} rows -> {filename}")
                    results["success"] += 1
                else:
                    print(f"  {season}: No data")
                    results["failed"] += 1

                completed_tasks.add(season)
                progress["completed"] = list(completed_tasks)
                save_progress(progress)

            except Exception as e:
                print(f"  {season}: ERROR - {e}")
                results["failed"] += 1

            delay = random_delay()
            print(f"  (waiting {delay:.1f}s)")

        print("\n" + "=" * 70)
        print("COMPLETE")
        print("=" * 70)
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
        print(f"Skipped: {results['skipped']}")
        print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Progress saved.")
        return 1
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            container.web_driver_factory().close_driver()
            print("\nWebDriver closed")
        except:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
