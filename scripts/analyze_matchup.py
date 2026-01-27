#!/usr/bin/env python3
"""
NBA Team Matchup Analysis System

Analyzes two teams using the 4-dimension framework:
1. Four Factors Clash - Rebounding, Turnovers, Free Throws, Shooting
2. Style & Geometry - Pace, Rim Attack, 3PT, PlayType
3. Key Matchups - Player archetypes vs defensive resources
4. Context & Form - Recent 10-game trends, rest days, back-to-back

Usage:
    python scripts/analyze_matchup.py HOU LAL
    python scripts/analyze_matchup.py HOU LAL --out "LeBron James"
    python scripts/analyze_matchup.py HOU LAL --month december
"""

import sys
import argparse
import time
import random
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any

import pandas as pd
import numpy as np

# Try to import zoneinfo (Python 3.9+) or fall back to pytz
try:
    from zoneinfo import ZoneInfo
except ImportError:
    try:
        from pytz import timezone as ZoneInfo
    except ImportError:
        ZoneInfo = None

# Configuration
DATA_DIR = Path("data/newly_scraped/tracking_monthly/2025_26")
ANALYSIS_DIR = Path("data/analysis")
SCHEDULE_DIR = Path("data/schedules")
CURRENT_SEASON = "2025-26"

# NBA uses US Eastern Time for scheduling
US_EASTERN_TZ = "America/New_York"

# Common timezone shortcuts
TIMEZONE_SHORTCUTS = {
    'beijing': 'Asia/Shanghai',
    'shanghai': 'Asia/Shanghai',
    'china': 'Asia/Shanghai',
    'cst': 'Asia/Shanghai',      # China Standard Time
    'et': 'America/New_York',    # US Eastern Time
    'eastern': 'America/New_York',
    'pt': 'America/Los_Angeles', # US Pacific Time
    'pacific': 'America/Los_Angeles',
    'ct': 'America/Chicago',     # US Central Time
    'central': 'America/Chicago',
    'utc': 'UTC',
    'gmt': 'UTC',
}

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def convert_to_us_eastern(local_date: datetime, local_tz_str: str) -> datetime:
    """
    Convert a local date to US Eastern Time date.

    Args:
        local_date: Date in user's local timezone (naive datetime, date only)
        local_tz_str: Timezone string (e.g., 'Asia/Shanghai', '+8', 'beijing')

    Returns:
        Date in US Eastern Time (naive datetime, date only)
    """
    if ZoneInfo is None:
        print("Warning: Timezone conversion requires Python 3.9+ or pytz package")
        print("         Install pytz: pip install pytz")
        return local_date

    # Handle shortcuts
    tz_str = TIMEZONE_SHORTCUTS.get(local_tz_str.lower(), local_tz_str)

    # Handle UTC offset format (+8, -5, +08:00, etc.)
    if tz_str.startswith(('+', '-')):
        try:
            # Parse offset like +8, -5, +08:00
            offset_str = tz_str.replace(':', '')
            if len(offset_str) <= 3:  # +8 or -5
                hours = int(offset_str)
                minutes = 0
            else:  # +0800 or -0500
                hours = int(offset_str[:-2])
                minutes = int(offset_str[-2:])
            offset = timedelta(hours=hours, minutes=minutes)
            local_tz = timezone(offset)
        except ValueError:
            print(f"Warning: Invalid timezone offset '{local_tz_str}'")
            return local_date
    else:
        # Use named timezone
        try:
            local_tz = ZoneInfo(tz_str)
        except Exception as e:
            print(f"Warning: Unknown timezone '{tz_str}': {e}")
            print("         Use format like 'Asia/Shanghai' or '+8'")
            return local_date

    try:
        us_eastern = ZoneInfo(US_EASTERN_TZ)
    except Exception:
        # Fallback: US Eastern is typically UTC-5 (EST) or UTC-4 (EDT)
        # Use UTC-5 as default
        us_eastern = timezone(timedelta(hours=-5))

    # Assume local_date is at 23:59 local time (end of day)
    # This ensures we get the correct US date for games played in the evening
    local_datetime = local_date.replace(hour=23, minute=59)

    # Make it timezone-aware
    if hasattr(local_tz, 'localize'):
        # pytz style
        local_aware = local_tz.localize(local_datetime)
    else:
        # zoneinfo style
        local_aware = local_datetime.replace(tzinfo=local_tz)

    # Convert to US Eastern
    us_eastern_datetime = local_aware.astimezone(us_eastern)

    # Return date only (naive datetime)
    return datetime(us_eastern_datetime.year, us_eastern_datetime.month, us_eastern_datetime.day)

# ============================================================================
# Team Mapping
# ============================================================================

ABBREV_TO_FULL = {
    'ATL': 'Atlanta Hawks', 'BOS': 'Boston Celtics', 'BKN': 'Brooklyn Nets',
    'BRK': 'Brooklyn Nets', 'CHA': 'Charlotte Hornets', 'CHI': 'Chicago Bulls',
    'CLE': 'Cleveland Cavaliers', 'DAL': 'Dallas Mavericks', 'DEN': 'Denver Nuggets',
    'DET': 'Detroit Pistons', 'GSW': 'Golden State Warriors', 'HOU': 'Houston Rockets',
    'IND': 'Indiana Pacers', 'LAC': 'LA Clippers', 'LAL': 'LA Lakers',
    'MEM': 'Memphis Grizzlies', 'MIA': 'Miami Heat', 'MIL': 'Milwaukee Bucks',
    'MIN': 'Minnesota Timberwolves', 'NOP': 'New Orleans Pelicans',
    'NYK': 'New York Knicks', 'OKC': 'Oklahoma City Thunder', 'ORL': 'Orlando Magic',
    'PHI': 'Philadelphia 76ers', 'PHX': 'Phoenix Suns', 'POR': 'Portland Trail Blazers',
    'SAC': 'Sacramento Kings', 'SAS': 'San Antonio Spurs', 'TOR': 'Toronto Raptors',
    'UTA': 'Utah Jazz', 'WAS': 'Washington Wizards'
}

