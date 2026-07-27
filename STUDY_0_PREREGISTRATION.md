# Study 0 预注册 — NQ Opening Drive **Continuation** 图谱与 Edge 天花板

```yaml
id: S0
version: 0.4   # v0.3 → v0.4：MC 交接改为每合约日内路径；判定统计量两层化；TP/FP 选日规则冻结
status: DRAFT — 待 Aaron diff 复核；冻结时本字段在 Freeze Commit A 内改为 FROZEN
date: 2026-07-27
trial_ledger: formal_trial_count 登记 S0 = 1；researcher_exposure 另行记账（见 §9）
```

## 0. 研究问题与非目标

- Q1：NQ 的 opening drive（09:30–10:00 方向性移动）之后，**顺驱动方向**的延续现象基础率与分布如何？
- Q2：在 10:00 只完美知道"今天顺驱动方向交易是否值得"（不知道任何未来价格路径、不知道反转）的 Oracle，受可执行约束与 Micro 整数仓位约束后，成本后表现如何？
- Q3：将 Oracle 的**逐日 USD P&L 分布**交给 Prop MC，由**商业 EV** 裁决 GO / STOP / 边界区。

**非目标**：不开发入场信号、不做参数扫描、不做 ML、不评估真实策略、不宣称统计发现。
**明确排除**：opening drive 失败后的反转研究属于未来独立 Study/H2，不得混入本次 continuation 天花板。

## 1. 数据与数据角色（四角色隔离）

| 角色 | 数据 | 范围 | 状态与允许用途 |
|---|---|---|---|
| Development | NQ.v.0 ohlcv-1m | 2010-06-06 → 2022-01-01(excl) | 本计划采购（PP items A1）；S0 全部 alpha 侧计算仅用此段 |
| Internal Validation (IV) | NQ.v.0 ohlcv-1m | 2022-01-01 → 2025-07-01(excl) | **现在不采购、不存在于本机**；H1 冻结 commit 完成后作为独立采购（A3）另行批准；访问预算 1 次；IV 失败 = 假设死亡 |
| Execution Cost Calibration | MNQ.v.0 bbo-1s | 2025-01-01 → 2025-04-01(excl) | 本计划采购（A2）。仅成本统计。工程隔离：`cost_calibration/` 读取原始 BBO，只输出 `spread_cost_table.parquet`；`alpha_research/` 只能读取该表；价格方向/收益/信号表现不得用于任何 alpha 分析 |
| Physical Lockbox | 2025-07-01 → 最终评估日 | 不购买、不存在于本机 |

- Bar 时间戳约定：`ts_event` = bar 开始时刻；"HH:MM bar" 指以该时刻开始的 1 分钟 bar。
- 换月：`is_roll_transition` = continuous 映射实际切换的交易日；`is_roll_window` = 切换日前后各 2 个 RTH 交易日；symbology 映射随数据归档。
- `.v.0` 按**前一交易日**成交量排名换月（无当日前视，已核官方说明）；管道验证项：
  实证检查映射从不在同一 RTH session 内切换；禁止把 roll jump 解释为 alpha。

## 2. Development 内部稳定性检查（替代 IV 访问）

时代切片 2010–2013 / 2014–2017 / 2018–2021；按年表格（强制）＋ leave-one-year-out；
多空分开；20 日实现波动率三分位分层。

## 3. Session 与时间（冻结）

时区 America/New_York；RTH 09:30–16:00；观察窗 09:30–09:59 bar；决策 10:00；
入场价 = 10:00 bar 开盘价 ± 成本；强制退出以 15:44 bar 收盘价 ± 成本；
隔夜区间 = 前日 18:00 → 当日 09:30；日历 = pandas-market-calendars(CME Equity) ＋ CME 通告核对；DST/假日单元测试。
**剔除日**（仅此三类）：半日市；RTH 无成交；RTH bar 缺失 > 10%。
**NA 政策**：除剔除日外不得整日删除；特征无法计算记 NA，该日仍进入 Oracle 总体统计；每表强制报告 NA 数。

## 4. 归一化与特征（公式唯一化；全矩阵报告）

