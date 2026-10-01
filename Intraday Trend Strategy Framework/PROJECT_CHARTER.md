# 项目章程 v1.2 — 期货 Prop 环境下的自动化日内策略研究与执行系统

```yaml
version: 1.2-r2   # r2: 采纳 GPT 评审新增条款 13/14、第二副本期限、两阶段冻结
status: FROZEN（Freeze Commit A，tag s0-freeze-v1，2026-07-27；修订仅可以新版本条目追加）
date: 2026-07-27
parties: Aaron（决策）/ Claude Code（main agent，执行与证伪）/ GPT（consultant）
```

## 使命

以期货 Prop 账户为过渡执行环境，建立一条能够批量证伪日内策略假设的研究流水线；
若找到经过全部纪律检验的 edge，通过 Prop 现金流为自有资本复利提供种子资金和执行证据。
Prop 不是终点，是过渡层。

## 三层成功定义

1. **确定性成功**：Prop 经济模型、回测流水线、trial ledger、风控引擎、自动执行＋kill switch、知识库。
2. **研究成功**：找到能稳定区分趋势日/震荡日/事件日的状态变量。
3. **商业成功**：一个经过成本、滑点、OOS、多重检验、Prop 规则、forward test 后仍然存在的 edge。

策略失败是基准预期；流水线才是资产。

## 冻结条款（结果不好也不得悄悄修改）

1. 所有测试变体进入 trial ledger 计数；失败结果保留，不覆盖旧实验。
2. 最终评估使用 deflated Sharpe 或等价多重检验校正。
3. 预注册先于数据：任何研究计算之前，定义、公式、kill 规则必须冻结并 commit。
4. 物理 lockbox：最终确认期数据不购买、不存在于本机，评估时刻才补购。
5. Micro 合约成本独立建模（用 micro 自身报价，不用 mini 代替）。
6. 五套 null benchmark 内建于回测引擎（随机入场同退出、regime 内开盘持有、裸 ORB、固定时间随机方向、regime 匹配日期置换）。
7. 止损永远活在服务器端（bracket/OCO），EA 只移动、不代替。
8. 上线验收 = 逐笔成交对账报告（模拟 vs 回测预测），不是"模拟赚钱了"。
9. Study 0 之后设正式继续/搁置评审；此后每完成一个假设闭环评审一次。
10. 第一个完整假设闭环前，不接入新市场（CL/6E/ZN 等）。
11. 假设版本化留痕：失败后修订 = H1.1 或新假设 H2，附预先记录的机制理由；禁止悄悄改参数仍叫 H1。
12. Alpha/Risk 边界：平台状态（buffer、consistency、日损）只允许进入 Risk Engine，
    永远不进入 Alpha Engine；Risk Engine 对信号只有缩减/跳过/停止权限，且政策全部预注册。
13. 研究暴露记账：所有已查看的特征、标签、切片和参数候选进入 EXPOSURE_LEDGER.md；
    raw exposure count 作为**保守上界**完整报告；正式多重检验必须预注册从 raw exposure
    推导相关性调整后 N_eff 的方法（或使用适合相关候选的校正方法）；
    禁止只使用最终存活的策略版本数量。
14. 数据角色隔离：Development / Internal Validation / Execution Cost Calibration /
    Physical Lockbox 必须具有独立目录、读取边界和用途；成本校准数据不得用于
    Alpha 特征或收益分析。

## 证据层级与元规则

```
Level 1：实际文件、checksum、程序输出
Level 2：带日期的官方规则快照
Level 3：可复现分析结果
Level 4：有依据的推断
Level 5：直觉或意见
```

低层级证据不得推翻高层级证据。
**元规则**：任何一方（Claude / GPT / Aaron）对可验证事实提出修正时，不因其表达自信、
身份或论证风格而接受；必须核对 Level 1–2 证据后才接受。
（案例存档：2026-07-27，Claude 错误宣称原始数据已清理，GPT 放弃了自己正确的库存主张。）

## 数据治理

- Canonical research corpus 必须：免费报价 → Aaron 批准 → batch 提交 → 立即下载 →
  SHA-256 校验 → 连同官方 support files 归档（OneDrive 之外）→ 本地 manifest → 第二离线副本。
- 第二物理副本（不同物理介质）必须在**采购完成后、首次研究计算之前**完成；
  现有 carry 双副本同盘的状态须在同一期限内一并解决。
- 流式接口无恢复通道，永不作为 canonical 数据源；小额 probe 与免费 metadata 查询除外。
- 平台规则、报价、费率一律保存带抓取日期的官方快照；规则数字不硬编码进策略代码。
- 交易所假日/session 日历用独立来源（exchange calendar 库＋CME 通告），不从数据缺口反推。
- 时间系统同时保存 UTC / America/New_York / 交易所时区 / 交易日 ID；DST 切换写单元测试。

## 三本账

- **R&D 账**：数据、评估费、重置费、基础设施、订阅。
- **Prop Engine 账**：通过率、账户死亡率、payout 速度、多账户复制、平台风险、净现金流。
- **Personal Compounding 账**：转入自有资金、自有账户风险与增长、何时降低 Prop 依赖。

Prop 净现金流须先覆盖 R&D burn 才算为正。转移点是 MC 的计算输出，不是感觉。

## 平台四 Gate（当前状态：候选均未通过任何 Gate）

Gate 1 规则引擎（版本化官方快照，含合约上限/scaling plan 字段）
Gate 2 自动化通道 PoC（含断线后挂单存续实测）
Gate 3 Prop 经济模型（路径依赖 MC，输出 MVE 与最优 sizing 政策）
Gate 4 经营与规则风险（场景折扣）
Gate 1/2/3 并行开发；只有结论依赖参数。候选：LucidFlex / Topstep / FTMO 2-Step。

## 可调整项（调整必须成为有日期的新版本，不得抹掉过去）

最终入场与退出、开发市场顺序、平台、因子集、仓位政策、单/多账户、是否加入 MR 路由器、
是否扩展 CL/6E/ZN、entry_mode（evaluation vs instant funded）。

## 预算纪律

- 当前批准范围：仅 purchase_plan.yaml 中经 Aaron 明确批准的条目；credit 优先。
- Aaron 已声明的自付上限量级：小几百美元级；任何超出 credit 的支出均需单独逐笔批准。
- 每个采购计划带 hard_cost_cap；实际报价超过即中止。
