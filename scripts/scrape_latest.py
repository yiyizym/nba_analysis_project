#!/usr/bin/env python3
"""
一键抓取最新 NBA 数据

用途：抓取最近一个月或整个赛季的所有数据（球队、球员、教练）

使用方法：
    # 抓取当前月份数据（默认）
    python scripts/scrape_latest.py

    # 抓取整个赛季数据
    python scripts/scrape_latest.py --season

    # 指定赛季和月份
    python scripts/scrape_latest.py --year 2025-26 --month january

    # 只抓取球队数据
    python scripts/scrape_latest.py --team-only

    # 只抓取球员数据
    python scripts/scrape_latest.py --player-only

适合放入 cron 定时任务：
    # 每月 1 日凌晨 3 点抓取上个月数据
    0 3 1 * * cd /path/to/nba_analysis_project && ./scripts/scrape_latest.py >> logs/scrape.log 2>&1
"""

import sys
import time
import random
import json
import argparse
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.nba_app.webscraping.di_container import DIContainer

# ============================================================================
# 配置
# ============================================================================

DELAY_MIN = 10  # 请求间最小延迟（秒）
DELAY_MAX = 15  # 请求间最大延迟
DELAY_CATEGORY = 20  # 类别间延迟
MAX_RETRIES = 2

# 月份映射
MONTH_MAP = {
    "october": "1", "november": "2", "december": "3", "january": "4",
    "february": "5", "march": "6", "april": "7"
}

MONTH_NAMES = ["october", "november", "december", "january", "february", "march", "april"]

# ============================================================================
# 球队数据配置
# ============================================================================

TEAM_CATEGORIES = {
    # 基础统计
    "team_traditional": {"stat_category": "traditional", "extra_params": None},
    "team_advanced": {"stat_category": "advanced", "extra_params": None},

    # Four Factors
    "team_four_factors": {"stat_category": "four-factors", "extra_params": None},
    "opponent_four_factors": {
        "stat_category": "four-factors",
        "extra_params": {"OpponentTeamID": "0"}
    },

    # PlayType (11种)
    "playtype_isolation": {"stat_category": "isolation", "extra_params": None, "is_playtype": True},
    "playtype_transition": {"stat_category": "transition", "extra_params": None, "is_playtype": True},
    "playtype_ball_handler": {"stat_category": "ball-handler", "extra_params": None, "is_playtype": True},
    "playtype_roll_man": {"stat_category": "roll-man", "extra_params": None, "is_playtype": True},
    "playtype_post_up": {"stat_category": "playtype-post-up", "extra_params": None, "is_playtype": True},
    "playtype_spot_up": {"stat_category": "spot-up", "extra_params": None, "is_playtype": True},
    "playtype_handoff": {"stat_category": "hand-off", "extra_params": None, "is_playtype": True},
    "playtype_cut": {"stat_category": "cut", "extra_params": None, "is_playtype": True},
    "playtype_off_screen": {"stat_category": "off-screen", "extra_params": None, "is_playtype": True},
    "playtype_putbacks": {"stat_category": "putbacks", "extra_params": None, "is_playtype": True},
    "playtype_misc": {"stat_category": "playtype-misc", "extra_params": None, "is_playtype": True},

    # 防守
    "defense_overall": {"stat_category": "defense-dash-overall", "extra_params": None},
    "defense_lt6": {"stat_category": "defense-dash-lt6", "extra_params": None},
    "opponent_shooting": {
        "stat_category": "opponent-shooting",
        "extra_params": {"DistanceRange": "By+Zone"}
    },

    # Hustle
    "hustle": {"stat_category": "hustle", "extra_params": None},
}

# ============================================================================
# 球员数据配置
# ============================================================================

