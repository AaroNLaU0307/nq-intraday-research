# Builder 裁定 —— 2026-09-02

编号承接 `ops/BUILDER_DECISIONS_2026-08-29.md`（BD-1..BD-4 已占用）。
初稿把这两条误编为 BD-2 / BD-3，与该文件冲突，已改为 BD-5 / BD-6。

BASIS=Aaron 2026-08-29「很多决定不需要问我」——工程判断归 builder，
Aaron 保留六类：成本 / Primary 指标 / 样本切分 / 何时动真实数据 /
promotion-falsified / quant-data 建目录。

**这份文件不是 owner 裁定。** 与 `ops/OWNER_DECISIONS_*.md` 严格分开。
每一条都写明**为什么它是工程判断而不是研究判断**。

---

## BD-5 `archived_bytes_deleted` 的终态：~~**A1**~~ —— **2026-09-02 收回**

> **收回。** 复审席位反驳了下面的排除法，反驳可复现：
> P3 的已批后继是 `P4 / A1 / F2 / CR1` **四个**——我把「Router B 函数的
> 返回值集合」当成了「状态机的后继集合」，F2 与 CR1 从未被排除；
> `A1` 行必填 `archive_code`，而 `archived_bytes_deleted` 不在 5 个
> `ARCHIVE_CODES` 里，**这行根本写不出来**；`A2` 作为 A1 的唯一出口，
> 只断言**本次 run 拷贝**的一致性，治不了「更早归档的字节被删」。
>
> 代码已退回**具名拒绝**，`post_archive_ok` 参数移除。
> 详见 `ops/REVIEW_RESULT_ENG_SAFETY_2026-09-02.md` §3。
>
> **下面的原文保留**，因为一条被推翻的裁定的价值，在于它错在哪里可被读到。
> 其中「这条不占 Aaron 六类保留项、因而归 builder」一半仍然成立——
> **但『可以由我决定』不等于『可以由我决定错』。**

### 起因，以及我先犯的错

`ops/N04_EXECUTION_PATH_CHECKPOINT_4_2026-09-02.md` §2 把这一条写成
**「欠 Aaron 一条裁定」**。

**那是越级。** 它不碰成本、不碰 Primary、不碰样本切分、不动真实数据、
不产生 promotion/falsified、不建 quant-data 目录——**六类一条都不沾**。
它只回答「这个失败被记成哪个终态」，和 BD-1 是同一种问题。

Aaron 随后说「你不能决定就交给 Fable 裁决」。**这两件都不成立：**
一是这条本来就该我定；二是他自己的规矩写着
**「Fable 可顾问不可代签——它是我调用的」**，所以我既不该把裁决权转给 Fable，
也不该由我去调用它。

### 结论

```
run_c_build_3 报 archived_bytes_deleted
  且 local seal 存活
  -> decide_after_seal(local_seal_ok=True, report, post_archive_ok=False)
  -> A1
```

### 为什么 A1 不是发明，而是**排除法**

路由器 B 的答案空间是**封闭的**：`P4 / A1 / 被拒的 seal`。

```
P4                 Policy A：P4 需要 local_seal_ok AND archive_ok
                   而 R3 §1 的 C_BUILD_3 判据(b)「无任何已归档字节被删除」
                   刚刚被违反 -> 不是 ok -> 排除
被拒的 seal        seal 活着。这正是本码与 local_seal_absent /
                   local_seal_mutated 的**全部区别** -> 排除
────────────────────────────────────────────────
剩下               A1
```

**三取其二被排除，A1 是已批枚举剩下的那个，不是 builder 偏好的那个。**

### 为什么「排除法」在这里是足够的

单靠排除法**不够**——除非 A1 本身不是「放行」。它不是：

> A1 是**非终态陷阱**（`NON_TERMINAL_TRAPS`），`P5` 在一次显式的 `A2`
> 之前不可达。

所以把「证据被毁」判成 A1 **挡住了完成**，而不是把它挥手放过。
**如果 A1 意味着「继续」，上面的排除就不足以支撑这条裁定，我会把它递上去。**

