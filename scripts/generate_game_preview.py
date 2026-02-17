#!/usr/bin/env python3
"""
NBA 比赛前瞻 Prompt 生成器

生成用于 Claude 写作的完整 prompt 文件。

用法:
    python scripts/generate_game_preview.py HOU LAL
    python scripts/generate_game_preview.py HOU LAL --out "LeBron James" --live
    python scripts/generate_game_preview.py HOU LAL --date 2026-02-03 --tz beijing

工作流程:
    1. 运行此脚本生成 prompt 文件
    2. 复制 prompt 内容到 Claude 对话
    3. Claude 生成文章
    4. 保存文章到 data/articles/
"""

import sys
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

# Add scripts directory to path for importing analyze_matchup
sys.path.insert(0, str(Path(__file__).parent))

from analyze_matchup import (
    run_analysis,
    ABBREV_TO_FULL,
    convert_to_us_eastern,
    load_injuries
)

# Configuration
PROMPTS_DIR = Path("data/prompts")
ARTICLES_DIR = Path("data/articles")
SYSTEM_PROMPT_FILE = Path("data/prompts/system_prompt.md")


def load_system_prompt() -> str:
    """
    加载 system_prompt.md 内容。

    Returns:
        system_prompt 内容，如果文件不存在则返回空字符串
    """
    if SYSTEM_PROMPT_FILE.exists():
        with open(SYSTEM_PROMPT_FILE, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return ""


def build_prompt(team_a: str, team_b: str, analysis: Dict,
                 game_date: Optional[datetime] = None,
                 out_players: List[str] = None,
                 fan_team: Optional[str] = None) -> str:
    """
    构建完整的 Claude prompt。

    Args:
        team_a: 球队 A 缩写
        team_b: 球队 B 缩写
        analysis: run_analysis() 返回的分析结果
        game_date: 比赛日期
        out_players: 缺阵球员列表
        fan_team: 主队视角 (如 "HOU")，None 表示中立视角

    Returns:
        完整的 prompt 字符串
    """
    team_a_full = ABBREV_TO_FULL.get(team_a, team_a)
    team_b_full = ABBREV_TO_FULL.get(team_b, team_b)
    out_players = out_players or []

    # 格式化日期
    date_str = game_date.strftime('%Y年%m月%d日') if game_date else datetime.now().strftime('%Y年%m月%d日')

    # 提取各维度数据
    ff = analysis.get('four_factors', {})
    style = analysis.get('style_geometry', {})
    matchups = analysis.get('key_matchups', {})
    context = analysis.get('context_form', {})
    win_conditions = analysis.get('win_conditions', {})
    danger_zones = analysis.get('danger_zones', {})

    # 格式化四要素对比
    ff_text = format_four_factors(ff, team_a, team_b)

    # 格式化风格分析
    style_text = format_style_analysis(style, team_a, team_b)

    # 格式化关键对位
    matchups_text = format_key_matchups(matchups, team_a, team_b)

    # 格式化状态趋势
    context_text = format_context_form(context, team_a, team_b)

    # 格式化胜利条件
    win_text = format_win_conditions(win_conditions, team_a, team_b)

    # 格式化危险信号
    danger_text = format_danger_zones(danger_zones, team_a, team_b)

    # 格式化历史交手
    h2h = analysis.get('head_to_head')
    h2h_text = format_head_to_head(h2h, team_a, team_b)

    # 格式化新闻和排名
    news_data = analysis.get('team_news')
    news_text = format_team_news(news_data, team_a, team_b)

    # 缺阵球员
    out_text = ""
    if out_players:
        out_text = f"\n**已知缺阵球员**: {', '.join(out_players)}\n"

    # 主队视角说明
    if fan_team:
        fan_team_full = ABBREV_TO_FULL.get(fan_team, fan_team)
        perspective_text = f"""
## 写作视角

本文的目标读者是**{fan_team_full}球迷**。请以{fan_team_full}的视角撰写文章：
- 更多关注{fan_team_full}的表现、战术和球员
- 分析对手时，着重分析{fan_team_full}如何应对
- 胜负预测时，侧重分析{fan_team_full}的获胜条件
- 但仍需保持专业客观，不要盲目乐观或贬低对手

---
"""
    else:
        perspective_text = ""

    prompt = f"""请根据以下数据撰写一篇中文赛前预览文章。请用【专业新闻风】或【直白分析风】写作，不要比喻，直接分析数据。
{perspective_text}

---

## 比赛信息

- **对阵**: {team_a_full} vs {team_b_full}
- **日期**: {date_str}
{out_text}
---

## 历史交手

{h2h_text}

---

## 数据分析

### 1. 四要素对比 (Four Factors)

{ff_text}

### 2. 风格碰撞 (Style & Geometry)

{style_text}

### 3. 关键对位 (Key Matchups)

{matchups_text}

### 4. 状态与趋势 (Context & Form)

{context_text}

---

## 胜负关键

### {team_a} 获胜需要:
{win_text[team_a]}

### {team_b} 获胜需要:
{win_text[team_b]}

---

## 危险信号

### {team_a} 需警惕:
{danger_text[team_a]}

### {team_b} 需警惕:
{danger_text[team_b]}

---

## 新闻动态

{news_text}

---

## 写作要求

请按以下结构撰写文章:

1. **标题**: 吸引眼球，点明比赛核心看点（15字以内）
2. **导语**: 一段话概括比赛核心看点（50-80字）
3. **四要素分析**: 解读篮板/失误/罚球/投篮四个维度的对比，指出关键差距
4. **风格碰撞**: 分析双方打法是否相克，节奏控制权归属
5. **关键对位**: 指出最关键的1-2组球员对位，分析攻防匹配
6. **近期状态**: 分析双方近期表现趋势，谁更火热
7. **伤病影响**: 如有缺阵球员，分析其对比赛的影响
8. **胜负预测**: 给出你的预测和理由，预测分差范围

## 风格要求

- 语言专业但不晦涩，让普通球迷也能看懂
- 数据支撑观点，但不要堆砌数字，选取最关键的2-3个数据点
- 直接分析数据，不要使用比喻和类比
- 总字数控制在 **800-1200字**
- 使用 Markdown 格式，方便发布
- 请不要用小标题，直接用段落分隔内容
- 球员名字只使用姓氏（如 "Durant" 而不是 "Kevin Durant"，"VanVleet" 而不是 "Fred VanVleet"）

---

请直接输出文章内容:
"""

    return prompt


def format_four_factors(ff: Dict, team_a: str, team_b: str) -> str:
    """格式化四要素数据"""
    if 'error' in ff:
        return f"数据加载失败: {ff['error']}"

    lines = []
    lines.append(f"| 指标 | {team_a} | {team_b} | 优势方 |")
    lines.append("|------|--------|--------|--------|")

    for clash in ff.get('clashes', []):
        adv = clash['advantage']
        adv_marker = f"**{adv}**" if adv != 'EVEN' else "持平"
        lines.append(f"| {clash['metric_cn']} | {clash['team_a_desc']} | {clash['team_b_desc']} | {adv_marker} |")

    lines.append("")
    lines.append(f"**维度胜者**: {ff['dimension_winner']} ({ff['team_a_wins']}-{ff['team_b_wins']})")

    return "\n".join(lines)


def format_style_analysis(style: Dict, team_a: str, team_b: str) -> str:
    """格式化风格分析"""
    if 'error' in style:
        return f"数据加载失败: {style['error']}"

    lines = []

    # 节奏
    pace = style.get('pace', {})
    if pace:
        lines.append(f"**节奏对比**: {pace.get('insight', 'N/A')}")
        lines.append("")

    # 禁区防守
    rim = style.get('rim', {})
    if rim:
        lines.append(f"**禁区防守**: {rim.get('insight', 'N/A')}")
        lines.append("")

    # 攻防效率
    ratings = style.get('ratings', {})
    if ratings:
        a_rat = ratings.get('team_a', {})
        b_rat = ratings.get('team_b', {})
        lines.append("**攻防效率**:")
        lines.append(f"- {team_a}: 进攻 {a_rat.get('OffRtg', 0):.1f} | 防守 {a_rat.get('DefRtg', 0):.1f} | 净效率 {a_rat.get('NetRtg', 0):+.1f}")
        lines.append(f"- {team_b}: 进攻 {b_rat.get('OffRtg', 0):.1f} | 防守 {b_rat.get('DefRtg', 0):.1f} | 净效率 {b_rat.get('NetRtg', 0):+.1f}")
        lines.append("")

    # PlayType
    playtypes = style.get('playtypes', [])
    if playtypes:
        lines.append("**关键战术效率**:")
        for pt in playtypes[:5]:
            rating_cn = {'elite': '顶级', 'good': '良好', 'poor': '较弱'}.get(pt['rating'], '')
            lines.append(f"- {pt['team']} {pt['type']}: {pt['ppp']:.2f} PPP (联盟第{pt['percentile']:.0f}百分位) {rating_cn}")

    return "\n".join(lines)


def format_key_matchups(matchups: Dict, team_a: str, team_b: str) -> str:
    """格式化关键对位"""
    if 'error' in matchups:
        return f"数据加载失败: {matchups['error']}"

    lines = []

    # 缺阵球员
    out_players = matchups.get('out_players', [])
    if out_players:
        out_list = ", ".join([f"{p['player']} ({p['team']}, {p['archetype']})" for p in out_players])
        lines.append(f"**缺阵球员**: {out_list}")
        lines.append("")

    # 核心得分手
    lines.append(f"**{team_a} 核心得分手**:")
    for s in matchups.get('team_a_scorers', []):
        lines.append(f"- {s['player']} [{s['archetype']}] - {s['pts']:.1f} PPG, {s['usg']:.1f}% 使用率")

    lines.append("")
    lines.append(f"**{team_b} 核心得分手**:")
    for s in matchups.get('team_b_scorers', []):
        lines.append(f"- {s['player']} [{s['archetype']}] - {s['pts']:.1f} PPG, {s['usg']:.1f}% 使用率")

    lines.append("")

    # 防守资源
    a_defenders = matchups.get('team_a_defenders', [])
    b_defenders = matchups.get('team_b_defenders', [])

    if a_defenders or b_defenders:
        lines.append("**防守资源**:")
        if a_defenders:
            def_list = ", ".join([f"{d['player']} ({d['archetype']})" for d in a_defenders])
            lines.append(f"- {team_a}: {def_list}")
        if b_defenders:
            def_list = ", ".join([f"{d['player']} ({d['archetype']})" for d in b_defenders])
            lines.append(f"- {team_b}: {def_list}")

    # 缺阵影响
    out_impact = matchups.get('out_impact', [])
    if out_impact:
        lines.append("")
        lines.append("**缺阵影响分析**:")
        for impact in out_impact:
            lines.append(f"- {impact}")

    return "\n".join(lines)


def format_context_form(context: Dict, team_a: str, team_b: str) -> str:
    """格式化状态趋势"""
    lines = []
    trend_cn = {'improving': '上升趋势', 'declining': '下滑趋势', 'stable': '保持稳定', 'insufficient_data': '数据不足'}

    # 最近10场（如果有）
    last_10 = context.get('last_10_games')
    if last_10:
        lines.append("**最近10场表现** (实时数据):")
        for team in [team_a, team_b]:
            if team in last_10:
                d = last_10[team]
                w, l = d.get('W', 0), d.get('L', 0)
                netrtg = d.get('NetRtg', 0)
                efg = d.get('eFG%', 0)
                lines.append(f"- {team}: {w}胜{l}负 | 净效率 {netrtg:+.1f} | eFG% {efg:.1f}%")

        # 对比
        if team_a in last_10 and team_b in last_10:
            a_net = last_10[team_a].get('NetRtg', 0)
            b_net = last_10[team_b].get('NetRtg', 0)
            if a_net > b_net + 3:
                lines.append(f"\n**{team_a} 近期状态明显更佳**")
            elif b_net > a_net + 3:
                lines.append(f"\n**{team_b} 近期状态明显更佳**")
            else:
                lines.append("\n**双方近期状态接近**")
        lines.append("")

    # 月度趋势
    lines.append("**月度趋势**:")
    a_monthly = context.get('team_a_monthly', [])
    if a_monthly:
        a_trend_str = " → ".join([f"{m['month'][:3].capitalize()}({m['NetRtg']:+.1f})" for m in a_monthly])
        lines.append(f"- {team_a}: {a_trend_str}")
        lines.append(f"  趋势: {trend_cn.get(context.get('team_a_trend', ''), '未知')}")

    b_monthly = context.get('team_b_monthly', [])
    if b_monthly:
        b_trend_str = " → ".join([f"{m['month'][:3].capitalize()}({m['NetRtg']:+.1f})" for m in b_monthly])
        lines.append(f"- {team_b}: {b_trend_str}")
        lines.append(f"  趋势: {trend_cn.get(context.get('team_b_trend', ''), '未知')}")

    return "\n".join(lines)


def format_win_conditions(win_conditions: Dict, team_a: str, team_b: str) -> Dict[str, str]:
    """格式化胜利条件"""
    result = {}

    for team in [team_a, team_b]:
        conditions = win_conditions.get(team, [])
        if conditions:
            lines = []
            for i, c in enumerate(conditions, 1):
                priority = c.get('priority', 'MED')
                priority_marker = "🔴" if priority == 'HIGH' else "🟡"
                lines.append(f"{i}. {priority_marker} {c['condition']}")
            result[team] = "\n".join(lines)
        else:
            result[team] = "暂无数据"

    return result


def format_danger_zones(danger_zones: Dict, team_a: str, team_b: str) -> Dict[str, str]:
    """格式化危险信号"""
    result = {}

    for team in [team_a, team_b]:
        dangers = danger_zones.get(team, [])
        if dangers:
            lines = []
            for d in dangers:
                severity = d.get('severity', 'WARNING')
                severity_marker = "⚠️" if severity == 'CRITICAL' else "⚡"
                lines.append(f"- {severity_marker} {d['danger']}")
            result[team] = "\n".join(lines)
        else:
            result[team] = "暂无明显风险"

    return result


def format_head_to_head(h2h: Optional[Dict], team_a: str, team_b: str) -> str:
    """格式化历史交手记录"""
    if not h2h:
        return "本赛季两队尚未交手"

    lines = []
    lines.append(f"**上次交手**: {h2h.get('game_date', 'N/A')}")

    home_team = h2h.get('home_team', '')
    away_team = h2h.get('away_team', '')
    home_score = h2h.get('home_score', 0)
    away_score = h2h.get('away_score', 0)
    winner = h2h.get('winner', '')

    # 主客场
    if home_team and away_team:
        lines.append(f"- 主场: {home_team} | 客场: {away_team}")

    # 比分
    if home_score and away_score:
        lines.append(f"- 比分: {home_team} {home_score} - {away_score} {away_team}")

    # 胜者
    if winner:
        lines.append(f"- 胜者: **{winner}**")

    # 赛季战绩
    season_series = h2h.get('season_series', '')
    if season_series:
        lines.append(f"- 赛季交手: {team_a} {season_series} {team_b}")

    return "\n".join(lines)


def format_team_news(news_data: Optional[Dict], team_a: str, team_b: str) -> str:
    """格式化球队新闻和排名"""
    if not news_data:
        return ""

    lines = []

    for team in [team_a, team_b]:
        if team not in news_data:
            continue

        team_data = news_data[team]
        lines.append(f"\n### {team} 近期动态\n")

        # 排名
        standings = team_data.get('standings')
        if standings:
            conf = standings.get('conference', '')
            rank = standings.get('rank', 0)
            wins = standings.get('wins', 0)
            losses = standings.get('losses', 0)
            streak = standings.get('streak', '')
            last_10 = standings.get('last_10', '')

            lines.append(f"**当前排名**: {conf}区第{rank}名")
            lines.append(f"- 战绩: {wins}-{losses}")
            if streak:
                lines.append(f"- 连胜/连败: {streak}")
            if last_10:
                lines.append(f"- 近10场: {last_10}")
            lines.append("")

        # 新闻
        news_items = team_data.get('news', [])
        if news_items:
            lines.append("**近期新闻**:")
            for item in news_items[:3]:
                type_cn = {
                    'injury': '[伤病]',
                    'player_quote': '[发言]',
                    'coach_quote': '[教练]',
                    'trade': '[交易]',
                    'team_news': '[动态]',
                    'game_recap': '[战报]'
                }.get(item.get('news_type', ''), '[新闻]')
                lines.append(f"- {type_cn} {item.get('headline', '')}")
            lines.append("")

    return "\n".join(lines) if lines else ""


def save_prompt(content: str, team_a: str, team_b: str,
                game_date: Optional[datetime] = None,
                include_system_prompt: bool = True) -> Path:
    """
    保存 prompt 到文件。

    Args:
        content: prompt 内容
        team_a: 球队 A 缩写
        team_b: 球队 B 缩写
        game_date: 比赛日期
        include_system_prompt: 是否在开头添加 system_prompt.md 内容

    Returns:
        保存的文件路径
    """
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)

    date_str = (game_date or datetime.now()).strftime('%Y-%m-%d')
    filename = f"{date_str}_{team_a}_vs_{team_b}_prompt.md"
    filepath = PROMPTS_DIR / filename

    # 合并 system_prompt 和数据 prompt
    final_content = content
    if include_system_prompt:
        system_prompt = load_system_prompt()
        if system_prompt:
            final_content = f"{system_prompt}\n\n---\n\n{content}"

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(final_content)

    return filepath


