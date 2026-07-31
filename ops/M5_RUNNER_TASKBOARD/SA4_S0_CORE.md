DISPATCH: 建议模型 = Claude Opus 5（claude-opus-5），effort = high。
理由：冻结公式→代码的忠实翻译＋"歧义必须 STOP 而非硬解"的判断密度
是本里程碑最高的。不需要浏览器。可与 SA-5 并行。

SUBAGENT TASK ID: M5-T1 / SA-4
TASK NAME: S0 核心计算库（特征/标签/Oracle/引擎，纯函数，合成测试）
ROLE: 冻结预注册量化研究项目的核心计算工程师
OBJECTIVE: 把 STUDY_0_PREREGISTRATION.md（tag s0-freeze-v1）的 F1-F11、
Y 标签族、双 Oracle 与 E1/E2 引擎实现为纯函数库。frame 进 frame 出，
零文件 I/O，零真实数据访问，全部合成 fixture 测试。

项目背景（自包含）：
- 仓库：C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\
- 这是冻结预注册研究；你的实现是"翻译"不是"设计"——任何冻结文本不能
  唯一推出的口径都是 STOP 条件，不是你的判断题。
- 真实 S0 运行由 main agent 的 runner 入口另行完成；你只交纯函数库。

REQUIRED READING（先读完再动手）:
- STUDY_0_PREREGISTRATION.md 行 41-45、49-63、75-96、86-91、130-145、236
- IMPLEMENTATION_RESOLUTIONS.md 全部（IR-1..20；直接约束你的：IR-2/11
  描述性口径、IR-7 场景 slip、IR-12/13/14/17/18 F10、IR-15 路径、
  IR-19 前收盘、IR-20 F4）
- S0_REAL_RUN_AUTHORIZATION_PACKET.md §5、§7
- src/itsf/s0/contracts.py（main agent 定稿的共享接口——照用，不得改）
- scripts/s0_input_preflight.py（只读参考：资格漏斗与锚点/NA 语义的
  已批实现，你的特征层必须与其口径一致）
- ops/M5_RUNNER_TASKBOARD/TASKBOARD.md

ALLOWED FILES（全部新建）:
- src/itsf/s0/__init__.py、features.py、labels.py、oracle.py、engines.py
- tests/test_s0_features.py、test_s0_labels.py、test_s0_oracle.py、
  test_s0_engines.py
- （如需）DECISION_PACKET_S0CORE_*.md（仓库根）

FORBIDDEN FILES: 冻结文件五件套；FREEZE_LOG.md；src/itsf/data/**；
src/itsf/guards.py；src/itsf/mc/**；scripts/**；ops/**；registry；
授权包；SA-5 的 runinfra.py 与其测试；git tag/历史。

INPUTS: contracts.py 定义的 DayFrame/RunConfig 类型（main agent 提供）。
OUTPUTS: 上述模块＋测试全绿。

IMPLEMENTATION REQUIREMENTS:
1. **纯函数**：所有公开函数 frame/数组进、frame/数组出；无文件读写、
   无网络、无全局可变状态、无 print；随机性只经显式传入的 seed
   （bootstrap 用，默认不落任何随机路径）。
2. F1-F11 逐条按冻结定义＋已批 IR 口径；F10 输入为已编码类别列
   （编码本身在 main agent 的 runner 层完成），你实现消费侧；
   F5 消费 IR-19 语义的 prev_close 列；路径类按 IR-15 实际 close 序列
   差分。
3. 标签：Y_cont/Y1（O1000、C1544）、Y2-Y5 按行 86-91 与 IR-11；
   L82 零方向日（ret_open30==0）单列 NA 处理与计数。
4. 双 Oracle：theoretical 与 executable 按行 130-145；方向恒 = d_open；
   延续判据 Y_cont ≥ θ（主 0.5 副 0.3 都算，禁止事后升格）。
5. E1（OR 对侧止损，未触发 15:45 退出）与 E2（无止损 15:45 定时退出）；
   强制输出最差日 P1/P5 所需的原始序列；成本挂钩 $1.74＋spread 场景
   （场景表作为参数传入，不得内嵌数字）。
6. **无前视**：任何特征在日 d 只可用 ≤ d 的数据；写机器化断言测试
   （扰动 d+1 数据不得改变 d 的任何特征/标签中间量——标签本身按定义
   使用当日盘中未来，属预注册设计，不在此断言范围，测试里注明）。
7. NA 原因分类必须与 Preflight 的原因枚举一致（枚举在 contracts.py）。
8. 每个模块配合成 golden 测试：手算可验的小 fixture（例如 5-10 根 bar
   构造的迷你日），断言到具体数值。

REQUIRED TESTS: 见上 6/8；另加：θ 主副判据分开输出且无"事后升格"路径；
E2 恒定退出时刻；E1 止损优先级 bar 内约定与冻结文本一致（不一致即
STOP，见 D-E1FILL）；全部函数 inspect 断言无任何可覆盖冻结常数的参数。

EVIDENCE REQUIREMENTS: 每个公式实现处注释冻结出处（文件＋行号＋IR 号）；
返回中列公式→出处对照表。

STOP CONDITIONS（任一触发即停，写 DECISION_PACKET_S0CORE_<主题>.md，
推荐栏留空给 main agent）:
- 冻结文本不能唯一推出的任何口径（预计候选：executable Oracle 成交
  假设细节、bootstrap 规格、E1 bar 内 gap-through 成交价、Y2/Y3 读法）；
- 需要修改 contracts.py 或任何共享接口；
- 需要改变冻结规则；与 Preflight 已批口径冲突；
- 超出文件所有权；发现可能影响 Primary 的未批准选择。

禁止：创建其他 subagent；git commit（工作树变更留给 main agent 审查
集成）；读取 C:\Users\Aaron\quant-data 任何真实文件；运行真实 S0；
输出任何策略数字（合成 fixture 的 golden 数值不算——它们是手算测试值，
必须在测试注释中标明构造过程）。

RETURN FORMAT:
- files_read: / files_modified: / tests_run: / test_results:（pytest
  末行原文）/ formula_source_map:（公式→冻结出处对照）/ unresolved: /
  decisions_required: / frozen_files_untouched: / real_s0_not_run:
