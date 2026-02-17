# 工作日志

## 2026-02-17

### 文章语音生成功能

**新增脚本：** `scripts/text_to_speech.py`

使用 edge-tts 将生成的比赛前瞻文章转换为语音。

**功能特点：**
- 使用微软 Edge TTS API，默认 `zh-CN-YunxiNeural` 男声
- 智能分段处理长文章（每段不超过 2000 字符）
- 自动清理 Markdown 格式符号
- 使用 pydub 拼接多个音频片段
- 支持自定义语音和语速

**依赖安装：**
```bash
pip install edge-tts pydub
# 系统需要安装 ffmpeg
```

**使用示例：**
```bash
# 基本用法
python scripts/text_to_speech.py data/prompts/2026-02-19_HOU_vs_CHA_prompt.md

# 指定输出文件
python scripts/text_to_speech.py article.md -o output.mp3

# 使用女声
python scripts/text_to_speech.py article.md --voice zh-CN-XiaoxiaoNeural

# 加快语速
python scripts/text_to_speech.py article.md --rate "+10%"

# 测试简单文本
python scripts/text_to_speech.py --test "这是一个测试"

# 列出可用语音
python scripts/text_to_speech.py --list-voices
```

**输出位置：** `data/audio/*.mp3`

---

### 文章生成风格优化

**修改文件：** `scripts/generate_game_preview.py`

在风格要求中新增：
- 请不要用小标题，直接用段落分隔内容

---

### 2月份比赛数据更新

**抓取时间：** 2026-02-17 11:00-11:17

**抓取内容：**
- 球队数据：19个类别全部成功
- 球员数据：19/21成功（defense_lt6 无数据，hustle 超时）

**2月份球队 NetRtg 排名 (交易后)：**

| 排名 | 球队 | 战绩 | OffRtg | DefRtg | NetRtg |
|------|------|------|--------|--------|--------|
| 1 | Detroit Pistons | 5-1 | 122.8 | 102.9 | **+19.9** |
| 2 | Cleveland Cavaliers | 5-0 | 126.6 | 109.4 | **+17.2** |
| 3 | San Antonio Spurs | 6-0 | 122.3 | 107.4 | **+14.8** |
| 4 | New York Knicks | 5-2 | 119.0 | 107.3 | +11.6 |
| 5 | Miami Heat | 3-3 | 115.0 | 103.9 | +11.2 |
| 6 | Boston Celtics | 5-1 | 115.9 | 105.0 | +10.8 |
| ... | ... | ... | ... | ... | ... |
| 28 | Dallas Mavericks | 0-5 | 109.1 | 122.2 | -13.1 |
| 29 | Washington Wizards | 2-4 | 109.7 | 124.3 | -14.6 |
| 30 | Chicago Bulls | 0-6 | 106.9 | 127.4 | **-20.6** |

**2月份得分榜 Top 5：**

| 排名 | 球员 | 球队 | PTS | REB | AST |
|------|------|------|-----|-----|-----|
| 1 | Joel Embiid | PHI | 30.7 | 7.0 | 4.3 |
| 2 | Kawhi Leonard | LAC | 28.9 | 8.0 | 4.4 |
| 3 | Anthony Edwards | MIN | 28.5 | 5.7 | 3.7 |
| 4 | Jaylen Brown | BOS | 28.4 | 7.4 | 3.0 |
| 5 | Donovan Mitchell | CLE | 28.0 | 2.2 | 7.4 |

**被交易球员新球队表现：**

| 球员 | 新球队 | GP | PTS | AST |
|------|--------|----|----|-----|
| James Harden | CLE | 3 | 19.3 | 8.7 |
| Jaren Jackson Jr. | UTA | 4 | 24.3 | 2.5 |
| Ayo Dosunmu | MIN | 5 | 14.2 | 3.4 |
| Luke Kennard | LAL | 5 | 10.4 | 2.4 |
| Jared McCain | OKC | 6 | 7.2 | 1.7 |

