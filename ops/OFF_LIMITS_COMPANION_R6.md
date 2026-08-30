＃ 禁区清单 —— 随 `c-build-2-wording-r6` 一同交付

```ini
RECORD_TYPE=OFF_LIMITS_COMPANION
FOR_REVIEW=c-build-2-wording-r6
DELIVER_WITH=ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND6.md
```

## 为什么这份清单不在评审包里面

**D-2 裁定（Fable，2026-08-26，`DELEGATED=YES`），在第二个复审席位被烧之后。**

那次的链条是：禁区清单写在**提示词**里，而当轮的交付载体是 **Review Packet**——
**清单没有随之传递**。席位没有刻意打开任何东西，一次广域符号搜索就把隔离锚的片段
带了出来。

所以规则变成：**清单必须是一份独立的伴随件，随每一种交付载体一起交付。**
`tests/test_artifacts_under_review_are_frozen.py` 机械地要求每一个 LIVE review
都有这样一份文件存在。

## 权威清单

**权威在 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。**
下面逐条列出**只是为了标记它们是禁区**，不是引导你去读：

```
OFF-LIMITS   ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
OFF-LIMITS   ops/outcome_quarantine/**  （整个子树）
OFF-LIMITS   ops/EXPOSURE_LEDGER.md
OFF-LIMITS   EXPOSURE_LEDGER.md         （仓根那份）
OFF-LIMITS   ops/OUTCOME_CARRYING_ARTIFACTS.json 中 carries_outcome 的其余全部路径
```

**不得打开、不得 grep、不得列目录。**

## 可执行的检索边界（不是散文）

```
允许检索的根   src/  ·  tests/  ·  提示词 §2 表中逐条列名的 ops 文件
禁止          仓根范围的 grep / rglob / find
禁止          ops/ 全目录枚举
```

**成因如实记下**：第 3 轮之后，一个决裁席位在本仓做了两次仓根范围检索，
作用域含两份禁区台账。**那是 builder 的缺陷** —— 禁区只写成了文字，
没有随包给出可执行的约束。**同一形态第三次**，所以现在它是规则。

需要上表之外的字节：**列出路径向工作会话索取**，不要自己去开。

## 若你的工具把检索结果持久化到磁盘

请在回答里**报告那个文件的路径**，并**不要打开它**。
第 5 行席位就遇到过：33.9KB 完整输出被落盘，它自陈未读 ——
如实报告使那次事件可被处置，而不是变成一个无人知晓的缺口。

## 席位记账

本轮消耗一个 fresh Sol 席位。返回后 builder 会把它记进
`ops/REVIEWER_EXPOSURE_LOG.md`（**席位轴，不消耗任何研究自由度**）。

请在回答里给出 `SEAT_STATUS` 与 `OUTCOME_EXPOSED` 的自评。
**builder 不下调你的自评**；若认为过高，会另起一行记异议，不改你的行。