**归一化 ADR14** = 前 14 个完整 RTH 交易日 (RTH high − RTH low) 均值（不含当日）。

| # | 特征 | 定义 |
|---|---|---|
| F1 | ret_open30 | (C₀₉₅₉ − O₀₉₃₀) / ADR14 |
| F2 | or_width | (H − L)₀₉₃₀₋₁₀₀₀ / ADR14 |
| F3 | de_open30 | 见下方唯一公式 |
| F4 | rvol_open30 | Vol(09:30–10:00) ÷ 前 60 交易日同窗中位数；roll window 内分层解读 |
| F5 | gap | (O₀₉₃₀ − 前日 RTH 收盘) / ADR14；is_roll_transition 日记 NA |
| F6 | open_loc_on | (O₀₉₃₀ − ON_low)/(ON_high − ON_low) ＋ above/inside/below |
| F7 | on_range | (ON_high − ON_low) / ADR14 |
| F8 | retrace_open30 | 见下方唯一公式 |
| F9 | close_pos_open30 | (C₀₉₅₉ − L)/(H − L) 窗口内 |
| F10 | is_event_day | ∈ {CPI, NFP, FOMC, none}（BLS/Fed 官方时刻表快照） |
| F11 | is_roll_transition / is_roll_window | 见 §1 |

**F3（close-path 版本，禁止改用分钟 high/low）**：

```
path_open30 = |C0930 − O0930| + Σ[t=09:31..09:59] |C_t − C_(t−1)|
de_open30   = |C0959 − O0930| / path_open30
```

**F8（方向化 running-max 回撤）**：

```
z_t = d_open × (C_t − O0930)，t ∈ [09:30..09:59]
max_retrace     = max_t [ max_(u≤t)(z_u) − z_t ]
retrace_open30  = max_retrace / |C0959 − O0930|     （分母为 0 → NA）
```

## 5. 方向与标签

**d_open = sign(ret_open30)**；ret_open30 = 0：无方向、不可交易、单独计数报告。

| # | 标签 | 定义 | 地位 |
|---|---|---|---|
| **Y_cont** | **d_open × (C₁₅₄₄ − O₁₀₀₀) / ADR14** | 主标签：延续幅度 | Oracle 判定用 |
| Y1 | (C₁₅₄₄ − O₁₀₀₀) / ADR14 | 双向下午收益 | 仅描述，禁用于 Oracle 方向 |
| Y2 | de_pm（close-path 版本，见下） | 下午方向效率 | 描述 |
| Y3 | close_pos_pm | 收盘位置 | 描述 |
| Y4/Y5 | MFE/MAE | 相对 d_open 自 O₁₀₀₀ 起算，/ADR14 | 描述＋E1 输入 |
| Y6 | cont_decile | Y_cont 在 Development 分年内十分位 | 描述 |

**Y2（唯一公式）**：

```
path_pm = |C1000 − O1000| + Σ[t=10:01..15:44] |C_t − C_(t−1)|
de_pm   = |C1544 − O1000| / path_pm
```

## 6. 成本模型（可编码；参数在首次计算前锁定）

**结构**：`market_friction`（spread＋滑点，来自 CostCal 表）＋ `platform_fee`（期货 prop 候选官方费率快照中较保守者；FTMO 为 CFD 不进入 S0 费率场景；禁止见结果后改选）。

- `spread_cost_table` 中的 spread 为**完整 bid–ask 宽度**；每边成交使用 **spread/2**。
- 场景：Base = 时段中位＋1 tick/边；Conservative = P90＋2 tick/边；
  **Stress = Base 的 market_friction × 2（platform_fee 不重复翻倍）**；Severe = P95＋3 tick/边。
- 代理假设明示：2025Q1 spread 分布用于其他年份，四档场景共同覆盖该不确定性。

**成交公式（d = +1 多头，−1 空头）**：

```
entry_fill      = P_ref + d × (spread/2 + slippage)
timed_exit_fill = P_ref − d × (spread/2 + slippage)

止损（1 分钟 OHLC）：
  多头 gap 穿越: trigger_ref = min(stop, bar_open)
  空头 gap 穿越: trigger_ref = max(stop, bar_open)
  bar 内触及:    trigger_ref = stop
  stop_fill = trigger_ref − d × (spread/2 + adverse_slippage)
  禁止假设永远在 stop 价成交
```

