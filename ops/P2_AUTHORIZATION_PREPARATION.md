# N09 的 P2 —— 它到底要什么，以及为什么今天签了也没用

```
RECORD_TYPE=PREPARATION（不是授权，不含任何已批准值）
BY=Opus 5，builder seat，2026-08-27
BASIS=Aaron 2026-08-27「关于这个我不清楚，你找到后发给我，我会同意」
STATUS=NOTHING_AUTHORIZED —— 本文件不签、不代填、不生效
```

**我不能替你写这一句，这不是我谨慎。** 决策包 §D.10.4 逐字写着：

```
EACH_EXECUTION_STILL_NEEDS=Aaron 单独的、绑定完整 40 位 commit 的精确授权语句
SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES
```

**如果这句是我填的，它就不再是那条规则要的东西了。**

---

## 1. P2 这一行长什么样

`P2` 的事件规格（`supplement_contract.EVENTS["P2"]`，已批准）：

```
token   SUPPLEMENT_EXECUTION_AUTHORIZED
actor   Aaron          ← 只有你
class   NUMBERED       ← 占用编号序列
必填    supplement_id · authorized_commit_40hex · output_root ·
        verbatim_authorization_sentence
前驱    P1 | P2S | T1
后继    P3 | F1 | F3
```

已批准 profile（R3）对这句话的约束：

```
EXECUTION_SENTENCE_BINDS=supplement_id+40hex_commit+output_root
EXECUTION_SENTENCE_ONE_RUN_ONLY=YES
EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE=YES
```

**后两条是要害**：**一句话只管一次运行，且 commit 一动就作废。**

四个值里三个我可以查实并给你，第四个只能是你的话：

| 字段 | 值 | 来源 |
|---|---|---|
| `supplement_id` | `MC-DS-S001` | `day_strata_supplement.SUPPLEMENT_ID`，已固定 |
| `authorized_commit_40hex` | **待定** | 必须是**真正要跑的那棵树**的 40 位 commit。今天填任何值都会被下一次提交作废 |
| `output_root` | `C:\Users\Aaron\quant-data\itsf-runs`（归档侧 `…\itsf-runs-archive` 由治理根派生，不由本句指定） | `contracts.RULED_RUNS_ROOT`，两个根都已存在 |
| `verbatim_authorization_sentence` | **只能是你本人的话** | §D.10.4 |

---

## 2. 今天签了也生效不了 —— 四条，逐条实测

### ① P2 没有前驱可挂 —— 这条最硬

```
grep -c "MC-DS-S001" ops/TRIAL_REGISTRY.md   ->  0
```

**registry 里 `MC-DS-S001` 一行都没有。** 而 P2 的前驱是 `P1 | P2S | T1`，三个都不存在。

**所以 P2 今天根本追加不进去**，签了也挂不上链。需要先有 `P1`
（`SUPPLEMENT_PROPOSED`，actor = main agent，必填四字段）。

### ② 追加 P1 本身需要另一条授权

```
REGISTRY_EVENT_APPEND_AUTHORIZED=NO
```

而 D-3 的 HOLD 条件 3 另外规定：**生产代码不得获得任何 registry 写能力**，
直至 fresh Sol PASS ＋ 你的授权。D-3 现在是 HOLD，五项待你裁。

### ③ 目录创建是**另一条**授权，且尚未给

```
DIRECTORY_CREATION_AUTHORIZED=NO
SEPARATE_DIRECTORY_CREATION_AUTHORIZATION_STILL_REQUIRED=YES   （§D.10.4 原文）
```

