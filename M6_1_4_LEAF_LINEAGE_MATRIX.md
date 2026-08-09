# M6_1_4_LEAF_LINEAGE_MATRIX — 叶粒度血统矩阵（M6.1.4-R2 / S2）

> # ⚠ 状态：`PROVISIONAL / REJECTED AS TRUTH SOURCE`
> （M6.1.6 / S3 治理更正轮落标，2026-08-09）
>
> **本文件保留为历史设计材料，不得作为源码事实的引用来源。**
>
> **被拒的范围（具名，不含糊）**：
> - **§1 散文**——其「121 行中有 10 行在任何粒度上都没有独立权威」的措辞，
>   蕴含「其余 111 行在每个粒度上都有权威」，**已被 M6.1.4-R2 复核员 R2
>   实测证伪**（`EV-9.level_dates` 的元素、`EV-1.y_cont` 的值、
>   `TOP.record_fields` 的子键都没有，且三者均为 `INDEPENDENT_BOUND` 无标记）。
>   见 `CODEX_REVIEW_PACKET_M6_1_4.md` §10.4 第 4 条。
> - **§4 机制散文**——其描述的 `LeafSpec.marker_reason`、第四类残差
>   `wrong_axis`、逐标签叶 id（`EV-11.available.y1`）、写入口 `_emit_leaf`
>   在代码中**均不存在**。见同上 §10.4 第 6 条。
> - **`authority` 列**（§4.1 的 `LeafSpec.authority` 字段与 §5 各族表的
>   「独立原子来源」列）——§9 的机器可读块**只有 6 列且不含 authority**，
>   故该列**两个方向都没有被测试钉住**；已实测到至少一条为假
>   （`LEAF_REGISTRY["EV-1.y_cont_available"].authority` 所称的比较**不存在**）。
>   见同上 §10.4 第 5 条与 §10.5 第 3 条。
>
> **本文件并非惰性文件（必须一并披露）**：`tests/test_s0_evidence.py:2372`
> 将本文件路径钉为 `_MATRIX_PATH`，解析 **§9** 的机器可读围栏块
> （6 列 × 121 行）并与 `evidence.LEAF_REGISTRY` **双向**比对
> （`test_leaf_registry_matches_the_lineage_matrix_document` 与
> `test_the_matrix_declares_exactly_121_leaf_rows`）。
> **§9 因此是活的测试期望来源，本轮一个字节未改；被拒的是上列散文与列，
> 不是 §9。**
>
> **⚠ 编辑本文件者注意（M6.1.6 实测）**：该解析器以
> `text.index(_FENCE)` 取**第一处**围栏标记。因此在 §9 **之前**的任何
> 位置写出该标记的字面量（哪怕只是在散文里引用它），都会把解析窗口挪到
> 错误位置并使上述两个测试同时变红。引用它时请**只用文字描述**，
> 不要写出标记本身。

> 本文件是 `src/itsf/s0/evidence.py::LEAF_REGISTRY` 的**独立维护的预期表**。
> `tests/test_s0_evidence.py` 从本文件 §9 的机器可读表**解析**测试期望，
> 再与实现的注册表双向比对；期望**绝不**由实现自身的 dataclass 反射生成。
> 反射只用于一件事：断言注册表**覆盖**了每一个被捕获的 dataclass 字段。

**残留（如实记录，不得掩盖）**：registry↔matrix 被测试钉死，matrix↔truth **没有**。
本文件是手工维护的裁决记录，它自己可能相对研究现实漂移。

---

## 1. 本轮闭合的是什么，不是什么

F-2 的复发形态是：`CheckSpec.field` 指向**顶层字段**，`applicable` 数元素，
`compared_count` 数被消费的元素，**叶粒度没有注册表、没有完备性判据、没有披露**。

本轮把注册表与完备性判据下沉到叶粒度。**Token 完备性证明检查
"访问过"每一个叶，它不证明该叶的取值有独立权威。** 121 行中有 10 行
在任何粒度上都没有独立权威，它们被登记为 `DISCLOSURE_UNVERIFIED` 并各自
带一条指名到叶路径的 PARTIAL。

**任何把本轮读作"每个被捕获的叶现在都已被验证"的表述都是错的。**

---

## 2. 实测基线（方法陈述在前）

两轮只读探针，跑在 `tests/test_s0_evidence.py::_real_pieces` 的**密闭合成夹具**
（46 天 / 32 可构造日 / 8 封存单元）上，驱动真实的
`reconcile_with_evidence` / `reconcile_outcomes`。改造前基线：`hard=0, partial=12`。

**探针 A —— 对全部 107 个被捕获 dataclass 叶逐个做"全元素单叶变异"**：
**54 项 SILENT**（输出与诚实基线逐字节相同）。

这与 packet 的 "50" **不是同一个度量**，不作转述：

* 本表包含**被读取但未被完备性约束**的叶：`EV-7.seeds → ()` 静默（改成
  非空错误 seed 反而会被抓）、`EV-6.n_tp_available`/`n_fp_available`
  （检查读的是**载荷**的副本，从不读 pool 的）、`EV-7.n`
  （`_compare_series_block` 用 `study._series_block` 自己的 `n`）、
  `EV-5.year`（`evidence.py:3117-3120` 的裸 `except` 吞掉损坏，
  **静默停用 CR-4 跨约定交叉检查**）。
* 54 项中有 2 项是**夹具伪影**而非空洞：`EV-13.observed`
  （夹具本就未提供观测）、`EV-10.raw_categories`（合成日全部是 `none`）。
* 净额：**52 个实测未消费叶**，外加 **6 个字段粒度不可见的 Mapping 级空洞**。

**探针 B —— 动态 Mapping 与保值攻击（此前未度量）**：

| 攻击（作用于全部元素） | 结果 |
|---|---|
| `EV-11.available` 每天删除一个必需键（`y1` / `y_cont` / `y4_mfe`） | **SILENT** —— hard=0, partial=12, 完全相同 |
| `EV-11.available` **保持总量的成对交换**（同一标签 A 日 True→False，B 日 False→True） | **SILENT**（新发现） |
| `EV-6.tp_pools` 内容→常量日期，**计数保持不变** | **SILENT**（比复核员的"清空"更细） |
| `EV-9.exclusion_reason` 整体替换 | **SILENT** |
| `record_pnl` 每个单元**多出**一个被捕获日期 | **SILENT**（键集检查是单向的） |
| `provenance` **多出**一个未注册键 | **SILENT**（注册表只迭代自己的键） |
| `EV-11.available` 只删**一天**的键 | CAUGHT（`evidence_label_anchor_mismatch:y1.unavailable_days:14!=13`） |
| `EV-11.available` 每天**增加**词表外键 | CAUGHT（2 hard） |
| `EV-11` 五个布尔在 46 天上**全部翻转** | **SILENT** —— 复核员第 1 项在 reconcile 层复现 |
| `EV-11.trade_date` → 常量 | CAUGHT（47 hard） |
| `EV-13.observed` 伪造一条路径 | CAUGHT（精确键集检查） |
| `EV-5.tp_fp_class` 每天删除一个 theta 键 | CAUGHT（循环迭代 `evidence.thetas`，不迭代该 Mapping） |
| `record_fields` 多出一个日期 | CAUGHT（精确日期集检查） |

### 2.1 对指派主张的判定

**已证实，且比原表述更锋利。** 在每一行的 `available` 中删除同一个必需标签键，
在 reconcile 层与诚实运行逐字节相同：`_reconcile_ev11_coverage` 只判
`isinstance(available, Mapping) and available`（非空），
`_reconcile_label_availability` 按**存在什么键就迭代什么键**构造 `counts`，
再 `for label in sorted(counts)` 比对 —— 在**每一行**都缺席的键从不进入 `counts`，
因此从不与 `declared` 比对。两个 EV-11 检查都报 `(46, 46, complete)`，
专属 PARTIAL 因而被丢弃。