ABBREV_TO_TEAM_ID = {
    'ATL': 1610612737, 'BOS': 1610612738, 'BKN': 1610612751, 'BRK': 1610612751,
    'CHA': 1610612766, 'CHI': 1610612741, 'CLE': 1610612739, 'DAL': 1610612742,
    'DEN': 1610612743, 'DET': 1610612765, 'GSW': 1610612744, 'HOU': 1610612745,
    'IND': 1610612754, 'LAC': 1610612746, 'LAL': 1610612747, 'MEM': 1610612763,
    'MIA': 1610612748, 'MIL': 1610612749, 'MIN': 1610612750, 'NOP': 1610612740,
    'NYK': 1610612752, 'OKC': 1610612760, 'ORL': 1610612753, 'PHI': 1610612755,
    'PHX': 1610612756, 'POR': 1610612757, 'SAC': 1610612758, 'SAS': 1610612759,
    'TOR': 1610612761, 'UTA': 1610612762, 'WAS': 1610612764
}

TEAM_ID_TO_ABBREV = {v: k for k, v in ABBREV_TO_TEAM_ID.items() if k != 'BKN'}

# ============================================================================
# Data Loading Functions
# ============================================================================

def load_csv_safe(filepath: Path) -> Optional[pd.DataFrame]:
    """Load CSV file if exists, otherwise return None."""
    if filepath.exists():
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            print(f"Warning: Could not load {filepath}: {e}")
    return None


def get_team_row(df: pd.DataFrame, team_abbrev: str) -> Optional[pd.Series]:
    """Get team row from dataframe, handling different column names."""
    full_name = ABBREV_TO_FULL.get(team_abbrev)
    team_id = ABBREV_TO_TEAM_ID.get(team_abbrev)

    if full_name is None:
        return None

    # Try different column names
    for col in ['Team', 'TEAM']:
        if col in df.columns:
            match = df[df[col] == full_name]
            if not match.empty:
                return match.iloc[0]

    # Try by TEAM_ID
    if 'TEAM_ID' in df.columns and team_id:
        match = df[df['TEAM_ID'] == team_id]
        if not match.empty:
            return match.iloc[0]

    return None


def load_four_factors(month: str = "january") -> Optional[pd.DataFrame]:
    """Load four factors data for a month."""
    filepath = DATA_DIR / f"four_factors_{month}.csv"
    return load_csv_safe(filepath)


def load_team_advanced(month: str = "january") -> Optional[pd.DataFrame]:
    """Load team advanced stats for a month."""
    filepath = DATA_DIR / f"team_advanced_{month}.csv"
    return load_csv_safe(filepath)


def load_defense_rim(month: str = "january") -> Optional[pd.DataFrame]:
    """Load rim defense data (defense dash lt6)."""
    filepath = DATA_DIR / f"defense_dash_lt6_{month}.csv"
    return load_csv_safe(filepath)


def load_playtype_data(month: str = "january") -> Dict[str, pd.DataFrame]:
    """Load all playtype data files for a month."""
    playtypes = {}
    playtype_names = [
        'isolation', 'transition', 'ball_handler', 'roll_man',
        'post_up', 'spot_up', 'handoff', 'cut', 'off_screen', 'putbacks', 'misc'
    ]

    for ptype in playtype_names:
        filepath = DATA_DIR / f"playtype_{ptype}_{month}.csv"
        df = load_csv_safe(filepath)
        if df is not None:
            playtypes[ptype] = df

    return playtypes


def load_player_classifications() -> Optional[pd.DataFrame]:
    """Load player classification data."""
    filepath = ANALYSIS_DIR / "player_classification_2025_26.csv"
    return load_csv_safe(filepath)


# ============================================================================
# Real-time Data Scraping Functions
# ============================================================================

def get_scraper():
    """Initialize and return the team stats scraper."""
    try:
        from src.nba_app.webscraping.di_container import DIContainer
        container = DIContainer()

        # Initialize the logger first
        app_logger = container.app_logger()
        app_logger.setup("matchup_analysis.log")

        return container.team_stats_scraper(), container
    except Exception as e:
        print(f"Warning: Could not initialize scraper: {e}")
        return None, None


def scrape_last_n_games(stat_category: str, n: int = 10,
                        scraper=None) -> Optional[pd.DataFrame]:
    """
    Scrape team stats for the last N games.

    Args:
        stat_category: Category to scrape (e.g., 'four-factors', 'advanced')
        n: Number of recent games (default: 10)
        scraper: Pre-initialized scraper (optional)

    Returns:
        DataFrame with last N games stats, or None if failed.
    """
    if scraper is None:
        scraper, container = get_scraper()
        if scraper is None:
            return None

    try:
        df = scraper.scrape_team_stats_for_season(
            season=CURRENT_SEASON,
            stat_category=stat_category,
            season_type="Regular+Season",
            extra_params={"LastNGames": str(n)}
        )
        return df
    except Exception as e:
        print(f"Warning: Could not scrape {stat_category} (Last {n} games): {e}")
        return None


def scrape_team_schedule(team_id: int, scraper=None) -> Optional[pd.DataFrame]:
    """
    Scrape a team's full season schedule from NBA.com.

    The schedule page format: https://www.nba.com/team/{TEAM_ID}/schedule

    Args:
        team_id: NBA team ID (e.g., 1610612745 for HOU)
        scraper: Pre-initialized scraper (optional)

    Returns:
        DataFrame with schedule data, or None if failed.
    """
    # Note: This would require custom scraping logic since schedule pages
    # have a different format than stats pages. For now, we'll use a
    # simplified approach or return None.
    return None


def load_or_scrape_schedule(season: str = "2025_26") -> Optional[pd.DataFrame]:
    """
    Load team schedule from cache, or scrape if not available.

    Schedule is cached because it's fixed at the start of the season.

    Args:
        season: Season identifier (e.g., '2025_26')

    Returns:
        DataFrame with all team schedules, or None if not available.
    """
    SCHEDULE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = SCHEDULE_DIR / f"schedule_{season}.csv"

    if cache_file.exists():
        return pd.read_csv(cache_file)

    # Schedule scraping would be implemented here
    # For now, return None (feature to be implemented)
    return None


