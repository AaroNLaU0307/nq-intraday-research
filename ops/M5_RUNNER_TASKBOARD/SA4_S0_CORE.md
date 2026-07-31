DISPATCH: 建议模型 = Claude Opus 5（claude-opus-5），effort = high。
理由：冻结公式→代码的忠实衔接＋"歧义必须 STOP"的判断密度最高。
不需要浏览器。可与 SA-5 并行。
（v2，2026-07-31：按 M5-T0 审计重写——五个既有核心模块 KEEP/
REPLACE_PROHIBITED，本任务是**补缺**不是实现。）

SUBAGENT TASK ID: M5-T1 / SA-4
TASK NAME: S0 计算缺口补齐（context.py＋dataset.py；既有五模块只读消费）
ROLE: 冻结预注册量化研究项目的核心计算工程师
OBJECTIVE: 在**不重写任何既有实现**的前提下，补齐 S0 计算链的两个真实
缺口：(1) `src/itsf/s0/context.py` 逐日上下文装配；(2)
`src/itsf/s0/dataset.py` 数据集装配。全部纯函数、零文件 I/O、零真实
数据访问、合成 fixture 测试。

项目背景（自包含）：
- 仓库：C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\
- **既有实现（M1 骨架，均有专属测试，一行不许重写）**：
  `src/itsf/s0/features.py`（F1-F9 计算＋F10/F11 消费）、`labels.py`
  （d_open/Y_cont/Y1-Y5；Y6 留给 dataset 层）、`oracle.py`（双 Oracle）、
  `costs.py`、`paths.py`（E1/E2 build_record）。你的模块**调用**它们。
- 共享契约：`src/itsf/contracts.py`（包顶层，MAIN-AGENT OWNED，含
  RunConfig/RunStage/APPROVED_NA_REASONS/错误类型与 DayFeatures 等）——
  照用，不得改；改动需求写进 unresolved。

REQUIRED READING:
- ops/M5_RUNNER_TASKBOARD/M5_T0_INTERFACE_AUDIT.md（模块状态表——你的
  边界的权威定义）
- src/itsf/contracts.py 全文；src/itsf/s0/ 五个既有模块全文＋其测试
- STUDY_0_PREREGISTRATION.md 行 41-45、49-63、75-96、86-91、130-145、236
- IMPLEMENTATION_RESOLUTIONS.md（IR-15/16/17/18/19/20 直接约束你）
- scripts/s0_input_preflight.py（已批语义参考：漏斗/锚点/NA/roll
  session-date；你的 context.py 必须与其口径一致——runner 层会用
  expected_preflight_assertions 比对兜底）
- S0_REAL_RUN_AUTHORIZATION_PACKET.md §5/§7

ALLOWED FILES:
- src/itsf/s0/context.py（新建）
- src/itsf/s0/dataset.py（新建）
- src/itsf/s0/features.py —— **仅限一个单点**：EVENT_FLAGS 校验接受
  None（IR-12/18 的 F10=NA，contracts 已放开类型），其余任何行禁改
- tests/test_s0_context.py、tests/test_s0_dataset.py（新建）
- （如需）DECISION_PACKET_S0CORE_*.md（仓库根）

FORBIDDEN FILES: labels.py/oracle.py/costs.py/paths.py（READ-ONLY）、
src/itsf/s0/__init__.py、src/itsf/contracts.py、既有测试文件、冻结文件
五件套、FREEZE_LOG.md、src/itsf/data/**、guards.py、src/itsf/mc/**、
scripts/**、ops/**、registry、授权包、SA-5 文件、git tag/历史。

IMPLEMENTATION REQUIREMENTS:

A. context.py —— 逐日上下文装配（输出即 features/labels 的入参）：
   - obs/pm 窗口切片（bar-start 约定，obs=09:30..09:59，pm=[10:00,15:45)）；
   - ADR14 滚动（前 14 个完整 RTH 日，不含当日，跳过不完整日）；
   - F4 参照集按 **IR-20**（前 60 个实际 RTH 交易日且早盘 30 根完整，
     含半日市，不要求下游资格）；
   - prev_rth_close 按 **IR-19**（前一实际 CME session；半日市取最后
     排期 RTH bar close＋sidecar 标记；vendor-degraded 不跳过→NA；
     禁一切替代/填充）；
   - F10 编码按 **IR-13/18**（92 预定 statement 日；IR-13 后判冲突，
     9 天→None=NA；multi-hot 只进 diagnostic sidecar 结构）；
   - roll session-date 按官方 mapping 区间 d0 起第一个有效 RTH 交易日
     （与 preflight §F11 断言语义一致）；is_roll_window 前后各 2 RTH 日；
   - 隔夜窗（前实际 session 18:00 → 当日 09:30）；
   - 剔除日三类＋漏斗顺序与 preflight 一致；
   - 每个 NA 必须携带 APPROVED_NA_REASONS 中的原因。

B. dataset.py —— 数据集装配：
   - 逐日调用 context→features/labels，产出特征表＋标签表；
   - Y6：Development 分年内 Y_cont decile pass（labels.py 文件头明示
     该职责在此层）；
   - 按年与 leave-one-year-out 分组结构；proxy/actual-micro 两时代轴
     （2019-05-06 边界）；频率输出结构（行 236）；
   - NA 总表（按 APPROVED_NA_REASONS 逐项计数，zero_direction_day_l82
     与 direction_undeterminable_na 分开）；
   - 只出结构与表，不做任何汇总统计判断。

C. 纯函数纪律：零 I/O、零网络、零全局态、零 print；随机性只经显式
   seed 参数；inspect 断言无可覆盖冻结常数的参数。
D. 无前视：日 d 的 context/特征只用 ≤ d 数据；机器化扰动断言
   （改 d+1 数据不得影响 d 的特征；标签按设计用当日盘中未来，注明
   排除在断言外）。
E. 合成 golden 测试：手算可验迷你 fixture 断言到具体数值（构造过程
   写在测试注释）。

STOP CONDITIONS（写 DECISION_PACKET_S0CORE_<主题>.md，推荐栏留空）:
- 冻结文本不能唯一推出的口径（预登记候选 D-EXEC/D-BOOT/D-E1FILL/
  D-Y23 之外的新发现同样 STOP）；
- 需要改 contracts.py、__init__.py 或任何 FORBIDDEN 文件；
- 与 preflight 已批语义冲突；与既有五模块的接口假设冲突；
- 超出文件所有权；可能影响 Primary 的未批准选择。

禁止：创建其他 subagent；git commit；读取 C:\Users\Aaron\quant-data
任何真实文件；运行真实 S0；输出策略数字（合成 golden 值除外，须注明
构造）。

RETURN FORMAT:
- files_read: / files_modified: / tests_run: / test_results:（pytest
  末行原文）/ formula_source_map:（新实现→冻结出处对照）/
  existing_modules_untouched:（labels/oracle/costs/paths/__init__/
  contracts 逐一确认）/ unresolved: / decisions_required: /
  frozen_files_untouched: / real_s0_not_run:
