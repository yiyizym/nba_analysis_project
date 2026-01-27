# 脚本使用指南

本文档记录了项目中所有脚本的用途和使用方法。

## 运行环境准备

所有 Python 脚本都需要先激活虚拟环境并设置 PYTHONPATH：

```bash
cd /path/to/nba_analysis_project
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
```

---

## 快速开始：一键抓取

**推荐使用 `scrape_latest.py`**，它可以一次性抓取所有数据：

```bash
# 抓取上个月的所有数据（球队 + 球员）
python scripts/scrape_latest.py

# 抓取整个赛季的数据
python scripts/scrape_latest.py --season

# 只抓取球队数据
python scripts/scrape_latest.py --team-only

# 只抓取球员数据
python scripts/scrape_latest.py --player-only

# 指定赛季和月份
python scripts/scrape_latest.py --year 2025-26 --month january
```

### 定时任务设置 (cron)

```bash
# 每月 2 日凌晨 3 点自动抓取上个月数据
0 3 2 * * cd /path/to/nba_analysis_project && source .venv/bin/activate && PYTHONPATH="${PYTHONPATH}:$(pwd)/src" python scripts/scrape_latest.py >> logs/scrape.log 2>&1
```

---

## 一、数据抓取脚本

### 1.1 球队数据抓取

| 脚本 | 用途 | 输出目录 |
|------|------|----------|
| `scrape_monthly_data.py` | 抓取球队月度基础统计 (traditional, advanced) | `data/newly_scraped/tracking_monthly/` |
| `scrape_four_factors_monthly.py` | 抓取球队 Four Factors 数据 | `data/newly_scraped/tracking_monthly/` |
| `scrape_playtype_monthly.py` | 抓取球队 PlayType 数据 (11种战术) | `data/newly_scraped/tracking_monthly/` |
| `scrape_shooting_distance_monthly.py` | 抓取球队投篮距离分布 | `data/newly_scraped/tracking_monthly/` |
| `scrape_defense_monthly.py` | 抓取球队防守数据 | `data/newly_scraped/tracking_monthly/` |
| `scrape_home_away_monthly.py` | 抓取球队主客场数据 | `data/newly_scraped/tracking_monthly/` |
| `scrape_historical_monthly.py` | 批量抓取历史赛季月度数据 | `data/newly_scraped/tracking_monthly/` |
| `scrape_january_2026.py` | 专门抓取 2026 年 1 月数据 | `data/newly_scraped/tracking_monthly/` |
| `scrape_2025_26_season.py` | 抓取 2025-26 赛季数据 | `data/newly_scraped/tracking_monthly/` |

**使用示例：**
```bash
python scripts/scrape_monthly_data.py
python scripts/scrape_four_factors_monthly.py
```

### 1.2 球员数据抓取

| 脚本 | 用途 | 输出目录 |
|------|------|----------|
| `scrape_player_stats_monthly.py` | 球员 Traditional + Advanced 统计 | `data/newly_scraped/player_monthly/` |
| `scrape_player_bio.py` | 球员身高、体重、位置 | `data/newly_scraped/player_monthly/` |
| `scrape_player_tracking_monthly.py` | 球员 Touches、Time of Poss 等 | `data/newly_scraped/player_monthly/` |
| `scrape_player_playtype_monthly.py` | 球员 11 种 PlayType 数据 | `data/newly_scraped/player_monthly/` |
| `scrape_player_shooting_monthly.py` | 球员投篮区域分布 | `data/newly_scraped/player_monthly/` |
| `scrape_player_defense_monthly.py` | 球员防守数据 | `data/newly_scraped/player_monthly/` |
| `scrape_player_scoring_monthly.py` | 球员 Scoring 数据 (FGM %UAST) | `data/newly_scraped/player_monthly/` |
| `run_all_player_scrapers.sh` | **一键运行所有球员抓取脚本** | - |

**使用示例：**
```bash
# 一键抓取所有球员数据
./scripts/run_all_player_scrapers.sh

# 或单独运行
python scripts/scrape_player_stats_monthly.py
python scripts/scrape_player_playtype_monthly.py
```

### 1.3 其他数据抓取

| 脚本 | 用途 | 输出目录 |
|------|------|----------|
| `scrape_coaches.py` | 抓取教练信息 | `data/newly_scraped/` |
| `scrape_leverage.py` | 抓取 Leverage 数据 (前 50) | `data/newly_scraped/` |
| `scrape_leverage_full.py` | 抓取完整 Leverage 数据 | `data/newly_scraped/` |
| `scrape_tight_shots.py` | 抓取紧逼防守投篮数据 | `data/newly_scraped/` |
| `scrape_tracking_stats.py` | 抓取球员追踪数据 | `data/newly_scraped/` |
| `scrape_team_schedules.py` | 抓取球队赛程（用于对阵分析） | `data/schedules/` |

---

## 二、模型构建脚本

### 2.1 进攻模型 (TCI - Team Contribution Index)

