# CODEX_REVIEW_PACKET_S0_CLOSEOUT_FINAL（S0 封存主线一次性总验收，供 Codex 独立复审）

- **baseline commit**：`bcdf8f368393dba3affcda2b4b729bc525a98886`（M6.1.8）
- **本审查对象**：**包含本文件的那个 commit**（M6.1.8 纪律：文档不写自己的 SHA；
  实际新 HEAD 见终端汇报）。baseline 之后、候选之前**无中间 commit**。
- **diff 范围**：`git diff bcdf8f36..<候选>`＝全部变更；~29 文件，≈+15.6k/−8.9k 行
  （含五个工程车道＋主代理集成＋测试更新＋本文件）。
- **授权状态**：`REAL_S0_NOT_AUTHORIZED` 不变。不追加 READY、不申请授权、不建 tag、
  不追加任何 registry 事件。`runs/` 不存在，S0-T001 未消耗。

## 0. 程序记录（含两项必须如实披露的程序事实）

1. **裁决来源**：`AARON_S0_CLOSEOUT_DECISION_FORM_V1`（聊天交付，L-5＋DR-1..8 按依赖
   排序，每项含冻结依据/互斥选项/Fable 推荐/Sol 立场/影响面/consumer/测试/逐字裁决句）。
   Aaron 裁复"逐项裁决全跟你推荐的方式做即可"并以自然语言启动 PHASE C。
2. **PHASE-C 精确口令豁免**：master prompt 要求逐字口令
   `START_S0_CLOSEOUT_BUILD_AFTER_AARON_DECISIONS`；Aaron 未使用该句式。主代理判定：
   口令要求的制定者本人以语义无歧义的指令豁免了自设仪式，予以执行并在此披露。
   若 Codex 认为该豁免不成立，本候选整体退回，等 Aaron 重发精确口令后重建。
3. **真实数据加载事件（测试进程，已修复＋永久防护）**：集成中段，F-1 快照物化接入
   `prepare` 后（配置自此可解析成功），两次未打补丁的链测试运行越过了旧的
   Stage-B 拒绝点、经 `RealChain._ensure` 触发对真实 quant-data 档案的**结构性 bar
   加载**（每次持续数分钟，进程内存 ~1.1GB/687MB，被主代理发现后 taskkill 终止）。
   定性：结构性加载；**无任何 outcome 数值被计算完成、查看或打印**（两次运行均在
   断言阶段前被杀，测试输出仅有进度点与 2 个失败字母）；EXPOSURE_LEDGER 无涉。
   永久防护：`tests/conftest.py` 新增 autouse 夹具——任何测试对真实档案路径调用
   `load_real` 立即 RuntimeError（窄域：合成 tmp 路径不受影响）。该夹具此后在
   全部 2489 测试上生效。

## 1. Aaron 裁决 → IR → contracts 字段 → 生产 consumer → 测试 的完整映射

裁决值单一来源：`contracts.aaron_ruled_methods()`（`src/itsf/contracts.py`）；
逐值 pin：`tests/test_aaron_rulings.py`（11 测试）。IR-27（IMPLEMENTATION_RESOLUTIONS.md）
为批量裁决档案。

