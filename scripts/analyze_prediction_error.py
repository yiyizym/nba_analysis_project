#!/usr/bin/env python3
"""
Analyze prediction error patterns in December 2025 data.
Focus on relationship between actual OffRtg and prediction error.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from scipy import stats

# Paths
DATA_2024_25 = Path("data/newly_scraped/tracking_monthly/2024_25")
DATA_2025_26 = Path("data/newly_scraped/tracking_monthly/2025_26")
OUTPUT_DIR = Path("data/analysis")

MONTHS_2024_25 = ["october", "november", "december", "january", "february", "march", "april"]


def clean_column_names(df):
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_month_data(data_dir, month):
    passing = clean_column_names(pd.read_csv(data_dir / f"tracking_passing_{month}.csv"))
    speed = clean_column_names(pd.read_csv(data_dir / f"tracking_speed_distance_{month}.csv"))
    advanced = clean_column_names(pd.read_csv(data_dir / f"team_advanced_{month}.csv"))
    scoring = clean_column_names(pd.read_csv(data_dir / f"team_scoring_{month}.csv"))
    very_tight = clean_column_names(pd.read_csv(data_dir / f"shots_very_tight_{month}.csv"))
    tight = clean_column_names(pd.read_csv(data_dir / f"shots_tight_{month}.csv"))
    open_shots = clean_column_names(pd.read_csv(data_dir / f"shots_open_{month}.csv"))
    wide_open = clean_column_names(pd.read_csv(data_dir / f"shots_wide_open_{month}.csv"))

    df = advanced[['TEAM', 'TEAM_ID', 'GP', 'POSS', 'OffRtg']].copy()
    df['Month'] = month
    df['POSS_PER_GAME'] = df['POSS'] / df['GP']

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
        cols = data[['TEAM_ID', 'Freq%']].copy()
        cols = cols.rename(columns={'Freq%': col_name})
        df = df.merge(cols, on='TEAM_ID', how='left')

    scoring_cols = scoring[['TEAM_ID', 'FGM %AST']].copy()
    scoring_cols = scoring_cols.rename(columns={'FGM %AST': 'FGM_AST_Pct'})
    df = df.merge(scoring_cols, on='TEAM_ID', how='left')

    return df


def load_all_months(data_dir, months):
    all_data = []
    for month in months:
        try:
            df = load_month_data(data_dir, month)
            all_data.append(df)
        except Exception as e:
            print(f"  Error loading {month}: {e}")
    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def main():
    print("=" * 90)
    print("TCI 模型预测误差分析 - 2025 年 12 月")
    print("=" * 90)

    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct']

    # Train model
    print("\n训练模型 (2024-25 数据)...")
    train_df = load_all_months(DATA_2024_25, MONTHS_2024_25)
    train_df = train_df.dropna(subset=feature_cols + ['OffRtg'])

    X_train = train_df[feature_cols].values
    y_train = train_df['OffRtg'].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = Ridge(alpha=1.0)
    model.fit(X_train_scaled, y_train)

    # Load December 2025
    print("加载 2025 年 12 月数据...")
    dec_df = load_month_data(DATA_2025_26, "december")
    dec_df = dec_df.dropna(subset=feature_cols + ['OffRtg'])

    X_dec = dec_df[feature_cols].values
    X_dec_scaled = scaler.transform(X_dec)
    dec_df['Predicted_OffRtg'] = model.predict(X_dec_scaled)

    # Error = Actual - Predicted (正值表示低估，负值表示高估)
    dec_df['Error'] = dec_df['OffRtg'] - dec_df['Predicted_OffRtg']

    # Sort by actual OffRtg (descending)
    dec_df = dec_df.sort_values('OffRtg', ascending=False).reset_index(drop=True)

    # Display results
    print("\n" + "=" * 90)
    print("按实际 OffRtg 排序 (高 → 低)")
    print("误差 = 实际 OffRtg - 预测 OffRtg")
    print("正值 = TCI 低估 (实际比预测好)，负值 = TCI 高估 (实际比预测差)")
    print("=" * 90)
    print(f"{'#':>2} {'球队':<25} {'实际OffRtg':>10} {'预测OffRtg':>10} {'误差':>8} {'说明':<15}")
    print("-" * 90)

    for i, row in dec_df.iterrows():
        idx = dec_df.index.get_loc(i) + 1
        error = row['Error']

        if error > 3:
            desc = "严重低估"
        elif error > 1.5:
            desc = "低估"
        elif error < -3:
            desc = "严重高估"
        elif error < -1.5:
            desc = "高估"
        else:
            desc = "准确"

        print(f"{idx:>2} {row['TEAM']:<25} {row['OffRtg']:>10.2f} {row['Predicted_OffRtg']:>10.2f} {error:>+8.2f} {desc:<15}")

    print("-" * 90)

    # Correlation analysis
    print("\n" + "=" * 90)
    print("误差模式分析")
    print("=" * 90)

    correlation = dec_df['OffRtg'].corr(dec_df['Error'])
    slope, intercept, r_value, p_value, std_err = stats.linregress(dec_df['OffRtg'], dec_df['Error'])

    print(f"\n实际 OffRtg 与 误差 的相关性: {correlation:.4f}")
    print(f"线性回归: Error = {slope:.4f} × OffRtg + {intercept:.2f}")
    print(f"R² = {r_value**2:.4f}, p-value = {p_value:.4f}")

    if correlation > 0.3:
        print("\n结论: OffRtg 越高，误差越大 (正相关)")
        print("       → TCI 倾向于【低估】高效率球队")
    elif correlation < -0.3:
        print("\n结论: OffRtg 越高，误差越小 (负相关)")
        print("       → TCI 倾向于【高估】高效率球队")
    else:
        print("\n结论: OffRtg 与误差相关性较弱")

    # Group analysis
    print("\n" + "-" * 90)
    print("分组分析:")
    print("-" * 90)

    # Top 10, Middle 10, Bottom 10
    top_10 = dec_df.head(10)
    mid_10 = dec_df.iloc[10:20]
    bot_10 = dec_df.tail(10)

    print(f"\n{'分组':<15} {'平均实际OffRtg':>15} {'平均预测OffRtg':>15} {'平均误差':>12} {'说明':<20}")
    print("-" * 80)

    for name, group in [("Top 10 (高效)", top_10), ("Mid 10 (中等)", mid_10), ("Bot 10 (低效)", bot_10)]:
        avg_actual = group['OffRtg'].mean()
        avg_pred = group['Predicted_OffRtg'].mean()
        avg_error = group['Error'].mean()

        if avg_error > 1:
            desc = "TCI 低估"
        elif avg_error < -1:
            desc = "TCI 高估"
        else:
            desc = "TCI 准确"

        print(f"{name:<15} {avg_actual:>15.2f} {avg_pred:>15.2f} {avg_error:>+12.2f} {desc:<20}")

    # Regression to mean analysis
    print("\n" + "-" * 90)
    print("回归到均值分析:")
    print("-" * 90)

    overall_mean = dec_df['OffRtg'].mean()
    print(f"\n12 月 OffRtg 均值: {overall_mean:.2f}")

    above_mean = dec_df[dec_df['OffRtg'] > overall_mean]
    below_mean = dec_df[dec_df['OffRtg'] <= overall_mean]

    print(f"\n高于均值的球队 ({len(above_mean)} 支):")
    print(f"  平均实际 OffRtg: {above_mean['OffRtg'].mean():.2f}")
    print(f"  平均预测 OffRtg: {above_mean['Predicted_OffRtg'].mean():.2f}")
    print(f"  平均误差: {above_mean['Error'].mean():+.2f} (TCI {'低估' if above_mean['Error'].mean() > 0 else '高估'})")

    print(f"\n低于均值的球队 ({len(below_mean)} 支):")
    print(f"  平均实际 OffRtg: {below_mean['OffRtg'].mean():.2f}")
    print(f"  平均预测 OffRtg: {below_mean['Predicted_OffRtg'].mean():.2f}")
    print(f"  平均误差: {below_mean['Error'].mean():+.2f} (TCI {'低估' if below_mean['Error'].mean() > 0 else '高估'})")

    # Save detailed results
    output_df = dec_df[['TEAM', 'OffRtg', 'Predicted_OffRtg', 'Error']].copy()
    output_df = output_df.round(2)
    output_path = OUTPUT_DIR / "december_2025_error_analysis.csv"
    output_df.to_csv(output_path, index=False, encoding='utf-8-sig')
    print(f"\n结果已保存至: {output_path}")


if __name__ == "__main__":
    main()
