# N-D2 ＋ N-D3 合并决策包

```
PACKET_ID=DECISION_PACKET_ND2_ND3
PACKET_VERSION=1
PREPARED_BY=Opus 5 main agent（builder seat）
DECIDER=Fable 5（Aaron 明示委托，2026-08-24）
RATIFIER=Aaron（一次性批准或逐项改）
ITEM_COUNT=32（M15 / D2 / O4 / E3 / G8）
NOTHING_HERE_IS_APPROVED=YES
```

本包**不含任何已批准值**。全部条目为待裁。包作者（builder）不对任何一项表达
偏好，只陈述：冻结文本说了什么、代码现在是什么状态、待裁的具体问题是什么、
有哪些选项、各自后果。

---

## 0. 使用方式

1. Fable 按 `ops/ND2_ND3_FABLE_DECISION_PROMPT.md` 对本包逐项裁定，输出提案。
2. Aaron 整体批准或逐项修改。
3. 只有 Aaron 批准之后，工程侧才能开始 N07（feasibility 实现）与 N12/N13。

**先例（形式上可直接沿用）**：IR-28 批次的现势状态是
`DECIDED_BY_EXPLICIT_FABLE_DELEGATION`（`IMPLEMENTATION_RESOLUTIONS.md:171`）。
但同一段记录了 Codex 的一次纠正：**泛化委托**（"你替我研究以及做决定"）曾被
降级为 `PENDING_AARON_RATIFICATION`，理由是它"未逐项撤销 Charter 中 Aaron
专属的边界"。本包因此按**具名批次委托**处理，并保留 Aaron 的最终批准动作。

---

## 1. 机械现状（可逐项复核，非转述）

feasibility 在代码里是**有原始量、无判据**的状态：

```
consumer.py:1479   FEASIBILITY_GATE_STATUS = "DECISION_REQUIRED"
consumer.py:1515   FeasibilityEvidence 里不存在任何 `feasible` 布尔
verdict.py:31      VerdictInput.feasible: bool —— 是判定表的【输入】，产生它的门不存在
contracts.py:1014  OVER_BUDGET_PREDICATE_RULED = False
```

`FEASIBILITY_METRICS_STATUS`（consumer.py:1487）十二项中十项 `COMPUTED`，两项
`DECISION_REQUIRED`：`e2_over_budget_days`（谓词未裁）与
`qualifying_distribution_vs_payout_requirements`（规则未裁）。

已计算的原始量（`atoms.py:1314 reduce_feasibility_counts`，只有计数与份额，
无布尔、无阈值）：

```
n_paths · payout_event_paths · total_payout_events · total_skips_n0
total_offered · total_executed_trade_days · total_winning_days
total_days_profit_ge_150 · total_qualifying_days · total_ambiguous_days
exhausted_paths · total_b2f_used · total_contract_cap_hits
total_e2_over_budget_days · payout_event_path_share · exhausted_share
ambiguous_share
```

冻结常量：`QUALIFYING_DAY_MIN_PROFIT_USD = 150.0`（atoms.py:59，取自
platform_params，**代码注释明写它不是 feasibility 门、不得当频率代理**）。

`test_mc_cold_replay.py:1102 test_no_fixed_world_selection_rule_was_invented`
——树里有一条测试专门确保没人偷偷发明 fixed-world 选择规则。

---

## 2. 三个必须先说的发现

### 2.1 `0.5 / 0.75 / 0.50` 三个候选阈值在仓库里没有出处

主计划 §5 把它们写成待裁的既有候选。**全仓搜索没有找到任何来源**：不在
`MC_METHOD_SPEC.md`，不在 `STUDY_0_PREREGISTRATION.md`，不在
`IMPLEMENTATION_RESOLUTIONS.md`，不在任何 gate 文档。仓库里出现的 `0.75` 只有
附录 A 网格的 `q ∈ {0.35…0.75}`，`0.50` 只有成本项 `−$0.50/合约`。

**后果**：M1–M4 不是"追认已有数值"，是**从零设定**。Fable 若认为需要一个先前
提出过的锚，必须由 Aaron 提供出处文档；否则按从零设定处理并如实标注。

### 2.2 存在一份揭盲后的文档，已经就 feasibility 作出断言

`ops/S0_T001_RESULT_DECISION_ADDENDUM.md:26` 有一行：
「可行性天花板作为独立断言记 **PASS**」。

