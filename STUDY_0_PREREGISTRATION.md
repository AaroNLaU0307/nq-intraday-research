# Study 0 预注册 — NQ Opening Drive **Continuation** 图谱与 Edge 天花板

```yaml
id: S0
version: 0.2   # v0.1 经 GPT 评审否决冻结；本版实施全部 7 项强制修改（修订记录见文末）
status: DRAFT — 待 Aaron 针对性复核；冻结 = 两阶段 commit（见 §12）
date: 2026-07-27
trial_ledger: formal_trial_count 登记 S0 = 1；researcher_exposure_count 另行记账（见 §9）
```

## 0. 研究问题与非目标

- Q1：NQ 的 opening drive（09:30–10:00 方向性移动）之后，**顺驱动方向**的延续现象基础率与分布如何？
- Q2：在 10:00 只完美知道"今天顺驱动方向交易是否值得"（不知道任何未来价格路径、不知道反转）的 Oracle，受可执行约束与 Micro 整数仓位约束后，成本后期望上限是多少？
- Q3：将 Oracle 的**逐日 P&L 分布**（非仅均值）交给 Prop MC → GO / STOP / 边界区。

**非目标**：不开发入场信号、不做参数扫描、不做 ML、不评估真实策略、不宣称统计发现。
**明确排除**：opening drive 失败后的反转研究属于未来独立 Study/H2，不得混入本次 continuation 天花板。

## 1. 数据与数据角色（四角色隔离）

| 角色 | 数据 | 范围 | 允许用途 |
|---|---|---|---|
| Development | NQ.v.0 ohlcv-1m | 2010-06-06 → 2021-12-31 | 描述与假设开发（S0 全部 alpha 侧计算仅用此段） |
| Internal Validation (IV) | NQ.v.0 ohlcv-1m | 2022-01-01 → 2025-06-30 | **访问预算 1 次**，保留给完全冻结后的 H1 首次验证；**S0 不得访问**；IV 失败 = 假设死亡，不是迭代燃料 |
| Execution Cost Calibration | MNQ.v.0 bbo-1s | 2025-01-01 → 2025-04-01 | 仅成本统计。工程隔离：`cost_calibration/` 模块读取原始 BBO，只输出 `spread_cost_table.parquet`（分时 spread 分位数＋预声明执行偏差统计）；`alpha_research/` 只能读取该表，禁止读取原始 BBO；其价格方向/收益/信号表现不得用于任何 alpha 分析 |
| Physical Lockbox | 2025-07-01 → 最终评估日 | 不购买、不存在于本机 |

- 采购按 `purchase_plan.yaml` PP-2026-07-27-A（rev2）。
- Bar 时间戳约定：`ts_event` = bar 开始时刻；"HH:MM bar" 指以该时刻开始的 1 分钟 bar。
- 换月：`is_roll_transition` = continuous 映射实际切换的交易日；`is_roll_window` = 切换日前后各 2 个 RTH 交易日。symbology 映射随数据归档。

## 2. Development 内部稳定性检查（替代 IV 访问）

S0 的稳定性检查全部在 Development 内完成，预先固定：

- 时代切片：2010–2013 / 2014–2017 / 2018–2021；
- 按年表格（强制）＋ leave-one-year-out 描述；
- 多空分开；20 日实现波动率三分位分层。

## 3. Session 与时间（同 v0.1，冻结）

时区 America/New_York；RTH 09:30–16:00；观察窗 09:30–09:59 bar；决策 10:00；
入场价 = 10:00 bar 开盘价 ± 成本；强制退出以 15:44 bar 收盘价 ± 成本；
隔夜区间 = 前日 18:00 → 当日 09:30；日历 = pandas-market-calendars(CME Equity) ＋ CME 通告核对；DST/假日单元测试。
**剔除日**（仅此三类）：半日市；RTH 无成交；RTH bar 缺失 > 10%。

**NA 政策**：除剔除日外，任何日子不得整日删除。特征因分母为零（隔夜区间为 0、OR 宽度为 0）、
换月污染（切换日 gap）、或历史不足（前 60 日 RVOL、前 14 日 ADR）而无法计算时，该特征记 NA，
该日仍进入 Oracle 总体统计；每张表强制报告 NA 数量。

## 4. 归一化与特征（公式冻结；全矩阵报告）

**归一化：ADR14** = 前 14 个完整 RTH 交易日的 (RTH high − RTH low) 均值（不含当日）。
不使用 True Range——continuous 合约换月跳空会污染跨日 close-to-close 计算；ADR14 只依赖当日内部区间。

