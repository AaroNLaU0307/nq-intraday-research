# 两份决裁席裁定（生效）—— 边界与迁移

```
RECORD_TYPE=RULING
REVIEW_IDS=dec-scope-boundary-2026-08-27 · dec-registry-migration-2026-08-27
SEAT=Fable 5，各自 fresh top-level session，READ_ONLY，零文件修改
DELEGATED=YES —— Aaron 2026-08-27「给我决策的部分一律让 fable 替我选择，我同意」
ADOPTED_BY_AARON=2026-08-27「可以 直接做」
TRANSPORT_PRECHECK=PASS（两份各自逐条重算哈希）
L6_GATE_EFFECT=NONE —— 不释放任何 transition，不闭任何维护窗，不授权任何迁移
```

## 裁定

| 件 | 裁定 | 置信 |
|---|---|---|
| 边界①R3 骨架可建范围 | **NARROW** | HIGH |
| 边界②`save_dir` 合同 | **BOTH**（词法层 ＋ 渲染层） | 方向 HIGH／机制 MEDIUM |
| 迁移·路线 | **A** —— 目标位置本身做成 git 仓 | HIGH |
| 迁移·不变量 | 六条全采纳（第 4 条改）＋ 增补 7–10 | HIGH |

---

## 1. builder 的审核 —— 八条可证伪断言逐条复现，无一虚报

**这是本记录存在的第一个理由**：两份裁定都不是被采信的，是被核过的。

| 断言 | 结论 |
|---|---|
| `_read_text` 对缺失文件返回空串 | **属实**，且后果比它说的更准（见 §3） |
| 失败模型边界 (3) 要求追加与 `git commit` 同一步骤 | **逐字属实** |
| 仲裁顺序「git 历史 > 见证 > 工作区」 | **逐字属实** |
| §5.2 恢复取证用 `git log -p -- ops/TRIAL_REGISTRY.md` | **逐字属实** |
| §6 写「迁出同步树是结构性关死该窗口的唯一办法」 | **逐字属实**（它用 builder 自己的文档拒了 builder 给的选项 C） |
| `realpath("OPS/packets")` 返回规范大小写 | **实测成立**——它标 MEDIUM 是对的（平台相关），但在本机可行 |
| 收尾句不是四件中任何一件的正式 RULING，无自己的 REASONS/FALSIFIER | **属实** |
| R3 §6 逐字承接 Sol 最小解阻条件 3 第二分支 | **属实**（R3 第 11、34、247 行） |

---

## 2. 边界① NARROW —— 它给的理由比 builder 的强

builder 把这件事框成「两种读法都说得通，取限制性的」。**决裁席给了一条决定性的**：

> 若把收尾句读成对差额三样的授权，`dec-four-owner` 内部即相抵（§4「运行时那一半
> 不可建」＋§9「八项全 NO」）；读成松散转述，全文自洽。**Aaron 追认的是整份裁定，
> 而整份裁定只有一种自洽读法。追认一对互相矛盾的句子，不产生其中较宽那句的独立效力。**

**不是二选一，是其中一种会让被追认的对象自相矛盾。**

它的第 4 条理由同样扎：「摘要句拉伸」正是**同一个维护窗里刚付过学费的形态**——
D-4 的「the rendering sites」差点漏掉 `header.py:201`，而 R2 的处置是显式 EXTENSION、
拒绝追溯读法（`MAINTENANCE_WINDOW_2` 第 107 行逐字 `stretch later`）。

**并指出 builder 文档的一个真缺口**：R3 §6 的机械判据是 AST 可达性（registry 写
调用），**而封存／归档是磁盘写、不是 registry 调用**——那条判据对 WIDE 根本不够。
是 builder 自己写的判据，builder 自己没发现它覆盖不了自己列的三样。

---

## 3. 迁移 —— 它找到的比 builder 多

### 放大：git 依赖不止在 CR1 语法块

builder 只找到 `c251335f…` 里的两句。**决裁席核出 `REGISTRY_SYNC_FAILURE_MODEL.md`
的边界 (3)（现行有效）同样依赖 git**：追加与 `git commit` 属同一操作步骤、仲裁顺序
git 历史居首、恢复程序取证用 `git log -p`。

