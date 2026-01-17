"""
team_stats_shooting_scraper.py

This module contains the TeamStatsShootingScraper class, which is responsible for scraping NBA team
shooting statistics from the official NBA stats website. Unlike boxscore data which is per-game,
team stats represent aggregated statistics for teams across a season or season segment.

The scraper targets the NBA stats team shooting page at:
https://www.nba.com/stats/teams/shooting

Key features:
- Scrapes team shooting statistics for multiple seasons
- Supports different season types (Regular Season, Playoffs, Play-In)
- Implements comprehensive logging using structured logging
- Uses custom exceptions for granular error handling
"""

import logging
from typing import List, Optional, Tuple
from datetime import datetime
import pandas as pd
from selenium.webdriver.remote.webelement import WebElement

from .base_scraper_classes import (
    BaseTeamStatsScraper,
    BasePageScraper,
)
from ml_framework.framework.data_access.base_data_access import BaseDataAccess
from ml_framework.core.config_management.base_config_manager import BaseConfigManager
from ml_framework.core.error_handling.error_handler_factory import ErrorHandlerFactory
from ml_framework.core.app_logging import log_performance, log_context, structured_log, AppLogger


class TeamStatsShootingScraper(BaseTeamStatsScraper):
    """
    A class for scraping NBA team shooting statistics.

    This class provides methods to scrape aggregated team shooting stats for multiple seasons.
    Unlike boxscores which are per-game, these are season-level aggregated statistics.

    Attributes:
        config (BaseConfigManager): Configuration object.
        data_access (BaseDataAccess): Data access object for saving scraped data.
        page_scraper (BasePageScraper): An instance of PageScraper for web scraping operations.
        app_logger (AppLogger): Application logger instance.
        error_handler (ErrorHandlerFactory): Error handler factory instance.
    """

    def __init__(
        self,
        config: BaseConfigManager,
        data_access: BaseDataAccess,
        page_scraper: BasePageScraper,
        app_logger: AppLogger,
        error_handler: ErrorHandlerFactory
    ) -> None:
        """
        Initialize the TeamStatsShootingScraper with configuration, data access, and page scraper.

        Args:
            config (BaseConfigManager): Configuration object.
            data_access (BaseDataAccess): Data access object.
            page_scraper (BasePageScraper): Page scraper object.
            app_logger (AppLogger): Application logger instance.
            error_handler (ErrorHandlerFactory): Error handler factory instance.

        Raises:
            ConfigurationError: If there's an issue with the provided configuration or dependencies.
        """
        if not all([config, data_access, page_scraper]):
            raise error_handler.create_error_handler(
                'configuration',
                "Required dependencies must be provided: config, data_access, page_scraper"
            )

        self.config = config
        self.data_access = data_access
        self.page_scraper = page_scraper
        self.app_logger = app_logger
        self.error_handler = error_handler

        self.app_logger.structured_log(
            logging.INFO,
            "TeamStatsShootingScraper initialized successfully",
            page_scraper_type=type(page_scraper).__name__
        )

    @log_performance
    def scrape_and_save_team_stats(self, seasons: List[str], stat_category: str = 'shooting') -> None:
        """
        Scrape and save team statistics for specified seasons and stat category.

        Args:
            seasons (List[str]): A list of seasons to scrape (e.g., ["2021-22", "2022-23"]).
            stat_category (str, optional): The category of stats to scrape. Defaults to 'shooting'.

        Raises:
            DataValidationError: If seasons list is empty.
            ScrapingError: If there's an error during scraping process.
        """
        if not seasons:
            raise self.error_handler.create_error_handler(
                'data_validation',
                "Seasons list cannot be empty"
            )

        with log_context(operation="scrape_team_stats", seasons=seasons, stat_category=stat_category):
            self.app_logger.structured_log(
                logging.INFO,
                f"Starting to scrape team {stat_category} stats",
                seasons=seasons,
                stat_category=stat_category
            )

            try:
                all_stats_dataframes = []

                for season in seasons:
                    self.app_logger.structured_log(
                        logging.INFO,
                        f"Scraping {stat_category} stats for season {season}",
                        season=season
                    )

                    # Scrape for each season type (regular season, playoffs, play-in)
                    season_types = self._get_season_types()

                    for season_type in season_types:
                        try:
                            df = self.scrape_team_stats_for_season(season, stat_category, season_type)
                            if not df.empty:
                                df['Season'] = season
                                df['SeasonType'] = season_type
                                all_stats_dataframes.append(df)
                                self.app_logger.structured_log(
                                    logging.INFO,
                                    f"Successfully scraped {season_type} for {season}",
                                    season=season,
                                    season_type=season_type,
                                    rows=len(df)
                                )
                        except Exception as e:
                            self.app_logger.structured_log(
                                logging.ERROR,
                                f"Error scraping {season_type} for {season}",
                                season=season,
                                season_type=season_type,
                                error_message=str(e)
                            )
                            # Continue with next season type instead of failing completely
                            continue

                # Combine all dataframes and save
                if all_stats_dataframes:
                    combined_df = pd.concat(all_stats_dataframes, axis=0, ignore_index=True)
                    file_name = f"team_stats_{stat_category}.csv"
                    self.data_access.save_dataframes([combined_df], [file_name])

                    self.app_logger.structured_log(
                        logging.INFO,
                        f"Successfully saved team {stat_category} stats",
                        total_rows=len(combined_df),
                        file_name=file_name
                    )
                else:
                    self.app_logger.structured_log(
                        logging.WARNING,
                        f"No data scraped for team {stat_category} stats"
                    )

            except Exception as e:
                self.app_logger.structured_log(
                    logging.ERROR,
                    f"Error in scrape_and_save_team_stats",
                    error_message=str(e),
                    error_type=type(e).__name__
                )
                raise self.error_handler.create_error_handler(
                    'scraping',
                    f"Error scraping team stats: {str(e)}"
                )

    @log_performance
    def scrape_team_stats_for_season(
        self,
        season: str,
        stat_category: str,
        season_type: str = "Regular+Season"
    ) -> pd.DataFrame:
        """
        Scrape team statistics for a specific season, stat category, and season type.

        Args:
            season (str): The season to scrape (e.g., "2022-23").
            stat_category (str): The category of stats to scrape (e.g., "shooting").
            season_type (str, optional): The type of season. Defaults to "Regular+Season".

        Returns:
            pd.DataFrame: A DataFrame containing scraped team statistics.

        Raises:
            ScrapingError: If there's an error during the scraping process.
        """
        with log_context(
            operation="scrape_team_stats_for_season",
            season=season,
            stat_category=stat_category,
            season_type=season_type
        ):
            try:
                self.app_logger.structured_log(
                    logging.INFO,
                    f"Scraping {stat_category} stats for {season} {season_type}"
                )

                # Construct URL
                url = self._construct_team_stats_url(stat_category, season, season_type)
                self.app_logger.structured_log(logging.INFO, "Constructed URL", url=url)

                # Scrape the table
                table = self.page_scraper.scrape_page_table(
                    url,
                    self.config.table_class_name,
                    self.config.pagination_class_name,
                    self.config.dropdown_class_name
                )

                if table is None:
                    self.app_logger.structured_log(
                        logging.WARNING,
                        f"No data found for {season} {season_type}",
                        season=season,
                        season_type=season_type
                    )
                    return pd.DataFrame()

                # Convert table to DataFrame
                df = self._convert_table_to_df(table)

                self.app_logger.structured_log(
                    logging.INFO,
                    "Successfully scraped team stats",
                    rows=len(df),
                    columns=len(df.columns)
                )

                return df

            except Exception as e:
                self.app_logger.structured_log(
                    logging.ERROR,
                    "Error scraping team stats for season",
                    error_message=str(e),
                    season=season,
                    season_type=season_type
                )
                raise self.error_handler.create_error_handler(
                    'scraping',
                    f"Error scraping team stats: {str(e)}"
                )

    def _construct_team_stats_url(
        self,
        stat_category: str,
        season: str,
        season_type: str = "Regular+Season"
    ) -> str:
        """
        Construct the URL for NBA team stats website.

        Args:
            stat_category (str): The category of stats (e.g., "shooting").
            season (str): The season (e.g., "2022-23").
            season_type (str, optional): The type of season. Defaults to "Regular+Season".

        Returns:
            str: The constructed URL string.

        Raises:
            ConfigurationError: If there's an error constructing the URL.
        """
        try:
            # Base URL for team stats
            base_url = f"https://www.nba.com/stats/teams/{stat_category}"

            # Add query parameters
            url = f"{base_url}?SeasonType={season_type}&Season={season}"

            self.app_logger.structured_log(logging.INFO, "Constructed team stats URL", url=url)

            return url.rstrip('\\').strip()

        except Exception as e:
            self.app_logger.structured_log(
                logging.ERROR,
                "Error constructing team stats URL",
                error_message=str(e)
            )
            raise self.error_handler.create_error_handler(
                'configuration',
                f"Error constructing team stats URL: {str(e)}"
            )

    def _convert_table_to_df(self, data_table: WebElement) -> pd.DataFrame:
        """
        Convert a WebElement table to a DataFrame.

        Args:
            data_table (WebElement): A WebElement containing the table data.

        Returns:
            pd.DataFrame: A DataFrame representation of the table.

        Raises:
            DataExtractionError: If there's an error extracting data from the table.
        """
        try:
            table_html = data_table.get_attribute('outerHTML')
            dfs = pd.read_html(table_html, header=0)

            if not dfs:
                self.app_logger.structured_log(
                    logging.WARNING,
                    "No tables found in HTML"
                )
                return pd.DataFrame()

            df = pd.concat(dfs, ignore_index=True)

            # Extract team IDs from the table links
            team_ids = self._extract_team_ids(data_table)
            if len(team_ids) == len(df):
                df[self.config.team_id_column] = team_ids
            else:
                self.app_logger.structured_log(
                    logging.WARNING,
                    "Team ID count mismatch",
                    team_ids_count=len(team_ids),
                    dataframe_rows=len(df)
                )

            self.app_logger.structured_log(
                logging.INFO,
                "Successfully converted table to DataFrame",
                rows=len(df),
                columns=len(df.columns)
            )

            return df

        except Exception as e:
            self.app_logger.structured_log(
                logging.ERROR,
                "Error converting table to DataFrame",
                error_message=str(e)
            )
            raise self.error_handler.create_error_handler(
                'data_extraction',
                f"Error converting table to DataFrame: {str(e)}"
            )

    def _extract_team_ids(self, data_table: WebElement) -> pd.Series:
        """
        Extract team IDs from the team stats table.

        Args:
            data_table (WebElement): A WebElement containing the table data.

        Returns:
            pd.Series: A Series containing team IDs.

        Raises:
            DataExtractionError: If there's an error extracting team IDs.
        """
        try:
            links = self.page_scraper.get_elements_by_class(
                self.config.teams_and_games_class_name,
                data_table
            )

            if links:
                links_list = [link.get_attribute("href") for link in links]
                # Extract team IDs from URLs like .../teams/1610612739/...
                team_ids = pd.Series([
                    link[-10:] for link in links_list
                    if 'teams' in link and '/stats' not in link
                ])
            else:
                team_ids = pd.Series(dtype=str)

            self.app_logger.structured_log(
                logging.INFO,
                "Successfully extracted team IDs",
                team_ids_count=len(team_ids)
            )

            return team_ids

        except Exception as e:
            self.app_logger.structured_log(
                logging.ERROR,
                "Error extracting team IDs",
                error_message=str(e)
            )
            raise self.error_handler.create_error_handler(
                'data_extraction',
                f"Error extracting team IDs: {str(e)}"
            )

    def _get_season_types(self) -> List[str]:
        """
        Get the list of season types to scrape.

        Returns:
            List[str]: A list of season type strings.
        """
        return [
            self.config.regular_season_text,
            self.config.playoffs_season_text,
            # Only include play-in if configured
            # self.config.play_in_season_text,
        ]