| 脚本 | 用途 | 输出 |
|------|------|------|
| `build_tci_model.py` | 构建赛季级别 TCI 模型 | `data/analysis/tci_model.json` |
| `build_tci_model_monthly.py` | 构建月度 TCI 模型 (推荐) | `data/analysis/tci_model_monthly.json` |
| `validate_tci_model.py` | 验证 TCI 模型性能 | 控制台输出 |

**使用示例：**
```bash
python scripts/build_tci_model_monthly.py
```

### 2.2 防守模型 (DefRtg)

| 脚本 | 用途 | 输出 |
|------|------|------|
| `build_defrtg_model_monthly.py` | 构建月度 DefRtg 模型 | `data/analysis/defrtg_model_monthly.json` |

**使用示例：**
```bash
python scripts/build_defrtg_model_monthly.py
```

### 2.3 球员分类模型

| 脚本 | 用途 | 输出 |
|------|------|------|
| `build_player_features_monthly.py` | 合并球员特征矩阵 | `data/analysis/player_features_*.csv` |
| `classify_players.py` | 将球员分类为 10 种 archetype | `data/analysis/player_classification_*.csv` |

**使用示例：**
```bash
# 先构建特征，再分类
python scripts/build_player_features_monthly.py
python scripts/classify_players.py
```

---

## 三、分析脚本

### 3.1 比赛对阵分析

| 脚本 | 用途 | 输出 |
|------|------|------|
| `analyze_matchup.py` | 两队对阵博弈分析 | 控制台/JSON |
| `scrape_team_schedules.py` | 抓取球队赛程（用于休息天数计算） | `data/schedules/` |

**`analyze_matchup.py` 详细用法：**

```bash
# 基础分析（使用本地月度数据）
python scripts/analyze_matchup.py HOU LAL

# 启用实时 Last 10 Games 数据抓取
python scripts/analyze_matchup.py HOU LAL --live

# 指定分析月份
python scripts/analyze_matchup.py HOU LAL --month december

# 标记缺阵球员（支持多人）
python scripts/analyze_matchup.py HOU LAL --out "LeBron James"
python scripts/analyze_matchup.py HOU LAL --out "LeBron James,Anthony Davis"

# 指定比赛日期（用于休息天数计算）
python scripts/analyze_matchup.py HOU LAL --live --date 2026-01-28

# JSON 格式输出
python scripts/analyze_matchup.py HOU LAL --output json
```

**分析框架（4 个维度）：**
1. **Four Factors Clash** - 篮板、失误、罚球、命中率的攻防对抗
2. **Style & Geometry** - 节奏、禁区攻防、PlayType 效率
3. **Key Matchups** - 球员类型 vs 防守资源
4. **Context & Form** - 月度趋势、最近 10 场表现、休息天数

**参数说明：**
| 参数 | 说明 |
|------|------|
| `team_a`, `team_b` | 球队缩写 (如 HOU, LAL, BOS) |
| `--month` | 数据月份 (october/november/december/january) |
| `--out` | 缺阵球员名单（可多次使用或逗号分隔） |
| `--live` | 启用实时抓取 Last 10 Games 数据 |
| `--date` | 比赛日期 (YYYY-MM-DD)，用于计算休息天数 |
| `--timezone`, `--tz` | 你的时区，自动转换为美东时间 (如 `beijing`, `+8`) |
| `--output` | 输出格式 (console/json) |

**时区转换示例：**
```bash
# 北京时间 2026-01-28 的比赛 -> 自动转换为美东时间
python scripts/analyze_matchup.py HOU LAL --date 2026-01-28 --tz beijing

# 支持的时区格式: beijing, shanghai, china, Asia/Shanghai, +8, cst
```

**运行注意事项：**

1. **必须激活虚拟环境并设置 PYTHONPATH**：
   ```bash
   source .venv/bin/activate
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

   # 或一行命令
   source .venv/bin/activate && PYTHONPATH="$(pwd)/src:$PYTHONPATH" python scripts/analyze_matchup.py HOU LAL
   ```

2. **`--live` 参数需要额外依赖**：
   ```bash
   # 安装实时抓取所需的依赖
   pip install selenium webdriver-manager mlflow lxml pyyaml dependency-injector
   ```

3. **常见错误及解决方案**：

   | 错误信息 | 原因 | 解决方案 |
   |----------|------|----------|
   | `No module named 'ml_framework'` | PYTHONPATH 未设置 | `export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"` |
   | `No module named 'mlflow'` | 虚拟环境未激活或依赖未安装 | `source .venv/bin/activate && pip install mlflow` |
   | `Logger not initialized` | 内部初始化问题 | 已修复，更新代码即可 |
   | `llvmlite build failed` | LLVM 未安装（shap 依赖） | 只安装最小依赖，跳过 shap |

4. **不使用 `--live` 时的基础运行**：
   ```bash
   # 基础分析不需要 mlflow 等依赖，只需要 pandas
   python scripts/analyze_matchup.py HOU LAL --month january
   ```

### 3.2 预测分析

