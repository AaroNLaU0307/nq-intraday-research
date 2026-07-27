# MC_METHOD_SPEC — Prop 经济模型方法规范

```yaml
id: MC1
version: 0.1
status: DRAFT — 待 Aaron/GPT 评审；冻结 = 两阶段 commit（tag mc-freeze-v1）
date: 2026-07-28
references:
  charter_sha256: 5176320fb54a30e5e5dcc7f1ee96b828e7d38f727a573e8bd152ca3ff4299327
  s0_prereg_sha256: 6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132
  gate1_snapshot_manifest_sha256: 3c9e2a34c318217d7ac01502a3d1895e191d282afc08bb36df3feec829222a7b
  gate1_snapshot_date: 2026-07-28
约束: 本规范冻结之前，S0 不得运行产出任何可读数字报告（S0 §10.2）
```

## 1. 目的与接口

- **输入**：S0 §10.1 的每合约日内路径记录（每引擎 E1/E2 × 每成本场景，含
  `mtm_close_pnl_1m[]` 与 `mtm_adverse_pnl_1m[]`）；附录 A 网格的交易日标记序列。
- **输出**：S0 §10.4 判定所需的认知层统计量（prop_operating_EV 的 P5/中位数/P95，
  按组合），结果层分布报告，及可行性标志（频率、整数仓位、payout 路径）。
- 判定条件本身在 S0 §10.4（已冻结），本规范只定义其计算方法。

## 2. 平台状态机（参数一律转录自 2026-07-28 官方快照，逐项引用文件名）

### 2.1 参数转录纪律
所有数字参数进入 `gate1/platform_params.yaml`，每项标注来源快照文件与该文件
SHA-256（见 snapshot_manifest.json）；转录由 Claude 完成、GPT 对照快照复核；
platform_params.yaml 与本规范一同冻结。**评审重点：逐项核对转录值。**

### 2.2 LucidFlex 50K（候选 A）
- MLL：EOD trailing，随最高日终余额上移至锁定点（lucid_flex_drawdown.html）。
- **违规判定双变体**（开放项，直至 lucid_inquiry 获书面回答）：
  V-A 静态阈值＋实时 equity（含浮亏）触发 → 用 adverse-path；
  V-B 仅日终 balance 判定 → 用 close-path 日终值。
- 评估：利润目标、50% consistency（申请通过时刻检查）（lucid_flex_evaluation.html）。
- Funded：无 DLL、无 consistency；payout 周期 5 个达标盈利日、单次提取 ≤50% 利润
  且有上限、5 次后 live review（lucid_flex_funded.html / lucid_flex_payouts.html）。
- 费用与合约上限：lucid_products_comms.html / lucid_flex_* 转录。

### 2.3 Topstep 50K Combine → XFA（候选 B）
- MLL：地板按日终更新、**违规实时判定且含未实现盈亏** → 恒用 adverse-path
  （topstep_mll.html）。
- DLL（topstep_dll.html）；scaling plan 合约上限（topstep_scaling.html）；
  月费/activation/XFA 与 Live 结构（topstep_pricing.html / topstep_live_funded.html）；
  payout 政策（topstep_payout.html）。

### 2.4 FTMO
不建模（CFD 标的不可比，S0 §6 已排除）。

## 3. 账户模拟器

- 时间步：1 分钟，直接消费 S0 路径数组；违规检查按平台/变体选 close-path 或
  adverse-path（S0 §10.1 双路径规则，含 ambiguous 双场景）。
- **Sizing 政策集合（预注册，冻结后不得增删）**：
  P1 固定风险 $75/笔；P2 固定风险 $100/笔；
  P3 剩余 buffer 的 4%/笔；P4 阶梯（buffer>$1500→$100；$800–1500→$75；<$800→$50）。
- 整数合约：`n = floor(risk_budget ÷ risk_usd_per_1_MNQ_planned)`；n=0 → 跳过并计数。
- 每日至多 1 笔、不隔夜（S0 约束）；个人日损/周损规则**不在** S0-MC 中引入
  （属 H1 之后的 Risk Engine 层，此处只测平台规则本身）。

## 4. 商业层

- 组合维度：{Lucid V-A, Lucid V-B, Topstep} × {P1..P4} × {E1, E2} ×
  {Conservative, Stress}（Base 与 Severe 场景只作诊断输出，不进判定）。
- 费用：评估费、重置费、月费、activation fee（快照转录）。
- 重购政策两档：R0 不重购；R1 账户死亡立即重购同档评估，生命周期内最多 6 次。
- 期界 T = 24 个月日历时间；数据日序列由 bootstrap 世界生成（§5）。
- 四级 EV 台账（S0 §10.5）：strategy_account_EV → prop_operating_EV（判定用）→
  net_business_EV_after_RD（R&D = 实际数据支出＋评估费累计摊销）→
  risk_haircut_EV（payout 折扣 0% / 25% / 50% 三场景）。

## 5. 两层不确定性实现（S0 §10.3）

- **认知层**：B = 1,000 个 stationary bootstrap 数据世界（期望块长 5 交易日，
  与 S0 §9 一致；seeds {7,13,31} 派生子流）；每个世界内 M = 200 条平台路径模拟
  （评估→funded→payout→死亡/重购），取该世界均值 → B 个均值构成认知层分布。
- **结果层**：B×M 池化的单账户尝试结果分布，单独报告：P(净损失评估费)、
  P5/P50/P95、时间-至-首次 payout 分布、最大回撤分布。
- 附录 A 网格：每格 K = 50 次分层抽样重复（seeds 派生）走同一流程。
- 随机数：numpy PCG64；完整 seed 派生表随规范冻结。
- **算力注记**：B/M/K 为草案值；评审时可依 pilot 运行的收敛诊断（认知层分位数的
  MC 标准误 < 判定余量的 1/10）调整，冻结后不得改。

## 6. 输出规格（全部进入 STUDY_0_REPORT 附件）

- `verdict_inputs.json`：每组合的认知层 P5/median/P95 ＋ 可行性标志。
- `aleatoric_report.json`：结果层分布。
- `feasibility.json`：月均交易数、达标盈利日分布 vs payout 要求、n=0 跳过率、
  合约上限触碰率、ambiguous 日占比。
- 判定表的机械应用结果（STOP/GO/α/β）与人工复核记录。

## 7. 冻结机制

评审通过 → Freeze Commit（本文件＋gate1/platform_params.yaml，tag `mc-freeze-v1`）
→ FREEZE_LOG 登记 blob 哈希（两阶段流程同 S0 §12）。
Lucid 书面回答到达后：双变体收敛为单变体 = 参数更新，登记 FREEZE_LOG，
不构成规范修改。
