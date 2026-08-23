# N06 review handoff — ITSF supplement machinery

```
ARTIFACT_TYPE=REVIEW_HANDOFF
IS_CONFORMANT_REVIEW_PACKET_V1=NO
WHY_NOT=qros packet is the only producer of a Review Packet v1; it renders
        from a qros-state.yaml this project does not have, and LANE/STAGE
        are DECLARED fields that spec §2.4 says are never inferred.
PRODUCED_BY=Opus 5 main agent (builder seat) — self-report, not a verification
GENERATED_AT_HEAD=5f094cbfd7b54eeb7091e345af10331094e9d4d3
ARTIFACT_TRANSPORT=durable file in the project directory; SHA256 recorded below
```

> **Read this as the builder's hand-off, not as a generated packet.** Every
> line is origin-tagged. `MECH` = computed here from the repository;
> `BUILDER` = self-reported; `DECLARED` = **belongs to Aaron and is not
> filled in**; `CANON` = verbatim excerpt with a path.

---

## 0. Round 2 returned HOLD; this is the round-2 repair candidate

A SECOND fresh Sol session reviewed 17904bf and returned **HOLD** on one
High: `seal_supplement_production` read the caller's payload several times,
so a stateful mapping (reachable with nothing private) showed compliant
rows to every check and rows carrying `pnl` to the serializer --
`SEAL_RETURNED=YES`, `ROWS_READS=4`, `FORBIDDEN_PNL_SERIALIZED=True`,
`DECLARED_ROWS_DIGEST_MATCH=False`. Reproduced independently here, then
repaired: `freeze_payload()` consumes the caller's mapping ONCE at seal
entry and every check plus the serialization consume that snapshot.

That finding also **refuted a claim I had made** -- that the forgeable
capability was harmless because "re-derivation catches every lie".
Re-derivation only holds when the bytes derived from and the bytes used
are the same. The claim is struck through in place in
`ops/N06_HOLD_REPAIR_EVIDENCE.md` §3 rather than deleted. Full record:
`ops/N06_ROUND2_HOLD_REPAIR_EVIDENCE.md`.

Round 2 also independently confirmed all four round-1 closures.

**N06 has NOT passed.** Round 3 belongs to a THIRD fresh Sol session that
was neither the builder nor either previous reviewer.

## 0b. What changed since the first hand-off

A fresh Sol N06 review returned **HOLD** on the previous candidate and
raised four findings. All four were confirmed by independent
recomputation, and all four are now closed:

```
HIGH    implementation preceded governance approval
        RESOLVED - Aaron ratified ND1_RECOMMENDED_PROFILE_R2 on 2026-08-23,
        so the P3 transitions the code implements are now covered verbatim
        by an in-force profile (ops/ND1_PROFILE_RATIFICATION.md section 8)
MEDIUM  scope digest did not match the runtime encoding
        RESOLVED - this file now calls the runtime's own
        serialize.scope_content_digest; the previous b38505fb... came from a
        format I invented instead of reading
LOW     three unswept `$` anchors in day_strata_supplement.py
        RESOLVED - the earlier round swept two modules and CLAIMED the
        class, which was false; a cross-module guard now covers all six
LOW     Python version contract left latent
        RESOLVED - .python-version = 3.13, and the battery asserts >= 3.13
```

**N06 itself has NOT passed.** A ratified profile is not an acceptance, and
this candidate has moved since the review, so the formal N06 must be redone
by a DIFFERENT fresh Sol session against the new HEAD.

## 1. Why this is not a Review Packet v1

L6 Runtime went **OPERATIONAL on 2026-08-23** (OD-OPERATIONAL). The N03/N04/
N05 build and this N06 repair round were carried out **before that record was
read by this session**, under the manual discipline, and were never brought
under the runtime. Three things are consequently missing, and none of them is
mine to supply:

```
QROS_STATE_FILE=ABSENT            (no qros-state.yaml anywhere in the workspace)
PROJECTS_YAML_ENTRY=ABSENT        (projects: [] — CLI reads it, never writes it)
LANE / STAGE                      DECLARED fields; spec §2.4: "Never inferred"
```

`qros packet` therefore renders **nothing** for this project today, which is
the specified behaviour and not a fault: a Review Packet v1 exists or it does
not (§5.1), and there is no partial one.

## 2. The gate question Aaron must settle first

Which gate this review is decides whether a packet is even generable:

