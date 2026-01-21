"""
Tests for TeamStatsShootingScraper
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch
from selenium.webdriver.remote.webelement import WebElement

from nba_app.webscraping.team_stats_shooting_scraper import TeamStatsShootingScraper
from ml_framework.core.error_handling.error_handler import (
    DataValidationError,
    ConfigurationError,
    DataExtractionError,
    ScrapingError
)


@pytest.fixture
def mock_config():
    """Create a mock configuration object."""
    config = Mock()
    config.regular_season_text = "Regular+Season"
    config.playoffs_season_text = "Playoffs"
    config.play_in_season_text = "PlayIn"
    config.table_class_name = "table-class"
    config.pagination_class_name = "pagination-class"
    config.dropdown_class_name = "dropdown-class"
    config.teams_and_games_class_name = "links-class"
    config.team_id_column = "TEAM_ID"
    return config


@pytest.fixture
def mock_data_access():
    """Create a mock data access object."""
    data_access = Mock()
    data_access.save_dataframes = Mock()
    return data_access


@pytest.fixture
def mock_page_scraper():
    """Create a mock page scraper object."""
    return Mock()


@pytest.fixture
def scraper(mock_config, mock_data_access, mock_page_scraper, mock_app_logger, mock_error_handler):
    """Create a TeamStatsShootingScraper instance for testing."""
    return TeamStatsShootingScraper(
        mock_config,
        mock_data_access,
        mock_page_scraper,
        mock_app_logger,
        mock_error_handler
    )


def test_initialization(mock_config, mock_data_access, mock_page_scraper, mock_app_logger, mock_error_handler):
    """Test that the scraper initializes correctly with valid dependencies."""
    scraper = TeamStatsShootingScraper(
        mock_config,
        mock_data_access,
        mock_page_scraper,
        mock_app_logger,
        mock_error_handler
    )

    assert scraper.config == mock_config
    assert scraper.data_access == mock_data_access
    assert scraper.page_scraper == mock_page_scraper
    assert scraper.app_logger == mock_app_logger
    assert scraper.error_handler == mock_error_handler


def test_initialization_error(mock_app_logger, mock_error_handler):
    """Test that initialization fails with missing dependencies."""
    with pytest.raises(ConfigurationError):
        TeamStatsShootingScraper(None, None, None, mock_app_logger, mock_error_handler)


def test_get_season_types(scraper):
    """Test that _get_season_types returns the correct season types."""
    season_types = scraper._get_season_types()

    assert scraper.config.regular_season_text in season_types
    assert scraper.config.playoffs_season_text in season_types
    assert len(season_types) >= 2


def test_construct_team_stats_url(scraper):
    """Test URL construction for team stats."""
    url = scraper._construct_team_stats_url(
        stat_category="shooting",
        season="2022-23",
        season_type="Regular+Season"
    )

    assert "shooting" in url
    assert "2022-23" in url
    assert "Regular+Season" in url
    assert "https://www.nba.com/stats/teams/" in url


def test_extract_team_ids(scraper):
    """Test extraction of team IDs from table."""
    mock_table = Mock(spec=WebElement)
    mock_link1 = Mock()
    mock_link1.get_attribute.return_value = "https://www.nba.com/teams/1610612739"
    mock_link2 = Mock()
    mock_link2.get_attribute.return_value = "https://www.nba.com/teams/1610612740"

    scraper.page_scraper.get_elements_by_class.return_value = [mock_link1, mock_link2]

    team_ids = scraper._extract_team_ids(mock_table)

    assert len(team_ids) == 2
    assert isinstance(team_ids, pd.Series)


def test_extract_team_ids_no_links(scraper):
    """Test extraction of team IDs when no links are found."""
    mock_table = Mock(spec=WebElement)
    scraper.page_scraper.get_elements_by_class.return_value = None

    team_ids = scraper._extract_team_ids(mock_table)

    assert len(team_ids) == 0
    assert isinstance(team_ids, pd.Series)


def test_convert_table_to_df(scraper):
    """Test conversion of web table to DataFrame."""
    mock_table = Mock(spec=WebElement)
    mock_table.get_attribute.return_value = """
        <table>
            <tr><th>Team</th><th>FG%</th></tr>
            <tr><td>Lakers</td><td>0.450</td></tr>
        </table>
    """

    with patch('pandas.read_html') as mock_read_html:
        mock_df = pd.DataFrame({'Team': ['Lakers'], 'FG%': [0.450]})
        mock_read_html.return_value = [mock_df]

        with patch.object(scraper, '_extract_team_ids') as mock_extract:
            mock_extract.return_value = pd.Series(['1610612747'])

            result = scraper._convert_table_to_df(mock_table)

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            assert scraper.config.team_id_column in result.columns


def test_convert_table_to_df_no_tables(scraper):
    """Test conversion when no tables are found in HTML."""
    mock_table = Mock(spec=WebElement)
    mock_table.get_attribute.return_value = "<div>No table here</div>"

    with patch('pandas.read_html') as mock_read_html:
        mock_read_html.return_value = []

        result = scraper._convert_table_to_df(mock_table)

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 0


def test_scrape_team_stats_for_season(scraper):
    """Test scraping team stats for a single season."""
    mock_table = Mock(spec=WebElement)
    mock_table.get_attribute.return_value = """
        <table>
            <tr><th>Team</th><th>FG%</th></tr>
            <tr><td>Lakers</td><td>0.450</td></tr>
        </table>
    """

    scraper.page_scraper.scrape_page_table.return_value = mock_table

    with patch('pandas.read_html') as mock_read_html:
        mock_df = pd.DataFrame({'Team': ['Lakers'], 'FG%': [0.450]})
        mock_read_html.return_value = [mock_df]

        with patch.object(scraper, '_extract_team_ids') as mock_extract:
            mock_extract.return_value = pd.Series(['1610612747'])

            result = scraper.scrape_team_stats_for_season(
                season="2022-23",
                stat_category="shooting",
                season_type="Regular+Season"
            )

            assert isinstance(result, pd.DataFrame)
            assert len(result) == 1
            scraper.page_scraper.scrape_page_table.assert_called_once()


def test_scrape_team_stats_for_season_no_data(scraper):
    """Test scraping when no data is available."""
    scraper.page_scraper.scrape_page_table.return_value = None

    result = scraper.scrape_team_stats_for_season(
        season="2022-23",
        stat_category="shooting",
        season_type="Regular+Season"
    )

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


def test_scrape_and_save_team_stats_validation(scraper):
    """Test validation in scrape_and_save_team_stats."""
    with pytest.raises(DataValidationError):
        scraper.scrape_and_save_team_stats([], "shooting")


def test_scrape_and_save_team_stats_success(scraper):
    """Test successful scraping and saving of team stats."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers', 'Warriors'],
        'FG%': [0.450, 0.460]
    })

    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = mock_df

        scraper.scrape_and_save_team_stats(["2022-23"], "shooting")

        # Verify data_access.save_dataframes was called
        scraper.data_access.save_dataframes.assert_called_once()

        # Check the saved dataframe
        call_args = scraper.data_access.save_dataframes.call_args
        saved_dfs = call_args[0][0]
        saved_filenames = call_args[0][1]

        assert len(saved_dfs) == 1
        assert len(saved_filenames) == 1
        assert "team_stats_shooting.csv" in saved_filenames[0]
        assert 'Season' in saved_dfs[0].columns
        assert 'SeasonType' in saved_dfs[0].columns


def test_scrape_and_save_team_stats_multiple_seasons(scraper):
    """Test scraping multiple seasons."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers'],
        'FG%': [0.450]
    })

    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = mock_df

        scraper.scrape_and_save_team_stats(["2021-22", "2022-23"], "shooting")

        # Should be called for each season and each season type
        assert mock_scrape.call_count >= 2
        scraper.data_access.save_dataframes.assert_called_once()


def test_scrape_and_save_team_stats_no_data(scraper):
    """Test when no data is scraped."""
    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = pd.DataFrame()

        scraper.scrape_and_save_team_stats(["2022-23"], "shooting")

        # save_dataframes should not be called if no data
        scraper.data_access.save_dataframes.assert_not_called()


def test_scrape_and_save_team_stats_partial_failure(scraper):
    """Test that scraping continues even if one season type fails."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers'],
        'FG%': [0.450]
    })

    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        # First call succeeds, second call fails, third call succeeds
        mock_scrape.side_effect = [mock_df, Exception("Test error"), mock_df]

        # Should not raise exception, should continue
        scraper.scrape_and_save_team_stats(["2022-23"], "shooting")

        # Should still save the data that was successfully scraped
        scraper.data_access.save_dataframes.assert_called_once()
