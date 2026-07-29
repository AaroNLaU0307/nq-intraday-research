# DECISION PACKET — F10 多事件日的作用域（IR-12 × IR-13 组合口径）

状态：PENDING（SA-3 提出；推荐栏留空给 main agent）
来源：M4-T4 / SA-3 S0_INPUT_PREFLIGHT，input_commit `d09ce4e`

## 1. 问题

IR-12 规定"同日多事件 → 冻结 F10 单类别记 NA"，并写明"报告全部多事件
日期与数量（**当前 19 天**）"。IR-13 规定 F10=FOMC **仅**取官方预定
statement 发布日（92 天），会议第一天不标。

两条已批复决策单独看都唯一，但**组合后 F10 记 NA 的日期集合有两种读法**，
相差 10 个交易日：

- 读法 A（在 IR-13 之后判定多事件）：多事件 = 该日映射到 ≥2 个**冻结
  F10 类别** {CPI, NFP, FOMC(92 预定 statement 日)} → **9 天**。
- 读法 B（按 IR-12 字面的 19 天）：多事件 = f10_events.csv 原表同日出现
  ≥2 个 event_type（FOMC 行含会议第一天/conference call/notation vote）
  → **19 天**。

## 2. 冻结章节与依据

- 预注册行 62：`F10 is_event_day ∈ {CPI, NFP, FOMC, none}`（单一类别）。
- 预注册行 45：NA 政策（记 NA，日不删除，每表报 NA 数）。
- IR-12（D1 Option C，APPROVED 2026-07-29）。
- IR-13（D2+D2a Option A＋限制，APPROVED 2026-07-29）。

## 3. 事实（本次 preflight 实测，f10_events.csv sha256 5e92ad00…bb5e8c）

- 原表 468 行；is_fomc_statement_day=True 共 **96** 行；减 IR-13 列举的 4 个
  非预定行动（2019-10-11、2020-03-03、2020-03-15、2020-03-23）= **92**，
  与 IR-13 所述 92 完全一致。
- 原表同日 ≥2 个 event_type 的日期：**19 天**（与 IR-12 括注一致，也与
  F10_SOURCE_LOG §5.7 的 19 天一致）。
- 按 IR-13 归类后仍映射到 ≥2 个冻结类别的日期：**9 天**
  2013-10-30、2014-09-17、2014-12-17、2016-03-16、2017-03-15、2017-06-14、
  2017-12-13、2019-12-11、2020-06-10。
- 两者之差的 **10 天**：2010-10-15、2013-06-18、2013-09-17、2013-12-17、
  2014-03-18、2014-06-17、2015-09-16、2015-12-15、2018-06-12、2019-10-04。
  这 10 天的 FOMC 行**都不是**预定 statement 发布日（会议第一天 /
  conference call / unscheduled 会议日），按 IR-13 本就不编码为 FOMC。
- 其中 2019-10-04 是唯一的 NFP+FOMC 日；其 statement 实际于 2019-10-11
  发布（F10_SOURCE_LOG §5.3）。

## 4. Option A（在 IR-13 之后判定，F10 NA = 9 天）

这 10 天各自只映射到一个冻结类别（CPI 或 NFP），单类别无歧义，故不记 NA，
按其唯一类别编码。多事件 NA 仅在冻结类别真正冲突时发生。

## 5. Option B（按 IR-12 字面 19 天，F10 NA = 19 天）

上述 10 天也记 NA，理由是"当日客观上存在两个官方事件"，即便其中一个按
IR-13 不进入 F10 编码。

## 6. 影响方向

- 样本日数不变（两案都不删日）；Primary 判据、成本、标签均不受影响。
- 差异仅在 F10 的取值与 NA 计数：A 案 F10 NA = 9、10 天保留为 CPI/NFP；
  B 案 F10 NA = 19、这 10 天的 CPI/NFP 信息在 F10 上丢失（仍留在
  diagnostic sidecar）。
- A 案信息量更大；B 案更贴 IR-12 括注的字面数字。
- 两案都不需要发明事件优先级（IR-12 明令禁止），故都不违反该禁令。

## 7. main agent 推荐

main agent 推荐 **Option A（IR-13 之后判定，F10 NA = 9 天）**（仅供
Aaron/ChatGPT 参考）：IR-12 记 NA 的立法目的是"不得在冻结类别之间发明
优先级"；那 10 天的额外 FOMC 条目按 IR-13 本就不进入冻结 F10，当日只
剩一个冻结类别，**无冲突可言、无优先级可发明**，记 NA 反而无端丢弃
10 个无歧义标签日。IR-12 括注"19 天"是 IR-13 组合效果可见之前对原表的
计数，非独立立法。完整 19 天结构无损保留在 diagnostic sidecar
（IR-12 本就要求），信息零丢失。

## 8. 是否阻塞

**部分阻塞**：阻塞 F10 的 NA 最终计数定稿。不阻塞漏斗、锚点、其余
F1-F9/F11、标签锚点等全部段落——这些已完成并交付。

preflight 当前实现按 **Option A（9 天）** 计数，并把 19 天原表口径完整
输出在 `raw_multi_event_days_pre_ir13_sidecar` 中，两个数字同时披露，
未做任何不可逆选择；若批 B 案，只需改一处判定并重跑。

## 9. 涉及文件

- `gate1/f10_event_calendar/f10_events.csv`（只读，无需改）
- `scripts/s0_input_preflight.py`（`load_f10()`）
- `S0_INPUT_PREFLIGHT.json` / `S0_INPUT_PREFLIGHT_REPORT.md`
- 未来特征构建模块的 F10 编码

## 10. 需 Aaron 批准的问题

F10 的"多事件"判定发生在 IR-13 归类**之后**（9 天，Option A）还是按
IR-12 括注的**原表**口径（19 天，Option B）？