def calculate_rest_days(schedule_df: pd.DataFrame, team_abbrev: str,
                        game_date: datetime) -> Optional[int]:
    """
    Calculate rest days for a team before a specific game.

    Args:
        schedule_df: Full schedule DataFrame
        team_abbrev: Team abbreviation (e.g., 'HOU')
        game_date: Date of the upcoming game

    Returns:
        Number of rest days, or None if cannot calculate.
    """
    if schedule_df is None:
        return None

    team_id = ABBREV_TO_TEAM_ID.get(team_abbrev)
    if team_id is None:
        return None

    # Filter team's games before game_date
    team_games = schedule_df[
        (schedule_df['TEAM_ID'] == team_id) &
        (pd.to_datetime(schedule_df['GAME_DATE']) < game_date)
    ].sort_values('GAME_DATE', ascending=False)

    if team_games.empty:
        return None

    last_game_date = pd.to_datetime(team_games.iloc[0]['GAME_DATE'])
    rest_days = (game_date - last_game_date).days - 1

    return rest_days


def is_back_to_back(schedule_df: pd.DataFrame, team_abbrev: str,
                    game_date: datetime) -> Optional[bool]:
    """
    Check if a game is the second of a back-to-back.

    Args:
        schedule_df: Full schedule DataFrame
        team_abbrev: Team abbreviation
        game_date: Date of the game

    Returns:
        True if B2B second game, False otherwise, None if cannot determine.
    """
    rest_days = calculate_rest_days(schedule_df, team_abbrev, game_date)
    if rest_days is None:
        return None
    return rest_days == 0


# ============================================================================
# Analysis Functions - Dimension 1: Four Factors Clash
# ============================================================================

def analyze_four_factors_clash(team_a: str, team_b: str,
                                ff_df: pd.DataFrame,
                                adv_df: pd.DataFrame) -> Dict:
    """
    Analyze four factors clash between two teams.

    Compares:
    - Rebounding: A's OREB% vs B's allowed OREB%
    - Turnovers: A's TOV% vs B's forced TOV%
    - Free throws: A's FTA Rate vs B's fouling tendency
    - Shooting: A's eFG% vs B's defensive eFG%
    """
    a_ff = get_team_row(ff_df, team_a)
    b_ff = get_team_row(ff_df, team_b)
    a_adv = get_team_row(adv_df, team_a)
    b_adv = get_team_row(adv_df, team_b)

    if any(x is None for x in [a_ff, b_ff, a_adv, b_adv]):
        return {"error": "Could not find team data"}

    clashes = []

    # 1. Rebounding clash
    a_oreb = a_ff.get('OREB%', 0)
    b_opp_oreb = b_ff.get('Opp OREB%', 0)
    b_dreb = b_adv.get('DREB%', 0)

    rebound_diff = a_oreb - b_opp_oreb
    clashes.append({
        'metric': 'Rebounding',
        'metric_cn': '篮板争夺',
        'team_a_val': a_oreb,
        'team_a_desc': f"{a_oreb:.1f}% OREB",
        'team_b_val': b_opp_oreb,
        'team_b_desc': f"{b_opp_oreb:.1f}% allow",
        'advantage': team_a if rebound_diff > 2 else (team_b if rebound_diff < -2 else 'EVEN'),
        'magnitude': abs(rebound_diff),
        'insight': f"{team_a} 前场篮板率 {a_oreb:.1f}%，{team_b} 允许 {b_opp_oreb:.1f}%"
    })

    # 2. Turnover clash
    a_tov = a_ff.get('TOV%', 0)
    b_force_tov = b_ff.get('Opp TOV%', 0)

    tov_diff = b_force_tov - a_tov  # Higher force - lower commit = advantage for B's defense
    clashes.append({
        'metric': 'Turnovers',
        'metric_cn': '失误控制',
        'team_a_val': a_tov,
        'team_a_desc': f"{a_tov:.1f}% TOV",
        'team_b_val': b_force_tov,
        'team_b_desc': f"{b_force_tov:.1f}% force",
        'advantage': team_b if tov_diff > 2 else (team_a if tov_diff < -2 else 'EVEN'),
        'magnitude': abs(tov_diff),
        'insight': f"{team_a} 失误率 {a_tov:.1f}%，{team_b} 造失误率 {b_force_tov:.1f}%"
    })

    # 3. Free throw clash
    a_fta = a_ff.get('FTA Rate', 0)
    b_opp_fta = b_ff.get('Opp FTA Rate', 0)

    fta_diff = a_fta - b_opp_fta
    clashes.append({
        'metric': 'Free Throws',
        'metric_cn': '罚球控制',
        'team_a_val': a_fta,
        'team_a_desc': f"{a_fta:.3f} FTA",
        'team_b_val': b_opp_fta,
        'team_b_desc': f"{b_opp_fta:.3f} foul",
        'advantage': team_a if fta_diff > 0.03 else (team_b if fta_diff < -0.03 else 'EVEN'),
        'magnitude': abs(fta_diff),
        'insight': f"{team_a} 罚球率 {a_fta:.3f}，{team_b} 犯规率 {b_opp_fta:.3f}"
    })

    # 4. Shooting efficiency clash
    a_efg = a_ff.get('eFG%', 0)
    b_opp_efg = b_ff.get('Opp eFG%', 0)

    efg_diff = a_efg - b_opp_efg
    clashes.append({
        'metric': 'Shooting',
        'metric_cn': '投篮效率',
        'team_a_val': a_efg,
        'team_a_desc': f"{a_efg:.1f}% eFG",
        'team_b_val': b_opp_efg,
        'team_b_desc': f"{b_opp_efg:.1f}% allow",
        'advantage': team_a if efg_diff > 2 else (team_b if efg_diff < -2 else 'EVEN'),
        'magnitude': abs(efg_diff),
        'insight': f"{team_a} 有效命中率 {a_efg:.1f}%，{team_b} 防守限制为 {b_opp_efg:.1f}%"
    })

    # Calculate dimension winner
    a_wins = sum(1 for c in clashes if c['advantage'] == team_a)
    b_wins = sum(1 for c in clashes if c['advantage'] == team_b)

    return {
        'clashes': clashes,
        'team_a_wins': a_wins,
        'team_b_wins': b_wins,
        'dimension_winner': team_a if a_wins > b_wins else (team_b if b_wins > a_wins else 'EVEN'),
        'raw_data': {
            'team_a': {'OREB%': a_oreb, 'TOV%': a_tov, 'FTA_Rate': a_fta, 'eFG%': a_efg},
            'team_b': {'Opp_OREB%': b_opp_oreb, 'Opp_TOV%': b_force_tov, 'Opp_FTA_Rate': b_opp_fta, 'Opp_eFG%': b_opp_efg}
        }
    }


