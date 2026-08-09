# CODEX_REVIEW_PACKET_M6_1_4（证据架构候选，供 Codex 独立复审）

> ## 时效声明（M6.1.6 / S3 治理更正轮补，2026-08-09）
>
> **本 packet 描述 M6.1.4-R2 轮。其后 M6.1.6 轮已在同一未提交工作树上继续
> 改动**（`scripts/s0_real_run.py`、`src/itsf/s0/runner.py`，另新增
> `src/itsf/s0/output_proof.py` 与其测试）。**本文件的以下数字绑定的是
> R2 轮的工作树字节，该字节已不存在，不可从当前字节复算**：
>
> | 本文件所载 | R2 轮值 | 当前工作树值（M6.1.6，S3 实测） |
> |---|---|---|
> | 电池 | 2093 | **2146** |
> | `MIN_COLLECTED_TESTS` | 2093 | **2146** |
> | `s0_real_run.py` sha256[:16] | `5ea7b7f11e84577c` | **`937c96bf6b15d26b`** |
> | 工作树条目 | `10 modified + 8 untracked` | **21 条** |
>
> 其余生产源哈希（`contracts.py d72a9b05dbf481a4`、`report.py 52d050bb6f1095e9`、
> `handoff.py a1f2c0a1ac77f96d`、`evidence.py 676fbcd1ae0ac2a9`）经 S3 复算
> **与当前字节仍一致**。**不得对本文件整体加「全部陈旧」的笼统标注**——
> 那对上述四行为假。当前轮次见 **`CODEX_REVIEW_PACKET_M6_1_6.md`**。
>
> **本文件 §10 的复核结论（R1 PASS 附条件 / R2 FAIL）是终局记录，未被 M6.1.6
> 推翻**；M6.1.6 未触碰叶／token 证据系统。

- **baseline（父 commit）**：`1e188b54ace011bb4c2ab7356f775af6d32aab37`（M6.1.3，Codex 判 HOLD）
- **本审查对象**：`UNCOMMITTED_WORKTREE_SNAPSHOT`（**尚未提交**的工作树：
  `10 modified + 8 untracked`，父 commit 即上述 baseline）。本文件在 HOLD 期间
  **不使用** `THIS_COMMIT`／"本 commit"字样——没有 commit 可指。仅当所有门通过
  并确实生成候选 commit 时，本行才改写为 `THIS_COMMIT`。
- **状态沿革**：
  - `M6_1_4_STATUS=HOLD`（首次收口）—— 最终独立复核（全新只读代理）判 2 MEDIUM
    ＋ 2 LOW，两个 MEDIUM 均为**此前修复轮曾判闭合、经独立复核重新打开**的缺陷类
    （F-1／F-2），故按停止规则不提交、不再堆叠局部修改，C-7／C-12 撤回降级。
  - `M6_1_4_ARCH_STATUS=HOLD`（ARCH 轮，Aaron 授权的独立架构闭合轮）——
    当时判 **F-1 结构性闭合（PASS）／F-2 未闭合**，并据此新建 C-15 行。
    **该 F-1 PASS 已于 R2 轮被证伪**（见 §9），C-15 因此撤回。
  - `M6_1_4_R2_STATUS=HOLD`（**本轮**）—— R2 只读事实核查（S3）在 ARCH 轮宣告
    PASS 的配置网关上**实证两条新的绕过机制**，F-1 **第二次**在宣告闭合后复发；
    F-2 的叶粒度缺口经 S2 叶谱系车道补强但仍未闭合。两条工程车道（S1／S2）
    已就位并全绿。
    **【时态更正 —— M6.1.6 / S3，2026-08-09】此处原写「两名独立复核员尚未
    开跑」，与本文件自己的 §10 矛盾且已过时：两名复核员其后确已开跑并交出
    判定——`R1_VERDICT=PASS`（附三条声明更正条件）／`R2_VERDICT=FAIL`
    （见 §10）。结论不变（F-1／F-2 同为 `PARTIAL + ENGINEERING_REQUIRED`），
    但理由改为 §10.6 所载：F-1 因三条声明被证伪而未 CLOSED，F-2 因 R2 判
    FAIL 而未闭合。**
    故本 packet 一律写**未闭合态**：**F-1 与 F-2 同为
    `PARTIAL + ENGINEERING_REQUIRED`**。
- **裁定前提**：Codex 对 M6.1.3 判
  `M6_1_3_VERDICT=HOLD / REAL_RUN_READY=NO`，RC-1（重算锚点不达原子）与
  RC-2（准入只重算 schema 不重算语义）由 `DECISION_REQUIRED` 改列
  **`ENGINEERING_REQUIRED`**。本里程碑即该两项的工程闭合。
- **REAL_RUN_READY=NO**、**STRATEGY_COUNCIL=LOCKED**（不变）。不追加 READY、
  不申请授权、不建 tag、不追加任何 registry 事件。

## 0. 验收门实测

**证据级别声明**：下表主体为 **`FABLE/OPUS_REPORTED`**（本工程会话主代理＋子代理
本机实测）＋ **`S3_INDEPENDENTLY_RERUN`**（只读代理 S3 于 2026-08-09 在同一未提交
工作树字节上自行复跑，逐项复算，非转录）。**`CODEX_NOT_FULLY_RERUN`**：Codex 尚未
独立复跑，复审时应视为待验证的自报数据，而非已核实事实。

| 门 | 结果（M6.1.4-R2 收口，串行前台实测） |
|---|---|
| `pytest -q -rs` | **2093 passed / 0 failed / 0 skipped**（S3 复跑同值，260.52s） |
| collected == `MIN_COLLECTED_TESTS` == 钉 | 2093 == 2093 == 2093（`scripts/s0_real_run.py` 与 `tests/test_s0_runner.py` 双钉，S3 逐文件核对） |
| 分套件（**部分**，占 850/2093；其余 1243 分布于另 **24** 个测试文件，全库共 27 个 `tests/test_*.py`） | m6_chain 163 · config 363 · evidence 324 |
| 本轮增量算术 | 1891（ARCH）＋ 125（S1／F-1）＋ 77（S2／F-2）= **2093** |
| `guards.verify_frozen_hashes()` | OK（`FROZEN_HASHES` 共 **7** 项） |
| `scripts/final_candidate_scans.py` | `SCANS=CLEAN`，exit 0 |
| `git diff --check` | 净（exit 0） |
| `ops/TRIAL_REGISTRY.md` sha256 | `de63b3d690c5c4be1def67aff9e0302138e9910df5b9a89acb1db57697b0b440`（＝基线，未修改） |
| `EXPOSURE_LEDGER.md` sha256 | `394813431d879555b7504d2501c40123368d67a517359e056692eb6b0f6bc9e6`（＝基线，未修改） |
| `runs/` | 不存在 |
| 真实数据 | 零读取；`RealChain._ensure` 从未在真实数据上调用；未运行真实 S0 |

**"0 skipped" 的性质（两类陈述必须分开）**：

- **观测值**：本环境本次运行报告 `0 skipped`。
- **代码事实**（与上一行不同的一类陈述）：套件内**仍存在**条件性跳过——
  `tests/test_preflight.py` 有 **10 处** `pytest.skip`，且为全库**唯一**含
  `pytest.skip` 的文件（S3 全库计数核实）。preflight 工件缺失时会触发。
  因此 `0 skipped` 是**观测结果**，**不是结构保证**。

**历史电池值（不同工作树，均不可从当前字节复算）**：

| 值 | 归属 | 标注 |
|---|---|---|
| 1707 passed | M6.1.4 首次收口工作树 | `FABLE/OPUS_REPORTED; NOT_REPRODUCIBLE_FROM_CURRENT_BYTES` |
| 1891 passed | M6.1.4-ARCH 工作树 | `FABLE/OPUS_REPORTED; NOT_REPRODUCIBLE_FROM_CURRENT_BYTES` |
| 2093 passed | **本轮（R2）工作树** | `FABLE/OPUS_REPORTED; S3_INDEPENDENTLY_RERUN; CODEX_NOT_FULLY_RERUN` |

生产源哈希（sha256 前 16 位，M6.1.4-R2 收口值，S3 复算）：
`s0_real_run.py 5ea7b7f11e84577c` · `contracts.py d72a9b05dbf481a4` ·
`report.py 52d050bb6f1095e9` · `handoff.py a1f2c0a1ac77f96d` ·
`evidence.py 676fbcd1ae0ac2a9`。
授权包 §0 环境锁中 `s0_real_run.py` / `contracts.py` / `evidence.py` 三行
**已标注为陈旧快照**（其余 10 行经 S3 核对与当前字节一致）；**须在生成候选
commit 前重渲染**（HOLD 期间不重渲染，以免声称一个不存在的候选）。

## 1. 审查工件（可从仓库独立读取）

