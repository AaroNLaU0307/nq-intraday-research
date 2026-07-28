# MC_METHOD_SPEC — Prop 经济模型方法规范

```yaml
id: MC1
version: 0.3   # v0.2 → v0.3：吸收 platform_params v0.2/v0.3 的实证发现（XFA 零余额、
               # scaling 分层×仓位交互、DLL 状态机、Live 排除、分平台 payout 行为）
status: DRAFT — 待 Aaron/GPT 终审（与 platform_params.yaml v0.3、evidence_registry.yaml 三件套复核）
date: 2026-07-28
references:
  charter_sha256: 5176320fb54a30e5e5dcc7f1ee96b828e7d38f727a573e8bd152ca3ff4299327
  s0_prereg_sha256: 6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132
  gate1_snapshot_manifest_sha256: 3c9e2a34c318217d7ac01502a3d1895e191d282afc08bb36df3feec829222a7b
  lucid_breach_evidence_sha256: 620dee3911e616fafeacf9c399da054dfda4cf1414a0d0a24fd46d2a0358925a
约束: 本规范冻结之前，S0 不得运行产出任何可读数字报告（S0 §10.2）
```

## 0. 与已冻结 S0 的接口约定

S0 §10.4 的判定量词"存在同一组合"作用于**本规范 §2.5 冻结的 Primary 决策集合**；
Sensitivity 与 Excluded 组合不参与判定、不得翻转判决。此为对 S0 中
"预注册平台 × risk policy 组合"一词的正式绑定，非对冻结文本的修改。

## 1. 接口

- 输入：S0 §10.1 每合约日内路径记录（E1/E2 × 成本场景，含 close 与 adverse 双数组）；
  附录 A 网格的交易日标记序列。
- 输出：§6 规格。判定条件在已冻结的 S0 §10.4，本规范只定义计算。

## 2. 平台生命周期变体（参数一律转录自快照，逐项引用文件＋哈希）

### 2.1 转录纪律
全部数字参数进 `gate1/platform_params.yaml`（与本规范一同冻结）；每项标注
来源快照文件与其 SHA-256；Claude 转录、GPT 对照快照逐项复核。
**变体单位 = firm × product × path × account_size × dll_option × phase**，
禁止以"Lucid"/"Topstep"为参数单位。

### 2.2 LucidFlex 50K 生命周期（评估 → sim funded；live 见 §2.6 排除）

状态机要点（参数与公式见 platform_params.yaml v0.3）：
- 评估：无 scaling（首日满仓 4/40）、严格 50% consistency（cushion 不进 Primary）、
  MLL 引擎按机器公式；评估价格/重置价 = 缺口 G1（Aaron 截图后填入，冻结前硬阻断）。
- Funded：**首日容量仅 2 手/20 micro**（分层 [0,1000)→2、[1000,2000)→3、[2000,∞)→4，
  EOD 更新、双向浮动、payout 扣减可降档）；负模拟盈利档位 UNRESOLVED（G7），
  确认前保守取最低档 2/20 并在输出中标注该假设；payout 后 MLL = $50,100。
- Payout 处理期：**halt**（官方明示处理前交易可致拒付）。
- **违规判定（已由 Level 2 证据关闭）**：阈值按日终余额更新（EOD trailing），
  违规监控为盘中实时、含未实现盈亏，触及即违规
  （gate1/lucid_inquiry_reply/RESOLUTION.md，哈希见头部）→ **恒用 adverse-path**。
  违规 = 账户即时死亡；损失按触发价 ± adverse slippage。
- 评估目标 / 50% consistency（申请时刻）/ funded 无 DLL 无 consistency /
  payout 周期 5 个达标盈利日、≤50% 利润、金额上限、payout 对 MLL 与 scaling 的影响：
  全部由 platform_params.yaml 转录。
- Live 迁移**不是确定事件**（进入 review pool ≠ 保证迁移），见 §2.6 情景。

### 2.3 Topstep 50K 生命周期
- Combine：$50,000 起步、MLL $48,000 起 trail 锁 $50,000、**consistency 为软规则**
  （超标 = 目标抬至 best_day÷0.5，不判死）；月费按 synthetic 日历扣取。
