# N00 与 N08 —— 只读 provenance 审计

```
RECORD_TYPE=PROVENANCE_AUDIT
SCOPE=N00（Round-4 权威文本）／N08（延后审计窗口 9/12 簇）
DATE=2026-08-25
BY=Opus 5，builder seat（本审计只读；无重建、无新定义冒充旧 authority）
HEAD=0991d6f24fcc9b8744606eb294dbb8b73ef011c7
REQUESTED_BY=Aaron，2026-08-25：「你自己做完整的 read-only provenance audit」
```

**本审计未做**：零真实数据读取；零执行；零 registry／exposure 事件；零目录
创建；未读 `ops/S0_T001_RESULT_DECISION_ADDENDUM.md` 与 `EXPOSURE_LEDGER.md`
的揭盲行；未重建任何缺失内容；未把新定义写成旧 authority。

---

## 第一部分 —— N08：延后审计窗口（9/12 簇）

### 1.1 它到底是什么

全仓**唯一**的定义是主计划 §4 DAG 的一行：

```
| N08 | N06 | 延后审计窗口（9/12 簇） | 工程 | none | — |
```

「9/12 簇」是什么、12 簇是哪 12 簇、9 簇为何延后——这一行之外**没有任何
文字**。

### 1.2 搜过哪里（全部零命中）

| 搜索面 | 关键词 | 结果 |
|---|---|---|
| 工作树 `ops/*.md`、仓根 `*.md` | 延后审计／审计窗口／audit window | 只命中主计划那一行与本审计引用它的文件 |
| git history（`--all`，pickaxe `-S`） | `9/12`、`簇`、`cluster` | 只命中我自己 2026-08-24／25 的 commit |
| git commit messages（`--all --grep`） | 簇／cluster／audit | 无历史来源 |
| 全仓 | `逻辑审计`／`LOGIC_AUDIT`／`全库审计` | **零** |
| 全仓 | 「已完成 3 簇」的任何审计报告 | **零** |
| git history（`--diff-filter=A`） | 任何 council／round4／matrix 命名的新增文件 | 只有无关的 lineage matrix 与我自己的 N06 提示词 |

### 1.3 为什么树里找不到——来源链本身不在仓内

主计划自述其来源链是：Fable 架构会议 V1 → V1.1 → V1.2 → Codex 综合稿
`OPUS5_MC_TO_STRATEGY_V1`。**这四份源文档全部不在仓内**（`OPUS5_MC_TO_STRATEGY_V1`
只作为字符串被主计划与 packet 引用，从未作为文件入库）。主计划在 `ba7fa4a`
被创建时就已含 N08 那一行。

所以「9/12 簇」是**从一份只存在于聊天里的源文档抄进来的**。这不是「文件丢了」，
是它从未入过库。

### 1.4 一条必须披露的线索，以及为什么不采用

本 agent 持有一份跨会话记忆笔记，其中写着「全库逻辑审计剩余 9/12 簇
（report／evidence／handoff／entry-script／runner-runinfra／dataset-context／
stability-study／output-proof-oracle-loader／governance-docs）……已完成 3 簇
零确认 critical/major」。

**它不构成 authority，本审计不据以重建范围**，理由三条：

1. 它是 agent 自撰的未经复核笔记，不是仓内工件，未经任何 review；
2. 树与 git history **对其中任何一个簇名零命中**——九个名字一个都对不上；
3. Aaron 本轮第 7 条明令：「对缺失历史内容禁止推测重建；新的定义不能伪装成
   旧 authority」。拿一份未复核笔记去填一个已批准 DAG 节点的范围，正是该条
   要防的事。

记在这里，是因为**隐瞒一条线索比采用它更糟**。若 Aaron 认得这九个名字并能
确认其出处，N08 就从 DROP 变成 RECOVER；在他确认之前，它只是一条线索。

### 1.5 治理作用与下游依赖（机械扫描）

