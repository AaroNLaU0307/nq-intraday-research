# RESEARCHER EXPOSURE LEDGER — 研究暴露台账

章程条款 13：所有实际查看过的特征×标签×方向×切片×参数候选在此登记，
即使不构成正式 trial。raw exposure count 是**保守上界**，必须完整报告；
正式多重检验须预注册从 raw exposure 推导相关性调整后 N_eff 的方法
（高度相关的表格单元不等于独立实验），禁止只使用最终存活版本数。

与 formal trial ledger 的关系：
- formal_trial_count：预注册研究/假设的数量（S0 = 1）。
- researcher_exposure_count：眼睛实际看过的候选关系数量（本文件累计）。

归一化规则（L6 §10.1 要求；由工作会话声明，2026-08-24）
依 Aaron 2026-08-24 逐字指示「直接按你建议的做吧，能执行的全执行」。
**本块只描述本台账既有各列已有的含义，不新增、不改写、不重排任何行，
不改变任何计数。** 本块可由 Aaron 随时更正。

列映射（本台账 → §10.1 固定列）：

```
日期                       -> ts
研究                       -> scope
查看内容（特征×标签×切片） -> granularity（所查看的轴）
备注 内的路径/文件引用     -> artifact_or_pointer
备注                       -> note
数量                       -> researcher_exposure_count 的本行贡献
```

classification 推导（行 → NONE | AGGREGATE | TARGET_METRIC）：

```
TARGET_METRIC  本行记录查看了预注册判定统计量，或由其派生的值
AGGREGATE      本行记录只查看了聚合/摘要值，未及逐候选关系
NONE           本行记录零 outcome 值查看
UNKNOWN        本行文本不足以判定 —— fail-closed，绝不折算为 NONE
```

**`数量` 与 classification 正交**：一行可以是 `数量=0` 而 classification
为 `AGGREGATE`（交叉引用行即如此）。三轴不得互推。

| 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注 |
|---|---|---|---|---|
| — | — | —（零研究 outcome 暴露；见下方 incident 交叉引用行） | — | — |
| 2026-08-10 | S0（incident cross-reference，非研究查看） | 结构性测试加载事件：两次未打补丁的链测试经 RealChain._ensure 结构性加载 Development bars；零候选关系被查看、零 outcome 生成（quantity=0；outcome_seen=NO；formal_trial=NO）。详见 ops/INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md。本行不改变累计研究结果暴露数量（仍 0）。裁定：IR-28d（具名 Fable 委托，2026-08-10） | 0 | append-only 交叉引用行；依 Codex 建议与 R5 提示词明文授权追加 |
| 2026-08-14 | S0-T001（正式运行完成，盲式收口） | S0-T001 首次真实运行 A→F 全链完成，结果已生成、封存并归档（outcome_generated=YES）；Stage C 已消耗授权包预登记的 exposure slot sequence 1（registry RUN_STARTED 行为正式记录，formal_trial_count=1）；**无任何人查看任何结果值**（outcome_seen=NO；raw_viewed_relation_count=0）；累计 researcher exposure 仍 0。盲式独立验证全过，见 ops/S0_T001_POST_RUN_ATTESTATION.md | 0 | append-only；依具名提示词 START_S0_T001_POST_RUN_BLIND_CLOSEOUT_AFTER_PROMPT_AUDIT 授权追加 |
| 2026-08-14 | S0-T001 RESULT_REVEAL_STARTED | Aaron 主动发送揭盲口令，授权一次性完整揭示封存正式报告（outcome_generated=YES；reveal_authorized=YES；formal_trial_count=1）。揭盲前以纯键/形状遍历（零数值）机械枚举本次将查看的全部正式 feature×label×direction×slice×parameter 关系格：**保守 raw exposure count=1575**（相关格不合并、歧义向上计、纯保管元数据与未授权 MC/EV 内容不计入）。清单：ops/S0_T001_REVEAL_EXPOSURE_MANIFEST.jsonl，sha256=02381b025316548994b6c2862abd40d8dca37722a6826b3fd6209189de0d1e16。本行在任何研究值进入模型上下文前先行提交；流程中断计数不回滚 | 1575 | append-only；依具名提示词 START_S0_T001_RESULT_REVEAL_AND_DECISION_COUNCIL_AFTER_BLIND_CLOSEOUT 授权 |
| 2026-08-14 | S0-T001 RESULT_REVEAL_COMPLETED（交叉引用行） | 一次性完整揭盲完成：manifest 全部 1575 关系格已按预注册顺序整体查看并交付决策评审（无择取、无新增切片、无契约外指标）；本行为完成标记，不重复计数。逐层裁定与完整结果备忘录见当轮聊天终报；结构化摘要见 ops/S0_T001_RESULT_REVEAL_ATTESTATION.md | 0 | append-only；与 RESULT_REVEAL_STARTED 行配对，避免双计 |
| 2026-08-14 | S0-T001 DECISION_ADDENDUM（交叉引用行，非查看） | 揭盲结论追加式纠正（六项：Checkpoint-0 推断撤回／Option C taxonomy 限定／sensitivity 跨总体百分比撤回／endpoint spread 精确值 0.20477498240675374／16 个 zero-direction mean=0 格承认／现势 OVERALL_S0_VERDICT=INCONCLUSIVE_PENDING_MC＋RECOMMENDATION=HOLD_FOR_SPECIFIC_MISSING_EVIDENCE）。针对同一批已揭露结果的解释纠正，零新研究关系查看。全文见 ops/S0_T001_RESULT_DECISION_ADDENDUM.md | 0 | append-only；依具名提示词 START_DR5_MC_CONSUMER_ENGINEERING_AFTER_S0_REVEAL_REVIEW_CORRECTION |
| 2026-08-24 | S0-T001 builder 读取 DECISION_ADDENDUM 摘要行（交叉引用行，非查看候选关系） | builder（Opus，N13 建造者）在 `tail -3 EXPOSURE_LEDGER.md` 时读到本台账 DECISION_ADDENDUM 行内嵌的揭盲后摘要，含 endpoint spread 精确值与 zero-direction 格计数。此前曾声明不读该内容，实际读了，如实登记。零新研究关系被查看，故 `数量=0`；但 `outcome_seen=YES`，故 builder 自此不再具备 outcome-blind 资格，`REVEALED_OUTCOME_READ_BY_BUILDER` 由 NO 改为 YES（范围：addendum 摘要行，非任何 feasibility 判据量）。事件记录见 ops/INCIDENT_HANDOFF_ARTIFACTS_CARRY_OUTCOME_20260824.md | 0 | append-only；classification=AGGREGATE（见上方归一化规则）；比照 IR-28d 交叉引用行先例；依 Aaron 2026-08-24 授权 |

累计 exposure：1575（全部来自 S0-T001 正式揭盲一次性查看；历史各行均为 0 查看行）
