"""
Tests for TeamStatsScraper (generic multi-category scraper)
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from selenium.webdriver.remote.webelement import WebElement

from nba_app.webscraping.team_stats_scraper import TeamStatsScraper, StatCategoryConfig
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
    config.team_stats_categories = None  # No categories by default
    return config


@pytest.fixture
def mock_config_with_categories():
    """Create a mock configuration with team_stats_categories."""
    config = Mock()
    config.regular_season_text = "Regular+Season"
    config.playoffs_season_text = "Playoffs"
    config.play_in_season_text = "PlayIn"
    config.table_class_name = "table-class"
    config.pagination_class_name = "pagination-class"
    config.dropdown_class_name = "dropdown-class"
    config.teams_and_games_class_name = "links-class"
    config.team_id_column = "TEAM_ID"

    # Simulate team_stats_categories configuration
    config.team_stats_categories = {
        'traditional_stats': {
            'enabled': True,
            'categories': [
                {'name': 'traditional'},
                {'name': 'advanced'}
            ]
        },
        'shooting_stats': {
            'enabled': True,
            'categories': [
                {
                    'name': 'shooting',
                    'extra_params': [
                        {'DistanceRange': 'By+Zone'},
                        {'DistanceRange': '5ft+Range'}
                    ]
                }
            ]
        },
        'disabled_stats': {
            'enabled': False,
            'categories': [
                {'name': 'hustle'}
            ]
        }
    }
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
    """Create a TeamStatsScraper instance for testing."""
    return TeamStatsScraper(
        mock_config,
        mock_data_access,
        mock_page_scraper,
        mock_app_logger,
        mock_error_handler
    )


@pytest.fixture
def scraper_with_categories(mock_config_with_categories, mock_data_access, mock_page_scraper, mock_app_logger, mock_error_handler):
    """Create a TeamStatsScraper instance with categories config for testing."""
    return TeamStatsScraper(
        mock_config_with_categories,
        mock_data_access,
        mock_page_scraper,
        mock_app_logger,
        mock_error_handler
    )


# ==================== Basic Initialization Tests ====================

def test_initialization(mock_config, mock_data_access, mock_page_scraper, mock_app_logger, mock_error_handler):
    """Test that the scraper initializes correctly with valid dependencies."""
    scraper = TeamStatsScraper(
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
        TeamStatsScraper(None, None, None, mock_app_logger, mock_error_handler)


# ==================== StatCategoryConfig Tests ====================

def test_stat_category_config_file_suffix_no_params():
    """Test file suffix generation without extra params."""
    category = StatCategoryConfig(name="traditional")
    assert category.get_file_suffix() == "traditional"


def test_stat_category_config_file_suffix_with_params():
    """Test file suffix generation with extra params."""
    category = StatCategoryConfig(
        name="shooting",
        extra_params=[{"DistanceRange": "By+Zone"}]
    )
    assert category.get_file_suffix({"DistanceRange": "By+Zone"}) == "shooting_by_zone"


def test_stat_category_config_file_suffix_5ft_range():
    """Test file suffix generation for 5ft Range."""
    category = StatCategoryConfig(
        name="shooting",
        extra_params=[{"DistanceRange": "5ft+Range"}]
    )
    assert category.get_file_suffix({"DistanceRange": "5ft+Range"}) == "shooting_5ft_range"


# ==================== URL Construction Tests ====================

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


def test_construct_team_stats_url_with_extra_params(scraper):
    """Test URL construction with extra parameters."""
    url = scraper._construct_team_stats_url(
        stat_category="shooting",
        season="2022-23",
        season_type="Regular+Season",
        extra_params={"DistanceRange": "By+Zone"}
    )

    assert "shooting" in url
    assert "2022-23" in url
    assert "Regular+Season" in url
    assert "DistanceRange=By+Zone" in url


def test_construct_team_stats_url_with_multiple_extra_params(scraper):
    """Test URL construction with multiple extra parameters."""
    url = scraper._construct_team_stats_url(
        stat_category="shots-general",
        season="2022-23",
        season_type="Regular+Season",
        extra_params={"DistanceRange": "By+Zone", "CloseDefDist": "0-2 Feet - Very Tight"}
    )

    assert "shots-general" in url
    assert "DistanceRange=By+Zone" in url
    assert "CloseDefDist=0-2 Feet - Very Tight" in url


# ==================== Season Types Tests ====================

def test_get_season_types(scraper):
    """Test that _get_season_types returns the correct season types."""
    season_types = scraper._get_season_types()

    assert scraper.config.regular_season_text in season_types
    assert scraper.config.playoffs_season_text in season_types
    assert len(season_types) >= 2


# ==================== Team ID Extraction Tests ====================

def test_extract_team_ids(scraper):
    """Test extraction of team IDs from table."""
    mock_table = Mock(spec=WebElement)
    mock_link1 = Mock()
    mock_link1.get_attribute.return_value = "/stats/team/1610612739/traditional/"
    mock_link2 = Mock()
    mock_link2.get_attribute.return_value = "/stats/team/1610612740/traditional/"

    scraper.page_scraper.get_elements_by_class.return_value = [mock_link1, mock_link2]

    team_ids = scraper._extract_team_ids(mock_table)

    assert len(team_ids) == 2
    assert isinstance(team_ids, pd.Series)
    assert team_ids.iloc[0] == "1610612739"
    assert team_ids.iloc[1] == "1610612740"


def test_extract_team_ids_no_links(scraper):
    """Test extraction of team IDs when no links are found."""
    mock_table = Mock(spec=WebElement)
    scraper.page_scraper.get_elements_by_class.return_value = None

    team_ids = scraper._extract_team_ids(mock_table)

    assert len(team_ids) == 0
    assert isinstance(team_ids, pd.Series)


# ==================== Table Conversion Tests ====================

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


# ==================== Single Season Scraping Tests ====================

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


def test_scrape_team_stats_for_season_with_extra_params(scraper):
    """Test scraping team stats with extra URL parameters."""
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
                season_type="Regular+Season",
                extra_params={"DistanceRange": "By+Zone"}
            )

            assert isinstance(result, pd.DataFrame)


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


# ==================== Get Enabled Categories Tests ====================

def test_get_enabled_categories_no_config(scraper):
    """Test get_enabled_categories when no categories config exists."""
    scraper.config.team_stats_categories = None

    categories = scraper.get_enabled_categories()

    assert len(categories) == 0


def test_get_enabled_categories_with_config(scraper_with_categories):
    """Test that enabled categories are correctly parsed from config."""
    categories = scraper_with_categories.get_enabled_categories()

    # Should have: traditional, advanced, shooting (from enabled groups)
    assert len(categories) == 3

    category_names = [c.name for c in categories]
    assert 'traditional' in category_names
    assert 'advanced' in category_names
    assert 'shooting' in category_names

    # Hustle should not be included (disabled group)
    assert 'hustle' not in category_names


def test_get_enabled_categories_with_extra_params(scraper_with_categories):
    """Test that extra params are correctly loaded."""
    categories = scraper_with_categories.get_enabled_categories()

    shooting_category = next(c for c in categories if c.name == 'shooting')

    assert shooting_category.extra_params is not None
    assert len(shooting_category.extra_params) == 2


# ==================== Backwards Compatibility Tests ====================

def test_scrape_and_save_team_stats_validation(scraper):
    """Test validation in scrape_and_save_team_stats."""
    with pytest.raises(DataValidationError):
        scraper.scrape_and_save_team_stats([], "shooting")


def test_scrape_and_save_team_stats_single_category_backwards_compatible(scraper):
    """Test that single category mode still works (backwards compatible)."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers', 'Warriors'],
        'FG%': [0.450, 0.460]
    })

    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = mock_df

        scraper.scrape_and_save_team_stats(["2022-23"], stat_category="shooting")

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

        scraper.scrape_and_save_team_stats(["2021-22", "2022-23"], stat_category="shooting")

        # Should be called for each season and each season type
        assert mock_scrape.call_count >= 2
        scraper.data_access.save_dataframes.assert_called_once()