**关键发现：**
- Detroit Pistons 2月份表现惊人，NetRtg +19.9 联盟第一
- Cleveland Cavaliers 获得 Harden 后 5-0 全胜
- San Antonio Spurs 6-0 完美开局，Wembanyama 场均 26.3 分 10.8 篮板
- Dallas Mavericks 交易 AD 后 0-5，阵容磨合需要时间
- Chicago Bulls 大幅重建后 0-6，NetRtg -20.6 联盟垫底

**输出文件：**
- `data/newly_scraped/tracking_monthly/2025_26/*_february.csv` (19个球队文件)
- `data/newly_scraped/player_monthly/2025_26/*_february.csv` (19个球员文件)

---

### 2026 NBA 交易截止日球员名单更新

**背景：** 2026年2月5日交易截止日创下历史纪录，共完成28笔交易，涉及73名球员。需要更新各球队最新阵容信息以支持后续比赛分析。

**数据来源：**
- NBA.com Trade Tracker
- Hoops Rumors

**重磅交易汇总：**

| 交易 | 获得方 | 送出方 |
|------|--------|--------|
| James Harden ↔ Darius Garland | CLE ↔ LAC | 互换全明星后卫 |
| Anthony Davis | WAS | DAL (三方) |
| Jaren Jackson Jr. | UTA | MEM + 3首轮 |
| Kristaps Porzingis ↔ Jonathan Kuminga | GSW ↔ ATL | 互换核心球员 |
| Nikola Vucevic | BOS | CHI |
| Jared McCain | OKC | PHI |
| Trae Young | WAS | ATL (1月9日) |

**阵容变化最大的球队：**

| 球队 | 主要变动 |
|------|----------|
| Cleveland Cavaliers | +Harden, +Schroder / -Garland, -Hunter |
| Washington Wizards | +AD, +Trae Young / -McCollum, -Middleton |
| LA Clippers | +Garland, +Mathurin / -Harden, -Zubac |
| Utah Jazz | +JJJ, +Lonzo Ball / -Anderson, -Niang |
| Golden State Warriors | +Porzingis / -Kuminga, -Hield |
| Chicago Bulls | +Simons, +Ivey, +Dillingham / -Vucevic, -Dosunmu |

**未被交易的重要球星：**
- Giannis Antetokounmpo (MIL)
- Ja Morant (MEM)
- Domantas Sabonis (SAC)

**输出文件：**
- `data/rosters/trade_deadline_2026.md` - 完整交易记录与各队阵容变动

**对分析系统的影响：**
- 比赛预测模型需考虑新阵容磨合期
- 球队进攻/防守风格可能发生变化
- 建议等待 10-15 场比赛后再更新月度数据

---

## 2026-01-27

### 比赛对阵分析系统 - 实时数据功能增强

**背景：** 在完成基础的 4 维度对阵分析框架后，增加了实时数据抓取功能以获取更准确的近期表现数据。

**新增功能：**

#### 1. `--live` 参数 - 实时抓取 Last 10 Games 数据
从 NBA.com 实时抓取最近 10 场比赛的统计数据：
- **Four Factors**: eFG%, TOV%, OREB%, FTA Rate
- **Advanced**: W-L 记录, NetRtg, OffRtg, DefRtg

**实现原理：**
```python
# 使用 LastNGames 参数请求 NBA Stats
extra_params = {"LastNGames": "10"}
url = "https://www.nba.com/stats/teams/four-factors?LastNGames=10"
```

#### 2. `--date DATE` 参数 - 比赛日期用于赛程分析
指定比赛日期（格式: YYYY-MM-DD），配合赛程数据计算：
- 休息天数 (Rest Days)
- 背靠背第二场 (Back-to-Back)

#### 3. `--timezone` / `--tz` 参数 - 自动转换时区
由于 NBA 赛程使用美东时间，可通过此参数将本地日期自动转换为美国日期：
```bash
# 北京时间 2026-01-28 -> 自动转换为美东时间
python scripts/analyze_matchup.py HOU LAL --date 2026-01-28 --timezone beijing
```

**支持的时区格式：**
| 格式 | 示例 |
|------|------|
| 城市别名 | `beijing`, `shanghai`, `china` |
| IANA 时区 | `Asia/Shanghai`, `America/New_York` |
| UTC 偏移 | `+8`, `-5`, `+08:00` |
| 缩写 | `cst` (中国), `et` (美东), `pt` (美西) |

