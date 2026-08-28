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

---

## 10. 2026-08-27 追加 —— §5 有机制了，且实测推翻了 §5 自己的三处事实陈述

守卫：`tests/test_n09_precheck_evidence_rules.py`（22 项，五条变异全红）。
合同层新增 `PRECHECK_EVIDENCE_*` 四条常量与 `decide_evidence_write_failure`。

### 10.1 「三份同体的 canonical_json」—— **不同体**

§5 写「本仓现存三份同体的 `canonical_json`」。实测：

```
atoms.canonical_json         sort_keys ensure_ascii separators  allow_nan=False
cold_reducer._canonical      sort_keys ensure_ascii separators  allow_nan=False
day_strata.canonical_json    sort_keys ensure_ascii separators  ← 没有 allow_nan
```

**后果是具体的**：`day_strata.canonical_json` 对 `NaN`／`Infinity`／`-Infinity`
返回 `{"x":NaN}` 这类**不是合法 JSON**的字符串，另两份抛 `ValueError`。
而它正是 `canonical_rows_digest`（supplement 行摘要）用的那一份 ——
摘要可能取在非 JSON 的字节上，而冷读者用另两份复算时会**抛异常而非给出不同答案**。

**这个发现是撞出来的，值得记下过程**：我先写的是「三份逐字节一致」那条测试，
**它通过了** —— 因为用例里没有 NaN。**以错误的理由变绿**，正是这个仓平时在别处
猎捕的那类缺陷，出现在一条为猎捕它而写的测试里。

**未修，理由有两条**：§5 自己写明「R3 不修它（超出本设计范围）」；且摘要函数不是
builder 可凭自己判断更改的东西 —— 已封存的每一个摘要都是用现在这一份取的。

**已做的是把它钉住**：supplement 行的四个字段全为字符串或整数年份，float 进不来，
所以 NaN 到不了。**加一个字段就红** —— 那正是这个分歧不再潜伏的时刻。

#### 10.1bis 修正，2026-08-28 —— Aaron 作废了 §5 的范围声明

Aaron 原话：

> **R3 §5 那句范围声明作废，改**

**作废的是范围声明，不是发现。** §5 把重复实现排除在自己范围外，理由写的是
「三份**同体**」；三份并不同体，所以那句排除的**前提是假的**。前提没了，
排除的依据也没了。

**改动**：`day_strata_supplement.canonical_json` 加 `allow_nan=False`。
三份现在一致拒绝 `NaN`／`Infinity`／`-Infinity`。

**改之前先测了两件，正是它们让这次改动变便宜**：

```
已封存的 supplement   零   —— registry 无 P4 事件、磁盘无 supplement 字节、无子树
                           因此没有任何既有摘要会因此无法复算
可达输入的行为变化     零   —— 行的四个字段没有 float，NaN 本就到不了
```

**守卫也跟着换了形态**：原来断言「它们分歧」，现在断言「它们一致」，
并新增一条断言**属性而非实例** —— 任何用 MC canonical 形式而缺 `allow_nan=False`
的实现都红。**只钉那三份的话，第四份只要不是它们中的一份就能绕过去。**

变异证红两条：撤销本次修复 -> 红；另加一份缺 `allow_nan` 的新实现 -> 红。

### 10.2 名字：`cold_reducer.canonical_json` 实为 `_canonical`

§5 把第三份写成 `cold_reducer.py:69` 的 `canonical_json`，那里的函数叫 `_canonical`。
行号对，名字不对。**实质（三份并存）为真。** 记下来，免得后来者 grep
`canonical_json` 只找到两份而以为 §5 把数目搞错了。

**守卫因此按参数签名找，不按名字找** —— 一份换个名字加进来的第四份，
名字基的扫描会走过去。

### 10.3 数目：按签名找是**五份**，但那是两套合同

`s0/runinfra.py` 另有两处同签名实现（`canonicalize_manifest_record`、
`append_manifest_record`），**它们用 `ensure_ascii=False`** —— 与 MC 那三份相反。

读它的 docstring 与冻结的 per-record schema：manifest 是 UTF-8 工件，
`ensure_ascii=False` 是刻意的。**那是另一套 canonical 形式，不是第四份拷贝。**

守卫因此**按合同分开计数**：MC 形式恰三份，manifest 形式恰两份。
我的第一版把两套混成一套，会得到一条永远红的测试，
**更糟的是会给出「把两套本该不同的合同统一起来」的论据**。

### 10.4 §5 的失败处置：路由器 A 现在会给 F2

```
实测   plan_failure_event(..., has_p3=True)  ->  F2
§5     P3 之后落盘失败 -> INDETERMINATE，不追加 F2、不重试、停机上交
```

路由器 A 对**门失败**判 F2 是对的；对**证据落盘失败**不是。
与 §2 的 `archive_policy_a` 同形：**P3 之后是不确定的半转移，
把它自动归入 F2 会让一个未知状态被记成一个已知状态。**

因此 `decide_evidence_write_failure` 是一条独立的失败类决策，
**层叠在两个路由器旁边，不改任何一个**。今天没有任何东西路由到它 ——
骨架在证据被写之前就拒绝了 —— **而这正是要点：规则先于能力落地，
能力就不能在没有规则的情况下到来。**

---

## 11. 2026-08-27 追加 —— §1 的另两条 checkpoint 有机制了，并测出 §1 自己的一个缺口

守卫：`tests/test_n09_checkpoint_assertions.py`（19 项，四条变异全红）。
至此 §1–§6 全部有机制。

