# MC-DS 供给链干跑 —— 样本输出

```ini
RECORD_TYPE=SAMPLE_OUTPUT（不授权、不追加、不写任何治理路径）
GENERATED=2026-08-29；**你可以自己重跑**：`python scripts/mc_ds_rehearsal.py`
INPUTS=全部合成：编造的收盘价、test_only=True 的 authority、内存里的 registry
```

## 这是什么

**第一次把整条链端到端走通**：上下文装配 → A_PRECHECK 十三门 → B_DERIVE 五门 →
C_BUILD 机制 → 分类 → 失败事件规划。

在此之前每个零件都有测试，**接缝没有** —— 而第一次走接缝就抓到一个真缺陷
（见下文「它已经赚回成本」）。

## 它不是什么

**不是「真跑能过」的证据，而且永远不可能是。**
`custody_authority_production` 按设计拒绝 test_only authority ——
正是这条分区让干跑可以安全地指向任何东西。所以 C_BUILD 那段是
**绕过门直接驱动机制**的，报告里也这么写着。

## 它已经赚回成本

首次走通立刻暴露：`run_c_build` 把 **每一个** builder 异常都分类成
`row_schema_blind`，依据是一句注释「builder 校验的是它拿到的行」。
**那句是假的** —— builder 也校验 authority。于是
`production_authority_test_only`（一个 B_DERIVE 的 custody 缺陷）
被记成 C_BUILD 的行模式缺陷。

**门名和阶段正是 F1/F2 行携带的两样东西**，所以那是把错的缺陷记到错的阶段。
已订正：新增 `STAGE_GATE_OF_BUILDER_CODE`（对着 builder 源码推导校验）、
`CALLER_ERROR_BUILDER_CODES`（调用方 bug 抛出而不入账），
`CBuildFailure` 增加 `stage` 字段。

---

### A. 事件旗标缺失

```
MC-DS SUPPLEMENT REHEARSAL — synthetic inputs, nothing written

A_PRECHECK   PASS
B_DERIVE     REFUSED at custody_authority_production
    custody_authority_production     …ction': SupplementRunnerError (a test_only authority may never enter the production path)

THE GATES DID NOT APPROVE THIS, AND THEY ARE NOT SUPPOSED TO.
`custody_authority_production` refuses a test_only authority by design —
that partition is what makes a rehearsal safe to point at anything. So the
C_BUILD mechanism below was driven DIRECTLY, with the gates not consulted.
It shows what the machinery produces. It is NOT evidence a real run would
pass, and it never can be.

C_BUILD      REFUSED  gate=day_set_exact code=event_day_missing
             5 sealed day(s) absent from the event mapping, first ['2026-08-03', '2026-08-04', '2026-08-05']
WOULD RECORD F1 (SUPPLEMENT_ATTEMPT_FAILURE)
             attempts_dir             <scratch>\attempts
             consumption_statement    nothing consumed
             error_class              DayStrataRowsError
             gate_name                day_set_exact
             incident_id              INC-000000000000
             stage                    C_BUILD
             supplement_id            MC-DS-S001

NOTHING WAS WRITTEN, APPENDED, OR CREATED. The governed subtrees were
snapshotted before and after and are byte-identical.
```

### B. 五天旗标齐全

```
MC-DS SUPPLEMENT REHEARSAL — synthetic inputs, nothing written

A_PRECHECK   PASS
B_DERIVE     REFUSED at custody_authority_production
    custody_authority_production     …ction': SupplementRunnerError (a test_only authority may never enter the production path)

THE GATES DID NOT APPROVE THIS, AND THEY ARE NOT SUPPOSED TO.
`custody_authority_production` refuses a test_only authority by design —
that partition is what makes a rehearsal safe to point at anything. So the
C_BUILD mechanism below was driven DIRECTLY, with the gates not consulted.
It shows what the machinery produces. It is NOT evidence a real run would
pass, and it never can be.

C_BUILD      REFUSED  gate=custody_authority_production code=production_authority_test_only
             production_authority_test_only: a test_only authority may never build a production supplement
WOULD RECORD F1 (SUPPLEMENT_ATTEMPT_FAILURE)
             attempts_dir             <scratch>\attempts
             consumption_statement    nothing consumed
             error_class              SupplementProductionError
             gate_name                custody_authority_production
             incident_id              INC-000000000000
             stage                    B_DERIVE
             supplement_id            MC-DS-S001

NOTHING WAS WRITTEN, APPENDED, OR CREATED. The governed subtrees were
snapshotted before and after and are byte-identical.
```
