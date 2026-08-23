# N-D2 ＋ N-D3 合并决策包 — Fable 裁定提案（全 32 项）

```
PROPOSAL_ID=RULING_PROPOSAL_ND2_ND3_FABLE_V1
PROPOSAL_DATE=2026-08-24
DECIDER_SEAT=Fable 5（Aaron 具名批次委托，对抗审计席）
PACKET=ops/DECISION_PACKET_ND2_ND3.md
PACKET_SHA256_RECOMPUTED=7bc92817e045af67bd6ebc0077acce63361b298ead1376b9cd5678a76ab2552a（匹配）
PACKET_COMMIT=cb8bef39f358fbeaeef982c3be32d0bc8f5f3e8e（工作区与该 commit 字节一致，git diff 空）
REPO_HEAD_AT_RULING=28cff2eba5a24db106ba708c29a3abe02fb4d843
STATUS=PROPOSAL_ONLY — 非 PACKET_OUTCOME，不释放任何 gate transition，待 Aaron 整体批准或逐项修改
REPO_WRITES=0（read-only 全程遵守）
WORKFLOWS_USED=0 / 预算 3（理由见附录三）
```

## 防火墙执行申报（先于一切裁定）

**读取白名单实际使用**：包正文全文；STUDY_0_PREREGISTRATION.md §8–§12＋附录 A；MC_METHOD_SPEC.md §2.5–§7；主计划 §5–§7、§12；FREEZE_LOG.md（冻结时点行）；IMPLEMENTATION_RESOLUTIONS.md（IR-28c/IR-29a 段）；ops/ND1_PROFILE_RATIFICATION.md；ops/TRIAL_REGISTRY.md（事件链）；EXPOSURE_LEDGER.md（台账行）；生产代码 atoms/consumer/contracts/verdict/gridmix 定向段；tests 定向段。
**禁读件零打开**：`ops/S0_T001_RESULT_DECISION_ADDENDUM.md` 正文、`ops/S0_T001_RESULT_REVEAL_ATTESTATION.md`、`S0_REPORT.json` 及一切结果段、逐 θ 结果——均未打开。
**意外暴露申报（如实）**：(1) EXPOSURE_LEDGER.md 第 19 行（允许读的运营文件）内嵌 addendum 六项纠正的摘要短语，其中含一个数值（endpoint spread 0.20477498240675374）与"16 个 zero-direction mean=0 格"字样——已隔离，未用于任何一项裁定；该量与三门任何判据量纲无关，评估为不可反推门槛通过性。(2) 包 §2.2 引用的单行断言（「可行性天花板作为独立断言记 PASS」）经包正文进入上下文——唯一用途是 O3 披露措辞中的转述。(3) 会话级已声明聚合：OVERALL_S0_VERDICT=INCONCLUSIVE_PENDING_MC、researcher_exposure=1575（来自任务提示词）。
**候选阈值出处复核（包 2.1）**：在白名单范围内复核属实——MC_METHOD_SPEC 无 0.75/0.50；预注册中 0.75 仅出现于附录 A 网格 q 上界（L268）；src 无任何 feasibility 阈值常量。三个阈值按**从零设定**处理。

---

## Tier M

```
ITEM_ID=M1
TIER=M
RULING=payout 门：per-path 布尔 = 该 path（world×phase 一次 24 个月生命周期）payout_count ≥ 1；逐世界聚合份额 s_b =（世界内 payout_count≥1 的 path 数）/M；门 = 认知层经验 P5({s_b}) ≥ 0.50，在 M5 场景集（Conservative 与 Stress）各自成立；视界末截尾周期照实记入（不剔除、不折算——未完成周期自然产生 0 个 payout 事件）；达标盈利日分布（基于平台自身计数器 total_qualifying_days）按 MC §6 全量披露但不作门。
理由=判据落在平台自己的 payout 事件上（可行性的直接实现，且避开 days_profit_ge_150 的明文禁令波及）；逐 path→世界份额→认知层分位与冻结判定层同构（§10.3 判定分位作用于认知层），避免把 B×M 混合当独立样本；P5 世界 ≥50% = 认知层 5% 逆风世界里 payout 仍是多数结局，通道在坏世界也运作；截尾照实记入与冻结 terminal 规则同构（尚不可提=0，不虚构比例现金）。
备选=混合份额 payout_event_path_share≥0.75＋Wilson 下界（拒：同世界 path 相关，Wilson 独立性前提为假、n=B×M 虚高；混合层判据与 §10.3 层分离纪律冲突）；先聚合再判定（拒：少数 path 大量 payout 掩盖分布性失败）；剔除截尾周期（拒：默认稳态，方向性放松且与 terminal 冻结口径矛盾）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES
若被裁反=改混合份额+Wilson 须同时改 M3/M4 的量词架构（层一致性），且统计上高估有效样本；P5 层改 0.75 会把 EV 强度的活揽进可行性门，可能误杀 EV 合格但通道正常的组合；剔除截尾则 GO 变易。
```

```
ITEM_ID=M2
TIER=M
RULING=frequency 门：建在 S0 §10.5 冻结输出「Oracle 月均频率」单一标量上，Oracle 月均可交易日频率 ≥ 5.0 日/月即通过；p 与年可交易日数按 §10.5 强制随报、不作门；(c) q_min ≤ min(65%,2.2p) 维持「辅助直觉检查、不决定 GO」原样，不升格；本门与 MC 场景无关（S0 数据侧测量），每组合同值；2.3 的固有暴露照实披露（门的评估必然消费已揭盲量，此为结构性事实）。
理由=阈值 5.0 从平台结构算术导出、零自由参数：一次 payout 周期需 5 个达标盈利日（Lucid qualifying_days_required=5；Topstep XFA 同为 5×$150），达标日⊆盈利日⊆交易日（代码冻结单调链），月均交易日<5 的策略在任何一个月内都算术上不可能凑齐一个周期的达标日；且计费按 30 天 rebill 滚动（冻结 billing_calendars），月粒度断流=订阅/重购成本在两次 payout 间结构性失血。5.0 是「月内完成一个达标集算术上可能」的必要条件下界。
备选=更高阈值留裕度（拒：裕度无机制推导，EV 门已管盈利强度，可行性门只验通道存在性——假严格）；建在年可交易日数≥60（拒：与 5.0/月同源冗余）；p 门（拒：p 是事件基础率非执行频率，与「经 MC 确认」的执行语义隔层）。
CONSULTED_S0=NONE（只用 §10.5 定义与平台冻结参数，未读任何实际频率值）
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES（(c) 单独标注：升格 q_min = 改变冻结文本效力，超出补定义，须走独立修订程序——本提案裁 不升格）
若被裁反=取消本门则 GO 条件的「频率…可行性经 MC 确认」失去实现，N13 无法编译 feasible 布尔；升格 q_min 触发改冻结效力的程序义务。
```

```
ITEM_ID=M3
TIER=M
RULING=integer-position 门：(a) offered 追认代码语义 = 模拟窗口内存在 S0 信号路径记录的日（consumer.py:1441，不过滤账户状态）；(b) executed = 其中 sizing 得 n≥1 且实际执行的日（冻结单调链 executed≤offered）；门的分母用「尝试日」attempted_b = skips_n0_b + executed_trade_days_b（逐世界）；(c) 逐世界 skip 份额 u_b = skips_n0_b/attempted_b，门 = 认知层经验 P95({u_b}) ≤ 0.25，在 M5 场景集各自成立；attempted_b=0 且 offered_b>0 的世界取 u_b=1.0（fail-closed）；全体世界 offered=0 → 门直接 FAIL；(d) contract_cap_hits 不进门（触顶=可行但受限），全量披露；typed-absent 照 token 披露、永不折算为 0。
理由=(a) 代码已冻结一种可机械复核的读法（信号日∩窗口）；换「存活日」会用无信号日稀释分母（方向性放松），换「结构合格日」把门挂到 S0 侧口径脱离 MC 执行语义。(c) 分母用尝试日：门测的是「sizing 被咨询时多久饿死一次」，死账户/halt 日无 sizing 咨询，进分母只稀释饥饿信号；P95 于坏尾（skip 是坏量）；0.25 的机制 = executed 子集是窄止损日子集，skip 率超 1/4 时 E1 证据（全部信号日上测得）对已执行子集的可迁移性被选择效应实质扭曲——门止损的是证据搬运缺口。(d) 触顶日仍执行，饥饿门管存在性不管最优规模。
备选=分母用 offered（拒：稀释）；阈值 0.10（拒：P2=$100 对 MNQ 波动分布天然产生一部分宽止损日，0.10 把正常摩擦当结构失败——假严格）；cap_hits 计入门（拒：混淆受限与不可行，且 absent 语义被迫折算）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES
若被裁反=分母改 offered → skip 率数倍缩小（包正文明言），0.25 必须同时重设（单改必错）；取消 u_b=1.0 规则 → attempted=0 的死账户世界从门里消失，饥饿与死亡互相掩护。
```