### 11.1 缺口：C_BUILD_2 断言的状态，调用者观测不到

§1 给 C_BUILD_2 的断言是「FINAL 缺席 ＋ `.partial` 在场 ＋ 分歧件在场」，
并注明「三者都是文件系统事实」。**实测**：

```
resolve_partial 不是「staged 之后停在那里」——
它 stage、verify、promote 在**同一次调用内**完成。
调用返回后：FINAL 在场，`.partial` 已不存在。
```

因此「FINAL 缺席 ＋ `.partial` 在场」这个状态**只存在于 `resolve_partial` 内部**，
而它**不提供任何让门在那一刻运行的钩子**。

**今天是潜伏的，不是活的**：`seal_staging_partial` 是默认拒绝的桩，
什么都不观测。但若将来把它接上，**接到哪里**这个问题 §1 没有回答 ——
接在调用之后，断言必然为假。

**未替它选一个接法**：那是「实现者自行挑一种读法」，而且改的是一道门的运行时机。
记录在此，留给下一轮复审或 Aaron。

### 11.2 因此断言落在机制上，而不是落在门上

门是桩，观测不到东西；能今天钉住的是**门将来要分类的那个机制**。已钉：

```
promote 是原子的，调用后不留 .partial
相同字节 -> already_sealed，不销毁任何东西
不同字节盖在已封存件上 -> **拒绝**（不是改名）——「已封存的 supplement 永不覆写」
陈旧 .partial（崩溃残留）-> BRANCH_C 改名移开＋允许重试，字节逐字保留，
                            分歧件名按 BRANCH_E 的模板携带 incident_id
incident_id 不合法 -> 在触碰任何字节之前拒绝
resolve_partial 的源码里没有 unlink/rmtree/remove（SILENT_DELETE_FORBIDDEN 的代码层形式）
```

**其中「不同字节 -> 拒绝而非改名」是我原本想错的一条**：我以为它会走分歧改名，
实测是 `supplement_seal_conflict`。

#### 11.2bis 标签更正，2026-08-28 —— 决裁席指出，builder 核准

决裁席发现 R3 与 runner 的 docstring 对 BRANCH_C／E 的归属互相矛盾，
并因未读批准原文而让渡不裁。**批准原文就逐字引在 `supplement_contract.py:153`**，
builder 据此核：

```
批准原文  ND1_PARTIAL_MODIFY_TEXT =
          BRANCH_E_RENAME_TO_.partial.divergent.<incident_id> ;
          BRANCH_C_RENAME_THEN_ALLOW_RETRY

runner:905  陈旧 .partial 字节不同 -> _preserve -> retry_permitted
            = 改名后允许重试 = **BRANCH_C**（runner 标注为 C，对）
runner:913  写后复读不符         -> _preserve -> raise（拒绝，无重试）
            = 改名到那个名字     = **BRANCH_E**（runner 标注为 E，对）
```

**两个分支都改名，都用同一个模板产生的名字。** 区别在后半句：
**E 规定改名的目标名，C 规定改名之后允许重试。**

结论逐条：

```
R3 §1(c)   把「分歧件的名字」归给 BRANCH_E   —— **对**，不改
§11.2      把陈旧 .partial 的**动作**归给 E  —— **错**，是 C，已改
测试注释    同一处错，两条已改
runner     两处标注都对
```

**决裁席说「行为本身两处钉得都对，唯标签归属互相矛盾」——精确。**
它让渡是因为没读批准原文；那段原文在本仓可读，builder 读了，所以这一条不必上交。

### 11.3 C_BUILD_3：断言落在已批准事件的既有字段上

A1 的 `required_fields` 确实已含 `local_seal_sha256` 与 `local_seal_immutable`
（实测）。**断言的是重算与记录值相等，不是读那个 flag** ——
一个写着「immutable」的标志本身什么也不证明，**读它而不重算，正是一句假声明得以存活的方式**。

### 11.4 「三条互不蕴含」也被钉住了

§1 结尾那句是这套断言最容易被后人推平的地方 ——
有人会注意到「它们都在查副作用」而把它们合回一条通用规则，也就是 R2 被 HOLD 的那条。

钉的形式是**可观测的对立**：C_BUILD_1 断言输出集为空，C_BUILD_3 断言封存件在场且可重算。
**一个目录不可能同时满足两者**，所以没有单一规则能覆盖两者 ——
把 R2 的错误表述成一个事实，而不是一条教训。

C_BUILD_2 因 11.1 的缺口不能用运行时对立来钉，改为按已批准词表钉它的**主体不同**
（`.partial` 残留，A1 的字段表里没有这个词）。

---

## 12. C_BUILD_2 的新措辞 —— 起草稿（裁定 B，待 fresh Sol 复审 ＋ Aaron 批）

```
STATUS=DRAFT —— 未生效。生效条件见 dec-c-build-2-hook-2026-08-28 的 CONDITIONS：
       经 fresh Sol 复审、Aaron 批准后方生效。
FORM=追加／超越，§1 的 C_BUILD_2 原文一字不删（沿 §10.1bis 成例）
MECHANISM_CHANGES=零。GATE_TABLE 与 CHECKPOINT_OF 零改动。
```

### 12.0 先答裁定的 FALSIFIER —— builder 已核，未触发

裁定写：若已批准的 ND1/N-D2 原文**以批准值**规定该门必须「在 staging 期间」运行，
则 B 触及批准实质、裁定作废。**核验结果**：

