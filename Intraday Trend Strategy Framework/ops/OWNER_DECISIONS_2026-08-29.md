# Aaron 裁定 —— D-3 的五项 UNRESOLVED_FOR_AARON

```ini
RECORD_TYPE=OWNER_DECISION_RECORD
DATE=2026-08-29
DECIDER=Aaron
RECORDED_BY=Opus 5，builder seat（工作会话）
SOURCE=ops/RULING_SOL_D3_HOLD_2026-08-26.md 的 UNRESOLVED_FOR_AARON 五项
FORM=builder 呈交四个带推荐的选项组，Aaron 逐项选择
APPEND_ONLY=YES
```

## 0. 这次裁定的形式，如实记

builder 把五项归并为四组（①②耦合，合为一组），每组给出选项与**明写的推荐**，
Aaron 逐项选择。**四项全部选了 builder 推荐的那一项。**

**这一点必须记下来**：四项都采纳推荐，意味着 builder 的推荐在本次裁定中承重。
若其中任何一条日后被证明是错的，**责任链是「builder 推荐 → Aaron 采纳」，
不是「Aaron 独立判断」。** 记录形式本身是证据的一部分。

---

## 1. 逐项裁定

### ①＋② actor 是否同时表达实际执行者 —— **保持绑定**

```
裁定   取 Sol 的窄解释：运行器存活并捕获到的 A1／F1／F2 仍由运行器追加；
       硬崩溃后的检测与恢复归主代理。
不做   不增加独立 executor provenance 字段；不修订已批准 profile、planner
       或 S0 生产先例。
```

**builder 呈交的理由（Aaron 据以采纳）**：Sol 实测已批准工件事实上把 actor 与
执行者绑定了——`supplement_contract.py:238` 把 P3 指给 runner，`:246` 起
A1／F1／F2 同样指 `main agent (mc_ds_runner)`，`supplement_runner.py:648` 的
`plan_failure_event` 又硬编码 runner。加独立字段是 schema 变更，须走修正案；
而本项目 A2 永久 HOLD，使任何设计修正案都没有可满足的前置门。

**Sol 的原话（本次复审最有价值的一段，逐字）**：

> 不能在不修订合同的情况下让主代理写行却仍标称 runner。**较窄且与现有合同一致的
> 解释是：运行器存活并捕获到的 A1/F1/F2 仍由运行器追加；硬崩溃后的检测／恢复由
> 主代理负责，并使用 Aaron 批准的独立恢复语义。**

### ③ P3 之后硬崩溃 —— **主代理追加，每次恢复写入需 Aaron 一次性授权**

```
裁定   恢复事件由主代理追加。
       **每一次恢复写入都需要 Aaron 单独的一次性授权**，不是一次总授权。
形态   fail-closed。恢复写入不是常规写入。
```

**未由本裁定解决的**：Sol finding 3 列出的整套状态机仍未定义——租约取得、持有
范围、所有合法写者、崩溃释放、PID／时钟失效、恢复事件词表，以及 P3 后无终止行时
下一次 bootstrap 的精确拒绝条件。**本裁定只定了「谁写、凭什么授权」两件。**

### ④ OneDrive canonical 写入面 —— **批准有界运行封套 ＋ 机械绊线**

```
裁定   registry 可以继续在当前 OneDrive 树中作为 canonical 写入面，
       但仅在下列封套内，且绊线一旦触发即 STOP。
依据   builder 2026-08-29 复测：仓根无 ReparsePoint；
       Offline/ReparsePoint 文件数 0；OneDrive 冲突副本数 0；
       OneDrive 进程未运行。
绊线   OneDrive 进程启动，或出现任何冲突副本 -> STOP，不得继续 canonical 写入。
持久解 迁移仍是持久解，本裁定不取消它，只是不让它阻断当下。
```

**明写这个封套建立在什么之上**：一次**当下的**测量。休眠可以终止而
Desktop 仍是 OneDrive 重定向——这一点在
`ops/OWNER_DECISIONS_2026-08-27.md` §1 已记为实测事实。
**因此绊线不是装饰，它是这条裁定成立的条件。**

### ⑤ 租约回收 —— **fail-closed，等人工裁定**

```
裁定   租约回收不得自动执行。
理由   自动回收正是会静默做错事的那一类；且今天根本没有租约机制，
       fail-closed 也是代码现在的行为。
```

