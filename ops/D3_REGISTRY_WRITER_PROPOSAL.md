# D-3 提案 —— 谁向 registry 追加 P3 与失败事件

```
RECORD_TYPE=PROPOSAL_FOR_RATIFICATION
ITEM_ID=D-3
STATUS=提案，第一步／共三步。**不释放任何门，不授权任何写入。**
PROPOSED_BY=Fable 5（决裁席，2026-08-26），`DELEGATED=YES`
NEXT=fresh Sol 批准或修改 → Aaron 终裁
OUTCOME_CLEAN=是（机械扫描；本件永不进入 carries_outcome）
```

> **本件为什么单独存在。** Fable 的裁决全文
> （`ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md`）**是隔离件** —— 它自身复述了一个
> 被隔离的数值，转录时即登记。**复审席位不得打开它。** 本件是其中 D-3 一节的
> outcome-clean 可读副本，经同一台扫描器验证干净，并补上 builder 的独立复核。
>
> 起点、禁区与检索禁令见 `ops/RECOVERY_ANCHOR.md`。

---

## 一、被提议的裁定（Fable 原文，逐字）

```
RULING=C（分开裁），且本裁定整体只是三步中的第一步（Fable 提案），非终裁。
  · P3：运行器自行追加（A 形），依「受托单写」限缩解释——边界第 4 条的
    「主代理单写」读作「同一时刻恰一个写者，在主代理权限下，每次追加可追溯到
    主代理发起的动作」。运行器在 run 期间持显式写者租约、事件词表受限（仅获授
    类型）、schema 校验、追加后不再重读。理由：P3 是暴露消耗点，记录必须与不可
    逆动作原子耦合；B 的人工介入窗口本身是风险。scripts/s0_real_run.py 的
    RUN_STARTED 先例据此被规整为合规，不回溯拆除。
  · 失败事件：仅主代理追加（B 形）。plan_failure_event 保持只规划不写；运行器
    永不写自己的讣告——失败观察者必须在失败后存活，编排器做不到。缺失终止事件
    由下次 bootstrap fail-closed 检出；该检出机制必须存在并有测试，若无则属本
    提案的建造义务。
CONDITIONS=
  1. 流程走满：本提案 → fresh Sol 批准 → Aaron 裁决。
  2. Sol 审查必须专门猎取四点（见本件 §三）。
  3. Sol PASS ＋ Aaron 授权之前，生产代码不得获得任何 registry 写能力。
FALSIFIER=任一观察到的双写者交错；或一次跨越 P3 的运行未留 registry 行且下次
  bootstrap 未标红 ⇒ 受托单写构造不安全，回落 B 并接受介入窗口。
```

**背景冲突**：两份已批准文本相抵。全局边界第 4 条写 registry「只允许主代理
单写」；而 `scripts/s0_real_run.py` 在**已完成的真实 S0 运行**中由运行器自己
追加了 `RUN_STARTED`。两种读法都成立，需要一次调和——与
`MC-REG-COLLISION-001` 同形，那一次走完三步时 Sol 在提案里找出了一个真实漏洞。

## 二、builder 的独立复核 —— **三条实测事实，提案未言明**

**这三条改变了这份提案的性质，请先读。**

### 2.1 「写者租约」今天并不存在

全仓检索 `lease`／`LEASE`（排除 release／please）：**唯一命中是
`src/itsf/mc/supplement_runner.py:3` docstring 里的「lane leases」**——那是车道
任务分配，与 registry 写者无关。

**所以提案里的「运行器在 run 期间持显式写者租约」是待建之物，不是现存之物。**
Sol 审的是一份**设计**，不是一段可运行代码；「租约」的语义、获取、释放、崩溃后
回收全部未定义。

### 2.2 never-re-read 是纪律，不是机制

`scripts/s0_real_run.py` 三处注释陈述该纪律（2602、2679、2820 一带），措辞为
「the path is never re-read after RUN_STARTED」。**它由注释与代码结构维持，
没有任何机制阻止将来某次改动重新读取。** 提案说「代码已示 never-re-read 纪律，
Sol 复核而非采信」——复核的对象因此是**结构**，不是**保证**。

