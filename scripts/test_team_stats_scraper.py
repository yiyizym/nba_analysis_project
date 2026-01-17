"""
Minimal end-to-end test for TeamStatsShootingScraper.

This script performs a single request to test the scraper:
- Only scrapes 1 season (2024-25)
- Only scrapes Regular Season (not playoffs)
- Expected: 1 HTTP request total

Usage:
    uv run python scripts/test_team_stats_scraper.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer


def main():
    """Run minimal end-to-end test for TeamStatsShootingScraper."""
    container = DIContainer()

    try:
        # Setup components
        config = container.config()
        app_logger = container.app_logger()
        app_logger.setup("test_team_stats.log")

        team_stats_scraper = container.team_stats_scraper()

        print("=" * 60)
        print("TeamStatsShootingScraper - Minimal End-to-End Test")
        print("=" * 60)
        print("\nThis test will:")
        print("  - Scrape ONLY 1 season (2024-25)")
        print("  - Scrape ONLY Regular Season")
        print("  - Make approximately 1 HTTP request")
        print("  - Get shooting stats for all 30 NBA teams")
        print("\n" + "-" * 60)

        # Only scrape current season, only regular season
        test_seasons = ["2024-25"]

        print(f"\nStarting scrape for season: {test_seasons[0]}")
        print("URL: https://www.nba.com/stats/teams/shooting?SeasonType=Regular+Season&Season=2024-25")
        print("\nScraping...")

        # Scrape single season
        df = team_stats_scraper.scrape_team_stats_for_season(
            season="2024-25",
            stat_category="shooting",
            season_type="Regular+Season"
        )

        print("\n" + "=" * 60)
        print("RESULTS")
        print("=" * 60)

        if df.empty:
            print("\n❌ No data returned. Possible issues:")
            print("   - NBA.com website structure may have changed")
            print("   - Network/timeout issue")
            print("   - Season data not available yet")
        else:
            print(f"\n✅ Successfully scraped {len(df)} teams!")
            print(f"\nColumns ({len(df.columns)}):")
            print(f"  {list(df.columns)}")
            print(f"\nFirst 5 rows:")
            print(df.head().to_string())

            # Save to test output
            output_path = Path("data/newly_scraped/test_team_stats_shooting.csv")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            df.to_csv(output_path, index=False)
            print(f"\n✅ Data saved to: {output_path}")

    except Exception as e:
        print(f"\n❌ Error during scraping: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Close web driver
        try:
            web_driver = container.web_driver_factory()
            web_driver.close_driver()
            print("\n✅ WebDriver closed")
        except:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
