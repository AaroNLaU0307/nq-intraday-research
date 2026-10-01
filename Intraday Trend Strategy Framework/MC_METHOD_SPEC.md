# MC_METHOD_SPEC — Prop 经济模型方法规范

```yaml
id: MC1
version: 0.6   # v0.5 → v0.6：GPT 第五轮 6 封口项（生命周期次数上限、Lucid rail 归位＋
               # 保守费、G9 唯一 Primary＋机器阻断、v5 清单、哈希预填、manifest 检查补全）
status: FROZEN（Freeze Commit A，tag mc-freeze-v1，2026-07-28；修订仅可以 MC1.x 增补或 Evidence Resolution Addendum 追加）
date: 2026-07-28
references:
  charter_sha256: 5176320fb54a30e5e5dcc7f1ee96b828e7d38f727a573e8bd152ca3ff4299327
  s0_prereg_sha256: 6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132
  gate1_snapshot_manifest_v5_sha256: 5b6083b5ee61db9c44b119fae3bfdb2c0c039b9c53f5d7c67a74c69f6d4e0434
  evidence_registry_sha256: c14d576ba2076f8f08cb4f8bef16fc5a99c881071baed303f9d8a73964a6b35c
  lucid_breach_reply_png_sha256: 620dee3911e616fafeacf9c399da054dfda4cf1414a0d0a24fd46d2a0358925a
  lucid_breach_resolution_md_sha256: af7c498946789b899839af9c34221a6c0a07a4703ba894830e6a1f920964823e
约束: 本规范冻结之前，S0 不得运行产出任何可读数字报告（S0 §10.2）
evidence_note: Lucid support 回复为 AI bot 生成（Level 2-AI）；详见 platform_params
  的 evidence_grade_note——无数字参数以 bot 回答为唯一来源，V-A 为保守方向。
```

## 0. 与已冻结 S0 的接口约定

S0 §10.4 中的**全部量词——GO 的存在量词、STOP 的全称量词、边界区 α/β 的组合范围——
均仅作用于本规范 §2.5 冻结的 Primary 决策集合**；Sensitivity 与 Excluded 组合不参与
任何判定分类（包括不影响 STOP 的"所有组合"条件），不得翻转判决。
此为对 S0 中"预注册平台 × risk policy 组合"一词的正式绑定，非对冻结文本的修改。

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

状态机要点（参数与公式一律以 platform_params.yaml 当前冻结版为准）：
- 评估：无 scaling（首日满仓 4/40）、严格 50% consistency（cushion 不进 Primary）、
  MLL 引擎按机器公式；费用已冻结——首购 $98、重购 Primary $140（coupon 复用未证明，
  防虚假 GO）、reset $95。
- Funded：**首日容量仅 2 手/20 micro**（分层 [0,1000)→2、[1000,2000)→3、[2000,∞)→4，
  EOD 更新、双向浮动、payout 扣减可降档）；负模拟盈利档位 UNRESOLVED（G7），
  确认前保守取最低档 2/20 并在输出中标注该假设；payout 后 MLL = $50,100。
- Payout 处理期：**halt**（官方明示处理前交易可致拒付）。
- **违规判定（v0.5：冻结的保守建模假设，非已确认事实）**：

  ```yaml
  lucid_intraday_breach:
    evidence_status: unresolved_human_confirmation
    available_evidence: [official_page_ambiguous, lucid_ai_support_reply]
    primary_model_rule: realtime_equity_including_unrealized
    model_role: conservative_assumption   # 相对 EOD-only 只会加速死亡、压低 EV：
    path: adverse_path                    # 不会经 Lucid 制造虚假 GO，可能产生假 STOP
  ```

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
  $599、全部清零重来）；payout 后死亡 → 只能新 Combine；评估死亡 → 调用 subscription/reset engine（credit 优先，无则付费）。
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
    # live 迁移情景已整体移入 excluded（§2.6：状态机未冻结禁止运行）
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

- 时间步 1 分钟；违规检查两平台**均用 adverse-path**（Topstep：官方确认实时含浮亏；
  Lucid：冻结的保守建模假设，见 §2.2）；
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
- **buffer 定义（v0.4 唯一化，P3/P4 用）**：
  `buffer_at_entry = 10:00 入场前 realtime_equity − 当前 MLL floor`；
  不预扣本笔交易费用；**锚定 MLL 而非 DLL**（DLL 非账户死亡线，其 halt 效果由
  DLL 状态机独立处理，不进入 buffer 计算）。
- 每日至多 1 笔、不隔夜；个人风控层规则不进入 S0-MC。

## 4. 商业层

### 4.1 Synthetic 日历（v0.2 新增）
固定 24 个月模板日历 `2026-08-01 → 2028-07-31`：CME 交易日、周末、假日、半日市
按真实交易所日历生成；**bootstrap 只决定放置在模板交易日上的交易结果序列，
不决定日历本身**。**计费日历（v0.5 分拆，消除自然月矛盾）**：

