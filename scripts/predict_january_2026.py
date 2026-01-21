#!/usr/bin/env python3
"""
Predict January 2026 OffRtg using trained TCI model.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import json

# Paths
DATA_DIR = Path("data/newly_scraped/tracking_monthly")
OUTPUT_DIR = Path("data/analysis")

# Training seasons
TRAINING_SEASONS = {
    "2021_22": ["october", "november", "december", "january", "february", "march", "april"],
    "2022_23": ["october", "november", "december", "january", "february", "march", "april"],
    "2023_24": ["october", "november", "december", "january", "february", "march", "april"],
    "2024_25": ["october", "november", "december", "january", "february", "march", "april"],
}


def clean_column_names(df):
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_monthly_data(data_dir, months, season_name=""):
    """Load and combine monthly data files."""
    all_data = []

    for month in months:
        try:
            passing = clean_column_names(pd.read_csv(data_dir / f"tracking_passing_{month}.csv"))
            speed = clean_column_names(pd.read_csv(data_dir / f"tracking_speed_distance_{month}.csv"))
            advanced = clean_column_names(pd.read_csv(data_dir / f"team_advanced_{month}.csv"))
            scoring = clean_column_names(pd.read_csv(data_dir / f"team_scoring_{month}.csv"))

            very_tight_file = data_dir / f"shots_very_tight_{month}.csv"
            tight_file = data_dir / f"shots_tight_{month}.csv"
            open_file = data_dir / f"shots_open_{month}.csv"
            wide_open_file = data_dir / f"shots_wide_open_{month}.csv"

            very_tight = clean_column_names(pd.read_csv(very_tight_file)) if very_tight_file.exists() else None
            tight = clean_column_names(pd.read_csv(tight_file)) if tight_file.exists() else None
            open_shots = clean_column_names(pd.read_csv(open_file)) if open_file.exists() else None
            wide_open = clean_column_names(pd.read_csv(wide_open_file)) if wide_open_file.exists() else None

            df = advanced[['TEAM', 'TEAM_ID', 'GP', 'POSS', 'OffRtg', 'OREB%', 'TOV%']].copy()
            df['Month'] = month
            df['Season'] = season_name
            df['POSS_PER_GAME'] = df['POSS'] / df['GP']
            df = df.rename(columns={'OREB%': 'OREB_Pct', 'TOV%': 'TOV_Pct'})

            passing_cols = passing[['TEAM_ID', 'Passes Made', 'Secondary AST', 'Potential AST', 'AST To Pass%']].copy()
            passing_cols = passing_cols.rename(columns={'AST To Pass%': 'AST_To_Pass_Pct'})
            df = df.merge(passing_cols, on='TEAM_ID', how='left')

            df['Passes_Per_Poss'] = df['Passes Made'] / df['POSS_PER_GAME']
            df['Potential_AST_To_Pass_Pct'] = df['Potential AST'] / df['Passes Made'] * 100

            speed_cols = speed[['TEAM_ID', 'Dist. Miles Off']].copy()
            speed_cols = speed_cols.rename(columns={'Dist. Miles Off': 'Dist_Miles_Off'})
            df = df.merge(speed_cols, on='TEAM_ID', how='left')

            for data, col_name in [(very_tight, 'Very_Tight_Pct'), (tight, 'Tight_Pct'),
                                   (open_shots, 'Open_Pct'), (wide_open, 'Wide_Open_Pct')]:
                if data is not None:
                    cols = data[['TEAM_ID', 'Freq%']].copy()
                    cols = cols.rename(columns={'Freq%': col_name})
                    df = df.merge(cols, on='TEAM_ID', how='left')
                else:
                    df[col_name] = np.nan

            scoring_cols = scoring[['TEAM_ID', 'FGM %AST']].copy()
            scoring_cols = scoring_cols.rename(columns={'FGM %AST': 'FGM_AST_Pct'})
            df = df.merge(scoring_cols, on='TEAM_ID', how='left')

            shooting_distance_file = data_dir / f"shooting_distance_{month}.csv"
            if shooting_distance_file.exists():
                shooting_distance = clean_column_names(pd.read_csv(shooting_distance_file))
                shooting_distance['Total_FGA'] = (
                    shooting_distance['Less_than_5ft_FGA'] +
                    shooting_distance['5-9_ft_FGA'] +
                    shooting_distance['10-14_ft_FGA'] +
                    shooting_distance['15-19_ft_FGA'] +
                    shooting_distance['20-24_ft_FGA'] +
                    shooting_distance['25-29_ft_FGA']
                )
                shooting_distance['Mid_Range_Pct'] = (
                    (shooting_distance['10-14_ft_FGA'] + shooting_distance['15-19_ft_FGA'])
                    / shooting_distance['Total_FGA'] * 100
                )
                mid_range_cols = shooting_distance[['TEAM_ID', 'Mid_Range_Pct']].copy()
                df = df.merge(mid_range_cols, on='TEAM_ID', how='left')
            else:
                df['Mid_Range_Pct'] = np.nan

            all_data.append(df)

        except Exception as e:
            print(f"  Error loading {month}: {e}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def main():
    print("=" * 70)
    print("January 2026 OffRtg Prediction")
    print("=" * 70)

    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct',
                    'OREB_Pct', 'TOV_Pct', 'Mid_Range_Pct']

    # Load training data
    print("\nLoading training data...")
    all_train = []
    for season_name, months in TRAINING_SEASONS.items():
        data_dir = DATA_DIR / season_name
        if data_dir.exists():
            df = load_monthly_data(data_dir, months, season_name)
            if not df.empty:
                all_train.append(df)
    train_df = pd.concat(all_train, ignore_index=True)

    # Fill missing values
    for feat in feature_cols:
        if train_df[feat].isnull().any():
            mean_val = train_df[feat].mean()
            train_df[feat] = train_df[feat].fillna(mean_val)

    train_df = train_df.dropna(subset=['OffRtg'])
    print(f"Training samples: {len(train_df)}")

    # Load January 2026 data
    print("\nLoading January 2026 data...")
    jan_df = load_monthly_data(DATA_DIR / "2025_26", ["january"], "2025_26")
    print(f"January 2026 samples: {len(jan_df)}")

    # Train model
    X_train = train_df[feature_cols].values
    y_train = train_df['OffRtg'].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = Ridge(alpha=1.0)
    model.fit(X_train_scaled, y_train)

    # Predict January 2026
    X_jan = jan_df[feature_cols].values
    X_jan_scaled = scaler.transform(X_jan)
    jan_df['Predicted_OffRtg'] = model.predict(X_jan_scaled)
    jan_df['Error'] = jan_df['Predicted_OffRtg'] - jan_df['OffRtg']

    # Calculate metrics
    rmse = np.sqrt(np.mean(jan_df['Error'] ** 2))
    mae = np.mean(np.abs(jan_df['Error']))
    r2 = 1 - (np.sum(jan_df['Error'] ** 2) / np.sum((jan_df['OffRtg'] - jan_df['OffRtg'].mean()) ** 2))

    print(f"\n{'='*70}")
    print("Prediction Results for January 2026")
    print(f"{'='*70}")
    print(f"R²:   {r2:.4f}")
    print(f"RMSE: {rmse:.2f}")
    print(f"MAE:  {mae:.2f}")

    # Sort by actual OffRtg
    jan_df = jan_df.sort_values('OffRtg', ascending=False)

    print(f"\n{'Team':<25}{'Actual':>10}{'Predicted':>12}{'Error':>10}")
    print("-" * 57)
    for _, row in jan_df.iterrows():
        error_flag = " ***" if abs(row['Error']) > 5 else ""
        print(f"{row['TEAM']:<25}{row['OffRtg']:>10.1f}{row['Predicted_OffRtg']:>12.1f}{row['Error']:>+10.1f}{error_flag}")

    # Save results
    output_cols = ['TEAM', 'OffRtg', 'Predicted_OffRtg', 'Error'] + feature_cols
    jan_df[output_cols].to_csv(OUTPUT_DIR / "january_2026_prediction.csv", index=False)
    print(f"\nSaved: {OUTPUT_DIR / 'january_2026_prediction.csv'}")

    # Show worst predictions
    print(f"\n{'='*70}")
    print("Largest Prediction Errors (|Error| > 5)")
    print(f"{'='*70}")
    large_errors = jan_df[abs(jan_df['Error']) > 5].sort_values('Error', key=abs, ascending=False)
    if len(large_errors) > 0:
        for _, row in large_errors.iterrows():
            direction = "高估" if row['Error'] > 0 else "低估"
            print(f"  {row['TEAM']}: {direction} {abs(row['Error']):.1f} 分")
    else:
        print("  无")


if __name__ == "__main__":
    main()
