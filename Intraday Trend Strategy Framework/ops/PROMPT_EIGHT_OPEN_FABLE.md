# 八项待裁 —— 交 Fable 决裁席（Aaron 明示委托）

```ini
REVIEW_ID=dec-eight-open-2026-08-26
DELIVERY_STATUS=RETURNED
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=xhigh
EXECUTION_MODE=STANDARD
ROLE=决裁席（decision seat），不是审计席，不是 builder
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=提出 D-3 提案的那个 Fable 会话的延续；不得是本仓任何工作会话的延续
LANE=FULL
OUTCOME_EXPOSED=UNKNOWN（本席位轴分类为 PENDING_AARON，见 §1）
PREREG_SEALED=YES
SUBAGENT_OR_WORKFLOW_BUDGET=默认 3 个 workflow，单波最多 3 且范围互不重叠，硬上限 6 需 Aaron 另批；子 workflow 不得再生 workflow
WHY_THIS_MODEL=Aaron 2026-08-26 明示：「fable将会替我做选择，把这八项都交给fable」
```

**DECISION_ID=dec-eight-open-2026-08-26**　**DELEGATED=YES**

> **本文件必须从磁盘读取（read it from disk），不要用聊天里贴给你的副本。**
> 路径 `ops/PROMPT_EIGHT_OPEN_FABLE.md`。**line 71 of it must read**
> `REVIEWED_SET_UNCHANGED_SINCE=…`。行号或内容对不上 ⇒ 你手里是旧副本，**STOP**。
>
> 这条不是形式：2026-08-25 有一次复审就是因为提示本身以粘贴形式过期而作废——
> 工件按规则核了哈希，**声明工件的那份文档没核**。

---

## 0. 你被授权做什么

Aaron 于 2026-08-26 说：**「fable将会替我做选择，把这八项都交给fable」**。

**所以这八项的实质裁定由你作出**，标 `DELEGATED=YES`，与 2026-08-24 那批
Sol 委托裁定同形。**但「裁定」不等于「执行解锁」**，理由是全局常设规则：
凡触及全局文件、已批准 profile、已认证运行时仓、preregistration/seal、
KB schema、validator 或 verdict 的**写入**，都需要一次**后续的、单独的**明示
授权。你替 Aaron 作的是**选择**，不是那次授权。

**因此每一项都必须回答两件事**：`RULING`（实质选择）＋
`EXECUTION_UNLOCKED_BY_THIS_RULING = YES | NO`（NO 时写明还欠谁的哪一次授权）。
**不要把两者混成一句。** 你上一轮自己的 §三「执行锁重申」就是这个形状。

## 1. 开工之前

**本仓已烧掉三个复审席位，其中两个从未刻意打开过任何文件**（一个死于广域符号
搜索，一个死于单模式定向 grep）。**第三个是你**——上一轮决裁席自陈经一次定向
grep 触到隔离锚一行治理边界文本，席位轴分类记为 `PENDING_AARON`。所以：

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不得在本仓做任何检索**——不 grep、不 rglob、不广域符号搜索、不「先看看目录
结构」。只打开 §2 表里逐条列出的十个路径，别的一律不开。需要别的字节：
**列出路径，回给工作会话**，由它经 `PULL_PROTOCOL` 供给。