- **XFA：余额从 $0 起步**（"50K"为购买力标签）；MLL −$2,000 → 锁 $0；
  scaling 按余额分层（<1500→2、[1500,2000]→3、>2000→5 手，次一 session 生效）；
  payout 后 MLL 永久 = $0、计数重启；**payout 处理期不 halt**（资金即时扣账、
  官方允许立即交易；申请当日不计入下轮资格）。
- DLL：Sensitivity 变体使用 platform_params 的完整状态机（平仓＋撤单＋禁新仓至
  次日 17:00 CT＋临时违规阻断 payout；账户存活）；Primary 无 DLL。
- 失败-复活：XFA 首次 payout 前死亡 → Back2Funded（**每账户最多 2 次**、30 天窗口、
  $599、全部清零重来）；payout 后死亡 → 只能新 Combine；评估死亡 → Reset（$49）。
- 违规判定恒用 adverse-path；XFA → LFA 非确定事件，见 §2.6。
- 多账户约束（v1.1 用）：同时最多 5 个活跃 XFA。

### 2.4 FTMO：不建模（S0 §6 已排除）。

### 2.5 决策角色（冻结；在看任何 S0 结果之前）

```yaml
decision_roles:
  primary:            # S0 §10.4 判定量词的作用域——仅此两条生命周期 × P2
    - lucidflex_50k_eval_to_simfunded            # sizing = P2
    - topstep_50k_stdpurchase_xfastd_nodll       # sizing = P2
  secondary_sensitivity:   # 完整报告；不得翻转 Primary 判决
    - 上述两条生命周期 × {P1, P3, P4}
    - topstep_50k_stdpurchase_xfaconsistency_nodll × P2
    - topstep 购买路径与 DLL 变体 × P2
    - payout_policy_sensitivity（见 §4.2）
    - live 迁移上界情景（见 §2.6）
  excluded_from_checkpoint_0:   # 只展示
    - 其他账户规模、LucidPro/Direct/Daily、R&D 备选一切组合
```

Primary sizing = **P2（固定 $100/笔 ≈ 初始 MLL 的 5%）**；选择理由：贴近达标盈利日
金额门槛的可达性；P1/P3/P4 降为敏感性。此选择供评审否决，冻结后不得改。

### 2.6 Live 迁移（v0.3 修正：完整排除，不再保留未定义的 Sensitivity）

```yaml
live_transition:
  primary:
    action: remain_sim_funded_for_full_24_month_horizon
  sensitivity:
    action: excluded_until_full_live_state_machine_is_frozen
    # 理由：Topstep LFA 涉及余额合并、20% 立即可交易、$10,000 最低起始、reserve、
    # 动态风险扩张、ProjectX API 禁令；Lucid Live 有独立 drawdown/bonus/scaling。
    # 参数不完整的 Live 状态禁止在任何 MC 运行中出现。
```

## 3. 账户模拟器

- 时间步 1 分钟；违规检查两平台**均用 adverse-path**（含浮亏实时判定，Level 2 证据）；
  close-path 用于日终结算、payout 与 P&L 会计。ambiguous 日按 S0 §10.1 双场景。
- **Sizing 锚点（v0.2 修正）**：
  E1：`sizing_anchor = 实际计划止损距离（含成本）`；
  E2：`sizing_anchor = 反事实 E1 止损距离（含成本）`，**不下实际止损单**——
  锚点仅用于仓位计算，不是亏损上限。E2 强制报告：
  `realised_loss/sizing_anchor` 分布、`P(realised_loss > 预算)`、
  `P(intraday_adverse_loss > 预算)`、`worst_loss_multiple`。
- 整数合约（v0.3：与 scaling 分层交互）：
  `n = min( floor(risk_budget ÷ sizing_anchor_usd), 当日 scaling 档位 micro 上限, absolute_max_micros )`；
  n=0 → 跳过并计数；scaling 档位取自**上一 session 收盘后**的余额/模拟盈利（盘中不变）。
- Sizing 政策集合（冻结）：P1 $75；P2 $100（Primary）；P3 剩余 buffer 4%；
  P4 阶梯（>$1500→$100；$800–1500→$75；<$800→$50）。
