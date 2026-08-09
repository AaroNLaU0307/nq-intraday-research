# CODEX_REVIEW_PACKET_M6_1_3（M6.1.3 定向修复候选，供 Codex 独立复审）

- **baseline（上一候选）**：`712532ddd6d2276ec665eaed6db7ce270df9c544`（M6.1.2）
- **本候选 commit**：与本 packet 同 commit（单一新 commit，未 amend baseline）
- **电池**：`pytest -q -rs` → **1141 passed / 0 failed / 0 skipped**；
  collected == `MIN_COLLECTED_TESTS` == 1141（scripts/s0_real_run.py 与
  tests/test_s0_runner.py 双钉）
- **扫描**：`final_candidate_scans.py` exit 0；`guards.verify_frozen_hashes()`
  CLEAN；`git diff --check` 净
- **治理不变量**：`ops/TRIAL_REGISTRY.md` sha256
  `de63b3d690c5c4be1def67aff9e0302138e9910df5b9a89acb1db57697b0b440`、
  `EXPOSURE_LEDGER.md` sha256
  `394813431d879555b7504d2501c40123368d67a517359e056692eb6b0f6bc9e6`
  ——与 M6.1.2 基线逐字节一致；`runs/` 不存在；真实数据零读取；
  S0-T001 未消耗，无新授权申请
- **变更文件哈希（sha256，完整）**：
  - `scripts/s0_real_run.py`
    `16f75aa43dd6908b734056ae1be8b1cea051c1b6f6be685feae1dc96ed8e5546`
  - `src/itsf/contracts.py`
    `ddc2123beb6f5f6a78645b05058c19521c75f624df6d0ac0674f26be25a0bbef`
  - `src/itsf/s0/report.py`
    `13d89a7311e6ad69385d71f4f7868d606de1acc8ed4a0095d9fa27797985191e`
  - `src/itsf/s0/handoff.py`
    `b1ea761c442c3fdc7661fe4cddc694152f41c72489fc791bd9d9b9f4731409ab`
  - 其余：`DECISION_REQUIRED_M6_1.md`(r5)、
    `S0_REAL_RUN_AUTHORIZATION_PACKET.md`(§0 四行哈希重渲染)、
    `tests/test_m6_chain.py`、`tests/test_s0_report.py`、
    `tests/test_s0_handoff.py`、`tests/test_s0_runner.py`、本 packet

---

## 1. 审计方法（本轮证据从何而来）

1. **三车道并行工程**（S1 report / S2 handoff / S3 只读旧候选证据矩阵）＋
   主代理集成（reconcile 接线、配置新鲜源绑定、estimator_status 生产）。
2. **S3 证据矩阵**（git-archive 快照 712532dd，合成 fixtures）：8 缺陷类中
   **7 类在旧候选上逐字实证为活缺口**（D1 空壳准入、D2 伪造年桶、D3 假
   min/max、D5 cache 绕过且 ready()=True、D6a θ :g 格式、D6b float-seed
   集合相等、D7 无 estimator 治理、D8 准入崩溃）＋ D4 诚实已拒。
3. **盲式 Opus 对抗审计 round-1**：只给冻结规范与目标、不给已知反例清单；
   自造并实际执行 **约 130 个反例**，四边界（validator / sealed-files /
   真实 renderer / production 配置缝）分别穿透；判 **OPENS_REMAIN
   （1 High / 3 Med / 6 Low）**，并给出四条架构级根因（RC-1..RC-4）。
4. **修复轮 1**（仅首现缺陷）＋ **修复轮 2**（修复自身引入的 3 个 Low）＋
   **同一审计员定向复验：40/40 CAUGHT、零回归、字节恒等证明**。
5. 复发类 **RC-1/RC-2 按任务书未做局部修补**（同类两度复现 → 停补丁、
   出架构级根因、升级裁决）。

---

## 2. 三分栏