**本包作者没有读这份文件的正文**——我是 N13 的建造者，读揭盲值会把我自己
污染成"既算分数又定门槛"。Fable 同样受防火墙约束，也不应读。

因此这一项**必须由 Aaron 本人处理**（他已解盲，读它不产生新污染）：
判断那句断言是否已经构成对 feasibility 门的实质约束。若是，则 M1–M5 的裁定
在时序上晚于一次 feasibility 结论，N17 记录必须如实披露这一点。

### 2.3 frequency 门无法在对 S0 无知的情况下定义

N-D2 明文要求 frequency 门"锚定 S0 §10.5 冻结频率输出"（延续事件基础率 p、
年可交易日数、Oracle 月均频率）。S0 已揭盲。**这不是可以修好的问题，只能
如实披露**：这一门的阈值必然是在已知这些量的情况下定的。

---

## 3. Tier M — 方法，直接决定 GO/STOP

> M1–M5 同样属于**冻结后补定义**：冻结文本（S0 §10.4 row 2、MC §6）点名了
> 三道门，但从未定义任何一道怎么算过。裁定时须带 `POST_FREEZE_DEFINITION=YES`。

### M1 — payout 门

**冻结文本**：S0 §10.4 row 2 要求"payout 路径可行性经 MC 确认"；MC §6 要求
`feasibility.json` 报告"达标盈利日分布 vs payout 要求"。两处都没定义"确认"。

**平台事实（冻结）**：Lucid `qualifying_days_required=5`、
`qualifying_day_min_profit_usd=150`；Topstep XFA standard 同为"5 个盈利日，
每日净利 ≥ $150"。

**代码**：`qualifying_distribution_vs_payout_requirements=DECISION_REQUIRED`。
可用原始量：`total_qualifying_days`（平台自己的计数器）、
`total_days_profit_ge_150`、`total_payout_events`、`payout_event_paths`、
`payout_event_path_share`。

**待裁**
- (a) 判据落在哪个量上：达标日计数？实际 payout 事件数？出现过 payout 的
  路径份额？
- (b) 量词：逐 path 判定后取份额，还是先聚合再判定？门槛按认知层分位
  （P5/中位）还是按路径份额？
- (c) 阈值。
- (d) **截尾周期**：24 个月视界末尾未走完的 payout cycle 记入、剔除、还是
  按比例折算。

**后果**：(a) 选"平台自己的 qualifying 计数"最保守也最贴平台语义；选
`days_profit_ge_150` 会与 M2 抢同一个量（见 M2 的明文禁令）。(d) 若记入，
末尾半个周期会系统性拉低通过率；若剔除，等于默认稳态。

### M2 — frequency 门

**冻结文本**：S0 §10.5「频率输出（强制）」：延续事件基础率 p、每年可交易
日数、Oracle 月均频率、附录 A 网格预期交易数。§10.5 另有一句：
「辅助直觉检查（不决定 GO）：q_min ≤ min(65%, 2.2p)」——**明示不决定 GO**。

**明文禁令**：主计划 §5 与 `atoms.py:58` 都写死 `days_profit_ge_150`
**不得**冒充 frequency 代理。

**待裁**
- (a) 门建在哪个量上（月均交易频率？年可交易日数？两者合取？）
- (b) 量词与阈值。
- (c) `q_min ≤ min(65%, 2.2p)` 是否从"辅助直觉检查"升格为门的一部分——
  **升格即为改变冻结文本的效力，不只是补定义**，须单独标注。

**依赖**：与 2.3 的披露绑定。

### M3 — integer-position 门

**冻结文本**：MC §3 定义
`n = min(floor(risk_budget ÷ sizing_anchor_usd), 当日 scaling 档位 micro 上限,
absolute_max_micros)`；`n=0 → 跳过并计数`。冻结文本只说计数，没说多少算不可行。

**代码**：`total_skips_n0`、`total_offered`、`total_executed_trade_days`、
`total_contract_cap_hits`（可能为 typed-absent）。

**待裁**
- (a) `offered` 的定义：结构合格日？策略给出信号日？账户存活日？——
  **这是分母，直接决定 skip 率的量级。**
- (b) `executed` 的定义与 `offered` 的关系。
- (c) skip 率的门槛与量词。
- (d) `contract_cap_hits` 是否进这道门（触顶是"可行但受限"还是"不可行"）。