| # | 特征 | 定义 |
|---|---|---|
| F1 | ret_open30 | (C₀₉₅₉ − O₀₉₃₀) / ADR14 |
| F2 | or_width | (H − L)₀₉₃₀₋₁₀₀₀ / ADR14 |
| F3 | de_open30 | \|C₀₉₅₉ − O₀₉₃₀\| ÷ Σ\|ΔC\|（1 分钟路径） |
| F4 | rvol_open30 | Vol(09:30–10:00) ÷ 前 60 交易日同窗中位数；roll window 内的值须分层解读 |
| F5 | gap | (O₀₉₃₀ − 前日 RTH 收盘) / ADR14；**is_roll_transition 日记 NA** |
| F6 | open_loc_on | (O₀₉₃₀ − ON_low)/(ON_high − ON_low) ＋ above/inside/below |
| F7 | on_range | (ON_high − ON_low) / ADR14 |
| F8 | retrace_open30 | 开盘驱动最大逆向回撤 ÷ \|驱动幅度\| |
| F9 | close_pos_open30 | (C₀₉₅₉ − L)/(H − L) 窗口内 |
| F10 | is_event_day | ∈ {CPI, NFP, FOMC, none}（BLS/Fed 官方时刻表快照） |
| F11 | is_roll_transition / is_roll_window | 见 §1 定义 |

## 5. 方向与标签

**驱动方向 d_open = sign(ret_open30)**；ret_open30 = 0 的日子：无方向，不可交易，单独计数报告。

| # | 标签 | 定义 | 地位 |
|---|---|---|---|
| **Y_cont** | **d_open × (C₁₅₄₄ − O₁₀₀₀) / ADR14** | **主标签：延续幅度（顺驱动为正）** | Oracle 判定用 |
| Y1 | (C₁₅₄₄ − O₁₀₀₀) / ADR14 | 双向下午收益 | 仅描述，禁止用于 Oracle 方向 |
| Y2 | de_pm | 10:00–15:45 方向效率 | 描述 |
| Y3 | close_pos_pm | 收盘位置 | 描述 |
| Y4/Y5 | MFE/MAE | 相对 **d_open** 方向自 O₁₀₀₀ 起算，/ADR14 | 描述＋E1 输入 |
| Y6 | cont_decile | Y_cont 在 Development 分年内的十分位 | 描述 |

## 6. 成本模型（可编码公式；参数在首次计算前锁定）

**结构拆分**：`market_friction`（spread＋滑点，来自 CostCal 表）＋ `platform_fee`（佣金/费用）。

- platform_fee 来自 Gate 1 冻结的**期货 prop 候选**官方费率快照（Lucid、Topstep）；kill 场景采用其中**较保守的已验证全含费率**；FTMO 为 CFD、标的不可比，**不进入 S0 费率场景**。禁止看到结果后改选便宜费率。
- spread 场景（Base/Conservative/Stress/Severe）同 v0.1：时段中位＋1 tick ／ P90＋2 tick ／ Base×2 ／ P95＋3 tick。
- **代理假设明示**：2025Q1 MNQ spread 分布用于其他年份，是"当前微观结构代理"；四档场景共同覆盖该不确定性。

**成交规则（冻结）**：

```
多头入场:  fill = P_ref + half_spread + slippage        （空头反向）
定时退出:  fill = P_ref − half_spread − slippage        （多头；空头反向）
止损触发（1 分钟 OHLC）:
  若 bar 开盘已穿越 stop → 按 bar 开盘价 + adverse slippage 成交
  否则若 bar 内触及 stop → 按 stop 价 + adverse slippage 成交
  禁止假设永远在 stop 价成交
```

## 7. 双 Oracle（方向永远 = d_open；冻结）

延续事件：**Y_cont ≥ θ**；θ 主 0.5、副 0.3（副阈值完整报告，**不得**在主阈值失败后升格为主结果）。
Oracle 只在延续事件日交易，方向恒为 d_open；仅知"今天顺驱动交易值得"，不知任何价格路径。

- **理论 Oracle**（仅经济上限，不入 kill gate）：10:00 开盘价按 d_open 入场，
  在 **d_open 方向的后续最有利价格**退出，减 Base 成本。
- **可执行 Oracle**：10:00 开盘价 ± 成本入场；每日至多 1 笔；不隔夜；退出引擎：

| 引擎 | 定义 | 地位 |
|---|---|---|
| E1 | 初始止损 = 开盘区间对侧极值（多头 = OR 低点，空头 = OR 高点）；未触发则 15:45 退出 | **资本约束主引擎** |
| E2 | 无止损，15:45 定时退出 | **执行上限参照**；须报告最差日分布（P1/P5）作尾部披露 |

E3（ATR 跟踪）自 v0.1 删除，留待 H1 预注册。
**单位**：1R = E1 初始止损距离（仅作归一化）；所有结果**同时以 USD / 1 MNQ 合约**报告——这才是与 MC 对接的单位。

## 8. 整数仓位粒度输出（强制）

逐日输出：`stop_distance_points`、`risk_usd_per_1_MNQ`、`cost_usd_per_1_MNQ`、
`cost_as_pct_of_R`、`minimum_1_contract_risk`。
并在**非决策性**风险预算 {$50, $75, $100, $150} 下报告可执行覆盖率
（该日 1 手 MNQ 的 E1 风险 ≤ 预算的日子占比）。不从中挑选最佳，仅供 MC 观察仓位粒度。

## 9. 统计与两本台账（冻结）