### CLOSED（三证齐全：生产接线＋独立重算＋反例测试）

| # | 项 | 生产接线 | 独立重算 | 反例证据 |
|---|---|---|---|---|
| C-1 | **形式层聚合防伪**：`reconcile_with_internal` 接入真实渲染器（封存前边界，传原始 compute 结果） | s0_real_run.py 渲染链 validate→**reconcile**→manifest→seal | oracle 序列/stability 各轴 vs internal 对账 | 盲审 C1/C2：同步伪造 formal 序列＋n/sum/mean/min/max 与全轴 stability——**真实 renderer 拒绝**；F8 防空转（formal-as-internal 拒） |
| C-2 | **报告 schema 矩阵＋未知键 fail-closed＋畸形树永不崩** | validate_formal_payload ×2（manifest 前后） | 13 节 `_ALLOWED_KEYS` 逐层 | 盲审 A 系列 40+ CAUGHT（root=None/True/0/set、九处 unknown-key、深层叶破坏、estimator_status 五变体、P1>P5 三处、跨种子均值漂移等） |
| C-3 | **配置唯一新鲜源绑定（缺陷类 3）**：型钉→test_only→methods 恒等→注入件源门，全部先于 ready() | `_validated_config` 使用点重验 | 每次与 `_resolved_methods()` 新读比对；注入件须来自 `_approved_injectables()`（今日 None=fail-closed） | E1-E10 全拒；**E6 假 `__eq__` 鸭型→型钉拒；F3 methods 匹配私带 scalars/callables→注入件门拒；N3 raising property→拒因而非异常；N4c 畸形 inj→拒因而非 TypeError**；复验 40/40 |
| C-4 | **第 8 字段结构门**（worst_day_estimator 类型校验；值语义仍待裁） | structural_problems() → derive/StudyConfig/`_validated_config` 三处消费 | `_str` 非空字符串门 | F4/E18/E19：''/'   '/42/{}/0/['linear']/True 七变体全拒＋合法串对照可派生 |
| C-5 | **准入批量调用＋归属单射＋stray fail-closed**（D44/F9/N1b） | 渲染器一次 `formal_seal_admission(候选全集)` → `_partition_admission` | `"{name}: "` 前缀归属；候选名禁含 `": "`；不可归属问题串抛错 | D44d：网格 {7,13,31} vs 同call假manifest {1,2,3} **跨工件检查首次在生产可达并拒**；N1b 碰撞名拒；spy 断言单次调用 |
| C-6 | **estimator 治理 fail-closed 机制**（DR-M6-H 未裁期间不可封存） | producer 发 `unresolved_DR-M6-H` → renderer `worst_day_estimator_unresolved` 拒 | 状态独立于自报旗标 | 盲审 F5/F6/A19-A23；TEST_ONLY 不可达生产（F7/E2） |
| C-7 | **A52/A56/G7**：oracle note 内容化、NA 守恒旗标-证据矛盾拒、七字段诚实计数 | report.py 两处校验；DR 文档 r5 | note 非空；conservation_ok=True 与非空 unregistered_reasons/miscounted_columns、假 conserved/per_column_ok 并存即拒 | 盲审复验 A52×3、A56×5 全 CAUGHT，untampered 对照零误报 |
| C-8 | **sealed-files 完整性 manifest**（种植/移除/改行/自排除滥用） | 渲染器逐文件 sha256＋`_ALLOWED_SELF_EXCLUDED` frozenset | manifest 完整性双向 | 盲审 B2-B7/B9 全 CAUGHT |

### PARTIAL（诚实申报：机制存在但未达全量闭合；或无生产消费者）

