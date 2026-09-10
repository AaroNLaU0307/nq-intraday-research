# N14 CLAIM-BLIND NORMATIVE AUTHORITIES

```
RECORD_TYPE=CLAIM_BLIND_NORMATIVE_AUTHORITY_EXTRACT
FOR=N14 exact-tree MC review
CONTENT=prospective rules, definitions, thresholds, scopes, quantifiers and
        precedence ONLY. Field-selected from the sources, never row-copied.
EXCLUDED_BY_CONSTRUCTION=any prior verdict, acceptance judgement, closure claim,
        test result, or retrospective assessment of the implementation under review.
        Excluded material is COUNTED below and is not reproduced anywhere here.
CREATED=2026-09-10
```

Everything below is verbatim from an existing authority. Nothing here says, or
implies, anything about whether the implementation satisfies these rules. That
is the question you are being asked; this file only supplies the rules.

## 1. O7 -- frozen convergence policy

```
SOURCE_ID        = MC-METHOD-SPEC-S5
SOURCE_PATH      = MC_METHOD_SPEC.md   (on your allowlist, read it there in full)
SOURCE_SHA256    = a6de4a286eaff5ab7487298593f590cbee845afa1939ad4ea675ec219cf29608
SOURCE_RANGE     = section 5
AUTHORITY_TYPE   = FROZEN METHODOLOGY SPECIFICATION
WHY_REQUIRED     = O5, O6, O7, O8, O9, O10, O11 -- the inner random sources are
                   enumerated exhaustively there, and the convergence rule is
                   stated there in five clauses (a)-(e) under a heading declaring
                   that what is frozen is the RULE and not the counts.
PROVENANCE       = the runner seals a `method_spec_sha256` of this exact file into
                   the run identity; verifiable inside your allowlist.
```

## 2. O12 -- ratified boundary / drift / quantifier design

```
SOURCE_ID        = ND2-M6..M10
SOURCE_ARTIFACT  = ops/outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md **OFF-LIMITS (outcome-carrying, do not open)**
                   Quoted here so you never need to reach for it.
SOURCE_SHA256    = e9745ead35a8f51ed550ccbb08fef2d172989166fee5047311ee1dab11519380
SOURCE_RANGE     = M6 lines 88-99, M7 lines 100-111, M8 lines 112-123, M9 lines 124-135, M10 lines 136-147
AUTHORITY_TYPE   = RATIFIED DESIGN (RATIFIED_UNCHANGED 2026-08-24), prospective
FIELDS_INCLUDED  = ITEM_ID / TIER / RULING / POST_FREEZE_DEFINITION only
FIELDS_OMITTED   = rationale, alternatives, counterfactual and consultation fields;
                   omitted for minimality, not because they were adverse
WHY_REQUIRED     = O12 -- boundary band (M8), drift transplant (M9), quantifiers (M10),
                   and the object/role items M6 and M7 the later two depend on
```

```
ITEM_ID=M6
TIER=M
RULING=K 收敛对象 = 附录 A（v0.6）已冻结定义的两张分类图——positive_EV_region 与 deployable_region（逐 cell 按冻结定义算出的 (q,r)→类别映射）；比较同 seed 下 K 与 2K 两次网格分析的两张图，等价判据见 M8；明确不用不消费 K 的 Checkpoint 类别做对象（主计划 §5 禁令，空验证）。
POST_FREEZE_DEFINITION=YES
```

```
ITEM_ID=M7
TIER=M
RULING=region 角色：两 region 对 Checkpoint-0 判决是报告项（不进 GO/STOP、不作 kill）；但其 K-收敛（M6/M8）是网格分析章节自身的有效性前置——K 臂未收敛 → 按 (e) 对 K 加倍重跑（受已裁 GridRepeatPolicy.max_doublings 上限约束），未收敛期间网格章节封存为 NON_CONVERGED，deployable_region 不得支持任何 H1 进入宣称；Checkpoint-0 判决不因网格未收敛被扣押——判决不以网格结果为证据基础（verdict.py 只消费 VerdictInput 分位与 feasible；feasibility 门走 Oracle 通道计数，均不含网格）。
POST_FREEZE_DEFINITION=YES
```

```
ITEM_ID=M8
TIER=M
RULING=等价判据 = 带边界带的相等：K 与 2K 两张图逐 cell 必须同类，唯一豁免是「边界带 cell」——其定类统计量（Conservative P5；deployable 判据另含 Stress 中位）在 K 与 2K 两次取值都落在冻结 (c) 容差 max($25, 相对5%) 以内贴零（|值|≤容差）且两次取值之差亦 ≤ 同一容差；此类 cell 在两张图中一律改标第三类 boundary_band 后重比，图仍须逐 cell 相等；任何非边界带翻类 = 未收敛 → 按 (e) 加倍 K 重跑，直至收敛或触 GridRepeatPolicy.max_doublings；触限仍未收敛 → 网格章节 fail-closed 封存为 NON_CONVERGED（M7 后果生效），不得静默放行。
POST_FREEZE_DEFINITION=YES
```