| Reading | scope_kind | Minimum base (§5.2.1) | Generable today? |
|---|---|---|---|
| **Stage I** (FULL lane) | `STAGE_I_SEAL_TO_HEAD` | `seal_revision` → HEAD **in full, including the required A2 record** | **NO** — see §3 |
| **Discretionary Tier-1** | `TIER1_BATCH` | no canonical minimum; a chosen phase boundary, pinned by `scope_content_digest` | **YES**, once LANE/STAGE are declared |

The routing headers of this work said `LANE=MEASUREMENT`, whose chain is
`C→D→E→F→L` — **it contains no Stage I at all**. That points at the Tier-1
reading, but a prompt header is not a state declaration, and the ITSF S0 study
itself is a sealed preregistered study. **This is a material research choice
and it is Aaron's.**

## 3. Under the Stage I reading, generation must STOP

Stage I's minimum base requires the A2 record. Measured:

```
runs/ DIRECTORY                 ABSENT
runs/*stage-a2* RECORDS         0 found
MATERIAL_DESIGN_CONTRIBUTOR     UNKNOWN
INDEPENDENCE_UNKNOWN            YES
```

Per §5.2.1 an unresolvable Tier-2 base means
`PACKET_GENERATION_RESULT=REJECTED_INCOMPLETE`, **no** REQUIRED SAVE PATH,
**no** `PACKET_ISSUANCE`, and the gate's transition is held. This document
does not work around that; it reports it.

## 4. Fields that ARE mechanically resolvable

```
HEAD                          MECH      5f094cbfd7b54eeb7091e345af10331094e9d4d3
BASIS                         MECH      HEAD
WORKTREE                      MECH      CLEAN
SCOPE_BASE                    SELECTED  617f7c33d20051fd991d74afa7c76716720e385d
SCOPE_BASE_ORIGIN             MECH      selected  <selector: builder>
SCOPE_CONTENT_DIGEST          MECH      517c2ef22e299f794058f59640c9bc3b0a1c7a569e632ccef9759880bb2779f1
PREREG_REF                    CANON     STUDY_0_PREREGISTRATION.md
PREREG_SHA256                 MECH      6cca20b7b1ce496d582ef5b4677333ba1b74bc577020ab29df00ff0c0d1af132
SEAL_REVISION                 MECH      c685ebc1ed65e0c6fc9b9b7212a054289d1b37fd  (tag s0-freeze-v1)
SEAL                          MECH      VERIFIED
LINEAGE_ANCHOR                DECLARED  ### 修订记录
TRIAL_ACCOUNTING_REF          CANON     ops/TRIAL_REGISTRY.md
TRIAL_ACCOUNTING_RESOLUTION   MECH      sha256 ee9da33fdbb47725dc036243adc76d7d9ba69ff06df0df443b09103f897353d6
OUTCOME_EXPOSURE_DECLARED     BUILDER   NONE   (this round read no outcome value)
OUTCOME_EXPOSURE_CANONICAL    CANON     EXPOSURE_LEDGER.md sha256 382182bf8563a8e466115bf3024e3c1e1bd2f4b9f102d24d755e91c4174ba7ba
                                        cumulative researcher exposure unchanged at 1575
EXPOSURE_CONFLICT             MECH      NO
S0_ATTESTATION                MECH      sha256 d839b965a35e749f0a9052cc3fb85f9b4032ed5d412043f36ac3349779941805
```

### 4.1 FILE_MANIFEST over the selected base (26 paths)

