#!/usr/bin/env python3
"""
NBA 球队新闻和排名爬虫

获取球队最新新闻、伤病动态、排名信息。

用法:
    python scripts/scrape_team_news.py HOU
    python scripts/scrape_team_news.py HOU --json
"""

import sys
import argparse
import json
import time
import random
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

import requests
from bs4 import BeautifulSoup

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configuration
NEWS_CACHE_DIR = Path("data/news")
CURRENT_SEASON = "2025-26"

# Team abbreviation to ESPN slug mapping
ABBREV_TO_ESPN_SLUG = {
    'ATL': 'atl/atlanta-hawks', 'BOS': 'bos/boston-celtics',
    'BKN': 'bkn/brooklyn-nets', 'BRK': 'bkn/brooklyn-nets',
    'CHA': 'cha/charlotte-hornets', 'CHI': 'chi/chicago-bulls',
    'CLE': 'cle/cleveland-cavaliers', 'DAL': 'dal/dallas-mavericks',
    'DEN': 'den/denver-nuggets', 'DET': 'det/detroit-pistons',
    'GSW': 'gs/golden-state-warriors', 'HOU': 'hou/houston-rockets',
    'IND': 'ind/indiana-pacers', 'LAC': 'lac/la-clippers',
    'LAL': 'lal/los-angeles-lakers', 'MEM': 'mem/memphis-grizzlies',
    'MIA': 'mia/miami-heat', 'MIL': 'mil/milwaukee-bucks',
    'MIN': 'min/minnesota-timberwolves', 'NOP': 'no/new-orleans-pelicans',
    'NYK': 'ny/new-york-knicks', 'OKC': 'okc/oklahoma-city-thunder',
    'ORL': 'orl/orlando-magic', 'PHI': 'phi/philadelphia-76ers',
    'PHX': 'phx/phoenix-suns', 'POR': 'por/portland-trail-blazers',
    'SAC': 'sac/sacramento-kings', 'SAS': 'sa/san-antonio-spurs',
    'TOR': 'tor/toronto-raptors', 'UTA': 'utah/utah-jazz',
    'WAS': 'wsh/washington-wizards'
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


class NewsType(Enum):
    INJURY = "injury"
    PLAYER_QUOTE = "player_quote"
    COACH_QUOTE = "coach_quote"
    TEAM_NEWS = "team_news"
    TRADE = "trade"
    GAME_RECAP = "game_recap"


@dataclass
class TeamNewsItem:
    """球队新闻条目"""
    news_type: str
    headline: str
    summary: str
    source: str
    date: str
    url: Optional[str] = None
    player_name: Optional[str] = None


@dataclass
class TeamStandings:
    """球队排名信息"""
    team: str
    conference: str
    rank: int
    wins: int
    losses: int
    pct: float
    games_back: float
    streak: str
    last_10: str


def get_request_headers() -> Dict:
    """Get standard request headers"""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
    }


def scrape_standings() -> Dict[str, TeamStandings]:
    """
    Scrape NBA standings from NBA Stats API.

    Returns:
        Dictionary mapping team abbreviation to standings info.
    """
    url = "https://stats.nba.com/stats/leaguestandings"
    params = {
        "LeagueID": "00",
        "Season": CURRENT_SEASON,
        "SeasonType": "Regular Season"
    }

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://www.nba.com/',
        'Origin': 'https://www.nba.com',
        'Accept': 'application/json',
        'x-nba-stats-origin': 'stats',
        'x-nba-stats-token': 'true'
    }

    try:
        print("  Fetching standings from NBA.com...", end=" ")
        time.sleep(random.uniform(1, 2))

        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()

        data = response.json()
        result_sets = data.get('resultSets', [])

        if not result_sets:
            print("no data")
            return {}

        headers_list = result_sets[0].get('headers', [])
        rows = result_sets[0].get('rowSet', [])

        print(f"{len(rows)} teams")

        standings = {}
        for row in rows:
            row_dict = dict(zip(headers_list, row))

            team_id = row_dict.get('TeamID')
            team_abbrev = None
            for abbrev, tid in ABBREV_TO_TEAM_ID.items():
                if tid == team_id and abbrev != 'BRK':
                    team_abbrev = abbrev
                    break

            if not team_abbrev:
                continue

            # Determine conference
            conference = row_dict.get('Conference', '')

            standings[team_abbrev] = TeamStandings(
                team=team_abbrev,
                conference=conference,
                rank=row_dict.get('PlayoffRank', 0),
                wins=row_dict.get('WINS', 0),
                losses=row_dict.get('LOSSES', 0),
                pct=row_dict.get('WinPCT', 0.0),
                games_back=row_dict.get('ConferenceGamesBack', 0.0),
                streak=row_dict.get('strCurrentStreak', ''),
                last_10=row_dict.get('L10', '')
            )

        return standings

    except requests.exceptions.RequestException as e:
        print(f"failed: {e}")
        return {}
    except Exception as e:
        print(f"error: {e}")
        return {}