```
搜索面   ops/*.md（非隔离）＋ src/itsf/mc/*.py
命中     「staging 期间」只出现在 R2、R3 与裁定记录自身 —— 全部是 builder 侧
         的设计文本或对它的转述，无一是批准值
相关批准值  ND1_PARTIAL_RECOVERY_RULE=MODIFY
            ND1_PARTIAL_MODIFY_TEXT=BRANCH_E_… ; BRANCH_C_…
            SILENT_DELETE_FORBIDDEN=YES
            —— 三者都规定「分歧字节怎么处置」，无一规定门何时运行
```

**结论：门的运行时机从来不是批准值，是 R2 自己写下的一句设计措辞。** FALSIFIER 未触发。

### 12.1 新措辞

```
C_BUILD_2 —— 调用边界（B 重述）

门的位置与职能（判据 5 要求明写，不留开放读法）
    seal_staging_partial 在 resolve_partial 的**调用边界**上运行：
    对该次调用的**结局或异常**做分类。
    门不观测调用内部，不实现第二份不变量（承 §3 的门学说）。

断言（调用返回或抛出之后，逐类不合并）

  (a) 未经校验的 FINAL 不存在
      防的违规类：一份没被复读校验过的 FINAL 被当作已封存
      检出途径：**调用后的文件系统事实** —— FINAL 若在场，其字节 == intended
      依据：机制在 os.replace 之后自己复读一次并在不符时抛
            supplement_post_promotion_verify；门分类的是这个结局

  (b) 没有任何 .partial 字节被静默销毁
      防的违规类：残留被删而不是被移开
      检出途径：**被钉住的机制性质** —— resolve_partial 的 AST 里没有
            unlink / rmtree / remove；每一条移开路径都产出 preserved_as
      依据：SILENT_DELETE_FORBIDDEN=YES（已批准）

  (c) 若发生分歧改名，分歧件在场且名字携带 incident_id
      防的违规类：分歧发生而无可追溯的残留
      检出途径：**调用后的文件系统事实** —— 两条分歧结局各自留下
            <filename>.partial.divergent.<incident_id>：
              retry_permitted（branch C：改名后允许重试）
              supplement_partial_verify（branch E：改名后拒绝）
      依据：ND1_PARTIAL_MODIFY_TEXT 的 BRANCH_E 子句给出名字模板（已批准）
```

**(a)(c) 是调用后的文件系统事实，(b) 是被钉住的机制性质 —— 逐类标明，不合并**（判据 1）。

### 12.2 逐条对照五判据

```
(1) 覆盖保全     三个违规类逐条列出，各自标明检出途径是「调用后文件系统事实」
                 还是「被钉住的机制性质」，未合并。
                 **并补上了旧措辞漏掉的一半**：(c) 原只覆盖 branch C 那条结局，
                 实测 branch E 同样留下分歧件（见 12.3 的新测试）。
(2) 证伪保全     三条子句各配变异，清单见 12.3。
(3) 不得回并     主体仍是 .partial 纪律；C_BUILD_1（输出集为空）与
                 C_BUILD_3（封存件在场且可重算）的「互不蕴含」钉子不受影响 ——
                 新措辞不含任何可与那两条合并的通用形式。
(4) 锚定保全     (b) 由 SILENT_DELETE_FORBIDDEN 导出，(c) 由
                 DIVERGENT_PARTIAL_TEMPLATE 导出，既有 premise 测试
                 （test_the_ratified_values_this_asserts_against_are_still_in_force）
                 在批准值一变时即红。
(5) 缺口出清     门的位置与职能写在措辞第一段：调用边界、分类结局或异常。
                 「接到哪里」不再开放。
```

### 12.3 变异证红清单（判据 2）

```
(a) 删掉 os.replace 之后的复读校验            -> 红（**本次新增测试**）
(b) 在 resolve_partial 里加一处 unlink        -> 红（既有测试）
(b) 让 _preserve 不返回 preserved_as          -> 红
(c) 令 branch C 不改名                        -> 红（既有测试）
(c) 令 branch E 删除而不移开                  -> 红（**本次新增测试**）
锚定 撤销 SILENT_DELETE_FORBIDDEN             -> 红（既有 premise 测试）
```

**这份清单第一次跑的时候把草稿自己驳回了。** (a) 那条最初是**绿**的 ——
删掉 promote 后的复读校验，套件里没有任何东西发现，因为顺利路径上 FINAL 永远读回
正确字节，删掉检查对既有测试不可见。

**一条没有变异证据的子句不满足裁定的判据 (2)。** 补了一条测试：在 `os.replace`
之后令 FINAL 读出不同字节（正是被污染或竞态的文件系统会做的事），机制必须拒绝
而不是报告封存。补完才红。

**(c) 的另一半也是这样补上的**：旧措辞只覆盖 branch C 那条分歧结局，
实测 branch E（写后复读不符 -> 改名 -> 拒绝）同样留下分歧件，此前无测试。

### 12.4 本稿不做的

不改机制一个字节；不改 `GATE_TABLE`／`CHECKPOINT_OF`；不删 §1 的原文；
**不主张本稿已生效** —— 它要过 fresh Sol 再过 Aaron。
`test_c_build_2s_state_is_not_observable_to_a_caller` 按 CONDITIONS 保留为陈旧化绊线：
若将来 `.partial` 真的存活过调用，它会红，而那正是本稿前提失效的时刻。

### 12.5 起草稿自纠 —— (a) 声称的违规类比它的检出途径宽

