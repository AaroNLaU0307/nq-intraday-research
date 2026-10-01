# MC_DR5_CONSUMER_SOURCE_MATRIX（DR-5 生产消费者来源→消费矩阵，2026-08-14）

授权：`START_DR5_MC_CONSUMER_ENGINEERING_AFTER_S0_REVEAL_REVIEW_CORRECTION`
PHASE C。逐条映射冻结来源 → 消费者原子输入 → 封存供给 → 生产/校验/测试
落点。检查封存 bundle 仅用文件名/schema/大小/哈希/manifest/治理元数据；
**未读取任何 MC_HANDOFF 研究数值**（grid 结构检查仅键/类型/长度）。

## 0. 关键问题四答（R2 更正——R1 的 YES **显式撤回**）

```
CAN_GRID_SAMPLES_BE_RECONSTRUCTED_FROM_CURRENT_SEAL=NO
MISSING_AUTHORITY=EXACT_PER_DAY_DAY_STRATA
GRID_REPLAY_STATUS=BLOCKED
RAW_DEVELOPMENT_DATA_REQUIRED_FOR_REPLAY=YES_AND_FORBIDDEN
NEW_RESEARCH_DEFINITION_REQUIRED=NO
```

**R2 事实审计（Codex 质疑成立）**：R1 的 YES 基于"seeds＋日池＋冻结算法
可重放"，漏了一个必需原子——分层抽样按 **year × volatility_regime ×
event_flag** 逐日归层（cell.method 冻结文本明载"stratified by year ×
volatility_regime × event_flag (injected mapping)"），重放 k≥1 需要
**2842 日全池的逐日 strata 映射**。封存件里有的是：headline（k=0）的
per-seed 已抽日期/逐层分配计数/day_markers、fp_alloc 层配额、digests。
**没有的是全池逐日 vol/event 归层**（DAY_STRATA 工件当时按 DR-5 分阶段
被 withheld；正式报告只含层级聚合）。digest 只能验证不能反演；从原始
Development 数据重建被本轮明令禁止。故 grid 重放 BLOCKED，
deployable_region/H1 资格层机器拒绝。Checkpoint-0 主判定不需要 grid
样本（MC §5 内层随机源 (2) "仅网格分析"），不受此阻断。三选一决策包见
MC_DR5_BUILD_PACKET.md §9。

## 1. 矩阵

