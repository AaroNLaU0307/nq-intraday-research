# N-D1 工程证据包（N03 ／ N04 ／ N05 候选，2026-08-20）

```
PACKET_TYPE=ENGINEERING_EVIDENCE_PACKET
STATUS=CANDIDATE_AWAITING_FRESH_SOL_N06_EXACT_TREE_VERIFICATION
PRODUCED_BY=Opus 5 main agent (builder seat) ＋ 两个零交集实现子任务
NOT_A_VERIFICATION=YES（本文件是 builder 自陈，不是独立验证件）
```

## 1. commit 链

| 角色 | commit |
|---|---|
| 批准所绑定的 doc head（本段起点） | `803d99162d0a018ae5a3b44273601d98d9439d50` |
| N-D1 ratification record（doc-only） | `652ce301eecf115451ef9225e242478bb03e560e` |
| N04 runner ＋ 共享 contract | `a963199bfd4995ffbf81a6cdc61117df37864029` |
| N03 supplement authority | `f7aab7331354acdc9c09da355899a33818c20266` |
| N05 registry grammar/parser | `de3b6c61a754f9e28169f2cf45d39cc873a22dc7` |
| 集成、地板重钉、治理现势 | 本文件所在 commit |

## 2. 文件租约与交付

| 车道 | 独占文件 | 交付 |
|---|---|---|
| **主代理** | `supplement_contract.py`、`supplement_runner.py`、`test_mc_supplement_runner.py`、`test_mc_supplement_integration.py`、治理文档、地板 pin | N04 ＋ 集成 |
| **S1（N03）** | `supplement_authority.py`、`test_mc_supplement_authority.py` | authority／custody 绑定 |
| **S2（N05）** | `supplement_registry.py`、`test_mc_supplement_registry.py` | grammar／parser／resolver |

零交集，零递归 spawn，无跨租约编辑。S2 的两处 `pytest.skip` 由**原车道
follow-up 自行修正**，主代理未直接编辑其文件。

## 3. requirement → test 映射（摘要；逐项映射见各车道回执与测试文件）

| 需求 | 落点 |
|---|---|
| N03-1 authority 只能由批准 custody source 构造 | `test_a1_*`（9 项） |
| N03-2 test-only 不入生产 | `test_a2_*`（6 项） |
| N03-3 任一绑定字段不同即拒 | `test_a3_*`（16 参数化 ＋ 5） |
| N03-4/5/6 §D.2.2 恒等式三条 | `test_a4_*`、`test_a5_*`、`test_a6_*` |
| N03-7 缺／重／多／同数换日／跨 θ 漂移 | `test_a7_*`（11 项） |
| N03-8 同步伪造仍不能绕过 | `test_a8_*`（3 项） |
| N03-9/10 盲式 ／ 非授权 | `test_a9_*`、`test_a10_*`（9 项） |
| N04 gate enum 机械导出 | `test_gate_enum_matches_the_implemented_gates_exactly_and_in_order` |
| N04 每个 A_PRECHECK gate 负例 | 13 gate 各自负例 |
| N04 F1/F2 由 P3 分界决定 | `test_the_same_stage_becomes_f1_or_f2_purely_by_the_p3_boundary` |
| N04 全部合法边 ／ 全部禁边 | `test_every_ratified_edge_is_reachable`（20）、`test_the_declared_forbidden_edges_are_all_unreachable` |
| N04 archive A 全分支 ＋ 分类器全码 | `test_classifier_covers_every_declared_archive_code`、`test_an_unclassifiable_archive_failure_stops_the_chain` |
| N04 `.partial` C/E 故障注入 | `test_branch_c_*`、`test_branch_e_*`、`test_no_branch_of_resolve_partial_deletes_a_file` |
| N04 protected-state zero-write | `test_production_entry_writes_nothing_anywhere` |
| N05 六格契约／编号／宽度／字段 | 见 S2 映射 1–5 |
| N05 P2S 十一码 | 每码一测 |
| N05 archive A1/A2/AX 全分支 | 见 S2 映射 11 |
| N05 P6／MC 按名拒绝 | `test_nd3_deferred_tokens_refused_by_name`（5） |
| N05 任一缺陷拒整个 resolution | `test_a_defect_in_one_chain_poisons_every_chain` |
| 跨车道接缝 | `test_the_runner_discovers_the_registry_resolver_through_its_seam` 等 6 项 |
| 代码 ↔ 治理文本同步 | §2 of integration（11 项，从 packet 逐项重导） |