```
ITEM_ID=M4
TIER=M
RULING=合成与区间：(a) 三门 AND，逐 Primary 组合评出单个 feasible 布尔（喂 VerdictInput.feasible），任一门不过或任一门输入退化（M3 fail-closed 条款）即 False；(b) Wilson 区间不采用——份额类判据的不确定性由认知层分位承担（M1 P5／M3 P95，与冻结判定层同一机器），点估计与完整分布随 feasibility.json 全量披露；(c) 三阈值 = M1 0.50（P5 层）、M2 5.0 日/月、M3 0.25（P95 层），全部为从零设定（2.1 复核确认无出处）。
理由=三门检验三个互不替代的必要条件（收入通道／信号频率／sizing 存活），必要条件按合取合成，无自由度；Wilson 被拒的机制：atoms 按世界聚簇、世界内 path 高度相关，Wilson 以 n=B×M 独立为前提会系统性收窄区间（虚假确信）；认知层分位是冻结文本已为判定量选好的不确定性机器，同时解决相关性与层混合。
备选=点估计+任一门过（最松端，拒：必要条件不可析取）；Wilson 下界+AND（拒：比点估计严但统计前提为假——假严格与假宽松同坏）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES
若被裁反=改 OR/两门过 → GO 条件三者并举的冻结措辞被弱化，须单独论证冻结允许析取；改回 Wilson → M1/M3 量词整体重导（层架构联动）。
```

```
ITEM_ID=M5
TIER=M
RULING=场景归属：feasibility 的路径类门（M1/M3）在 Conservative 与 Stress 两场景各自计算，逐组合两场景全过才置 feasible=True；M2 与场景无关；Base 与 Severe 的可行性原始量全量披露、不进门。
理由=冻结判定表已把决策权重放在恰好这两个场景（Conservative P5／Stress 中位数），可行性子句在同一行 GO 条件里并列出现，最贴文本的读法是与 EV 证据同场景共行；Severe 入门=冻结后新造判定面（EV 腿自己都不受 Severe 约束），Base 单用=把门挂在决策层不看的场景上。
备选=仅 Conservative（拒：同行条件被拆开读，Stress 侧通道断裂不拦 GO）；全场景 AND（拒：Severe 扩权是假严格）；Base（拒：镜像放松）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES
若被裁反=仅 Conservative → N17 须显式披露 Stress 场景通道风险窗；全场景 AND → 须为 Severe 的决策权补冻结文本外论证。
```

```
ITEM_ID=M6
TIER=M
RULING=K 收敛对象 = 附录 A（v0.6）已冻结定义的两张分类图——positive_EV_region 与 deployable_region（逐 cell 按冻结定义算出的 (q,r)→类别映射）；比较同 seed 下 K 与 2K 两次网格分析的两张图，等价判据见 M8；明确不用不消费 K 的 Checkpoint 类别做对象（主计划 §5 禁令，空验证）。
理由=规则 (a) 说「判定类别不得变化」，网格层唯一有类别结构且消费 K 的对象就是这两张冻结区域图；定义逐字已冻结（Conservative P5>0；同组合全判据），无需发明新统计量；deployable_region 是「有资格支持进入 H1」的唯一对象，其稳定性正是 K 存在的理由。
备选=仅 positive_EV_region（拒：H1 资格挂在 deployable 上）；关键分位数作唯一对象（拒：连续量漂移可不翻类，「类别不变」失去载体——分位检查由 M9 补充承担）；裁 K 不适用 (a)（拒：K 是 §5 明列加倍轴且恰是抽样轴，豁免需 IR-29a 级"非抽样轴"论证而 K 不满足）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（对象选择不改 GO/STOP 方向；区域非 Checkpoint 输入，见 M7）
POST_FREEZE_DEFINITION=YES
若被裁反=对象改分位数-only → M8 失去载体、M7 类别语义悬空；对象含 Checkpoint 类别 → 触发 §5 禁令。
```

```
ITEM_ID=M7
TIER=M
RULING=region 角色：两 region 对 Checkpoint-0 判决是报告项（不进 GO/STOP、不作 kill）；但其 K-收敛（M6/M8）是网格分析章节自身的有效性前置——K 臂未收敛 → 按 (e) 对 K 加倍重跑（受已裁 GridRepeatPolicy.max_doublings 上限约束），未收敛期间网格章节封存为 NON_CONVERGED，deployable_region 不得支持任何 H1 进入宣称；Checkpoint-0 判决不因网格未收敛被扣押——判决不以网格结果为证据基础（verdict.py 只消费 VerdictInput 分位与 feasible；feasibility 门走 Oracle 通道计数，均不含网格）。
理由=附录 A 冻结限定「仅为可行性边界，不构成 H1 表现宣称」——把 region 升为 kill 等于冻结后授予它判决权（冻结文本恰在剥夺方向写死了它的地位）；反向也不放松任何东西（region 从未是判决输入）。(e)「禁止用未收敛结果判决」按「判决所用的结果」读：判决用的是 B/seeds 臂与 (c)(d) 覆盖的判定统计量；网格未收敛冻结的是网格自己的输出资格（H1 入场）——正是它有权力的那一层。
备选=网格未收敛扣押整个判决（更保守读法，如实呈报但拒：让非判决诊断以噪声人质挟持冻结主判决，算力暴露仅由 max_doublings 兜底；Aaron 若采此读法，M8 容差带从"减少重跑"升级为"判决能否发出"的关键路径，E3/M10 算力须按最坏重算）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（两个方向都不该在冻结后移动权力）
POST_FREEZE_DEFINITION=YES
若被裁反=deployable_region 升为 GO 判据 → 与附录 A 冻结限定正面冲突，须走冻结修订而非裁定；采扣押读法 → N16 最坏时延由网格收敛决定。
```

```
ITEM_ID=M8
TIER=M
RULING=等价判据 = 带边界带的相等：K 与 2K 两张图逐 cell 必须同类，唯一豁免是「边界带 cell」——其定类统计量（Conservative P5；deployable 判据另含 Stress 中位）在 K 与 2K 两次取值都落在冻结 (c) 容差 max($25, 相对5%) 以内贴零（|值|≤容差）且两次取值之差亦 ≤ 同一容差；此类 cell 在两张图中一律改标第三类 boundary_band 后重比，图仍须逐 cell 相等；任何非边界带翻类 = 未收敛 → 按 (e) 加倍 K 重跑，直至收敛或触 GridRepeatPolicy.max_doublings；触限仍未收敛 → 网格章节 fail-closed 封存为 NON_CONVERGED（M7 后果生效），不得静默放行。
理由=纯 exact equality 在离散网格上会因单个贴零 cell 的 MC 噪声翻转而无限加倍——不是保守，是不可终止；自由发明第二个容差是新数字。用冻结 (c) 的 max($25,5%) 做边界带宽度是唯一零新数字方案：贴零幅度小于判定容差的 cell 其符号本在冻结精度之下，诚实标 boundary_band 比强迫站队更真；max_doublings 是已裁结构（DR-M6-E）。
备选=exact equality（拒：非终止风险）；「允许 ≤N 个 cell 翻转」（拒：N 是凭空新数字，且允许非贴零 cell 翻转吞掉真失稳）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（不触 GO/STOP；比 exact 弱、比自由容差严，另强制 boundary_band 诚实披露）
POST_FREEZE_DEFINITION=YES
若被裁反=改 exact equality 须同时给 max_doublings 触限处置（否则 N16 无终止保证）；改自由 N-cell 容差 → 无出处新数，N17 按 2.1 同款披露。
```

