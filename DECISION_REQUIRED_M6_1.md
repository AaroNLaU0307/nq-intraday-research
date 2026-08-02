# DECISION_REQUIRED_M6_1（六项方法裁决包；Fable 起草，Sol 立场并列，Aaron 裁决）

通用声明：全部机制已参数化实现或以 UNRESOLVED 阻断；任何一项未裁 →
`ResolvedS0Methods` 对应字段为 None → Stage B 拒绝、零 exposure。
本文件零 S0 结果引用。落地形式栏指 IR 或 S0.x addendum。

---

## DR-1（DR-M6-A-v2）spread 表 → 每笔成本 ＋ IR-7 adverse slip 定稿

- **frozen source**：S0 §6（"Base=时段中位＋1 tick/边；Conservative=P90
  ＋2；Stress=Base×2；Severe=P95＋3"；成交公式）；contracts.py:32
  （"full width for the applicable minute"）；spread_cost_table.csv
  （逐分钟 slot：spread_median/p90/p95_points, n_obs；QA 披露 RTH
  slot-median 的 median=0.50、p90-of-medians=0.50）。
- **精确歧义**：①"时段"未定（全 RTH／交易窗）；②跨 slot 聚合统计量
  未定；③fill-minute 逐分钟读法与场景常量读法均与文本兼容；
  ④IR-7 adverse ticks 是暂用值；⑤现实现 adverse 是**替代** regular
  slip 而非相加（contracts 注释"extra"与实现不符，须正字）。
- **候选 normative text ＋公式**：
  - **A（全 RTH 聚合）**：slots S=[570,959]。子式 A-i：
    (Q50(med_s), Q50(p90_s), Q50(p95_s))；子式 A-ii：
    (Q50(med_s), Q90(med_s), Q95(med_s))（QA 披露口径含 A-ii 的
    Conservative）。Q* = 等权 slot、numpy linear 插值、不再舍入。
  - **B（交易窗聚合）**：同 A 两子式，S=[600,944]（entry/exit/stop
    仅发生于此窗）。
  - **C（fill-minute lookup）**：entry 用 slot(600) 行、timed exit 用
    slot(944) 行、stop 用触发 bar 分钟行、理论 Oracle 退出用最有利
    价首次出现 bar 分钟行；场景取该行对应列（Base=median 列、
    Cons=p90、Sev=p95、Stress=median×2 乘子）。n_obs 权重仅在池化
    变体使用（预否：需回 BBO，违 §1 隔离）。
  - **IR-7 定稿向量**（adverse 替代语义，正字后）：
    Option i（现状转正，Sol 倾向 Primary）：{Base 1, Cons 2,
    Stress 1×2乘子⇒有效2, Severe 3}；
    Option ii（+1 tick）：加于乘子**前** {2,3,2×2⇒4,4} 或乘子**后**
    {2,3,3,4}——若采 ii 须指明。
- **10:00 可观察性**：表为 2025Q1 外生固定 → A/B/C 全可观察；C 的
  stop 分钟为成交时刻自身信息，无前视。
- **lookahead/NA/样本/verdict 影响**：纯成本层；不改样本与 NA；
  方向单调（成本↑ ⇒ 全引擎 P&L↓）；C 使 Stress/Severe 场景内
  日间成本异质化。
- **数据可得性**：全部来自已锁 spread_cost_table.csv；无新采购。
- **conservation/fail-closed**：所选规则以字符串常量入
  ResolvedS0Methods.spread_scalar_rule；scalars 派生函数配单测锁值。
- **计算成本**：A/B 一次性；C 每 fill 一次 dict 查找，可忽略。
- **Fable 推荐**：B-i ＋ IR-7 Option i 为 Primary、Option ii 入
  sensitivity 通道（**接受 Sol 的 IR-7 立场**，撤回我先前"ii 为
  Primary"建议）；C 不预判违冻结，列为备选交裁。
- **Sol 立场**：公式明确后偏向 B；IR-7 维持现值为 Primary、+1 tick
  作显式 sensitivity。
- **分歧状态**：spread 归约 A-i/A-ii/B-i/B-ii/C 待裁（Fable=B-i，
  Sol=B 族）；IR-7 双方一致（i Primary＋ii sensitivity）。
- **落地**：IR（IR-7 定稿＋新 IR-27a）。

## DR-2（DR-M6-B-v2）20 日实现波动率三分位

- **frozen source**：S0 §2"20 日实现波动率三分位分层"；附录 A step 3
  "year × volatility_regime × event_flag"。
- **精确歧义**：窗口/收盘源/半日与 roll/收益型/ddof/滞后/定界总体/
  warm-up/NA 全部未逐字定义；§2 与附录 A 是否共用 mapping 未定。
