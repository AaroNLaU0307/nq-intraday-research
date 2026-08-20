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


---

## 11.【R2.1 现势（provenance closeout 轮）——与上文冲突处以本节为准】

授权：`START_MC_DR5_CONSUMER_R2_1_PROVENANCE_CLOSEOUT`。
Subagent 模式：两车道均已使用——S1（tests/test_mc_convergence_provenance.py，
20 测试）完整交付；S2（tests/test_mc_custody_calendar.py，15 测试）在
API 限额中断前完成文件写入；两车道文件租约零交集，主代理按其标注的
集成接缝统一对齐（参数名 custody_authority 采纳 S2 命名；
FeasibilityEvidence 新字段与 M/K 拒绝顺序按 S1 合同）——全程披露。

### 11.1 Codex 三反例修复前后

| 反例 | 修复前（R2） | 修复后（R2.1） |
|---|---|---|
| 外层 RunEvidence 元数据可伪装规模/种子 | 外层 B/M/K/seed 仅记录，不校验内层 | `validate_inner_binding`：外层逐字段对内层 EpistemicResult（含 world_means 实际长度、M=实际相位数、prepared_digest、θ 通道、combo 标签、场景角色）；旗舰反例（内层全 B=2/seed=7，仅改外层）逐项确定性拒绝 |
| 手搭全绿 ConvergenceReport 可入 seal | verdict/render 收 report 对象 | verdict/render 只收证据三元组，收敛在内部重算；report 对象无入口 |
| feasibility 布尔偷裁 | "any payout＋非全跳过"必要条件读法当门 | **撤回**：`FEASIBILITY_GATE_STATUS=DECISION_REQUIRED`，gate 确定性拒绝出票（CHECKPOINT0_VERDICT_REACHABLE=NO）；机械指标保留并扩充（ambiguous_share 新增） |

另落地：MCSE 零方差严格化（between=0 仅 within=0 过；NaN/inf/负/空样本
→ `epistemic_samples_invalid`）；prepared_digest 绑全内容（逐日历
day_id/offset/首月相位/全日序列/快照规范化摘要——同长异日必异摘要）；
注入日历复制 tuple 化＋参数改名 `test_only_calendar`（生产入口无此
seam）；**typed CustodyAuthority**＋生产来源接线
`load_custody_authority_from_attestation`（解析盲式 post-run attestation
14 行哈希表；对真实文件实测通过）＋非测试生产 caller
`mc/real_input.py::prepare_real_mc_input`（gate-first：guards→授权拒绝
→在任何封存字节被读之前停止）；test_only authority 进生产入口
→ `custody_authority_test_only_in_production` 拒绝；authority 与 bundle
的 trial/commit 绑定无条件校验。

### 11.2 现势状态（PHASE I 模板，事实决定）

```
MC_CONSUMER_BUILD=PARTIAL
CONVERGENCE_EVIDENCE_READY=PARTIAL   # M 语义未裁＋K 证据 BLOCKED＋base 冻结规模无真实运行
MC_INPUT_BUNDLE_READY=YES            # typed authority＋生产来源接线＋非测试 caller 齐备
GRID_REPLAY_STATUS=BLOCKED
DECISION_REQUIRED_M_AXIS=YES
FEASIBILITY_METRICS_READY=YES        # 指标机械计算（per-metric 状态见 11.3C）
FEASIBILITY_GATE=DECISION_REQUIRED
CHECKPOINT0_VERDICT_REACHABLE=NO
MC_REAL_RUN_READY=NO
MC_EXECUTED=NO
MC_REGISTRY_EVENTS_APPENDED=NO
STRATEGY_BUILD_STARTED=NO
```

### 11.3 三份最小 Aaron 决策包（不替选）

**A. GRID/DAY_STRATA（同 §10.3 三选一，附本轮建议）**：

```
GRID_RECOMMENDATION=B_BLIND_SUPPLEMENTAL_DAY_STRATA_SEAL
```

理由：零 trial 消耗；盲式可设计（结构性访问登记、零 outcome 查看）；
原封存件不动；工件独立封存＋commit/seeds/日池交叉绑定。代价=审计上
弱于运行时封存（须披露晚于揭盲生成）。A（永缺 H1 资格层）与 C（消耗
S0-T002＋重复检验语义）备选保留。

**B. M 轴语义**：

```
M_AXIS_RECOMMENDATION=FINITE_SUPPORT_EXHAUSTIVE_ENUMERATION_EXEMPT_FROM_DOUBLING
```

机器义务（批准后代码强制）：完整合法 start-phase 集合＝首月全部交易日
相位；每一 phase 恰好一次（无缺失/重复/额外）；B/K 加倍规则原样保留；
**批准前不得生效**（当前代码对任何 M 条目确定性拒绝）。

**C. Feasibility 冻结输出与候选阈值（逐项，Aaron 择定或另定）**：