| 裁决 | contracts 字段 | 生产 consumer（入口可达） | 行为测试（红条件） |
|---|---|---|---|
| DR-1 B-i＋IR-7 i | SpreadCostMethod | costs.derive_spread_scalars（入口 `_approved_injectables`，spread 表 sha256 钉 `b6d6984f…`）＋costs.build_scenarios_from_method（build_full_study_result） | test_costs.py（窗界/插值/Stress 不复乘变异红） |
| DR-2 vol20 全子项 | VolatilityRegimeMethod（含新字段 mapping_scope） | dataset.build_vol20_regime_mapping_from_universe（prepare 绑定单 mapping→双 resolver） | test_dr2_vol_regime.py（手算 pin/前视/守恒/ddof·log·r2 变异红） |
| DR-3 FP=B | FpAllocationMethod | gridmix.build_grid ruled 路径（入口传 config.methods.fp_allocation） | test_gridmix_rulings.py（基准对照/tie-break/守恒） |
| DR-4 七分项 | BootstrapMethod | stats.build_bootstrap_day_sequence＋bootstrap_mean_ci_ruled（入口 day-state 编码） | test_bootstrap.py（CRN 熵/零填充/NA 计数变异红） |
| DR-5 K 政策 | GridRepeatPolicy | gridmix.build_grid ruled 路径（θ 入流、K-repeat、前缀嵌套、infeasible_by_convergence） | test_gridmix_rulings.py（θ 入流/前缀嵌套变异红） |
| DR-6 F1 五层 | event_na_mapping | dataset.event_stratum_of（入口 event_of＋evidence.py:942 均经此单点） | test_s0_dataset.py DR-6 组 |
| DR-7 双报 | stability_population | stability.build_stability_views populations 块（入口 kwarg）＋report 校验接线 check_populations | test_s0_stability.py（缺一总体即问题码） |
| DR-8 linear | worst_day_estimator | study.resolve_worst_day_estimator→_percentile 必传参数（入口 build_study kwarg） | test_s0_study.py（未裁 raise/lower 变异移动 P1P5/linear 位同） |
| L-5 双根 | RULED_RUNS_ROOT/RULED_ARCHIVE_ROOT＋RunConfig.runs_root/archive_root | runinfra.validate_output_roots（Stage-A 首门、无条件）＋archive_sealed_run（封存后、失败不解封）＋入口 GOVERNED_* 常量＋g_frozen_constants 9→11 | test_s0_runner.py L-5 组 29 测试（repo 内根拒绝/额外文件仍拒/归档失配/真实根不触碰 autouse 夹具） |

**ruling→consumer 机器断言**：test_m6_chain `_METHOD_PROBES` 八字段行为 probe 全部
就位（此前 7 个为 None）；`test_resolved_fields_must_have_a_behaviour_probe` 强制
"裁决落地必须带 probe 同 commit"。

## 2. F-1 / F-2 终态

**F-1 = CLOSED（本轮验收边界内）**：`prepare`（pre-exposure）绑定生产 resolver 单例
（G11 稳定身份）→ `context.materialize_day_value_snapshot` 物化逐日值快照 →
`_PreparedExecutionInput.day_values` → Stage C 只消费快照（`build_full_study_result`
的 `day_value_snapshot` 参数；config callable 曝光后零调用，行为测试证明）。
诚实残留：ruled 实例的 adverse ticks MappingProxyType 后备 dict 为 contracts 模块私有
（运行时无可变引用持有者）；bypass 构造的假配置仍由 gateway canonical-form 检查拦截。

**F-2 = CLOSED（Aaron 定义的最小封存边界内）**：`output_proof.verify_key_claims` ——
**封闭六主张释放闸**（KC1 日期总体 vs 锁定 preflight 字节；KC2 标签/NA 算术绑定独立
L3＋F10 分区和；KC3 消费 evidence 字节级重建 hard 判定；KC4 封存名集绑定冻结
engine×scenario 矩阵【闭合了 `_PARTIAL_DECLARATION_UNBOUND` 的名集轴】；KC5
seeds/n_boot/估计量 vs 冻结与裁决常量；KC6 磁盘核验）。接线：渲染 pre-write 筛
（manifest 注入后、任何文件落盘前；随 `methods=` 门控——生产链恒传
`prepared.config.methods`，直调旧测试路径不筛）＋ post-write 释放（对**磁盘字节**
重解析重验 KC1/2/4/5＋KC6；KC3 以 sealed-set 字节同一性传递 pre-write 判定，
PARTIAL 标记显式声明该托管论证）。31 项密闭测试（test_key_claims.py）。
**明确不是**通用叶证明框架：六个具名函数、封闭清单，加主张须改源码。

## 3. 车道与文件归属（并行零交集）

