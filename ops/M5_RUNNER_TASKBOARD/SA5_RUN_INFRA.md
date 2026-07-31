DISPATCH: 建议模型 = Claude Sonnet 5（claude-sonnet-5），effort = high。
理由：规格完全定死的基础设施实现（manifest 链/守卫/比对器），照规格
落地＋测试矩阵兜底。不需要浏览器。可与 SA-4 并行。

SUBAGENT TASK ID: M5-T2 / SA-5
TASK NAME: S0 运行基础设施（hash 链 manifest／Stage-C 日志守卫／NA 守恒
检查器／Preflight 断言比对器／失败报告生成器）
ROLE: 运行治理基础设施工程师
OBJECTIVE: 按 S0_REAL_RUN_AUTHORIZATION_PACKET.md §6/§7/§8 的已批规格，
实现 runner 所需的全部治理机件为可测库函数。零真实数据访问。

项目背景（自包含）：
- 仓库：C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\
- 你实现"机制"；"何时调用"与 trial registry 状态转换归 main agent。

REQUIRED READING:
- S0_REAL_RUN_AUTHORIZATION_PACKET.md 全文（§0 状态机、§6 manifest 链、
  §7 阶段与日志守卫/NA 守恒、§8 失败处理、§9 硬门清单）
- ops/TRIAL_REGISTRY.md（事件链格式）
- src/itsf/contracts.py（包顶层，main agent 定稿接口——照用不改；
  你依赖的：RunStage/TrialState/APPROVED_NA_REASONS/RunConfig/
  RunGateError/NAConservationError/AssertionMismatchError/LogLeakError）
- ops/M5_RUNNER_TASKBOARD/M5_T0_INTERFACE_AUDIT.md（所有权边界权威）
- S0_INPUT_PREFLIGHT.json（断言目标的真实形状，只读）
- ops/M5_RUNNER_TASKBOARD/TASKBOARD.md

ALLOWED FILES（全部新建）:
- src/itsf/s0/runinfra.py
- tests/test_runinfra.py

FORBIDDEN FILES: 冻结文件；src/itsf/data/**；guards.py；src/itsf/mc/**；
scripts/**；ops/**（registry 只读）；授权包；SA-4 的全部文件；tag/历史。

IMPLEMENTATION REQUIREMENTS:
1. **JSONL hash-chain manifest writer**：append-only；每条
   {stage, relative_path, file_sha256, previous_record_hash}；manifest
   不对自身求 hash（manifest_self_excluded）；stage seal 记录；提供
   verify_chain() 重放校验；临时未关闭文件不得入 final manifest。
2. **Stage-C 日志守卫**：logger 包装器，只放行白名单消息 schema
   （阶段状态/心跳/文件 hash/非研究性完成状态）；数字白名单只允许
   计数与 hash；检测到 Oracle/标签/E1/E2/年度/频率/分布类词汇或
   非白名单浮点即抛异常（fail-closed，宁可误杀）；词汇表放
   contracts.py 引用。
3. **NA 守恒检查器**：输入产出 NA 表＋批准原因枚举（contracts.py），
   逐项守恒断言；未登记原因的 NA/NaN → 结构化失败对象；禁止内部用
   dropna/填充。
4. **expected_preflight_assertions 比对器**：从 contracts 载入断言表，
   与 runner 独立计算值逐项比对，输出逐项 pass/fail；**比对器不得把
   断言值回写或提供给计算路径**（单向只读）。
5. **RUN_FAILURE_REPORT / PRE_RUN_ATTEMPT_FAILURE 生成器**：结构化
   markdown＋json 双写入 trial 目录（目录路径由调用者传入；你不创建
   目录）；含失败点、已释放信息清单、chain 状态。
6. 全部函数纯参数化；无全局状态；无网络；不读真实数据。

REQUIRED TESTS（合成 fixture）:
- chain：追加/重放/篡改检测（改一条记录 verify 必败）；自引用排除；
- 日志守卫：白名单通过、研究词汇拦截、裸浮点拦截、计数与 hash 放行；
- NA 守恒：守恒通过、未登记原因拦截、多计/漏计拦截；
- 断言比对：全符/单项不符/形状不符三态；
- 失败报告：字段完整性。

STOP CONDITIONS: 规格歧义；需要改 contracts.py；超出文件所有权；
需要触碰 registry 写路径（那是 main agent 的）；发现可能影响 Primary
的未批准选择。写 DECISION_PACKET_RUNINFRA_*.md 后停。

禁止：创建其他 subagent；git commit；读取 C:\Users\Aaron\quant-data；
运行真实 S0；输出策略数字。

RETURN FORMAT:
- files_read: / files_modified: / tests_run: / test_results: /
  evidence_added: / unresolved: / decisions_required: /
  frozen_files_untouched: / real_s0_not_run:
