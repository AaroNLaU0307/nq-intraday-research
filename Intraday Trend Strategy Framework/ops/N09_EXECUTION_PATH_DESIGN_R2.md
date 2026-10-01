# N09 执行路径 —— 设计 R2（**仍未实现**）

```
RECORD_TYPE=DESIGN_FOR_CHALLENGE
NODE=N09 的门内代码（N09 的执行仍需 Aaron 的 P2）
BY=Opus 5，builder seat，2026-08-26
SUPERSEDES=ops/N09_EXECUTION_PATH_DESIGN.md（R1；保留不改，作为被审过的那一份）
BASIS=R1 ＋ fresh Sol 的 REDESIGN 六条（非正式工程意见，L6_GATE_EFFECT=NONE，
      记录见 ops/A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md）
STATUS=NOTHING_IMPLEMENTED
DESIGN_CONTRIBUTION=第 1–6 条的 checkpoint 与 snapshot 规则源自该 Sol 会话，
      `DELEGATED=YES`，按其要求在 N09 lineage 具名登记
```

---

## 0. R1 错在哪（两条，均由 builder 独立复核后确认）

**R1 说「跑 A→B→C」——不成立。** `GateContext` 的字段里**没有 `product`、没有
seal 证据、没有 archive report**（`archive_root` 只是根路径）。而五个 C_BUILD
门分属三个不同时刻。一次批量调用不可能让它们各自在正确时刻放行。

**R1 §4 把最终 event-stratum 映射归给了 `s0/context.py`——写错了。** 它归
`s0/dataset.py`（`event_stratum_of` / `build_event_stratum_map` /
`RULED_EVENT_NA_MAPPING` / `EVENT_STRATA`）；`context` 只提供上游 flag。

---

## 1. Checkpoint 架构（取代 R1 的「跑 A→B→C」）

五个 C_BUILD 门属于三个时刻，就拆成三个 checkpoint：

```
A_PRECHECK                        13 门   —— 不变
B_DERIVE                           5 门   —— 不变
C_BUILD_1  首次写入之前             row_schema_blind
                                   day_set_exact
                                   rows_digest_recompute
C_BUILD_2  staging 期间             seal_staging_partial
C_BUILD_3  archive report 存在之后   archive_policy_a
```

`GATE_TABLE["C_BUILD"]` 的**成员不变**（那是已批准的封闭枚举）；新增的是一层
`CHECKPOINT_OF: gate -> checkpoint`，把同一批门分派到三个时刻。**枚举不动，
时序另立**——改已批准枚举是另一件事，不搭这次的车。

### 1.1 门是分类器，不是校验器

Sol 第 1 条：「生产侧校验仍是唯一真相源，runner 的门只对其结果/异常做分类，
不重复实现不变量。」

**这与既有意图一致，不是新发明。** 现有桩自己的注释就写着：

> `row_schema_blind`：「The blind guarantee is enforced row-by-row by
> `day_strata_supplement._validate_row`; this gate exists so the failure has a
> NAMED stage/gate in the F1/F2 vocabulary.」

所以门的实现形态是：**调用生产侧校验，捕获其异常，映射到 F1/F2 词汇里的
具名 stage/gate**。门内不得出现第二份不变量实现——那正是本项目反复付过代价的
「第二份实现」形态。

## 2. 上下文类型：让门**不可能**在证据存在之前运行（Sol 第 2 条）

不是加运行时检查，是**用类型**：

```
PrecheckContext   A_PRECHECK 所需（今日 GateContext 减去 authority/prepared）
DeriveContext     ＋ authority, prepared            （必填）
BuildContext      ＋ product                        （必填）
StagingContext    ＋ staging evidence（.partial 与目标路径的实测状态）
ArchiveContext    ＋ archive_report                 （必填）
```

必填即 dataclass 的必填字段：**没有 product 就构造不出 `BuildContext`**，于是
`row_schema_blind` 在 product 存在之前根本无法被调用。这比「门里判断
`if ctx.product is None: fail`」强一级——后者仍然允许调用，只是会失败。

每个 checkpoint 的运行器只接受对应类型；类型不符是编程错误，不是门失败。

### 2.1 每门一条红证，外加「通过前无副作用」

Sol 第 2 条后半：「每个 C_BUILD 门配一条红证/变异证明，并证明该门通过之前不
产生任何效果。」

红证 = 构造一个该门必须拒绝的输入，证明它拒绝；**并且**在拒绝之后断言：
无文件写入、无目录创建、无 archive 尝试、无 registry 追加。

## 3. 三个快照，三个名字，三个类型（Sol 第 4 条）

```
SupplementRegistrySnapshotBeforeP3    registry_boundary 取，P3 追加之前
SupplementRegistrySnapshotAfterP3     registry_boundary 取，P3 追加之后
S0CustodyAuthorizationSnapshot        S0 封存 custody 的授权快照
```

**类型互不兼容。** `consumer.prepare_mc_input` 只接
`S0CustodyAuthorizationSnapshot`（今日它接的是裸 dict，改为具名类型），因此把
registry 快照误传进去是构造错误而非静默错误。

**不得调用 `real_input.prepare_real_mc_input`**——它带的是**真实 MC 运行**的授权
门，引进来就把 MC 运行的门装进了 supplement 生命周期，会死锁。R1 已如此主张，
Sol 复核同意；builder 已核 `consumer.prepare_mc_input` 自身**不含** MC 门。

