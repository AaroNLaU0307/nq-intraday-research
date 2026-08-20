# MC → VERDICT → POST-S0 STRATEGY 主计划（自包含恢复锚）

```
MASTER_PROMPT_ID=OPUS5_MC_TO_STRATEGY_V1
PLAN_DOC_VERSION=1
BASE_HEAD=a9148f1f141b4ac421a8aa6d08f1539c315caaf9
AARON_FINAL_DECISION_AUTHORITY=YES
CODEX_ROLE=INDEPENDENT_REVIEW_AND_FINAL_ACCEPTANCE
```

本文件是**唯一恢复锚**。任何模型切换、上下文压缩或续跑，按 §1 恢复序读取仓库
记录，**不得以聊天记忆替代本文件与 registry**。本文件由主代理独占写入。

来源链：Fable 架构会议 V1 → V1.1 → V1.2（correction-only 三轮，Codex 逐轮审核）
→ Codex 综合稿 `OPUS5_MC_TO_STRATEGY_V1`（Aaron 逐字发送
`EXECUTE_OPUS5_MC_TO_STRATEGY_MASTER_V1` 启动执行）。V1/V1.1/V1.2 的旧节点编号
**已被本文件 §4 的 canonical DAG 取代**，不得再引用。

---

## 1. 恢复序（每次续跑按序读取）

1. `ops/MC_DR5_BUILD_PACKET.md` 顶部现势节（冲突时以最高编号节为准）
2. `IMPLEMENTATION_RESOLUTIONS.md` 尾部（现行 IR，含 IR-29）
3. **本文件**（DAG、节点状态、租约、停止点）
4. `ops/TRIAL_REGISTRY.md` 尾部（事件真相源，append-only）
5. 最新 sealed attestation（`ops/S0_T001_POST_RUN_ATTESTATION.md`）＋
   `EXPOSURE_LEDGER.md` 尾部

---

## 2. 基线事实

> **本表是"OPUS5 master 执行首段（N-PLAN/N01/N02）的起点"快照，非现势 HEAD。**
> 现势 HEAD 与逐节点状态见 §10 节点台账；两者冲突时**以 §10 为准**。
> 本轮（N01_N02_BOUNDARY_REPAIR）起点 HEAD=`ec55ac869aa33205ef9c30b5a00a20a02f715ae4`，
> 起点测试地板=3118。

| 项 | 值（首段起点） |
|---|---|
| HEAD | `a9148f1f141b4ac421a8aa6d08f1539c315caaf9` |
| 工作树 | clean（0 porcelain） |
| tags | 恰两枚：`mc-freeze-v1`、`s0-freeze-v1`（无漂移） |
| registry sha256 前缀 | `ee9da33f` |
| exposure sha256 前缀 | `382182bf`；累计 researcher exposure=1575 |
| S0-T001 封存 | 14 文件，run==archive 逐字节全等 |
| attestation sha256 | `d839b965…41805`（== 代码 pin `ATTESTATION_SHA256_PINNED`） |
| 测试地板 | `MIN_COLLECTED_TESTS=2761`（首段起点值；N01 已重钉 3118，见 §10） |
| MC_EXECUTED / SUPPLEMENT_EXECUTED / STRATEGY_BUILD_STARTED | NO / NO / NO |
| S0 verdict 现势 | `INCONCLUSIVE_PENDING_MC`；`RECOMMENDATION=HOLD_FOR_SPECIFIC_MISSING_EVIDENCE` |
| M 轴 | IR-29a：有限穷尽支撑豁免加倍；`DOUBLING_AXES={B,K}` |
| GRID | IR-29b：Option B；supplement `MC-DS-S001` 工具已建、**未执行**、默认拒绝 |
| feasibility | `gate_status=DECISION_REQUIRED`；`CHECKPOINT0_VERDICT_REACHABLE=NO` |

---

## 3. 全局不可违反边界（PHASE B 转录）

1. S0-T001 全部 sealed run/archive 字节**永久只读**；每节点前后复核哈希。
2. 未经具名授权不读真实 Development 数据、封存结果值或 MC outcome。
3. synthetic-only 节点不得触碰真实 ruled roots。
4. registry / exposure / supplement ledger 均 append-only，**只允许主代理单写**。
5. 不填授权模板占位符，不代 Aaron 决定方法。
6. 不选择 feasibility、K、fixed-world、day-universe、Round-4 Primary 或策略参数。
7. 不把推荐值写成已批准值。
8. 不生成 READY / RUN_AUTHORIZED / RUN_STARTED / COMPLETED / verdict 事件，
   除非到达对应节点**并**获得精确授权。
9. 每节点一个 commit，不 amend，不覆盖历史。
10. 每节点最多一轮修复；仍有 High/Medium 或同类反复即停。
11. 测试不得 skip；权限/环境不足必须硬失败并披露。
12. Fable/Opus 做纯工程节点；**Aaron 决定方法、运行与揭盲**；Codex 独立审查，
    不能替 Aaron 授权。