| 工件 | 内容 | 溯源 |
|---|---|---|
| [B0_SOURCE_LINEAGE_MATRIX.md](B0_SOURCE_LINEAGE_MATRIX.md) | 13 个正式节＋handoff 工件的 **148 个决策性叶值**逐行 lineage（8 列）、EV-1..EV-13 证据对象清单、CR-1..CR-12 一致性风险、S5/S6 的 RC-1/RC-2 定量陈述与"无裁决不可闭"清单 | B0 只读车道原件**逐字节**入库（sha256 `c932f85fe797d7fd8e2c11cb054f635c0ce87d1182b4811cf44ed6e760fcdf80`，S3 复算一致；148 个 `L###` 行、EV-1..EV-13、CR-1..CR-12 均经 S3 计数核实），非重写、非重建。**身份限定：它是 M6.1.4 动工前在 baseline `1e188b5` 上测得的 BASELINE 设计矩阵**，供实现车道作设计契约与审计员作评分依据；**它不描述最终实现状态**——实现后的实际覆盖以本 packet §2／§7／§9 与代码测试为准 |
| [M6_1_4_LEAF_LINEAGE_MATRIX.md](M6_1_4_LEAF_LINEAGE_MATRIX.md) | **本轮新增（S2 车道）**：把注册表与完备性判据下沉到**叶粒度**的谱系矩阵——每个被捕获的 dataclass 叶登记其处置与权威来源，或反向声明为不消费并在披露中写明。**121 行**叶级登记 | sha256 `c982f80b48c05e38b1fd24971f4def76f71788bfa20608e726c4ee23770b43fe`（R2 轮 S3 复算一致；**M6.1.6 已改动该文件，此哈希不再是当前值**）。**S2 声明的残余（逐字转录，未经本 packet 加工）**：「registry↔matrix 由测试钉住，matrix↔truth 没有；token 完备性只证明某个 check **访问过**每个叶，从不证明该叶有独立权威——121 行中有 **10** 行没有独立权威。」该残余是 F-2 未闭合的一部分，不得读作闭合证据。**【M6.1.6 / S3 状态变更】该文件现已标为 `PROVISIONAL / REJECTED AS TRUTH SOURCE`：其 §1／§4 散文与 `authority` 列不得作为源码事实引用（依据即本 packet §10.4 第 4／5／6 条）；其 §9 机器可读块仍被 `tests/test_s0_evidence.py:2372` 解析，故文件**非惰性**，§9 一字节未改** |
| [PHASE_D_COUNTEREXAMPLE_EVIDENCE.md](PHASE_D_COUNTEREXAMPLE_EVIDENCE.md) | 14 类反例的旧候选（`1e188b5`／前身 `712532d`）活复现 vs 新候选拒绝串矩阵；类 4 的 HIGH 发现与其闭合 | **证据限制（三条，文件内亦已声明）**：(1) harness 脚本位于会话临时目录、**未入库**；(2) 本文件是该车道最终报告的**转录**，不是重新执行的结果；(3) 因此**不能一键独立重放**——逐例复算需按文件 §0 的方法重建 harness（`git archive` 快照 ＋ 合成 fixture）。矩阵中的拒绝串可与当前代码逐条核对，这是它可被独立验证的部分 |
| [DECISION_REQUIRED_READY_SUPERSESSION.md](DECISION_REQUIRED_READY_SUPERSESSION.md) | READY 事件与当前 HEAD 的 append-only 语义待裁；A/B/C 三选项 | 事实按 **registry 字节 / git 历史 / 外部裁定** 三类分述；Codex 裁定标注为无库内一手来源。**S3 已对该文件全部事实逐条复算，无一需更正** |

## 2. 四分栏

### CLOSED（逐行申报证据类型；本栏**不**主张每行三证齐全）

> **栏首声明**：本栏内任一行的证据强度以其**本行**格子为准；**不存在跨行统一
> 的证据标准**。无该类证据的格子填 `—`。上一版表头曾写「生产接线 ＋ 独立重算
> ＋ 反例测试，三证齐全」，但表体已收缩为两列，且多行本就没有"独立重算"这一腿
> （见 C-13、原 C-15），该表头属过度声明，现撤销。

| # | 项 | 生产接线 | 独立重算 | 反例测试 |
|---|---|---|---|---|
| C-1 | **捕获期规范证据**：`CanonicalS0Evidence` 在 `build_full_study_result` 末尾捕获（EV-1..EV-13），深度不可变，与 formal **零可变对象身份重叠** | 捕获点在 `build_full_study_result` 末尾 | 身份分离实测 57 870 ∩ 434 = ∅（`FABLE/OPUS_REPORTED`，无库内工件，S3 未复算） | PHASE D 类 5；`test_s0_evidence.py` 身份分离与捕获后篡改测试 |
| C-2 | **reducer 覆盖子树由 evidence 重建，且与 producer 分歧即拒封** | 渲染器封存前边界 | 6 个 reducer 键（见 §3）逐一重建后比对 | 不等即 `evidence-reducer divergence from producer output — refusing to seal`；PHASE D 类 5/6 |
| C-3 | **封存字节逐字段绑定**：`MC_HANDOFF_*.jsonl` 解析回行后与 `evidence.record_fields` **19** 字段逐字段严格比对（S3 复算 `FORMAL_RECORD_FIELDS` == 19） | 渲染链内 | 另有时间序、量级栏、`max_favourable ≥ max(mtm_close)` | PHASE E round-2 复验 C32/C1/C7/C8/C29(×4)/C33 由 MISSED 全部转 CAUGHT |
| C-4 | **TP 日 entry fill 锚到 bar 前像**：EV-2 `entry_ref_price`（10:00 bar open）＋ EV-4 成本快照重导出，四种场景 | 渲染链内 | 成本快照重导出 | round-2 新反例 C19b：`evidence_record_entry_fill_vs_ev2:…20043.0!=20030.5` |
| C-5 | **网格抽样内容锚定**（PHASE D 类 4 的 HIGH 缺口）：成员资格（EV-1 分区）＋算术恒等（计数/markers/realized/allocation） | 渲染链内 | `mixture_mean_pnl` 由**解析字节**重导出 | `test_grid_draw_*` **5** 个测试（S3 计数核实），含宇宙外日期 `1999-01-04` 与"总数已修复"的类别对调 |
| C-6 | **结构层 COUNT 接线（限计数级——范围见下方粗体）** | 渲染链内 | 第二条结构不同的观测路径（EV-8 经 `pandas.isna` 读 features/labels 表） | round-2 C20/C21/C22/C23/C24 由 MISSED 全部转 CAUGHT |
| ~~C-7~~ | **撤回**：标记-消费不变量 —— 最终独立复核证明其仍可空转（§6 F-2），已降级为 **P-11** | — | — | — |
| C-8 | **EV-13 冻结哈希字节锚定**：`RealChain.compute` 从磁盘重算 **7** 个冻结文件摘要传入（S3 复算 `FROZEN_HASHES` == 7 项） | Stage-A 门 → evidence | 对账要求观测键集 == 声明键集且非空才移除标记 | **7** 个具名测试（`test_ev13_*`，S3 计数核实）＋ `evidence_frozen_hash_key_set_mismatch` |
| C-9 | **RC-2 bundle-atomic 准入**：依赖图（GRID→唯一有效 DAY_STRATA＋唯一 SEED_MANIFEST）、跨工件守恒 | `formal_seal_admission` | 语义重算（era/epoch 由日期重导、θ 嵌套、event tri-state、**63** 点格重建〔S3 复算 9×7=63〕、manifest 全量深等） | PHASE D 类 7/8/9/10 全 REFUSED；PHASE E auditor#2 判"依赖图对我构造的每一种形状都成立" |
| C-10 | **SourceContext 逐槽校验＋每次调用重验证**：13 个冻结槽钉到所属模块，词表必须是 set-of-str，空 θ 轴被拒，鸭型/子类被拒且不逃异常 | 每次调用重验证 | — | auditor#2 A8/A9/A10/A11 全闭；`test_med1_every_source_context_slot_is_validated` 用 `dataclasses.fields` 保证覆盖每个字段 |
| C-11 | **θ 冻结成员资格**：`SourceContext.thetas` 绑定 `study.FROZEN_THETAS` 单一真源（AST 测试断言 handoff.py 内无第二处字面量），非空、无重复、严格 float 子集 | 单一真源绑定 | AST＋token 双扫确认 handoff.py 内零字面量 | `test_closeout_theta_*` **8** 测试（S3 计数核实）；`(0.7,)` 拒因点名冻结源；复核另以 19 种形状实测全拒（`FABLE/OPUS_REPORTED`，无库内工件） |
| ~~C-12~~ | **撤回**：配置门"契约永不破"过宽 —— 同一函数内另有两处未包护执行点（§6 F-1），已降级为 **P-12** | — | — | — |
| C-13 | **never-crash**：四个消费者门对任意 JSON-like 畸形树只返回问题列表 | 四个消费者门 | — | PHASE D 类 11/12（旧候选抛 TypeError/AttributeError）；fuzz 测试 |
| ~~C-15~~ | **撤回**：配置网关"结构性闭合"过宽 —— R2 轮在 ARCH 轮宣告 PASS 的网关上**实证两条新的绕过机制**（`_atom_number` 的 int→float 转换、`_atom_ticks` 对可变 dict 与只读 mappingproxy 的同一化），网关据此交出**非规范的缓存实例**（§9）。已降级回 **F-1**，仍列 `ENGINEERING_REQUIRED` | — | — | — |

**C-6 的精确范围（本轮按代码逐函数收窄；上一版表述过宽）**：

- **已闭合（计数级）**：EV-9 funnel **各级基数**、EV-10 f10 **按类别计数**
  （`_reconcile_f10_raw` 另含词表外类别硬拒）、EV-11 **每日一行存在性 ＋
  `available` 聚合计数**、EV-8 **na/not_na 计数**。
