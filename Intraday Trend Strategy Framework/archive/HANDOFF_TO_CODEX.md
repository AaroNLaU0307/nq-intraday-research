# HANDOFF_TO_CODEX — 项目统一交接入口

生成：2026-08-01，main agent（Fable），Aaron 指令。
本文件**只总结当前有效规则**；被后续裁决推翻的旧建议一律不载入。
所有重要结论均链接仓库内原始文档；本文件与原始文档冲突时，**以原始
冻结文档／IR／registry／审计报告为准**。

---

## 1. 项目目标与 S0 研究边界

- 目标：以证伪优先的预注册流程，检验 NQ opening-drive continuation
  是否存在可用于 prop-firm（Lucid/Topstep 50K）报考决策的日内结构性
  edge。三方分工：Aaron 决策、Fable（main agent）执行与证伪、
  Codex/ChatGPT 独立评审（Aaron 转发）。
- S0 = 双 Oracle 天花板研究（E1/E2 引擎、方向恒 = d_open、Y_cont 主
  标签、ADR14 归一化、分钟 close+adverse 双路径交 MC，判定优先序
  STOP→GO→β→α）。冻结全文：[STUDY_0_PREREGISTRATION.md](STUDY_0_PREREGISTRATION.md)、
  [PROJECT_CHARTER.md](PROJECT_CHARTER.md)。
- 样本：Development = NQ.v.0 1m，2010-06-06 → 2022-01-01（硬边界，
  DataRole 枚举强制，见 src/itsf/roles.py）；IV（2022→2025H1）**未采购、
  不上机**，H1 冻结后才买（访问预算 1 次）。
- S0 无任何"策略收益"结论资格：产出是 Oracle 天花板与结构统计，进
  MC 门槛判定（[MC_METHOD_SPEC.md](MC_METHOD_SPEC.md)），再到 Checkpoint 0。

## 2. 冻结文件与哈希（当前规范字节）

冻结两批：`s0-freeze-v1`（commit 89e2505928342d131c8f6eff93369bcc46f909b4）
与 `mc-freeze-v1`（commit 5d1ec10ee3ff66cf9bd9c432458d3367dea42da6）；
两相登记见 [FREEZE_LOG.md](FREEZE_LOG.md)。规范哈希单一真源 =
`src/itsf/guards.py::FROZEN_HASHES`（7 项）：

| 文件 | sha256（前 16） |
|---|---|
| PROJECT_CHARTER.md | 5176320fb54a30e5 |
| STUDY_0_PREREGISTRATION.md | 6cca20b7b1ce496d |
| purchase_plan.yaml | 02edbc2cb8481089 |
| MC_METHOD_SPEC.md | a6de4a286eaff5ab |
| gate1/platform_params.yaml | 702b983baba88d83（MC1.1-G9 addendum 后规范） |
| gate1/evidence_registry.yaml | 8ec318088ebedc9a（同上） |
| gate1/snapshots/2026-07-28/snapshot_manifest_v5.json | 5b6083b5ee61db9c |

运行前电池：全量 pytest（内含冻结哈希校验测试）＋
`guards.verify_frozen_hashes()`＋[scripts/final_candidate_scans.py](scripts/final_candidate_scans.py)
（秘密/占位/skip 三扫描，排除规则 E1-E7 全披露于脚本内）。
环境七件锁（runner 关键源哈希 9 项＋requirements.lock＋preflight 两工件）
见 [S0_REAL_RUN_AUTHORIZATION_PACKET.md](S0_REAL_RUN_AUTHORIZATION_PACKET.md) §0。

## 3. 已批准 IR 完整索引（全文见 [IMPLEMENTATION_RESOLUTIONS.md](IMPLEMENTATION_RESOLUTIONS.md)）

| IR | 一行摘要 |
|---|---|
| IR-1..11 | M2/M3 批复批次（IR-1 diagnostic_only；IR-10 B2F separate counters 不耗全局 6 次计数等） |
| IR-12/18 | F10 多事件日＝NA＋diagnostic sidecar，禁发明优先级；互斥分区 128+134+83+2528+9=2882 |
| IR-13 | FOMC 仅官方预定 statement 日 92 天；非预定行动仅诊断；cancelled 不入表 |
| IR-14 | as-released 口径（D3） |
| IR-15 | 路径用实际收盘差分；缺 bar 不代换（配合 IR-19/26 锚点规则） |
| IR-16 | symbology 仅验证与披露合约身份，不反向改 Primary 语义；F-32 reconciliation 段已批 |
| IR-17 | 2010-15 FOMC 无官方时刻 45 行＝NA＋release_time_status 列，禁凭记忆补 |
| IR-19 | prev_rth_close＝紧邻上一实际 CME RTH session；早收盘日取最后排期 bar close＋sidecar；vendor 零 bar 参照不跳过 |
| IR-20 | F4 参照集＝严格早于当日的 60 个实际 RTH 完整早盘日 |
| IR-21 | Y6 按年 average-rank decile；禁 tie-break；n_year=1→decile 1 是显式 singleton 约定（勘误在案） |
| IR-22 | 必需 opening volume 非有限＝INPUT_DATA_DEFECT，Stage B STOP；禁 np.nansum |
| IR-23 | Y1/Y2/Y3 逐标签独立可算性；删 d_open==0 整行早退；labels.py 限定解锁 |
| IR-24 | L82＝冻结字面 Option B（ret_open30 可算且恰为零）；diagnostic opening_numerator_zero；禁锚点相等替代 |
| IR-25 | 运行可满足性：状态无关 registry 测试＋RUN_AUTHORIZATION_SUPERSEDED 存活集合语义（0/1/>1 fail-closed） |
| IR-26 | vendor-degraded 标记仅诊断；锚点可用性＝精确排期收盘 bar 存在且 finite；禁收窄标记集（实施边界）；八条语义全文见台账 |