## 7. 双 Oracle（方向永远 = d_open；冻结）

延续事件：**Y_cont ≥ θ**；θ 主 0.5、副 0.3（完整报告，不得事后升格）。
Oracle 只在延续事件日交易，方向恒为 d_open，仅知"今天顺驱动交易值得"。

- **理论 Oracle**（仅经济上限）：10:00 开盘价按 d_open 入场，d_open 方向后续最有利价格退出，减 Base 成本。
- **可执行 Oracle**：10:00 开盘价 ± 成本；每日至多 1 笔；不隔夜。

| 引擎 | 定义 | 地位 |
|---|---|---|
| E1 | 初始止损 = 开盘区间对侧极值；未触发则 15:45 退出 | 资本约束主引擎 |
| E2 | 无止损，15:45 定时退出 | 执行上限参照；强制报告最差日 P1/P5 |

E3 已删除（留待 H1）。1R = E1 初始止损距离（仅归一化）；**所有结果同时以 USD / 1 MNQ 报告**。

## 8. 整数仓位粒度输出（强制）

逐日输出：`stop_distance_points`、`risk_usd_per_1_MNQ_planned`（正常 stop 成交＋成本）、
`risk_usd_per_1_MNQ_realized`（含 gap 穿越真实损失）、`cost_usd_per_1_MNQ`、
`cost_as_pct_of_R`、`minimum_1_contract_risk`。
非决策性风险预算 {$50, $75, $100, $150} 下报告可执行覆盖率；不从中挑选，仅供 MC。

## 9. 统计与两本台账（冻结）

- Primary：stationary bootstrap，期望块长 5 交易日，10,000 次，seeds {7,13,31}，百分位法 95% CI；Sensitivity：块长 21。
- formal_trial_count：S0 = 1。
- researcher_exposure：全部查看记录入 EXPOSURE_LEDGER.md，作为**保守上界**完整报告；
  正式多重检验须预注册从 raw exposure 推导相关性调整后 N_eff 的方法（或使用适合相关候选的校正），
  禁止只用最终存活版本数。

## 10. Kill Gate（Checkpoint 0 —— 由 MC 商业 EV 直接裁决）

### 10.1 交接单位：每 1 手 MNQ 的日内交易路径（非日终向量）

Topstep 实时监控含未实现盈亏的 MLL、盘中触及即违规（官方确认）；E2 无止损时
"盘中 −$1,800、收盘 +$300" 的日子在日终向量里是盈利日、在实时判违规平台上是爆仓日。
因此 S0 向 MC 交付的**原子记录**为（每引擎 × 每成本场景，每笔、每合约）：

```
trade_date, entry_timestamp, exit_timestamp, direction,
entry_fill, exit_fill, final_pnl_per_contract,
running_pnl_1m[]           # 1 分钟 mark-to-market 全路径（保留，不只压缩统计）
max_adverse_pnl, max_favourable_pnl, time_of_max_adverse,
planned_stop, actual_stop_fill, stop_triggered
```

**仓位逻辑归属**：S0 不再按风险预算预生成固定向量；下 0/1/N 手、buffer 不足跳过、
合约上限、平台状态缩仓，全部由 MC 依账户当时状态决定。§8 的 {$50–$150} 预算档
仅保留为描述性覆盖率报告。

**开放核实项（Gate 1 阻断）**：Lucid EOD 回撤的盘中违规判定在第三方描述中互相矛盾
（"盘中回落不爆仓" vs "盘中触及即违规"）；必须以官方 Level-2 快照钉死；
钉死前 MC 对 Lucid 同时建模两种变体并分别报告。

### 10.2 封存顺序（冻结）