- **明确不覆盖（三处，均经源码核实）**：
  1. **EV-9 各级日期集合的内容**——`_reconcile_funnel` 只比较 `len(levels[k])`，
     成员全错而基数正确者通过；
  2. **EV-10 的按日身份**——`_reconcile_f10_exclusive` 依 `m.final_category`
     计数，**从不以 `m.trade_date` 归键**（这正是 §8 第 5 项"46 个 `trade_date`
     全塌成 `ZZZ`"不可见的原因）。表内"含词表外类别硬拒"描述的是
     `_reconcile_f10_raw` 这一**另一个**函数，不修补互斥分区的按日缺口；
  3. **EV-11 的五个 per-day IR-23 布尔**（`o1000`/`c1544`/`pm_ok`/`adr_ok`/
     `dir_ok` 在 `evidence.py` 内**零引用**，S3 以 AST 普查确认）**与
     `available` 的标签键集完备性**（`compared` 按**日**计数、不按**标签**
     计数，故标签真子集在每一日出现时仍满足 `complete`）。

  上述三项归 **P-11 叶粒度未闭部分**；其中 EV-11 两项已由本轮新增披露标记
  显式暴露（§9 标记表）。

### PARTIAL（机制存在但未达全量闭合——如实申报，不称 CLOSED）

| # | 项 | 边界 |
|---|---|---|
| P-1 | **executable EXIT fill 与 FP-only 日 entry fill 的 bar 前像缺失** | 真原子是 1 分钟 bar，进程内不可留存。**捕获后**字节篡改已闭（C-3），但**compute 之前**被毒化的生产者不可达。封存标记 `PARTIAL:records.executable_fills:`；auditor 实测 EV-2 覆盖 32 个封存日期中的 16 个，措辞与实测一致 |
| P-2 | **MTM 序列（`mtm_close_pnl_1m`/`mtm_adverse_pnl_1m`）的完整 bar 前像** | 同 P-1；现有为字段绑定＋量级/一致性栏，非 bar 重导出 |
| P-3 | **DAY_STRATA / GRID_SAMPLES 未进入真实 renderer** | 生产 candidates 仅 `SEED_MANIFEST.json`（B0 L144/L145 标 NOT PRODUCED）。语义 checker 与依赖图已就绪并可测，但**无生产消费者**，故不称生产可达 |
| P-4 | **SEED_MANIFEST 生产态被 withheld** | `k_policy`/`crn_scope` 未裁（DR-M6-E / DR-4.7），UNRESOLVED 标记两向 fail-closed |
| P-5 | **bootstrap CI 区间未重放** | EV-7 只绑定输入序列摘要；未做 10 000 重采样重放（B0 L082） |
| P-6 | **网格 per-seed RNG 重放** | 抽样**内容**已锚定（C-5），但"流抽了哪几天"不可验证——分层键两轴无词汇（DR-2/3/6，B0 §S6.2） |
| P-7 | **stability_views 总体** | DR-7 未裁；可复现不等于正确（B0 §S6.1）。**并入 DR-7 的观察（原 D-3，已从 DECISION_REQUIRED 移出）**：不存在针对 stability 总体的**专项**封存拒绝门（A2b 以 D_TP 条件总体读法产出数值）。**措辞边界**：这不等于"DR-7 可以在生产链上通过"——全局 `StudyConfig` pending gate 仍会因 `stability_population` 未裁而阻断派生，Stage B 拒绝、零 exposure。缺的是**专项**门，不是**总门**。这是一条**观察**，不是新增裁决项 |
| P-8 | **NA 原因级归因** | EV-8 闭合 na/not_na **计数**级；per-date 原因归因仍单前像（CR-1 剩余部分） |
| P-9 | **全部 USD 数字** | DR-1 未裁：成本层输入未定，`_approved_injectables()` 恒 None，真实链 fail-closed（B0 §S6.3） |
| P-10 | `verify_handoff_conservation` 等无生产调用者的检查器 | 与 M6.1.3 相同，未改变 |
| **P-11** | **标记-消费不变量：字段／元素粒度已闭，叶粒度仍未闭**（原 C-7 → P-11 → ARCH 轮部分闭合 → R2 轮由 S2 叶谱系补强，**仍未闭合**；见 §7 F-2-ARCH、§8、§9）。**已闭部分**：22 个字段各有唯一登记处置、**35** 个 check、`complete >= applicable`、标记由遍历注册表派生、漏跑即硬问题（S3 复算 `CHECK_REGISTRY`==35、`FIELD_REGISTRY`==22 且键集 == `CanonicalS0Evidence` 字段集）。**未闭部分见下方"叶粒度证据分级"** | 首次收口时的实况：`checks[...]` 门覆盖 8 个分支，但 EV-3/EV-5/EV-7/provenance 被清空时无标记、无问题、封存字节与诚实运行**逐字节相同**；ARCH 轮另测出**部分剥离类**（EV-3 留 1/32、EV-7 留 1/32、EV-5 留 23/46）同样静默 |
| ~~P-12~~ | **配置门包护完全性**（原 C-12 → 降级 P-12 → ARCH 轮以架构机制闭合并升为 C-15 → **R2 轮 C-15 撤回**，回到 **F-1**，见 §9） | 首次收口时的实况：四类具名失败确经公共 `ready()` 拒绝（builder 调用 0），但同函数内 `cfg.methods != fresh_methods` 的 dataclass `__eq__` 与缓存元组解包两处未包护；ARCH 轮独立复现时又在同函数四行之后找到**同构的第三、第四个逃逸点**（`cfg != fresh_cfg`） |

**P-11 的叶粒度证据分级（本轮重写；旧表述"51 个捕获叶"过强，撤销）**：

- **(a) reconcile 级普查**：**50 个被捕获的 dataclass 叶字段未被任何比较消费**
  ——复核员报数，**方法未入库、不可独立重算**。S3 以 AST 静态普查独立确认
  其中 **29 个在 `evidence.py` 内零引用**（107 个叶字段中），此 29 为**硬下界**。
- **(b) 1 个键集完备性家族**：EV-11 `available` 的标签键集（见 C-6 范围）。
- **(c) 经真实 `render_s0_report` 实测的 11 个 FAMILY 级变体**（§8），
  其中第 1–6 项在 ARCH 轮无任何标记／处置／硬码覆盖。
- **(d) 本轮 S2 叶谱系矩阵**：121 行叶级登记，**其中 10 行没有独立权威**
  （S2 逐字残余，见 §1 工件表）。

**在本轮 per-leaf 参数化测试与两名独立复核员的复核真正落地之前，不得把上述
任一数字写成"51 个叶已逐一证明沉默"，也不得读作 F-2 已闭合。**

### ENGINEERING_REQUIRED（纯工程，可在既有权限内完成）

**分类正交性声明**：`PARTIAL` 描述的是**现状覆盖度**，`ENGINEERING_REQUIRED`
描述的是**闭合它所需的工作性质**。二者正交——同一问题可同时出现在两栏
（如 P-1 与 E-1、P-8 与 E-3、P-11/P-12 与 F-1/F-2）。

**本栏当前成员共 9 项（F-1、F-2、E-1…E-5、E-6、E-7），单表列出。**
**只有在两名独立复核员对 F-1 与 F-2 同时判 PASS 之后**，本栏才可缩减为
E-1…E-7。**【时态更正 —— M6.1.6 / S3，2026-08-09】该条件已被实测判定为
不满足：两名复核员已开跑，R1 判 PASS 但其三条声明被证伪，R2 判 FAIL
（§10／§10.6）。故本栏维持 9 项。** 仍**不得以任何形式预记闭合**——
不写"已闭合"、不写"预计闭合"、不在 §0 状态行声明 PASS。

| # | 项 | 关系／现状 |
|---|---|---|
| **F-1** | 配置网关的**完全**规范性与异常包护（原为 P-12 的工作面） | **未闭合 —— `PARTIAL + ENGINEERING_REQUIRED`。** 历史：盲审#2 MED-2 → 修复轮判闭合（C-12）→ 最终独立复核**重开**（§6 F-1）→ ARCH 轮网关重构、PHASE F 判 PASS（C-15）→ **R2 轮第二次重开**（§9）。同一缺陷类**两度**在宣告闭合后复现。S1 车道已就位修复（+125 测试，两条机制现均被拒，S3 实测复验）。**【时态更正 —— M6.1.6 / S3】原写「两名独立复核员尚未开跑」已过时：复核员已开跑，R1 判 PASS 但附带三条被证伪的声明（§10.4 第 1／2／3 条），故按 §10.6 状态维持未闭合。** |
| **F-2** | 证据消费的**完备性**判据，需下沉到**叶**粒度（原为 P-11 的工作面） | **未闭合 —— `PARTIAL + ENGINEERING_REQUIRED`。** 历史：首轮加 `checks[]` 标志与 AST 自测 → 独立复核重开 → ARCH 轮改为处置注册表＋`complete>=applicable`（字段／元素粒度闭合，叶粒度复发）→ R2 轮 S2 叶谱系矩阵＋5 个新披露标记（+77 测试）。**残余（S2 逐字）**：registry↔matrix 由测试钉住，matrix↔truth 没有；token 完备性只证明某个 check 访问过每个叶，从不证明该叶有独立权威——**121 行中 10 行没有独立权威**。闭合要求见 §8 |
| E-1 | 捕获 executable **exit** 参考价与 FP 日 entry 参考价（EV-2 式可执行路径记录扩展），闭合 P-1 的生产者毒化面 | 不涉任何未裁定义；纯捕获面扩展 |
| E-2 | 捕获 MTM 逐分钟 bar 前像（体量较大，需先定证据规模策略），闭合 P-2 | 同上 |
| E-3 | NA **原因级**第二观测路径，闭合 P-8 | 同上 |
| E-4 | 把 DAY_STRATA/GRID_SAMPLES 接入真实 renderer（P-3 的接线部分） | 接线本身是工程；其**内容**受 DR-2/3/6 约束，故接线后仍会 withheld |
| E-5 | 序列化器统一（CR-10：三个 canonical JSON 实现）与 `theta_key` 单点化残余（CR-11 在 handoff 侧已闭，report/study 侧仍双份） | 纯重构 |
| **E-6** | **ticks 值的 int-vs-float 分歧尚无封存字节后果**（**归属：S1 车道本轮提出**） | S1 逐字：adverse-slippage 映射中 int 与 float 的 tick **值**，只有在某个 `DR-M6-A-v2` 消费者把该映射接进 `build_scenarios` **之后**才会取得封存字节级分歧；**今日该映射到不了任何封存字节**。故列为待接线后复查的工程项，**不是**今日的活缺口，也**不**构成 F-1 的未闭合理由 |
| **E-7** | **叶级披露的机器可读化与权威补齐**（**归属：S2 车道本轮提出**） | 由 S2 残余直接派生：为 121 行中**无独立权威的 10 行**补权威来源，或将其固化为永久披露。其**机器可读 schema 扩展**部分受 D4 约束（见 DECISION_REQUIRED），故 E-7 的可完成部分限于权威补齐与文档披露 |