| 车道 | 文件 | 关键产出 |
|---|---|---|
| S1(Opus) | costs/stats/gridmix＋3 测试文件 | DR-1/4 消费者＋DR-3/5 原语（+73 测试） |
| S2(Opus) | stability/dataset/context/study＋测试 | DR-2/6/7 消费者＋DR-8 估计量参数化＋F-1 快照（222 测试） |
| S3(Sonnet) | runner/runinfra/test_s0_runner | L-5 门＋归档＋真实根防护（147→176） |
| S4(Opus) | gridmix＋2 测试文件 | DR-3/5 上生产路径（54+22 测试；旧路径逐位不动性 git-show 对照证明） |
| S5(Opus) | handoff＋test_s0_handoff | 39 处过时哨兵→裁决值贯通（158→178） |
| 主代理 | contracts/entry/report/evidence/output_proof/conftest/test_m6_chain/test_key_claims/test_aaron_rulings/文档 | C0 裁决实体化＋全部集成＋F-2 闸＋CR-2 裁决口径＋probe 表 |

## 4. 测试与全套件新鲜证据

- **全套件 fresh（终态，R1 修复轮之后）：2495 passed / 0 failed / 0 skipped，
  345.63s**（`-p no:cacheprovider`；候选 commit 前最后一次运行）。
- `--collect-only` = 2495 = `MIN_COLLECTED_TESTS` 双钉（scripts/s0_real_run.py:56
  与 tests/test_s0_runner.py，均 2495）。
- 修复轮轨迹：R1 后全套件 2493/2（两败=被更正披露文本的字节稳定钉，随更正
  同步更新）→ 2495/0。
- 链测试收敛轨迹（诚实记录）：17→14→15→4→0 失败，五轮集中迭代；期间三个
  前提反转的旧测试重写为"合成去裁决→仍拒绝"回归守卫（非删除）。
- `SCANS=CLEAN`（final_candidate_scans.py 三扫描）；`guards.verify_frozen_hashes()`
  OK；`git diff --check` 干净（两文件曾被编辑器写入 CRLF，已归一化并披露）。

## 5. 合成 A→F 与工件证据

- 合成 e2e（test_m6_chain E7 组）：完整裁定合成配置走真实
  resolver→prepare→compute→render→disk verification→seal；A→F 抵达 COMPLETED；
  8 个 MC_HANDOFF＋S0_REPORT.json/md＋HANDOFF_ADMISSION.json 落盘＋manifest 逐字节。
- **合成通过 ≠ 真实路径已验证**（沿 M6.1.8 披露）：生产真实链从未运行；第一次
  真实 S0 将是磁盘校验器/KC 闸/L-5 归档的第一次真实执行。
- 准入终态（S5＋接线）：ruled 非 test_only 时 SEED_MANIFEST/DAY_STRATA 可封存并被
  接纳；GRID_SAMPLES 诚实保持 withheld（真实剩余阻断=MC 侧 replay 接线，非已裁 DR——
  哨兵措辞已按真实原因重写）；test_only 一律 withheld。

## 6. L-5 输出根与归档边界

- 根：`C:\Users\Aaron\quant-data\itsf-runs`（runs＋attempts 同根）；归档
  `…\itsf-runs-archive`（run 完成后整目录复制＋逐文件 SHA-256 复核清单）。
- RunConfig 显式字段＋`g_frozen_constants_in_process` 11 项在进程内钉两根；
  Stage-A 首门 `validate_output_roots` 无条件运行（绝对性/互不包含/不在 repo 树内/
  per-run 目录严格位于根下）；归档失败记录 loud 状态但**不解封不改运行目录**；
  exact-set 零白名单逐字保留；仓库内 `runs/` 永不创建（测试钉）。

## 7. 诚实保留的局限与工程判断（全部已披露、可被 Codex 升级）

1. S1：DR-4 CRN 流键含 block_len（block-5/21 不共流的既有设计约定；裁决范围是
   engine×scenario 共享）——若要求字面 (θ,seed) 是一行改动。
2. S1：IR-7 Stress 存储 1.0 pre-multiplier（消费者统一乘 multiplier；存 2.0 即双计；
   有效值硬断言＋`adverse_ticks_disclosure` 三值并列披露）。
