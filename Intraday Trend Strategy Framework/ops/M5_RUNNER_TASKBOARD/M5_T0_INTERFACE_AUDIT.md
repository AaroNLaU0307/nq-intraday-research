# M5-T0 共享接口定稿 — 现状审计与模块状态表

main agent 亲自完成（2026-07-31）。纠正 M5 任务板初版的事实错误：
features/labels/oracle/costs/paths 及 contracts 均有 M1 骨架期的历史实现
与专属测试，**不得**按"新建"派工、不得从零覆盖。

## 模块状态表

| 文件 | 状态 | 依据与说明 |
|---|---|---|
| `src/itsf/contracts.py` | **EXTEND（main agent，已完成）** | 位置在包顶层（非 s0 子包，任务原文的路径笔误在此勘正）。既有：MNQ 常数、$1.74、CostScenarioParams、TradePathRecord、DayFeatures、DayLabels、AccountEvent，文件头即声明 MAIN-AGENT OWNED。本次扩展：RunStage/TrialState 枚举、APPROVED_NA_REASONS（冻结＋IR＋preflight 分类）、四个错误类型、RunConfig（frozen dataclass，禁嵌 Preflight 观测数字）；DayFeatures.is_event_day 放开为 `str \| None`（IR-12/18 的 F10=NA 此前**无法表达**——审计发现的真实缺口） |
| `src/itsf/s0/features.py` | **KEEP＋定点 EXTEND** | F1-F9 完整冻结引用实现（F3/F8 close-path 与 IR-15 兼容——消费上游实际存在 close 序列）；F10/F11 为消费侧。**唯一允许改动**：EVENT_FLAGS 校验接受 None（F10 NA），其余一行不许动。REPLACE_PROHIBITED |
| `src/itsf/s0/labels.py` | **KEEP** | d_open/Y_cont/Y1-Y5 完整；Y6 设计上留给 dataset 层年度 decile pass（文件头明示）。d_open 对 ret_open30==0 与 NA 均返 0——上游必须分别计数（APPROVED_NA_REASONS 已区分 zero_direction_day_l82 / direction_undeterminable_na）。REPLACE_PROHIBITED |
| `src/itsf/s0/oracle.py` | **KEEP** | 双 Oracle 完整（theoretical 上界＋executable E1/E2 经 paths.build_record）；day 选择在上游。REPLACE_PROHIBITED |
| `src/itsf/s0/costs.py` | **KEEP** | 场景成本/成交价（test_costs.py 覆盖）。REPLACE_PROHIBITED |
| `src/itsf/s0/paths.py` | **KEEP** | ENTRY_TIME/FORCED_EXIT_BAR_TIME/build_record（TradePath 双 mtm 数组）。REPLACE_PROHIBITED |
| `src/itsf/s0/__init__.py` | **main agent 所有** | 包级导出/公共 API 归集成接口，SA 不得动 |
| `src/itsf/s0/context.py` | **新建（SA-4）** | 真实缺口①：逐日上下文装配——obs/pm 切片、ADR14 滚动、IR-20 rvol 参照集、IR-19 prev_close、IR-18 F10 编码、roll session-date 映射、隔夜窗。必须与 preflight 已批语义一致（断言比对兜底） |
| `src/itsf/s0/dataset.py` | **新建（SA-4）** | 真实缺口②：数据集装配——逐日循环出特征/标签表、Y6 年内 decile pass、按年与 LOYO 分组、proxy/actual-micro 时代轴、频率输出、NA 总表（按 APPROVED_NA_REASONS） |
| `src/itsf/s0/runinfra.py` | **新建（SA-5）** | 真实缺口③：hash 链 manifest／Stage-C 日志守卫／NA 守恒检查器／断言比对器／失败报告生成器 |
| `scripts/s0_real_run.py` | **新建（main agent，M5-T3）** | 入口＋Stage A-F 状态机＋13 硬门＋attempts→runs 原子转换＋registry 事件 |
| 既有测试 test_features/labels/oracle/costs | **KEEP** | 只增不改；SA-4 新测试文件独立命名 |

## 环境锁定交付（main agent，最终包重渲染时执行）

requirements/lockfile 确定性版本、Python 与关键包版本采集
（pandas/databento/pandas-market-calendars/tzdata）、OS 与时区、calendar
版本、runner 关键源码 SHA-256——七件套按包 §0 锁入最终版。

## 零交集确认

SA-4 允许集 = {context.py, dataset.py, features.py 的 F10-NA 单点,
tests/test_s0_context.py, tests/test_s0_dataset.py}；
SA-5 允许集 = {runinfra.py, tests/test_runinfra.py}；交集 = ∅。
contracts / __init__ / scripts / registry / 授权包全归 main agent。
