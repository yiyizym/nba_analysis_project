"""
Scrape 2025-26 season data for TCI analysis.

Categories:
- tracking stats (passing, speed-distance, drives, etc.)
- advanced (for OffRtg)
- scoring (for Assisted %)
- shots-closest-defender (for Open/Wide Open %)

Usage:
    uv run python scripts/scrape_2025_26_season.py
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer

SEASON = "2025-26"
DELAY_BETWEEN_REQUESTS = 8
DELAY_BETWEEN_CATEGORIES = 15

# Tracking categories that worked for 2024-25
TRACKING_CATEGORIES = [
    "drives",
    "defensive-impact",
    "catch-shoot",
    "passing",
    "touches",
    "pullup",
    "rebounding",
    "speed-distance",
]

# Months played in 2025-26 season (Oct 2025 - Jan 2026)
MONTHS = {
    "all": "0",
    "october": "1",
    "november": "2",
    "december": "3",
    "january": "4",
}

# Shot defender distance ranges
DEFENDER_RANGES = [
    ("0-2 Feet - Very Tight", "very_tight"),
    ("2-4 Feet - Tight", "tight"),
    ("4-6 Feet - Open", "open"),
    ("6%2B%20Feet%20-%20Wide%20Open", "wide_open"),
]


def main():
    container = DIContainer()

    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_2025_26.log")

        scraper = container.team_stats_scraper()

        output_dir = Path("data/newly_scraped/2025_26")
        output_dir.mkdir(parents=True, exist_ok=True)

        print("=" * 70)
        print(f"Scraping {SEASON} Season Data")
        print("=" * 70)

        results = {"success": 0, "failed": 0}

        # 1. Scrape tracking categories with months
        print("\n[1/4] Tracking Stats")
        print("-" * 50)

        for category in TRACKING_CATEGORIES:
            print(f"\n  Category: {category}")

            for month_name, month_value in MONTHS.items():
                extra_params = {"Month": month_value} if month_value != "0" else None

                try:
                    df = scraper.scrape_team_stats_for_season(
                        season=SEASON,
                        stat_category=category,
                        season_type="Regular+Season",
                        extra_params=extra_params
                    )

                    if not df.empty:
                        df["Month"] = month_name
                        df["Season"] = SEASON
                        df["SeasonType"] = "Regular+Season"
                        df["StatCategory"] = category

                        filename = f"tracking_{category}_{month_name}.csv"
                        df.to_csv(output_dir / filename, index=False)
                        print(f"    {month_name}: {len(df)} rows -> {filename}")
                        results["success"] += 1
                    else:
                        print(f"    {month_name}: No data")
                        results["failed"] += 1

                except Exception as e:
                    print(f"    {month_name}: Error - {e}")
                    results["failed"] += 1

                time.sleep(DELAY_BETWEEN_REQUESTS)

            time.sleep(DELAY_BETWEEN_CATEGORIES)

        # 2. Scrape advanced stats
        print("\n[2/4] Advanced Stats")
        print("-" * 50)

        try:
            df = scraper.scrape_team_stats_for_season(
                season=SEASON,
                stat_category="advanced",
                season_type="Regular+Season"
            )
            if not df.empty:
                df["Season"] = SEASON
                df["SeasonType"] = "Regular+Season"
                df.to_csv(output_dir / "team_advanced_all.csv", index=False)
                print(f"  -> {len(df)} teams saved")
                results["success"] += 1
            else:
                print("  -> No data")
                results["failed"] += 1
        except Exception as e:
            print(f"  -> Error: {e}")
            results["failed"] += 1

        time.sleep(DELAY_BETWEEN_CATEGORIES)

        # 3. Scrape scoring stats
        print("\n[3/4] Scoring Stats")
        print("-" * 50)

        try:
            df = scraper.scrape_team_stats_for_season(
                season=SEASON,
                stat_category="scoring",
                season_type="Regular+Season"
            )
            if not df.empty:
                df["Season"] = SEASON
                df["SeasonType"] = "Regular+Season"
                df.to_csv(output_dir / "team_scoring_all.csv", index=False)
                print(f"  -> {len(df)} teams saved")
                results["success"] += 1
            else:
                print("  -> No data")
                results["failed"] += 1
        except Exception as e:
            print(f"  -> Error: {e}")
            results["failed"] += 1

        time.sleep(DELAY_BETWEEN_CATEGORIES)

        # 4. Scrape shots-closest-defender
        print("\n[4/4] Shots Closest Defender")
        print("-" * 50)

        for range_param, filename_suffix in DEFENDER_RANGES:
            try:
                df = scraper.scrape_team_stats_for_season(
                    season=SEASON,
                    stat_category="shots-closest-defender",
                    season_type="Regular+Season",
                    extra_params={"CloseDefDistRange": range_param}
                )
                if not df.empty:
                    df["CloseDefDistRange"] = range_param
                    df["Season"] = SEASON
                    df["SeasonType"] = "Regular+Season"
                    df.to_csv(output_dir / f"team_shots_defender_{filename_suffix}.csv", index=False)
                    print(f"  {filename_suffix}: {len(df)} teams saved")
                    results["success"] += 1
                else:
                    print(f"  {filename_suffix}: No data")
                    results["failed"] += 1
            except Exception as e:
                print(f"  {filename_suffix}: Error - {e}")
                results["failed"] += 1

            time.sleep(DELAY_BETWEEN_REQUESTS)

        # Summary
        print("\n" + "=" * 70)
        print("COMPLETE")
        print("=" * 70)
        print(f"Success: {results['success']}")
        print(f"Failed: {results['failed']}")
        print(f"Files saved to: {output_dir}")

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
