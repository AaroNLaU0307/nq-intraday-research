# D-3 复审提示 —— fresh Sol，Tier-1 自主复审

```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=High
EXECUTION_MODE=STANDARD
ROLE=reviewer（Tier-1 discretionary design review）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=本仓任何工作会话的延续；不得是曾读过隔离件的席位
LANE=FULL
OUTCOME_EXPOSED=NONE（本席位必须保持 outcome-blind，见 §1）
PREREG_SEALED=YES
WHY_THIS_MODEL=D-3 是设计裁定的独立复核；Fable 出提案，故复核必须换族
```

**REVIEW_ID=rv-f4207865a116-c004854e6828**（gate=`TIER1_DISCRETIONARY`）

> **本文件必须从磁盘读取（read it from disk），不要用聊天里贴给你的副本。**
> 路径 `ops/PROMPT_D3_SOL_REVIEW.md`。**line 60 of it must read**
> `REVIEWED_SET_UNCHANGED_SINCE=…`。行号或内容对不上 ⇒ 你手里是旧副本，**STOP**。
>
> 这条不是形式：2026-08-25 有一次复审就是因为提示本身以粘贴形式过期而作废——
> 工件按规则核了哈希，**声明工件的那份文档没核**。

---

## 1. 开工之前：你可能被烧掉

**本仓已烧掉三个复审席位，其中两个从未刻意打开过任何文件。**

- 第 1 个：做常规状态定位，打开了旧恢复序指向的隔离锚。
- 第 2 个：**一次广域符号搜索**带出了隔离片段。
- 第 3 个：**一次单模式定向 grep**。

所以：

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不得在本仓做任何检索** —— 不 grep、不 rglob、不广域符号搜索、不「先看看目录
结构」。只打开 §2 表里逐条列出的那几个路径，别的一律不开。需要别的字节：
**列出路径，回给工作会话**，由它经 `PULL_PROTOCOL` 供给。

