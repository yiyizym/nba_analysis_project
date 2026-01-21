"""
team_stats_scraper.py

Generic scraper for all NBA team statistics categories from the official NBA stats website.
Supports 50+ stat categories including Traditional, Advanced, Clutch, Playtype, Tracking,
Defense Dashboard, Shot Dashboard, Shooting, and Hustle stats.

URL pattern: https://www.nba.com/stats/teams/{category}?SeasonType={season_type}&Season={season}

Key features:
- Configuration-driven: categories defined in webscraping_config.yaml
- Supports extra URL parameters (e.g., DistanceRange for shooting stats)
- Scrapes team statistics for multiple seasons
- Supports different season types (Regular Season, Playoffs, Play-In)
- Implements comprehensive logging using structured logging
- Uses custom exceptions for granular error handling
"""

import logging
import re
import time
import itertools
from io import StringIO
from typing import List, Optional, Dict, Any, Iterator
from dataclasses import dataclass, field
import pandas as pd
from selenium.webdriver.remote.webelement import WebElement

from .base_scraper_classes import (
    BaseTeamStatsScraper,
    BasePageScraper,
)
from ml_framework.framework.data_access.base_data_access import BaseDataAccess
from ml_framework.core.config_management.base_config_manager import BaseConfigManager
from ml_framework.core.error_handling.error_handler_factory import ErrorHandlerFactory
from ml_framework.core.app_logging import log_performance, log_context, AppLogger


@dataclass
class StatCategoryConfig:
    """Configuration for a single stat category."""
    name: str
    extra_params: Optional[List[Dict[str, str]]] = field(default_factory=list)

    def get_file_suffix(self, extra_param: Optional[Dict[str, str]] = None) -> str:
        """
        Generate file suffix based on category and extra params.

        Args:
            extra_param: Optional extra parameter dict (e.g., {"DistanceRange": "By+Zone"})

        Returns:
            str: File suffix like "shooting_by_zone" or "traditional"
        """
        if extra_param:
            # Convert "By+Zone" -> "by_zone", "5ft+Range" -> "5ft_range"
            param_value = list(extra_param.values())[0]
            clean_value = param_value.replace('+', '_').replace(' ', '_').lower()
            return f"{self.name}_{clean_value}"
        return self.name


@dataclass
class DimensionConfig:
    """Configuration for a single dimension parameter (Month, LastNGames, etc.)."""
    name: str
    values: List[str]
    enabled: bool = True


@dataclass
class PerTeamScrapingConfig:
    """Configuration for per-team scraping."""
    enabled: bool
    team_ids: List[str]
    team_id_to_abbrev: Dict[str, str]
    dimensions: List[DimensionConfig]
    rate_limiting: Dict[str, Any]
    categories: List[StatCategoryConfig]


class RateLimiter:
    """
    Rate limiter for web scraping requests to avoid IP blocking.

    Implements delays between requests, between teams, and exponential backoff on errors.
    """

    def __init__(
        self,
        delay_between_requests: float = 2.0,
        delay_between_teams: float = 5.0,
        max_retries: int = 3,
        retry_base_delay: float = 2.0
    ):
        """
        Initialize the rate limiter.

        Args:
            delay_between_requests: Seconds to wait between each request.
            delay_between_teams: Extra seconds to wait when switching teams.
            max_retries: Maximum number of retries on error.
            retry_base_delay: Base delay for exponential backoff.
        """
        self.delay_between_requests = delay_between_requests
        self.delay_between_teams = delay_between_teams
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self._last_request_time: Optional[float] = None
        self._current_team_id: Optional[str] = None

    def wait_before_request(self, team_id: str) -> None:
        """
        Apply appropriate delay before the next request.

        Args:
            team_id: The team ID for the upcoming request.
        """
        current_time = time.time()

        # Check if switching teams
        if self._current_team_id is not None and self._current_team_id != team_id:
            time.sleep(self.delay_between_teams)
            self._current_team_id = team_id
        elif self._current_team_id is None:
            self._current_team_id = team_id

        # Enforce delay between requests
        if self._last_request_time is not None:
            elapsed = current_time - self._last_request_time
            if elapsed < self.delay_between_requests:
                time.sleep(self.delay_between_requests - elapsed)

        self._last_request_time = time.time()

    def get_retry_delay(self, retry_count: int) -> float:
        """
        Get delay for exponential backoff.

        Args:
            retry_count: Current retry attempt number (0-indexed).

        Returns:
            Delay in seconds (capped at 60 seconds).
        """
        delay = self.retry_base_delay ** (retry_count + 1)
        return min(delay, 60.0)