| 冻结输出（MC §6） | 计算状态 | 候选阈值（仅列，不选） | 后果 |
|---|---|---|---|
| 月均交易数/频率 | 可由 offered/24 派生（COMPUTED-DERIVABLE） | ≥2/月 或 ≥3/月 | 过低→样本不足以支撑 payout 周期 |
| 达标盈利日分布 vs payout 要求 | PENDING_ENGINEERING（需 per-event 管道） | payout 资格月覆盖率 ≥50%/≥80% | 决定 payout 路径现实性 |
| n=0 跳过率 | COMPUTED（total_skips_n0/total_offered） | ≤25% 或 ≤50% | 过高→整数仓位不可行 |
| 合约上限触碰率 | PENDING_ENGINEERING | ≤10% | 过高→scaling 档位约束失真 |
| payout 实现概率/次数 | COMPUTED（payout_realized_share） | >0 或 ≥25% 世界实现 | GO 的"payout 路径可行"主证 |
| ambiguous 占比 | COMPUTED（ambiguous_share） | ≤5% | 过高→双场景不确定性支配结果 |
| E2 超预算概率 | PENDING_ENGINEERING（需记录级 realised/anchor 管道） | P(超预算)≤10% | E2 无止损尾部纪律 |

规则：布尔归约=以上各项的合取式（Aaron 定每项阈值与是否入选）；未裁
前 `VerdictInput` 不可构造（gate 确定性拒绝，已测）。

### 11.4 证据等级

```
FABLE_MEASURED=三 MC 测试文件 75 项＋既有 87 项全绿；全套件见终报；attestation loader 对真实文件实测
CODEX_NOT_YET_REPRODUCED=YES
```


---

## 12.【R2.2 现势（self-authenticating evidence 轮）——与上文冲突处以本节为准】

授权：`START_MC_DR5_R2_2_SELF_AUTHENTICATING_EVIDENCE`（Aaron 执行令，
并确认 Fable 对 Codex 审核持最终裁量权——本轮三项反例经独立核实全部
成立后采纳）。Subagent 租约：S1/S2 各自续话自改本车道文件（接口涟漪
经 follow-up 由原车道修复，主代理零触碰）；主代理新增独占
`tests/test_mc_r2_2_integration.py`。

### 12.1 三反例修复前后

| Codex 反例 | 修复前（R2.1） | 修复后（R2.2） |
|---|---|---|
| 伪造派生统计量（world_means=[-100]×B 声明 p5=+999/mcse_ok=true） | dataclass 构造器接受任意声明值，`dataclasses.replace` 可伪造 | **类型自认证**：`__post_init__` 从原始样本（含完整 `within_world_ses` tuple，长度必须=B）精确复算全部派生量，失配即 `epistemic_derived_stats_mismatch`；构造与 replace 均拒；进不了 RunEvidence |
| 合法收敛证据＋手工正收益 VerdictInput | `verdict_or_refuse(primary_inputs=…)` 独立信任面存在 | **入口删除**：`verdict_and_seal_from_evidence(prepared, base, doubled, seeds)` 为唯一判定＋封印路径，Primary 表由 `base.results` 内部归约，封印表与机械 verdict 共用同一归约对象；签名扫描测试钉"无任何公共函数收 primary_inputs" |
| 手构 `CustodyAuthority(test_only=False)` | 任何调用方可构造并投喂生产入口 | **生产入口只收原始 attestation 字节**：authority 由内部构造器生成，来源 id＋文档摘要双 pin 于代码（`ATTESTATION_SHA256_PINNED=d839b965…`）；同步改写 attestation＋bundle＋manifest 仍败于代码 pin；测试入口拒 test_only=False（`custody_authority_production_object_in_test_entry`）；`real_input.py` 收敛为唯一正式 caller |

### 12.2 现势状态

```
MC_CONSUMER_BUILD=PARTIAL
CONVERGENCE_EVIDENCE_READY=PARTIAL
MC_INPUT_BUNDLE_READY=YES
GRID_REPLAY_STATUS=BLOCKED
DECISION_REQUIRED_M_AXIS=YES
FEASIBILITY_GATE=DECISION_REQUIRED
CHECKPOINT0_VERDICT_REACHABLE=NO
MC_REAL_RUN_READY=NO
MC_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO
```

### 12.3 Feasibility 决策包 v2（阈值改从冻结平台规则推导，取代 §11.3C 的整数候选）

**GO 必需门**（S0 §10.4 row 2 明名三项，各自的量从冻结参数落地）：

