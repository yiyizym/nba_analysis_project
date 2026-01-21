# 工作日志

## 2026-01-21

### TCI 模型 v5 - 添加 Four Factors 特征

**背景：** Dean Oliver 的 Four Factors 理论认为进攻效率由四个核心因素决定：
1. eFG% (有效命中率) - 公式: `(FGM + 0.5 × 3PM) / FGA`
2. TOV% (失误率) - 已有
3. OREB% (进攻篮板率) - 已有
4. FTA Rate (罚球尝试率) - **新增**

**新增数据抓取：**
- 脚本: `scripts/scrape_four_factors_monthly.py`
- 抓取 5 个赛季 (2021-22 至 2025-26) 共 32 个月份数据
- 数据保存: `data/newly_scraped/tracking_monthly/*/four_factors_*.csv`

**模型特征扩展至 17 个（新增 2 个）：**
| 特征 | 含义 | 权重 |
|------|------|------|
| **eFG_Pct** | **有效命中率** | **+4.15** |
| OREB_Pct | 进攻篮板率 | +2.11 |
| TOV_Pct | 失误率 | -1.94 |
| **FTA_Rate** | **罚球尝试率 (FTA/FGA)** | **+0.87** |
| AST_To_Pass_Pct | 传球转助攻率 | +0.77 |
| FGM_AST_Pct | 受助攻率 | -0.58 |
| Passes_Per_Poss | 每回合传球数 | +0.47 |
| Rim_Pct | 篮下出手占比 | -0.22 |
| Three_Pt_Pct | 三分出手占比 | +0.16 |
| Mid_Range_Pct | 中距离出手占比 | -0.10 |
| Secondary AST | 二次助攻 | +0.09 |
| Potential_AST_To_Pass_Pct | 潜在助攻率 | -0.07 |
| Open_Pct | 空位出手占比 | -0.07 |
| Very_Tight_Pct | 极紧逼出手占比 | -0.04 |
| Wide_Open_Pct | 大空位出手占比 | -0.03 |
| Tight_Pct | 紧逼出手占比 | -0.02 |
| Dist_Miles_Off | 进攻跑动距离 | +0.01 |

**模型演进（完整版）：**

| 版本 | 特征数 | 训练样本 | Training R² | Validation R² | R² Drop |
|------|--------|----------|-------------|---------------|---------|
| v1 (赛季级别) | 10 | 30 | 0.9107 | 0.5328 | 0.3779 |
| v2 (月份级别) | 10 | 330 | 0.7706 | 0.5212 | 0.2494 |
| v3 (多赛季) | 13 | 840 | 0.7556 | 0.6456 | 0.1100 |
| v4 (+ 出手距离) | 15 | 840 | 0.7796 | 0.6824 | 0.0971 |
| **v5 (+ Four Factors)** | **17** | **840** | **0.9718** | **0.9271** | **0.0446** |

**关键改进：**
- Validation R² 提升 **+24.5%**（0.6824 → 0.9271）
- 过拟合程度降低 **54%**（R² Drop: 0.0971 → 0.0446）
- RMSE 从 ~2.5 降至 **1.21**
- **eFG_Pct 成为最重要特征**（权重 +4.15）

### eFG% vs OffRtg 相关性分析

**问题：** eFG% 和 OffRtg 是否只是"换种说法说同一件事"？

**分析结果：**
- 相关系数 r = 0.82，R² = 0.67
- **33% 的 OffRtg 变化无法被 eFG% 单独解释**

**反例 - eFG% 低但 OffRtg 高：**
| 球队 | 月份 | eFG% | OffRtg | 差值 | 原因 |
|------|------|------|--------|------|------|
| 火箭 | 24-25/10月 | 47.8 | 114.0 | +9.5 | OREB% 37.5%（超高） |
| 火箭 | 25-26/10月 | 56.5 | 125.2 | +8.0 | OREB% 42.9% + FTA Rate 0.395 |

**反例 - eFG% 高但 OffRtg 低：**
| 球队 | 月份 | eFG% | OffRtg | 差值 | 原因 |
|------|------|------|--------|------|------|
| 独行侠 | 24-25/4月 | 54.2 | 105.1 | -8.8 | TOV% 17.8%（失误过多） |
| 篮网 | 24-25/4月 | 52.6 | 103.8 | -7.7 | TOV% 16.7% + OREB% 23.8%（低） |

