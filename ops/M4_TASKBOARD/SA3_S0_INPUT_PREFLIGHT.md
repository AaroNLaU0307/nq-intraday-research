SUBAGENT TASK ID: M4-T4 / SA-3
TASK NAME: S0_INPUT_PREFLIGHT — 无策略数字的输入资格终检
ROLE: 结构性 QA 工程师（最后一道 pre-S0 输入闸口）
OBJECTIVE: 在不运行 Oracle/收益/EV/MC/判决的前提下，逐日验证 S0 全部输入
（日期资格、精确锚点、F1-F11 可构建性、标签锚点可用性），产出
S0_INPUT_PREFLIGHT_REPORT.md 与 S0_INPUT_PREFLIGHT.json。

启动前置（缺一即 STOP，不得开工）：
- main agent 已集成 M4-T2（src/itsf/data/roles.py 存在且
  DEV_END_EXCLUSIVE == 2022-01-01）——用代码断言确认；
- gate1/f10_event_calendar/f10_events.csv 存在且 D1-D4 已批复
  （若 F10 编码决议尚未回流，F10 段只报 csv 原始覆盖计数并标注
  ENCODING_PENDING，不得自行编码映射）。

项目背景（自包含）：
- 仓库：C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\
- 冻结要点（STUDY_0_PREREGISTRATION.md）：
  - 行 41-43：ET 时区；RTH 09:30-16:00；观察窗 09:30-09:59 bar；决策 10:00；
    入场 = 10:00 bar 开盘；强制退出 = 15:44 bar 收盘；隔夜区间前日 18:00→
    当日 09:30；日历 pandas-market-calendars CME Equity。
  - 行 44 剔除日仅三类：半日市；RTH 无成交；RTH bar 缺失 >10%。
  - 行 45 NA 政策：除剔除日外不得整日删除；特征算不出记 NA，该日仍进
    Oracle 总体统计；每表强制报 NA 数。
  - 行 49：ADR14 = 前 14 个完整 RTH 交易日 (RTH high−RTH low) 均值（不含当日）。
  - 行 53-63：F1-F11 定义（F4 需前 60 交易日同窗中位数；F5 在
    is_roll_transition 日记 NA；F10 事件日历；F11 roll 标志）。
  - 行 86-91：标签表（Y_cont 需 O1000 与 C1544；Y1 同；Y2/Y3/Y4/Y5 见表）。
- DATA_QA_ADDENDUM.md 已给出窗口完整性基线（0930-1000 完整 2960；
  1000-1544 完整 2873；20 个不完整日全分类）——你的逐日结果必须与之交叉
  核对，不一致即 STOP。

REQUIRED READING:
- STUDY_0_PREREGISTRATION.md 行 24-32、41-63、75-96、86-91
- DATA_QA_REPORT.md、DATA_QA_ADDENDUM.md 全文
- src/itsf/data/dbn_loader.py、src/itsf/data/roles.py、
  src/itsf/data/validation.py（只读，理解接口与 QA 事件范式）
- gate1/f10_event_calendar/f10_events.csv 与其 SOURCE_LOG
- ops/M4_TASKBOARD/TASKBOARD.md 中 SA-3 相关行与 D6/D7 决策点描述

ALLOWED FILES:
- scripts/s0_input_preflight.py（新建）
- tests/test_preflight.py（新建）
- S0_INPUT_PREFLIGHT_REPORT.md、S0_INPUT_PREFLIGHT.json（仓库根）
- （如需）DECISION_PACKET_PREFLIGHT_*.md（仓库根）

FORBIDDEN FILES:
- src/itsf/** 全部（只 import，不修改）；所有冻结文件；guards；loaders；
  scripts/** 现有文件；DATA_QA_*；qa_addendum_*；spread_cost_table.csv；
  gate1/**（f10 csv 只读）；ops/**；FREEZE_LOG.md；git tag/历史。

INPUTS: DevelopmentSignalLoader（唯一数据入口，A1 job 目录
C:\Users\Aaron\quant-data\databento-archive\intraday-trend\development_signal\
GLBX-20260727-DL3BEBCHJA）；f10_events.csv；pandas-market-calendars CME_Equity。
OUTPUTS: 报告＋json；两者状态行固定：
INPUT_PREFLIGHT_ONLY / REAL_S0_NOT_RUN / AWAITING_AARON_APPROVAL

IMPLEMENTATION REQUIREMENTS:

A. 日期资格漏斗（逐级计数，json 中逐级列日期集合大小与差集去向）：
   scheduled trading days → observed RTH days → 完整 RTH days →
   减 early-close 剔除 → 减 zero-bar 剔除 → 减 >10% missing 剔除 →
   减 ADR14 warm-up（前 14 个完整 RTH 日不足）→ 最终进入特征构建的日期数。
   剔除日只允许冻结的三类＋warm-up；任何日期不得因其他理由消失。

B. 精确锚点逐日检查（对资格漏斗过线的每一日）：
   O09:30（09:30 bar open）、C09:59（09:59 bar close）、O10:00（10:00 bar
   open）、C15:44（15:44 bar close）、previous RTH close（前一 RTH 交易日
   15:59 bar close；若前日 15:59 bar 缺失，这属于锚点缺失，记录之，如何
   降级是 D7 类决策，不得自行选择替代 bar）。
   每锚点分别报告：available count / missing count / affected dates /
   missing 原因（对照 DATA_QA_ADDENDUM 的分类）/ downstream 是字段 NA 还是
   整日排除（只依据冻结行 44-45 判定；判定不唯一时写 DECISION_PACKET）。
   硬禁止：前值填充、下一根 bar 替代、插值、最近成交替代、任何隐式补齐。

C. 非关键缺失分钟（≤10% 缺失的正常完整交易日）：
   - 不得整日删除；
   - 路径类特征（F3/F8 及行 96 path_pm 公式）在缺分钟时用"实际存在 bar
     差分"还是"完整分钟网格"——冻结行 96 未唯一确定，这是 D6：若 main
     agent 尚未给你批复结论，此段只输出受影响日期数与两种口径下的 NA/
     可算计数对比表（不选择、不实现任何一种作为默认），并写
     DECISION_PACKET_PREFLIGHT_D6.md 后继续其余部分；
   - 所有 NA 显式计数。

D. F1-F11 输入完整性（只查可构建性与 NA，不算特征值与任何 Alpha 关系）：
   每特征：非 NA 可构建日数 / NA 日数 / NA 原因分类（锚点缺失、ADR14
   warm-up、F4 前 60 日 warm-up、F5 roll 日记 NA、F10 日历缺口、其他）。
   F10：报告日历覆盖（各 event_type 的日期数、与交易日的交集数、
   development 窗内无匹配事件的年份）；不得报告事件与任何收益的关系。
   F11：47 次 transition 与 is_roll_window（前后各 2 RTH 日）覆盖计数；
   与 DATA_QA_ADDENDUM §8 的 47 次交叉核对。
   报告任何未识别类别与意外全常量字段。

E. 标签输入（只查锚点存在性）：
   Y_cont / Y1（O1000, C1544）；Y2/Y3/Y4/Y5 按行 86-91 所需锚点逐一列出
   所需输入与逐日可用计数。不得计算标签值、分布、均值、命中率或任何
   未来收益统计。

F. 输出与守卫：
   - json 顶层必须含 status 三行、生成时间、代码版本（git rev-parse HEAD
     由 main agent 集成时填，你留占位）、全部计数结构；
   - 报告与 json 禁用词守卫测试：不得出现 return/收益/pnl/ev/sharpe/
     hit/win_rate/edge/alpha_decay 等策略词（tests 中固化该断言）；
   - 与 DATA_QA_ADDENDUM 交叉核对表（scheduled 2989 / observed 2969 /
     完整窗口计数等）必须逐项一致，任何不一致 = STOP 上交，不得"就近取信"。

REQUIRED TESTS（tests/test_preflight.py，合成 fixture，不读真实数据）:
- 锚点存在性判定正确（含前日收盘锚点跨日逻辑）；
- 资格漏斗每级计数正确且总量守恒（无日期无声消失）；
- 三类剔除＋>10% 规则正确；
- NA 计数与原因分类正确；
- 禁用词守卫；
- 状态三行存在。

EVIDENCE REQUIREMENTS: 报告附漏斗表、每锚点计数表、交叉核对表；json 与
报告数字必须同源（同一次运行生成）。

STOP CONDITIONS:
- 启动前置不满足；与 DATA_QA_ADDENDUM 交叉核对不一致；
- 冻结规范不能唯一确定的任何口径（D6/D7 及新发现）；
- 需要修改共享接口；官方证据冲突；超出文件所有权；
- 发现可能影响 Primary、样本资格、成本、标签或判决的未批准选择。
一律写简洁 DECISION_PACKET（问题/冻结章节/事实/Option A/Option B/影响
方向/推荐留空给 main agent/是否阻塞/涉及文件/需 Aaron 批准的问题）后停止。

禁止：
- 运行 Oracle、策略收益、成本后收益、EV、MC、GO/STOP、Checkpoint 0；
- 创建其他 subagent；修改冻结文件；创建最终 commit；输出策略数字；
- 触碰 execution_cost_calibration 或任何 IV 路径。

RETURN FORMAT:
- files_read:
- files_modified:
- tests_run:
- test_results:
- evidence_added:（漏斗最终日数、各锚点 missing 数、NA 总表）
- unresolved:
- decisions_required:
- frozen_files_untouched: true/false
- real_s0_not_run: true/false