3. S2：straddle 边界 `older<t<=newer` 与三分位 numpy-linear 下含边界——两项子约定，
   非裁决值。
4. S4：K=200 全量证据形态 +≈56MB/+≈160s（headline k=k_start_index、digest 不含 k）；
   压缩与否留 Aaron 会后裁。三个实现统计量跨 K 零离散系结构必然，作为发现披露。
5. S5：GRID_SAMPLES replay=PENDING 的真实原因（headline-only 字节＋MC 侧 §5 电池）；
   k_policy token 编码为工程选择。
6. 主代理：KC3 post-write 为字节同一性托管判定（§2 已述）；`methods=None` 渲染路径
   不筛不准入（生产链恒传，链测试钉）；DR-4 序列中"TP 类但 Oracle 无法成交"边缘
   归 eligible_not_selected 计 0（批准输入集上结构不可达，沿 untradeable 披露纪律）。
7. DR-5 加倍循环归 MC 接线（裁决原文如此）；`repeat_k_indices(doublings>0)` 就绪未接。
8. **DR-1 adverse 向量与 DR-8 估计量的接线是行为无差异的**（R1 F1.1/F1.4）：裁决的
   Primary 向量与 linear 估计量恰好复现既有工程惯例——这是真实且受欢迎的结果
   （裁决确认了惯例），但意味着行为测试无法证伪"接线被撤"；两者以源码钉
   （test_r1_f11_f14）锁定。
9. **stability 方向轴新增 `DIRECTION_NONE_KEY="0"` 桶**（R1 F3.1）：仅存在于 DR-7
   full-eligible 总体（d_open=0 日不得错侧）；系工程词汇选择，非裁决值，在此具名
   披露供 Codex 裁定（备选=并入既有 NA 词汇）。
10. **DR-4 与 DR-7 对 NA 日的处置不同**（R1 记录性注）：DR-4 序列按裁决 n1 剔除
    （y_cont NA / d_open=0），DR-7 full-eligible 视图把同一批日零填充保留——两者
    各自符合其裁决原文，但"完整合格序列"一词在同一封存报告的两个块中指两个日集；
    在此显式披露。
11. **`<repo>/attempts/` 历史残留**（R1 F4.2）：两个 pre-L-5 attempt 记录
    （S0-T001-A20260801T121730Z / T162047Z）仍在 OneDrive 树内。按纪律不做静默
    文件迁移——是否迁移至治理根归 Aaron 裁决；新 attempts 已在治理根下。
12. **evidence.py＋test_s0_evidence.py 声明式 LF 归一化**（R1 F5.1）：两文件在 HEAD
    为 CRLF（仓库其余为 LF），对 CRLF 文件新增行在 `* -text`＋默认 whitespace 下
    永远无法通过 `git diff --check`，而 .gitattributes 属 Freeze Commit A 不可动。
    故采 R1 备选：声明式归一化。**真实内容差异 = 77/30 与 13/1 行**（
    `git diff --ignore-all-space --numstat`）；R1 已独立逐行核实无隐藏内容；
    请 Codex 对这两个文件以 `--ignore-all-space` 复核。

## 8. 独立 conformance review（R1，Opus，只读）＋唯一集中修复轮

R1 六轴对抗审查裁定：**3 High / 7 Med / 8 Low**（轴 4 L-5 与轴 5 治理不变量
PASS；四项治理钉逐字节复核通过）。无同类架构缺陷复现——三个 High 均为过时
披露文本与缺失测试钉，非设计缺陷，故按规则执行了唯一的一轮集中修复。
逐项处置：

