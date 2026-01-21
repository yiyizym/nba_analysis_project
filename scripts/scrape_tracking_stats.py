"""
Scrape team-level tracking stats with Month dimension.

Categories: drives, defensive-impact, catch-shoot, passing, touches,
           pull-up, rebounding, speed-distance, elbow-touches,
           post-touches, paint-touches

Dimensions: All Season (Month=0) + Each Month played

Usage:
    uv run python scripts/scrape_tracking_stats.py
"""

import sys
import time
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer


# Tracking stats categories
TRACKING_CATEGORIES = [
    "drives",
    "defensive-impact",
    "catch-shoot",
    "passing",
    "touches",
    "pull-up",
    "rebounding",
    "speed-distance",
    "elbow-touches",
    "post-touches",
    "paint-touches",
]

# Month mapping for NBA.com
# For 2024-25 season (Oct 2024 - now Jan 2025)
MONTHS = {
    "all": "0",       # All Season
    "october": "1",   # October
    "november": "2",  # November
    "december": "3",  # December
    "january": "4",   # January
    "february": "5",  # February
    "march": "6",     # March
    "april": "7",     # April
}

# Only scrape months that have been played
MONTHS_TO_SCRAPE = ["all", "october", "november", "december", "january"]


def main():
    """Scrape tracking stats with Month dimension."""
    container = DIContainer()

    try:
        # Setup
        app_logger = container.app_logger()
        app_logger.setup("scrape_tracking_stats.log")

        team_stats_scraper = container.team_stats_scraper()

        print("=" * 70)
        print("Team-Level Tracking Stats Scraper")
        print("=" * 70)
        print(f"\nCategories: {len(TRACKING_CATEGORIES)}")
        print(f"Months: {MONTHS_TO_SCRAPE}")
        print(f"Total requests: ~{len(TRACKING_CATEGORIES) * len(MONTHS_TO_SCRAPE)}")
        print("\n" + "-" * 70)

        output_dir = Path("data/newly_scraped/tracking")
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}
        total = len(TRACKING_CATEGORIES) * len(MONTHS_TO_SCRAPE)
        count = 0

        for category in TRACKING_CATEGORIES:
            for month_name in MONTHS_TO_SCRAPE:
                count += 1
                month_value = MONTHS[month_name]

                print(f"\n[{count}/{total}] {category} - {month_name} (Month={month_value})")

                extra_params = {"Month": month_value} if month_value != "0" else None

                try:
                    df = team_stats_scraper.scrape_team_stats_for_season(
                        season="2024-25",
                        stat_category=category,
                        season_type="Regular+Season",
                        extra_params=extra_params
                    )

                    if df.empty:
                        print(f"  -> No data returned")
                    else:
                        # Add metadata columns
                        df["Month"] = month_name
                        df["Season"] = "2024-25"
                        df["SeasonType"] = "Regular+Season"
                        df["StatCategory"] = category

                        # Save to file
                        filename = f"tracking_{category}_{month_name}.csv"
                        filepath = output_dir / filename
                        df.to_csv(filepath, index=False)

                        print(f"  -> {len(df)} rows, {len(df.columns)} columns")
                        print(f"  -> Saved to: {filepath}")

                        key = f"{category}_{month_name}"
                        results[key] = {"rows": len(df), "cols": len(df.columns)}

                except Exception as e:
                    print(f"  -> Error: {e}")

                # Rate limiting
                print("  -> Waiting 2 seconds...")
                time.sleep(2)

        # Summary
        print("\n" + "=" * 70)
        print("SUMMARY")
        print("=" * 70)
        print(f"\nSuccessfully scraped: {len(results)}/{total}")

        if results:
            print("\nFiles saved:")
            for key, info in results.items():
                print(f"  - {key}: {info['rows']} rows, {info['cols']} columns")

    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            web_driver = container.web_driver_factory()
            web_driver.close_driver()
            print("\nWebDriver closed")
        except:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