```
ITEM_ID=M9
TIER=M
RULING=(a) rule-(c) 移植到 cell 层、仅用于 K 臂：每 cell × Primary 组合的键集 = {Conservative 认知层 P5, Stress 认知层中位数}（即两张区域图的定类统计量本身），K→2K 变化须 ≤ max($25, 相对5%)；(b) 美元项在 cell 层保留原义——cell 统计量与 §4.4 同量纲（月均 prop_operating USD），$25 直接适用、数值不改；非 USD 键（realized precision/recall、样本计数等）不受 (c) 管辖，属配置/身份数据，K→2K 必须逐位相等，不等即未收敛。
理由=(c) 原作用对象（§4.4 月均 prop_operating USD 分位）在 cell 层有直接同量纲对应物，移植零换算零新数；键集取定类统计量因它们是 M6/M8 的力学来源——分位漂移超容差而未翻类是「正在滑向翻类」的前兆，(c) 显式拦截；对 Checkpoint 自身的量，(c) 保持原冻结作用域。
备选=键集扩到全部 cell 输出分位（拒：与 M8 分类图判据冗余、报告噪声大）；美元项在 cell 层作废只用 5%（拒：量纲就是 USD/月，贴零 cell 的相对 5% 退化为零容差）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（K 臂新增漂移检查，属诚实性）
POST_FREEZE_DEFINITION=YES
若被裁反=移植取消 → M8 边界带失去冻结数字来源，须另立数；非 USD 键若套 $25 → 量纲错误。
```

```
ITEM_ID=M10
TIER=M
RULING=量词：(a) K 加倍在全部三个 master seeds 上各做（3×{K,2K} 网格分析）；(b) B 加倍同样三 seeds 各做（3×{B,2B} 全量）；M 轴不加倍——IR-29a 已裁生效（穷尽枚举支撑豁免），本项遵行不重裁；收敛要求 = 每 seed 各自满足 (a)/(c)/(d)，且 (b) 跨 seed 判定类别一致在基础档与加倍档都成立；(c) cross-seed region：三 seed 各自出图全量披露，正式发布 region = 三图交集（positive/deployable 均取交集，boundary_band 取并集），任何 cell 三 seed 异类落入并集边界带披露。算力形态如实呈报：3 seeds×（基础全跑＋2B 全跑）＝6 次全量 MC，另加 3 seeds×2K 网格通道重跑（2K 只重跑网格通道，Oracle 主通道不消费 K）；α 分支按 M14 使主通道认知层算力 ≈×2；与 E3 同席呈 Aaron。
理由=S0 现势聚合为 INCONCLUSIVE_PENDING_MC——本次 MC 的存在理由就是边界邻近，而「单 seed 加倍收敛、其余 seed 不收敛」恰是边界邻近时最可能的失效形态；只在一个 seed 上做加倍等于假设掉要检验的东西。交集发布是零新参数的保守合成：只有三条独立随机流都认账的 cell 才进正式图。
备选=单 seed 加倍（省 4 次全量跑；拒为默认，留作 Aaron 的显式降档选项——残余风险=seed 特异未收敛不被发现，须 N17 披露）；region 取并集（拒：单流侥幸 cell 入图）；三图逐 cell 强制相同（拒：把 (b) 的「判定类别一致」扩写成逐 cell 一致，强于冻结文本且与 M8 边界带冲突）。
CONSULTED_S0=[OVERALL_S0_VERDICT=INCONCLUSIVE_PENDING_MC（聚合级，来自任务提示词/包正文，非本轮查阅封存值）]
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES
若被裁反=降单 seed 加倍 → 残余风险披露义务；M 轴要求加倍 → 与已生效 IR-29a 冲突，须先撤销该 IR。
```

```
ITEM_ID=M11
TIER=M
RULING=fixed-world 选择 = 选项 (b) 的确定化形式：conditional_aleatoric 报告固定三个世界——B 个世界按世界均值 monthly prop_operating EV 升序排序，取序号 ⌈0.05B⌉、⌈0.5B⌉、⌈0.95B⌉（B=1000 → 第 50、500、950 位）的世界，平手取世界索引小者；每 Primary 组合 × M5 场景集各报一组；规则为纯排序统计量、零自由裁量；实现时 test_no_fixed_world_selection_rule_was_invented 由 N07 替换为「断言恰为本已批规则」的守卫（守卫对象从"无规则"变为"仅此规则"）。
理由=(a) 单个预注册世界在揭盲后指定可被质疑，且单世界高方差低信息；(c) 全部 1000 世界条件切片使报告与封存字节爆炸（E2 custody 线性放大），为一个冻结为「不作 GO 门槛」的诊断层付出全量成本不成比例——且切片可按需从封存 handoff 冷重放导出，(c) 的边际价值趋零；(b) 的排序统计量覆盖中位与两尾，「邻近」被精确化为 order statistic，无需邻域度量。
备选=(a)（拒：post-hoc 指定嫌疑）；(c)（拒：成本，见上）；(b)＋距离度量定义邻近（拒：度量选择又是新自由度）。
CONSULTED_S0=NONE（规则只引用 MC 运行内排序位）
MAKES_GO_HARDER=NO（诊断层报告口径；冻结明令 aleatoric 不作 GO 门槛）
POST_FREEZE_DEFINITION=YES
若被裁反=改 (c) → E2 预算与封存字节重估；改 (a) → 须 Aaron 亲自指名世界索引并披露指定时点在揭盲后。
```

```
ITEM_ID=M12
TIER=M
RULING=α 敏感性检查唯一对象 = 认知层 bootstrap 以 S0 §9 已冻结的 Sensitivity 块长 21 完整重算（同 B=1000、同三 seeds、同穷尽相位支撑、同组合域、同场景统计）；一次性判决量词与门槛逐字沿用主门槛：存在同一 Primary E1 组合，在块长-21 结果上 Conservative P5>0 ∧ Stress 中位数≥0 ∧ 可行性（M1–M5 定义在块长-21 世界上重算）通过 → GO，否则 STOP；gate2_cost_guard 语义同时适用——块长-21 下仅 Lucid 组合满足者，因一次性判决无 α 可去，判 STOP；门槛零降低（冻结明文）。
理由=α 是兜底类（含 Lucid-only 降级与分腿失败等混合证据形态），共同疑点是边界证据对统计机器假设的脆弱性；块长是 S0 §9 冻结命名的唯一敏感性轴（Primary 5／Sensitivity 21），检查它=检验时间依赖结构假设是否驱动了边界结论——机制上正对 α 的病灶，且全部机器均为冻结件、零新自由度。
备选=IR-28c +1 tick 成本敏感性作对象（拒：role 已裁死 never_primary，用作 α 判决输入=参与决定 GO/STOP，与已生效裁定冲突；成本脆弱性由它作为常设敏感性披露继续覆盖）；B 加倍作对象（拒：已是 (a) 收敛义务，复用即空验证——与 K 禁令同构）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES
若被裁反=换成本敏感性对象 → 须先解除 IR-28c 的 never_primary 钉定（独立程序）；换任何消费收敛臂的量 → 落入伪收敛同款空验证。
```

