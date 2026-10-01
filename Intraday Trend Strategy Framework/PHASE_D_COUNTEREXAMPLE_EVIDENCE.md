# PHASE D — 反例证据附件（旧候选 vs 新候选）

**里程碑**：M6.1.4
**旧候选（OLD）**：`1e188b54ace011bb4c2ab7356f775af6d32aab37`（M6.1.3，即本工作树的父 commit）
**更早前身**：`712532ddd6d2276ec665eaed6db7ce270df9c544`（M6.1.2，仅类 14 用到）
**新候选（NEW）**：`UNCOMMITTED_WORKTREE_SNAPSHOT` —— 尚未提交的工作树字节
（测矩阵当时为 `10 modified + 8 untracked`；父 commit 即上述 baseline）

> **快照时点声明其二（M6.1.6 / S3 补，2026-08-09）—— 本矩阵现已落后两轮。**
>
> 本文件头部的 "NEW" 侧指的是 **M6.1.4-ARCH** 的工作树字节。此后：
> **R2 轮**改动了 `scripts/s0_real_run.py`、`src/itsf/contracts.py`、
> `src/itsf/s0/evidence.py`；**M6.1.6 轮**又改动了
> `scripts/s0_real_run.py` 与 `src/itsf/s0/runner.py`，并新增了
> `src/itsf/s0/output_proof.py`（＋其测试）。当前工作树为
> **21 条** `git status --porcelain` 条目，**不再是** `10 modified +
> 8 untracked`。
>
> **因此下表 NEW 侧的每一个拒绝串都应读作「M6.1.4-ARCH 字节上的当时实测」，
> 而不是当前字节的行为。** 本矩阵**未在 R2 字节上重跑，也未在 M6.1.6
> 字节上重跑。**
>
> **M6.1.6 明确未做的事**（故本矩阵的失效范围不再扩大）：本轮未触碰
> 叶／token 证据系统、未触碰 EV-11 语义、未触碰 `evidence.py`。
> 本轮新增的两条接缝（prepare 生命周期、治理输出证明）**不在本矩阵的
> 十四类反例覆盖范围内**，其证据在
> `CODEX_REVIEW_PACKET_M6_1_6.md` §1／§3。

> **快照时点声明（M6.1.4-R2 补）**：本矩阵测于 **M6.1.4-ARCH** 的工作树字节，
> 该字节**已不存在**（R2 轮的 S1／S2 车道其后改动了 `scripts/s0_real_run.py`、
> `src/itsf/contracts.py`、`src/itsf/s0/evidence.py`）。因此下表 NEW 侧的
> 拒绝串应读作**当时**的实测值；其中配置网关相关的类 13／14，其"闭合"结论
> 已被 R2 轮部分证伪（见 `CODEX_REVIEW_PACKET_M6_1_4.md` §9.1——网关在
> ARCH 字节上仍可被两条新机制绕过并交出非规范实例）。R2 修复后该两条机制
> 各自被新阶段拒绝，但**本矩阵未在 R2 字节上重跑**。

## 0. 证据溯源声明（诚实披露）

- 旧候选侧的复现通过 `git archive <commit>` 导出快照后以 importlib 加载执行，
  **不使用 worktree / branch / checkout**，仓库工作树全程只读。该车道进出场
  均验证 `git status --porcelain` 与 `git diff | sha256` 字节恒等，结论为
  未修改仓库任何文件。
