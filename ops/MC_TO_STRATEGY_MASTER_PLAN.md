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

## 2. 基线事实（执行起点，PHASE A 实测）

| 项 | 值 |
|---|---|
| HEAD | `a9148f1f141b4ac421a8aa6d08f1539c315caaf9` |
| 工作树 | clean（0 porcelain） |
| tags | 恰两枚：`mc-freeze-v1`、`s0-freeze-v1`（无漂移） |
| registry sha256 前缀 | `ee9da33f` |
| exposure sha256 前缀 | `382182bf`；累计 researcher exposure=1575 |
| S0-T001 封存 | 14 文件，run==archive 逐字节全等 |
| attestation sha256 | `d839b965…41805`（== 代码 pin `ATTESTATION_SHA256_PINNED`） |
| 测试地板 | `MIN_COLLECTED_TESTS=2761`（双 pin：scripts/s0_real_run.py＋tests/test_s0_runner.py） |
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
| N01 | — | 统一原子＋冷重放（PHASE D 除 D5） | 工程 | synthetic | — |
| N02 | — | 平台权威事件（D5） | 工程＋Codex 验收 | synthetic | — |
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
1. supplement day-universe 定义：A=`∪θ(tp∪fp)`／B=八文件 `ref_dates` 结构总体；
   只出计数的关系探针是否获准、如何计 exposure。
2. supplement registry 批 1 事件词汇／字段／状态转移。
3. MC-DS-S001 是否 formal trial。
4. MC-DS `STARTED`、post-start failure 与重试记账。
5. supplement ledger／exposure quantity。
6. output root 与 `supplements\` 创建授权。
7. late-after-reveal 显著披露措辞。

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
| 2026-08-15 | N-PLAN | 本 commit | 未跑（doc-only） | 主计划落盘；DAG 与租约冻结 |
