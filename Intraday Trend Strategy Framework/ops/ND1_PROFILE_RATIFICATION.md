# N-D1 PROFILE RATIFICATION — Aaron 正式裁决的持久记录

```
RECORD_TYPE=RATIFICATION_RECORD
RECORD_STATUS=EFFECTIVE
APPEND_ONLY=YES
RECORD_AUTHOR=Opus 5 main agent (builder seat)
RECORD_DATE=2026-08-20
RECORDED_FROM_HEAD=803d99162d0a018ae5a3b44273601d98d9439d50
```

> 本文件**只追加**。它记录一次已经发生的批准，不重述、不改写、不解释
> `803d991` 中已批准的 profile 正文——那份正文是 `ops/DECISION_PACKET_N00_AND_ND1.md`
> §D.9.3 的 `ND1_RECOMMENDED_PROFILE_R1`，其字节不因本文件而改变。

---

## 1. Aaron 的批准（逐字转录）

Aaron 在 2026-08-20 的具名消息中主动发送了下列三行，构成对指定 profile 的
正式批准：

```
AARON_ND1_PROFILE_RATIFICATION_V1
APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R1
APPROVED_PROFILE_SHA256=0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5
APPROVAL_BINDS_DOC_HEAD=803d99162d0a018ae5a3b44273601d98d9439d50
```

```
APPROVAL_SOURCE=Aaron 具名消息（2026-08-20，本会话）
APPROVAL_MODE=ACTIVE_VERBATIM_SEND（非默许、非条件同意、非阅读终报）
APPROVAL_SCOPE=严格限于 803d991 中该 profile 的治理与工程定义
```

## 2. 机械复核（本会话在 `803d991` 工作树上实测）

| 项 | 结果 |
|---|---|
| profile canonical bytes | `BEGIN`/`END` 之间 49 行、2527 字节、LF、UTF-8 |
| 重算 SHA-256 | `0a08319a408f068ce4c92f93c2c4c39e409937dddfd0ef9f7af43618c70b50a5` |
| 与批准值比对 | **相等** |
| 承载该 profile 的 doc HEAD | `803d99162d0a018ae5a3b44273601d98d9439d50` |
| 与 `APPROVAL_BINDS_DOC_HEAD` 比对 | **相等** |
| `PROFILE_ID` | `ND1_RECOMMENDED_PROFILE_R1`，与批准值相等 |
| worktree | clean（0 porcelain） |

```
PROFILE_SHA256_MATCH=YES
DOC_HEAD_MATCH=YES
PROFILE_ID_MATCH=YES
ND1_PROFILE_RATIFICATION=VALID
```

## 3. C1–C10 跨字段一致性复核（逐条，机械）

| 规则 | 结论 | 依据 |
|---|---|---|
| C1 GLOBAL 序列 | PASS | `ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=GLOBAL` |
| C2 SEPARATE 四项规范 | 不适用 | 未选 SEPARATE |
| C3 reauth ⇒ P2S 语法 | PASS | `PRESTART_COMMIT_CHANGE_REAUTH=YES` 且 `GRAMMAR_P2S=ADOPT_AS_WRITTEN` |
| C4 new-id ⇒ F3+T1 | PASS | `POSTSTART_FAILURE_NEW_ID=YES` 且 `GRAMMAR_F3`/`GRAMMAR_T1` 均 ADOPT |
| C5 同 id 重试状态机 | 不适用 | 未选 `POSTSTART_FAILURE_NEW_ID=NO` |
| C6 supersede/id-reuse/后继登记互洽 | PASS | `SUPERSEDE_TARGET=2_SUPERSEDES_SUPPLEMENT_ID_ITSELF` 与 new-id=YES 相容，T1 已采纳 |
| C7 至多一个 live P2 | PASS | 语法含 `MULTIPLE_LIVE_P2_FOR_ONE_ID=REFUSE` 与 `MULTIPLE_LIVE_P2_AFTER_P2S=REFUSE` |
| C8 每个 MODIFY 带完整文本 | PASS | 唯一 MODIFY 为 `ND1_PARTIAL_RECOVERY_RULE`，其文本在 `ND1_PARTIAL_MODIFY_TEXT` |
| C9 政策 B 的 B1-B5 | 不适用 | `ND1_ARCHIVE_FAILURE_POLICY=A` |
| C10 partial MODIFY 文本 | PASS | `BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;BRANCH_C_RENAME_THEN_ALLOW_RETRY` |

