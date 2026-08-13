# MC_DR5_BUILD_PACKET（DR-5 MC 生产消费者工程包，2026-08-14）

授权：`START_DR5_MC_CONSUMER_ENGINEERING_AFTER_S0_REVEAL_REVIEW_CORRECTION`。
本轮两个 commit：①纯文档揭盲纠正（PHASE B）；②本工程候选（PHASE D/E）。
零真实 MC、零 registry 事件、零封存件改动、零 MC_HANDOFF 研究值读取。

## 1. 来源→消费者矩阵摘要

全文见 `ops/MC_DR5_CONSUMER_SOURCE_MATRIX.md`（15 规则）。终态：
R1-R11、R13-R15 = READY（本轮建成 R9/R10/R13/R14）；**R12 grid 重放
harness = PARTIAL**（headline＋digest＋fp_alloc 已封存、K 全量为确定性
重放待建——只阻断 deployable_region 层，不阻断 Checkpoint-0）。

```
CAN_GRID_SAMPLES_BE_RECONSTRUCTED_FROM_SEALED_BUNDLE=YES
GRID_SAMPLES_SOURCE=S0_REPORT.json feasibility_grid.cells（per_seed headline＋digest＋fp_alloc＋repeats 参数）＋SEED_MANIFEST 流派生＋冻结 gridmix 确定性重放
RAW_DEVELOPMENT_DATA_REQUIRED=NO
NEW_RESEARCH_DEFINITION_REQUIRED=NO
```

## 2. 已闭合工程边界

新模块 `src/itsf/mc/consumer.py`（唯一新生产模块）＋
`src/itsf/mc/bootstrap.py` 两个**纯加法**参数（`pool_n`/`length`，默认
行为逐字节不变，既有调用者零影响）：

- **PreparedMCInput**：typed/frozen/slots、MappingProxy 封装、mtm 序列
  tuple 化、快照 JSON 深拷贝——曝光后计算只消费该对象（不携带任何路径/
  句柄，负例证明源删除后仍可运行）。
- **十项验证电池**（fail-closed，逐项负例）：exact-set（含 planted
  GRID_SAMPLES 拒绝）/manifest 全覆盖双核哈希/trial+commit 双源绑定/
  E×scn 轴＋记录 19 字段 schema/seed 恒等＋k_policy 结构化解析/严格升序
  （拒绝不修复）＋跨八文件记录集合恒等＋tp⊆records/TP∩FP=∅/realized
  counts 对账/冻结方法 digest（repo-root 锚定）/授权快照前置。
- **认知/结果层分离**：worlds **填满全部模板槽**（评审 H1 修复——池与
  槽长解耦）；世界级均值 monthly prop_operating_EV → P5/median/P95；
  aleatoric 单尝试分布独立报告且类型上进不了 GO 门；跨组合拼接
  Conservative/Stress 拒绝；同组合角色（Cons/Stress）拒绝错位。
- **判定域强制**（评审 H2 修复）：verdict 路径要求恰好覆盖冻结 Primary
  判定网格 {lucid,topstep}×{E1,E2}×P2（四格，标签逐一自洽），子集/错标
  拒绝；顺序 STOP→GO→β→α 与 gate2 守卫沿用既有 `verdict.py`。
- **收敛门**（评审 M1 修复）：rule(a) 要求 B/M/K 三轴分别加倍且类别
  全同；rule(b) 要求恰好 7/13/31 三 seed；rule(c) 空比较拒绝；类别词表
  校验；未收敛 → `MCNotConverged` 拒绝判决（rule(e)）。
- **封印候选** `render_verdict_inputs`（MC §6 形状）：绑定 trial/commit/
  method_digest/**bundle 逐文件 sha**/seeds；未收敛不可渲染。
- **授权门**：`authorize_real_mc` 确定性拒绝（registry 语法无
  `MC_RUN_AUTHORIZED` 词表；相似 token 亦拒并明示）；
  `run_real_mc` guards→gate 后不可达；`handoff.mc_ready_gate` 原样保留。

