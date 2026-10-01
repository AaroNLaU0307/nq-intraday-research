# Fable 复审记录 —— 真实数据前的 outcome-blind 工程安全复审

```ini
RECOMMENDED_MODEL=Fable 5.1
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=xhigh
EXECUTION_MODE=STANDARD
ROLE=auditor
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder / producing session（Opus 5）
LANE=N/A（工程安全复审；不是 A2，不是 Stage I，不解开任何 QROS 门）
OUTCOME_EXPOSED=NONE（逐项声明见 §7）
PREREG_SEALED=N/A
SUBAGENT_OR_WORKFLOW_BUDGET=0 used（单会话、零子代理、零 workflow）
REVIEW_ID=ENG-SAFETY-PRE-REAL-DATA-001
REVIEWED_PACKET_SHA256=d21c552e5c1887b2693192c51136c55a538575107940495f77162a7daf4846fa
REVIEWED_PACKET_SOURCE=git HEAD c18ef1546f2faed33b9ee7944701ce9b1303cf93 的已提交字节（与开工时登记册一致）
MEASURED_AT(packet)=0cefc1503858ecf3b1dc5c90ec8bb3de9b1daa97
SOURCE_SET_PIN=bbae823edc782cf999120cb8441bf3bafae4304f（7 个源文件 sha256 与登记册逐一相符，复审始末各核一次）
DATE=2026-09-05
WRITES_TO_REPO=0（本记录只落在会话 scratchpad；抄进 ops/ 是接收方的动作）
```

---

## 0. 裁定

**HOLD。**

不是因为今天不安全。今天没有任何代码路径能读到 Development 数据，这一点我复现了（§3 第一条）。
HOLD 是因为送审包 R2 的承重证据「链路能跑到 P4」在两处不成立：

- **H1** P4 能在「封存件从未进入归档」的情况下取得，且这正是现有测试的构造方式。
- **H2** 从真实入口到 P4 的 gate-first 组合路径不存在；现有链路跳过全部 18 道 A_PRECHECK / B_DERIVE 门。

两条都是复现的事实，不是自述。在它们闭合之前，任何把 ① 接线出来的运行路径都不应被当作「已验证到 P4」。

**Q3 直接回答：不存在阻断 Aaron「命名一个 job_dir」这一治理动作的工程发现。**
H1 / H2 阻断的是把 job_dir 接进任何被当作运行路径的代码，也就是 ① 的后半句（「我接线、跑全套」），不是前半句。

---

## 1. Critical / High

### H1（High，已复现）`run_supplement_chain` 从不把 `out_dir` 与 `runs_dir` 绑定；P4 可在封存件未归档时取得

- 封存写到 `out_dir`（`run_c_build_2 -> seal_supplement_production -> resolve_partial(out_dir, …)`）。
  归档拷的是 `runs_dir`（`ARCHIVE_SEAM(runs_dir, archive_root)`）。两者是独立参数，链路里没有任何一行断言 `out_dir` 位于 `runs_dir` 之下或等于它。
- `run_c_build_3` 只断言 (a) 本地 seal 未变、(b) 已归档字节未丢失。它从不检查归档里含有 seal 的 sha256。
- **复现（真实 `archive_sealed_run`，未打桩，仅 tmp 目录）**：`out_dir=tmp/seal`、`runs_dir=tmp/runs`（空目录）、`archive_root=tmp/arch`
  → `verdict=P4`，`archive_status=archive_ok`，seal 在 `tmp/seal`，归档里只有一个空的 `runs/`。
  脚本：scratchpad `test_repro_out_dir_unbound.py::test_A`。
- **现有证据本身就是这个形状**：`tests/test_supplement_chain.py` 的 `_drive` 与 `test_bars_to_P4_with_NOTHING_mocked_but_the_archive`
  都用 `out=tmp/"seal"`、`runs_dir=tmp/"runs"`；`test_it_creates_no_directory_of_its_own` 断言 P4 之后 `tmp/runs` 不存在。
  所以「链路到 P4」是在归档一个不存在的目录（且归档步打桩）时测得的。
