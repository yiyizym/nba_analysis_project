#!/usr/bin/env python3
"""
Scrape NBA PlayType stats for monthly periods.

PlayType categories:
- isolation: 单打
- transition: 转换进攻
- ball-handler: 挡拆持球人 (Pick & Roll Ball Handler)
- roll-man: 挡拆顺下人 (Pick & Roll Roll Man)
- post-up: 低位单打
- spot-up: 定点投篮
- handoff: 手递手
- cut: 空切
- off-screen: 无球掩护
- putbacks: 二次进攻
- misc: 其他
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
DELAY_MIN = 8
DELAY_MAX = 12
MAX_RETRIES = 2

# PlayType categories (URL slug -> file name)
# Note: Some categories have different URL patterns on nba.com
PLAYTYPE_CATEGORIES = {
    "isolation": "playtype_isolation",
    "transition": "playtype_transition",
    "ball-handler": "playtype_ball_handler",
    "roll-man": "playtype_roll_man",
    "playtype-post-up": "playtype_post_up",  # URL uses "playtype-post-up"
    "spot-up": "playtype_spot_up",
    "hand-off": "playtype_handoff",  # URL uses "hand-off"
    "cut": "playtype_cut",
    "off-screen": "playtype_off_screen",
    "putbacks": "playtype_putbacks",
    "playtype-misc": "playtype_misc",  # URL uses "playtype-misc"
}

# Seasons to scrape
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
    },
}

PROGRESS_FILE = Path("data/newly_scraped/tracking_monthly/playtype_progress.json")


def load_progress():
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE) as f:
            return json.load(f)
    return {"completed": []}


def save_progress(progress):
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, indent=2)


def get_task_key(season, playtype, month):
    return f"{season}_{playtype}_{month}"


def random_delay(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def scrape_with_retry(scraper, season, playtype, month_value, max_retries=MAX_RETRIES):
    """Scrape playtype data for a specific month."""
    params = {"Month": month_value}

    for attempt in range(max_retries + 1):
        try:
            df = scraper.scrape_team_stats_for_season(
                season=season,
                stat_category=playtype,
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
    print("PlayType Data Scraper (Monthly)")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Categories: {len(PLAYTYPE_CATEGORIES)}")
    print()

    progress = load_progress()
    completed_tasks = set(progress["completed"])

    # Calculate total tasks
    total_tasks = sum(
        len(PLAYTYPE_CATEGORIES) * len(season_info["months"])
        for season_info in SEASONS.values()
    )
    remaining_tasks = total_tasks - len(completed_tasks)

    print(f"Total tasks: {total_tasks}")
    print(f"Already completed: {len(completed_tasks)}")
    print(f"Remaining: {remaining_tasks}")

    if remaining_tasks == 0:
        print("All tasks already completed!")
        return 0

    # Estimated time
    avg_time = (DELAY_MIN + DELAY_MAX) / 2 + 3
    print(f"Estimated time: ~{remaining_tasks * avg_time / 60:.0f} minutes")
    print()

    container = DIContainer()
    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_playtype.log")
        scraper = container.team_stats_scraper()

        results = {"success": 0, "failed": 0, "skipped": 0}

        for season, season_info in SEASONS.items():
            output_dir = Path(season_info["output_dir"])
            output_dir.mkdir(parents=True, exist_ok=True)

            print(f"\n{'='*60}")
            print(f"Season: {season}")
            print(f"Output: {output_dir}")
            print("=" * 60)

            for playtype_slug, file_prefix in PLAYTYPE_CATEGORIES.items():
                print(f"\n  {playtype_slug}:")

                for month_name, month_value in season_info["months"].items():
                    task_key = get_task_key(season, playtype_slug, month_name)

                    if task_key in completed_tasks:
                        print(f"    {month_name}: [skipped]")
                        results["skipped"] += 1
                        continue

                    try:
                        df = scrape_with_retry(scraper, season, playtype_slug, month_value)

                        if df is not None and not df.empty:
                            df["Month"] = month_name
                            df["Season"] = season
                            df["PlayType"] = playtype_slug

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