## 3. 仍缺失的封存输入 / 4. 是否需要新研究裁决

| 缺口 | 性质 | 需要谁决定 |
|---|---|---|
| grid 重放 harness（R12） | 纯工程（确定性重放＋digest 核验），无新研究定义 | 下一工程轮即可建；Codex 验收 |
| **Checkpoint-0 的 θ 通道绑定** | **冻结文档未钉**：S0 §10.4/MC §2.5 组合=平台×政策，未指明 oracle 选择通道用 θ=0.3 还是 0.5（或双通道各自报告、判定量词如何跨 θ） | **Aaron 具名裁决＋Codex 复核**（预注册语义级） |
| `MC_RUN_AUTHORIZED` registry 词表＋解析器 | 治理语法扩展（照 §10/IR-25 纪律） | Aaron 批准语法；工程实现＋Codex |
| feasibility 旗标的机器判定电池（月交易数/达标盈利日 vs payout/n=0 率/合约上限/ambiguous 占比/E2 超预算，MC §6） | 工程（消费者当前以注入旗标承载，未自动判定） | 下一工程轮；Codex 验收 |

**无需新研究定义**；θ 绑定是对既有冻结语义的解释性裁决，非新方法值。

## 5. Synthetic production-path 证据

`tests/test_mc_consumer.py`：**48 项**（提示词负例类全覆盖：缺/多/换型
文件、hash 与 manifest 覆盖、trial/commit/manifest 失配、轴/seed/K、乱序
（拒绝不修复）/重复/集合漂移（含跨场景选择性删除）、TP/FP 重叠、counts
失配、GRID_SAMPLES 植入拒绝、平台 variant 缺失、收敛四规则各负例、判定
网格子集/错标、跨组合拼接、单尝试分位数冒充认知门、非整数仓位、冻结方法
漂移、曝光后源删除仍运行、公共 runner 无授权确定性拒绝、相似 token 不开
门）；正例全链 `prepare → 十项验证 → epistemic(全网格) → aleatoric →
convergence → verdict → seal candidate` 通过，零真实封存值。

**内部盲式 conformance review（1 轮修复上限，已执行）**：独立评审交出
3 High / 6 Medium / 10 Low。修复轮闭合 H1（世界长度=模板槽数）、H2
（判定网格全覆盖强制）、H3（升序拒绝＋跨文件记录集恒等＋tp⊆records）、
M1-M5（收敛门/manifest 覆盖/k 解析/叶不可变/日历校验）；**M6 经引证
驳回**——评审称"bootstrap 池应为全部历史交易日"，但 S0 DR-4 冻结的
bootstrap 人口即 2842=tp∪fp 合格方向日序列（S0-T001 封存
`bootstrap_ci.*.n_days_in_sequence=2842` 为其实测钉），消费者继承同一
冻结人口定义。Low 项：已顺手修复 5（CWD 锚定/类别词表/快照深拷贝/封印
provenance/重言检查删除），余 5 记 P3（MCSE 退化默认/CRN 跨平台性质测试
/aleatoric SE 语义注记/`pytest.raises(Exception)` 一处/记录实例属性级
可变性——dataclass 非 frozen 属 contracts 层，改动越权本轮）。

## 6. 全套件与不变量（最终字节树 fresh）

```
COLLECTED=2676  PASSED=2676  FAILED=0  SKIPPED=0  (363.81s)
MIN_COLLECTED_TESTS=2676（双钉同步重钉，旧 2615）
SCANS=CLEAN  FROZEN_7=OK  DIFF_CHECK=CLEAN
REGISTRY_SHA256=ee9da33f…（S0-T001 事件链后现势，本轮零追加）
EXPOSURE_SHA256=382182bf…（本轮仅 PHASE B quantity=0 追加行；累计 1575 不变）
SEALED_S0_RUN/ARCHIVE=14 文件逐字节不变（双树 inventory 恒等复核）
repo runs/ ABSENT；无 tag；无 amend
```

