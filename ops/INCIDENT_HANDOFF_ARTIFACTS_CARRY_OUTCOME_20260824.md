# INCIDENT — 必读交付工件复述 outcome，烧掉一个 Stage I 席位

```
INCIDENT_ID=INC-HANDOFF-OUTCOME-20260824
SEVERITY=MEDIUM-HIGH（无错误裁定入档；代价是一个不可恢复的 Stage I 审查席位）
CAUSED_BY=builder/architect seat（Opus main agent）—— 本席
DETECTED_BY=Sol delegated_decider，其独立性声明的 empirical 维
```

## 1. 发生了什么

Sol 在裁定的独立性声明里自陈：

> 两份必读钉定工件自身复述了聚合结果及与 feasibility 相关的结果分类；虽然
> 禁读源文件均未打开、这些信息也未用于理由，本会话仍须记
> `OUTCOME_EXPOSED=TARGET_METRIC`，已不具备 outcome-blind 的未来 Stage I 资格。

**那两份工件是我写的。** 我在提示词里列了一张禁读清单，却把被禁内容的**复述**
放进了同一份提示词要求它必读的工件里：

- `DECISION_PACKET_ND2_ND3.md` §2.2 逐字引用了 addendum 里那句
  「可行性天花板作为独立断言记 **PASS**」——一条与 feasibility 直接相关的
  结果分类；
- `ND2_ND3_RULING_REVIEW_FINDINGS.md` 同段转述，并复述
  `verdict=INCONCLUSIVE_PENDING_MC` 与 `exposure=1575`。

我当时的意图是**诚实披露**（告诉审查方存在这样一份文件、归 Aaron 裁）。
意图没错，**落点错了**：披露一件事的存在，不需要复述它的内容。

## 2. 代价，具体

runtime 的 §9.1 `GRAD-*` 需要一个**真实 Stage I pilot**。ITSF 已经因为封存
早于 runtime 而不能当 A2 pilot（无 `runs/` A2 记录）；Stage I 是它唯一能供的
那个。

**这个 Sol 会话现在不能当。** 任何读过这两份工件的后续 Sol 会话同样作废。
席位不是用完可再生的——`OUTCOME_EXPOSED` 一旦记上就跟着会话走。

## 3. 这是同一个模式的第三次

```
1. EXPOSURE_LEDGER.md 被我列进 Fable 的可读白名单，而它内嵌揭盲后摘要
2. 我自己 tail 了那一行（说过不读）
3. 我把 outcome 的复述写进了必读交付工件
```

三次的共同点：**我把"outcome 在哪里"当成了位置问题，而它是内容问题。**
一份文件是不是暴露面，取决于它写了什么，不取决于它叫什么、放在哪个目录。

## 4. 规则（即刻生效，约束我自己）

**必读交付工件不得复述 outcome，包括引用。** 需要让审查方知道某份禁读文件
存在时：

- 只给**路径、存在性、以及它归谁裁**；
- **不给**其中任何数值、结论、分类或逐字引文；
- 若审查方确实需要内容才能工作，那说明该任务本身不该给一个 outcome-blind
  的席位——改路由，不要改披露。

## 5. 机械守卫

`tests/test_review_artifacts_are_outcome_clean.py`：对
`ops/ARTIFACTS_UNDER_REVIEW.json` 里登记的每一份工件，扫描已知的
outcome-复述模式（揭盲 verdict 串、累计 exposure 数、addendum 的
feasibility 断言引文、逐 θ 结果串）。命中即失败。

守卫不能证明一份文件干净——它只挡住**已知会烧席位的那几种**。判断仍在我。

## 6. 未做的事

未改动 Sol 的任何结论——它的裁定不受影响，它明说这些信息未用于理由。
未追加 exposure 事件（归 Aaron，与 INC-TRANSPORT 那笔一并待裁）。