def scrape_espn_news(team_abbrev: str, max_items: int = 5) -> List[TeamNewsItem]:
    """
    Scrape news from ESPN team page.

    Args:
        team_abbrev: Team abbreviation (e.g., 'HOU')
        max_items: Maximum number of news items to return

    Returns:
        List of TeamNewsItem objects.
    """
    espn_slug = ABBREV_TO_ESPN_SLUG.get(team_abbrev)
    if not espn_slug:
        print(f"  Warning: Unknown ESPN slug for {team_abbrev}")
        return []

    url = f"https://www.espn.com/nba/team/_/name/{espn_slug}"

    try:
        print(f"  Fetching ESPN news for {team_abbrev}...", end=" ")
        time.sleep(random.uniform(1, 2))

        response = requests.get(url, headers=get_request_headers(), timeout=30)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, 'html.parser')

        news_items = []

        # Find news articles - ESPN uses various class patterns
        # Try multiple selectors
        article_selectors = [
            'article.contentItem',
            '.contentItem__content',
            '[class*="ContentList"] article',
            '.headlineStack__list li'
        ]

        for selector in article_selectors:
            articles = soup.select(selector)
            if articles:
                break

        if not articles:
            # Fallback: look for any links with headlines
            articles = soup.select('a[class*="headline"], h2 a, .headlineStack a')

        for article in articles[:max_items]:
            try:
                # Extract headline
                headline_elem = article.select_one('h2, .contentItem__title, .headlineStack__headline')
                if not headline_elem:
                    headline_elem = article
                headline = headline_elem.get_text(strip=True)

                if not headline or len(headline) < 10:
                    continue

                # Extract link
                link_elem = article if article.name == 'a' else article.select_one('a')
                url = link_elem.get('href', '') if link_elem else ''
                if url and not url.startswith('http'):
                    url = f"https://www.espn.com{url}"

                # Determine news type from headline keywords
                news_type = NewsType.TEAM_NEWS.value
                headline_lower = headline.lower()
                if any(kw in headline_lower for kw in ['injury', 'injured', 'out', 'miss', 'return']):
                    news_type = NewsType.INJURY.value
                elif any(kw in headline_lower for kw in ['trade', 'traded', 'deal', 'acquire']):
                    news_type = NewsType.TRADE.value
                elif any(kw in headline_lower for kw in ['says', 'said', 'talks', 'speaks']):
                    news_type = NewsType.PLAYER_QUOTE.value

                news_items.append(TeamNewsItem(
                    news_type=news_type,
                    headline=headline,
                    summary="",
                    source="ESPN",
                    date=datetime.now().strftime('%Y-%m-%d'),
                    url=url
                ))

            except Exception:
                continue

        print(f"{len(news_items)} items")
        return news_items

    except requests.exceptions.RequestException as e:
        print(f"failed: {e}")
        return []
    except Exception as e:
        print(f"error: {e}")
        return []


def fetch_team_news(
    team_abbrev: str,
    max_items: int = 5,
    include_standings: bool = True
) -> Dict:
    """
    Fetch team news and standings.

    Args:
        team_abbrev: Team abbreviation (e.g., 'HOU')
        max_items: Maximum number of news items per source
        include_standings: Whether to include standings info

    Returns:
        Dictionary with news and standings data:
        {
            'standings': TeamStandings or None,
            'news': List[TeamNewsItem],
            'fetch_time': str
        }
    """
    result = {
        'standings': None,
        'news': [],
        'fetch_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Get standings
    if include_standings:
        all_standings = scrape_standings()
        if team_abbrev in all_standings:
            result['standings'] = asdict(all_standings[team_abbrev])

    # Get news from ESPN
    news_items = scrape_espn_news(team_abbrev, max_items)
    result['news'] = [asdict(item) for item in news_items]

    return result


def main():
    parser = argparse.ArgumentParser(
        description='获取 NBA 球队新闻和排名'
    )
    parser.add_argument('team', type=str, help='球队缩写 (如 HOU)')
    parser.add_argument('--max-news', type=int, default=5,
                        help='最多获取几条新闻 (默认: 5)')
    parser.add_argument('--no-standings', action='store_true',
                        help='不获取排名数据')
    parser.add_argument('--json', action='store_true',
                        help='输出 JSON 格式')

    args = parser.parse_args()

    team = args.team.upper()

    print("=" * 60)
    print(f"获取 {team} 新闻和排名")
    print("=" * 60)

    result = fetch_team_news(
        team,
        max_items=args.max_news,
        include_standings=not args.no_standings
    )

    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        # Pretty print
        print()
        if result['standings']:
            s = result['standings']
            print(f"排名: {s['conference']}区第{s['rank']}名")
            print(f"战绩: {s['wins']}-{s['losses']} ({s['pct']:.3f})")
            print(f"连胜/连败: {s['streak']}")
            print(f"近10场: {s['last_10']}")
            print()

        if result['news']:
            print("近期新闻:")
            for item in result['news']:
                type_cn = {
                    'injury': '[伤病]',
                    'player_quote': '[发言]',
                    'coach_quote': '[教练]',
                    'trade': '[交易]',
                    'team_news': '[动态]',
                    'game_recap': '[战报]'
                }.get(item['news_type'], '[新闻]')
                print(f"  {type_cn} {item['headline']}")
        else:
            print("暂无新闻")

    return 0


if __name__ == "__main__":
    sys.exit(main())
