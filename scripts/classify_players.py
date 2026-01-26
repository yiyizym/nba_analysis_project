#!/usr/bin/env python3
"""
Classify NBA players into archetypes based on their playing style.

Player Archetypes (13 types):

Big Men (Height >= 6'10" or Position == C):
1. Stretch Big - 3PA Rate > 40%
2. Versatile Big - AST% > 20%
3. Post Scorer - PostUp Freq > 20%
4. Anchor Big - DFG Rim < 55%
5. Rim Runner - Default big

Wings/Guards:
6. Primary Initiator - USG% > 28% AND Time Of Poss > 6min
7. Secondary Ball Handler - USG% > 20% AND PnR Handler Freq > 25%
8. Movement Shooter - OffScreen Freq > 10% AND 3PA Rate > 60%
9. Shot Creator - Isolation Freq > 15% AND Unassisted FG% > 50%
10. 3&D Wing - SpotUp Freq > 40% AND good defense
11. Athletic Finisher - Cut+Transition > 30% AND Rim Freq > 50%
12. Slashing Creator - High Rim Freq AND moderate isolation
13. Role Player - Default wing
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Configuration
INPUT_DIR = Path("data/analysis")
OUTPUT_DIR = Path("data/analysis")


def classify_player(row):
    """
    Classify a single player based on their stats.
    Returns (archetype_name, archetype_category)
    """
    # Extract features with defaults
    height_inches = row.get('Height_Inches', None)
    position = str(row.get('POS', '')).upper() if pd.notna(row.get('POS')) else ''

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

    # Unassisted FG%
    unassisted_fg_pct = row.get('Unassisted_FG_Pct', 50) or 50

    # Shooting zones (estimate rim frequency from available data)
    rim_freq = 0
    if 'Restricted_Area_FGA_Pct' in row:
        rim_freq = row.get('Restricted_Area_FGA_Pct', 0) or 0

    # Step 1: Determine if Big or Wing/Guard
    is_big = False
    if height_inches is not None and height_inches >= 82:  # 6'10" = 82 inches
        is_big = True
    elif 'C' in position or 'PF' in position:
        is_big = True

    # Step 2: Classify based on category
    if is_big:
        # Big Men Classification
        if threept_rate > 40:
            return "Stretch Big", "Big"
        elif ast_pct > 20:
            return "Versatile Big", "Big"
        elif post_up_freq > 20:
            return "Post Scorer", "Big"
        elif dfg_rim_pct < 55:
            return "Anchor Big", "Big"
        else:
            return "Rim Runner", "Big"
    else:
        # Wings/Guards Classification

        # Primary ball handlers (high usage + high time of possession)
        if usg_pct > 28 and time_of_poss > 5.0:
            return "Primary Initiator", "Primary"

        # Movement shooter (high off-screen frequency + elite 3PT rate)
        # Check this before secondary handler for players like Curry
        if off_screen_freq > 10 and threept_rate > 55:
            return "Movement Shooter", "Shooter"

        # Elite shooter (high 3PT rate + high usage, even without off-screen data)
        if threept_rate > 55 and usg_pct > 25:
            return "Movement Shooter", "Shooter"

        # Secondary ball handlers
        if usg_pct > 20 and pnr_handler_freq > 20:
            return "Secondary Ball Handler", "Secondary"

        # Shot creator
        if isolation_freq > 15 and unassisted_fg_pct > 50:
            return "Shot Creator", "Wing"

        # 3&D Wing (spot up shooter with decent defense)
        if spot_up_freq > 40:
            return "3&D Wing", "Wing"

        # Athletic finisher
        if (cut_freq + transition_freq) > 30 and rim_freq > 50:
            return "Athletic Finisher", "Wing"

        # Slashing creator
        if rim_freq > 40 and isolation_freq > 10:
            return "Slashing Creator", "Wing"

        # Default
        return "Role Player", "Role"


def classify_players_df(df):
    """Classify all players in a dataframe."""
    results = []

    for idx, row in df.iterrows():
        archetype, category = classify_player(row)
        results.append({
            'PLAYER_ID': row.get('PLAYER_ID'),
            'PLAYER': row.get('PLAYER'),
            'TEAM': row.get('TEAM'),
            'Season': row.get('Season'),
            'Month': row.get('Month'),
            'Archetype': archetype,
            'Category': category,
            # Include key features for reference
            'USG_Pct': row.get('USG_Pct'),
            'AST_Pct': row.get('AST_Pct'),
            'ThreePt_Rate': row.get('ThreePt_Rate'),
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
    print("Player Classification")
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
    print("EXAMPLE CLASSIFICATIONS")
    print("=" * 70)

    # Get latest season data
    latest_season = results_df['Season'].dropna().max()
    latest_df = results_df[results_df['Season'] == latest_season].drop_duplicates(subset=['PLAYER_ID'])

    for archetype in results_df['Archetype'].unique():
        arch_players = latest_df[latest_df['Archetype'] == archetype]
        if not arch_players.empty:
            # Get top players by points
            top_players = arch_players.nlargest(3, 'PTS')['PLAYER'].tolist()
            players_str = ', '.join([str(p) for p in top_players if pd.notna(p)])
            print(f"  {archetype}: {players_str}")

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
