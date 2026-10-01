# N14 NORMATIVE AUTHORITIES -- the external rules O1-O12 are judged against

```
RECORD_TYPE=NORMATIVE_AUTHORITY_EXTRACT_FOR_REVIEW
FOR=N14 exact-tree MC review
CREATED=2026-09-10
CLASS=AUTHORITY (not implementation, not test evidence, not builder declaration)
```

## Why this file exists

A previous reviewer stopped here, correctly. Two mandatory obligations asked it to
decide whether the implementation conforms to a frozen rule, and the frozen rule was
not on its read surface -- only the implementation's own comments describing it. **A
producer's comment is evidence about what the producer believes it built. It cannot
establish the external rule that same producer is being judged against.** Refusing to
treat one as the other was the right call and this file is the answer to it.

Four classes are kept apart throughout, because collapsing them is the failure this
file exists to prevent:

```
NORMATIVE AUTHORITY     the rule. External to the implementation. THIS FILE, plus
                        MC_METHOD_SPEC.md and STUDY_0_PREREGISTRATION.md.
IMPLEMENTATION          what is under review. src/itsf/**. Never authority for itself.
MECHANICAL TEST         evidence about behaviour. tests/**. Never authority either --
                        a test can pin the wrong rule, which is obligation O14's point.
BUILDER DECLARATION     scope statements in the brief. Contestable by you, and never
                        a substitute for either of the first two.
```

Everything below is quoted text from an existing authority, not a paraphrase. Where a
source line had to be withheld the gap is marked inline and says what it was.

## 1. O7 -- the frozen convergence policy

**Controlling authority: `MC_METHOD_SPEC.md` section 5**, which is on your read
allowlist in full. Read it there; it is the authority, and this section only tells you
which part of it O7 turns on.

Section 5 fixes two things O7 needs:

- the exhaustive enumeration of INNER RANDOM SOURCES, which is what determines M for a
  given configuration (the spec states the Oracle primary configuration has exactly one
  such source, so M is the number of start phases, and it gives a specific expected
  value for that count);
- the CONVERGENCE RULE, five clauses (a)-(e), under the spec's own heading stating that
  **what is frozen is the RULE and not the counts**.

Clause (a) is the K-doubling requirement O7 asks about; clause (c) is the key-quantile
tolerance that obligation O12 also depends on, through the M9 transplant below.

`STUDY_0_PREREGISTRATION.md` Appendix A (also on your allowlist) supplies the frozen
grid the K draws are taken over. Where the spec and the preregistration both speak, the
preregistration is the sealed document.

**Provenance.** `MC_METHOD_SPEC.md` is named as the frozen method authority by the
project's own freeze machinery rather than by a code comment: the runner records a
`method_spec_sha256` of this exact file into the sealed run identity, and the
preregistration's interface section binds to it. You can verify that binding inside your
allowlist without taking any comment's word for it.

## 2. O12 -- boundary band, drift, and cross-seed quantifiers

Two authorities apply and they do not conflict. **The precedence below is the project's,
stated in the sources themselves -- not the builder's reading of them.**

### 2.1 RATIFIED DESIGN -- N-D2 items M6 through M10

Ratified `RATIFIED_UNCHANGED` on 2026-08-24 under Aaron's named batch delegation. The
text below is quoted from the ratification record, which is itself **OFF-LIMITS
(outcome-carrying, do not open)** -- `ops/outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`.
You do not need it: what follows is the extract, taken under an Owner authorization and
scanned line by line against the project's outcome-restatement patterns before display.

**Two source lines were withheld.** Both sit inside the M10 block, both are
rationale/consultation keys, and **no `RULING=` line was withheld** -- that was asserted
mechanically before this file was written. The withheld lines are marked in place.