| rule_id | authoritative_source | required_input | sealed_source | production_consumer | independent_validator | synthetic_test | status | refusal_reason |
|---|---|---|---|---|---|---|---|---|
| R1 路径记录 | S0 §10.1＋MC §1 | E×scn 每合约日内路径原子记录（17 字段含双 mtm 数组/stop 三元组/sizing_anchor） | `MC_HANDOFF_{E1,E2}_{4 scn}.jsonl`（8 文件全封存） | `mc/consumer.py::prepare_mc_input` 解析 | 字段集=report.FORMAL_RECORD_FIELDS；行数=manifest counts；日期序/去重 | bundle 负例电池 | READY | 文件缺/多/换型/hash 不符/行 schema 违约 → MCInputError |
| R2 模板日历 | MC §4.1（冻结算法） | 2026-08-01→2028-07-31 CME 交易日模板＋cal_offset | 不在 bundle（规范冻结算法，离线日历库生成） | `consumer.build_template_calendar` | 首尾日期钉＋计数上下界＋周末/假日抽查 | 日历确定性测试 | READY | 生成器不可用 → 拒绝（不得手编日历） |
| R3 认知层 worlds | MC §5（B=1000、块长 5、PCG64、seeds 7/13/31） | day-id 序列×B | —（代码） | `mc/bootstrap.build_worlds`（既有） | seed∈MASTER_SEEDS 强制；CRN=同一 worlds 列表复用 | 既有 test_bootstrap＋消费者 CRN 测试 | READY | 非冻结 seed → ValueError |
| R4 平台生命周期 | MC §2.2/2.3＋platform_params.yaml（冻结哈希钉） | Lucid eval→simfunded / Topstep Combine→XFA 全状态机 | —（代码＋冻结参数） | `mc/platforms/*`＋`mc/orchestrator.run_lifecycle`（既有） | 既有平台测试族 | 既有＋费用/reset/rebuy/payout/MLL 漂移负例 | READY | 参数漂移由 guards.FROZEN_HASHES(platform_params) 拒绝 |
| R5 仓位政策 | MC §3（P1-P4；整数手 min 三元；buffer=MLL 锚定） | sizing_anchor_usd/余额/floor/档位 | anchor 在 R1 记录内 | `mc/account.py`（既有） | 既有 account 测试 | 非整数仓位负例 | READY | n=0 跳过计数（非拒绝） |
| R6 Primary 决策集 | MC §2.5（冻结：2 生命周期×P2） | 组合枚举与角色隔离 | —（规范） | `consumer.PRIMARY_COMBOS` 常量＋驱动器 | verdict.py 只收 Primary；sensitivity 不可翻转 | 拼接/越权组合负例 | READY | 非 Primary 进判定 → 拒绝 |
| R7 判定表 | S0 §10.4＋MC §0（顺序 STOP→GO→β→α；量词域=Primary；gate2 守卫） | 认知层 P5/median/P95＋可行性旗标 | —（代码） | `mc/verdict.apply_verdict`（既有） | 既有 test_verdict | 顺序错误/跨组合拼接负例 | READY | 空 Primary 集 → ValueError |
| R8 EV 台账 | MC §4.4（四层会计；单位=24月总/24） | payout/fees/terminal/strategy | —（代码） | `orchestrator.Ledgers`（既有） | 既有 orchestrator 测试 | 会计链漂移负例 | READY | — |
| R9 认知/结果层分离 | MC §5 三层 | worlds→世界内均值分布；conditional aleatoric=固定世界内 M 路径；total predictive=B×M | R1+R2+R3 | `run_epistemic`＋`run_conditional_aleatoric`（R2：固定世界绑定，平铺已废）；**total predictive 未实现** | 认知层仅世界级均值；aleatoric 类型上进不了 GO 门；世界成员/长度校验 | 层混用/伪世界负例 | **PARTIAL**（total predictive 缺） | 层混用/非法世界 → 拒绝 |
| R10 收敛规则 | MC §5（B/M/K 各自加倍类别不变＋三 seed 一致＋max($25,5%)＋MCSE≤10%） | RunEvidence（run 身份/输入摘要/轴/规模/全网格实际结果） | — | **R2 重建 `convergence_from_evidence`**（verdict/漂移/MCSE 全部从证据计算，拒绝调用方声明） | 轴集/规模/provenance/seed 身份/类别词表逐项拒绝 | 缺轴/换轴/改规模/异源/伪 seed 负例 | READY（机制）；**M 轴=DECISION_REQUIRED_M_AXIS**（穷尽枚举无唯一加倍语义，生产不可组装） | 任一证据违规 → MCInputError；未收敛 → MCNotConverged |
| R11 CRN | MC §5 | 同一 worlds/流跨政策/平台复用 | — | 驱动器按 (day_ids,B,seed) 构建一次并复用 | build_worlds 确定性 | 复用身份测试 | READY | 每组合重抽 → 结构禁止（API 不提供） |
| R12 grid 标记序列 | S0 附录A＋MC §1/§5(2) | K 次 TP/FP 分层抽样日标记序列＋realized precision/recall＋trade counts＋**全池逐日 year×vol×event 归层** | headline 已抽日/逐层计数/digest/fp_alloc 封存；**全池逐日 strata 未封存**（DAY_STRATA 当时 withheld） | —（重放输入缺失，harness 无从建） | digest 只可验证不可反演 | — | **BLOCKED**（R2 撤回 R1 的 PARTIAL/YES） | MISSING_AUTHORITY=EXACT_PER_DAY_DAY_STRATA → deployable_region/H1 资格层机器拒绝；三选一决策包见 BUILD_PACKET §9 |
| R16 θ 通道绑定 | **S0 §7 L133（冻结）："θ 主 0.5、副 0.3（完整报告，不得事后升格）"** | Checkpoint-0 仅收 theta_0.5；theta_0.3 仅报告/敏感性 | day_universe 双通道均封存 | `PRIMARY_THETA_CHANNEL` 常量（源自 study.THETA_PRIMARY）＋gate 双层拒绝（epistemic 门＋verdict 门） | VerdictInput.channel 必携带；seal 绑定 primary_theta_channel | θ.3 全绿仍拒绝／θ.5 同输入放行 | READY（R2 修复；R1 误列 Aaron 决策已更正） | channel≠theta_0.5 → theta_channel_not_primary |
| R13 授权门 | DR-5 裁定＋R2 提示词 | typed **深度不可变** PreparedMCInput＋**强制外部保管链 authority**（键集=全 14 文件含 manifest，逐文件 64-hex）＋显式 MC 运行授权 | bundle＋registry＋**外部** digest 记录（盲式 attestation 表/archive inventory） | `consumer.prepare_mc_input`（expected_file_sha256 必需）＋`authorize_real_mc`；`handoff.mc_ready_gate` 原样保留 | 十项电池＋外部 custody 恒等；payload+内部 manifest 同步改写攻击夹具必败 | 全负例电池（含攻击夹具）＋无授权拒绝 | READY（R2 强化） | 缺/多/坏外部 digest、任一失配、无授权 → MCInputError/McConsumerAbsent |
| R14 曝光后冻结 | 本提示词 §D.11 | 一切可变输入在 exposure 前读入 PreparedMCInput（slots、mappingproxy） | — | PreparedMCInput 不可变构造 | 曝光后重读 source 负例 | 重读拒绝测试 | READY(本轮建) | 计算路径持路径/句柄 → 结构不可（不携带） |
| R15 ambiguous 日 | S0 §10.1（更不利顺序 或 标记双场景） | 记录级 ambiguous 旗标 | **记录 schema 第 19 字段 `ambiguous_stop_vs_floor` 显式在册**（TradePathRecord/FORMAL_RECORD_FIELDS） | R1 消费按记录字节；平台 sim 依旗标走双场景/更不利分支（既有 platforms 代码） | schema 钉（19 字段恒等） | schema 违约负例＋旗标类型负例 | READY | 旗标缺失/非 bool → MCInputError |

