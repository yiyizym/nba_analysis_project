#!/usr/bin/env python3
"""
Scrape historical monthly data for TCI model (2021-22 to 2023-24 seasons).

Safety measures:
- 10-15 second delay between requests (randomized)
- 25 second delay between categories
- Progress saving for resume capability
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
DELAY_CATEGORY = 25
MAX_RETRIES = 2

# Historical seasons to scrape
SEASONS = {
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
}

# Data categories
CATEGORIES = {
    "tracking_passing": {"stat_category": "passing", "extra_params": None},
    "tracking_speed_distance": {"stat_category": "speed-distance", "extra_params": None},
    "team_advanced": {"stat_category": "advanced", "extra_params": None},
    "team_scoring": {"stat_category": "scoring", "extra_params": None},
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

PROGRESS_FILE = Path("data/newly_scraped/tracking_monthly/scrape_historical_progress.json")


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


def scrape_with_retry(scraper, season, stat_category, month_value, extra_params, max_retries=MAX_RETRIES):
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
                wait_time = (attempt + 1) * 30
                print(f"      Retry {attempt + 1}/{max_retries} after {wait_time}s: {e}")
                time.sleep(wait_time)
            else:
                raise


def main():
    print("=" * 70)
    print("Historical Monthly Data Scraper (2021-22 to 2023-24)")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    progress = load_progress()
    completed_tasks = set(progress["completed"])

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

    avg_time_per_task = (DELAY_MIN + DELAY_MAX) / 2 + 5
    estimated_minutes = (remaining_tasks * avg_time_per_task) / 60
    print(f"Estimated time: ~{estimated_minutes:.0f} minutes")
    print()

    container = DIContainer()
    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_historical.log")
        scraper = container.team_stats_scraper()

        results = {"success": 0, "failed": 0, "skipped": 0}
        last_progress_report = time.time()

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
                            df["Month"] = month_name
                            df["Season"] = season
                            df["SeasonType"] = "Regular+Season"

                            filename = f"{cat_name}_{month_name}.csv"
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

                    # Progress report every 5 minutes
                    if time.time() - last_progress_report > 300:
                        completed = results["success"] + results["failed"] + results["skipped"]
                        print(f"\n  [Progress: {completed}/{total_tasks} tasks, {results['success']} success, {results['failed']} failed]")
                        last_progress_report = time.time()

                print(f"  [Category done, waiting {DELAY_CATEGORY}s]")
                time.sleep(DELAY_CATEGORY)

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