```
C1_C10_ALL_PASS=YES
PROFILE_CROSS_FIELD_CHECK=PASS
```

## 4. 批准的效力边界（Aaron 在同一消息中逐条声明）

```
SUPPLEMENT_EXECUTION_AUTHORIZED=NO
REAL_DATA_READ_AUTHORIZED=NO
DIRECTORY_CREATION_AUTHORIZED=NO
WRITE_PROBE_AUTHORIZED=NO
REGISTRY_EVENT_APPEND_AUTHORIZED=NO
EXPOSURE_EVENT_APPEND_AUTHORIZED=NO
MC_EXECUTION_AUTHORIZED=NO
STRATEGY_BUILD_AUTHORIZED=NO
```

批准的是**语法与治理定义**，不是任何一次执行。将来每一次真实执行仍需 Aaron
单独的、绑定完整 40 位 commit 的精确授权语句（决策包 §D.10.4）。

## 5. 同一消息中的独立工程授权（与上面的 profile 批准分开）

Aaron 另行授权在已批准 profile 之下实现 N03／N04／N05，使用 synthetic／
test-only 数据完成测试，形成工程候选后停止等待 fresh Sol 的 N06 exact-tree
verification。该工程授权**不**扩大到真实 supplement 执行、真实数据读取、
输出目录创建或事件追加。

```
ENGINEERING_AUTHORIZATION=IMPLEMENT_N03_N04_N05_WITH_SYNTHETIC_TESTS_ONLY
ENGINEERING_AUTHORIZATION_STOPS_AT=N06_FRESH_SOL_EXACT_TREE_VERIFICATION
```

## 6. 派生量（由已批准字段推导，非独立批准项）

```
ID_REUSE_POLICY=NEVER_AFTER_START
SUCCESSOR_REGISTRATION_REQUIRED=YES（T1）
P2_PERMITTED_PREDECESSOR=P1 | P2S
F1_PERMITTED_SUCCESSOR=P3（commit 未变）| P2S（commit 变）| F3
P4_PERMITTED_SUCCESSOR=P5 | F2v
P5_PERMITTED_PREDECESSOR=P4 | A2
AX_TERMINAL=NO（唯一后继 F3）
FINAL_ARCHIVE_FAILURE_TERMINAL=F3
SILENT_DELETE_FORBIDDEN=YES（因 PARTIAL_RECOVERY_RULE=MODIFY）
NUMBERED_ROW_SEQ_SOURCE=既有全局递增序列
```

## 7. 修改路径（若日后需要改动任一已批准值）

只能走决策包 §D.10.3：Aaron 指出要改什么 → builder 产出
`ND1_RECOMMENDED_PROFILE_R2` → 跨字段检查重跑 → 新 canonical SHA-256 →
新的 doc-only commit → Aaron 批准 R2 的 id + hash + 精确 doc HEAD。
不得从参照清单里挑值直接生效，也不得就地改写本记录。


---

*仅追加。以下为 R2 的批准记录；上方 R1 的记录一字未改。*

---

## 8. `ND1_RECOMMENDED_PROFILE_R2` 批准记录（2026-08-23）

