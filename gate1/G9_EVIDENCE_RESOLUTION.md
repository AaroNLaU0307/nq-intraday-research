# G9 Evidence Resolution Addendum（MC1.1，冻结后证据修订）

```yaml
addendum_id: MC1.1-G9
date: 2026-07-28
process: MC_METHOD_SPEC §7 Evidence Resolution Addendum（冻结历史不重写；tag 不动）
outcome: CASE_A_confirmed_conservative
```

## 新证据（Level 2，官方原始文件）

| 文件 | SHA-256 | 来源 |
|---|---|---|
| cme_fee_schedule_2026-07-27.pdf | 58f842b1c07d8e1a5fe3e31cff798b210d702ff0a6c770aa43ca500f583873d2 | https://www.cmegroup.com/company/files/cme-fee-schedule-2026-07-27.pdf |
| cme_fee_schedule_2026-07-27.xls | 7c4ff19c6f732ca176b71c86c273bff8c481615656ad539d29d44dc2915bf90b | https://www.cmegroup.com/company/files/cme-fee-schedule-2026-07-27.xls |

- 抓取路径：cmegroup.com/company/clearing-fees.html（内置浏览器渲染，HTTP 200）→
  官方文件直链经浏览器会话内 fetch（status 200）→ 本地回传落盘。
- 抓取时间：2026-07-28（本地 +08:00；文件哈希即时计算并登记）。
- 页面标题："Clearing & Trading Fees"；费表自述生效日 **2026-07-27**
  （"CME Equity Product Fee Schedules as of July 27, 2026"）。

## 精确证据段落（XLS Equity 表机器提取）

- 表头声明："Fees are charged per side (both buy and sell side) per contract."
- 区块：**Non-Members (Including: CTA/Hedge Fund Incentive Program Participants)** ——
  与本研究使用场景（非会员客户）一致。
- 列：**Micro E-mini Index**（期货）——MNQ（Micro E-mini Nasdaq-100）属此产品列。
- 行 Globex - Outrights：**$0.35 / side**（非会员电子盘单腿）。
- 行 Delivery/Cash Settlement：$0.05——不适用（策略日内强平，永不持仓至交割/现金结算）。
- 无其他适用 CME 组件（费表为单一每边综合费；NFA 费另行，见既有官方快照）。

## 参数决议

| 参数 | 旧值 | 新值 |
|---|---|---|
| execution_costs.lucidflex_mnq.cme_exchange_clearing_fee_per_side_usd | 0.35 **PROVISIONAL** | 0.35 **VERIFIED** |
| s0_cost_handoff.primary_round_turn_usd | 1.74（PROVISIONAL 联动） | **1.74（不变，VERIFIED）** |
| s0_cost_handoff.cme_component_status | unresolved_official_confirmation | verified_official |
| s0_cost_handoff.hard_run_blocker | true | **false** |

- **Primary 算法不变**（全期恒定 $1.74 = 2×(0.50+0.35+0.02)，Case A：官方值恰等于
  冻结假定，上限保守性维持）。
- **S0 cost handoff 无需修改**；对历史冻结结论**零影响**。
- 本决议**仅解除 G9 hard_run_blocker**；真实运行仍被第二物理副本 guard 阻断
  （双 flag 缺一不可）。

## 防"见数改规"声明

本决议时点，S0 从未产出任何可读研究数字（G9＋第二副本双阻断自冻结起持续生效，
本轮 Phase 0 复验）。费用参数确认先于任何数据结果，不存在依据结果调整规则的通道。