## 4. baseline sensitivity（实测，非源码阅读）

`.partial` 规则改动对旧实现的判别力，在临时目录上实测：

```
branch C（前次崩溃遗留的 divergent partial）
  OLD  supplement_partial_residue；residue_still_blocking_path=True
  NEW  retry_permitted；evidence_preserved=True；path 解除阻塞
branch E（本次写入后 re-read 不符）
  OLD  supplement_partial_verify；bytes_on_disk=[]        ← 被 unlink
  NEW  supplement_partial_verify；保留为 …partial.divergent.INC-…
```

故两条新 `.partial` 测试对旧实现**都会红**。

各车道另做了变异证明：S1 七个定向变异，每个杀死 1–4 个测试；S2 十二个
guard-disabling 变异，每个杀死 4–108 个测试。

## 5. 已披露残留（交 N06 / Aaron）

1. **builder 边界未闭合**（最重要）：N03 关的是 `build_day_strata_supplement`
   两个决定性参数的**来源**，不是 builder 本身。手搭 `(expected_day_set,
   binding)` 仍可造出合法 supplement——形态同 `c5c819b` 修掉的
   factory-boundary 缺陷。当前 `src/`、`scripts/` **无任何生产 caller**，故
   不可达；已用两条 invariant 钉住（integration §6），一旦有人加旁路 caller
   即红。硬化＝让 builder 要求 authority，属受审代码改动，本轮未做。
2. **TP∩FP 在 authority 投影内结构性不可达**（`consumer.py:1209`
   `traded[theta] = frozenset(tp)`）；检查保留＋源码钉，disjointness 在
   prepare 电池层测试。
3. **同数换日无专属码**，落在 `fp_day_without_record`；测试先证明"仅计数会漏"。
4. **N05 两个 guard 级码不可经 registry 文本到达**，按 guard 测试。
5. **N05 若干派生规则**（F3/T1 bracket id、P5 失败验证即拒、P5/F2v actor
   不得是产出会话、live P2 被其 P3 消费）待 N06 复核。
6. **§D.3.2 两处 predecessor/successor 不对称**（P3 缺 A1 后继、P3 缺 F1
   前置），按二对一读法实现并在声明处记录，待 Aaron 裁定是否回改文档。
7. **模块私有不是安全边界**（Python 通例，与 `c5c819b` 同一已记录残留）：
   能改写 `_AUTHORITY_CAPABILITY` / `_BATTERY_CAPABILITY` 的调用者可绕过。
8. **一处测试触及 consumer 私有** `_issue_battery_receipt`，用于构造
   acceptance-8 夹具；替代方案需改动 Stage-I 已验证的生产代码，本轮未做。

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
PUSHED=NO ／ TAGGED=NO ／ AMENDED=NO
```

## 7. 验证结果（本轮实测）

```
FULL_SUITE_FRESH=3725 passed / 0 failed / 0 skipped（367.91s）
COLLECTED=3725（与地板 pin 相等）
MIN_COLLECTED_TESTS 双 pin 重钉=3380 -> 3725
  scripts/s0_real_run.py:56 ＋ tests/test_s0_runner.py:1011
FOCUSED:
  test_mc_supplement_authority.py   68 passed
  test_mc_supplement_registry.py   145 passed
  test_mc_supplement_runner.py     100 passed
  test_mc_supplement_integration.py 32 passed
  test_mc_day_strata_supplement.py  27 passed
  supplement 家族合计               372 passed
  doc/governance 专项                93 passed
SCANS=同 HEAD 的 3 项 atoms.py 既有 false positive，零新增
DIFF_CHECK=CLEAN
FROZEN_7=OK
REGISTRY_SHA256=ee9da33f…（逐字不变）
EXPOSURE_SHA256=382182bf…（累计 1575 不变）
ATTESTATION_SHA256=d839b965…41805（== 代码 pin）
SEALED_S0_T001=14 文件 run==archive 逐字节全等
SUPPLEMENTS_DIRECTORIES_EXIST=NO（两个）
REGISTRY_SUPPLEMENT_ROWS=0
WORKTREE=CLEAN
```

**一次集成修复轮的使用情况**：接缝零摩擦（N04 的 named resolver seam 与 N05 的
`resolve_supplement_chain` 一次对上），未动用集成修复轮。期间的两次修正分别是
S2 车道自行修 `pytest.skip`，与主代理修自身 integration 测试的自匹配缺陷。