#### 4. 赛程数据抓取与缓存
- 创建 `scripts/scrape_team_schedules.py` 用于抓取完整赛季赛程
- 赛程数据缓存到 `data/schedules/schedule_{season}.csv`
- 因为赛程是赛季初确定的，只需抓取一次

**使用示例：**
```bash
# 基础分析（使用本地月度数据）
python scripts/analyze_matchup.py HOU LAL

# 启用实时 Last 10 Games 数据
python scripts/analyze_matchup.py HOU LAL --live

# 指定比赛日期（用于休息天数计算）
python scripts/analyze_matchup.py HOU LAL --live --date 2026-01-28

# 标记缺阵球员（多人用逗号分隔）
python scripts/analyze_matchup.py HOU LAL --out "LeBron James,Anthony Davis"
```

**输出示例（启用 --live 后）：**
```
--------------------------------------------------------------------------------
4. CONTEXT & FORM (状态趋势)
--------------------------------------------------------------------------------
【最近10场表现】(实时数据)
  HOU L10: +3.2 NetRtg | 7-3 | 52.1% eFG | 12.8% TOV
  LAL L10: -1.5 NetRtg | 4-6 | 49.8% eFG | 14.2% TOV
  >>> HOU 近期状态明显更佳

【休息与疲劳】
  HOU: 距上场 2天
  LAL: 距上场 1天 | 背靠背第2场
  >>> LAL 体能劣势，背靠背作战

【月度趋势】
HOU: Oct(+9.2) -> Nov(+12.8) -> Dec(+4.1) -> Jan(+0.0)
  趋势: 下滑
```

**修改的文件：**
| 文件 | 修改内容 |
|------|----------|
| `scripts/analyze_matchup.py` | 添加 `--live`, `--date` 参数；实现 `scrape_last_n_games()`, `fetch_last_10_games_data()` 函数；更新输出格式 |
| `scripts/scrape_team_schedules.py` | 新增赛程抓取脚本 |

**技术细节：**
- 使用项目已有的 `DIContainer` 和 `TeamStatsScraper` 进行数据抓取
- 抓取失败时优雅降级，继续使用本地月度数据
- WebDriver 在抓取完成后自动关闭

**注意事项：**
- `--live` 需要项目的 `ml_framework` 依赖才能正常工作
- 实时抓取需要 ~10 秒（两次请求，含延迟）
- 赛程数据需要先运行 `python scripts/scrape_team_schedules.py` 生成缓存

---

## 2026-01-23 (续)

### 教练评估模型 - 基于残差分析

**目标：** 量化评估 NBA 主教练的执教水平，使用 TCI 和 DefRtg 模型的残差作为代理指标。

**核心思路：**
```
教练贡献 ≈ 实际表现 - 模型预测的"纸面实力"
```
- **进攻残差 (Off_Residual)** = 实际 OffRtg - 预测 OffRtg
- **防守残差 (Def_Residual)** = 预测 DefRtg - 实际 DefRtg（符号反转，正值=更好）
- **总分 (Total_Score)** = Off_Residual + Def_Residual

**脚本：**
- `scripts/evaluate_coaches.py` - 2025-26 赛季教练评估
- `scripts/evaluate_coach_career.py` - 单个教练生涯评估

---

### 教练数据验证与修正

**问题：** 最初使用硬编码的教练数据（来自我的训练数据，截止 2025 年 5 月），存在过时信息。

**解决方案：**
1. 尝试从 NBA.com 抓取教练数据 → 部分赛季数据不准确
2. 使用 Basketball-Reference 验证 → 获得准确的历史数据

**2025-26 赛季换帅（我的训练数据没有）：**
| 球队 | 旧教练 | 新教练 |
|------|--------|--------|
| Denver Nuggets | Michael Malone | **David Adelman** |
| Memphis Grizzlies | Taylor Jenkins | **Tuomas Iisalo** |
| New York Knicks | Tom Thibodeau | **Mike Brown** |
| Phoenix Suns | Mike Budenholzer | **Jordan Ott** |
| Portland Trail Blazers | Chauncey Billups | **Tiago Splitter** |