**这一条是在给 fresh Sol 写 prompt 的过程中量出来的**，写的正是那句
「请判：一个未经校验的 FINAL 若字节恰好正确，(a) 还检得出来吗」。
写完停下来量了，答案是**检不出来**，于是它不再是问题而是缺陷。

#### 实测

```python
out/"f.json" 由本机制之外的东西写出（手抄／备份还原／没有 promote-后复读的旧版本）
resolve_partial(...) -> PartialAction(action='already_sealed', detail='byte-identical')
(a) 的检出途径「FINAL 在场则字节 == intended」  -> 通过
本次调用复读校验过它吗                          -> 没有。该分支只做了一次相等比较
```

`resolve_partial` 开头：

```python
if final.exists():
    existing = final.read_bytes()
    if existing == intended:
        return PartialAction("already_sealed", detail="byte-identical")
```

**任何**字节相符的既存 FINAL 都走这里，与它由什么产出无关。

#### 因此 §12.1 (a) 的措辞不满足判据 (1)

原稿写：

```
(a) 未经校验的 FINAL 不存在
    防的违规类：一份没被复读校验过的 FINAL 被当作已封存
    检出途径：调用后的文件系统事实 —— FINAL 若在场，其字节 == intended
```

**声称的类严格宽于检出途径能看见的集合。** 这比诚实划界更糟：
读措辞的人会以为宽的那个类被覆盖了。

**这是今天第三次同一形态**（另两次在姊妹仓，复审席已为其编号至第五实例）：
**我守的边界一直比我声称的属性窄。**

#### 更正后的 (a)

```
(a) 字节与 intended 不符的 FINAL 不会被当作已封存
    防的违规类：一份字节与 intended 不符的 FINAL 被当作已封存
    检出途径：调用后的文件系统事实 —— FINAL 若在场，其字节 == intended
              （既存不符 -> supplement_seal_conflict 拒绝；
                本次 promote -> promote 后复读无条件运行）
    依据：机制在 os.replace 之后自己复读一次并在不符时抛
          supplement_post_promotion_verify；门分类的是这个结局
```

#### 明写的残余 —— 不声称已闭合

```
既存 FINAL 若字节相符，本机制凭字节接受，不问出处。
关闭它需要一份机制现在没有的 provenance 记录，而造一份是设计变更 ——
裁定 B 的 CONDITIONS 明令本稿「机制零改动」，因此本稿不得关闭它。
```

钉在 `tests/test_c_build_2_wording_coverage.py`，**四条测量全绿**：
残余存在（`already_sealed`）· 检出途径对它通过 · 字节不符仍拒 ·
本次 promote 的那一半确实被无条件校验。

**这条残余是否需要处理，归 Aaron**，不归本稿、也不归复审席。

### 12.6 起草稿自纠之二 —— (b) 同病，且更硬

§12.5 更正 (a) 之后我按同一把尺子量了 (b)。**同一个病。**

(b) 声称的违规类是「没有任何 `.partial` 字节被静默销毁」，
检出途径是「`resolve_partial` 的 AST 里没有 unlink / rmtree / remove」。
**那把尺子只量一个函数体。** 实测三种写法：

```
局部别名        rm = os.remove; rm(partial)      -> 旧检查看不见
Path 方法经变量  p = partial; p.unlink()          -> 看得见（调用名仍是 unlink）
被调函数里删     _preserve(...) 内部删            -> 旧检查看不见
```

**第三条要命**：`_preserve` 在**两条分歧分支上都被调用**
（branch C 改名后允许重试、branch E 改名后拒绝）。
把一句删除搬进 `_preserve`，旧检查**完整通过**。

#### 处置 —— 只改测试，机制零改动（CONDITIONS 允许）

`test_nothing_is_ever_unlinked_by_the_staging_path` 的扫描面从
「`resolve_partial` 一个函数体」放宽为「`resolve_partial` ＋ 它经直接调用
可达的每个模块级函数」，并新增两条：

```
test_no_destructive_call_is_hidden_behind_a_local_alias   别名绑定
test_the_walk_actually_reaches_the_helpers                走到了 _preserve（否则前两条空转）
test_the_scan_declares_what_it_cannot_see                 明写它看不见什么
```

**变异证红（实测）**：

```
删移进 _preserve         -> 红（旧检查：绿）
局部别名 rm = os.remove  -> 红（旧检查：绿）
还原                     -> 24 绿
```

`test_the_walk_actually_reaches_the_helpers` 是为防**这条修复自己空转**而加的：
一个什么都没走到的传递扫描，会让上面每一条断言都自动通过。

#### 明写残余 —— 这把尺子仍看不见什么

```
方法体内的删除 · 被导入模块内部的删除 · 经由值到达的删除
（传进来的可调用对象、handler 字典）
```

**不声称穷尽。** 由 `test_the_scan_declares_what_it_cannot_see` 钉住 ——
它断言扫描没有下沉到导入模块，所以哪天真下沉了，这条边界说明会红而不是变成陈述性谎言。

#### 因此 §12.1 的 (b) 更正为

```
(b) 没有任何 .partial 字节被静默销毁
    防的违规类：残留被删而不是被移开
    检出途径：被钉住的机制性质 —— resolve_partial 及其经直接调用可达的
              每个模块级函数（含 _preserve），其 AST 中无删除调用，
              且无删除调用被绑到局部名；每一条移开路径都产出 preserved_as
    看不见的：方法体内、被导入模块内、经由值到达的删除（明写，不声称穷尽）
    依据：SILENT_DELETE_FORBIDDEN=YES（已批准）
```