```
APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R2
APPROVED_PROFILE_SHA256=a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d
APPROVAL_BINDS_DOC_HEAD=c56286b684b03d7544db9db16b59b5443182f9e6
ND1_PROFILE_R2_RATIFICATION=VALID
R1_STATUS=SUPERSEDED_BY_R2_FOR_P3_ONLY（R1 记录本身仍在，未改写、未宣称无效）
```

### 8.1 Aaron 的批准（逐字）

Aaron 在 2026-08-23 的消息中主动答复：

```
批准 R2
```

**披露（重要，勿省略）**：Aaron 的原话是上面两个字，**不是**三行块本身。
三行的具体取值（id / sha256 / doc head）是 builder 在上一条消息中呈交、
Aaron 据以答复"批准 R2"的那一份，逐字如下，此处照录以便任何冷读者核对
他批准的究竟是哪一组字节：

```
AARON_ND1_PROFILE_RATIFICATION_V2
APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R2
APPROVED_PROFILE_SHA256=a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d
APPROVAL_BINDS_DOC_HEAD=c56286b684b03d7544db9db16b59b5443182f9e6
```

若 Aaron 认为绑定值应为别的取值，**在本文件末尾追加一行更正即可**，
不得就地改写本节。

### 8.2 `APPROVAL_BINDS_DOC_HEAD` 的歧义与其解决（builder 判断，非 Aaron 裁定）

决策包 §D.10.2 写"承载该 profile 的那一个 doc commit"，而生效条件行写
`exact_current_40hex_doc_commit`。两种读法在 R1 那次恰好重合（`803d991`
既是当时 HEAD 又是最后改动决策包的 commit），所以先例不解歧。

采用"承载 profile 字节的 commit"这一读法，理由是机械的：若取"当前 HEAD"，
则任何一次**与决策包无关**的 commit 都会使批准失效，该字段将不可用。
`c56286b` 是决策包最后一次被修改（§D.11 落盘）的 commit。

**因此本轮不修改 `ops/DECISION_PACKET_N00_AND_ND1.md`**——改它会把
"承载 profile 的 commit"变成另一个 commit，反而毁掉刚刚建立的绑定。
§D.11.5 的可签署块在决策包里保持 `UNRESOLVED` 原状，与 R1 的 §D.10.1
完全同形；批准这一事实只活在本记录件里。

### 8.3 机械复核（本会话实测）

| 项 | 结果 |
|---|---|
| R2 canonical bytes 重算 SHA-256 | `a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d` |
| 与批准值比对 | **相等** |
| `P3_PERMITTED_PREDECESSOR` | `P2\|F1` |
| `P3_PERMITTED_SUCCESSOR` | `P4\|A1\|F2` |
| 与代码实现比对 | 相等（`supplement_contract.EVENTS["P3"]`） |
| C1–C10 | PASS（R2 correction-only，47/51 行逐字继承 R1） |

### 8.4 R2 批准解决了什么，没解决什么

```
RESOLVED=fresh Sol N06 的 High 项——"实现先于治理批准"。代码实现的 P3 转移
         规则自此被生效 profile 逐字覆盖。
NOT_RESOLVED=N06 本身。批准 profile 不是通过验收；候选 HEAD 因本轮改动而
         变化，须重出 packet，并由**另一个** fresh Sol 会话重做正式 N06。
STILL_NO=supplement 执行、真实数据读取、目录创建、写探针、registry/exposure
         追加、MC 执行、策略 build —— 一律未授权。
```

---

*仅追加。以下为 R3 的批准记录；上方 R1 与 R2 的记录一字未改。*

---

## 9. `ND1_RECOMMENDED_PROFILE_R3` 批准记录（2026-08-27）

```
APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R3
APPROVED_PROFILE_SHA256=d40ad864571ec4773d68cdd4049b0eb8423da4cdf3fee7a145705f29c65f0d1d
APPROVED_CR1_GRAMMAR_SHA256=c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483
APPROVAL_BINDS_DOC_HEAD=2728e437b4c01ced97349e45077f2f87db7ac21d
ND1_PROFILE_R3_RATIFICATION=VALID
R2_STATUS=SUPERSEDED_BY_R3_FOR_P3_AND_F3_ONLY（R2 记录本身仍在，未改写、未宣称无效）
```

