# 被引用而不可达的记录 —— 实测findings

```ini
REVIEW_ID=findings-dangling-citations-2026-08-27
DELIVERY_STATUS=RETURNED
```

**产出席位**：builder（Opus 5）。本文件只陈述实测事实，不作裁定，不改任何引用。

---

## 0. 一句话

`ops/*.md` 里有 **15 处形如 `ops/X` 的路径引用不可达**；其中 11 处是真问题：
**8 处指向已移入隔离区的文件**，**3 处指向从未在 git 历史中存在过的文件**。

---

## 1. 为什么这不只是整洁问题

陈旧引用是 **fail-safe 的**（读者得到「找不到」），但读者下一步会做什么？搜索。

本项目已烧掉的三个复审席里：

```
第二席  从未打开过那份隔离文件 —— 一次广域符号搜索把片段带了出来
第三席  只做了一次单模式定向 grep —— 同样触到
```

**一条解析不到的引用，等于在邀请那个被明令禁止的动作。** 8 处陈旧引用中，
被引用的对象恰恰全部在隔离区里。

---

## 2. 实测方法

```
扫描集合   ops/*.md（非递归 —— 隔离子树是引用的「目标」，不是「来源」）
文档数     94
提取式     `?(ops/[A-Za-z0-9_./-]+\.(?:md|json|py))`?
判据       (REPO / ref).exists() 为假即计入
历史判据   git log --all --diff-filter=AD -- <ref>  无输出 ⇒ 从未增删
```

守卫：`tests/test_cited_records_exist.py`（11 测试，四类变异全部证红）。

---

## 3. 分类结果

### A. QUARANTINED_MOVED —— 8 处，文件在隔离区，引用没跟着走

```
ops/DECISION_PACKET_ND2_ND3.md
ops/MC_DR5_BUILD_PACKET.md
ops/MC_TO_STRATEGY_MASTER_PLAN.md
ops/ND2_ND3_FABLE_DECISION_PROMPT.md
ops/ND2_ND3_RULING_REVIEW_FINDINGS.md
ops/RULING_FABLE_FOUR_OPEN_2026-08-26.md
ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
ops/S0_T001_RESULT_DECISION_ADDENDUM.md
```

每一条都已核对：`ops/outcome_quarantine/<同名>` 确实存在（守卫每次运行重测，
若被移回或删除，该分类即变假而报红）。

引用这些路径的文档包括 `D124_RULINGS_CLEAN_EXTRACT.md`（一份刻意做成
outcome-clean 的摘录）、`FINDINGS_FABLE_FOUR_OPEN_TRANSPORT_STOP.md`、
`DECISION_PACKET_FOUR_OPEN_2026-08-26.md`、`REVIEWER_EXPOSURE_LOG.md` 等。

### B. CITED_BUT_NEVER_EXISTED —— 3 处，全历史无增无删

```
ops/MC_RUN_REGISTRY.md            <- DECISION_MC_REGISTRY_COLLISION.md
                                     RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md
ops/STRATEGY_COUNCIL_ROUND4_LOCK.md <- DECISION_PACKET_N00_AND_ND1.md
                                     N00_N08_PROVENANCE_AUDIT_2026-08-25.md
ops/SUPPLEMENT_LEDGER.md          <- DECISION_PACKET_N00_AND_ND1.md
```

**与 2026-08-26「一份裁定只存在于聊天里」是同一形态**：文档引用一份记录，
记录不在。当时那次由本人手工发现并逐字恢复；这三处此前无人发现。

### C. 合法的 4 处（已登记，非缺陷）

```
ops/...md · ops/PROMPT_...md                          行文中的省略号占位
ops/TRIAL_REGISTRY.pre-migration.2026-08-27.md        迁移方案提出的文件名
                                                      （正因撞边界 (2) 而在决裁中）
ops/migration-2026-08-27/registry-snapshot-pre-migration.md
                                                      S5 选项 RENAME_OUT 的举例路径
```

---

## 4. builder 明确未做的事，以及为什么

**没有改动任何一条引用。** A 类看似只是路径打错，实则不是：
`D124_RULINGS_CLEAN_EXTRACT.md` 是**刻意做成 outcome-clean 的摘录**，把它的引用
改指进隔离区，与它存在的目的相反；而 `DECISION_PACKET_*` 里点名隔离路径反而是
现行惯例（S5/R4 包 §2 就逐字点名 `ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md`
作为禁区）。**同一处改动，在不同文档里是相反的正确做法。**

这属于隔离纪律的判断，不是路径纠错。本周已两次为「实现者自行挑一种读法」付过代价
（第六轮 HOLD 的 Finding 1；S5 文件名）。不再自选。

B 类同样不自处理：三份记录**是否本该存在**（有人写了没提交）与**是否根本不该被引用**
（引用是错的）是两个不同的事实，且只有当事人能分辨。

---

## 5. 已落地的机械保障

```
tests/test_cited_records_exist.py
  新出现的未登记悬空引用          -> 红
  册中登记而实际已可解析（陈旧豁免）-> 红
  分类名超出四个合法值            -> 红
  隔离件被降级成「行文占位」       -> 红   ← 首版有此洞，变异测出后补上
  谎称某件在隔离区里              -> 红
  扫描返回空                     -> 红   ← 本文件自身受同一条规矩约束
```

**当前状态被钉死：不会增长，但也不会自行消失。**