```

```
ITEM_ID=M6
TIER=M
RULING=K 收敛对象 = 附录 A（v0.6）已冻结定义的两张分类图——positive_EV_region 与 deployable_region（逐 cell 按冻结定义算出的 (q,r)→类别映射）；比较同 seed 下 K 与 2K 两次网格分析的两张图，等价判据见 M8；明确不用不消费 K 的 Checkpoint 类别做对象（主计划 §5 禁令，空验证）。
理由=规则 (a) 说「判定类别不得变化」，网格层唯一有类别结构且消费 K 的对象就是这两张冻结区域图；定义逐字已冻结（Conservative P5>0；同组合全判据），无需发明新统计量；deployable_region 是「有资格支持进入 H1」的唯一对象，其稳定性正是 K 存在的理由。
备选=仅 positive_EV_region（拒：H1 资格挂在 deployable 上）；关键分位数作唯一对象（拒：连续量漂移可不翻类，「类别不变」失去载体——分位检查由 M9 补充承担）；裁 K 不适用 (a)（拒：K 是 §5 明列加倍轴且恰是抽样轴，豁免需 IR-29a 级"非抽样轴"论证而 K 不满足）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（对象选择不改 GO/STOP 方向；区域非 Checkpoint 输入，见 M7）
POST_FREEZE_DEFINITION=YES
若被裁反=对象改分位数-only → M8 失去载体、M7 类别语义悬空；对象含 Checkpoint 类别 → 触发 §5 禁令。
```

```
ITEM_ID=M7
TIER=M
RULING=region 角色：两 region 对 Checkpoint-0 判决是报告项（不进 GO/STOP、不作 kill）；但其 K-收敛（M6/M8）是网格分析章节自身的有效性前置——K 臂未收敛 → 按 (e) 对 K 加倍重跑（受已裁 GridRepeatPolicy.max_doublings 上限约束），未收敛期间网格章节封存为 NON_CONVERGED，deployable_region 不得支持任何 H1 进入宣称；Checkpoint-0 判决不因网格未收敛被扣押——判决不以网格结果为证据基础（verdict.py 只消费 VerdictInput 分位与 feasible；feasibility 门走 Oracle 通道计数，均不含网格）。
理由=附录 A 冻结限定「仅为可行性边界，不构成 H1 表现宣称」——把 region 升为 kill 等于冻结后授予它判决权（冻结文本恰在剥夺方向写死了它的地位）；反向也不放松任何东西（region 从未是判决输入）。(e)「禁止用未收敛结果判决」按「判决所用的结果」读：判决用的是 B/seeds 臂与 (c)(d) 覆盖的判定统计量；网格未收敛冻结的是网格自己的输出资格（H1 入场）——正是它有权力的那一层。
备选=网格未收敛扣押整个判决（更保守读法，如实呈报但拒：让非判决诊断以噪声人质挟持冻结主判决，算力暴露仅由 max_doublings 兜底；Aaron 若采此读法，M8 容差带从"减少重跑"升级为"判决能否发出"的关键路径，E3/M10 算力须按最坏重算）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（两个方向都不该在冻结后移动权力）
POST_FREEZE_DEFINITION=YES
若被裁反=deployable_region 升为 GO 判据 → 与附录 A 冻结限定正面冲突，须走冻结修订而非裁定；采扣押读法 → N16 最坏时延由网格收敛决定。
```

```
ITEM_ID=M8
TIER=M
RULING=等价判据 = 带边界带的相等：K 与 2K 两张图逐 cell 必须同类，唯一豁免是「边界带 cell」——其定类统计量（Conservative P5；deployable 判据另含 Stress 中位）在 K 与 2K 两次取值都落在冻结 (c) 容差 max($25, 相对5%) 以内贴零（|值|≤容差）且两次取值之差亦 ≤ 同一容差；此类 cell 在两张图中一律改标第三类 boundary_band 后重比，图仍须逐 cell 相等；任何非边界带翻类 = 未收敛 → 按 (e) 加倍 K 重跑，直至收敛或触 GridRepeatPolicy.max_doublings；触限仍未收敛 → 网格章节 fail-closed 封存为 NON_CONVERGED（M7 后果生效），不得静默放行。
理由=纯 exact equality 在离散网格上会因单个贴零 cell 的 MC 噪声翻转而无限加倍——不是保守，是不可终止；自由发明第二个容差是新数字。用冻结 (c) 的 max($25,5%) 做边界带宽度是唯一零新数字方案：贴零幅度小于判定容差的 cell 其符号本在冻结精度之下，诚实标 boundary_band 比强迫站队更真；max_doublings 是已裁结构（DR-M6-E）。
备选=exact equality（拒：非终止风险）；「允许 ≤N 个 cell 翻转」（拒：N 是凭空新数字，且允许非贴零 cell 翻转吞掉真失稳）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（不触 GO/STOP；比 exact 弱、比自由容差严，另强制 boundary_band 诚实披露）
POST_FREEZE_DEFINITION=YES
若被裁反=改 exact equality 须同时给 max_doublings 触限处置（否则 N16 无终止保证）；改自由 N-cell 容差 → 无出处新数，N17 按 2.1 同款披露。
```

```
ITEM_ID=M9
TIER=M
RULING=(a) rule-(c) 移植到 cell 层、仅用于 K 臂：每 cell × Primary 组合的键集 = {Conservative 认知层 P5, Stress 认知层中位数}（即两张区域图的定类统计量本身），K→2K 变化须 ≤ max($25, 相对5%)；(b) 美元项在 cell 层保留原义——cell 统计量与 §4.4 同量纲（月均 prop_operating USD），$25 直接适用、数值不改；非 USD 键（realized precision/recall、样本计数等）不受 (c) 管辖，属配置/身份数据，K→2K 必须逐位相等，不等即未收敛。
理由=(c) 原作用对象（§4.4 月均 prop_operating USD 分位）在 cell 层有直接同量纲对应物，移植零换算零新数；键集取定类统计量因它们是 M6/M8 的力学来源——分位漂移超容差而未翻类是「正在滑向翻类」的前兆，(c) 显式拦截；对 Checkpoint 自身的量，(c) 保持原冻结作用域。
备选=键集扩到全部 cell 输出分位（拒：与 M8 分类图判据冗余、报告噪声大）；美元项在 cell 层作废只用 5%（拒：量纲就是 USD/月，贴零 cell 的相对 5% 退化为零容差）。
CONSULTED_S0=NONE
MAKES_GO_HARDER=NO（K 臂新增漂移检查，属诚实性）
POST_FREEZE_DEFINITION=YES
若被裁反=移植取消 → M8 边界带失去冻结数字来源，须另立数；非 USD 键若套 $25 → 量纲错误。
```

```
ITEM_ID=M10
TIER=M
RULING=量词：(a) K 加倍在全部三个 master seeds 上各做（3×{K,2K} 网格分析）；(b) B 加倍同样三 seeds 各做（3×{B,2B} 全量）；M 轴不加倍——IR-29a 已裁生效（穷尽枚举支撑豁免），本项遵行不重裁；收敛要求 = 每 seed 各自满足 (a)/(c)/(d)，且 (b) 跨 seed 判定类别一致在基础档与加倍档都成立；(c) cross-seed region：三 seed 各自出图全量披露，正式发布 region = 三图交集（positive/deployable 均取交集，boundary_band 取并集），任何 cell 三 seed 异类落入并集边界带披露。算力形态如实呈报：3 seeds×（基础全跑＋2B 全跑）＝6 次全量 MC，另加 3 seeds×2K 网格通道重跑（2K 只重跑网格通道，Oracle 主通道不消费 K）；α 分支按 M14 使主通道认知层算力 ≈×2；与 E3 同席呈 Aaron。
[SOURCE LINE 139 WITHHELD -- it matches an outcome-restatement pattern. It is a rationale/consultation key, NOT a RULING line; every RULING line in this extract is present and unredacted.]
备选=单 seed 加倍（省 4 次全量跑；拒为默认，留作 Aaron 的显式降档选项——残余风险=seed 特异未收敛不被发现，须 N17 披露）；region 取并集（拒：单流侥幸 cell 入图）；三图逐 cell 强制相同（拒：把 (b) 的「判定类别一致」扩写成逐 cell 一致，强于冻结文本且与 M8 边界带冲突）。
[SOURCE LINE 141 WITHHELD -- it matches an outcome-restatement pattern. It is a rationale/consultation key, NOT a RULING line; every RULING line in this extract is present and unredacted.]
MAKES_GO_HARDER=YES
POST_FREEZE_DEFINITION=YES
若被裁反=降单 seed 加倍 → 残余风险披露义务；M 轴要求加倍 → 与已生效 IR-29a 冲突，须先撤销该 IR。
```

```

