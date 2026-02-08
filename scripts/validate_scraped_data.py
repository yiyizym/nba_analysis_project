#!/usr/bin/env python3
"""
NBA 数据校验模块

提供统一的数据校验功能，检测抓取数据的质量问题。

校验级别:
    - ERROR: 严重错误，数据不可用，应阻止保存
    - WARNING: 轻微问题，数据可用但需注意

使用方式:
    from validate_scraped_data import DataValidator, validate_team_stats

    # 方式1: 使用预定义的校验函数
    result = validate_team_stats(df, stat_type='four-factors')

    # 方式2: 使用校验器类
    validator = DataValidator(df)
    validator.check_row_count(expected=30)
    validator.check_required_columns(['Team', 'GP', 'W', 'L'])
    result = validator.get_result()

    if result.has_errors:
        print("数据有严重问题，不应保存")
    if result.has_warnings:
        print("数据有轻微问题")
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple, Any
from enum import Enum
import pandas as pd
import numpy as np


class Severity(Enum):
    """校验问题严重程度"""
    ERROR = "ERROR"      # 严重错误，阻止保存
    WARNING = "WARNING"  # 轻微警告，继续使用


@dataclass
class ValidationIssue:
    """单个校验问题"""
    severity: Severity
    message: str
    column: Optional[str] = None
    details: Optional[Dict] = None

    def __str__(self):
        prefix = f"[{self.severity.value}]"
        col_info = f" (列: {self.column})" if self.column else ""
        return f"{prefix} {self.message}{col_info}"


@dataclass
class ValidationResult:
    """校验结果"""
    issues: List[ValidationIssue] = field(default_factory=list)
    stats: Dict[str, Any] = field(default_factory=dict)

    @property
    def has_errors(self) -> bool:
        """是否有严重错误"""
        return any(i.severity == Severity.ERROR for i in self.issues)

    @property
    def has_warnings(self) -> bool:
        """是否有警告"""
        return any(i.severity == Severity.WARNING for i in self.issues)

    @property
    def is_valid(self) -> bool:
        """数据是否可用（无严重错误）"""
        return not self.has_errors

    @property
    def errors(self) -> List[ValidationIssue]:
        """所有错误"""
        return [i for i in self.issues if i.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[ValidationIssue]:
        """所有警告"""
        return [i for i in self.issues if i.severity == Severity.WARNING]

    def add_error(self, message: str, column: str = None, details: Dict = None):
        """添加错误"""
        self.issues.append(ValidationIssue(Severity.ERROR, message, column, details))

    def add_warning(self, message: str, column: str = None, details: Dict = None):
        """添加警告"""
        self.issues.append(ValidationIssue(Severity.WARNING, message, column, details))

    def summary(self) -> str:
        """生成摘要"""
        error_count = len(self.errors)
        warning_count = len(self.warnings)

        if error_count == 0 and warning_count == 0:
            return "✅ 数据校验通过"

        lines = []
        if error_count > 0:
            lines.append(f"❌ {error_count} 个错误")
        if warning_count > 0:
            lines.append(f"⚠️ {warning_count} 个警告")

        return " | ".join(lines)

    def print_report(self):
        """打印详细报告"""
        print("\n" + "=" * 50)
        print("数据校验报告")
        print("=" * 50)
        print(f"结果: {self.summary()}")

        if self.stats:
            print(f"\n统计信息:")
            for key, value in self.stats.items():
                print(f"  {key}: {value}")

        if self.errors:
            print(f"\n错误 ({len(self.errors)}):")
            for e in self.errors:
                print(f"  {e}")

        if self.warnings:
            print(f"\n警告 ({len(self.warnings)}):")
            for w in self.warnings:
                print(f"  {w}")

        print("=" * 50)


class DataValidator:
    """数据校验器"""

    def __init__(self, df: pd.DataFrame, stat_type: str = "unknown"):
        """
        初始化校验器

        Args:
            df: 要校验的 DataFrame
            stat_type: 数据类型 (如 'four-factors', 'advanced', 'playtype')
        """
        self.df = df
        self.stat_type = stat_type
        self.result = ValidationResult()
        self.result.stats['stat_type'] = stat_type
        self.result.stats['rows'] = len(df)
        self.result.stats['columns'] = len(df.columns)

    def check_not_empty(self) -> 'DataValidator':
        """检查 DataFrame 不为空"""
        if self.df is None or self.df.empty:
            self.result.add_error("DataFrame 为空或 None")
        return self

    def check_row_count(self, expected: int = 30, tolerance: int = 0) -> 'DataValidator':
        """
        检查行数是否符合预期

        Args:
            expected: 预期行数 (NBA 有 30 支球队)
            tolerance: 允许的误差
        """
        actual = len(self.df)
        if abs(actual - expected) > tolerance:
            if actual < expected - tolerance:
                self.result.add_error(
                    f"行数不足: 期望 {expected}，实际 {actual}",
                    details={'expected': expected, 'actual': actual}
                )
            else:
                self.result.add_warning(
                    f"行数异常: 期望 {expected}，实际 {actual}",
                    details={'expected': expected, 'actual': actual}
                )
        return self

    def check_required_columns(self, columns: List[str]) -> 'DataValidator':
        """检查必需列是否存在"""
        missing = [c for c in columns if c not in self.df.columns]
        if missing:
            self.result.add_error(
                f"缺少必需列: {missing}",
                details={'missing_columns': missing}
            )
        return self

    def check_column_types(self, type_map: Dict[str, type]) -> 'DataValidator':
        """
        检查列数据类型

        Args:
            type_map: {列名: 期望类型} 映射
        """
        for col, expected_type in type_map.items():
            if col not in self.df.columns:
                continue

            if expected_type in (int, float, 'numeric'):
                # 检查是否可以转换为数值
                try:
                    pd.to_numeric(self.df[col], errors='raise')
                except (ValueError, TypeError):
                    self.result.add_warning(
                        f"列应为数值类型，但包含非数值数据",
                        column=col
                    )
        return self

    def check_value_range(self, column: str, min_val: float = None,
                          max_val: float = None,
                          severity: Severity = Severity.WARNING) -> 'DataValidator':
        """
        检查列值是否在合理范围内

        Args:
            column: 列名
            min_val: 最小值
            max_val: 最大值
            severity: 超出范围时的严重程度
        """
        if column not in self.df.columns:
            return self

        try:
            values = pd.to_numeric(self.df[column], errors='coerce')
            actual_min = values.min()
            actual_max = values.max()

            out_of_range = []
            if min_val is not None and actual_min < min_val:
                out_of_range.append(f"最小值 {actual_min} < {min_val}")
            if max_val is not None and actual_max > max_val:
                out_of_range.append(f"最大值 {actual_max} > {max_val}")

            if out_of_range:
                message = f"值超出预期范围: {', '.join(out_of_range)}"
                if severity == Severity.ERROR:
                    self.result.add_error(message, column=column)
                else:
                    self.result.add_warning(message, column=column)

        except Exception:
            pass  # 非数值列跳过

        return self

    def check_no_nulls(self, columns: List[str],
                       severity: Severity = Severity.WARNING) -> 'DataValidator':
        """检查指定列是否有空值"""
        for col in columns:
            if col not in self.df.columns:
                continue

            null_count = self.df[col].isna().sum()
            if null_count > 0:
                message = f"列包含 {null_count} 个空值"
                if severity == Severity.ERROR:
                    self.result.add_error(message, column=col)
                else:
                    self.result.add_warning(message, column=col)
        return self

    def check_unique_teams(self, team_column: str = 'Team') -> 'DataValidator':
        """检查球队是否唯一（无重复）"""
        if team_column not in self.df.columns:
            # 尝试其他常见列名
            for alt in ['TEAM', 'team']:
                if alt in self.df.columns:
                    team_column = alt
                    break
            else:
                return self

        duplicates = self.df[team_column].duplicated().sum()
        if duplicates > 0:
            self.result.add_warning(
                f"存在 {duplicates} 个重复球队",
                column=team_column
            )
        return self

    def check_team_ids(self, id_column: str = 'TEAM_ID') -> 'DataValidator':
        """检查 TEAM_ID 是否为有效的 NBA 球队 ID"""
        if id_column not in self.df.columns:
            return self

        VALID_TEAM_IDS = {
            1610612737, 1610612738, 1610612739, 1610612740, 1610612741,
            1610612742, 1610612743, 1610612744, 1610612745, 1610612746,
            1610612747, 1610612748, 1610612749, 1610612750, 1610612751,
            1610612752, 1610612753, 1610612754, 1610612755, 1610612756,
            1610612757, 1610612758, 1610612759, 1610612760, 1610612761,
            1610612762, 1610612763, 1610612764, 1610612765, 1610612766
        }

        try:
            ids = set(self.df[id_column].dropna().astype(int))
            invalid_ids = ids - VALID_TEAM_IDS
            if invalid_ids:
                self.result.add_warning(
                    f"存在无效的 TEAM_ID: {invalid_ids}",
                    column=id_column
                )
        except (ValueError, TypeError):
            self.result.add_warning(
                "TEAM_ID 列包含非数值数据",
                column=id_column
            )
        return self

    def check_percentage_columns(self, columns: List[str]) -> 'DataValidator':
        """检查百分比列是否在 0-100 范围内"""
        for col in columns:
            self.check_value_range(col, min_val=0, max_val=100)
        return self

    def check_rate_columns(self, columns: List[str]) -> 'DataValidator':
        """检查比率列是否在 0-1 范围内"""
        for col in columns:
            self.check_value_range(col, min_val=0, max_val=1)
        return self

    def get_result(self) -> ValidationResult:
        """获取校验结果"""
        return self.result


# ============================================================================
# 预定义的校验函数
# ============================================================================

def validate_team_stats(df: pd.DataFrame, stat_type: str = 'unknown') -> ValidationResult:
    """
    校验球队统计数据

    Args:
        df: 球队统计 DataFrame
        stat_type: 数据类型

    Returns:
        ValidationResult
    """
    validator = DataValidator(df, stat_type)

    # 基础检查
    validator.check_not_empty()
    if df is None or df.empty:
        return validator.get_result()

    # 行数检查 (NBA 30 支球队)
    validator.check_row_count(expected=30, tolerance=0)

    # 根据数据类型进行特定检查
    if stat_type in ['four-factors', 'four_factors']:
        validator.check_required_columns(['Team', 'GP', 'eFG%', 'TOV%', 'OREB%'])
        validator.check_percentage_columns(['eFG%', 'TOV%', 'OREB%', 'Opp eFG%', 'Opp TOV%', 'Opp OREB%'])
        validator.check_value_range('FTA Rate', min_val=0, max_val=0.5)
        validator.check_value_range('Opp FTA Rate', min_val=0, max_val=0.5)

    elif stat_type == 'advanced':
        validator.check_required_columns(['TEAM', 'GP', 'OffRtg', 'DefRtg', 'NetRtg'])
        validator.check_value_range('OffRtg', min_val=90, max_val=130)
        validator.check_value_range('DefRtg', min_val=90, max_val=130)
        validator.check_value_range('NetRtg', min_val=-30, max_val=30)
        validator.check_value_range('PACE', min_val=85, max_val=115)

    elif stat_type.startswith('playtype'):
        validator.check_required_columns(['TEAM', 'GP', 'PPP', 'PERCENTILE'])
        validator.check_value_range('PPP', min_val=0, max_val=2.0)
        validator.check_value_range('PERCENTILE', min_val=0, max_val=100)
        validator.check_value_range('FG%', min_val=0, max_val=100)

    elif stat_type in ['defense_dash_lt6', 'defense-dash-lt6']:
        validator.check_required_columns(['Team', 'GP', 'DFG%'])
        validator.check_value_range('DFG%', min_val=30, max_val=80)

    # 通用检查
    validator.check_team_ids()
    validator.check_unique_teams()

    return validator.get_result()


def validate_live_data(df: pd.DataFrame, stat_type: str,
                       context: str = "Last 10 Games") -> ValidationResult:
    """
    校验实时抓取的数据（如 Last 10 Games）

    比离线数据校验更严格，因为实时数据更容易出错。

    Args:
        df: 实时抓取的 DataFrame
        stat_type: 数据类型
        context: 数据上下文描述

    Returns:
        ValidationResult
    """
    result = validate_team_stats(df, stat_type)
    result.stats['context'] = context

    # 额外的实时数据检查
    if df is not None and not df.empty:
        # 检查 GP (比赛场次) 是否合理
        gp_col = 'GP' if 'GP' in df.columns else None
        if gp_col:
            try:
                gp_values = pd.to_numeric(df[gp_col], errors='coerce')
                if context == "Last 10 Games":
                    # Last 10 Games 的 GP 应该是 10
                    if (gp_values != 10).any():
                        result.add_warning(
                            f"Last 10 Games 数据中 GP 不全为 10",
                            column=gp_col,
                            details={'unique_values': gp_values.unique().tolist()}
                        )
            except Exception:
                pass

    return result


def print_validation_summary(result: ValidationResult, title: str = "数据校验"):
    """打印简洁的校验摘要"""
    status = "✅" if result.is_valid else "❌"
    summary = result.summary()
    print(f"{title}: {status} {summary}")

    if result.errors:
        for e in result.errors[:3]:  # 只显示前3个错误
            print(f"  {e}")
        if len(result.errors) > 3:
            print(f"  ... 还有 {len(result.errors) - 3} 个错误")


# ============================================================================
# 命令行测试
# ============================================================================

def main():
    """命令行测试"""
    import argparse
    from pathlib import Path

    parser = argparse.ArgumentParser(description='校验 NBA 数据文件')
    parser.add_argument('file', type=str, help='CSV 文件路径')
    parser.add_argument('--type', type=str, default='unknown',
                        help='数据类型 (four-factors, advanced, playtype, etc.)')
    parser.add_argument('--verbose', '-v', action='store_true',
                        help='显示详细报告')

    args = parser.parse_args()

    filepath = Path(args.file)
    if not filepath.exists():
        print(f"文件不存在: {filepath}")
        return 1

    print(f"校验文件: {filepath}")

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        print(f"无法读取文件: {e}")
        return 1

    # 自动检测数据类型
    stat_type = args.type
    if stat_type == 'unknown':
        filename = filepath.stem.lower()
        if 'four_factors' in filename or 'four-factors' in filename:
            stat_type = 'four-factors'
        elif 'advanced' in filename:
            stat_type = 'advanced'
        elif 'playtype' in filename:
            stat_type = 'playtype'
        elif 'defense_dash' in filename:
            stat_type = 'defense_dash_lt6'

    result = validate_team_stats(df, stat_type)

    if args.verbose:
        result.print_report()
    else:
        print_validation_summary(result)

    return 0 if result.is_valid else 1


if __name__ == "__main__":
    exit(main())
