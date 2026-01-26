#!/usr/bin/env python3
"""
Build player feature matrix from scraped monthly data.

This script merges data from multiple sources to create a comprehensive
feature matrix for player classification.

Feature dimensions:
1. Ball Handling & Creation: USG%, AST%, Time Of Poss, Unassisted FG%
2. Play Type Distribution: P&R Handler, Isolation, Spot-Up, etc.
3. Shot Geometry: 3PA Rate, Rim Freq, MidRange Freq
4. Defense & Physicality: DFG% at Rim, BLK%, STL%, Height, Weight
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

# Configuration
DATA_DIR = Path("data/newly_scraped/player_monthly")
OUTPUT_DIR = Path("data/analysis")
SEASONS = ["2021_22", "2022_23", "2023_24", "2024_25", "2025_26"]
MONTHS = ["october", "november", "december", "january", "february", "march", "april"]

# Minimum sample thresholds (for monthly data, max GP per month is ~14-17)
MIN_GP = 5  # At least 5 games in the month
MIN_MPG = 15.0


def load_csv_safe(filepath):
    """Load CSV file if it exists, otherwise return None."""
    if filepath.exists():
        try:
            return pd.read_csv(filepath)
        except Exception as e:
            print(f"    Warning: Could not load {filepath}: {e}")
    return None


def standardize_columns(df):
    """Standardize column names to expected format."""
    if df is None:
        return None

    # Column name mappings (actual -> expected)
    column_mappings = {
        'Player': 'PLAYER',
        'Team': 'TEAM',
        'Min': 'MIN',
        '3PM': 'FG3M',
        '3PA': 'FG3A',
        '3P_Pct': 'FG3_Pct',
        'Time_Of_Poss': 'TIME_OF_POSS',
        'Avg_Sec_Per_Touch': 'AVG_SEC_PER_TOUCH',
        'Front_CT_Touches': 'FRONT_CT_TOUCHES',
        'Elbow_Touches': 'ELBOW_TOUCHES',
        'Post_Ups': 'POST_TOUCHES',
        'Paint_Touches': 'PAINT_TOUCHES',
        'Freq_Pct': 'FREQ_PCT',
    }

    # Apply mappings
    for old_name, new_name in column_mappings.items():
        if old_name in df.columns:
            df = df.rename(columns={old_name: new_name})

    return df


def merge_player_data(dfs, on_cols=['PLAYER_ID', 'Season', 'Month']):
    """Merge multiple dataframes on player ID."""
    result = None
    for df in dfs:
        if df is not None and not df.empty:
            if result is None:
                result = df
            else:
                # Find common merge columns
                merge_cols = [c for c in on_cols if c in result.columns and c in df.columns]
                if merge_cols:
                    result = result.merge(df, on=merge_cols, how='outer', suffixes=('', '_dup'))
                    # Remove duplicate columns
                    result = result[[c for c in result.columns if not c.endswith('_dup')]]
    return result


def calculate_derived_features(df):
    """Calculate derived features from raw stats."""
    if df is None:
        return None

    # Unassisted FG% (if FGM_AST_Pct exists)
    if 'FGM_AST_Pct' in df.columns:
        df['Unassisted_FG_Pct'] = 100 - df['FGM_AST_Pct']
    elif 'AST_Pct' in df.columns:
        # Approximate from assist percentage
        df['Unassisted_FG_Pct'] = None  # Will need to calculate differently

    # 3PA Rate
    if 'FG3A' in df.columns and 'FGA' in df.columns:
        df['ThreePt_Rate'] = (df['FG3A'] / df['FGA'] * 100).replace([np.inf, -np.inf], 0).fillna(0)

    return df


def build_features_for_season(season):
    """Build feature matrix for a single season."""
    season_dir = DATA_DIR / season

    if not season_dir.exists():
        print(f"  Season directory not found: {season_dir}")
        return None

    print(f"\n  Processing {season}...")

    # Determine which months exist for this season
    if season == "2025_26":
        months = ["october", "november", "december", "january"]
    else:
        months = MONTHS

    all_months_data = []

    for month in months:
        print(f"    {month}...", end=" ")

        # Load all data sources for this month
        traditional = load_csv_safe(season_dir / f"player_traditional_{month}.csv")
        advanced = load_csv_safe(season_dir / f"player_advanced_{month}.csv")
        touches = load_csv_safe(season_dir / f"player_touches_{month}.csv")

        # PlayType data
        playtype_files = {
            'Isolation': f"player_playtype_isolation_{month}.csv",
            'Transition': f"player_playtype_transition_{month}.csv",
            'PnR_Handler': f"player_playtype_ball_handler_{month}.csv",
            'RollMan': f"player_playtype_roll_man_{month}.csv",
            'PostUp': f"player_playtype_post_up_{month}.csv",
            'SpotUp': f"player_playtype_spot_up_{month}.csv",
            'Handoff': f"player_playtype_handoff_{month}.csv",
            'Cut': f"player_playtype_cut_{month}.csv",
            'OffScreen': f"player_playtype_off_screen_{month}.csv",
            'Putbacks': f"player_playtype_putbacks_{month}.csv",
        }

        playtype_dfs = {}
        for name, filename in playtype_files.items():
            pt_df = load_csv_safe(season_dir / filename)
            if pt_df is not None:
                # Rename FREQ% column to be specific
                freq_col = [c for c in pt_df.columns if 'FREQ' in c.upper()]
                if freq_col:
                    pt_df = pt_df.rename(columns={freq_col[0]: f'{name}_Freq'})
                playtype_dfs[name] = pt_df

        # Shooting data
        shooting_zone = load_csv_safe(season_dir / f"player_shooting_by_zone_{month}.csv")

        # Defense data
        defense_overall = load_csv_safe(season_dir / f"player_defense_overall_{month}.csv")
        defense_lt6 = load_csv_safe(season_dir / f"player_defense_lt6_{month}.csv")
        hustle = load_csv_safe(season_dir / f"player_hustle_{month}.csv")

        # Check if we have minimum data
        if traditional is None or advanced is None:
            print("Missing required data")
            continue

        # Standardize column names
        traditional = standardize_columns(traditional)
        advanced = standardize_columns(advanced)
        if touches is not None:
            touches = standardize_columns(touches)

        # Start with traditional + advanced merge
        if 'PLAYER_ID' in traditional.columns and 'PLAYER_ID' in advanced.columns:
            merge_cols = ['PLAYER_ID']
            if 'Month' in traditional.columns:
                merge_cols.append('Month')
            if 'Season' in traditional.columns:
                merge_cols.append('Season')

            # Select key columns from each source
            trad_cols = ['PLAYER_ID', 'PLAYER', 'TEAM', 'GP', 'MIN', 'PTS', 'REB', 'AST',
                        'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA', 'Month', 'Season']
            trad_cols = [c for c in trad_cols if c in traditional.columns]

            adv_cols = ['PLAYER_ID', 'USG_Pct', 'AST_Pct', 'TS_Pct', 'eFG_Pct',
                       'OFF_RATING', 'DEF_RATING', 'NET_RATING', 'PIE']
            adv_cols = [c for c in adv_cols if c in advanced.columns]

            df = traditional[trad_cols].merge(
                advanced[adv_cols],
                on='PLAYER_ID',
                how='inner'
            )
        else:
            print("Missing PLAYER_ID")
            continue

        # Add touches data
        if touches is not None and 'PLAYER_ID' in touches.columns:
            touch_cols = ['PLAYER_ID', 'TOUCHES', 'TIME_OF_POSS', 'AVG_SEC_PER_TOUCH',
                         'FRONT_CT_TOUCHES', 'ELBOW_TOUCHES', 'POST_TOUCHES', 'PAINT_TOUCHES']
            touch_cols = [c for c in touch_cols if c in touches.columns]
            if touch_cols:
                df = df.merge(touches[touch_cols], on='PLAYER_ID', how='left')

        # Add playtype frequencies
        for name, pt_df in playtype_dfs.items():
            if pt_df is not None and 'PLAYER_ID' in pt_df.columns:
                freq_col = f'{name}_Freq'
                if freq_col in pt_df.columns:
                    df = df.merge(
                        pt_df[['PLAYER_ID', freq_col]],
                        on='PLAYER_ID',
                        how='left'
                    )

        # Add defense data
        if defense_lt6 is not None and 'PLAYER_ID' in defense_lt6.columns:
            def_cols = ['PLAYER_ID']
            # Look for DFG% column for rim protection
            dfg_cols = [c for c in defense_lt6.columns if 'DFG' in c.upper() and 'PCT' in c.upper()]
            if dfg_cols:
                defense_lt6 = defense_lt6.rename(columns={dfg_cols[0]: 'DFG_Rim_Pct'})
                def_cols.append('DFG_Rim_Pct')
            if len(def_cols) > 1:
                df = df.merge(defense_lt6[def_cols], on='PLAYER_ID', how='left')

        # Calculate derived features
        df = calculate_derived_features(df)

        # MIN is already MPG in the scraped data
        if 'MIN' in df.columns:
            df['MPG'] = df['MIN']

        print(f"{len(df)} players")
        all_months_data.append(df)

    if not all_months_data:
        return None

    # Combine all months
    season_df = pd.concat(all_months_data, ignore_index=True)

    return season_df


def apply_filters(df):
    """Apply minimum sample thresholds."""
    if df is None:
        return None

    original_count = len(df)

    # Filter by GP and MPG
    if 'GP' in df.columns and 'MPG' in df.columns:
        df = df[(df['GP'] >= MIN_GP) & (df['MPG'] >= MIN_MPG)]

    filtered_count = len(df)
    print(f"  Filtered: {original_count} -> {filtered_count} players (GP >= {MIN_GP}, MPG >= {MIN_MPG})")

    return df


def add_bio_data(df, season):
    """Add bio data (height, weight) from season-level file."""
    bio_file = DATA_DIR / f"player_bio_{season}.csv"
    bio_df = load_csv_safe(bio_file)

    if bio_df is None:
        print(f"  Warning: Bio data not found for {season}")
        return df

    # Standardize columns
    bio_df = standardize_columns(bio_df)

    # Select relevant columns
    bio_cols = ['PLAYER_ID']

    # Height
    height_cols = [c for c in bio_df.columns if 'HEIGHT' in c.upper()]
    if height_cols:
        bio_cols.append(height_cols[0])

    # Weight
    weight_cols = [c for c in bio_df.columns if 'WEIGHT' in c.upper()]
    if weight_cols:
        bio_cols.append(weight_cols[0])

    # Height in inches (if calculated)
    if 'Height_Inches' in bio_df.columns:
        bio_cols.append('Height_Inches')

    if len(bio_cols) > 1 and 'PLAYER_ID' in df.columns:
        df = df.merge(bio_df[bio_cols], on='PLAYER_ID', how='left')

    return df


def main():
    print("=" * 70)
    print("Player Feature Builder")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Seasons: {SEASONS}")
    print()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    all_data = []

    for season in SEASONS:
        season_df = build_features_for_season(season)

        if season_df is not None and not season_df.empty:
            # Add bio data
            season_df = add_bio_data(season_df, season)

            # Apply filters
            season_df = apply_filters(season_df)

            if season_df is not None and not season_df.empty:
                all_data.append(season_df)

                # Save season-specific file
                output_file = OUTPUT_DIR / f"player_features_{season}.csv"
                season_df.to_csv(output_file, index=False)
                print(f"  Saved: {output_file}")

    # Combine all seasons
    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)

        # Save combined file
        output_file = OUTPUT_DIR / "player_features_all_seasons.csv"
        combined_df.to_csv(output_file, index=False)
        print(f"\nCombined file: {output_file}")
        print(f"Total records: {len(combined_df)}")

        # Print feature summary
        print("\nFeature columns:")
        for col in sorted(combined_df.columns):
            non_null = combined_df[col].notna().sum()
            print(f"  {col}: {non_null}/{len(combined_df)} non-null")

    print("\n" + "=" * 70)
    print("COMPLETE")
    print("=" * 70)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