```
ITEM_ID=M9
TIER=M
RULING=(a) rule-(c) 移植到 cell 层、仅用于 K 臂：每 cell × Primary 组合的键集 = {Conservative 认知层 P5, Stress 认知层中位数}（即两张区域图的定类统计量本身），K→2K 变化须 ≤ max($25, 相对5%)；(b) 美元项在 cell 层保留原义——cell 统计量与 §4.4 同量纲（月均 prop_operating USD），$25 直接适用、数值不改；非 USD 键（realized precision/recall、样本计数等）不受 (c) 管辖，属配置/身份数据，K→2K 必须逐位相等，不等即未收敛。
POST_FREEZE_DEFINITION=YES
```

```
ITEM_ID=M10
TIER=M
RULING=量词：(a) K 加倍在全部三个 master seeds 上各做（3×{K,2K} 网格分析）；(b) B 加倍同样三 seeds 各做（3×{B,2B} 全量）；M 轴不加倍——IR-29a 已裁生效（穷尽枚举支撑豁免），本项遵行不重裁；收敛要求 = 每 seed 各自满足 (a)/(c)/(d)，且 (b) 跨 seed 判定类别一致在基础档与加倍档都成立；(c) cross-seed region：三 seed 各自出图全量披露，正式发布 region = 三图交集（positive/deployable 均取交集，boundary_band 取并集），任何 cell 三 seed 异类落入并集边界带披露。算力形态如实呈报：3 seeds×（基础全跑＋2B 全跑）＝6 次全量 MC，另加 3 seeds×2K 网格通道重跑（2K 只重跑网格通道，Oracle 主通道不消费 K）；α 分支按 M14 使主通道认知层算力 ≈×2；与 E3 同席呈 Aaron。
POST_FREEZE_DEFINITION=YES
```

Dependency, quoted from the same ratification:

```
5. **M6→M7→M8→M9 是链**：对象（区域图）→角色（报告+自身有效性）→等价判据（边界带）→漂移检查（(c) 移植）。改 M6 对象则后三项失去载体；M7 改「扣押整判」则 M8 的 max_doublings 触限处置升级为判决关键路径，E3/M10 算力按最坏重算。
```

## 3. O12 -- Owner ruling that disambiguates the scope M8 applies at

```
SOURCE_ID        = DEC-N11-B25-1
SOURCE_PATH      = ops/DECISIONS.md   (FORBIDDEN to you -- it is the claim record;
                   the rule-defining cell is quoted here so you never open it)
SOURCE_SHA256    = 5ef0d06600343ee696e23d6a94e8c03a379341b5ca96771f1f3b2ed0108234ed
SOURCE_RANGE     = row DEC-N11-B25-1, verdict cell ONLY
AUTHORITY_TYPE   = OWNER RULING, rule-defining (interpretation and scope)
WHY_REQUIRED     = O12 -- fixes WHICH statistics the M8 band is applied to
CELL_EXCLUDED    = the consequence cell of the same row, and the whole of the
                   following row, whose function is retrospective rather than
                   rule-defining. See the exclusion counts in section 5.
```

```
**interpretation (ii).** Boundary-band classification applies to the CELL-LEVEL EXISTENTIAL REGION DECISION. A non-decisive combination must NOT veto convergence merely because its own statistics lie outside the band. A cell is boundary only when the combination-level statistic(s) that actually determine its existential region membership lie within the already-frozen M8 band. For the referred case — combo A stably far negative (−$5000), combo B the existentially relevant candidate moving +$3 → −$2 — the boundary logic is governed by B and is NOT vetoed by A. **This ruling introduces no new tolerance**; only the already-ratified M8 band is used, and it must not be reinterpreted as "all combinations must satisfy the band"
```

## 4. CONTROLLING PRECEDENCE

Quoted from the sources, not decided here.

```
CONTROLLING_PRECEDENCE_SOURCE   = DEC-N11-B25-1, verdict cell (quoted in full above)
CONTROLLING_PRECEDENCE_VERBATIM = "This ruling introduces no new tolerance; only the
        already-ratified M8 band is used, and it must not be reinterpreted as 'all
        combinations must satisfy the band'"

Therefore, on the sources' own terms:
  M8    defines the boundary-band equivalence test and its width.
  B-25  is later and fixes the SCOPE at which that test is applied. It changes
        neither the band nor its width, by its own words.
  M9    transplants clause (c) to the cell layer; its tolerance is clause (c)'s,
        taken from MC_METHOD_SPEC.md section 5.
  M10   fixes the quantifiers.
Where the sealed preregistration or MC_METHOD_SPEC.md speak directly, they outrank
this extract; both are on your allowlist in full.
```

## 5. WHAT WAS EXCLUDED, AND WHY

Counted, not reproduced. Reproducing it is exactly what contaminated the previous
package and stopped the previous seat.

```
PRIOR_VERDICT_EXCLUDED             = 1
PRIOR_ACCEPTANCE_EXCLUDED          = 1
PRIOR_CLOSURE_EXCLUDED             = 4
PRIOR_TEST_RESULT_EXCLUDED         = 4
IMPLEMENTATION_CORRECTNESS_EXCLUDED = 2

None of the excluded material is a rule. All of it is some prior actor's
assessment of the implementation you are reviewing, which is the one thing a
claim-blind surface may not carry. It exists in the project record; it is not
on your surface, and you must not go looking for it.
```

## 6. What this file is NOT

- Not a claim about the implementation, in either direction.
- Not authority over `MC_METHOD_SPEC.md` or `STUDY_0_PREREGISTRATION.md`.
- Not a substitute for reading the rules in their own files where they are on
  your allowlist.
- Not an outcome: every quoted line was pattern-scanned before inclusion.
