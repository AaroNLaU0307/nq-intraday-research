# RESEARCHER EXPOSURE LEDGER — 研究暴露台账

章程条款 13：所有实际查看过的特征×标签×方向×切片×参数候选在此登记，
即使不构成正式 trial。raw exposure count 是**保守上界**，必须完整报告；
正式多重检验须预注册从 raw exposure 推导相关性调整后 N_eff 的方法
（高度相关的表格单元不等于独立实验），禁止只使用最终存活版本数。

与 formal trial ledger 的关系：
- formal_trial_count：预注册研究/假设的数量（S0 = 1）。
- researcher_exposure_count：眼睛实际看过的候选关系数量（本文件累计）。

| 日期 | 研究 | 查看内容（特征×标签×切片） | 数量 | 备注 |
|---|---|---|---|---|
| — | — | —（零研究 outcome 暴露；见下方 incident 交叉引用行） | — | — |
| 2026-08-10 | S0（incident cross-reference，非研究查看） | 结构性测试加载事件：两次未打补丁的链测试经 RealChain._ensure 结构性加载 Development bars；零候选关系被查看、零 outcome 生成（quantity=0；outcome_seen=NO；formal_trial=NO）。详见 ops/INCIDENT_STRUCTURAL_TEST_LOAD_20260810.md。本行不改变累计研究结果暴露数量（仍 0）。裁定：IR-28d（具名 Fable 委托，2026-08-10） | 0 | append-only 交叉引用行；依 Codex 建议与 R5 提示词明文授权追加 |
| 2026-08-14 | S0-T001（正式运行完成，盲式收口） | S0-T001 首次真实运行 A→F 全链完成，结果已生成、封存并归档（outcome_generated=YES）；Stage C 已消耗授权包预登记的 exposure slot sequence 1（registry RUN_STARTED 行为正式记录，formal_trial_count=1）；**无任何人查看任何结果值**（outcome_seen=NO；raw_viewed_relation_count=0）；累计 researcher exposure 仍 0。盲式独立验证全过，见 ops/S0_T001_POST_RUN_ATTESTATION.md | 0 | append-only；依具名提示词 START_S0_T001_POST_RUN_BLIND_CLOSEOUT_AFTER_PROMPT_AUDIT 授权追加 |
| 2026-08-14 | S0-T001 RESULT_REVEAL_STARTED | Aaron 主动发送揭盲口令，授权一次性完整揭示封存正式报告（outcome_generated=YES；reveal_authorized=YES；formal_trial_count=1）。揭盲前以纯键/形状遍历（零数值）机械枚举本次将查看的全部正式 feature×label×direction×slice×parameter 关系格：**保守 raw exposure count=1575**（相关格不合并、歧义向上计、纯保管元数据与未授权 MC/EV 内容不计入）。清单：ops/S0_T001_REVEAL_EXPOSURE_MANIFEST.jsonl，sha256=02381b025316548994b6c2862abd40d8dca37722a6826b3fd6209189de0d1e16。本行在任何研究值进入模型上下文前先行提交；流程中断计数不回滚 | 1575 | append-only；依具名提示词 START_S0_T001_RESULT_REVEAL_AND_DECISION_COUNCIL_AFTER_BLIND_CLOSEOUT 授权 |

| 2026-08-14 | S0-T001 RESULT_REVEAL_COMPLETED（交叉引用行） | 一次性完整揭盲完成：manifest 全部 1575 关系格已按预注册顺序整体查看并交付决策评审（无择取、无新增切片、无契约外指标）；本行为完成标记，不重复计数。逐层裁定与完整结果备忘录见当轮聊天终报；结构化摘要见 ops/S0_T001_RESULT_REVEAL_ATTESTATION.md | 0 | append-only；与 RESULT_REVEAL_STARTED 行配对，避免双计 |

累计 exposure：1575（全部来自 S0-T001 正式揭盲一次性查看；历史各行均为 0 查看行）
