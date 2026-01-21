#!/usr/bin/env python3
"""
Scrape latest January 2026 data for prediction.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer

OUTPUT_DIR = Path("data/newly_scraped/tracking_monthly/2025_26")

# Categories to scrape
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
    "shooting_distance": {
        "stat_category": "shooting",
        "extra_params": {"DistanceRange": "5ft+Range"}
    },
}


def main():
    print("=" * 60)
    print("Scraping January 2026 Data")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    container = DIContainer()
    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_jan_2026.log")
        scraper = container.team_stats_scraper()

        for cat_name, cat_config in CATEGORIES.items():
            print(f"\n{cat_name}...")

            params = {"Month": "4"}  # January = Month 4 in 2025-26 season
            if cat_config["extra_params"]:
                params.update(cat_config["extra_params"])

            try:
                df = scraper.scrape_team_stats_for_season(
                    season="2025-26",
                    stat_category=cat_config["stat_category"],
                    season_type="Regular+Season",
                    extra_params=params
                )

                if df is not None and not df.empty:
                    df["Month"] = "january"
                    df["Season"] = "2025-26"
                    filename = f"{cat_name}_january.csv"
                    df.to_csv(OUTPUT_DIR / filename, index=False)
                    print(f"  Saved: {filename} ({len(df)} rows)")
                else:
                    print(f"  No data")

            except Exception as e:
                print(f"  Error: {e}")

            time.sleep(3)

        print("\n" + "=" * 60)
        print("Done!")
        print("=" * 60)

    finally:
        try:
            container.web_driver_factory().close_driver()
        except:
            pass


if __name__ == "__main__":
    main()