PLAYER_CATEGORIES = {
    # 基础统计
    "player_traditional": {"url_category": "traditional", "extra_params": None},
    "player_advanced": {"url_category": "advanced", "extra_params": None},

    # Tracking
    "player_touches": {"url_category": "touches", "extra_params": None},

    # PlayType (11种)
    "player_playtype_isolation": {"url_category": "isolation", "extra_params": None},
    "player_playtype_transition": {"url_category": "transition", "extra_params": None},
    "player_playtype_ball_handler": {"url_category": "ball-handler", "extra_params": None},
    "player_playtype_roll_man": {"url_category": "roll-man", "extra_params": None},
    "player_playtype_post_up": {"url_category": "playtype-post-up", "extra_params": None},
    "player_playtype_spot_up": {"url_category": "spot-up", "extra_params": None},
    "player_playtype_handoff": {"url_category": "hand-off", "extra_params": None},
    "player_playtype_cut": {"url_category": "cut", "extra_params": None},
    "player_playtype_off_screen": {"url_category": "off-screen", "extra_params": None},
    "player_playtype_putbacks": {"url_category": "putbacks", "extra_params": None},
    "player_playtype_misc": {"url_category": "playtype-misc", "extra_params": None},

    # Shooting
    "player_shooting_zone": {
        "url_category": "shooting",
        "extra_params": {"DistanceRange": "By+Zone"}
    },
    "player_shooting_5ft": {
        "url_category": "shooting",
        "extra_params": {"DistanceRange": "5ft+Range"}
    },

    # Defense
    "player_defense_overall": {"url_category": "defense-dash-overall", "extra_params": None},
    "player_defense_lt6": {"url_category": "defense-dash-lt6", "extra_params": None},
    "player_hustle": {"url_category": "hustle", "extra_params": None},

    # Scoring (includes FGM %UAST - Unassisted FG%)
    "player_scoring": {"url_category": "scoring", "extra_params": None},
}


# ============================================================================
# 工具函数
# ============================================================================

def get_current_season():
    """获取当前赛季（如 2025-26）"""
    now = datetime.now()
    year = now.year
    month = now.month

    # NBA 赛季从 10 月开始
    if month >= 10:
        return f"{year}-{str(year + 1)[2:]}"
    else:
        return f"{year - 1}-{str(year)[2:]}"


def get_current_month():
    """获取当前月份名称（NBA 统计月份）"""
    now = datetime.now()
    month = now.month

    # NBA 月份映射 (10月=1, 11月=2, ...)
    nba_months = {10: "october", 11: "november", 12: "december",
                  1: "january", 2: "february", 3: "march", 4: "april"}

    return nba_months.get(month, "january")


def get_previous_month():
    """获取上个月的月份名称"""
    now = datetime.now()
    first_day = now.replace(day=1)
    last_month = first_day - timedelta(days=1)
    month = last_month.month

    nba_months = {10: "october", 11: "november", 12: "december",
                  1: "january", 2: "february", 3: "march", 4: "april"}

    return nba_months.get(month, "january")


def get_season_months(season):
    """获取赛季包含的月份列表"""
    # 当前赛季只返回到当前月份
    current_season = get_current_season()
    current_month = get_current_month()

    if season == current_season:
        try:
            idx = MONTH_NAMES.index(current_month)
            return MONTH_NAMES[:idx + 1]
        except ValueError:
            return MONTH_NAMES[:4]  # 默认到1月
    else:
        return MONTH_NAMES  # 历史赛季返回全部月份


def random_delay(min_sec=DELAY_MIN, max_sec=DELAY_MAX):
    """随机延迟"""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)
    return delay


def season_to_dir(season):
    """将赛季格式转换为目录格式（2025-26 -> 2025_26）"""
    return season.replace("-", "_")


# ============================================================================
# 进度管理
# ============================================================================

class ProgressTracker:
    def __init__(self, progress_file):
        self.progress_file = Path(progress_file)
        self.completed = set()
        self.load()

    def load(self):
        if self.progress_file.exists():
            with open(self.progress_file) as f:
                data = json.load(f)
                self.completed = set(data.get("completed", []))

    def save(self):
        self.progress_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.progress_file, "w") as f:
            json.dump({"completed": list(self.completed)}, f, indent=2)

    def is_done(self, task_key):
        return task_key in self.completed

    def mark_done(self, task_key):
        self.completed.add(task_key)
        self.save()

    def clear(self):
        self.completed = set()
        self.save()


# ============================================================================
# 抓取函数
# ============================================================================

