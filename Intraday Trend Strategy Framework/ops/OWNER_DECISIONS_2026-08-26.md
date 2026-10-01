# Aaron 本人裁定 —— 2026-08-26（采纳八项委托裁定）

```
RECORD_TYPE=OWNER_DECISION
DECIDED_BY=Aaron，本人
DELEGATED=NO —— 「采纳」这个动作是 Aaron 自己的；被采纳的八项内容是 Fable
          在他明示委托下作出的（DELEGATED=YES）。引用时两层都要带。
EFFECT=即时生效
TRANSCRIBED_BY=Opus 5 main agent（builder seat）—— 转录，非背书
BASIS=ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md
      SHA256 5116f7b03dabe6cc4a8a2357b02b4b30e3a9227d050e41d9c1f0943262ed7dd3
      （该哈希证明的是本次转录的字节；裁定经聊天送达，非磁盘交付）
```

---

## OD-2026-08-26-1 —— 委托 Fable 裁这八项

Aaron 原话：**「fable将会替我做选择，把这八项都交给fable」**（2026-08-26）。

```
DELEGATION_SCOPE=dec-eight-open-2026-08-26 的全部八项
DELEGATE=Fable 5，fresh top-level session
```

## OD-2026-08-26-2 —— 采纳八项裁定全文

Aaron 原话：**「你审核一下，就让fable推荐的做」**（2026-08-26，读过八项裁定之后）。

```
ADOPTED=ITEM 1..8 全部，逐字如 ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md §一
BUILDER_AUDIT=已做（同件 §二），全部引用 REPRODUCED；一处论证更正见下方 OD-…-4
```

**「采纳」在这里精确地意味着什么** —— 因为八项里**每一项**都自陈
`EXECUTION_UNLOCKED_BY_THIS_RULING=NO`：

- **实质选择**已定，不再重开。八项的 RULING 段即受裁文本。
- **执行**并未因采纳而全部解锁。凡裁定自己点名「欠某项 Aaron 具体动作」的，
  那个动作仍然欠着 —— 采纳裁定 ≠ 执行那个动作。
- **例外是第 4、5 项**：两者所欠的**仅**是「Aaron 决策记录 append」，而记录是
  转录 Aaron 的决定、由 builder 落盘。本记录即是。**故第 4、5 项自本记录起
  完成**，且两者本就是零改动裁定（「无执行动作存在」）。

## OD-2026-08-26-3 —— 逐项结算：什么完成了，什么还欠 Aaron

