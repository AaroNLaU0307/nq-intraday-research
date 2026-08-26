# 其余决定 —— 交 Fable 决裁席（Aaron 再次明示委托）

```ini
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=xhigh
EXECUTION_MODE=STANDARD
ROLE=决裁席（decision seat），不是审计席，不是 builder
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=2026-08-26 裁八项的那个 Fable 会话的延续；本仓任何工作会话的延续
LANE=FULL
OUTCOME_EXPOSED=UNKNOWN（席位轴分类 PENDING_AARON，见 §1）
PREREG_SEALED=N/A
SUBAGENT_OR_WORKFLOW_BUDGET=默认 3，单波最多 3 且范围互不重叠，硬上限 6 需 Aaron 另批；子 workflow 不得再生 workflow
WHY_THIS_MODEL=Aaron 2026-08-26：「其余的决定依旧让fable替我决定」
```

**DECISION_ID=dec-remaining-2026-08-26**　**DELEGATED=YES**

> **本文件必须从磁盘读取（read it from disk）。绝对路径：**
> `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_REMAINING_FABLE.md`
> **line 83 of it must read** `REVIEWED_SET_UNCHANGED_SINCE=…`。对不上 ⇒ **STOP**。
>
> 上一个 Fable 会话为找到提示文件做了三次检索（只命中文件名），成因是 builder
> 给了仓相对路径而决裁席在仓外。**已修：本件给绝对路径。**

---

## 0. **本包最重要的一件事：你上一轮说这些归 Aaron**

你 2026-08-26 裁八项时，`STILL_AARON_ONLY` 明列：

```
1. 全部执行授权：第 1 项全局文本修订、第 2 项 carve-out 行使＋hold 范围确认、
   第 3 项维护窗开启、第 6 项 profile R3 修订 ratify、各项决策记录 append。
3. 席位台账第 3 行的终分类（PENDING_AARON）与第 4 行 NOT_EXPOSED 分类值的存废。
4. GRAD pilot 排程及其与维护窗的先后。
5. 本席开工前定位披露的席位轴分类。
```

**Aaron 现在把它们又交回给你了**（原话：「其余的决定依旧让fable替我决定」）。

**所以每一项你必须先答一个前置问题：**

```
DELEGABLE = YES | NO
```

`NO` 的判据不是「重要」，而是**结构性**：它是不是对 **Aaron 本人财产或全局约束**
的许可，而非一项研究判断？例如——改 `C:\Users\Aaron\.claude\CLAUDE.md`（管辖**所有**
项目的全局指令）、在 `C:\Users\Aaron\quant-data\` 下建目录——这类「许可」与
「哪个选项更对」是两种东西。**你完全可以对同一项答
「RULING=<选项>，但 DELEGABLE=NO，执行仍须 Aaron 本人点头」。**

**自指提醒**：你是在裁「你自己上一轮划为 Aaron-only 的东西能不能委托给你」。
无法自证归零，如实写进 `SEAT_INDEPENDENCE_CONCERN`。

## 1. 开工之前

本仓已烧掉三个复审席位，**其中两个从未刻意打开任何文件**（一死于广域符号搜索，
一死于单模式定向 grep；后者就是上一个决裁席）。所以：

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不得在本仓做任何检索。** 只打开 §2 表里列出的八条。需要别的字节：列出路径，
回给工作会话，经 `PULL_PROTOCOL` 供给。

**禁区权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`（12 条），
每一条都当作关闭。** 点名两条，只为标记禁区：

```
OFF-LIMITS   ops/MC_TO_STRATEGY_MASTER_PLAN.md
OFF-LIMITS   ops/EXPOSURE_LEDGER.md
```

**允许的 outcome-clean 入口：`ops/RECOVERY_ANCHOR.md`。**

## 2. 传输核对（先做，不通过就 STOP）

```
REVIEWED_SET_UNCHANGED_SINCE=acf5a26f3b3cee0cd1d58049eab7ed73ed2ce8cd
```