| path | sha256 @ HEAD | status |
|---|---|---|
| `.python-version` | `02e735b3dfe1c328…` | A |
| `ops/DECISION_PACKET_N00_AND_ND1.md` | `da64a3d68454e6f1…` | M |
| `ops/MC_DR5_BUILD_PACKET.md` | `24ddac668ade881e…` | M |
| `ops/MC_TO_STRATEGY_MASTER_PLAN.md` | `af68429093da40ae…` | M |
| `ops/N06_HOLD_RED_PROOF.md` | `22ad0408bec397d6…` | A |
| `ops/N06_HOLD_REPAIR_EVIDENCE.md` | `6b12ca2a1868f2a6…` | A |
| `ops/N06_REVIEW_HANDOFF.md` | `271c6036bb2d2c34…` | A |
| `ops/N06_ROUND2_HOLD_REPAIR_EVIDENCE.md` | `28ab25041bf0b20c…` | A |
| `ops/N06_ROUND2_SOL_PROMPT.md` | `98ca22f114de79de…` | A |
| `ops/ND1_PROFILE_RATIFICATION.md` | `cf2c3cb2bdb79b34…` | M |
| `scripts/s0_real_run.py` | `2ce3787ecd1afd4c…` | M |
| `src/itsf/mc/day_strata_supplement.py` | `069659902e50abc3…` | M |
| `src/itsf/mc/supplement_authority.py` | `2db52ac1f716c07e…` | M |
| `src/itsf/mc/supplement_contract.py` | `c51d25e58545f7c4…` | M |
| `src/itsf/mc/supplement_production.py` | `b94466ac6360a1b2…` | A |
| `src/itsf/mc/supplement_registry.py` | `c1628b51d94a5475…` | M |
| `src/itsf/mc/supplement_runner.py` | `dca137e6fa2217cc…` | M |
| `tests/test_mc_day_strata_supplement.py` | `ece6593aa21cf132…` | M |
| `tests/test_mc_supplement_authority.py` | `6f08afee5a017a11…` | M |
| `tests/test_mc_supplement_integration.py` | `f6b0ff3bd0280f81…` | M |
| `tests/test_mc_supplement_paths_battery.py` | `820e06b2c398ecb5…` | A |
| `tests/test_mc_supplement_provenance_battery.py` | `89ffbf9ddc6cc3dd…` | A |
| `tests/test_mc_supplement_registry.py` | `f950bae560963cb2…` | M |
| `tests/test_mc_supplement_runner.py` | `3dc719db3f34e8a6…` | M |
| `tests/test_nd1_profile_r2.py` | `1c8a47832d3a33fc…` | A |
| `tests/test_s0_runner.py` | `1dd541d01988af83…` | M |

`SCOPE_CONTENT_DIGEST` above is taken over the ordered `(path, sha256)` pairs
of exactly this manifest, serialized UTF-8/LF, lowercase hex, one pair per
line — §5.2.1a's rule, so it pins **the content the reviewer is shown** and
nothing else.

## 5. LINEAGE_AMENDMENTS — verbatim at the declared anchor

> Mandatory at Stage I. The anchor is `### 修订记录`, which is exactly the
> heading-divergence case the spec's §5.2.3 design-time observation records
> for this workspace.