**残差与其他因素相关性：**
| 因素 | 相关性 | 解释 |
|------|--------|------|
| OREB% | +0.62 | 进攻篮板创造额外得分机会 |
| TOV% | -0.43 | 失误浪费进攻回合 |
| FTA_Rate | +0.13 | 罚球提供"免费"得分 |

### 火箭队 2026 年 1 月详细分析

**OffRtg: 111.6（联盟第 23），低于联盟平均 114.0**

**优势（提升 OffRtg）：**
| 特征 | 火箭 | 联盟均值 | 排名 | 分析 |
|------|------|----------|------|------|
| OREB_Pct | 40.4% | 29.98% | 1/30 | 进攻篮板联盟第一，高出 35% |
| FGM_AST_Pct | 54.1% | 63.73% | 3/30 | 受助攻率低 = 个人单打能力强 |
| FTA_Rate | 0.26 | 0.25 | 10/30 | 造罚球能力不错 |

**劣势（拖累 OffRtg）：**
| 特征 | 火箭 | 联盟均值 | 排名 | 分析 |
|------|------|----------|------|------|
| eFG_Pct | 49.0% | 54.25% | 30/30 | 有效命中率联盟垫底 |
| AST_To_Pass_Pct | 8.0% | 9.31% | 30/30 | 传球转化助攻率垫底 |
| Mid_Range_Pct | 23.3% | 13.76% | 29/30 | 中距离出手占比高出 70% |

**结论：** 火箭 1 月进攻风格为"蓝领进攻"——靠抢篮板和造罚球得分，而非投篮效率。eFG% 联盟垫底是最大问题，中距离出手过多拖累效率。

---

## 2026-01-20 (续)

### TCI 模型优化 - 多赛季训练 + 新特征

**模型特征扩展至 15 个：**
| 特征 | 含义 | 权重 |
|------|------|------|
| AST_To_Pass_Pct | 传球转助攻率 | +7.40 |
| FGM_AST_Pct | 受助攻率 | -4.85 |
| Passes_Per_Poss | 每回合传球数 | +3.99 |
| Mid_Range_Pct | 中距离出手占比 (10-19ft) | -0.97 |
| Rim_Pct | 篮下出手占比 (<5ft) | -0.83 |
| OREB_Pct | 进攻篮板率 | +0.82 |
| TOV_Pct | 失误率 | -0.70 |
| Secondary AST | 二次助攻 | +0.63 |
| Three_Pt_Pct | 三分出手占比 (25-29ft) | +0.43 |
| Dist_Miles_Off | 进攻跑动距离 | -0.36 |
| Tight_Pct | 紧逼出手占比 | -0.17 |
| Potential_AST_To_Pass_Pct | 潜在助攻率 | -1.20 |
| Open_Pct | 空位出手占比 | -0.06 |
| Wide_Open_Pct | 大空位出手占比 | -0.04 |
| Very_Tight_Pct | 极紧逼出手占比 | +0.01 |

**模型演进（完整版）：**

| 版本 | 特征数 | 训练样本 | Training R² | Validation R² | R² Drop |
|------|--------|----------|-------------|---------------|---------|
| v1 (赛季级别) | 10 | 30 | 0.9107 | 0.5328 | 0.3779 |
| v2 (月份级别) | 10 | 330 | 0.7706 | 0.5212 | 0.2494 |
| v3 (多赛季) | 13 | 840 | 0.7556 | 0.6456 | 0.1100 |
| **v4 (+ 出手距离)** | **15** | **840** | **0.7796** | **0.6824** | **0.0971** |

**关键改进：**
1. **训练数据扩展**：加入 2021-22、2022-23、2023-24 历史数据，样本数 330 → 840
2. **缺失值处理**：采用均值填充而非删除整行，保留更多数据
3. **新增出手距离特征**：Rim_Pct、Mid_Range_Pct、Three_Pt_Pct
4. **验证集表现提升**：R² 从 0.5212 提升至 0.6824

**新增脚本：**
| 脚本 | 用途 |
|------|------|
| `scripts/scrape_shooting_distance_monthly.py` | 抓取出手距离数据 |
| `scripts/scrape_january_2026.py` | 抓取 2026 年 1 月最新数据 |
| `scripts/predict_january_2026.py` | 1 月 OffRtg 预测 |
| `scripts/analyze_rockets.py` | 火箭队详细分析 |

### 火箭队 2026 年 1 月分析