# ============================================================================
# Analysis Functions - Dimension 2: Style & Geometry
# ============================================================================

def analyze_style_geometry(team_a: str, team_b: str,
                           adv_df: pd.DataFrame,
                           def_rim_df: pd.DataFrame,
                           playtype_data: Dict[str, pd.DataFrame]) -> Dict:
    """
    Analyze style and geometry matchups.

    Includes:
    - Pace control
    - Rim attack vs rim defense
    - PlayType efficiency matchups
    """
    a_adv = get_team_row(adv_df, team_a)
    b_adv = get_team_row(adv_df, team_b)

    if a_adv is None or b_adv is None:
        return {"error": "Could not find team advanced data"}

    analysis = {}

    # 1. Pace analysis
    a_pace = a_adv.get('PACE', 0)
    b_pace = b_adv.get('PACE', 0)
    pace_diff = a_pace - b_pace

    analysis['pace'] = {
        'team_a_pace': a_pace,
        'team_b_pace': b_pace,
        'faster_team': team_a if pace_diff > 0 else team_b,
        'pace_delta': abs(pace_diff),
        'insight': f"{team_a} ({a_pace:.1f}) vs {team_b} ({b_pace:.1f})" +
                   (" - 节奏接近" if abs(pace_diff) < 2 else
                    f" - {team_a if pace_diff > 0 else team_b} 偏好快节奏")
    }

    # 2. Rim attack vs rim defense
    if def_rim_df is not None:
        a_rim = get_team_row(def_rim_df, team_a)
        b_rim = get_team_row(def_rim_df, team_b)

        if a_rim is not None and b_rim is not None:
            # DFG% at rim - lower is better defense
            b_rim_dfg = b_rim.get('DFG%', 65)

            analysis['rim'] = {
                'team_b_rim_dfg': b_rim_dfg,
                'insight': f"{team_b} 护框 DFG% = {b_rim_dfg:.1f}%" +
                          (" (较弱)" if b_rim_dfg > 65 else " (较强)" if b_rim_dfg < 60 else " (中等)")
            }

    # 3. PlayType analysis
    key_playtypes = ['isolation', 'transition', 'ball_handler', 'spot_up', 'post_up']
    playtype_analysis = []

    for ptype in key_playtypes:
        if ptype in playtype_data:
            df = playtype_data[ptype]
            a_pt = get_team_row(df, team_a)
            b_pt = get_team_row(df, team_b)

            if a_pt is not None:
                ppp = a_pt.get('PPP', 0)
                freq = a_pt.get('FREQ%', 0)
                percentile = a_pt.get('PERCENTILE', 50)

                playtype_analysis.append({
                    'type': ptype,
                    'team': team_a,
                    'ppp': ppp,
                    'freq': freq,
                    'percentile': percentile,
                    'rating': 'elite' if percentile > 75 else 'good' if percentile > 50 else 'poor'
                })

    analysis['playtypes'] = playtype_analysis

    # 4. Overall style characterization
    a_offrtg = a_adv.get('OffRtg', 0)
    a_defrtg = a_adv.get('DefRtg', 0)
    b_offrtg = b_adv.get('OffRtg', 0)
    b_defrtg = b_adv.get('DefRtg', 0)

    analysis['ratings'] = {
        'team_a': {'OffRtg': a_offrtg, 'DefRtg': a_defrtg, 'NetRtg': a_offrtg - a_defrtg},
        'team_b': {'OffRtg': b_offrtg, 'DefRtg': b_defrtg, 'NetRtg': b_offrtg - b_defrtg}
    }

    return analysis


# ============================================================================
# Analysis Functions - Dimension 3: Key Matchups
# ============================================================================