### 9.1 Aaron 的批准（逐字）

**与 R2 那次不同，Aaron 这次逐字给出了五行块本身**，不是「批准 R3」三个字：

```
APPROVED_PROFILE_ID=ND1_RECOMMENDED_PROFILE_R3
APPROVED_PROFILE_SHA256=d40ad864571ec4773d68cdd4049b0eb8423da4cdf3fee7a145705f29c65f0d1d
APPROVED_CR1_GRAMMAR_SHA256=c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483
APPROVAL_BINDS_DOC_HEAD=2728e437b4c01ced97349e45077f2f87db7ac21d
ND1_PROFILE_R3_RATIFICATION=VALID
```

**披露**：这五行的取值由 builder 在上一条消息中呈交，Aaron 逐字回贴。
§8.1 那种「原话两个字、取值另附」的歧义在本次不存在。

若 Aaron 认为绑定值应为别的取值，**在本文件末尾追加一行更正即可**，
不得就地改写本节。

### 9.2 builder 在记录之前的独立核验（未采信呈交值）

**Aaron 的数字与 builder 呈交的数字一致并不构成核验**——两者同源。
所以逐条对着**那个 commit 的字节**重算，不是对着工作树：

```
git show 2728e43:ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md
```

| 项 | 结论 |
|---|---|
| `2728e43` 存在，且为核验时的当前 HEAD | 是 |
| 该 commit 为 doc-only | 是——`ops/R3_CROSS_FIELD_RECHECK_2026-08-27.md` ＋ `ops/README.md`，零代码零测试 |
| R3 块在该 commit 的字节算得 `d40ad864…` | 相符 |
| CR1 语法块在该 commit 的字节算得 `c251335f…` | 相符 |

### 9.3 新增第三个字段的理由

R1／R2 的批准块只有 `id + sha256 + doc head` 三项。R3 多一项
`APPROVED_CR1_GRAMMAR_SHA256`，因为 R3 引入的 CR1 语法**不在 profile 块内**：
它自成一个 canonical 块，profile 里以 `RECOMMENDED_CR1_GRAMMAR_SHA256` 一行绑定。

绑定行落在 R3 哈希覆盖范围内，所以批准 `d40ad864…` **已经传递性地钉死了语法字节**
——改语法一字即破 `c251335f…`，要修绑定行必改 R3 块即破 `d40ad864…`。
第三项因此是**冗余的显式化，不是新的信任根**：它让冷读者不必先理解传递关系
才能核对语法字节。

该构造经决裁席审查后接受（`ops/RULING_FABLE_ITEM6_OPEN_2026-08-27.md` 的 R-B），
附三条 CONDITIONS，**均已在批准之前执行完毕**。

### 9.4 本批准的效力边界

**与 R1／R2 完全一致，一条未松**：

```
SUPPLEMENT_EXECUTION_AUTHORIZED=NO
REAL_DATA_READ_AUTHORIZED=NO
DIRECTORY_CREATION_AUTHORIZED=NO
WRITE_PROBE_AUTHORIZED=NO
REGISTRY_EVENT_APPEND_AUTHORIZED=NO
EXPOSURE_EVENT_APPEND_AUTHORIZED=NO
MC_EXECUTION_AUTHORIZED=NO
STRATEGY_BUILD_AUTHORIZED=NO
```

批准的是**语法与治理定义**，不是任何一次执行。R3 引入 CR1（崩溃裁定事件）这件事
**不授权任何崩溃恢复动作**——它只是让「如果发生，用什么词表记它」有了定义。

将来每一次真实执行仍需 Aaron 单独的、绑定完整 40 位 commit 的精确授权语句
（决策包 §D.10.4）。