```
ITEM_ID=M13
TIER=M
RULING=β 替代风险结构集合的穷尽枚举 = Primary 决策集内的两个 E2 组合：{lucidflex_50k_eval_to_simfunded × P2 × E2, topstep_50k_stdpurchase_xfastd_nodll × P2 × E2}，别无其他；量词镜像冻结 GO 的存在量词：存在其中同一 E2 组合满足完整主判据（Conservative P5>0 ∧ Stress 中位数≥0 ∧ 可行性按 M1–M5 同定义在该 E2 组合上评出）→ GO，否则 STOP；门槛与主门槛完全相同、零降低；gate2_cost_guard 同时适用（仅 Lucid E2 满足 → STOP）。
理由=集合不是选出来的，是被冻结文本逼出来的：MC §2.5 把 P1/P3/P4 与一切生命周期变体钉死为 secondary_sensitivity 且「不得翻转 Primary 判决」——β 的替代结构从那里取即违反冻结角色表；Primary 集内的风险结构轴只有 E1/E2 一根（verdict.py 冻结 Primary=2 生命周期×P2×{E1,E2}），「替代风险结构」的唯一合法外延=E2。此读法统一覆盖 β 两个触发臂：β(i)（E2 有 EV 证据而 E1 无）本就是 E2 在申请；β(ii)（E1 EV 过而可行性败）的唯一冻结内替代也是换风险结构=E2。
备选=纳入 P1/P3/P4（拒：违 §2.5 冻结角色；且三者预算≤P2，对 integer-position 失败方向机制上只会更糟）；发明新风险治理结构（拒：即发明新策略候选，明令禁止）；空集合（拒：冻结文本明写 β 有一次替代结构检查）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=YES（最小合法集合=2 元；集合越大 β 翻 GO 越易）
POST_FREEZE_DEFINITION=YES
若被裁反=扩集合 → 每加一元多耗研究自由度（冻结文本自记账），且须为绕过 §2.5 角色钉定给出冻结级论证。
```

```
ITEM_ID=M14
TIER=M
RULING=YES：α 分支（块长-21 全套判定输入）与 β 分支（两 E2 组合完整主判据评估）随主 MC 同一授权、同一运行预计算，各自独立密封（独立 payload、独立 SHA-256、独立封存事件），manifest 先行登记（G7 形态）；揭盲只开实际触发分支（M15）；未触发分支永久密封。算力披露：β 分支零额外模拟（E2 组合本就是 Primary 集成员，STOP 行要求全评）；α 分支 ≈ 主通道认知层算力 ×2（块长-21 平行世界组），纳入 M10 的 seed×加倍表（α 分支同受 (b)/(c)/(d) 与 B 加倍臂约束——判决可能落在它身上，(e) 收敛义务随之）。
理由=预计算+盲封是「看到 primary 再设计检查」指控的唯一结构性免疫（包正文所述实质理由，经查属实）；α 分支若事后计算，块长-21 运行将发生在已知主结果的时点，2.3 型披露再添一层。成本是真金（≈2×主通道），如实呈报。
备选=事后计算（拒：时序污染自造）；只预算 α 不预算 β（无意义：β 免费）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（时序诚实性，不动门槛）
POST_FREEZE_DEFINITION=YES
若被裁反=NO → M15 自动失效、§7 揭盲序重导、G7 形态改变（包 §8 已列）；且 N16 若判 α，检查不可避免在知主结果后运行，N17 按 2.3 同款披露。
```

```
ITEM_ID=M15
TIER=M
RULING=确认主计划 §7 步 5–6 预设（N-D3 第 9 项=YES，成立于 M14=YES）：揭盲序 = sealed/exposure manifest 先行 → primary verdict 揭盲 → exposure ledger → GO/STOP 即终局 → 落 α/β 时仅开对应预封分支 → 未触发分支永不揭示 → 同一主门槛一次性判决 → append-only 终局事件 → 禁降门槛、禁二次选择；本项随 M14 连动，M14 若被改 NO 则本项自动失效、§7 重导（非本提案可预写）。
理由=序列力学在于每步先固定「将看什么」再看（S0-T001 manifest→reveal 实史模式）；未触发分支不可见杜绝「两条都看挑好的讲」；与 M14 联合构成完整时序免疫。
备选=双分支都揭（拒：免费获得一次未消费自由度的窥视）；先揭分支后揭 primary（拒：分支身份由 primary 决定，颠倒因果）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（揭盲纪律）
POST_FREEZE_DEFINITION=NO（§7 已成文，本项确认预设非补洞）
若被裁反=NO → §7 步 5–6 重写归 Aaron/builder 下轮，G7 的 manifest/exposure 形态同步重导。
```

## Tier D

```
ITEM_ID=D1
TIER=D
RULING=E2 over_budget 谓词（三基准各定其一，共同定义 per-day 布尔）：适用域 = E2 组合、当日实际持仓 n≥1 的交易日；over_budget_day ⇔ 当日整仓 realised_loss（USD，close-path 日终口径）> 当日该组合 sizing 政策的 policy risk_budget（Primary=P2 即 $100/笔；其他政策通道用各自政策预算）；total_e2_over_budget_days 计数器绑定此布尔；P(intraday_adverse_loss>预算) 用同一预算基准、损失取整仓盘中 adverse-path 最不利值，作为并行第二布尔与概率披露（N07 增设独立累加器，不与前者混计）；无持仓/halt/死账户日维持 NOT_APPLICABLE_NO_TRADE，E1 日维持 NOT_APPLICABLE（冻结披露 E2-scoped）；三基准 = {realised 与 intraday_adverse 双布尔并行、整仓口径、policy budget 口径}；裁定生效后方可翻转 OVER_BUDGET_PREDICATE_RULED=True。
理由=预算基准取 policy budget 是文本指称：MC §3 全节唯一名为「预算」的量就是 sizing 公式里的 risk_budget，n×anchor 读法要求「预算」指一个该节从未用此名的派生量；损失口径取整仓是量纲一致性：risk_budget 是整仓政策量，逐合约损失对它无定义——而「逐合约损失 vs anchor」的信息冻结文本已另行强制（realised_loss/sizing_anchor 分布；loss/anchor>n ⇔ 整仓损失>n×anchor，n×anchor 侧超越率已被该分布完整覆盖，不因本裁定丢失）；双布尔并行因冻结文本强制报告两个 P()，各需自己的日布尔——只定义一个等于砍掉一半冻结义务。
备选=n×anchor 基准（拒：文本指称弱；信息由 ratio 分布覆盖；n 被 scaling 截断时两口径之差恰是截断日子集，作为派生披露列随报即可）；逐合约口径（拒：量纲）；只定义 realised 一个布尔（拒：冻结义务是两个 P()）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（纯披露谓词，不入任何门——E2 组合本就不可 GO（GO 要求 E1 组合）；机制=文本指称+量纲一致，非松严选择；n×anchor 侧信息未丢）
POST_FREEZE_DEFINITION=YES
若被裁反=改 n×anchor → 超预算率数值级放大（floor 截断日全体易位），与 ratio 分布形成双重计数表观矛盾，N17 须解释两组数为何不同源；改逐合约 → P() 分母语义与 §3 预算量纲脱钩。
```

```
ITEM_ID=D2
TIER=D
RULING=(a) 冻结 §4.4 层-1 文字一字不动；缺陷按 MC 规范 §7 自带的 Evidence Resolution Addendum 通道处理：落 MC1.x addendum（Lucid 官方生命周期证据原文+哈希 → registry/params 更新 → evidence-resolution commit → FREEZE_LOG 登记），声明层-1 的权威实现语义 = 平台真实生命周期（评估期利润按平台规则于通关时点弃置），冻结文字与实现的偏差自此为已登记已量化的定义-实现分歧；(b) 双口径累加器并存保留至 N17 终局封存（差额序列全程可测并随报），终局后旧口径按 O4 勘误通道退役。判定统计量零接触——prop_operating_EV = payout_cash + terminal_cash − fees 不以层-1 为输入，绝缘由 test_checkpoint0_statistic_is_insulated_from_layer1_accounting 钉定（本轮核实该测试存在且如包所述）。任何会改动判定统计量的裁法越出本项授权，须单独提请 Aaron。
理由=冻结文本自备「冻结后官方证据修正」通道（§7：状态机语义变化必须走此流程），Lucid 弃置评估期利润正是平台状态机语义的官方事实——用冻结自带通道处理，比改字（预注册 §11「依据结果修改冻结定义」禁令的邻域）与裸披露偏差（错定义永挂权威名）都干净；双口径保留到 N17 是差额可审计的唯一办法。
备选=直接改 §4.4 文字（拒：post-freeze 改字先例，且 addendum 通道等效合规）；只披露不落 addendum（拒：§7 明文要求走流程）；立即退役旧口径（拒：差额失测）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（判定统计量绝缘，测试钉定）
POST_FREEZE_DEFINITION=YES
若被裁反=选择改冻结文字 → 须走冻结修订并在 N17 披露改字事件本身；立即退役旧口径 → 层-1 历史可比性断裂。
```