- 附带：`_assert_c_build_1` 的「写前为空」快照对的是 `runs_root`，不是实际写入的 `out_dir`。

Policy A 的 `P4 = local_seal_ok AND archive_ok` 在这段代码里只保证了「某个目录归档成功」，没有保证「封存件有第二份拷贝」。
这是 R2 的核心承重，也是 ND1 归档策略存在的理由。

### H2（High，已复现）不存在 gate-first 的组合生产路径；链路跳过 A_PRECHECK 与 B_DERIVE

- `run_supplement_production` 是 `NoReturn`：过 `assert_real_run_allowed` → 读 registry → 数 P2 → 无条件 raise。它从不调用任何门，也不调用链路。签了 P2 也走不到链路。
- `supplement_precheck / supplement_derive / supplement_build` 是报告器（逐门跑、不停、返回报告），不是组合。
  仓内没有任何代码把 A_PRECHECK → B_DERIVE → 数据读取 → 链路串起来（`run_supplement_chain` / `run_stage_gates` 在 src 中无生产调用方）。
- 链路自己只跑 C_BUILD 的门（`gates_at`），而且测试给它的 `base_ctx` 是 `runs_root=None, head_commit="0"*40, registry_text=""`。
  13 道 A_PRECHECK 与 5 道 B_DERIVE 一道都没跑就到了 P4。
- **目录创建这一步无人拥有**：`plan_supplement_paths` 在 `runs_target` 已存在时拒绝（`plan_target_exists`），而 `resolve_partial` 要求 `out_dir` 已存在。
  `out_dir` 不存在时链路以裸 `FileNotFoundError` 逃出，不是 `ChainRefusal`，不是任何门（复现：`test_C`）。
  A1 授权只建了空的 `supplements/`（两个治理根下各一个，均为空，已核），`<id>_<UTC>` 仍要有人 mkdir，而链路文档写明 creates no directory。
- 推论：① 之后，真正读到 Development 数据的那条路径将是 builder 新写的入口；没有任何结构性机制迫使它在 `load_real` 之前过 18 道门与 live P2。
  这与 `ops/P2_WITHDRAWN_NO_EXECUTION_PATH_2026-08-31.md`（对一个永远无法行使的入口签了 P2）同形。

---

## 2. Medium

### M1（Medium，已复现）`retry_permitted` 被当作封存成功；链路在 Router B 察觉之前先执行了归档 I/O

- `run_c_build_2` 对任何不抛异常的 `resolve_partial` 结果都返回 `local_seal_ok=True`，包括 `retry_permitted`（分支 C：把歧义残留移开、不写最终文件）。
- 链路随后执行 `ARCHIVE_SEAM`（真实拷贝），然后 `run_c_build_3` 才发现 `local_seal_absent` → Router B `local_seal_failed`。
- 复现：预置一个歧义 `.partial` → `ChainRefusal C_BUILD_3 / local_seal_failed`，但 `arch/runs` 已存在（`test_B`）。
  后果：归档根下出现一个从未封存的 run 的「archive of record」；下一次重试会撞 `dest.exists()` 拒绝，一个 seal 正常的 run 会被记成 A1。
- 修法方向（不施工）：`action == "retry_permitted"` 应在第二时刻就产生 `local_seal_ok=False`。

### M2（Medium，论证缺口已复现）BD-5「archived_bytes_deleted → A1」的排除法不封闭

Aaron 要求攻击的就是这条。三处：

1. **答案空间取错了层。** 排除法排的是 Router B 的三元 {P4, A1, 被拒的 seal}；但已批 P3 的后继是 `('P4', 'A1', 'F2', 'CR1')`（复现：`sc.EVENTS["P3"].successors`）。
   F2（post-start failure、residue 保留、带 incident）从未被排除。项目自己的先例 R3 §5 更把「P3 之后的未知状态」路由到 INDETERMINATE → Aaron，
   理由正是「把未知状态记成已知状态」。归档字节是谁删的、还删了什么，此刻是未知的。
