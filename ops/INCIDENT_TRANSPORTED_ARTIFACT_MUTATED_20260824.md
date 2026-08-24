# INCIDENT — 交付中的工件被 builder 改动，导致一次委托裁定作废

```
INCIDENT_ID=INC-TRANSPORT-20260824
SEVERITY=MEDIUM（无数据损失、无错误裁定入档；代价是一次完整审查会话）
CAUSED_BY=builder seat（Opus main agent）—— 本席，非审查方
DETECTED_BY=Sol delegated_decider，closing recheck
RULING_ISSUED=NO
```

## 1. 发生了什么

Sol 被授权代 Aaron 裁定两件事，按提示词以 SHA-256 钉定四份工件。
**开局 precheck 四份全部匹配。** 在它工作期间，builder 继续提交：

```
79a0539  Measure the per-pass cost ...   ← 往 ND2_ND3_RULING_REVIEW_FINDINGS.md 追加 §8
1fcee82  Register every coercion ...
```

Sol 的收尾 recheck：

```
FILE=ops\ND2_ND3_RULING_REVIEW_FINDINGS.md
EXPECTED_SHA256=8DC87212BDE8329694A22E5F5B7B32F8874FE725D8813562836922E67955EDD7
ACTUAL_SHA256=E2493F1AE0316C4B0CA38C62410521179477A014C263F480C2493B3B2636E94E
HEAD_AT_START=154c9b73…  HEAD_AT_FINAL_RECHECK=79a05390…
STATUS=STOP_HASH_MISMATCH   DELEGATED_RULING_ISSUED=NO
```

**审查方行为完全正确**：按「任一不匹配即停止并报告」停下，未签发任何裁定，
未对仓库写入。整场会话的成本由 builder 的一次追加造成。

## 2. 根因

常设 artifact transport 规则要求：交付物必须是磁盘上的持久文件、记录 SHA256、
接收方重算比对。**它没有说发出方此后不得再动它。** 这就是缺口。

而我当时正处在「你能做什么先就先做」的自主授权下，把新测得的成本数据
**追加到了一份已经交付出去的文件**。追加本身是好的工作，落点是错的。

**这不是记性问题，是缺少控制。** 「我会记得不动它」不是控制。

## 3. 处置

1. **§8 拆出**到独立记录 `ops/MC_COST_PROBE_FINDINGS.md`——新发现开新记录，
   与 registry 的 append-only 同纪律。
2. `ND2_ND3_RULING_REVIEW_FINDINGS.md` **逐字节复原**为交付时的字节
   （`8dc87212…`，取自 commit `f6c5c14`）。四个哈希因此全部回到提示词所列值，
   **提示词无需重发**。
3. 新增机械守卫：`ops/ARTIFACTS_UNDER_REVIEW.json` 登记在审工件，
   `tests/test_artifacts_under_review_are_frozen.py` 在每次全套件运行时
   重算并比对。审查期间任何一份被改动，builder 自己的测试立刻失败。
   变异验证过：往被冻结文件追加一个换行 → 测试失败。
4. 提示词加注说明第一次 STOP 的原因在 builder 一侧，并说明 HEAD 仍会移动
   （builder 在其他文件上继续工作），工件由内容哈希钉定而非 HEAD。

## 4. 未做的事

未修改 Sol 的任何结论——它没有出结论。未追加 registry / exposure 事件
（本事件零 outcome 暴露、零真实数据接触）。未改动那四份工件的内容语义。

## 5. 留给下一个我的一句话

**审查发出的那一刻，那些文件就不是你的了。** 新发现开新文件。