### 为什么需要一个新参数，而不是造一份报告

`archive_sealed_run` 只校验它**刚做的那份拷贝**，从不看更早归档的字节。
所以它的报告可以说 `archive_ok`，而检查点说归档毁了证据。

`classify_archive_report` 按设计拒绝一份 `archive_ok` 的报告
（抛 `archive_ok_has_no_code`）。**要绕过它只有两条路：**

```
甲  合成一份「失败」的报告喂给它     —— 为了拿到一个结论而伪造证据
乙  把检查点的判定作为参数告诉路由器 —— decide_after_seal(post_archive_ok=)
```

**选乙。** 甲是这个项目最不该出现的一种动作。

参数默认 `True`，所以每一个既有调用方行为不变，且这一点被签名测试钉住。
另外钉住：`local_seal_ok=False` **压过**检查点的判定——seal 没活下来时，
结论仍是「nothing was sealed」。

### 边界：BD-5 只定了**一个**码

C_BUILD_3 将来新增的码**仍然失败关闭**——链路抛
`no ruled verdict covers <code>`，与 BD-1 对封印码的要求一致。
**一条被裁定的码，不给后来的码开门。**

---

## 与 BD-5 一起交回的两件事（**不是**我能定的）

```
①  何时动真实数据        Aaron 保留的六类之一
③  签一条 live P2        消耗研究自由度，只有 Aaron 能签
```

这两件**不能转给 Fable**：Fable 可顾问不可代签，且由 Aaron 调用。
若 Aaron 要 Fable 的**意见**（而非签字），我可以备送审包，由他发起。

---

## BD-6 封存码推导加宽为跟着调用走，并给新浮出的码分桶

### 结论

```
推导      _seal_codes_from_source 改为递归跟随模块内调用
          （与 builder 侧 2026-08-29 的加宽完全同型）
          扫出的码：7 -> 18
分桶      CALLER_ERROR_SEAL_CODES  4 条（调用方错误 / 伪造路线）
          UNMAPPED_SEAL_CODES      7 条（各带自己的开放问题）
          STAGE_GATE_OF_SEAL_CODE  不新增
          ROUTER_B_SEAL_CODES      不新增（其数量是被刻意钉住的）
```

### 为什么是工程判断

它不碰六类中的任何一类。它只回答「这个失败被记到哪一栏」，与 BD-1 同型。

### 怎么发现的 —— **不是读出来的**

把链路端到端组合起来之后，一个**真实调用方**吃到
`ClassificationError: production_product_type is in neither table`。
该码在 `_product_receipt` 里抛出，比 `seal_supplement_production` 低一层，
而推导只扫函数体 —— **它同时逃过了表和那条本该管住它的测试**。

**builder 侧 2026-08-29 已经为完全相同的缺陷加宽过一次**，注释里写着
「守卫比它的声称更窄」。**封存侧一直留着那个缺陷。**

加宽后另外还抓到 `filename_not_a_plain_name` ——
**那是我自己第 7 轮加的越界防护，从来没有任何表见过它。**

### 我先做错的一步，以及是谁拦下的

初稿把三个「两条路径共用的 raise 点」直接沿用 builder 的答案，理由是
「同一 raise 点该同一裁定」。

`test_the_SEAL_side_still_refuses_the_same_code` **当场拒绝**，而且它是对的：

> `freeze_payload` 冻结**整个** payload 含 binding，所以在封存路径上
> 来源确实有歧义，该码**不得**继承 builder 的答案。

**一个共用 raise 点已经被证明在两条路径上含义不同。既然有一个是错的，
三个我一个都不拿。** 全部记为 UNMAPPED 并写下各自的开放问题。

### 边界

新增的桶**不给任何码一道门**。七条 UNMAPPED 全部大声拒绝，
并说明**真正开放的问题是什么**（而不是「加到某处去」）。

按 Aaron 2026-09-02 的安排，它们**不单独开审**，
搭到下一个自然 review 节点一起过 —— 那里正需要一个不是我的读者。
