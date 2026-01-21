"""
Scrape remaining tracking stats with conservative rate limiting.

Remaining categories: pull-up, rebounding, speed-distance,
                     elbow-touches, post-touches, paint-touches

Rate limiting:
- 8 seconds between requests
- 30 seconds between categories

Usage:
    uv run python scripts/scrape_tracking_stats_safe.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer


# Remaining categories to scrape
# Note: URL uses "pullup" not "pull-up"
REMAINING_CATEGORIES = [
    "pullup",
    "rebounding",
    "speed-distance",
    "elbow-touches",
    "post-touches",
    "paint-touches",
]

MONTHS = {
    "all": "0",
    "october": "1",
    "november": "2",
    "december": "3",
    "january": "4",
}

MONTHS_TO_SCRAPE = ["all", "october", "november", "december", "january"]

# Conservative rate limiting
DELAY_BETWEEN_REQUESTS = 8    # seconds
DELAY_BETWEEN_CATEGORIES = 30  # seconds


def main():
    container = DIContainer()

    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_tracking_safe.log")

        team_stats_scraper = container.team_stats_scraper()

        print("=" * 70)
        print("Tracking Stats Scraper (Safe Mode)")
        print("=" * 70)
        print(f"\nRemaining categories: {len(REMAINING_CATEGORIES)}")
        print(f"Months: {len(MONTHS_TO_SCRAPE)}")
        print(f"Total requests: {len(REMAINING_CATEGORIES) * len(MONTHS_TO_SCRAPE)}")
        print(f"\nRate limiting:")
        print(f"  - {DELAY_BETWEEN_REQUESTS}s between requests")
        print(f"  - {DELAY_BETWEEN_CATEGORIES}s between categories")
        print(f"\nEstimated time: ~{(len(REMAINING_CATEGORIES) * len(MONTHS_TO_SCRAPE) * DELAY_BETWEEN_REQUESTS + len(REMAINING_CATEGORIES) * DELAY_BETWEEN_CATEGORIES) // 60} minutes")
        print("\n" + "-" * 70)

        output_dir = Path("data/newly_scraped/tracking")
        output_dir.mkdir(parents=True, exist_ok=True)

        results = {}
        total = len(REMAINING_CATEGORIES) * len(MONTHS_TO_SCRAPE)
        count = 0

        for cat_idx, category in enumerate(REMAINING_CATEGORIES):
            print(f"\n{'='*50}")
            print(f"Category: {category} ({cat_idx + 1}/{len(REMAINING_CATEGORIES)})")
            print(f"{'='*50}")

            for month_name in MONTHS_TO_SCRAPE:
                count += 1
                month_value = MONTHS[month_name]

                print(f"\n  [{count}/{total}] {month_name} (Month={month_value})")

                extra_params = {"Month": month_value} if month_value != "0" else None

                try:
                    df = team_stats_scraper.scrape_team_stats_for_season(
                        season="2024-25",
                        stat_category=category,
                        season_type="Regular+Season",
                        extra_params=extra_params
                    )

                    if df.empty:
                        print(f"    -> No data")
                    else:
                        df["Month"] = month_name
                        df["Season"] = "2024-25"
                        df["SeasonType"] = "Regular+Season"
                        df["StatCategory"] = category

                        filename = f"tracking_{category}_{month_name}.csv"
                        filepath = output_dir / filename
                        df.to_csv(filepath, index=False)

                        print(f"    -> {len(df)} rows -> {filename}")
                        results[f"{category}_{month_name}"] = len(df)

                except Exception as e:
                    print(f"    -> Error: {e}")

                # Rate limiting between requests
                print(f"    -> Waiting {DELAY_BETWEEN_REQUESTS}s...")
                time.sleep(DELAY_BETWEEN_REQUESTS)

            # Extra delay between categories
            if cat_idx < len(REMAINING_CATEGORIES) - 1:
                print(f"\n  Category complete. Waiting {DELAY_BETWEEN_CATEGORIES}s before next...")
                time.sleep(DELAY_BETWEEN_CATEGORIES)

        # Summary
        print("\n" + "=" * 70)
        print("COMPLETE")
        print("=" * 70)
        print(f"\nSuccessfully scraped: {len(results)}/{total}")

    except Exception as e:
        print(f"\nError: {e}")
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
