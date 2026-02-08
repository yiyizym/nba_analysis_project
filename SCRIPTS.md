# 脚本使用指南

本文档记录了项目中所有脚本的用途和使用方法。

## 运行环境准备

### 方式一：使用 uv（推荐）

项目使用 [uv](https://github.com/astral-sh/uv) 管理依赖，无需手动激活虚拟环境：

```bash
cd /path/to/nba_analysis_project

# 直接运行脚本（uv 自动处理环境和依赖）
uv run python scripts/scrape_latest.py

# 安装新依赖
uv add package_name
```

### 方式二：传统方式

手动激活虚拟环境并设置 PYTHONPATH：

```bash
cd /path/to/nba_analysis_project
source .venv/bin/activate
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
python scripts/scrape_latest.py
```

> **注意**：本文档中的示例默认使用 `uv run python`，如果使用传统方式请自行替换。

---

## 快速开始：一键抓取

**推荐使用 `scrape_latest.py`**，它可以一次性抓取所有数据：

```bash
# 抓取上个月的所有数据（球队 + 球员）
uv run python scripts/scrape_latest.py

# 抓取整个赛季的数据
uv run python scripts/scrape_latest.py --season

# 只抓取球队数据
uv run python scripts/scrape_latest.py --team-only

# 只抓取球员数据
uv run python scripts/scrape_latest.py --player-only

# 指定赛季和月份
uv run python scripts/scrape_latest.py --year 2025-26 --month january
```

### 定时任务设置 (cron)

```bash
# 使用 uv（推荐）
0 3 2 * * cd /path/to/nba_analysis_project && uv run python scripts/scrape_latest.py >> logs/scrape.log 2>&1

# 或使用传统方式
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
uv run python scripts/scrape_monthly_data.py
uv run python scripts/scrape_four_factors_monthly.py
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
uv run python scripts/scrape_player_stats_monthly.py
uv run python scripts/scrape_player_playtype_monthly.py
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
uv run python scripts/build_tci_model_monthly.py
```

### 2.2 防守模型 (DefRtg)

| 脚本 | 用途 | 输出 |
|------|------|------|
| `build_defrtg_model_monthly.py` | 构建月度 DefRtg 模型 | `data/analysis/defrtg_model_monthly.json` |

**使用示例：**
```bash
uv run python scripts/build_defrtg_model_monthly.py
```

### 2.3 球员分类模型

| 脚本 | 用途 | 输出 |
|------|------|------|
| `build_player_features_monthly.py` | 合并球员特征矩阵 | `data/analysis/player_features_*.csv` |
| `classify_players.py` | 将球员分类为 10 种 archetype | `data/analysis/player_classification_*.csv` |

**使用示例：**
```bash
# 先构建特征，再分类
uv run python scripts/build_player_features_monthly.py
uv run python scripts/classify_players.py
```

---

## 三、分析脚本

### 3.1 比赛对阵分析

| 脚本 | 用途 | 输出 |
|------|------|------|
| `analyze_matchup.py` | 两队对阵博弈分析 | 控制台/JSON |
| `generate_game_preview.py` | 生成比赛前瞻 Prompt（用于 Claude 写文章） | `data/prompts/*.md` |
| `scrape_schedule.py` | 抓取 NBA 球队赛程 | 控制台/CSV |
| `scrape_team_schedules.py` | 抓取球队赛程（用于休息天数计算） | `data/schedules/` |

**`analyze_matchup.py` 详细用法：**

```bash
# 基础分析（使用本地月度数据）
uv run python scripts/analyze_matchup.py HOU LAL

# 启用实时 Last 10 Games 数据抓取
uv run python scripts/analyze_matchup.py HOU LAL --live

# 指定分析月份
uv run python scripts/analyze_matchup.py HOU LAL --month december

# 标记缺阵球员（支持多人）
uv run python scripts/analyze_matchup.py HOU LAL --out "LeBron James"
uv run python scripts/analyze_matchup.py HOU LAL --out "LeBron James,Anthony Davis"

# 指定比赛日期（用于休息天数计算）
uv run python scripts/analyze_matchup.py HOU LAL --live --date 2026-01-28

# JSON 格式输出
uv run python scripts/analyze_matchup.py HOU LAL --output json
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

**伤病自动加载：** 赛季报销 (`out_for_season`) 和长期缺阵 (`long_term`) 球员会从 `configs/nba/injuries.yaml` 自动加载，无需每次手动指定。详见 [5.5 伤病配置](#55-伤病配置)。

**时区转换示例：**
```bash
# 北京时间 2026-01-28 的比赛 -> 自动转换为美东时间
uv run python scripts/analyze_matchup.py HOU LAL --date 2026-01-28 --tz beijing

# 支持的时区格式: beijing, shanghai, china, Asia/Shanghai, +8, cst
```

**运行注意事项：**

1. **使用 uv（推荐）**：
   ```bash
   # uv 自动处理环境，无需手动激活
   uv run python scripts/analyze_matchup.py HOU LAL
   ```

2. **传统方式（需手动设置环境）**：
   ```bash
   source .venv/bin/activate
   export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"
   python scripts/analyze_matchup.py HOU LAL
   ```

3. **`--live` 参数需要额外依赖**（使用 uv 会自动安装）：
   ```bash
   # 如需手动安装
   uv add selenium webdriver-manager mlflow lxml pyyaml dependency-injector
   ```

4. **常见错误及解决方案**：

   | 错误信息 | 原因 | 解决方案 |
   |----------|------|----------|
   | `No module named 'ml_framework'` | PYTHONPATH 未设置 | 使用 `uv run python` 或手动设置 PYTHONPATH |
   | `No module named 'mlflow'` | 依赖未安装 | `uv add mlflow` |
   | `Logger not initialized` | 内部初始化问题 | 已修复，更新代码即可 |

5. **不使用 `--live` 时的基础运行**：
   ```bash
   # 基础分析不需要 mlflow 等依赖，只需要 pandas
   uv run python scripts/analyze_matchup.py HOU LAL --month january
   ```

**`generate_game_preview.py` 详细用法：**

生成用于 Claude 写作的完整 Prompt 文件，包含数据分析结果和写作指导。

```bash
# 基础用法
uv run python scripts/generate_game_preview.py HOU LAL

# 带缺阵球员和实时数据
uv run python scripts/generate_game_preview.py HOU IND --out "Kevin Durant" --live

# 指定比赛日期（自动时区转换）
uv run python scripts/generate_game_preview.py HOU IND --date 2026-02-03 --tz beijing

# 同时打印到终端
uv run python scripts/generate_game_preview.py HOU IND --print
```

**工作流程：**
1. 运行脚本生成 Prompt → `data/prompts/2026-02-03_HOU_vs_IND_prompt.md`
2. 复制 Prompt 内容到 Claude 对话
3. Claude 生成文章
4. 保存文章到 `data/articles/`

**Prompt 包含内容：**
- 四要素对比（篮板/失误/罚球/投篮）
- 风格碰撞分析（节奏/禁区攻防）
- 关键对位（核心球员 vs 防守资源）
- 状态趋势（月度趋势/近10场）
- 胜利条件与危险信号
- 写作结构和风格要求

**`scrape_schedule.py` 详细用法：**

抓取 NBA 球队赛程信息。

```bash
# 抓取火箭队赛程（默认）
uv run python scripts/scrape_schedule.py

# 抓取其他球队
uv run python scripts/scrape_schedule.py --team lakers
uv run python scripts/scrape_schedule.py --team warriors

# 只显示未来比赛
uv run python scripts/scrape_schedule.py --upcoming

# 输出到文件
uv run python scripts/scrape_schedule.py --output data/schedules/rockets_schedule.csv
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
uv run python scripts/evaluate_coaches.py
uv run python scripts/evaluate_coach_career.py  # 会提示输入教练名字
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

### 5.4 数据校验

| 脚本 | 用途 |
|------|------|
| `validate_scraped_data.py` | 校验抓取数据质量（行数、列、范围等） |

**使用示例：**
```bash
# 校验单个文件
uv run python scripts/validate_scraped_data.py data/newly_scraped/tracking_monthly/2025_26/four_factors_january.csv --type four-factors -v

# 自动检测数据类型
uv run python scripts/validate_scraped_data.py data/.../team_advanced_january.csv -v
```

**校验内容：**
| 校验项 | 严重级别 | 说明 |
|--------|----------|------|
| 行数检查 | ERROR | NBA 应有 30 支球队 |
| 必需列检查 | ERROR | 关键列是否存在 |
| 数值范围 | WARNING | eFG% 0-100, OffRtg 90-130 等 |
| 空值检查 | WARNING | 关键列是否有空值 |
| TEAM_ID 校验 | WARNING | 是否为有效的 NBA 球队 ID |

**注意**：此模块已集成到 `generate_game_preview.py` 中，实时抓取数据时会自动校验。

### 5.5 伤病配置

伤病配置文件 `configs/nba/injuries.yaml` 用于持久化赛季报销或长期缺阵的球员，避免每次运行分析时手动指定 `--out` 参数。

**配置文件位置：** `configs/nba/injuries.yaml`

**配置格式：**
```yaml
season: "2025-26"

injuries:
  # Houston Rockets
  HOU:
    - name: "某球员"
      status: "out_for_season"
      note: "ACL撕裂"

  # Indiana Pacers
  IND:
    - name: "James Wiseman"
      status: "out_for_season"
      note: "跟腱手术"

  # Los Angeles Lakers
  LAL:
    - name: "某球员"
      status: "long_term"
      note: "背部手术，预计休息3个月"

    - name: "另一球员"
      status: "day_to_day"
      note: "脚踝扭伤"
```

**状态说明：**

| 状态 | 说明 | 自动排除 |
|------|------|----------|
| `out_for_season` | 赛季报销 | ✅ 是 |
| `long_term` | 长期缺阵（超过1个月） | ✅ 是 |
| `day_to_day` | 出战成疑 | ❌ 否，需手动 `--out` |

**使用示例：**

```bash
# James Wiseman (out_for_season) 会自动排除
# Kevin Durant (day_to_day) 需手动指定
uv run python scripts/analyze_matchup.py HOU IND --out "Kevin Durant"

# 输出会显示：
# Auto-loaded injuries: James Wiseman
# Manual --out: Kevin Durant
# Total out players: James Wiseman, Kevin Durant
```

**适用脚本：**
- `analyze_matchup.py` - 对阵分析
- `generate_game_preview.py` - 比赛前瞻 Prompt 生成

**管理工具 `scrape_injuries.py`：**

```bash
# 查看当前伤病配置
uv run python scripts/scrape_injuries.py --show

# 添加伤病球员
uv run python scripts/scrape_injuries.py --add HOU "Jabari Smith Jr." long_term "膝盖伤势"
uv run python scripts/scrape_injuries.py --add LAL "LeBron James" out_for_season "跟腱断裂"

# 移除球员（球员复出时）
uv run python scripts/scrape_injuries.py --remove HOU "Kevin Durant"

# 尝试从 ESPN 抓取（可能不稳定，建议手动更新）
uv run python scripts/scrape_injuries.py --fetch --dry-run
```

**数据来源：** 手动查阅 [ESPN NBA Injuries](https://www.espn.com/nba/injuries) 获取最新伤病信息。

### 5.6 其他工具

| 脚本 | 用途 |
|------|------|
| `fix_mlflow_paths.sh` | 修复 MLflow 路径问题 |
| `test_team_stats_scraper.py` | 测试球队统计抓取器 |
| `test_per_team_scraper.py` | 测试单球队抓取器 |

---

## 六、常用工作流

### 6.1 抓取最新数据并更新模型

```bash
# 使用 uv（无需手动激活环境）
uv run python scripts/scrape_monthly_data.py
uv run python scripts/scrape_four_factors_monthly.py
uv run python scripts/build_tci_model_monthly.py
uv run python scripts/build_defrtg_model_monthly.py
```

### 6.2 更新球员分类

```bash
# 1. 抓取球员数据 (耗时较长，约 2-3 小时)
./scripts/run_all_player_scrapers.sh

# 2. 构建特征并分类
uv run python scripts/build_player_features_monthly.py
uv run python scripts/classify_players.py
```

### 6.3 评估教练

```bash
uv run python scripts/evaluate_coaches.py
```

### 6.4 生成比赛前瞻文章

```bash
# 1. 查看火箭队赛程
uv run python scripts/scrape_schedule.py --team rockets

# 2. 生成对阵分析 Prompt（带实时数据）
uv run python scripts/generate_game_preview.py HOU IND --out "Kevin Durant" --live

# 3. 复制 data/prompts/*.md 内容到 Claude 对话
# 4. Claude 生成文章后，保存到 data/articles/
```

---

## 七、目录结构

```
nba_analysis_project/
├── configs/
│   └── nba/
│       ├── injuries.yaml          # 伤病配置（赛季报销/长期缺阵）
│       ├── app_config.yaml        # 应用配置
│       └── article_generation.yaml # 文章生成配置
│
├── data/
│   ├── newly_scraped/
│   │   ├── tracking_monthly/      # 球队月度数据
│   │   │   ├── 2021_22/
│   │   │   ├── 2022_23/
│   │   │   ├── 2023_24/
│   │   │   ├── 2024_25/
│   │   │   └── 2025_26/
│   │   └── player_monthly/        # 球员月度数据
│   │       ├── 2021_22/
│   │       ├── 2022_23/
│   │       ├── 2023_24/
│   │       ├── 2024_25/
│   │       └── 2025_26/
│   ├── schedules/                 # 球队赛程数据（用于对阵分析）
│   │   └── schedule_2025_26.csv
│   ├── prompts/                   # 比赛前瞻 Prompt 文件
│   │   └── 2026-02-03_HOU_vs_IND_prompt.md
│   ├── articles/                  # 生成的文章（手动保存）
│   │   └── 2026-02-03_HOU_vs_IND_preview.md
│   └── analysis/                  # 分析结果
│       ├── tci_model_monthly.json
│       ├── defrtg_model_monthly.json
│       ├── player_features_*.csv
│       └── player_classification_*.csv
│
└── scripts/                       # 脚本目录
```

---

## 八、注意事项

1. **抓取速度**：所有抓取脚本都有延迟设置 (10-15秒)，避免被 NBA.com 封禁
2. **断点续传**：大多数抓取脚本支持断点续传，通过 `*_progress.json` 文件跟踪进度
3. **Chrome 依赖**：抓取脚本需要安装 Chrome 浏览器和 ChromeDriver
4. **内存占用**：某些分析脚本处理大量数据时可能占用较多内存