该攻击是**不对称**的：**多余**的键因 `_get(declared, "y99_fake", ...)` 为 `None`
而被偶然抓住，**缺失**的键不会；且必须在所有日子上一致（只删一天会被总量抓住）。

**超出该主张的新发现：每日取值同样未被绑定。** 保持总量的成对交换是静默的。
被绑定的只有六个按标签的总量。

**范围限定，如实说明**：这些是**合成夹具上的 reconcile 层**度量，严格弱于复核的
11 个渲染器级变体。§9 的暴露测试把两个头条主张
（键删除、保总量成对交换）提升到**真实 `render_s0_report`** 边界。

---

## 3. EV-11 研究语义围栏 —— 裁定与引证

**归约器存在，但不在围栏承认的来源里。**

**(a) `src/itsf/s0/dataset.py:688-695`** —— 仓库中唯一完整的六标签关系：

```
        ok = {
            "y_cont": o1000 and c1544 and adr_ok and dir_ok,
            "y1": o1000 and c1544 and adr_ok,
            "y2_de_pm": o1000 and c1544 and pm_ok,
            "y3_close_pos_pm": c1544 and pm_ok,
            "y4_mfe": o1000 and pm_ok and adr_ok and dir_ok,
            "y5_mae": o1000 and pm_ok and adr_ok and dir_ok,
        }
```

`dataset.py` **不是冻结文件**：`src/itsf/guards.py:20-39` 只登记七条路径
（`PROJECT_CHARTER.md`、`STUDY_0_PREREGISTRATION.md`、`purchase_plan.yaml`、
`MC_METHOD_SPEC.md`、`gate1/platform_params.yaml`、`gate1/evidence_registry.yaml`、
`gate1/snapshots/2026-07-28/snapshot_manifest_v5.json`），**其中没有任何源码文件**。
故 (a) 不满足围栏。

**(b) `IMPLEMENTATION_RESOLUTIONS.md:71`（IR-23，`APPROVED_BY_AARON 2026-08-01`）**
—— 已批准，但**只做了部分枚举**：

> `每标签只按自身必要输入判可算：Y1{O1000,C1544,ADR14}、Y2{O1000,C1544,PM close path}、Y3{C1544,PM high,PM low}；… Y_cont/Y4/Y5 继续依赖方向`

| 标签 | IR-23 原文 | 代码 `ok` | 是否可用 |
|---|---|---|---|
| `y1` | `{O1000, C1544, ADR14}` | `o1000 and c1544 and adr_ok` | **是 —— 精确、已批准** |
| `y2_de_pm` | `{O1000, C1544, PM close path}` | `o1000 and c1544 and pm_ok` | 部分 —— "PM close path"→`pm_ok` 是**解读** |
| `y3_close_pos_pm` | `{C1544, PM high, PM low}` | `c1544 and pm_ok` | 部分 —— **两个**具名依赖被压成一个布尔 |
| `y_cont` | 仅"依赖方向" | `y1 ∧ dir_ok` | **无枚举** |
| `y4_mfe` / `y5_mae` | 仅"依赖方向" | `o1000 ∧ pm_ok ∧ adr_ok ∧ dir_ok` | **无枚举** |

> **【补正 —— M6.1.6 / S3，2026-08-09】不得把本节读作「preflight／EV-11
> 全然未获批准」。** 存在一条外部治理链，其授权对象是**用 preflight 的
> 结构性计数作为 expected 断言**：IR-22（`IMPLEMENTATION_RESOLUTIONS.md:70`，
> 已批准）明令 `context.py` 与 `s0_input_preflight.py` **同步修复同测试**；
> IR-26（同上 :123-，已批准，Aaron E5）收口于「全 66 断言 all_pass=True」；
> `ops/TRIAL_REGISTRY.md:33`（行 11）记录「Stage B 5/5 全过（含
> `preflight_assertions_match` 66/66）」。接线为
> `runinfra.translate_preflight_assertions` → `compare_preflight_assertions`
> → `scripts/s0_real_run.py:683` 的 `GateCheck`，其比较集**含**
> `label.<Y_cont|Y1..Y5>.{available,unavailable}` 共 12 键。
>
> **但这条链授权的是「用计数作比较」，不是把 reducer 冻结为研究语义**，
> 故本节 (a)(b) 的围栏裁定与 D1 上呈**不受影响，继续成立**。
>
> **同时披露一处 DOCUMENTATION-LAYER CONFLICT（本轮不自行解决）**：
> `S0_INPUT_PREFLIGHT.json` 的 `"approval"` 字段仍为
> `"AWAITING_AARON_APPROVAL"`（`S0_INPUT_PREFLIGHT_REPORT.md:5` 同），
> 而 `src/itsf/s0/dataset.py:667-668` 与 `src/itsf/s0/context.py:73`
> 两处 docstring 称其为 "approved"／"APPROVED"。
> 详见 `CODEX_REVIEW_PACKET_M6_1_6.md` §6.1／§6.3。

> **【更正 —— M6.1.6 / S3，2026-08-09】本段原文主张 `dataset._LABEL_DEPS`
> 与 `ok` 之间存在「内部矛盾／内容不同」。该主张为假，现予撤回。**
>
> 逐格复算（`_LABEL_DEPS` 四列 = O1000, C1544, ADR14, d_open）：
>
> | 标签 | `_LABEL_DEPS` | `ok` 在同四轴上 | 一致？ |
> |---|---|---|---|
> | `y_cont` | T T T T | T T T T | 是 |
> | `y1` | T T T F | T T T F | 是 |
> | `y2_de_pm` | T T F F | T T F F | 是 |
> | `y3_close_pos_pm` | F T F F | F T F F | 是 |
> | `y4_mfe` | T F T T | T F T T | 是 |
> | `y5_mae` | T F T T | T F T T | 是 |
>
> **六标签、四轴，全部一致**（含原文点名的 y4/y5：`ok` 确实丢掉 `c1544`，
> 而 `_LABEL_DEPS` 的 C1544 列**同样是 False**——两者在这一点上是**同意**的，
> 原文把「同意」误读成了「矛盾」）。唯一差别是 `ok` 另需 `pm_ok`，
> 而 `_LABEL_DEPS` **没有 PM 列**。
>
> **正确表述**：`_LABEL_DEPS` 是 `ok` 在五条依赖轴中**四条上的 PROJECTION**；
> 在该投影所表示的每一条轴上两者一致。**这不是矛盾，也不构成需要 Aaron
> 裁决的事项**；据此拟建的台账行 `NEW-LABELDEPS-CONFLICT` 已 **WITHDRAWN**
> （详见 `CODEX_REVIEW_PACKET_M6_1_6.md` §6.2）。
>
> **本更正不改变 §3 的裁定**：`y_cont`/`y4`/`y5` 的 reducer 仍无已批准枚举，
> 本节末的 fail-closed 处置与 D1 上呈**继续成立**。

原文（保留，供对照，**已知为假**）：`dataset._LABEL_DEPS`（`dataset.py:151-159`，
NA 归因表）给出 `y4/y5 = (O1000=True, C1544=False, ADR14=True, dir=True)`，
**完全没有 PM 列**；而 `ok` 要求 `pm_ok` 且丢掉 `c1544`。~~同一文件两张表，
内容不同，零交叉检查。~~

**裁定：本轮不可闭合。** 只有 `y1` 有明确的已批准归约器；
`y_cont`/`y4`/`y5` 一个都没有。**不自行推导。** 改为 fail-closed：
永久专属 `PARTIAL:structural.label_anchor_availability.per_day_values:`。
选项（冻结归约器 vs 接受永久 PARTIAL）作为 DECISION_REQUIRED 上呈 Aaron。