**后果**：(a) 的三种读法能让同一份数据的 skip 率相差数倍。这一项是三门里
最容易被分母定义悄悄决定结果的。

### M4 — 三门如何合成，以及是否用 Wilson 区间

**待裁**
- (a) 三门是 AND 还是别的合成（任一不过即不可行？两门过即可？）
- (b) 是否对份额类判据使用 Wilson 置信区间而非点估计；若用，置信水平与
  用区间的哪一端（下界更保守）。
- (c) 三个阈值的具体数值（见 2.1：无既有出处）。

**后果**：用 Wilson 下界＋AND 是最严的组合；用点估计＋任一门过是最松的。
两端之间的差距足以单独决定 GO/STOP。

### M5 — feasibility 在哪个场景下评估

**冻结文本**：场景集冻结为 `Base / Conservative / Stress / Severe`
（atoms.py:52）。S0 §10.4 的 EV 条件明确绑定场景（Conservative P5、
Stress 中位数），**但可行性那一句没有绑定任何场景**。

**待裁**：可行性在哪个场景下判？Conservative？与 EV 条件同场景？全场景 AND？
还是 Base？

**后果**：这是判定表里唯一一处场景归属留白。不裁则 N13 无法实现——
`VerdictInput.feasible` 是 per-combo 的单个布尔，必须知道它来自哪个场景。

### M6 — K 收敛：K-dependent 分类对象是什么

**冻结文本**：MC §5 收敛规则 (a)「B、M、K 分别加倍，判定类别不得变化」。
"判定类别"对 B/M 指 Checkpoint-0 四类（STOP/GO/β/α）。K 只作用于附录 A 网格
（MC §5 内层随机源 (2)：「TP/FP 分层抽样（K 次重复，**仅网格分析**）」）。

**问题**：网格分析**不产生** Checkpoint-0 类别。所以 K 加倍时"判定类别"指谁？

**明文禁令**：主计划 §5 —— **禁止**调用不消费 K 的 Checkpoint category 两次
来伪造收敛（那会必然相等，是空验证）。

**待裁**：K 的收敛对象是什么。选项：网格的 positive region（哪些 cell 为正）／
deployable region／关键分位数／或裁定 K 不适用 (a) 而改用 (c)/(d)。

### M7 — positive region 与 deployable region 的角色

**待裁**：这两个 region 是**判据**（区域不稳即 kill）还是**报告项**
（只披露不影响判定）。

**后果**：S0 §附录 A 有「网格地位限定：仅为可行性边界，不构成 H1 表现宣称；
禁止因某格漂亮而把该格的参数当成结论」。把 region 升为判据与这句话的关系
需要 Fable 明确处理。

### M8 — exact region equality 是 kill 还是报告

**待裁**：K 与 2K 的 region **完全相等**才算收敛，还是允许差异并只报告差异。

**后果**：exact equality 在离散网格上极严，容易因单个边界 cell 翻转而判不收敛
→ 按 (e) 必须加倍重跑 → 算力成本。允许差异则需要一个"差多少算收敛"的第二
阈值，那又是一个待裁量。

### M9 — cell 的关键分位键集，与 rule-(c) 是否移植

**冻结文本**：收敛规则 (c)「关键分位数变化 ≤ max($25, 相对 5%)」，作用对象
按 MC §4.4 是**月均 prop_operating USD**。

**待裁**
- (a) 若 (c) 移植到 cell 层，cell 的"关键分位数"是哪几个键？
- (b) `max($25, 5%)` 的美元项在 cell 层还有意义吗（cell 的量纲可能不是 USD）？

### M10 — K/2K × seeds 与 B doubling × seeds 的量词，及 cross-seed region 规则

**冻结文本**：(b)「三个独立 master seeds（7/13/31 派生流）判定类别一致」。

**待裁**
- (a) K 加倍要不要在**每个** seed 上都做（3 seeds × K/2K = 6 次网格）还是
  只在一个 seed 上做。
- (b) B 加倍同问。
- (c) cross-seed 的 region 规则：三个 seed 的 region 必须相同？取交集？取并集？

**后果**：这一项直接决定 N16 那次真实运行的算力量级，**请与 E5 一起裁**。

### M11 — fixed-world 选择

**冻结文本**：MC §5「conditional_aleatoric：固定世界内 M 条账户路径的结果
分布」。哪个世界是"那个固定世界"，从未定义。