- **harness 脚本位于会话临时目录**
  `…\scratchpad\phase_d\`（`sides.py` / `common.py` / `bundles.py` /
  `forge.py` / `c1_6.py` / `c4_probe.py` / `c4_c6_fix.py` / `c7_12.py` /
  `c13_14.py`，另有 `old/`、`pred/` 两个 git-archive 快照目录）。这些脚本
  **未入库**（临时目录内容不属于仓库工件）。本附件的矩阵为
  该车道最终报告的**转录**，不是重新执行的结果；逐例复算需重建 harness。
- 全部 fixture 为合成数据（`tests/test_m6_chain.py` 的 `_market()` /
  `_payload()` / `_test_methods()` 惯用法）。**零真实数据读取、零真实 S0
  运行、`RealChain._ensure` 从未在真实数据上调用。**
- 正向对照（production-shaped，非最小假 dict）：真实
  `build_full_study_result` 载荷在两侧**均可封存**；真实 builder 产出的
  `{DAY_STRATA, SEED_MANIFEST, GRID_SAMPLES}` bundle 在两侧**均被接纳**
  （`formal_seal_admission → []`）。因此下表每一条 NEW 侧拒绝都是真实
  判别，而非"一律拒绝"的退化行为。

## 1. 十四类矩阵

| # | 伪造内容 | 边界 | OLD 结果 | NEW 结果（拒绝串摘要） |
|---|---|---|---|---|
| 1 | 单条 `TradePathRecord.final_pnl_per_contract` +500（compute 后、render 前） | `render_s0_report` | **SEALED**（11 文件全集封存） | **REFUSED** `evidence reconciliation failed: evidence_series_pair_mismatch:oracle_daily\|theta_0.5\|E1\|Base\|pooled[0]` ＋ sum/mean/max 三处 |
| 2 | 内部 `d_tp` 与 formal oracle 序列、stability、bootstrap、grid 混合 P&L **全部同步**重算 | `render_s0_report` | **SEALED**（两轮修补后；旧 `reconcile_with_internal` 逐条指明该修哪里，修完即过） | **REFUSED** 同族 ＋ `evidence_stability_mismatch:…epochs\|2018-2021.sum_usd`、`evidence_cr2_oracle_mean_vs_series`、`evidence_cr2_bootstrap_mean_vs_series` |
| 3 | 改写封存 JSONL 单行，并修复 `sha256` ＋ `files` ＋ `sealed_files` ＋ 重发 `S0_REPORT.json` | 两个校验器 ＋ 对账 | **SEALED**（`validate_formal_payload` 与 `validate_sealed_files` 均返回 `[]`） | **REFUSED** `evidence_series_pair_mismatch:…686.26!=1463.26`；`…sum_usd:10980.16!=11757.16` |
| 4 | grid 日期/P&L/总数同步伪造（FP 日换 TP 日，计数、realized、markers、allocation、mixture 全修） | `render_s0_report` | **SEALED** | 见 §2（PHASE D 当时 **SEALED＝HIGH 发现**，已于修复轮闭合） |
| 5 | formal 与 evidence 共享可变对象身份 | capture 身份 ＋ renderer | **机制不存在**（`ModuleNotFoundError: itsf.s0.evidence`；`oracle_daily[tk].day_universe is study.per_theta[tk].day_universe` 为 `True`——formal **就是** producer 树） | **分离**：57 870 formal 节点 ∩ 434 evidence 节点 = ∅；篡改本身 **REFUSED** `evidence-reducer divergence from producer output — refusing to seal: oracle_daily.day_universe:theta_0.5` |
| 6 | capture **之后**改 formal（两个 θ 的 day_universe 各改一天，计数不变、θ 嵌套守恒） | `render_s0_report` | **SEALED** | **REFUSED** `evidence-reducer divergence … oracle_daily.day_universe:theta_0.3; …theta_0.5` |
| 7 | DAY_STRATA ×7：year↔date、era 槽填 epoch、epoch 槽填 era、`event_na=True` 配 `'none'`、`event_na=False` 配 `None`、`d_open=0` 当 TP、θ 嵌套违反 | `formal_seal_admission` | **ADMITTED 7/7** | **REFUSED 7/7**，例：`micro_execution_era '2010-2013' != the era RECOMPUTED from the date itself ('counterfactual_micro_execution', frozen S0 §6 boundary '2019-05-06')`；`d_open == 0 … can never be TP`；`THETA NESTING MONOTONICITY violated` |
| 8 | GRID_SAMPLES ×7：缺件、重复 (θ,eng,scn)、1 胞、62 胞、64 胞、q/r 乱值、TP/FP 对调 | `formal_seal_admission` | **ADMITTED 6/7**（q/r 乱值 = ALREADY_REFUSED，但旧侧漏掉 `r_mil=-5`） | **REFUSED 7/7**，例：`cells is missing 62 of the frozen 63-point (q, r) lattice REBUILT from gridmix.Q_GRID_MILLIS x R_GRID_MILLIS`；`DUPLICATE GRID_SAMPLES: 2 artifacts … claim the same (theta, engine, scenario)`；`1 date(s) are marked TP for theta_0.5 but DAY_STRATA does not class them TP` |
| 9 | SEED_MANIFEST：缺失、重复、seed 类型 `7.0` / `"7"` / `True` | `formal_seal_admission` | 缺失＋重复 **ADMITTED**；三种 seed 类型 ALREADY_REFUSED | **REFUSED 5/5**：`dependency SEED_MANIFEST is ABSENT`；`… is DUPLICATED`；类型三例连带 withhold 依赖它的 grid |
| 10 | 依赖非法但被依赖件自称可封存（grid `formal_sealable=True` ＋ 破损/缺失 DAY_STRATA） | 准入 ＋ `_partition_admission` | **两次都放行被依赖件**（`ADMITTED=['grid_samples','seed_manifest']`） | **两次全 withheld**：`dependency DAY_STRATA is ABSENT … a lone grid submission can never bypass the dependency graph` |
| 11 | str/int 混合的未知键（两个校验边界） | 准入 ＋ `validate_formal_payload` | **两处均 CRASH**：`TypeError: '<' not supported between instances of 'int' and 'str'` | **REFUSED 两处**：`unexpected extra field(s) [...]; non-string field name(s) ['7']` / `non_str_key:$.frequency:7` |
| 12 | 非字符串 manifest 键 | `validate_sealed_files` | **CRASH** `AttributeError: 'int' object has no attribute 'partition'` | **REFUSED** `sealed_file_spec_key_type:13`；`sealed_files_manifest_entry_missing_file:7` |
| 13 | injectables：空 / 缺键 / 多键 / 类型错 / 非 Mapping（经**真实** resolver，仅换 `_resolved_methods`/`_approved_injectables` 两个源 seam） | `resolved_study_config` ＋ `RealChain.ready` | 冷路径 ALREADY_REFUSED 但**理由错**（报"derivation not implemented"，注入件门根本没走到）；**缓存路径 5 例中 4 例 CRASH**（`TypeError: derive_study_config() missing 3 required keyword-only arguments`、`ValueError: StudyConfig…`） | **REFUSED 5/5 两条路径**，按 schema 命名：`injectables.empty`、`injectables.missing_key:regime_of`、`injectables.extra_key:extra`、`injectables.spread_scalars_not_a_tuple`、`injectables.not_a_mapping`；`ready()=False`，builder 调用 **0** |
| 14 | resolver 旁路：缓存注入已解析配置、鸭型 methods 带说谎 `__eq__`、methods 匹配下走私 injectables、绕过冻结 dataclass | `resolved_study_config` ＋ `ready` | **`1e188b5` 已全部拒绝（4/4）**；按任务书回退到前身 **`712532d` 上活复现 3/4**：`resolved_study_config -> RESOLVED: injected \|\| RealChain().ready() -> True: stage C wiring ready (full study chain)` | **REFUSED 4/4**，同拒因串；builder 调用 0 |

**判读**：13 类当场闭合。类 11/12/13 在旧候选上表现为**异常退出**——校验器
抛出 `TypeError`／`AttributeError`（见表内 OLD 列的原始堆栈串）而非返回问题
列表，即**违反 `(problems: list)` 契约**、产生**不确定的拒绝形态**。新候选
一律转为有理由的确定性拒绝。

> **措辞勘误（M6.1.4-R2）**：本行原写「gate 因异常 **fail-open**」。该括注
> 与本表自身的证据相反，应予撤销：表内 OLD 列记录的是未捕获异常
> （`TypeError: '<' not supported…`、`AttributeError: 'int' object has no
> attribute 'partition'`、`TypeError: derive_study_config() missing 3
> required keyword-only arguments`）。未捕获异常会中止调用方，
> **没有任何工件被准入、没有任何字节被封存**。本附件**不主张**这三类情形
> 下封存被放行；**全文无任何证据表明封存被允许**。准确的描述是
> 「异常退出／契约破坏／不确定的拒绝」，不是 fail-open。

## 2. 类 4 —— PHASE D 当场的 HIGH 发现与其闭合

PHASE D 判定：`evidence._reconcile_grid` 当时只对账池规模与解析记录数，
**per-seed 抽样内容**（`tp_dates` / `fp_dates` / `day_markers` /
`realized_precision` / `realized_recall` / allocations / `mixture_mean_pnl`）
无任何独立前像。三个变体在**两侧**均封存，其中最强的一个把
**`1999-01-04`（不属于任何 S0 宇宙的日期）**写进 `tp_dates` 并出现在封存
字节里：`S0_REPORT.json … per_seed['7'].tp_dates == ['1999-01-04', …]`。
诚实边界：池级变体（`n_tp_available += 1`）两侧**都**能拒（
`feasibility_grid_seed_realized_recall_mismatch`），故缺口限于抽样**内容**。

**修复轮闭合**（本工作树快照内）：新增 `evidence._reconcile_grid_draws`，对每个
per-seed 抽样施加三重锚定——

1. **成员资格**：每个抽中日期必须属于 EV-1 分区的对应类别
   （`evidence_grid_draw_membership_tp/fp`），并检查重复与 TP/FP 交叠；
2. **算术恒等**：`n_tp_actual`/`n_fp_actual`、`day_markers`（CR-8）、
   `realized_precision`、`realized_recall`、`allocation_tp/fp` 合计；
3. **P&L 重导出**：`mixture_mean_pnl` 由**已解析的封存字节**在恰好抽中的
   日期上重算（`evidence_grid_draw_mixture_mean`），抽中日期若在封存记录
   中不存在则 `evidence_grid_draw_pnl_rows_missing`。

反例测试（`tests/test_s0_evidence.py`）：
`test_grid_draw_swapped_class_date_is_caught_despite_repaired_totals`、
`test_grid_draw_out_of_universe_date_is_caught`、
`test_grid_draw_marker_desync_is_caught`、
`test_grid_draw_mixture_mean_tamper_is_caught`，
另有 `test_grid_draw_checks_pass_on_the_honest_fixture` 作诚实对照。

**残留 PARTIAL（不声称闭合）**：RNG **重放**本身——即"流在合法成员中
究竟抽了哪几天"——仍不可验证，因分层键 `(year, volatility_regime,
event_flag)` 的两个轴无既定词汇（DR-2 / DR-3 / DR-6）。封存的
`HANDOFF_ADMISSION.json` 以 `PARTIAL:feasibility_grid.per_seed:` 明示。