### 3.1 无需触碰研究语义即可闭合的部分（本轮实施）

1. **`available` 精确键集 × 实体集** —— 词表权威是
   `dataset.PRE_Y6_LABEL_NA_FIELDS`（`dataset.py:136-137`），一个独立于 EV-11 的
   冻结模块元组。闭合实测空洞。纯词表，无语义。
2. **`dir_ok`** —— `dataset.py:687` 定义 `dir_ok = (r.direction_status ==
   DIRECTION_DIRECTIONAL)`，`dataset.py:307-308`（`_direction_status`）给出
   `d_open != 0 → DIRECTION_DIRECTIONAL`，即 `dir_ok ⟺ EV-1.d_open != 0`。
   EV-1.d_open 已被绑定到封存 `direction` 与 `stability_views.by_direction`。
   **夹具上逐日验证为真。** 这是机械恒等式，不是被围栏的标签集归约器。
3. **`adr_ok` 总体总量** —— `Σ adr_ok == structural.na_table.per_field.
   features.adr14.not_na`。EV-8 经 `pandas.isna` 扫 `ds.features_table` 得到该计数；
   `adr_ok` 来自 `record.features.adr14 is not None`。**夹具上 32 == 32 验证通过。**
   仅总量级。
4. **蕴含轨**（单向、无研究语义）：`trade_constructible ⟹ pm_ok`
   （`evidence.py:655-658`）、`EV-2 覆盖 ⟹ o1000`（`entry_ref_price` 是有限的
   10:00 open）。

**保持开放并披露**：`o1000`/`c1544`/`pm_ok`/`adr_ok` 的逐日取值，
以及 `available[<label>]` 的每一个逐日取值。

---

## 4. Token 完备性机制（取代元素计数器）

```python
@dataclass(frozen=True)
class LeafSpec:
    family: str            # "EV-11"
    leaf: str              # "o1000" 或路径模式 "available.<KEYSET>"
    disposition: str       # 六选一
    entity_axis: str       # ENTITY_AXES 的键 —— 绝不读取它所守卫的叶
    key_vocab_axis: str    # 非 Mapping 叶为 ""
    authority: str         # 独立来源（散文）
    marker_section: str    # 仅 DISCLOSURE_UNVERIFIED / DR_PARTIAL 非空
    marker_reason: str
```

* 每个叶检查发出**精确 token**：`("EV-11.o1000", "2020-01-02")`、
  `("EV-7.seeds", "theta_0.3|E1|Base|block5")`、
  `("EV-11.available.y1", "2020-01-02")`。用 `Counter`，不是 `set`。
* `_emit_leaf` 是 `leaf_tokens` 的**唯一写入者**（`_run_check` 纪律下沉一级）。
* `expected_tokens = {(leaf_id, e) for e in ENTITY_AXES[spec.entity_axis]}`，
  在任何叶被读取**之前**构造。
* **`CheckOutcome.complete` 改为 multiset 相等。** 四个独立具名残差：
  `missing`、`extra`、`duplicate`、`wrong_axis`。错日期落成同一叶上的
  `missing ∧ extra` 并如此报告。
* **`compared_count >= applicable` 作为完成判据被退役。**
  `applicable`/`compared_count` 保留为两个 multiset 的 `len()` 派生显示值，
  渲染方式与今天完全一致 —— packet §8 的六 seed 确定性证据以该三元组陈述，
  退役数字会白白摧毁比较基准。
* **动态 Mapping 规则**：Mapping 叶携带 `(key_vocab_axis, entity_axis)`，
  按 **`set(mapping) == VOCAB` 对每一个实体** 加 **实体集精确相等** 检查。
  叶检查中禁止 `for k in mapping:`，由静态测试强制。

### 4.1 ENTITY_AXES 与各自的非循环权威

| axis | 权威（绝不读取被守卫的叶） |
|---|---|
| `af1_days` | `EV-9.level_dates["L3_structurally_eligible_days"]` —— 夹具上**实测等于 46 个 EV-1 日期**（L4 是 32，不是 AF1 集）。S0Universe 原子。 |
| `af1_days`（无 universe 时） | **无权威** → 发 `PARTIAL:evidence.entity_axis.af1_days:`，**绝不**回落到用被守卫族自身定尺 |
| `sealed_dates` / `sealed_cells` / `sealed_rows` | 解析后的 `MC_HANDOFF_*.jsonl` 字节 |
| `constructible_days` | `EV-1.trade_constructible`（守卫 EV-3，绝不守卫 EV-1） |
| `constructible_days_long` / `_short` | 同上再按 `EV-1.d_open` 的符号过滤 |
| `tp_union` | `EV-1` × `study.FROZEN_THETAS`（守卫 EV-2） |
| `theta_eng_scn` / `boot_cells` / `axis_*` | 冻结模块常量 |
| `na_fields` | `dataset.FEATURE_NA_FIELDS + LABEL_NA_FIELDS`（18） |
| `label_vocab` | `dataset.PRE_Y6_LABEL_NA_FIELDS`（6） |
| `funnel_levels` | `evidence._FUNNEL_LEVELS`（6） |
| `excluded_days` | 由 EV-9 层级差 `(L0−L1) ∪ (L1−L2) ∪ (L2−L3)` 导出 |
| `f10_population` | `EV-9.L3`（无 universe 时同 `af1_days` 规则） |
| `record_field_names` | `report.FORMAL_RECORD_FIELDS`（19） |
| `provenance_keys` | `PROVENANCE_REGISTRY`（21） |
| `frozen_hash_paths` | **声明的** `governance.frozen_hashes` 键集 |
| `singleton` | 常量 1 |

**文件中已有的先例**（本机制是既有正确代码的推广，不是发明）：
`_reconcile_record_fields`（精确日期集 × 冻结字段元组，严格类型）、
`_reconcile_frozen_hashes`（精确键集，具名 missing/extra）、
`_reconcile_day_strata` 的 `tp_fp_class`（迭代 `evidence.thetas` 而非该 Mapping）。

---

## 5. 矩阵本体 —— 121 行

统一列被提到族标题；逐叶行携带其余列。
`applicability source` = 族的 entity axis（行内覆盖除外）。
`expected-token construction` 全程为 `{(leaf_id, e) : e ∈ ENTITY_AXES[entity_axis]}`。
状态：**B**=原已绑定，**S**=实测 SILENT，**N**=本轮新绑定，**†**=夹具伪影。

### EV-1 `CanonicalDayFact` — 实体键 `trade_date`；axis `af1_days`（46）；研究依赖：无