### DECISION_REQUIRED（不自行裁决；受影响车道保持 fail-closed）

> **待 Aaron 裁决的完整集合 = DR-1…DR-8（八项方法家族）＋ READY supersession
> （A/B/C），共两组。** 下表 D-4/D-5/D-6 **不是新增的第三、四、五组**，而是
> **挂在既有 DR 伞下、被一条未落裁决卡住的工程项**——它们不增加 Aaron 需要
> 做的裁决数量，只说明"哪条已在队列中的裁决落地后，哪块工程才能动"。
> **凡属观察而非裁决请求者，一律不进本栏**（原 D-3 已按此规则移入 P-7）。

| # | 项 | 现状 |
|---|---|---|
| D-1 | **DR-1 … DR-8 八个方法家族全部未裁**（DR-8 ＝ DR-M6-H：E2 P1/P5 估计量；S3 已对 `DECISION_REQUIRED_M6_1.md` 核实确为 DR-1..DR-8 共 8 族） | 任一未裁 → `pending_method_decisions` 非空 → StudyConfig 不可派生 → Stage B 拒绝、零 exposure。`numpy.percentile(method='linear')` 在全库**未被写成 approved/frozen**，仅记为未批准的工程惯例；封存对 `estimator_status != "resolved"` 硬拒 |
| D-2 | **READY supersession**：registry 行 11 READY 属历史 commit `6cb7eb7…`，当前 HEAD 无 READY | 见独立裁决包，A/B/C 选项待 Aaron；本轮**未选择**、未追加事件。S3 已复算：`resolve_authorizations` 返回 **0 条存活授权**，链无 problem |
| **D-4** | **（DR 伞下·工程受阻）EV-11 五布尔→标签集 reducer 的冻结**（**归属：S2 车道 D1**） | 二选一，**均需 Aaron 一句裁决**：(a) 以一条新的 approved IR 冻结"五个 per-day 布尔如何归约为标签可用集"的规则，此后该 reducer 可被独立重算；或 (b) 接受一条**永久** `PARTIAL:structural.label_anchor_availability.per_day_values:` 披露。**本轮已按 (b) 的形态发出该标记**（见 §9 标记表），但那是 fail-closed 的**临时**姿态，不是对 (b) 的选择 |
| **D-5** | **（DR 伞下·工程受阻）机器可读的逐叶披露需要冻结 schema 扩展**（**归属：S2 车道 D4**） | 叶级披露若要成为机器可消费的结构（而非散文标记），须扩展已冻结的报告 schema；schema 属冻结面，未获裁决前不得扩展。故 E-7 只能先做权威补齐与文本披露 |
| **D-6** | **（DR 伞下·工程受阻）单调 `y_cont` 轨**（**归属：S2 车道 D6**） | 该轨的成立取决于 `y_cont` 总体口径，与 DR-4（bootstrap population）／DR-7（stability 总体）相邻；未裁前不实现，受影响处维持 fail-closed |

> **【本栏的 M6.1.6 / S3 更正，2026-08-09 —— 一条撤回、一条补正、一条降级】**
>
> **(1) 撤回一条从未落到字节的候选台账行 `NEW-LABELDEPS-CONFLICT`。**
> 其依据（`dataset._LABEL_DEPS` 与 `ok` 「互斥／内容不同」）**经逐格复算为假**：
> 在 `_LABEL_DEPS` 所载的四条轴（O1000, C1544, ADR14, d_open）上，
> 两者对**全部六个标签**取值一致（y_cont TTTT · y1 TTTF · y2 TTFF ·
> y3 FTFF · y4 TFTT · y5 TFTT）；唯一差别是 `ok` 另需 `pm_ok`，
> 而 `_LABEL_DEPS` 没有 PM 列。正确表述是 **PROJECTION**，不是矛盾。
> **它不是 Aaron 需要做的裁决**，队列长度不变。
> （检索确认该字面量全库零命中——撤回为纯文档性；真正落在字节里的
> 那段散文已在 `M6_1_4_LEAF_LINEAGE_MATRIX.md` §3 就地更正。）
>
> **(2) 补正：不得把 D-4 的背景读作「preflight／EV-11 全然未获批准」。**
> 存在外部治理链（IR-22 / IR-26 / registry 行 11），其授权对象是
> **用 preflight 的结构性计数作为 expected 断言**。**但该链不冻结 reducer**，
> 故 **D-4 本身不变，仍待 Aaron 二选一**。同时披露一处
> DOCUMENTATION-LAYER CONFLICT（工件 `approval` 字段说「待批」，
> `dataset.py:667-668` 与 `context.py:73` 两处 docstring 说「已批」）——
> 本轮**不解决**。详见 `CODEX_REVIEW_PACKET_M6_1_6.md` §6.1。
>
> **(3) 降级一条未经核实的同一性主张**：前序车道称 `ok` 与 preflight 的
> `required_anchors` 在六个标签上**精确一致**。由于同一车道在 (1) 上判断
> 有误，该主张按 **UNVERIFIED** 处理；M6.1.6 进一步实测到**三处谓词级
> 差异**（PM high vs PM 行计数、Y2 的 PM close 谓词、direction 的派生路径），
> 详见 `CODEX_REVIEW_PACKET_M6_1_6.md` §6.3。可陈述的只有**轴集一致**
> 与 **A1 数据上的经验一致**。

## 3. 措辞精确化（避免过度声明）

1. **只有 reducer 覆盖的 formal 子树"由 evidence 重建"**，共 6 个键：
   `structural.eras`、`structural.groups`、`era_axis.axes`、
   `oracle_daily.day_universe`、`frequency`、`theoretical_oracle`。
   其余节仍由 producer 产出，随后**与 evidence 对账**；两者不等即拒封。
   本 packet 不声称"全部 formal 由 evidence 生成"。
2. **JSONL 由 `records` 序列化**（`record_to_formal_dict`），随后解析回行、
   与 `evidence.record_fields` 逐字段核对。**不是**由 evidence 生成 JSONL。
3. reducer 覆盖区的篡改被拒是"分歧拒封"，不等于"该区数值经原子证明为真"——
   数值真实性的边界见 P-1/P-2/P-9。
4. **C-6 的闭合限于计数级**，且**不覆盖** EV-9 各级日期集合内容、EV-10 的按日
   身份、EV-11 的五个 per-day 布尔与 `available` 标签键集（三项的源码依据见
   §2 C-6 范围块）；原因级 NA 仍 PARTIAL（P-8）。
5. PHASE D 附件的旧候选证据为**转录**，harness 未入库（该文件已披露）。
6. **数字的证据级别必须随数字一起写**：凡"复核员自造 N 例"一类的计数
   （如 C-11 的 19 种形状、C-1 的 57 870∩434、原 C-15 的 27 种），**无库内
   工件、不可独立复算**，一律标 `FABLE/OPUS_REPORTED`，不得与库内可计数的
   测试数（如 `test_ev13_*`=7、`test_grid_draw_*`=5、`test_closeout_theta_*`=8）
   混列而不加区分。

## 4. 审计轮次与残留

- **PHASE D**（旧/新逐类对照）：13 类当场闭合，1 类（网格抽样内容）判 HIGH →
  已在本工作树快照内闭合（C-5），并留 P-6 残余。
- **PHASE E 盲审 #1（evidence lineage）**：round-1 判 OPENS_REMAIN（HIGH-1 出场价
  无前像／死证据、HIGH-2 标记以捕获而非检查为门、4 Medium、3 Low）→ 修复轮后
  round-2 复验：C1/C7/C8/C29/C32/C33/C20/C21/C22/C23/C24/C5/C6/C10b/C12b/C25/C26/C27
  **全部由 MISSED 转 CAUGHT 或转诚实披露**；剩 1 Medium（EV-13 门）＋2 Low →
  **EV-13 门与 f10 词表外类别当时判为闭合**（C-8／C-6），剩余 1 Low ＝ P-6（已披露）。
  **注意**：此处"闭合"是当时修复轮的判断；其后最终独立复核**重新打开了
  F-1／F-2**（见 §6），R2 轮又**第二次打开 F-1**（见 §9），说明"修复轮自判闭合"
  与"独立复核确认闭合"不是同一件事。本 packet 一律以最新一次独立复核为准。
