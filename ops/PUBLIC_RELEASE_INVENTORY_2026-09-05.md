＃ 公开发布 inventory —— 只分类，不删除、不重构、不阻塞主线

```ini
RECORD_TYPE=INVENTORY（不改代码、不删文件、不阻塞 N09）
BY=Opus 5，builder seat，2026-09-05
判据=这个测试／文档是否保护**真实研究性质或复现能力**
     —— 不按数量、不按「看起来专业」
执行时机=最终研究完成之后
```

---

## 0. 先说一个改变结论的数字

```
A 公开保留    55 个文件    **3529 条测试**    6 分 24 秒
B 内部归档    77 个文件      1477 条测试      36 秒
─────────────────────────────────────────────────
             132                5006
```

**70% 的测试是研究保护,而它们只占 42% 的文件。** 治理文件数量多,但个个小而快。

**所以公开仓不是「精简版」——它保留 3529 条测试。**
被拿掉的是 77 个文件的席位记账与包管理,不是研究证据。

## 1. 我用的判据（照 Aaron 给的，逐条）

```
A  数据完整性 · 无 look-ahead/泄漏 · 策略逻辑 · 回测正确性 · 成本/滑点
   walk-forward/OOS · bootstrap/MC · 预注册研究门 · 核心端到端集成
B  席位记账 · 包的冻结/哈希机械 · 决策/复审包格式 · 授权管道历史
   被取代的治理裁定 · 历史恢复机械 · 守卫的守卫
C  已被新实现完全取代，且既不保护研究性质、也不需要作为最终审计证据
```

## 2. A. PUBLIC_KEEP —— 55 个测试文件

```
研究核心（S0）
  s0_config  s0_context  s0_dataset  s0_evidence  s0_gridmix  s0_handoff
  s0_output_proof  s0_report  s0_runner  s0_stability  s0_stats  s0_study

特征 / 标签 / 成本 / 日历
  features  labels  costs  calendar  f10_calendar  dr2_vol_regime  oracle

数据边界与泄漏
  dev_boundary  loader  cost_calibration_loader_boundaries

MC / bootstrap / 收敛
  bootstrap  mc_atoms  mc_consumer  mc_convergence_provenance
  mc_fixed_world_selection  mc_over_budget_predicate  mc_battery_boundary
  mc_bundle_precheck  mc_cold_replay  mc_custody_calendar
  mc_feasibility_composition  mc_feasibility_gates  mc_node_integration
  mc_r2_2_integration  mc_r2_3_evidence  mc_bprov_seal_provenance
  mc_supplement_authority  mc_supplement_provenance_battery
  mc_day_strata_supplement

day-strata 补充的研究内容
  day_strata_context  day_strata_pipeline  day_strata_rows_producer
  run_c_build_2  supplement_chain  supplement_inputs

平台 / 编排 / 端到端
  m6_chain  orchestrator  platform_authoritative_events  topstep  lucid
  verdict  runinfra  resolve_partial_observed_behaviour
```

**几个需要说明的判断:**

```
resolve_partial_observed_behaviour  留 A —— 它保护「封存时不会静默丢字节」，
                                    那是证据完整性。而同族的 path_contract 与
                                    state_diff 是**为审查造的仪器**，归 B
runinfra                            留 A —— 归档与运行基础设施，端到端要用
mc_supplement_provenance_battery    留 A —— 它挡的是伪造的 prepared input，
                                    属于研究来源可信性，不是治理记账
supplement_chain / inputs           留 A —— 执行路径本身，端到端集成
```

## 3. B. INTERNAL_ARCHIVE —— 77 个测试文件

```
席位与包机械
  a_prompts_measured_numbers_are_current  a_prompts_range_claim_actually_holds
  a_proposal_states_the_hash_of_its_own_block  artifacts_under_review_are_frozen
  delivery_names_no_quarantined_path  issued_deliveries_are_registered
  review_artifacts_are_outcome_clean  the_delivery_cannot_pin_itself
  the_register_speaks_one_vocabulary  the_review_round_cap_is_respected
  the_seat_ledger_ids_are_unique  the_seat_ledger_is_not_shipped_to_seats
  exposure_discoverability  recovery_anchor_is_clean
  no_committed_walk_reaches_the_quarantine
  quarantine_register_identity_survives_migration
  no_settled_question_is_sent_to_adjudication

文档与索引管理
  ops_index_is_complete  cited_records_exist  governance_docs
  every_approval_is_accounted_for  exposure_ledger_migration
  source_line_endings  the_main_block_is_last  the_precommit_hook_is_installed

裁定与档案一致性
  aaron_rulings  gridmix_rulings  the_writer_rulings_are_already_in_the_contract
  nd1_profile_r2  nd1_profile_revision_chain  feasibility_errata_register
  the_ratified_preimage_is_reconstructible

授权 / 登记管道
  registry_absence_refuses  registry_boundary  registry_path_single_construction
  registry_witness  mc_registry_contract  mc_registry_parser
  mc_supplement_registry  executor_provenance  what_the_registry_append_unlocks
  chain_state_permits_start  mc_supplement_paths_battery
  mc_supplement_coercion_census  mc_supplement_runner  mc_supplement_integration
  supplement_refusals_never_executed  the_refusing_entries_really_write_nothing
  the_subtree_gate_observes_collision_not_absence  every_sealed_final_was_read_back
  mc_n01_repairs  build_precheck_context_actually_runs

N09 脚手架与门接线
  n09_checkpoint_assertions  n09_precheck_evidence_rules  n09_r3_design_facts
  n09_scaffold_criteria  the_c_build_1_wiring_landed  c_build_2_wording_coverage
  c_build_3_over_a_real_archive  checkpoint_and_router_layers
  day_strata_classification  day_strata_dryrun  day_strata_failure_planning
  supplement_precheck  supplement_derive  supplement_build  preflight

守卫的守卫 / 覆盖仪器
  no_vacuous_guards  the_governed_subtree_helper_bites
  every_identity_pattern_is_swept  platform_gated_guards_are_declared
  no_public_mc_function_is_unreached  key_claims
  the_three_unreached_refusals  the_last_eight_unreached_branches
  resolve_partial_path_contract  resolve_partial_state_diff
```

