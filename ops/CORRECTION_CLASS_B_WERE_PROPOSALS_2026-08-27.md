# 更正：三处「从未存在」全部是提案，不是凭空引用

```ini
REVIEW_ID=correction-class-b-2026-08-27
DELIVERY_STATUS=RETURNED
RECORD_TYPE=BUILDER_SELF_CORRECTION
CORRECTS=ops/FINDINGS_DANGLING_CITATIONS_2026-08-27.md §3.B
AFFECTS=ops/RULING_FABLE_CITATIONS_2026-08-27.md 第 2 件（前提失效）
```

**本件按裁定 C2 出具**：被更正的 findings 曾被已签发决裁包以哈希钉死
（`ae0e5f84…`，决裁席逐字节核过），**不就地改写**，以本件承载更正。

---

## 0. 一句话

我把三条路径分类为 `CITED_BUT_NEVER_EXISTED`（「被当作既存记录援引，而记录从未存在」）。
**三条全部错。逐条读引用行之后，三条都是提案或声明的落盘目标。**
决裁席据我的分类推理，因此其第 2 件的事实前提失效。

---

## 1. 逐条更正（证据为引用行本身）

### 1.1 `ops/MC_RUN_REGISTRY.md` —— 一个**被否决的选项**的假设文件

```
DECISION_MC_REGISTRY_COLLISION.md:167   ### R1 — a separate MC registry file
DECISION_MC_REGISTRY_COLLISION.md:169   `ops/MC_RUN_REGISTRY.md`, with its own dirty allowlist entry.
```

同一文档并列 `### R2`（builder's recommendation）与 `### R3`。而
`RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md` 写着 **`RULING=R2`**。

**即：R1 未被采纳，这个文件按设计永远不会存在。** 另一处引用
（`RULING_PROPOSAL…:110`）明白写着 “under R1 a separate `ops/MC_RUN_REGISTRY.md`
is parsed by NOBODY until N13 wires it” —— 全程虚拟语气。

### 1.2 `ops/STRATEGY_COUNCIL_ROUND4_LOCK.md` —— 已在册恢复路径的**落盘目标**

```
N00_N08_PROVENANCE_AUDIT_2026-08-25.md:138
  | `ops/STRATEGY_COUNCIL_ROUND4_LOCK.md`（既定的落盘目标） | 不存在，且 **git history 里从未存在过** |
```

**这条 2026-08-25 就被记下了，而且是穷尽搜索之后**：全历史 `--diff-filter=A`、
全仓 `STRATEGY_COUNCIL`（8 处命中全是状态令牌）、兄弟仓 `quant-research-knowledge-base`、
`Quant trade\` 下全部 14 个仓、全盘文件名搜索。同一节还写明恢复路径已在册
（`DECISION_PACKET_N00_AND_ND1.md` §D.1.3：Aaron 提供 sealed proposal 原文 → 逐字转录
→ sha256 → 入 FREEZE_LOG → 签署），并给出结论：

> **这不是「仓里找不到」的问题，是「Aaron 手上还有没有那份 sealed proposal 原文」的问题。**

**审计不是「引用即断言其存在」——审计正是在报告它不存在。**

### 1.3 `ops/SUPPLEMENT_LEDGER.md` —— 字面上的一个待裁问题

```
DECISION_PACKET_N00_AND_ND1.md:161
  1. 是否新建 `ops/SUPPLEMENT_LEDGER.md`（现势索引，逐字段可由 registry 事件重建；
     工程建议：建，registry 仍是唯一事件真相源）。
```

---

## 2. 我错在哪里，以及为什么这个错特别难看

机械的那一半我量了，而且是对的：三条在 git 全历史中确实无增无删。
**意图的那一半我没量，直接断言了。**

而我是在**同一份文档里论证「意图不可机械判定」之后**做这件事的——findings §4 与
决裁包 §5 都写着「两类在磁盘上同形、事后不可机械区分」。那句话是对的，
但它推不出「所以可以凭眼判」。**意图确实不在文件系统里，它就在引用行的上下文里，
而上下文是可读的——我只是没读。**

更难看的一点：`STRATEGY_COUNCIL_ROUND4_LOCK` 那条我还写了「这三处此前无人发现」。
**两天前的一份审计不仅发现了，还穷尽搜索、写明了恢复路径和结论。**
我的扫描器命中了那一行，我没有读它。

---

## 3. 对决裁席那份裁定的影响，逐块认定

| 裁定内容 | 状态 |
|---|---|
| **第 1 件全部**（MARK_ONLY · D124 一字不改 · C1–C4） | **不受影响，成立** —— 它论的是 8 处隔离引用，与本更正无关 |
| **第 2 件 · 问 1**（三条均 UNRESOLVED_FOR_AARON） | **前提失效**。席位写「三处均以援引既存记录的语气被引」，并特别举 `SUPPLEMENT_LEDGER` 说它「读起来就不是提案」——而原文正是「**是否新建**……工程建议：建」。席位是盲席、未持有那些字节，它推理的是**我给的分类** |
| **第 2 件 · 问 1 给 Aaron 的三条追问** | **两条已由磁盘回答**（1.1 R1 未采纳；1.3 字面是待裁问题）。1.2 那条追问（Aaron 手上还有没有 sealed proposal 原文）**有效且早在 2026-08-25 就已提出**，本更正只是重申，不是新问题 |
| **第 2 件 · 问 2**（就地标注 OPEN） | **形式成立、措辞须改**：标注不能写「该记录不在仓中」（会把提案误报成缺失记录），应写「该路径为提案/声明的落盘目标，尚未落盘」 |
| **第 2 件 · 问 3**（「先有字节再引用」升为纪律条款） | **不受影响，且被本更正**加强 —— 条款要求 PROPOSED 在写入当时声明。这三条正是**未经声明的提案**，恰是该条款要堵的缺口。若当初声明过，我就不会误分类，决裁席也不会白裁一件 |

---

## 4. 已落地的机械更正

```
tests/test_cited_records_exist.py
  三条 CITED_BUT_NEVER_EXISTED -> PROPOSED_NOT_YET_EXISTING，逐条附证据
  删除 test_the_never_existed_ones_are_still_absent_from_history
      —— 该类清空后它对零个条目断言，永久变绿而什么都不查；
         且它被 test_the_two_absent_classes_are_absent_from_history_too 完全包含
  代之以「该类当前为空」这一事实的钉死：若有条目重入该类即红
  更正 test_the_two_absent_classes… 的 docstring —— 它举的反例是假的：
      名称基判据在 SUPPLEMENT_LEDGER 这个例子上恰好是对的
```

**该类清空后留下一条空断言守卫，而我的空断言探测器看不见它**（它不做文件系统发现，
探测器只认 glob/rglob/listdir/scandir/os.walk）。这是探测器覆盖面的一个已知缺口，
记录在此，不在本轮扩探测器——扩它属另一件事。

---

## 5. 未做的

**没有改动任何一条引用。** 第 1 件的 MARK_ONLY 执行与问 2 的标注另行进行，
且须先按本更正把标注措辞改对。

**没有替 Aaron 决定是否重开第 2 件。** 席位是在错误前提上作业的，
是否要在正确前提上重裁，归 Aaron。builder 的意见（非裁定）：问 3 的条款可直接采纳，
问 1/问 2 值得在正确前提上重问一次——但代价是再烧一个决裁席位，而三条的实际去向
现在已经从字节里清楚了，可能不值。
