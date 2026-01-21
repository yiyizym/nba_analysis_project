"""Scrape 2025-26 tight shots data (2-4 feet defender distance)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer

SEASON = "2025-26"

def main():
    container = DIContainer()

    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_tight.log")

        scraper = container.team_stats_scraper()

        output_dir = Path("data/newly_scraped/2025_26")
        output_dir.mkdir(parents=True, exist_ok=True)

        print(f"Scraping tight shots (2-4 feet) for {SEASON}...")

        df = scraper.scrape_team_stats_for_season(
            season=SEASON,
            stat_category="shots-closest-defender",
            season_type="Regular+Season",
            extra_params={"CloseDefDistRange": "2-4 Feet - Tight"}
        )

        if not df.empty:
            df["CloseDefDistRange"] = "2-4 Feet - Tight"
            df["Season"] = SEASON
            df["SeasonType"] = "Regular+Season"
            df.to_csv(output_dir / "team_shots_defender_tight.csv", index=False)
            print(f"Success: {len(df)} teams saved to team_shots_defender_tight.csv")
        else:
            print("No data returned")
            return 1

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            container.web_driver_factory().close_driver()
        except:
            pass

    return 0

if __name__ == "__main__":
    sys.exit(main())
