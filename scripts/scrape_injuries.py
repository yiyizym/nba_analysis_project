#!/usr/bin/env python3
"""
NBA 伤病数据抓取器

从 ESPN 抓取 NBA 伤病报告并更新 configs/nba/injuries.yaml

用法:
    uv run python scripts/scrape_injuries.py          # 抓取并更新配置
    uv run python scripts/scrape_injuries.py --dry-run  # 只显示不更新
    uv run python scripts/scrape_injuries.py --show     # 显示当前配置
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import yaml

# 添加项目根目录到 path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    from src.nba_app.webscraping.di_container import DIContainer
    SELENIUM_AVAILABLE = True
except ImportError:
    SELENIUM_AVAILABLE = False

# 配置
INJURIES_FILE = Path("configs/nba/injuries.yaml")
ESPN_INJURIES_URL = "https://www.espn.com/nba/injuries"

# 球队名称到缩写的映射
TEAM_NAME_TO_ABBREV = {
    'Atlanta Hawks': 'ATL',
    'Boston Celtics': 'BOS',
    'Brooklyn Nets': 'BKN',
    'Charlotte Hornets': 'CHA',
    'Chicago Bulls': 'CHI',
    'Cleveland Cavaliers': 'CLE',
    'Dallas Mavericks': 'DAL',
    'Denver Nuggets': 'DEN',
    'Detroit Pistons': 'DET',
    'Golden State Warriors': 'GSW',
    'Houston Rockets': 'HOU',
    'Indiana Pacers': 'IND',
    'LA Clippers': 'LAC',
    'Los Angeles Clippers': 'LAC',
    'LA Lakers': 'LAL',
    'Los Angeles Lakers': 'LAL',
    'Memphis Grizzlies': 'MEM',
    'Miami Heat': 'MIA',
    'Milwaukee Bucks': 'MIL',
    'Minnesota Timberwolves': 'MIN',
    'New Orleans Pelicans': 'NOP',
    'New York Knicks': 'NYK',
    'Oklahoma City Thunder': 'OKC',
    'Orlando Magic': 'ORL',
    'Philadelphia 76ers': 'PHI',
    'Phoenix Suns': 'PHX',
    'Portland Trail Blazers': 'POR',
    'Sacramento Kings': 'SAC',
    'San Antonio Spurs': 'SAS',
    'Toronto Raptors': 'TOR',
    'Utah Jazz': 'UTA',
    'Washington Wizards': 'WAS',
}

# ESPN 状态到我们状态的映射
STATUS_MAPPING = {
    'out for season': 'out_for_season',
    'out indefinitely': 'long_term',
    'out': 'long_term',  # 需要根据描述进一步判断
    'doubtful': 'day_to_day',
    'questionable': 'day_to_day',
    'day-to-day': 'day_to_day',
    'probable': 'day_to_day',
}


def fetch_espn_injuries_selenium() -> Optional[str]:
    """使用 Selenium 从 ESPN 获取伤病页面 HTML"""
    if not SELENIUM_AVAILABLE:
        print("Selenium 不可用，请确保已安装 ml_framework 依赖")
        return None

    container = None
    try:
        container = DIContainer()
        app_logger = container.app_logger()
        app_logger.setup("injury_scraper.log")

        driver_factory = container.web_driver_factory()
        driver = driver_factory.create_driver()

        print(f"  正在访问 {ESPN_INJURIES_URL}...")
        driver.get(ESPN_INJURIES_URL)
        time.sleep(3)  # 等待页面加载

        # 滚动页面以加载所有内容
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)

        html = driver.page_source
        return html

    except Exception as e:
        print(f"Selenium 获取失败: {e}")
        return None

    finally:
        if container:
            try:
                container.web_driver_factory().close_driver()
            except:
                pass


def fetch_espn_injuries() -> Optional[str]:
    """从 ESPN 获取伤病页面 HTML（优先使用 Selenium）"""
    # 优先使用 Selenium（ESPN 需要 JavaScript 渲染）
    if SELENIUM_AVAILABLE:
        return fetch_espn_injuries_selenium()

    # 备用方案：直接请求（可能不完整）
    try:
        import requests
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(ESPN_INJURIES_URL, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"获取 ESPN 伤病数据失败: {e}")
        return None


def parse_espn_injuries(html: str) -> Dict[str, List[Dict]]:
    """
    解析 ESPN 伤病页面

    Returns:
        按球队缩写分组的伤病字典
    """
    if not BS4_AVAILABLE:
        print("BeautifulSoup 不可用，请安装: uv add beautifulsoup4")
        return {}

    soup = BeautifulSoup(html, 'html.parser')
    injuries = {}

    # ESPN 2024+ 页面结构：每个球队是一个带有球队名的区块
    # 查找所有包含球队名称的标题
    team_headers = soup.find_all(['h2', 'h3', 'div'], class_=re.compile(r'headline|TeamHeader|teamName', re.I))

    # 备用方案：查找所有表格
    tables = soup.find_all('table')

    current_team = None

    # 方法1：通过球队标题和后续表格
    for header in team_headers:
        header_text = header.get_text(strip=True)

        # 检查是否是球队名称
        for team_name, abbrev in TEAM_NAME_TO_ABBREV.items():
            if team_name.lower() in header_text.lower():
                current_team = abbrev

                # 查找该标题后的表格
                next_table = header.find_next('table')
                if next_table:
                    injuries[current_team] = parse_injury_table(next_table, current_team)
                break

    # 方法2：如果方法1没找到，尝试直接解析所有表格
    if not injuries:
        for table in tables:
            # 尝试在表格前找到球队名
            prev_elem = table.find_previous(['h2', 'h3', 'div', 'span'])
            if prev_elem:
                prev_text = prev_elem.get_text(strip=True)
                for team_name, abbrev in TEAM_NAME_TO_ABBREV.items():
                    if team_name.lower() in prev_text.lower():
                        current_team = abbrev
                        injuries[current_team] = parse_injury_table(table, current_team)
                        break

    # 方法3：通过页面文本模式匹配
    if not injuries:
        injuries = parse_injuries_from_text(soup.get_text())

    return injuries


def parse_injury_table(table, team: str) -> List[Dict]:
    """解析单个伤病表格"""
    players = []
    rows = table.find_all('tr')

    for row in rows:
        cells = row.find_all(['td', 'th'])
        if len(cells) >= 2:
            # 获取文本
            texts = [cell.get_text(strip=True) for cell in cells]

            # 跳过表头
            if any(h in texts[0].lower() for h in ['name', 'player', 'pos', 'position', '']):
                continue

            player_name = texts[0]
            if not player_name or len(player_name) < 2:
                continue

            # 获取状态和描述
            status_text = ''
            injury_desc = ''

            for i, text in enumerate(texts[1:], 1):
                text_lower = text.lower()
                if any(s in text_lower for s in ['out', 'day', 'doubtful', 'questionable', 'probable']):
                    status_text = text_lower
                elif len(text) > 5:  # 可能是伤病描述
                    injury_desc = text

            # 确定状态
            status = determine_status(status_text, injury_desc)

            players.append({
                'name': player_name,
                'status': status,
                'note': (injury_desc[:80] if injury_desc else status_text)[:80],
            })

    return players


def determine_status(status_text: str, injury_desc: str) -> str:
    """根据状态文本和伤病描述确定状态类型"""
    combined = (status_text + ' ' + injury_desc).lower()

    # 赛季报销
    if any(phrase in combined for phrase in ['out for season', 'season-ending', 'out indefinitely']):
        return 'out_for_season'

    # 长期伤病（手术、ACL、跟腱等严重伤病）
    if any(phrase in combined for phrase in ['surgery', 'acl', 'achilles', 'torn', 'fracture']):
        if 'out' in combined:
            return 'out_for_season'
        return 'long_term'

    # 按状态文本判断
    for key, value in STATUS_MAPPING.items():
        if key in status_text:
            return value

    return 'day_to_day'


def parse_injuries_from_text(text: str) -> Dict[str, List[Dict]]:
    """从纯文本中提取伤病信息（备用方案）"""
    injuries = {}

    # 尝试匹配 "球员名 (球队) - 状态 - 描述" 模式
    # 这是一个简单的备用方案

    lines = text.split('\n')
    current_team = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 检查是否是球队名
        for team_name, abbrev in TEAM_NAME_TO_ABBREV.items():
            if team_name in line and len(line) < 50:
                current_team = abbrev
                if current_team not in injuries:
                    injuries[current_team] = []
                break

    return injuries


def parse_injuries_simple(html: str) -> Dict[str, List[Dict]]:
    """
    简单解析方式 - 直接提取文本中的伤病信息

    由于 ESPN 页面结构复杂，使用备用解析方式
    """
    injuries = {}
    soup = BeautifulSoup(html, 'html.parser')

    # 获取所有文本
    text = soup.get_text()

    # 查找球队和球员模式
    for team_name, abbrev in TEAM_NAME_TO_ABBREV.items():
        # 在文本中查找球队相关内容
        if team_name in text:
            injuries[abbrev] = []

    return injuries


def load_current_injuries() -> Dict:
    """加载当前的伤病配置"""
    if not INJURIES_FILE.exists():
        return {'season': '2025-26', 'injuries': {}}

    with open(INJURIES_FILE, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f) or {'season': '2025-26', 'injuries': {}}


def save_injuries(config: Dict):
    """保存伤病配置"""
    INJURIES_FILE.parent.mkdir(parents=True, exist_ok=True)

    # 构建 YAML 内容（手动格式化以保持注释）
    lines = [
        "# NBA 伤病名单配置",
        "# 赛季报销或长期缺阵的球员会自动从对阵分析中排除",
        f"# 更新时间: {datetime.now().strftime('%Y-%m-%d')}",
        "# 数据来源: ESPN NBA Injuries",
        "",
        "# 格式说明:",
        "#   - 按球队缩写分组",
        "#   - 每个球员包含: 名字、状态、预计复出时间（可选）",
        '#   - status: "out_for_season" (赛季报销) | "long_term" (长期缺阵) | "day_to_day" (出战成疑)',
        "",
        f'season: "{config.get("season", "2025-26")}"',
        "",
        "injuries:",
    ]

    injuries = config.get('injuries', {})

    # 按球队缩写排序
    for team in sorted(injuries.keys()):
        players = injuries[team]
        if not players:
            continue

        lines.append(f"  # {team}")
        lines.append(f"  {team}:")

        for player in players:
            lines.append(f'    - name: "{player["name"]}"')
            lines.append(f'      status: "{player["status"]}"')
            if player.get('note'):
                lines.append(f'      note: "{player["note"]}"')
        lines.append("")

    lines.extend([
        "# 自动排除规则:",
        "# - out_for_season: 总是排除",
        "# - long_term: 总是排除",
        "# - day_to_day: 不自动排除，需要手动用 --out 指定",
        "",
    ])

    with open(INJURIES_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def merge_injuries(current: Dict[str, List], fetched: Dict[str, List]) -> Dict[str, List]:
    """
    合并当前配置和新抓取的伤病数据

    策略:
    - 保留当前的 out_for_season 和 long_term 球员
    - 更新 day_to_day 球员
    - 添加新发现的伤病球员
    """
    merged = {}

    # 首先添加所有当前的长期伤病
    for team, players in current.items():
        if team not in merged:
            merged[team] = []
        for player in players:
            if player['status'] in ['out_for_season', 'long_term']:
                merged[team].append(player)

    # 然后添加/更新新抓取的数据
    for team, players in fetched.items():
        if team not in merged:
            merged[team] = []

        existing_names = {p['name'].lower() for p in merged.get(team, [])}

        for player in players:
            if player['name'].lower() not in existing_names:
                merged[team].append(player)

    # 清理空球队
    merged = {k: v for k, v in merged.items() if v}

    return merged


def display_injuries(injuries: Dict[str, List], title: str = "伤病列表"):
    """显示伤病列表"""
    print(f"\n{'=' * 60}")
    print(f"{title}")
    print('=' * 60)

    status_icons = {
        'out_for_season': '🔴',
        'long_term': '🟠',
        'day_to_day': '🟡',
    }

    total = 0
    for team in sorted(injuries.keys()):
        players = injuries[team]
        if not players:
            continue

        print(f"\n{team}:")
        for p in players:
            icon = status_icons.get(p['status'], '⚪')
            note = f" - {p['note']}" if p.get('note') else ""
            print(f"  {icon} {p['name']} ({p['status']}){note}")
            total += 1

    print(f"\n总计: {total} 名球员")
    print('=' * 60)


def add_injury(team: str, player: str, status: str, note: str = ""):
    """添加伤病球员到配置"""
    if team not in TEAM_NAME_TO_ABBREV.values():
        print(f"无效的球队缩写: {team}")
        print(f"有效的缩写: {', '.join(sorted(TEAM_NAME_TO_ABBREV.values()))}")
        return False

    if status not in ['out_for_season', 'long_term', 'day_to_day']:
        print(f"无效的状态: {status}")
        print("有效的状态: out_for_season, long_term, day_to_day")
        return False

    config = load_current_injuries()
    injuries = config.get('injuries', {})

    if team not in injuries:
        injuries[team] = []

    # 检查是否已存在
    for p in injuries[team]:
        if p['name'].lower() == player.lower():
            print(f"球员 {player} 已在 {team} 的伤病名单中，正在更新...")
            p['status'] = status
            p['note'] = note
            break
    else:
        injuries[team].append({
            'name': player,
            'status': status,
            'note': note,
        })

    config['injuries'] = injuries
    save_injuries(config)
    print(f"✅ 已添加: {player} ({team}) - {status}")
    return True


def remove_injury(team: str, player: str):
    """从配置中移除伤病球员"""
    config = load_current_injuries()
    injuries = config.get('injuries', {})

    if team not in injuries:
        print(f"球队 {team} 没有伤病记录")
        return False

    original_count = len(injuries[team])
    injuries[team] = [p for p in injuries[team] if p['name'].lower() != player.lower()]

    if len(injuries[team]) == original_count:
        print(f"未找到球员: {player}")
        return False

    # 清理空球队
    if not injuries[team]:
        del injuries[team]

    config['injuries'] = injuries
    save_injuries(config)
    print(f"✅ 已移除: {player} ({team})")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='管理 NBA 伤病配置',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 查看当前伤病配置
    uv run python scripts/scrape_injuries.py --show

    # 添加伤病球员
    uv run python scripts/scrape_injuries.py --add HOU "Jabari Smith Jr." long_term "膝盖伤势"

    # 移除球员
    uv run python scripts/scrape_injuries.py --remove HOU "Kevin Durant"

    # 尝试从 ESPN 抓取（可能不稳定）
    uv run python scripts/scrape_injuries.py --fetch

数据来源:
    手动查阅 ESPN 伤病报告: https://www.espn.com/nba/injuries
        """
    )
    parser.add_argument('--show', action='store_true',
                        help='显示当前伤病配置')
    parser.add_argument('--add', nargs=4, metavar=('TEAM', 'PLAYER', 'STATUS', 'NOTE'),
                        help='添加伤病球员: --add HOU "Player Name" out_for_season "伤病描述"')
    parser.add_argument('--remove', nargs=2, metavar=('TEAM', 'PLAYER'),
                        help='移除伤病球员: --remove HOU "Player Name"')
    parser.add_argument('--fetch', action='store_true',
                        help='尝试从 ESPN 抓取伤病数据（可能不稳定）')
    parser.add_argument('--dry-run', action='store_true',
                        help='只显示抓取结果，不更新配置文件')
    parser.add_argument('--force', action='store_true',
                        help='强制覆盖现有配置（而不是合并）')

    args = parser.parse_args()

    # 显示当前配置
    if args.show:
        current = load_current_injuries()
        display_injuries(current.get('injuries', {}), "当前伤病配置")
        return 0

    # 添加伤病球员
    if args.add:
        team, player, status, note = args.add
        return 0 if add_injury(team.upper(), player, status, note) else 1

    # 移除伤病球员
    if args.remove:
        team, player = args.remove
        return 0 if remove_injury(team.upper(), player) else 1

    # 抓取 ESPN 数据
    if args.fetch:
        print("正在从 ESPN 获取伤病数据...")
        html = fetch_espn_injuries()

        if not html:
            print("获取失败，请检查网络连接")
            return 1

        print("正在解析伤病数据...")
        fetched = parse_espn_injuries(html)

        if not fetched:
            print("未能解析到伤病数据，可能 ESPN 页面结构已更改")
            print("\n提示: 请手动访问 https://www.espn.com/nba/injuries 查看伤病信息")
            print("然后使用 --add 命令手动添加:")
            print('  uv run python scripts/scrape_injuries.py --add HOU "Player Name" out_for_season "伤病描述"')
            return 1

        display_injuries(fetched, "ESPN 伤病报告")

        if args.dry_run:
            print("\n[--dry-run 模式] 未更新配置文件")
            return 0

        # 加载当前配置并合并
        current = load_current_injuries()

        if args.force:
            merged = fetched
            print("\n[--force 模式] 将覆盖现有配置")
        else:
            merged = merge_injuries(current.get('injuries', {}), fetched)
            print("\n已合并现有配置和新数据")

        # 保存
        new_config = {
            'season': current.get('season', '2025-26'),
            'injuries': merged,
        }
        save_injuries(new_config)

        print(f"✅ 已更新配置文件: {INJURIES_FILE}")
        display_injuries(merged, "更新后的伤病配置")
        return 0

    # 默认显示帮助
    parser.print_help()
    print("\n快速开始:")
    print("  uv run python scripts/scrape_injuries.py --show")
    return 0


if __name__ == "__main__":
    exit(main())