def scrape_team_data(scraper, season, month, categories, output_dir, progress):
    """抓取球队数据"""
    results = {"success": 0, "failed": 0, "skipped": 0}
    month_value = MONTH_MAP[month]

    for cat_name, cat_config in categories.items():
        task_key = f"team_{season}_{cat_name}_{month}"

        if progress.is_done(task_key):
            print(f"    [跳过] {cat_name}")
            results["skipped"] += 1
            continue

        try:
            params = {"Month": month_value}
            if cat_config.get("extra_params"):
                params.update(cat_config["extra_params"])

            # PlayType 使用不同的 URL
            if cat_config.get("is_playtype"):
                df = scraper.scrape_team_stats_for_season(
                    season=season,
                    stat_category=cat_config["stat_category"],
                    season_type="Regular+Season",
                    extra_params=params,
                    is_playtype=True
                )
            else:
                df = scraper.scrape_team_stats_for_season(
                    season=season,
                    stat_category=cat_config["stat_category"],
                    season_type="Regular+Season",
                    extra_params=params
                )

            if df is not None and not df.empty:
                df["Month"] = month
                df["Season"] = season

                filename = f"{cat_name}_{month}.csv"
                df.to_csv(output_dir / filename, index=False)
                print(f"    [OK] {cat_name}: {len(df)} 行 -> {filename}")
                results["success"] += 1
                progress.mark_done(task_key)
            else:
                print(f"    [空] {cat_name}: 无数据")
                results["failed"] += 1

        except Exception as e:
            print(f"    [错误] {cat_name}: {e}")
            results["failed"] += 1

        random_delay()

    return results


def scrape_player_data(page_scraper, season, month, categories, output_dir, progress):
    """抓取球员数据"""
    results = {"success": 0, "failed": 0, "skipped": 0}
    month_value = MONTH_MAP[month]

    for cat_name, cat_config in categories.items():
        task_key = f"player_{season}_{cat_name}_{month}"

        if progress.is_done(task_key):
            print(f"    [跳过] {cat_name}")
            results["skipped"] += 1
            continue

        try:
            # 构建 URL
            url_category = cat_config["url_category"]
            url = f"https://www.nba.com/stats/players/{url_category}?SeasonType=Regular+Season&Season={season}&Month={month_value}"

            if cat_config.get("extra_params"):
                for key, value in cat_config["extra_params"].items():
                    url += f"&{key}={value}"

            df = page_scraper.scrape_page(url)

            if df is not None and not df.empty:
                df["Month"] = month
                df["Season"] = season

                # 添加 PLAYER_ID
                if "PLAYER_ID" not in df.columns:
                    df["PLAYER_ID"] = range(1, len(df) + 1)

                filename = f"{cat_name}_{month}.csv"
                df.to_csv(output_dir / filename, index=False)
                print(f"    [OK] {cat_name}: {len(df)} 行 -> {filename}")
                results["success"] += 1
                progress.mark_done(task_key)
            else:
                print(f"    [空] {cat_name}: 无数据")
                results["failed"] += 1

        except Exception as e:
            print(f"    [错误] {cat_name}: {e}")
            results["failed"] += 1

        random_delay()

    return results


def scrape_player_bio(page_scraper, season, output_dir, progress):
    """抓取球员 Bio 数据（赛季级别）"""
    task_key = f"player_bio_{season}"

    if progress.is_done(task_key):
        print(f"    [跳过] player_bio")
        return {"success": 0, "failed": 0, "skipped": 1}

    try:
        url = f"https://www.nba.com/stats/players/bio?SeasonType=Regular+Season&Season={season}"
        df = page_scraper.scrape_page(url)

        if df is not None and not df.empty:
            df["Season"] = season

            # 解析身高为英寸
            if "Height" in df.columns:
                def parse_height(h):
                    try:
                        if isinstance(h, str) and "-" in h:
                            parts = h.split("-")
                            return int(parts[0]) * 12 + int(parts[1])
                    except:
                        pass
                    return None
                df["Height_Inches"] = df["Height"].apply(parse_height)

            filename = f"player_bio_{season_to_dir(season)}.csv"
            df.to_csv(output_dir / filename, index=False)
            print(f"    [OK] player_bio: {len(df)} 行 -> {filename}")
            progress.mark_done(task_key)
            return {"success": 1, "failed": 0, "skipped": 0}
        else:
            print(f"    [空] player_bio: 无数据")
            return {"success": 0, "failed": 1, "skipped": 0}

    except Exception as e:
        print(f"    [错误] player_bio: {e}")
        return {"success": 0, "failed": 1, "skipped": 0}