对 §4 DAG 全部 20 行做依赖扫描：

```
以 N08 为前置的节点：无。一个都没有。
```

DAG 表自身给出的属性：`权限=工程`、`数据面=none`。即 N08 **不承担**
preregistration／exposure／authority／provenance／candidate-selection 中的
任何一项——这不是我的判断，是那张已批准的表自己写的。

### 1.6 丢掉它会不会削弱审计能力

不会，且理由不是「找不到所以算了」：

- **一个没有范围的节点执行不了任何审计。** 它今天提供的覆盖是零。
- 树内已有的独立复审覆盖：11 份 Codex review packet（M6／M6.1／M6.1.1–1.4／
  1.6／1.7／1.8／IR26／S0_CLOSEOUT_FINAL）＋ N06 四轮 exact-tree（终态
  ACCEPTED_WITH_DISCLOSED_RESIDUAL）＋ Fable 独立一致性审计 V2（2026-08-20）＋
  Stage I 记录 ＋ 4167 项测试。
- **留着它反而有害**：一个永远无法被标记为完成的节点，是一份永久的假未决项，
  会稀释真正的阻断项（今天真正的阻断项是 N09 与 N00）。让 Aaron 以为 N08
  覆盖了什么、而它什么也没覆盖——这才是审计能力的净损失。

### 1.7 N08 结论

```
N08 = DROP（作为 DAG 节点废弃）
理由 = 全仓仅一行表格定义、来源文档从未入库、零下游依赖、DAG 表自述
       数据面=none／权限=工程故不承担任何关键治理职能；其可能意图已由
       11 份 Codex packet＋N06 四轮＋Fable V2 覆盖。
警告 = 若日后仍想做一次广域逻辑审计，那是一次**新的范围裁定**，必须以新
       名义登记，不得写成「恢复了 N08」。
```

---

## 第二部分 —— N00：Round-4 权威文本

### 2.1 它到底是什么（两层，主计划 §11.4 明令勿合并）

```
N00_STATE_RULING_SETTLES=WHETHER_PRIMARY/HYPOTHESIS/WRAPPER_WERE_SELECTED
N00_STATE_RULING_DOES_NOT_SUPPLY=ROUND4_MATRIX_TEXT_OR_CANDIDATE_DEFINITIONS
```

- **第一层**：Aaron 对三个字段的状态裁决（`PRIMARY_SELECTED` /
  `HYPOTHESIS_SELECTED` / `DESIGN_WRAPPER_APPROVED`）。
- **第二层**：五份权威正文，清单在 `ops/DECISION_PACKET_N00_AND_ND1.md`
  §D.1.3 `N00_MISSING_AUTHORITY_CHECKLIST`：

```
[ ] 1. ROUND4_JOINT_MATRIX_FULL_TEXT            = MISSING
[ ] 2. FABLE_CONTINUATION_CANDIDATE_DEFINITION  = MISSING
[ ] 3. SOL_FAILED_BREAK_RECAPTURE_DEFINITION    = MISSING
[ ] 4. PER_CELL_JOINT_SIGNOFF_OR_EQUIVALENT     = MISSING
[ ] 5. OPTION_C_OR_OTHER_WRAPPER_DEFINITION
       + ITS_AARON_STATE_RULING_SOURCE          = MISSING
```

§11.4 的效力句：**即使三字段全裁为 YES，五项不齐就不得开始任何
candidate-specific strategy build。**

### 2.2 搜过哪里

