"""
Minimal end-to-end test for per-team stats scraping.

This script performs a single request to test the per-team scraper:
- Only scrapes 1 team (Boston Celtics)
- Only scrapes 1 category (traditional)
- Only scrapes 1 season (2024-25)
- No dimension filters (baseline test)
- Expected: 1 HTTP request total

Usage:
    uv run python scripts/test_per_team_scraper.py
"""

import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer
from src.nba_app.webscraping.team_stats_scraper import (
    StatCategoryConfig,
    DimensionConfig,
    PerTeamScrapingConfig
)


def main():
    """Run minimal end-to-end test for per-team stats scraper."""
    import time
    container = DIContainer()

    try:
        # Setup components
        config = container.config()
        app_logger = container.app_logger()
        app_logger.setup("test_per_team_stats.log")

        team_stats_scraper = container.team_stats_scraper()

        print("=" * 60)
        print("Per-Team Stats Scraper - Lineups Categories")
        print("=" * 60)

        # Houston Rockets lineups categories
        team_id = "1610612745"
        team_abbrev = "HOU"
        lineups_categories = [
            "lineups-traditional",
            "lineups-advanced",
            "lineups-four-factors",
            "lineups-misc",
            "lineups-scoring",
            "lineups-opponent"
        ]

        print(f"\nTeam: Houston Rockets ({team_id})")
        print(f"Categories: {', '.join(lineups_categories)}")
        print(f"Season: 2024-25")
        print("\n" + "-" * 60)

        results = {}
        for category in lineups_categories:
            url = f"https://www.nba.com/stats/team/{team_id}/{category}?SeasonType=Regular+Season&Season=2024-25"
            print(f"\nScraping {category}...")
            print(f"URL: {url}")

            df = team_stats_scraper.scrape_per_team_stats_for_season(
                team_id=team_id,
                season="2024-25",
                stat_category=category,
                season_type="Regular+Season"
            )

            if df.empty:
                print(f"  -> No data returned for {category}")
            else:
                print(f"  -> Successfully scraped {len(df)} rows, {len(df.columns)} columns")
                # Save to file
                output_path = Path(f"data/newly_scraped/rockets_{category.replace('-', '_')}.csv")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                df.to_csv(output_path, index=False)
                print(f"  -> Saved to: {output_path}")
                results[category] = df

            # Rate limiting - wait between requests
            print("  -> Waiting 3 seconds before next request...")
            time.sleep(3)

        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"\nSuccessfully scraped {len(results)}/{len(lineups_categories)} categories:")
        for cat, df in results.items():
            print(f"  - {cat}: {len(df)} rows, {len(df.columns)} columns")

    except Exception as e:
        print(f"\nError during scraping: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        # Close web driver
        try:
            web_driver = container.web_driver_factory()
            web_driver.close_driver()
            print("\nWebDriver closed")
        except:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