def analyze_key_matchups(team_a: str, team_b: str,
                         player_df: pd.DataFrame,
                         out_players: List[str] = None) -> Dict:
    """
    Analyze key player matchups based on archetypes.
    """
    if player_df is None:
        return {"error": "Player classification data not available"}

    out_players = out_players or []
    out_players_lower = [p.lower() for p in out_players]

    # Get team rosters
    a_players = player_df[player_df['TEAM'] == team_a].copy()
    b_players = player_df[player_df['TEAM'] == team_b].copy()

    # Get latest month data and deduplicate
    a_players = a_players.sort_values('Month').groupby('PLAYER_ID').last().reset_index()
    b_players = b_players.sort_values('Month').groupby('PLAYER_ID').last().reset_index()

    # Mark out players
    a_players['is_out'] = a_players['PLAYER'].str.lower().isin(out_players_lower)
    b_players['is_out'] = b_players['PLAYER'].str.lower().isin(out_players_lower)

    analysis = {
        'out_players': [],
        'team_a_scorers': [],
        'team_b_scorers': [],
        'team_a_defenders': [],
        'team_b_defenders': [],
        'out_impact': []
    }

    # Record out players
    for _, p in a_players[a_players['is_out']].iterrows():
        analysis['out_players'].append({'team': team_a, 'player': p['PLAYER'], 'archetype': p['Archetype']})
    for _, p in b_players[b_players['is_out']].iterrows():
        analysis['out_players'].append({'team': team_b, 'player': p['PLAYER'], 'archetype': p['Archetype']})

    # Filter out players that are out
    a_active = a_players[~a_players['is_out']]
    b_active = b_players[~b_players['is_out']]

    # Top scorers (by PTS)
    scorer_categories = ['Primary', 'Scorer', 'Secondary', 'Shooter']

    a_scorers = a_active.nlargest(3, 'PTS')
    for _, p in a_scorers.iterrows():
        analysis['team_a_scorers'].append({
            'player': p['PLAYER'],
            'archetype': p['Archetype'],
            'category': p['Category'],
            'pts': p['PTS'],
            'usg': p.get('USG_Pct', 0)
        })

    b_scorers = b_active.nlargest(3, 'PTS')
    for _, p in b_scorers.iterrows():
        analysis['team_b_scorers'].append({
            'player': p['PLAYER'],
            'archetype': p['Archetype'],
            'category': p['Category'],
            'pts': p['PTS'],
            'usg': p.get('USG_Pct', 0)
        })

    # Defensive resources
    defensive_archetypes = ['Rim Protector', '3&D Wing']

    a_defenders = a_active[a_active['Archetype'].isin(defensive_archetypes)]
    for _, p in a_defenders.iterrows():
        analysis['team_a_defenders'].append({
            'player': p['PLAYER'],
            'archetype': p['Archetype'],
            'size': p.get('Size', 'Unknown')
        })

    b_defenders = b_active[b_active['Archetype'].isin(defensive_archetypes)]
    for _, p in b_defenders.iterrows():
        analysis['team_b_defenders'].append({
            'player': p['PLAYER'],
            'archetype': p['Archetype'],
            'size': p.get('Size', 'Unknown')
        })

    # Analyze impact of out players
    for out_info in analysis['out_players']:
        team = out_info['team']
        archetype = out_info['archetype']
        player = out_info['player']

        if archetype == 'Rim Protector':
            analysis['out_impact'].append(f"{team} 失去唯一的 Rim Protector，护框能力大幅下降")
        elif archetype in ['Primary Initiator', 'Shot Creator']:
            analysis['out_impact'].append(f"{team} 缺少 {archetype}，进攻火力下降")
        elif archetype == '3&D Wing':
            analysis['out_impact'].append(f"{team} 缺少 3&D Wing，侧翼防守削弱")

    # Archetype distribution
    analysis['team_a_distribution'] = a_active.groupby('Archetype').size().to_dict()
    analysis['team_b_distribution'] = b_active.groupby('Archetype').size().to_dict()

    return analysis


# ============================================================================
# Analysis Functions - Dimension 4: Context & Form
# ============================================================================

def analyze_context_form(team_a: str, team_b: str,
                         fetch_live: bool = False,
                         game_date: Optional[datetime] = None) -> Dict:
    """
    Analyze recent form using monthly data and optional live data.

    Args:
        team_a: First team abbreviation
        team_b: Second team abbreviation
        fetch_live: Whether to fetch live Last 10 Games data
        game_date: Date of the matchup (for schedule analysis)

    Returns:
        Dictionary with context and form analysis.
    """
    months = ['october', 'november', 'december', 'january']

    monthly_data = {team_a: [], team_b: []}

    for month in months:
        adv_df = load_team_advanced(month)
        if adv_df is not None:
            for team in [team_a, team_b]:
                row = get_team_row(adv_df, team)
                if row is not None:
                    monthly_data[team].append({
                        'month': month,
                        'NetRtg': row.get('NetRtg', 0),
                        'OffRtg': row.get('OffRtg', 0),
                        'DefRtg': row.get('DefRtg', 0),
                        'W': row.get('W', 0),
                        'L': row.get('L', 0)
                    })

    def calculate_trend(data):
        if len(data) < 2:
            return 'insufficient_data'
        netrtgs = [d['NetRtg'] for d in data]
        recent = np.mean(netrtgs[-2:]) if len(netrtgs) >= 2 else netrtgs[-1]
        early = np.mean(netrtgs[:2]) if len(netrtgs) >= 2 else netrtgs[0]
        diff = recent - early
        if diff > 3:
            return 'improving'
        elif diff < -3:
            return 'declining'
        return 'stable'

    result = {
        'team_a_monthly': monthly_data[team_a],
        'team_b_monthly': monthly_data[team_b],
        'team_a_trend': calculate_trend(monthly_data[team_a]),
        'team_b_trend': calculate_trend(monthly_data[team_b]),
        'last_10_games': None,
        'last_10_requested': fetch_live,  # Track if live data was requested
        'schedule_info': None,
    }

    # Fetch live Last 10 Games data if requested
    if fetch_live:
        print("  Fetching Last 10 Games data...")
        last10_data = fetch_last_10_games_data(team_a, team_b)
        if last10_data:
            result['last_10_games'] = last10_data

        # Load schedule data
        schedule_df = load_or_scrape_schedule()
        if schedule_df is not None and game_date is not None:
            result['schedule_info'] = {
                team_a: {
                    'rest_days': calculate_rest_days(schedule_df, team_a, game_date),
                    'is_b2b': is_back_to_back(schedule_df, team_a, game_date)
                },
                team_b: {
                    'rest_days': calculate_rest_days(schedule_df, team_b, game_date),
                    'is_b2b': is_back_to_back(schedule_df, team_b, game_date)
                }
            }

    return result