| leaf | disposition | 独立原子来源 | reducer | consumer/check | marker 后果 | 状态 |
|---|---|---|---|---|---|---|
| `trade_date` | INDEPENDENT_BOUND | `S0Universe.funnel.structurally_eligible` ＋解析字节 | identity | `EV-1.sealed_day_membership` ＋ `leaf.EV-1` | hard | B/N |
| `year` | INDEPENDENT_BOUND | `structural.groups.by_year`、`frequency` | `rebuild_frequency` | `EV-1.reducer_subtrees` | hard | B |
| `era` | INDEPENDENT_BOUND | `ctx.MICRO_ERA_BOUNDARY`、`structural.eras` | `_rederived_era` | `EV-1.reducer_subtrees` | hard | B |
| `record_year` | DERIVED_REDUNDANT | EV-1.`year` | `==` | `leaf.EV-1` | hard | **S** |
| `record_era` | DERIVED_REDUNDANT | EV-1.`era` | `==` | `leaf.EV-1` | hard | **S** |
| `d_open` | INDEPENDENT_BOUND | 封存 `direction`、`stability_views.by_direction` | `_reconcile_stability` | `EV-1.stability_views` | hard | B |
| `y_cont` | INDEPENDENT_BOUND | theta 划分→封存行；`disclosures.untradeable.y_cont` | `_partition_from_facts` | `EV-1.untradeable` | hard | B |
| `y_cont_available` | DERIVED_REDUNDANT | EV-1.`y_cont`；总量对 EV-8 `labels.y_cont.not_na` | `is not None` | `leaf.EV-1` | hard | **S** |
| `direction_status` | INDEPENDENT_BOUND | `dataset.py:307-308`（`≡ d_open != 0`）；总量对 `structural.na_table.direction` 三类 | 谓词＋Counter | `leaf.EV-1` | hard | **S**→N |
| `oracle_candidate` | INDEPENDENT_BOUND | `oracle_daily.day_universe`、`frequency` | `rebuild_day_universe` | `EV-1.reducer_subtrees` | hard | B |
| `record_oracle_candidate` | DERIVED_REDUNDANT | EV-1.`oracle_candidate`（`dataset.py:247`） | `==` | `leaf.EV-1` | hard | **S** |
| `tradeable_direction` | DERIVED_REDUNDANT | EV-1.`d_open`（`dataset.py:246`） | `== (d_open != 0)` | `leaf.EV-1` | hard | **S** |
| `trade_constructible` | INDEPENDENT_BOUND | 封存行总体、`frequency` | `rebuild_frequency` | `EV-1.reducer_subtrees` | hard | B |
| `untradeable_reason` | INDEPENDENT_BOUND | `disclosures.untradeable` ＋**新增**词表 `study.UNTRADEABLE_REASONS` | `_reconcile_untradeable` | hard | B/N |
| `is_event_day` | INDEPENDENT_BOUND | EV-10.`final_category` 逐日；`None` 计数对 EV-8 `features.is_event_day.na` | 按 `trade_date` join | `leaf.EV-1` | hard | **S**→N |

### EV-2 `TheoreticalPathRecord` — 实体键 `trade_date`；axis `tp_union`（16）；研究依赖：无（DR-8 只碰百分位块）

| leaf | disposition | 来源 / reducer | check | 状态 |
|---|---|---|---|---|
| `trade_date` | INDEPENDENT_BOUND | EV-1 × `FROZEN_THETAS` | `EV-2.tp_union_coverage` | B |
| `direction` | DERIVED_REDUNDANT | `== EV-1.d_open` | `leaf.EV-2` | **S** |
| `scenario_name` | INDEPENDENT_BOUND | `== study.BASE_SCENARIO_NAME` | `leaf.EV-2` | **S** |
| `entry_ref_price` | INDEPENDENT_BOUND | 封存 `entry_fill` 经 `costs.entry_fill` | `EV-2.entry_fill_binding` | B |
| `entry_fill` | DERIVED_REDUNDANT | `costs.scenario_entry_fill(entry_ref_price, d, Base)` | `leaf.EV-2` | **S** |
| `favourable_extreme_price` | DERIVED_REDUNDANT | 由 `exit_fill` 反解 `costs.scenario_timed_exit_fill` | `leaf.EV-2` | **S** |
| `favourable_extreme_ts` | DISCLOSURE_UNVERIFIED | bars 是进程内的；轨：ISO ts 落在 `trade_date` 的 `[ENTRY_TIME, FORCED_EXIT_BAR_TIME]` | `PARTIAL:theoretical_oracle.favourable_extreme_ts` | **S** |
| `exit_fill` | DERIVED_REDUNDANT | `entry_fill + (pnl + fee)/(d·MNQ_POINT_VALUE_USD)` | `leaf.EV-2` | **S** |
| `pnl_per_contract` | INDEPENDENT_BOUND | `theoretical_oracle` 子树 | `EV-1.reducer_subtrees` | B |
| `platform_fee_rt_usd` | DERIVED_REDUNDANT | `== EV-4["Base"].platform_fee_rt_usd` | `leaf.EV-2` | **S** |

### EV-3 `OpeningRangeFact` — 实体键 `trade_date`；axis `constructible_days`（32）；研究依赖：无

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `trade_date` | INDEPENDENT_BOUND | `EV-1.trade_constructible` | B |
| `or_high` **WHERE `d_open == -1`** | DERIVED_REDUNDANT | `== anchor_stop`（`study.py:225-228`） | **S** |
| `or_high` **WHERE `d_open == +1`** | DISCLOSURE_UNVERIFIED | 非锚一侧；轨 `or_high >= or_low` | **S** |
| `or_low` **WHERE `d_open == +1`** | DERIVED_REDUNDANT | `== anchor_stop` | **S** |
| `or_low` **WHERE `d_open == -1`** | DISCLOSURE_UNVERIFIED | 非锚一侧 | **S** |
| `n_obs_bars` | DISCLOSURE_UNVERIFIED | 无封存消费者；轨 `1 ≤ n ≤ |[OBS_LO, OBS_HI]|` | **S** |
| `anchor_stop` | INDEPENDENT_BOUND | 封存 `stop_level_points` / E1 `planned_stop` | B |
| `d_open` | DERIVED_REDUNDANT | `== EV-1.d_open` | **S** |

两条 DISCLOSURE_UNVERIFIED 行与 `n_obs_bars` 共用
`PARTIAL:sizing_outputs.opening_range_non_anchor_extreme:`。

### EV-4 `CostScenarioSnapshot` — 实体键 `name`；axis `axis_scenarios`（4）；研究依赖：**DR-1**

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `name` | INDEPENDENT_BOUND | `_SCENARIO_AXIS` | B |
| `spread_points` | INDEPENDENT_BOUND | 封存成交价＋`sizing_outputs.cost_usd_per_1_MNQ` | B |
| `slippage_ticks_per_side` | INDEPENDENT_BOUND | 同上 | B |
| `adverse_slippage_ticks` | INDEPENDENT_BOUND | 同上 | B |
| `friction_multiplier` | INDEPENDENT_BOUND | 同上 | B |
| `platform_fee_rt_usd` | INDEPENDENT_BOUND | 同上 | B |
| `spread_scalars` | INDEPENDENT_BOUND | `costs.build_scenarios(*spread_scalars)` 必须重建全部四个快照；四行之间必须一致 | **S**→N |
| `reduction_rule_id` | DR_PARTIAL | 词表＋`== UNRESOLVED_DR-M6-A-v2 ⟺ provenance["EV-4_dr1_status"] == "unresolved"`；沿用既有 `sizing_outputs.cost_layer` | **S** |
| `adverse_semantics` | DR_PARTIAL | 同上 | **S** |

### EV-5 `DayStratumFact` — 实体键 `trade_date`；axis `af1_days`（46）；研究依赖：**DR-2 + DR-6**

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `trade_date` | INDEPENDENT_BOUND | `af1_days` | B |
| `year` | DERIVED_REDUNDANT | `== EV-1.year`（今天 `int()` 失败被**吞掉**） | **S** |
| `micro_execution_era` | DERIVED_REDUNDANT | `== EV-1.era` | B |
| `stability_epoch` | INDEPENDENT_BOUND | CR-4：`dataset.STABILITY_EPOCHS` vs `stability._epoch_of` | B |
| `d_open` | DERIVED_REDUNDANT | `== EV-1.d_open` | **S** |
| `volatility_regime_label` | DR_PARTIAL | DR-2，链上无原子；轨 `vol_status == unresolved ⟹ == UNRESOLVED_DR-M6-B-v2`；沿用 `stability_views.vol_terciles` | **S** |
| `vol_status` | INDEPENDENT_BOUND | `== provenance["EV-5_dr2_status"]`，词表 `_DR_STATUS_VOCABULARY` | **S**→N |
| `event_flag_final` | DERIVED_REDUNDANT | `== EV-1.is_event_day or "NA_multi_event"` | **S** |
| `event_na` | DERIVED_REDUNDANT | `== (EV-1.is_event_day is None)` | **S** |
| `event_stratum` | DR_PARTIAL | DR-6；轨 `dr6_status == unresolved ⟹ == UNRESOLVED_DR-M6-F`；沿用 `day_strata` | **S** |
| `tp_fp_class[<theta_key>]`（×2） | INDEPENDENT_BOUND | EV-1 theta 划分；迭代 `evidence.thetas` | B |