- Primary：stationary bootstrap，期望块长 5 个交易日，10,000 次重抽，seeds = {7, 13, 31}，百分位法 95% CI。
- Sensitivity：期望块长 21 个交易日。
- **formal_trial_count**：S0 = 1 个预注册描述研究。
- **researcher_exposure_count**：所有实际查看过的特征×标签×方向×分层组合记入
  `EXPOSURE_LEDGER.md`；未来 H1 的 deflated Sharpe/等价校正必须以 exposure 计数为准，
  而非 H1 代码实际运行的版本数。

## 10. Kill Gate（Checkpoint 0，冻结）

**交接方式**：向 MC 提交可执行 Oracle 的**逐日 P&L 向量**（每引擎 × 每成本场景 × 每风险预算，
含整数合约取整与预算不足跳过），而非仅标量均值。MC 在平台规则（trailing、consistency、
payout 达标盈利日、合约上限）下输出商业 EV。标量 X（E1，Conservative，θ=0.5，USD/合约）
仅作可读摘要。

**频率输出（强制）**：延续事件基础率 p、每年可交易日数、Oracle 月均交易频率、
precision–recall 网格下的预期交易数（附录 A）。

| 判定 | 条件 | 动作 |
|---|---|---|
| STOP | E1 与 E2 在 Conservative 成本下均低于各自 MVE | 终止 continuation 策略族；不再开发任何过滤器/入场/ML |
| GO | E1 ≥ 1.5 × MVE 且频率/仓位粒度经 MC 确认可行 | 按附录 A 计算 precision–recall 可行区域，进入 H1 预注册 |
| 边界区 α | MVE ≤ E1 < 1.5 × MVE | 一次预注册敏感性检查（成本±、分年、多空、θ=0.3、入场推迟 5 分钟）→ 一次性 GO/STOP |
| 边界区 β | E2 明显可行但 E1 不可行 | 现象可能存在但风险架构不成立：允许**一次**预注册的替代风险结构检查，之后一次性 GO/STOP |

MVE 为函数 MVE(trades_per_month, risk_policy, payout_day_distribution, platform_rules)，
由 MC v1 独立产生；MVE 冻结前 S0 数值结果封存不作决定。
辅助直觉检查（不单独决定 GO）：q_min ≤ min(65%, 2.2 × p)。

## 11. 禁止事项

参数扫描、多窗口 ORB、指标族、ML、delta、回踩逻辑、入场优化、反转方向研究、
S0 访问 IV、访问/购买 lockbox、alpha 侧读取 CostCal 原始 BBO、依据结果修改冻结定义。

## 12. 冻结机制（两阶段 commit）

1. **Freeze Commit A**：仅含被冻结文档（本文件＋PROJECT_CHARTER.md）；打 annotated tag `s0-freeze-v1`。
2. **Registry Commit B**：计算 Commit A 中目标文件 SHA-256，连同 Commit A hash 写入
   FREEZE_LOG.md 后提交。锚定对象是 **Commit A**。
3. **Purchase Approval Commit C**：Aaron 填写 purchase_plan.yaml 批准字段（含三份文件的
   approved SHA-256）后单独提交；执行脚本核对 hash 一致且实际可用 credit ≥ 实际重报价，否则中止。

## 附录 A：precision–recall 可行区域

设基础率 p（Y_cont ≥ θ 日占比）、召回 r、精确率 q，年交易日 N≈252：
年交易数 F(q,r) = p·r·N / q；每笔期望 E(q) = q·R_o − (1−q)·|R_f|
（R_o = Oracle 延续日成本后均值；R_f = 非延续日误交易成本后均值，E1 下 ≈ −1R − 成本）。
**可行区域 = {(q, r) : E(q) ≥ MVE(F(q,r)/12, …)}**。
S0 报告 q ∈ {0.35…0.75} × r ∈ {0.2…0.8} 网格的 E、月频与可行性，交 MC 判定。

---
### v0.1 → v0.2 修订记录（GPT 评审 2026-07-27，全部采纳）
1. Oracle 方向由 sign(Y1) 改为恒等于 d_open（修复未来方向泄漏）；新增主标签 Y_cont。
2. MNQ 2025Q1 改列第四数据角色 Execution Cost Calibration，工程隔离。
3. IV 访问预算 3 → 1（仅冻结后 H1）；S0 稳定性检查改用 Development 内部时代切片。
4. E1 单引擎生死判决改为 E1/E2 双判据＋边界区 β；E3 删除。
5. MVE 升级为频率相关函数；附录 A 升级为 precision–recall 可行区域；增加频率强制输出。
6. 归一化 ATR14(TR) → ADR14(RTH range)；gap 在 roll transition 日 NA；roll 标志精确化。
7. 成本/止损成交规则写成可编码公式；platform_fee 与 market_friction 拆分，费率平台无关化。
8. 新增整数仓位粒度输出（§8）与逐日 P&L 分布交接（§10）。
9. bootstrap 完整规格＋两本台账；冻结改两阶段 commit。