| # | 题 | 本记录之后的状态 | 还欠 Aaron 的**具体动作** |
|---|---|---|---|
| 1 | 全局 L6 exposure 句限缩 | 受裁：**改写措辞**（非裸限缩） | 对全局 `~/.claude/CLAUDE.md` L6 段的**修订授权**，并 append 改写句的逐字终稿。**过渡形继续**：临时生效，方向 fail-closed |
| 2 | D-2 S1(a) ＋注册表 carve-out | 受裁：**做**，carve-out 取外科形 | (i) path 字段编辑与文件迁移的**执行授权**；(ii) 确认 08-25「Sol 返回前不推进」hold 不覆盖本项。**过渡形继续**：(b)＋S2 |
| 3 | D-4 `_SAVE_DIR` 配置化 | 受裁：**下一个维护窗**，一轮 fresh Sol（High），B 按事件失效 | **开启维护窗**（qros-runtime 仓）。**过渡形继续**：B |
| 4 | actor 是否兼表执行者 | ✅ **完成** —— 是，复合 token，不加字段，双向绑定 | 无。零改动 |
| 5 | A1/F1/F2 的 actor | ✅ **完成** —— 保留，零修订；「观察者存活」为受裁切口 | 无。零改动 |
| 6 | P3 后硬崩溃 | 受裁：新增 CR1 事件＋bootstrap 悬链拒绝＋逐 incident 授权 | ND1 profile **R3 修订的 ratify**（走提案→fresh Sol→Aaron 三步）。**今日不阻塞任何事**：MC 生产路径不存在 |
| 7 | registry 留在 OneDrive 树？ | 受裁：**有边界地允许**，四条边界 | 决策记录（本件即是）；**另**：见证目录若需在 `C:\Users\Aaron\quant-data\` 下新建，须单独的**目录创建授权** |
| 8 | 租约回收自动化 | 受裁：**fail-closed，永远**；自动回收否决 | 无执行动作（租约尚不存在）。约束未来设计 |

**第 6 项特别声明**：`CR1` 是**工作名**，终名与字段归 profile 修订流程。
本记录不构成对 ND1 profile 的修订，也不授权任何人修订它。

## OD-2026-08-26-4 —— 一处经 builder 复核的论证更正（不改任何裁定）

第 7 项的**风险叙述**里有一句不成立：「半写行会死在六格解析上……fail-closed」。

**实测**：`parse_registry_events`（`scripts/s0_real_run.py:183-184`）对格数不符的行
是 **`continue` 而非 raise**，畸形行被静默丢弃；且 `ops/TRIAL_REGISTRY.md`
**被 clean gate 白名单豁免**（`:113`，用于 `:596`），registry 变脏不打红
`git_clean`。**所以截断末行的半写与静默回退可观测状态相同——致命通道是两条。**

**这不改第 7 项的裁定，反而加重其条件 (1)**：反回退见证比对
{sha256, 事件计数, 末行}，丢一行会让计数低于见证，同样被抓。**边界 (1) 是这两条
通道唯一的共同拦截点** —— 将来任何以「解析器会挡住半写」为由削减边界 (1) 的提议，
其前提是假的。

冲突副本那半句成立：`_clean_gate_exempt` 只豁免精确路径，冲突副本是另一个文件名的
未跟踪文件，会打红 `git_clean`。

## OD-2026-08-26-5 —— 仍然只有 Aaron 能做的（Fable 的 `STILL_AARON_ONLY`，加一条）

1. 上表所有「还欠」栏的执行授权。
2. 仓库整体是否迁出主动同步树（第 7 项的彻底形）。
3. 席位台账第 3 行的终分类（`PENDING_AARON`）、第 4 行 `NOT_EXPOSED` 分类值的存废、
   **以及新增的第 5 行**（本轮 Fable 的三次定位操作）。
4. GRAD pilot 排程及其与维护窗的先后（第 3 项条件 4 的两分支择一）。
5. **（builder 追加）** D-3 本身的去向：八项裁定**不解锁 D-3**。按 Fable 的
   `CROSS_ITEM_CONFLICTS`，重启 MC 需要按第 4/5/6/7/8 项**重写 D-3 提案并重走
   三步全程**。是否重启、何时重启，未裁。

## OD-2026-08-26-6 —— 未被采纳所改变的东西（免得日后误读）

- **D-3 的 HOLD 仍在**：条件 3 继续在 force —— fresh Sol PASS ＋ Aaron 授权之前，
  生产代码不得获得任何 registry 写能力。
- **N09 的 P2 仍不签**（OD-2026-08-25-1 未被本次触及）。
- **三条独立授权仍不得合并**（ND1）：目录创建 / 写探针 / 执行。第 7 项的见证目录
  正是「目录创建」那一条。
- `A2→B` 与 `I→J` 的 HOLD 未变；本轮不涉及任何 gate 释放。


---

# 2026-08-26（下午）—— Aaron 采纳 Fable 的 R1–R10，并亲授 R4／R6／R7

```
RECORD_TYPE=OWNER_DECISION（续）
BASIS=ops/RULING_FABLE_REMAINING_2026-08-26.md
      SHA256 617c8524a3402f1f5b7551f727c31065c3c0115fa2cab06f78acd0e92c69b3e8
DELEGATED=NO（采纳与 R4／R6／R7 的授权是 Aaron 本人的动作）
```

## OD-2026-08-26-7 —— 采纳 R1–R10 全部

Aaron 原话：**「这些就按fable建议的做就行，我同意了」**（针对我列出的 R4／R6／R7
三条 `DELEGABLE=NO`）。合并前一条「其余的决定依旧让fable替我决定」，本记录把
**R1–R10 全部**记为已采纳；其中 R4／R6／R7 由本条**补上 Fable 判定必须由他本人
给出的那三次许可**。

## OD-2026-08-26-8 —— R4 已执行：全局 L6 exposure 句已替换

**授权**：Aaron 同意按 Fable R4 的建议执行。
**执行**：`C:\Users\Aaron\.claude\CLAUDE.md` 第 90 行已替换。

**替换后的逐字终稿**（R4 条件 3 要的是终稿本身，不是「已批准」三个字）：

```
  5. Exposure — two axes, never merged. RESEARCH axis: append every researcher/statistical exposure event to the project's `ops/EXPOSURE_LEDGER.md` (append-only; normalization rule in its header) even when `N_trials` does not move. SEAT axis: append every reviewer-seat exposure event to the project's `ops/REVIEWER_EXPOSURE_LOG.md` (append-only); burning a seat consumes no research degrees of freedom and never enters the research ledger. Per axis: no ledger/record ⇒ that axis is `UNKNOWN`, never `NONE`. An event that cannot be assigned to an axis fails closed into the seat ledger marked `PENDING_AARON`. A project's `qros-state.yaml` `outcome_exposure` block must name both ledgers.