**代码**：`consumer.py:1925` ——「the caller NAMES the world; no fixed-world
SELECTION rule exists」；并有测试 `test_no_fixed_world_selection_rule_was_
invented` 守着。

**待裁（主计划已列三个选项）**
- (a) 单个预注册 world；
- (b) P5–P50–P95 邻近集合；
- (c) 不选，报告全部 world 的条件切片。

**后果**：(a) 需要"预注册"一个世界，但 S0 已揭盲，事后指定单个世界是可被
质疑的；(b) 需要定义"邻近"；(c) 最保守也最贵（报告规模膨胀），且与 M10 的
seeds 量词相乘。

### M12 — α 的唯一检查对象、量词与门槛

**冻结文本**：S0 §10.4 —— α 是**兜底类别**（其余全部情况）；边界区处理为
「一次预注册检查（α：敏感性检查）后**强制一次性判决**」，判据「与主门槛
完全相同」，「门槛只能持平，不得降低」。

**待裁**：α 的"敏感性检查"具体检查什么——**唯一**对象、量词、门槛。

**约束**：不得降低主门槛（冻结文本明文）。所以这一项裁的是"检查什么"，
不是"用什么门槛"。

### M13 — β 的唯一替代结构集合、量词与门槛

**冻结文本**：β 的替代风险结构「作为新受限候选，同样适用主门槛」。

**待裁**：那个替代结构集合的**穷尽枚举**是什么。

**后果**：集合越大，β 分支越可能翻成 GO，但每多一个结构就多消耗一次研究
自由度。冻结文本已声明这是"额外消耗一次研究自由度"的分支。

### M14 — α/β 是否随主 MC 预计算并分别盲封

**待裁**：预计算 + 分别盲封，还是等主判定出来再算。

**后果**：预计算+盲封能避免"看到 primary 结果之后再设计检查"的指控——这是
本项唯一实质性的方法论理由。代价是算力（两条分支都算，但只揭一条）。

### M15 — primary 先揭盲、只揭示实际触发分支

**冻结文本**：主计划 §7 步 5–6 「α/β 仅揭示已预封的对应分支；未触发分支
保持不可见」，并注明「预设 N-D3 第 9 项裁为 YES；若裁 NO，揭盲序按裁定重导」。

**待裁**：确认或推翻这个预设。

**依赖**：**M14 裁 NO 则本项自动失效**（没有预封就没有"只揭一条"可言），
§7 揭盲序必须重导。这是本包最强的一条依赖。

---

## 4. Tier D — 冻结文本里的洞

> 两项都必须带 `POST_FREEZE_DEFINITION=YES`。

### D1 — E2 `over_budget` 谓词

**冻结文本**：MC §3 强制报告 `P(realised_loss > 预算)` 与
`P(intraday_adverse_loss > 预算)`。同节定义 E2 的 `sizing_anchor` =
反事实 E1 止损距离，并明写「**不下实际止损单**——锚点仅用于仓位计算，
**不是亏损上限**」。

**从未定义**：per-day 布尔指上述哪一个；损失基准是每合约还是整个仓位；
预算基准是 policy budget 还是 `n × anchor`。

**代码现状**：`OVER_BUDGET_PREDICATE_RULED = False`；期间
`AccountEvent` **拒绝携带**布尔（contracts.py:1217），E2 交易日发
`PENDING_RULING`，`total_e2_over_budget_days` 为 typed-absent。代码注释
（contracts.py:996）：「NEVER encode an unruled quantity as False/0 —— 那在
下游读作已测量的『没有超预算』，等于凭空制造证据」。

**待裁**：三个基准各选一个，共同定义 per-day 布尔。

**后果**：`n × anchor` 与 policy budget 在 n 因 scaling 上限被截断时不相等；
每合约与整仓在 n>1 时不相等。三个选择的组合会产生量级不同的超预算率，而
这个率是 E2 组合的强制披露项。

### D2 — 冻结层-1 会计与 Lucid 生命周期不符

**冻结文本**：MC §4.4 `strategy_account_EV` = 「平台内交易净损益」。

**实测事实**：Lucid 生命周期通过评估阶段时会丢弃评估期利润——两个 +1500 的
日报为 `0.0`，而权威和为 `3000.0`。