### EV-6 `GridPoolFact` — 实体键 `(theta_key, engine, scenario)`；axis `theta_eng_scn`（16）；研究依赖：**DR-2 + DR-3 + DR-6**（仅层分配）

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `theta_key` | INDEPENDENT_BOUND | 冻结轴 | B |
| `engine` | INDEPENDENT_BOUND | 冻结轴 | B |
| `scenario` | INDEPENDENT_BOUND | 冻结轴 | B |
| `tp_pools.<UNION>` | INDEPENDENT_BOUND | `⋃ values == EV-1 TP 划分`，精确、无重复 | **S**→N |
| `fp_pools.<UNION>` | INDEPENDENT_BOUND | `⋃ values == EV-1 FP 划分` | **S**→N |
| `tp_pools[<stratum_key>]` | DR_PARTIAL | 分配需要 DR-2/DR-6 词表；沿用 `feasibility_grid.per_seed` | **S** |
| `fp_pools[<stratum_key>]` | DR_PARTIAL | 同上 | **S** |
| `tp_avail` | DERIVED_REDUNDANT | `== {k: len(v)}` of `tp_pools`；非负整数 | B/N |
| `fp_avail` | DERIVED_REDUNDANT | 同上 | B/N |
| `n_tp_available` | DERIVED_REDUNDANT | `== sum(tp_avail.values()) == |EV-1 TP|`（夹具验证） | **S** |
| `n_fp_available` | DERIVED_REDUNDANT | 同上 | **S** |
| `grid_stream_tag` | INDEPENDENT_BOUND | `== gridmix.GRID_STREAM_TAG`（活常量，CR-9） | **S**→N |
| `stratum_axes` | INDEPENDENT_BOUND | 内联字面量提升为模块常量 `GRID_STRATUM_AXES` 后精确绑定 | **S**→N |

### EV-7 `BootstrapInputFact` — 实体键 `cell_key`；axis `boot_cells`（32）；研究依赖：**DR-4** 只作用于重采样本身，不作用于以下任何叶

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `cell_key` | INDEPENDENT_BOUND | `theta×eng×scn×block` 乘积 | B |
| `theta_key` | DERIVED_REDUNDANT | `cell_key.split("\|")` | B |
| `engine` | DERIVED_REDUNDANT | 同上 | B |
| `scenario` | DERIVED_REDUNDANT | 同上 | B |
| `block_len` | INDEPENDENT_BOUND | `FROZEN_BLOCKS` | B |
| `n` | DERIVED_REDUNDANT | 重算有序序列的 `len` | **S** |
| `series_sha256` | INDEPENDENT_BOUND | 字节导出的 D_TP 上的 `_series_digest` | B |
| `series_mean_sum_over_n` | INDEPENDENT_BOUND | CR-2 三路 | B |
| `series_mean_numpy` | INDEPENDENT_BOUND | CR-2 三路 | B |
| `series_sum` | DERIVED_REDUNDANT | `== mean_sum_over_n · n`（夹具验证） | **S** |
| `first_date` | DERIVED_REDUNDANT | 重算序列首项；`None ⟺ n == 0` | **S** |
| `last_date` | DERIVED_REDUNDANT | 重算序列末项 | **S** |
| `seeds` | INDEPENDENT_BOUND | **精确元组** `== contracts.RESEARCH_BOOTSTRAP_SEEDS`（今天 `()` 静默） | **S**→N |
| `stats_stream_tag` | INDEPENDENT_BOUND | `== stats.STATS_STREAM_TAG` | **S**→N |
| `block_stream_key` | INDEPENDENT_BOUND | `== stats.block_stream_key(block_len)` | **S**→N |
| `n_boot` | INDEPENDENT_BOUND | `== stats.N_BOOT` ＋ per-seed 载荷 | B/N |
| `ci_level` | INDEPENDENT_BOUND | `== stats.CI_LEVEL` | **S**→N |
| `percentile_method_id` | INDEPENDENT_BOUND | `== stats.PERCENTILE_METHOD == EV-12.stats_percentile_method` | **S**→N |

### EV-8 `NAObservationFact` — 实体键 `(table, column)`；axis `na_fields`（18）；研究依赖：CR-1 reason 级仍 PARTIAL

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `table` | INDEPENDENT_BOUND | 冻结 NA 字段表 | B |
| `column` | INDEPENDENT_BOUND | 冻结 NA 字段表 | B |
| `n_null` | INDEPENDENT_BOUND | `structural.na_table.per_field`；**新增** `n_null + n_not_null == population` | B/N |
| `n_not_null` | INDEPENDENT_BOUND | 同上 | B/N |
| `observation_method_id` | INDEPENDENT_BOUND | `== NA_OBSERVATION_METHOD_ID[table]`（新模块常量，披露词表） | **S**→N |

### EV-9 `FunnelFact`

| leaf | disposition | 实体轴 | 来源 / reducer | 状态 |
|---|---|---|---|---|
| `level_dates[<level>]` | INDEPENDENT_BOUND | `funnel_levels`（6） | 键集 `== _FUNNEL_LEVELS`；计数→全部十个 `funnel_counts` 键；**新增**轨：已排序、无重复、`L4⊆L3⊆L2⊆L1⊆L0` | B/N |
| `exclusion_reason[<date>]` | INDEPENDENT_BOUND | `excluded_days` | 键集 `== (L0−L1)∪(L1−L2)∪(L2−L3)`；取值由日期落在哪个差集决定；词表＝冻结 L44 三原因（`context.py:566-575`） | **S**→N |
| `provenance` | INDEPENDENT_BOUND | `singleton` | `PROVENANCE_REGISTRY["EV-9"]` 绑定 | B |

### EV-10 `F10MembershipFact` — 实体键 `trade_date`；axis `f10_population`（= EV-9 L3）；研究依赖：IR-12/18 词表

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `trade_date` | INDEPENDENT_BOUND | `== EV-9.L3` 精确集（今天互斥检查数元素、不按日身份归键 —— 复核员第 5 项） | **S**→N |
| `raw_categories` | DISCLOSURE_UNVERIFIED | 提供日历时总量绑定到 `f10_raw_membership_counts`；**逐日归属未验证**；词表已绑定 | **S**† |
| `final_category` | INDEPENDENT_BOUND | 逐日 `== EV-1.is_event_day`（或 `NA_multi_event`）**且**计数对 `structural.f10_counts` | B/N |
| `raw_provenance` | INDEPENDENT_BOUND | `PROVENANCE_REGISTRY["EV-10"]` | B |

`raw_categories` 的 marker：`PARTIAL:structural.f10_raw_membership.per_date:`。

### EV-11 `LabelAvailabilityFact` — 实体键 `trade_date`；axis `af1_days`（46）；研究依赖：**IR-23，仅部分枚举（见 §3）**

