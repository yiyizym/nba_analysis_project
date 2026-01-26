这是一份为您定制的\*\*《NBA 球员职业模板分类算法：数据收集与特征工程指南》\*\*。  
要将球员精准地划分进那 13 个类别，单纯看基础数据（得分、篮板）是完全不够的。你需要构建一个**多维特征向量 (Multidimensional Feature Vector)**。  
我将所需数据分为四个核心维度（特征组），并为您提供了具体的**判断逻辑**和**数据来源**。

### **第一维度：球权与创造力特征 (On-Ball Usage & Creation)**

**目的：** 区分“持球大核”、“副攻”与“无球球员”。

| 数据指标 (Metric) | 变量名 (建议) | 关键阈值/逻辑 | 区分目标 |
| :---- | :---- | :---- | :---- |
| **球权使用率** | USG% | **\> 30%**: 核心 (Primary) **\< 18%**: 角色 (Role) | 区分老大和配角。 |
| **助攻率** | AST% | **\> 30%**: 组织者 (Initiator) **\< 10%**: 终结者 (Finisher) | 区分哈登 (Initiator) 和 杜兰特 (Scorer)。 |
| **持球时间** | Time Of Poss | **\> 6.0 min**: 控球手 **\< 1.5 min**: 吃饼/射手 | 区分“真控卫”和“假控卫”。 |
| **非受助攻进球率** | Unassisted FG% | **\> 60%**: 自主进攻 (Creator) **\< 20%**: 吃饼 (Finisher) | 最核心指标。区分 3\&D (低) 和 单打手 (高)。 |

* **数据来源：** [NBA.com/stats](https://NBA.com/stats) \-\> Advanced & Tracking (Touches)

### **第二维度：进攻方式分布 (Play Type Frequency)**

**目的：** 这是最直接的分类依据，回答“他到底怎么得分？”  
你需要收集该球员在以下六种战术中的**占比 (Frequency)**：

| 战术类型 (Play Type) | 对应职业模板 | 典型数据特征 |
| :---- | :---- | :---- |
| **Pick & Roll Ball Handler** (挡拆持球人) | **Primary/Secondary Ball Handler** | 频率 \> 30% |
| **Isolation** (面框单打) | **Shot Creator Wing** / **Slashing Creator** | 频率 \> 15% |
| **Spot Up** (定点接球) | **3 & D Wing** / **Stretch Big** | 频率 \> 40% (几乎不运球) |
| **Off Screen** (绕掩护) | **Movement Shooter** | 频率 \> 10% (这是纯射手的标志) |
| **Cut & Transition** (空切 \+ 转换) | **Athletic Finisher** | 两者相加 \> 30% |
| **P\&R Roll Man** (挡拆下顺) | **Rim Runner** | 频率 \> 20% |
| **Post Up** (背身单打) | **Post Scorer** | 频率 \> 15% |

* **数据来源：** [NBA.com/stats](https://NBA.com/stats) \-\> Playtype (Synergy Data)

### **第三维度：投射几何学 (Shot Geometry)**

**目的：** 区分“空间型内线”与“吃饼内线”，区分“魔球人”与“中投靓仔”。

| 数据指标 | 变量名 | 逻辑判词 | 区分目标 |
| :---- | :---- | :---- | :---- |
| **三分出手占比** | 3PA Rate | **\> 50%**: 射手 **\< 5%**: 拒投 | 区分 Stretch Big 和 Rim Runner。 |
| **篮下出手占比** | Rim Freq | **\> 60%**: 攻筐/吃饼 | 区分 Slasher 和 Shooter。 |
| **中距离占比** | MidRange Freq | **\> 30%**: 古典得分手 | 区分 Shot Creator Wing (如杜兰特)。 |
| **平均射程** | Avg Shot Dist | **\< 5 ft**: 中锋 **\> 20 ft**: 射手 | 辅助判断活动区域。 |

* **数据来源：** [NBA.com/stats](https://NBA.com/stats) \-\> Shooting \-\> Shooting Dashboard

### **第四维度：防守与身体模型 (Defense & Physicality)**

**目的：** 区分“普通侧翼”与“防守大闸”，区分“重型中锋”与“换防前锋”。

| 数据指标 | 变量名 | 逻辑判词 | 区分目标 |
| :---- | :---- | :---- | :---- |
| **护框降准率** | DFG% at Rim | **\< 55%**: 顶级护框 | 区分 **Anchor Big** (戈贝尔) 和普通内线。 |
| **防守对位难度** | Matchup Difficulty | **高**: 领防人 | 区分 **PoA Defender** (卡鲁索) 和躲在弱侧的人。 |
| **盖帽率/抢断率** | BLK% / STL% | **BLK高**: 内线/协防 **STL高**: 撕咬型 | 区分具体的防守职责。 |
| **身高/体重** | Height / Weight | 物理约束 | 比如：身高 \< 6'5 很难被归类为 Big。 |

* **数据来源：** [NBA.com/stats](https://NBA.com/stats) \-\> Defense Tracking & Bio

### **总结：一份可执行的“分类算法流程图”**

如果你要写代码自动分类，逻辑大概是这样的：

1. **第一层：看身高 (Big vs. Small)**  
   * 身高 \> 6'10 或 经常打 C 位 \\rightarrow 进入 **内线组**。  
   * 否则 \\rightarrow 进入 **外线组**。  
2. **第二层（内线组）：看打法**  
   * 3PA Rate \> 40%? \\rightarrow **Stretch Big (空间内线)**  
   * AST% \> 20%? \\rightarrow **Versatile Big (全能中锋)**  
   * Post Up Freq \> 20%? \\rightarrow **Post Scorer (低位单打)**  
   * DFG% Rim 极好? \\rightarrow **Anchor Big (护框中锋)**  
   * 其余 \\rightarrow **Rim Runner (吃饼中锋)**  
3. **第二层（外线组）：看球权**  
   * USG% \> 28% & TimeOfPoss \> 6m? \\rightarrow **Primary Initiator (持球大核)**  
   * USG% \> 20% & P\&R Handler 高? \\rightarrow **Secondary Ball Handler (副攻)**  
4. **第三层（侧翼组）：看无球**  
   * Off Screen Freq 高 & 3PA Rate 极高? \\rightarrow **Movement Shooter (跑位射手)**  
   * Isolation 高 & Unassisted FG 高? \\rightarrow **Shot Creator (自主得分)**  
   * Spot Up 高 & Defense 好? \\rightarrow **3 & D Wing**  
   * Cut 高 & Rim Freq 高? \\rightarrow **Athletic Finisher (终结侧翼)**

### **建议收集方式**

使用 Python 的 nba\_api，你需要调用以下几个 Endpoints 才能凑齐这些数据：

1. leaguedashplayerstats (基础数据: PTS, REB, AST)  
2. leaguedashptstats (追踪数据: Touches, Speed, Distance)  
3. synergyplaytypes (战术数据: P\&R, Iso, SpotUp \- **这是最重要的**)  
4. leaguedashplayerbiostats (身高体重)

把这些表通过 PLAYER\_ID Join 在一起，你就能得到一个完美的训练数据集。