`MC_METHOD_SPEC`（方法、平台规则快照、risk policy 组合、EV 判定条件、重抽次数与 seeds）
必须在**任何人查看 S0 数字结果之前** commit 冻结（tag `mc-freeze-v1`）。顺序：
冻结 S0 规范 → 冻结 MC_METHOD_SPEC → 冻结 Gate 1 费用快照 → 运行 S0 与 MC → 合并判决。
S0 代码可并行开发，但在 MC_METHOD_SPEC 冻结前不得运行产出可读报告。

### 10.3 两层不确定性（判定统计量的定义）

- **认知层（epistemic）**：对历史交易日做 block bootstrap 形成 B 个数据世界；
  每个世界内运行大量平台路径模拟并**取均值**，得到该世界的平均商业 EV；
  B 个均值构成 **估计均值 EV 的分布** —— 判定分位数作用于此分布。
- **结果层（aleatoric）**：单账户尝试的结果分布（含挑战费损失概率、尾部、离散度）
  单独完整报告，用于 bankroll 与多账户规划，**不作为 GO 门槛**。
  ——若把判定分位数直接作用于单次尝试结果分布，挑战费的二元损失质量会使
  P5 几乎永远为负，GO 将系统性无法触发（对 GPT 提案的必要修正）。

### 10.4 判定表（统计量 = 认知层分布；组合 = 平台 × 账户类型 × risk policy × sizing policy）

| 判定 | 条件 |
|---|---|
| **STOP** | E1 与 E2 的所有预注册组合：Conservative 下认知层 P95 ≤ 0 |
| **GO** | 存在**同一**E1 组合：Conservative 下认知层 P5 > 0 **且** Stress 下认知层中位数 ≥ 0，且整数仓位、频率、payout 路径可行性经 MC 确认 |
| **边界区 α** | 非 STOP 非 GO，且有 E1 组合 Conservative 认知层中位数 > 0 |
| **边界区 β** | 所有 E1 组合不成立但存在 E2 组合 Conservative 认知层 P5 > 0；或 E1 满足 EV 条件而可行性未过 |

边界区处理：一次预注册检查（α：敏感性检查；β：替代风险结构检查）后**强制一次性判决**，
判据冻结为：同一组合 Conservative 认知层中位数 > 0 且 Stress 认知层中位数 ≥ 0 → GO，否则 STOP。

### 10.5 EV 台账定义（MC 输出，全部报告）

`strategy_account_EV`（平台内交易 EV）→ `prop_operating_EV`（含评估费/重置/订阅与重购政策）
→ `net_business_EV_after_RD`（扣数据摊销与 R&D burn）→ `risk_haircut_EV`（Gate 4 场景折扣后）。
**Checkpoint 0 判定表使用 `prop_operating_EV`**；最终部署要求 `risk_haircut_EV > 0`。
EV 计量单位：预注册重购政策下 T 月期的月均净 USD（T 在 MC_METHOD_SPEC 冻结）。

**频率输出（强制）**：延续事件基础率 p、每年可交易日数、Oracle 月均频率、附录 A 网格预期交易数。
MVE 概念保留为解释性诊断与 classifier feasibility 工具，不作最终生死判据。
辅助直觉检查（不决定 GO）：q_min ≤ min(65%, 2.2p)。

## 11. 禁止事项

参数扫描、多窗口 ORB、指标族、ML、delta、回踩、入场优化、反转研究、S0 访问 IV、
访问/购买 lockbox、alpha 侧读取 CostCal 原始 BBO、MC_METHOD_SPEC 冻结前运行可读 S0 报告、
依据结果修改冻结定义。

## 12. 冻结机制（两阶段 commit）

1. **Freeze Commit A**：仅含冻结文档（本文件＋PROJECT_CHARTER.md）；annotated tag `s0-freeze-v1`。
2. **Registry Commit B**：Commit A 内文件 SHA-256 ＋ Commit A hash 写入 FREEZE_LOG.md 后提交；锚定 Commit A。
3. **Purchase Approval Commit C**：purchase_plan.yaml 批准字段（含 canonical 哈希，见该文件算法）单独提交；
   执行脚本核对哈希与实际可用 credit ≥ 实际重报价，否则中止。
4. `MC_METHOD_SPEC` 冻结适用同样的两阶段流程（tag `mc-freeze-v1`）。