**裸迁出 git 会同时废掉一条已裁定生效的边界与恢复程序，不只是一个语法字段。**
这让路线 B 的真实代价远高于 builder 估的，并直接支撑了拒 B。

### 不变量 8 找到一个 builder 没找到的活缺陷

**实测确认，且后果比它描述的更准**：

```
_read_text 对不存在的文件返回 ""
缺失 registry      -> "no supplement event chain exists ... NOT AUTHORIZED"
真 registry 无该链  -> 逐字相同的字符串
两者可区分: False
```

**迁移后一个路径笔误会伪装成「还没授权」，且不可区分。** 它归类为「把崩溃说成
未授权」的同型缺陷——准确。

---

## 4. builder 执行时发现的三件，两份裁定都没有

### ① 不变量 8 单独修不管用

修完 `registry_boundary._read_text` 之后实测：**四处生产站点每一处都带同一个
`else ""` 静默空串，完全绕过边界**。所以不变量 5 与 8 是同一个修法——不收敛，
8 就是个空修。

### ② `consumer.py` 用的是相对路径

`Path("ops/TRIAL_REGISTRY.md")` ——只在进程恰好从仓根启动时才解析得对。
收敛顺带修掉了，**这一处两份裁定都没点到**。

### ③ 裁定说「不可建」的能力已经在树里，只是未接线

```
supplement_production.build_supplement_from_authority   存在，调用 hermetic 核心
   —— 自陈「从已封存 S0 输入到已封存 supplement 的唯一生产路径」
supplement_runner（C_BUILD 执行路径）                    不 import、不调用
全仓除该模块自身外                                        零处调用
```

**NARROW 今天靠「没接线」满足，不是靠「能力不存在」。** 详见
`ops/RULING_FABLE_FOUR_OWNER_2026-08-27.md` §11 的如实更正。

---

## 5. builder 已执行 / 未执行

**已执行（四项，全部变异证红）**：

```
不变量 8       缺失即拒（BoundaryError）                     3 红
不变量 5       四处路径构造收敛到 registry_boundary 一处      3 红（含裁定 Q4 点名的那条）
边界①CONDITIONS 1  C_BUILD 执行路径不得触及 hermetic 核心      1 红
边界①CONDITIONS 3  台账追加（四件裁定记录 §11）                ——
```

全量 4319 passed / 0 failed。**三个生产入口仍全部 gate-first 拒绝**，收敛未削弱它。

**未执行，且不可代做**：

```
① 路线 A 的具体迁移方案包 → fresh Sol 审 → Aaron 亲批（链未走完）
② 新仓的创建（DIRECTORY_CREATION_AUTHORIZED=NO，授权记录件现为零授权）
③ 边界②的渲染层实现 —— 属 qros-runtime 仓，且须整体交第 4 轮 fresh Sol
④ dec-four-owner §8 的五项，P2 签署与 verbatim 句居首
```

---

## 6. 两条必须留给 Aaron 判的披露

### 模型同源性已是三连

`dec-four-owner`、`dec-scope-boundary`、`dec-registry-migration` **全部是 Fable 5**，
三份都自陈了这一点。其中**边界①是同模型会话去收窄同模型会话的措辞**——结果经
builder 复核是对的，但**整条链没有跨家族多样性**。三份都写了「Aaron 应知悉后再追认」。

### 边界②的机制草案出自决裁席自己

> 设计贡献：第 2 件的渲染层机制草案（最深既存祖先的最终拼写比较）出自本席——
> **本席因此对该修法的未来审查不再独立，第 4 轮 Sol 须被告知此来源。**

已写进边界②的 CONDITIONS 第 4 条，第 4 轮提示词须带。

### 路线 A 的弱点，决裁席自陈

> 我选 A 的核心红利是「已批准字节一字不改」，但这是**字面为真、所指已移**——
> `c251335f…` 批准时「git 历史」的默认所指显然是 ITSF 仓，A 把所指换成了一个
> 批准时不存在的仓。……若 Aaron 或 Sol 认为这不够、仍须 R4，我不反对。

**缓解是治理性的，不是机械的**：Aaron 的批准文本必须显式指名新仓为
`COLD_RECOMPUTE` 的所指，使所指变更经过他之手而非默认发生。
