#!/usr/bin/env python3
"""
Compare TCI rankings with actual OffRtg rankings for 2025-26 season.
"""

import pandas as pd
from pathlib import Path

# Load TCI rankings
tci_path = Path("data/analysis/tci_rankings_2025_26.csv")
df = pd.read_csv(tci_path)

# TCI Rank is already in the file as 'Rank'
df = df.rename(columns={'Rank': 'TCI_Rank'})

# Calculate actual OffRtg ranking (higher OffRtg = better rank)
df['OffRtg_Rank'] = df['OffRtg'].rank(ascending=False, method='min').astype(int)

# Calculate rank difference (positive = TCI overestimates, negative = TCI underestimates)
df['Rank_Diff'] = df['OffRtg_Rank'] - df['TCI_Rank']

# Calculate prediction error
df['Prediction_Error'] = df['OffRtg'] - df['Predicted_OffRtg']

# Mark significant deviations (|Rank_Diff| >= 5)
df['Deviation'] = df['Rank_Diff'].apply(
    lambda x: '↑↑ TCI高估' if x >= 5 else ('↓↓ TCI低估' if x <= -5 else '')
)

# Reorder columns for output
output_cols = [
    'TCI_Rank', 'OffRtg_Rank', 'Rank_Diff', 'TEAM', 'TCI', 'OffRtg',
    'Predicted_OffRtg', 'Prediction_Error', 'Deviation'
]
df_output = df[output_cols].copy()

# Round numeric columns
df_output['TCI'] = df_output['TCI'].round(1)
df_output['Predicted_OffRtg'] = df_output['Predicted_OffRtg'].round(2)
df_output['Prediction_Error'] = df_output['Prediction_Error'].round(2)

# Sort by TCI rank
df_output = df_output.sort_values('TCI_Rank')

# Save to CSV
output_path = Path("data/analysis/tci_vs_offrtg_rankings_2025_26.csv")
df_output.to_csv(output_path, index=False, encoding='utf-8-sig')

print("=" * 100)
print("2025-26 赛季 TCI 排名 vs 实际 OffRtg 排名")
print("=" * 100)
print()

# Print header
print(f"{'TCI':>4} {'OffRtg':>6} {'Diff':>5} {'球队':<25} {'TCI值':>7} {'OffRtg':>7} {'预测OffRtg':>10} {'误差':>7} {'偏离':<12}")
print("-" * 100)

for _, row in df_output.iterrows():
    diff_str = f"{row['Rank_Diff']:+d}" if row['Rank_Diff'] != 0 else "0"
    print(f"{row['TCI_Rank']:>4} {row['OffRtg_Rank']:>6} {diff_str:>5} {row['TEAM']:<25} {row['TCI']:>7.1f} {row['OffRtg']:>7.2f} {row['Predicted_OffRtg']:>10.2f} {row['Prediction_Error']:>+7.2f} {row['Deviation']:<12}")

print("-" * 100)
print()

# Summary statistics
print("统计摘要:")
print(f"  - 排名完全一致: {(df_output['Rank_Diff'] == 0).sum()} 支球队")
print(f"  - 排名差异 ≤2: {(df_output['Rank_Diff'].abs() <= 2).sum()} 支球队")
print(f"  - 排名差异 ≥5: {(df_output['Rank_Diff'].abs() >= 5).sum()} 支球队")
print(f"  - 平均排名差异: {df_output['Rank_Diff'].abs().mean():.2f}")
print(f"  - 预测 RMSE: {(df_output['Prediction_Error']**2).mean()**0.5:.2f}")
print()

# List significant deviations
deviations = df_output[df_output['Deviation'] != '']
if not deviations.empty:
    print("显著偏离的球队 (排名差异 ≥5):")
    for _, row in deviations.iterrows():
        direction = "高于" if row['Rank_Diff'] > 0 else "低于"
        print(f"  - {row['TEAM']}: TCI排名 {row['TCI_Rank']} vs OffRtg排名 {row['OffRtg_Rank']} ({direction}实际 {abs(row['Rank_Diff'])} 名)")

print()
print(f"结果已保存至: {output_path}")