**影响范围已机械钉死**：Checkpoint-0 判定用 `prop_operating_EV`
（S0 §10.5、MC §4.4 末行），其公式 `payout_cash + terminal_cash − fees` 不以
层-1 为输入，故该缺陷**够不到判定统计量**——由
`tests/test_mc_node_integration.py::test_checkpoint0_statistic_is_insulated_from_layer1_accounting`
钉定。当前权威累加器与旧口径**并存**，使差额可测。

**待裁**：(a) 冻结层-1 的定义按实际行为修正，还是保留定义并披露偏差；
(b) 并存的两套口径是否保留，保留到什么时候。

**注意**：这一项**不改判定统计量**。若某个裁法会改，那就不是补定义而是改
冻结数值，须单独提请 Aaron。

---

## 5. Tier O — N-D2 其他项

### O1 — θ=0.3 完整报告规模

**待裁**：θ0.3 通道的完整报告出到什么规模（全部组合？仅 Primary？）。
**后果**：直接影响报告体量与封存字节数。

### O2 — IR-28c：真实重放 vs 近似

**现状**：IR-28c 已定裁 sensitivity `+1 tick` = 乘子后
`{Base 2, Conservative 3, Stress 3, Severe 4}`，且**本轮已接入正式报告与封存
校验**——实现方式是「由 Primary records 纯算术导出的 E1 每场景 delta
（adverse 只作用 E1 止损侧，每止损日恰 −$0.50/合约，线性精确）」，
即**近似（算术导出）而非重跑**；E2 零 by construction；`role=never_primary`。

**待裁**：追认这条算术导出路径，还是要求一次真实重放来产生同一组数字。

**后果**：真实重放会产生额外算力与一轮封存；算术导出的正确性依赖"adverse
只作用 E1 止损侧且线性"这一论证是否被接受。

### O3 — late-phase bias 披露

**待裁**：披露措辞与落点（报告内？attestation？两者）。

### O4 — 历史 feasibility 文档勘误批准

**待裁**：历史文档中与现势不符的 feasibility 表述，按勘误处理并批准。
**约束**：勘误只改表述，不得改任何已封存数值。

---

## 6. Tier E — 工程事实追认

### E1 — mean / SD / SE 的数值实现追认

**现状（N01 引入，已登记未裁）**
```
MEAN_SD_SE_NUMERICAL_IMPLEMENTATION_STATUS=PENDING_AARON_RATIFICATION
ESTIMATOR_FAMILY_UNCHANGED=YES
ULP_LEVEL_BEHAVIOR_CHANGED_FROM_R2_3=YES
```
统计核从 numpy 迁至规范化纯 float（为使独立 cold reducer 可逐位复核）。
实测非逐位率：`mean_of` vs `np.mean` 47.8%、`sample_sd` 33.2%、
`stderr_of` 30.6%，**全部 ULP 级**（max_rel ≤ 1.7e-12），估计量族未变。
percentile 已在边界修复轮恢复 NumPy-linear 逐位行为，不在此项内。

**结构性事实（诚实披露）**：mean/SD 的 numpy 位兼容**不可达**——numpy 的
pairwise 求和序是非契约的内部实现，写不成两份独立实现都能复现的书面规范。
故"完整恢复 R2.3 位连续性"任何方案都做不到。

**生产规模从未执行 ⇒ 无任何已封存数字被改变。**

**待裁**：追认现实现，或另定。

### E2 — custody 链的生产规模开销预算

**实测外推**（synthetic 三档外推到生产；8 个 `MC_HANDOFF_*` 合计 91.6 MB，
size 取自封存 attestation）
```
常驻内存      +91.6 MB / prepared
一次全量重解析  ≈ 8 s
一次 records 规范摘要 ≈ 24 s（流式灌 hash，峰值 6–12 KB）
一次 cold_replay_observation_set = 4 次全量解析 + ~7 次摘要 ≈ 2.5–3.5 分钟
40 个 observation set ⇒ 约 100–140 分钟纯 custody 开销
重放峰值内存 ≈ 0.9 GB（修复前 ≈ 0.28 GB）
```
**未做缓存**——缓存会破坏 "cold" 语义。

**待裁**：接受该预算；或要求按文件切分 records 摘要以支持增量验证。

**明确不可选**：跳过重解析。那会让冷重放不再是独立验证。

### E3 — 是否要求一次生产规模冒烟运行

**事实（诚实披露，非本轮造成）**：**生产规模从未被执行过。** 全部逻辑测试
在 B=2 / M=2。任何只在 B=1000 或 M=21 才显形的缺陷——浮点累加顺序、type-7
分位边界、内存/耗时——在本仓库任何地方都未被执行。R2.3 当年那个"生产规模"
夹具是用已删除的 `from_world_means` **伪造的摘要**，同样从未真跑。