3. **M3(a) 分母与 M3(c)=0.25 必须同改**：分母改回 offered 则 0.25 失效（skip 率数倍缩小）。
4. **M5 改场景集 ⇒ M1/M3 的「两场景各自成立」量词同步改**。
5. **M6→M7→M8→M9 是链**：对象（区域图）→角色（报告+自身有效性）→等价判据（边界带）→漂移检查（(c) 移植）。改 M6 对象则后三项失去载体；M7 改「扣押整判」则 M8 的 max_doublings 触限处置升级为判决关键路径，E3/M10 算力按最坏重算。
6. **M10 依赖 IR-29a（已生效）**：M 轴要加倍须先撤该 IR；M10 的 6 全量跑＋3 网格加倍、M12/M14 的 α×2、E3 冒烟两跑共同构成 N16 算力总账——三处必须同席裁。
7. **M12 依赖 IR-28c 的 never_primary 钉定**（改用成本敏感性作 α 对象须先解钉）；**M13 依赖 §2.5 冻结角色表**（扩集合须冻结级论证）。
8. **M11 生效 ⇒ N07 必须替换 fixed-world 守卫测试**（从「无规则」改为「仅此规则」），漏做即出现「代码守无规则、裁定有规则」自锁。
```

### 2.2 OWNER RULING -- B-25, 2026-09-08

Quoted from the decision ledger, which is on your forbidden list because it is the
CLAIM record. These two rows are the ruling itself, extracted so you never need to open
that ledger:

```
| DEC-N11-B25-1 | 2026-09-08 | Aaron | OWNER_DECISION | **interpretation (ii).** Boundary-band classification applies to the CELL-LEVEL EXISTENTIAL REGION DECISION. A non-decisive combination must NOT veto convergence merely because its own statistics lie outside the band. A cell is boundary only when the combination-level statistic(s) that actually determine its existential region membership lie within the already-frozen M8 band. For the referred case — combo A stably far negative (−$5000), combo B the existentially relevant candidate moving +$3 → −$2 — the boundary logic is governed by B and is NOT vetoed by A. **This ruling introduces no new tolerance**; only the already-ratified M8 band is used, and it must not be reinterpreted as "all combinations must satisfy the band" | `src/itsf/mc/grid_replay.py` — `satisfying_combos` (the frozen per-combination predicate, single source of both the cell's class and of which combinations changed it) and `compare_region_maps` (deciding set = `satisfying(K) XOR satisfying(2K)`); `tests/test_mc_grid_replay_n11.py::test_b25_case1_a_non_decisive_combination_does_not_veto` fails under (i) and passes only under (ii); `::test_b25_case4_the_ruling_introduced_no_new_tolerance` asserts mechanically that no epsilon, threshold, percentage or second tolerance entered | **B-25 CLOSED**; the refusal code `grid_replay_boundary_band_multi_combo_unruled` is removed because the case it named is now ruled. **N11 = CLOSED** — its closure conditions are satisfied (tier A+B 5295 passed / 0 failed; full suite 5515 passed, 1 known B-20 xfail). B-26 is untouched and out of scope |
| DEC-N11-B25-2 | 2026-09-08 | Aaron | OWNER_DECISION | **B-25 semantic acceptance check: PASS, and a CORRECTION to the evidence wording of DEC-N11-B25-1.** That row described the deciding set as `satisfying(K) XOR satisfying(2K)` without stating the precondition, and the module docstring went further and claimed a cell's class "changes exactly when the satisfying set changes". **That claim is false**: witness substitution — `satisfying(K)={A}`, `satisfying(2K)={B}`, IN at both passes — changes the set completely while membership holds. The RULING and the CODE were never wrong: `compare_region_maps` compares the cell-level classes first and returns before the deciding set is computed, so M8 was never reachable by witness substitution. Only the prose was wrong | measured: `satisfying(K)={A}`, `satisfying(2K)={B}`, XOR={A,B} non-empty, `cell_category` IN at both, `boundary_band_cells=()` and `flipped_cells=()` — M8 did NOT fire, while rule (c) independently reported 126 drift violations and `converged=False`. The executable AST of `grid_replay.py` is byte-identical to the pre-correction commit with docstrings stripped, so the fix is documentation-only. Pinned by `tests/test_mc_grid_replay_n11.py::test_b25_caseA..caseD` and `::test_b25_membership_not_witness_identity_gates_m8`, which asserts `M8 fired IFF the class changed` across all four cases | **B-25 stays CLOSED** and **N11 stays CLOSED**; no production-logic change was made and none was warranted. Tier A+B 5300 passed / 0 failed; full suite 5520 passed, 1 known B-20 xfail |
```

### 2.3 PRECEDENCE -- as the sources establish it, not as the builder prefers it

```
M8 (ratified 2026-08-24)   defines the boundary-band EQUIVALENCE TEST and its width.
B-25 (Owner, 2026-09-08)   later, and DISAMBIGUATES the SCOPE at which M8 is applied
                           for a multi-combination cell. Its own text settles the
                           relationship: "This ruling introduces no new tolerance; only
                           the already-ratified M8 band is used, and it must not be
                           reinterpreted as 'all combinations must satisfy the band'."
                           So B-25 does NOT alter the band. It fixes WHICH statistics
                           the band is applied to.
B-25-2 (Owner, same day)   corrects the EVIDENCE WORDING of B-25-1 and a module
                           docstring. Its own text states the ruling and the code were
                           never wrong -- only the prose. It changes no rule.
M9                         transplants clause (c) to the cell layer, K arm only. Its
                           tolerance is clause (c)'s, taken from MC_METHOD_SPEC section 5;
                           it introduces no new number.
M10                        fixes the quantifiers: which seeds double, and that the
                           published region is the INTERSECTION across seeds.
```

The ratification record also states the dependency chain explicitly:
**M6 -> M7 -> M8 -> M9 is a chain** -- object, then role, then equivalence test, then
drift check -- so a finding that one link is misimplemented has consequences for the
ones after it. That sentence is in the extract above.

**If you find the implementation applying the band at a scope B-25 excludes, or
inventing a second tolerance, that is a conformance finding against these authorities**
-- and it is exactly the comparison O12 asks for. This file takes no position on whether
it does.

## 3. What this file is NOT

- Not a claim that the implementation conforms. It states the rules; you decide.
- Not a substitute for reading `MC_METHOD_SPEC.md` and `STUDY_0_PREREGISTRATION.md`
  yourself -- both are on your allowlist in full, and both outrank this extract where
  they speak directly.
- Not an outcome. No statistical result, verdict or revealed value appears here; the
  extraction was pattern-scanned before display and the withheld lines are marked.
- Not authority over the reviewer contract, the node definition, or the sealed
  preregistration. It sits under all three.