```

**条件逐条落实**：

| R4 条件 | 做法 | 结果 |
|---|---|---|
| 1. **精确字符串**替换，不按行号定位 | 从准备件抽出「现状」串，断言它在全局文件中**恰出现 1 次**，再 `replace(…, 1)` | 通过。行数 92→92（单行换单行） |
| 2. 重跑两个测试，绿且语义零动 | `test_exposure_ledger_migration.py` ＋ `test_exposure_discoverability.py` | **9 passed**；两测试文件 `git diff` **无输出**（零改动） |
| 3. 终稿逐字入 OWNER_DECISIONS | 即上方代码块 | 已录 |
| 4. `L6_RUNTIME_SPEC.md` 已批准字节零触碰 | 未打开、未修改 | 遵守 |
| 5. 若 R1 改选 B 须先重备终稿 | R1 裁为 **A′**（两份台账都不迁），故 `ops/EXPOSURE_LEDGER.md` 路径恒真 | 不适用 |

## OD-2026-08-26-9 —— R7 已执行：见证目录已创建（**仅创建**）

**授权**：Aaron 同意按 Fable R7 的建议执行；路径采用 Fable 建议值。

```
AUTHORIZED_PATH=C:\Users\Aaron\quant-data\registry-witness\itsf\
SCOPE=仅覆盖「创建空目录」。**不含**写探针，**不含**执行。
```

**R7 条件 1（创建前的机械核验）—— 已跑，结果如下**：

```
C:\Users\Aaron\quant-data        Attributes=Directory   ReparsePoint=否
逐级祖先 quant-data / Users\Aaron / Users / C:\   全部 reparse=否
在 C:\Users\Aaron\OneDrive 之下 = 否
OneDrive 认领的同步根（HKCU\SOFTWARE\Microsoft\OneDrive\Accounts）= 仅 C:\Users\Aaron\OneDrive
=> 该路径不在任何主动同步 scope 内。条件 1 满足。
```

**实际创建了两级**，如实记录：授权文本点名的是叶路径，而创建叶必然创建其父。

```
C:\Users\Aaron\quant-data\registry-witness        新建
C:\Users\Aaron\quant-data\registry-witness\itsf   新建
```

**零字节写入的证明**：`itsf` 递归计数 **0 项**；`registry-witness` 递归计数 1 项，
即其子目录 `itsf` 本身。**没有任何文件被写入。**

**仍未授权**（ND1 三条不得合并，Aaron 只给了第一条）：

- **写探针**（首条见证写入）—— 未授权，`registry_witness.py` 因此仍未接线。
- **执行** —— 未授权。

## OD-2026-08-26-10 —— R6：第二维护窗已开启

**授权**：Aaron 同意按 Fable R6 的建议执行 ⇒ **维护窗开启**（D-4 条件 5 的定义性
要件由此满足）。

```
WINDOW=第二维护窗（qros-runtime）
SCOPE=R2 裁定的两侧联合整改，冻结，窗内零范围蔓延：
      · qros_runtime/packet.py:64  _SAVE_DIR
      · qros_runtime/header.py:200-201  内联 "runs/prompts/%s.header"
CERTIFICATION=机器检查先行（全套件＋22 conformance＋25 render-checks＋新增用例），
      **后一轮 fresh Sol（High）**；HOLD 走 reproduce-first 环
ORDERING=窗完成或回滚在先，第一个 GRAD pilot 在后（R6 条件 4；若倒序，
      D-4 条件 4 的既裁回退自动接手，pilot 不被阻塞）
```

**R2 的补裁句，逐字入录**（R2 条件 4）：

```
本席补裁：header.py:200–201（qros prompt 的 REQUIRED SAVE PATH 面）与 packet.py:64
属同一缺陷类——运行时硬编码 <repo>/runs/ 存放路径，与 L-5/R5 禁令冲突——纳入同一
维护窗、受 D-4 条件 1–4 与同一 falsifier 约束整改；默认值 "runs/prompts" 恒不变，
配置化必须加性（可选参数/可选字段），无显式配置时行为零变化。此为对 D-4 范围的明示
扩充，非对其原文的追溯解释。
```

## OD-2026-08-26-11 —— R7 条件 2 照字面**不可满足**，如实报告

R7 条件 2 要求「创建动作记 ops event」。**运行时的 `ops_events[]` 是封闭词表，
只有三种 type**：

```
OWNER_HOLD | PACKET_REJECTED_INCOMPLETE | ERRATUM
```

**没有任何一种能承载「目录已创建」。** 我不发明 type——封闭词表 fail-closed 是
它存在的理由。故该事件记于**本记录 OD-2026-08-26-9**，并在此说明为何没进
`ops_events`。**这是条件 2 的一处未满足，公开记录，不是悄悄跳过。**

**顺带补上一个真缺口**：查词表时发现 `PACKET_REJECTED_INCOMPLETE` **是**合法
type，而 2026-08-26 的**两次复审拒绝我一次都没记**。已按 schema
（`ts/type/source/actor/reason`，`source=review`）补进 `qros-state.yaml` 的
`ops_events`，`qros check` 无拒绝。**运行时一直给着这个槽位，是我没用。**