| leaf | disposition | 来源 / reducer | marker | 状态 |
|---|---|---|---|---|
| `trade_date` | INDEPENDENT_BOUND | `af1_days` | hard | B |
| `o1000` | DISCLOSURE_UNVERIFIED | 无；轨 `EV-2 覆盖 ⟹ True` | `structural.label_anchor_availability.dependency_booleans` | **S** |
| `c1544` | DISCLOSURE_UNVERIFIED | 无 | 同上 | **S** |
| `pm_ok` | DISCLOSURE_UNVERIFIED | 无；轨 `trade_constructible ⟹ True` | 同上 | **S** |
| `adr_ok` | DISCLOSURE_UNVERIFIED（逐日） | **总体总量硬绑定**：`Σ adr_ok == na_table…features.adr14.not_na` | 同上，文案指名残余粒度 | **S** |
| `dir_ok` | INDEPENDENT_BOUND | `⟺ EV-1.d_open != 0`（`dataset.py:307-308, 687`），逐日验证 | hard | **S**→N |
| `available.<KEYSET>` | INDEPENDENT_BOUND | **精确** `set(available) == dataset.PRE_Y6_LABEL_NA_FIELDS`，对**每一个**实体；且实体集精确 | hard | **S**→N |
| `available[<label>]`（6 × 46） | DISCLOSURE_UNVERIFIED | 按标签总量仍绑定到 `structural.label_anchor_availability`；归约器被围栏 | `structural.label_anchor_availability.per_day_values` | **S** |

### EV-12 `EstimatorIdentityFact` — axis `singleton`；研究依赖：**DR-8**（仅百分位取值）

| leaf | disposition | 来源 / reducer | 状态 |
|---|---|---|---|
| `study_percentile_method` | INDEPENDENT_BOUND | `study.PERCENTILE_METHOD` | B |
| `stability_percentile_method` | INDEPENDENT_BOUND | `stability.PERCENTILE_METHOD` | B |
| `stats_percentile_method` | INDEPENDENT_BOUND | `stats.PERCENTILE_METHOD` | B |
| `all_three_agree` | INDEPENDENT_BOUND | 由三个字符串重derive | B |
| `worst_day_estimator_ruling` | DERIVED_REDUNDANT | `None ⟺ estimator_status_expected == "unresolved_DR-M6-H"` | **S** |
| `estimator_status_expected` | INDEPENDENT_BOUND | `e2_worst_days.<t>.<scn>.estimator_status` | B |

### EV-13 `FrozenHashObservationFact`

| leaf | disposition | 实体轴 | 来源 / reducer | 状态 |
|---|---|---|---|---|
| `observed[<path>]` | INDEPENDENT_BOUND | `frozen_hash_paths` | 精确键集对声明集；未提供时该轴为空 → AUTHORITATIVE_NOT_APPLICABLE ＋既有 `governance.frozen_hashes` PARTIAL | B |
| `provenance` | INDEPENDENT_BOUND | `singleton` | `PROVENANCE_REGISTRY["EV-13"]` | B |

### 顶层 `CanonicalS0Evidence`

| leaf | disposition | 实体轴 | 来源 / reducer | 状态 |
|---|---|---|---|---|
| `schema_version` | INDEPENDENT_BOUND | `singleton` | 冻结常量 | B |
| `thetas` | INDEPENDENT_BOUND | `axis_thetas` | `study.FROZEN_THETAS` | B |
| `engines` | INDEPENDENT_BOUND | `axis_engines` | `study.ENGINES` | B |
| `scenarios` | INDEPENDENT_BOUND | `axis_scenarios` | `_SCENARIO_AXIS` | B |
| `eras` | INDEPENDENT_BOUND | `axis_eras` | `study.ERA_AXIS` | B |
| `blocks` | INDEPENDENT_BOUND | `axis_blocks` | `FROZEN_BLOCKS` | B |
| `record_pnl[<cell>][<date>]` | INDEPENDENT_BOUND | `sealed_cell_dates` | 封存 `final_pnl_per_contract`；**新增 extra 方向** | B/N |
| `record_fields[<cell>][<date>][<field>]` | INDEPENDENT_BOUND | `record_field_tokens` | 精确日期集 × `FORMAL_RECORD_FIELDS`，严格类型（先例） | B |
| `provenance[<key>]` | INDEPENDENT_BOUND | `provenance_keys` | `PROVENANCE_REGISTRY`；**新增 extra 方向** | B/N |

### 5.1 展开量（合成夹具形状：D=46, C=32, U=16, cells=16, boot=32, 封存 8×32）

EV-1 690 · EV-2 160 · EV-3 192＋96 · EV-4 36 · EV-5 506 · EV-6 176 ·
EV-7 576 · EV-8 90 · EV-9 6＋|excl|＋1 · EV-10 184 · EV-11 322＋92 ·
EV-12 6 · EV-13 1 · record_pnl 256 · record_fields 4,864 · provenance 21

**实测预期 token 总数 = 8,178，实际发出 = 8,178，121 行全部 complete**
（设计说明中的"≈8,900"是估算；此处为实测值，以实测为准）。

---

## 6. 处置统计（121 行）

| disposition | 行数 | 其中今天实测 SILENT |
|---|---:|---:|
| INDEPENDENT_BOUND | 75 | 17 |
| DERIVED_REDUNDANT | 30 | 30 |
| DISCLOSURE_UNVERIFIED | 10 | 10 |
| DR_PARTIAL | 6 | 6 |
| AUTHORITATIVE_NOT_APPLICABLE | 0 新增（EV-2/EV-3 族既有状态 ＋ EV-13 未提供状态） | — |
| REMOVE_UNUSED | 0（2 项提呈裁决，裁定为**不移除**） | — |

**净额：121 行中 63 行从静默转为"被绑定"或"被明确披露"。10 行仍未验证 ——
每一行都带一条指名自身路径的 marker，不是族级一揽子。**

**对 packet 措辞的一处更正（已被协调方接受并记录）**：复核员第 7-10 项曾被
部分解释为"落在永久标记 5/7/10/11 的诚实范围内"。该解释**过宽**。永久标记覆盖的是
**DR 门控的取值**（重采样、成本模型、出场价前像），它们从未覆盖
`seeds`、`stats_stream_tag`、`block_stream_key`、`ci_level`、
`percentile_method_id`、`series_sum`、`first_date`/`last_date`、`spread_scalars`
以及 EV-2 可重derive 的成交价 —— **17 个非 DR 叶在毫无 DR 借口的情况下搭了便车。**
本轮全部闭合。

---

## 7. 新增 marker 字符串与诚实运行计数变化

诚实运行的 `partial_coverage` 由 **12 条增至 17 条**。新增 5 条全部是
**既有披露列表中的新条目**，不是 schema 扩展。

| # | section | 触发 | 性质 |
|---|---|---|---|
| 1 | `theoretical_oracle.favourable_extreme_ts` | EV-2.`favourable_extreme_ts` | 永久 |
| 2 | `sizing_outputs.opening_range_non_anchor_extreme` | EV-3 非锚极值 ＋ `n_obs_bars` | 永久 |
| 3 | `structural.label_anchor_availability.dependency_booleans` | EV-11 `o1000`/`c1544`/`pm_ok`/`adr_ok` | 永久（DECISION_REQUIRED D1 未决前） |
| 4 | `structural.label_anchor_availability.per_day_values` | EV-11 `available[<label>]` 逐日取值 | 永久（同上） |
| 5 | `structural.f10_raw_membership.per_date` | EV-10.`raw_categories` 逐日归属 | 永久 |

另有 1 条**条件性**新 marker，诚实运行**不出现**（因夹具与生产都传入 universe）：

| # | section | 触发 |
|---|---|---|
| 6 | `evidence.entity_axis.af1_days` | 未提供 `universe=` 时；此时 `af1_days` 轴**无权威**，绝不回落到用被守卫族定尺 |

**`bf7628a4b42985fb` 不再是锚点。** 封存集 digest 变化是**本设计声明的、逐条枚举的
披露增长**，不是篡改。任何把 digest 变化读作篡改的解读，请对照本节的 5 条。

---

## 8. DECISION_REQUIRED（不自行裁决）