### 12.7 起草稿自纠之三 —— (c) 的枚举短了一半

按同一把尺子量 (c)。它的检出途径写「**两条**分歧结局各自留下
`<filename>.partial.divergent.<incident_id>`」。**实测有四条：**

```
branch C                  retry_permitted            产出具名分歧件
branch E                  supplement_partial_verify  产出具名分歧件
divergent_partial_exists  拒绝                       残留以原名 .partial 留在原地
incident_id_malformed     拒绝                       残留以原名 .partial 留在原地
```

后两条是 `_preserve` 在改名**之前**的两道拒绝：
分歧件同名已存在（不覆盖前一次事故的证据）、`incident_id` 不匹配
`INCIDENT_RE = ^INC-[0-9a-f]{12}\Z`。

#### (c) 声称的类仍成立，但路线写短了

「分歧发生而无可追溯的残留」这个**类**在四条结局上都成立 ——
后两条把字节以原名留在原地，可追溯。**但路线只枚举了两条**，
按路线逐条核对现实的读者会发现它短了一半。

**这是本文档内第三次同一形态**（§12.5 的 (a)、§12.6 的 (b)）。
三次都不是设计时想到的，都是拿尺子逐条量出来的。

#### 更正后的 (c)

```
(c) 分歧发生时，字节不丢失且残留可追溯
    防的违规类：分歧发生而无可追溯的残留
    检出途径：调用后的文件系统事实，四条分歧结局逐条：
      branch C  retry_permitted           -> <filename>.partial.divergent.<incident_id>
      branch E  supplement_partial_verify -> <filename>.partial.divergent.<incident_id>
      divergent_partial_exists            -> 残留以原名 .partial 在场，
                                             且前一次事故的分歧件字节不变
      incident_id_malformed               -> 残留以原名 .partial 在场
    依据：ND1_PARTIAL_MODIFY_TEXT 的 BRANCH_E 子句给出名字模板（已批准）；
          SILENT_DELETE_FORBIDDEN=YES 覆盖后两条
```

四条各自钉在 `tests/test_c_build_2_wording_coverage.py`，
含一条跨四结局的类断言 `test_no_divergence_outcome_destroys_bytes`
（防前四条各自成立而类本身无人守）。

---

### 12.8 三次自纠的共同形态 —— 写给复审席，也写给我自己

```
(a)  声称的违规类  宽于  检出途径能看见的集合
(b)  声称的性质    宽于  扫描面（一个函数体 vs 可达调用图）
(c)  声称的路线    短于  实际结局数（两条 vs 四条）
```

**三条都是「我声称的」与「我实际守的」不一致，方向还不一样** ——
(a)(b) 是声称得太宽，(c) 是守得比声称的更全但写得太少。

**发现方式全都一样**：不是设计时想到的，是**逐条拿检出途径去跑现实**。
姊妹仓 `qros-runtime` 的同一形态今天被复审席编号到第五实例，
诊断是「**我守的边界一直比我声称的属性窄**」。本文档三条是同一个诊断的第三、四、五例。

**对复审席的意义**：判据 (1)「覆盖保全」不能靠读措辞判 ——
措辞读起来永远是自洽的。**只有拿路线去跑现实才判得出来。**

---

## 13. 措辞复审（`c-build-2-wording`）返回 HOLD —— 逐条处置

```
VERDICT=HOLD
WORDING_MAY_GO_TO_AARON=NO
TRANSPORT_PRECHECK=STOP
CONDITIONS_MET=1 met · 2 not met · 3 not met · 4 met · 5 met
```

### 13.1 HIGH ① 传输锚点不存在 —— 我的错，已订正

提示第 31 行声称「本提示的字节由 §1 表中它自己的 SHA-256 把守」，
**而 §1 表里没有本提示那一行。** 复审席实测本提示为
`13638` bytes、`caa00e4db927229c63c9b0837579a4efc0835f587f320d1319e24c1b4f7faa90`，
**与我复算一字不差** —— 但没有可比对的声明值，所以 STOP 成立。

发行字节实际记在 `ops/ARTIFACTS_UNDER_REVIEW.json` 的 `role: delivery` 条目里。
提示已改为指向那里。**登记册在提示之外，所以没有不动点问题** ——
这也正是 §12 那次 delivery-pin 修复的同一条道理，我修好了机制却在文字里指错了地方。

### 13.2 HIGH ③ falsifier —— 现已在**批准原文字节**上闭合

复审席判 `FALSIFIER_INDEPENDENTLY_CHECKED=NOT_CLOSED`，理由正确：
包里送的 `supplement_contract.py` 是**转录件**，拿转录件核原文等于自己核自己。

已重建批准原像并逐字核验：

```
commit   803d99162d0a018ae5a3b44273601d98d9439d50
file     ops/DECISION_PACKET_N00_AND_ND1.md
span     第 1309 行起 49 行 · 2527 bytes · LF · UTF-8
sha256   0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5
         == ops/ND1_PROFILE_RATIFICATION.md 的 APPROVED_PROFILE_SHA256
```

在这 49 行内检索 staging／期间／during／时机／when／运行时／中途／mid／checkpoint：
**命中 1 行，`RECOMMENDED_F1_GATE_NAME_ENUM=DEFER_TO_N04`，管的是门的命名不是时机。**

**结论：falsifier 未触发，且这个结论现在建立在批准字节上。**
钉在 `tests/test_the_ratified_preimage_is_reconstructible.py`，每轮从 git 重建。

