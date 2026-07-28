# IR_APPROVAL_PACKET — 11 项 Implementation Resolution 批复包

```yaml
status: PENDING_AARON_APPROVAL
date: 2026-07-28
reviewer: main agent（Phase 1 逐项重审，非沿用上轮结论）
批复方式: 每卡选 A/B/C/D；C/D 项列出受影响文件
```

**重审中的关键新发现**：IR-1 的结算值经溯源确认**不进入任何判决输入**
（prop_operating = payouts + terminal − fees；死亡余额只入 strategy_account_pnl 诊断项，
Lucid 死账不再使用、Topstep reset 后满血重置）——影响等级从"EV 输入"降为"诊断"。
**IR-10 是全包唯一非保守方向项**，单独标 C 请你二选一。

---

## IR-1 breach 结算 `min(floor, 分钟极值) − n×$1`
- 冻结章节：MC §2.2「损失按触发价 ± adverse slippage」
- 歧义：1 分钟 OHLC 下触发价不可观测
- 重审四问：(a) 会低于 MLL？会（极值可穿地板）；(b) 死亡余额影响商业会计？
  **否**（溯源如上，不进 prop_operating/verdict）；(c) 应否截断为清算值？无必要
  （仅诊断字段；截断反而丢信息）；(d) 两平台同一处理？是（base.breach_settlement 唯一实现）
- 判决输入：不变 ｜ 方向：保守 ｜ 描述性：是（业务层面）
- 规范唯一推出：否
- **推荐：B**；新增测试：断言结算值不进入 prop_operating（本轮已加）

## IR-2 max_favourable 极值口径
- 冻结章节：S0 §10.1（列字段未定义路径）
- 重审确认：全代码溯源——不进 Oracle 标签、成本、feasibility、verdict 任何一项
- **推荐：A**（纯实现解释）；已在 contracts.py 加 `diagnostic_only` 显式标记＋静态测试

## IR-3 Lucid payout 利润基数 = 账户模拟盈利（gross 扣减后 balance−50000）
- 冻结章节：platform_params payouts.max_request "50% of profit"
- 判决输入：**改变**（payout 金额/时点→EV）｜ 方向：中性（官方表措辞支持此读法，
  与 scaling 基数一致）｜ 唯一推出：否（cycle-profit 读法未被排除）
- **推荐：B**；不接受时改 lucid.py `_gross_candidate` ＋ test_lucid/test_orchestrator

## IR-4 sizing anchor 含 $1.74 平台费
- 冻结章节：MC §3「含成本」（含成本本身是冻结文本；歧义仅在费是否属"成本"）
- 判决输入：改变（n 取整）｜ 方向：保守（anchor 大→n 小）
- **推荐：B**；不接受时改 paths.py anchor 计算＋test_oracle

## IR-5 Reset Credit 到期边界 age≥365 失效
- 冻结章节：reset_policy.expires_after_days: 365（未定含当日与否）
- 判决输入：改变（费用，量级 ~$49 级）｜ 方向：保守
- **推荐：B**；不接受改 topstep.ResetCredit.expired 一行＋测试

## IR-6 申请日损益不入任何 cycle；pass 撞 rebill 日先扣 $49
- 冻结章节：payout_paths.standard（只定义"不入下轮"）；subscription pass_deadline
- 判决输入：改变（资格时点＋≤$49/次）｜ 方向：保守
- **推荐：B**

## IR-7 场景 adverse slip 暂用值（= 该场景 per-side slip）
- 冻结章节：S0 §6（未冻结独立 adverse 网格）
- 判决输入：改变（stop 成交价）｜ 方向：待定
- **推荐：B（附硬条件）**——成本模型锁定时定稿为冻结参数，已有 pre-run 硬关卡；
  在定稿前任何真实运行本就被 G9 阻断

## IR-8 Lucid 处理期 halt = 请求日＋2 个模板交易日
- 冻结章节：MC §4.2 halt；payouts.processing "2 个工作日"
- 判决输入：改变（Lucid 侧少 2 交易日/次 payout）｜ 方向：保守
- **推荐：B**

## IR-9 API $29 自生命周期起计费（含 Combine 期）
- 冻结章节：billing_calendars topstep_api "from_activation"（activation 指 API 订阅激活）
- 判决输入：改变（多计 1-3 期 ≈ $29-87）｜ 方向：保守（自动化自 Combine 起即需 API，
  事实上也更真实）
- **推荐：B**

## IR-10 ⚠ B2F 不消耗 6 次评估计数 —— 全包唯一非保守项
- 冻结章节：MC §4.3 lifecycle_attempt_policy（funded_failure_restart_consumes_attempt: true，
  注释枚举 new_evaluation/new_combine）vs failure_policy（b2f 为独立 action、自带 ≤2 上限）
- 歧义真实：字段名泛指 vs 注释枚举
- 判决输入：**改变**（重启预算→EV）｜ 方向：**乐观（虚假 GO 方向）**——不计数 = 更多复活机会
- **推荐：C，请二选一**：
  (i) 保守版：B2F 也消耗计数（total 复活预算更紧）→ 改 orchestrator ~3 行＋2 个测试；
  (ii) 文本版：维持不计数（依据：b2f 是政策表中与 new_combine 并列的不同 action，
      且自带独立 ≤2 上限）
  主 agent 倾向：默认应选 (i) 保守版，除非你认可文本读法
- 受影响文件（若选 i）：orchestrator.py、test_orchestrator.py

## IR-11 Y3/Y4/Y5 统计口径（F9 类比；极值；原始带符号）
- 冻结章节：S0 §5（Y3 仅名称；Y4/Y5 一行定义）
- 判决输入：不变（纯描述性标签，不进 verdict）
- **推荐：A**

---

## 汇总

| 推荐 | 项 |
|---|---|
| A（纯实现解释） | IR-2, IR-11 |
| B（保守 Addendum） | IR-1, IR-3, IR-4, IR-5, IR-6, IR-7*, IR-8, IR-9 |
| C（需你决定） | **IR-10** |
| D | 无 |

*IR-7 附硬条件：成本锁定前不得真实运行（既有关卡覆盖）。
批复后：A/B 项转正式 Addendum 登记；IR-10 按你的选择实施并补测试。
