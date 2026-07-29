# M4 任务板 — S0 输入封口（Pre-S0 Input Closure）

状态：PENDING_AARON（任务板与提示词已备好，无任何 subagent 已启动）
基线：commit `ac2979f`，工作树干净，174 tests 全绿，双运行门机械开启，
真实 S0 行政锁定。派工模式：手动受控（Aaron 亲自启动每个 subagent）。
配置：ultracode_auto_orchestration_enabled: false / automatic_workflow_creation:
false / recursive_subagent_delegation: false。

## 里程碑目标

在不产生任何策略数字的前提下，关闭真实 S0 前的最后四项输入治理工作：
(1) F10 官方事件日历；(2) Development 数据硬边界；(3) symbology mapping
治理缺口；(4) S0_INPUT_PREFLIGHT。四项全部关闭并经 Aaron 明确批准后，
才进入"是否运行真实 S0"的审批。

## 已核实的当前事实（main agent 本轮亲自检查）

- 预注册 §1（行 24-26）冻结边界：Development `2010-06-06 → 2022-01-01(excl)`；
  IV `2022-01-01 → 2025-07-01(excl)` 不采购不上机；purchase_plan A1
  `end: "2022-01-01"`。
- **确认 bug**：`src/itsf/data/dbn_loader.py:29` 写 `DEV_END_EXCLUSIVE =
  "2025-07-01"`，注释错误地援引 purchase_plan A1（milestone-3 由 main agent
  引入）。错误边界另出现于 `scripts/render_qa_addendum.py:384`（进入了已
  批准 Addendum 的阈值一节）与 `tests/test_loader.py:263`（测的是错边界）。
- F10 冻结定义（预注册行 62）：`is_event_day ∈ {CPI, NFP, FOMC, none}
  （BLS/Fed 官方时刻表快照）`——单一类别；多事件同日无冻结解。
- F11/roll 冻结定义（行 30-32）：is_roll_transition = continuous 映射实际
  切换的交易日；is_roll_window = 前后各 2 个 RTH 交易日；**"symbology 映射
  随数据归档"**——但 A1 batch package 实际缺 symbology 文件（治理缺口成立）。
- 剔除日冻结规则（行 44）仅三类：半日市；RTH 无成交；RTH bar 缺失 >10%。
  NA 政策（行 45）：除剔除日外不得整日删除；特征算不出记 NA，该日仍进
  Oracle 总体统计；每表强制报 NA 数。
- 路径公式（行 96）`path_pm = |C1000−O1000| + Σ[t=10:01..15:44] |C_t−C_(t−1)|`
  ——缺分钟时"实际 bar 差分"还是"完整网格"冻结文本未唯一确定 → 决策点 D6。
- **意外发现**：commodity-carry 归档含 5,031 个逐日 `*.definition.dbn.zst`
  （2010-06-06 起）。若 universe 覆盖 NQ，symbology Option A 可能零成本、
  零联网闭合（M4-T3 调查第一步）。
- A1 层面 47 次 instrument_id transition 全部发生在 00:00 UTC，无同一
  RTH session 内切换（DATA_QA_ADDENDUM §8）。

## 任务清单

| Task ID | 名称 | 执行者 | 状态 |
|---|---|---|---|
| M4-T0 | 基线核查（仓库/冻结/QA 报告比对） | main agent | 完成（本轮） |
| M4-T1 | F10 官方事件日历证据采集与事件表 | **SA-1**（建议 subagent） | 待 Aaron 启动 |
| M4-T2 | Development 硬边界修复＋角色强类型化 | **SA-2**（建议 subagent） | 待 Aaron 启动 |
| M4-T3 | symbology 调查＋SYMBOLOGY_DECISION_PACKET | main agent（保留） | 待 Aaron 指令 |
| M4-T4 | S0_INPUT_PREFLIGHT 构建与运行 | **SA-3**（建议 subagent） | 阻塞（见依赖） |
| M4-T5 | 集成、全量验证、Addendum 勘误、里程碑 commit | main agent（保留） | 阻塞 |

建议 subagent 数量：**3**（SA-1 / SA-2 / SA-3，串并结合），另可在 M4-T5
后建议 1 个独立只读审计 subagent（同样等 Aaron 手动启动）。

## 依赖与并行关系