```
### 修订记录
**v0.1 → v0.2**（GPT 评审，7 项全采纳）：Oracle 方向修复（d_open）；四数据角色＋隔离；IV 预算 1；
E1/E2 双判据＋E3 删除；MVE 函数化；ADR14；成交公式化；整数仓位输出；bootstrap 规格；两阶段冻结。
**v0.2 → v0.3**（GPT 终审 3 项＋Claude 补丁 2 项）：
1. 判定表去标量化 —— 直接以 MC net_business_EV 裁决；MVE 降级为诊断工具；新增封存顺序（MC_METHOD_SPEC 先于 S0 结果）。
2. 附录 A 改为 D_TP/D_FP 经验分布混合法；−1R 近似降级为 sanity check。
3. F3/F8/Y2 公式唯一化（close-path 版本）；成本公式补 spread/2、Stress 范围、signed-d、gap 穿越 trigger_ref；风险输出分 planned/realized。
4. [Claude 补丁] GO 条件要求 Conservative 与 Stress 由**同一组合**满足，防止拼凑通过。
5. [Claude 补丁] E1 满足 EV 但可行性未过 → 归入边界区 β，避免判定表出现未定义单元格。

**v0.5 → v0.6**（GPT 第四轮终审，全部核查成立、全部采纳）：
1. 判定表改为互斥且穷尽：优先顺序 STOP → GO → β → α，α 成为兜底类别
   （修复"E1 P95>0 但中位数≤0、E2 全负"等未定义单元格）。
2. 附录 A 拆分 `positive_EV_region` 与 `deployable_region`，仅后者支持进入 H1
   （消除附录判据弱于主门槛的不一致）。
3. MNQ 边界精确为 2019-05-06（CME 官方上市日），两时代轴给出精确排他边界。
4. 强制报告 target/realized precision–recall，MC 使用 realized 值。
5. §12 补 Registry Commit B 的 blob 哈希计算要求与机械检查清单。

**v0.4 → v0.5**（GPT 第三轮终审 5 项，全部核查成立、全部采纳）：
1. 交接路径双数组化：`mtm_close_pnl_1m[]` ＋ `mtm_adverse_pnl_1m[]`（多头 minute_low／空头 minute_high）；
   实时判违规平台用 adverse-path；分钟内顺序不明取对账户更不利者或标记 ambiguous 双场景；
   stop 触发 bar 的 adverse 标记截断于 stop 成交价。
2. 边界区强制判决改用与主门槛完全相同的判据（禁止降门槛——证据不足＋额外自由度后门槛只能持平）。
3. Commit A 范围统一为 .gitattributes ＋ 三份冻结文件；封存顺序修正为
   S0/采购计划 → Gate 1 快照 → 引用快照 hash 的 MC_METHOD_SPEC → 运行。
4. "保守下界"更正为"幅度中性基准，不构成乐观或保守界"；网格步长、n_tp/n_fp 取整、
   分层不足处理规则冻结。
5. 新增反事实 Micro 执行披露：2010→2019-05 为 counterfactual_micro_execution，
   与 actual_micro_available_era 强制分列。
   另：Lucid 开放项改为官方文本歧义框架（快照＋书面回答，Level 2 证据），不再引用第三方冲突。

**v0.3 → v0.4**（GPT 第二轮终审 2 项＋Claude 修正 1 项＋抽样规则）：
1. [GPT，采纳] MC 交接单位改为每 1 手 MNQ 的日内 1 分钟 P&L 路径（Topstep 实时判违规已官方证实）；
   S0 与 MC 的仓位逻辑解耦（预算档降为描述性）；新增 Lucid 盘中/日终判违规开放核实项。
2. [GPT，采纳＋修正] 判定加入分位数门槛，但统计量修正为**认知层**（估计均值 EV 的 bootstrap 分布）——
   GPT 原表述若作用于单次尝试结果分布，挑战费二元损失会使 P5 恒负、GO 永不触发；
   结果层分布单独报告用于 bankroll 规划。新增边界区强制判决的冻结判据与四级 EV 台账。
3. [GPT，采纳] 附录 A 冻结 TP/FP 分层均匀随机选日规则＋幅度中性声明＋网格地位限定。
```

## 6. BUILDER-SUPPLIED section

```
CLAIM_BEING_EVALUATED
  The supplement machinery's four repaired seams hold under adversarial
  attack, and no production path can seal a supplement that the ten-check
  battery did not produce.

KNOWN_FAILURES
  None outstanding in the suite. Eight disclosed residuals stand, listed in
  ops/N06_HOLD_REPAIR_EVIDENCE.md §3.

KNOWN_ASSUMPTIONS
  - RETRACTED at round 3, and it was mine. This line used to read "the
    boundary that holds is RE-DERIVATION, not the capability object".
    Round 2 refuted it (re-derivation only holds when the bytes derived
    from and the bytes used are one snapshot) and round 3 showed the
    consequence: a str subclass whose __eq__ always returns True passes
    the re-derived digest comparison while JSON writes its real value.
    The framing was also wrong in a second way -- the attack needs only
    PUBLIC __new__ and object.__setattr__, so module privacy was never
    the question. F1/F2 is NOT a benign residual: composed with the
    scalar-freeze defect it produces a real sealed-byte violation.
  - R1's §D.3.2 P3 contract contradicts its own state diagram twice; the code
    implements the diagram reading, which NO ratified profile covers
    verbatim until ND1_RECOMMENDED_PROFILE_R2 is ratified.

UNRESOLVED_UNCERTAINTIES
  - Whether this review is Stage I or a discretionary Tier-1 review (§2).
  - Whether the ITSF project's LANE/STAGE declarations bring it under the
    L6 runtime at all, and with what values.
  - Whether the absent Stage A2 record for the S0 seal is a gap to be
    filled or a deliberate historical fact.
```

## 7. What Aaron must supply before a conformant packet can exist

```
1. LANE and STAGE declarations for this project (spec §2.4 — never inferred)
2. A qros-state.yaml at the ITSF repo root, per spec §2.4's schema
3. The gate decision of §2 above (Stage I vs discretionary Tier-1)
4. If Stage I: a resolution for the absent runs/ A2 record, or an explicit
   record that none exists for this seal
5. Optionally a projects.yaml entry; --state can point at the file instead
```

Only then does `qros packet` render, and only then is there a
`PACKET_ISSUANCE` to record.
