# Lucid Support 书面问询（Gate 1 开放核实项）

状态：草稿——由 Aaron 通过官方渠道（support chat / email）发送；收到回复后将
原文截图＋文本存档于本目录，作为 Level 2 证据关闭该开放项。
发送前后均不得由第三方网站替代此答案（章程证据层级）。

---

**Subject: LucidFlex — clarification on how MLL breach is evaluated intraday**

Hi Lucid team,

I have a question about the LucidFlex Max Loss Limit that I could not find
explicitly answered in the Help Center (I have read "LucidFlex Drawdown" and
"LucidFlex Funded Account").

I understand the MLL **updates** based on the highest end-of-day balance
(End-of-Day trailing). My question is about **when a breach is evaluated**,
not when the threshold updates:

During a trading session, suppose my account equity **including unrealized
open P&L** touches the current MLL threshold intraday, but the position then
recovers and the account **closes the day above the MLL**.

Which of the following applies to LucidFlex (evaluation and simulated funded)?

- (a) This is a breach: the MLL is a static intraday threshold and equity
  including unrealized P&L is compared against it in real time; touching it
  intraday fails the account (and/or triggers liquidation), OR
- (b) This is NOT a breach: the MLL is only evaluated against the account's
  end-of-day balance, so intraday unrealized drawdowns below the threshold
  do not fail the account as long as the day closes above it.

A simple "(a)" or "(b)" for evaluation accounts and for simulated funded
accounts respectively would be perfect. If there is a documentation page that
states this explicitly, a link would be appreciated.

Thank you!

---

发送后待办：
- [ ] 回复原文（文本＋截图）存入 `gate1/lucid_inquiry_reply/`
- [ ] platform_params.yaml 中 Lucid 违规判定从"双变体"改为确认值
- [ ] MC_METHOD_SPEC 若已冻结，以参数更新形式登记 FREEZE_LOG
