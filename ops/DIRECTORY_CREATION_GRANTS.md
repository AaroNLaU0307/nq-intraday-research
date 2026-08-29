# 目录创建授权 —— 记录件

```
RECORD_TYPE=DIRECTORY_CREATION_GRANTS
APPEND_ONLY=YES —— 只追加，永不编辑、永不重排
CREATED=2026-08-27
BASIS=决裁 dec-four-owner-2026-08-27 第 2 件（Aaron 2026-08-27 采纳）
AUTHORITY=本件记录授权与执行证据。**建立本件不授权任何目录创建。**
GRANTS_RECORDED=0
```

**本文件今天为空，且这不是遗漏。** 决裁席明写「记录件由 builder 建（本席 READ_ONLY
不建）」——它定的是形制，不是任何一次授权。`DIRECTORY_CREATION_AUTHORIZED=NO` 未变。

---

## 1. 一份授权必须有的五个槽（决裁第 2 件，逐槽）

### 来源

**Aaron 具名消息中的主动逐字发送**（`ACTIVE_VERBATIM_SEND`）。先例是 ND1 R3 的
`ops/ND1_PROFILE_RATIFICATION.md` §9.1：builder 呈交块、Aaron 逐字回贴即可。

**「好」「批准」二字不够。**

> **决裁席自陈的置信度分歧**，如实转录：槽形式 HIGH，但「builder 呈交块＋Aaron 逐字
> 回贴」是否够格 **MEDIUM**——「R3 先例支持，但那是 profile 批准而非操作授权；
> 若 Aaron 更愿意亲笔拟句，从严者胜」。
>
> **builder 的建议：取从严者。** 目录创建会改变文件系统状态且不可无痕撤销，而
> profile 批准不改变任何状态。两者的可逆性不同，形制不必相同。

### actor

```
授权   只能是 Aaron
执行   可委托主代理**手工**执行
```

**「模块永不自己创建」永久保持**——生产代码不获得目录创建能力，本条不因任何一次
授权而改变。

执行时须留**门前门后 exact-set 快照证据**，追加进本文件。

### 精确文本

必须逐字，且含**封闭枚举的绝对路径清单**——**不得含通配符**。

**不入 registry。** 现行事件词表没有「目录创建」token，且不为此扩词表：扩词表是
§D.10.3 的 R4 级动作。registry 是 supplement 生命周期的真相源，目录创建是治理运维
动作，链上没有它的位置（P2 的前驱是 `P1|P2S|T1`，插不进也不该插）。

### 绑定

**绑路径，不绑 commit。**

理由（决裁原文）：目录是文件系统状态，不是树状态；`mkdir` 不依赖任何代码字节。
绑 commit 会继承 P2 那个「任何一次提交即作废」的陷阱，换来零安全收益。

### 有效期

**绑事件：用掉即失效。** 一份授权 ＝ 一次创建动作 ＝ 恰好那个封闭清单。执行完毕、
证据落档，授权即死。

**附加的 fail-closed（决裁明列）**：执行时若**清单中任一路径已存在**，
**STOP 上报**，不得以「反正目标态一样」继续。

> 这一条防的是同步残渣造出的幻影目录。L-5 是真实缺陷（2026-08-10 裁定），
> 其机制**会**烧掉一次 trial；**实测：至今没有 trial 被烧掉过**（见
> `ops/CORRECTION_NO_TRIAL_WAS_BURNED_2026-08-27.md`）——
> 那正是 qros-runtime 第二维护窗存在的原因。

---

## 2. FALSIFIER（决裁原文）

> 若门后 exact-set 快照出现清单之外的任何字节，本次授权执行判失败，全部上报，
> **不得清理后重试**。

---

## 3. 当前状态（实测，2026-08-27）

```
C:\Users\Aaron\quant-data\itsf-runs             存在
C:\Users\Aaron\quant-data\itsf-runs-archive     存在
两个根下的 supplements\ 子树                     **都不存在**
DIRECTORY_CREATION_AUTHORIZED=NO
```

`supplement_subtree_absent` 是 A_PRECHECK 的 13 道门之一——子树不存在时它拒绝，
且模块永不自行创建。

