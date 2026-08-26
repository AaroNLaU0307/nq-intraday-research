# MC FACTORY BOUNDARY — Stage I 持久化证据记录

```
RECORD_TYPE=TRANSCRIBED_EVIDENCE_RECORD
SOURCE=AARON_PROVIDED_STAGE_I_HANDOFF
ORIGINAL_REPORT_BYTES_ARCHIVED=NO
RECORD_AUTHOR=Opus 5 main agent (builder seat)
RECORD_DATE=2026-08-20
RECORD_PREPARED_FROM_HEAD=c5c819beb5c13e52bcd7ca974a4e40787684b10f
```

> **本文件不是 Stage I 原始报告的逐字副本。** 本会话**不持有**该报告的原始
> 完整字节；下文全部 Stage I 事实由 Aaron 在具名提示词中转交，由本会话转录。
> 任何读者不得把本文件当作 verbatim 原件引用。若原始报告字节日后可得，正确
> 做法是按 `session-conventions.md` §4／§9 逐字归档为独立不可变记录，并在此
> 处加一条指针，**不是**改写本文件使其看起来像原件。

---

## 1. 记录对象

| 项 | 值 |
|---|---|
| `TARGET_HEAD` | `c5c819beb5c13e52bcd7ca974a4e40787684b10f` |
| `TARGET_PARENT` | `b3ac4534486f607242f5758cecbc918cbe2157be` |
| 被审对象 | factory-boundary 修复（"a prepared MC input is seal-admissible only if the battery built it"） |
| builder 自陈 | `MC_FACTORY_BOUNDARY_REPAIR_RECEIPT.md`（同一 commit 内，非验证件） |

## 2. 转录的 Stage I 事实

```
TARGET_HEAD=c5c819beb5c13e52bcd7ca974a4e40787684b10f
TARGET_PARENT=b3ac4534486f607242f5758cecbc918cbe2157be
REVIEWER=CODEX_GPT_5_6_SOL
REVIEW_WINDOW=FRESH_TOP_LEVEL_SESSION
STAGE_I_VERDICT=PASS
CRITICAL_FINDINGS=0
HIGH_FINDINGS=0
FACTORY_BOUNDARY_TESTS=44/44
MC_TEST_SUITE=587/587
FULL_SUITE_FRESH=3380/0/0
BASELINE_SENSITIVITY=28_FAILED/16_PASSED
WORKTREE_AT_REVIEW=CLEAN
DIFF_CHECK=PASS
RESEARCH_VALUES_VIEWED=NO
MC_EXECUTED=NO
SUPPLEMENT_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO
RUN_AUTHORIZED=NO
```

### 2.1 证据来源分层（诚实披露，勿跳过）

上表五个数字（44/44、587/587、3380/0/0、28/16、`DIFF_CHECK`）**与 builder
自陈回执 §5 的数字相同**。因为原始 Stage I 报告字节未归档，**本记录无法机械
区分**其中哪些是 Sol 在自己的树上重新实测得到的、哪些是 Sol 复核 builder 已
报数字后确认的。两种情形对 verdict 的含义不同：

```
STAGE_I_NUMBERS_INDEPENDENTLY_REPRODUCED=UNKNOWN_FROM_THIS_RECORD
BUILDER_SELF_REPORTED_SAME_NUMBERS=YES (RECEIPT §5)
```

任何后续引用必须携带这一限定，不得把本表升格为"两方独立实测一致"。

### 2.2 本会话（2026-08-20）另行机械复核的锚点

以下**不是**转录，是本会话在 `c5c819b` 工作树上直接实测，可被任何冷读者
逐条重放：

