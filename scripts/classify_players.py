#!/usr/bin/env python3
"""
Classify NBA players into archetypes based on their playing style.

v2: 打法优先，身高次要

分类逻辑（按优先级）：
1. Primary Initiator - 高 USG% + 高持球时间（持球核心）
2. Shot Creator - 高单打频率（自主得分手）
3. Playmaking Big - 高助攻率 + 内线身高（组织型内线）
4. Movement Shooter - 高绕掩护 + 高三分率（跑位射手）
5. Stretch Shooter - 高三分率 + 中高使用率（空间射手）
6. Secondary Ball Handler - 中高 USG% + 高挡拆频率（副攻手）
7. 3&D Wing - 高定点频率（3D侧翼）
8. Post Scorer - 高低位频率（低位单打）
9. Roll/Cut Finisher - 高顺下/空切/转换频率（终结者）
10. Rim Protector - 优秀篮下防守 + 内线身高（护框中锋）
11. Role Player - 默认

身高仅用于：
- 区分 Playmaking Big vs Playmaker
- 区分 Rim Protector vs Defensive Wing
- 输出结果中添加 Size 标签
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Configuration
INPUT_DIR = Path("data/analysis")
OUTPUT_DIR = Path("data/analysis")


def get_size_label(height_inches):
    """根据身高返回体型标签"""
    if height_inches is None:
        return "Unknown"
    elif height_inches >= 82:  # 6'10"+
        return "Big"
    elif height_inches >= 78:  # 6'6" - 6'9"
        return "Forward"
    else:  # < 6'6"
        return "Guard"


def classify_player(row):
    """
    Classify a single player based on their playing style (not height).
    Returns (archetype_name, category, size_label)
    """
    # Extract features with defaults
    height_inches = row.get('Height_Inches', None)

    usg_pct = row.get('USG_Pct', 0) or 0
    ast_pct = row.get('AST_Pct', 0) or 0
    time_of_poss = row.get('TIME_OF_POSS', 0) or 0

    threept_rate = row.get('ThreePt_Rate', 0) or 0
    if threept_rate == 0 and 'FG3A' in row and 'FGA' in row:
        fga = row.get('FGA', 0) or 0
        fg3a = row.get('FG3A', 0) or 0
        threept_rate = (fg3a / fga * 100) if fga > 0 else 0

    # PlayType frequencies (default to 0 if not available)
    pnr_handler_freq = row.get('PnR_Handler_Freq', 0) or 0
    isolation_freq = row.get('Isolation_Freq', 0) or 0
    spot_up_freq = row.get('SpotUp_Freq', 0) or 0
    off_screen_freq = row.get('OffScreen_Freq', 0) or 0
    cut_freq = row.get('Cut_Freq', 0) or 0
    transition_freq = row.get('Transition_Freq', 0) or 0
    roll_man_freq = row.get('RollMan_Freq', 0) or 0
    post_up_freq = row.get('PostUp_Freq', 0) or 0

    # Defense
    dfg_rim_pct = row.get('DFG_Rim_Pct', 100) or 100  # Default to 100 (bad defense)

    # Size label (for output, not classification)
    size = get_size_label(height_inches)
    is_big = height_inches is not None and height_inches >= 82
    is_wing = height_inches is not None and height_inches >= 76  # 6-4 or taller for wing players

    # ========================================
    # 分类逻辑（打法优先）
    # ========================================

    # 1. Primary Initiator - 持球核心
    # 高使用率 + 高持球时间
    if usg_pct > 28 and time_of_poss > 4.5:
        return "Primary Initiator", "Primary", size

    # 2. Shot Creator - 自主得分手
    # 高单打频率
    if isolation_freq > 12:
        return "Shot Creator", "Scorer", size

    # 3. Playmaking Big - 组织型内线
    # 高助攻率 + 内线身高
    if ast_pct > 20 and is_big:
        return "Playmaking Big", "Big", size

    # 4. Movement Shooter - 跑位射手
    # 高绕掩护频率 + 高三分率
    if off_screen_freq > 8 and threept_rate > 45:
        return "Movement Shooter", "Shooter", size

    # 5. Stretch Shooter - 空间射手
    # 高三分率 + 中高使用率（非跑位型）
    if threept_rate > 50 and usg_pct > 18:
        return "Stretch Shooter", "Shooter", size

    # 6. Secondary Ball Handler - 副攻手
    # 中高使用率 + 高挡拆持球频率
    if usg_pct > 20 and pnr_handler_freq > 15:
        return "Secondary Ball Handler", "Secondary", size

    # 7. 3&D Wing - 3D侧翼
    # 高定点频率 + 侧翼身高 (6-4 以上)
    if spot_up_freq > 25 and is_wing:
        return "3&D Wing", "Wing", size

    # 8. Post Scorer - 低位单打
    # 高低位频率
    if post_up_freq > 12:
        return "Post Scorer", "Big", size

    # 9. Roll/Cut Finisher - 终结者
    # 高顺下、空切或转换频率
    if roll_man_freq > 15 or cut_freq > 12 or (cut_freq + transition_freq) > 25:
        return "Finisher", "Finisher", size

    # 10. Rim Protector - 护框中锋
    # 优秀的篮下防守 + 内线身高
    if dfg_rim_pct < 58 and is_big:
        return "Rim Protector", "Big", size

    # 11. Default - 角色球员
    return "Role Player", "Role", size


def classify_players_df(df):
    """Classify all players in a dataframe."""
    results = []

    for idx, row in df.iterrows():
        archetype, category, size = classify_player(row)
        results.append({
            'PLAYER_ID': row.get('PLAYER_ID'),
            'PLAYER': row.get('PLAYER'),
            'TEAM': row.get('TEAM'),
            'Season': row.get('Season'),
            'Month': row.get('Month'),
            'Archetype': archetype,
            'Category': category,
            'Size': size,
            # Include key features for reference
            'USG_Pct': row.get('USG_Pct'),
            'AST_Pct': row.get('AST_Pct'),
            'ThreePt_Rate': row.get('ThreePt_Rate'),
            'Isolation_Freq': row.get('Isolation_Freq'),
            'Height_Inches': row.get('Height_Inches'),
            'GP': row.get('GP'),
            'MPG': row.get('MPG'),
            'PTS': row.get('PTS'),
        })

    return pd.DataFrame(results)


def generate_summary(df):
    """Generate summary statistics for classifications."""
    summary = df.groupby(['Archetype', 'Category']).agg({
        'PLAYER_ID': 'count',
        'USG_Pct': 'mean',
        'AST_Pct': 'mean',
        'ThreePt_Rate': 'mean',
        'PTS': 'mean',
    }).rename(columns={'PLAYER_ID': 'Player_Count'})

    summary = summary.round(1)
    return summary


def main():
    print("=" * 70)
    print("Player Classification v2 (打法优先)")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Try to load combined features file
    features_file = INPUT_DIR / "player_features_all_seasons.csv"

    if not features_file.exists():
        print(f"Features file not found: {features_file}")
        print("Please run build_player_features_monthly.py first.")
        return 1

    print(f"Loading features from: {features_file}")
    df = pd.read_csv(features_file)
    print(f"Loaded {len(df)} player records")

    # Classify players
    print("\nClassifying players...")
    results_df = classify_players_df(df)

    # Save results
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    output_file = OUTPUT_DIR / "player_classification_all_seasons.csv"
    results_df.to_csv(output_file, index=False)
    print(f"\nClassification results saved to: {output_file}")

    # Save per-season files
    for season in results_df['Season'].dropna().unique():
        season_df = results_df[results_df['Season'] == season]
        season_formatted = str(season).replace("-", "_")
        season_file = OUTPUT_DIR / f"player_classification_{season_formatted}.csv"
        season_df.to_csv(season_file, index=False)
        print(f"  {season}: {len(season_df)} players -> {season_file.name}")

    # Generate and save summary
    print("\n" + "=" * 70)
    print("ARCHETYPE DISTRIBUTION")
    print("=" * 70)

    summary = generate_summary(results_df)
    print(summary.to_string())

    summary_file = OUTPUT_DIR / "player_archetypes_summary.csv"
    summary.to_csv(summary_file)
    print(f"\nSummary saved to: {summary_file}")

    # Show some example players
    print("\n" + "=" * 70)
    print("EXAMPLE CLASSIFICATIONS (2025-26)")
    print("=" * 70)

    # Get latest season data
    latest_season = results_df['Season'].dropna().max()
    latest_df = results_df[results_df['Season'] == latest_season].drop_duplicates(subset=['PLAYER_ID'])

    for archetype in sorted(results_df['Archetype'].unique()):
        arch_players = latest_df[latest_df['Archetype'] == archetype]
        if not arch_players.empty:
            # Get top players by points
            top_players = arch_players.nlargest(3, 'PTS')
            players_list = []
            for _, p in top_players.iterrows():
                name = p['PLAYER'] if pd.notna(p['PLAYER']) else 'Unknown'
                size = p['Size'] if pd.notna(p['Size']) else ''
                players_list.append(f"{name} [{size}]")
            players_str = ', '.join(players_list)
            print(f"  {archetype}: {players_str}")

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