- **PHASE E 盲审 #2（admission/config/governance）**：判 OPENS_REMAIN（HIGH-1
  治理文档事实错误、MED-1 SourceContext 零校验、MED-2 配置门异常逃逸、MED-3/4
  措辞与陈旧哈希、6 Low）→ **当时的修复轮曾判其全部闭合**（治理文件 §1 三分来源改写并列出 5 个
  带码候选全哈希；C-10；C-12；本 packet §0 与授权包 §0 重渲染；-0.0 归一化、
  非字符串工件名、E7 路径密封化、`_EVENT_FLAG_VALUES` 单源化等 Low 逐条修复）。
  该审计员同时判定：**RC-2 依赖图成立、E7 三 seam 正例为真**（两个源 seam 单独
  都不能使 `ready()=True`，鸭型 methods 过不了型钉）。
- **PHASE E-final（原误写作"PHASE 4"）**：见 §6。
- **PHASE F**：见 §8。
- **PHASE R2（只读事实核查 S3 ＋ 工程车道 S1/S2）**：见 §9。
- **E7 正例的准确称谓**：**合成 config-to-compute 集成**（合成 dataset/bars，
  `_ensure` 被替换）。**不是**真实数据链，**不是**完整 A→F 生产运行。

## 5. Codex 复审入口

1. §0 验收门 → §2 四分栏 → §3 措辞精确化（重点核对是否有超出代码证据的 CLOSED）。
2. 独立工件：`B0_SOURCE_LINEAGE_MATRIX.md`（148 叶 lineage 与 PARTIAL/DR 归因）、
   `M6_1_4_LEAF_LINEAGE_MATRIX.md`（121 行叶级登记，含 10 行无独立权威的残余）、
   `PHASE_D_COUNTEREXAMPLE_EVIDENCE.md`（旧/新行为对照）。
3. **F-1／F-2 均写作未闭合**。**【时态更正 —— M6.1.6 / S3，2026-08-09】
   两名独立复核员已开跑：`R1_VERDICT=PASS`（附三条声明更正条件，其后被
   证伪）／`R2_VERDICT=FAIL`（§10）。因此「若两者均获通过」这一前件
   **未**成立，`ENGINEERING_REQUIRED` 未缩减，本栏维持 9 项。**
4. 若接受工程闭合：DR-1…DR-8 与 READY supersession 仍需 Aaron 裁决；
   Strategy Council 在 Codex 工程裁定通过前保持关闭。

## 6. PHASE E-final 独立复核结果与 HOLD 判定

复核由**全新只读代理**执行（未参与任何实现车道），10 行矩阵中
**7 行 CONFIRMED**（冻结 θ、准入依赖图与每调用重验证、hard/PARTIAL 的
EV-13 四态、渲染器分歧拒封 6/6、工件可独立读取且 148 叶实测在册、治理不变量
与 registry/git 事实逐条核对、电池 1707/0/0 与双钉一致），**3 行 NOT_CONFIRMED
（＝ 下表 F-1／F-2／F-3）**。**F-4 是矩阵之外的附带观察**，不计入 10 行。

> **阶段名勘误**：本节旧称"PHASE 4"，该标识在全库仅此一处、从无定义；
> 其余阶段一律用字母（PHASE D / E 盲审#1 / E 盲审#2 / F）。现更名为
> **PHASE E-final** 并已登记进 §4 阶段名册。

| ID | 级别 | 内容 | 闭合要求（不在该轮实施） |
|---|---|---|---|
| **F-1** | MEDIUM **（复发）** | `RealChain.ready()` 的 `(bool, str)` 契约仍有两处未包护执行点：`scripts/s0_real_run.py` 的 `cfg.methods != fresh_methods`（两个型钉均已通过后，dataclass `__eq__` 逐字段比较，字段内的恶意对象或 numpy 数组即可抛出/歧义）与 `cfg, why = _CONFIG_CACHE["cfg"]`（非 2-tuple／`__iter__` 抛出即逃逸）。**该轮实际暴露为零**：`runner.py` 将 Stage-B 异常转为 `_fail_pre_run`（注意其捕获 `Exception` 而非 `BaseException`）。缺陷在**声明准确性与纵深防御** | 将缓存解包与两处相等比较一并 `try/except BaseException → (None, reason)`；补三条回归 |
| **F-2** | MEDIUM **（复发）** | 清空 `opening_ranges`/`day_strata`/`bootstrap_inputs`/`provenance` 的证据对象**可经真实渲染器封存**：`hard_problems == []`、PARTIAL 标记与诚实运行一字不差、**全部封存文件字节相同**。根因：`checks["day_strata"]` 被写入却未被 `_partial_markers` 读取；`_reconcile_sizing`/`_reconcile_record_internals` 的 EV-3 锚点为空时静默跳过 L137 重算；`_reconcile_bootstrap` 的 EV-7 为空时所有摘要绑定与 CR-2 比较消失；`provenance` 仅读一个键，缺键即静默通过。AST 自测只验字段名出现，验不出**空转消费** | 为 sizing / record_internals / bootstrap 返回并存储 `ran` 标志并补 EV-3、EV-7 条件标记；`_partial_markers` 消费 `checks["day_strata"]`；缺失 `provenance["EV-2_oracle_cross_check"]` 改为硬问题；把 AST 自测替换为**行为式** |
| **F-3** | LOW | 本 packet C-11 原写"9 测试"，实为 **8**（已更正；S3 复算 `test_closeout_theta_*` == 8，确认更正正确） | 已修正 |
| **F-4** | LOW | `src/itsf/s0/stats.py` 有一行以 `# frozen: S0 §9` 开头的注释内含 `method="linear"` 字样，唯一可能被误读处。全库无任何文本把该估计量写作 approved/frozen，`report.py`／`study.py` 均标 UNAPPROVED；`git diff` 对该文件为空（非本候选引入） | 措辞澄清（非本候选范围） |

**该轮判定**：两个 MEDIUM 均属"上一轮宣告闭合、本轮复现"的同一缺陷类
（F-1 ← 盲审#2 MED-2；F-2 ← 盲审#1 HIGH-2）。按执行任务书
「若相同问题仍存在，停止并报告 HOLD，不继续堆叠局部修改」，该轮**停止工程
修补、不生成候选 commit**，仅对本 packet 作诚实性更正（撤回 C-7/C-12、修正
计数、补录本节）。

## 7. M6.1.4-ARCH —— F-1／F-2 的架构级处理（ARCH 轮）

Aaron 授权的独立架构轮。两条车道**先出设计说明、经主代理评审后才动笔**；
评审的否决条件预先声明为「再给点名行号加 try」与「每字段加一个 if」。

> **本节的效力限定（R2 轮后加）**：本节记录 ARCH 轮**当时**的设计与自判结论。
> 其中 F-1 的"结构性闭合"结论**已被 §9 证伪**；F-2 的粒度收窄结论仍成立但
> 仍未闭合。阅读本节时以 §9 为准。

### 原 C-15（F-1）配置网关 —— 单一信任边界 ＋ 阶段游标

- `_gateway_body(cursor)` 是**唯一**的配置解析路径，内部**零 try/except**：
  各求值点 `raise _Refusal(...)`；唯一的边界在网关外层，捕获 `_Refusal`（枚举
  拒因）与 `BaseException`（未枚举，按游标当前阶段归属并附消毒后的异常类型名）。
  **覆盖是结构性的**：将来任何人在 `_gateway_body` 内新增的求值点自动被覆盖。
  **求值点计数勘误（R2）**：本节旧写"13 个求值点各自 `raise _Refusal`"。源码
  自身的注释（`scripts/s0_real_run.py`，`_EVALUATION_POINTS` 上方）明确写道：
  13 个受命求值点中**只有 11 个**是带自身拒因的真实阶段——第 12 项
  **仅作归属**（进程内缓存写入无合法失败模式），第 13 项**不是阶段**而是
  单路径不变量。实现层面另有 `_GATE_STAGES` 19 项与 24 处 `_refuse`（S3 复算）。
- 支撑件：`_ConfigCacheEntry`（`__slots__` 不可变类，`type is` 判定，**不触碰
  对象**即拒绝 plain object / 1-tuple / 3-tuple / dict / 抛出型 `__iter__`；
  且无自动生成的 `__eq__`/`__repr__`）；**拒绝不再入缓存**；等价性一律走
  **指纹**；callable 仅按**进程内对象恒等**比较。
  **勘误（R2）**：本节旧写"numpy 与自定义 `Real` 一律**拒绝而非转换**"。作为
  原子层的一般性质，该表述为**假**——`_atom_number` 对普通 `int` 执行的正是
  **转换**（`value = float(value)`），这正是 §9 机制 (1) 的成因。准确表述为：
  「numpy 与自定义 `Real` 被拒绝；但**允许的叶类型之间**（`int`→`float`）
  存在归一化转换，故指纹在允许叶类型上**并非单射**」。
- **实测**：恶意 `__eq__` 的调用计数为 **0**。首轮点名的 2 个逃逸点、以及 ARCH
  轮独立复现时找到的**另外 2 个同构逃逸点**（`cfg != fresh_cfg`）全部关闭。
- **`ready()` 的 `(bool, str)` 契约现覆盖其自身函数体**（原先 **4** 个
  `Path.exists()` 探测未包护；S3 复算 `_ready_body` 确为 4 个探测目标）。