```bash
git log --oneline acf5a26f3b3cee0cd1d58049eab7ed73ed2ce8cd..HEAD -- ops/PREP_ITEM1_L6_EXPOSURE_TEXT.md ops/PREP_ITEM2_QUARANTINE_MIGRATION.md ops/PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md ops/REGISTRY_SYNC_FAILURE_MODEL.md ops/REVIEWER_EXPOSURE_LOG.md ops/OWNER_DECISIONS_2026-08-26.md ops/D124_RULINGS_CLEAN_EXTRACT.md ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md
```

**必须为空。**

| SHA-256 | 字节 | 路径 | 为什么给你 |
|---|---|---|---|
| `536317a3233c31e5eaf39a9511b79f5a968b08c53946362b4731727bb6128691` | 4349 | `ops/PREP_ITEM1_L6_EXPOSURE_TEXT.md` | 第 1 项：逐字终稿＋条件 2 核验证据 |
| `58639de5add0f30f600240a7e5e8f39a4af25d2a76974c6411981686f8b6d970` | 6241 | `ops/PREP_ITEM2_QUARANTINE_MIGRATION.md` | 第 2 项：可行性实测（含仓根台账例外）＋迁移计划 |
| `aacd058f305d9ec0d0f0b1921aee03340367f729c32cdd08e73b338e3110ac77` | 6740 | `ops/PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md` | 第 3 项：补丁设计＋`header.py:201` 范围发现 |
| `8734c430534314e8c7592c998e43a0485b90c37b9b0fb9df5d5736200d979424` | 5448 | `ops/REGISTRY_SYNC_FAILURE_MODEL.md` | 第 7 项边界 (3)(4)；两条致命通道 |
| `14610486a4b823452c93164986a2485bb8eaacf3d6f618cb0f35d8288c4d4826` | 10039 | `ops/REVIEWER_EXPOSURE_LOG.md` | 席位轴台账：第 3／4／5 行待分类 |
| `41c69205401aa1e1516ab46c0ee4a2a9b4276f1f6a3fe7de130293c001287d03` | 6225 | `ops/OWNER_DECISIONS_2026-08-26.md` | Aaron 采纳八项的记录＋逐项结算表 |
| `5d6e8b65b4a7f9d030d13a074f40a9c388bad763e17c610b9c529d14e5634745` | 10350 | `ops/D124_RULINGS_CLEAN_EXTRACT.md` | D-1／D-2／D-4 裁决逐字副本（原件隔离） |
| `5116f7b03dabe6cc4a8a2357b02b4b30e3a9227d050e41d9c1f0943262ed7dd3` | 33457 | `ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md` | 上一轮 Fable 八项裁定全文＋builder 审核 |

## 3. 要你裁的（第 6 项不在内，它走 Sol 复核）

### 组 A —— 三个「选项题」

| # | 题 | 选项 |
|---|---|---|
| **R1** | **第 2 项：仓根台账怎么办。** 裁定说「把 `carries_outcome` 全部路径迁入一个子树」，但 `EXPOSURE_LEDGER.md` **在仓根、不在 `ops/` 下**；搬它等于把仓根权威台账挪进 `ops/`，是改身份不是改路径 | (A) 只迁 `ops/` 下的 11 条 · (B) 两份都迁并改写恒等测试端点 · (C) 仓根那份不该在隔离名单上 |
| **R2** | **第 3 项：修补范围。** `_SAVE_DIR` 缺陷在运行时里**有两处**，D-4 只点名 `packet.py:64`，未点名 `header.py:201`（内联 `runs/prompts/`）。后者今日潜伏（ITSF 从未用过 `qros prompt`），且它连 `repo` 参数都不收，配置化要改签名 | (A) 只按字面修 packet · (B) 一并修 · (C) 一并修但需你补一句授权范围 |
| **R3** | **第 2 项：hold 范围。** Aaron 08-25 说「Sol 返回前不推进」。Sol 已返回，但 D-2 条件 5 要求含糊时取限制性读法，故 builder 不自行判其失效 | 失效 · 仍覆盖本项 · 部分覆盖（写明哪部分） |

### 组 B —— 四个「许可题」（先答 `DELEGABLE`）