#### 重建过程中额外量到一件，没人问

**`SILENT_DELETE_FORBIDDEN` 不在批准原像里。** 它是导出值 —— `MODIFY ⇒ YES` ——
导出表在同一文件第 1299 行，而原像从 1309 行开始，**表在原像之外**。

§12.1 (b) 写「依据：`SILENT_DELETE_FORBIDDEN=YES`（已批准）」。
**不精确**：它是**有已批准前件的导出值**（前件 `ND1_PARTIAL_RECOVERY_RULE=MODIFY`
确在原像内），这与「已批准值」是两回事，而差别恰好落在判据 (4) 锚定保全被主张的地方。

**(b) 的依据行更正为**：
`依据：SILENT_DELETE_FORBIDDEN=YES —— 由已批准的 ND1_PARTIAL_RECOVERY_RULE=MODIFY
按 DECISION_PACKET_N00_AND_ND1.md:1299 的导出表导出，非批准原像内的值`

### 13.3 MEDIUM ④ (b) 的守卫仍有两条语法绕法 —— 已复现，已修

```
ast.Assign 别名      rm = os.remove          现守卫 DETECTED=True
ast.AnnAssign 别名   rm: object = os.remove  现守卫 DETECTED=False   <- 绕过
write_bytes 截断     p.write_bytes(b"")      现守卫 DETECTED=False   <- 绕过
```

**修**：绑定形式扩到 `Assign / AnnAssign / AugAssign / NamedExpr`（加注解不是另一种行为）；
新增就地清空检测 —— `write_bytes / write_text / truncate` 带**字面空载荷**即拒
（`write_bytes` 本身合法且在 staging 路径上使用，所以只禁可证的空载荷）。
**`SILENT_DELETE_FORBIDDEN` 管的是字节，不是哪个系统调用。**

明写看不见的：非字面的空载荷（`write_bytes(payload)` 而 `payload` 运行时恰为空）、
计算出来的 `truncate(n)`。由 `test_the_truncation_scan_declares_what_it_cannot_see` 钉住。

变异证红（实测）：`AnnAssign` 绕法 → 1 红；`write_bytes(b"")` → 3 红；还原 → 26 绿。

### 13.4 LOW ⑤ 「跨四结局」证据映射错误 —— 已复现，已修

§12.7 声称 `test_no_divergence_outcome_destroys_bytes` 跨四结局，
**实测它只跑三条**（branch C、分歧件已存在、非法 incident_id），
docstring 的表里列了 branch E 而测试从未到达它。

branch E 的行为本身另有测试覆盖，所以**这是证据映射错误，不是实现缺陷** ——
但「声称四条而跑三条」正是 §12.8 那个形态，所以闭合而不是解释。
新增 `test_branch_e_writes_the_named_divergent_file`，并把类断言扩到真跑四条。

### 13.5 HIGH ② (a) 不满足覆盖保全 —— **不由 builder 处置，归 Aaron**

复审席的 `STRONGEST_OBJECTION`：

> 裁定要求旧违规类逐类继续可检出，但 §12.5 明确承认同字节、未知 provenance 的
> FINAL 仍会被接受。**缩窄违规类不能同时叫作「覆盖保全」。**

**我接受这个判断，并且不认为它能由起草稿解决。** 三条路各自需要 Aaron 的裁量：

```
(一) 放宽判据 (1)          承认「未经校验的 FINAL」在门学说下本就不可检出，
                          把它移出覆盖保全的要求
(二) 重开 B                承认 B 在现 CONDITIONS 下无法满足，回到 A 或第三条路
(三) 授权机制改动          加一份 provenance 记录 —— 但 CONDITIONS 明令机制零改动，
                          所以这需要 Aaron 先解除那条约束
```

**这三条我一条都不能自己选**：(一)(二) 改的是决裁席定的判据，
(三) 改的是 CONDITIONS 明令不动的东西。决裁包见
`ops/DECISION_PACKET_A_COVERAGE_CANNOT_BE_PRESERVED.md`。

**因此 §12 整体仍是 `STATUS=DRAFT`，且不再是「等复审」而是「等 Aaron 裁 (a)」。**

---

## 14. 撤回 §12.5 —— 那个缺陷是我造出来的

```
RETRACTION_OF=§12.5（并因此撤回 §13.5 与 ops/DECISION_PACKET_A_COVERAGE_CANNOT_BE_PRESERVED.md）
DATE=2026-08-29
FOUND_BY=builder，在 Aaron 批准「按推荐重开 B」之后、执行之前
STATUS=§12.5 文本按追加惯例保留不删；本节推翻其结论
```

### 14.1 触发

Aaron 采纳了我的推荐（重开 B）。**动手之前我回去核推荐的依据**，
也就是 §12.5 那句「`already_sealed` 分支……不问出处、**从未复读校验**」。

**「不问出处」是真的。「从未复读校验」是假的。**

```python
if final.exists():
    existing = final.read_bytes()          # <- 这就是复读
    if existing == intended:               # <- 这就是校验
        return PartialAction("already_sealed", ...)
```

它与 `os.replace` 之后那次 `final.read_bytes() != intended` 是**同一个检查**。

### 14.2 实测（计数 `Path.read_bytes` 落在 FINAL 名上的次数）

```
既存 FINAL 字节相符    already_sealed     读 FINAL 1 次，== intended
既存 FINAL 字节不符    拒绝               读 FINAL 1 次，!= intended
无 partial 正常封存    promote            读 FINAL 1 次，== intended
partial 相符续做封存   promote            读 FINAL 1 次，== intended
partial 不符           retry_permitted    读 0 次 —— 而它没有任何 FINAL 被当作已封存
```

