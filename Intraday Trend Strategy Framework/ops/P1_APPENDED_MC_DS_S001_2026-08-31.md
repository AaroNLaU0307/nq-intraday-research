＃ P1 已追加 —— `MC-DS-S001` 的 `SUPPLEMENT_PROPOSED` 行

```ini
RECORD_TYPE=EXECUTION_EVIDENCE
AUTHORIZED_BY=Aaron，2026-08-31，逐条点名「追加 P1」
EXECUTED_BY=Opus 5，builder seat
REGISTRY_COMMIT=e53234e（registry 仓）
```

## 1. 追加了什么

```
序号        14（实测：追加前最大为 13）
时间戳      2026-08-30T21:25:10+00:00（UTC；registry 用 UTC，行 12 同形）
commit      007f404a0a092f0cb6aea79538f6e548745413b3（框架仓 HEAD）
actor       main agent
note        [MC-DS-S001] ir_basis: IR-29b Option B;
            schema: mc_day_strata_supplement.v1;
            non_authorization_disclaimer: this row is not an authorization
sha256      ee9da33f… -> 3ddbfb62…
见证        WITNESS_P1_APPENDED_2026-08-31.json  sha256 892bcd15…
```

**见证不是可选的**：`ops/REGISTRY_SYNC_FAILURE_MODEL.md` (1) 要求
**每次 registry 追加后**把 `{sha256, 事件计数, 末行}` 写进非同步受治理根，append-only。
我原本会漏掉这一条 —— 是追加前查「有没有别的义务」时才看见的。

## 2. 它解开了什么：**零**

追加后**实测**，不是引用 08-29 的结论：

```
chain.problem         ''（解析通过）
short_ids             ('P1',)
live_authorizations   0
生产入口              仍是 SupplementRunNotAuthorized
                      MC-DS-S001: 0 live SUPPLEMENT_EXECUTION_AUTHORIZED row(s)
```

**拒绝点与拒绝信息一字未变。** P1 之所以必须存在，是因为没有它 P2 不合语法。

## 3. 第一次尝试是坏的 —— 如实记录

我把决策包 §D.3.2 的 `NOTE_SHAPE`（散文）当成 note 的**字面内容**照抄：

```
[MC-DS-S001] 依 IR-29b Option B 提案；schema mc_day_strata_supplement.v1；本行非授权
```

链整体拒绝：

```
note_segment_not_field [MC-DS-S001, row #14]:
  '…' is not a `key: value` field; supplement notes are machine-parsed so
  that unknown/duplicate/missing fields can be refused (§D.3.5)
```

**那句 NOTE_SHAPE 描述的是 note 传达什么，不是 note 本身。**
真实文法：`;` 分隔的 `key: value` 段，key 匹配 `^[a-z][a-z0-9_]*$`。

### 处置

```
坏行        未进任何历史（追加后、提交前即被发现），registry 仓还原到 SHA0
            —— 还原前先确认该仓只有这一个文件是脏的
坏行的见证  **保留**。见证根是 append-only，而它记录的是一个确实短暂存在过的状态。
            新见证里逐字写明它被取代及原因
```

## 4. 真正的教训是**顺序**

我先追加、后解析。正确顺序是先在内存里拿生产解析器试通过，再碰文件 ——
第二次就是这么做的（两个候选 note 在内存里各试一遍，都通过，取不重复 id 的那个）。

**这与今日反复出现的那一族同源**：先做、后验，而不是先验、后做。

## 5. 现在停在哪

```
下一步    P2 —— actor 必须是 Aaron，四个必填字段：
          supplement_id · authorized_commit_40hex · output_root ·
          verbatim_authorization_sentence
顺序陷阱  authorized_commit_matches_head 要求 P2 的 commit == 运行时的 HEAD。
          **P2 之后、真跑之前不得有任何提交。**
待量      output_root 该填哪一条 —— 呈 P2 块之前先实测，不凭印象
```
