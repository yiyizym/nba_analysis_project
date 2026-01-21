#!/usr/bin/env python3
"""
Analyze FGM_AST_Pct negative weight phenomenon.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge, LinearRegression
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt

# Paths
DATA_2024_25 = Path("data/newly_scraped/tracking_monthly/2024_25")
DATA_2025_26 = Path("data/newly_scraped/tracking_monthly/2025_26")

MONTHS_2024_25 = ["october", "november", "december", "january", "february", "march", "april"]
MONTHS_2025_26 = ["october", "november", "december", "january"]


def clean_column_names(df):
    df.columns = df.columns.str.replace('\xa0', ' ')
    return df


def load_monthly_data(data_dir, months):
    all_data = []
    for month in months:
        try:
            passing = clean_column_names(pd.read_csv(data_dir / f"tracking_passing_{month}.csv"))
            speed = clean_column_names(pd.read_csv(data_dir / f"tracking_speed_distance_{month}.csv"))
            advanced = clean_column_names(pd.read_csv(data_dir / f"team_advanced_{month}.csv"))
            scoring = clean_column_names(pd.read_csv(data_dir / f"team_scoring_{month}.csv"))
            very_tight = clean_column_names(pd.read_csv(data_dir / f"shots_very_tight_{month}.csv"))
            tight = clean_column_names(pd.read_csv(data_dir / f"shots_tight_{month}.csv"))
            open_shots = clean_column_names(pd.read_csv(data_dir / f"shots_open_{month}.csv"))
            wide_open = clean_column_names(pd.read_csv(data_dir / f"shots_wide_open_{month}.csv"))

            df = advanced[['TEAM', 'TEAM_ID', 'GP', 'POSS', 'OffRtg', 'OREB%', 'TOV%']].copy()
            df['Month'] = month
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
                cols = data[['TEAM_ID', 'Freq%']].copy()
                cols = cols.rename(columns={'Freq%': col_name})
                df = df.merge(cols, on='TEAM_ID', how='left')

            scoring_cols = scoring[['TEAM_ID', 'FGM %AST']].copy()
            scoring_cols = scoring_cols.rename(columns={'FGM %AST': 'FGM_AST_Pct'})
            df = df.merge(scoring_cols, on='TEAM_ID', how='left')

            all_data.append(df)
        except Exception as e:
            pass

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def main():
    print("=" * 70)
    print("FGM_AST_Pct 负权重分析")
    print("=" * 70)

    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct',
                    'OREB_Pct', 'TOV_Pct']

    # Load data
    print("\n加载数据...")
    train_df = load_monthly_data(DATA_2024_25, MONTHS_2024_25)
    val_df = load_monthly_data(DATA_2025_26, MONTHS_2025_26)
    all_df = pd.concat([train_df, val_df], ignore_index=True)
    all_df = all_df.dropna(subset=feature_cols + ['OffRtg'])
    print(f"样本数: {len(all_df)}")

    # 1. Simple correlation
    print("\n" + "=" * 70)
    print("1. FGM_AST_Pct 与 OffRtg 的简单相关性")
    print("=" * 70)
    simple_corr = all_df['FGM_AST_Pct'].corr(all_df['OffRtg'])
    print(f"   相关系数: {simple_corr:.4f}")

    if simple_corr > 0:
        print("   → 单独看，FGM_AST_Pct 与 OffRtg 是正相关的！")
    else:
        print("   → 单独看，FGM_AST_Pct 与 OffRtg 是负相关的")

    # 2. Correlation with other features
    print("\n" + "=" * 70)
    print("2. FGM_AST_Pct 与其他特征的相关性 (多重共线性检查)")
    print("=" * 70)

    correlations = []
    for feat in feature_cols:
        if feat != 'FGM_AST_Pct':
            corr = all_df['FGM_AST_Pct'].corr(all_df[feat])
            correlations.append((feat, corr))

    correlations.sort(key=lambda x: abs(x[1]), reverse=True)
    print(f"\n{'特征':<35} {'与 FGM_AST_Pct 的相关性':>20}")
    print("-" * 60)
    for feat, corr in correlations:
        flag = " *** 高度相关" if abs(corr) > 0.5 else ""
        print(f"   {feat:<30} {corr:>+.4f}{flag}")

    # 3. Single feature regression vs multi-feature regression
    print("\n" + "=" * 70)
    print("3. 单特征回归 vs 多特征回归")
    print("=" * 70)

    # Single feature
    X_single = all_df[['FGM_AST_Pct']].values
    y = all_df['OffRtg'].values

    scaler_single = StandardScaler()
    X_single_scaled = scaler_single.fit_transform(X_single)

    model_single = LinearRegression()
    model_single.fit(X_single_scaled, y)

    print(f"\n   单特征回归 (只用 FGM_AST_Pct):")
    print(f"   权重: {model_single.coef_[0]:+.4f}")
    print(f"   R²: {model_single.score(X_single_scaled, y):.4f}")

    # Multi feature
    X_multi = all_df[feature_cols].values
    scaler_multi = StandardScaler()
    X_multi_scaled = scaler_multi.fit_transform(X_multi)

    model_multi = Ridge(alpha=1.0)
    model_multi.fit(X_multi_scaled, y)

    fgm_idx = feature_cols.index('FGM_AST_Pct')
    print(f"\n   多特征回归 (12 个特征):")
    print(f"   FGM_AST_Pct 权重: {model_multi.coef_[fgm_idx]:+.4f}")
    print(f"   R²: {model_multi.score(X_multi_scaled, y):.4f}")

    # 4. Explanation
    print("\n" + "=" * 70)
    print("4. 解释")
    print("=" * 70)

    # Find correlation with AST_To_Pass_Pct
    corr_with_ast = all_df['FGM_AST_Pct'].corr(all_df['AST_To_Pass_Pct'])

    print(f"""
   FGM_AST_Pct (受助攻率) = 进球中来自助攻的比例
   AST_To_Pass_Pct (传球转助攻率) = 传球转化为助攻的比例

   这两个变量的相关性: {corr_with_ast:.4f}

   多元回归中的权重含义:
   "控制其他变量不变时，该变量对目标的边际效应"

   可能的解释:
   1. 当 AST_To_Pass_Pct（传球转助攻率）已经很高时，
      FGM_AST_Pct（受助攻率）继续升高可能意味着:
      - 球队过度依赖配合，缺乏个人得分能力
      - 进攻模式单一，容易被针对

   2. 高效球队往往有多样化进攻:
      - 既有团队配合 (AST_To_Pass_Pct 高)
      - 也有个人单打 (FGM_AST_Pct 不一定最高)