## 7. 两个新 commit

- doc-only 揭盲纠正：`3234958`（追加式；OVERALL_S0_VERDICT=
  INCONCLUSIVE_PENDING_MC）
- 工程候选：本文件所在 commit（SHA 见终端汇报；含 consumer.py＋
  bootstrap 加法参数＋48 测试＋矩阵＋本包）

## 8. Codex 终审入口

复核重点：consumer.py 十项电池逐项 fail-closed 性；H1 修复的
pool/length 语义（bootstrap 加法参数默认行为不变性）；H2 判定网格
恒等；收敛门四规则忠实度；M6 驳回是否成立（DR-4 人口引证）；θ 绑定
缺口定性；`authorize_real_mc` 不可绕过性。

## 9. 下一次真实 MC 的最小授权条件（缺口未清，不生成运行授权语句）

1. Aaron 裁决 θ 通道绑定（上表）；2. Aaron 批准 `MC_RUN_AUTHORIZED`
registry 语法；3. grid 重放 harness＋feasibility 机器判定电池建成并经
Codex 验收；4. Codex 对本候选 PASS；5. Aaron 以新语法发出精确 MC 运行
授权。在此之前 `run_real_mc` 保持确定性拒绝。


---

## 10.【R2 现势（Codex findings 轮）——与上文冲突处以本节为准】

授权：`START_MC_DR5_CONSUMER_ENGINEERING_R2_CODEX_FINDINGS`（Aaron 勘误：
seed-11=笔误按冻结 7/13/31；θ 按 S0 §7 L133 机械修复；M 轴不发明定义）。

### 10.1 六项 R2 修复（全部落地＋行为测试）

1. **θ 硬绑定**（PHASE B）：S0 §7 L133"θ 主 0.5、副 0.3，不得事后升格"
   ——`PRIMARY_THETA_CHANNEL`/`SECONDARY_THETA_CHANNEL` 源自
   study.THETA_PRIMARY/SECONDARY；VerdictInput 携带 channel；epistemic
   门与 verdict 门双层拒绝 θ.3（全绿也拒）；seal 绑定
   primary_theta_channel；**R1 packet 把 θ 列为 Aaron 决策系误判，撤回**。
2. **外部保管链**（PHASE C）：`expected_file_sha256` 必需；键集=全 14
   文件（含 manifest.jsonl）精确恒等；逐文件 64-hex 校验；payload＋内部
   manifest 同步改写攻击夹具必败；缺一/多一/未钉 manifest/换型全拒。
3. **GRID 事实审计**（PHASE D）：R1 的 `YES` **显式撤回**——
   `CAN_GRID_SAMPLES_BE_RECONSTRUCTED_FROM_CURRENT_SEAL=NO`、
   `MISSING_AUTHORITY=EXACT_PER_DAY_DAY_STRATA`、
   `GRID_REPLAY_STATUS=BLOCKED`（分层抽样需全池逐日 year×vol×event
   归层；封存件仅有 headline 已抽日/层级计数/digest；DAY_STRATA 当时
   withheld；digest 不可反演；读原始数据重建被禁）。
4. **收敛/feasibility 生产化**（PHASE E）：`convergence_from_evidence`
   全部从 RunEvidence 计算（run 身份/prepared 摘要/轴/规模校验、per-axis
   漂移图精确键集、seed verdict 从实际结果算出、MCSE 从实际样本）；
   `FeasibilityEvidence` 从 lifecycle 输出机械计算（§10.4 三项的直读：
   整数仓位未全跳过＋交易机会存在＋payout 路径实际实现——必要条件读法，
   Codex 可收紧）；调用方布尔与手工全绿对象全面废除（gate 签名无
   feasible 参数，静态测试钉）。**M 轴=DECISION_REQUIRED_M_AXIS**：MC §5
   把 M 钉为穷尽枚举起始相位（≈21），"加倍 M"无唯一冻结语义——生产
   不可组装合法 M-doubled run，收敛因此结构性不可满足直至 Aaron 裁决
   （测试同时证明：机制在合成 M 夹具下端到端可用，语义未被发明）。
