#!/usr/bin/env python3
"""
TCI Model with Monthly Data

Train TCI model using monthly-level data for larger sample size.
- Training: 2024-25 season (7 months × 30 teams = 210 samples)
- Validation: 2025-26 season (4 months × 30 teams = 120 samples)
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

# Training data: 2021-22, 2022-23, 2023-24, 2024-25
TRAINING_SEASONS = {
    "2021_22": ["october", "november", "december", "january", "february", "march", "april"],
    "2022_23": ["october", "november", "december", "january", "february", "march", "april"],
    "2023_24": ["october", "november", "december", "january", "february", "march", "april"],
    "2024_25": ["october", "november", "december", "january", "february", "march", "april"],
}

# Validation data: 2025-26 (current season)
VALIDATION_SEASONS = {
    "2025_26": ["october", "november", "december", "january"],
}


def clean_column_names(df):
    """Replace non-breaking spaces."""
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_monthly_data(data_dir, months, season_name=""):
    """Load and combine monthly data files."""
    all_data = []

    for month in months:
        try:
            # Load each category for this month
            passing = clean_column_names(pd.read_csv(data_dir / f"tracking_passing_{month}.csv"))
            speed = clean_column_names(pd.read_csv(data_dir / f"tracking_speed_distance_{month}.csv"))
            advanced = clean_column_names(pd.read_csv(data_dir / f"team_advanced_{month}.csv"))
            scoring = clean_column_names(pd.read_csv(data_dir / f"team_scoring_{month}.csv"))

            # Shot defender distances (may be missing for some historical data)
            very_tight_file = data_dir / f"shots_very_tight_{month}.csv"
            tight_file = data_dir / f"shots_tight_{month}.csv"
            open_file = data_dir / f"shots_open_{month}.csv"
            wide_open_file = data_dir / f"shots_wide_open_{month}.csv"

            very_tight = clean_column_names(pd.read_csv(very_tight_file)) if very_tight_file.exists() else None
            tight = clean_column_names(pd.read_csv(tight_file)) if tight_file.exists() else None
            open_shots = clean_column_names(pd.read_csv(open_file)) if open_file.exists() else None
            wide_open = clean_column_names(pd.read_csv(wide_open_file)) if wide_open_file.exists() else None

            # Load four-factors data for FTA Rate
            four_factors_file = data_dir / f"four_factors_{month}.csv"
            four_factors = clean_column_names(pd.read_csv(four_factors_file)) if four_factors_file.exists() else None

            # Build feature matrix for this month
            # Include eFG% from advanced stats
            df = advanced[['TEAM', 'TEAM_ID', 'GP', 'POSS', 'OffRtg', 'OREB%', 'TOV%', 'eFG%']].copy()
            df['Month'] = month
            df['Season'] = season_name
            df['POSS_PER_GAME'] = df['POSS'] / df['GP']
            # Rename for consistency
            df = df.rename(columns={'OREB%': 'OREB_Pct', 'TOV%': 'TOV_Pct', 'eFG%': 'eFG_Pct'})

            # Add FTA Rate from four-factors
            if four_factors is not None:
                ff_cols = four_factors[['TEAM_ID', 'FTA Rate']].copy()
                ff_cols = ff_cols.rename(columns={'FTA Rate': 'FTA_Rate'})
                df = df.merge(ff_cols, on='TEAM_ID', how='left')
            else:
                df['FTA_Rate'] = np.nan

            # Passing features
            passing_cols = passing[['TEAM_ID', 'Passes Made', 'Secondary AST', 'Potential AST', 'AST To Pass%']].copy()
            passing_cols = passing_cols.rename(columns={'AST To Pass%': 'AST_To_Pass_Pct'})
            df = df.merge(passing_cols, on='TEAM_ID', how='left')

            df['Passes_Per_Poss'] = df['Passes Made'] / df['POSS_PER_GAME']
            df['Potential_AST_To_Pass_Pct'] = df['Potential AST'] / df['Passes Made'] * 100

            # Speed-distance
            speed_cols = speed[['TEAM_ID', 'Dist. Miles Off']].copy()
            speed_cols = speed_cols.rename(columns={'Dist. Miles Off': 'Dist_Miles_Off'})
            df = df.merge(speed_cols, on='TEAM_ID', how='left')

            # Shot defender distances (handle missing data)
            for data, col_name in [(very_tight, 'Very_Tight_Pct'), (tight, 'Tight_Pct'),
                                   (open_shots, 'Open_Pct'), (wide_open, 'Wide_Open_Pct')]:
                if data is not None:
                    cols = data[['TEAM_ID', 'Freq%']].copy()
                    cols = cols.rename(columns={'Freq%': col_name})
                    df = df.merge(cols, on='TEAM_ID', how='left')
                else:
                    df[col_name] = np.nan

            # Scoring
            scoring_cols = scoring[['TEAM_ID', 'FGM %AST']].copy()
            scoring_cols = scoring_cols.rename(columns={'FGM %AST': 'FGM_AST_Pct'})
            df = df.merge(scoring_cols, on='TEAM_ID', how='left')

            # Shot distance percentages
            shooting_distance_file = data_dir / f"shooting_distance_{month}.csv"
            if shooting_distance_file.exists():
                shooting_distance = clean_column_names(pd.read_csv(shooting_distance_file))
                # Calculate total FGA
                shooting_distance['Total_FGA'] = (
                    shooting_distance['Less_than_5ft_FGA'] +
                    shooting_distance['5-9_ft_FGA'] +
                    shooting_distance['10-14_ft_FGA'] +
                    shooting_distance['15-19_ft_FGA'] +
                    shooting_distance['20-24_ft_FGA'] +
                    shooting_distance['25-29_ft_FGA']
                )
                # Rim shots (< 5ft)
                shooting_distance['Rim_Pct'] = (
                    shooting_distance['Less_than_5ft_FGA'] / shooting_distance['Total_FGA'] * 100
                )
                # Mid-range (10-19 ft)
                shooting_distance['Mid_Range_Pct'] = (
                    (shooting_distance['10-14_ft_FGA'] + shooting_distance['15-19_ft_FGA'])
                    / shooting_distance['Total_FGA'] * 100
                )
                # Three-point (25-29 ft)
                shooting_distance['Three_Pt_Pct'] = (
                    shooting_distance['25-29_ft_FGA'] / shooting_distance['Total_FGA'] * 100
                )
                shot_cols = shooting_distance[['TEAM_ID', 'Rim_Pct', 'Mid_Range_Pct', 'Three_Pt_Pct']].copy()
                df = df.merge(shot_cols, on='TEAM_ID', how='left')
            else:
                df['Rim_Pct'] = np.nan
                df['Mid_Range_Pct'] = np.nan
                df['Three_Pt_Pct'] = np.nan

            all_data.append(df)
            print(f"    {month}: {len(df)} teams")

        except Exception as e:
            print(f"    {month}: Error - {e}")

    if all_data:
        combined = pd.concat(all_data, ignore_index=True)
        return combined
    return pd.DataFrame()


def load_all_seasons(seasons_dict):
    """Load data from multiple seasons."""
    all_data = []
    for season_name, months in seasons_dict.items():
        print(f"  {season_name}:")
        data_dir = DATA_DIR / season_name
        if data_dir.exists():
            df = load_monthly_data(data_dir, months, season_name)
            if not df.empty:
                all_data.append(df)
        else:
            print(f"    Directory not found: {data_dir}")

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def main():
    print("=" * 70)
    print("TCI Model Training with Monthly Data (Multi-Season)")
    print("=" * 70)

    # 17 features including Four Factors (eFG%, FTA_Rate, TOV_Pct, OREB_Pct)
    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct',
                    'OREB_Pct', 'TOV_Pct',
                    'Rim_Pct', 'Mid_Range_Pct', 'Three_Pt_Pct',
                    'eFG_Pct', 'FTA_Rate']  # Four Factors features

    # Load training data (2021-22 to 2024-25)
    print("\nLoading training data (2021-22 to 2024-25)...")
    train_df = load_all_seasons(TRAINING_SEASONS)
    print(f"Total training samples (before cleaning): {len(train_df)}")

    # Load validation data (2025-26)
    print("\nLoading validation data (2025-26)...")
    val_df = load_all_seasons(VALIDATION_SEASONS)
    print(f"Total validation samples (before cleaning): {len(val_df)}")

    # Check for missing values
    print("\nChecking for missing values...")
    train_missing = train_df[feature_cols].isnull().sum()
    val_missing = val_df[feature_cols].isnull().sum()
    print("  Training missing by feature:")
    for feat in feature_cols:
        if train_missing[feat] > 0:
            print(f"    {feat}: {train_missing[feat]}")
    print(f"  Validation: {val_missing.sum()} total missing")

    # Fill missing values with mean (instead of dropping rows)
    print("\nFilling missing values with feature mean...")
    for feat in feature_cols:
        if train_df[feat].isnull().any():
            mean_val = train_df[feat].mean()
            n_filled = train_df[feat].isnull().sum()
            train_df[feat] = train_df[feat].fillna(mean_val)
            print(f"  {feat}: filled {n_filled} values with mean={mean_val:.2f}")

    # Drop rows only if OffRtg is missing
    train_df = train_df.dropna(subset=['OffRtg'])
    val_df = val_df.dropna(subset=['OffRtg'])
    print(f"\nAfter processing:")
    print(f"  Training samples: {len(train_df)}")
    print(f"  Validation samples: {len(val_df)}")

    # Prepare data
    X_train = train_df[feature_cols].values
    y_train = train_df['OffRtg'].values
    X_val = val_df[feature_cols].values
    y_val = val_df['OffRtg'].values

    # Standardize
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_val_scaled = scaler.transform(X_val)

    # Train Ridge model
    print("\n" + "=" * 70)
    print("Training Ridge Regression")
    print("=" * 70)

    model = Ridge(alpha=1.0)
    model.fit(X_train_scaled, y_train)

    # Evaluate
    train_r2 = model.score(X_train_scaled, y_train)
    val_r2 = model.score(X_val_scaled, y_val)

    y_train_pred = model.predict(X_train_scaled)
    y_val_pred = model.predict(X_val_scaled)

    train_rmse = np.sqrt(np.mean((y_train - y_train_pred) ** 2))
    val_rmse = np.sqrt(np.mean((y_val - y_val_pred) ** 2))

    print(f"\nTraining R²:   {train_r2:.4f}")
    print(f"Validation R²: {val_r2:.4f}")
    print(f"R² Drop:       {train_r2 - val_r2:.4f}")
    print(f"\nTraining RMSE:   {train_rmse:.2f}")
    print(f"Validation RMSE: {val_rmse:.2f}")

    # Feature weights
    weights = dict(zip(feature_cols, model.coef_))
    print("\nFeature Weights (standardized):")
    for feat, w in sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"  {feat}: {w:+.4f}")

    # Save model info
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    model_info = {
        "data_type": "monthly_multi_season",
        "training_seasons": list(TRAINING_SEASONS.keys()),
        "validation_seasons": list(VALIDATION_SEASONS.keys()),
        "training_samples": len(train_df),
        "validation_samples": len(val_df),
        "training_r2": float(train_r2),
        "validation_r2": float(val_r2),
        "training_rmse": float(train_rmse),
        "validation_rmse": float(val_rmse),
        "weights": {k: float(v) for k, v in weights.items()},
        "feature_order": feature_cols
    }

    with open(OUTPUT_DIR / "tci_model_monthly.json", "w") as f:
        json.dump(model_info, f, indent=2)
    print(f"\nSaved: {OUTPUT_DIR / 'tci_model_monthly.json'}")

    # Compare with previous model
    print("\n" + "=" * 70)
    print("Comparison: v4 (15 features) vs v5 (17 features + Four Factors)")
    print("=" * 70)
    print(f"{'Metric':<20}{'v4 (15 features)':<25}{'v5 (17 features)':<25}")
    print("-" * 70)
    print(f"{'Training R²':<20}{'0.7796':<25}{train_r2:<25.4f}")
    print(f"{'Validation R²':<20}{'0.6824':<25}{val_r2:<25.4f}")
    print(f"{'R² Drop':<20}{'0.0971':<25}{train_r2 - val_r2:<25.4f}")
    print("\nNew features added:")
    print("  - eFG_Pct (Effective Field Goal %)")
    print("  - FTA_Rate (Free Throw Attempt Rate = FTA/FGA)")

    print("\nDone!")


if __name__ == "__main__":
    main()