**禁区权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`（12 条）。
每一条都当作关闭。** 其中点名两条，只为标记禁区、不是指路：

```
OFF-LIMITS   ops/MC_TO_STRATEGY_MASTER_PLAN.md         （DAG／节点台账；旧恢复入口）
OFF-LIMITS   ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md  （D-3 裁决全文；§5 说明为何不给你）
```

**允许的 outcome-clean 入口：`ops/RECOVERY_ANCHOR.md`。** 需要项目定位就读它，
不要自己找路。

## 2. 传输核对（先做，不通过就 STOP）

```
REVIEWED_SET_UNCHANGED_SINCE=7b582b1240e4a9d93cd8c9d9ac470ca98525ce02
```

**语义**：该 commit **之后**没有任何 commit 触碰过下表任一路径。它不是当前分支头，
也不该等于当前分支头——提交本提示、登记本、issuance 记录都会推动分支头，而那些
提交都不碰下表的路径。你可以自己验，**这一条命令是允许的**（它不是检索，是范围
核对）：

```bash
git log --oneline 7b582b1240e4a9d93cd8c9d9ac470ca98525ce02..HEAD -- ops/D3_REGISTRY_WRITER_PROPOSAL.md src/itsf/mc/supplement_contract.py src/itsf/s0/runner.py src/itsf/mc/registry_boundary.py src/itsf/mc/supplement_runner.py scripts/s0_real_run.py
```

**必须为空。** 非空 ⇒ 工件在你手里动了 ⇒ STOP。

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `2ae3db75f6fff99d88a9868e09d3dbb13a972ccf96a75706aa6882c190b3cfd3` | 11124 | `ops/D3_REGISTRY_WRITER_PROPOSAL.md` |
| `c6d5b46f71404044d3e0d2ce770bfda2f4eaa88b3448e397d035b3ec8aff7298` | 20014 | `src/itsf/mc/supplement_contract.py` |
| `e0be5ae9771029d8c3e96a7d06f41808f15f28902d4e8739c33350df575bd8ee` | 78591 | `src/itsf/s0/runner.py` |
| `fdb6f99a58180e1439749f6a1e2b9343fb83b7e59e42461b28ddffd56c7f0520` | 9185 | `src/itsf/mc/registry_boundary.py` |
| `3cb698aef52dcc14ee0987e585ee5b46705a3046e7e53ea42d3db69e001cf746` | 45975 | `src/itsf/mc/supplement_runner.py` |
| `fa6f2adbd92b771cb4b66c4297d19d8e531519ae01149c3fbc7f2a73e4c42044` | 159369 | `scripts/s0_real_run.py` |
| `452afc10e86909e15cf7884cbe134d249221dd9a7ae8c2e3315b42211c56d731` | 16637 | `ops/packets/rv-f4207865a116-c004854e6828.packet` |

**packet 里 `BASIS=WORKTREE` / `WORKTREE=DIRTY(1 modified, 1 untracked)` 是预期的，
不要据此 STOP。** 生成 packet 的那一刻，工作区里未提交的正是**交付材料本身**——
`ops/NEXT_HANDOFF.md`（modified）与 `ops/PROMPT_D3_SOL_REVIEW.md`（untracked，
即本文件）。这是固定点问题：packet 记录分支头，而提交 packet 会推动分支头，
所以 packet 永远无法在「包含自己」的干净树上生成。**两者都不是送审路径。**
权威判据是下表六个哈希 ＋ 上面那条 `git log` 为空，不是 `BASIS`。

**同理，packet 的 `FILE_MANIFEST` 里 `ops/README.md` 与 `qros-state.yaml` 两行的
哈希现在已经对不上了，这也是预期的，同样不要据此 STOP。** 它们正是**记录这次交付
本身**的两个文件——前者加索引条目，后者追加 `PACKET_ISSUANCE`——所以在 packet
生成之后必然继续变。**两者都不是送审路径，都没被冻结。** 送审集是下表前六行，
只有它们受 `ARTIFACTS_UNDER_REVIEW.json` 冻结、受那条 `git log` 保护。

**逐个重算并比对**，缺失／截断／不符 ⇒ STOP 并报告。前六行经
`ops/ARTIFACTS_UNDER_REVIEW.json` 登记冻结；最后一行是 Review Packet v1 本体
（存 `ops/packets/` 而非运行时硬编码的 `runs/packets/`，理由见
`ops/RUNTIME_DEVIATION_PACKET_SAVE_DIR.md`，该偏离已入账）。

## 3. 你要裁的东西

**读 `ops/D3_REGISTRY_WRITER_PROPOSAL.md`（全文）。** 它已经写全了：被提议的裁定
原文、背景冲突、builder 的实测复核（§2.1–2.7）、要猎的五点、返回格式、禁触清单。
**本提示不复述它**——复述就会有两份会互相漂移的副本，那正是上面第二段警告的东西。

一句话概括：**边界第 4 条「registry 只允许主代理单写」，与已完成真实运行中运行器
自行追加 `RUN_STARTED` 的先例相抵。** Fable 提案拆开裁——P3 由运行器自追加（受托
单写限缩解释），失败事件仅主代理追加。**你判这个构造安不安全。**

### 请先看 §2.5–2.7，它可能改变整个问题

builder 在出这份提示的过程中实测到：**已批准的 `ND1_RECOMMENDED_PROFILE_R2`
（sha256 `a3d40b7c…`，2026-08-23 批准）的 actor 表，把 P3／P4／A1／F1／F2 全判给
`main agent (mc_ds_runner)`，只把 A2／AX／F3 判给 `main agent`。**

于是：提案的 **P3 一半与已批准文本一致**；提案的**失败事件一半与已批准文本相抵，
抵在 A1／F1／F2 三行上**。而且已批准表用的正是提案自己的理由（观察者必须在失败后
存活），切口就在「运行器还在不在」。

另外 `src/itsf/s0/runner.py:725` **今天就在跨过不可逆点之后追加 `FAILED`**。

**§2.7 提出的问题请你正面回答**：「谁是记录 actor」与「哪个进程执行追加」是同一个
问题还是两个问题？——若是同一个，受托单写在 2026-08-23 就已随 actor 表批准，本次
冲突比表述的窄得多；若是两个，照字面实施失败事件一半就要改三行已批准 actor 并
删掉一处生产代码里的追加。**builder 不替你定，也不替 Aaron 定。**

## 4. 三条你不能替任何人做的事

1. **PASS 不授权任何写入。** 条件 3：Sol PASS ＋ Aaron 授权之前，生产代码不得获得
   任何 registry 写能力。你 PASS 之后仍需 Aaron 终裁。
2. **不要替 Aaron 决定**。凡是你觉得「这应该由所有者定」的，写进
   `UNRESOLVED_FOR_AARON`，不要自己收口。
3. **只读。** 不改文件、不打补丁、不追加任何 registry／台账事件、不签发授权、
   不填 P2 占位符、不在 `C:\Users\Aaron\quant-data\` 下创建目录、不读真实数据、
   不执行任何 run。

## 5. 为什么不给你 Fable 的裁决全文

`ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md` **是隔离件**：它自身复述了一个被隔离的
数值，转录当时即登记。`ops/D3_REGISTRY_WRITER_PROPOSAL.md` 是其中 D-3 一节的
outcome-clean 副本，经同一台扫描器验过干净，并补上了 builder 的独立复核。

**这不是删节。** 被摘出来的是 D-3 那一节的全部；未给你的是同一份文件里另外三项
（D-1、D-2、D-4）的裁决，与 D-3 无关。

## 6. 返回格式

```
ITEM_ID=D-3
REVIEW_ID=rv-f4207865a116-c004854e6828
TRANSPORT_PRECHECK=PASS|STOP（逐个哈希 ＋ 上面那条 git log 为空）
VERDICT=PASS | HOLD | REJECTED_INCOMPLETE
STRONGEST_OBJECTION=<即使 PASS 也要写出最强的反对>
FINDINGS=<逐条，带文件与符号>
五点逐一作答：① 分快照读 ② 陈旧租约 ③ 并发竞争 ④ OneDrive 原子性
             ⑤ actor 表三行冲突（§2.5–2.7）
UNRESOLVED_FOR_AARON=<你与 builder 都不得替他决定的部分>
INDEPENDENCE_STATEMENT=<按维度分别陈述：会话独立性、是否读过任何隔离件、
                        是否做过任何检索>
SEAT_STATUS=BLIND|EXPOSED（读过隔离件或检索命中隔离内容就是 EXPOSED，如实报）
```

`SEAT_STATUS` 请务必如实——**烧掉席位不消耗研究自由度**，两条轴分开记账
（`ops/REVIEWER_EXPOSURE_LOG.md` 记席位轴，可读）。瞒报才是不可逆损失。