| 锚点 | 实测值 |
|---|---|
| `git rev-parse HEAD` | `c5c819beb5c13e52bcd7ca974a4e40787684b10f` |
| `git rev-parse HEAD~1` | `b3ac4534486f607242f5758cecbc918cbe2157be` |
| `git rev-list --count b3ac453..c5c819b` | `1` |
| `git status --porcelain` | 空（clean） |
| `git tag --points-at HEAD` | 空（仓库共两枚 tag：`mc-freeze-v1`、`s0-freeze-v1`，均不在 HEAD） |
| `git diff --check` | clean |
| 测试地板 pin @`c5c819b` | `scripts/s0_real_run.py:56` 与 `tests/test_s0_runner.py:1011` 均 `3380` |
| 测试地板 pin @`b3ac453` | 双 pin 均 `3336` |
| 测试地板 pin @`54ab7f2` | 双 pin 均 `3323` |
| 测试地板 pin @`a9148f1` | 双 pin 均 `2761` |
| `ops/TRIAL_REGISTRY.md` sha256 | `ee9da33fdbb47725dc036243adc76d7d9ba69ff06df0df443b09103f897353d6` |
| `EXPOSURE_LEDGER.md` sha256 | `382182bf8563a8e466115bf3024e3c1e1bd2f4b9f102d24d755e91c4174ba7ba` |
| `ops/S0_T001_POST_RUN_ATTESTATION.md` sha256 | `d839b965a35e749f0a9052cc3fb85f9b4032ed5d412043f36ac3349779941805`（== 代码 pin `ATTESTATION_SHA256_PINNED`） |
| 三者相对 `b3ac453` 的 git diff | 空 |
| S0-T001 封存件 | run 与 archive 各 14 文件，逐文件 sha256 全等；14 个摘要全部出现在 attestation 的摘要表中 |
| `…\itsf-runs\supplements\` / `…\itsf-runs-archive\supplements\` | **不存在**（本轮亦未创建） |
| registry 中 SUPPLEMENT／MC 事件行 | **零**（仅 S0-T001 链，末行 `COMPLETED`） |

**测试地板 pin ≠ 实测套件通过数。** 上表证明的是"地板常量在该 commit 上等于
该数字"，不是"该 commit 上真跑出了该数字"。`3380/0/0` 的实跑证据仍只来自
Stage I 转录与 builder 回执（§2.1 的限定适用）。本轮**未**重跑全套件——本轮
禁止修改生产代码，重跑不会产生新信息。

## 3. 独立性边界（QROS §2 四维度，逐维声明）

| 维度 | 状态 | 说明 |
|---|---|---|
| **CONTEXT / session** | **有** | Stage I 在 fresh top-level session 进行，未继承 builder 上下文 |
| **ARTIFACT AUTHORSHIP** | **有** | 被审产物（`consumer.py` 修复、`test_mc_battery_boundary.py`、回执）全部由 Opus builder 会话构建；Sol 未参与撰写 |
| **MODEL-FAMILY DIVERSITY** | **有限** | Sol 曾参与制定本次修复所依据的部分验收标准（该边界缺陷的合成复现与判据出自 Codex 侧）。故 factory-boundary **验收标准本身**不具备跨家族评审多样性；实现、测试与回执的评审具备 |
| **EMPIRICAL / sample** | **不适用** | 本次是工程边界验证，不触碰样本、不产生 outcome、不构成任何复制 |

按 QROS §3.1，独立性必须**按维度、按对象**陈述。本记录的合法表述是：

> "独立于实现与 builder 上下文；在 Sol 自身贡献的验收判据这一部分上不具备
> 模型家族评审多样性。"

**非法表述**（不得使用）："完全独立的第三方验证"、"两方独立复现"、
"跨模型一致因而结果更可信"。

## 4. Stage I PASS 的效力边界

```
STAGE_I_PASS_IS_ENGINEERING_ACCEPTANCE_ONLY=YES
STAGE_I_PASS_AUTHORIZES_RESEARCH=NO
STAGE_I_PASS_AUTHORIZES_ANY_RUN=NO
STAGE_I_PASS_AUTHORIZES_MC=NO
STAGE_I_PASS_AUTHORIZES_SUPPLEMENT=NO
STAGE_I_PASS_AUTHORIZES_STRATEGY_BUILD=NO
STAGE_I_PASS_RESOLVES_N00=NO
STAGE_I_PASS_RESOLVES_ND1=NO
STAGE_I_PASS_CHANGES_S0_VERDICT=NO
```

S0 现势 verdict 仍为 `INCONCLUSIVE_PENDING_MC`，
`RECOMMENDATION=HOLD_FOR_SPECIFIC_MISSING_EVIDENCE`，不因本 PASS 变动。
`CHECKPOINT0_VERDICT_REACHABLE=NO` 不变（feasibility gate 仍 `DECISION_REQUIRED`，
K 轴仍 `k_axis_evidence_blocked_grid_replay`）。

## 5. 被审修复自带的残留限制（转自回执 §6，非本记录新增）

1. Python 模块私有不是安全边界：能改写 `itsf.mc.consumer._BATTERY_CAPABILITY`
   或 `ATTESTATION_SHA256_PINNED` 的调用者可绕过（测试夹具即故意如此）。该边界
   防的是正常外部调用与全部意外路径。
2. 封印候选 schema `mc_verdict_inputs.v4` → `v5`（仅记录 receipt 摘要，无研究值）。
3. production-like 夹具 patch 了 `build_template_calendar` 为小日历。
4. 回执本身是 builder 自陈，不是验证件。

## 6. 后继动作（本记录不授权其中任何一项）

- N00：Round-4 权威文本入库 + 三状态裁定 → `ops/DECISION_PACKET_N00_AND_ND1.md`
- N-D1：决策批 1 逐项批准 → 同上，`AARON_ND1_RATIFICATION_BLOCK_V1`
- N03–N05：均 `BLOCKED_ON_N-D1`
- 若日后取得 Stage I 原始报告字节：逐字归档为独立文件并在此加指针