- 每日至多 1 笔、不隔夜；个人风控层规则不进入 S0-MC。

## 4. 商业层

### 4.1 Synthetic 日历（v0.2 新增）
固定 24 个月模板日历 `2026-08-01 → 2028-07-31`：CME 交易日、周末、假日、半日市
按真实交易所日历生成；**bootstrap 只决定放置在模板交易日上的交易结果序列，
不决定日历本身**。月费/订阅在模板日历的自然月扣取；payout processing 按模板
business days 计算；达标盈利日按模板月/周期归属。模板起始日期可在冻结前调整，
算法不可。

### 4.2 Payout 政策（v0.2 新增，冻结）

```yaml
payout_policy_primary:
  request_timing: first_eligible_session
  request_amount: maximum_allowed
  trading_while_processing:             # v0.3：分平台（依官方规则，非拍脑袋）
    lucidflex: halt                     # 处理前交易可致拒付（官方明示）
    topstep_xfa: continue               # 资金即时扣账、官方允许立即交易
payout_policy_sensitivity:
  request_timing: after_drawdown_floor_locked
  request_amount: maximum_allowed
```

**Terminal value（T=24 月末，冻结）**：
`terminal_value = 已满足提款资格的净可提金额`；尚不可提的模拟余额计 **0**
（敏感性中另报按 50% 折价的备选口径，不进判定）。

### 4.3 失败-重购政策（按账户状态，分平台转录费用）

```yaml
failure_policy:                # Primary；R0（完全不重购）为敏感性
  evaluation_failure:
    topstep: {action: reset, fee_usd: 49, max_total_attempts: 6}
    lucid:   {action: reset_or_repurchase, fee_usd: PENDING_G1, max_total_attempts: 6}
  funded_pre_first_payout_failure:
    topstep: {action: back2funded, fee_usd: 599, max_per_xfa: 2, window_days: 30,
              after_exhausted: new_combine}
    lucid:   {action: new_evaluation}   # Lucid 无同类复活机制（以 platform_params 为准）
  funded_post_payout_failure:
    topstep: {action: new_combine}      # B2F 对已 payout 账户不可用（官方）
    lucid:   {action: new_evaluation}
  live_failure: {action: not_applicable} # Live 已整体排除（§2.6）
```

各动作费用以 platform_params.yaml 为准；Lucid 侧待 G1 截图填入。

### 4.4 会计（v0.2 修正双重计费）

```
strategy_account_EV      = 平台内交易净损益（分成前）
prop_operating_EV        = payout 流入 × 分成 − 评估/重置/重购 − 订阅/月费
                           − activation/reactivation − payout 手续费 + terminal_value
net_business_EV_after_RD = prop_operating_EV − 数据支出 − 基础设施/软件 − 研究工具
                           （评估类费用不得再入 R&D）
risk_haircut_EV          = retention × (未来 payout 流入 + terminal_withdrawable)
                           − 全部运营与 R&D 成本；retention ∈ {100%, 75%, 50%}
```

Checkpoint 0 判定使用 **prop_operating_EV**；部署门槛 risk_haircut_EV > 0。

## 5. 不确定性三层（v0.2 修正）

```
epistemic_distribution：B 个 bootstrap 世界各自的平均商业 EV → GO/STOP 判定
conditional_aleatoric：固定世界内 M 条账户路径的结果分布 → 单账户风险理解
total_predictive：B×M 混合 → bankroll 压力测试（明示为混合分布，不再称"结果层"）
```

- **内层随机源（穷尽列举；无随机源的配置 M=1，不做冗余重复）**：
  (1) 尝试起始日在模板日历首月内的相位偏移（uniform）；
  (2) 附录 A 网格的 TP/FP 分层抽样（K 次重复，仅网格分析）；
  (3) ambiguous 日的双场景分支（枚举，非随机）；
  (4) payout processing 时长：**确定性取官方最大天数**（保守），不随机化。
  Oracle 主判定配置的随机源仅 (1)，故 M = 起始相位数（≈21），非 200。
