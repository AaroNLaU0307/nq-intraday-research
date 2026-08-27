# 11 处不可达引用如何处理 —— 决裁包

```ini
DELIVERY_STATUS=ISSUED
REVIEW_ID=dec-citations-2026-08-27
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=决裁席（adversarial decision seat）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被裁字节的作者；dec-s5-r4-2026-08-27 的那个会话；
            dec-registry-migration-2026-08-27 的那个会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
DELEGATED=YES —— Aaron 2026-08-27「给我决策的部分一律让 fable 替我选择，我同意」
SUBAGENT_OR_WORKFLOW_BUDGET=0
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_CITATION_REMEDIATION.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 0. 处境

`ops/*.md`（94 份）里有 15 处 `ops/X` 形式的路径引用不可达。4 处合法（行文占位、
方案提出的路径）。**11 处是真问题，且分两类，处理方式很可能不同。**

builder 已建机械保障把当前状态钉死（不会增长），**但一条引用都没改** —— 见 §4，
不是怠工，是这件事在不同文档里有相反的正确答案。

---

## 1. 传输核对（先做，不通过就 STOP）

| SHA-256 | 字节 | 路径 |
|---|---|---|
| `c2d51f80dce7a8aa47f274fd1867c4404ef30d53cb52c7cb30e00a8c04e014a0` | `4873` | `ops/FINDINGS_DANGLING_CITATIONS_2026-08-27.md` |
| `eb3b089f30f3a6b6c3dfb371e27733eb959d02323f031fa8a1c0801a3f1b67fb` | `13128` | `tests/test_cited_records_exist.py` |
| `a61c125b4e2e551955ce59816c9ccbc6a449a91d7f7701095eeb586e5c155f4b` | `2563` | `ops/OUTCOME_CARRYING_ARTIFACTS.json`（权威禁区表） |
| `5d6e8b65b4a7f9d030d13a074f40a9c388bad763e17c610b9c529d14e5634745` | `10350` | `ops/D124_RULINGS_CLEAN_EXTRACT.md`（争议焦点文档） |

任一条不匹配 ⇒ STOP。

---

## 2. 禁区 —— 本节必须随包

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不 grep、不 rglob、不广域符号搜索、不「顺手看一眼」。** 需要哪个路径就列出来，
由工作会话提供逐字节内容。

**为什么是禁令而不是提醒**：已烧掉的三个席位里，**第二个从未打开过那份隔离文件**
——一次广域符号搜索把片段带了出来；第三个只做了**一次单模式定向 grep**，同样触到了。

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`（本包已随附，
逐字读它，把里面每一条路径当作关闭）。尤其点名（以下全部为禁区）：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

**许可起点**：`ops/RECOVERY_ANCHOR.md`（outcome-clean，永不隔离）。

**两条暴露轴不得合并**：研究轴那份本身就在禁区名单上；席位轴
`ops/REVIEWER_EXPOSURE_LOG.md` outcome-clean，可读。

**本包特别提示**：§3 会逐字列出 8 个隔离文件的**文件名**。文件名不是内容，
列出它们是为了让你能判断如何引用它们。**不要打开其中任何一个。**

---

## 3. 第 1 件 · 8 处指向隔离件的陈旧引用

文件移进了 `ops/outcome_quarantine/`，引用留在原处写着 `ops/X.md`。
**这 8 个对象全部在 `carries_outcome` 表上** —— 陈旧引用指向的，恰是会烧席位的那批。

```
ops/DECISION_PACKET_ND2_ND3.md              ops/ND2_ND3_RULING_REVIEW_FINDINGS.md
ops/MC_DR5_BUILD_PACKET.md                  ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md
ops/MC_TO_STRATEGY_MASTER_PLAN.md           ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
ops/ND2_ND3_FABLE_DECISION_PROMPT.md        ops/S0_T001_RESULT_DECISION_ADDENDUM.md
```

### 危害不是「文件找不到」，是找不到之后会发生什么

引用解析不到 ⇒ 读者搜索 ⇒ 这正是烧掉第二、第三席的那个动作。
**一条陈旧引用是一份搜索邀请函，而被邀请去搜的对象在禁区表上。**

### 三个选项

```
选项 REPOINT   —— 引用改指 ops/outcome_quarantine/X.md
  优点：引用可解析，读者不必搜索；且与现行惯例一致（S5/R4 包 §2 就逐字点名
        隔离路径作为禁区）。
  代价：把隔离路径写进了更多文档，其中包括刻意做成 outcome-clean 的那些。

选项 MARK_ONLY —— 引用不给路径，改成具名标记，如
  「（该记录已隔离，见 ops/OUTCOME_CARRYING_ARTIFACTS.json；不得打开）」
  优点：既消除搜索诱因，又不在文档里散播隔离路径。
  代价：读者若确有正当需要读它（非盲席位），得多一跳。

选项 PER_DOCUMENT —— 按文档类别分别处理
  决裁包／提示词类 -> REPOINT（它们本就要点名禁区）
  outcome-clean 摘录类 -> MARK_ONLY（指进隔离区与其存在目的相反）
  优点：每处都对。代价：需要一条可机械判定的分类规则，否则又回到「实现者自选读法」。
```

**请裁三选一**，若选 PER_DOCUMENT，**请给出分类判据本身**（builder 不自拟）。

### 争议焦点：`ops/D124_RULINGS_CLEAN_EXTRACT.md`（已随包）

这份是**刻意做成 outcome-clean 的裁定摘录**，目的正是让席位不必去碰隔离原件。
它当前引用 `ops/MC_TO_STRATEGY_MASTER_PLAN.md` 与
`ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md` 两个陈旧路径。

**把它的引用改指进隔离区，与它存在的目的相反。**
这正是 builder 不自行统一处理的原因：同一处改动，在决裁包里是对的，在这里可能是错的。

---

## 4. 第 2 件 · 3 处指向从未存在过的文件

```
ops/MC_RUN_REGISTRY.md              <- DECISION_MC_REGISTRY_COLLISION.md
                                       RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md
ops/STRATEGY_COUNCIL_ROUND4_LOCK.md <- DECISION_PACKET_N00_AND_ND1.md
                                       N00_N08_PROVENANCE_AUDIT_2026-08-25.md
ops/SUPPLEMENT_LEDGER.md            <- DECISION_PACKET_N00_AND_ND1.md
```

**实测**：`git log --all --diff-filter=AD -- <path>` 对三者均无输出，工作区亦无 ——
**全历史从未增、从未删**。守卫每次运行重测这一点。

**与 2026-08-26 那次是同一形态**：一份 fresh Sol 的 HOLD 裁定只存在于聊天里，
而一份 handoff 引用了一份「记录」，磁盘上那份记录内容不同。当时靠人工发现并逐字恢复。
**这三处此前无人发现。**

### 请裁

```
1. 这三份记录本该存在（有人写了没提交），还是引用本身是错的？
   —— 若你判定无法从现有字节确定，请直接说 UNRESOLVED_FOR_AARON，不要猜。
2. 在弄清之前，引用要不要就地标注（如「该记录不在仓中 —— 见
   FINDINGS_DANGLING_CITATIONS_2026-08-27.md」）？
   —— 不标注，则下一个读者会重走一遍今天这条路。
3. 这一类是否需要一条常设规则：新增引用前必须存在被引用的字节？
   —— 机械形式已就位（tests/test_cited_records_exist.py 会拦下新增的悬空引用），
      问的是它该不该升格为纪律条款。
```

---

## 5. builder 已落地的（供你判是否修对了）

```
tests/test_cited_records_exist.py     14 测试，随包
  新增未登记的悬空引用 -> 红 · 陈旧豁免（已可解析却仍登记）-> 红
  分类名超出四个合法值 -> 红 · 隔离件被降级成「行文占位」-> 红
  谎称某件在隔离区里 -> 红 · 扫描返回空 -> 红（本文件自身受同一规矩约束）
  禁区表：为空 -> 红 · 含悬空路径 -> 红 · 隔离区里有未申报的文件 -> 红
```

**首版有洞，变异测出后才补**：把隔离件的分类从 `QUARANTINED_MOVED` 改成
`PROSE_PLACEHOLDER` 时全绿 —— 唯一有检查的类，正是被逃离的那一类。
现在每个分类都可证伪。

**明确未做机械化的一点，如实写出**：`PROPOSED_NOT_YET_EXISTING` 与
`CITED_BUT_NEVER_EXISTED` 在磁盘上完全同形，二者之分是意图判断。曾试过用引用方
文档名（PACKET/PROPOSAL 即视为提案）来区分，已否决 ——
`DECISION_PACKET_N00_AND_ND1.md` 引用 `SUPPLEMENT_LEDGER.md`，该规则会把一份
真正缺失的记录悄悄重分类为合法提案。**说明它不可机械判定，好过假装它可以。**

---

## 6. 常设禁令（对你同样在 force）

不读真实 Development 数据；不执行 supplement／MC／S0／strategy；不在
`C:\Users\Aaron\quant-data\` 下创建任何目录；不做写探针；不追加任何 registry／
exposure 事件；不写 `APPROVED`／`EFFECTIVE`／`RATIFIED` 值；**不代签 P2**；
不执行任何迁移；不推送、不打标签、不 amend。

**READ_ONLY**：只裁不做，零文件修改。**不得打开 §3 列出的任何一个隔离文件。**

---

## 7. 返回格式

```
ITEM=CITATION-REMEDIATION
DELEGATED=YES
TRANSPORT_PRECHECK=PASS|STOP

ITEM=第 1 件 8 处陈旧引用
  RULING=REPOINT|MARK_ONLY|PER_DOCUMENT
  若 PER_DOCUMENT：给出可机械判定的分类判据本身
  D124_RULINGS_CLEAN_EXTRACT 单独作答
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE
ITEM=第 2 件 3 处从未存在
  三问逐条作答
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE

BUILDER_WORK_ASSESSED=<§5，修对了|有问题>
STRONGEST_OBJECTION=<对你自己两条裁定中最弱的那条>
STILL_AARON_ONLY=<你认定不可代裁的>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本裁定不释放任何 gate，不授权任何迁移，不创建任何目录。**