def main():
    parser = argparse.ArgumentParser(
        description='生成 NBA 比赛前瞻 Prompt',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python scripts/generate_game_preview.py HOU IND
    python scripts/generate_game_preview.py HOU IND --out "Kevin Durant" --live
    python scripts/generate_game_preview.py HOU IND --date 2026-02-03 --tz beijing

生成后:
    1. 打开 data/prompts/ 目录中的 prompt 文件
    2. 复制内容到 Claude 对话
    3. Claude 将根据数据生成文章
        """
    )
    parser.add_argument('team_a', type=str, help='球队 A 缩写 (如 HOU)')
    parser.add_argument('team_b', type=str, help='球队 B 缩写 (如 IND)')
    parser.add_argument('--month', type=str, default='january',
                        choices=['october', 'november', 'december', 'january'],
                        help='分析数据月份 (默认: january)')
    parser.add_argument('--out', type=str, action='append', default=[],
                        help='缺阵球员 (可多次指定或逗号分隔)')
    parser.add_argument('--live', action='store_true',
                        help='抓取实时 Last 10 Games 数据')
    parser.add_argument('--date', type=str, default=None,
                        help='比赛日期 (YYYY-MM-DD)')
    parser.add_argument('--timezone', '--tz', type=str, default=None,
                        help='您的时区，用于转换为美东时间 (如 "beijing", "+8")')
    parser.add_argument('--print', action='store_true',
                        help='同时打印 prompt 到终端')
    parser.add_argument('--no-system-prompt', action='store_true',
                        help='不添加 system_prompt.md 内容')
    parser.add_argument('--h2h', action='store_true',
                        help='获取历史交手数据')
    parser.add_argument('--news', action='store_true',
                        help='获取球队最新新闻和排名')
    parser.add_argument('--full', action='store_true',
                        help='获取所有数据 (等同于 --live --h2h --news)')
    parser.add_argument('--fan', type=str, default='HOU',
                        help='主队视角，写作面向该队球迷 (如 HOU)，设为 "neutral" 表示中立视角')

    args = parser.parse_args()

    # 处理 --full 参数
    if args.full:
        args.live = True
        args.h2h = True
        args.news = True

    # 标准化球队缩写
    team_a = args.team_a.upper()
    team_b = args.team_b.upper()

    # 解析命令行缺阵球员
    manual_out_players = []
    for out_arg in args.out:
        manual_out_players.extend([p.strip() for p in out_arg.split(',')])

    # 从配置文件加载伤病
    config_out_players = load_injuries(team_a, team_b)

    # 合并并去重（不区分大小写）
    seen = set()
    out_players = []
    for p in config_out_players + manual_out_players:
        if p.lower() not in seen:
            seen.add(p.lower())
            out_players.append(p)

    # 解析比赛日期
    game_date = None
    if args.date:
        try:
            game_date = datetime.strptime(args.date, '%Y-%m-%d')
            if args.timezone:
                game_date = convert_to_us_eastern(game_date, args.timezone)
        except ValueError:
            print(f"警告: 日期格式无效 '{args.date}'，应为 YYYY-MM-DD")

    print("=" * 60)
    print("NBA 比赛前瞻 Prompt 生成器")
    print("=" * 60)
    print(f"对阵: {team_a} vs {team_b}")
    print(f"数据月份: {args.month}")
    if config_out_players:
        print(f"自动加载伤病: {', '.join(config_out_players)}")
    if manual_out_players:
        print(f"手动指定 --out: {', '.join(manual_out_players)}")
    if out_players:
        print(f"全部缺阵球员: {', '.join(out_players)}")
    if args.live:
        print("实时数据: 已启用")
    if args.h2h:
        print("历史交手: 已启用")
    if args.news:
        print("新闻排名: 已启用")
    if game_date:
        print(f"比赛日期: {game_date.strftime('%Y-%m-%d')}")
    if args.fan and args.fan.lower() != 'neutral':
        print(f"主队视角: {args.fan.upper()} 球迷")
    else:
        print("主队视角: 中立")
    print()

    # 步骤 1: 运行对阵分析
    print("[1/3] 运行对阵分析...")
    analysis = run_analysis(
        team_a, team_b, args.month, out_players,
        fetch_live=args.live, game_date=game_date,
        fetch_h2h=args.h2h, fetch_news=args.news
    )

    if 'error' in analysis:
        print(f"错误: {analysis['error']}")
        return 1

    print("      分析完成")

    # 处理主队视角
    fan_team = args.fan.upper() if args.fan and args.fan.lower() != 'neutral' else None

    # 步骤 2: 构建 prompt
    print("[2/3] 构建 Prompt...")
    prompt = build_prompt(team_a, team_b, analysis, game_date, out_players, fan_team)
    print("      Prompt 构建完成")

    # 步骤 3: 保存文件
    print("[3/3] 保存文件...")
    include_sys_prompt = not getattr(args, 'no_system_prompt', False)
    filepath = save_prompt(prompt, team_a, team_b, game_date,
                          include_system_prompt=include_sys_prompt)
    print(f"      已保存到: {filepath}")
    if include_sys_prompt:
        print("      (已包含 system_prompt.md)")

    # 可选: 打印到终端
    if getattr(args, 'print', False):
        print()
        print("=" * 60)
        print("Prompt 内容:")
        print("=" * 60)
        print(prompt)

    print()
    print("=" * 60)
    print("下一步:")
    print("=" * 60)
    print(f"1. 打开文件: {filepath}")
    print("2. 复制全部内容到 Claude 对话")
    print("3. Claude 将生成文章")
    print("4. 保存文章到 data/articles/")
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