13. 任何真实运行每次都需 Aaron 独立、精确、绑定完整 40 位 commit 的授权。
14. GO 不自动授权策略 build、真实研究或部署。

---

## 4. Canonical DAG（取代 V1/V1.1/V1.2 旧编号）

| 节点 | 依赖 | 内容 | 权限 | 数据面 | 状态 |
|---|---|---|---|---|---|
| N-PLAN | — | 本文件＋doc-only commit | 工程 | none | **DONE** |
| N01 | — | 统一原子＋冷重放（PHASE D 除 D5） | 工程 | synthetic | **LANDED_WITH_BOUNDARY_REPAIR** |
| N02 | — | 平台权威事件（D5） | 工程＋Codex 验收 | synthetic | **LANDED_WITH_BOUNDARY_REPAIR** |
| N01_N02_BOUNDARY_REPAIR | N01,N02 | C1 records custody／C2 qualifying ⟺／C3 E2 pending 消费闸／C4 生产链严格验证／C5 percentile 位兼容／C6 day-universe 等式／C7 格式与文档 | 工程 | synthetic | 见 §10 |
| N00 | — | Round-4 权威文本入库＋三状态裁定 | **Aaron** | none | **BLOCKED_ON_AARON** |
| N-D1 | — | 决策批 1（七项，见 §5） | **Aaron** | none | **BLOCKED_ON_AARON** |
| N03 | N-D1 | supplement authority 加固（C3 四层绑定） | 工程 | none | — |
| N04 | N03 | supplement runner（默认拒绝） | 工程 | none | — |
| N05 | N-D1 | supplement grammar（仅获批批 1） | 工程 | none | — |
| N06 | N01–N05 | Codex R3 exact-tree 审查 | **Codex** | none | — |
| N-D2 | N06 | 决策批 2（方法，见 §5） | **Aaron** | none | — |
| N07 | N-D2 | feasibility 实现（仅已裁形态）＋历史文档勘误 | 工程 | none | — |
| N08 | N06 | 延后审计窗口（9/12 簇） | 工程 | none | — |
| N09 | N04,N05,N06,N-D1＋**Aaron P2 精确授权** | MC-DS-S001 执行封存 | **Aaron** | structural | — |
| N10 | N09 | 独立验证＋attestation＋pin（两 commit 序列） | 工程＋**Codex** | structural | — |
| N11 | N07,N10 | GRID/K 接线（GridReplayAuthority＋KReplayEvidence） | 工程 | structural | — |
| N-D3 | N-D2 | 决策批 3（MC 治理＋α/β 状态机，见 §5） | **Aaron** | none | — |
| N12 | N-D3 | MC registry/parser 批 2（仅获批语法） | 工程 | none | — |
| N13 | N11,N-D3,N12 | 完整 MC runner | 工程 | none | — |
| N14 | N13 | Codex exact-tree MC 审查（**不追加 READY、不授权**） | **Codex** | none | — |
| N15 | N14 PASS | READY 未提交模式（见 §6） | 工程 | none | — |
| N16 | N15＋**Aaron 精确授权** | 真实 MC＋盲式收口 | **Aaron** | outcome（封存不读） | — |
| N17 | N16＋**Aaron 揭盲口令** | 揭盲与终局（见 §7） | **Aaron** | outcome | — |
| N18-C | N17∈{GO,β→GO,α→GO}＋N00＋Aaron freeze＋build 口令 | S0 continuation | **Aaron** | 分阶段 | — |
| N18-I | S0/MC 终局（任意类别）＋N00＋**Aaron 明确批准** | 独立新假设（**不要求 GO**） | **Aaron** | 分阶段 | — |
| N19 | N18-C/I | 策略 build 与未来运行（每次运行单独授权） | **Aaron**／Codex 终审 | 分阶段 | — |

**本次执行允许的最大连续范围**：`N-PLAN → N01 → N02`，同时**准备**（不裁定）
N00 与 N-D1 决策包，随后**强制停止**。

---

## 5. 未决决策清单（Aaron 专属；未裁前相关节点 fail-closed）

### N00 — Round-4 权威文本
Aaron 提供 sealed proposal 原文 → 逐字转录 → hash → 冻结 → 分别裁定：
`PRIMARY_SELECTED=` / `HYPOTHESIS_SELECTED=` / `DESIGN_WRAPPER_APPROVED=`。
**已知冲突（本轮无法仲裁，留 N00 裁决）**：Aaron 提示词曾述"不重新选择
Round-4 已锁定的策略 Primary"，而 Codex 审核述 `PRIMARY_SELECTED=NO`。
在权威文本入库前，一切规划按**最弱读法（未选择）**执行；仓库内只有
`STRATEGY_COUNCIL=LOCKED` 令牌、无权威文本（已核实）。N00 完成前禁止任何
candidate-specific 策略代码；两候选不得被模糊记成一个 raw variant。

### N-D1 — 决策批 1（阻断 N03/N04/N05/N09）

