# Aaron 手上四件 —— 决裁席裁定（生效）

```
RECORD_TYPE=RULING
REVIEW_ID=dec-four-owner-2026-08-27
SEAT=Fable 5，决裁席，fresh top-level session
DELEGATED=YES —— Aaron 2026-08-27「我手上的四件可以和 fable 商量提案，我会同意它推荐的方式去做」
ADOPTED_BY_AARON=2026-08-27「这是fable结果 我同意，继续推进」
TRANSPORT_PRECHECK=PASS（四件哈希与字节数逐字匹配）
SEAT_STATUS=BLIND（零检索；但见 §6 的两条独立性披露）
L6_GATE_EFFECT=NONE —— 不释放任何 transition，不是研究授权，不是运行授权
```

## 裁定摘要

| 件 | 裁定 | 置信 |
|---|---|---|
| **1** P3／失败事件的写者 | 采纳窄读法；**executor provenance 成文化，不加新字段** | HIGH |
| **2** 目录创建授权 | 五槽定形；绑路径不绑 commit；用掉即失效 | HIGH（形式）／MEDIUM（来源形制） |
| **3** D-3 五项 | 逐项裁；**#4 分两相**；三项可代裁，两项不可 | #1/#2/#3/#5 HIGH，**#4 MEDIUM** |
| **4** P2 排序与 P1 路径 | P2 排最后；P1 走主代理手工，范围化授权 | HIGH |

---

## 1. builder 跑了裁定自己的 FALSIFIER —— 不触发

第 1 件的 FALSIFIER（原文）：

> 打开 `supplement_contract.py` 若发现 P3/A1/F1/F2 的 actor 字符串**不是**
> `role (executor)` 形（例如裸 `runner`），则「成文化既存约定」失去基础。

**实测：四个全是 `main agent (mc_ds_runner)`，`role (executor)` 形成立。**
裁定基础成立，已由 `tests/test_executor_provenance.py` 持续钉住。

## 2. 但裁定的措辞与它自己的模型不一致 —— builder 按模型实施，不按字面

§1.3 要求 **`actor = main agent (<实际执行进程>)`**。**照字面写校验器会拒掉
15 个事件里的 9 个**：

```
带括号（5）  P3 P4 A1 F1 F2       main agent (mc_ds_runner)
裸 role（6） P1 A2 AX CR1 F3 T1   main agent
占位符（2）  P5 F2v               <verifier>
择一（1）    P2S                  Aaron|main agent
owner（1）   P2                   Aaron
```

**而同一份裁定的 `CROSS_ITEM_CONSISTENCY` 给的是两类模型**：

> 执行者二分——治理时＝主代理手工，运行时＝存活运行器

**实测：这个划分精确成立。** 带括号的集合 `{P3,P4,A1,F1,F2}` 恰好等于运行时事件；
裸 role 的 `{P1,A2,AX,CR1,F3,T1}` 恰好等于治理时事件。

**所以实施的是两类模型（它自己的 CROSS_ITEM_CONSISTENCY），不是 §1.3 的单一形式。**
`actor_form()` 分五形并 fail-closed，`executor_of()` 取括号内的执行进程。

## 3. 第 1 件为什么消解了那个矛盾

已批准 actor 表把 A1/F1/F2 派给 `main agent (mc_ds_runner)`，全局边界 4 说
「只有主代理写 registry」。**读成一句话它们相抵，读成两句话就不抵**：

```
边界 4      说的是所有权   —— 每个 writer 都是主代理拥有的
括号里      说的是执行进程 —— 谁的进程实际写下这一行
```

**约定本来就在每一个 actor 字符串里，只是从没写下来。** 因此**没有任何已批准字节
需要修改**——这正是选这个读法的最大红利，也是第 3 件 #2「保留，一字不改」的依据。

**「运行器存活」由谁判定**（裁定的回答）：**不需要任何人在写入时判定，它由追加行为
本身回溯证成。** 死进程追加不了任何东西：registry 尾部若存在运行器署名的终止事件，
运行器当时必然存活；P3 之后无终止行即推定崩溃，进入 CR1 路径。

**「崩溃的进程无法自陈崩溃」只在你要求运行器写自己的讣告时才是矛盾**——CR1 不是
讣告，是**对缺失终止行的裁定事件**，其 `actor=main agent` 与窄读法同向。
`test_cr1_is_governance_not_runtime` 钉住这一点。

## 4. 仍在 force 的（裁定明写，builder 复核成立）

