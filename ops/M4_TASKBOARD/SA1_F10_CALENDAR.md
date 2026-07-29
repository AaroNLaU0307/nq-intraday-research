DISPATCH: 建议模型 = Claude Opus 5（claude-opus-5），effort = high。
理由：12 年跨度的官方档案浏览与交叉互证，判断"是否官方/是否冲突"的
质量直接决定证据链成色；抽取本身由确定性脚本兜底，无需 Fable 级成本。
需要带浏览器权限的会话。可与 SA-2 并行。

SUBAGENT TASK ID: M4-T1 / SA-1
TASK NAME: F10 官方事件日历证据采集与事件表（2010-06-06 → 2021-12-31）
ROLE: 证据采集与结构化提取工程师（evidence-first，falsification 项目纪律）
OBJECTIVE: 仅用 BLS 与 Federal Reserve 官方来源，构建 CPI 发布日、
NFP/Employment Situation 发布日、FOMC 公告日的机器可读事件表，并按本项目
证据标准归档全部原始材料。不做任何策略计算。

项目背景（你没有本会话之外的上下文，以下即全部所需背景）：
- 仓库：C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\
- 这是一个冻结预注册的量化研究项目。F10 特征冻结定义（STUDY_0_PREREGISTRATION.md
  行 62）：`is_event_day ∈ {CPI, NFP, FOMC, none}（BLS/Fed 官方时刻表快照）`。
- 你的产出只提供"官方事件日期事实"，不决定任何编码/映射规则。

REQUIRED READING（开工前必读）:
- STUDY_0_PREREGISTRATION.md 行 41-45（时区约定）与行 62（F10 冻结定义）
- PROJECT_CHARTER.md 证据等级 L1-L5 一节
- gate1/G9_EVIDENCE_RESOLUTION.md（本项目官方证据归档范式的样板）
- ops/M4_TASKBOARD/TASKBOARD.md 中 SA-1 相关行