- **候选 normative text**：vol20(d) = std(r_1..r_20, ddof=1)，
  r_i = (C_{t-i+1} − C_{t-i}) / C_{t-i}（simple；log 备选），
  C = **精确排期 RTH 官方收盘**（IR-19/26 同一定义点：常规 15:59
  bar close、早收盘取最后排期 bar close；15:44 与 settlement 备选，
  settlement 无数据=**data_unavailable**）；窗口=严格早于 d 的最近
  20 个有官方收盘的实际 RTH 交易日（lag 终点 d−1，无前视）；
  **跨 roll transition 的相邻收盘对**：Option r1=剔除该 return 并向
  前多取一日补窗；Option r2=照用（污染披露）。
- **定界总体**（三分位阈值）：(a) 全 Development 一次性（**ex-post
  descriptive**，须如此标注）；(b) within-year（同为 ex-post）；
  (c) expanding past-only＋burn-in（10:00 可观察）；(d) 固定先验期。
  §2 描述性分层可用 a/b；**附录 A 抽样若被要求 10:00 可观察须用
  c/d**——但附录 A 本质是事后可行性构造，Fable 认为可与 §2 共用
  a（幅度中性论证不依赖可观察性）；此点本身交裁。
- **NA**：<20 个合格先行收盘或成分缺失 → vol_na **独立层**（不入
  任何三分位、不删日；附录 A 分层含第四层 vol_na）。
- **影响**：仅分层/描述轴；不触 Primary 标签与成本。
- **conservation**：全日集 = T1∪T2∪T3∪vol_na（机器断言）。
- **Fable 推荐**：simple、ddof=1、official_close、r1 剔除补窗、
  定界=(a) 全 Dev（标 ex-post descriptive）、§2 与附录 A 共用同一
  mapping。**Sol 立场**：待其对 ex-post 标注与共用 mapping 表态。
- **分歧状态**：unresolved（等 Sol/Aaron）。落地：IR。

## DR-3（DR-M6-C）FP 分层构成基准

- **frozen source**：附录 A step 3（TP/FP 各自"按 year×regime×event
  分层后层内均匀随机"）＋"缺额按其余层的可用日数比例重新分配"。
- **精确歧义**：FP 的层**配额**来源未定；SA-18 已证：A 机制下缺额
  规则不可达。
- **机制形式化**：
  - **A（自池构成）**：fp_alloc_s = Hamilton(n_fp × avail_fp_s /
    Σavail_fp)；TP 同理自池。缺额规则死代码。
  - **B（FP 跟随 TP 构成）**：fp_alloc_s = Hamilton(n_fp ×
    **selected_tp_s** / n_tp)（权重=该网格点**实际选中** TP 构成——
    非完整 TP 池、非目标配额；因 TP 配额由确定性 allocation 决定、
    seed 只动层内日期，故 selected_tp_s 跨 seed 稳定）；FP-only 层
    权重 0；TP-only/零交集层（FP 无可用日）→ 缺额按其余层 FP
    可用量比例再分配（冻结字面激活）；tie-break=层键升序；
    守恒断言 Σfp_alloc == n_fp；realized FP 构成与 TP 构成的逐层
    偏离全披露。
  - **C（第三机制，补列）**：FP 按**全 FP 池**在 TP-支撑层上的
    截断再归一构成（介于 A/B；无缺额时=A 限制到 TP 支撑）。
- **经济/分类器机制**：B=层内混淆模型（分类器 FP 与 TP 同域）；
  A=分类器错误与无条件非延续总体同分布；C=域限制但错误率随 FP
  密度。
- **影响**：改变 D_FP 混合构成 → 网格 EV 区域形状；不触 Primary。
- **Fable 推荐**：B。**Sol 立场**：暂倾向 A。
- **分歧状态**：**unresolved_disagreement（正式登记）**，Aaron 裁。
- 落地：IR；ResolvedS0Methods.fp_allocation_basis。

## DR-4（DR-M6-D）Primary bootstrap 总体与统计量

- **frozen source**：S0 §9（"stationary bootstrap，期望块长 5 交易日，
  10,000 次，seeds {7,13,31}，百分位法 95% CI"）。
- **精确歧义**：抽样序列（D_TP 子序列 vs 完整交易日序列）；每日
  状态编码；10,000 的归属；三 seed 合并；统计量定义。
- **每日状态表（normative 提案）**：
  | 状态 | 编码 | 序列地位 |
  |---|---|---|
  | oracle 交易日（该 θ） | 当日 USD P&L | 入 |
  | 可交易未选日（FP/低于 θ） | 0（观察到的不交易） | 入 |
  | 方向不可判/Y_cont NA 日 | **NA——不得静默写零** | Option n1 剔出序列（披露 n）；Option n2 保留 NA 且统计量分母排除 |
  | 冻结整日剔除（半日/零bar） | 不在 L3 样本 | 不入 |
  序列=结构合格日按日期序（block 邻接=真实交易日邻接）；
  统计量=**每交易日均值 USD**（频率×盈亏联合；口径与 D_TP 均值
  不同须在契约 A7 标注）；10,000 次**每 seed**（现实现语义）；
  三 seed 各自 CI＋收敛披露＋引用 seed 7（固定约定）；percentile
  linear（正式化现披露）；**CRN**：同 θ 内 engine×scenario 共用
  重抽索引（可比性）vs 各自独立——交裁。