## 2. R13 十项验证电池（prepare_mc_input 逐项，全 fail-closed）

1 bundle exact-set（文件名集合恒等，缺/多均拒）；2 每文件 sha256 对
manifest/独立重算双核；3 trial_id＋authorized_commit 绑定（registry 快照
与 bundle 治理元数据一致）；4 engine/scenario(/platform) 轴恒等（E1/E2 ×
四场景 × 双平台常量）；5 seed/K 对 SEED_MANIFEST 与冻结常量；6 日期严格
升序且集合跨场景一致；7 TP/FP 不相交（θ 内）；8 realized counts 对账
（记录数 vs manifest counts vs 轴积）；9 冻结方法 digest
（MC_METHOD_SPEC＋platform_params 现场重算 == guards.FROZEN_HASHES）；
10 authorization snapshot（构造时注入，运行期不重读）。

## 3. 新模块所有权

`src/itsf/mc/consumer.py`（主代理authored，本轮唯一新生产模块）：
PreparedMCInput／prepare_mc_input（十项电池）／build_template_calendar／
run_epistemic／run_aleatoric／convergence_check／authorize_real_mc
（默认拒绝；`handoff.mc_ready_gate` 保留不删）。测试
`tests/test_mc_consumer.py`。不触碰既有 mc 模块的任何行为。