---

## 2. 本裁定**不**授权什么

```
不解除 D-3 条件 3   生产代码仍不得获得任何 registry 写能力，
                    直至 fresh Sol PASS ＋ Aaron 授权
不给   目录创建授权（两个 supplements\ 子树仍不存在，且必须保持不存在）
不给   registry 追加授权
不给   P2 执行授权
不给   真实数据读取
不改   样本／标签／NA 政策／成本／Primary／Oracle／feasibility／运行定义
不释放 任何 gate。A2->B 与 I->J 仍 HOLD；F->L 仍因 materiality UNKNOWN 而 HOLD
```

## 3. 对 N09 §7 的影响 —— **四项里定了一项半**

`ops/N09_EXECUTION_PATH_DESIGN_R3.md` §7「越过骨架需要什么」列四项：

| # | 内容 | 本裁定后 |
|---|---|---|
| 1 | P3 与失败事件的写者是谁 | **半定**：失败事件已定（①②③）；**P3 的写者未定** |
| 2 | 目录创建授权（四个槽） | 未给 |
| 3 | D-3 的五项 | **已定** |
| 4 | N09 的 P2 | 未给 |

设计原文：「它们定了，骨架的拒绝出口才**逐个**打开」。
**因此本裁定单独不打开任何出口。** 第 1 项的另一半与第 2 项定了之后，
builder 才能越过 `BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`。

### 第 1 项剩下的那一半，精确是什么

已批准 actor 表把 **P3** 指给 runner（`supplement_contract.py:238`），
而全局边界 4 写「只有主代理写 registry」。**两者相抵，且本次四问没有问到 P3。**

builder 不代裁。它与 ①② 同形，但**不能由 ①② 推出来**——
①② 处理的是 A1／F1／F2（失败与归档事件），P3 是封存事件，是链上的不同位置。

## 4. 下一步

```
Aaron   裁 §7 第 1 项的另一半（P3 的写者）
Aaron   给 supplements\ 子树的目录创建授权（四个槽，builder 已备准备件）
builder 越过骨架，把 C_BUILD 五道门建成真的分类器
fresh Sol  复审（D-3 条件 3 要求）
Aaron   registry 追加授权 -> P1 -> P2 -> 真跑
```

---

## 5. 追加裁定（同日，第二组两问）

### §7 第 1 项剩下的那一半 —— **P3 由运行器追加**

```
裁定   已批准 actor 表把 P3 指给 runner（supplement_contract.py:238），照此执行。
形态   与 ①② 同一套窄解释：已批准 actor 表怎么写就怎么执行，零合同修订。
代价   **全局边界 4「只有主代理写 registry」需要一条明写的例外**：
       P3 由运行器写。这条例外必须被记录，不能靠沉默。
```

**至此 §7 第 1 项全部定完**：失败事件（运行器存活时归运行器，硬崩溃后归主代理
且每次单授权）＋ 封存事件 P3（运行器）。

### 每次运行的 `<id>_<UTC>` 目录 —— **乙：运行时刻再签一份**

```
裁定   不由 P2 蕴含（那会正面抵触 ND1「目录创建与执行不得合并」的明令），
       也不修订命名规则（那要动已批准值）。
       执行前 builder 把实际 UTC 查实、呈交封闭清单，Aaron 当场签。
代价   Aaron 必须在运行那一刻在场（几分钟）。
```

---

## 6. §7 四项的现状 —— **设计侧全通，运行侧仍缺两条授权**

| # | 内容 | 状态 |
|---|---|---|
| 1 | P3 与失败事件的写者 | **✅ 全部定完**（本记录 §1 与 §5） |
| 2 | 目录创建授权 | **形制已定（乙），但父层那一份授权仍未给** |
| 3 | D-3 的五项 | **✅**（本记录 §1） |
| 4 | N09 的 P2 | 未给 |

**第 1、3 项是设计侧的阻断项，两项都已解除。** 第 2、4 项是运行侧的。

**因此 builder 现在可以越过 `BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`**：
把 C_BUILD 五道门从「无条件拒绝」建成真的分类器，
而 `assert_real_run_allowed`、目录创建、registry 追加、P2 **全部继续拒绝**。

**这是本记录最重要的一条后果，也是它与 §2「本裁定不授权什么」并存的原因**：
建代码不等于跑代码。
