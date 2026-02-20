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

# Team abbreviation to Chinese name mapping for Hupu
ABBREV_TO_CHINESE = {
    'ATL': '老鹰', 'BOS': '凯尔特人',
    'BKN': '篮网', 'BRK': '篮网',
    'CHA': '黄蜂', 'CHI': '公牛',
    'CLE': '骑士', 'DAL': '独行侠',
    'DEN': '掘金', 'DET': '活塞',
    'GSW': '勇士', 'HOU': '火箭',
    'IND': '步行者', 'LAC': '快船',
    'LAL': '湖人', 'MEM': '灰熊',
    'MIA': '热火', 'MIL': '雄鹿',
    'MIN': '森林狼', 'NOP': '鹈鹕',
    'NYK': '尼克斯', 'OKC': '雷霆',
    'ORL': '魔术', 'PHI': '76人',
    'PHX': '太阳', 'POR': '开拓者',
    'SAC': '国王', 'SAS': '马刺',
    'TOR': '猛龙', 'UTA': '爵士',
    'WAS': '奇才'
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

def scrape_hupu_news(team_abbrev: str, max_items: int = 5) -> List[TeamNewsItem]:
    """
    从虎扑抓取球队新闻（含正文）

    Args:
        team_abbrev: 球队缩写 (如 'HOU')
        max_items: 返回的最大新闻数量

    Returns:
        List of TeamNewsItem objects.
    """
    chinese_name = ABBREV_TO_CHINESE.get(team_abbrev)
    if not chinese_name:
        print(f"  Warning: Unknown Chinese name for {team_abbrev}")
        return []

    # Search keywords: Chinese name
    search_keywords = [chinese_name]

    print(f"  Fetching Hupu news for {team_abbrev} ({chinese_name})...")

    news_items = []

    # Loop through pages to find enough news
    # Typically check first 10 pages
    for page in range(1, 11):
        if len(news_items) >= max_items:
            break

        url = f"https://voice.hupu.com/nba/{page}"
        try:
            # Polite delay
            time.sleep(random.uniform(1, 2))

            response = requests.get(url, headers=get_request_headers(), timeout=30)
            if response.status_code != 200:
                print(f"  Failed to fetch page {page}: {response.status_code}")
                continue

            soup = BeautifulSoup(response.text, 'html.parser')

            # Hupu structure: a[class*="voice-list-content"] -> ... -> p (title)
            article_links = soup.select('a[class*="voice-list-content"]')

            if not article_links:
                # Try finding without class if hashing changed, looking for common structure
                # Fallback might be needed but for now rely on verified selector
                pass

            for link in article_links:
                if len(news_items) >= max_items:
                    break

                title_elem = link.select_one('p')
                if not title_elem:
                    continue

                title = title_elem.get_text(strip=True)

                # Filter by team name
                if not any(kw in title for kw in search_keywords):
                    continue

                # Found relevant article
                article_url = link.get('href')
                if article_url and not article_url.startswith('http'):
                    article_url = f"https://voice.hupu.com{article_url}"

                # Check for duplicates based on URL
                if any(item.url == article_url for item in news_items):
                    continue

                # Fetch article content
                try:
                    time.sleep(random.uniform(0.5, 1.5))
                    detail_resp = requests.get(article_url, headers=get_request_headers(), timeout=30)
                    detail_soup = BeautifulSoup(detail_resp.text, 'html.parser')

                    # Content is usually in div.bbs-content-font
                    content_div = detail_soup.select_one('.bbs-content-font')
                    if content_div:
                        content = content_div.get_text(separator='\n\n', strip=True)
                    else:
                        content = ""

                    # Determine news type
                    news_type = NewsType.TEAM_NEWS.value
                    title_lower = title.lower()
                    if any(kw in title_lower for kw in ['伤病', '缺席', '受伤', '手术', '报销']):
                        news_type = NewsType.INJURY.value
                    elif any(kw in title_lower for kw in ['交易', '签约', '裁掉', '续约']):
                        news_type = NewsType.TRADE.value
                    elif any(kw in title_lower for kw in ['采访', '谈到', '表示', '说']):
                        news_type = NewsType.PLAYER_QUOTE.value

                    # Try to parse date from list item if possible, otherwise use today
                    # <div class="index_voice-list-detail__..."> ... <span>source <time>time</time> ...</span>
                    date_str = datetime.now().strftime('%Y-%m-%d')

                    news_items.append(TeamNewsItem(
                        news_type=news_type,
                        headline=title,
                        summary=content, # Use content as summary
                        source="Hupu",
                        date=date_str,
                        url=article_url
                    ))
                    print(f"    Found: {title}")

                except Exception as e:
                    print(f"    Error fetching detail for {title}: {e}")
                    continue

        except Exception as e:
            print(f"  Error fetching page {page}: {e}")
            continue

    print(f"  Found {len(news_items)} items")
    return news_items

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

    # Get news from Hupu
    news_items = scrape_hupu_news(team_abbrev, max_items)
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
