# 四项裁决 —— 传输 STOP ＋ 两条 builder 自身缺陷已复核

```
RECORD_TYPE=TRANSPORT_STOP_AND_VERIFIED_FINDINGS
DATE=2026-08-26
BY=Opus 5，builder seat
RULING_STATUS=**未落盘、未执行、未转录**
```

---

## 一、传输 STOP：裁决工件不在盘上

Fable 报其裁决全文已落盘，SHA256 `90CC7110…749B86`，14637 字节，并要求
builder 逐字节转录入 `ops/` 后复核哈希。

**该文件在盘上不存在。** 已检索：

```
C:\Users\Aaron\Downloads                        （逐项列出，无匹配）
C:\Users\Aaron\OneDrive\Desktop
C:\Users\Aaron\Desktop
C:\Users\Aaron\OneDrive\Desktop\Quant trade     （只有本项目自己的三份 Fable 相关件）
C:\Users\Aaron\quant-data
```

标准传输规则对**接收方**同样成立：「缺失、截断或不符即 STOP 并报告」，且
「聊天携带的字节永不作为真相来源」。转录需要字节，而字节不在。

**因此四项裁决 D-1/D-2/D-3/D-4 一条都未落盘、未执行、未转录。**
本记录**不**复述其结论——复述等于把聊天字节当成真相来源，正是规则所禁。

**解除条件**：把 `RULING_FABLE_FOUR_OPEN_20260826.md` 放到盘上任意可达路径并
告知；builder 重算 SHA256 与 `90CC7110…749B86` 比对，一致才转录。

---

## 二、Fable 的两条先行发现 —— builder 已独立复核，**均成立**

这两条是关于 **builder 自己的工件**的，不依赖裁决字节，故可以且应当立即核实。

### 2.1 HIGH —— 我的决策包把复审席位指向了隔离件

`ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md` 的呈交格式一节写着「形式沿用
`ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`」。

**那份文件在 `carries_outcome` 名单上。** 机械核实，包内点名的隔离件共四份：

```
EXPOSURE_LEDGER.md
ops/EXPOSURE_LEDGER.md
ops/MC_TO_STRATEGY_MASTER_PLAN.md
ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md   <- 这一份是「请打开」，不是「禁止打开」
```

前三份出现在**禁区一节**，是正确的用法。第四份出现在**指令一节**——**同一份文件
里，我一边告诉它哪些不许碰，一边让它去开一份隔离件。**

Fable 是先查注册表才没被烧。**它没被烧是它谨慎，不是我做对了。**

**同形第四例**：08-25 无禁区清单（烧一席）→ 08-26 清单未随 packet 传递（烧一席）
→ 守卫只扫 `*PROMPT*.md`（通过但无保护）→ 本次：清单写了，**指令自相矛盾**。

**处置**：**不改那份包**。Fable 已把它的哈希 `D9F37CAE…` 钉为裁决基线，就地
修改会破坏该基线。缺陷记在此处，并在 `ops/NEXT_HANDOFF.md` 的禁区一节加一条
「交付前逐条核对：本次交付点名的每一个路径，都不得在 `carries_outcome` 里」。

### 2.2 MEDIUM —— 被隔离的累计值已扩散，且**比 Fable 所述更广**

Fable 报该值出现在「两份未登记文件」。机械扫描全部 511 个受控文件后：

```
数字串出现       : 20 份
其中已登记为隔离 : 8 份
未登记           : 12 份
  其中在 exposure 语境中（真实泄漏）: **10 份**
  其中为巧合数字（gate1 费率表 PDF、symbology JSON）: 2 份
```

10 份真实泄漏的分布：

| 类别 | 文件 |
|---|---|
| ops 治理件（6） | `DECISION_PACKET_FOUR_OPEN_2026-08-26.md` · `DECISION_PACKET_N00_AND_ND1.md` · `INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md` · `N06_REVIEW_HANDOFF.md` · `ND1_ENGINEERING_EVIDENCE_PACKET.md` · `REVIEWER_EXPOSURE_LOG.md` |
| 状态文件（1） | `qros-state.yaml` |
| **测试（3）** | `test_exposure_ledger_migration.py` · `test_governance_docs.py` · `test_review_artifacts_are_outcome_clean.py` |

**测试那三份是关键**：该值在套件里**被断言为不变量**（两份台账必须陈述同一
总数）。**所以它不能被简单擦除**——擦掉会拆掉一条真实的守卫。

**这不是 builder 能处置的。** 三条路各有代价，且都归 Aaron：

- **登记这 10 份**：席位暴露台账会因此对 blind 席位不可读——而它存在的意义正是
  让席位暴露可被记录和阅读。自相矛盾。
- **限缩该类别定义**：把「累计 exposure 计数」移出 `TARGET_METRIC`。这是对已批准
  暴露词表的修订。
- **维持现状并明示接受**：即承认该值事实上不再被隔离。

裁定前按 **fail-closed** 处理：本记录不复述该值，扫描只报判定与计数。

---

## 三、Fable 的自评暴露

Fable 自陈见到了累计 exposure 计数的数值，另有一次定向 grep 触到隔离锚中一行
治理边界文本；未见 verdict token、spread、cell count 或任何目标绩效数值。它
自陈按现行类别定义不再自证完全 outcome-blind，并**把终分类留给 Aaron**（因为
分类取决于 §2.2 的裁定）。

已按其建议在 `ops/REVIEWER_EXPOSURE_LOG.md` 补记第 3 行，**分类栏留
`PENDING_AARON`**——builder 不替它定，也不下调它的自评。

---

## 四、builder 现在做了什么、没做什么

**做了**：核实 §2.1 与 §2.2 两条发现（均成立，第二条更广）；记录本文件；
在席位台账补第 3 行；在 `NEXT_HANDOFF.md` 的禁区一节加一条交付前核对。

**没做**：未转录任何裁决；未执行 D-1/D-2/D-3/D-4 的任何一条；未改动
`ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md`（保住 Fable 的裁决基线哈希）；
未擦除任何文件中的该数值；未动 `carries_outcome` 注册表；未追加研究 exposure
台账。