**输出文件：**
- `data/newly_scraped/coaches_by_season_verified.json` - 经 BR 验证的教练数据 (5 个赛季)
- `data/analysis/coach_evaluation_2025_26.csv` - 2025-26 教练评估结果

---

### 2025-26 教练完整排名（修正版）

| 排名 | 教练 | 球队 | 战绩 | 进攻+ | 防守+ | 总分 |
|------|------|------|------|-------|-------|------|
| 1 | Jordi Fernandez | Brooklyn Nets | 12-29 | +1.12 | +0.87 | **+1.99** |
| 2 | Mike Brown | New York Knicks | 25-18 | +1.11 | +0.64 | **+1.75** |
| 3 | Tyronn Lue | LA Clippers | 19-23 | +1.08 | +0.24 | +1.32 |
| 4 | Steve Kerr | Golden State Warriors | 25-19 | +0.47 | +0.64 | +1.11 |
| 5 | Mark Daigneault | Oklahoma City Thunder | 36-8 | +0.28 | +0.60 | +0.89 |
| ... | ... | ... | ... | ... | ... | ... |
| 11 | **Ime Udoka** | **Houston Rockets** | 25-15 | -0.65 | **+0.86** | +0.21 |
| ... | ... | ... | ... | ... | ... | ... |
| 28 | Brian Keefe | Washington Wizards | 10-32 | -0.63 | -1.10 | -1.74 |
| 29 | JJ Redick | Los Angeles Lakers | 25-16 | -1.79 | -0.16 | -1.95 |
| 30 | Chris Finch | Minnesota Timberwolves | 27-16 | -2.02 | -0.12 | **-2.13** |

**关键发现：**
- **防守型教练**：Ime Udoka (+0.86 防守), Willie Green (+0.71), Mark Daigneault (+0.60)
- **进攻型教练**：Jordi Fernandez (+1.12 进攻), Mike Brown (+1.11), Tyronn Lue (+1.08)

---

### Ime Udoka 生涯评估

| 赛季 | 球队 | 战绩 | 胜率 | 进攻+ | 防守+ | 总分 |
|------|------|------|------|-------|-------|------|
| 2021-22 | Boston Celtics | 51-31 | 62.2% | +0.47 | +0.19 | +0.66 |
| 2023-24 | Houston Rockets | 41-41 | 50.0% | -0.51 | -0.39 | -0.90 |
| 2024-25 | Houston Rockets | 52-30 | 63.4% | -0.22 | +0.52 | +0.30 |
| 2025-26 | Houston Rockets | 25-15 | 62.5% | -0.37 | +0.77 | +0.40 |
| **生涯** | | **169-117** | **59.1%** | **-0.16** | **+0.27** | **+0.12** |

**结论：** 中等偏上的**防守型教练**，生涯防守残差 +0.27，联盟第 17 位（48 位教练中前 65%）

---

### NBA Inside the Game 新数据抓取

抓取了 NBA 官网的三个新高级统计数据：

**1. Leverage（影响力指数）**
- URL: `https://www.nba.com/inside-the-game/player/leverage`
- 含义：球员对球队胜率的影响程度（1.0 = 贡献 10% 胜率）
- 抓取数量：264 名球员
- 输出文件：`data/newly_scraped/leverage_stats_full.csv`

| 排名 | 球员 | 球队 | 总 Leverage | 进攻 | 防守 |
|------|------|------|-------------|------|------|
| 1 | Nikola Jokić | DEN | **5.21** | 2.61 | 2.60 |
| 2 | Shai Gilgeous-Alexander | OKC | 3.87 | 1.80 | 2.07 |
| 3 | Tyrese Maxey | PHI | 3.09 | 0.52 | 2.57 |

**2. Gravity（引力指数）**
- URL: `https://www.nba.com/inside-the-game/player/gravity`
- 含义：球员吸引防守注意力的程度
- 抓取数量：264 名球员
- 输出文件：`data/newly_scraped/gravity_stats_full.csv`

