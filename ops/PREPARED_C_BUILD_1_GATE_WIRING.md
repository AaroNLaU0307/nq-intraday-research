# C_BUILD_1 三道门的接线 —— 已写好，待第 3 轮复审返回后落地

```
STATUS      = PREPARED_NOT_APPLIED
PATCH       = ops/PREPARED_C_BUILD_1_GATE_WIRING.patch（106 行）
TARGET      = src/itsf/mc/supplement_runner.py
BLOCKED_BY  = ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND3.md（DELIVERY_STATUS=ISSUED）
UNBLOCKS_ON = 该轮 RETURNED，且其条目从 ops/ARTIFACTS_UNDER_REVIEW.json 移除
```

## 1. 为什么写好了却不落地

`src/itsf/mc/supplement_runner.py` 此刻被 fresh Sol 持有，
pin `446ebd4bf51dc797…`，review_id `c-build-2-wording-r3`，**状态仍是 ISSUED**。

传输规则要求接收方**先重算哈希再干活，不匹配就 STOP**。我改了这个文件，
它的哈希会变成 `981d098819f340b4…` —— Sol 回来复核时会 STOP，
**那一轮席位白烧**。席位不会再生，这是这里最贵的东西。

而且不是"碰巧同一个文件"：我的改动**包含 `_g_seal_staging_partial`**，
正是这一轮在审的那段措辞。

`tests/test_artifacts_under_review_are_frozen.py` 在提交前抓到了它。
**这就是那个冻结登记册存在的理由**，它按设计工作了。

**排序教训**：动文件**之前**查 `ops/ARTIFACTS_UNDER_REVIEW.json`，不是之后。
守卫抓到是兜底，不是流程。

## 2. 这个授权是真的（不是我在自我放行）

`ops/OWNER_DECISIONS_2026-08-29.md:170`，Aaron 本人裁定：

> **因此 builder 现在可以越过 `BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`**：
> 把 C_BUILD 五道门从「无条件拒绝」建成真的分类器，
> 而 `assert_real_run_allowed`、目录创建、registry 追加、P2 **全部继续拒绝**。
>
> 这是本记录最重要的一条后果……**建代码不等于跑代码。**

**另订正一条我自己的过期记录**：我一直记着「`supplement_runner.py` 冻结，
门接不了线」。**该文件从来不在 `guards.FROZEN_HASHES` 里** ——
冻的只有 `PROJECT_CHARTER.md`、`STUDY_0_PREREGISTRATION.md`、
`purchase_plan.yaml`、`MC_METHOD_SPEC.md` 和三份 gate1 件。
挡住接线的一直是 `BUILD_SCOPE`，而它 08-29 已解除。
**我因为一条过期的记忆少干了活。**

## 3. 补丁做了什么

| 改动 | 内容 |
|---|---|
| `GateContext` | 新增 `c_build_outcome: object \| None = None` |
| `_classify_c_build_1(ctx, gate)` | 新增共用函数：三道 C_BUILD_1 门的**全部**函数体 |
| `_g_row_schema_blind` / `_g_day_set_exact` / `_g_rows_digest_recompute` | 从无条件拒绝改为调用上面那个分类器 |
| `_g_seal_staging_partial` | **仍拒绝**，但说明改为真实理由（见下） |
| `_g_archive_policy_a` | **仍拒绝**，注明 Router B 拥有其结局 |

### 门只分类，不复查

R3 §3 门教条：门分类调用的**结局**，不观测调用内部，不实现第二份不变量。
`day_strata_rows` 执行不变量并给出码，`day_strata_classify` 把码映到唯一一道门，
门只负责用 F1/F2 词表把它报出来。**在门里再查一遍行**，就是把 R2 的缺陷
换个地方再犯一次 —— 两份同一不变量的实现，第一次改动就开始分叉。

### 缺席是拒绝，不是通过

`c_build_outcome is None` 时门**拒绝**。通过的话，就是把
「未发现缺陷」记到一次**根本没跑过的构建**头上。

这与 `day_strata_failure.p3_boundary` 拒绝中毒链是同一个方向，
也是同一个道理：**写出假话不需要犯错，只需要让一个字段空着。**

### 另两道门为什么不接（各有理由，都不是"还没来得及"）

- **`seal_staging_partial`（C_BUILD_2）**：① 这条路径上什么都不会被封印；
  ② **它的措辞正在外审**。R2 当初被 HOLD，正是因为把一条「零副作用」规则
  横跨三个检查点断言，而 C_BUILD_2 就是打破它的那个 —— staging 在能验证
  `.partial` **之前**就已经写了它。规范未定就接线，是在流沙上盖房子。
- **`archive_policy_a`（C_BUILD_3）**：它**根本不该**变成普通分类器。
  `ROUTER_OF` 把它的结局给了路由器 B；当普通门路由会经 Router A 到 F2，
  而已批准的 `ND1_ARCHIVE_FAILURE_POLICY=A` 要求 A1。
  `test_routing_it_as_an_ordinary_gate_contradicts_policy_a` **执行**这个矛盾。
  接线就是把它重新制造一遍。

## 4. 落地时要一起做的（补丁本身不含）

应用补丁后这三条会变红，**都是我写的绊线按设计触发**，不得删除：

```
test_day_strata_context.py::test_c_build_reads_nothing_from_the_context_today
test_day_strata_context.py::test_so_the_completeness_check_is_vacuous_for_it
test_day_strata_context.py::test_and_the_gates_are_still_stubs
```

它们的 docstring 已写明该怎么办：
「The assertion below goes RED the moment the gates are wired —— which is
exactly when someone should look at whether the assembler supplies what
they started reading.」

所以落地清单是：

1. 应用补丁
2. 三条绊线改为活形式（`required_fields("C_BUILD")` 现在返回 `{"c_build_outcome"}`）
3. `day_strata_context` 增加一个供给该字段的 C_BUILD 上下文装配器
4. 变异证明：缺席通过、门交叉分类、分类器复查行
5. 全量套件