| 门 | 冻结依据 | 派生候选（Aaron 择定/另定） | 归类 |
|---|---|---|---|
| payout 路径可行 | Lucid：`qualifying_days_required=5`＋`qualifying_day_min_profit_usd=$150`（每次 payout 后重计）；Topstep XFA：~~`≥3 交易日（每日≥1笔）＋ largest_winning_day/total ≤ 0.40`~~ **【勘误 → §14.7】本行 Topstep 参数取自 `payout_paths.consistency`（sensitivity 路径），Primary 生命周期 `topstep_50k_stdpurchase_xfastd_nodll` 用的是 standard 路径＝5 盈利日×每日净利 ≥$150** | 认知层世界中**模拟内实际实现 payout** 的世界占比 ≥X%（X∈{25,50}）——或最低要求：≥1 次实现（当前 `payout_realized_share>0` 即此读法） | GO 必需 |
| 频率可行 | 同上（5 达标日/周期与 ≥3 日/周期是频率的冻结下界来源） | 月均可交易日 ≥ 派生下界：Lucid 周期内可达 5×$150 日（≈月均 ≥5 个交易机会才可能）；Topstep ≥3 | GO 必需 |
| 整数仓位可行 | MC §3 `n = min(floor(budget/anchor), 档位, absolute_max)`；n=0 跳过计数为冻结输出 | n=0 跳过率 ≤Y%（Y 无冻结值——**纯 Aaron 裁量**，候选 25/50 仅为区间示例并如实标注为非推导值） | GO 必需 |

**仅报告项**（MC §6 强制输出、冻结文本未 GO 条件化）：ambiguous 占比
（COMPUTED）；E2 超预算概率（PENDING_ENGINEERING）；合约上限触碰率
（PENDING_ENGINEERING）；达标盈利日 vs payout 要求全分布
（PENDING_ENGINEERING）；exhausted 占比（COMPUTED）。

规则不变：布尔归约未获 Aaron 冻结前，归约步确定性拒绝
（`feasibility_gate_decision_required`），VerdictInput 不可构造；批准后
唯一合法扩展=一份 typed、provenance-bound decision evidence 附着于同一
base 归约，不重开任意 Boolean。

### 12.4 证据等级

```
FABLE_MEASURED=车道 S1 25 项（自改后）＋S2（见其回执）＋主代理 43 项；全套件见终报
CODEX_NOT_YET_REPRODUCED=YES
```

## 13.【R2.3 现势（evidence hardening＋M 枚举＋GRID-B 准备轮）——与上文冲突处以本节为准】

授权：`START_MC_DR5_R2_3_EVIDENCE_HARDENING_M_ENUMERATION_AND_GRID_B_PREPARATION`
（Aaron："你看看有没有必要做吧，审核提示词"→Fable 审核 ACCEPT→Aaron：
"那现在执行吧"）。提示词内两项裁定行随逐字发送即批准并已登记为
**IR-29**（见 IMPLEMENTATION_RESOLUTIONS.md）：M 轴有限支撑豁免加倍＋
GRID 采 Option B（本轮仅工具构建）。**feasibility 阈值明确未批**。
车道租约：S1＝`tests/test_mc_r2_3_evidence.py`（20 项，独占新文件）；
S2＝`src/itsf/mc/day_strata_supplement.py`＋`tests/test_mc_day_strata_supplement.py`
（27 项，独占新文件）；主代理＝consumer.py 集成＋既有测试文件
（provenance/consumer/r2_2_integration 已归主代理"既有测试"）＋治理文档。

### 13.1 红字证明（修复前 @`a327f1e` 实测）

| 探针 | @`a327f1e` 行为 | R2.3 修复后 |
|---|---|---|
| PROBE1：调用方持有 world_means list，构造后原地 append/篡改 | **成立**——EpistemicResult 存的是调用方 list 的别名，构造后突变使 world_means 与已存 p5 分道（自认证被绕过） | `_canonical_float_tuple` 在 `__post_init__` 第一步把样本折叠为纯 float tuple（断别名；bool/非数/非有限拒 `epistemic_samples_invalid`），派生量复算基于折叠后副本 |
| PROBE2：`FeasibilityEvidence(n_paths=-5, payout_realized_share=3.7, …)` | **成立**——聚合标量为构造器直收，负数/超界/凭空声明全接受 | 聚合层重建：唯一入口 `from_observations`（B×M 条 `FeasibilityObservation` 原始层，逐条验证 `feasibility_observation_invalid`；计数=expected_n 且 (world,phase) 无重复；六项聚合量从原始层复算，失配拒 `feasibility_derived_stats_mismatch`）＋绑定八元组（digest/platform/engine/scenario/channel/B/M/master_seed）由 `EpistemicResult.__post_init__` 交叉核验（`feasibility_binding_mismatch`） |

上游化效应：R2.1 的 digest/channel 内层篡改反例现于**构造点**即拒
（provenance 两测试相应上移；收敛层内外绑定检查保留为纵深防御）。
`RunEvidence.__post_init__` 深冻结 results（MappingProxyType＋tuple 对）。

### 13.2 IR-29 落地（M 轴）