### 2.3 qros-runtime 没有任何文件锁

检索 `fcntl`／`msvcrt`／`filelock`／`FileLock`／`.lock`：**零命中**。运行时自己
的写入器也没有「临时文件 ＋ `os.replace`」的原子写模式（唯一 `os.replace` 命中
在 conformance 的允许名单里，不是写入器）。

**所以并发的 `qros` 调用之间没有任何东西把它们串行化。**

### 2.4 仓在 OneDrive 同步树下

已核。**L-5 缺陷正是 OneDrive 残渣类**（同步产生的 `desktop.ini`／`*.tmp` 会让
M6.1.7 的 exact-set 磁盘不变量判为封存拒绝、烧掉一次 trial）。

### 2.5 已批准的 actor 表**已经**把失败事件判给运行器 —— 三行相抵

`src/itsf/mc/supplement_contract.py` 的 `EVENTS` 表逐字转录
`ND1_RECOMMENDED_PROFILE_R2`（sha256 `a3d40b7c…`，**2026-08-23 已批准**）。
实测全表 actor：

| 事件 | token | 已批准 actor |
|---|---|---|
| P3 | `SUPPLEMENT_RUN_STARTED` | **`main agent (mc_ds_runner)`** |
| P4 | `SUPPLEMENT_SEALED` | **`main agent (mc_ds_runner)`** |
| **A1** | `SUPPLEMENT_ARCHIVE_FAILED` | **`main agent (mc_ds_runner)`** |
| **F1** | `SUPPLEMENT_ATTEMPT_FAILURE` | **`main agent (mc_ds_runner)`** |
| **F2** | `SUPPLEMENT_FAILED` | **`main agent (mc_ds_runner)`** |
| A2 | `SUPPLEMENT_ARCHIVE_RECOVERED` | `main agent` |
| AX | `SUPPLEMENT_ARCHIVE_PERMANENTLY_FAILED` | `main agent` |
| F3 | `SUPPLEMENT_SUPERSEDED` | `main agent` |
| P1 | `SUPPLEMENT_PROPOSED` | `main agent` |
| P2 | `SUPPLEMENT_EXECUTION_AUTHORIZED` | `Aaron` |
| P5 / F2v | 验证类 | `<verifier>` |

**两点，都要看：**

**(a) 提案的 P3 一半与已批准文本一致**，不是新裁——P3 的 actor 本来就是运行器。

**(b) 提案的失败事件一半与已批准文本相抵，抵在三行上**（A1、F1、F2）。提案写
「失败事件：仅主代理追加（B 形）」，而已批准表把这三个失败事件都判给了运行器。

**并且已批准表用的正是提案自己的理由。** 提案说「失败观察者必须在失败后存活」——
已批准表就是按这条切的：运行器还活着时观察到的失败（A1／F1／F2）归运行器；
运行器已经不在时才发生的（A2 归档恢复、AX 永久失败、F3 被取代）归主代理。
**那条原则已经实现了，切口就在「观察者还在不在」。**

### 2.6 S0 运行器今天就在写自己的讣告

`src/itsf/s0/runner.py` 经**同一个** `append_registry_event` 回调发四类事件
（`scripts/s0_real_run.py:3136` 把它接成 actor 恒为 `"main agent (s0_real_run)"`）：

| 行 | 事件 | 何时 |
|---|---|---|
| 685 | `PRE_RUN_ATTEMPT_FAILURE` | P3 之前，`exposure NOT consumed` |
| **725** | **`FAILED`** | **P3 之后，注释原文 `trial permanently consumed; outputs retained`** |
| 772 | `RUN_STARTED` | Stage C 入口 |
| 1340 | `COMPLETED` | 报告封存 |

**725 行就是运行器在跨过不可逆点之后写自己的讣告，且已在生产代码里。**
提案说「运行器永不写自己的讣告——失败观察者必须在失败后存活，编排器做不到」，
可 725 行的运行器**确实活着**：它是在异常处理路径里写的，门失败不等于进程死亡。
真正写不了的只有**硬崩溃**，而那一种现有设计另有办法——772 行的 `except` 落
`HALF_TRANSITION` 标记。