2. **A1 的行造不出来。** A1 必填 `archive_code`，取值只能是封闭的 `ARCHIVE_CODES`（`inventory_unavailable / file_unreadable / file_digest_mismatch / set_equality_refused / set_equality_unreached`）。
   `archived_bytes_deleted` 不在其中，而 `classify_archive_report` 按设计拒绝 `archive_ok` 报告。
   复现：`PlannedEvent("A1", …)` 无 `archive_code` → `planned_event_missing_field`。所以 `decide_after_seal` 返回的 "A1" 是一个没有合法登记行的字符串。
3. **A1 是非终态，但它的出口对的是错的对象。** A2 必填 `source_and_archive_exact_inventory_match / per_file_sha256_match / n_files`，全部关于本 run 的拷贝；
   对「更早 run 的已归档字节被删」不要求任何恢复证据。A1 → A2 → P5 可以在被毁证据毫无交代的情况下闭合本链。

今天无实害（没有任何代码追加登记行），但这是一条将被接线的裁定。它应当作为问题回到 Aaron，而不是由席位改签。我在这里不做裁定。

### M3（Medium，已复现）真实读取前的两道「锚」今天都不锚

- `assert_real_run_allowed()` 以生产默认值通过（复现）。`ops/SECOND_COPY_ATTESTED.flag` 断言的是 2026-07-28 的状态；
  attestation 里的 `backup_root=E:\quant-data` 现在不存在（复现）。门只查 flag 是否存在，不查此刻可达。
- manifest 是信任根却无处钉住：`manifest.json` sha256 `d8d1edc7…`（候选 A、B 逐字节相同，复现）只出现在 preflight 文档里，不在 `FROZEN_HASHES`，不在任何授权句里。
  `load_manifest` 让 `_local_manifest.json` 优先。它今天没有 `files` 映射，哪天多了一个就静默压过官方 manifest。
  备份卷不在，读取时就没有任何独立于 job_dir 自身的东西能证明 manifest 没被换。
- 建议（仅建议，属 Aaron 的 ① 措辞）：授权句里逐字钉 `manifest.json` 的 sha256，并在 ① 前决定是否先恢复第二份副本。

### M4（Medium，流程，已复现）交付件在席位持有期间被反复改写，登记册随之改钉

时间线（本机时钟）：

| 时刻 | 观察 |
|---|---|
| ~03:59 开工 | `git status` 仅 `ops/ARTIFACTS_UNDER_REVIEW.json` 改动；包 sha256 `d21c552e…` = 登记册 = HEAD 已提交字节 |
| 04:00:38 | 包与 `ops/NEXT_HANDOFF.md` 被另一会话改写（包 §1 表格改成代码块，含字面 `%d`：「以下 %d 条」）；包 → `c7d9fbec…` |
| 04:00:54 | 登记册把包的 sha256 改为 `c7d9fbec…`，`issued_at` 未动 |
| 全套件运行中 | `test_the_delivery_cannot_pin_itself` 看到第三个版本 `0cb52697…` |
| 04:12:57 / 04:14:18 / 04:14:27 | 包 → `522b435f…`（第四版）；handoff 再改；登记册再改钉；`ops/REVIEWER_EXPOSURE_LOG.md` 亦出现改动 |

登记册表头写着 Frozen while a reviewer holds them。这是 `INCIDENT_TRANSPORTED_ARTIFACT_MUTATED_20260824` 的同类。
本记录绑定的是已提交字节 `d21c552e…`；受审源码 7 件始终未动，所以技术裁定不受影响；但「席位审的是哪份包」需要 Aaron 认定。
另：`ops/_head.tmp`、`ops/_offlimits_table.tmp` 被提交进了 c18ef15。

---

## 3. 对 §3 四条自述弱点的核实