| 排名 | 球员 | 球队 | Gravity | On-Ball | Off-Ball |
|------|------|------|---------|---------|----------|
| 1 | Stephen Curry | GSW | **20.5** | 15.2 | 29.7 |
| 2 | Kevin Durant | HOU | 17.0 | 15.1 | 18.5 |
| 3 | Luka Dončić | LAL | 15.8 | 19.1 | 17.6 |

**3. Shot Difficulty（投篮难度）**
- URL: `https://www.nba.com/inside-the-game/shot-difficulty`
- 含义：xFG%（预期命中率）vs 实际 FG%
- 抓取数量：136 名球员
- 输出文件：`data/newly_scraped/shot_difficulty_stats_full.csv`

| 排名 | 球员 | 球队 | xFG% | FG% | FG%+ |
|------|------|------|------|-----|------|
| 1 | Nikola Jokić | DEN | 47.8 | 60.5 | **+12.7** |
| 2 | Shai Gilgeous-Alexander | OKC | 47.4 | 55.5 | +8.1 |
| 3 | Cam Spencer | MEM | 39.7 | 47.6 | +7.9 |

**关键发现：**
- Jokić 在 Leverage 和 Shot Difficulty 都是独一档
- Stephen Curry 的 Off-Ball Gravity (29.7) 远超所有人
- 火箭 Kevin Durant Gravity 排名第 2，说明仍是顶级进攻威胁

**抓取脚本：**
- `scripts/scrape_leverage.py`
- `scripts/scrape_leverage_full.py`
- `scripts/scrape_coaches.py`

---

## 2026-01-23

### DefRtg 预测模型 v1

**背景：** 完成进攻端 TCI 模型后，转向防守端研究。建立类似的 DefRtg 预测模型。

**数据来源 (5 个赛季: 2021-22 至 2025-26)：**
| 数据类型 | 文件数 | 来源 |
|----------|--------|------|
| defense_dash_overall | 32 | 整体防守 FG% |
| defense_dash_lt6 | 32 | 篮下防守 (<6ft) |
| hustle | 31 | 抢断、干扰投篮等 |
| opponent_shooting_zone | 30 | 对手各区域命中率 |
| four_factors | 32 | 对手 eFG%、TOV%、FTA Rate |

**模型特征 (16 个)：**

| 特征 | 权重 | 解释 |
|------|------|------|
| **Opp_eFG_Pct** | **+4.31** | 对手有效命中率（最重要） |
| **Opp_TOV_Pct** | **-2.28** | 迫使对手失误率 |
| **DREB_Pct** | **-1.70** | 防守篮板率 |
| **Opp_FTA_Rate** | **+0.65** | 对手罚球率 |
| Overall_DFG_Pct | -0.21 | 整体防守 FG% |
| Rim_Diff_Pct | +0.13 | 篮下防守差值 |
| Overall_Diff_Pct | -0.07 | 整体防守差值 |
| Rim_DFG_Pct | -0.07 | 篮下防守 FG% |
| Opp_3PT_FG_Pct | +0.05 | 对手三分命中率 |
| Deflections | -0.04 | 干扰传球次数 |
| Opp_MidRange_FG_Pct | +0.04 | 对手中距离命中率 |
| DEF_Loose_Balls | -0.02 | 防守松散球 |
| Opp_Rim_FG_Pct | -0.02 | 对手篮下命中率 |
| Opp_Paint_FG_Pct | -0.02 | 对手油漆区命中率 |
| Charges_Drawn | +0.01 | 造进攻犯规 |
| Contested_Shots | +0.00 | 干扰投篮次数 |

**模型性能：**

| 指标 | 训练集 | 验证集 |
|------|--------|--------|
| **R²** | 0.9718 | **0.9501** |
| **RMSE** | 0.84 | 1.05 |
| 样本数 | 840 | 120 |
| R² Drop | | 0.0217 |

**关键发现：**

1. **Four Factors 防守版本主导模型**
   - Opp_eFG_Pct (+4.31) 是最重要特征，类似进攻端的 eFG_Pct (+4.15)
   - 前四大特征都是 Four Factors (防守版)，占权重 90%+

