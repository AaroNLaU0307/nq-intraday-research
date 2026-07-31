DISPATCH: Opus 5 / high（评分：exposure 语义＋安全门＋跨模块 ≥2）。
SUBAGENT TASK ID: M5-T4b / SA-7 — runner 栈硬化（SA-6 CRITICAL/HIGH 修复）
ROLE: 运行治理硬化工程师。基线 f67d3bb 之后的 SA-6 审计落档 commit。

必读：ops/M5_RUNNER_TASKBOARD/SA6_AUDIT_FINDINGS.md（你的任务书本体）；
S0_REAL_RUN_AUTHORIZATION_PACKET.md §3/§5/§6/§8/§9/§10；
src/itsf/contracts.py；ops/TRIAL_REGISTRY.md 事件表格式。

ALLOWED FILES: scripts/s0_real_run.py、src/itsf/s0/runner.py、
src/itsf/s0/runinfra.py、.gitignore、tests/test_s0_runner.py、
tests/test_runinfra.py。
FORBIDDEN: 其余一切（含 context/dataset/labels/features/contracts/
冻结件/registry 本体——registry 只读格式参照）。

修复清单（逐项闭环并配测试；fix direction 见 findings 文件）：
- F-01 g_authorized 解析事件表行（event 列恰为 RUN_AUTHORIZED＋note 含
  逐字 §10 语句模板＋40 位 hash 与 HEAD 全等）；实现门 13。
- F-02 Stage-C 接线占位改为 Stage-B 门 stage_c_wiring_activated。
- F-03 clean 门白名单（ops/TRIAL_REGISTRY.md、attempts/、runs/）＋
  .gitignore 增 attempts/、runs/；授权 commit 从事件行解析（联动 F-11）。
- F-04 runner 消息 schema 化（stage=X status=start|end|heartbeat）＋注入
  logger 强制经 runinfra.validate_log_event 包装；加集成测试断言接线。
- F-05 失败文本降格：错误类＋不透明 incident id 进 registry note 与报告
  正文；原始异常细节只进 runs 目录内 sealed detail 文件。
- F-06 接线四机件：Stage B 用 compare_preflight_assertions（expected 由
  调用者从 assertions 文件载入后传参——runinfra 仍不得自读）；Stage D 用
  check_na_conservation；Stage E 产物经 append_manifest_record 入链＋
  stage seal；F 验 verify_chain_records。
- F-07 补门：seal_check（subprocess 调 quant-data\tools\seal_check.py，
  只读）、structure assertions（pyyaml parse）、LOCKED 增 A1 manifest
  d8d1edc7…、raw_file_set 08fca11b…（按包 §4 公式现算对比）、preflight
  json 5c0ae2d7…。
- F-08 runs/ 预存检查改为按 trial id 前缀扫描目录；RUN_STARTED 追加失败
  时写 HALF_TRANSITION.md 入孤儿目录。
- F-09 git/pytest 子进程洗净 env（显式最小 allowlist）＋pytest 门断言
  collected 总数（从输出解析≥当前 347）。
- F-10 Stage A/B 门调用与 mkdir 全包裹 try→PRE_RUN_ATTEMPT_FAILURE 路径。
- F-11 authorized_commit=事件行解析值；与 HEAD 不等→门失败。
- F-13 check_na_conservation 删 approved_reasons 参数、reported_total_na
  必填（同步修其测试）。
- F-14 写显式翻译层 translate_preflight_assertions()（preflight json 词表
  →contracts 词表、funnel 10 键→5 数链、剔除 adr14 行）——纯映射函数＋
  测试；**不改两侧语义**。
- F-20 守卫词表增 theta|base_rate|cont|adr|rvol|gap|retrace|warmup|
  funnel|\bna\b；file_hash 文件名拒含数字下划线组合模式；completion 的
  records= 上限治理不必做（计数合法）但文件名模式要堵。
- F-26/27 verify_chain 要求每阶段 seal＋≥1 记录；corrupt tail →
  ManifestIntegrityError；exc_type 只允许真实 isinstance 映射。
- F-34 Stage A 首门改调 guards.assert_real_run_allowed()（消双实现）。

禁触方法决策区（等 Aaron）：F-15/F-17/F-25 相关行为不得改。
禁 git commit；不读真实数据（quant-data 只允许 seal_check 工具调用）；
测试全合成；pytest 全量只增不破（基线 347）。
RETURN FORMAT：files_read/files_modified/tests_run/test_results/
fixes_closed(逐 F 编号)/unresolved/decisions_required/
frozen_files_untouched/real_s0_not_run。