ALLOWED FILES（只允许创建/修改这些）:
- gate1/f10_event_calendar/raw/**（原始 HTML/PDF/XLS/CSV/浏览器渲染件）
- gate1/f10_event_calendar/F10_SOURCE_LOG.md
- gate1/f10_event_calendar/f10_events.csv
- gate1/f10_event_calendar/f10_extraction.py
- gate1/f10_event_calendar/f10_evidence_registry_fragment.yaml
- tests/test_f10_calendar.py
- （如需）gate1/f10_event_calendar/DECISION_PACKET_F10_*.md

FORBIDDEN FILES:
- src/itsf/** 全部；scripts/** 现有文件；所有冻结文件（PROJECT_CHARTER.md、
  STUDY_0_PREREGISTRATION.md、purchase_plan.yaml、MC_METHOD_SPEC.md、
  gate1/platform_params.yaml）；gate1/evidence_registry.yaml（只写 fragment，
  合并归 main agent）；FREEZE_LOG.md；DATA_QA_REPORT.md；DATA_QA_ADDENDUM.md；
  qa_addendum_*.json；spread_cost_table.csv；ops/** 其余文件；git tag/历史。

INPUTS:
- 允许域名白名单（硬性）：*.bls.gov、*.federalreserve.gov。任何其他域名的
  数据一律不得进入事件表（包括第三方经济日历、经纪商日历、新闻、博客、
  搜索摘要、你自己的记忆）。
- 候选官方入口（仅为起点，须自行核实官方性并记录 final URL）：
  - BLS 历史发布日程档案（news release schedule archives）
  - BLS CPI 与 Employment Situation 各自的 release calendar/archive 页
  - federalreserve.gov FOMC calendars 页（2015 至今）及历年 FOMC
    historical materials / meeting archive 页（覆盖 2010-2014）

OUTPUTS:
1. f10_events.csv，字段严格为：
   date_et, event_type, source_id, source_sha256, official_release_time_et,
   is_fomc_statement_day, is_cpi_release_day, is_nfp_release_day
   - event_type ∈ {CPI, NFP, FOMC}
   - 同日多事件：每事件独立一行，不合并、不定优先级（编码归 D1 决策）
   - FOMC 行：会议日与 statement 发布日如不一致，两类日期都记录，
     is_fomc_statement_day 只在 statement 发布日为 true；采用哪个进入 F10
     是 D2 决策，你不得自行选择，只负责把两类日期都如实提供
   - 覆盖 2010-06-06 → 2021-12-31（含端点内所有事件）
2. F10_SOURCE_LOG.md，逐来源记录：原始 URL、final URL（重定向后）、抓取
   时间（UTC）、页面标题、覆盖年份、原始文件名与 SHA-256、提取文本/表的
   SHA-256、来源等级（应为 Level 1 官方）、缺失年份与异常记录。
3. raw/ 下归档全部原始件（HTML 存渲染后完整文件；PDF/XLS/CSV 存原件）。
4. f10_extraction.py：从 raw/ 原始件到 f10_events.csv 的确定性提取脚本
   （重跑必须产生字节相同的 csv；不联网）。
5. f10_evidence_registry_fragment.yaml：按 gate1/evidence_registry.yaml
   现有条目格式写 fragment（id、url、fetched_at、raw_sha256、tier），
   不直接改主 registry。
6. tests/test_f10_calendar.py：schema 校验；确定性（重跑 extraction 对比
   sha256）；逐年计数断言（CPI 每年 12、NFP 每年 12、FOMC statement 每年
   8 为基线，任何偏差在 F10_SOURCE_LOG.md 显式列出并给官方出处）；测试
   不联网。

INTERFACES:
- csv 的 schema 是冻结接口，不得增删改字段名；下游（S0_INPUT_PREFLIGHT
  与 F10 编码落地）由 main agent 负责。

IMPLEMENTATION REQUIREMENTS:
- 日期一律转 America/New_York 语义下的日历日；BLS 发布时间通常为 08:30 ET、
  FOMC statement 通常为 14:00/14:15 ET（2010-2012 存在 12:30 等历史差异）——
  以官方页面记载为准填 official_release_time_et，不得凭记忆填写。
- 逐年交叉核对：用 BLS 年度 schedule 页与各指标 archive 页互证；FOMC 用
  日历页与逐次会议档案互证。互相矛盾 = 触发 STOP。
- 政府停摆/延期发布（已知例：2013 年 10 月停摆导致 9 月 NFP/CPI 延期）：
  照实记录官方实际发布日期，并在 F10_SOURCE_LOG.md 异常一节单列；如何
  编码归 D3 决策，你不得自行决定。
- 不得计算任何策略结果、不得把事件表与任何价格/收益数据做关联分析。

REQUIRED TESTS: 见 OUTPUTS 第 6 条。

EVIDENCE REQUIREMENTS: 全部原始件落盘＋SHA-256；来源等级标注；抓取时间；
final URL；缺失与异常显式列表。达不到 Level 1 官方标准的年份不得静默用
低级来源顶替——触发 STOP 并写 DECISION_PACKET（对应 D4）。

STOP CONDITIONS（满足任一立即停止，写明现状后上交）:
- 遇到方法歧义（含 D1-D4 任何一项需要选择时）；
- 需要修改共享接口或 csv schema；
- 需要改变冻结规则；
- 官方证据相互冲突（如 BLS schedule 页与 archive 页日期不一致）；
- 超出 ALLOWED FILES 的文件所有权；
- 发现可能影响 Primary 的未批准选择；
- 官方来源某年份缺失或不可达。
遇到需要决策的情况，生成简洁 DECISION_PACKET（问题/冻结章节/事实/
Option A/Option B/对样本与 Primary 的影响方向/是否阻塞/涉及文件/需 Aaron
批准的明确问题），放入 gate1/f10_event_calendar/，然后停止。

禁止：
- 创建其他 subagent；
- 修改冻结文件、tag 或历史；
- 创建最终 commit（可做工作区变更，最终 commit 由 main agent 完成；
  如会话要求 commit，只 commit 自己 ALLOWED FILES 内的文件并在返回中注明）；
- 运行真实 S0 或任何策略计算；
- 输出策略数字。

RETURN FORMAT（返回时逐项填写）:
- files_read:
- files_modified:
- tests_run:
- test_results:
- evidence_added:（来源数、原始件数、总事件行数、逐年计数表）
- unresolved:
- decisions_required:（含已写 DECISION_PACKET 路径）
- frozen_files_untouched: true/false
- real_s0_not_run: true/false