- **不解除 D-3 HOLD 条件 3。** 窄读法的运行时那一半（运行器真的追加）在临界区／
  单写不变量／torn-line 处置建成并经 fresh Sol PASS ＋ Aaron 授权之前仍不可建。
- bootstrap 必须把**畸形尾行**（半写）与「无终止行」同等处置为 **INDETERMINATE →
  停机上交**，不得自动归入 F2。
- 若成文化需触碰已批准 profile 字节，走 §D.10.3 出 R4。**builder 复核：不需要**
  ——actor 字符串在代码里，profile 只写 `GRAMMAR_*=ADOPT_AS_WRITTEN`，未触碰。

## 5. 第 3 件 #4 —— OneDrive canonical 写入面，分两相

```
现相   全部追加皆为主代理手工时，容忍 OneDrive canonical，
       但每次手工追加必须配套：追加前后冲突副本扫描（*-<机器名>* 等）
       ＋ 追加后逐字节读回核对
迁移相 在任何生产代码运行时追加能力被启用之前，canonical registry
       必须迁出主动同步树（候选：C:\Users\Aaron\quant-data\ 治理根之下）
```

**方向已裁；具体迁移方案须单独出包、经 fresh Sol 审后由 Aaron 亲批——迁移的执行
不可代裁。**

**FALSIFIER**：现相的容忍以「零事故」为前提。手工追加阶段一旦检出任何冲突副本或
torn line，现相裁定即被证伪，立即升级为「迁移先行、追加冻结」。

## 6. 决裁席自陈的两条独立性缺口 —— **Aaron 应知悉后再追认第 1 件**

裁定原文，逐字要点：

> **模型同源性**：D-3 被 HOLD 的原提案出自**另一个 Fable 会话**；本席与其**同模型
> 不同会话**，而第 1 件裁定**部分采纳了那份提案**与已批准 actor 表一致的那一半。
> 此模型同源性已如实标出，**Aaron 应知悉后再追认第 1 件**。

> **持久记忆通道**：本席位的持久记忆索引在会话启动时注入了 ITSF 项目脉络
> （HEAD、Aaron 既往裁定、节点状态），其中**不含**任何还原内容——**但这是一条
> fresh 会话之外的既存信息通道**，应记录在案由 Aaron 判定是否影响席位定性。

**builder 不代 Aaron 判定这两条。** 它们如实转录于此，是本记录存在的理由之一。

## 7. 决裁席自陈的最弱处（逐字）

> **第 3 件 #4 的「现相容忍」。** 本项目已经因云同步残渣烧过一次 trial，而 Sol F5
> 明确说审阅范围内**没有证据**表明半写与冲突副本可被可靠检出——我开出的缓解
> （读回核对＋冲突副本扫描）是 builder 形状的控制，**在本仓从未被测试过**。
> 怀疑者可以正当地说：我为了不让迁移成本挡住 P1→P2 链条，对一个**已经兑现过的
> 风险**给了过轻的处置。……但若 Aaron 愿意付迁移成本，**「迁移先行」是更保守且
> 我不会反对的替代裁定**。

## 8. `STILL_AARON_ONLY`（裁定原文，五项）

```
① P2 的签署与 verbatim_authorization_sentence —— 绝对保留，任何席位代拟即失格
② 第 2、4 件里每一份范围化授权的实际签发（本裁定只定形制）
③ 每一次 CR1 追加的逐事件授权
④ registry 迁移方案的批准与执行
⑤ 若 executor 成文化需 R4，R4 的批准（builder 复核：不需要）
```

## 9. builder 已执行 / 未执行

**已执行**：第 1 件的成文化（`actor_form` / `executor_of` ＋ 8 项守卫、3 条变异
证红）；第 2 件的记录件 `ops/DIRECTORY_CREATION_GRANTS.md`（**空，
`GRANTS_RECORDED=0`**，建立它不授权任何创建）。

**未执行，且不可代做**：§8 的五项；第 3 件 #4 的迁移；第 4 件的七步序中属 Aaron 的
每一步。**八个授权字段仍全部为 `NO`。**

## 10. 裁定的收尾句 —— 它解锁了一步 builder 的活，但边界有歧义

原文逐字：

> 后续机械路径：Aaron 追认（或改裁）→ builder 按第 1 件把 R3 骨架从
> `DEFAULT_REFUSE_SCAFFOLD_ONLY` 扩到「除 registry 写出口外全部可建」→
> 其余按第 4 件的七步序走，P2 仍然最后、仍然只能是 Aaron 的话。