| # | 项 | 现状 | 已知开口（盲审实证） |
|---|---|---|---|
| P-1 | **RC-1（High）：重算锚点在被检子树内部，链未达 §10.1 原子 records** | reconcile 锚在 `internal["study"]` 聚合与 `internal["dataset"]`；records 仅数量对账 | F2/C4/C5（记录值 vs 报告）、F1（formal＋d_tp 全同步）、B8（JSONL＋双哈希同修）、A34/A46-A51（网格重算锚其自报日期与 n_tp_available）、A54/G6（F 重算读载荷自身 p）、A29/C14（bootstrap 均值仅同侪互检）、G3-G5（vol_terciles/理论oracle序列/sizing_outputs 无 internal 对应）——**均可密封**。按令未补丁，见 §3 架构裁决 |
| P-2 | **RC-2（Med）：准入重算 schema 不重算语义** | 种子/θ/词表/replay/空集诸门真实有效（D14-46 多数拒） | D1-D13（day_strata 全 schema 假件：era↔epoch 混淆、year vs 日期矛盾、THETA-NESTING 违反等 13/13 被收）、D26-D34（grid_samples 语义矛盾 8 件被收）、D39-D41（seed_manifest 语义改写被收）。按令未补丁，见 §3 |
| P-3 | 方法单源**七**字段无消费者（r5 修正计数；worst_day_estimator 今日仅翻转状态串不选估计器） | 裁决落地=写字段＋接线消费者＋mutation test 同 commit（既定规则） | — |
| P-4 | `verify_handoff_conservation` / `build_day_strata` / `build_grid_samples` 无生产调用者 | 8 胞冻结矩阵检查器存在、测试覆盖，渲染器未产此二工件（HANDOFF_ADMISSION.json 如实披露） | — |
| P-5 | `replay_status = "PARTIAL_single_stratum_only"`；SEED_MANIFEST 今日 withheld（admitted=[]） | 如实申报，非声称 CLOSED | — |
| P-6 | RC-4 半闭：结构门已加（C-4），但 `estimator_status="resolved"` 仅由 non-None 派生，未与实际所用 `percentile_estimator` 串交叉核验（盲审 G1/G2） | 待 DR-M6-H 裁决时把字段接入 PERCENTILE_METHOD 并交叉断言（裁决落地三件套的一部分） | — |

### DECISION_REQUIRED（不自行裁决；受影响车道 fail-closed）

| # | 项 | 待谁 | fail-closed 现状 |
|---|---|---|---|
| D-1 | **DR-M6-H（=DR-8）**：E2 P1/P5 估计器未批准（numpy linear 从未冻结/批准，仅工程惯例） | Aaron（八项包 r5） | 未裁期间 formal 封存被 renderer 拒绝（C-6） |
| D-2 | **RC-1 架构方案**：原子层重算改造——方向性规则「一切报告数字须可由 records 重导出」；reconcile 由 `TradePathRecord.final_pnl_per_contract` 按 trade_date 重建 d_tp/d_fp；覆盖扩至 theoretical_oracle / sizing_outputs / vol_terciles / bootstrap 均值 / 网格 per-seed 选择重放（`default_rng([master, GRID_STREAM_TAG, q_mil, r_mil])` 已有文档可重放）。建议为 **M6.1.4** 单独里程碑 | Aaron＋Codex（工程架构，非方法裁决，但按令因同类两度复现而升级） | 真实链仍零暴露（Stage B 拒、全部裁决未落、S0-T001 未耗） |
| D-3 | **RC-2 架构方案**：准入语义重算——将 builder 不变式抽为单一共享 checker 供 build_* 与 admission 共用（或准入重跑 builder 后比对）。建议并入 M6.1.4 | 同上 | DAY_STRATA/GRID_SAMPLES 今日根本不产（P-4），假件仅能来自未来的生产者 |
| D-4 | DR-1..DR-7 八项方法裁决包其余各项（r5） | Aaron | 全部 None → StudyConfig 不可派生 → Stage B 拒 |

---

## 3. 已知残洞总账（无一遗漏申报）

- RC-1 全部 guises（P-1 列举）：**今日不可利用**——生产渲染仅由
  `build_full_study_result` 的自产 payload 驱动，攻击面要求能改内存中间产物；
  但作为「审计员可密封伪造」的证明成立，故列 High 待架构闭合。
