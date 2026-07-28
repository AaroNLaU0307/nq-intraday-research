# ADJUDICATIONS — 主 agent 对冻结规范的解释裁决记录

> 裁决对冻结文本的解释具有约束力；冻结文本本身不变。新增裁决只能追加。

## 2026-07-28（S0/MC 工程首轮，采纳 spec-audit findings）

**R1 · breach 结算统一约定**（audit M1）：MC §2.2 "损失按触发价 ± adverse slippage"
的唯一实现 = `base.breach_settlement()`：结算余额 = min(floor, 触发分钟 adverse 极值
equity) − n × $1.00/micro（暂用 Conservative 2 tick；成本模型锁定时定稿）。
三个引擎（lucid/topstep/account）一律调用同一函数。

**R2 · 绝对仓位上限按平台**（audit H1）：Lucid 40 / Topstep 50 micros；
`platform.max_contracts_today()` 必须内嵌各自绝对上限，`n_micros` 仅在显式传参时
额外裁剪。原全局 40 硬编码为错误，已修复。

**R3 · F7 零隔夜区间 = 0.0**（audit M2，推翻我给 A2 的口头指示）：按冻结字面公式
(ON_high−ON_low)/ADR14，零区间无除零问题 → 0.0；F6 为 0/0 → NA。隔夜数据缺失两者皆 NA。

**R4 · max_favourable 采用极值口径**（audit M4）：与 adverse 对称（多头分钟 high／
空头分钟 low）；stop/退出 bar 只按已实现值计（不 credit 顺序不可知的有利极值）。

**R5 · 生命周期组合裁决**（audit M5）：平台 Lifecycle 类为 canonical 账户模拟器；
`account.run_account` 降级为 sizing 测试挽具；business-layer orchestrator（下一里程碑）
直接驱动 Lifecycle.step_day/process_day，sizing 经 account.py 纯函数。

**R6 · 运行护栏机械化推迟至数据加载层**（audit M6）：真实数据的唯一入口将是
data loader，`assert_real_run_allowed()` 在 loader 构造时强制调用；本轮为纪律性约定。

**确认类裁决**（对 subagent unresolved 的批复）：
- 排除日"无成交"按 zero-bars 操作化；真实 loader 落地时补 volume 合计==0 检查（A1）。
- roll window 含切换日本身（±2 含 0）（A1）。
- Y4/Y5 极值口径＋原始带符号值（不设 0 下限）；Y3 = F9 在 [10:00,15:45) 的类比公式（A2）。
- F8 方向源 = sign(C0959−O0930)（几何驱动方向），与标签层 d_open（可交易方向，
  NA→0）为不同对象；行为不变，语义已注释（A2/audit M3）。
- sizing anchor 含 $1.74 平台费（inclusive 读法）；E2 的 planned_stop 存 None（A3）。
- 各场景 adverse slip 默认 = 该场景 per-side slip，成本锁定前为暂用值（A3/audit L）。
- Lucid payout "50% of profit" 基数 = 账户模拟盈利（balance−50000，gross 扣减后），
  与 scaling 基数一致（A4）。
- Topstep credit 到期边界 age≥365 失效（保守）；申请日损益不入任何 cycle；
  pass 恰逢 rebill 日多计一次 $49（保守，接受）（A5）。
- 无交易日也执行 eod_update（floor 单调，无害）（A6）。
- 理论 Oracle 必须以 Base 场景调用（调用方职责，运行器将断言）（A3/audit L）。