Aaron 已追认，所以这一步已授权。**但「除 registry 写出口外全部可建」比 R3 §6 宽**：

```
R3 §6 的不可建   任何能让结构真的产出行、真的封存、真的归档、真的追加 P3 的能力
裁定收尾句的不可建 registry 写出口
```

**两者的差是「产出行／封存／归档」这三样。** 照 R3 §6 它们不可建；照收尾句它们可建。

**builder 取限制性读法并只建两者的交集**——即 R3 §1–§5 的结构层
（checkpoint 分派、`ROUTER_OF`、两个路由器矩阵、structural-only 调用图的 AST 守卫、
precheck 证据规则），**不建行生产、不建封存、不建归档、不建任何 registry 写出口**。

**这个差额作为开放项交下一轮决裁**（`ops/DECISION_PACKET_SCOPE_AND_BOUNDARY.md`）。
理由：两种读法都说得通，而「中间态」正是第六轮 HOLD 的 Finding 1 形态——
builder 不自行选一种读法然后建到一半。

**第 1 件的 CONDITIONS 在两种读法下都成立且未变**：运行时那一半（运行器真的追加）
在临界区／单写不变量／torn-line 处置建成并经 fresh Sol PASS ＋ Aaron 授权之前不可建。

---

## 11. 收尾句被后续裁定澄清为 NARROW（CONDITIONS 3 要求的追加）

```
CLARIFIED_BY=dec-scope-boundary-2026-08-27 第 1 件，RULING=NARROW
ADOPTED_BY_AARON=2026-08-27
```

§10 标出的那个差额（行生产／封存／归档）**已裁为不可建**。决裁席给的决定性理由
不是「两种读法都说得通、选保守的」，而是更强的一条：

> 若把收尾句读成对差额三样的授权，裁定内部即相抵（§4「运行时那一半不可建」
> ＋ §9「八项全 NO」）；读成松散转述，全文自洽。**Aaron 追认的是整份裁定，
> 而整份裁定只有一种自洽读法。追认一对互相矛盾的句子，不产生其中较宽那句的
> 独立效力。**

**并指出 builder 文档里一个真缺口**：R3 §6 给的机械判据是 AST 可达性（registry 写
调用），**而封存／归档是磁盘写、不是 registry 调用**——那条判据对 WIDE 根本不够。
是 builder 自己写的判据，builder 自己没发现它覆盖不了自己列的三样。

### builder 执行 CONDITIONS 1 时的一条如实更正

CONDITIONS 1 的原话是「`_test_only` hermetic 核心**保持现状**」。
**builder 实测的「现状」与该措辞可能暗示的不同，如实记录**：

```
supplement_production.build_supplement_from_authority   存在，且调用 hermetic 核心
   —— 自陈「从已封存 S0 输入到已封存 supplement 的唯一生产路径」
supplement_runner（C_BUILD 执行路径）                    不 import、不调用它
全仓除该模块自身外                                        零处调用
```

**所以 WIDE 的能力已经在树里，只是未接线**——与 `registry_witness.py` 同一形态：
写好了、正确、**故意没接线**。

NARROW 今天靠「没接线」满足，**不是靠「能力不存在」**。两者在今天等价，但若决裁席
是按后者裁的，其理由基础与实际不同。**结论不受影响**（NARROW 仍成立，且这个事实
让它更该成立），但下一份决裁包须带上此更正。

守卫钉的正是这一点：`test_the_execution_path_does_not_reach_the_hermetic_core`
——**接线必须打红，而不是静默通过**。变异实测：把核心接进 runner ⇒ 红。

---

## 12. §7 与 §5 所依据的一个前提，builder 事后查出是夸大的

**§7 转录的决裁席原话一字未改，也不得改**——转录不因转录者事后发现前提有误而被改写。

但那段话里的「本项目已经因云同步残渣烧过一次 trial」与「已经兑现过的风险」，
**其事实基础来自 builder 写进决裁包的一句错话**。实测：

```
ops/TRIAL_REGISTRY.md 中 BURNED / ABORTED / VOID 事件数    0
S0-T001                                                   成功封存
```

L-5 是真实**缺陷**，R5 是真实**事故**，而「烧掉一次 trial」是缺陷的**机制**
（`D3_REGISTRY_WRITER_PROPOSAL` §2.4 原文用的是「**会让**」）。

**这削弱了拒绝路线 C 的力度**，也改变了 §7 自陈弱点的分量。
全文见 `ops/CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md`。