```
Phase 1（可并行）：SA-1 ∥ SA-2 ∥ M4-T3(main)
    SA-1 与 SA-2 文件所有权完全不相交，可同时跑；
    M4-T3 为 main agent 本机只读调查＋写决策包，与两者无文件冲突。
Phase 2（串行闸口）：
    main agent 审查并集成 SA-2 → 全量测试 →（此后 SA-3 才允许启动）
    D1-D4（F10 编码等）经 Aaron+ChatGPT 批复 → SA-3 的 F10 覆盖段才能定稿
    D5（symbology A/B）批复 → SA-3 报告的披露文本定稿
Phase 3：SA-3 运行 preflight → main agent 审查、集成、勘误 Addendum、
    seal_check/structure/frozen-hash 全套 → 里程碑 commit →
    （可选）只读审计 subagent → 申请 Aaron 批准真实 S0。
```

不可并行：SA-3 不得与 SA-2 并行（消费其接口）；M4-T5 必须最后。

## 文件所有权

| 任务 | 允许创建/修改 | 明确禁止 |
|---|---|---|
| SA-1 | `gate1/f10_event_calendar/**`（新目录：raw/、F10_SOURCE_LOG.md、f10_events.csv、f10_extraction.py、f10_evidence_registry_fragment.yaml）；`tests/test_f10_calendar.py` | `src/itsf/**`、`scripts/**` 现有文件、所有冻结文件、`gate1/evidence_registry.yaml`（只出 fragment，由 main agent 合并）、DATA_QA_*、FREEZE_LOG.md |
| SA-2 | `src/itsf/data/roles.py`（新）、`src/itsf/data/dbn_loader.py`、`src/itsf/data/cost_calibration_loader.py`（仅接入 DataRole 枚举的最小改动）、`tests/test_dev_boundary.py`（新）、`tests/test_loader.py`（仅修正 :263 错误边界用例＋追加） | 所有冻结文件、`src/itsf/guards.py`、`src/itsf/mc/**`、`scripts/**`（含 render_qa_addendum.py:384 的勘误——归 main agent 的 Addendum 勘误流程）、DATA_QA_*、qa_addendum_*.json |
| M4-T3 (main) | `SYMBOLOGY_DECISION_PACKET.md`（新，仓库根） | 冻结文件；不重新下载/联网补取付费数据 |
| SA-3 | `scripts/s0_input_preflight.py`（新）、`tests/test_preflight.py`（新）、`S0_INPUT_PREFLIGHT_REPORT.md`、`S0_INPUT_PREFLIGHT.json` | `src/itsf/**` 全部（只 import 不修改）、所有冻结文件、loaders、guards、DATA_QA_*、gate1/** |
| M4-T5 (main) | 共享接口终审、`DATA_QA_ADDENDUM.md` 勘误段（新 commit 追加，不改历史）、`gate1/evidence_registry.yaml` 合并、集成 commit | — |

## 必读冻结章节（各任务提示词内已列）

- STUDY_0_PREREGISTRATION.md：§1 数据角色表（行 24-27）与 roll 定义（行 30-32）；
  行 41-45（时区/RTH/锚点/剔除日/NA 政策）；行 49-63（ADR14 与 F1-F11 表）；
  行 75-96（MVE/retrace/路径公式）；行 86-91（标签表）。
- purchase_plan.yaml：A1/A2/A3 的 data_role 与窗口块。
- PROJECT_CHARTER.md：数据角色隔离条款（条款 14）；"所有清洗决定形成 QA 事件"。
- FREEZE_LOG.md：冻结哈希登记模型（何为可加注、何为不可触）。
- DATA_QA_ADDENDUM.md：§8（47 次 roll、00:00 UTC）、A2 §4-5（事件化范式）。

## 输入/输出接口

- SA-1 输出 `f10_events.csv` 字段（冻结 schema，由 main agent 现在定义）：
  `date_et, event_type, source_id, source_sha256, official_release_time_et,
  is_fomc_statement_day, is_cpi_release_day, is_nfp_release_day`
  （event_type ∈ {CPI, NFP, FOMC}；多事件日各出一行，**不做**类别合并——
  合并/优先级属 D1，等批复后由 main agent 定稿映射）。
- SA-2 目标接口（main agent 现在定义，SA-2 照此实现，不得自行改动）：
  ```python
  # src/itsf/data/roles.py
  class DataRole(str, Enum):
      DEVELOPMENT_SIGNAL = "development_signal"
      EXECUTION_COST_CALIBRATION = "execution_cost_calibration"
      INTERNAL_VALIDATION_SIGNAL = "internal_validation_signal"  # 永不可加载

  ROLE_WINDOWS = {  # (start_inclusive, end_exclusive)，冻结引用见文件头注释
      DataRole.DEVELOPMENT_SIGNAL: ("2010-06-06", "2022-01-01"),
      DataRole.EXECUTION_COST_CALIBRATION: ("2025-01-01", "2025-04-01"),
  }  # INTERNAL_VALIDATION_SIGNAL 故意不在表内：任何加载路径一律 RoleError
  ```
  边界为模块级常量，**不可通过构造参数/方法参数放宽**；loader 对外签名不变
  （`load_real(filename, source_format)`）。
- SA-3 输入：`DevelopmentSignalLoader`（集成后版本）、
  `gate1/f10_event_calendar/f10_events.csv`（D1-D4 批复后）、
  DATA_QA_ADDENDUM 的日历/窗口统计作交叉核对基准。
  输出：`S0_INPUT_PREFLIGHT_REPORT.md` + `S0_INPUT_PREFLIGHT.json`，状态行
  固定为 `INPUT_PREFLIGHT_ONLY / REAL_S0_NOT_RUN / AWAITING_AARON_APPROVAL`。

## 必须测试的边界

- SA-2（Aaron 八条全部落为具名测试）：2010-06-06 允许；2021-12-31 允许；
  2022-01-01 拒绝；2025 文件拒绝；hash 正确角色错误拒绝；文件名伪装
  Development 但内部时间戳进 IV 拒绝；跨边界单文件整文件拒绝（不截断）；
  synthetic 入口可测。另加：边界不可参数化（构造器不接受边界覆盖）、
  IV 角色枚举任何路径 RoleError、cost↔development 目录互换拒绝。
- SA-1：抽取脚本确定性（同一 raw 文件重跑得到相同 csv sha256）；schema
  校验；逐年计数断言（CPI/NFP 每自然年 12、FOMC statement 每年 8±，
  偏差必须显式列出并说明）；测试不联网（只读已归档 raw）。
- SA-3：合成 fixture 上的锚点存在性判定；NA 计数正确性；禁用词守卫
  （json 键与报告中不得出现 return/pnl/ev/sharpe/edge/win 等）；剔除日
  三类规则与 >10% 规则的正确实施；F4 前 60 日 warm-up 计数。

## 可能影响研究结果的决策点（全部上交，不得自行决定）

| ID | 问题 | 冻结依据 | 阻塞 |
|---|---|---|---|
| D1 | 同日多事件时 F10 编码（单类别 vs multi-hot 内部保存＋映射） | 预注册行 62 单类别集合 | 阻塞 SA-3 的 F10 段 |
| D2 | FOMC 采用会议日还是 statement 发布日 | 行 62 仅写 "FOMC" | 阻塞 SA-1 表定稿 |
| D3 | 延期发布/政府停摆（如 2013-10）如何编码 | 无冻结解 | 阻塞 SA-1 表定稿 |
| D4 | 官方来源缺失年份的 fail-closed 规则 | 无冻结解 | 视 SA-1 发现 |
| D5 | symbology Option A vs B | 行 30 "映射随数据归档" 未满足 | 阻塞 M4 收口 |
| D6 | ≤10% 缺失日路径特征：实际 bar 差分 vs 完整分钟网格 | 行 96 公式未唯一确定 | 阻塞 SA-3 实现该段 |
| D7 | （条件触发）标签锚点缺失日：标签 NA 后该日在 Oracle 总体统计中的地位 | 行 45 未对"标签 NA"细分 | 视 preflight 发现 |

**需要 Aaron 带回 ChatGPT 讨论：D1、D2、D3、D5、D6**（D4/D7 视触发情况）。
main agent 将在各 DECISION_PACKET 中给出推荐与方向性影响，但不自行批准；
"更保守"不作为自动批准理由。

## main agent 保留职责（不派工）

冻结规范最终解释；F10 多事件编码最终选择（批复后落地）；symbology A/B
最终裁决落地；共享 contracts/schema 修改（roles.py 接口定稿与终审）；
跨模块接口调整；SA 成果审查与 unresolved 裁决；全量测试；seal_check；
structure assertions；frozen hash verification；git diff 审计；
DATA_QA_ADDENDUM 勘误段（追加 commit，不改历史）；evidence_registry 合并；
最终集成 commit；是否申请 Aaron 批准真实 S0。

## 建议启动顺序（等 Aaron 指令）

1. Aaron 启动 SA-1 与 SA-2（可并行），同时指示 main agent 执行 M4-T3；
2. SA-2 返回 → main agent 审查集成 → Aaron 决定是否启动 SA-3；
3. D1-D5 批复回流 → SA-3 定稿运行 → M4-T5 集成与全套校验；
4. （可选）Aaron 启动只读审计 subagent → 审计通过 → 申请真实 S0 批准。