class TeamStatsScraper(BaseTeamStatsScraper):
    """
    Generic scraper for NBA team statistics supporting all categories.

    Supports:
    - Traditional, Advanced, Four-Factors, Misc, Scoring, Opponent, Defense, Estimated-Advanced
    - Clutch stats (all variants)
    - Playtype stats (Isolation, Transition, Ball-Handler, etc.)
    - Tracking stats (Drives, Passing, Touches, etc.)
    - Defense Dashboard
    - Shot Dashboard
    - Shooting (with DistanceRange parameter)
    - Hustle stats

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
        Initialize the TeamStatsScraper with configuration, data access, and page scraper.

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
            "TeamStatsScraper initialized successfully",
            page_scraper_type=type(page_scraper).__name__
        )

    def get_enabled_categories(self) -> List[StatCategoryConfig]:
        """
        Get list of enabled stat categories from configuration.

        Reads the team_stats_categories config section and returns
        all categories from enabled groups.

        Returns:
            List[StatCategoryConfig]: List of enabled category configurations.
        """
        enabled_categories = []

        # Get team_stats_categories from config
        categories_config = getattr(self.config, 'team_stats_categories', None)

        if not categories_config:
            self.app_logger.structured_log(
                logging.WARNING,
                "No team_stats_categories found in config"
            )
            return enabled_categories

        # Handle SimpleNamespace or dict
        if hasattr(categories_config, '__dict__'):
            categories_dict = vars(categories_config)
        else:
            categories_dict = categories_config

        for group_name, group_config in categories_dict.items():
            # Handle SimpleNamespace or dict for group_config
            if hasattr(group_config, '__dict__'):
                group_dict = vars(group_config)
            else:
                group_dict = group_config

            if not group_dict.get('enabled', False):
                continue

            categories_list = group_dict.get('categories', [])
            for cat_config in categories_list:
                # Handle SimpleNamespace or dict for cat_config
                if hasattr(cat_config, '__dict__'):
                    cat_dict = vars(cat_config)
                else:
                    cat_dict = cat_config

                extra_params = cat_dict.get('extra_params', None)
                # Convert extra_params from list of SimpleNamespace/dict to list of dict
                if extra_params:
                    converted_params = []
                    for param in extra_params:
                        if hasattr(param, '__dict__'):
                            converted_params.append(vars(param))
                        else:
                            converted_params.append(param)
                    extra_params = converted_params

                category = StatCategoryConfig(
                    name=cat_dict.get('name'),
                    extra_params=extra_params if extra_params else []
                )
                enabled_categories.append(category)

        self.app_logger.structured_log(
            logging.INFO,
            "Loaded enabled categories from config",
            category_count=len(enabled_categories)
        )

        return enabled_categories

    @log_performance
    def scrape_and_save_team_stats(
        self,
        seasons: List[str],
        stat_category: Optional[str] = None,
        categories: Optional[List[StatCategoryConfig]] = None
    ) -> None:
        """
        Scrape and save team statistics for specified seasons and categories.

        Args:
            seasons (List[str]): A list of seasons to scrape (e.g., ["2021-22", "2022-23"]).
            stat_category (str, optional): Single category for backwards compatibility.
            categories (List[StatCategoryConfig], optional): List of category configurations.

        Raises:
            DataValidationError: If seasons list is empty.
            ScrapingError: If there's an error during scraping process.
        """
        if not seasons:
            raise self.error_handler.create_error_handler(
                'data_validation',
                "Seasons list cannot be empty"
            )

        # Determine categories to scrape
        if categories is None:
            if stat_category:
                # Backwards compatibility: single category mode
                categories = [StatCategoryConfig(name=stat_category)]
            else:
                # Use enabled categories from config
                categories = self.get_enabled_categories()

        if not categories:
            self.app_logger.structured_log(
                logging.WARNING,
                "No categories enabled for team stats scraping"
            )
            return

        with log_context(operation="scrape_team_stats", seasons=seasons):
            self.app_logger.structured_log(
                logging.INFO,
                "Starting team stats scraping",
                seasons=seasons,
                category_count=len(categories),
                categories=[c.name for c in categories]
            )

            for category in categories:
                try:
                    self._scrape_category(seasons, category)
                except Exception as e:
                    self.app_logger.structured_log(
                        logging.ERROR,
                        f"Error scraping category {category.name}",
                        error_message=str(e),
                        error_type=type(e).__name__
                    )
                    # Continue with next category instead of failing completely
                    continue

    def _scrape_category(
        self,
        seasons: List[str],
        category: StatCategoryConfig
    ) -> None:
        """
        Scrape a single category, handling extra parameters if present.

        Args:
            seasons: List of seasons to scrape
            category: Category configuration
        """
        if category.extra_params:
            # Scrape multiple variations with different extra params
            for extra_param in category.extra_params:
                self._scrape_and_save_single_category(
                    seasons, category, extra_param
                )
        else:
            # Scrape without extra params
            self._scrape_and_save_single_category(seasons, category, None)

    def _scrape_and_save_single_category(
        self,
        seasons: List[str],
        category: StatCategoryConfig,
        extra_param: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Scrape and save data for a single category/param combination.

        Args:
            seasons: List of seasons to scrape
            category: Category configuration
            extra_param: Optional extra URL parameter
        """
        file_suffix = category.get_file_suffix(extra_param)

        with log_context(
            operation="scrape_single_category",
            category=category.name,
            extra_param=extra_param
        ):
            self.app_logger.structured_log(
                logging.INFO,
                f"Scraping team {category.name} stats",
                category=category.name,
                extra_param=extra_param,
                file_suffix=file_suffix
            )

            all_stats_dataframes = []

            for season in seasons:
                self.app_logger.structured_log(
                    logging.INFO,
                    f"Scraping {category.name} stats for season {season}",
                    season=season
                )

                for season_type in self._get_season_types():
                    try:
                        df = self.scrape_team_stats_for_season(
                            season,
                            category.name,
                            season_type,
                            extra_param
                        )
                        if not df.empty:
                            df['Season'] = season
                            df['SeasonType'] = season_type
                            df['StatCategory'] = category.name
                            if extra_param:
                                for key, value in extra_param.items():
                                    df[key] = value
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
                        # Continue with next season type instead of failing
                        continue

            # Combine all dataframes and save
            if all_stats_dataframes:
                combined_df = pd.concat(all_stats_dataframes, axis=0, ignore_index=True)
                file_name = f"team_stats_{file_suffix}.csv"
                self.data_access.save_dataframes([combined_df], [file_name])

                self.app_logger.structured_log(
                    logging.INFO,
                    f"Successfully saved team stats: {file_name}",
                    total_rows=len(combined_df),
                    file_name=file_name
                )
            else:
                self.app_logger.structured_log(
                    logging.WARNING,
                    f"No data scraped for team {category.name} stats",
                    category=category.name,
                    extra_param=extra_param
                )

    @log_performance
    def scrape_team_stats_for_season(
        self,
        season: str,
        stat_category: str,
        season_type: str = "Regular+Season",
        extra_params: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Scrape team statistics for a specific season, stat category, and season type.

        Args:
            season (str): The season to scrape (e.g., "2022-23").
            stat_category (str): The category of stats to scrape (e.g., "shooting").
            season_type (str, optional): The type of season. Defaults to "Regular+Season".
            extra_params (Dict[str, str], optional): Extra URL parameters.

        Returns:
            pd.DataFrame: A DataFrame containing scraped team statistics.

        Raises:
            ScrapingError: If there's an error during the scraping process.
        """
        with log_context(
            operation="scrape_team_stats_for_season",
            season=season,
            stat_category=stat_category,
            season_type=season_type,
            extra_params=extra_params
        ):
            try:
                self.app_logger.structured_log(
                    logging.INFO,
                    f"Scraping {stat_category} stats for {season} {season_type}",
                    extra_params=extra_params
                )

                # Construct URL
                url = self._construct_team_stats_url(
                    stat_category, season, season_type, extra_params
                )
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
        season_type: str = "Regular+Season",
        extra_params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Construct the URL for NBA team stats website.

        Args:
            stat_category (str): The category of stats (e.g., "shooting").
            season (str): The season (e.g., "2022-23").
            season_type (str, optional): The type of season. Defaults to "Regular+Season".
            extra_params (Dict[str, str], optional): Extra URL parameters.

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

            # Add extra parameters if provided
            if extra_params:
                for key, value in extra_params.items():
                    url = f"{url}&{key}={value}"

            self.app_logger.structured_log(
                logging.INFO,
                "Constructed team stats URL",
                url=url,
                extra_params=extra_params
            )

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
            dfs = pd.read_html(StringIO(table_html), header=0)

            if not dfs:
                self.app_logger.structured_log(
                    logging.WARNING,
                    "No tables found in HTML"
                )
                return pd.DataFrame()

            df = pd.concat(dfs, ignore_index=True)

            # Fix multi-level headers (must be done before adding team IDs)
            df = self._fix_multi_level_header(df)

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

    def _fix_multi_level_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Fix multi-level headers in NBA stats tables.

        NBA tables often have two header rows:
        - Row 1: Distance ranges (e.g., "Less than 5ft.", "5-9 ft.")
        - Row 2: Metrics (e.g., "FGM", "FGA", "FG%")

        This method detects and merges them into single-level column names.

        Args:
            df (pd.DataFrame): DataFrame with potential multi-level header issue.

        Returns:
            pd.DataFrame: DataFrame with fixed column names.
        """
        if df.empty:
            return df

        # Check if first row looks like a header row
        first_row = df.iloc[0].astype(str).tolist()
        header_indicators = {'Team', 'FGM', 'FGA', 'FG%', 'GP', 'W', 'L', 'MIN'}

        if not any(val in header_indicators for val in first_row):
            return df

        self.app_logger.structured_log(
            logging.INFO,
            "Detected multi-level header, fixing column names"
        )

        # Build new column names by combining header row 1 (current columns) and row 2 (first data row)
        new_columns = []
        current_columns = df.columns.tolist()

        for i, (col, metric) in enumerate(zip(current_columns, first_row)):
            col_str = str(col)
            metric_str = str(metric)

            # Handle "Unnamed" columns - use the metric name directly
            if col_str.startswith('Unnamed'):
                new_col = metric_str
            # Handle duplicate column names (e.g., "Less than 5ft.", "Less than 5ft..1")
            elif metric_str in header_indicators - {'Team'}:
                # Remove trailing dots and numbers from pandas' duplicate handling
                base_col = col_str.rstrip('.0123456789')
                # Clean up the column name
                base_col = base_col.replace(' ', '_').replace('.', '')
                new_col = f"{base_col}_{metric_str}"
            else:
                new_col = metric_str if metric_str != 'nan' else col_str

            new_columns.append(new_col)

        # Apply new column names and remove the header row from data
        df.columns = new_columns
        df = df.iloc[1:].reset_index(drop=True)

        self.app_logger.structured_log(
            logging.INFO,
            "Fixed multi-level header",
            new_column_count=len(new_columns)
        )

        return df

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
                # Extract team IDs from URLs like /stats/team/1610612738/traditional/
                team_id_pattern = re.compile(r'/team/(\d+)/')
                team_ids = []
                for link in links_list:
                    if link:
                        match = team_id_pattern.search(link)
                        if match:
                            team_ids.append(match.group(1))
                team_ids = pd.Series(team_ids, dtype=str)
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

    # ==================== Per-Team Scraping Methods ====================

    def get_per_team_config(self) -> Optional[PerTeamScrapingConfig]:
        """
        Parse per-team scraping configuration from config.

        Returns:
            PerTeamScrapingConfig if enabled, None otherwise.
        """
        try:
            per_team_config = getattr(self.config, 'per_team_stats', None)
            if not per_team_config or not per_team_config.get('enabled', False):
                return None

            # Load team mapping
            team_mapping = getattr(self.config, 'team_id_to_abbrev', {})
            if not team_mapping:
                self.app_logger.structured_log(
                    logging.WARNING,
                    "No team_id_to_abbrev mapping found in config"
                )
                return None

            # Determine team IDs
            teams_config = per_team_config.get('teams', 'all')
            if teams_config == 'all':
                team_ids = list(team_mapping.keys())
            else:
                team_ids = teams_config

            # Parse dimensions
            dimensions = []
            dims_config = per_team_config.get('dimensions', {})
            for dim_name, dim_data in dims_config.items():
                if dim_data.get('enabled', False):
                    dimensions.append(DimensionConfig(
                        name=dim_name,
                        values=dim_data.get('values', []),
                        enabled=True
                    ))

            # Parse rate limiting
            rate_limiting = per_team_config.get('rate_limiting', {
                'delay_between_requests': 2.0,
                'delay_between_teams': 5.0,
                'max_retries': 3,
                'retry_base_delay': 2
            })

            # Get categories (use existing enabled categories if not specified)
            categories_config = per_team_config.get('categories', [])
            if not categories_config:
                categories = self.get_enabled_categories()
            else:
                categories = [StatCategoryConfig(name=c) for c in categories_config]

            return PerTeamScrapingConfig(
                enabled=True,
                team_ids=team_ids,
                team_id_to_abbrev=team_mapping,
                dimensions=dimensions,
                rate_limiting=rate_limiting,
                categories=categories
            )

        except Exception as e:
            self.app_logger.structured_log(
                logging.ERROR,
                "Error parsing per-team config",
                error_message=str(e)
            )
            return None

    def _construct_per_team_url(
        self,
        team_id: str,
        stat_category: str,
        season: str,
        season_type: str,
        dimension_params: Optional[Dict[str, str]] = None,
        extra_params: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Construct URL for per-team stats page.

        URL pattern: https://www.nba.com/stats/team/{team_id}/{category}?SeasonType={}&Season={}&...

        Args:
            team_id: NBA team ID (e.g., "1610612737")
            stat_category: Category name (e.g., "traditional")
            season: Season string (e.g., "2024-25")
            season_type: Season type (e.g., "Regular+Season")
            dimension_params: Dimension filters (Month, LastNGames, etc.)
            extra_params: Category-specific params (DistanceRange, etc.)

        Returns:
            Constructed URL string.
        """
        base_url = f"https://www.nba.com/stats/team/{team_id}/{stat_category}"
        url = f"{base_url}?SeasonType={season_type}&Season={season}"

        # Add dimension parameters
        if dimension_params:
            for key, value in dimension_params.items():
                if value:  # Skip empty values
                    url = f"{url}&{key}={value}"

        # Add extra parameters (category-specific)
        if extra_params:
            for key, value in extra_params.items():
                url = f"{url}&{key}={value}"

        return url.rstrip('\\').strip()

    def _generate_dimension_combinations(
        self,
        dimensions: List[DimensionConfig]
    ) -> List[Dict[str, str]]:
        """
        Generate all combinations of dimension parameters.

        Args:
            dimensions: List of enabled dimension configs

        Returns:
            List of dimension parameter dictionaries.
            Returns [{}] if no dimensions enabled (single scrape with no filters).
        """
        if not dimensions:
            return [{}]

        # Build list of (name, values) pairs
        dim_lists = [(d.name, d.values) for d in dimensions if d.enabled and d.values]

        if not dim_lists:
            return [{}]

        # Generate cartesian product
        names = [d[0] for d in dim_lists]
        value_lists = [d[1] for d in dim_lists]

        combinations = []
        for combo in itertools.product(*value_lists):
            combinations.append(dict(zip(names, combo)))

        return combinations

    def _generate_per_team_filename(
        self,
        category: StatCategoryConfig,
        team_abbrev: str,
        dimension_params: Dict[str, str],
        extra_param: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Generate descriptive filename for per-team data.

        Args:
            category: Category configuration
            team_abbrev: Team abbreviation (e.g., "LAL")
            dimension_params: Active dimension filters
            extra_param: Category-specific param

        Returns:
            Filename like "per_team_stats_traditional_lal_all.csv"
        """
        base = f"per_team_stats_{category.get_file_suffix(extra_param)}"
        team_part = team_abbrev.lower()

        # Build dimension suffix
        if dimension_params:
            dim_parts = []
            for key, value in sorted(dimension_params.items()):
                if value:
                    clean_value = value.lower().replace('+', '_').replace(' ', '_')
                    dim_parts.append(f"{key.lower()}_{clean_value}")
            dim_suffix = "_".join(dim_parts) if dim_parts else "all"
        else:
            dim_suffix = "all"

        return f"{base}_{team_part}_{dim_suffix}.csv"

    def scrape_per_team_stats_for_season(
        self,
        team_id: str,
        season: str,
        stat_category: str,
        season_type: str,
        dimension_params: Optional[Dict[str, str]] = None,
        extra_params: Optional[Dict[str, str]] = None
    ) -> pd.DataFrame:
        """
        Scrape stats for a single team with specific dimension filters.

        Args:
            team_id: NBA team ID
            season: Season string
            stat_category: Category name
            season_type: Season type
            dimension_params: Dimension filters
            extra_params: Category-specific params

        Returns:
            DataFrame with scraped data, includes metadata columns.
        """
        url = self._construct_per_team_url(
            team_id, stat_category, season, season_type,
            dimension_params, extra_params
        )

        self.app_logger.structured_log(
            logging.INFO,
            "Scraping per-team stats",
            team_id=team_id,
            category=stat_category,
            season=season,
            url=url
        )

        try:
            data_table = self.page_scraper.scrape_page_table(
                url,
                self.config.table_class_name,
                self.config.pagination_class_name,
                self.config.dropdown_class_name
            )
            if data_table is None:
                self.app_logger.structured_log(
                    logging.WARNING,
                    "No data table found for per-team stats",
                    team_id=team_id,
                    category=stat_category
                )
                return pd.DataFrame()

            df = self._convert_table_to_df(data_table)

            # Add metadata columns
            df['TEAM_ID'] = team_id
            df['Season'] = season
            df['SeasonType'] = season_type
            df['StatCategory'] = stat_category

            # Add dimension parameters as columns
            if dimension_params:
                for key, value in dimension_params.items():
                    df[key] = value

            # Add extra parameters as columns
            if extra_params:
                for key, value in extra_params.items():
                    df[key] = value

            return df

        except Exception as e:
            self.app_logger.structured_log(
                logging.ERROR,
                "Error scraping per-team stats",
                team_id=team_id,
                category=stat_category,
                error_message=str(e)
            )
            return pd.DataFrame()

    @log_performance
    def scrape_and_save_per_team_stats(
        self,
        seasons: List[str],
        per_team_config: Optional[PerTeamScrapingConfig] = None
    ) -> None:
        """
        Scrape per-team statistics with dimension parameters.

        This method:
        1. Iterates through each team
        2. For each team, iterates through enabled categories
        3. For each category, iterates through dimension combinations
        4. Applies rate limiting throughout
        5. Saves data with descriptive file names

        Args:
            seasons: List of seasons to scrape
            per_team_config: Optional override config (uses get_per_team_config() if None)
        """
        if per_team_config is None:
            per_team_config = self.get_per_team_config()

        if per_team_config is None:
            self.app_logger.structured_log(
                logging.WARNING,
                "Per-team scraping not enabled or config invalid"
            )
            return

        # Initialize rate limiter
        rate_limiter = RateLimiter(
            delay_between_requests=per_team_config.rate_limiting.get('delay_between_requests', 2.0),
            delay_between_teams=per_team_config.rate_limiting.get('delay_between_teams', 5.0),
            max_retries=per_team_config.rate_limiting.get('max_retries', 3),
            retry_base_delay=per_team_config.rate_limiting.get('retry_base_delay', 2)
        )

        # Generate dimension combinations
        dimension_combinations = self._generate_dimension_combinations(per_team_config.dimensions)

        self.app_logger.structured_log(
            logging.INFO,
            "Starting per-team stats scraping",
            team_count=len(per_team_config.team_ids),
            category_count=len(per_team_config.categories),
            dimension_combinations=len(dimension_combinations),
            seasons=seasons
        )

        total_requests = (
            len(per_team_config.team_ids) *
            len(per_team_config.categories) *
            len(dimension_combinations) *
            len(seasons) *
            len(self._get_season_types())
        )
        self.app_logger.structured_log(
            logging.INFO,
            f"Estimated total requests: {total_requests}"
        )

        for team_id in per_team_config.team_ids:
            team_abbrev = per_team_config.team_id_to_abbrev.get(team_id, team_id)

            self.app_logger.structured_log(
                logging.INFO,
                f"Processing team: {team_abbrev} ({team_id})"
            )

            for category in per_team_config.categories:
                # Handle categories with extra_params
                extra_param_list = category.extra_params if category.extra_params else [None]

                for extra_param in extra_param_list:
                    for dim_params in dimension_combinations:
                        all_data = []

                        for season in seasons:
                            for season_type in self._get_season_types():
                                # Apply rate limiting
                                rate_limiter.wait_before_request(team_id)

                                # Scrape with retry logic
                                for retry in range(rate_limiter.max_retries):
                                    try:
                                        df = self.scrape_per_team_stats_for_season(
                                            team_id=team_id,
                                            season=season,
                                            stat_category=category.name,
                                            season_type=season_type,
                                            dimension_params=dim_params,
                                            extra_params=extra_param
                                        )
                                        if not df.empty:
                                            all_data.append(df)
                                        break  # Success, exit retry loop

                                    except Exception as e:
                                        self.app_logger.structured_log(
                                            logging.WARNING,
                                            f"Retry {retry + 1}/{rate_limiter.max_retries} for {team_abbrev}",
                                            error_message=str(e)
                                        )
                                        if retry < rate_limiter.max_retries - 1:
                                            time.sleep(rate_limiter.get_retry_delay(retry))
                                        else:
                                            self.app_logger.structured_log(
                                                logging.ERROR,
                                                f"Failed after {rate_limiter.max_retries} retries",
                                                team_id=team_id,
                                                category=category.name
                                            )

                        # Save data for this category/dimension combination
                        if all_data:
                            combined_df = pd.concat(all_data, ignore_index=True)
                            filename = self._generate_per_team_filename(
                                category, team_abbrev, dim_params, extra_param
                            )
                            self.data_access.save_dataframes(
                                {filename.replace('.csv', ''): combined_df},
                                self.config.newly_scraped_data_path
                            )
                            self.app_logger.structured_log(
                                logging.INFO,
                                f"Saved {len(combined_df)} rows to {filename}"
                            )

        self.app_logger.structured_log(
            logging.INFO,
            "Per-team stats scraping completed"
        )


# Backwards compatibility alias
TeamStatsShootingScraper = TeamStatsScraper
