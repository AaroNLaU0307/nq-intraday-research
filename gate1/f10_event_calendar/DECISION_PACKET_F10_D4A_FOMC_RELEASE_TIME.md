# DECISION PACKET — F10 / D4a：FOMC 2010–2015 发布时刻无官方记载

```yaml
id: D4a
task: M4-T1 / SA-1
raised_by: SA-1（证据采集）
blocking: 不阻塞事件日期；仅涉及 f10_events.csv 的 official_release_time_et 列
related: TASKBOARD D4（官方来源缺失时的 fail-closed 规则）
# 编号说明：项目级 D5 已被 symbology 决策占用，故此包编为 D4a（属 D4 证据缺口族）
```

## 问题

任务书要求 `official_release_time_et` **以官方页面记载为准，不得凭记忆填写**。
federalreserve.gov 现行归档的 FOMC statement 新闻稿页中，**2016 年起**才在正文
写出 `For release at H:MM p.m. E[SD]T`；**2010–2015 年**的 statement 页一律只写
`For immediate release`，不含时钟时间。

窗口内 96 个 statement 日中，**45 行**因此无官方时刻可填。

## 冻结章节

- 任务书 IMPLEMENTATION REQUIREMENTS：
  "以官方页面记载为准填 `official_release_time_et`，不得凭记忆填写"。
- 任务书 EVIDENCE REQUIREMENTS：
  "达不到 Level 1 官方标准的年份不得静默用低级来源顶替"。
- `PROJECT_CHARTER.md` 元规则：可验证事实必须核对 Level 1–2 证据后才接受，
  不因表达自信而接受。

## 事实

1. **有官方时刻的**：2016-01-27 起共 51 行，取自 statement 页
   `<p class="releaseTime">For release at ...</p>`（已归档，逐份 SHA-256 在
   `f10_evidence_registry_fragment.yaml`）。其中包含非 14:00 的四例：
   2019-10-11 = 11:00、2020-03-03 = 10:00、2020-03-15 = 17:00、
   2020-03-23 = 08:00（ET）。
2. **无官方时刻的**：2010–2015 共 45 行，页面正文为 `For immediate release`。
3. **PDF 回退不可用**：2016 年起 statement 页附
   `/monetarypolicy/files/monetary<yyyymmdd>a1.pdf`；2010–2015 年该直链
   **HTTP 404**（已实测 2010-01-27、2012-06-20 等）。
4. **候选替代源 1 — 2011-03-24 官方新闻稿**
   （`fed_press_20110324a_press_briefings.htm`，已归档）：
   > "In 2011, the Chairman's press briefings will be held at 2:15 p.m.
   > following FOMC decisions scheduled on April 27, June 22 and November 2 …
   > For these meetings, the FOMC statement **is expected to be released at
   > around 12:30 p.m.**, one hour and forty-five minutes earlier than for
   > other FOMC meetings."

   性质：**事前预告**（"is expected"、"around"），且"其他会议"的 2:15 p.m.
   只能由"提前 1 小时 45 分"反推得出（Level 4 推断，非直接记载）。
   覆盖面也只有 2011 年。
5. **候选替代源 2 — 理事会新闻稿 JSON feed**
   （`fed_ne_press_feed.json`，已归档）：每条新闻稿带时间戳，但为**上站时间**
   而非官方发布时刻。证据：2010 年八次 statement 一律为 `2:20:00 PM`；
   2011-04-27 为 `12:40:00 PM`、2011-06-22 为 `12:35:00 PM`——系统性晚于既定
   时刻数分钟，且同一年内取值不一致。**不可作为官方发布时刻**。
6. SA-1 当前处理：这 45 行填哨兵值
   `NOT_ATTESTED_IN_OFFICIAL_SOURCE`，未做任何推断填充。

## Option A：维持哨兵值（SA-1 当前状态）

- 完全符合"不得凭记忆填写"与"不得静默顶替"。
- `official_release_time_et` 列在 2010–2015 段不可用于任何下游逻辑。
- 若下游只用日级 `is_event_day`（预注册行 62 的字面定义），**零影响**。

## Option B：用官方一级证据可推得的值填充，并标注推断等级

- 2011 年三次记者会会议（04-27、06-22、11-02）填 `12:30`，
  其余 2010–2015 各行填 `14:15`（2010–2012）/ `14:00`（2013–2015）。
- 问题：`14:00` 与 `14:15` 的分界年份**在归档官方页面中找不到直接记载**；
  Option B 实际要求接受 Level 4 推断进入 Level 1 表，与冻结证据规则冲突。
- 若采用，必须在 CSV 之外增设推断等级标注（当前 schema 已冻结，无处安放）。

## Option C：把该列在 2010–2015 段整体标记为 `NA`，并在冻结附注中声明
`official_release_time_et` 仅对 BLS 事件与 2016 年起的 FOMC 事件有效

- 与 Option A 结果相同，但把"该列的适用范围"写进冻结记录，避免下游误用。
- 代价：需要一条冻结附注（不改预注册正文，走 addendum 流程）。

## 对样本与 Primary 的影响方向

**方向性影响为零，前提是 F10 只按日级类别编码**（预注册行 62 的字面定义即如此：
`is_event_day ∈ {CPI, NFP, FOMC, none}`，不含时刻）。

只有在下游试图用发布时刻做**盘中窗口**判断时才有影响。本项目的观察窗为
09:30–09:59、决策 10:00 —— BLS 的 08:30 ET 发布**早于**观察窗开始，
FOMC 的 14:00/14:15 ET 发布**晚于**决策时点，两者都不落在观察窗内。
唯一需要时刻信息才能判定的是 2020-03-23 的 **08:00 ET** 声明
（早于 08:30，仍在观察窗之前）与 2020-03-15 的**周日 17:00**（非交易日发布，
影响的是次日 03-16 的开盘）——而这两行**恰好都有官方时刻**。

结论：45 行缺口不触及任何需要时刻判断的日子。

## 是否阻塞

不阻塞。事件日期与三个布尔位全部为 Level 1；仅时刻列在 2010–2015 为哨兵值。

## 涉及文件

- `gate1/f10_event_calendar/f10_events.csv`（`official_release_time_et` 列）
- `gate1/f10_event_calendar/F10_SOURCE_LOG.md` §5.5
- 若选 Option C：需要一条冻结附注（FREEZE_LOG / addendum，归 main agent）

## 需 Aaron 明确批复的问题

1. 采用 **A / B / C** 中的哪一个？（SA-1 建议 **C**：结果与 A 相同，
   但把该列的适用范围写死，杜绝下游误用。）
2. 是否确认 F10 编码**只使用日级类别**、不使用 `official_release_time_et`？
   若确认，本缺口对 Primary 的影响可正式判为零。
3. 是否需要 SA-1 继续在 federalreserve.gov 内寻找 2012–2015 的时刻记载？
   （已检索：statement 页、statement PDF、FOMC 日历/历史页、年度会议日程新闻稿、
   新闻稿 JSON feed，均无直接记载。继续检索的边际收益预计很低。）