def fetch_last_10_games_data(team_a: str, team_b: str) -> Optional[Dict]:
    """
    Fetch Last 10 Games statistics for both teams.

    Args:
        team_a: First team abbreviation
        team_b: Second team abbreviation

    Returns:
        Dictionary with Last 10 Games stats for both teams, or None if failed.
    """
    scraper, container = get_scraper()
    if scraper is None:
        print("  Warning: Scraper not available, skipping Last 10 Games data")
        return None

    try:
        result = {}

        # Scrape Four Factors (Last 10 Games)
        print("    Scraping four-factors (Last 10 games)...", end=" ")
        time.sleep(random.uniform(2, 4))
        ff_df = scrape_last_n_games("four-factors", n=10, scraper=scraper)

        if ff_df is not None:
            print(f"{len(ff_df)} teams")
            for team in [team_a, team_b]:
                row = get_team_row(ff_df, team)
                if row is not None:
                    result[team] = {
                        'eFG%': row.get('eFG%', 0),
                        'TOV%': row.get('TOV%', 0),
                        'OREB%': row.get('OREB%', 0),
                        'FTA_Rate': row.get('FTA Rate', 0),
                    }
        else:
            print("failed")

        # Scrape Advanced stats (Last 10 Games) for W/L and NetRtg
        print("    Scraping advanced (Last 10 games)...", end=" ")
        time.sleep(random.uniform(2, 4))
        adv_df = scrape_last_n_games("advanced", n=10, scraper=scraper)

        if adv_df is not None:
            print(f"{len(adv_df)} teams")
            for team in [team_a, team_b]:
                row = get_team_row(adv_df, team)
                if row is not None:
                    if team not in result:
                        result[team] = {}
                    result[team].update({
                        'W': row.get('W', 0),
                        'L': row.get('L', 0),
                        'NetRtg': row.get('NetRtg', 0),
                        'OffRtg': row.get('OffRtg', 0),
                        'DefRtg': row.get('DefRtg', 0),
                    })
        else:
            print("failed")

        return result if result else None

    except Exception as e:
        print(f"  Warning: Error fetching Last 10 Games data: {e}")
        return None

    finally:
        # Clean up WebDriver
        try:
            if container:
                container.web_driver_factory().close_driver()
        except:
            pass


# ============================================================================
# Win Conditions & Danger Zones
# ============================================================================

def identify_win_conditions(team: str, opponent: str, analysis: Dict) -> List[Dict]:
    """Identify key win conditions for a team."""
    conditions = []

    # From four factors
    ff = analysis.get('four_factors', {})
    clashes = ff.get('clashes', [])

    for clash in clashes:
        if clash['advantage'] == team and clash['magnitude'] > 3:
            conditions.append({
                'priority': 'HIGH',
                'condition': f"利用 {clash['metric_cn']} 优势 (差距: {clash['magnitude']:.1f})",
                'metric': clash['metric']
            })
        elif clash['advantage'] == team:
            conditions.append({
                'priority': 'MED',
                'condition': f"保持 {clash['metric_cn']} 优势",
                'metric': clash['metric']
            })

    # From style
    style = analysis.get('style_geometry', {})
    pace = style.get('pace', {})

    if pace.get('faster_team') == team:
        conditions.append({
            'priority': 'MED',
            'condition': f"加快节奏到 {pace.get('team_a_pace', 100):.0f}+ 回合",
            'metric': 'pace'
        })
    else:
        conditions.append({
            'priority': 'MED',
            'condition': f"控制节奏在 {pace.get('team_b_pace', 100):.0f} 回合以下",
            'metric': 'pace'
        })

    return conditions[:5]  # Top 5 conditions


def identify_danger_zones(team: str, opponent: str, analysis: Dict) -> List[Dict]:
    """Identify danger zones for a team."""
    dangers = []

    # From four factors - where opponent has advantage
    ff = analysis.get('four_factors', {})
    clashes = ff.get('clashes', [])

    for clash in clashes:
        if clash['advantage'] == opponent and clash['magnitude'] > 3:
            dangers.append({
                'severity': 'CRITICAL',
                'danger': f"对手在 {clash['metric_cn']} 有明显优势",
                'detail': clash['insight']
            })
        elif clash['advantage'] == opponent:
            dangers.append({
                'severity': 'WARNING',
                'danger': f"对手在 {clash['metric_cn']} 略占优势",
                'detail': clash['insight']
            })

    # From matchups - missing key players
    matchups = analysis.get('key_matchups', {})
    for impact in matchups.get('out_impact', []):
        if team in impact:
            dangers.append({
                'severity': 'CRITICAL',
                'danger': impact,
                'detail': '缺阵影响'
            })

    return dangers[:5]


# ============================================================================
# Output Formatting
# ============================================================================

