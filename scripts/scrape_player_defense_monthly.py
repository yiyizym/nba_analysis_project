#!/usr/bin/env python3
"""
Scrape NBA Player Defense stats for monthly periods.

This script scrapes player defensive statistics with monthly granularity.

URL pattern: https://www.nba.com/stats/players/{category}?SeasonType=Regular+Season&Season={season}&Month={month}

Defense categories:
- defense-dash-overall: Overall defensive stats (DFG%, contested shots)
- defense-dash-lt6: Defense at the rim (<6 ft) - rim protection
- hustle: Hustle stats (deflections, charges drawn, loose balls)
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

# Defense categories
DEFENSE_CATEGORIES = {
    "defense-dash-overall": "player_defense_overall",
    "defense-dash-lt6": "player_defense_lt6",
    "hustle": "player_hustle",
}

# Seasons to scrape (5 seasons)
SEASONS = {
    "2021-22": {
        "months": {
            "october": "1",
            "november": "2",
            "december": "3",
            "january": "4",
            "february": "5",
            "march": "6",
            "april": "7",
        },
        "output_dir": "data/newly_scraped/player_monthly/2021_22"
    },
    "2022-23": {
        "months": {
            "october": "1",
            "november": "2",
            "december": "3",
            "january": "4",
            "february": "5",
            "march": "6",
            "april": "7",
        },
        "output_dir": "data/newly_scraped/player_monthly/2022_23"
    },
    "2023-24": {
        "months": {
            "october": "1",
            "november": "2",
            "december": "3",
            "january": "4",
            "february": "5",
            "march": "6",
            "april": "7",
        },
        "output_dir": "data/newly_scraped/player_monthly/2023_24"
    },
    "2024-25": {
        "months": {
            "october": "1",
            "november": "2",
            "december": "3",
            "january": "4",
            "february": "5",
            "march": "6",
            "april": "7",
        },
        "output_dir": "data/newly_scraped/player_monthly/2024_25"
    },
    "2025-26": {
        "months": {
            "october": "1",
            "november": "2",
            "december": "3",
            "january": "4",
        },
        "output_dir": "data/newly_scraped/player_monthly/2025_26"
    },
}

PROGRESS_FILE = Path("data/newly_scraped/player_monthly/player_defense_progress.json")


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": []}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def get_task_key(season, category, month):
    return f"{season}_{category}_{month}"


def random_delay(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def construct_defense_url(category, season, month_value, season_type="Regular+Season"):
    """Construct URL for NBA player defense page."""
    base_url = f"https://www.nba.com/stats/players/{category}"
    url = f"{base_url}?SeasonType={season_type}&Season={season}&Month={month_value}"
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
        print(f"      Warning: Could not extract player IDs: {e}")
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
        .replace('+', '_Plus')
        .replace('-', '_')
        .replace('<', 'lt')
        .replace('>', 'gt')
        for c in df.columns
    ]
    return df


def scrape_defense_stats(page_scraper, config, url):
    """Scrape player defense from a URL and return DataFrame."""
    try:
        if not page_scraper.go_to_url(url):
            return None

        time.sleep(3)

        table = page_scraper.scrape_page_table(
            url,
            config.table_class_name,
            config.pagination_class_name,
            config.dropdown_class_name
        )

        if table is None:
            return None

        table_html = table.get_attribute('outerHTML')
        dfs = pd.read_html(StringIO(table_html), header=0)

        if not dfs:
            return None

        df = pd.concat(dfs, ignore_index=True)
        df = fix_multi_level_header(df)

        player_ids = extract_player_ids(table)
        if len(player_ids) == len(df):
            df['PLAYER_ID'] = player_ids
        else:
            print(f"      Warning: Player ID count mismatch ({len(player_ids)} vs {len(df)} rows)")

        return df

    except Exception as e:
        print(f"      Error scraping: {e}")
        return None


def scrape_with_retry(page_scraper, config, url, max_retries=MAX_RETRIES):
    """Scrape with retry logic."""
    for attempt in range(max_retries + 1):
        try:
            df = scrape_defense_stats(page_scraper, config, url)
            if df is not None and not df.empty:
                return df
            elif attempt < max_retries:
                wait_time = (attempt + 1) * 30
                print(f"      No data, retry {attempt + 1}/{max_retries} after {wait_time}s")
                time.sleep(wait_time)
        except Exception as e:
            if attempt < max_retries:
                wait_time = (attempt + 1) * 30
                print(f"      Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise
    return None


def main():
    print("=" * 70)
    print("Player Defense Scraper (Defense Dash + Hustle, Monthly)")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categories: {list(DEFENSE_CATEGORIES.keys())}")
    print()

    progress = load_progress()
    completed_tasks = set(progress["completed"])

    total_tasks = sum(
        len(DEFENSE_CATEGORIES) * len(season_info["months"])
        for season_info in SEASONS.values()
    )
    remaining_tasks = total_tasks - len(completed_tasks)

    print(f"Total tasks: {total_tasks}")
    print(f"Already completed: {len(completed_tasks)}")
    print(f"Remaining: {remaining_tasks}")

    if remaining_tasks == 0:
        print("All tasks already completed!")
        return 0

    avg_time = (DELAY_MIN + DELAY_MAX) / 2 + 5
    print(f"Estimated time: ~{remaining_tasks * avg_time / 60:.0f} minutes")
    print()

    container = DIContainer()
    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_player_defense.log")

        config = container.config()
        page_scraper = container.page_scraper()

        results = {"success": 0, "failed": 0, "skipped": 0}

        for season, season_info in SEASONS.items():
            output_dir = Path(season_info["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n{'='*60}")
            print(f"Season: {season}")
            print(f"Output: {output_dir}")
            print("=" * 60)

            for category, file_prefix in DEFENSE_CATEGORIES.items():
                print(f"\n  {category}:")

                for month_name, month_value in season_info["months"].items():
                    task_key = get_task_key(season, category, month_name)

                    if task_key in completed_tasks:
                        print(f"    {month_name}: [skipped]")
                        results["skipped"] += 1
                        continue

                    try:
                        url = construct_defense_url(category, season, month_value)
                        print(f"    {month_name}: Scraping...")

                        df = scrape_with_retry(page_scraper, config, url)

                        if df is not None and not df.empty:
                            df["Month"] = month_name
                            df["Season"] = season
                            df["StatCategory"] = category

                            filename = f"{file_prefix}_{month_name}.csv"
                            df.to_csv(output_dir / filename, index=False)
                            print(f"    {month_name}: {len(df)} rows -> {filename}")
                            results["success"] += 1
                        else:
                            print(f"    {month_name}: No data")
                            results["failed"] += 1

                        completed_tasks.add(task_key)
                        progress["completed"] = list(completed_tasks)
                        save_progress(progress)

                    except Exception as e:
                        print(f"    {month_name}: ERROR - {e}")
                        results["failed"] += 1

                    delay = random_delay()
                    print(f"    (waiting {delay:.1f}s)")

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