| # | builder 自述 | 核实结果 | 严重度 |
|---|---|---|---|
| 一 | `assert_real_run_allowed` 不拦 `load_real`；保护来自「无人调用」+「无 job_dir」 | 属实，复现：门通过；src 中零处构造 `DevelopmentSignalLoader`、零处 `job_dir` 常量；tests 只用 tmp_path，且 conftest 按路径子串（`databento-archive` / `c:\users\aaron\quant-data`）拦真实归档，候选 A、B 都命中该子串、均被拦。 | 作为今天的状态可接受；作为 ③ 之前的保护形态不可接受（见 H2） |
| 二 | `_check_role` 分不清 attested primary 与副本 | 属实，复现：A、B 都通过；另 `development_signal\..\..\evil\JOB`、`development_signal_fake\JOB`、role 标记只在文件名里，三者也都通过；只有混合 role 被拒。`load_real(filename)` 亦不校验 `filename`（`..` / 绝对路径可出 job_dir），靠 manifest 按 basename 查 sha256 兜底。 | Low（loader 属性）；A/B 之选是 Aaron 的治理选择，守卫不会替他选。机械事实支持 A |
| 三 | `UNMAPPED_SEAL_CODES` 7 条无门、全部大声拒绝 | 属实：`seal_failure_router` 在 `run_c_build_2` 的 except 内抛 `ClassificationError`，原样逃出（非 ChainRefusal、非门）。7 个 raise 点都在 `resolve_partial` 写入之前，无残留。 | 可接受（fail-closed）；但 P3 之后逃出的未分类异常 = 悬挂 P3 → CR1，与 H2 的裸 OSError 同形 |
| 四 | BD-5 由封闭枚举排除法得到 | 不封闭，见 M2 | Medium |

---

## 4. Low / 备注

- **L1** `_require_plain_name` 的「bare file name」声称在 Windows 上比代码宽：`NUL`、`CON.json`、`x.json.`、`x.json `、含 `\x00`、含 RTL override 全部接受（探测）。
  生产只传常量 `SUPPLEMENT_FILENAME`，且该码已归 caller-error。`resolve_partial` 也不查 `partial` / `final` 本身是否 reparse point（规划器只查根与父目录）。声称与代码的缺口，不是缺陷。
- **L2** `archive_sealed_run` 开头对陈旧 `<run>.partial` 目录做 `rmtree`（S0 closeout 裁定）。它是从链路可达的删除路径；补充件的 `SILENT_DELETE_FORBIDDEN` 是否覆盖归档侧目录，文本上没有说。提请知悉。
- **L3** 结构性守卫 `_FORBIDDEN=(build_s0_dataset, compute_day, iter_day_contexts, d_open_from_ret_open30, _ensure)` 覆盖整个 `itsf/mc` 包；`supplement_inputs` 改用 `encode_f10` 的自述与代码一致。R3 本身没有发现问题。
- **R1 本体**：`resolve_partial` 五个分支行为与文档一致，九种越界形式全拒（探测）；`_preserve` 不覆写既有 divergent 件。修复本身站得住；不够的是接在它上面的层（M1、H1）。这是 Q1 的答案：不安全，但不是因为那次修复。

---

## 5. 四问

- **Q1** 修复够不够：机制够，承重不够。`run_c_build_2` 把「没抛异常」当作「封存成功」（M1），链路不知道 seal 落在哪里（H1）。
- **Q2** 一：Medium（今天可接受，③ 前不可）；二：Low，外加一个必须由 Aaron 做的 A/B 选择；三：可接受；四：Medium。
- **Q3** 无发现阻断「命名 job_dir」。H1、H2 阻断「把 job_dir 接进被当作运行路径的代码」。建议命名 A（attestation 覆盖的 primary），理由机械。
- **Q4** 未被审到的高风险面：(a) `supplement_registry.py`（1501 行，P2 解析器；R4 残留「契约字段名 ≠ 解析器字段名」），我没有读它；(b) `registry_boundary.py`，未读；
  (c) 无人拥有的 `<id>_<UTC>` mkdir 步骤（H2）；(d) `build_universe` 吃 139 个月 1 分钟 bars 的内存与时间，不是安全问题，是 P3 之后的崩溃风险；(e) 归档侧陈旧 `.partial` 的 rmtree（L2）。