2. **Hustle 数据影响有限**
   - Deflections、Contested_Shots 等权重都 < 0.05
   - 可能原因：这些是过程指标，而 Four Factors 直接衡量结果

3. **与进攻模型对比**
   | 对比项 | 进攻 (TCI v5) | 防守 (DefRtg v1) |
   |--------|---------------|------------------|
   | 最重要特征 | eFG_Pct (+4.15) | Opp_eFG_Pct (+4.31) |
   | Validation R² | 0.9271 | 0.9501 |
   | R² Drop | 0.0446 | 0.0217 |

**2026 年 1 月预测分析：**

| 预测偏差类型 | 球队 | 实际 | 预测 | 差值 |
|--------------|------|------|------|------|
| 被低估（防守更好） | LA Clippers | 114.3 | 117.2 | -2.9 |
| 被低估（防守更好） | San Antonio Spurs | 107.5 | 110.3 | -2.8 |
| 被高估（防守更差） | Boston Celtics (10月) | 111.2 | 107.8 | +3.4 |

**输出文件：**
- `scripts/build_defrtg_model_monthly.py` - 模型训练脚本
- `data/analysis/defrtg_model_monthly.json` - 模型参数
- `data/analysis/defrtg_predictions_2025_26.csv` - 预测结果

---

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

### PlayType 对 eFG% 的影响分析

**数据：** 352 个 PlayType 文件（5 个赛季，11 种 PlayType）

**各 PlayType 效率排名：**
| PlayType | eFG% | PPP | 使用率 |
|----------|------|-----|--------|
| Cut (空切) | 66.7% | 1.31 | 6.9% |
| Transition (转换) | 60.8% | 1.13 | 18.4% |
| Putbacks (二次进攻) | 58.1% | 1.12 | 5.3% |
| Roll-man (顺下) | 57.4% | 1.11 | 5.3% |
| Spot-up (定点) | 53.2% | 1.05 | 24.4% |
| Isolation (单打) | 45.0% | 0.92 | 7.2% |

**关键发现：执行质量 > 战术选择**
- 高效球队在几乎所有 PlayType 上 eFG% 都更高
- Isolation 执行差距最大：高效队 49.3% vs 低效队 44.8% (+4.5%)
- PlayType 使用频率与球队整体 eFG% 相关性很弱（< 0.15）
- 结论：球队 eFG% 高是因为"做什么都更准"，而非"选择更好的战术"

### 主客场与赛程密集度分析

**新增数据抓取：**
- 脚本: `scripts/scrape_home_away_monthly.py`
- 抓取 5 个赛季主客场分开的 team_advanced 数据（64 个文件）
- 数据保存: `data/newly_scraped/tracking_monthly/*/team_advanced_*_home.csv` 和 `*_road.csv`

**主场优势分析结果：**
| 指标 | 主场 | 客场 | 差异 |
|------|------|------|------|
| **OffRtg** | 114.4 | 112.4 | **+2.0** |
| eFG% | 54.6% | 53.7% | +0.8% |
| TOV% | 13.9% | 14.2% | -0.2% |
| OREB% | 28.7% | 28.3% | +0.4% |

- **T检验 p < 0.0001**，统计高度显著
- 主场优势来源：投篮更准、失误更少、篮板更好

**主场优势差异最大的球队 (2024-25 + 2025-26)：**
| 主场优势最大 | | 主场优势最小 | |
|--------------|--------|--------------|--------|
| 快船 | +5.4 | 老鹰 | -2.7 |
| 雄鹿 | +4.9 | 公牛 | -1.9 |
| 凯尔特人 | +4.6 | 掘金 | -1.7 |

**赛程密集度分析：**
- 月度 GP 与 OffRtg 相关性仅 0.10
- 原因：月度数据粒度太粗，无法捕捉 back-to-back 等疲劳效应

**对模型的建议：**
| 场景 | 主客场特征 | 赛程密集度 |
|------|------------|------------|
| 月度预测 | 用处不大（被平均化） | 用处不大（粒度太粗） |
| **单场预测** | **非常重要 (+2.0)** | 需要 back-to-back 标记 |

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