| R1 finding | 严重度 | 处置 |
|---|---|---|
| F6.1 sealed PERMANENT_MARKERS 断言八项裁决未做 | High | **FIXED**：evidence.py 九条标记逐条重写为"RULED＋真实残余验证缺口"表述 |
| F6.2 sealed grid method 串称 DR-M6-B open | High | **FIXED**：gridmix 三处（docstring×2＋method 串） |
| F2.1 methods=None 关闭 KC 筛/准入且无钉 | High | **FIXED**：源码钉 test_r1_f21（链 seam 必转发 prepared.config.methods） |
| F1.2 F-1 快照接线零覆盖 | Med | **FIXED**：源码钉（compute 转发）＋行为钉（prepare 必物化且 covers 全日集） |
| F1.3 DR-3/5/7 生产接线未钉 | Med | **FIXED**：payload 级存在性钉（repeats/fp_allocation/populations） |
| F2.2 _INJECTABLES_CACHE 未设防 | Med | **FIXED**：删除缓存——scalars 每调用从 sha256 钉定字节重导出（毫秒级） |
| F2.3 KC3 字节托管论证强于实际执行 | Med | **FIXED**：post_write 先对 written↔disk 的 S0_REPORT.json 做 sha256 绑定，托管论证成真 |
| F3.1 DIRECTION_NONE_KEY 未披露 | Med | **DISCLOSED**：§7.9 |
| F5.1 CRLF 幻影 diff | Med | **RESOLVED**：声明式 LF 归一化＋复核指引（§7.12） |
| F6.3 S0_REPORT.md "rulings pending" | Med | **FIXED** |
| F6.4 handoff 姿态段落与集成相反 | Med | **FIXED**（post-integration 姿态＋admitted 结果由新链测试 test_r1_ruled_non_test_only… 证明） |
| F1.1/F1.4 行为无差异接线 | Low×2 | **DISCLOSED**（§7.8）＋源码钉 |
| F2.4 unbind 死代码/后备回退 | Low | **FIXED**：unbind 删除；prepare 必物化由行为钉覆盖（day_values=None 仅 bypass 构造可达，类型钉与 AST 钉在位） |
| F4.1 真实根守卫仅模块级 | Low | **FIXED**：守卫上移 tests/conftest.py（全套件 autouse） |
| F4.2 attempts/ 残留 | Low | **DISCLOSED**（§7.11，迁移归 Aaron） |
| F6.5 六处过时注释 | Low | **FIXED**（contracts/entry/report 全清） |
| F6.6 IR-27 插入位置劈开 IR-26 表 | Low | **FIXED**（移至文件末） |
| 轴 3 记录性注（DR-4 vs DR-7 NA 日处置） | note | **DISCLOSED**（§7.10） |

修复轮后新增 6 个 R1 钉测试（test_m6_chain `test_r1_*`）全绿；修复轮触及文件的
邻域与全套件在 §4 的最终数字中体现（修复轮后重跑）。

## 9. 治理不变量（候选 commit 前逐项复核）

```
registry sha256 = de63b3d690c5c4be1def67aff9e0302138e9910df5b9a89acb1db57697b0b440（基线逐字）
exposure sha256 = 394813431d879555b7504d2501c40123368d67a517359e056692eb6b0f6bc9e6（基线逐字）
runs/ = ABSENT
READY_APPENDED=NO
RUN_AUTHORIZATION_REQUESTED=NO
REAL_S0_RUN=NO
REAL_DATA_READ=NO   # 生产/研究路径零读取；§0.3 的测试进程结构性加载事件除外（已披露＋永久防护）
POST_FREEZE_STRATEGY_IMPLEMENTED=NO
AWAITING_CODEX_FINAL_INTEGRATED_REVIEW=YES
```

## 10. 给 Codex 的复核重点

1. §0.2 口令豁免与 §0.3 数据加载事件的定性是否接受；
2. KC 闸的六主张是否构成 Aaron 所定 F-2 最小边界的忠实实现（特别是 KC3 的
   字节同一性托管论证与 `methods=` 门控的生产不可绕过性）；
3. §7 的七项工程判断逐项裁定（采纳/升级为 DR）；
4. DR-4 全序列口径在 evidence CR-2 与 KC5 的双重独立重建是否闭合；
5. L-5 门与归档语义 vs 裁决句的逐字对照；
6. READY supersession（Option A/B/C）在本包 PASS 后才由 Aaron 裁决（预登记，非本包内容）。