## Tier O

```
ITEM_ID=O1
TIER=O
RULING=θ0.3 通道报告与 θ0.5 主通道完全同构：同 schema、同组合覆盖（Primary 全量 + secondary_sensitivity 全量，按 §2.5「完整报告」义务）、同 feasibility 原始量、同封存与 custody 待遇；通道标签钉 theta_0.3；consumer 的 Checkpoint 门继续拒其进入 VerdictInput（θ 主 0.5 冻结于 S0 §7、不得事后升格，已由代码 gate 强制）；字节与 custody 成本按同构比例上浮，纳入 E2 预算观察。
理由=§2.5 对 sensitivity 层的冻结义务本就是「完整报告；不得翻转」；θ0.3 是冻结副通道，砍规模=选择性报告的结构性开口（「副通道当年被少报了」不可反驳）；同构是唯一无新自由度的规模定义。
备选=仅 Primary 组合（拒：违 §2.5 完整报告义务贴近读法）；仅摘要统计（拒：摘要字段选择本身是新自由度，且冷重放可从全量导出摘要、反向不行）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（报告规模，不动门槛）
POST_FREEZE_DEFINITION=NO
若被裁反=砍到仅 Primary → N17 须披露副通道非同构及理由；custody 分钟按比例下降（量化于 E2）。
```

```
ITEM_ID=O2
TIER=O
RULING=追认算术导出路径为终态：sensitivity_adverse_plus1 以 Primary records 纯算术导出（adverse 只作用 E1 止损侧、每止损日恰 −$0.50/合约、线性精确、E2 零 by construction、乘子后向量 {Base 2, Cons 3, Stress 3, Severe 4} 逐值钉定、role=never_primary、校验器拒篡改——以上均为已接线已测状态，本轮核实 IR-28c 记录与代码状态相符）；不要求真实重放；唯一附加条件：N16 的 cold_replay_observation_set 覆盖清单须含对该导出向量的独立重算比对（若现行 seal 校验已含，条件即满足，N07 复核勾销）。
理由=在 IR-28c 已冻结的定义域内导出是恒等式而非近似——「+1 tick=每止损日 −$0.50/合约」下 delta 是止损日计数的线性函数；重放只能检验实现，而实现由独立 cold reducer 逐位重算覆盖；真实重放边际信息为零，代价是一轮算力+一轮封存+一个新出错面。M12 已把 α 检查对象定为块长-21（非本路径），never_primary 角色无冲突。
备选=真实重放（拒：零边际信息；Aaron 若仍要，属独立性仪式的合法偏好，工程无害但计入 N16 时延）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO
POST_FREEZE_DEFINITION=NO（IR-28c 已裁，本项终态追认）
若被裁反=要求重放 → N16 增一段运行与封存；结果按构造应与导出逐位一致，任何不一致=实现缺陷（届时反证本裁定比对条件有值）。
```

```
ITEM_ID=O3
TIER=O
RULING=late-phase bias 披露定稿措辞：「本研究的下列方法定义在 S0-T001 揭盲（2026-08-14，researcher exposure 1575）之后才被最终确定：feasibility 三门（M1–M5）、K 收敛对象与容差带（M6–M9）、加倍×seeds 量词（M10）、fixed-world 报告规则（M11）、α/β 检查的对象与集合（M12–M13）、E2 over_budget 谓词（D1）、层-1 会计语义（D2）。其中 frequency 门在定义上锚定已揭盲的 S0 §10.5 频率输出（结构性，不可修复，仅可披露）；另有一份揭盲后文档（ops/S0_T001_RESULT_DECISION_ADDENDUM.md）曾就 feasibility 作出断言，其效力由 Aaron 单独裁定。上述定义的裁定者为独立于 builder 的对抗席，全部裁定申报 CONSULTED_S0 且以让-GO-更难为并列时取向，但时序事实本身不可消除。」落点 = 三处并行：STUDY_0_REPORT 方法/限制章、N16 post-run attestation、N17 揭盲终局事件（步 1 manifest 随行）。
理由=这是 M/D 层全部 POST_FREEZE_DEFINITION 标记的收口件——2.2/2.3 披露义务在此落地；三落点对应三类不可跳过的读者（报告读者/审计者/终局链）；措辞点名机制（哪些定义、为何不可修复、谁裁的、什么偏向）而非泛泛「存在事后定义」。
备选=仅报告内（拒：审计链读者可不经报告正文）；泛化措辞不点名（拒：不可核对=不可反驳=无披露力）。
CONSULTED_S0=NONE（措辞引用的 1575 与揭盲日期为已声明聚合）
MAKES_GO_HARDER=NO（披露义务）
POST_FREEZE_DEFINITION=NO（本项即披露机制本身）
若被裁反=削落点 → 相应读者群失去披露；Aaron 增删点名清单须与相应项的 POST_FREEZE 标记联动。
```

```
ITEM_ID=O4
TIER=O
RULING=批准勘误程序、不预批内容：设 append-only 勘误登记件（N07 落 ops/FEASIBILITY_ERRATA_REGISTER.md；新建文件属实现阶段动作非本轮），每条勘误必含 {目标文档+行、原文逐字、更正后文本、理由、NUMERIC_CHANGE=NO 声明}；只改表述、封存字节零接触（勘误活在登记件里，被勘误文件一字不动——与 TRIAL_REGISTRY「勘误以新事件追加」同款纪律）；具体勘误清单须逐条枚举后由 Aaron 一次性批准生效；本提案不含对任何未枚举内容的空白背书；任何触及已封存数值的「勘误」自动越权、fail-closed。
理由=包正文未附勘误清单——对未枚举内容整体批准是空白支票，fail-closed 下只能批程序不批内容；append-only 登记件形态是本仓已验证的勘误纪律（registry 头部规则）直接复用。
备选=整体预批「凡与现势不符者」（拒：空白支票）；就地改历史文档（拒：append-only 纪律与封存完整性）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO
POST_FREEZE_DEFINITION=NO
若被裁反=若 Aaron 愿整体预批 → 至少要求 builder 先出全清单快照并哈希，批准绑定该哈希（否则集合可事后膨胀）。
```

## Tier E

```
ITEM_ID=E1
TIER=E
RULING=追认 N01 现实现（规范化纯 float 统计核）为权威实现，范围限 mean/SD/SE（percentile 已双分支恢复 NumPy-linear 逐位、不在本项；DR-M6-H worst-day 估计量另案未决、本项不触碰）；追认绑定两条件：(i) 「与 numpy ULP 级差异（max_rel≤1.7e-12）、估计量族不变」的效力范围限于已执行测试尺度，生产尺度数值行为由 E3 冒烟中「独立 cold reducer 于 B=1000/M=穷尽支撑逐位复算一致」关卡承接；(ii) 「numpy 位兼容不可达（pairwise 求和序非契约）」作为结构性事实记入 N17 方法披露，「恢复 R2.3 位连续性」从一切后续目标清单移除。生产从未执行 ⇒ 零封存数字被改，追认不构成任何历史数字重述。
理由=独立冷重放的前提是「能写成两份实现都可逐位复现的书面规范」——numpy 内部求和序做不到而规范化纯 float 做得到；这不是精度取舍，是可审计性的构造要求；1.7e-12 相对差与判定容差 max($25,5%) 相距 12 个数量级以上，估计量族未变，统计意义为零。
备选=回退 numpy（拒：冷重放逐位复核失去书面规范基础——独立验证降级为同库复跑）；要求任何位连续性恢复方案（拒：已证不可达）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（可审计性工程；条件 (i) 把尺度外推的口子交给 E3 关卡）
POST_FREEZE_DEFINITION=NO（数值实现约定，非冻结方法量）
若被裁反=回退 → 冷重放规范问题重开且位连续性依然不可达（两头空）；不绑条件 (i) → 生产尺度数值行为在 N16 首跑当场首验（E3 的反面）。
```

