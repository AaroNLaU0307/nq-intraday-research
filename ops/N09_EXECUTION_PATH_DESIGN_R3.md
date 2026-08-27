# N09 执行路径 —— 设计 R3（**仍未实现**）

```
RECORD_TYPE=DESIGN_FOR_CHALLENGE
NODE=N09 的门内代码（N09 的执行仍需 Aaron 的 P2）
BY=Opus 5，builder seat，2026-08-27
SUPERSEDES=ops/N09_EXECUTION_PATH_DESIGN_R2.md（R2；保留不改，作为被审过的那一份）
BASIS=R2 ＋ fresh Sol 对 R2 的 HOLD（3 High／1 Medium ＋ 五条最小解阻条件），
      裁定全文与 builder 逐条复现见 ops/RULING_SOL_N09_R2_HOLD_2026-08-26.md
STATUS=NOTHING_IMPLEMENTED
BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY —— 取 Sol 最小解阻条件 3 的**第二分支**
DESIGN_CONTRIBUTION=checkpoint／snapshot／day_rows／precheck 四组规则源自 08-25 与
      08-26 两个 Sol 会话，`DELEGATED=YES`，按其要求在 N09 lineage 具名登记。
      **该 08-26 会话自陈在这四组规则上非独立**，不得作为它们的唯一独立认证。
```

---

## 0. R3 相对 R2 改了什么，以及为什么这一版写得出来

**R2 被 HOLD 的最强反对是一个自相矛盾**：R2 同时要求 `C_BUILD_2` 在 staging
期间运行、`C_BUILD_3` 在 archive 尝试之后运行，**又**要求每一次 C_BUILD 拒绝都
证明「没有文件写入、没有 archive 尝试」。两者不可能同时实现，也不可能同时测。
现有 staging 机制**按构造**先写 `.partial` 字节再验它（`resolve_partial` 的
docstring 首行即 "Stage `intended` into `<filename>.partial` and decide what
happens"）。

**R3 的核心改动**：零副作用断言**只对 C_BUILD_1 成立**，另两个 checkpoint 换成
各自可测的不变量（§1）。

**关于「这一版写不写得出来」——builder 的一条自纠。** `ops/NEXT_HANDOFF.md` 此前
写「R3 在 D-3 返回之前写不了」。那是对 Sol High #2 的转述，而原文明确给了第二
分支：`or limit the authorized build explicitly to an always-refusing scaffold`。
五条最小解阻条件里 **1／2／4／5 全是 builder 的活**。R3 即取第二分支。

---

## 1. 条件 1 —— 三个 checkpoint 各自的副作用断言

R2 那条统一的「零副作用」被拆成三条，**每条都是它那个时刻真能成立、真能测的**：

### C_BUILD_1 —— 首次写入之前

```
门：row_schema_blind · day_set_exact · rows_digest_recompute
断言：输出根下 supplement 字节的**精确文件集合**在门前门后逐字节相同，且为空；
      零 archive 尝试。
可测：对输出根取 exact-set 快照，门前门后比对。这是本项目已有的 exact-set 磁盘
      不变量形态，不是新发明。
拒绝后：无残留可保，`residue_path` 由 §2 的 P3 边界决定。
```

### C_BUILD_2 —— staging 期间

```
门：seal_staging_partial
断言：**不是「无写入」**——`.partial` 字节按构造已存在。断言是：
      (a) FINAL 路径不存在；
      (b) 没有任何 `.partial` 字节被删除
          （`SILENT_DELETE_FORBIDDEN=YES`，已批准）；
      (c) 若发生分歧改名，分歧件存在于
          `<filename>.partial.divergent.<incident_id>`
          （`ND1_PARTIAL_RECOVERY_RULE=MODIFY` 的 BRANCH_E，已批准）。
可测：final 路径缺席 ＋ `.partial` 在场 ＋ 分歧件在场。三者都是文件系统事实。
```

### C_BUILD_3 —— archive 尝试之后