**决裁的 CONDITIONS 明写**：两个根下的 `supplements\` 子树**在授权执行前继续保持
不存在**。

---

## 4. 授权台账

| # | ts | 授权文本（逐字） | 封闭路径清单 | 执行者 | 门前快照 | 门后快照 | 状态 |
|---|---|---|---|---|---|---|---|
| 1 | 2026-08-29 | **Aaron 亲笔、主动逐字发送**：「授权在 C:\Users\Aaron\quant-data\itsf-runs\supplements 与 C:\Users\Aaron\quant-data\itsf-runs-archive\supplements 这两条逐字路径上创建目录。」 | 两条，无通配符：`C:\Users\Aaron\quant-data\itsf-runs\supplements` · `C:\Users\Aaron\quant-data\itsf-runs-archive\supplements` | 主代理手工（Opus 5 builder seat） | `DIRGRANT_A1_PRE_GATE_SNAPSHOT.json` sha256 `7345bef75e712ab2ae92e4dbef301025…` —— 19＋15 条目，两目标均**不存在** | `DIRGRANT_A1_POST_GATE_SNAPSHOT.json` sha256 `b20e8ffd2498f40e0c67a3c1e059d711…` —— diff **恰为**两条 `dir supplements`，无增无删无字节，两者均空 | **USED（用掉即失效）** |

### 第 1 行的执行记录

`mkdir()` 调用**不带** `parents=` 与 `exist_ok=` —— 父目录缺失或目标已存在都会直接抛，
这正是决裁 §4 要求的 fail-closed，而不是「反正目标态一样」。

四条 fail-closed 逐条应答：

```
清单中任一路径已存在      -> 执行前重测：两条均 exists=False，未触发
父层被隐式创建            -> 两个治理根执行前实测 is_dir()=True，未发生隐式创建
门后快照出现清单外字节    -> 未出现；added 恰为两条 dir，removed 为空
门前门后 exact-set 快照   -> 本行两列所指的 JSON 是全文，不是摘要；
                            diff 已由两份磁盘文件独立重算一次，不采信执行时的内存判断
```

**一处过程瑕疵，如实记下**：门前快照最初落在项目根而不是 `ops/`，我第一次去挪它时
找错了目录，一度以为它不存在。它完好无损（19＋15 条目，不含 `supplements`），
已归位。记在这里是因为「我的模式没匹配到」被当成「东西不存在」，
在本项目今天已经是第四次。

**这份授权已用掉。** 它绑路径不绑 commit，因此任何 commit 变化都不使它复活，
也不使它扩展到别的路径。第二层（`<supplements>\<id>_<UTC>` 运行时目录）**不在本行覆盖范围内**
—— 见 `ops/SUPPLEMENTS_SUBTREE_GRANT_PREPARATION.md` §2 的甲乙丙三条出路，
Aaron 尚未裁，builder 倾向**乙**（运行时刻查实 UTC 后再签一份封闭清单）。

---

## 5. 本文件不做什么

不授权任何目录创建；不创建任何目录；不追加任何 registry／exposure 行；
不改变八个授权字段中的任何一个。

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

**本件 `APPEND_ONLY=YES`**，故 §3 的原句一字未动 —— 抹掉它既违反追加纪律，
也会掩盖「一份已交付的决裁包携带过它」这个事实。

---

## 订正-ALREADY-RULED-2026-08-30

```
CORRECTION_ID=订正-ALREADY-RULED-2026-08-30
FOUND_BY=Fable 决裁席（顾问级：builder spawn 的子代理，对 builder 不独立）
SEVERITY=流程缺陷，非代码缺陷
```

### 被订正的句子（**原句保留，本件只追加**）

> 第二层（`<supplements>\<id>_<UTC>` 运行时目录）**不在本行覆盖范围内**
> —— 见 `ops/SUPPLEMENTS_SUBTREE_GRANT_PREPARATION.md` §2 的甲乙丙三条出路，
> **Aaron 尚未裁**，builder 倾向**乙**。

**「Aaron 尚未裁」是假的。**

`ops/OWNER_DECISIONS_2026-08-29.md` §5 逐字裁了**乙**：

> 裁定　不由 P2 蕴含（那会正面抵触 ND1「目录创建与执行不得合并」的明令），
> 　　　也不修订命名规则（那要动已批准值）。
> 　　　执行前 builder 把实际 UTC 查实、呈交封闭清单，Aaron 当场签。

同记录 §6 状态表写着「形制已定（乙）」。

### 代价：我把一件已裁事项送进了决裁包

`ops/DECISION_PACKET_FOUR_OPEN_2026-08-29.md` 第 2 件问的正是这条。
**最坏形态**：如果决裁席裁出了不同答案，就会变成**一个 builder spawn 的子席位
静默覆盖 owner 裁定**。它没有 —— 它认出这条已裁并拒绝重裁，那是它的功劳，不是我的。

### 形态

**未经核对的陈述，写在真实事实旁边，读起来一模一样。**
这与 `订正-SUBTREE-GATE-2026-08-29` 同形，也与 Sol 两轮都在打的
「把我列出的当成全部」同形。差别只在这次错的是**治理事实**而不是机制事实。

### 机械化

`tests/test_no_settled_question_is_sent_to_adjudication.py` —— 决裁包里的问题
不得已在 `OWNER_DECISIONS_*` 里被裁过。