```
ITEM_ID=E2
TIER=E
RULING=接受实测外推预算（+91.6 MB 常驻/prepared、全量重解析≈8 s、records 规范摘要≈24 s、observation set≈2.5–3.5 min、40 set≈100–140 min、重放峰值≈0.9 GB）为 N16 规划口径；不做缓存（cold 语义）、不跳重解析（包正文列为不可选，本裁定确认）；按文件切分的增量摘要方案本轮不要求——验证路径在真实运行前夕的改动是对最完整性关键组件的无谓回归面，推迟到 N16 后维护窗；设 fail-closed 绊线：E3 冒烟实测 custody 总时长 >2× 外推上界（>280 min）或峰值内存 >2 GB → 暂停并回开本项，先裁增量方案再进 N16；O1/M11/M14 的报告规模裁定使封存字节上浮，绊线以冒烟实测为准而非今日外推。
理由=100–140 分钟对一次决定性终局运行是可承受的一次性成本；成本压缩两条路里冻结语义只允许「切分摘要」方向，其收益（分钟级）与风险（验证器改动引入缺陷）在 N16 前不成比例；绊线把「外推错了」从静默吞掉改为显式回开。
备选=现在做增量切分（拒：见上）；无绊线接受（拒：外推基于 synthetic 三档，尺度外推需失效出口）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（运维预算；绊线是 fail-closed 而非门槛）
POST_FREEZE_DEFINITION=NO
若被裁反=要求先做增量方案 → N16 推迟一轮验证器改动+复审；去绊线 → 冒烟与真实运行间失去资源失控显式停点。
```

```
ITEM_ID=E3
TIER=E
RULING=要求：N16 之前必须完成一次生产规模冒烟并 PASS，作为 READY 前置。规格：数据=纯 synthetic（固定种子生成器、零真实 Development 字节、生成规范随 SMOKE 工件存档）；形态=两跑：基础档（B=1000、M=穷尽相位支撑、k_per_seed=200、seed 7，全管线：主通道+网格通道+α 块长-21 分支+feasibility 归约+custody 链+一次完整 cold_replay_observation_set+收敛比较器对拍）与 2B 档（B=2000 同 seed，压内存/耗时上界）。PASS 判据（全部机械）：(1) 两跑零异常完结；(2) 全部输出无 NaN/Inf、typed-absent 零折算；(3) 同 seed 重执行归约输出逐位相同；(4) 独立 cold reducer 生产尺度逐位复算一致（E1 条件 (i) 落点）；(5) type-7/percentile 边界自检在生产 N 上通过；(6) 时长与峰值 RSS 落档，custody 实测 ≤2× E2 外推（绊线联动）；(7) 写盘限 SMOKE 专用输出根，零 registry/exposure/封存目录接触。治理：冒烟需 Aaron 单独一句执行授权（本提案不构成授权）；登记于 ops 事件但用独立 SMOKE 命名空间（SMOKE-001），非 formal trial、不动 N_trials、零 exposure（无真实数据）、id 序列与 MC-R### 永不混用（G3/G6 联动）；任一判据不过 → 修复后整套重跑，N16 保持封锁。
理由=不做冒烟，N16 同时是这套代码的首次生产规模执行——一次写 registry、消耗研究自由度、结果终局的运行去承担浮点累加序、分位边界、内存耗时三类只在尺度显形的首跑风险；R2.3 的「生产规模」夹具是已删除 API 伪造的摘要，历史上没有任何一次真跑可依；PASS 判据全部机械化，避免冒烟自己变成一次「看结果」的机会。
备选=真实数据不封存（拒：真实 Development 字节入引擎=事实暴露面，「不封存」削弱的是保管而非暴露）；仅基础档不跑 2B（拒：内存上界正是 2B 档，M10 加倍臂会真跑它）；不要求冒烟（拒：首跑风险与终局运行合并）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=YES（真实运行新增硬前置）
POST_FREEZE_DEFINITION=NO（工程门，不触冻结方法）
若被裁反=取消冒烟 → N16 承担首跑风险，N17 须披露「生产规模首执行=决定性运行」；砍 2B 档 → M10 的 2B 臂在真实运行中首次触顶内存。
```

## Tier G

```
ITEM_ID=G1
TIER=G
RULING=词表闭合枚举，形态沿用 S0-T001 registry 状态机与 ND1-R2 语法族（沿形态、不假定同一）：事件 = {MC_PACKET_DRAFTED, MC_PACKET_APPROVED, MC_RUNNER_READYCHECKED(含 SMOKE_PASS 引用), MC_READY_FOR_RUN_AUTHORIZATION, MC_RUN_AUTHORIZED, MC_BRANCH_SEALED(alpha/beta 各一), MC_RUN_STARTED, MC_PRE_RUN_ATTEMPT_FAILURE, MC_RUN_AUTHORIZATION_SUPERSEDED, MC_RUN_FAILED_POSTSTART, MC_RUN_COMPLETED, MC_PRIMARY_REVEALED, MC_BRANCH_REVEALED, MC_BRANCH_RETIRED_SEALED, MC_RUN_CLOSED, MC_ERRATUM}；必填字段（全事件）= {utc, event, commit(^[0-9a-f]{40}$), actor, trial_ref=MC-R###, 原因/备注}，按事件另补 {incident_id(INC-<12hex>)｜supersedes_event_sequence+superseded_commit+reason_code｜payload_sha256+byte_length+branch∈{alpha,beta}｜exposure_seq}；合法转移 = 主链线性顺序 + {AUTHORIZED→PRE_RUN_ATTEMPT_FAILURE→(SUPERSEDED→READY)…}（S0 实史环）+ {STARTED→FAILED_POSTSTART→CLOSED}；词表外事件、字段缺失、转移非法、40-hex 不匹配一律 fail-closed 拒收；LIVE 授权语义沿用 S0 规则（format-legal AUTHORIZED 减精确 supersede；0 live=未授权；>1 live=fail-closed）。授权句式（逐字模板，Aaron 亲发才有效）：「启动第一次真实MC，授权run_id: MC-R001，使用commit: <40位full hex>，绑定封存分支: alpha=<sha256> beta=<sha256>，smoke: SMOKE-001=PASS」；句内 commit 必须等于行 commit（S0 既有规则延用）。
理由=S0-T001 的状态机+LIVE 语义+supersede 字段集经两次 pre-run 失败实战检验；ND1-R2 是 Aaron 已批近亲词族——沿形态不假定同一（与 supplement 词表明确不同名域）；新增三处（SMOKE 引用、分支哈希绑定、RETIRED_SEALED 终局）分别落 E3/M14/G7 义务。
备选=全新词族（拒：无谓分叉，审计者两套心智模型）；直接复用 supplement 词表（拒：生命周期不同——MC 有分支密封/揭盲结构）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（治理语法；fail-closed 全程）
POST_FREEZE_DEFINITION=NO
若被裁反=改任何事件名/字段 → 校验器与 N07 同步改；砍分支哈希绑定 → 授权与预封脱钩，M14 免疫力减损。
```

