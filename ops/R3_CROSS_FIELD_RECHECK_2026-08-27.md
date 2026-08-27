# R3 跨字段检查重跑 —— §7 路线的 builder 步骤

```
RECORD_TYPE=CROSS_FIELD_RECHECK
SUBJECT=ND1_RECOMMENDED_PROFILE_R3（提案，未批准）
BY=Opus 5，builder seat，2026-08-27
ROUTE=ops/ND1_PROFILE_RATIFICATION.md §7：
      Aaron 指出要改什么 → builder 产出 R_n+1 → **跨字段检查重跑** →
      新 canonical SHA-256 → 新的 doc-only commit → Aaron 批准 id + hash + 精确 doc HEAD
STATUS=本文件完成「跨字段检查重跑」这一步。**批准仍未发生。**
```

**本文件不含任何已批准值。** `PROFILE_STATUS=PROPOSED_NOT_EFFECTIVE` 逐字仍真。

---

## 1. C1–C10 逐条（机械重跑，口径与 R2 那次相同）

| 规则 | 结论 | 依据 |
|---|---|---|
| C1 GLOBAL 序列 | PASS | `RECOMMENDED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=GLOBAL` |
| C2 SEPARATE 四项规范 | 不适用 | 未选 SEPARATE |
| C3 reauth ⇒ P2S 语法 | PASS | `RECOMMENDED_ND1_PRESTART_COMMIT_CHANGE_REAUTH=YES` 且 `RECOMMENDED_GRAMMAR_P2S=ADOPT_AS_WRITTEN`（R3 未触该行） |
| C4 new-id ⇒ F3+T1 | PASS | `RECOMMENDED_ND1_POSTSTART_FAILURE_NEW_ID=YES`；`GRAMMAR_F3=ADOPT_AS_CORRECTED_BY_R3`；`GRAMMAR_T1=ADOPT_AS_WRITTEN` |
| C5 同 id 重试状态机 | 不适用 | 未选 `POSTSTART_FAILURE_NEW_ID=NO` |
| C6 supersede/id-reuse/后继登记互洽 | PASS | `SUPERSEDE_TARGET=2_SUPERSEDES_SUPPLEMENT_ID_ITSELF` 与 new-id=YES 相容；`F3_PERMITTED_SUCCESSOR=T1` |
| C7 至多一个 live P2 | PASS | 两条 `REFUSE` 位于 P2／P2S 语法内，R3 对二者均为 `ADOPT_AS_WRITTEN`，**继承而非重述** |
| C8 每个 MODIFY 带完整文本 | PASS | 唯一 MODIFY 为 `ND1_PARTIAL_RECOVERY_RULE`，文本在 `ND1_PARTIAL_MODIFY_TEXT` |
| C9 政策 B 的 B1–B5 | 不适用 | `ND1_ARCHIVE_FAILURE_POLICY=A` |
| C10 partial MODIFY 文本 | PASS | `BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;BRANCH_C_RENAME_THEN_ALLOW_RETRY` |

```
C1_C10_ALL_PASS=YES
PROFILE_CROSS_FIELD_CHECK=PASS
FAIL_COUNT=0   PASS_COUNT=7   NOT_APPLICABLE_COUNT=3
```

**一条 builder 自纠**：首次重跑时我用了 `RECOMMENDED_PRESTART_…` 这类键名，四条报「缺」。
**那是我猜错了前缀，不是 R3 缺字段**——真实键名是 `RECOMMENDED_ND1_*`。上表用的是从
块里实际读出的键，不是我记忆里的键。

## 2. R3 独有的一致性 —— C1–C10 没覆盖，因为 CR1 是新的

```
CR1 ∈ P3.successors            YES   (P4|A1|F2|CR1)
CR1.predecessor == P3          YES
CR1.successor   == F3          YES
CR1 ∈ F3.predecessors          YES   (P1|P2|F1|F2|F2v|AX|CR1)
```

**双向声明闭合。** 单向声明正是第四轮 HOLD 的直接成因，由
`tests/test_nd1_profile_revision_chain.py` 机械守着。

## 3. Canonical SHA-256（§7 的下一步）

```
PROFILE_ID=ND1_RECOMMENDED_PROFILE_R3
R3_CANONICAL_SHA256=d40ad864571ec4773d68cdd4049b0eb8423da4cdf3fee7a145705f29c65f0d1d
R3_CANONICAL_BYTES=3222
CR1_GRAMMAR_SHA256=c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483
CR1_GRAMMAR_BYTES=1585
```

口径：`BEGIN_…` 与 `END_…` 两行**之间**、不含这两行、LF、UTF-8、逐字。
两个块的标记在提案文件中各恰出现一次（`test_each_canonical_marker_appears_exactly_once`）。

## 4. 边界 —— 本文件与本步骤都不授权任何东西

```
PROFILE_STATUS=PROPOSED_NOT_EFFECTIVE
PROFILE_CONTAINS_NO_EXECUTION_AUTHORIZATION=YES
PROFILE_CREATES_NO_DIRECTORY=YES
PROFILE_APPENDS_NO_REGISTRY_OR_EXPOSURE_EVENT=YES
```

**§7 路线的最后一步没有发生，且 builder 不得代做**：Aaron 批准 R3 的
`id + hash + 精确 doc HEAD`。在他的批准落盘之前，R3 一个字节都不进代码。