* **D1 —— EV-11 归约器（围栏）**。不可闭合，见 §3。呈 Aaron 二选一：
  (i) 冻结该归约器（新的已批准 IR，或把 `_LABEL_DEPS`/`ok` 纳入冻结工件）；
  (ii) 接受永久 `PARTIAL:structural.label_anchor_availability.per_day_values:`
  与 `…dependency_booleans:`。本轮按 (ii) fail-closed 实施。
* **D4 —— 机器可读的逐叶披露**（如 `partial_coverage.leaves`）需要冻结 schema
  扩展。**仅登记，不实施。**
* **D6 —— 单调轨 `y_cont is not None ⟹ available["y_cont"]`**：需要"锚存在是标签
  可算的必要条件"这一裁决。**不假定、不实施。**

已裁决并已实施：D2（digest 变化获批，见 §7）、D3（`af1_days` 有 universe 时以
`EV-9.L3` 为权威，无 universe 时发专属 PARTIAL 且不回落）、D5（`int(s.year)` 的裸
`except` 改为 hard）、REMOVE_UNUSED（本轮零移除；`n_obs_bars` 与
`favourable_extreme_ts` 保留为 DISCLOSURE_UNVERIFIED）。

---

## 9. 机器可读注册表（测试期望的唯一来源）

格式：`family<TAB>leaf<TAB>disposition<TAB>entity_axis<TAB>key_vocab_axis<TAB>marker_section`。
空列写 `-`。测试解析本块并与 `evidence.LEAF_REGISTRY` **双向**比对。

```leafregistry
EV-1	trade_date	INDEPENDENT_BOUND	af1_days	-	-
EV-1	year	INDEPENDENT_BOUND	af1_days	-	-
EV-1	era	INDEPENDENT_BOUND	af1_days	-	-
EV-1	record_year	DERIVED_REDUNDANT	af1_days	-	-
EV-1	record_era	DERIVED_REDUNDANT	af1_days	-	-
EV-1	d_open	INDEPENDENT_BOUND	af1_days	-	-
EV-1	y_cont	INDEPENDENT_BOUND	af1_days	-	-
EV-1	y_cont_available	DERIVED_REDUNDANT	af1_days	-	-
EV-1	direction_status	INDEPENDENT_BOUND	af1_days	-	-
EV-1	oracle_candidate	INDEPENDENT_BOUND	af1_days	-	-
EV-1	record_oracle_candidate	DERIVED_REDUNDANT	af1_days	-	-
EV-1	tradeable_direction	DERIVED_REDUNDANT	af1_days	-	-
EV-1	trade_constructible	INDEPENDENT_BOUND	af1_days	-	-
EV-1	untradeable_reason	INDEPENDENT_BOUND	af1_days	-	-
EV-1	is_event_day	INDEPENDENT_BOUND	af1_days	-	-
EV-2	trade_date	INDEPENDENT_BOUND	tp_union	-	-
EV-2	direction	DERIVED_REDUNDANT	tp_union	-	-
EV-2	scenario_name	INDEPENDENT_BOUND	tp_union	-	-
EV-2	entry_ref_price	INDEPENDENT_BOUND	tp_union	-	-
EV-2	entry_fill	DERIVED_REDUNDANT	tp_union	-	-
EV-2	favourable_extreme_price	DERIVED_REDUNDANT	tp_union	-	-
EV-2	favourable_extreme_ts	DISCLOSURE_UNVERIFIED	tp_union	-	theoretical_oracle.favourable_extreme_ts
EV-2	exit_fill	DERIVED_REDUNDANT	tp_union	-	-
EV-2	pnl_per_contract	INDEPENDENT_BOUND	tp_union	-	-
EV-2	platform_fee_rt_usd	DERIVED_REDUNDANT	tp_union	-	-
EV-3	trade_date	INDEPENDENT_BOUND	constructible_days	-	-
EV-3	or_high@short	DERIVED_REDUNDANT	constructible_days_short	-	-
EV-3	or_high@long	DISCLOSURE_UNVERIFIED	constructible_days_long	-	sizing_outputs.opening_range_non_anchor_extreme
EV-3	or_low@long	DERIVED_REDUNDANT	constructible_days_long	-	-
EV-3	or_low@short	DISCLOSURE_UNVERIFIED	constructible_days_short	-	sizing_outputs.opening_range_non_anchor_extreme
EV-3	n_obs_bars	DISCLOSURE_UNVERIFIED	constructible_days	-	sizing_outputs.opening_range_non_anchor_extreme
EV-3	anchor_stop	INDEPENDENT_BOUND	constructible_days	-	-
EV-3	d_open	DERIVED_REDUNDANT	constructible_days	-	-
EV-4	name	INDEPENDENT_BOUND	axis_scenarios	-	-
EV-4	spread_points	INDEPENDENT_BOUND	axis_scenarios	-	-
EV-4	slippage_ticks_per_side	INDEPENDENT_BOUND	axis_scenarios	-	-
EV-4	adverse_slippage_ticks	INDEPENDENT_BOUND	axis_scenarios	-	-
EV-4	friction_multiplier	INDEPENDENT_BOUND	axis_scenarios	-	-
EV-4	platform_fee_rt_usd	INDEPENDENT_BOUND	axis_scenarios	-	-
EV-4	spread_scalars	INDEPENDENT_BOUND	axis_scenarios	-	-
EV-4	reduction_rule_id	DR_PARTIAL	axis_scenarios	-	sizing_outputs.cost_layer
EV-4	adverse_semantics	DR_PARTIAL	axis_scenarios	-	sizing_outputs.cost_layer
EV-5	trade_date	INDEPENDENT_BOUND	af1_days	-	-
EV-5	year	DERIVED_REDUNDANT	af1_days	-	-
EV-5	micro_execution_era	DERIVED_REDUNDANT	af1_days	-	-
EV-5	stability_epoch	INDEPENDENT_BOUND	af1_days	-	-
EV-5	d_open	DERIVED_REDUNDANT	af1_days	-	-
EV-5	volatility_regime_label	DR_PARTIAL	af1_days	-	stability_views.vol_terciles
EV-5	vol_status	INDEPENDENT_BOUND	af1_days	-	-
EV-5	event_flag_final	DERIVED_REDUNDANT	af1_days	-	-
EV-5	event_na	DERIVED_REDUNDANT	af1_days	-	-
EV-5	event_stratum	DR_PARTIAL	af1_days	-	day_strata
EV-5	tp_fp_class	INDEPENDENT_BOUND	af1_days	theta_keys	-
EV-6	theta_key	INDEPENDENT_BOUND	theta_eng_scn	-	-
EV-6	engine	INDEPENDENT_BOUND	theta_eng_scn	-	-
EV-6	scenario	INDEPENDENT_BOUND	theta_eng_scn	-	-
EV-6	tp_pools.UNION	INDEPENDENT_BOUND	theta_eng_scn	-	-
EV-6	fp_pools.UNION	INDEPENDENT_BOUND	theta_eng_scn	-	-
EV-6	tp_pools.STRATUM	DR_PARTIAL	theta_eng_scn	-	feasibility_grid.per_seed
EV-6	fp_pools.STRATUM	DR_PARTIAL	theta_eng_scn	-	feasibility_grid.per_seed
EV-6	tp_avail	DERIVED_REDUNDANT	theta_eng_scn	-	-
EV-6	fp_avail	DERIVED_REDUNDANT	theta_eng_scn	-	-
EV-6	n_tp_available	DERIVED_REDUNDANT	theta_eng_scn	-	-
EV-6	n_fp_available	DERIVED_REDUNDANT	theta_eng_scn	-	-
EV-6	grid_stream_tag	INDEPENDENT_BOUND	theta_eng_scn	-	-
EV-6	stratum_axes	INDEPENDENT_BOUND	theta_eng_scn	-	-
EV-7	cell_key	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	theta_key	DERIVED_REDUNDANT	boot_cells	-	-
EV-7	engine	DERIVED_REDUNDANT	boot_cells	-	-
EV-7	scenario	DERIVED_REDUNDANT	boot_cells	-	-
EV-7	block_len	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	n	DERIVED_REDUNDANT	boot_cells	-	-
EV-7	series_sha256	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	series_mean_sum_over_n	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	series_mean_numpy	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	series_sum	DERIVED_REDUNDANT	boot_cells	-	-
EV-7	first_date	DERIVED_REDUNDANT	boot_cells	-	-
EV-7	last_date	DERIVED_REDUNDANT	boot_cells	-	-
EV-7	seeds	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	stats_stream_tag	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	block_stream_key	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	n_boot	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	ci_level	INDEPENDENT_BOUND	boot_cells	-	-
EV-7	percentile_method_id	INDEPENDENT_BOUND	boot_cells	-	-
EV-8	table	INDEPENDENT_BOUND	na_fields	-	-
EV-8	column	INDEPENDENT_BOUND	na_fields	-	-
EV-8	n_null	INDEPENDENT_BOUND	na_fields	-	-
EV-8	n_not_null	INDEPENDENT_BOUND	na_fields	-	-
EV-8	observation_method_id	INDEPENDENT_BOUND	na_fields	-	-
EV-9	level_dates	INDEPENDENT_BOUND	funnel_levels	-	-
EV-9	exclusion_reason	INDEPENDENT_BOUND	excluded_days	-	-
EV-9	provenance	INDEPENDENT_BOUND	singleton	-	-
EV-10	trade_date	INDEPENDENT_BOUND	f10_population	-	-
EV-10	raw_categories	DISCLOSURE_UNVERIFIED	f10_population	-	structural.f10_raw_membership.per_date
EV-10	final_category	INDEPENDENT_BOUND	f10_population	-	-
EV-10	raw_provenance	INDEPENDENT_BOUND	f10_population	-	-
EV-11	trade_date	INDEPENDENT_BOUND	af1_days	-	-
EV-11	o1000	DISCLOSURE_UNVERIFIED	af1_days	-	structural.label_anchor_availability.dependency_booleans
EV-11	c1544	DISCLOSURE_UNVERIFIED	af1_days	-	structural.label_anchor_availability.dependency_booleans
EV-11	pm_ok	DISCLOSURE_UNVERIFIED	af1_days	-	structural.label_anchor_availability.dependency_booleans
EV-11	adr_ok	DISCLOSURE_UNVERIFIED	af1_days	-	structural.label_anchor_availability.dependency_booleans
EV-11	dir_ok	INDEPENDENT_BOUND	af1_days	-	-
EV-11	available.KEYSET	INDEPENDENT_BOUND	af1_days	label_vocab	-
EV-11	available.VALUE	DISCLOSURE_UNVERIFIED	af1_days	label_vocab	structural.label_anchor_availability.per_day_values
EV-12	study_percentile_method	INDEPENDENT_BOUND	singleton	-	-
EV-12	stability_percentile_method	INDEPENDENT_BOUND	singleton	-	-
EV-12	stats_percentile_method	INDEPENDENT_BOUND	singleton	-	-
EV-12	all_three_agree	INDEPENDENT_BOUND	singleton	-	-
EV-12	worst_day_estimator_ruling	DERIVED_REDUNDANT	singleton	-	-
EV-12	estimator_status_expected	INDEPENDENT_BOUND	singleton	-	-
EV-13	observed	INDEPENDENT_BOUND	frozen_hash_paths	-	-
EV-13	provenance	INDEPENDENT_BOUND	singleton	-	-
TOP	schema_version	INDEPENDENT_BOUND	singleton	-	-
TOP	thetas	INDEPENDENT_BOUND	axis_thetas	-	-
TOP	engines	INDEPENDENT_BOUND	axis_engines	-	-
TOP	scenarios	INDEPENDENT_BOUND	axis_scenarios	-	-
TOP	eras	INDEPENDENT_BOUND	axis_eras	-	-
TOP	blocks	INDEPENDENT_BOUND	axis_blocks	-	-
TOP	record_pnl	INDEPENDENT_BOUND	sealed_cell_dates	-	-
TOP	record_fields	INDEPENDENT_BOUND	record_field_tokens	-	-
TOP	provenance	INDEPENDENT_BOUND	provenance_keys	-	-
```