### 3.1 snapshot₂ 的比较域：字节级，不是解析等价（Sol 第 3 条）

R1 提的是「解析后事件序列恰差一行」。Sol 要求更精确，**采纳**：

```
snapshot₂.text == snapshot₁.text + CANONICAL_P3_LINE
```

逐字节，不是「解析后等价」。理由是解析等价能被多种字节写法满足（空白、行尾、
列宽），而我们要证明的恰恰是**没有别的东西被写进去**。

### 3.2 半转移：不自动归 F2，走 Aaron（Sol 第 3 条）

```
P3 追加失败 / 半追加 / 回读不符  =  INDETERMINATE_HALF_TRANSITION
```

**不得自动记为普通 F2。** F2 的前提是「运行已开始」；而半追加意味着
**我们不知道它是否开始了**。把未知记成已知，正是 exposure 记账里最贵的那种错。

处置：停机、保留现场、转人工，**交 Aaron 裁定**这次是否消耗了 exposure。

## 4. `day_rows` 生产者（Sol 第 5 条，含对 R1 的事实纠正）

- **复用生产侧 S0 universe/data assembly 路径**，不另起一条读数据的路。
- **vol 与 event 两个分层都取自 `s0.dataset` 的映射**
  （`event_stratum_of` / `build_event_stratum_map` / 三分位那一组常量）；
  `s0.context` 提供的是**上游事件事实**，不是最终 event-stratum 映射。
- **对 `authority.expected_day_set` 做逐日精确对拍**：生产出的行集合必须与
  authority 派生的日集合**逐日相等**，不是「覆盖」也不是「包含」。

生产者自身**不得携带任何分层逻辑**。

## 5. bundle_precheck 的表要落盘并精确绑定（Sol 第 6 条）

`bundle_precheck.precheck_bundle_on_disk` 已返回 `recomputed`（逐文件
name/size/sha256）与 `summary_digest`。R2 追加两条要求：

1. **持久化**该表进运行证据——不是「查过了」的布尔，是查到的东西本身；
2. **在 P3 之前**把它与 `prepared.file_sha256` **精确绑定**（逐文件相等，不是
   摘要相等）。不符即在 STARTED 之前拒绝。

顺序是关键：绑定必须发生在 P3 之前，因为 P3 之后 exposure 已消耗。

## 6. 目录创建：**第三次独立授权**，签了 P2 也不够

Sol 把这条列为 `UNRESOLVED_FOR_AARON`。**查实后它比「待裁」更硬——它是已批准的
不变量**，见 `ops/DECISION_PACKET_N00_AND_ND1.md`：

```
SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES   # 不变量，非可选项
DIRECTORY_CREATION_AUTHORIZED=NO
ND1_WRITE_PROBE_AUTHORIZED=NO
「目录创建、写探针、执行是三次独立授权，不得合并」
```

**设计后果**：编排器即使拿到合法的 P2，在 `DIRECTORY_CREATION_AUTHORIZED=NO`
时**仍必须拒绝**，且这条拒绝**不得从 `output_root` 推导出来**——P2 声明输出根
不等于授权创建其下的子树。

`_g_supplement_subtree_absent` 今日只**观察**目标不存在。R2 追加一条同级门
（或把它扩成两段）：**观察不存在 ＋ 校验创建授权令牌**，两者都过才允许进入会
创建目录的那一步。

**留给 Aaron 的，是一个更小的问题**：他是否希望未来的 P2 句式**同时**承载目录
创建授权（即合并三授权中的两个）。默认答案是「不合并」，因为不合并是已批准的
不变量；合并需要一次修订裁定。**builder 不替他选。**

## 7. 仍归 Aaron，不在本设计内决定

1. **P3 与失败事件由谁追加**（R1 Q1/Q2，Sol 未裁，明确转 Aaron）。全局边界第 4
   条说「只允许主代理单写」，而 `scripts/s0_real_run.py` 在真实 S0 上开了相反
   先例。两种读法都成立。
2. **§3.2 的半转移裁定**：真发生时，那一次是否消耗 exposure。
3. **§6 的三授权是否合并**。
4. （承前）**exposure 事件入账授权** 与 **恢复锚 outcome-carrying 的处置**，见
   `ops/A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md` §5。

## 8. 验证计划

- **每个 C_BUILD 门一条红证**，外加「拒绝之后零副作用」的断言（§2.1）。
- **类型层面**：证明缺证据时对应 context **构造不出来**，而不是构造出来后失败。
- **snapshot₂**：一条证明字节级恒等成立；一条证明任何额外字节落到
  `INDETERMINATE_HALF_TRANSITION` 而不是 F2。
- **day_rows**：对 `authority.expected_day_set` 逐日对拍；分层值来自 `s0.dataset`
  的映射，且生产者内**无分层逻辑**（AST 层面钉住）。
- **bundle_precheck 绑定**：逐文件相等，且证明绑定发生在 P3 追加之前。
- **默认拒绝不被削弱**：`SUPPLEMENT_EXECUTION_AUTHORIZED=NO` 与
  `DIRECTORY_CREATION_AUTHORIZED=NO` 时，整条路径仍确定性拒绝。

## 9. 本设计不做什么

不读真实 Development 数据；不创建任何目录（两个 `supplements\` 子树仍不存在）；
不追加 registry 行；不动 exposure；不填 P2 占位符；不改样本／标签／NA 政策／
成本／Primary／Oracle／feasibility／运行定义。