`DOUBLING_AXES={B,K}`；`M_AXIS_DOUBLING_STATUS=
"RESOLVED_BY_IR29_EXHAUSTIVE_SUPPORT_CERTIFICATE"`。收敛证据新增必要件
`ExhaustiveSupportCertificate`（绑定 prepared_digest＋支撑序列）：
doubled_by_axis 现 "M" 条目→`m_axis_doubling_forbidden_by_ir29`；证书
缺失→`m_support_certificate_missing`；证书六类违规各有专码（wrong_calendar/
duplicate_phase/incomplete/extra/order_violation/execution_mismatch）。
B/K 义务不变；K 维持 `k_axis_evidence_blocked_grid_replay`（终端拒绝——
证书有效时 K 拒绝可达性已被测试钉定）。
`verdict_and_seal_from_evidence` 签名相应扩为五参（签名扫描测试已更新）。

### 13.3 Feasibility 逐指标状态（FEASIBILITY_METRICS_STATUS，代码内 MappingProxyType）

| 指标 | 状态 |
|---|---|
| payout_realization / payout_count / n0_skip_rate / ambiguous_share / exhaustion_share | COMPUTED |
| winning_days（台账逐日余额差）/ days_profit_ge_150（冻结 Lucid $150 地板） | COMPUTED |
| contract_cap_hits（事件流无逐日 n） | PENDING_ENGINEERING |
| e2_over_budget_days（需 record 级管道） | PENDING_ENGINEERING |
| qualifying_distribution_vs_payout_requirements | PENDING_ENGINEERING |

原始层已为 PENDING 三项预留 None 字段（None=PENDING_ENGINEERING 显式语义，
非 0 伪装）。

### 13.4 GRID Option B 工具（S2 车道交付；BUILT，未执行）

`src/itsf/mc/day_strata_supplement.py`：`SUPPLEMENT_ID="MC-DS-S001"`、
schema `mc_day_strata_supplement.v1`；`build_day_strata_supplement` 纯函数
（4 键行、禁研究值字段即拒、日集与冻结全池精确相等、5 键绑定头）；
`seal_supplement` .partial 暂存后原子落位；`authorize_supplement` **默认
无条件拒绝**（`SupplementNotAuthorized`），`run_supplement_production`
gate-first 同拒。**本轮零真实执行、零真实数据读取。**

### 13.5 MC-DS-S001 执行授权模板（模板≠授权；本轮不生成任何可用授权语句）

未来 Aaron 如决定执行补充封存，需逐字发送（占位符由 Aaron 填写，缺一即无效）：

```
START_MC_DS_S001_DAY_STRATA_SUPPLEMENT_EXECUTION
supplement_id: MC-DS-S001
authorized_commit: <40-hex commit>
output_root: <真实输出根路径>
```

本模板含未填占位符，**不构成授权**；default-refuse 工具在收到上述逐字
语句并核验三字段前维持拒绝。真实 MC 运行授权另需 §10.4 全部条件，两者
互不替代。

### 13.6 Feasibility 决策包 v3（分平台呈列；派生 vs 裁量显式分栏；取代 §12.3 表）

**Lucid（冻结参数：qualifying_days_required=5；qualifying_day_min_profit_usd=$150，每次 payout 后重计）**

| 门 | 候选阈值 | 性质 |
|---|---|---|
| payout 路径 | 世界内模拟实际实现 payout 的世界占比 ≥X%（X∈{25,50}）；最弱读法＝≥1 次实现。**注意：`payout_realized_share>0` 只证明"模拟内出现过 payout 事件"，不得表述为"已确认可行"** | X 为裁量；"≥1 次"为最弱下界（派生自"路径存在"字面） |
| 频率 | 周期内 `days_profit_ge_150`≥5 的世界占比 ≥X% | 5×$150 为冻结派生；X 为裁量 |
| 整数仓位 | n=0 跳过率 ≤Y%（候选 25/50 仅为区间示例，非推导值） | **纯裁量** |

**Topstep XFA** ~~（冻结参数：≥3 交易日（每日≥1 笔）＋ largest_winning_day/total ≤0.40）~~ **【勘误 → §14.7】该括号内为 `payout_paths.consistency`（sensitivity）路径参数；Primary 冻结路径是 standard ＝ 5 盈利日 × 每日净利 ≥$150**

| 门 | 候选阈值 | 性质 |
|---|---|---|
| payout 路径 | 同 Lucid 读法（standard 路径：5 盈利日×$150）；~~consistency 0.40 约束下的实现占比~~【勘误 → §14.7】 | 5×$150 为冻结派生；占比阈值裁量 |
| 频率 | 周期内 winning_days≥3 的世界占比 ≥X% | 3 为冻结派生；X 为裁量 |
| 整数仓位 | 同 Lucid | **纯裁量** |

规则不变：Aaron 未择定前，`gate_status="DECISION_REQUIRED"` 冻结在
FeasibilityEvidence 上，归约步确定性拒绝，VerdictInput 不可构造，
CHECKPOINT0_VERDICT_REACHABLE=NO。