| 搜索面 | 结果 |
|---|---|
| `ops/STRATEGY_COUNCIL_ROUND4_LOCK.md`（既定的落盘目标） | 不存在，且 **git history 里从未存在过** |
| git `--diff-filter=A` 全历史新增文件 | 从未有 council／round4／joint-matrix 工件入库 |
| 全仓 `STRATEGY_COUNCIL` | 8 处命中，**全部只是状态令牌**（`STRATEGY_COUNCIL=LOCKED` / `BLOCKS_STRATEGY_COUNCIL=NO`），无一携带正文 |
| 兄弟仓 `quant-research-knowledge-base` | **零命中**（记忆笔记里「见 KB」指的是那条 KB 笔记，不是 KB 仓内容） |
| `Quant trade\` 下全部 14 个仓 | `STRATEGY_COUNCIL` 只出现在 ITSF 内 |
| 文件名搜索 round4／council／joint matrix／联合矩阵（全盘 maxdepth 4） | 只有我自己的 `N06_ROUND4_SOL_PROMPT.md`（无关） |

**一条待 Aaron 亲自核的线索**：`ops/S0_T001_RESULT_DECISION_ADDENDUM.md:40`
含单个词 `recapture`（用 `-o` 只取匹配词，未读该行、未读第 26 行）。单次出现
不构成候选定义，但该文件 Aaron 可自由阅读，值得他扫一眼。

### 2.3 恢复路径（已在册，不是仓内问题）

`ops/DECISION_PACKET_N00_AND_ND1.md` §D.1.3 已写死补交路径：

```
Aaron 提供 sealed proposal 原文 → 逐字转录至
ops/STRATEGY_COUNCIL_ROUND4_LOCK.md → sha256 → 入 FREEZE_LOG.md → 签署
本会话不得凭记忆、推断或摘要重建任何一项
```

即：**这不是「仓里找不到」的问题，是「Aaron 手上还有没有那份 sealed proposal
原文」的问题。** 任何 AI 都无法代为解决。

### 2.4 治理作用与下游依赖（机械扫描）

```
以 N00 为前置的节点，恰两个：
  N18-C   N17∈{GO,β→GO,α→GO} ＋ N00 ＋ Aaron freeze ＋ build 口令
  N18-I   S0/MC 终局（任意类别）＋ N00 ＋ Aaron 明确批准
N09…N17 之中，无一以 N00 为前置。
```

N00 承担的正是 **candidate-selection authority**——Aaron 本轮列出的
「不得 DROP」类别之一。两候选还必须**分立登记**，不得被记成同一 raw variant
的两种写法；没有正文就做不到这一点。

### 2.5 N00 结论

```
N00 = KEEP（保持 unresolved）
理由 = 它是 candidate-selection authority，且 N18-C／N18-I 两条 build 路径
       都以它为前置；缺的是权威正文本身，禁止重建（§D.1.3 明令）。
最小解决动作 = Aaron 提供 sealed proposal 原文，逐字转录 → sha256 →
       FREEZE_LOG → 签署；三状态字段另行裁决。
若原文确已不存 = 这不是可以静默 DROP 的项，见第三部分。
```

---

## 第三部分 —— 唯一需要 Aaron 本人决定的事项

**只有一件**：Round-4 sealed proposal 原文是否还在他手上。

- **在** → 走 §D.1.3 的补交路径，N00 从 KEEP 转 RECOVER，candidate-specific
  build 的门解开。
- **不在** → 才轮到 `FORMALLY_LOST`。但**宣告丢失本身不解锁任何东西**：
  §11.4 的效力是「五项不齐即不得 build」，所以宣告丢失＝
  **candidate-specific build 永久封锁**，除非另行授权一次**新的**候选定义
  程序（新 authority，新登记，明确写明它不是 Round-4 的恢复）。
  这第二步是一次独立的范围裁定，不包含在「宣告丢失」里。

N08 不需要 Aaron 决定任何事——除非他认得 §1.4 那九个簇名并能给出出处，
那样它就变成 RECOVER。

---

## 附录 —— 阻断关系一览

| 项 | 阻断 N09→N17？ | 阻断 N17 之后的 candidate-specific build？ |
|---|---|---|
| **N08** | 否（零下游依赖） | 否 |
| **N00** | 否（不在 N09…N17 任何一条前置里） | **是**（N18-C 与 N18-I 都以它为前置） |