## 附录 A：precision–recall 可行性 —— 经验分布混合法（主要方法）

对每个引擎与成本场景，预先构建两个**经验 USD P&L 分布**：

```
D_TP：Y_cont ≥ θ 的日子，按真实 E1/E2 规则交易（方向 d_open）的逐日 USD P&L
D_FP：Y_cont < θ 的日子，仍按 d_open 方向按同规则交易的逐日 USD P&L
```

对每个 (precision q, recall r) 网格点（q ∈ {0.35..0.75}, r ∈ {0.2..0.8}）：

1. 从 D_TP 按 recall 抽取 true positives；
2. 从 D_FP 补足 false positives 使组合达到 precision q；
3. **选日规则（冻结）**：TP 必须在 Y_cont ≥ θ 日中、FP 必须在 Y_cont < θ 日中
   按 year × volatility_regime × event_flag 分层后**层内均匀随机**选择，使用预注册
   seeds {7, 13, 31}；**禁止**按未来 P&L、MFE、Y_cont 幅度或任何结果标签排序选择——
   否则网格会变成"不仅知道哪些日子是 TP、还知道哪些 TP 最赚钱"的半 Oracle。
   均匀抽样 = 幅度中性假设，是可行性的保守下界；任何"分类器偏好大幅度日"的
   加成主张只能由 H1 用真实特征证明；
4. 形成交易日标记序列，与每合约日内路径（§10.1）共同交给 MC；
5. 可行区域 = {(q,r) : prop_operating_EV 认知层 P5 > 0 于至少一个预注册组合}。

年交易数 F(q,r) = p·r·N/q（N≈252）随网格一并报告。
**网格地位限定**：仅为可行性边界，不构成 H1 表现宣称；禁止因某格漂亮而把该格的
时间选择模式反向用于分类器设计。
参数化公式 E(q) = q·mean(D_TP) − (1−q)·|mean(D_FP)| 仅作 sanity check，不作为主要计算。

---
### 修订记录
**v0.1 → v0.2**（GPT 评审，7 项全采纳）：Oracle 方向修复（d_open）；四数据角色＋隔离；IV 预算 1；
E1/E2 双判据＋E3 删除；MVE 函数化；ADR14；成交公式化；整数仓位输出；bootstrap 规格；两阶段冻结。
**v0.2 → v0.3**（GPT 终审 3 项＋Claude 补丁 2 项）：
1. 判定表去标量化 —— 直接以 MC net_business_EV 裁决；MVE 降级为诊断工具；新增封存顺序（MC_METHOD_SPEC 先于 S0 结果）。
2. 附录 A 改为 D_TP/D_FP 经验分布混合法；−1R 近似降级为 sanity check。
3. F3/F8/Y2 公式唯一化（close-path 版本）；成本公式补 spread/2、Stress 范围、signed-d、gap 穿越 trigger_ref；风险输出分 planned/realized。
4. [Claude 补丁] GO 条件要求 Conservative 与 Stress 由**同一组合**满足，防止拼凑通过。
5. [Claude 补丁] E1 满足 EV 但可行性未过 → 归入边界区 β，避免判定表出现未定义单元格。

**v0.3 → v0.4**（GPT 第二轮终审 2 项＋Claude 修正 1 项＋抽样规则）：
1. [GPT，采纳] MC 交接单位改为每 1 手 MNQ 的日内 1 分钟 P&L 路径（Topstep 实时判违规已官方证实）；
   S0 与 MC 的仓位逻辑解耦（预算档降为描述性）；新增 Lucid 盘中/日终判违规开放核实项。
2. [GPT，采纳＋修正] 判定加入分位数门槛，但统计量修正为**认知层**（估计均值 EV 的 bootstrap 分布）——
   GPT 原表述若作用于单次尝试结果分布，挑战费二元损失会使 P5 恒负、GO 永不触发；
   结果层分布单独报告用于 bankroll 规划。新增边界区强制判决的冻结判据与四级 EV 台账。
3. [GPT，采纳] 附录 A 冻结 TP/FP 分层均匀随机选日规则＋幅度中性声明＋网格地位限定。