实测：两个治理根都存在，但**`supplements\` 子树在两个根下都不存在**。
而 `supplement_subtree_absent` 是 A_PRECHECK 的 13 道门之一。

**签 P2 不等于可以建目录**——ND1 明写三条独立授权不得合并。

### ④ 执行路径本身还是「默认拒绝骨架」

C_BUILD 的五道门**今天全部无条件拒绝**（实测）：

```
row_schema_blind        unreachable in this build: no rows are ever derived
day_set_exact           unreachable in this build: no day set is ever derived
rows_digest_recompute   unreachable in this build: no rows digest is ever computed
seal_staging_partial    unreachable in this build: nothing is ever sealed
archive_policy_a        unreachable in this build: nothing is ever archived
```

这是 `ops/N09_EXECUTION_PATH_DESIGN_R3.md` 的
`BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`——而那个范围**正是因为上面 ①②③ 才取的**。

---

## 3. 所以正确的顺序是什么

**P2 必须是最后一步，不是第一步。** 理由是机械的：
`EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE=YES`——你现在签一句绑定某个 commit
的授权，**之后任何一次提交都会把它作废**，你得重签。

```
1. D-3 的五项裁定           ← 决定「P3 由谁写」，进而决定执行路径能建成什么样
2. 目录创建授权             ← 四要素：来源／actor／精确文本／commit 绑定／有效期
3. registry 追加授权         ← 让 P1 能被追加（或裁定由谁手工追加）
4. 建执行路径本体            ← 把 C_BUILD 五道门从「无条件拒绝」变成真的分类器
5. 追加 P1                   ← SUPPLEMENT_PROPOSED
6. 你签 P2                   ← 绑定第 4 步完成后的那个精确 commit
7. 真跑
```

**第 1–3 步全是你的**；第 4 步是我的，但它等第 1 步；第 5 步等第 3 步；
第 6 步只能是你，且只有在第 4 步落地、commit 稳定之后签才有意义。

---

## 4. 我建议你现在做什么

**不是签 P2。** 是先把第 1、2 步交出去——你已经说了这四件可以交决裁席商量。

等它们回来、执行路径建成、commit 稳定，我会把那时的 40 位 commit 查实后再来找你，
届时这一句话才有它该有的效力。**那时我仍然只给你字段和值，句子还是你写。**

---

## 5. 边界

本文件不签任何东西、不代填任何占位符、不追加任何 registry 行、不创建任何目录。
八个授权字段仍全部为 `NO`。

---

## 订正-SUBTREE-GATE-2026-08-29

```
CORRECTION_ID=订正-SUBTREE-GATE-2026-08-29
FOUND_BY=builder（Opus 5），在 Aaron 授权创建两条 supplements 父层之后
         去实测「这解开了什么」时
METHOD=执行门本身，不是读代码
```

### 被订正的句子（**原句保留，本件只追加**）

> `supplement_subtree_absent` 是 A_PRECHECK 的 13 道门之一 ——
> **子树不存在时它拒绝**，且模块永不自行创建。

**「子树不存在时它拒绝」是假的。** 实测三种情形，门**全部通过**：
两个父层都不存在、只有一个存在、两个都存在。它在目录被创建之前就是通过的。

### 它实际拒绝什么

它规划真实目标 `<root>/supplements/<id>_<UTC>`，由规划器拒绝：

```
碰撞          目标已存在                -> plan_target_exists
根缺失        <root> 本身不存在          -> plan_root_absent   ← 是「根」，不是 supplements
reparse 点    根是重解析点/符号链接
逃逸          目标逃出根
无 UTC 戳     目录名 <id>_<UTC> 无法规划
```

**「根」与「supplements 子层」的区别就是这条订正的全部内容。**

`ops/N09_EXECUTION_PATH_DESIGN_R2.md` 一直是对的：
「`_g_supplement_subtree_absent` 今日只**观察**目标不存在」。
**设计文档对，治理文档错。**

### 代价：多少，以及不是多少

裁定 `dec-four-owner-2026-08-27` 问的是五个槽应当取什么**形式**，
答的是封闭枚举、无通配符、绑路径不绑 commit、四条 fail-closed。
**没有一条依赖这句假话** —— 它是动机，不是前提。**所以裁定站得住。**

真实代价是：这份授权被描述成能解开一道门，而它**不解开任何一道门**。
A_PRECHECK 十三道门在创建前后的结果**完全一致**。

### 授权本身仍然必要，理由是另一条（真的）

运行目录 `<root>/supplements/<id>_<UTC>` 在「不隐式创建父层」的纪律下，
需要父层先存在，而**生产路径不创建任何目录**。

实测的精确版本：`mc/` 包里**有且只有一处 `mkdir`**，在
`seal_supplement_test_only` —— 函数名自己声明了范围，且全仓无生产调用者。

**一条如实记下的残留**：那处 `mkdir` 用的是 `parents=True, exist_ok=True`。
若有人拿治理根去调它，它**会**把 `supplements` 父层一起建出来。
所以「模块永不自己创建」这条保证**扛在调用方，不在被调方** ——
它是一条有实测支撑的命名约定，不是机制。

### 机械化

`tests/test_the_subtree_gate_observes_collision_not_absence.py`
把上述每一条都执行了一遍，并守着这句假话不再回来。

本件未写出那句假话，只是把「两个根下 supplements 都不存在」与
「`supplement_subtree_absent` 是十三道门之一」并置，**并置本身产生了因果暗示**。
在此标明：两者无因果关系。