def test_scrape_and_save_team_stats_no_data(scraper):
    """Test when no data is scraped."""
    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = pd.DataFrame()

        scraper.scrape_and_save_team_stats(["2022-23"], stat_category="shooting")

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
        scraper.scrape_and_save_team_stats(["2022-23"], stat_category="shooting")

        # Should still save the data that was successfully scraped
        scraper.data_access.save_dataframes.assert_called_once()


# ==================== Multi-Category Mode Tests ====================

def test_scrape_and_save_team_stats_multi_category(scraper_with_categories):
    """Test scraping multiple categories from config."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers'],
        'FG%': [0.450]
    })

    with patch.object(scraper_with_categories, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = mock_df

        # Call without stat_category to use config-driven multi-category mode
        scraper_with_categories.scrape_and_save_team_stats(["2022-23"])

        # Should save multiple files (one for each category/param combination)
        # traditional, advanced, shooting_by_zone, shooting_5ft_range = 4 files
        assert scraper_with_categories.data_access.save_dataframes.call_count == 4


def test_scrape_and_save_team_stats_no_categories_warning(scraper):
    """Test warning when no categories are enabled."""
    scraper.config.team_stats_categories = None

    # Should not raise, but log a warning and return
    scraper.scrape_and_save_team_stats(["2022-23"])

    # save_dataframes should not be called
    scraper.data_access.save_dataframes.assert_not_called()


def test_scrape_category_with_extra_params(scraper):
    """Test _scrape_category handles extra params correctly."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers'],
        'FG%': [0.450]
    })

    category = StatCategoryConfig(
        name="shooting",
        extra_params=[
            {"DistanceRange": "By+Zone"},
            {"DistanceRange": "5ft+Range"}
        ]
    )

    with patch.object(scraper, '_scrape_and_save_single_category') as mock_single:
        scraper._scrape_category(["2022-23"], category)

        # Should be called twice (once for each extra param)
        assert mock_single.call_count == 2