```
门：archive_policy_a
断言：**不是「无 archive 尝试」**——尝试已经发生。断言是：
      (a) 本地 seal **不可变**：重算其 sha256 等于 seal 时记录的
          `local_seal_sha256`；
      (b) 无任何已归档字节被删除。
可测：重算比对。A1 的字段表里本就有 `local_seal_sha256` 与
      `local_seal_immutable` 两项——断言的对象是**已批准事件的既有字段**，
      不是为 R3 新造的。
```

**这三条互不蕴含。** 把它们写成一条通用规则正是 R2 出错的地方。

---

## 2. 条件 2 —— 冻结的转移矩阵

Sol High #1：R2 把门描述成「把生产异常分类进 F1/F2」，**而已批准状态机要求
post-seal 的普通 archive 失败发 A1、不是 F2**。

**根因（builder 复现后确认，比 Sol 的表述更具体）：这里有两个不相干的路由器，
R2 把它们混成了一个。**

### 路由器 A —— 门拒绝，由 P3 边界决定

`plan_failure_event(...)` 已实现且已批准。其 docstring 逐字：

> F1 vs F2 is decided by the P3 BOUNDARY, never by the stage name
> (§D.3.2 P3: `BOUNDARY=P3 是 pre-start / post-start 的唯一分界`).

```
has_p3 = False  ->  F1  （必须给 attempts_dir；consumption_statement="nothing consumed"）
has_p3 = True   ->  F2  （必须给 residue_path；residue_preserved="YES"）
```

**阶段名不参与判断。** A_PRECHECK／B_DERIVE／C_BUILD 三个阶段名在这条路由里
没有任何作用——这一点 R2 写反了。

### 路由器 B —— seal 之后的结局，与门无关

`decide_after_seal(local_seal_ok, archive_report)` ＋
`classify_archive_report(report)`，两者均已实现且已批准
（`ND1_ARCHIVE_FAILURE_POLICY=A`）：

| local_seal_ok | archive 状态 | 结局 | 依据 |
|---|---|---|---|
| False | 任意 | 抛 `local_seal_failed`「no P4 and no A1: nothing was sealed」→ 转路由器 A 的 post-P3 分支 → **F2** | `decide_after_seal` |
| True | `archive_ok` | **P4** | `decide_after_seal` |
| True | `archive_failed`，成因可分类 | **A1** ＋ `archive_code` ∈ {`inventory_unavailable`, `file_unreadable`, `file_digest_mismatch`, `set_equality_refused`, `set_equality_unreached`} | `classify_archive_report` |
| True | `archive_failed`，成因**不可分类** | **INDETERMINATE** —— 抛 `ARCHIVE_UNCLASSIFIED_CODE` | `classify_archive_report` 末行 |
| True | 状态既非 ok 也非 failed | **INDETERMINATE** —— 抛 `archive_status_unknown` | `classify_archive_report` |

**INDETERMINATE 的处置（Sol 08-25 第 3 条）：不确定的半转移，走 Aaron。**
不追加任何事件、不自动归入 F2、不重试，停机上交。

### 由此暴露的一个真实缺陷 —— R3 必须修的

**`archive_policy_a` 现在是一道门**（在 `GATE_TABLE["C_BUILD"]` 的已批准闭合枚举
里）。若它将来作为门拒绝，路由器 A 会因 `has_p3=True` 发 **F2**——**而已批准政策
要求这一格发 A1**。

**修法（与 §3 的 checkpoint 分派同形：枚举不动，另立一层）**：

```
ROUTER_OF: gate -> {A, B}
  archive_policy_a -> B      # 其拒绝由 decide_after_seal 路由，不进 plan_failure_event
  其余 22 道门     -> A
```

`GATE_TABLE` 成员不变（那是已批准的封闭枚举，改它是另一件事，不搭这次的车）。
**变异证红要求**：把 `archive_policy_a` 的 `ROUTER_OF` 改成 A，必须有测试变红并
指出「archive 失败被路由成 F2，与 `ND1_ARCHIVE_FAILURE_POLICY=A` 相抵」。