| 脚本 | 用途 |
|------|------|
| `predict_december_2025.py` | 预测 2025 年 12 月 OffRtg |
| `predict_january_2026.py` | 预测 2026 年 1 月 OffRtg |
| `residual_analysis.py` | 分析模型残差 |
| `analyze_prediction_error.py` | 分析预测误差 |

### 3.3 球队分析

| 脚本 | 用途 |
|------|------|
| `analyze_rockets.py` | 分析火箭队数据 |
| `analyze_fgm_ast_pct.py` | 分析投篮助攻率 |
| `analyze_calibration.py` | 分析模型校准度 |
| `compare_tci_rankings.py` | 比较 TCI 排名 |

### 3.4 教练评估

| 脚本 | 用途 | 输出 |
|------|------|------|
| `evaluate_coaches.py` | 评估当前赛季教练表现 | `data/analysis/coach_evaluation_*.csv` |
| `evaluate_coaches_monthly.py` | 月度教练评估 | `data/analysis/coach_evaluation_monthly_*.csv` |
| `evaluate_coach_career.py` | 评估单个教练生涯 | `data/analysis/coach_career_*.csv` |

**使用示例：**
```bash
python scripts/evaluate_coaches.py
python scripts/evaluate_coach_career.py  # 会提示输入教练名字
```

---

## 四、Pipeline 脚本

| 脚本 | 用途 |
|------|------|
| `run_pipeline.py` | 运行完整数据处理 pipeline |
| `run_nightly_pipeline.sh` | 每日自动运行 pipeline |

---

## 五、工具/配置脚本

### 5.1 环境配置

| 脚本 | 用途 |
|------|------|
| `configure_proxy.sh` | 配置代理 |
| `detect_gpu.sh` | 检测 GPU |
| `setup_fork.sh` | 设置 Git fork |

### 5.2 Chrome/WebDriver 测试

| 脚本 | 用途 |
|------|------|
| `test_chrome_locally.sh` | 本地测试 Chrome |
| `test_chrome_verbose.py` | 详细测试 Chrome |
| `test_chrome_with_config.py` | 使用配置测试 Chrome |
| `test_chrome_with_proxy.sh` | 测试带代理的 Chrome |
| `test_custom_webdriver.py` | 测试自定义 WebDriver |
| `test_duplicate_flags.py` | 测试重复参数问题 |

### 5.3 Kaggle 数据

| 脚本 | 用途 |
|------|------|
| `download_kaggle_data.sh` | 从 Kaggle 下载数据 |
| `upload_to_kaggle.sh` | 上传数据到 Kaggle |
| `run_with_kaggle_data.sh` | 使用 Kaggle 数据运行 |
| `run_local_kaggle_refresh.sh` | 本地刷新 Kaggle 数据 |

### 5.4 其他工具

| 脚本 | 用途 |
|------|------|
| `fix_mlflow_paths.sh` | 修复 MLflow 路径问题 |
| `test_team_stats_scraper.py` | 测试球队统计抓取器 |
| `test_per_team_scraper.py` | 测试单球队抓取器 |

---

## 六、常用工作流

### 6.1 抓取最新数据并更新模型

```bash
# 1. 激活环境
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# 2. 抓取最新月度数据
python scripts/scrape_monthly_data.py
python scripts/scrape_four_factors_monthly.py

# 3. 重新训练模型
python scripts/build_tci_model_monthly.py
python scripts/build_defrtg_model_monthly.py
```

### 6.2 更新球员分类

```bash
# 1. 抓取球员数据 (耗时较长，约 2-3 小时)
./scripts/run_all_player_scrapers.sh

# 2. 构建特征并分类
python scripts/build_player_features_monthly.py
python scripts/classify_players.py
```

### 6.3 评估教练

```bash
python scripts/evaluate_coaches.py
```

---

## 七、数据目录结构

```
data/
├── newly_scraped/
│   ├── tracking_monthly/      # 球队月度数据
│   │   ├── 2021_22/
│   │   ├── 2022_23/
│   │   ├── 2023_24/
│   │   ├── 2024_25/
│   │   └── 2025_26/
│   └── player_monthly/        # 球员月度数据
│       ├── 2021_22/
│       ├── 2022_23/
│       ├── 2023_24/
│       ├── 2024_25/
│       └── 2025_26/
├── schedules/                 # 球队赛程数据（用于对阵分析）
│   └── schedule_2025_26.csv
└── analysis/                  # 分析结果
    ├── tci_model_monthly.json
    ├── defrtg_model_monthly.json
    ├── player_features_*.csv
    └── player_classification_*.csv
```

---

## 八、注意事项

1. **抓取速度**：所有抓取脚本都有延迟设置 (10-15秒)，避免被 NBA.com 封禁
2. **断点续传**：大多数抓取脚本支持断点续传，通过 `*_progress.json` 文件跟踪进度
3. **Chrome 依赖**：抓取脚本需要安装 Chrome 浏览器和 ChromeDriver
4. **内存占用**：某些分析脚本处理大量数据时可能占用较多内存