**关键发现：**
- 实际 OffRtg: 111.3 (联盟第 18)
- 中距离出手占比从 14% 上升至 23.3%（远高于联盟平均 15.5%）
- 中距离出手增加对 OffRtg 有负面影响（权重 -0.97）

### PlayType 数据抓取

**抓取脚本：** `scripts/scrape_playtype_monthly.py`

**PlayType 分类 (11 个)：**
| URL Slug | 文件前缀 | 中文含义 |
|----------|----------|----------|
| isolation | playtype_isolation | 单打 |
| transition | playtype_transition | 转换进攻 |
| ball-handler | playtype_ball_handler | 挡拆持球人 |
| roll-man | playtype_roll_man | 挡拆顺下人 |
| playtype-post-up | playtype_post_up | 低位单打 |
| spot-up | playtype_spot_up | 定点投篮 |
| hand-off | playtype_handoff | 手递手 |
| cut | playtype_cut | 空切 |
| off-screen | playtype_off_screen | 无球掩护 |
| putbacks | playtype_putbacks | 二次进攻 |
| playtype-misc | playtype_misc | 其他 |

**抓取结果：**
| 赛季 | 文件数 | 月份 |
|------|--------|------|
| 2024-25 | 77 | 7 月 × 11 分类 |
| 2025-26 | 44 | 4 月 × 11 分类 |
| **总计** | **121** | |

**数据字段：** TEAM, GP, POSS, FREQ%, PPP, PTS, FGM, FGA, FG%, EFG%, TOV FREQ%, PERCENTILE 等

**数据保存位置：** `data/newly_scraped/tracking_monthly/*/playtype_*.csv`

**注意事项：**
- 部分 URL 格式特殊：`post-up` → `playtype-post-up`，`misc` → `playtype-misc`，`handoff` → `hand-off`

---

## 2026-01-20

### TCI (战术配合指数) 模型构建

**目标：** 基于 NBA Tracking 数据构建 TCI 模型，量化球队战术配合水平。

**模型特征 (10 个)：**
| 特征 | 含义 | 权重 |
|------|------|------|
| AST_To_Pass_Pct | 传球转助攻率 | +7.16 |
| FGM_AST_Pct | 受助攻率 | -5.39 |
| Passes_Per_Poss | 每回合传球数 | +4.93 |
| Secondary AST | 二次助攻 | +0.73 |
| Tight_Pct | 紧逼出手占比 | -0.49 |
| Very_Tight_Pct | 极紧逼出手占比 | -0.14 |
| Potential_AST_To_Pass_Pct | 潜在助攻率 | -0.14 |
| Dist_Miles_Off | 进攻跑动距离 | -0.13 |
| Wide_Open_Pct | 大空位出手占比 | -0.10 |
| Open_Pct | 空位出手占比 | +0.09 |

**模型演进：**

| 版本 | 样本数 | Training R² | Validation R² | R² Drop |
|------|--------|-------------|---------------|---------|
| v1 (赛季级别) | 30 | 0.9107 | 0.5328 | 0.3779 |
| v2 (月份级别) | 330 | 0.7706 | 0.5212 | 0.2494 |

**关键发现：**
- 月份级别数据显著降低过拟合（R² Drop: 0.38 → 0.25）
- `AST_To_Pass_Pct` 是最重要的特征
- `FGM_AST_Pct` 虽然权重为负，但移除后模型性能大幅下降

### 月份级别数据抓取

**抓取脚本：** `scripts/scrape_monthly_data.py`

**安全措施：**
- 请求间延迟 10-15 秒（随机）
- 类别间延迟 25 秒
- 断点续传支持

**抓取数据：**
| 赛季 | 文件数 | 样本数 |
|------|--------|--------|
| 2024-25 | 56 | 7月 × 30队 = 210 |
| 2025-26 | 32 | 4月 × 30队 = 120 |
| **总计** | 88 | **330** |

**数据保存位置：** `data/newly_scraped/tracking_monthly/`

### 2025-26 赛季 TCI 排名 (Top 10)

| 排名 | 球队 | TCI | OffRtg |
|------|------|-----|--------|
| 1 | Boston Celtics | 100.0 | 121.2 |
| 2 | Denver Nuggets | 76.6 | 121.1 |
| 3 | Houston Rockets | 72.2 | 119.7 |
| 4 | Cleveland Cavaliers | 71.6 | 115.8 |
| 5 | Oklahoma City Thunder | 67.8 | 117.6 |
| 6 | New York Knicks | 57.6 | 117.4 |
| 7 | Minnesota Timberwolves | 57.0 | 117.3 |
| 8 | Chicago Bulls | 53.9 | 115.0 |
| 9 | Milwaukee Bucks | 53.3 | 113.7 |
| 10 | Los Angeles Lakers | 50.0 | 116.5 |

