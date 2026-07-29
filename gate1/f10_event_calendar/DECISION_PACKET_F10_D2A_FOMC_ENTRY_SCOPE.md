# DECISION PACKET — F10 / D2a：FOMC 条目类别的取舍

```yaml
id: D2a
task: M4-T1 / SA-1
raised_by: SA-1（证据采集）
blocking: 不阻塞 f10_events.csv 的产出；阻塞 F10 编码落地（SA-3 的 F10 段）
parent: TASKBOARD D2（FOMC 采用会议日还是 statement 发布日）
```

## 问题

预注册行 62 只写 `is_event_day ∈ {CPI, NFP, FOMC, none}`，没有定义"FOMC"
指哪一类日历条目。federalreserve.gov 的官方 FOMC 页面把条目分为五类：

`Meeting`（例会）/ `Conference Call` / `(unscheduled)` / `(notation vote)` /
`(cancelled)`。

窗口内非例会条目共 13 条（另有 1 条被官方标为 cancelled）。是否把它们计为
FOMC 事件日，直接改变样本中 `is_event_day = FOMC` 的天数。

## 冻结章节

- `STUDY_0_PREREGISTRATION.md` 行 62：`is_event_day ∈ {CPI, NFP, FOMC, none}
  （BLS/Fed 官方时刻表快照）` —— 只给集合，未给 FOMC 的界定。
- `PROJECT_CHARTER.md` 证据层级：Level 1 优先；低层级不得推翻高层级。

## 事实（全部来自已归档 Level 1 原始件）

窗口内（2010-06-06 → 2021-12-31）非例会条目：

| 官方标题 | 类别 | 会议日 | statement 日 |
|---|---|---|---|
| October 15 Conference Call - 2010 | Conference Call | 2010-10-15 | 无 |
| August 1 Conference Call - 2011 | Conference Call | 2011-08-01 | 无 |
| November 28 Conference Call - 2011 | Conference Call | 2011-11-28 | 无 |
| October 16 (unscheduled) - 2013 | unscheduled | 2013-10-16 | 无 |
| March 4 (unscheduled) - 2014 | unscheduled | 2014-03-04 | 无 |
| October 4 (unscheduled) - 2019 | unscheduled | 2019-10-04 | 2019-10-11 |
| March 2 (unscheduled) Meeting - 2020 | unscheduled | 2020-03-02 | 2020-03-03 |
| March 15 (unscheduled) Meeting - 2020 | unscheduled | 2020-03-15 | 2020-03-15 |
| March 19 (notation vote) - 2020 | notation vote | 2020-03-19 | 无 |
| March 23 (notation vote) - 2020 | notation vote | 2020-03-23 | 2020-03-23 |
| March 31 (notation vote) - 2020 | notation vote | 2020-03-31 | 无 |
| August 27 (notation vote) - 2020 | notation vote | 2020-08-27 | 无 |
| March 17-18 (cancelled) Meeting - 2020 | **cancelled** | 未召开 | 无 |

补充事实：

- 有 statement 的非例会条目共 4 条（2019-10-11、2020-03-03、2020-03-15、
  2020-03-23），其中 3 条集中在 2020 年 3 月。
- 2010-10-15 的 conference call 与当日 CPI 发布**同日**。
- 2020-03-15 的 statement 发布于**周日 17:00 ET**，2020-03-23 发布于 **08:00 ET**
  （即 RTH 开盘前），均不在常规 14:00 ET。
- **SA-1 已做的唯一主动排除**：`(cancelled)` 条目（2020-03-17、2020-03-18）
  不进表——该次例会未召开，记入等于断言未发生的事实。

## Option A：F10 的 FOMC 只取**例会**（scheduled Meeting）

- 每年恒为 8 次会议、8 份 statement，跨年可比性最强。
- 2020 年 3 月三次临时声明（含盘前 08:00 与周日 17:00 的两次）被编为 `none`，
  而这三天恰是 2020 年波动最极端的日子之一。
- 时代切片 2018–2021 的事件日定义与前两片一致。

## Option B：收录**所有实际发生的官方 FOMC 条目**（SA-1 当前表的内容）

- 与"官方时刻表快照"的字面含义一致：官方列了什么就是什么。
- 2020 年 FOMC 会议日 21 天、statement 10 天，明显高于其余年份；
  2013/2014/2019 各多 1 天无 statement 的 unscheduled 条目。
- 风险：notation vote 是**书面表决**，多数没有对外声明，把它当"事件日"
  在市场语义上难以成立（2020-03-19、03-31、08-27 三天当日无 FOMC 声明）。

## Option C（折中，需明确写入冻结附注）

`is_event_day = FOMC` 仅当**当日有官方 FOMC statement 发布**，
无论该 statement 来自例会、临时会议还是 notation vote；
无 statement 的会议日一律不计。

- 直接对应 `is_fomc_statement_day = true`，共 96 天，判定规则单一可验证。
- 自动吸收 2020-03-03/15/23 与 2019-10-11，同时排除全部无声明的会议日与
  notation vote。
- 与 D2"采用会议日还是 statement 日"合并为同一条规则，减少一个自由度。

## 对样本与 Primary 的影响方向

| 选项 | 窗口内 FOMC 事件日数 | 方向性影响 |
|---|---|---|
| A（仅例会） | 会议日 177 / statement 92 | 事件日最少，`none` 组最大；2020-03 极端日被划入 `none`，可能抬高 `none` 组的波动 |
| B（全收录） | 会议日 191 / statement 96 | 事件日最多；引入 8 个当日无任何 FOMC 对外声明的日子，属噪声方向 |
| C（有声明才算） | 96 | 与市场语义最贴合；相对 A 的 statement 集多 4 天，相对 B 少 95 天 |

三个选项的差异集中在 2013/2014/2019/2020 四年，会直接改变**按年表格**与
**leave-one-year-out** 的分组，尤其 2020 年。差异不对称：2020-03 的三天是
样本中波动最极端的一段，任何一种归类都会影响该年的事件日/非事件日对比。

**注意**：本决策在任何 S0 数字产生之前作出，不存在"见数改规"通道
（S0 双阻断持续生效，SA-1 未运行任何策略计算）。

## 是否阻塞

- 不阻塞：`f10_events.csv` 已产出，三类日期全部如实提供，信息无损——
  任一选项都可由现表用一行过滤实现。
- 阻塞：SA-3 的 F10 覆盖段定稿、以及 F10 特征编码落地。

## 涉及文件

- `gate1/f10_event_calendar/f10_events.csv`（无需重跑，只需下游过滤规则）
- `gate1/f10_event_calendar/F10_SOURCE_LOG.md` §5.3、§5.4、§5.6
- 下游：F10 编码实现与 `S0_INPUT_PREFLIGHT`

## 需 Aaron 明确批复的问题

1. `is_event_day = FOMC` 采用 **A / B / C** 中的哪一个？
2. 若选 C：与 D2 是否合并为同一条冻结附注（"FOMC 事件日 = 有官方 statement
   发布的日历日"）？
3. `(cancelled)` 条目的排除（2020-03-17、2020-03-18）是否确认？
   （SA-1 认为这是事实判断而非方法选择，但仍提请确认。）