```
ITEM_ID=G2
TIER=G
RULING=MC-R001 非新 formal trial：formal_trial_count 维持 1（S0=1）——MC-R001 是 S0-T001 预注册判定层（S0 §10 Checkpoint-0「由 MC 商业 EV 直接裁决」）的执行，其全部方法在 mc-freeze-v1（2026-07-28，先于 S0 真实运行与揭盲；FREEZE_LOG 本轮核实）冻结，不含任何新假设选择；但 (i) exposure 全额记账不减免（G3/G7：STARTED 消耗 slot、揭盲按 manifest 预枚举计数）；(ii) 判决落 α/β 时，分支检查按冻结 §10.4 明文「额外消耗一次研究自由度」——registry 事件+exposure ledger 追加行显式记账（RESEARCH_DF_CONSUMED=1），进入 §9 预注册的多重检验 N_eff 推导；(iii) 本裁定基于 MC 自身事实独立作出，未从 N-D1 第 2 项推导（包正文禁令遵守）。
理由=trial 记账对象是「预注册假设/研究的数量」（ledger 头部定义）而非执行次数；同一预注册研究的判定执行再计一次会把 DSR 账目从假设数污染成运行数；三轴正交——不动 trial 计数绝不意味着少记任何 exposure；α/β 的 +1 不是发明，是冻结文本自己写的账。
备选=计为新 trial（拒为默认：机制如上；Aaron 若择此属加严记账合法偏好，DSR 后果=未来 H1 门槛更高，但须同时声明「执行=trial」新原则的适用边界，否则冒烟/重试连环计数）。
CONSULTED_S0=NONE（冻结时点判断基于 FREEZE_LOG 与 §10.2，非任何结果值）
MAKES_GO_HARDER=NO（记账保真；α/β 的 +1 处按冻结从严落账）
POST_FREEZE_DEFINITION=NO
若被裁反=计新 trial → N_trials+1 的 DSR 折扣提前发生；须同时裁封「执行=trial」边界防外溢。
```

```
ITEM_ID=G3
TIER=G
RULING=两条序列永不混用：(i) run id 序列 = MC-R###（MC 专用命名空间、全局单调、next=MC-R001），MC_RUN_AUTHORIZED 时绑定授权句、MC_RUN_STARTED 时进入已消耗态（start 后永不复用，含失败）；(ii) exposure slot 序列 = 授权包预登记的 researcher-exposure slot（S0-T001 用 seq 1，MC-R001 预登记 next=seq 2），MC_RUN_STARTED 即 Stage-C 入口即正式消耗（S0 实史规则逐字延用：STARTED 行同时载 exposure_seq）；取值规则一律「现存最大值+1、registry 追加时机械读出」，禁止手填跳号；SMOKE-### 命名空间与两者物理隔离（E3 联动）。
理由=S0-T001 的「授权包预登记 slot + STARTED 消耗」模式已实战运转且被 attestation 链覆盖，MC 只换名域；run-id 与 exposure-seq 分离因语义正交（执行身份 vs 看结果配额），S0 历史里两者从未混同。
备选=单一混合序列（拒：pre-start 失败会产生「消耗了 exposure 名额的零暴露事件」或反之的语义错位）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO
POST_FREEZE_DEFINITION=NO
若被裁反=混序 → G4 的失败记账两难复活。
```

```
ITEM_ID=G4
TIER=G
RULING=pre-start（MC_RUN_STARTED 落笔之前一切失败，含 Stage A/B 门）：追加 MC_PRE_RUN_ATTEMPT_FAILURE（S0 语义：exposure NOT consumed、run id 不换、attempt 工件归档 attempts/MC-R001-A<UTC>/、incident 文档强制）；重试分叉：commit 未变且失败族=环境类 → 同授权下新 attempt；任何代码/配置变更 → MC_RUN_AUTHORIZATION_SUPERSEDED（四字段：supersedes_event_sequence/superseded_commit/reason_code/incident_id，S0 语法）→ 新 READY → Aaron 对新 40-hex 重发授权句（ND1-R2 PRESTART_COMMIT_CHANGE_REAUTH=YES 同款）。post-start（STARTED 之后）：追加 MC_RUN_FAILED_POSTSTART（incident 强制）；exposure slot 已消耗不回滚（S0 reveal 行「流程中断计数不回滚」同款纪律）；N_trials 不动（G2 框架本就不计执行）；若失败前任何 outcome 字节已出封存管线入人眼 → exposure ledger 按实计数追加（quantity 按已见关系格、outcome_seen=YES），严重性归 Aaron；重跑强制换 MC-R002（G5）。
理由=pre/post 分界线=STARTED 事件，它同时是 Stage-C 与 exposure 消耗落笔点（S0 冻结语义）；分界前无真实数据接触，id 与配额都不烧；之后配额已烧、执行身份已用，唯一诚实的路是新 id；环境类/代码变更分叉逐字继承 S0 两次 pre-run 失败实战处置与 ND1-R2 已批语法。
备选=pre-start 也烧 id（拒：S0 实史反例——两次 pre-run 失败均未换 S0-T001）；post-start 同 id 重试（拒：见 G5）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（fail-closed 记账）
POST_FREEZE_DEFINITION=NO
若被裁反=post-start 不换 id → 一 id 两次物理执行，封存字节↔id 单射破裂。
```

```
ITEM_ID=G5
TIER=G
RULING=YES，强制：任何 MC_RUN_STARTED 之后的失败，重跑一律新 id（MC-R002 起）；旧 id 以 FAILED_POSTSTART→CLOSED 终局、永不复用；新 id 须新授权句（commit 是否变更由失败性质定，代码变更必新 commit+复审）。
理由=id 是封存产物、exposure 消耗与授权句的三重锚点；post-start 失败后账户内状态不可知，同 id 续跑让「哪次物理执行产生了哪些封存字节」失去单射——RUN_AUTHORIZATION_SUPERSEDED 教训与 ND1-R2 POSTSTART_FAILURE_NEW_ID=YES 的机制推广。
备选=同 id 重试+attempt 后缀（拒：exposure_seq 与授权句均已绑定该 id 的「一次决定性执行」语义）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO
POST_FREEZE_DEFINITION=NO
若被裁反=同 id 重试 → 须为「一 id 多执行」重写 LIVE 语义与封存绑定，成本远超新 id。
```

```
ITEM_ID=G6
TIER=G
RULING=三条规则逐字：(R1)【id 不复用】任何 MC-R### 一经 MC_RUN_STARTED 即终身唯一，失败、中止、完成后均不得再授权、再启动或改写；attempt 目录名 MC-R###-A<UTC ISO8601> 同样终身唯一。(R2)【retry】重试永远是新事件链：pre-start 环境类=同 id 新 attempt（须先关 incident）；pre-start 代码/配置变更=SUPERSEDE→新 READY→新授权句；post-start=新 id（G5）；任何 retry 不得早于其 incident 文档落盘与 registry 事件追加。(R3)【incident】任何异常（门失败、非零退出、custody 不匹配、超 E2 绊线、崩溃）必须先落 INCIDENT_INC-<12hex> 文档并追加对应 registry 事件，才允许开启任何 retry/supersede 流程；静默重试=违规，发现即 fail-closed 冻结该 run 链待 Aaron。强制点 = registry 追加校验器（词表/字段/转移三重拒收）+ N15 型同 HEAD 链审。
理由=三条分别封死三类历史真实风险：id 重用的单射破裂（G5）、无痕重试（S0 两次失败全部有 incident+attempt 归档，先例已立标准）、跳过 incident 直接改码重跑（RUNTIME_SELFBLOCK 轮次反面教材）。
备选=宽松版（incident 仅 post-start 强制）（拒：pre-start 失败正是 S0 实史发生过两次的那类，最需要 incident 纪律）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO
POST_FREEZE_DEFINITION=NO
若被裁反=任一条弱化 → 对应风险面回开，审计链出现「无事件的物理执行」可能性。
```

```
ITEM_ID=G7
TIER=G
RULING=密封形态：MC_BRANCH_SEALED ×2（alpha/beta，字段含 payload_sha256、byte_length、branch），于 MC_RUN_COMPLETED 后、任何揭盲前追加；manifest（N17 步 1）逐条列两分支 {branch, sha256, bytes}——哈希与长度不泄露内容（两分支同 schema 恒被计算，长度差不载判定信息），值零暴露；exposure：分支揭盲沿用 S0 reveal 模式——先纯键/形状预枚举将看的关系格计数、追加 REVEAL_STARTED 行，后开封比对 sha256、追加 REVEAL_COMPLETED 配对行（不重复计数）；未触发分支：MC_BRANCH_RETIRED_SEALED 终局事件（永久密封声明，exposure quantity=0 交叉引用行），永不揭示；GO/STOP 直接终局时两分支均 RETIRED_SEALED。M14=NO 时本项形态失效（依赖照记）。
理由=S0-T001 的 manifest-先行+预枚举计数+配对行防双计是已实战的暴露纪律，分支密封只是把「整报告」换成「分支 payload」；RETIRED_SEALED 是账面上「永不可见」的显式承诺——没有它，未触发分支在链上是悬空态。
备选=分支不进 manifest（拒：N17 步 1 冻结要求 sealed manifest 先行，分支是 sealed 物）；等长填充防长度侧信道（拒：长度不载判定信息，填充是无收益复杂度）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO
POST_FREEZE_DEFINITION=NO
若被裁反=砍 RETIRED_SEALED → 未触发分支永久悬空；砍预枚举 → 分支揭盲的 exposure 计数失去 S0 级保守上界性质。
```