""")

    # 5. Visualize
    print("\n生成可视化...")

    fig, axes = plt.subplots(1, 3, figsize=(15, 5))

    # Plot 1: FGM_AST_Pct vs OffRtg
    ax = axes[0]
    ax.scatter(all_df['FGM_AST_Pct'], all_df['OffRtg'], alpha=0.5)
    z = np.polyfit(all_df['FGM_AST_Pct'], all_df['OffRtg'], 1)
    p = np.poly1d(z)
    x_line = np.linspace(all_df['FGM_AST_Pct'].min(), all_df['FGM_AST_Pct'].max(), 100)
    ax.plot(x_line, p(x_line), 'r-', linewidth=2, label=f'r={simple_corr:.3f}')
    ax.set_xlabel('FGM_AST_Pct (受助攻率)')
    ax.set_ylabel('OffRtg')
    ax.set_title('简单相关: FGM_AST_Pct vs OffRtg')
    ax.legend()

    # Plot 2: FGM_AST_Pct vs AST_To_Pass_Pct
    ax = axes[1]
    ax.scatter(all_df['FGM_AST_Pct'], all_df['AST_To_Pass_Pct'], alpha=0.5)
    ax.set_xlabel('FGM_AST_Pct (受助攻率)')
    ax.set_ylabel('AST_To_Pass_Pct (传球转助攻率)')
    ax.set_title(f'多重共线性: r={corr_with_ast:.3f}')

    # Plot 3: Compare weights
    ax = axes[2]
    features_to_show = ['AST_To_Pass_Pct', 'Passes_Per_Poss', 'FGM_AST_Pct', 'OREB_Pct', 'TOV_Pct']
    weights = [model_multi.coef_[feature_cols.index(f)] for f in features_to_show]
    colors = ['green' if w > 0 else 'red' for w in weights]
    ax.barh(features_to_show, weights, color=colors)
    ax.axvline(x=0, color='black', linestyle='-')
    ax.set_xlabel('权重 (标准化)')
    ax.set_title('多元回归权重')

    plt.tight_layout()
    plt.savefig('data/analysis/fgm_ast_pct_analysis.png', dpi=150, bbox_inches='tight')
    print("   保存至: data/analysis/fgm_ast_pct_analysis.png")

    plt.show()


if __name__ == "__main__":
    main()
