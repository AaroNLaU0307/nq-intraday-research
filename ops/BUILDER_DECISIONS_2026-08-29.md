# Builder 裁定 —— 2026-08-29

BASIS=Aaron 2026-08-29「很多决定不需要问我」——工程判断归 builder。

**这份文件不是 owner 裁定。** 它记录的是我在授权范围内自己做的工程决定。
与 `ops/OWNER_DECISIONS_2026-08-29.md` 严格分开：把两者混在一起，
就是用「Aaron 说过让我自己决定」去覆盖一条本该他决定的事。
每一条都写明**为什么它是工程判断而不是研究判断**。

---

## BD-1 两个未决封印码：不归门，归路由器 B

### 结论

`production_supplement_object_invalid` 和 `production_payload_drift`
**不获得门名**。它们是封印步骤的失败，其结局由路由器 B 拥有：

```
seal 失败 -> local_seal_ok=False
          -> decide_after_seal(...) 抛 local_seal_failed
          -> 「no P4 and no A1: nothing was sealed」
```

### 为什么这是工程判断

它不碰样本、标签、NA 政策、成本、Primary 指标、真实数据、也不产生
promotion/falsified 结论。它只回答「这个失败被记到哪一栏」。

### 为什么不是「挑一个门」

三条，按分量排：

**1. 项目已经为完全相同的形状裁定过一次，而且那次裁定是被执行的测试。**
`archive_policy_a` 是一个 C_BUILD 门，但把它当普通门路由会走 Router A 到 F2，
而已批准的 `ND1_ARCHIVE_FAILURE_POLICY=A` 要求 A1 —— 矛盾。
`tests/test_n09_r3_design_facts.py:142`
`test_routing_it_as_an_ordinary_gate_contradicts_policy_a` **执行**这个矛盾，
docstring 写着「This is the defect, executed. Not a hypothetical.」
解决办法当时就定了：`ROUTER_OF` 把该门的结局交给 Router B。

我在这里做的是**套用已裁定的先例**，不是发明原则。

**2. 现有的门没有一个说的是这两件事。**
C_BUILD 五个门是 `row_schema_blind`、`day_set_exact`、`rows_digest_recompute`、
`seal_staging_partial`、`archive_policy_a`。
`row_schema_blind` 管的是**行**；补充对象是容器，不是行。
把行的门拉去盖容器，正是这个项目今晚已经踩到第八次的
「守的边界比声称的属性窄/宽」。

**3. `GATE_TABLE` 是已批准的封闭枚举，我不能加门。**
`supplement_contract.py:377`：「GATE_TABLE IS NOT TOUCHED. It is an approved
closed enum... Editing the enum would be an R4-level act.」

所以「加一个合适的门」不在我的权限内，「挑一个不合适的门」会把缺陷记到
没人裁定过的名下 —— 而门名是 F1/F2 事件真正写进登记簿的东西。

### 实现方式：与项目已有做法一致

不改枚举，**在同名之上加一层独立映射** —— 正是 `CHECKPOINT_OF` 和 `ROUTER_OF`
的做法（`supplement_contract.py:360-398` 明写这是合法的层）。

`UNDECIDED_SEAL_CODES` 被 `ROUTER_B_SEAL_CODES` 取代。
`classify_seal_failure` 对这两个码仍然拒绝，但拒绝的措辞从
「没人裁定过」改成「**路由器 B 拥有它，去调 decide_after_seal**」——
从「不知道」变成「知道，而且知道该去哪」。

### 留给复核的一句话

如果 Fable 或 Sol 认为这两个码**确实**应该在 C_BUILD_2 拿到门名
（即封印失败也算门拒绝），那需要的是一次 R4 级枚举修订，不是我这一层。
我把决定和理由都摆在这里，是为了让那个反对意见有明确的靶子。

---

## BD-2 qros 席位台账：建

`ops/REVIEWER_EXPOSURE_LOG.md` 在 qros-runtime 下不存在，导致席位轴
按规矩只能读作 `UNKNOWN` 而不是 `NONE`。建一个空台账（带表头和归一化规则）
把 `UNKNOWN` 变成一个真实的「零条记录」。

**为什么是工程判断**：建一个空的仓内文件，不消耗任何研究自由度。
席位曝光与研究曝光是两根**永不合并**的轴，烧一个席位不消耗研究自由度。

## BD-3 qros「倒转默认」：正式采纳为设计

`_must_be_a_directory` 作为唯一接受规则（而不是列举拒绝理由），
已经过第 8、9 轮 Sol 复核并修好。正式采纳。

**为什么是工程判断**：这是「怎么写这个函数」，没有研究内容。

---

## BD-4 `production_payload_unsupported_type` —— **我明确不裁**

### 怎么发现的

端到端干跑之后，我把「一个模块捕获另一个模块的异常并重新分类」当成**一类**去扫，
扫出 11 处。查我关键路径上的那两处时发现：**我自己的推导测试只扫了
`build_supplement_from_authority` 的函数体，没跟着调用走。**

`production_payload_unsupported_type` 在 `_freeze_value` 里抛出，低一层，
于是**同时逃过了表和那条本该管住它的测试**。

**守卫比它声称的属性窄** —— 本项目今晚已经第九次出现这个形态，而这次是在
我为前八次写的守卫里。已把推导改成跟着调用递归。

### 这个码是什么

载荷里有一个键或值不是**恰好**内建类型 —— 一个敌意子类活过了冻结。
这是**完整性**缺陷，不是行模式缺陷。

### 为什么我不裁

C_BUILD 五道门没有一道说的是这件事：
`row_schema_blind` 管的是四个结构行字段与盲保证，而这条是关于**载荷里任何位置的
Python 类型**，而且那个值可能来自行，也可能来自 authority 的 binding。

BD-1 的规矩在这里同样成立：**门名会被写进 F1/F2 行，挑一个就是把缺陷记到没人裁过的
名下。** 而与封印码不同的是，这条在**构建期**触发，没有一个封印后的路由器 B 可以接手。

所以出路只有两条，**两条都不在我权限内**：

```
甲  新增一道门        -> 动已批准的封闭枚举 GATE_TABLE，是 R4 级动作
乙  归给某道现有门     -> 需要把理由写下来并被裁定，而不是我认为合适
```

**现状：`classify_builder_failure` 对它大声拒绝并附上这个问题。**
在被裁定之前，这条路径上的完整性缺陷会**停机**而不是被记成别的东西 ——
这是从严的一边，也是对的一边。

### 交给谁

不占 Aaron 的六条保留项，也不该由我自己了结。**建议随下一轮 Sol 或 Fable 一起过。**