```yaml
billing_calendars:
  topstep_combine:  {cadence: every_30_days_from_current_rebill_anchor}   # reset 将锚点重设为 reset 日
  topstep_api:      {cadence: every_30_days_from_activation}
  nfa_fee_step:     {change_date: "2027-07-01", per_side: "0.01 → 0.02",
                     decision_role: diagnostic_only}  # Primary 用全期恒定 $1.74（s0_cost_handoff）
  true_calendar_month_services: {cadence: calendar_month}                  # 仅适用真日历月计费项
```

payout processing 按模板 business days 计算；达标盈利日按模板周期归属。
模板起始日期可在冻结前调整，算法不可。

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
lifecycle_attempt_policy:      # v0.6：全生命周期上限唯一化（消除实现 A/B 分歧）
  scope: entire_24_month_platform_simulation
  max_evaluation_starts_including_initial: 6    # 含首次；评估 reset 每次计 1 次
  funded_failure_restart_consumes_attempt: true # funded 死亡后的 new_evaluation/new_combine
                                                # 消耗同一计数器，不重新获得 6 次
  counter_does_not_reset_after_passing_evaluation: true
  action_after_exhaustion: terminate_platform_lifecycle

failure_policy:                # Primary；R0（完全不重购）为敏感性
  evaluation_failure:
    topstep: {action: invoke_subscription_reset_engine}
             # 引擎决定用 Reset Credit（先到期先用、同规格同路径）还是付费 $49；
             # rebill 锚点重设为 reset 日 + 30 天；计数遵循 lifecycle_attempt_policy
    lucid:   {action: reset, fee_usd: 95}
  funded_pre_first_payout_failure:
    topstep: {action: back2funded, fee_usd: 599, max_per_xfa: 2, window_days: 30,
              after_exhausted: new_combine}
    lucid:   {action: new_evaluation, purchase_cost_policy: subsequent_repurchase_primary_140}
  funded_post_payout_failure:
    topstep: {action: new_combine}      # B2F 对已 payout 账户不可用（官方）
    lucid:   {action: new_evaluation, purchase_cost_policy: subsequent_repurchase_primary_140}
  live_failure: {action: not_applicable} # Live 已整体排除（§2.6）
```

各动作费用以 platform_params.yaml（当前冻结版）为准。
**Payout 会计与 S0 费用交接**：按 platform_params 的 `payout_accounting`
（gross 扣减余额、trader 现金 = gross×分成−通道费、terminal 同口径）与
`execution_costs.s0_cost_handoff`（单一保守平台费 $1.74 RT PROVISIONAL 烘入 S0 路径、
MC 不再扣交易费）执行，实现不得另行解释。

### 4.4 会计（v0.4：API 归类修正＋订阅引擎＋EV 单位）

```
strategy_account_EV      = 平台内交易净损益（分成前；交易费已在 S0 逐笔扣除，此层禁止再扣）
prop_operating_EV        = payout 流入 × 分成 − 评估/重置/重购（经订阅引擎与 Reset Credit
                           状态机计算，30 天 rebill 非自然月）− activation/reactivation
                           − payout 通道费（Topstep Primary = Wise $0；Lucid Primary = $30 保守代理）
                           − required_execution_costs（API $29/30天、必需实时数据/软件）
                           + terminal_value
net_business_EV_after_RD = prop_operating_EV − research_costs
                           （Databento、开发工具、研究软件；评估类与执行类费用不得入此层）
risk_haircut_EV          = retention × (payout 流入 + terminal_withdrawable)
                           − 全部运营成本 − research_costs；retention ∈ {100%, 75%, 50%}
```

**执行模式（冻结）**：`execution_mode_primary: automated_topstepx_api`（Topstep 侧，
$29/30 天进 prop_operating；$14.50 折扣价作 current-policy 敏感性）；Lucid 侧经
账户随附平台自动化（成本按 $0 建模并披露，实际软件费用留待 Gate 2 PoC 核实）。
**EV 单位（冻结）**：所有 P5/P50/P95、判定门槛与收敛容差 `max($25, 5%)` 的作用对象
= **24 个月总 prop_operating 结果 ÷ 24 = USD / 日历月**。

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

## 7. 冻结与证据修订（v0.4：证据 bundle 纳入冻结范围）

**Freeze Commit（tag `mc-freeze-v1`）包含全部四件**（两阶段流程同 S0 §12）：

```
MC_METHOD_SPEC.md
gate1/platform_params.yaml
gate1/evidence_registry.yaml
gate1/snapshots/2026-07-28/snapshot_manifest_v5.json
```

本文件 references 中的证据链哈希已在冻结前全部填入实值（v0.6 封口序）；
Freeze Commit A 前必须重跑 seal_check 确认引用与实际字节一致。
原始快照/截图文件本身以 manifest/registry 哈希锚定（体积原因
不入 commit，但任何字节改动都会被哈希暴露）。
冻结后的新官方证据（如 CME 费表确认 G9、人工客服复确认）按
**Evidence Resolution Addendum** 处理：原文＋哈希存档 → registry＋params 更新 →
MC1.x evidence-resolution commit → FREEZE_LOG 登记；状态机语义变化必须走此流程。

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
1. Lucid 违规判定采用 V-A（实时含浮亏）——后经 AI-bot 披露降级为冻结的保守建模假设；双变体删除，
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
