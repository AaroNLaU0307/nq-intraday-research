# IMPLEMENTATION RESOLUTIONS — B 类实现裁决登记（Addendum 候选）

> 定义：冻结规范存在歧义、且实现选择可能影响数值结果的裁决。
> 本文件不是冻结规范的同级依据；每项候选待 Aaron 批复后方可视为 Addendum 定案。
> A 类（规范唯一推出）裁决继续记录于 ADJUDICATIONS.md；C 类（冲突）= 立即停止，当前为零。

## 2026-07-28 登记（milestone 2 Phase 0 分类）

| ID | 内容 | 冻结章节 | 可能影响的输出 | 选择理由 |
|---|---|---|---|---|
| IR-1 (=R1) | breach 结算 = min(floor, 分钟 adverse 极值) − n×$1 | MC §2.2 | 爆仓后余额→重启费用→prop_operating_EV | 1 分钟 OHLC 下触发价不可观测；取更保守近似 |
| IR-2 (=R4) | max_favourable 极值口径 | S0 §10.1 | 仅描述性输出；不进判决统计量 | 与 adverse/Y4 对称 |
| IR-3 | Lucid payout "50% of profit" 基数 = 账户模拟盈利（balance−50000，gross 扣减后） | platform_params payouts.max_request | payout 金额与时点→EV | 与 scaling 基数一致；官方表措辞支持 |
| IR-4 | sizing anchor 含 $1.74 平台费 | MC §3 / S0 §8 | n 取整→EV（保守：anchor 大→n 小） | "incl cost" 的包含式读法 |
| IR-5 | Topstep credit 到期 age≥365 失效 | reset_policy.expires_after_days | 费用（保守：早失效→多付费） | 官方未定边界；防虚假 GO |
| IR-6 | 申请日损益不入任何 cycle；pass 撞 rebill 日仍计 $49 | payout_paths / subscription | 资格时点与费用（保守） | 官方只定义"不入下轮"；日粒度保守处理 |
| IR-7 | 场景 adverse slip 默认 = 该场景 per-side slip | S0 §6 | stop 成交价 | 暂用值；成本模型锁定前必须定稿（已有硬关卡） |
| IR-8 | Lucid 处理期 halt = 请求日＋后 2 个模板交易日 | MC §4.2 / payouts.processing "2 个工作日" | 交易日数→EV（保守：少交易） | 工作日≈模板交易日的近似 |
| IR-9 | Topstep API $29 计费自生命周期起（含 Combine 期） | billing_calendars topstep_api "from_activation" | 费用（保守：多计 1-3 期） | 自动化自 Combine 起即需 API |
| IR-10 | B2F 不消耗 6 次评估计数 | MC §4.3 failure_policy | 重启预算→EV | 冻结文本将 b2f 与 new_combine 列为不同 action；B2F 非 evaluation start |
| IR-11 | Y3 公式 = F9 在 [10:00,15:45) 类比；Y4/Y5 极值＋原始带符号 | S0 §5 | 仅描述性标签 | 唯一自然类比；见 ADJUDICATIONS 确认段 |

处置：以上全部为保守方向或仅描述性。批复方式：Aaron 逐条 accept/modify；
modify 项按两阶段流程形成正式 Addendum 并更新实现与测试。

## 批复定案（APPROVED_BY_AARON 2026-07-28，详见 IR_APPROVAL_PACKET.md）

- **A 类（纯实现解释）**：IR-2（diagnostic_only 标记＋静态测试）、IR-11。
- **diagnostic_only 附加条款**：IR-1（清算值不进任何判决输入；不变性测试固化——
  改变诊断清算值不得移动 prop_operating_EV 与 verdict）。
- **正式 Implementation Resolution Addendum（B 类）**：IR-1、IR-3、IR-4、IR-5、
  IR-6、IR-7（成本锁定硬条件维持）、IR-8、IR-9——冻结 tag 未动、历史未重写；
  影响 EV 的项在最终报告按方向披露（全部保守向）。
- **IR-10 = separate counters**：Primary 行为定案（B2F 不耗全局 6 次计数、每 XFA ≤2）；
  保守 sensitivity `b2f_consumes_attempt=True` 已实现并被机器强制限定为
  sensitivity-only（orchestrator 对 primary+consume 组合直接抛错）。
- 编号勘误：Aaron 批复第 3 条原文 "IR-4"，描述对应 IR-2；已按合理读法归位并明示。
本文件自此为已批复状态；后续新增 IR 以新条目追加。
