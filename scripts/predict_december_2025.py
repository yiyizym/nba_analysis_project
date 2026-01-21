#!/usr/bin/env python3
"""
Predict December 2025 OffRtg using TCI model and compare with actual values.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

# Paths
DATA_2024_25 = Path("data/newly_scraped/tracking_monthly/2024_25")
DATA_2025_26 = Path("data/newly_scraped/tracking_monthly/2025_26")
OUTPUT_DIR = Path("data/analysis")

MONTHS_2024_25 = ["october", "november", "december", "january", "february", "march", "april"]


def clean_column_names(df):
    """Replace non-breaking spaces."""
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_month_data(data_dir, month):
    """Load data for a single month."""
    passing = clean_column_names(pd.read_csv(data_dir / f"tracking_passing_{month}.csv"))
    speed = clean_column_names(pd.read_csv(data_dir / f"tracking_speed_distance_{month}.csv"))
    advanced = clean_column_names(pd.read_csv(data_dir / f"team_advanced_{month}.csv"))
    scoring = clean_column_names(pd.read_csv(data_dir / f"team_scoring_{month}.csv"))
    very_tight = clean_column_names(pd.read_csv(data_dir / f"shots_very_tight_{month}.csv"))
    tight = clean_column_names(pd.read_csv(data_dir / f"shots_tight_{month}.csv"))
    open_shots = clean_column_names(pd.read_csv(data_dir / f"shots_open_{month}.csv"))
    wide_open = clean_column_names(pd.read_csv(data_dir / f"shots_wide_open_{month}.csv"))

    # Build feature matrix
    df = advanced[['TEAM', 'TEAM_ID', 'GP', 'POSS', 'OffRtg']].copy()
    df['Month'] = month
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


def load_all_months(data_dir, months):
    """Load and combine multiple months."""
    all_data = []
    for month in months:
        try:
            df = load_month_data(data_dir, month)
            all_data.append(df)
        except Exception as e:
            print(f"  Error loading {month}: {e}")
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def main():
    print("=" * 80)
    print("TCI Model: December 2025 Prediction vs Actual")
    print("=" * 80)

    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct']

    # Step 1: Train model on 2024-25 data
    print("\n1. Training model on 2024-25 season data...")
    train_df = load_all_months(DATA_2024_25, MONTHS_2024_25)
    train_df = train_df.dropna(subset=feature_cols + ['OffRtg'])
    print(f"   Training samples: {len(train_df)}")

    X_train = train_df[feature_cols].values
    y_train = train_df['OffRtg'].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = Ridge(alpha=1.0)
    model.fit(X_train_scaled, y_train)
    print(f"   Training R²: {model.score(X_train_scaled, y_train):.4f}")

    # Step 2: Load December 2025 data only
    print("\n2. Loading December 2025 data...")
    dec_df = load_month_data(DATA_2025_26, "december")
    dec_df = dec_df.dropna(subset=feature_cols + ['OffRtg'])
    print(f"   December samples: {len(dec_df)}")

    # Step 3: Predict
    print("\n3. Predicting December 2025 OffRtg...")
    X_dec = dec_df[feature_cols].values
    X_dec_scaled = scaler.transform(X_dec)
    dec_df['Predicted_OffRtg'] = model.predict(X_dec_scaled)

    # Step 4: Calculate metrics
    dec_df['Error'] = dec_df['OffRtg'] - dec_df['Predicted_OffRtg']
    dec_df['Abs_Error'] = dec_df['Error'].abs()

    # Rankings
    dec_df['Actual_Rank'] = dec_df['OffRtg'].rank(ascending=False, method='min').astype(int)
    dec_df['Predicted_Rank'] = dec_df['Predicted_OffRtg'].rank(ascending=False, method='min').astype(int)
    dec_df['Rank_Diff'] = dec_df['Actual_Rank'] - dec_df['Predicted_Rank']

    # Sort by actual OffRtg
    dec_df = dec_df.sort_values('OffRtg', ascending=False)

    # Calculate R² for December
    ss_res = ((dec_df['OffRtg'] - dec_df['Predicted_OffRtg']) ** 2).sum()
    ss_tot = ((dec_df['OffRtg'] - dec_df['OffRtg'].mean()) ** 2).sum()
    r2_dec = 1 - ss_res / ss_tot
    rmse_dec = np.sqrt((dec_df['Error'] ** 2).mean())
    mae_dec = dec_df['Abs_Error'].mean()

    print(f"\n   December 2025 R²:   {r2_dec:.4f}")
    print(f"   December 2025 RMSE: {rmse_dec:.2f}")
    print(f"   December 2025 MAE:  {mae_dec:.2f}")

    # Step 5: Display results
    print("\n" + "=" * 80)
    print("December 2025: Actual OffRtg vs Predicted OffRtg")
    print("=" * 80)
    print(f"{'实际':>4} {'预测':>4} {'Diff':>5}  {'球队':<25} {'实际OffRtg':>10} {'预测OffRtg':>10} {'误差':>8}")
    print("-" * 80)

    for _, row in dec_df.iterrows():
        rank_diff = int(row['Rank_Diff'])
        diff_str = f"{rank_diff:+d}" if rank_diff != 0 else "0"

        # Mark large deviations
        marker = ""
        if abs(rank_diff) >= 5:
            marker = " ***"
        elif abs(rank_diff) >= 3:
            marker = " *"

        print(f"{int(row['Actual_Rank']):>4} {int(row['Predicted_Rank']):>4} {diff_str:>5}  {row['TEAM']:<25} {row['OffRtg']:>10.2f} {row['Predicted_OffRtg']:>10.2f} {row['Error']:>+8.2f}{marker}")

    print("-" * 80)

    # Step 6: Summary
    print("\n统计摘要:")
    print(f"  - R² (模型解释力): {r2_dec:.4f}")
    print(f"  - RMSE (均方根误差): {rmse_dec:.2f}")
    print(f"  - MAE (平均绝对误差): {mae_dec:.2f}")
    print(f"  - 排名完全一致: {(dec_df['Rank_Diff'] == 0).sum()} 支球队")
    print(f"  - 排名差异 ≤2: {(dec_df['Rank_Diff'].abs() <= 2).sum()} 支球队")
    print(f"  - 排名差异 ≥5: {(dec_df['Rank_Diff'].abs() >= 5).sum()} 支球队")

    # Step 7: Save to CSV
    output_cols = ['Actual_Rank', 'Predicted_Rank', 'Rank_Diff', 'TEAM', 'OffRtg',
                   'Predicted_OffRtg', 'Error', 'GP']
    output_df = dec_df[output_cols].copy()
    output_df = output_df.round({'OffRtg': 2, 'Predicted_OffRtg': 2, 'Error': 2})

    output_path = OUTPUT_DIR / "december_2025_prediction.csv"
    output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n结果已保存至: {output_path}")

    # Step 8: Show largest errors
    print("\n" + "=" * 80)
    print("误差最大的球队 (|Error| > 3):")
    print("=" * 80)
    large_errors = dec_df[dec_df['Abs_Error'] > 3].sort_values('Abs_Error', ascending=False)
    for _, row in large_errors.iterrows():
        direction = "高估" if row['Error'] < 0 else "低估"
        print(f"  - {row['TEAM']}: 实际 {row['OffRtg']:.1f}, 预测 {row['Predicted_OffRtg']:.1f} ({direction} {abs(row['Error']):.1f})")


if __name__ == "__main__":
    main()
