# N06 HOLD 修复轮 — 工程证据包（2026-08-21）

```
PACKET_TYPE=N06_HOLD_REPAIR_EVIDENCE
STATUS=REPAIR_CANDIDATE_AWAITING_FRESH_SOL_N06_STAGE_I
PRE_REPAIR_HEAD=617f7c33d20051fd991d74afa7c76716720e385d
PRODUCED_BY=Opus 5 main agent (builder seat) ＋ 两个零交集对抗测试子任务
NOT_A_VERIFICATION=YES（builder 自陈；N06 验收属 NEW TOP-LEVEL Sol 会话）
N06_FINAL_PASS=NO
```

## 1. 本轮修了什么（红证与前后对照见 `ops/N06_HOLD_RED_PROOF.md`）

| # | HOLD 缺陷 | 修复 |
|---|---|---|
| 1 | N03→N04 接缝**反向**：伪造 authority 通过全部 `B_DERIVE`，真实 authority 被拒 | `B_DERIVE` 五个 gate 全部 `type(x) is SupplementAuthority`；携带同源 `PreparedMCInput`；调用 `verify_supplement_authority`；bundle 摘要与 day-universe 恒等式**重新计算** |
| 2 | builder/seal factory boundary 未闭合 | 新增 `supplement_production.py` 为唯一生产路径；决定性参数内部派生、传入即拒；`init=False` capability receipt；hermetic 核心改名 `*_test_only` |
| 3 | output-root 未绑定 | 授权 root 与实际 `runs_root` 规范化后**精确比较**；新增纯 `plan_supplement_paths`（`<id>_<UTC>`、containment、basename 相同、目标不存在、非 reparse），**零目录创建** |
| 4 | registry 未 fail-closed 到位 | 13→99 跳号拒于 `supplement_seq_not_next_value`；六个计数字段设下界；`output_root` 须非空、绝对、可规范化 |

## 2. 对抗电池发现的、修复中引入或遗留的缺陷（**两个电池都由未写该代码的独立车道撰写**）

| 编号 | 严重度 | 内容 | 处置 |
|---|---|---|---|
| F3 | **High** | **生产 seal 比它取代的 hermetic 核心更弱**：后者在 seal 边界重跑 `_validate_supplement_object`（即盲式无-outcome 保证），前者没有。实测：每行带 `"pnl": 12.5` 的 payload 被 test-only seal **拒绝**、被生产 seal **封存** | **已修**：生产 seal 重跑对象校验＋逐行字段集检查（`production_supplement_object_invalid`、`production_forbidden_row_field`） |
| F4 | Medium | gate 用 `isinstance`、verifier 用 `type(...) is`，`__new__` 造的**子类**通过了那个「查类型不查形状」的 gate | **已修**：统一 `type(...) is` |
| F5 | Medium | 三个 `B_DERIVE` gate 完全不查类型；一个我写的测试**声称**了比实际更强的性质 | **已修**：五个 gate 共用 `_require_real_authority` |
| F6 | Medium | 一个产物可携带两个身份（payload 记 S001、receipt 记 S002）并通过校验 | **已修**：`production_supplement_id_divergence` |
| S2-1 | Medium | `$` 锚点接受尾随换行，`"MC-DS-S001\n"` 通过 id 语法并把换行带进规划出的目录名 | **已修，并按类清扫**：两个模块共 **7** 个锚点全部改为 `\Z`（对方只报了能触及的 2 个） |

## 3. 明确不修、留作已披露残留（交 N06 / Aaron）

1. **F1/F2（High，同一类）**：`__new__` ＋ `object.__setattr__` 可绕过 authority 与 receipt 两处 capability 检查，且 receipt 的六个分量摘要是**公开算术**，无需读取任何私有。
   与 `c5c819b` 已记录的残留同类——**Python 模块私有不是安全边界，任何进程内设计都挡不住改写模块内部的调用者**。
   **真正成立的安全论证是对抗车道自己测出来的**：起作用的边界是**重新推导**，不是 capability——16 项参数化表证明每一个被篡改的事实都在**各自专属的码**上被拒，因此 `__new__` 伪造只能复述真相。本包采纳该表述。
