# Gate 1 开放项关闭记录 — LucidFlex MLL 盘中违规判定

```yaml
resolved: 2026-07-28
evidence: lucid_reply_2026-07-28.png
evidence_sha256: 620dee3911e616fafeacf9c399da054dfda4cf1414a0d0a24fd46d2a0358925a
evidence_level: 2-AI   # 修订（同日）：Aaron 披露该回复由 Lucid AI support bot 生成，非人工
question_ref: gate1/lucid_inquiry.md
retention_rationale: |
  V-A 维持 Primary 的两点理由：(a) 与官方页原文一致（"If your account balance
  reached the MLL, your account will be breached"）；(b) V-A 是保守方向——若 bot
  答错、真实为仅日终判定，建模只会低估生存率导向 STOP，不产生虚假 GO。
  可选跟进：向人工客服复确认（非阻断）。
```

## 答复内容（转录）

For LucidFlex (evaluation and funded):
- Evaluation: **(a)**
- Funded: **(a)**

"Even though the MLL is calculated using end-of-day closing balances,
unrealized P&L still counts. If your equity (including open trades) touches
the MLL at any time during the day, it is considered a breach. So an intraday
dip below the MLL — even if you recover and close the day above it — still
counts as a breach."

## 结论

**LucidFlex = V-A**：阈值按日终余额更新（EOD trailing），但违规监控为
盘中实时、以含未实现盈亏的 equity 与当前阈值比较，触及即违规。
V-B（仅日终判定）删除。两个候选平台（Lucid、Topstep）均为实时判违规
→ MC 违规检查统一使用 adverse-path（S0 §10.1 分支选择，无冻结文本冲突）。

## 证据限制与非阻断跟进

- 截图为聊天窗口裁剪，未含客服署名与时间戳；建议在同一会话中请求
  email transcript 存档以强化证据（非阻断）。
- 未答复的子问题（非阻断，可同线程追问）：盘中违规时是否自动强平及成交
  处理；EOD 更新使用的官方 session 收盘时间与时区（转录时以官方文档为准）。
- MC 建模保守处理：违规 = 账户即时死亡，最终损失按触发价 ± adverse slippage。

## 流程定性

MC_METHOD_SPEC 尚未冻结（v0.1 DRAFT 被评审否决），故本关闭直接并入 v0.2，
不构成冻结后修订；若未来出现同类冻结后证据，按 Evidence Resolution
Addendum 流程处理（MC 规范 §7）。