---

## 3. checkpoint 分派（承自 R2，未变）

```
A_PRECHECK                        13 门   —— 不变
B_DERIVE                           5 门   —— 不变
C_BUILD_1  首次写入之前             row_schema_blind
                                   day_set_exact
                                   rows_digest_recompute
C_BUILD_2  staging 期间             seal_staging_partial
C_BUILD_3  archive report 存在之后   archive_policy_a
```

`CHECKPOINT_OF: gate -> checkpoint` 另立一层，`GATE_TABLE` 成员不动。

**门是分类器，不是校验器**（Sol 08-25 第 1 条）：门调用生产侧校验、捕获其异常、
映射到 F1/F2 词汇里的具名 stage/gate。门内不得出现第二份不变量实现。这与既有
意图一致——`_g_row_schema_blind` 现有注释自己就写着「The blind guarantee is
enforced row-by-row by `day_strata_supplement._validate_row`; this gate exists so
the failure has a NAMED stage/gate in the F1/F2 vocabulary」。

---

## 4. 条件 4 —— 钉死 structural-only 调用图

Sol High #3：「复用生产侧 S0 universe/data assembly 路径」可以被合理读成复用
`RealChain._ensure`，而它 import 并调用 `build_s0_dataset`，后者对每一天调
`compute_day`，`compute_day` 调 `labels_mod.d_open_from_ret_open30` —— **算标签**。
那越过 supplement 的 structural-only 边界。

**逐字节钉死的允许调用图**（builder 已逐条打开确认存在与签名）：

```
itsf.data.dbn_loader : DevelopmentSignalLoader.load_real
                              -> bars_by_date
itsf.s0.context      : build_universe(bars_by_date, schedule, events,
                                      roll_intervals)          # context.py:919
                              -> S0Universe
itsf.s0.dataset      : build_vol20_regime_mapping_from_universe(universe, method)
                                                               # dataset.py:1155
                              -> vol_stratum ∈ ("T1","T2","T3","vol_na")
itsf.s0.dataset      : build_event_stratum_map(flag_by_date, event_na_mapping)
                                                               # dataset.py:1227
                              -> event_stratum ∈ ("CPI","FOMC","NFP",
                                                  "NA_multi_event","none")
=> 行 = ROW_FIELDS = ("trade_date", "year", "vol_stratum", "event_stratum")
```

`build_vol20_regime_mapping_from_universe` 的 docstring 自陈
「**Nothing here reads bars**: the closes come from the summaries the universe
already computed」——这是该路径 structural-only 的自带证据。

**明令禁止（AST 层面钉住，不是注释约定）**：

```
itsf.s0.dataset.build_s0_dataset        # dataset.py:484 —— 对每天调 compute_day
itsf.s0.dataset.compute_day             # dataset.py:215 —— 调 labels_mod
itsf.s0.dataset.iter_day_contexts
itsf.s0.labels.*                        # 任何标签
Oracle 构造 · study 构造
scripts.s0_real_run.RealChain._ensure   # s0_real_run.py:2650 —— 正是 High #3 的路径
```

**词表一致性（builder 实测）**：`s0.dataset.EVENT_STRATA` 与
`mc.day_strata_supplement.EVENT_STRATA` 顺序不同但**集合相等**（五项逐一比对
通过）。R3 要求实现按**集合**比对，不得按顺序比对——按顺序会假红。

**生产者自身不得携带任何分层逻辑**，且对 `authority.expected_day_set` 做**逐日
精确相等**对拍（不是覆盖，不是包含）。

---

## 5. 条件 5 —— bundle_precheck 证据的格式、落点、时机、失败处置

Sol 的 Medium：R2 要求这张表落盘成运行证据，却没定序列化、落点、封存覆盖，
以及 P3 前后落盘失败怎么办。四项逐条定死：

**序列化**：`itsf.mc.atoms.canonical_json`（`atoms.py:184`）——
`sort_keys=True, ensure_ascii=True, separators=(",",":"), allow_nan=False`。