### 13.7 现势状态

```
EPISTEMIC_SELF_AUTHENTICATION=HARDENED_R2_3（别名断绝＋原始观测层）
FEASIBILITY_EVIDENCE_STATUS=OBSERVATION_LAYER_REBUILT（7 COMPUTED / 3 PENDING_ENGINEERING；gate=DECISION_REQUIRED）
M_SUPPORT_CERTIFICATE_STATUS=LANDED（IR-29；DOUBLING_AXES={B,K}）
GRID_B_TOOLING_STATUS=BUILT_DEFAULT_REFUSE
GRID_B_EXECUTED=NO
GRID_REPLAY_STATUS=BLOCKED（待 MC-DS-S001 真实封存）
FEASIBILITY_GATE=DECISION_REQUIRED
CHECKPOINT0_VERDICT_REACHABLE=NO
MC_REAL_RUN_READY=NO
MC_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO
```

### 13.8 证据等级

```
FABLE_MEASURED=S1 车道 20 项＋S2 车道 27 项＋provenance 25 项＋MC 家族合计 106 项；全套件与地板重钉见本节终态行
CODEX_NOT_YET_REPRODUCED=YES
```

### 13.9 终态（最终字节树 fresh 实测）

```
FULL_SUITE=2761 passed / 0 failed / 0 error（389.04s，最终树）
MIN_COLLECTED_TESTS 重钉=2714→2761（scripts/s0_real_run.py＋tests/test_s0_runner.py 双 pin，floor 子测试 6/6）
registry sha256 前缀=ee9da33f（逐字不变）；exposure sha256 前缀=382182bf（逐字不变）
S0-T001 封存 14 文件 run==archive 全等；真实输出根零写入
禁令扫描：代码/测试 delta 无 S0-T002/真实根路径/授权口令 token
```

## 14.【N01+N02 现势（OPUS5 master 执行首段）——与上文冲突处以本节为准】

授权：Codex 综合稿 `OPUS5_MC_TO_STRATEGY_V1`，Aaron 逐字发送
`EXECUTE_OPUS5_MC_TO_STRATEGY_MASTER_V1` 启动。恢复锚与 canonical DAG 见
`ops/MC_TO_STRATEGY_MASTER_PLAN.md`（**旧节点编号 V1/V1.1/V1.2 已作废**）。
本段执行范围＝`N-PLAN → N01 → N02`＋准备 N00/N-D1 决策包，随后强制停止。

### 14.1 架构变更（统一原子层取代三套 caller 输入）

| 项 | 变更 |
|---|---|
| **D1 统一原子** | 新 `src/itsf/mc/atoms.py`：`SimulationPathObservation`（每 (world,phase) 一条）＋`ObservationSet`。world means／分位／within-world SE／feasibility 指标／M 证书／verdict inputs／conditional aleatoric／total predictive **全部由同一组原子归约**（旧的三套互不绑定 caller 输入已删）。`total_predictive` 落地即闭合 R9 PARTIAL |
| **D2 身份绑定** | `lifecycle_config_digest`：`dataclasses.fields()` 机械枚举 LifecycleConfig 全字段＋**机械收割 61 个冻结常量**（orchestrator/lucid/topstep/account 的 UPPER_CASE 扫描，排除集为空且被测试钉死）＋轴／快照锚／版本锚，共 14 键前像；atom/container/cold-replay/seal **四层精确相等**；`combo` 降为显示标签（`combo_label_not_authoritative`） |
| **D3 冷重放封存门** | 删除一切可序列化的 `match=True`；`verdict_and_seal_from_evidence` 每次调用从 pinned prepared bytes＋config 前像＋RNG 规范**冷启动重放全部生命周期**，比完整键集与逐原子 digest，失配 `cold_replay_divergence`；receipt 只是审计描述，改成"全绿"也绕不过（有测试） |
| **D4 B×M 与 M 证书** | `expected_n` 全面删除（AST 钉死）；键集恒等 `range(B) × prepared.first_month_offsets`；四码 `key_grid_duplicate/substitution/missing/extra`；world 表冷重建绑定；**B-doubling world-digest 前缀内容证明**（`SeedSequence(seed).spawn(2B)[:B] == spawn(B)` 已实测成立且 seed-specific）；**M 证书改由 `derive_support_certificate` 从实际迹派生**，caller 参数删除 |
| **D5 平台权威事实** | `AccountEvent` 新增 `day_net_usd/qualifying_day/account_generation/requested_n/traded_n/cap_applied/over_budget`，由平台在**事件产生处**发射；`account_generation` 七个余额重置边界（三层证明无遗漏）；`qualifying_day` 三态且取自平台自身计数器（**不是** `day_net>=150` 重导——Topstep 申请日净额过 150 却不达标）；`balance−prev+payout_gross` 降级为同代非重置日交叉核验 |
| **D6 原始 trace 与双 reducer** | 规范 JSONL＋两级 digest；类型内 reducer declare-and-verify；独立 `cold_reducer.py`（import 集 ⊆ `{__future__,hashlib,json,math}`，AST 钉死零 `itsf` 依赖），失配 `reducer_disagreement`。为使逐位一致，`atoms.py` 以纯 float 重实现同一 type-7 分位与 ddof-1 SD，consumer 不再 import numpy |