# ============================================================================
# 主函数
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="一键抓取最新 NBA 数据")
    parser.add_argument("--season", action="store_true", help="抓取整个赛季（而非单月）")
    parser.add_argument("--year", type=str, help="指定赛季（如 2025-26）")
    parser.add_argument("--month", type=str, help="指定月份（如 january）")
    parser.add_argument("--team-only", action="store_true", help="只抓取球队数据")
    parser.add_argument("--player-only", action="store_true", help="只抓取球员数据")
    parser.add_argument("--clear-progress", action="store_true", help="清除进度，重新抓取")
    args = parser.parse_args()

    # 确定赛季和月份
    season = args.year or get_current_season()

    if args.season:
        months = get_season_months(season)
    elif args.month:
        months = [args.month]
    else:
        # 默认抓取上个月数据
        months = [get_previous_month()]

    # 确定抓取类型
    scrape_team = not args.player_only
    scrape_player = not args.team_only

    print("=" * 70)
    print("NBA 数据一键抓取")
    print("=" * 70)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"赛季: {season}")
    print(f"月份: {', '.join(months)}")
    print(f"抓取内容: {'球队 + 球员' if scrape_team and scrape_player else '球队' if scrape_team else '球员'}")
    print()

    # 初始化进度
    progress_file = Path(f"data/newly_scraped/scrape_latest_progress_{season_to_dir(season)}.json")
    progress = ProgressTracker(progress_file)

    if args.clear_progress:
        progress.clear()
        print("已清除进度，将重新抓取所有数据")
        print()

    # 计算任务数
    team_tasks = len(TEAM_CATEGORIES) * len(months) if scrape_team else 0
    player_tasks = (len(PLAYER_CATEGORIES) * len(months) + 1) if scrape_player else 0  # +1 for bio
    total_tasks = team_tasks + player_tasks

    print(f"总任务数: {total_tasks}")
    print(f"预计时间: ~{total_tasks * 15 / 60:.0f} 分钟")
    print()

    # 初始化容器和抓取器
    container = DIContainer()
    total_results = {"success": 0, "failed": 0, "skipped": 0}

    try:
        app_logger = container.app_logger()
        app_logger.setup("scrape_latest.log")

        team_scraper = container.team_stats_scraper() if scrape_team else None
        page_scraper = container.page_scraper()

        for month in months:
            print(f"\n{'='*50}")
            print(f"月份: {month.upper()}")
            print("=" * 50)

            # 球队数据
            if scrape_team:
                print(f"\n  [球队数据]")
                team_dir = Path(f"data/newly_scraped/tracking_monthly/{season_to_dir(season)}")
                team_dir.mkdir(parents=True, exist_ok=True)

                results = scrape_team_data(team_scraper, season, month, TEAM_CATEGORIES, team_dir, progress)
                for k, v in results.items():
                    total_results[k] += v

                time.sleep(DELAY_CATEGORY)

            # 球员数据
            if scrape_player:
                print(f"\n  [球员数据]")
                player_dir = Path(f"data/newly_scraped/player_monthly/{season_to_dir(season)}")
                player_dir.mkdir(parents=True, exist_ok=True)

                results = scrape_player_data(page_scraper, season, month, PLAYER_CATEGORIES, player_dir, progress)
                for k, v in results.items():
                    total_results[k] += v

        # 球员 Bio（只需要赛季级别）
        if scrape_player:
            print(f"\n  [球员 Bio]")
            player_dir = Path(f"data/newly_scraped/player_monthly")
            player_dir.mkdir(parents=True, exist_ok=True)

            results = scrape_player_bio(page_scraper, season, player_dir, progress)
            for k, v in results.items():
                total_results[k] += v

        # 总结
        print("\n" + "=" * 70)
        print("抓取完成")
        print("=" * 70)
        print(f"成功: {total_results['success']}")
        print(f"失败: {total_results['failed']}")
        print(f"跳过: {total_results['skipped']}")
        print(f"结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        if total_results["failed"] > 0:
            print("\n提示: 有失败的任务，可以重新运行脚本继续抓取（支持断点续传）")

    except KeyboardInterrupt:
        print("\n\n用户中断，进度已保存")
        return 1
    except Exception as e:
        print(f"\n致命错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        try:
            container.web_driver_factory().close_driver()
            print("\nWebDriver 已关闭")
        except:
            pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