### 9.1 dataclass 字段 → 注册行的映射（反射只用于覆盖断言）

`EV-3.or_high` 展开为 `or_high@short` / `or_high@long`；`EV-3.or_low` 同理；
`EV-6.tp_pools` 展开为 `tp_pools.UNION` / `tp_pools.STRATUM`，`fp_pools` 同理；
`EV-11.available` 展开为 `available.KEYSET` / `available.VALUE`。
除此之外每个 dataclass 字段恰好对应一行。107 个 dataclass 叶 ＋ 5 处拆分
＋ 6 条冻结轴 ＋ 3 个顶层 Mapping 模板 = **121 行**。

---

## 10. 实施相对设计说明的偏离（如实记录）

1. **`EntityAxisAuthority.reads` 改为叶精确，而非族精确。** 设计说明写的是
   "轴不得由它所守卫的**族**定尺"。实施时发现这是**过强且错误**的近似：
   `excluded_days` 由 `EV-9.level_dates` 构造、守卫 `EV-9.exclusion_reason`
   —— 同族不同叶，而 `level_dates` 本身已被十个 `funnel_counts` 键独立绑定。
   真正要害的不变式是"轴绝不读取它所守卫的**那个叶**"，测试按此强制。
2. **`funnel_levels` 与 `excluded_days` 与 `af1_days` 一同 fail-closed。**
   缩减捕获（无 universe）是合法且被披露的状态；若不一同跳过，
   `funnel` 字段的既有 DISCLOSURE 路径会被叶层错误地升级为 refusal。
3. **`compared_count >= applicable` 保留为"必要但不充分"的合取项。**
   设计说明写的是"退役"。完全删除会**丢掉一条真实披露**：诚实运行的
   `governance.frozen_hashes` PARTIAL 正是由该计数门驱动（EV-13 未提供观测时
   `compared=0 < applicable=7`）。因此：**判据之记录（criterion of record）是
   token multiset 相等**，计数比较仅作为不充分的合取项存活，且只在四条
   不拥有任何证据字段（因而不拥有任何叶）的字节轨上单独存活。
4. **两条设计说明里的测试攻击被更正为攻击真实不变式。** `EV-4` 的
   `reduction_rule_id` 与 `EV-12` 的 `worst_day_estimator_ruling` 的**取值**在
   reconcile 时没有独立权威（夹具是 `TEST_ONLY` 已裁决态），
   把它们改成另一个非空字符串本就**不可**被抓 —— 那是 DR_PARTIAL /
   DERIVED_REDUNDANT 的正确含义。测试改为攻击真正可判的 iff：
   `reduction_rule_id == UNRESOLVED ⟺ provenance["EV-4_dr1_status"] == unresolved`
   （双向各一例），以及 `ruling is None ⟺ estimator_status_expected ==
   "unresolved_DR-M6-H"`。
5. **既有测试的三处 `12` 计数钉与一处前缀断言被更新，属加强而非削弱**：
   `test_honest_run_marker_text_is_byte_stable`（12→17 并逐条列出 5 个新 section）、
   `test_an_internal_error_no_longer_empties_the_partial_list`（12→17）、
   `test_the_honest_fixture_seals_through_the_real_renderer`（12→17）、
   `test_high2_marker_is_gated_on_the_check_not_on_provenance`
   （`PARTIAL:structural.label_anchor_availability` → 加尾冒号的精确 section，
   否则两个新的永久叶级 section 会被前缀误伤）。