def test_scrape_category_without_extra_params(scraper):
    """Test _scrape_category handles no extra params correctly."""
    category = StatCategoryConfig(name="traditional")

    with patch.object(scraper, '_scrape_and_save_single_category') as mock_single:
        scraper._scrape_category(["2022-23"], category)

        # Should be called once with None extra_param
        mock_single.assert_called_once()
        call_args = mock_single.call_args
        assert call_args[0][2] is None  # extra_param should be None


def test_saved_dataframe_includes_stat_category_column(scraper):
    """Test that saved dataframe includes StatCategory column."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers'],
        'FG%': [0.450]
    })

    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = mock_df

        scraper.scrape_and_save_team_stats(["2022-23"], stat_category="traditional")

        call_args = scraper.data_access.save_dataframes.call_args
        saved_df = call_args[0][0][0]

        assert 'StatCategory' in saved_df.columns
        assert saved_df['StatCategory'].iloc[0] == 'traditional'


def test_saved_dataframe_includes_extra_param_column(scraper):
    """Test that saved dataframe includes extra param column when applicable."""
    mock_df = pd.DataFrame({
        'Team': ['Lakers'],
        'FG%': [0.450]
    })

    category = StatCategoryConfig(
        name="shooting",
        extra_params=[{"DistanceRange": "By+Zone"}]
    )

    with patch.object(scraper, 'scrape_team_stats_for_season') as mock_scrape:
        mock_scrape.return_value = mock_df

        scraper._scrape_and_save_single_category(
            ["2022-23"],
            category,
            {"DistanceRange": "By+Zone"}
        )

        call_args = scraper.data_access.save_dataframes.call_args
        saved_df = call_args[0][0][0]

        assert 'DistanceRange' in saved_df.columns
        assert saved_df['DistanceRange'].iloc[0] == 'By+Zone'


# ==================== Backwards Compatibility Alias Test ====================

def test_backwards_compatibility_alias():
    """Test that TeamStatsShootingScraper alias exists for backwards compatibility."""
    from nba_app.webscraping.team_stats_scraper import TeamStatsShootingScraper

    assert TeamStatsShootingScraper is TeamStatsScraper


# ==================== Per-Team Scraping Tests ====================

from nba_app.webscraping.team_stats_scraper import (
    DimensionConfig,
    PerTeamScrapingConfig,
    RateLimiter
)


def test_dimension_config():
    """Test DimensionConfig dataclass."""
    dim = DimensionConfig(name="Month", values=["0", "1", "2"], enabled=True)
    assert dim.name == "Month"
    assert len(dim.values) == 3
    assert dim.enabled is True


def test_rate_limiter_initialization():
    """Test RateLimiter initialization."""
    limiter = RateLimiter(
        delay_between_requests=1.0,
        delay_between_teams=3.0,
        max_retries=5,
        retry_base_delay=1.5
    )
    assert limiter.delay_between_requests == 1.0
    assert limiter.delay_between_teams == 3.0
    assert limiter.max_retries == 5
    assert limiter.retry_base_delay == 1.5


def test_rate_limiter_retry_delay():
    """Test RateLimiter exponential backoff."""
    limiter = RateLimiter(retry_base_delay=2.0)
    assert limiter.get_retry_delay(0) == 2.0  # 2^1
    assert limiter.get_retry_delay(1) == 4.0  # 2^2
    assert limiter.get_retry_delay(2) == 8.0  # 2^3
    assert limiter.get_retry_delay(10) == 60.0  # Capped at 60


def test_construct_per_team_url_basic(scraper):
    """Test per-team URL construction without filters."""
    url = scraper._construct_per_team_url(
        team_id="1610612738",
        stat_category="traditional",
        season="2024-25",
        season_type="Regular+Season"
    )
    assert url == "https://www.nba.com/stats/team/1610612738/traditional?SeasonType=Regular+Season&Season=2024-25"


def test_construct_per_team_url_with_dimensions(scraper):
    """Test per-team URL construction with dimension parameters."""
    url = scraper._construct_per_team_url(
        team_id="1610612738",
        stat_category="traditional",
        season="2024-25",
        season_type="Regular+Season",
        dimension_params={"Month": "1", "Location": "Home"}
    )
    assert "Month=1" in url
    assert "Location=Home" in url


def test_construct_per_team_url_with_extra_params(scraper):
    """Test per-team URL construction with extra parameters."""
    url = scraper._construct_per_team_url(
        team_id="1610612738",
        stat_category="shooting",
        season="2024-25",
        season_type="Regular+Season",
        extra_params={"DistanceRange": "By+Zone"}
    )
    assert "DistanceRange=By+Zone" in url


def test_generate_dimension_combinations_empty(scraper):
    """Test dimension combination generation with no dimensions."""
    combos = scraper._generate_dimension_combinations([])
    assert combos == [{}]


def test_generate_dimension_combinations_single(scraper):
    """Test dimension combination generation with single dimension."""
    dims = [DimensionConfig(name="Month", values=["0", "1"], enabled=True)]
    combos = scraper._generate_dimension_combinations(dims)
    assert len(combos) == 2
    assert {"Month": "0"} in combos
    assert {"Month": "1"} in combos


def test_generate_dimension_combinations_multiple(scraper):
    """Test dimension combination generation with multiple dimensions."""
    dims = [
        DimensionConfig(name="Month", values=["0", "1"], enabled=True),
        DimensionConfig(name="Location", values=["Home", "Road"], enabled=True)
    ]
    combos = scraper._generate_dimension_combinations(dims)
    assert len(combos) == 4  # 2 x 2 = 4
    assert {"Month": "0", "Location": "Home"} in combos
    assert {"Month": "1", "Location": "Road"} in combos


def test_generate_per_team_filename_basic(scraper):
    """Test per-team filename generation."""
    category = StatCategoryConfig(name="traditional")
    filename = scraper._generate_per_team_filename(
        category=category,
        team_abbrev="LAL",
        dimension_params={}
    )
    assert filename == "per_team_stats_traditional_lal_all.csv"


def test_generate_per_team_filename_with_dimensions(scraper):
    """Test per-team filename generation with dimension parameters."""
    category = StatCategoryConfig(name="traditional")
    filename = scraper._generate_per_team_filename(
        category=category,
        team_abbrev="BOS",
        dimension_params={"Month": "1", "Location": "Home"}
    )
    assert "per_team_stats_traditional_bos" in filename
    assert "location_home" in filename
    assert "month_1" in filename


def test_generate_per_team_filename_with_extra_params(scraper):
    """Test per-team filename generation with extra parameters."""
    category = StatCategoryConfig(name="shooting")
    filename = scraper._generate_per_team_filename(
        category=category,
        team_abbrev="GSW",
        dimension_params={},
        extra_param={"DistanceRange": "By+Zone"}
    )
    assert filename == "per_team_stats_shooting_by_zone_gsw_all.csv"


def test_get_per_team_config_disabled(scraper):
    """Test get_per_team_config returns None when disabled."""
    scraper.config.per_team_stats = None
    config = scraper.get_per_team_config()
    assert config is None


def test_get_per_team_config_no_team_mapping(scraper):
    """Test get_per_team_config returns None when no team mapping."""
    scraper.config.per_team_stats = {'enabled': True, 'teams': 'all'}
    scraper.config.team_id_to_abbrev = None
    config = scraper.get_per_team_config()
    assert config is None


def test_scrape_and_save_per_team_stats_not_enabled(scraper):
    """Test per-team scraping skips when not enabled."""
    scraper.config.per_team_stats = None

    with patch.object(scraper, 'scrape_per_team_stats_for_season') as mock_scrape:
        scraper.scrape_and_save_per_team_stats(["2024-25"])
        mock_scrape.assert_not_called()