2. **F7**：`production_day_universe_drift` 被 `production_binding_drift` 遮蔽（day-universe digest 是 binding 的成员），死分支，保留为纵深防御。
3. **F8**：`resolve_partial` 是公开函数并写出制品文件名；「唯一生产路径」是调用图性质，不是制品名的性质。当前无授权、governed root 另需独立目录创建授权，故不可达。
4. **F9**：`SupplementProduct` 的不可变是**浅**的（行 dict 仍可变）；就地篡改会被 `production_receipt_mismatch` 抓到（双向都有测试）。
5. **F10**：没有专名的 `production_prepared_test_only`；test-only prepared 仍被 provenance 比对挡下。
6. **S2-2**：`_g_output_root_structure` 把八种成因压成一个码；F1 行记录 `gate_name`，detail 串区分成因。
7. **不可达码**：`output_root_blank`（被 `field_value_empty` 遮蔽）、`plan_target_escapes_root`、`plan_basename_divergence`（经公共签名不可达，构造上恒真）。三者均以可执行测试记录，而非静默留白。
8. **§D.3.2 P3 的两处矛盾**——**不是工程能裁的**，见第 5 节。

## 4. 对抗电池的独立性与规模

```
S1  tests/test_mc_supplement_provenance_battery.py   authority / builder / runner provenance
S2  tests/test_mc_supplement_paths_battery.py        registry / output-root / global-sequence
两个车道均未撰写被测生产代码；文件租约零交集；均无递归派生
两个车道各自先断言 near-miss 确实通过它应通过的检查，再断言拒绝
```

## 5. 唯一交给 Aaron 的裁定：`ND1_RECOMMENDED_PROFILE_R2`

R1 的 §D.3.2 P3 逐事件合同与 §D.3.3 状态图**互相矛盾**（前置缺 `F1`、后继缺 `A1`）。
工程树实现图与邻接合同的读法，但**没有任何已批准 profile 逐字覆盖它**。

```
ND1_PROFILE_R2=PROPOSED_NOT_EFFECTIVE
CORRECTION_ONLY=YES（47/51 行逐字继承 R1；4 处改动全在 P3 与 PROFILE_ID）
R1_STATUS=RATIFIED_AND_STILL_EFFECTIVE（未 supersede、未宣称失效）
AARON_R2_RATIFICATION_REQUIRED=YES
```

正文、SHA-256 与可签署块见决策包 §D.11；「correction-only」由
`test_r2_is_correction_only_against_r1_line_by_line` 逐行 diff 证明。

## 6. 禁止状态（全部仍为 NO）

```
REAL_DATA_READ=NO
SUPPLEMENT_EXECUTED=NO
MC_EXECUTED=NO
STRATEGY_BUILD_STARTED=NO
REGISTRY_EVENTS_APPENDED=NO
EXPOSURE_EVENTS_APPENDED=NO
REAL_DIRECTORIES_CREATED=NO
WRITE_PROBE_WRITTEN=NO
P6_IMPLEMENTED=NO
N-D2_STARTED=NO ／ N09_STARTED=NO
PUSHED=NO ／ TAGGED=NO ／ AMENDED=NO
```

## 7. 固定后续顺序（不得跳步）

```
1. Aaron 主动批准或修改 ND1_RECOMMENDED_PROFILE_R2
2. Opus 只持久化该裁决，工程树不再变化
3. NEW TOP-LEVEL SESSION，GPT-5.6 Sol XHIGH，正式 N06 exact-tree Stage I
4. 只有 N06 PASS 之后才进入 N-D2；N09 仍须另行精确执行授权
```