裁决原始包：DECISION_PACKET_*.md（根目录，逐案）；M4 批次见
[DECISION_PACKETS_M4.md](DECISION_PACKETS_M4.md)。

## 4. 当前 HEAD

本 handoff commit 之前的状态基线 =
`b69714c0d22581cf3238900d56bce175825bfa77`（含 registry 行 11 READY 与
CODEX 评审包；与被 SA-16 审计的代码候选
`6cb7eb718c903d119b7e51c7171e6db6f43aca67` 零代码字节差）。
本文件自身随独立 handoff commit 入库（自引用限制：本文件不记载
自身 commit 哈希；以 `git log -1 -- HANDOFF_TO_CODEX.md` 取）。

## 5. Trial Registry 完整状态摘要（[ops/TRIAL_REGISTRY.md](ops/TRIAL_REGISTRY.md)）

append-only 事件链，13 事件＋2 个 runner 追加的 "+" 失败行：
1 TRIAL_REGISTERED → 2 GOVERNANCE_FRAMEWORK_APPROVED → 3 PACKET_APPROVED
→ 4 RUNNER_IMPLEMENTED @7960603 → 5 READY @7960603 → 6 RUN_AUTHORIZED
@524c9ab（Aaron §10 第一次）→ "+"（尝试 1 失败）→ 7 SUPERSEDED(6)
→ 8 READY @36c7b58 → 9 RUN_AUTHORIZED @08e74235（第二次）→ "+"（尝试
2 失败）→ 10 SUPERSEDED(9) → 11 READY @6cb7eb7。
生产解析器（scripts/s0_real_run.py::resolve_authorizations）当前返回
**0 条存活授权**——真实 S0 处于未授权态。状态机与词汇见
[S0_REAL_RUN_AUTHORIZATION_PACKET.md](S0_REAL_RUN_AUTHORIZATION_PACKET.md) §0/§10。

## 6. S0-T001 全部尝试与 exposure 状态

| 尝试 | 授权 commit | 终点 | incident | 工件 |
|---|---|---|---|---|
| 1（2026-08-01T12:17Z） | 524c9ab | Stage-A `full_pytest`（IR-25 自锁） | INC-e6fe49ec63de | attempts/S0-T001-A20260801T121730Z/ |
| 2（2026-08-01T16:20Z） | 08e74235 | Stage-B `preflight_assertions_match`（IR-26 语义分歧） | INC-fa9234e0e541 | attempts/S0-T001-A20260801T162047Z/ |

两次均为 PRE_RUN_ATTEMPT_FAILURE：**exposure 从未消耗，S0-T001 仍是
首次真实 trial**（exposure_seq 1，[EXPOSURE_LEDGER.md](EXPOSURE_LEDGER.md)）。
exposure 边界＝原子 RUN_STARTED（runs/ 目录创建＋事件同笔），Stage C
起烧号。第三次授权候选已 READY（registry 行 11）。

## 7. 未决问题与 P3 backlog

无阻塞项。P3（全部非阻塞，来源审计报告注明）：

| # | 项 | 来源 |
|---|---|---|
| 1 | post-RUN_STARTED registry hash 新鲜度变异测试（fixture 先追加行再调 hook） | SA-13（Aaron 已裁 P3） |
| 2 | §10 语句 >40-hex 截断接受（head_matches 兜底，无误授权风险） | SA-14 |
| 3 | supersede note 多字段组仅取首组 | SA-14 |
| 4 | 非数字 seq 的 RUN_AUTHORIZED 行将永久不可 supersede | SA-14 |
| 5 | 双状态测试合成 seq 89 与真实 seq 碰撞余量（现余 ~78 事件） | SA-15 |
| 6 | 测试 trial-ID 字面耦合（S0-T002 前须同步） | SA-15 |
| 7 | **跨 trial 授权行会楔死本 trial 解析——trial 2 启动前必须设计裁决** | SA-15 |
| 8 | IR-26 实施边界（完整 20 日标记集）无回归守卫；hermetic 修法＝monkeypatch 合成 condition.json 单测 load_real_session_schedule | SA-16 N1 |
| 9 | 非 finite 测试直调 _prev_close_map（可接受，合成市场无法造 inf） | SA-16 N2 |