5. **深度不可变**（PHASE F）：FrozenTradePath（由 contracts 动态生成的
   frozen/slots 镜像，mtm=tuple）；快照递归冻结（dict→MappingProxy、
   list→tuple）；prepare 后改源 dict/list/快照零影响；prepared 内部
   赋值/leaf 变异全部抛错；`prepared_digest` seal 前后复核相等。
6. **aleatoric 诚实边界**（PHASE G）：`run_conditional_aleatoric` 绑定
   **单一固定世界**（长度=全模板槽、成员⊆通道池、world_digest 入结果）；
   历史序列平铺已删除；**total predictive（B×M）未实现 → R9 降
   PARTIAL**。

### 10.2 现势状态（诚实）

```
MC_CONSUMER_BUILD=PARTIAL
MC_INPUT_BUNDLE_READY=YES        # 十项电池＋外部 custody 完整
GRID_SAMPLES_READY=NO            # BLOCKED（缺 EXACT_PER_DAY_DAY_STRATA）
GRID_REPLAY_STATUS=BLOCKED
DECISION_REQUIRED_M_AXIS=YES
MC_REAL_RUN_READY=NO
MC_EXECUTED=NO
MC_REGISTRY_EVENTS_APPENDED=NO
STRATEGY_BUILD_STARTED=NO
```

PARTIAL 依据（PHASE H PASS 条件对照）：θ 门✓、外部 custody✓、深度不可变✓、
收敛/MCSE/feasibility 证据化✓、conditional aleatoric✓——但 **GRID replay
来源不完整（BLOCKED）**、**total predictive 未实现**、**M 轴语义未决**，
三者任一都排除 PASS。

### 10.3 GRID/DAY_STRATA 三选一（Aaron 决策包，不替选）

| 选项 | 内容 | trial/exposure | 封存不可变性 | 可比性 |
|---|---|---|---|---|
| **A** | 接受 S0-T001 无法提供正式 deployable-region grid replay；MC 保持 HOLD（Checkpoint-0 主判定不受阻，但 H1 资格层永缺） | 零新 trial、零新 exposure | 封存件不动 | 完整——不引入任何新工件 |
| **B** | 授权一个**独立记账**的数据重建/补充封存流程：从原始 Development 数据重导 DAY_STRATA（逐日 year×vol×event），以新 registry 事件＋新封存目录记账 | 零 trial 消耗；**结构性数据访问需登记**（同 incident 纪律；零 outcome 查看可设计为盲式） | 原封存件不动；新工件独立封存＋哈希；与原 run 的绑定=commit＋seeds＋day 池交叉核验 | 需披露"补充工件晚于揭盲生成"——审计上弱于运行时封存 |
| **C** | 授权新 S0 trial（S0-T002）：运行时正式封存 DAY_STRATA/GRID_SAMPLES（handoff schema 已在，formal_sealable 条件已备） | **消耗 S0-T002 编号**＋一次完整真实运行；exposure 依盲式纪律可控 | 运行时密封=最强 | 最强，但 S0-T002 结果与 T001 存在重复检验语义需预注册处理 |

### 10.4 真实 MC 最小授权条件（更新）

1. Aaron 三选一裁决（10.3）；2. Aaron 裁 M 轴加倍语义（或裁定以 B/K 双轴
＋M=穷尽枚举豁免替代——同为语义级裁决）；3. `MC_RUN_AUTHORIZED` registry
语法批准＋实现；4. Codex 对本候选 PASS；5. 精确 MC 运行授权。
不满足前 `run_real_mc` 保持确定性拒绝；本轮不生成任何授权语句。
