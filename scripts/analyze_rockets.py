#!/usr/bin/env python3
"""
Analyze Houston Rockets January 2026 performance.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

DATA_DIR = Path("data/newly_scraped/tracking_monthly")

TRAINING_SEASONS = {
    "2021_22": ["october", "november", "december", "january", "february", "march", "april"],
    "2022_23": ["october", "november", "december", "january", "february", "march", "april"],
    "2023_24": ["october", "november", "december", "january", "february", "march", "april"],
    "2024_25": ["october", "november", "december", "january", "february", "march", "april"],
}

feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct',
                'OREB_Pct', 'TOV_Pct', 'Mid_Range_Pct']

feature_names_cn = {
    'Passes_Per_Poss': '每回合传球数',
    'Secondary AST': '二次助攻',
    'AST_To_Pass_Pct': '传球转助攻率',
    'Potential_AST_To_Pass_Pct': '潜在助攻率',
    'Dist_Miles_Off': '进攻跑动距离',
    'Very_Tight_Pct': '极紧防守出手%',
    'Tight_Pct': '紧防守出手%',
    'Open_Pct': '开放出手%',
    'Wide_Open_Pct': '大空位出手%',
    'FGM_AST_Pct': '受助攻率',
    'OREB_Pct': '进攻篮板率',
    'TOV_Pct': '失误率',
    'Mid_Range_Pct': '中距离出手%',
}


def clean_column_names(df):
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_monthly_data(data_dir, months, season_name=""):
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
                    shooting_distance['Less_than_5ft_FGA'] + shooting_distance['5-9_ft_FGA'] +
                    shooting_distance['10-14_ft_FGA'] + shooting_distance['15-19_ft_FGA'] +
                    shooting_distance['20-24_ft_FGA'] + shooting_distance['25-29_ft_FGA']
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
            pass

    if all_data:
        return pd.concat(all_data, ignore_index=True)
    return pd.DataFrame()


def main():
    print("=" * 70)
    print("Houston Rockets - January 2026 Analysis")
    print("=" * 70)

    # Load training data
    all_train = []
    for season_name, months in TRAINING_SEASONS.items():
        data_dir = DATA_DIR / season_name
        if data_dir.exists():
            df = load_monthly_data(data_dir, months, season_name)
            if not df.empty:
                all_train.append(df)
    train_df = pd.concat(all_train, ignore_index=True)

    # Fill missing values
    feature_means = {}
    for feat in feature_cols:
        if train_df[feat].isnull().any():
            mean_val = train_df[feat].mean()
            feature_means[feat] = mean_val
            train_df[feat] = train_df[feat].fillna(mean_val)
    train_df = train_df.dropna(subset=['OffRtg'])

    # Load January 2026 data
    jan_df = load_monthly_data(DATA_DIR / "2025_26", ["january"], "2025_26")

    # Train model
    X_train = train_df[feature_cols].values
    y_train = train_df['OffRtg'].values

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = Ridge(alpha=1.0)
    model.fit(X_train_scaled, y_train)

    # Get Rockets data
    rockets = jan_df[jan_df['TEAM'] == 'Houston Rockets'].iloc[0]

    # Calculate league averages for January 2026
    league_avg = jan_df[feature_cols].mean()

    # Predict
    X_rockets = rockets[feature_cols].values.reshape(1, -1)
    X_rockets_scaled = scaler.transform(X_rockets)
    predicted = model.predict(X_rockets_scaled)[0]

    print(f"\n{'='*70}")
    print("基本信息")
    print(f"{'='*70}")
    print(f"实际 OffRtg:    {rockets['OffRtg']:.1f}")
    print(f"预测 OffRtg:    {predicted:.1f}")
    print(f"误差:           {predicted - rockets['OffRtg']:+.1f}")
    print(f"联盟排名:       {(jan_df['OffRtg'] > rockets['OffRtg']).sum() + 1}/30")

    # Feature contribution analysis
    print(f"\n{'='*70}")
    print("特征分析 (与联盟1月平均值对比)")
    print(f"{'='*70}")

    weights = dict(zip(feature_cols, model.coef_))
    contributions = []

    for feat in feature_cols:
        rockets_val = rockets[feat]
        league_val = league_avg[feat]
        diff = rockets_val - league_val
        weight = weights[feat]

        # Standardized contribution
        std = train_df[feat].std()
        contrib = (rockets_val - train_df[feat].mean()) / std * weight

        contributions.append({
            'feature': feat,
            'rockets_val': rockets_val,
            'league_avg': league_val,
            'diff': diff,
            'weight': weight,
            'contribution': contrib
        })

    # Sort by absolute contribution
    contributions.sort(key=lambda x: abs(x['contribution']), reverse=True)

    print(f"\n{'特征':<25}{'火箭':>10}{'联盟均值':>10}{'差异':>10}{'权重':>8}{'贡献':>8}")
    print("-" * 71)

    for c in contributions:
        feat_cn = feature_names_cn.get(c['feature'], c['feature'])
        diff_sign = "+" if c['diff'] > 0 else ""
        contrib_sign = "+" if c['contribution'] > 0 else ""
        print(f"{feat_cn:<22}{c['rockets_val']:>10.2f}{c['league_avg']:>10.2f}{diff_sign}{c['diff']:>9.2f}{c['weight']:>+8.2f}{contrib_sign}{c['contribution']:>7.2f}")

    # Highlight key findings
    print(f"\n{'='*70}")
    print("关键发现")
    print(f"{'='*70}")

    # Top positive contributors
    pos_contrib = [c for c in contributions if c['contribution'] > 0.3]
    if pos_contrib:
        print("\n正面贡献 (提升 OffRtg):")
        for c in pos_contrib[:3]:
            feat_cn = feature_names_cn.get(c['feature'], c['feature'])
            print(f"  - {feat_cn}: {c['rockets_val']:.1f} (联盟 {c['league_avg']:.1f})")

    # Top negative contributors
    neg_contrib = [c for c in contributions if c['contribution'] < -0.3]
    if neg_contrib:
        print("\n负面贡献 (降低 OffRtg):")
        for c in neg_contrib[:3]:
            feat_cn = feature_names_cn.get(c['feature'], c['feature'])
            print(f"  - {feat_cn}: {c['rockets_val']:.1f} (联盟 {c['league_avg']:.1f})")

    # Compare with historical Rockets data
    print(f"\n{'='*70}")
    print("火箭队历史月度数据对比 (2024-25 赛季)")
    print(f"{'='*70}")

    rockets_2024_25 = train_df[(train_df['TEAM'] == 'Houston Rockets') & (train_df['Season'] == '2024_25')]
    if not rockets_2024_25.empty:
        print(f"\n{'月份':<12}{'OffRtg':>10}{'AST_To_Pass%':>15}{'Mid_Range%':>15}{'OREB%':>10}")
        print("-" * 62)
        for _, row in rockets_2024_25.iterrows():
            print(f"{row['Month']:<12}{row['OffRtg']:>10.1f}{row['AST_To_Pass_Pct']:>15.1f}{row['Mid_Range_Pct']:>15.1f}{row['OREB_Pct']:>10.1f}")

        # Add January 2026
        print("-" * 62)
        print(f"{'january 26':<12}{rockets['OffRtg']:>10.1f}{rockets['AST_To_Pass_Pct']:>15.1f}{rockets['Mid_Range_Pct']:>15.1f}{rockets['OREB_Pct']:>10.1f}")


if __name__ == "__main__":
    main()