> **必须点名这一份。** 本仓现存三份同体的 `canonical_json`：`atoms.py:184`、
> `cold_reducer.py:69`、`day_strata_supplement.py:149`。不点名就等于默许第四份。
> 三份并存本身是既有的第二份实现隐患，**R3 不修它**（超出本设计范围），只在此
> 具名，以便它不因 N09 而扩大。

**落点**：本次运行的证据目录下具名文件，且**进封存清单（inventory）覆盖**——
不进清单的证据在 seal 后不可验，等于没有。

**时机**：在 **P3 追加之前**计算并落盘，且精确绑定到 `prepared.file_sha256`。
绑定发生在 P3 之前这一点必须**可证**，不是声明。

**落盘失败的处置**：

```
P3 之前落盘失败      -> 普通 pre-start 失败 -> 路由器 A -> F1
P3 之后落盘失败      -> INDETERMINATE，走 Aaron（同 §2 末）
                        不追加 F2、不重试、停机上交
```

理由与 Sol 08-25 第 3 条同源：P3 之后的半状态是**不确定的半转移**，把它自动
归入普通 F2 会让一个未知状态被记成一个已知状态。

---

## 6. 条件 3 —— **本设计取第二分支：默认拒绝骨架**

Sol 最小解阻条件 3 给了两条路：取得 Aaron 的 P3／failure-writer 与目录授权裁定，
**或**把授权的 build 明确限定为一个永远拒绝的骨架。**R3 取后者。**

原因是磁盘上的字节，不是判断：`ops/ND1_PROFILE_RATIFICATION.md` §4 的效力边界
逐条为 `NO` ——

```
SUPPLEMENT_EXECUTION_AUTHORIZED=NO      REAL_DATA_READ_AUTHORIZED=NO
DIRECTORY_CREATION_AUTHORIZED=NO        WRITE_PROBE_AUTHORIZED=NO
REGISTRY_EVENT_APPEND_AUTHORIZED=NO     EXPOSURE_EVENT_APPEND_AUTHORIZED=NO
MC_EXECUTION_AUTHORIZED=NO              STRATEGY_BUILD_AUTHORIZED=NO
```

叠加 D-3 的 HOLD 条件 3：**生产代码不得获得任何 registry 写能力**，直至 fresh Sol
PASS ＋ Aaron 授权。D-3 现在是 HOLD，五项 `UNRESOLVED_FOR_AARON` 全在 Aaron 手里。

### 骨架的确切含义

**可建**：§1–§5 的全部结构——checkpoint 分派层、`ROUTER_OF` 层、两个路由器的
矩阵、structural-only 调用图的 AST 守卫、precheck 证据的格式与时机规则。

**不可建**：任何能让上述结构真的产出行、真的封存、真的归档、**真的追加 P3** 的
能力。骨架在每一个这样的出口处**确定性拒绝**，并且拒绝本身是被变异证红守住的。

**判据（可机械检查，不靠自陈）**：

```
1. 生产包内不存在任何向 registry 写入的调用路径（AST 可达性，非 grep）。
2. 两个 supplements 子树仍不存在；无任何代码创建目录。
3. 把任一拒绝改成放行，必须有测试变红，且报错点名被越过的授权字段。
4. `SUPPLEMENT_EXECUTION_AUTHORIZED=NO` 与 `DIRECTORY_CREATION_AUTHORIZED=NO`
   为真时，整条路径确定性拒绝——这是判据 3 的正向形。
```

判据 3 是关键的一条：**骨架的价值不在于它今天拒绝，而在于它不能被悄悄改成不拒绝。**

---

## 7. 越过骨架需要什么 —— 这一节全部归 Aaron，builder 不代填