### 14.2 修复轮（N01 唯一一轮）关闭的三项

1. **D-1 强度回退（必修）**：声明-派生比对原为**数值**相等，因 `True == 1.0` 使
   `world_means=(True, False)` 在派生值恰为 `(1.0, 0.0)` 时被接受——R2.3 曾显式
   拒绝布尔样本。已加 `strict_scalar_equal`（`type(got) is type(expected)`）与
   `strict_float_sequence_equal`（逐元素 `type(x) is float`）；三种伪装
   （bool 冒 float、int 冒 float 分位、bool 冒 feasibility 计数）各有负例，且每个
   负例**先断言数值比较确实相等**再断言拒绝。
2. **D-2 空集≠零噪声**：`stderr_of(())`/`sample_sd(())` 原返回 `0.0`（会让
   MC §5 规则 (d) 免费通过）；现 n==0 拒绝 `epistemic_samples_invalid`，
   n==1 保留真实的 ddof-1 零。cold_reducer 同步。
3. **D-4 fail-closed 词汇**：`convergence_from_evidence` 末端 `AssertionError`
   → `MCInputError("convergence_unreachable_state")`，K 轴将来解封时不再以
   非 MCInputError 逃逸绕过 fail-closed 语义。

### 14.3 既有电池迁移（48 项，零弱化）

36 `MIGRATED_STRONGER` / 9 `MIGRATED_SAME_STRENGTH` / 3 `OBSOLETE_BY_CONSTRUCTION`
（后者**全部保留为测试**并改为断言"入口不存在"＋接上更深的后继守卫，无一删除）
＋2 项新增（冻结常量值 pin、`from_world_means` 已删缝红线）。
**变异证明**：57 个变异锚点，对照组 0 红，48+2 个测试**每一个都被至少一个针对性
变异杀死**（程序化核验）。变异工装置于 session scratchpad，未入库（锚点为源码
字符串精确匹配，脆但响亮）——是否转为常设审计资产待定。
生产规模夹具不可行（B=1000×M=21×8 组≈百万原子），裁定：逻辑测试 monkeypatch
`B_WORLDS_FROZEN`（仅此一个，K 与 seed 保持真值 200/7），常量真值另由
`test_frozen_scale_constants_are_pinned_at_production_values` 独立钉死。

### 14.4 主代理跨车道集成裁定（三项，`tests/test_mc_node_integration.py` 25 项）

1. **令牌词表跨钉**：两车道"按规范约定、不靠 import"各自定义缺失令牌，唯一机械
   守卫在此——任一侧改名会改变封存报告的**含义**而其他测试全绿。
2. **不变量冲突已裁**：S1 要求 `contract_cap_hits ≤ executed_trade_days`，S2 允许
   `cap_applied=True` 配 `traded_n=0`。核实 Lucid 在 `micros>0` 守卫外不计算请求、
   Topstep 上限恒为 {20,30,50}/50 → 该组合**生产路径结构性不可达**，两侧不冲突
   （跨平台×跨盈亏扫描测试钉死）。
3. **层-1 缺陷范围**：见 §14.5-2，隔离性已成测试。

### 14.5 新增待裁事项（全部入主计划 N-D2；本轮未替 Aaron 决定）

1. **E2 `over_budget` 谓词未定义**：冻结文本要求披露却从未定义（哪个损失／哪个
   基准／哪个预算）。两车道拒绝发射布尔，改发类型化 `PENDING_RULING`；
   `OVER_BUDGET_PREDICATE_RULED=False` 期间 `AccountEvent` **拒绝携带布尔**。
2. **冻结层-1 会计确认缺陷**：Lucid 过阶时 `strategy_account_EV` 丢弃评估期利润
   （实测两个 +1500 日报 0.0，权威和 3000.0）。**影响范围机械钉死**：
   Checkpoint-0 用 `prop_operating_EV`＝`payout_cash+terminal_cash−fees`，
   不以层-1 为输入 → 缺陷**够不到判定统计量**。改冻结层数字属 Aaron 裁定，
   本轮未改；权威累加器与旧口径并存使差额可测（且不入 `ledger_report`）。
3. **生产规模从未执行**（诚实披露）：全部逻辑测试在 B=2/M=2。R2.3 的"生产规模"
   夹具是用已删除接口**伪造的摘要**，同样从未真跑——本轮把该缺口由"被掩盖"
   变为"显式"。是否要求一次生产规模冒烟运行归 Aaron。

### 14.6 现势状态

