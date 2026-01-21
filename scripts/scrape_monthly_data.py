#!/usr/bin/env python3
"""
Scrape monthly-level data for TCI model training.

This script scrapes data by month to increase sample size from 30 (season-level)
to ~210 (month-level) for 2024-25 season.

Safety measures to avoid IP ban:
- 10-15 second delay between requests (randomized)
- 20-30 second delay between categories
- Progress saving for resume capability
- Graceful error handling with retries
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
DELAY_MIN = 10  # Minimum delay between requests (seconds)
DELAY_MAX = 15  # Maximum delay between requests
DELAY_CATEGORY = 25  # Delay between different categories
MAX_RETRIES = 2  # Max retries per request

# Seasons and months to scrape
SEASONS = {
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

# Data categories to scrape
CATEGORIES = {
    # Tracking stats (already have some, need to complete)
    "tracking_passing": {"stat_category": "passing", "extra_params": None},
    "tracking_speed_distance": {"stat_category": "speed-distance", "extra_params": None},

    # Advanced and scoring (need month versions)
    "team_advanced": {"stat_category": "advanced", "extra_params": None},
    "team_scoring": {"stat_category": "scoring", "extra_params": None},

    # Shots by defender distance (need month versions)
    "shots_very_tight": {
        "stat_category": "shots-closest-defender",
        "extra_params": {"CloseDefDistRange": "0-2 Feet - Very Tight"}
    },
    "shots_tight": {
        "stat_category": "shots-closest-defender",
        "extra_params": {"CloseDefDistRange": "2-4 Feet - Tight"}
    },
    "shots_open": {
        "stat_category": "shots-closest-defender",
        "extra_params": {"CloseDefDistRange": "4-6 Feet - Open"}
    },
    "shots_wide_open": {
        "stat_category": "shots-closest-defender",
        "extra_params": {"CloseDefDistRange": "6%2B%20Feet%20-%20Wide%20Open"}
    },
}

# Progress file
PROGRESS_FILE = Path("data/newly_scraped/tracking_monthly/scrape_progress.json")


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


def get_task_key(season, category, month):
    """Generate unique key for a scraping task."""
    return f"{season}_{category}_{month}"


def random_delay(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    """Sleep for a random duration."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def scrape_with_retry(scraper, season, stat_category, month_value, extra_params, max_retries=MAX_RETRIES):
    """Scrape with retry logic."""
    params = {"Month": month_value}
    if extra_params:
        params.update(extra_params)

    for attempt in range(max_retries + 1):
        try:
            df = scraper.scrape_team_stats_for_season(
                season=season,
                stat_category=stat_category,
                season_type="Regular+Season",
                extra_params=params
            )
            return df
        except Exception as e:
            if attempt < max_retries:
                wait_time = (attempt + 1) * 30  # Exponential backoff
                print(f"      Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise


def main():
    print("=" * 70)
    print("Monthly Data Scraper for TCI Model")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load progress
    progress = load_progress()
    completed_tasks = set(progress["completed"])

    # Calculate total tasks
    total_tasks = sum(
        len(CATEGORIES) * len(season_info["months"])
        for season_info in SEASONS.values()
    )
    remaining_tasks = total_tasks - len(completed_tasks)

    print(f"Total tasks: {total_tasks}")
    print(f"Already completed: {len(completed_tasks)}")
    print(f"Remaining: {remaining_tasks}")
    print()

    if remaining_tasks == 0:
        print("All tasks already completed!")
        return 0

    # Estimate time
    avg_time_per_task = (DELAY_MIN + DELAY_MAX) / 2 + 5  # +5 for scraping time
    estimated_minutes = (remaining_tasks * avg_time_per_task) / 60
    print(f"Estimated time: ~{estimated_minutes:.0f} minutes")
    print()

    # Initialize scraper
    container = DIContainer()
    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_monthly.log")
        scraper = container.team_stats_scraper()

        results = {"success": 0, "failed": 0, "skipped": 0}

        for season, season_info in SEASONS.items():
            output_dir = Path(season_info["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n{'='*50}")
            print(f"Season: {season}")
            print(f"Output: {output_dir}")
            print("=" * 50)

            for cat_name, cat_config in CATEGORIES.items():
                print(f"\n  Category: {cat_name}")
                print(f"  {'-'*40}")

                for month_name, month_value in season_info["months"].items():
                    task_key = get_task_key(season, cat_name, month_name)

                    # Skip if already completed
                    if task_key in completed_tasks:
                        print(f"    {month_name}: [skipped - already done]")
                        results["skipped"] += 1
                        continue

                    try:
                        df = scrape_with_retry(
                            scraper,
                            season,
                            cat_config["stat_category"],
                            month_value,
                            cat_config["extra_params"]
                        )

                        if df is not None and not df.empty:
                            # Add metadata
                            df["Month"] = month_name
                            df["Season"] = season
                            df["SeasonType"] = "Regular+Season"

                            # Save file
                            filename = f"{cat_name}_{month_name}.csv"
                            df.to_csv(output_dir / filename, index=False)
                            print(f"    {month_name}: {len(df)} rows -> {filename}")
                            results["success"] += 1
                        else:
                            print(f"    {month_name}: No data")
                            results["failed"] += 1

                        # Mark as completed
                        completed_tasks.add(task_key)
                        progress["completed"] = list(completed_tasks)
                        save_progress(progress)

                    except Exception as e:
                        print(f"    {month_name}: ERROR - {e}")
                        results["failed"] += 1

                    # Delay between requests
                    delay = random_delay()
                    print(f"    (waiting {delay:.1f}s)")

                # Extra delay between categories
                print(f"  [Category done, waiting {DELAY_CATEGORY}s]")
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