**每一条「把 FINAL 当作已封存」的路径，都在同一次调用里把它读回并与 intended 比较过。**
唯一 0 次读的路径根本不封存 FINAL。

### 14.3 因此

**§12.1 (a) 声称防的违规类 —— 「一份没被复读校验过的 FINAL 被当作已封存」——
没有实例。原措辞覆盖它，判据 (1) 在 (a) 这一条上本来就成立。**

### 14.4 我实际做错的是什么

我把 (a) 的类**偷换**成了「出处未知的 FINAL 被接受」——**那是我自己引进的、更宽的类**——
然后宣布 (a) 覆盖不了「它自己的」类，再把 (a) 缩窄到我能检的范围。

```
量对的一半   already_sealed 确实不问出处
错掉的一半   由此推出「未经复读校验」—— 那是另一个类
```

**这与同一天那次 Class B 误分类是同一个形状**：机械可测的一半量对了，
另一半靠断言。而 §12.8 那个诊断（「声称的覆盖宽于实际的检出」）
我恰恰用在了一个声称与检出本来就吻合的地方 ——
**靠的是把声称悄悄换成我自己发明的更宽版本。**

### 14.5 复审席的 HIGH ② 不成立，但它没有判错

复审席的 `STRONGEST_OBJECTION` 写：

> 裁定要求旧违规类逐类继续可检出，但 §12.5 **明确承认**同字节、未知 provenance 的
> FINAL 仍会被接受。缩窄违规类不能同时叫作「覆盖保全」。

**这个推理在给定 §12.5 的前提下完全正确。** 前提是我供的，前提是错的。
**复审席不该为此被记一笔**——它读的是我写下的「明确承认」，那正是它该采信的东西。

**这一条要记住的是**：一个只读席位的判断质量，上限是我交给它的事实的质量。
我给了它一个我自己发明的缺陷，它就在那个缺陷上做了正确的推理。
**送审包里的每一句自陈，都是复审席无法独立复核的输入。**

### 14.6 处置

```
§12.1 (a)   恢复原措辞（下方 14.7），§12.5 的「更正后的 (a)」作废
§12.5       文本保留，结论撤回
§13.5       撤回（它是 §12.5 的下游）
决裁包       ops/DECISION_PACKET_A_COVERAGE_CANNOT_BE_PRESERVED.md -> WITHDRAWN
重开 B      **不执行** —— 依据已消失
出处未知     仍然为真，但它是一条**关于机制的独立事实**，不是 (a) 的缺陷。
            单独记在 14.8，不再挂在覆盖保全名下
```

### 14.7 (a) 恢复为

```
(a) 未经校验的 FINAL 不存在
    防的违规类：一份没被复读校验过的 FINAL 被当作已封存
    检出途径：调用后的文件系统事实 —— FINAL 若在场，其字节 == intended
    依据：两条封存路径各自复读一次并比对 intended ——
          既存件走 `existing == intended`，新封存走 promote 后的
          `final.read_bytes() != intended` -> supplement_post_promotion_verify。
          门分类的是这个结局。
    实测：tests/test_every_sealed_final_was_read_back.py，五条路径逐条计数
```

### 14.8 出处未知 —— 独立记录，不是 (a) 的缺陷

```
既存 FINAL 若字节与 intended 相符，机制凭字节接受，不问是谁写的。
这是真的，且无法由任何措辞关闭 —— 关闭它需要一份机制不保存的 provenance 记录。
它不属于 (a) 的违规类：(a) 管的是「字节有没有被确认」，不是「谁写的」。
是否需要处置，归 Aaron，且与判据 (1) 无关。
```

### 14.9 CONDITIONS 现状（builder 自评，不自证）

```
1 追加/超越且旧文本不删                met
2 五判据对照及有效变异证红              (a) 的障碍消失；(b)(c) 的实际缺陷已闭合
                                       —— 但**这需要一轮新的 fresh Sol 判定，我不自证**
3 fresh Sol 复审并经 Aaron 批准         not met（需新一轮）
4 机制、GATE_TABLE、CHECKPOINT_OF 零改动  met（本次仍零改动）
5 陈旧化绊线保留                        met
```

---

## 15. 第 2 轮措辞复审（`c-build-2-wording-r2`）返回 HOLD —— 四条逐条处置

```
VERDICT=HOLD   WORDING_MAY_GO_TO_AARON=NO   TRANSPORT_PRECHECK=PASS
CRITERION_1_NOW_MET=NO —— (a) NO · (b) YES · (c) YES
CONDITIONS_MET=1 met · 2 not met · 3 not met · 4 met · 5 met
```

**四条全部先复现后修。** 复审席这一轮独立复核了 51 项测试、原像重建、
全窗唯一性、四条分歧结局，并明列了它**无法**独立复核的三类历史事实 ——
那份 `UNVERIFIABLE_SELF_REPORTS` 清单本身就是我要的东西。

### 15.1 HIGH ① 过程性质被标成状态事实 —— 成立，已改

复审席的话：

> 即使当前机制确实执行比较，`FINAL bytes == intended` 也无法证明比较曾发生。

**复现（变异实测）**：把 `already_sealed` 改成不读 FINAL 直接返回 ——

```
变异体      action=already_sealed
调用后事实   FINAL 在场=True，其字节==intended=True
未变异体    完全相同
```