| # | 题 |
|---|---|
| **R4** | **第 1 项**：准不准 builder 用 `ops/PREP_ITEM1_L6_EXPOSURE_TEXT.md` §2 的逐字终稿替换全局 `CLAUDE.md` 第 90 行。**该文件管辖所有项目，不只本仓。** |
| **R5** | **第 2 项**：carve-out 的行使（编辑注册表 `path` 字段以追踪迁移）＋迁移执行授权 |
| **R6** | **第 3 项**：何时开 qros-runtime 维护窗；以及与第一个 GRAD pilot 的先后（你上一轮建议「先修再 pilot」，条件 4 已给排序失败的回退） |
| **R7** | **第 7 项**：准不准在 `C:\Users\Aaron\quant-data\` 下**新建一个见证目录**。ND1 把「目录创建／写探针／执行」列为**三条不得合并**的独立授权，这是第一条 |

### 组 C —— 席位轴分类（三行）

| # | 题 |
|---|---|
| **R8** | 第 3 行（你上一轮，一次定向 grep 触到隔离锚一行治理文本）现为 `PENDING_AARON` —— 终分类是什么？ |
| **R9** | 第 4 行是 builder 新引入的 classification 值 `NOT_EXPOSED`（记录一个**没被烧**的席位，作为缓解措施奏效的量度）。这个值该不该存在于一份名为「暴露台账」的文件里？ |
| **R10** | 第 5 行（上一个决裁席开工前三次**仅文件名**的定位操作，零内容命中）—— 终分类是什么？先例是第 3 行以「一行治理文本」得 `PENDING_AARON`。 |

## 4. builder 要你知道的三条实测（都在送审件里，此处只标位置）

1. **第 2 项**：生产代码对隔离路径**零路径引用**（唯一 `src/` 命中在模块 docstring
   内，AST 实测行范围 1–43）。32 条待改全在测试／配置／文档。
2. **第 3 项**：`packet.py:146` **已收 `repo` 却没用它**——接缝早在；而
   `header.py:200` 连 `repo` 都不收。两者难度不对称。
3. **第 7 项**：致命通道**是两条不是一条**——你上一轮写「半写行会死在六格解析上」
   不成立（解析器对格数不符是 `continue` 静默丢弃，且 registry 被 clean gate
   白名单豁免）。**药没问题，病理描述漏了一条**，已在 `OWNER_DECISIONS_2026-08-26.md`
   OD-…-4 更正。

## 5. 只裁，不做

- **只读。** 不改文件、不打补丁、不实现任何一项。
- 不追加任何 registry／台账事件；不签发任何授权；不填 P2 占位符；
  不在 `C:\Users\Aaron\quant-data\` 下创建目录；不读真实数据；不执行任何 run。
- **不得自我升格**：本文件授权你**裁**，不授权你**写**。含糊取限制性读法。
- **先跑机器检查再花模型 token**。

## 6. 返回格式

每一项（R1..R10）一个块：

```
ITEM=<R1..R10>  TITLE=<一句话>
DELEGABLE=YES|NO   若 NO：为什么是结构性的，以及仍需 Aaron 做什么
RULING=<你的实质选择，含选项名与理由>
CONDITIONS=<可机械检查；每条指明由谁落地>
FALSIFIER=<观察到什么就推翻本裁>
CONFIDENCE=<HIGH|MEDIUM|LOW> ＋ 一句为什么
```

之后再给：

```
CROSS_ITEM_CONFLICTS=<十项之间是否互相矛盾>
SEAT_INDEPENDENCE_CONCERN=<你在裁「你自己划为 Aaron-only 的东西能否委托给你」>
STILL_AARON_ONLY=<即使被委托，你判断仍必须由他本人做的，逐条>
STRONGEST_OBJECTION_TO_MY_OWN_RULINGS=<对你自己这十项最强的反对>
SEAT_STATUS=BLIND|EXPOSED|UNCHANGED（如实报）
INDEPENDENCE_STATEMENT=<按维度分别陈述>
```

`SEAT_STATUS` 请务必如实——**烧掉席位不消耗研究自由度**，两轴分账
（`ops/REVIEWER_EXPOSURE_LOG.md` 记席位轴，在送审集内可读）。瞒报才是不可逆损失。