- **与 MC 频率关系**：S0 CI 为描述性；MC 世界层自行重抽日集，
  频率不双计（口径"更一致"而非同构——MC 另含账户非线性）。
- **Fable 推荐**：完整序列＋n1 剔除披露＋每 seed 10k＋CRN 共用。
- **Sol 立场**：提出完整序列方向；细目待其确认。
- **分歧状态**：方向趋同，细目 unresolved。落地：IR。

## DR-5（DR-M6-E）网格 K 次重复与收敛

- **frozen source**：附录 A（每网格点抽样；seeds {7,13,31}）；
  MC_METHOD_SPEC §5（收敛四规则）。
- **精确歧义**：K 未定义；stream 是否含 θ；收敛判据在 S0 侧的
  作用面。
- **提案（K=200 仅提案，未实现）**：K/seed/cell=200，k 从 **0**；
  RNG=PCG64 via default_rng(SeedSequence([master, GRID_TAG, θ_mil,
  q_mil, r_mil, k]))——**θ 入 stream**（避免跨 θ 相同抽签相关）；
  per-k 独立流 ⇒ K→2K 时前 K 个 repeat **天然前缀嵌套**；
  规模：63 cells×3 seeds×200≈37,800 次分层抽样（合成 benchmark
  于实现时报告，预估分钟级）；infeasible cell：K 全跳、照常全报；
  最大加倍 2 次（200→400→800），仍未收敛 →
  `infeasible_by_convergence` fail-closed 标记。
- **收敛判据（MC §5 全四条，非仅离散度）**：verdict category 不变；
  关键分位变化 ≤ max($25,5%)；inner MCSE ≤ between-world SD 10%；
  三 master seeds 判定一致。S0 侧先报 realized 统计量跨 K 离散度，
  完整四条在 MC 接线处生效——K 政策须与 MC 共裁。
- **CRN scope**（engine/scenario/platform/policy 轴复用或隔离）：
  **未裁不得默认**；提案=engine/scenario 共用（可比）、platform/
  policy 隔离（MC 侧）。
- **Fable 推荐**：如上提案。**Sol 立场**：待表态。
- **分歧状态**：unresolved。落地：IR＋MC spec 交叉引用。

## DR-6（DR-M6-F）event NA 在附录 A 分层中的地位

- **frozen source**：IR-12/18（F10 多事件日=NA＋sidecar，互斥五类
  128+134+83+2528+9）；附录 A step 3（event_flag 分层）；§3 NA
  政策（不删日）。
- **当前事实（精确陈述）**：`"none"` 保持 `"none"`；**仅 `None`**
  （multi-event NA，9 日）被映射为未批准哨兵 `"none_or_na"`。
  无合并发生；缺陷=哨兵词不在批准词表。
- **选项**：
  - **F1**：五层 {CPI, NFP, FOMC, none, NA_multi_event}——NA 日
    独立层，可抽样、不删日、词表=IR-12/18 现有五类。
  - **F2**：三层 {event, non_event, event_na}。
  - **F3**：NA 日排除出网格抽样池（9 日；与"不删日"精神冲突，
    列出仅为完备）。
- **影响**：层粒度 ↔ 每层样本量（F1 的 FOMC×年×regime 胞可能
  很薄 → 缺额路径更常触发，与 DR-3 联动）；样本守恒：
  Σ层 = 全部 TP/FP 日（F3 除外）。
- **Fable 推荐**：F1（词表零新增）。**Sol 立场**：待表态。
- **分歧状态**：unresolved。落地：IR；
  ResolvedS0Methods.event_na_stratum_rule。

---

## 汇总

| DR | 字段 | Fable | Sol | 状态 |
|---|---|---|---|---|
| 1 | spread_scalar_rule＋adverse_slippage_final | B-i；IR-7=i 主+ii 敏感 | B 族；同 IR-7 | spread 子式待裁；IR-7 一致 |
| 2 | volatility_regime | official_close/simple/ddof1/r1/全Dev ex-post/共用 | 待表态 | unresolved |
| 3 | fp_allocation_basis | B | A | **unresolved_disagreement** |
| 4 | bootstrap_population | 完整序列+n1+每seed10k+CRN共用 | 方向同 | 细目 unresolved |
| 5 | grid_repeat_policy | K=200/θ入流/前缀嵌套/加倍2次 | 待表态 | unresolved |
| 6 | event_na_stratum_rule | F1 五层 | 待表态 | unresolved |
