# N09 执行路径 —— 设计（**未实现，待挑战**）

```
RECORD_TYPE=DESIGN_FOR_CHALLENGE
NODE=N09 的门内代码（不是 N09 本身；N09 的执行仍需 Aaron 的 P2）
BY=Opus 5，builder seat，2026-08-25
HEAD=d4d7c6ead513f6526f7237bfca3f81ca4fb92d14
STATUS=NOTHING_IMPLEMENTED —— 本记录是设计，不是补丁
WHY_A_DESIGN_PASS=这是唯一会读真实 Development 数据、在 quant-data 下创建
     目录、写封存字节的工程块。QROS FULL 车道对这一类要求先过 fresh Sol 的
     A2 式设计挑战，再动手。
```

---

## 1. 已有什么（实测，非记忆）

| 组件 | 状态 |
|---|---|
| 23 个门（A_PRECHECK 13／B_DERIVE 5／C_BUILD 5） | **全部已注册于 `supplement_runner.GATES`** |
| 其中 C_BUILD 的 5 个 | **刻意的 `unreachable in this build` 桩** |
| `run_stage_gates(stage, ctx)` | 已实现 |
| `plan_supplement_paths` / `plan_failure_event` / `plan_next_short_id` / `assert_chain_closed` / `classify_archive_report` / `decide_after_seal` / `resolve_partial` | 已实现 |
| `supplement_production.build_supplement_from_authority` | 已实现 |
| `supplement_production.seal_supplement_production` | 已实现 |
| `supplement_authority.derive_supplement_authority` | 已实现 |
| `consumer.prepare_mc_input` | 已实现，**自身不含 MC 授权门** |
| `registry_boundary`（C2） | 已实现（本日） |
| **编排器（构造 GateContext、跑 A→B→C、写盘、封存、追加事件）** | **不存在** |
| **`day_rows` 的生产者** | **不存在** |

## 2. 一个我担心过、经查不存在的循环依赖

我先前怀疑：supplement 需要 `PreparedMCInput`，而生产上取得它要过
`real_input.prepare_real_mc_input` → `authorize_real_mc`（**真实 MC 运行**的
授权门），而 MC 运行在 supplement 之后 —— 循环。

**经查不成立。** `consumer.prepare_mc_input` **本身没有 MC 授权门**；门在
`real_input` 的包装层上。所以 supplement 执行路径必须**自己走 `prepare_mc_input`，
绝不经由 `real_input`**——后者会把 MC 运行的门引进 supplement 生命周期，那是
范畴错误，并且会死锁。

## 3. 调用链（全部由已有件组成）

```
attestation 字节（代码 pin：consumer.ATTESTATION_SHA256_PINNED）
  + S0-T001 封存 bundle 的 14 个文件字节（永久只读）
  → bundle_precheck.precheck_bundle_on_disk(...)        [N09 强制缓解]
  → consumer.prepare_mc_input(bundle, snapshot, attestation_bytes)
                                                        → PreparedMCInput
  → supplement_authority.derive_supplement_authority(prepared)
                                                        → SupplementAuthority
  → 【缺】day_rows 生产者（唯一的真实数据触点）
  → supplement_production.build_supplement_from_authority(auth, prepared, rows)
  → supplement_production.seal_supplement_production(product, out_dir, ...)
  → 归档 + 逐文件 SHA-256 复核
```

## 4. `day_rows` 生产者 —— 复用，不发明

每行四个结构键（`day_strata_supplement.ROW_FIELDS`）：
`trade_date` / `year` / `vol_stratum` / `event_stratum`。

**两个分层的定义都已裁定且已实现**，生产者只做联接：

- **vol**（`T1|T2|T3|vol_na`）—— `s0/dataset.py`：
  `RULED_VOL_TERCILE_REFERENCE="full_development_expost"`（裁定的是**取阈样本**），
  估计量与边界为已披露并钉住的工程约定
  （`numpy.quantile(v,[1/3,2/3],method="linear")`，`lower_inclusive_le_threshold`），
  窗口 `VOL20_N_RETURNS=20 / VOL20_N_CLOSES=21`。
- **event**（`CPI|FOMC|NFP|NA_multi_event|none`）—— `s0/context.py`，含
  「多类别计数 == 互斥 NA_multi_event 类」的守恒不变量。

**设计立场：生产者不得自带任何分层逻辑。** 它按日查这两个已裁来源并联接。
任何在此处重新实现三分位或事件归类的做法，都是把已裁方法复制成第二份实现——
本项目已经因为「第二份实现」付过代价。

## 5. C2 制造出来的一个新问题：P3 追加会让快照过期

这是本设计里最需要被挑战的一点。