**待裁**：N16 之前要不要先做一次生产规模冒烟运行；若要，用什么数据
（synthetic？真实但不封存？）、算力口径、以及它是否需要单独授权。

**后果**：不做，则 N16 那次真实运行同时是这套代码的**首次生产规模执行**——
一次会写进 registry、消耗研究自由度的运行，同时承担首跑风险。

**依赖**：与 M10（seeds × doubling 量词）共同决定算力总量。

---

## 7. Tier G — MC 治理词汇（N-D3）

> 本层裁定标准是**自洽 + fail-closed**，不涉及 outcome。可参照 N-D1 已批准的
> supplement registry 语法（`ND1_RECOMMENDED_PROFILE_R2`，2026-08-23 批准）
> 保持形态一致——但**不得**假定两者必须相同。

### G1 — MC 批 2 事件词表／字段／状态转移／授权句式
待裁：完整闭合枚举、每个事件的必填字段、合法状态转移、以及 Aaron 授权语句
的精确句式（须绑定完整 40 位 commit）。

### G2 — MC-R001 的 formal-trial 地位
待裁：是否 formal trial。**后果**：决定它是否移动 `N_trials`，进而影响 DSR
账目。（与 N-D1 第 2 项同类问题，但**不得**由那一项自动推出。）

### G3 — `MC_RUN_STARTED` 消耗的 run/exposure 序列
待裁：消耗哪一条序列、如何取 next value。

### G4 — pre-start 与 post-start failure 的记账
待裁：两类失败各自的事件、是否消耗序列、是否可重试。

### G5 — post-start failure 是否必须用 MC-R002
待裁：失败后重跑是否强制换新 id。

### G6 — retry／incident／id 不复用
待裁：三条规则的精确措辞与强制点。

### G7 — α/β 的 exposure／manifest／终局事件
待裁：预封的分支如何在 manifest 中体现而不泄露；未触发分支的记账形态。
**依赖**：M14 裁 NO 则本项形态改变。

### G8 — READY 未提交模式在 MC registry 中的精确复用
**现状（主计划 §6，S0-T001 实史模式）**
```
READY_APPEND=UNCOMMITTED
HEAD_UNCHANGED=YES
DIRTY_ALLOWLIST=ops/TRIAL_REGISTRY.md_ONLY
N15_REVIEW=REGISTRY_CHAIN_REVIEW_ON_SAME_REVIEWED_HEAD
POST_RUN_CLOSEOUT_COMMIT=PERSISTS_EVENTS
```
待裁：在 MC registry 中如何精确复用（"commit READY→新 HEAD→重审"已被否决，
理由是多耗一轮 Codex 且正是当年 `RUN_AUTHORIZATION_SUPERSEDED` 的教训形态）。

---

## 8. 依赖关系（Aaron 逐项改时最容易踩的坑）

```
M14 = NO        ⇒ M15 自动失效，主计划 §7 揭盲序必须重导；G7 形态改变
M2(c) 升格      ⇒ 改变冻结文本效力，不再是补定义
M3(a) offered   ⇒ 同一数据的 skip 率可差数倍，M3(c) 阈值必须与之同时裁
M6 = "不适用"   ⇒ M7/M8/M9/M10(a) 全部失去对象
M10 + E3        ⇒ 共同决定 N16 的算力总量，必须一起裁
D2 若改判定量   ⇒ 越出"补定义"范围，须单独提请 Aaron
2.2 未处理      ⇒ M1–M5 的时序披露无法完成
```

---

## 9. 禁止状态（本包生成过程中，全部为 NO）

```
REAL_DATA_READ=NO          REVEALED_OUTCOME_READ_BY_BUILDER=NO
SUPPLEMENT_EXECUTED=NO     MC_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO  REGISTRY_EVENTS_APPENDED=NO
EXPOSURE_EVENTS_APPENDED=NO  REAL_DIRECTORIES_CREATED=NO
ANY_VALUE_APPROVED=NO      N06_FINAL_PASS=NO
```

本包**未**读取 `ops/S0_T001_RESULT_DECISION_ADDENDUM.md` 正文（见 2.2）。
所引的那一行来自全仓 grep 的单行匹配，未展开上下文。