## 8. Fable 自动派工权限（FABLE_AUTO_ORCHESTRATOR ＋ AUTONOMOUS_MILESTONE_MODE，Aaron 2026-08-01）

- 自主：分解工程任务；自动选 Sonnet（默认工程）/Opus（高歧义/跨模块/
  对抗审计）；自动派低风险 subagent（最多并行 2、零文件交集）；审查
  subagent 实际落盘文件（不信自述）；电池/扫描/变异验证；集成 commit。
  普通工程缺陷最多自动修复两轮。
- 不再逐项向 Aaron 汇报普通小任务/测试红绿/局部修复/subagent 状态——
  这些写入 commit message、审计文档与任务台账。
- 审计型 subagent 一律只读；隔离副本探针技术（授权态 Stage A/B、
  变异注入）是标准做法，真实仓库离场必须 clean＋哈希核对。
- 每个里程碑 commit 备 CODEX_REVIEW_PACKET_*.md 供 Codex 查真实仓库
  （非文字转述）。

## 9. 必须升级给 Aaron 的决策类型（七类，逐字有效）

1. 新方法歧义或任何 DECISION_PACKET；
2. 需改冻结规则、IR、NA 分类学、标签、样本资格、Primary、Oracle、
   成本、fill 或 exposure 边界；
3. 需真实数据研究运行或新的 trial 授权；
4. 两轮自动修复后仍有 OPEN/PARTIAL；
5. 发现可能改变正式研究数字的实现偏差；
6. Codex 独立审计与 main-agent 裁决实质冲突；
7. 正式密封报告或结构化失败报告生成。

升级包固定格式：当前 HEAD／发生了什么／已确认事实／未决问题／
Option A-B／影响方向／main-agent 推荐／Codex 审计意见／是否触碰
真实数据或消耗 exposure。

## 10. Codex 只读审计职责

- 对照 CODEX_REVIEW_PACKET_*.md 独立检查**真实仓库字节**（哈希重算、
  diff 范围、测试与扫描重跑、变异判定力复验），不接受 main agent 的
  文字总结为证据。
- 有权（在隔离副本内）复刻授权态探针；不得改真实仓库、不得运行
  真实 S0、不得计算或展示 Oracle/标签/收益数字。
- 与 main agent 结论冲突时→升级类型 6，Aaron 仲裁。
- 历史审计范式参考：SA-16 报告（见 registry 行 11 注记）、
  [CODEX_REVIEW_PACKET_IR26.md](CODEX_REVIEW_PACKET_IR26.md)。

## 11. 硬边界（真实数据／Oracle／MC／IV／lockbox／trial 授权）

- **真实 S0/Oracle/EV/MC/Checkpoint 0：全部锁定**，唯一解锁途径＝
  Aaron 单独发送 §10 逐字语句（模板见 packet §10；解析器逐字匹配，
  附加任何文字即无效）。
- trial 状态转换（registry 事件追加）＝main agent 独占写者；append-only，
  勘误只能以 SUPERSEDED 类事件追加（IR-25 语义）。
- IV 数据：未采购、不上机、H1 冻结后才买（访问预算 1 次）。
- lockbox/二副本：E:\quant-data 三方核对＋SECOND_COPY_ATTESTED.flag
  （[ops/physical_copy_attestation.json](ops/physical_copy_attestation.json)）；禁自证/自翻 flag。
- API key：仅环境变量，禁打印/入库/入异常文本；Databento key 生命周期
  已关闭（[M4_KEY_CLOSURE_ATTESTATION.md](M4_KEY_CLOSURE_ATTESTATION.md)）。
- 冻结文件/tag/历史：永不修改；里程碑 commit 一律机器退出码硬闸。
- 运行期间零信息释放：Stage-C 日志词汇机器守卫；失败细节密封于
  attempt/run 目录内 INCIDENT_*.md；正式数字只能出现在 Stage E 封存
  报告中一次性交付。

## 12. 下一项允许执行的动作

**等待 Aaron 对其选定的 HEAD 发出第三次 §10 逐字语句。**
收到后（且仅收到后）：追加 RUN_AUTHORIZED（不建 commit）→ 零参数
入口 `python scripts/s0_real_run.py` → Stage A 13＋1 门 → Stage B
5 检查 → exposure 前 registry 复核 → 原子 RUN_STARTED（烧号点）→
Stage C 真实计算 → Stage D 完整性 → Stage E/F 封存 → 一次性交付
密封报告或结构化失败报告（升级类型 7）。
在此之前允许的仅有：只读确认、文档/记忆维护、Aaron 明示的新任务。
**不得自动再授权、不得自动运行、不得动 P3 项（除非 Aaron 点名）。**
