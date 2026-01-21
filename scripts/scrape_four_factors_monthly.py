#!/usr/bin/env python3
"""
Scrape four-factors monthly data for TCI model.

Four Factors (Dean Oliver):
1. eFG% - Effective Field Goal Percentage (already in team_advanced)
2. TOV% - Turnover Percentage (already in team_advanced)
3. OREB% - Offensive Rebound Percentage (already in team_advanced)
4. FT Rate - Free Throw Rate (FTA/FGA) - NEED TO SCRAPE

This script scrapes the four-factors stat category to get FT Rate.
"""

import sys
import time
import random
import json
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer

# Configuration
DELAY_MIN = 10
DELAY_MAX = 15
DELAY_CATEGORY = 20
MAX_RETRIES = 2

# Seasons and months to scrape
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
        "output_dir": "data/newly_scraped/tracking_monthly/2021_22"
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
        "output_dir": "data/newly_scraped/tracking_monthly/2022_23"
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
        "output_dir": "data/newly_scraped/tracking_monthly/2023_24"
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
        "output_dir": "data/newly_scraped/tracking_monthly/2024_25"
    },
    "2025-26": {
        "months": {
            "october": "1",
            "november": "2",
            "december": "3",
            "january": "4",
        },
        "output_dir": "data/newly_scraped/tracking_monthly/2025_26"
    }
}

# Progress file
PROGRESS_FILE = Path("data/newly_scraped/tracking_monthly/four_factors_progress.json")


def load_progress():
    """Load progress from file."""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": []}


def save_progress(progress):
    """Save progress to file."""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def get_task_key(season, month):
    """Generate unique key for a scraping task."""
    return f"{season}_four_factors_{month}"


def random_delay(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    """Sleep for a random duration."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def scrape_with_retry(scraper, season, month_value, max_retries=MAX_RETRIES):
    """Scrape with retry logic."""
    params = {"Month": month_value}

    for attempt in range(max_retries + 1):
        try:
            df = scraper.scrape_team_stats_for_season(
                season=season,
                stat_category="four-factors",
                season_type="Regular+Season",
                extra_params=params
            )
            return df
        except Exception as e:
            if attempt < max_retries:
                wait_time = (attempt + 1) * 30
                print(f"      Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise


def main():
    print("=" * 70)
    print("Four Factors Monthly Data Scraper")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load progress
    progress = load_progress()
    completed_tasks = set(progress["completed"])

    # Calculate total tasks
    total_tasks = sum(len(season_info["months"]) for season_info in SEASONS.values())
    remaining_tasks = total_tasks - len(completed_tasks)

    print(f"Total tasks: {total_tasks}")
    print(f"Already completed: {len(completed_tasks)}")
    print(f"Remaining: {remaining_tasks}")
    print()

    if remaining_tasks == 0:
        print("All tasks already completed!")
        return 0

    # Estimate time
    avg_time_per_task = (DELAY_MIN + DELAY_MAX) / 2 + 5
    estimated_minutes = (remaining_tasks * avg_time_per_task) / 60
    print(f"Estimated time: ~{estimated_minutes:.0f} minutes")
    print()

    # Initialize scraper
    container = DIContainer()
    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_four_factors.log")
        scraper = container.team_stats_scraper()

        results = {"success": 0, "failed": 0, "skipped": 0}

        for season, season_info in SEASONS.items():
            output_dir = Path(season_info["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n{'='*50}")
            print(f"Season: {season}")
            print(f"Output: {output_dir}")
            print("=" * 50)

            for month_name, month_value in season_info["months"].items():
                task_key = get_task_key(season, month_name)

                # Skip if already completed
                if task_key in completed_tasks:
                    print(f"  {month_name}: [skipped - already done]")
                    results["skipped"] += 1
                    continue

                try:
                    df = scrape_with_retry(scraper, season, month_value)

                    if df is not None and not df.empty:
                        # Add metadata
                        df["Month"] = month_name
                        df["Season"] = season
                        df["SeasonType"] = "Regular+Season"

                        # Save file
                        filename = f"four_factors_{month_name}.csv"
                        df.to_csv(output_dir / filename, index=False)
                        print(f"  {month_name}: {len(df)} rows -> {filename}")
                        results["success"] += 1
                    else:
                        print(f"  {month_name}: No data")
                        results["failed"] += 1

                    # Mark as completed
                    completed_tasks.add(task_key)
                    progress["completed"] = list(completed_tasks)
                    save_progress(progress)

                except Exception as e:
                    print(f"  {month_name}: ERROR - {e}")
                    results["failed"] += 1

                # Delay between requests
                delay = random_delay()
                print(f"  (waiting {delay:.1f}s)")

            # Extra delay between seasons
            print(f"  [Season done, waiting {DELAY_CATEGORY}s]")
            time.sleep(DELAY_CATEGORY)

        # Summary
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