- 边界的诚实限度（写进源码，不在文档里粉饰）：`except BaseException` 会把
  `KeyboardInterrupt`/`SystemExit` 也转成拒绝；`_safe_type_name` 内另有一处
  **必需**的 try，因此"单一边界"表述为**流水线的单一边界**；
  `MappingProxyType` 的一次读取是**边界守护**而非非执行——不作"绝无外来代码
  执行"的主张。
- **该轮库内回归为 12 例具名敌意形状**（`_F1_CASES`，S3 计数核实）。当时文中
  所称"27 种"为复核员自造、**未入库、不可独立复算**，标 `FABLE/OPUS_REPORTED`。
  **更要紧的是形状而非计数**：该 12 例**全部是拒绝断言**，无一例断言
  "被接受的缓存配置必须是规范实例"——这正是 §9 的结构性根因。

### F-2-ARCH（原 F-2）证据消费 —— 处置注册表 ＋ 完备性判据（**粒度受限，未闭合**）

> **标识勘误（R2）**：本小节旧标 `C-14`。`C-*` 是 §2 **CLOSED** 表的编号，而
> §2 CLOSED 表**从无 C-14 行**，读者沿"见 §7 C-14"跳转会误判为已闭合。现统一
> 更名为 **F-2-ARCH**，§2 P-11、F-2 行与 §8 PKT-1 的交叉引用一并改写。

> **闭合范围声明（PHASE F 复核后收窄）**：以下机制在**字段粒度与元素粒度**
> 成立并经攻击验证通过；它**不覆盖元素之下的"叶"粒度**，该层的同类缺陷已
> 由复核实证复发，见 §8。本节任何表述均不构成 F-2 已闭合的主张。

- `CheckOutcome` 的 `ran`／`complete`／`not_applicable` 全为**派生属性**。
  **判据升级为 `complete = compared_count >= applicable`** —— 这是该轮车道
  **实测推翻原任务书**的结果：原定的 `ran = compared_count > 0` 挡不住
  **部分剥离**（EV-3 留 1/32、EV-7 留 1/32、EV-5 留 23/46 **全部静默封存**）。
- `FIELD_REGISTRY` 为 `CanonicalS0Evidence` 的 **22 个字段各登记恰好一种处置**
  （S3 复算：22 项，键集与 dataclass 字段集**完全相同**），每个字段的
  `applicable` 由**从不读取该字段**的权威总体推导。
- 标记集由 `_markers_from_registry` **遍历注册表**生成（而非遍历结果），
  使"写入却从未被读的 check"结构上不可能；`_run_check` 是唯一写入口；
  漏跑扫描发 `evidence_check_not_run:<id>`；`try/finally` 修好"内部错误会抹掉
  全部披露"的缺陷。（S3 复算 `CHECK_REGISTRY` == **35** 项，其中 4 项为
  `field=None` 的字节侧轨，不挂在任何 `FieldDisposition` 下——属设计如此。）
- provenance 四态分明：缺失／类型错／词表外／明确不一致，各有独立问题码，
  **缺失绝不等价于 agrees**。EV-12 现**重新导出**三方一致性并绑定三个**活的**
  `PERCENTILE_METHOD` 常量（不裁 DR-8）。
- 迭代顺序独立性：AST 审计 ＋ 4 个 `PYTHONHASHSEED` 实测，并有回归测试锁定。
- 该轮引入的**新 fail-closed 模式**（经主代理批准）：`EV-8` 对冻结 18 列 NA
  清单做硬校验——某列从 `ds.features_table` 消失属 schema 漂移，应拒绝封存。

### 一条被推翻的既有主张（如实记录）

`_reconcile_record_internals` 原 docstring 称 L137 的 `sizing_anchor_usd`
重算是"唯一必须依赖 EV-3 的重算"——对 EV-3 未覆盖的日期为**假**，且 EV-3 的
覆盖度当时无人度量。该措辞已删除；覆盖度现由注册表的权威总体强制。

### 一个跨车道疑点：现状确定，成因未经证实

Track A 曾报告封存路径疑似 `PYTHONHASHSEED` 依赖。**现状已验证**：多轮
seed 实测下有序问题列表、全部 `(check, applicable, compared_count)` 三元组、
封存集 digest 与 `partial_coverage` 逐字节相同。**成因未经证实**：先前写的
"系读到另一车道写文件的中间态"是**一个未被复现验证的解释**，原观察已无留存
工件可供追溯。结论应读作：封存路径现在是确定性的；当初为何不确定，无法从
现有证据判定。

## 8. PHASE F 独立复核结果（ARCH 轮收口）

复核由**全新只读代理**执行（未参与任何实现车道，未获任何预设结论）。
逐区判定：**F-1 PASS**（**该 PASS 已被 §9 证伪**）、**F-2 HOLD**、确定性 PASS、
治理 PASS、电池 PASS。

### F-2 复发实证（同一缺陷类，低一级粒度）

**基线锚点的时效声明（R2 更新）**：该轮诚实基线为 11 个封存文件、
`hard_problems == []`、**12 条 PARTIAL**、封存集 digest `bf7628a4b42985fb`。
**R2 轮后该 digest 已不再是锚**——标记集由 12 条增至 **17** 条（见 §9），
`HANDOFF_ADMISSION.json` 字节**按设计改变**。任何复核不得再以
`bf7628a4b42985fb` 作为"诚实运行"的判据。

下列每一项都作用于**全部**元素并经**真实 `render_s0_report`** 驱动，在
**ARCH 轮的字节上**产出的 digest、hard 数与 marker 全部与当时的诚实基线
**逐字节相同**：

1. `label_availability`：46 天的 `o1000`/`c1544`/`pm_ok`/`adr_ok`/`dir_ok`
   **全部翻转**。**最具判决性**——`EV-11` 仍判 `complete`，其专属 PARTIAL
   因而被**丢弃**：封存的 `HANDOFF_ADMISSION.json` 正面宣称了一项从未执行的覆盖。
2. `opening_ranges`：32 行的 `or_high=or_low=0.0`、`n_obs_bars=0`、`d_open=0`
   （仅 `anchor_stop` 被消费）。
3. `day_facts`：`y_cont_available`／`record_oracle_candidate`／
   `tradeable_direction` 翻转——而该字段正是给其他字段定总体的**权威**。
4. `day_facts`：`record_year`／`record_era`／`direction_status`／`is_event_day` → `"Z"`。
5. `f10_memberships`：46 个 `trade_date` 全塌成 `"ZZZ"`（互斥分区检查数元素、
   不按日身份归键——源码依据见 §2 C-6 范围块第 2 条）。
6. `grid_pools`：`tp_pools`/`fp_pools` 清空、`stratum_axes=()`、
   `grid_stream_tag=0`（仅 `*_avail` 计数被绑定）。
7–10. `bootstrap_inputs`／`cost_scenarios`／`theoretical_paths`／`day_strata`
   的多个叶被伪造（**这四项部分落在永久标记的诚实范围内**）。
11. **八族同时伪造** —— digest 仍为 `bf7628a4b42985fb`。

**未被任何标记、任何登记处置、任何硬码覆盖的是第 1、2、3、4、5、6 项。**
全量普查的报数与其证据分级见 §2 P-11「叶粒度证据分级」——**不再以
"51 个沉默叶"的单一数字表述**。

**根因（复核陈述）**：`CheckSpec.field` 指向顶层字段，`applicable` 数元素，
`compared_count` 数被消费的元素；**叶粒度没有注册表、没有完备性判据、
没有披露**，因此"某个被捕获的叶从未被任何比较读取"在结构上既可能发生、
又结构性不可见。这与上一轮 F-2 的形状相同，只是低了一级。

**闭合要求**：把注册表与完备性判据下沉到叶粒度（每个被捕获 dataclass 字段
登记处置与权威来源，或反向声明为不消费并在披露中写明），使"捕获但无人读取
的叶"要么被比较、要么被公开标记。**R2 轮 S2 已按此方向落地叶谱系矩阵与 5 个
新披露标记，但其自陈残余（121 行中 10 行无独立权威；token 完备性只证明访问、
不证明权威）说明闭合要求尚未满足。**

### ARCH 轮新增 LOW（记录）

| ID | 内容 |
|---|---|
| F1-d | `_Refusal` 快路径的 reason **未消毒**：经 `_atom_ticks` 的 mappingproxy 残留触达的外来代码可让多行载荷原样进入拒因（`BaseException` 分支已消毒）。已被 `runner._fail_pre_run` 的模板化处理围堵 |
| F1-e | 同一触发下 `resolved_study_config()` 可返回非 `str` 的 reason，违反自身注解；`ready()`／`compute()` 均 f-string 之，故公共 `(bool, str)` 契约仍成立 |
| F1-f | `_approved_injectables()` 若两次读取返回不同值，G8 校验读取 #1、`derive_study_config` 消费读取 #2；除"另一组同样合法的三元组"外，其余全部被 `StudyConfig.__post_init__` 二次拦截 |
| PKT-1 | 本 packet 曾以 C-14/C-15 指代闭合但 §2 无对应行（**R2 处置：C-15 已撤回；C-14 更名为 F-2-ARCH，不再占用 CLOSED 编号空间**） |
| PKT-2 | §7 曾写 `test_s0_evidence` "240 passed"（中途值）（**R2 现值：324，S3 复算**） |
| DOC-1 | `evidence.py::_reconcile_label_availability` 的 docstring 称比较 EV-11 的五个 IR-23 依赖布尔，实际只读 `fact.available`——**为假**。**R2 强化证据**：S3 以 AST 普查确认 `o1000`/`c1544`/`pm_ok`/`adr_ok`/`dir_ok` 五个名字在 `src/itsf/s0/evidence.py` 内、`LabelAvailabilityFact` 定义之外**零出现**，任何复核可用一次 grep 复算 |
| BAT-1 | "0 skipped" 是**实测结果**而非结构保证：`tests/test_preflight.py` 仍有 **10** 处环境条件性 `pytest.skip`（S3 复算：全库唯一含 `pytest.skip` 的文件），preflight 工件缺失时会触发。**已提升至 §0 正文单列** |