```
UNIFIED_ATOM_LAYER=LANDED（单一归约源；三套 caller 输入已删）
COLD_REPLAY_SEAL_GATE=LANDED（无可序列化 match；每次调用冷重放）
LIFECYCLE_CONFIG_DIGEST=LANDED（14 键前像／61 常量机械收割／四层相等）
PLATFORM_AUTHORITATIVE_FACTS=LANDED（7 字段／7 代边界／三态 qualifying_day）
M_SUPPORT_CERTIFICATE=DERIVED_FROM_TRACE（caller 入口已删）
FEASIBILITY_GATE=DECISION_REQUIRED（未裁；无 feasible 布尔存在）
GRID_REPLAY_STATUS=BLOCKED（K 轴终端拒绝；MC-DS-S001 未执行）
CHECKPOINT0_VERDICT_REACHABLE=NO
MC_EXECUTED=NO ／ SUPPLEMENT_EXECUTED=NO ／ STRATEGY_BUILD_STARTED=NO
NEXT=N00（Round-4 权威文本）＋N-D1（决策批 1）——均 BLOCKED_ON_AARON
```


### 14.7 历史文档勘误指针（事实修正，非方法裁定）

**Topstep Primary payout 路径参数**：§12.3 与 §13.6 把 `≥3 交易日＋0.40
consistency` 写成 Primary 冻结参数——**错误**。冻结事实（三处独立证据）：

| 证据 | 内容 |
|---|---|
| `gate1/platform_params.yaml:258-266` | XFA 两条路径二选一：`standard.qualifying="5 个盈利日，每日净利 ≥ $150"`；`consistency.qualifying="≥3 交易日（每日≥1笔）＋ largest_winning_day/total ≤ 0.40"` |
| `MC_METHOD_SPEC.md` §2.5 decision_roles | Primary 生命周期 = `topstep_50k_stdpurchase_xfastd_nodll`（**xfastd = standard**）；`topstep_50k_stdpurchase_xfaconsistency_nodll` 列在 `secondary_sensitivity` |
| `src/itsf/mc/platforms/topstep.py:61-62` | 生产代码常量 `XFA_QUALIFYING_DAY_MIN_NET_USD = 150.0`、`XFA_QUALIFYING_DAYS_REQUIRED = 5`；XFA 生命周期**无任何 0.40 consistency 规则** |

即：**生产代码自始正确，错的只有 packet 文档**。故本勘误是纯文档修正、零代码改动，
两处已加内联删除线与指针。0.40 与 ≥3 日只属 `xfaconsistency × P2` 敏感性通道，
永不进 Primary 门。**完整的 feasibility 决策包重述仍归 N-D2 裁定后的 N07 节点**
（本节只更正事实错误，不重开任何方法选择）。

**§13.3 逐指标状态表已被超越**：该表（`winning_days`="台账逐日余额差"、
`contract_cap_hits`/`e2_over_budget_days`=PENDING_ENGINEERING）反映 R2.3 状态。
N02 之后以代码内 `FEASIBILITY_METRICS_STATUS` 为准——`winning_days` 现由平台
权威 `day_net_usd` 发射（不再是余额差）、`contract_cap_hits` 已 COMPUTED、
`e2_over_budget_days` 为 DECISION_REQUIRED（谓词未裁，见 §14.5-1）。


---

## 15.【现势节（factory-boundary Stage I 之后，2026-08-20）——本节编号最高，与上文全部章节冲突处以本节为准】

授权：治理文档收口轮（纯 doc/governance；**零生产代码改动**）。本节只追加，
§1–§14 一字未删、未改写。

### 15.1 现势 HEAD 与已闭合的工程段

```
CURRENT_HEAD=c5c819beb5c13e52bcd7ca974a4e40787684b10f
CURRENT_HEAD_PARENT=b3ac4534486f607242f5758cecbc918cbe2157be
WORKTREE=CLEAN
TAGS_AT_HEAD=NONE（仓库共两枚 tag：mc-freeze-v1、s0-freeze-v1，均不在 HEAD）
N01=ENGINEERING_COMPLETE
N02=ENGINEERING_COMPLETE
FACTORY_BOUNDARY=STAGE_I_PASS
FACTORY_STAGE_I_DURABLE_RECORD=ops/MC_FACTORY_BOUNDARY_STAGE_I.md
FACTORY_BOUNDARY_BUILDER_RECEIPT=MC_FACTORY_BOUNDARY_REPAIR_RECEIPT.md
RECOVERY_ANCHOR=ops/MC_TO_STRATEGY_MASTER_PLAN.md §11
```

Stage I 记录为**转录件**（`RECORD_TYPE=TRANSCRIBED_EVIDENCE_RECORD`，
`ORIGINAL_REPORT_BYTES_ARCHIVED=NO`），其独立性按 QROS §2 四维度逐维声明：
context 有／authorship 有／model-family diversity **有限**（Sol 曾参与制定部分
验收判据）／empirical 不适用。**Stage I PASS 是工程验收，不是研究或运行授权。**