```
ITEM_ID=G8
TIER=G
RULING=逐字复用 S0-T001 实史模式并加两条 MC 特有前置：READY_APPEND=UNCOMMITTED；HEAD_UNCHANGED=YES（HEAD 停在 N14 等价复审通过的 exact HEAD，授权句绑定同一 40-hex）；DIRTY_ALLOWLIST=ops/TRIAL_REGISTRY.md_ONLY；N15_REVIEW=同 HEAD 链审；POST_RUN_CLOSEOUT_COMMIT=PERSISTS_EVENTS；禁止 reset/checkout/覆盖/丢失未提交事件，崩溃保留转人工。MC 特有前置：(i) α/β 密封 payload 及其 sha256、SMOKE-001 PASS 记录必须已在被复审的 HEAD 内（分支文件不入 dirty allowlist——它们是被授权对象的一部分，必须先于 READY 入库）；(ii) 授权句含分支哈希绑定（G1 句式）。「commit READY→新 HEAD→重审」维持已否决（多耗一轮且为 RUN_AUTHORIZATION_SUPERSEDED 教训形态）。
理由=该模式力学=授权、复审、运行钉在同一 40-hex，READY 行是唯一允许的脏字节；任何让 HEAD 移动的方案重开「授权的是哪棵树」问题；分支 payload 必须在审过的树里，否则授权句绑定的哈希指向树外字节——保管链开口。
备选=READY 入 commit（拒：已否决理由充分）；分支 payload 进 dirty allowlist（拒：保管链开口）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO
POST_FREEZE_DEFINITION=NO
若被裁反=放宽 allowlist → 授权对象与复审对象出现差集；改 commit-READY → 每次授权多一轮全量复审，历史教训形态复活。
```

---

## 附录一：相互依赖（Aaron 逐项改时最容易踩的坑）

1. **M14=NO ⇒ M15 自动失效、G7 形态失效、§7 揭盲序重导**（包 §8 原条）；另加：M12 的 α 检查将不可避免发生在知晓主结果之后，N17 须按 2.3 同款披露。
2. **M1/M3/M4 是一个量词架构整体**（逐 path→世界份额→认知层分位、Wilson 弃用）：单改任一（恢复 Wilson／改混合份额／改分位层）必须三项同改，否则层架构自相矛盾。
3. **M3(a) 分母与 M3(c)=0.25 必须同改**：分母改回 offered 则 0.25 失效（skip 率数倍缩小）。
4. **M5 改场景集 ⇒ M1/M3 的「两场景各自成立」量词同步改**。
5. **M6→M7→M8→M9 是链**：对象（区域图）→角色（报告+自身有效性）→等价判据（边界带）→漂移检查（(c) 移植）。改 M6 对象则后三项失去载体；M7 改「扣押整判」则 M8 的 max_doublings 触限处置升级为判决关键路径，E3/M10 算力按最坏重算。
6. **M10 依赖 IR-29a（已生效）**：M 轴要加倍须先撤该 IR；M10 的 6 全量跑＋3 网格加倍、M12/M14 的 α×2、E3 冒烟两跑共同构成 N16 算力总账——三处必须同席裁。
7. **M12 依赖 IR-28c 的 never_primary 钉定**（改用成本敏感性作 α 对象须先解钉）；**M13 依赖 §2.5 冻结角色表**（扩集合须冻结级论证）。
8. **M11 生效 ⇒ N07 必须替换 fixed-world 守卫测试**（从「无规则」改为「仅此规则」），漏做即出现「代码守无规则、裁定有规则」自锁。
9. **D1 生效 ⇒ N07 翻转 OVER_BUDGET_PREDICATE_RULED、增设 intraday 第二累加器**；改 n×anchor 基准则须解释与 ratio 分布的关系。
10. **D2 走 addendum 通道 ⇒ 与 O4 勘误登记件分工**（addendum=语义修正，errata=表述勘误），两件不得互相顶替。
11. **E1 条件 (i) 落点在 E3 判据 (4)**：砍 E3 或砍判据 (4) ⇒ E1 追认失去生产尺度支柱，须回改 E1 范围声明。
12. **E2 绊线以 E3 实测为触发器**：砍 E3 ⇒ 绊线失去数据源。
13. **O1/M11/M14 共同抬高封存字节与 custody 分钟**：以 E3 实测回填 E2 预算。
14. **G1 句式含分支哈希与 SMOKE 引用**：M14 或 E3 被砍 ⇒ 句式字段同步删；G8 前置 (i) 同理。
15. **G2 的 α/β RESEARCH_DF_CONSUMED=1 记账**依赖 M14/M15 分支结构与 G7 记账载体。
16. **O3 点名清单与全部 POST_FREEZE_DEFINITION=YES 标记一一对应**：Aaron 改任何 M/D 项 ⇒ O3 清单同步增删。
17. **2.2 未处理 ⇒ M1–M5 的时序披露无法完成**（包 §8 原条；O3 措辞已为此留了引用位）。

## 附录二：CANNOT_DECIDE_WITHOUT_OUTCOME 清单

**空集**——32 项中没有任何一项需要读取禁止内容才能裁定。两条如实注记：
1. **包 §2.2 的前置判断不在 32 项内且只能归 Aaron**：`ops/S0_T001_RESULT_DECISION_ADDENDUM.md` 那句「可行性天花板…PASS」是否已构成对 feasibility 门的实质约束——本席按防火墙未读该文件正文，无法也不应判断；若 Aaron 判定「是」，则 M1–M5 的裁定在时序上晚于一次 feasibility 结论，O3 措辞中已预留该披露位。
2. **M2 的"评估"（非"设定"）不可避免消费已揭盲值**：这是 2.3 的结构性事实，不是本席的缺口——阈值 5.0 的设定过程零 S0 值查阅（CONSULTED_S0=NONE），但门的应用天然读已揭盲的 §10.5 输出；已由 O3 披露承载。

## 附录三：独立性声明

- **context**：本件由全新顶层会话产出；非 builder 会话延续，未参与任何 N06 轮（MUST_NOT_BE 遵守）；全程 read-only（仓库零写入）；读取面与意外暴露逐项申报于卷首防火墙段；禁读件零打开。**workflow 使用 = 0/预算 3**：污染防火墙下 fan-out 子代理的读取面不可逐文件担保（一次误读禁读件即不可逆污染主上下文），全部证据需求经定向只读检索闭合，按 QROS「更便宜机制可解则不升级」停止。
- **authorship**：本会话非决策包作者、非任何被裁代码/冻结文本作者；本件是本会话唯一产出物。
- **model-diversity**：Fable（本件）≠ Opus（builder/包作者）≠ Sol（Stage I 待做）。按 session-conventions §1：模型多样性只构成评审多样性，不构成统计复制或经验独立。
- **empirical**：本轮零运行、零真实数据接触、零新证据生成；全部裁定基于冻结文本+生产代码+测试的静态读取；不含任何经验独立性宣称。
- **效力**：本件为**提案**，不是 Review Packet v1，不是 `PACKET_OUTCOME`，不释放任何 gate transition（A2／Stage I／material-measurement 均不涉），不含 APPROVED／EFFECTIVE／RATIFIED 语义。生效唯一路径 = Aaron 整体批准或逐项修改后批准；批准后由 builder 按 N-D2 要求落 MC1.x Addendum／Evidence Resolution 与实现（N07/N12/N13），每一次真实执行仍需 Aaron 单独的、绑定完整 40 位 commit 的精确授权语句。