## 9. PHASE R2 —— F-1 第二次复发、其修复，与叶谱系补强（本轮）

### 9.1 F-1 的第二次复发（只读代理 S3 实证）

ARCH 轮宣告 F-1「结构性闭合（PASS）」。R2 轮的只读事实核查在**同一份网关
代码**上实证了**两条新的绕过机制**，二者均使网关交出**非规范的缓存实例**：

1. **`_atom_number` 把 `int` 转换为 `float`**（`scripts/s0_real_run.py`，
   `_atom_number`）：
   ```python
   if type(value) is int:
       ...
       value = float(value)          # 转换，而非拒绝
   ```
   后果：绕过构造的 `spread_scalars=(0, 1, 1)` 与新鲜派生的 `(0.0, 1.0, 1.0)`
   指纹**逐值相同**（实测两侧均为 `('StudyConfig', <mfp>, (0.0, 1.0, 1.0))`）。
2. **`_atom_ticks` 对可变 `dict` 与规范只读 `MappingProxyType` 归一化结果相同**：
   类型闸只写 `type(value) is not dict and type(value) is not _MProxy`，两条
   分支归一化到同一元组。后果：`contracts._canonical_ticks` 所建立的
   "validate 之后不可变"性质在网关处**不可见**——而该 docstring 自陈其存在
   理由正是"mutate-after-validate 否则只能被**下一次**重验证捕获"，
   **网关就是那次重验证**。

**端到端实证**（仅使用库内测试自身使用的两个源 seam `_resolved_methods` /
`_approved_injectables`；未运行真实 S0、未读取真实数据）：

| 植入缓存 | 网关接受？ | 交出的是植入实例？ | 后果 |
|---|---|---|---|
| `spread_scalars=(0,1,1)`（int） | **是** | **是**（`cfg is bad`） | 交出的配置携带 `['int','int','int']`，从未经 `canonical_spread_scalars` |
| `methods.spread_cost.adverse_slippage_ticks` 为活 `dict` | **是** | **是**（`cfg is bad2`） | 交出容器为 `dict`；**在门通过之后**就地修改该 dict，交出配置读到的值随之由 `1.0` 变为 `9999.0` |

**严重性（两句话，缺一不可）**：

- **今日实际暴露为零**：live `_approved_injectables()` 恒返回 `None`，缓存路径
  在 `G6_injectable_source` 拒绝（S3 以对照实测确认）。
- **但这不是"仅止于声明准确性"的缺陷**：S1 车道的**修复前**暴露测试实测
  失败于 `assert 'run_failure' == 'pre_run_attempt'` —— runner **离开了
  pre-exposure 的 Stage-B 边界并进入了 Stage C**。因此一旦 DR-1／DR-2 落裁、
  `_approved_injectables()` 开始返回真实三元组，本缺陷即为**会消耗 exposure**
  的缺陷，而非纯粹的纵深防御问题。

### 9.2 结构性根因（本轮命名，归属 S3 事实核查 B-2）

**F-1 两度在宣告闭合后复发的根因不是"漏了某个逃逸点"，而是回归测试的形状：
库内 `_F1_CASES` 的 12 例敌意形状全部断言"应当被拒绝"，没有任何一例断言
"被接受的缓存配置必须是规范实例"。** 一个只测拒绝面的回归集，在定义上无法
发现"错误地接受"这一类缺陷；两轮补丁都在拒绝面上加固，因此两轮都没有触及
接受面。此根因**记为 F-1 复发的具名结构性成因**。

### 9.3 S1 车道的修复（已就位，**但状态仍写未闭合**）

S1 以**四钉环路**关闭 9.2 的根因，四钉相互咬合、绑定到**同一张规则表**：

1. 新增规范形式字段一旦出现在 `contracts` 的规范化实现中，**两个测试同时变红**
   （`test_f1_canonical_form_tables_cover_every_contracts_canonicalization`）；
2. 修复动作是**在规则表中加一行**，而不是在网关里加一个 `if`
   （`test_f1_canonical_form_binds_to_contracts_and_defines_no_second_rule`
   钉住"网关不得定义第二套规则"）；
3. **接受面义务由该表派生**，不是手写清单
   （`test_f1_accept_side_obligations_cover_every_canonical_form_rule`）；
4. 第四钉阻止义务清单退化为空
   （`test_f1_gateway_never_hands_out_a_non_canonical_instance` /
   `test_f1_accepted_config_is_canonical_on_every_obligation`）。

代码层面新增两个拒绝阶段 `G10_methods_canonical_form` 与
`G11_config_canonical_form`。**S3 复验**：§9.1 的两条机制现分别被这两个阶段
拒绝，网关不再交出植入实例；`_approved_injectables()==None` 的对照仍在
`G6_injectable_source` 拒绝。测试增量 **+125**。

**状态仍为 `PARTIAL + ENGINEERING_REQUIRED`**。
**【时态更正 —— M6.1.6 / S3，2026-08-09】原写「两名独立复核员尚未开跑」
已过时：R1 已开跑并判 PASS，但其三条声明经 §10.4 证伪，故按 §10.6
状态不变。** 按「同类缺陷两度复发」的既定规则，**修复轮自判闭合不构成闭合**。

### 9.4 S2 车道的叶谱系补强（已就位，**状态仍写未闭合**）

新增 `M6_1_4_LEAF_LINEAGE_MATRIX.md`（121 行叶级登记，sha256
`c982f80b48c05e38b1fd24971f4def76f71788bfa20608e726c4ee23770b43fe`，S3 复算
一致）与 **5 个新的永久披露节 ＋ 1 个条件披露节**。测试增量 **+77**。

**S2 自陈残余（逐字，不得改写）**：registry↔matrix 由测试钉住，matrix↔truth
没有；token 完备性只证明某个 check **访问过**每个叶，从不证明该叶有独立
权威——**121 行中有 10 行没有独立权威**。

### 9.5 披露标记集：12 → 17（`HANDOFF_ADMISSION.json` 字节按设计改变）

诚实运行的 PARTIAL 标记由 **12** 条增至 **17** 条（S3 复算：
`tests/test_s0_evidence.py` 两处钉住 `len(markers) == 17` 与
`len(rec["partial_coverage"]) == 17`）。新增的 5 个永久节：

| 新增披露节 | 所暴露的叶级缺口 |
|---|---|
| `theoretical_oracle.favourable_extreme_ts` | 该叶无独立权威 |
| `sizing_outputs.opening_range_non_anchor_extreme` | 仅 `anchor_stop` 被消费（§8 第 2 项） |
| `structural.label_anchor_availability.dependency_booleans` | EV-11 五布尔零消费（DOC-1／§8 第 1 项） |
| `structural.label_anchor_availability.per_day_values` | EV-11 逐日值无独立重算（**待 D-4 裁决**） |
| `structural.f10_raw_membership.per_date` | f10 按日身份未归键（§8 第 5 项） |

另有 1 个**条件**披露节 `evidence.entity_axis.af1_days`（仅在其适用总体成立
时发出，故不出现在诚实基线的 17 条固定集合中）。

**因此**：`HANDOFF_ADMISSION.json` 的字节**按设计且按枚举改变**，
**`bf7628a4b42985fb` 不再是任何判据的锚点**。§8 的基线锚点声明已相应更新。

### 9.6 结算一条长期未对账的计数（原 B-4）

§6 的 F-2 条目称当时诚实运行为 **11** 条 PARTIAL，而 §7／§8 称 **12** 条，
两者从未对账，且 §7 同时声称 `partial_coverage` 字节未变——三者不可同真。
**本轮按"每个数字必须绑定其工作树"的规则结算**：

| 工作树 | 诚实运行 PARTIAL 条数 | 可复算性 |
|---|---|---|
| M6.1.4 首次收口 | 11（`FABLE/OPUS_REPORTED`） | 字节已不存在，**不可复算** |
| M6.1.4-ARCH | 12 | 字节已不存在，不可复算；库内测试 docstring 称该 12 条literal 转录自**重构前**实现 |
| **M6.1.4-R2（本轮）** | **17** | **S3 实测复算，双处钉住** |

§7 中"`partial_coverage` 字节未变"的主张，其有效范围**仅限 ARCH 轮重构的
前后两侧**，**不跨越首次收口**，也**不适用于 R2**（R2 按设计改变了字节）。

## 10. PHASE E 双独立复核结果（R2 轮）与 `M6_1_4_R2_STATUS=HOLD`

两名**未参与任何实现**的只读复核员并行执行，范围严格互斥，均未获预设结论，
均以字节恒等出场（`git diff | sha256` 进出一致：`27a5524d…4abe3b`）。

| 复核员 | 范围 | 判定 |
|---|---|---|
| R1 | F-1 规范化配置 ＋ 公共 `ready()`／`compute()` 路径 | **`R1_VERDICT=PASS`**（附三条声明更正条件；无新 Medium/High） |
| R2 | 叶注册表／token 完备性／EV-11／真实 renderer／矩阵一致性 | **`R2_VERDICT=FAIL`** |