**输出文件：**
- `data/analysis/tci_model_monthly.json` - 模型权重
- `data/analysis/tci_rankings_2025_26.csv` - 球队排名

**新增脚本：**
| 脚本 | 用途 |
|------|------|
| `scripts/build_tci_model.py` | 赛季级别 TCI 模型 |
| `scripts/build_tci_model_monthly.py` | 月份级别 TCI 模型 |
| `scripts/validate_tci_model.py` | 模型验证 |
| `scripts/scrape_monthly_data.py` | 月份数据抓取 |
| `scripts/scrape_tight_shots.py` | 补充抓取 tight shots |

---

## 2026-01-19

### 修复 TeamStatsScraper 的 3 个已知问题

**修改的文件：**
| 文件 | 修改 |
|------|------|
| `team_stats_scraper.py` | 添加 `import re` 和 `from io import StringIO` |
| `team_stats_scraper.py` | 修复 `_extract_team_ids` 方法，使用正则匹配新 URL 格式 |
| `team_stats_scraper.py` | 添加 `_fix_multi_level_header` 方法处理多级表头 |
| `team_stats_scraper.py` | 更新 `_convert_table_to_df` 调用新方法 |
| `test_team_stats_scraper.py` | 更新测试用例匹配新 URL 格式 |

**修复详情：**
1. **Team ID 提取失败**: URL 格式变化导致正则不匹配，改用 `/team/(\d+)/`
2. **pandas FutureWarning**: 使用 `StringIO` 包装 HTML 字符串
3. **多级表头列名**: 检测并合并两行表头，生成清晰列名如 `Less_than_5ft_FGA`

**测试结果：** 31/31 全部通过

**验证结果：**
- `team_ids_count`: 0 → 30
- `dataframe_rows`: 31 → 30
- 列名: `Unnamed: 0, Less than 5ft..1` → `Team, Less_than_5ft_FGA`
- TEAM_ID 列: 缺失 → 已添加

---

## 2026-01-18

### TeamStatsScraper 重构 - 支持所有统计分类

将 `TeamStatsShootingScraper` 重构为通用的 `TeamStatsScraper`，支持 50+ 个统计分类。

**修改的文件：**
| 文件 | 修改 |
|------|------|
| `configs/nba/webscraping_config.yaml` | 添加 `team_stats_categories` 配置 |
| `base_scraper_classes.py` | 更新接口支持 `extra_params` |
| `team_stats_shooting_scraper.py` → `team_stats_scraper.py` | 重命名并重构 |
| `di_container.py` | 更新导入和类引用 |
| `nba_scraper.py` | 更新 facade 支持多分类模式 |
| `main.py` | 支持配置驱动的多分类模式 |
| `test_team_stats_shooting_scraper.py` → `test_team_stats_scraper.py` | 更新测试 |

**关键功能：**
- 配置驱动：在 YAML 中定义分类，可独立启用/禁用
- 额外参数支持：如 `DistanceRange=By+Zone`
- 向后兼容：`TeamStatsShootingScraper` 别名保留
- 独立文件输出：如 `team_stats_traditional.csv`, `team_stats_shooting_by_zone.csv`

**测试结果：** 31/31 全部通过

---

## 2026-01-17

### TeamStatsShootingScraper 实现与测试

- 单元测试：15/15 全部通过
- 端到端测试：成功抓取 30 支 NBA 球队的投篮统计数据
- 数据保存：`data/newly_scraped/test_team_stats_shooting.csv`

### 修复的问题

- **macOS Chrome 路径检测** (`web_driver.py:112-123`)
  - 添加了 `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome` 路径
- **chromedriver 搜索优先级** (`web_driver.py:142-151`)
  - 添加了 `~/bin/chromedriver` 优先搜索路径

### Git 提交

- `abf1b79` - Add TeamStatsShootingScraper for scraping NBA team shooting statistics
- `11214af` - Normalize line endings to LF for cross-platform consistency

### 环境配置备注

- **chromedriver 144** 已安装到 `~/bin/chromedriver`
- **Chrome 版本**: 144.0.7559.59
- **.gitattributes** 已配置为统一使用 LF 换行符
