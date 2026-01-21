#!/usr/bin/env python3
"""
Validate TCI model trained on 2024-25 data using 2025-26 season data.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# Paths
TRAIN_DIR = Path(__file__).parent.parent / "data" / "newly_scraped" / "tracking"  # 2024-25
TEST_DIR = Path(__file__).parent.parent / "data" / "newly_scraped" / "2025_26"    # 2025-26


def clean_column_names(df):
    """Replace non-breaking spaces with regular spaces."""
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_data(data_dir, season_name):
    """Load all required data files."""
    print(f"Loading {season_name} data...")

    advanced = clean_column_names(pd.read_csv(data_dir / "team_advanced_all.csv"))
    scoring = clean_column_names(pd.read_csv(data_dir / "team_scoring_all.csv"))
    passing = clean_column_names(pd.read_csv(data_dir / "tracking_passing_all.csv"))
    speed = clean_column_names(pd.read_csv(data_dir / "tracking_speed-distance_all.csv"))
    very_tight = clean_column_names(pd.read_csv(data_dir / "team_shots_defender_very_tight.csv"))
    tight = clean_column_names(pd.read_csv(data_dir / "team_shots_defender_tight.csv"))
    open_shots = clean_column_names(pd.read_csv(data_dir / "team_shots_defender_open.csv"))
    wide_open = clean_column_names(pd.read_csv(data_dir / "team_shots_defender_wide_open.csv"))

    print(f"  Loaded {len(advanced)} teams")

    return advanced, scoring, passing, speed, very_tight, tight, open_shots, wide_open


def build_feature_matrix(advanced, scoring, passing, speed, very_tight, tight, open_shots, wide_open):
    """Build feature matrix."""
    df = advanced[['TEAM', 'TEAM_ID', 'GP', 'POSS', 'OffRtg']].copy()
    df['POSS_PER_GAME'] = df['POSS'] / df['GP']

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

    # Shot defender distances
    for data, col_name in [(very_tight, 'Very_Tight_Pct'), (tight, 'Tight_Pct'),
                           (open_shots, 'Open_Pct'), (wide_open, 'Wide_Open_Pct')]:
        cols = data[['TEAM_ID', 'Freq%']].copy()
        cols = cols.rename(columns={'Freq%': col_name})
        df = df.merge(cols, on='TEAM_ID', how='left')

    # Scoring
    scoring_cols = scoring[['TEAM_ID', 'FGM %AST']].copy()
    scoring_cols = scoring_cols.rename(columns={'FGM %AST': 'FGM_AST_Pct'})
    df = df.merge(scoring_cols, on='TEAM_ID', how='left')

    return df


def main():
    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct']

    # Load training data (2024-25)
    train_data = load_data(TRAIN_DIR, "2024-25 (Training)")
    train_df = build_feature_matrix(*train_data)

    # Load test data (2025-26)
    test_data = load_data(TEST_DIR, "2025-26 (Validation)")
    test_df = build_feature_matrix(*test_data)

    # Prepare training data
    X_train = train_df[feature_cols].values
    y_train = train_df['OffRtg'].values

    # Standardize using training data statistics
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Train model on 2024-25 data
    print("\nTraining Ridge model on 2024-25 data...")
    model = Ridge(alpha=1.0)
    model.fit(X_train_scaled, y_train)

    train_r2 = model.score(X_train_scaled, y_train)
    print(f"  Training R²: {train_r2:.4f}")

    # Prepare test data
    X_test = test_df[feature_cols].values
    y_test = test_df['OffRtg'].values

    # Transform test data using training scaler
    X_test_scaled = scaler.transform(X_test)

    # Predict and evaluate on 2025-26 data
    y_pred = model.predict(X_test_scaled)
    test_r2 = model.score(X_test_scaled, y_test)

    print(f"\nValidation on 2025-26 data:")
    print(f"  Test R²: {test_r2:.4f}")

    # Calculate RMSE
    rmse = np.sqrt(np.mean((y_test - y_pred) ** 2))
    print(f"  RMSE: {rmse:.2f} points")

    # Show predictions vs actual
    print("\n" + "=" * 70)
    print("2025-26 Predictions vs Actual")
    print("=" * 70)
    print(f"{'Team':<25}{'Actual':>10}{'Predicted':>12}{'Error':>10}")
    print("-" * 70)

    results = test_df[['TEAM', 'OffRtg']].copy()
    results['Predicted'] = y_pred
    results['Error'] = results['OffRtg'] - results['Predicted']
    results = results.sort_values('OffRtg', ascending=False)

    for _, row in results.iterrows():
        print(f"{row['TEAM']:<25}{row['OffRtg']:>10.1f}{row['Predicted']:>12.1f}{row['Error']:>+10.1f}")

    # Summary
    print("\n" + "=" * 70)
    print("Summary")
    print("=" * 70)
    print(f"Training R² (2024-25):   {train_r2:.4f}")
    print(f"Validation R² (2025-26): {test_r2:.4f}")
    print(f"R² Drop:                 {train_r2 - test_r2:.4f}")
    print(f"RMSE:                    {rmse:.2f} points")


if __name__ == "__main__":
    main()