**禁区权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`（12 条）。
每一条都当作关闭。** 其中点名三条，只为标记禁区、不是指路：

```
OFF-LIMITS   ops/MC_TO_STRATEGY_MASTER_PLAN.md         （DAG／节点台账；旧恢复入口）
OFF-LIMITS   ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md  （你上一轮的裁决全文，见 §5）
OFF-LIMITS   ops/EXPOSURE_LEDGER.md                    （研究轴台账；D-1 的标的，但不得打开）
```

**允许的 outcome-clean 入口：`ops/RECOVERY_ANCHOR.md`。**

## 2. 传输核对（先做，不通过就 STOP）

```
REVIEWED_SET_UNCHANGED_SINCE=ce378c857f135e82287dfbade1da5aa910e1b39b
```

**语义**：该 commit **之后**没有任何 commit 触碰过下表任一路径。它不是当前分支头，
也不该等于当前分支头——提交本提示与登记本都会推动分支头，而那些提交都不碰下表
路径。**这一条命令是允许的**（它不是检索，是范围核对）：

```bash
git log --oneline ce378c857f135e82287dfbade1da5aa910e1b39b..HEAD -- ops/D124_RULINGS_CLEAN_EXTRACT.md ops/RULING_SOL_D3_HOLD_2026-08-26.md ops/D3_REGISTRY_WRITER_PROPOSAL.md ops/RUNTIME_DEVIATION_PACKET_SAVE_DIR.md ops/REVIEWER_EXPOSURE_LOG.md src/itsf/mc/supplement_contract.py src/itsf/mc/supplement_runner.py src/itsf/mc/registry_boundary.py src/itsf/s0/runner.py scripts/s0_real_run.py
```

**必须为空。** 非空 ⇒ 工件在你手里动了 ⇒ STOP。

| SHA-256 | 字节 | 路径 | 为什么给你 |
|---|---|---|---|
| `5d6e8b65b4a7f9d030d13a074f40a9c388bad763e17c610b9c529d14e5634745` | 10350 | `ops/D124_RULINGS_CLEAN_EXTRACT.md` | D-1／D-2／D-4 裁决逐字副本（原件隔离） |
| `5f533347622156932fce5c35f11ffa2b089771eba0f2dd6157b7bb2f801a00ff` | 10185 | `ops/RULING_SOL_D3_HOLD_2026-08-26.md` | D-3 的 Sol HOLD 全文＋builder 逐条复现 |
| `2ae3db75f6fff99d88a9868e09d3dbb13a972ccf96a75706aa6882c190b3cfd3` | 11124 | `ops/D3_REGISTRY_WRITER_PROPOSAL.md` | 被 HOLD 的 D-3 提案本体，含 §2.5–2.7 实测 |
| `04232aeae7fd41d05a7af4c1e0ab01f4fee2f789262b3bb7fdac8f077b3488f6` | 3638 | `ops/RUNTIME_DEVIATION_PACKET_SAVE_DIR.md` | D-4 的过渡形与实测冲突 |
| `40ac83f5863af2d7f345e803105ea13799f0e054d4c96185de2eee264e6283d3` | 8165 | `ops/REVIEWER_EXPOSURE_LOG.md` | D-1／D-2 的席位轴事实，含第 4 行未烧席位 |
| `c6d5b46f71404044d3e0d2ce770bfda2f4eaa88b3448e397d035b3ec8aff7298` | 20014 | `src/itsf/mc/supplement_contract.py` | 已批准 ND1 actor 表（D-3 第 1、2 问的标的） |
| `3cb698aef52dcc14ee0987e585ee5b46705a3046e7e53ea42d3db69e001cf746` | 45975 | `src/itsf/mc/supplement_runner.py` | plan_failure_event 硬编码 ACTOR_RUNNER |
| `fdb6f99a58180e1439749f6a1e2b9343fb83b7e59e42461b28ddffd56c7f0520` | 9185 | `src/itsf/mc/registry_boundary.py` | C2 单一校验边界（分快照读） |
| `e0be5ae9771029d8c3e96a7d06f41808f15f28902d4e8739c33350df575bd8ee` | 78591 | `src/itsf/s0/runner.py` | 1388 无锁 writer；725 跨不可逆点的 FAILED；772 三步分离 |
| `fa6f2adbd92b771cb4b66c4297d19d8e531519ae01149c3fbc7f2a73e4c42044` | 159369 | `scripts/s0_real_run.py` | 3136 registry_append 绑定；三处 never-re-read |

**逐个重算并比对**，缺失／截断／不符 ⇒ STOP 并报告。

## 3. 八项

### 前三项 —— 你上一轮裁决里留给 Aaron 的部分

**逐字原文读 `ops/D124_RULINGS_CLEAN_EXTRACT.md`。** 该件同时标出了 builder
**已经落地**的条件，别把已完成的重裁一遍。

| # | 项 | 要你定什么 |
|---|---|---|
| **1** | D-1 条件 3 | 把全局 L6 规则「append every exposure event」的 scope 限缩到**研究者／统计暴露轴**——批准、驳回、还是改写措辞？ |
| **2** | D-2 的 S1(a) ＋注册表 carve-out | 把 `carries_outcome` 全部路径迁进单一显名隔离子树，并对「路径迁移 ≠ 条目离开」作 carve-out——做、不做、还是以 (b) 单独成立？ |
| **3** | D-4 的运行时工作项 | `_SAVE_DIR` 配置化何时做、认证深度多少、过渡形 B 维持到什么时候？ |

**第 1、3 项各有一个前置事实你要先认**：第 1 项动的是**全局文件**（QROS／L6 层）；
第 3 项动的是**已认证的 qros-runtime 仓**（Sol 15 轮认证＋Fable 启用审计 PASS）。
两者的**写入**都超出 builder 常权。

### 后五项 —— D-3 被 fresh Sol 判 HOLD 之后留下的

**先读 `ops/RULING_SOL_D3_HOLD_2026-08-26.md`（Sol 全文 ＋ builder 逐条复现），
再读 `ops/D3_REGISTRY_WRITER_PROPOSAL.md`（被 HOLD 的提案本体）。**

| # | 项（Sol 的 `UNRESOLVED_FOR_AARON` 原文） |
|---|---|
| **4** | actor 是否同时表达实际执行者；若否，是否增加独立 executor provenance |
| **5** | 保留 A1／F1／F2 的 runner actor，还是修订已批准 profile、planner 与生产先例 |
| **6** | P3 后硬崩溃应产生什么事件、由谁追加，以及恢复写入的授权条件 |
| **7** | registry 是否允许继续在主动同步的 OneDrive 树中作为 canonical 写入面 |
| **8** | 租约回收能否自动执行，还是必须 fail-closed 等待人工裁定 |

## 4. 一件必须先跟你说清的事：**第 4–8 项是在裁你自己的提案**

**D-3 提案由上一个 Fable 会话提出。** 新会话满足会话独立性（独立性由会话承载，
不由模型承载），但**同族裁自己的东西有护短风险**，所以明写：

- **推翻它是被允许且被期待的。** 若 Sol 是对的，就说 Sol 是对的。
- **不要为「上一轮 Fable 已经这么裁过」赋予任何权重。** 那不是先例，是待检对象。
- 若你认为自己在这几项上无法给出独立判断，**如实写进
  `SEAT_INDEPENDENCE_CONCERN`，不要硬裁** —— 那一项退回 Aaron 比一个护短的裁定好。

**Sol 的实质发现（builder 已逐条复现，无一采信）**：读—校验—追加之间没有临界区，
writer 是无锁 `open("a")`；失败事件条款与已批准 actor 表相抵三行（A1／F1／F2）；
崩溃与陈旧租约无状态机，且当前**根本没有 MC 生产执行路径可审**；never-re-read
只是结构＋注释；OneDrive 原子性无法靠读代码排除。

**Sol 还给了一个较窄且与现有合同一致的解释**（它明说采不采用归所有者）：运行器
存活并捕获到的 A1／F1／F2 仍由运行器追加；硬崩溃后的检测／恢复由主代理负责，
用单独批准的恢复语义。**你可以采纳、修改或否决它。**

## 5. 为什么不给你自己上一轮的裁决全文

`ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md` **是隔离件**：它的 §二（决裁席暴露
自评）里带着一个被隔离的数值，转录当时即登记。
`ops/D124_RULINGS_CLEAN_EXTRACT.md` 是 D-1／D-2／D-4 三节 ＋ §三执行锁的
outcome-clean 逐字副本，**三段均经逐字节比对确认与原件一致**，未取的只有 §〇
与 §二。D-3 一节的干净副本是 `ops/D3_REGISTRY_WRITER_PROPOSAL.md`。

## 6. 只裁，不做

- **只读。** 不改任何文件、不打补丁、不实现任何一项。你是决裁席，不是 builder。
- 不追加任何 registry／台账事件；不签发任何授权；不填 P2 占位符；
  不在 `C:\Users\Aaron\quant-data\` 下创建目录；不读真实 Development 数据；
  不执行任何 run；不动 preregistration／seal。
- **不得自我升格**：本文件授权你**裁**，不授权你**写**。含糊之处取限制性读法。
- workflow 预算见顶部路由头。**先跑机器检查再花模型 token**：能被
  `python -m pytest tests` 或 `qros check` 否掉的，不要拿去开 workflow。

## 7. 返回格式

**每一项**都用这个块，八项各一个：

```
ITEM=<1..8>  TITLE=<一句话>
RULING=<你的实质选择，含选项名与理由>
EXECUTION_UNLOCKED_BY_THIS_RULING=YES|NO
  若 NO：还欠谁的哪一次授权，以及在那之前什么形态是受批准的过渡形