```
1. P3 与失败事件的写者是谁（D-3 的核心；已批准 actor 表写 runner，
   而全局边界 4 写「只有主代理写 registry」，两者相抵）
2. 目录创建授权：来源、actor、精确文本、commit/path 绑定、有效期
   （Sol High #2 点名 R2 的「token」四项全缺）
3. D-3 的五项 UNRESOLVED_FOR_AARON（见 ops/RULING_SOL_D3_HOLD_2026-08-26.md）
4. N09 的 P2（OD-2026-08-25-1 未被后续任何决定触及）
```

**这四项与本设计的关系是单向的**：它们未定，§1–§5 照样成立、照样可建、照样可测；
它们定了，骨架的拒绝出口才逐个打开。**反过来不成立**——没有任何一项可以由
「设计已经写好了」推出来。

---

## 8. 本设计不做什么

不读真实 Development 数据；不创建任何目录（两个 `supplements\` 子树仍不存在）；
不追加 registry 行；不动 exposure；不填 P2 占位符；不改样本／标签／NA 政策／
成本／Primary／Oracle／feasibility／运行定义；不释放任何 gate。

**R3 是设计，不是实现。** `STATUS=NOTHING_IMPLEMENTED` 在写下时逐字为真。

---

## 9. 2026-08-27 追加 —— §6 的四条判据现在有机制了

**先把话说准，免得这一节被读成「骨架建好了」**：

```
已有机制的   §6 的四条判据（它们自称「机械可检查，不靠自陈」，此前没有机制）
             §1 的 C_BUILD_1 零副作用断言（三个 checkpoint 里唯一今天可测的那个）
             §4 的 structural-only 调用图（AST 钉死，含禁用名的存在性自检）
             §2／§3 的 CHECKPOINT_OF／ROUTER_OF 两层（当日早些时候建，另有 11 项测试）
             §4 末尾的词表判据（EVENT_STRATA 按集合比对，并钉住两边顺序确实不同 ——
             否则那条「不得按顺序比」的告诫会在有人「简化」时悄悄失去依据）

仍未建的     骨架在各出口处的其余结构。**本次加的是守卫，不是骨架本身。**
```

守卫：`tests/test_n09_scaffold_criteria.py`（17 项）。

**变异证据（六条，含一次我自己打错的变异）**：

```
在边界模块里加一个写            -> 红
边界暴露一个名字像写的函数       -> 红
加第二个目录创建者              -> 红
让 runner 触到禁用名            -> 红
拒绝消息不再点名授权字段         -> 红   ← 判据 3，R3 称为承重的那条
把拒绝改成放行                  -> 红
```

**第五条第一次跑出来是绿的**，因为我的变异改的是第 16 行 docstring 里那次出现，
而消息插值的是第 78 行的常量。**是变异打错了，不是守卫弱。** 记下来，
因为「变异证绿」若不追究，会被当成守卫失效而去改守卫 —— 那才是真正的损失。

### 判据 1 的证明是两半，两半都机械

```
(a) 只有一个模块拼得出受治路径  —— test_registry_path_single_construction.py
                                （不变量 5，dec-registry-migration-2026-08-27）
(b) 那个模块不执行任何写，也不暴露任何名字像写的函数 —— 本次新增
```

合起来才闭合：**写不到一个它拼不出的路径。** 任何一半单独都不够 ——
所以 (a) 是被断言存在的，不是被记住的：它若被删，(b) 仍会全绿而什么都没证明。

### 判据 3 实测到的一件事，如实记录

三个生产入口点名的**不是同一类词**：

```
run_supplement_production  -> SUPPLEMENT_EXECUTION_AUTHORIZED（ND1 效力边界字段）
run_real_mc                -> MC_RUN_AUTHORIZED
prepare_real_mc_input      -> MC_RUN_AUTHORIZED（registry 语法词）
```

两者都为真，且是两个不同的事实：一个说 Aaron 未授权该效果，另一个说 registry
语法里没有这个词。**按实测钉住。** MC 那两个是否也该点名 `MC_EXECUTION_AUTHORIZED`
属于改门语义，裁定明确不归 builder。

**§7 的四项仍全部在 Aaron 手里，本节不触及其中任何一项。**