**该途径看不出比较是否发生过。** 所以 (a) 的检出途径**不是纯文件系统事实**，
是**被钉住的机制性质**。

**这与 §14 的撤回并不冲突，两件事都成立**：
类确实没有实例（§14 对），**而途径分类仍然错**（本节）。
我撤回了虚构的缺陷，却没有回头检查那条途径该怎么归类。

**(a) 更正为**：

```
(a) 未经校验的 FINAL 不存在
    防的违规类：一份没被复读校验过的 FINAL 被当作已封存
    检出途径：**被钉住的机制性质** —— 每一条把 FINAL 当作已封存的路径，
              都在同一次调用内把 FINAL 读回并与 intended 比对：
              既存件走 `existing == intended`，新封存走 promote 后的
              `final.read_bytes() != intended`。
              由 `test_wrong_bytes_are_still_refused` 与
              `test_every_sealed_final_was_read_back.py` 的读计数钉住。
    **明写不是什么**：调用后的「FINAL 在场且字节 == intended」**不能**充当本条的
              检出途径 —— 一个从不比较的变异体留下完全相同的状态（实测）。
              钉在 `test_post_call_state_cannot_show_the_comparison_happened`。
```

变异证红（实测）：撤掉 `already_sealed` 的比较 → 4 红；还原 → 17 绿。

### 15.2 HIGH ② 陈旧化保护不成立 —— 成立，且实情比 finding 更糟

复现：追加一份伪造的取代性批准（把 `ND1_PARTIAL_MODIFY_TEXT` 改成完全不同的值），
**34 条守卫全绿**。

**然后枚举出了真正的问题**：`ND1_PROFILE_RATIFICATION.md` 里**早就有三份批准**：

```
R1  0a08319a…  2026-08-20   ops/DECISION_PACKET_N00_AND_ND1.md 第 1309 行 49 行
R2  a3d40b7c…  2026-08-23   同文件第 1614 行 51 行     R1_STATUS=SUPERSEDED_BY_R2_FOR_P3_ONLY
R3  d40ad864…  2026-08-27   ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md 第 110 行 60 行
                            R2_STATUS=SUPERSEDED_BY_R3_FOR_P3_AND_F3_ONLY
```

**§13.2 只锚在 R1 上，而 R2、R3 当时已经存在。** 我没有注意到。

**逐份重建后核验的结果（这一条是好消息，但它是运气）**：

```
三个锚定值   三份批准逐字相同
时机词       三份各自零命中（用测试那条正则；加 gate 则 R1 有 1 行，
             是 RECOMMENDED_F1_GATE_NAME_ENUM=DEFER_TO_N04，管命名不管时机）
```

**所以锚定实质上站得住 —— 但没有任何机制在守它。**

**修**：新建 `tests/test_every_approval_is_accounted_for.py`：
逐份按哈希重建原像（R3 的在另一个文件里，是**搜出来的不是猜的**）·
三个锚定值在每一份里都必须一致 · falsifier 对每一份都查 ·
**出现第四份未检查的批准即失败**，并明写「不得放宽模式让它通过」。

变异证红（实测）：追加第四份 → 1 红；还原 → 6 绿 + 18 subtests。

### 15.3 MEDIUM 测试仍声称 comparison 不是 verification —— 成立，已改

`test_c_build_2_wording_coverage.py` 的模块 docstring 还留着
「Nothing in that branch verifies anything; it compares」，与 §14 直接矛盾。

**这比单纯的陈旧更糟**：读测试的复审席和读设计的复审席，
会从**同一个作者**那里拿到两个互相矛盾的故事。已重写，并把 §15.1 的
过程/状态区分一并写进去。一个测试也随之改名
（`..._accepted_on_bytes_alone` → `..._accepted`，因为前者读起来像「没检查就接受」，
而它是**检查了字节之后**接受的）。

### 15.4 LOW `unittest.main()` 位置导致半套件假绿 —— 成立，已改

```
直接运行   Ran 5 tests ... OK      <- 后半个文件根本没跑
pytest     10 passed
```

我用 `cat >>` 往文件尾部追加测试类时，把它们追加到了
`if __name__ == "__main__":` **之后**。**全仓扫描：只有这一处。**
已把 `unittest.main()` 移到文件末尾；直接运行现在跑满 10 条。

### 15.5 复审席点出的第五件（未列入 FINDINGS，但我接受）

> ⑤ 导出值锚定：锚定不必直达批准块；「批准前件＋固定、确定性的导出规则」
> 可以形成有效传递锚。**但现有 premise test 不会在「新批准值追加、代码仍旧」时变红。**

前半句是对我 §13.2 那条担心的**否定**——传递锚有效，我不必把 (b) 的依据行说得那么弱。
后半句正是 15.2，已修。

### 15.6 §10.1 的时态 —— 我自己审计出来的，一并施加

`ops/SELF_REPORT_AUDIT_2026-08-29.md` 记录：§10.1 那张表以现在时写着
`day_strata.canonical_json ← 没有 allow_nan`，而三份现在全部抛 `ValueError`
（Aaron 2026-08-27 授权补上，修复记在紧随的 §10.1bis）。

**不是假断言，是陈旧时态。** 表本身按追加惯例不改，此处标注：

```
§10.1 的表是 2026-08-27 当时的实测记录。
现势：三份 canonical_json 全部 allow_nan=False，全部对 NaN 抛 ValueError。
修复见 §10.1bis。只读 §10.1 不读 §10.1bis 会误以为缺陷仍在。
```