CONDITIONS=<可执行、可机械检查的条件；每条指明由谁落地>
FALSIFIER=<观察到什么就推翻本裁>
COLLATERAL=动：<路径>  不得动：<路径>
CONFIDENCE=<HIGH|MEDIUM|LOW> ＋ 一句为什么
```

八项之后再给：

```
CROSS_ITEM_CONFLICTS=<八项之间是否互相矛盾；有就点名>
SEAT_INDEPENDENCE_CONCERN=<第 4–8 项：你是否认为自己能独立裁自己的提案>
STILL_AARON_ONLY=<你判断仍必须由 Aaron 本人做的，逐条>
STRONGEST_OBJECTION_TO_MY_OWN_RULINGS=<对你自己这八项最强的反对>
SEAT_STATUS=BLIND|EXPOSED|UNCHANGED（读过隔离件或检索命中隔离内容就是 EXPOSED，如实报）
INDEPENDENCE_STATEMENT=<按维度分别陈述：会话独立性、是否读过任何隔离件、
                        是否做过任何检索、与 D-3 提案作者的关系>
```

`SEAT_STATUS` 请务必如实——**烧掉席位不消耗研究自由度**，两条轴分开记账
（`ops/REVIEWER_EXPOSURE_LOG.md` 记席位轴，可读，第 4 行是第一个没被烧的席位）。
瞒报才是不可逆损失。
