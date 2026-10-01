# DECISION_PACKET_VENDOR_DEGRADED_ANCHOR

状态：PENDING_AARON（阻塞第一次真实 S0 的第三次尝试）
提出：main agent，2026-08-01，第二次尝试 Stage B 失败后
事件：attempts/S0-T001-A20260801T162047Z（incident INC-fa9234e0e541）

## 0. 事实（全部数值可机器复现，均为 preflight 级结构事实）

1. 第二次尝试：**Stage A 十三门全过**（IR-25 自锁修复经实战验证），
   Stage B `preflight_assertions_match` 门失败。**exposure 未消耗，
   S0-T001 完好。**
2. 失配面完整清单（密封 incident 原文）：缺失键 1 个
   `na_reason.anchor.prev_rth_close.prev_rth_close_anchor_missing`；
   失配值 5 个，全部属 prev_rth_close/F5 家族。
3. 期望（锁定 json 9d6dd1c1 经 translate）vs 实测（生产链）：

   | 键 | 期望 | 实测 |
   |---|---|---|
   | anchor.prev_rth_close.available | 2864 | 2882 |
   | anchor.prev_rth_close.missing | 18 | 0 |
   | feature.F5.constructible | 2806 | 2800 |
   | feature.F5.na | 76 | 82 |
   | na_reason.F5.prev_rth_close_anchor_missing | 17 | 23 |
   | na_reason.anchor.prev_rth_close.…_missing | 18 | （未产生） |

   F5 其余原因（adr14_warmup=12、roll_transition_day_na=47）两侧一致。

## 1. 根因——两层，互相独立

### 层 1（纯记账镜像缺陷，无语义争议）

`scripts/s0_real_run.py` `structural_actuals_from`：
`prev_missing = [d for d in elig if d not in universe.prev_rth_close]`。
但 context.py `_prev_close_map` 给**每一天**都建条目（缺失锚点存
None＋cause）——成员测试永远为假 → missing 恒报 0、NA-reason 键从不
产生。真实值（按 `is None` 判）：24 缺失＝1 首日＋12 前日早收盘终
bar 缺失＋11 vendor 类。这解释 anchor 两键失配与缺失键。

### 层 2（语义分歧，6 天，需要裁决）

condition.json 实况：3604 available ＋ **20 degraded**；20 个标记日中
**11 个有 bar（官方收盘价存在）、9 个零 bar**。

- **preflight（锁定数字之源，scripts/s0_input_preflight.py:519-521）**：
  `vendor_zero_bar = zero_bar ∩ 标记日`——只有**既标记又零 bar**的
  参照日才致锚点 NA；**标记但有 bar 的参照日照常提供官方收盘价**。
  由此得 18＝12＋5＋1、F5 NA 76。IR-19 批复正是对这组数字做出、
  M5-T5 重跑后锁定（json 9d6dd1c1，packet §0 引用）。
- **生产接线（scripts/s0_real_run.py load_real_session_schedule:789）**：
  `degraded = 全部 condition != "available"`（20 日全量）传入
  SessionSchedule；context.py `_prev_close_map:760` 对任何参照日
  ∈ 该集合一律强制 NA。由此 24＝12＋11＋1、F5 NA 82。
- 差值 6＝以"标记但有 bar"日为前一实际 session 的合格日数。
- context.py 本身正确消费传入集合；其 docstring "(their anchor is
  NA)" 是实现者对 IR-19 的转述（over-general），非冻结文本。

## 2. 裁决问题（单点）

**"vendor-degraded 但当日有 bar" 的参照日，其官方收盘价是否可用作
prev_rth_close 锚点？**

- **Option A（推荐）：可用——与已批准锁定数字一致。** degraded 标记
  表数据质量告警而非缺失；收盘 print 客观存在；IR-19 批复、M4 收口、
  M5-T5 重锁全部建立在 18/76/2806 之上。修复＝入口接线把传入
  SessionSchedule 的集合收窄为 `标记 ∩ 零bar`（复刻 preflight
  519-521 行语义），context.py **一字不动**（其锁定哈希不变）。
- Option B：不可用——按生产现状 24/82/2800 重跑 preflight、重锁
  json、重渲染 packet。**不推荐**：等于用实现侧的转述推翻已批复
  数字；且 degraded-有-bar 日的收盘价在 QA/Addendum 从未被判不可信。

## 3. 修复方案（Option A 下，全部在入口，主代理专属面）

1. 层 1：`structural_actuals_from` 成员测试改
   `universe.prev_rth_close[d] is None`，cause 取自
   `prev_rth_close_cause`（既有逻辑保留）。
2. 层 2：RealChain 数据装载后、build_universe 前，从已载 summaries
   推导零 bar 集（窗口内排期日无 bar/n_rth==0），
   `vendor_degraded_dates = 标记 ∩ 零bar`。
3. 预期机械后果：24→18、82→76、2800→2806、23→17，六键全符锁定
   json；预跑同款诊断脚本核对后再走电池。
4. 收口链照 IR-25 先例：修复 → 全电池 → 新 commit → Opus 只读聚焦
   审计（重点＝Stage B 可满足性：隔离副本模拟授权态跑到 Stage B 门
   通过为止，不进 Stage C）→ 全 CLOSED → 追加 READY 事件 →
   停等 Aaron 对新 HEAD 的 §10。

## 4. 不做的事（除非另令）

- 不动 context.py/dataset.py（冻结哈希家族保持）；
- 不动锁定 json/preflight 工件；
- 裁决前不改任何 tracked 文件；
- 失败工件与事件行照例永久保留（行"+"×2 已在册）。