- 认知层：B = 1,000 stationary bootstrap 世界（块长 5 交易日，S0 §9 一致）。
- **收敛规则（冻结的是规则不是次数）**：
  (a) B、M、K 分别加倍，判定类别不得变化；
  (b) 三个独立 master seeds（7/13/31 派生流）判定类别一致；
  (c) 关键分位数变化 ≤ max($25, 相对 5%)；
  (d) 世界内均值的 MCSE ≤ 世界间 SD 的 10%；
  (e) 任一不满足 → 加倍重跑，禁止用未收敛结果判决。
- **Common random numbers**：跨政策/平台比较使用相同世界序列与相同抽样流。
- 随机数 numpy PCG64；seed 派生表随规范冻结。

## 6. 输出规格

`verdict_inputs.json`（Primary 组合的认知层 P5/median/P95 ＋可行性标志）；
`sensitivity_report.json`（全部 Sensitivity 组合，同格式，标注不可翻转判决）；
`aleatoric_report.json`（三层分布）；`feasibility.json`（月均交易数、达标盈利日
分布 vs payout 要求、n=0 跳过率、合约上限触碰率、ambiguous 占比、E2 超预算概率）；
判定表机械应用结果＋人工复核记录。全部进 STUDY_0_REPORT。

## 7. 冻结与证据修订

评审通过 → Freeze Commit（本文件＋gate1/platform_params.yaml，tag `mc-freeze-v1`，
两阶段流程同 S0 §12）。冻结后的新官方证据（如 Lucid 追问答复）按
**Evidence Resolution Addendum** 处理：原文＋哈希存档 → platform_params 更新 →
MC1.x evidence-resolution commit → FREEZE_LOG 登记；状态机语义变化必须走此流程，
不得只改 YAML 字段。

---
### v0.2 → v0.3 修订记录（platform_params 实证发现＋GPT 第二轮 4 阻断项）
1. §2.3 重写为 XFA 真实结构（余额 $0 起步、MLL −2000→锁 0、余额分层 scaling）。
2. §2.2 Lucid funded 首日容量 2 手（非 4）；负盈利档 UNRESOLVED（G7）保守取最低档；
   payout 处理期 halt。
3. §2.6 Live 完整排除（Primary 全程 sim；Sensitivity 在 Live 状态机冻结前禁止运行）。
4. §3 整数合约公式与 scaling 档位交互（min 三元）；档位取上一 session 收盘值。
5. §4.2 payout 处理期行为分平台（Lucid halt / Topstep XFA continue，均依官方规则）。
6. §4.3 失败政策按平台×状态展开（Topstep reset $49 / B2F $599×2 / 新 Combine；
   Lucid 待 G1）。
7. DLL 引用 platform_params 完整状态机；多账户 5-XFA 上限记入 v1.1 约束。

### v0.1 → v0.2 修订记录（GPT 评审 10 项阻断全部采纳＋证据关闭）
1. Lucid 违规判定开放项以 Level 2 证据关闭为 V-A（实时含浮亏）；双变体删除，
   两平台统一 adverse-path。
2. 平台参数单位改为完整生命周期变体（firm×product×path×size×dll×phase）。
3. 新增 §2.5 决策角色：Primary（2 生命周期 × P2）/ Sensitivity（不得翻转判决）/
   Excluded；绑定 S0 §10.4 量词作用域。
4. E2 sizing anchor = 反事实 E1 止损距离；新增 E2 超预算风险披露（GPT 阻断项 1）。
5. 新增 payout 政策（时点/金额/处理期行为）与 terminal value 保守定义（阻断项 2）。
6. Live 迁移改为情景边界（remain_sim primary / first_eligible sensitivity），
   不发明概率；重购政策拆为按失败状态的 failure_policy（阻断项 3）。
7. 会计闭环修复：评估类费用只入 prop_operating_EV，R&D 仅含真实研发支出；
   risk haircut 只作用于在险流入与可提余额（阻断项 4）。
8. 不确定性改为三层（epistemic / conditional aleatoric / total predictive）；
   内层随机源穷尽列举，确定性配置 M=1（阻断项 5）。
9. 新增 24 个月 synthetic 日历模板，bootstrap 只填充交易结果（阻断项 6）。
10. 收敛规则升级（加倍诊断、三 seed 判定一致、绝对/相对双容差、MCSE 上限、CRN）。