### 15.2 `HISTORICAL_SUPERSEDED` 指针（读者勿再把下列数字/HEAD 当现势）

| 位置 | 内容 | 状态 |
|---|---|---|
| §6 L88-89 | `COLLECTED=2676 PASSED=2676`；`MIN_COLLECTED_TESTS=2676（旧 2615）` | `HISTORICAL_SUPERSEDED` — DR-5 R1 时刻值 |
| §13.9 L470-471 | `FULL_SUITE=2761 passed`；`MIN_COLLECTED_TESTS 重钉=2714→2761` | `HISTORICAL_SUPERSEDED` — R2.3 时刻值 |
| §7 | 两个 commit（`3234958` 与"本文件所在 commit"） | `HISTORICAL_SUPERSEDED` — DR-5 R1 时刻 HEAD |
| §13.1 | 红字证明基线 `a327f1e` | `HISTORICAL` — R2.3 修复前基线，作为历史证据有效 |
| §14 全节 | N01+N02 首段现势 | 由本节续承；§14.6 的状态块以本节 15.3 为准 |

现势地板与套件（证据等级见主计划 §11.2）：

```
CURRENT_TEST_FLOOR=3380（scripts/s0_real_run.py:56 ＋ tests/test_s0_runner.py:1011 双 pin，本轮机械核实）
FULL_SUITE_AT_CURRENT_HEAD=3380/0/0（builder 自陈＋Stage I 转录；本轮未重跑）
FLOOR_LINEAGE=2615→2676→2714→2761→3118→3323→3336→3380
```

### 15.3 现势状态块（取代 §14.6）

```
UNIFIED_ATOM_LAYER=LANDED
COLD_REPLAY_SEAL_GATE=LANDED
LIFECYCLE_CONFIG_DIGEST=LANDED
PLATFORM_AUTHORITATIVE_FACTS=LANDED
M_SUPPORT_CERTIFICATE=DERIVED_FROM_TRACE
SEAL_PROVENANCE=B_PROV_LANDED（b3ac453）
BATTERY_FACTORY_BOUNDARY=LANDED_AND_STAGE_I_PASSED（c5c819b）
SEAL_CANDIDATE_SCHEMA=mc_verdict_inputs.v5
FEASIBILITY_GATE=DECISION_REQUIRED
GRID_REPLAY_STATUS=BLOCKED
CHECKPOINT0_VERDICT_REACHABLE=NO
S0_VERDICT=INCONCLUSIVE_PENDING_MC
MC_EXECUTED=NO
SUPPLEMENT_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO
MC_REGISTRY_EVENTS_APPENDED=NO
SUPPLEMENT_REGISTRY_EVENTS_APPENDED=NO
NEW_RUN_AUTHORIZATION=NONE
SUPPLEMENTS_DIRECTORIES_EXIST=NO
```

### 15.4 真实阻断（N00 与 N-D1）——不得读成"只差一个签字"

```
N00=BLOCKED_MISSING_AUTHORITY_ARTIFACTS_AND_AARON_STATE_RULING
N-D1=PROPOSED_AWAITING_AARON_RATIFICATION
N03=NOT_STARTED（BLOCKED_ON_N-D1）
N04=NOT_STARTED（BLOCKED_ON_N-D1）
N05=NOT_STARTED（BLOCKED_ON_N-D1）
```

**N00 是两层阻断**：Aaron 的三字段状态裁决**只解决状态**；Round-4 联合矩阵
正文、两个候选的正式定义、逐格签字、wrapper 定义**至今不在仓库**（本轮再次
机械核实：只有 `STRATEGY_COUNCIL=LOCKED` 一类状态令牌）。两层都补齐前，
candidate-specific strategy build 不得开工。清单见决策包
`N00_MISSING_AUTHORITY_CHECKLIST`。

**N-D1 全部为 `PROPOSED_NOT_EFFECTIVE`**：决策包内的 exact registry grammar、
输出根语义、`.partial` 规则与 trial/exposure 口径**一律未生效**，
`authorize_supplement` 与 `authorize_real_mc` 维持确定性拒绝。

### 15.5 §13.5 授权模板的现势读法

§13.5 的 `START_MC_DS_S001_DAY_STRATA_SUPPLEMENT_EXECUTION` 模板**仍不构成
授权**，且在 N-D1 批准前**语法上也无处落地**（registry 无 supplement 词表、
无 parser）。决策包已把该模板缺失的完整生命周期语法补全为**提案**，仍待裁。

### 15.6 本轮明确未做

零生产代码改动（`src/`、runner、registry parser、supplement 工具均未触碰）；
零 registry／exposure／READY／授权／运行事件；零封存件改动；零目录创建；
零探针；零研究结果值读取；未 push、未 tag、未 amend。
