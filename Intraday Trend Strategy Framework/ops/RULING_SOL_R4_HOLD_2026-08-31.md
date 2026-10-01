＃ R4 复审 fresh Sol：HOLD —— 复现与处置

```ini
REVIEW_ID=r4-cr1-anchoring
RETURNED=2026-08-31
VERDICT=HOLD
FINDINGS=4 阻断 ＋ 1 条对我用词的更正 ＋ 1 条陈旧数字
REPRODUCED_BY_BUILDER=4/4（可实测的全部实测）
BUILDER_AGREES=全部
FALSIFIER_INDEPENDENTLY_RUN=YES（席位自己走了冷读）
REGISTRY_REPO_READ=YES（本轮特许，已记席位轴台账第 14 行）
```

**他确认的三件（条件 (b) 要的正面结论）全部 PASS**：
`PREIMAGE` 核心语义 UNCHANGED、`CRITERION` EXACTLY_UNCHANGED、
`UNRESOLVED` TOCTOU EXACTLY_UNCHANGED 且未被悄悄改窄。
`REVISION_WEAKENS_ORIGINAL=NO`。

**但提案不能按现文本批准**，四条阻断如下。

---

## 1. 锚点：**我把「发现」和「验证」混为一谈了**

我在提案里写：

> **A FILESYSTEM PATH IS NOT THE ANCHOR** —— a path is machine-specific and
> moves without leaving a record. The commit pair is the anchor.

**席位实测证伪**：

```
框架仓 object DB 里查 N1   ->  不存在
registry 仓里查 N1         ->  存在
```

**commit hash 只能在一个已经被定位的 object database 里确认身份，它不能发现仓在哪。**
我那五跳之所以成立，是因为墓碑与 O1 里的**绝对路径仍然有效** ——
**是路径在做发现，commit 对只在做验证。**

我把两件事写成了一件，并且写在了一句加粗的否定句里。
这是「声称比事实宽」的又一次，而且这一次否定的恰好是真正承重的那一半。

**处置**：v2 必须把两个角色分开写，并把「仓被移动则冷读者无法发现」
如实留成残留，而不是用一句加粗掩盖。
是否因此触发证伪器（须回决裁层），**由席位与 Aaron 判，不由我判** ——
我上一次自己判「澄清」，就是这么判偏的。

## 2. 我加的那句话：**是仓选择判据，不是澄清；而且用词不准**

席位判 `NEW_REPOSITORY_SELECTION_CRITERION`，同时明确 `NOT_A_NEW_INTACT_CRITERION`。

**并更正了我的用词，这一条我完全接受**：

> 「INTACT-looking」不准确：墓碑是 **0 事件**，见证是 **17**，
> 按**未改的** `CRITERION` 它**并不 INTACT**，只是语法上可解析为空。

**我说的危险描述错了机制。** S7 那天三个测试之所以通过，
不是因为墓碑看起来 INTACT，而是因为**那些测试根本没有应用见证判据**。
判据本身是好的；漏的是调用它的人。

**我判给自己「澄清」，判错了。** 这正是我把它交出去的理由，而它没有白交。

## 3. `THIRD_FIELD_MISSED=YES` —— **提案不构成一个可哈希的块**

两部分，都成立：

```
一  已批准的 R3 profile 仍绑着 RECOMMENDED_CR1_GRAMMAR_SHA256=c251335f…
    我作废了那个哈希，却没说该绑定如何更新，也没给出新的完整 canonical bytes、
    新 SHA-256、或 profile 绑定结果
二  我的「未改字段」复述漏了原块 8 个字段：
    SHORT_ID · TOKEN · ROW_CLASS · ACTOR · TERMINAL ·
    INCIDENT_REQUIRED · PERMITTED_PREDECESSOR · PERMITTED_SUCCESSOR
```

**后果**：当前文本**不能唯一形成**一个可按 §D.10.3 批准的替代块。
换句话说，我交出去的不是一个可以被批准的东西。

**而我在包里点名请他攻的正是「两处，且只有两处」这句声称。**
它被证伪了，方向出乎我意料：不是第三个**语义**字段要改，
而是**块本身不完整，根本没有可批准的产物**。

## 4. `N1_BOUNDARY=FAIL`

席位实测：**N1 的父提交没有 `ops/TRIAL_REGISTRY.md`（exit 128）；N1 才首次加入它。**
我复现一致。

所以我写的「rows appended **at or after** N1」在**恰好 N1** 这一情形上无法成立：
registry 仓里 N1 的 preceding commit 取不到前像；
而随 N1 迁入的那些旧行属于旧仓历史。

**订正（v2 采用，并请席位复核）**：

```
N1 本身没有追加任何 CR1 行 —— 它搬文件，不写行（迁移时 CR1 行数为 0，实测）
所以正确的分界是：
  registry 仓：严格在 N1 之后追加的行
  框架仓    ：O0 及更早的行
「at or after」制造了一个不存在却无法解析的情形；「strictly after」不制造
```

---

## 5. 一条陈旧数字 —— **而它出在我为防止陈旧数字而造的守卫上**

包里 §2 写 `test_registry_boundary.py` 预期 `14 passed`，席位实测 **18**。

根因不是数字过期，是**我的计数器本身错**：

```
该文件有一个 @pytest.mark.parametrize，argvalues 是名字 _REFUSAL_STUBS（5 条）
我的 AST 把它数成 1 个函数；pytest 收集 5 个用例
14 − 1 + 5 = 18   分毫不差
```

而 `collected_tests` 的 docstring 写着
「**How many tests pytest would collect**」——**那句声称比代码宽**。
守卫因此不认为 14 有问题：它不是过期，是错的，而守卫看不出区别。

**处置（已落地）**：

```
新增 Uncountable   argvalues 不是字面量时 RAISE，而不是少数
                   —— 「我看不了」绝不能读成「没有」，这条规矩本仓到处都在用，
                      而它在这个守卫内部塌掉了
字面量列表         按长度相乘（test_dr2_vol_regime.py 因此从 29 改为 38 = pytest 实测）
拆成两个函数       defined_tests（数定义）· collected_tests（数用例）
                   —— 缩进那条独立推导看不见用例，继续拿它和用例数比，
                      会让两条都对的文件互相报错
stale_claims       遇到 Uncountable 逐条点名，并明说「送了 14 给审查席而实为 18」
```

---

## 6. 处置总结

```
R4 提案            作废现文本，起草 v2
v2 必须            ① 分开「发现」与「验证」，把仓移动残留写明
                   ② 那句话按「仓选择判据」定位，并改掉 INTACT-looking 的错误用词
                   ③ 给出完整 canonical 块（含遗漏的 8 个字段）＋ 新 SHA-256
                      ＋ R3 profile 绑定如何更新
                   ④ 分界改「strictly after N1」，并写明 N1 未追加任何行
冻结令             仍在 force —— CR1 行数 0
是否触发证伪器      **由席位与 Aaron 判，不由我判**
```