---

## 6. 复现记录（全部只读；仓库 HEAD 与受审源码复审始末未变；未生成 `__pycache__` / `.pytest_cache`）

```
HEAD                     c18ef1546f2faed33b9ee7944701ce9b1303cf93（未变）
4 个指定测试文件          86 passed, 40 subtests passed
全套件                    4 failed, 4993 passed, 468 subtests（期望 4997 passed）
                         4 条失败全部是登记册 / 交付件 / handoff 的治理守卫，而且是它们在正确地工作：
                           test_a_live_prompt_exists_EXACTLY_WHEN_the_register_is_armed   ISSUED prompts [] but armed reviews [ENG-SAFETY-PRE-REAL-DATA-001]
                           test_the_live_handoff_carrier_names_both_ledgers                NEXT_HANDOFF.md does not name ops/EXPOSURE_LEDGER.md
                           test_every_registered_review_has_a_delivery_that_claims_it      register armed for a review no ISSUED delivery claims
                           test_the_delivery_hash_still_matches_the_bytes_on_disk          c7d9fbec… != 0cb52697… "moved after issuance"
                         与 M4 的在途改写一致；与受审的 7 个源文件无关。
assert_real_run_allowed  通过（生产默认值）
E:\quant-data            不存在
候选 A / B               均存在；143 项 / 139 个 .dbn.zst；manifest.json sha256 相同 d8d1edc7…；_local_manifest.json 无 files 映射；
                         load_manifest 落到官方 manifest，141 条；数据文件不在 manifest 0，manifest 条目不在磁盘 0；
                         两端点 expected sha256 与 preflight 所记一致（未对任何 payload 计算哈希）
链路复现脚本             scratchpad/test_repro_out_dir_unbound.py（A / B / C 三条，全部按预期证实缺陷，仅 tmp 目录）
契约复现脚本             scratchpad/check_contract.py；loader 探测 scratchpad/check_loader_boundary.py
```

## 7. 席位曝光声明（供 `ops/REVIEWER_EXPOSURE_LOG.md` 追加；我只读，不写该台账）

- 未读 §1 的 12 个文件中任何一个；未列出 `ops/outcome_quarantine/` 目录内容；未打开任何 `.dbn.zst`；未调用 `load_real`。
- 读过的 ops/ 文件：`REVIEW_PACKET_PRE_REAL_DATA_2026-09-02.md`（HEAD 版）、`PREFLIGHT_1_DEVELOPMENT_INPUT_2026-09-02.md`、`PREFLIGHT_BEFORE_REAL_DATA_2026-09-02.md`、
  `DELIVERY_C_BUILD_2_WORDING_AT_CAP_2026-08-30.md`、`BUILDER_DECISIONS_2026-09-02.md`、`ARTIFACTS_UNDER_REVIEW.json`、`OUTCOME_CARRYING_ARTIFACTS.json`、
  `physical_copy_attestation.json`、`SECOND_COPY_ATTESTED.flag`、`_head.tmp`、`_offlimits_table.tmp`（= §1 表）、`NEXT_HANDOFF.md`（04:00:38 工作树版，作为数据读）、
  `REVIEWER_EXPOSURE_LOG.md` 的工作树 diff（只看了另一会话追加的行）。`ls ops` 只看了文件名。
- grep 范围：仅 `src/`、`tests/`、`gate1/`，模式为代码标识符（`load_real`、`job_dir`、`development_signal`、`run_supplement_chain` 等）。
  从未在 `ops/` 内检索，从未检索 verdict / exposure / 结果类词。NEXT_HANDOFF 的「BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY」是在我开工后才出现的，上述范围与它不冲突。
- 结论：`OUTCOME_EXPOSED=NONE`。本席位是否仍具备未来 Stage I 资格，由 Aaron 认定。

## 8. 本次没有做的事

未写入仓库任何字节；未修复任何发现；未创建任何目录；未追加任何台账；未开子代理或 workflow；未对 BD-5 改签。