> **已移除的原第 1 项（supplement day-universe A/B/C 三选一＋计数探针）**：经
> producer 侧核实，它不是方法选择而是**生产强制的工程等式**——
> `is_direction_tradeable ≡ oracle_candidate`（study.py:335-343）；`_partition`
> 在 tradeable 上按 `y_cont≥θ`/`<θ` 穷尽二分、无第三桶（:346-355）；records 对
> 每个 engine×scenario 遍历同一 `usable`（:663-671）；每 θ 的 tp/fp 都过滤到同一
> `traded_set`（:697-699）＋守恒布尔（:715-716）。故
> `ref_dates = traded_set = 每θ(tp∪fp)` 且跨 θ 恒等，A/B/C 命名的是**同一集合**，
> 计数探针不需要。该等式改由 consumer 在 prepare 阶段强制（C6），违反＝
> sealed-input integrity failure，fail-closed，不得"改选另一个 universe 继续"。
> 此项**不再需要 Aaron 裁定**，也不产生任何 exposure 决策。

1. supplement registry 批 1 事件词汇／字段／状态转移（含 P2/P4/P6 行模板、
   失败族语义、S001→S002 id 转移事件——完整候选见决策包）。
2. MC-DS-S001 是否 formal trial（**开放，未预填**）。
3. MC-DS `STARTED` 消耗何种序列、post-start failure 与重试记账。
4. supplement ledger 形态／exposure quantity 口径。
5. output root 与 `supplements\` 创建授权。
6. late-after-reveal 显著披露措辞与落点。
7. 后续精确执行授权语句的边界。

### N-D2 — 决策批 2（方法；须落 MC1.x Addendum／Evidence Resolution，非仅纪要）
- **feasibility 三门分别定义**：payout 门（平台 payout/cycle 原子；量词；截尾
  周期处理）／frequency 门（**锚定 S0 §10.5 冻结频率输出**：延续事件基础率 p、
  年可交易日数、Oracle 月均频率；`days_profit_ge_150` **不得冒充** frequency）／
  integer-position 门（n=0 skip；offered/executed 定义；量词与阈值）。
  Wilson、0.5/0.75/0.50、三门 AND、场景归属**全部待裁**；任何 proxy 裁定前
  只报告、不进 GO。
- **K 收敛**：K-dependent 分类对象；positive/deployable region 角色；exact region
  equality 是 kill 还是报告；cell 关键分位键集；rule-(c) 是否移植至 cell；
  K/2K×seeds 与 B doubling×seeds 量词；cross-seed region 规则。
  **禁止**调用不消费 K 的 Checkpoint category 两次来伪造收敛。
- 其他：θ0.3 完整报告规模；IR-28c 真实重放 vs 近似；**fixed-world 选择**
  （单个预注册 world／P5-P50-P95 邻近集合／不选而报告全部 world 条件切片）；
  late-phase bias 披露；历史 feasibility 文档勘误批准。
- **N01/N02 执行中新发现（2026-08-15 追加，五项；后两项为边界修复轮登记）**：
  1. **E2 `over_budget` 谓词未定义**。冻结文本（MC §3/§6）**要求披露**
     `P(realised_loss > 预算)` 与 `P(intraday_adverse_loss > 预算)`，却从未定义
     per-day 布尔指哪一个、损失基准（每合约 vs 仓位）、预算基准（policy budget
     vs n×anchor）。两条车道均拒绝发射布尔，改发类型化 `PENDING_RULING`；
     `AccountEvent` 在 `OVER_BUDGET_PREDICATE_RULED is False` 期间**拒绝携带布尔**，
     故无人能私自发明该谓词。Aaron 裁定谓词后方可翻转该常量。
  2. **冻结层-1 会计确认缺陷**。MC §4.4 层-1 `strategy_account_EV`＝"平台内交易
     净损益"，但 Lucid 生命周期通过评估阶段时会丢弃评估期利润（实测：两个 +1500
     日报为 0.0，权威和 3000.0）。**影响范围已机械钉死**：Checkpoint-0 判定用
     `prop_operating_EV`（S0 §10.5 L233），其公式 `payout_cash + terminal_cash −
     fees` 不以层-1 为输入，故缺陷**够不到判定统计量**（见
     `tests/test_mc_node_integration.py::test_checkpoint0_statistic_is_insulated
     _from_layer1_accounting`）。改冻结层的数字属 Aaron 裁定；本轮未改，权威累加器
     与旧口径并存以使差额可测。
  3. **mean/SD/SE 数值实现待追认**（N01 引入，边界修复轮登记，未裁）：
     ```
     MEAN_SD_SE_NUMERICAL_IMPLEMENTATION_STATUS=PENDING_AARON_RATIFICATION
     ESTIMATOR_FAMILY_UNCHANGED=YES
     ULP_LEVEL_BEHAVIOR_CHANGED_FROM_R2_3=YES
     MC_RUN_AUTHORIZED=NO
     ```
     事实：N01 把统计核整体从 numpy 迁至规范化纯 float（为使独立 cold reducer 可
     逐位复核）。实测非逐位率 `mean_of` vs `np.mean` 47.8%、`sample_sd` 33.2%、
     `stderr_of` 30.6%，全部 ULP 级（max_rel ≤ 1.7e-12），**估计量族未变**。
     percentile 已在边界修复轮恢复 NumPy-linear 逐位行为（双分支求值序，两套实现
     各自独立复刻），故不在此项内。**结构性事实**：mean/SD 的 numpy 位兼容
     *诚实不可达*——numpy 的 pairwise 求和序是非契约的内部实现，无法写成两份独立
     实现都能复现的书面规范；故"完整恢复 R2.3 位连续性"任何方案都做不到。
     生产规模从未执行 ⇒ 无任何已封存数字被改变。裁定归 Aaron（追认或另定）。
  4. **C1 custody 链的生产规模开销**（边界修复轮引入，实测外推，**非方法裁定**
     但影响真实 MC 的可行性预算，须 Aaron/Codex 知悉）：records 现由 custody
     校验过的 handoff 字节确定，冷重放**重新解析**而非复用调用方对象。实测
     synthetic 三档外推到生产（8 个 `MC_HANDOFF_*` 合计 91.6 MB，取自封存
     attestation 的 size 表）：新增常驻 **+91.6 MB/prepared**（只留 handoff 字节，
     刻意不留 349 MB 的 `S0_REPORT.json`）；一次全量重解析 ≈ **8 s**、一次
     records 规范摘要 ≈ **24 s**（流式灌 hash，峰值仅 6–12 KB）；一次
     `cold_replay_observation_set` = 4 次全量解析 + ~7 次摘要 ≈ **2.5–3.5 分钟**；
     40 个 observation set ⇒ **约 100–140 分钟纯 custody 开销**；重放峰值内存
     ≈ **0.9 GB**（修复前 ≈ 0.28 GB）。**未做缓存**——缓存会破坏 "cold" 语义。
     若需压缩开销，安全方向是按文件切分 records 摘要以支持增量验证，
     **而不是跳过重解析**。是否接受该预算、或要求增量方案，归 Aaron/Codex。
  5. **生产规模从未被执行过**（诚实披露，非本轮造成）。全部逻辑测试在 B=2/M=2；
     任何只在 B=1000 或 M=21 显形的缺陷（浮点累加顺序、type-7 分位边界、
     内存/耗时）在本仓库任何地方都未被执行。注意 R2.3 的"生产规模"夹具是用
     已删除的 `from_world_means` **伪造的摘要**，同样从未真跑——本轮把这条缺口
     从"被掩盖"变为"显式"。是否要求一次生产规模冒烟运行（及其算力/授权口径）
     归 Aaron。

### N-D3 — 决策批 3（MC 治理；须先于 MC parser 与完整 runner）
1. MC 批 2 事件词表／字段／状态转移／授权句式；2. MC-R001 formal-trial 地位；
3. `MC_RUN_STARTED` 消耗的 run/exposure 序列；4. pre-start 与 post-start failure；
5. post-start failure 是否必须用 MC-R002；6. retry／incident／id 不复用；
7. α 的唯一检查对象、量词与门槛；8. β 的唯一替代结构集合、量词与门槛；
9. α/β 是否随主 MC 预计算并分别盲封；10. primary 先揭盲、只揭示实际触发分支，
未触发分支保持不可见；11. α/β exposure／manifest／终局事件；
12. READY 未提交事件模式在 MC registry 中的精确复用。

---

## 6. READY 未提交模式（N15，S0-T001 实史模式）

```
READY_APPEND=UNCOMMITTED
HEAD_UNCHANGED=YES
DIRTY_ALLOWLIST=ops/TRIAL_REGISTRY.md_ONLY
N15_REVIEW=REGISTRY_CHAIN_REVIEW_ON_SAME_REVIEWED_HEAD
POST_RUN_CLOSEOUT_COMMIT=PERSISTS_EVENTS
```

READY 追加**不 commit**，HEAD 停在 N14 Codex 审过的 exact HEAD；授权绑定同一
HEAD；事件由 N16 盲式收口 commit 持久化。禁止 reset／checkout／覆盖或丢失未提交
事件；崩溃时保留并转人工恢复。（"commit READY→新 HEAD→重审"已否决：多耗一轮
Codex 且正是当年 `RUN_AUTHORIZATION_SUPERSEDED` 教训形态。）

---

## 7. 揭盲与终局顺序（N17）

1. sealed manifest／exposure manifest 先行提交；2. primary verdict 揭盲；
3. exposure ledger；4. GO/STOP 直接终局；5. α/β 仅揭示已预封的对应分支；
6. 未触发分支保持不可见；7. 同一主门槛强制一次判决；8. append-only 终局事件；
9. 禁止降门槛或二次选择。
（步 5–6 预设 N-D3 第 9 项裁为 YES；若裁 NO，揭盲序按裁定重导。）

---

## 8. 文件租约（PHASE C）

| 车道 | 独占文件 |
|---|---|
| **S1**（统一原子与证据） | 新 atoms/evidence 模块；`src/itsf/mc/consumer.py`；其新建测试文件 |
| **S2**（平台权威事件） | `src/itsf/contracts.py`；`src/itsf/mc/orchestrator.py`；`src/itsf/mc/platforms/*`；其新建平台事件测试 |
| **主代理** | `ops/*`（计划／packet／决策包）；集成测试；registry/ledger；floor pins；最终提交；**既有 MC 测试电池的迁移**（`tests/test_mc_consumer.py`、`tests/test_mc_convergence_provenance.py`、`tests/test_mc_r2_2_integration.py`、`tests/test_mc_r2_3_evidence.py`、`tests/test_mc_day_strata_supplement.py`、`tests/test_s0_runner.py`） |

车道文件只能由**原车道 follow-up** 修改；主代理不得直接改车道文件。车道限额
耗尽须明确披露后串行回退。共享测试缓存／真实输出根／registry／生成文件的检查
**禁止并行**。

---

## 9. 停止点（PHASE H）

- 本次执行止于 N01、N02 完成＋N00/N-D1 决策包呈交。
- 任何真实数据需求、方法选择、运行、揭盲或新增 trial → 停回 Aaron。
- 任何 High/Medium 未清零不得进入下一运行节点。
- Codex HOLD 不自动无限修复；保留候选并回 Aaron。
- 每次停止按 PHASE I 固定报告格式汇报。

---

## 10. 节点状态台账（append-only；每节点完成后追加一行）

| 时间 | 节点 | commit | 全套件 | 备注 |
|---|---|---|---|---|
| 2026-08-15 | N-PLAN | `ba7fa4a` | 未跑（doc-only） | 主计划落盘；DAG 与租约冻结 |
| 2026-08-15 | N02 | `314a2a5` | 见 N01 终态树 | 平台权威日事实（7 字段／7 代边界／三态 qualifying_day／over_budget 类型化缺席）；EV 台账逐值不变；58 新测试。孤立态绿由车道实测（主代理实测的是终态树） |
| 2026-08-15 | N01 | `9a09164` | **3118 / 0 / 0**（822s，终态树，主代理实测） | 统一原子＋冷重放门＋config digest＋B×M 键集＋迹派生 M 证书＋双 reducer；含唯一一轮修复（类型严格比对／空集拒绝／fail-closed 词汇）；48 项迁移零弱化＋57 变异全命中；floor 2761→3118 双 pin |
| 2026-08-15 | 决策包 | 本 commit | 未跑（doc-only） | N00＋N-D1 决策包；主计划 N-D2 追加三项；packet §14 现势节。**执行段到此强制停止** |
| 2026-08-15 | N02_BOUNDARY_REPAIR | `a34b975` | 未单独实测（地板 pin 3118） | 双向 qualifying 规则＋严格 stream verifier（车道 S2 后继） |
| 2026-08-15 | N01_BOUNDARY_REPAIR | `54798c4` | 未单独实测（地板 pin 3118） | records custody 链、E2 pending 闸、percentile 位兼容（车道 S1 后继） |
| 2026-08-15 | 集成电池＋治理现势 | `54ab7f2` | 地板 pin 3118→3323 | 主代理集成电池；边界修复轮收口 |
| 2026-08-20 | B-PROV custody provenance | `b3ac453` | 3336/0/0（builder 自陈；本轮机械核到地板 pin=3336） | custody provenance 穿过电池并在 seal 处重验 |
| 2026-08-20 | FACTORY_BOUNDARY | `c5c819b` | 3380/0/0（builder 自陈＋Stage I 转录；本轮机械核到地板 pin=3380） | battery receipt 令 direct construction／replace 不再 seal-admissible；**Stage I=PASS** |
| 2026-08-20 | 治理文档收口 | 本节所在 commit | 未跑全套（doc-only） | Stage I 持久化记录＋三份规划/决策文档现势勘误；**执行段仍强制停止** |

---

## 11. `CURRENT_RECOVERY_ANCHOR_AFTER_FACTORY_STAGE_I`（现势恢复锚；本节编号最高，与上文冲突处以本节为准）

> 本节**只追加**。§1–§10 全部保留原样，未删除、未改写。§2 基线表仍是
> "首段起点快照"，**不是**现势 HEAD；现势 HEAD 见下表。

### 11.1 commit 锚（40 位全长，机械取自 `git rev-parse`，非凭记忆）

| 角色 | 完整 commit |
|---|---|
| R2.3 工程基线（本计划 `BASE_HEAD`） | `a9148f1f141b4ac421a8aa6d08f1539c315caaf9` |
| 进入 factory-boundary 修复前的后续候选 | `54ab7f28a068a26d71fe0baf5348a7924d9f83d7` |
| provenance 封印修复（B-PROV） | `b3ac4534486f607242f5758cecbc918cbe2157be` |
| factory-boundary 修复＋Stage I PASS | `c5c819beb5c13e52bcd7ca974a4e40787684b10f` |

祖先链（`git log a9148f1..c5c819b`，机械核实）：
`a9148f1 → ba7fa4a → 314a2a5 → 9a09164 → ec55ac8 → a34b975 → 54798c4 →
54ab7f2 → b3ac453 → c5c819b`。`b3ac453..c5c819b` 恰为 1 个 commit。

### 11.2 测试证据（含证据等级披露）

```
a9148f1_TEST_FLOOR=2761
54ab7f2_TEST_FLOOR=3323
b3ac453_TEST_FLOOR=3336
c5c819b_TEST_FLOOR=3380
b3ac453_FULL_SUITE=3336/0/0
c5c819b_FULL_SUITE=3380/0/0
c5c819b_STAGE_I=PASS
```

**证据等级（不得跳过）**：四个 `_TEST_FLOOR` 是本轮在各 commit 上机械读取
`scripts/s0_real_run.py:56` 与 `tests/test_s0_runner.py:1011` 双 pin 得到的，
两处逐 commit 一致。两个 `_FULL_SUITE` 是 **builder 自陈**（回执 §5）与
**Stage I 转录**（`ops/MC_FACTORY_BOUNDARY_STAGE_I.md` §2）共同承载的实跑数字，
本轮**未重跑**（本轮禁止改生产代码，重跑不产生新信息）；机械可核的只是
"该 commit 的地板常量等于该数字"。二者不冲突，但**不是同一等级的证据**。

`c5c819b_STAGE_I=PASS` 的完整语义、独立性逐维声明与效力边界见
`ops/MC_FACTORY_BOUNDARY_STAGE_I.md`——该记录为**转录件**，原始报告字节
未归档（`ORIGINAL_REPORT_BYTES_ARCHIVED=NO`）。

与 §2 首段起点表的差异**不是矛盾**：§2 记录的是 `a9148f1` 时刻的快照
（地板 2761），§10 已记 N01 重钉 3118，本节续记 3323→3336→3380。

### 11.3 现势节点状态

```
N01=ENGINEERING_COMPLETE
N02=ENGINEERING_COMPLETE
FACTORY_BOUNDARY=STAGE_I_PASS
N00=BLOCKED_MISSING_AUTHORITY_ARTIFACTS_AND_AARON_STATE_RULING
N-D1=PROPOSED_AWAITING_AARON_RATIFICATION
N03=NOT_STARTED
N04=NOT_STARTED
N05=NOT_STARTED
MC_EXECUTED=NO
SUPPLEMENT_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO
```

同时不变（本轮零改动）：

```
REGISTRY_SHA256=ee9da33f…（相对 b3ac453 逐字不变）
EXPOSURE_SHA256=382182bf…（累计 researcher exposure=1575 不变）
ATTESTATION_SHA256=d839b965…41805（== 代码 pin）
SEALED_S0_T001=14 文件，run==archive 逐字节全等
SUPPLEMENTS_DIRECTORIES_EXIST=NO
NEW_RUN_AUTHORIZATION=NONE
CHECKPOINT0_VERDICT_REACHABLE=NO
S0_VERDICT=INCONCLUSIVE_PENDING_MC
```

### 11.4 N00 的两层区分（**关键，勿合并**）

Aaron 对三个 N00 字段的裁决**只能确定状态**，不能替代缺失的候选定义与矩阵正文：

```
N00_STATE_RULING_SETTLES=WHETHER_PRIMARY/HYPOTHESIS/WRAPPER_WERE_SELECTED
N00_STATE_RULING_DOES_NOT_SUPPLY=ROUND4_MATRIX_TEXT_OR_CANDIDATE_DEFINITIONS
```

即使三字段全部裁为 `YES`，在下列五项全部恢复入库之前，**不得开始任何
candidate-specific strategy build**：

1. 完整 Round-4 联合矩阵正文；
2. `Fable continuation` 候选的正式定义；
3. `Sol failed-break/recapture` 候选的正式定义；
4. 双方逐格签字或等价的联合锁定证据；
5. Option C／其他 wrapper 的正式定义，及其 Aaron 状态裁决的来源。

清单化形式见 `ops/DECISION_PACKET_N00_AND_ND1.md` 的
`N00_MISSING_AUTHORITY_CHECKLIST`。仓库内至今**只有** `STRATEGY_COUNCIL=LOCKED`
一类状态令牌，无足以实现候选的权威正文（本轮再次机械核实）。

### 11.5 恢复序补丁（§1 的现势读法）

§1 的五步恢复序不变，但第 1 步与第 3 步现应读作：

1. `ops/MC_DR5_BUILD_PACKET.md` 最高编号现势节（现为 **§15**）
3. 本文件最高编号节（现为 **§11**）＋`ops/MC_FACTORY_BOUNDARY_STAGE_I.md`

### 11.6 停止点（未变更）

本轮为纯治理文档轮：新增 Stage I 持久化记录＋三份文档现势勘误，形成一个
commit。**未**开始 N03/N04/N05，**未**执行 MC／supplement／策略研究，
**未**产生任何 registry／exposure／READY／授权／运行事件，**未**创建任何
输出目录或探针。下一步取决于 Aaron 对 N00 三字段与 N-D1 全部选项的逐字批准；
在此之前全部相关节点 fail-closed。


---

## 12. `CURRENT_RECOVERY_ANCHOR_AFTER_ND1_RATIFICATION`（现势恢复锚；本节编号最高，与上文冲突处以本节为准）

> 本节**只追加**。§1–§11 一字未删、未改写。§11 仍是 factory-boundary Stage I
> 之后的锚；本节续承 N-D1 批准与 N03/N04/N05 工程段。

### 12.1 Aaron 的 N-D1 裁决（已生效）

```
ND1_PROFILE_RATIFIED=YES
APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R1
APPROVED_PROFILE_SHA256=0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5
APPROVAL_BINDS_DOC_HEAD=803d99162d0a018ae5a3b44273601d98d9439d50
RATIFICATION_RECORD=ops/ND1_PROFILE_RATIFICATION.md
```

批准的是**语法与治理定义**，不是任何一次执行（记录 §4 逐条列出八个 `=NO`）。

### 12.2 本段 commit 链（40 位全长，机械取自 git）

| 角色 | commit |
|---|---|
| N-D1 ratification record（doc-only） | `652ce301eecf115451ef9225e242478bb03e560e` |
| N04 runner ＋ 共享 contract | `a963199bfd4995ffbf81a6cdc61117df37864029` |
| N03 supplement authority | `f7aab7331354acdc9c09da355899a33818c20266` |
| N05 registry grammar/parser | `de3b6c61a754f9e28169f2cf45d39cc873a22dc7` |

### 12.3 现势节点状态

```
N00=BLOCKED_MISSING_AUTHORITY_ARTIFACTS_AND_AARON_STATE_RULING
N-D1=RATIFIED（profile R1）
N03=IMPLEMENTED
N04=IMPLEMENTED_DEFAULT_REFUSE
N05=IMPLEMENTED
N06=AWAITING_FRESH_SOL_EXACT_TREE_VERIFICATION
N-D2=NOT_STARTED
N09=BLOCKED（另需 Aaron P2 精确授权）
P6_IMPLEMENTED=NO（归 N-D3）
MC_EXECUTED=NO
SUPPLEMENT_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO
REGISTRY_EVENTS_APPENDED=NO
EXPOSURE_EVENTS_APPENDED=NO
REAL_DIRECTORIES_CREATED=NO
REAL_DATA_READ=NO
CHECKPOINT0_VERDICT_REACHABLE=NO
S0_VERDICT=INCONCLUSIVE_PENDING_MC
```

不变（本段零改动）：registry `ee9da33f…`、exposure `382182bf…`
（累计 1575）、attestation `d839b965…41805`、S0-T001 封存 14 文件
run==archive 全等、两个 `supplements\` 目录仍不存在。

### 12.4 交给 N06（fresh Sol）的已披露残留

1. **builder 边界未闭合**：N03 关的是 `build_day_strata_supplement` 两个
   决定性参数的**来源**，不是 builder 本身——手搭 `(expected_day_set,
   binding)` 仍可造出合法 supplement。形态同 `c5c819b` 修掉的
   factory-boundary 缺陷（construction 公开、只关 seal admissibility）。
   当前无生产 caller，故不可达；已用两条 invariant 钉住
   （`tests/test_mc_supplement_integration.py` §6）。硬化方向＝让 builder
   要求一个 authority，属受审代码改动，本轮未做。
2. **TP∩FP 在 authority 投影内结构性不可达**：`traded_day_sets` 只存每 θ 的
   TP（`consumer.py:1209`），FP 由 population − TP 派生。检查保留并做了源码
   钉；disjointness 在 overlap 真能存在的那一层（prepare 电池
   `tp_fp_overlap`）测试。
3. **同数换日无专属码**：现落在 `fp_day_without_record`。测试先断言计数相等
   再断言该码，故"仅计数检查会漏"是被证明的。
4. **N05 两个 guard 级码不可经 registry 文本到达**
   （`multiple_live_p2_after_p2s`、`p3_without_live_p2`），按 guard 测试。
5. **N05 若干派生规则**（F3 bracket id 须等于 `superseded_supplement_id`；
   T1 bracket id 开启后继链；P5 记录失败验证即拒；P5/F2v actor 不得是产出
   会话；live P2 被其 P3 消费）——packet 蕴含但未逐字写明，待 N06 复核。
6. **§D.3.2 两处 predecessor/successor 不对称**（P3 缺 A1 后继、P3 缺 F1
   前置），按"二对一"读法实现并在声明处记录，待 Aaron 裁定是否回改文档。

### 12.5 停止点

本段止于工程候选。**不得**开始 N09、N-D2、MC 或策略 build；每一次真实执行
仍需 Aaron 单独的、绑定完整 40 位 commit 的精确授权语句。


---

## 13. `CURRENT_ANCHOR_AFTER_N06_HOLD_REPAIR`（现势恢复锚；本节编号最高，与上文冲突处以本节为准）

> 只追加。§1–§12 一字未删、未改写。

### 13.1 本轮性质

fresh Sol 的 N06 exact-tree 审查判 **HOLD**，列出工程缺陷。本轮**只修复这些
缺陷、补负向电池、并生成 correction-only 的 `ND1_RECOMMENDED_PROFILE_R2`
提案**。本轮**不是**验收：N06 仍未通过。

```
N06_STATUS=HOLD_REPAIRED_AWAITING_FRESH_SOL_STAGE_I
N06_FINAL_PASS=NO
```

### 13.2 修复的四条接缝（红证与对照见 `ops/N06_HOLD_RED_PROOF.md`）

1. **N03→N04 接缝原本是反的**：手工伪造 authority 通过全部 `B_DERIVE`，而
   **真实** authority 被拒（gate 读 `file_sha256_digest`，真实对象暴露
   `bundle_table_digest`）。现在 `B_DERIVE` 检查**类型**、携带同源
   `PreparedMCInput`、调用 `verify_supplement_authority`，并对 bundle 摘要与
   day-universe 恒等式**重新计算**而非读取自述。
2. **builder/seal factory boundary 未闭合**：手工 `(expected_day_set,
   binding)` 可造出并封存 supplement。新增 `src/itsf/mc/supplement_production.py`
   作为**唯一**生产路径：两个决定性参数由 authority 内部派生、调用方传入即拒；
   产物携带 `init=False` 的 capability-minted receipt；生产 seal 拒绝 Mapping、
   拒绝无 receipt 产物、拒绝不描述该 payload 的 receipt。hermetic 核心改名为
   `build_day_strata_supplement_test_only` / `seal_supplement_test_only`。
3. **output-root 未绑定**：P2 授权的 `output_root` 与实际 `runs_root` 不同、
   或为相对路径，旧版都接受。现在 gate 做**规范化后精确比较**；新增纯
   `plan_supplement_paths` 规划器，按已批准的 `<supplement_id>_<UTC>` 派生
   run/archive 目标，校验 containment、basename 相同、目标不存在、非 reparse。
   archive 侧由**已批准的 archive root 派生**，不由 P2 字符串替换。
   规划器**不创建任何目录**。
4. **registry 未 fail-closed 到位**：13→99 跳号被接受（旧规则只要求「递增」）；
   计数字段接受负数与零。现在跳号拒于 `supplement_seq_not_next_value`；六个
   计数字段设下界，拒于 `integer_field_below_minimum`；`output_root` 须非空、
   绝对、可规范化。

### 13.3 未由工程解决、交 Aaron 的一项

R1 的 §D.3.2 P3 逐事件合同与 §D.3.3 状态图**互相矛盾**（P3 的前置与后继各缺
一条边）。工程树实现的是图与邻接合同的读法，但该读法**未被任何已批准的
profile 逐字覆盖**。因此本轮生成 correction-only 的
`ND1_RECOMMENDED_PROFILE_R2`（决策包 §D.11），只改这两处，其余 47/51 行逐字
继承 R1。

```
ND1_PROFILE_R2=PROPOSED_NOT_EFFECTIVE
R1_STATUS=RATIFIED_AND_STILL_EFFECTIVE（未被 supersede、未被宣称失效）
AARON_R2_RATIFICATION_REQUIRED=YES
```

### 13.4 现势节点状态

```
N00=BLOCKED_MISSING_AUTHORITY_ARTIFACTS_AND_AARON_STATE_RULING
N-D1=RATIFIED（profile R1）；R2 correction-only 提案待裁
N03=IMPLEMENTED_AND_HOLD_REPAIRED
N04=IMPLEMENTED_DEFAULT_REFUSE_AND_HOLD_REPAIRED
N05=IMPLEMENTED_AND_HOLD_REPAIRED
N06=HOLD_REPAIRED_AWAITING_FRESH_SOL_STAGE_I
N-D2=NOT_STARTED
N09=NOT_STARTED（另需 Aaron P2 精确授权）
P6_IMPLEMENTED=NO（归 N-D3）
MC_EXECUTED=NO ／ SUPPLEMENT_EXECUTED=NO ／ STRATEGY_BUILD_STARTED=NO
REGISTRY_EVENTS_APPENDED=NO ／ EXPOSURE_EVENTS_APPENDED=NO
REAL_DIRECTORIES_CREATED=NO ／ REAL_DATA_READ=NO
```

### 13.5 固定后续顺序（不得跳步）

```
1. Aaron 主动批准或修改 ND1_RECOMMENDED_PROFILE_R2
2. Opus 只持久化该裁决，工程树不再变化
3. NEW TOP-LEVEL SESSION，GPT-5.6 Sol XHIGH，正式 N06 exact-tree Stage I
4. 只有 N06 PASS 之后才进入 N-D2；N09 仍须另行精确执行授权
```
