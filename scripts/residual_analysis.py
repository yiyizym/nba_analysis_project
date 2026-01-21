#!/usr/bin/env python3
"""
Residual Analysis for TCI Model.
Check for non-linear relationships between features and OffRtg.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import matplotlib.pyplot as plt
from scipy import stats

# Paths
DATA_2024_25 = Path("data/newly_scraped/tracking_monthly/2024_25")
DATA_2025_26 = Path("data/newly_scraped/tracking_monthly/2025_26")
OUTPUT_DIR = Path("data/analysis")

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
            print(f"  Error loading {month}: {e}")

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def main():
    print("=" * 70)
    print("Residual Analysis for TCI Model")
    print("=" * 70)

    feature_cols = ['Passes_Per_Poss', 'Secondary AST', 'AST_To_Pass_Pct',
                    'Potential_AST_To_Pass_Pct', 'Dist_Miles_Off', 'Very_Tight_Pct',
                    'Tight_Pct', 'Open_Pct', 'Wide_Open_Pct', 'FGM_AST_Pct',
                    'OREB_Pct', 'TOV_Pct']

    # Load all data
    print("\nLoading data...")
    train_df = load_monthly_data(DATA_2024_25, MONTHS_2024_25)
    val_df = load_monthly_data(DATA_2025_26, MONTHS_2025_26)

    # Combine for analysis
    all_df = pd.concat([train_df, val_df], ignore_index=True)
    all_df = all_df.dropna(subset=feature_cols + ['OffRtg'])
    print(f"Total samples: {len(all_df)}")

    # Train model
    X = all_df[feature_cols].values
    y = all_df['OffRtg'].values

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = Ridge(alpha=1.0)
    model.fit(X_scaled, y)

    # Calculate residuals
    y_pred = model.predict(X_scaled)
    residuals = y - y_pred
    all_df['Predicted'] = y_pred
    all_df['Residual'] = residuals

    print(f"\nModel R²: {model.score(X_scaled, y):.4f}")
    print(f"Residual mean: {residuals.mean():.4f}")
    print(f"Residual std: {residuals.std():.4f}")

    # Create residual plots
    fig, axes = plt.subplots(4, 4, figsize=(16, 14))
    axes = axes.flatten()

    # Plot 1: Residuals vs Predicted (most important)
    ax = axes[0]
    ax.scatter(y_pred, residuals, alpha=0.5, s=20)
    ax.axhline(y=0, color='r', linestyle='--')
    ax.set_xlabel('Predicted OffRtg')
    ax.set_ylabel('Residual')
    ax.set_title('Residuals vs Predicted')

    # Add LOWESS trend line
    from statsmodels.nonparametric.smoothers_lowess import lowess
    sorted_idx = np.argsort(y_pred)
    lowess_result = lowess(residuals[sorted_idx], y_pred[sorted_idx], frac=0.3)
    ax.plot(lowess_result[:, 0], lowess_result[:, 1], 'g-', linewidth=2, label='LOWESS')
    ax.legend()

    # Plot 2: Q-Q plot for normality check
    ax = axes[1]
    stats.probplot(residuals, dist="norm", plot=ax)
    ax.set_title('Q-Q Plot (Normality Check)')

    # Plot 3: Histogram of residuals
    ax = axes[2]
    ax.hist(residuals, bins=30, edgecolor='black', alpha=0.7)
    ax.axvline(x=0, color='r', linestyle='--')
    ax.set_xlabel('Residual')
    ax.set_ylabel('Frequency')
    ax.set_title('Residual Distribution')

    # Plots 4-15: Residuals vs each feature
    for i, feat in enumerate(feature_cols):
        ax = axes[i + 3]
        x_feat = all_df[feat].values
        ax.scatter(x_feat, residuals, alpha=0.5, s=20)
        ax.axhline(y=0, color='r', linestyle='--')
        ax.set_xlabel(feat)
        ax.set_ylabel('Residual')
        ax.set_title(f'Residuals vs {feat}')

        # Add LOWESS trend line
        sorted_idx = np.argsort(x_feat)
        try:
            lowess_result = lowess(residuals[sorted_idx], x_feat[sorted_idx], frac=0.3)
            ax.plot(lowess_result[:, 0], lowess_result[:, 1], 'g-', linewidth=2)
        except:
            pass

        # Calculate correlation between feature and residual
        corr = np.corrcoef(x_feat, residuals)[0, 1]
        ax.text(0.05, 0.95, f'r={corr:.3f}', transform=ax.transAxes,
                fontsize=9, verticalalignment='top')

    # Hide unused subplot
    axes[15].axis('off')

    plt.tight_layout()

    # Save plot
    output_path = OUTPUT_DIR / "residual_plots.png"
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"\nSaved: {output_path}")

    # Print correlation analysis
    print("\n" + "=" * 70)
    print("Residual Correlation Analysis")
    print("=" * 70)
    print("\nCorrelation between Residuals and Features:")
    print("(Non-zero correlation may indicate non-linear relationship)")
    print("-" * 50)

    correlations = []
    for feat in feature_cols:
        corr = np.corrcoef(all_df[feat].values, residuals)[0, 1]
        correlations.append((feat, corr))

    # Sort by absolute correlation
    correlations.sort(key=lambda x: abs(x[1]), reverse=True)

    for feat, corr in correlations:
        flag = " ***" if abs(corr) > 0.1 else ""
        print(f"  {feat:<30} r = {corr:+.4f}{flag}")

    print("\n*** = |r| > 0.1 (potential non-linear relationship)")

    # Shapiro-Wilk test for normality
    print("\n" + "-" * 50)
    print("Normality Test (Shapiro-Wilk):")
    stat, p_value = stats.shapiro(residuals[:500])  # Use subset for large samples
    print(f"  Statistic: {stat:.4f}")
    print(f"  p-value: {p_value:.4f}")
    if p_value < 0.05:
        print("  → Residuals are NOT normally distributed (p < 0.05)")
    else:
        print("  → Residuals appear normally distributed (p >= 0.05)")

    plt.show()


if __name__ == "__main__":
    main()