C2 要求「对每一个依赖 supplement 解析的结果，边界读一次 registry，两套解析跑
同一份不可变快照」。但执行路径**会在中途向同一份 registry 追加 P3**
（`SUPPLEMENT_RUN_STARTED`，pre-start／post-start 的唯一分界）。追加之后：

- A_PRECHECK 用的快照**已经过期**；
- 之后任何解析都需要**新快照**；
- 而新快照本身也必须两套语法都通过。

**提议的规则（待裁）**：

```
恰好两次快照，不多不少。
  snapshot₁  A_PRECHECK 全部通过之前
  【追加 P3】
  snapshot₂  追加之后立即取；B_DERIVE 与 C_BUILD 全程只用它

不变量：snapshot₂ 的事件序列 == snapshot₁ 的事件序列 + 恰好一行，
       且那一行就是本次运行自己的 P3。
任何其它差异 = 文件在运行中被别人改了 = post-start 失败（F2 族），
       exposure 已消耗且不回滚，id 作废。
```

理由：两次快照之间的差异是**这次运行自己造成的、且完全可预测**，所以它是可
机械验证的，而不是「重读一次希望没事」。

## 6. 归 Aaron／Sol 的问题（builder 不自行决定）

**Q1 —— 谁追加 P3？** 全局边界第 4 条写「registry／exposure／supplement
ledger 均 append-only，**只允许主代理单写**」。若编排器自己追加 P3，那就是生产
代码在写 registry。**但有先例**：S0 的真实运行由 `scripts/s0_real_run.py` 自己
追加了 `RUN_STARTED`。两种读法都讲得通，**这不是我能替 Aaron 定的**。

**Q2 —— 失败事件（F1/F2 族）由谁追加？** 同 Q1。`plan_failure_event` 只*规划*
事件，不写。规划与写之间的那道缝归谁，未裁。

**Q3 —— §5 的两次快照规则是否被接受？** 它是我提的，不是任何已批准文本要求
的。C2 只说「读一次」，没说运行中途合法追加之后该怎么办——因为写 C2 时执行
路径还不存在。

**Q4 —— C_BUILD 那 5 个桩何时变成实义？** 它们今天无条件拒绝。改成实义检查
是把无条件拒绝变成有条件拒绝——在没有编排器时是不可达的理论放宽，但仍是一次
拒绝语义的改变。**提议：与编排器同一次改动落地**，绝不让它们处在「已实义但
无人复核过它们检查什么」的中间态。

## 7. 本设计不做什么

- 不读任何真实 Development 数据（本轮零读取）。
- 不在 `C:\Users\Aaron\quant-data\` 下创建任何目录；两个 `supplements\` 子树
  仍不存在，已核。
- 不追加任何 registry 行，不动 exposure。
- 不填 P2 模板的占位符，不代 Aaron 签发。
- 不改样本／标签／NA 政策／成本／Primary／Oracle／feasibility／运行定义。

## 8. 落地后的验证计划

- `day_rows` 生产者：对已裁来源做**逐日对拍**，而不是自证；分层计数须与
  `s0/context.py` 的守恒不变量一致。
- 两次快照规则：一条行为测试证明第二次快照与第一次恰差一行且是本次 P3；一条
  证明任何其它差异落到 F2 族。
- C_BUILD 5 门：每门一条红证（修复前失败）。
- 编排器：`SUPPLEMENT_EXECUTION_AUTHORIZED=NO` 时**整条路径仍确定性拒绝**——
  实现执行路径不得削弱默认拒绝。

---

## STATUS — SUPERSEDED, 2026-08-26

**追加，未改写正文。** 上面是 fresh Sol 审过的那一份，包括它找出的两个错误：

1. §3 的「跑 A→B→C」不成立——`GateContext` 不携带 product／seal 证据／archive
   report，而五个 C_BUILD 门分属三个不同时刻。
2. §4 把最终 event-stratum 映射归给了 `s0/context.py`，实际归 `s0/dataset.py`。

两条 builder 均已独立复核确认。**就地改写会毁掉审查链**，故正文保持原样。

```
VERDICT      = REDESIGN（非正式工程意见）
L6_VERDICT   = REJECTED_INCOMPLETE   L6_GATE_EFFECT = NONE
SUPERSEDED_BY= ops/N09_EXECUTION_PATH_DESIGN_R2.md
REVIEW_RECORD= ops/A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md
```

R2 采纳了全部六条修改，并新增一条本文件漏掉的、已批准的不变量：**目录创建、
写探针、执行是三次独立授权，不得合并**（`SEPARATE_DIRECTORY_CREATION_
AUTHORIZATION_STILL_REQUIRED=YES`）——即签了 P2 也不足以创建那两个
`supplements\` 子树。