- RC-2 全部 guises（P-2 列举）：同理，今日无该二工件生产者。
- G1/G2（P-6）：estimator_status 与实际估计器串未交叉核验。
- N4b（非洞、行为钉）：StudyConfig 按**对象恒等**比较 callables 属正确
  fail-closed；未来 `_approved_injectables()` 必须每次返回**同一**可调用对象
  ——已加钉测试 `test_injectable_binding_compares_callables_by_identity`
  防后人为「修复」而弱化比较。

## 4. Codex 复审入口

1. 先读本 packet §2 三分栏与 §3 残洞账。
2. 对照盲审证据：修复轮共 13 个新反例测试（test_m6_chain 8、
   test_s0_report 2、结构门 1、其余 2 处改造断言），全部可独立重跑。
3. 复核 RC-1/RC-2 的「按令不补丁」处理是否符合 M6.1.3 任务书
   （同类复现两次 → 停止局部修补 → 架构级根因 → 升级裁决）。
4. 若接受：D-2/D-3 请给架构方案立场（M6.1.4 范围裁定权在 Aaron）。

---

## ERRATUM（2026-08-08，按 Codex M6.1.3 HOLD 裁定修正；上文原样保留）

1. **C-5 应为 PARTIAL，非 CLOSED**：生产渲染器的 admission candidates
   仅含 SEED_MANIFEST，grid↔manifest 跨工件检查在生产**不可达**——
   D44d 的"可达"证据来自合成同 call 集，不构成生产接线证明。真实
   production consumer 接线后方可 CLOSED。
2. **C-1 范围限定**：仅为 **formal-only 防篡改**（对账锚在 producer
   聚合 `study[...]` 上），不构成端到端数值真实性主张——该主张即
   RC-1，Codex 已列 ENGINEERING_REQUIRED，由 M6.1.4 处理。
3. **D-4 计数勘误**："DR-1..DR-7 八项方法裁决包其余各项"应为
   "**DR 家族共 8 个（DR-1..DR-8，DR-8=DR-M6-H）**，除 D-1 已单列外
   其余各项"。
4. **P-3 精确化**：**7 个**结构化字段无 computational consumer；
   `worst_day_estimator` 仅有 governance-status consumer（翻转
   `estimator_status` 状态串），**没有** estimator-selection consumer。
5. **D-2/D-3 归类更新**：Codex 已将 RC-1/RC-2 由 DECISION_REQUIRED
   改列 **ENGINEERING_REQUIRED**（不涉方法选择，Fable 权限内执行）；
   本 packet 写作时的归类反映当时状态，现以 Codex 裁定为准。

## ERRATUM 续（2026-08-09，M6.1.4-R2 只读事实核查；上文仍原样保留）

6. **电池数字的证据级别**：头部 `1141 passed / 0 failed / 0 skipped`
   标 `FABLE/OPUS_REPORTED`。与后续里程碑那些"工作树已消失、不可复算"
   的数字不同，**该值绑定已提交的 commit `1e188b5`**，原则上可由
   `git archive` 快照独立复算；**S3 本轮未复算**，故不标
   `S3_INDEPENDENTLY_RERUN`。当前工作树的对应值为 **2093**
   （S3 实测，见 M6.1.4 packet §0）。
7. **"0 skipped" 的性质**：与后继 packet 同——那是**本环境某次运行的
   观测值**，不是结构保证。代码事实是 `tests/test_preflight.py` 含
   **10** 处条件性 `pytest.skip`（全库唯一含 `pytest.skip` 的文件，
   S3 全库计数核实），preflight 工件缺失时会触发。