### 2.7 「谁是记录 actor」与「哪个进程执行追加」是两个问题

已批准表定的是**第一个**：actor 字符串。提案裁的是**第二个**：哪个进程去写文件。
**两者不是同一件事，提案把它们当成了一件。**

但请注意 actor 字符串**本身**长什么样：`main agent (mc_ds_runner)`、
`main agent (s0_real_run)`——**括号里点名的就是执行追加的那个工具**。要把它读成
「主代理事后手工补录」很勉强。也就是说：**「受托单写」这个限缩解释可能不是提案
现在才提出的新构造，而是 2026-08-23 就已随 actor 表批准了的东西。** 若如此，
§一所说的「两份已批准文本相抵」比表述的更窄——已批准的 profile 对 MC 生命周期
已经给了答案。

**builder 不替 Sol 定这个。** 两种读法都摆在这里，请 Sol 判，并把判不了的部分
写进 `UNRESOLVED_FOR_AARON`。

## 三、请专门猎取的四点（Fable 指定）

**① 分快照读。** `MC-REG-COLLISION-001` 的洞是「同一份可变文件被读成两个快照」，
Sol 当时正是在 Fable 的提案里找出它的。P3 追加会让运行开始前取的快照过期。
§2.2 说明 never-re-read 只是纪律——**请复核结构，不要采信注释**。

**② 崩溃后的陈旧租约。** 租约尚不存在（§2.1），所以这一点审的是**该被设计成
什么**：进程在持租约时崩溃，谁、何时、依据什么把它回收？回收本身是不是又一次
需要授权的写入？

**③ 并发 qros 调用竞争。** §2.3：今天没有锁。两个会话同时跑 `qros` 或同时追加
的后果未定义。

**④ OneDrive 同步树内追加的原子性。** §2.4。在被云同步的树里做 append-only
追加，是否可能出现半写、重复写、或同步冲突副本？这一条与 ①②③ 不同——**它是
环境属性，不是代码属性**，因此不能靠读代码排除。

## 四、必须返回什么

```
ITEM_ID=D-3
VERDICT=PASS | HOLD | REJECTED_INCOMPLETE
STRONGEST_OBJECTION=<即使 PASS 也要写出最强的反对>
FINDINGS=<逐条，带文件与符号>
四点逐一作答：① 分快照读 ② 陈旧租约 ③ 并发竞争 ④ OneDrive 原子性
⑤（builder 追加）§2.5–2.7：失败事件的裁定与已批准 actor 表的三行冲突怎么办？
   是提案该改，还是已批准表该改，还是两者本就管着不同的问题？
UNRESOLVED_FOR_AARON=<builder 与 Sol 都不得替他决定的部分>
INDEPENDENCE_STATEMENT=<按维度分别陈述>
```

**PASS 不授权任何写入。** 条件 3：Sol PASS ＋ Aaron 授权之前，生产代码不得获得
任何 registry 写能力。本次复审之后仍需 Aaron 终裁。

## 五、不得触碰

- `scripts/s0_real_run.py` 既有先例代码 —— 规整，非拆除。
- `ops/TRIAL_REGISTRY.md`、两份 `EXPOSURE_LEDGER.md` 本体。
- `src/itsf/mc/supplement_runner.py` 的 `plan_failure_event` —— 保持只规划不写。
- 主计划正文 —— 它是 append-only 且为隔离件；边界第 4 条的限缩解释随 Aaron 的
  决策记录附着，不改原文。

## 六、常设禁令（对复审席位同样在 force）

- **只读。** 不改任何文件，不打补丁。
- **不得在本仓做任何检索**（S1(b)）。需要什么路径就列出来，由工作会话经
  `PULL_PROTOCOL` 提供字节。三个席位已被烧，其中两个**从未打开过**那份文件——
  一个死于广域符号搜索，一个死于单模式定向 grep。
- 禁区权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`，
  每一条路径都当作关闭。**包括本提案所摘录的那份裁决全文。**
- 零真实数据读取；零执行；不在 `C:\Users\Aaron\quant-data\` 下创建目录；
  不追加 registry／exposure 事件；不签发授权；不填 P2 占位符。