def format_console_output(team_a: str, team_b: str, analysis: Dict) -> str:
    """Format analysis results for console output."""
    lines = []

    # Header
    lines.append("=" * 80)
    lines.append(f"{'MATCHUP ANALYSIS: ' + team_a + ' vs ' + team_b:^80}")
    lines.append("=" * 80)
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("")

    # Dimension 1: Four Factors
    lines.append("-" * 80)
    lines.append("1. FOUR FACTORS CLASH (四要素碰撞)")
    lines.append("-" * 80)

    ff = analysis.get('four_factors', {})
    if 'error' not in ff:
        lines.append(f"| {'指标':<12} | {team_a:<15} | {team_b:<15} | {'优势方':<8} |")
        lines.append("|" + "-" * 14 + "|" + "-" * 17 + "|" + "-" * 17 + "|" + "-" * 10 + "|")

        for clash in ff.get('clashes', []):
            adv = clash['advantage']
            lines.append(f"| {clash['metric_cn']:<12} | {clash['team_a_desc']:<15} | {clash['team_b_desc']:<15} | {adv:<8} |")

        lines.append("")
        lines.append(f"维度胜者: {ff['dimension_winner']} ({ff['team_a_wins']}-{ff['team_b_wins']})")
    else:
        lines.append(f"Error: {ff['error']}")

    lines.append("")

    # Dimension 2: Style & Geometry
    lines.append("-" * 80)
    lines.append("2. STYLE & GEOMETRY (风格碰撞)")
    lines.append("-" * 80)

    style = analysis.get('style_geometry', {})
    if 'error' not in style:
        pace = style.get('pace', {})
        lines.append(f"节奏: {pace.get('insight', 'N/A')}")

        rim = style.get('rim', {})
        if rim:
            lines.append(f"禁区防守: {rim.get('insight', 'N/A')}")

        lines.append("")
        lines.append("关键 PlayType:")
        for pt in style.get('playtypes', [])[:5]:
            rating_cn = {'elite': '顶级', 'good': '良好', 'poor': '较弱'}.get(pt['rating'], '')
            lines.append(f"  - {pt['team']} {pt['type']}: {pt['ppp']:.2f} PPP ({pt['percentile']:.0f}th %ile) {rating_cn}")
    else:
        lines.append(f"Error: {style.get('error', 'Unknown error')}")

    lines.append("")

    # Dimension 3: Key Matchups
    lines.append("-" * 80)
    lines.append("3. KEY MATCHUPS (关键对位)")
    lines.append("-" * 80)

    matchups = analysis.get('key_matchups', {})
    if 'error' not in matchups:
        # Out players
        out_players = matchups.get('out_players', [])
        if out_players:
            out_list = ", ".join([f"{p['team']}-{p['player']}" for p in out_players])
            lines.append(f"⚠️ 缺阵球员: {out_list}")
            lines.append("")

        # Team A scorers
        lines.append(f"{team_a} 核心得分手:")
        for s in matchups.get('team_a_scorers', []):
            lines.append(f"  {s['player']} [{s['archetype']}] - {s['pts']:.1f} PPG, {s['usg']:.1f}% USG")

        lines.append("")

        # Team B defenders
        lines.append(f"{team_b} 防守资源:")
        defenders = matchups.get('team_b_defenders', [])
        if defenders:
            for d in defenders:
                is_out = any(p['player'] == d['player'] for p in out_players)
                marker = "❌ " if is_out else "  "
                out_note = " - 缺阵" if is_out else ""
                lines.append(f"{marker}{d['player']} [{d['archetype']}]{out_note}")
        else:
            lines.append("  无明确防守专家")

        # Out impact
        if matchups.get('out_impact'):
            lines.append("")
            lines.append("缺阵影响分析:")
            for impact in matchups['out_impact']:
                lines.append(f"  >>> {impact}")
    else:
        lines.append(f"Error: {matchups.get('error', 'Unknown error')}")

    lines.append("")

    # Dimension 4: Context & Form
    lines.append("-" * 80)
    lines.append("4. CONTEXT & FORM (状态趋势)")
    lines.append("-" * 80)

    context = analysis.get('context_form', {})

    trend_cn = {'improving': '上升', 'declining': '下滑', 'stable': '稳定', 'insufficient_data': '数据不足'}

    # Last 10 Games data (if available)
    last_10 = context.get('last_10_games')
    last_10_requested = context.get('last_10_requested', False)

    if last_10:
        lines.append("【最近10场表现】(实时数据)")
        for team in [team_a, team_b]:
            if team in last_10:
                d = last_10[team]
                w, l = d.get('W', 0), d.get('L', 0)
                netrtg = d.get('NetRtg', 0)
                efg = d.get('eFG%', 0)
                tov = d.get('TOV%', 0)
                lines.append(f"  {team} L10: {netrtg:+.1f} NetRtg | {w}-{l} | {efg:.1f}% eFG | {tov:.1f}% TOV")

        # Compare recent form
        if team_a in last_10 and team_b in last_10:
            a_net = last_10[team_a].get('NetRtg', 0)
            b_net = last_10[team_b].get('NetRtg', 0)
            if a_net > b_net + 3:
                lines.append(f"  >>> {team_a} 近期状态明显更佳")
            elif b_net > a_net + 3:
                lines.append(f"  >>> {team_b} 近期状态明显更佳")
            else:
                lines.append("  >>> 双方近期状态接近")
        lines.append("")
    elif last_10_requested:
        # User requested live data but scraping failed
        lines.append("【最近10场表现】")
        lines.append("  (抓取失败，请检查网络或 ml_framework 依赖)")
        lines.append("")
    else:
        # User didn't request live data
        lines.append("【最近10场表现】")
        lines.append("  (未启用实时数据，使用 --live 参数获取)")
        lines.append("")

    # Schedule info (if available)
    schedule_info = context.get('schedule_info')
    if schedule_info:
        lines.append("【休息与疲劳】")
        for team in [team_a, team_b]:
            if team in schedule_info:
                info = schedule_info[team]
                rest_days = info.get('rest_days')
                is_b2b = info.get('is_b2b')

                rest_str = f"{rest_days}天" if rest_days is not None else "未知"
                b2b_str = " | 背靠背第2场" if is_b2b else ""
                lines.append(f"  {team}: 距上场 {rest_str}{b2b_str}")

        # Fatigue warning
        for team in [team_a, team_b]:
            if team in schedule_info:
                if schedule_info[team].get('is_b2b'):
                    lines.append(f"  >>> {team} 体能劣势，背靠背作战")
        lines.append("")

    # Monthly trends
    lines.append("【月度趋势】")
    a_monthly = context.get('team_a_monthly', [])
    if a_monthly:
        a_trend_str = " -> ".join([f"{m['month'][:3].capitalize()}({m['NetRtg']:+.1f})" for m in a_monthly])
        lines.append(f"{team_a}: {a_trend_str}")
        lines.append(f"  趋势: {trend_cn.get(context.get('team_a_trend', ''), '未知')}")

    b_monthly = context.get('team_b_monthly', [])
    if b_monthly:
        b_trend_str = " -> ".join([f"{m['month'][:3].capitalize()}({m['NetRtg']:+.1f})" for m in b_monthly])
        lines.append(f"{team_b}: {b_trend_str}")
        lines.append(f"  趋势: {trend_cn.get(context.get('team_b_trend', ''), '未知')}")

    lines.append("")

    # Win Conditions
    lines.append("=" * 80)
    lines.append(f"{'WIN CONDITIONS (胜利条件)':^80}")
    lines.append("=" * 80)

    conditions = analysis.get('win_conditions', {})

    for team in [team_a, team_b]:
        team_conditions = conditions.get(team, [])
        lines.append(f"{team} 获胜需要:")
        for i, c in enumerate(team_conditions, 1):
            lines.append(f"  {i}. [{c['priority']}] {c['condition']}")
        lines.append("")

    # Danger Zones
    lines.append("=" * 80)
    lines.append(f"{'DANGER ZONES (危险区域)':^80}")
    lines.append("=" * 80)

    dangers = analysis.get('danger_zones', {})

    for team in [team_a, team_b]:
        team_dangers = dangers.get(team, [])
        lines.append(f"{team} 需警惕:")
        for d in team_dangers:
            lines.append(f"  - [{d['severity']}] {d['danger']}")
        lines.append("")

    return "\n".join(lines)