## 4. C. DELETE_OBSOLETE_AFTER_COMPLETION

**现在只给判据和明确案例,完整清单等研究完成时再过一遍**——
那时才知道哪些真的没被引用。

```
判据   被新实现完全取代 ＋ 既不保护研究性质 ＋ 不是最终审计证据
明确案例
  ops/ 里被 v2 取代的 v1 提案（R4 v1 已被 v2 取代且 v2 已批）
  已撤回的授权记录中的重复副本
  同一轮复审的多份中间提示词（PROMPT_* 有 14 份）
  被 outcome_quarantine 迁移取代的旧路径引用
不动的
  **所有 RULING_* 与 OWNER_* 保留** —— 它们是审计证据，即使已被超越
  ops/ 全部进内部仓，C 类只在内部仓里清理，公开仓本来就不带 ops/
```

**注意:C 类几乎全在 `ops/`,而 `ops/` 整个不进公开仓。**
**所以 C 类对公开发布几乎没有影响**,它只是内部仓的整理。

## 5. 建议的公开 GitHub 结构

**关键认识:公开仓不是这个仓的子集,是一次「重新呈现」。**
面试官要的是「研究了什么 / 怎么验的 / 结论是什么」,不是学我们的治理框架。

```
nq-opening-drive-study/
├─ README.md                  <- **最重要的文件。5 分钟读完：
│                                问题 / 数据 / 方法 / 预注册 / 结论 / 如何复现**
├─ RESULTS.md                 <- 结论与图表，含证伪条件与未通过的假设
├─ METHOD.md                  <- 预注册方法：样本切分、成本模型、
│                                多重比较处理、walk-forward、bootstrap
├─ REPRODUCE.md               <- 一条命令跑通；数据从哪来、要多少钱
│
├─ src/itsf/
│   ├─ s0/                    <- 研究核心：dataset context features labels
│   │                            costs oracle stats stability gridmix study
│   ├─ mc/                    <- 多重比较：atoms bootstrap consumer
│   │                            convergence feasibility fixed_world verdict
│   ├─ data/                  <- 加载与边界：roles calendar validation manifests
│   └─ platforms/             <- 账户/成本模型
│
├─ tests/                     <- **3529 条，A 类 55 个文件原样保留**
│
├─ notebooks/                 <- 1–2 个：结果复现 + 关键图
├─ docs/
│   ├─ preregistration.md     <- 冻结的预注册（脱敏后）
│   └─ governance-summary.md  <- **一页**：说明本项目用了预注册 + 盲审 +
│                                曝光记账，审计轨迹在内部仓。**一页，不是一个目录**
└─ data/README.md             <- 不含数据；说明如何购买与校验（$14.30 + manifest 校验）
```

**不进公开仓的:**

```
ops/ 全部（159 份）        席位记账、包、裁定、恢复机械
B 类 77 个测试文件
qros-state.yaml 等运行时状态
EXPOSURE_LEDGER / REVIEWER_EXPOSURE_LOG
```

## 6. 一句话给面试官的版本（README 的开头该长这样）

> 本项目对 NQ 开盘趋势做了一次**预注册**的量化研究:先冻结假设与方法,
> 再接触数据;用 X 年 1 分钟数据做 walk-forward 与 bootstrap,
> 显式建模成本与滑点,并用多重比较框架控制「挑出来的最好那个」。
> **结论是 <…>,含证伪条件。**
> 全部结果可用 `make reproduce` 复现;数据需自购($14.30,含校验清单)。

**这一段现在还写不出来,因为研究还没做完。** 它是 §5 里最重要的文件,
**而它要等真实结论。**

## 7. 现在不做什么

```
不删任何文件        不重构        不阻塞 N09
本文件只是分类，执行在最终研究完成之后
```