8. **§2 "CLOSED（三证齐全：生产接线＋独立重算＋反例证据）"表头的效力
   仅限本 packet**：本 packet 的 CLOSED 表确为**四列**、逐行填三腿，
   表头因此有支撑。**后继 M6.1.4 packet 把表体收缩为两列却沿用了同一
   表头**，那里的"三证齐全"缺乏支撑，已在该 packet 内撤销并改为逐行
   申报证据类型。此处记录以免读者把两处表头当作同一标准。
9. **RC-1/RC-2 的后继状态（前向指针）**：本 packet 升级出的 RC-1／RC-2
   在 M6.1.4 中演化为 **F-1（配置网关）／F-2（证据消费完备性）**。
   截至 2026-08-09，**两者均未闭合**，同列
   `PARTIAL + ENGINEERING_REQUIRED`：F-1 已**两度**在宣告闭合后复发
   （M6.1.4 packet §9.1），F-2 的叶粒度缺口经叶谱系矩阵补强后仍留
   "121 行中 10 行无独立权威"的自陈残余。本 packet §3 的"已知残洞总账"
   **不**因后续里程碑而自动缩小。

## ERRATUM 续二（2026-08-09，M6.1.6 / S3 治理更正轮；上文仍原样保留）

10. **第 6 条的"当前工作树对应值 **2093**"已被 M6.1.6 追过**：当前工作树
    值为 **2146**（`MIN_COLLECTED_TESTS` 同步为 2146，双钉于
    `scripts/s0_real_run.py:47` 与 `tests/test_s0_runner.py:867`；
    S3 于 2026-08-09 复跑实测 **2146 passed / 0 failed / 0 skipped**，
    400.21s，exit 0）。本 packet 头部的 **1141** 仍绑定已提交的 commit
    `1e188b5`，标注不变（`FABLE/OPUS_REPORTED`，原则上可由 `git archive`
    快照独立复算，**S3 仍未复算**）。
11. **第 9 条的复核时态更正**：其"截至 2026-08-09"的判断成立，但理由须
    更新——M6.1.4-R2 的**两名独立复核员已开跑**（`R1_VERDICT=PASS`
    附三条其后被证伪的声明／`R2_VERDICT=FAIL`，见 M6.1.4 packet §10），
    **M6.1.6 的独立复核员亦已开跑并判 `M6_1_6_REVIEW=PASS`**
    （四轴、6 Low、0 High/0 Medium、**轴 4 research boundary 零发现**）。
    **结论不变**：F-1 整体与 F-2 整体仍为 `PARTIAL`。任何
    "复核员尚未开跑"的措辞在本仓库内均已过时，不得再写。
12. **第 9 条引用的"121 行中 10 行无独立权威"须加限定**：该措辞本身已被
    M6.1.4-R2 的复核员 R2 实测证伪（它蕴含"其余 111 行在每个粒度上都有
    权威"，而 `EV-9.level_dates` 的元素、`EV-1.y_cont` 的值、
    `TOP.record_fields` 的子键都没有）。其载体
    `M6_1_4_LEAF_LINEAGE_MATRIX.md` 现已标为
    **`PROVISIONAL / REJECTED AS TRUTH SOURCE`**。引用时请改引
    M6.1.4 packet §10.4，**不要**再引该矩阵的 §1／§4 散文或 `authority` 列。
13. **M6.1.6 轮闭合了两个具名接缝，均**不**是 RC-1／RC-2 的整体闭合**：
    prepared **LIFECYCLE 接缝**（CLOSED）与治理 **OUTPUT-PROOF 切片**
    （`governance.*` 五键，CLOSED）。同轮登记了一条**已核实、未修**的
    高严重度项：runner 以 `Path.write_text(..., encoding="utf-8")` 且
    **无** `newline=""` 落盘，Windows 上 CRLF 转译，导致同一封存输出内
    对同一工件存在**两个摘要**（磁盘 vs 内存），10 个 `sealed_files` 中
    **9 个**不匹配。详见 `CODEX_REVIEW_PACKET_M6_1_6.md` §1／§4。