# ============================================================================
# Main Function
# ============================================================================

def run_analysis(team_a: str, team_b: str, month: str = "january",
                 out_players: List[str] = None,
                 fetch_live: bool = False,
                 game_date: Optional[datetime] = None) -> Dict:
    """
    Run full matchup analysis.

    Args:
        team_a: First team abbreviation
        team_b: Second team abbreviation
        month: Month to use for analysis
        out_players: List of players that are out
        fetch_live: Whether to fetch live Last 10 Games data
        game_date: Date of the matchup (for schedule analysis)

    Returns:
        Dictionary with full analysis results.
    """
    out_players = out_players or []

    # Validate teams
    if team_a not in ABBREV_TO_FULL:
        return {"error": f"Unknown team: {team_a}"}
    if team_b not in ABBREV_TO_FULL:
        return {"error": f"Unknown team: {team_b}"}

    # Load data
    ff_df = load_four_factors(month)
    adv_df = load_team_advanced(month)
    def_rim_df = load_defense_rim(month)
    playtype_data = load_playtype_data(month)
    player_df = load_player_classifications()

    if ff_df is None or adv_df is None:
        return {"error": "Could not load required data files"}

    # Run analyses
    analysis = {}

    # Dimension 1: Four Factors
    analysis['four_factors'] = analyze_four_factors_clash(team_a, team_b, ff_df, adv_df)

    # Dimension 2: Style & Geometry
    analysis['style_geometry'] = analyze_style_geometry(team_a, team_b, adv_df, def_rim_df, playtype_data)

    # Dimension 3: Key Matchups
    analysis['key_matchups'] = analyze_key_matchups(team_a, team_b, player_df, out_players)

    # Dimension 4: Context & Form (with optional live data)
    analysis['context_form'] = analyze_context_form(team_a, team_b, fetch_live, game_date)

    # Synthesize win conditions and danger zones
    analysis['win_conditions'] = {
        team_a: identify_win_conditions(team_a, team_b, analysis),
        team_b: identify_win_conditions(team_b, team_a, analysis)
    }

    analysis['danger_zones'] = {
        team_a: identify_danger_zones(team_a, team_b, analysis),
        team_b: identify_danger_zones(team_b, team_a, analysis)
    }

    return analysis


def main():
    parser = argparse.ArgumentParser(
        description='Analyze NBA team matchups using the 4-dimension framework'
    )
    parser.add_argument('team_a', type=str, help='First team abbreviation (e.g., HOU)')
    parser.add_argument('team_b', type=str, help='Second team abbreviation (e.g., LAL)')
    parser.add_argument('--month', type=str, default='january',
                        choices=['october', 'november', 'december', 'january'],
                        help='Month to use for analysis (default: january)')
    parser.add_argument('--out', type=str, action='append', default=[],
                        help='Players that are out (can specify multiple times or comma-separated)')
    parser.add_argument('--live', action='store_true',
                        help='Fetch live Last 10 Games data from NBA.com')
    parser.add_argument('--date', type=str, default=None,
                        help='Game date (YYYY-MM-DD) for schedule analysis')
    parser.add_argument('--timezone', '--tz', type=str, default=None,
                        help='Your timezone for date conversion to US Eastern '
                             '(e.g., "beijing", "Asia/Shanghai", "+8")')
    parser.add_argument('--output', type=str, default='console',
                        choices=['console', 'json'],
                        help='Output format (default: console)')

    args = parser.parse_args()

    # Parse out players
    out_players = []
    for out_arg in args.out:
        out_players.extend([p.strip() for p in out_arg.split(',')])

    # Parse game date with optional timezone conversion
    game_date = None
    original_date_str = None
    if args.date:
        try:
            game_date = datetime.strptime(args.date, '%Y-%m-%d')
            original_date_str = args.date

            # Convert to US Eastern if timezone is specified
            if args.timezone:
                us_date = convert_to_us_eastern(game_date, args.timezone)
                if us_date != game_date:
                    original_date_str = f"{args.date} ({args.timezone})"
                game_date = us_date
        except ValueError:
            print(f"Warning: Invalid date format '{args.date}', expected YYYY-MM-DD")

    # Normalize team abbreviations to uppercase
    team_a = args.team_a.upper()
    team_b = args.team_b.upper()

    print(f"Analyzing: {team_a} vs {team_b}")
    print(f"Data month: {args.month}")
    if out_players:
        print(f"Out players: {', '.join(out_players)}")
    if args.live:
        print("Live data: Enabled (will fetch Last 10 Games from NBA.com)")
    if game_date:
        if args.timezone:
            print(f"Game date: {original_date_str} -> {game_date.strftime('%Y-%m-%d')} (US Eastern)")
        else:
            print(f"Game date: {game_date.strftime('%Y-%m-%d')} (assumed US Eastern)")
    print()

    # Run analysis
    analysis = run_analysis(
        team_a, team_b, args.month, out_players,
        fetch_live=args.live, game_date=game_date
    )

    if 'error' in analysis:
        print(f"Error: {analysis['error']}")
        return 1

    # Output
    if args.output == 'console':
        print(format_console_output(team_a, team_b, analysis))
    elif args.output == 'json':
        print(json.dumps(analysis, indent=2, ensure_ascii=False, default=str))

    return 0


if __name__ == "__main__":
    sys.exit(main())
