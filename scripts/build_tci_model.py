#!/usr/bin/env python3
"""
TCI (Tactical Cohesion Index) Model Builder

This script builds a Ridge regression model to quantify team tactical cohesion
based on NBA tracking data. The model uses offensive rating (OffRtg) as the
target variable and various passing/movement metrics as features.

Data: 2024-25 Season
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import json

# Paths
DATA_DIR = Path(__file__).parent.parent / "data" / "newly_scraped" / "tracking"
OUTPUT_DIR = Path(__file__).parent.parent / "data" / "analysis"


def clean_column_names(df):
    """Replace non-breaking spaces with regular spaces in column names."""
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_data():
    """Load all required data files."""
    print("Loading data files (2024-25 Season)...")

    # Team advanced stats (contains OffRtg and POSS)
    advanced = clean_column_names(pd.read_csv(DATA_DIR / "team_advanced_all.csv"))
    print(f"  - team_advanced_all.csv: {len(advanced)} rows")

    # Team scoring stats (contains FGM %AST)
    scoring = clean_column_names(pd.read_csv(DATA_DIR / "team_scoring_all.csv"))
    print(f"  - team_scoring_all.csv: {len(scoring)} rows")

    # Tracking: passing (contains Passes Made, Secondary AST)
    passing = clean_column_names(pd.read_csv(DATA_DIR / "tracking_passing_all.csv"))
    print(f"  - tracking_passing_all.csv: {len(passing)} rows")

    # Tracking: speed-distance (contains Dist. Miles Off)
    speed = clean_column_names(pd.read_csv(DATA_DIR / "tracking_speed-distance_all.csv"))
    print(f"  - tracking_speed-distance_all.csv: {len(speed)} rows")

    # Shots by defender distance (all 4 categories)
    very_tight = clean_column_names(pd.read_csv(DATA_DIR / "team_shots_defender_very_tight.csv"))
    print(f"  - team_shots_defender_very_tight.csv: {len(very_tight)} rows")

    tight = clean_column_names(pd.read_csv(DATA_DIR / "team_shots_defender_tight.csv"))
    print(f"  - team_shots_defender_tight.csv: {len(tight)} rows")

    open_shots = clean_column_names(pd.read_csv(DATA_DIR / "team_shots_defender_open.csv"))
    print(f"  - team_shots_defender_open.csv: {len(open_shots)} rows")

    wide_open = clean_column_names(pd.read_csv(DATA_DIR / "team_shots_defender_wide_open.csv"))
    print(f"  - team_shots_defender_wide_open.csv: {len(wide_open)} rows")

    return advanced, scoring, passing, speed, very_tight, tight, open_shots, wide_open


def build_feature_matrix(advanced, scoring, passing, speed, very_tight, tight, open_shots, wide_open):
    """Merge all data sources and build feature matrix."""
    print("\nBuilding feature matrix...")

    # Start with advanced stats (has OffRtg as target)
    df = advanced[['TEAM', 'TEAM_ID', 'GP', 'POSS', 'OffRtg']].copy()

    # Calculate possessions per game
    df['POSS_PER_GAME'] = df['POSS'] / df['GP']

    # Merge passing data
    passing_cols = passing[['TEAM_ID', 'Passes Made', 'Secondary AST', 'Potential AST', 'AST To Pass%']].copy()
    passing_cols = passing_cols.rename(columns={'AST To Pass%': 'AST_To_Pass_Pct'})
    df = df.merge(passing_cols, on='TEAM_ID', how='left')

    # Calculate Passes per Possession
    df['Passes_Per_Poss'] = df['Passes Made'] / df['POSS_PER_GAME']

    # Calculate Potential AST to Pass % (shot creation rate per pass)
    df['Potential_AST_To_Pass_Pct'] = df['Potential AST'] / df['Passes Made'] * 100

    # Merge speed-distance data
    speed_cols = speed[['TEAM_ID', 'Dist. Miles Off']].copy()
    speed_cols = speed_cols.rename(columns={'Dist. Miles Off': 'Dist_Miles_Off'})
    df = df.merge(speed_cols, on='TEAM_ID', how='left')

    # Merge all 4 shot defender distance categories
    very_tight_cols = very_tight[['TEAM_ID', 'Freq%']].copy()
    very_tight_cols = very_tight_cols.rename(columns={'Freq%': 'Very_Tight_Pct'})
    df = df.merge(very_tight_cols, on='TEAM_ID', how='left')

    tight_cols = tight[['TEAM_ID', 'Freq%']].copy()
    tight_cols = tight_cols.rename(columns={'Freq%': 'Tight_Pct'})
    df = df.merge(tight_cols, on='TEAM_ID', how='left')

    open_cols = open_shots[['TEAM_ID', 'Freq%']].copy()
    open_cols = open_cols.rename(columns={'Freq%': 'Open_Pct'})
    df = df.merge(open_cols, on='TEAM_ID', how='left')

    wide_open_cols = wide_open[['TEAM_ID', 'Freq%']].copy()
    wide_open_cols = wide_open_cols.rename(columns={'Freq%': 'Wide_Open_Pct'})
    df = df.merge(wide_open_cols, on='TEAM_ID', how='left')

    # Merge scoring data (FGM %AST)
    scoring_cols = scoring[['TEAM_ID', 'FGM %AST']].copy()
    scoring_cols = scoring_cols.rename(columns={'FGM %AST': 'FGM_AST_Pct'})
    df = df.merge(scoring_cols, on='TEAM_ID', how='left')

    print(f"  Merged dataset: {len(df)} teams")

    # Define feature columns
    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct']

    # Check for missing values
    missing = df[feature_cols].isnull().sum()
    if missing.sum() > 0:
        print(f"  Warning: Missing values:\n{missing[missing > 0]}")

    return df


def train_ridge_model(df, alpha=1.0):
    """Train Ridge regression model."""
    print(f"\nTraining Ridge regression (alpha={alpha})...")

    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct']

    X = df[feature_cols].values
    y = df['OffRtg'].values

    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Train Ridge model
    model = Ridge(alpha=alpha)
    model.fit(X_scaled, y)

    # Predictions and R²
    y_pred = model.predict(X_scaled)
    r2 = model.score(X_scaled, y)

    print(f"  R² score: {r2:.4f}")

    # Feature weights (standardized)
    weights = dict(zip(feature_cols, model.coef_))
    print("\n  Feature weights (standardized):")
    for feat, w in sorted(weights.items(), key=lambda x: abs(x[1]), reverse=True):
        print(f"    {feat}: {w:+.4f}")

    return model, scaler, weights, r2, y_pred


def calculate_tci_scores(df, model, scaler, feature_cols):
    """Calculate TCI score for each team."""
    print("\nCalculating TCI scores...")

    X = df[feature_cols].values
    X_scaled = scaler.transform(X)

    # TCI = weighted sum of standardized features
    tci_scores = X_scaled @ model.coef_

    # Normalize to 0-100 scale
    tci_min, tci_max = tci_scores.min(), tci_scores.max()
    tci_normalized = (tci_scores - tci_min) / (tci_max - tci_min) * 100

    df = df.copy()
    df['TCI_Raw'] = tci_scores
    df['TCI'] = tci_normalized

    return df


def save_results(df, weights, r2, output_dir):
    """Save results to files."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save feature matrix
    feature_cols = ['TEAM', 'TEAM_ID', 'OffRtg', 'Passes_Per_Poss', 'Secondary AST',
                    'AST_To_Pass_Pct', 'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off',
                    'Very_Tight_Pct', 'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct',
                    'FGM_AST_Pct', 'TCI_Raw', 'TCI']
    df[feature_cols].to_csv(output_dir / "tci_feature_matrix.csv", index=False)
    print(f"\nSaved: {output_dir / 'tci_feature_matrix.csv'}")

    # Save model weights
    model_info = {
        "season": "2024-25",
        "r2_score": r2,
        "weights": weights,
        "feature_order": list(weights.keys()),
        "description": "TCI = sum of (standardized_feature * weight)"
    }
    with open(output_dir / "tci_model_weights.json", "w") as f:
        json.dump(model_info, f, indent=2)
    print(f"Saved: {output_dir / 'tci_model_weights.json'}")

    # Save team rankings
    rankings = df[['TEAM', 'TCI', 'OffRtg']].sort_values('TCI', ascending=False).reset_index(drop=True)
    rankings.index = rankings.index + 1  # 1-based ranking
    rankings.index.name = 'Rank'
    rankings.to_csv(output_dir / "tci_team_rankings.csv")
    print(f"Saved: {output_dir / 'tci_team_rankings.csv'}")

    return rankings


def print_rankings(rankings):
    """Print team rankings table."""
    print("\n" + "="*50)
    print("TCI Team Rankings (2024-25 Season)")
    print("="*50)
    print(f"{'Rank':<6}{'Team':<25}{'TCI':>8}{'OffRtg':>8}")
    print("-"*50)
    for rank, row in rankings.iterrows():
        print(f"{rank:<6}{row['TEAM']:<25}{row['TCI']:>8.1f}{row['OffRtg']:>8.1f}")


def main():
    """Main entry point."""
    # Load data
    advanced, scoring, passing, speed, very_tight, tight, open_shots, wide_open = load_data()

    # Build feature matrix
    df = build_feature_matrix(advanced, scoring, passing, speed, very_tight, tight, open_shots, wide_open)

    # Train model
    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct']
    model, scaler, weights, r2, y_pred = train_ridge_model(df, alpha=1.0)

    # Calculate TCI scores
    df = calculate_tci_scores(df, model, scaler, feature_cols)

    # Save results
    rankings = save_results(df, weights, r2, OUTPUT_DIR)

    # Print rankings
    print_rankings(rankings)

    print("\nDone!")


if __name__ == "__main__":
    main()