**里程碑判定：`M6_1_4_R2_STATUS=HOLD`。不提交候选、不进入同类补丁循环、
本轮不再改动代码。**

### 10.1 R2 的决定性证据（同一缺陷类第三次复发，粒度再低一级）

诚实基线：`hard=0`，17 条 PARTIAL，121/121 叶 complete，expected==actual==**8,178** token。
下列篡改经**真实 `render_s0_report`** 驱动，产出 11 文件**逐字节相同**：

| 案例 | 篡改 | 粒度 | 注册行 | 结果 |
|---|---|---|---|---|
| **F1** | `EV-9.level_dates`：伪造 32 个 `L4_final_feature_construction_dates` 中的 14 个，并捏造全部 46 个 `side_diagnostic_complete_390_bar_rth_days` | Mapping 条目内的**元素** | `EV-9.level_dates`，`INDEPENDENT_BOUND`，**无标记** | **静默**；121 叶全 complete；封存**逐字节相同** |
| B1 | `EV-1.y_cont` 在 16 个 TP 日 +1000（θ 侧不变） | 标量叶的**值** | `EV-1.y_cont`，`INDEPENDENT_BOUND`，**无标记** | **静默**；逐字节相同 |
| B2 | 14 个非候选日 `y_cont := -99999.0`、`y_cont_available := True`（Σ 32→46） | 值 | 同上 | **静默**；逐字节相同 |
| B3 | `record_fields`：在 256 行中删除封存值为 `None` 的 `actual_stop_fill` 捕获键 | Mapping 叶内的**子键** | `TOP.record_fields`，`INDEPENDENT_BOUND`，**无标记** | **静默**；逐字节相同 |

根因：注册表止步于**叶**；叶以下（元素／子键／等价类内的值）再次**没有注册表、
没有完备性判据、没有披露**。`_reconcile_funnel` 只比较 `len(levels[k])`，
无任何检查绑定 L4 或 side-diagnostic 的**成员身份**。

### 10.2 R2 揭示的 token 机制根本缺陷（比"少一层"更重要）

1. **token 与比较解耦**：`_emit` 由每个行循环顶端的**固定名字列表**调用，
   先于且独立于任何比较。`_leaves_ev1` 为 `y_cont`／`year`／`era`／`d_open`／
   `oracle_candidate`／`trade_constructible` 各发 46 个 token 而**一个都不比较**。
   **token 证明的是"该行被访问"，不是"该叶被检查"** —— 本轮完备性主张的基础
   因此弱于其字面含义。
2. **`expected_tokens` 可被被守护叶清空**：`frozen_hash_paths` 轴由
   `evidence.frozen_hash_observation.observed` 定尺寸（实测 7→0），即**轴读取
   了它所守护的家族**；而 `test_every_leaf_entity_axis_authority_never_reads_
   its_own_leaf` 断言的是 `ENTITY_AXIS_AUTHORITIES[...].reads` 这个**注解**，
   不是行为。字段级有行为保证（清空字段后重测），**叶级没有**。
3. **形状对、含义错可通过**：`_reconcile_record_fields` 以 `_get(want, field)`
   默认 `None` 比对，**"捕获键被删除"与"捕获值为 None"不可区分**（B3）。

多重集相等本身实现正确：同数错 token、重复、错实体均被捕获。

### 10.3 R2 判定的其余各区

- **EV-11 —— PASS**：六项指定攻击（统一删键／单日删键／增键／五布尔全翻转／
  `dir_ok` 翻转／`adr_ok` 总数破坏）在 reconcile 与真实 renderer 两处**全部拒绝**，
  且两条专属 PARTIAL 在**全部 9 个 EV-11 变体**中**均在场**，无一可使其消失。
  两个静默案例（`available` 保聚合成对翻转、`adr_ok` 保总数成对翻转）**正是
  标记文本明说不可见的那两类**。研究栅栏为真：reducer 未被推导，标记点名
  `dataset.py:688-695` 未冻结 ＋ IR-23 仅部分列举。
- **`af1_days` —— PASS**：无 universe 时失败关闭（专属 PARTIAL、40 叶
  `expected=0` 且带 `skipped_reason`、**无**回退到 `len(day_facts)`）；
  universe 在场但 L3 清空则为**硬拒**（51 hard）而非回退。
- **架构 —— FAIL**：既有捕获类**新增字段**被覆盖（反射钉住 107），但**新增
  dataclass 家族**不被覆盖（测试内 `families` 字典与 9 项 `TOP.` 清单均为硬编码）；
  矩阵↔注册表的钉**很窄**——只钉 `family/leaf/disposition/entity_axis/
  key_vocab_axis/marker_section`，而**唯一陈述"到底绑定了什么"的 `authority`
  列两个方向都没钉**，且实测为假（见 10.4 第 2 条）。故该钉可在底层检查
  空转的情况下被完全满足。
- **电池 —— PASS**：`tests/test_s0_evidence.py` 324 passed / 0 failed / 0 skipped。

### 10.4 本轮被独立复核**证伪**的声明（撤回，不辩解）

R1 提出三条、R2 提出三条，全部接受：

| # | 出处 | 原声明 | 事实 |
|---|---|---|---|
| 1 | `scripts/s0_real_run.py:1537`（＋两处测试回声） | 「canonical wherever contracts specifies canonical, **exact-type-pinned everywhere else**」 | 后半句在 **tick 值**处为假：`_atom_number` 在同一槽位同时接受 `int` 与 `float` 并折叠 `-0.0`。与本 packet 自己的 E-6 矛盾 |
| 2 | `canonical_form_obligations` docstring | 「read-only and **total**: it reports, it never refuses」 | 对 `.methods` 为敌意 `__getattr__`／`None`／`int` 的配置**会抛出**。非活逃逸（仅对已接受配置调用），但"total"不成立 |
| 3 | `contracts.py:189`／`s0_real_run.py:1417`／`test_s0_config.py:989` | 「**CPython exposes no API** to reach the object behind a mappingproxy」 | **为假**：`gc.get_referents(proxy)` 即可（R1 实测）。该残留是**设计选择**，不是平台限制 |
| 4 | `evidence.py:1964-1969` ＋ 矩阵 §1 | 「10 个登记叶在任何粒度上都没有权威」 | 该措辞蕴含"其余 111 个在每个粒度上都有权威"。`EV-9.level_dates`（元素）、`EV-1.y_cont`（值）、`TOP.record_fields`（子键）都没有，且三者均为 `INDEPENDENT_BOUND` 无标记 |
| 5 | `LEAF_REGISTRY["EV-1.y_cont_available"].authority` ＋ 矩阵第 235 行 | 「population total vs EV-8 `labels.y_cont.not_na`」 | **该比较不存在**。诚实 Σ=32=EV-8 的 32；B2 把它改到 46 而**零问题产出** |
| 6 | 矩阵 §4 机制散文 | 描述了 `LeafSpec.marker_reason`、第四类残差 `wrong_axis`、逐标签叶 id（`EV-11.available.y1`）、写入口 `_emit_leaf` | 代码中**均不存在**（`LeafOutcome` 为 missing/extra/duplicate/skipped_reason；无 `marker_reason`；写入口是 `_emit`；每日只有单个 `EV-11.available.VALUE` token） |

另记 R1 的 E-6 扩展：`-0.0` 那一半比 int-vs-float **更尖锐**——将来消费者做
`float()` 归一化**修不掉**（`float(-0.0) == -0.0`），且符号位**算术活跃**
（`math.atan2(-0.0,-1)` 为 −π）；而新的接受侧义务机制对该字段**结构性失明**，
ticks 映射被接线时不会报警。

### 10.5 闭合要求（下一轮，若获授权；本轮不实施）

1. **token 必须由比较产生，而非由名字列表产生**：`_emit` 只能在一次实际比较
   完成后调用，或改为由比较函数返回 token；并加行为测试证明"发出的 token 数
   == 实际比较次数"。
2. **叶级非循环性必须行为化**：照字段级 `test_population_callables_never_read_
   the_field_they_guard` 的形态，清空被守护叶后重测轴尺寸必须不变；注解式
   `.reads` 断言不可作为证据。
3. **`authority` 列必须双向钉住**：矩阵与注册表的该列互钉，且每条 authority
   必须有一个证明其存在的行为测试（第 5 条撤回即因该列无钉而未被发现）。
4. **叶以下粒度**：为元素／子键／等价类内的值确定处置——要么绑定，要么给
   专属 PARTIAL，要么明确移出 canonical evidence。**这是第三次同类复发，
   下一轮方案应先给出"为何这次的粒度是最后一级"的论证**，而非再降一级。
5. `record_fields` 的"删除键"与"值为 None"必须可区分。
6. 新增 dataclass **家族**须与新增字段一样被反射覆盖。

### 10.6 状态

`F-1`：R1 判 PASS，但因第 1／2／3 条声明证伪，**本轮仍记 `ENGINEERING_REQUIRED`**
（待声明更正并经定向复验后方可 CLOSED）。
`F-2`：R2 判 FAIL，**`PARTIAL + ENGINEERING_REQUIRED`**，闭合要求见 10.5。
`REAL_RUN_READY=NO`、`STRATEGY_COUNCIL=LOCKED`。DR-1…DR-8 与 READY
supersession 仍是 Aaron 队列中**仅有的两组**裁决项。
