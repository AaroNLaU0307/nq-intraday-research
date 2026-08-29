＃ 怎么把第 3 轮复审发给 Sol —— 给 Aaron 的操作单

```
写给     Aaron
关于     ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND3.md（REVIEW_ID=c-build-2-wording-r3）
状态     提示词早已写好且 DELIVERY_STATUS=ISSUED，**只是可能从没真的发出去**
核验     2026-08-29 复查：十份参考件自 pin d34ce7c 起全部未被触碰，
         supplement_runner.py 仍哈希到 446ebd4b —— **可以原样发送**
```

## 0. 一句话背景

这一轮卡着的是**整条链最后一块**：`supplement_runner.py` 里 C_BUILD 的五道门
现在还是「无条件拒绝」的桩。接线补丁我已经写好了
（`ops/PREPARED_C_BUILD_1_GATE_WIRING.patch`），**但那个文件此刻被这一轮复审持有**，
改它会让 Sol 回来复核时哈希对不上，那一轮席位就白烧了。

**所以这一轮返回 = 接线落地 = C_BUILD 的门从桩变成真分类器。**

## 1. 开一个**全新**的 Codex 会话

不能用旧会话。提示词自己写明了不得是谁：

```
MUST_NOT_BE = builder
              被审字节的作者
              dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）
              第 1 轮 c-build-2-wording 与第 2 轮 c-build-2-wording-r2 的会话
              N09 R2/R3 的任何前序复审会话
```

模型 **Codex GPT-5.6 Sol**，effort **Extra High**。

## 2. 粘这一段，一字不改

```
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（C_BUILD_2 措辞复审第 3 轮）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；Fable 5 决裁席；第 1、2 轮复审会话

从磁盘读这份提示词，不要从粘贴读：

C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND3.md

仓根：
C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework

读到之后按它自己的 §1 走：先核 line 26 的 REVIEWED_SET_UNCHANGED_SINCE，
对不上就 STOP。其余一切以那份文件为准，本条消息只负责把你指过去。
```

**就这些。** 提示词是自足的 —— 它自己带着受审集清单、传输规则、
禁区清单和判定口径，我不需要在这条消息里重复任何一样。

## 3. 它会做什么

它会核对那行 `REVIEWED_SET_UNCHANGED_SINCE=d34ce7c9d30fa87493123cc12b504c5111418df5`，
然后自己去读 §1 表里的 1 份 delivery ＋ 10 份 reference，最后给出
**PASS 或 HOLD**，并逐条说明。

## 4. 回来之后你要做的（就一件）

把它的回答**原样**贴给我。我会：

1. 逐条复现它的每一条发现 —— **不采信自陈**，这是本项目的标准做法
2. 把 `ops/ARTIFACTS_UNDER_REVIEW.json` 里那一轮的条目移除（复审已返回）
3. 那一刻 `tests/test_the_prepared_patch_still_applies.py` 会**主动变红并宣告解锁**
   —— 它就是为这一刻写的
4. 落地接线补丁，把三条绊线改成活形式，跑全量

## 5. 如果它判 HOLD

**那不是坏消息。** 前两轮都是 HOLD，四条发现全部命中，其中一条还带出了一个更大的洞
（我只锚了三份批准中的第一份）。HOLD 意味着它干了活。

## 6. 席位记账

发出去之后这一轮就消耗了一个 fresh Sol 席位。返回后我会把它记进
`ops/REVIEWER_EXPOSURE_LOG.md`（**席位轴，不消耗任何研究自由度**）。
