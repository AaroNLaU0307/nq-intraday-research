# S0_REAL_RUN_AUTHORIZATION_PACKET

```
packet_approval_status:   PACKET_APPROVED          # registry 事件 3（Aaron, 2026-07-31）
draft_status_historical:  PENDING_AARON_APPROVAL   # 起草时标记，仅作历史记录
real_s0_authorization:    REAL_S0_NOT_AUTHORIZED   # 与上两行完全独立
drafted_at_utc: 2026-07-31
drafted_by: main agent (solo; no subagent, no workflow, no real data read)
```

**（M6.1.6 / S3，2026-08-09）词汇对齐**：第三行的值改用 **registry 的原文
词汇** `REAL_S0_NOT_AUTHORIZED`（`ops/TRIAL_REGISTRY.md:19`，事件 3 记
`real_s0 = REAL_S0_NOT_AUTHORIZED`）。**语义不变**，仅消除本包与 registry
之间的词汇分歧（原写 `NOT_AUTHORIZED`）。**registry 字节未改动。**

**三个状态字段的关系（2026-08-09 澄清，无行为改变）**：

- **本文件不是冻结件，可编辑。** `guards.FROZEN_HASHES` 仅 **7** 项
  （`PROJECT_CHARTER.md`、`STUDY_0_PREREGISTRATION.md`、`purchase_plan.yaml`、
  `MC_METHOD_SPEC.md`、`gate1/platform_params.yaml`、
  `gate1/evidence_registry.yaml`、`gate1/snapshots/2026-07-28/
  snapshot_manifest_v5.json`），**均不含本文件**；`FREEZE_LOG.md` 亦无本文件
  条目（只读代理 S3 于 2026-08-09 逐项复算确认）。append-only 约束属于
  `ops/TRIAL_REGISTRY.md`，**不属于本包**——故先前"保留旧头部是 append-only
  精神的延伸"这一理由不成立，已撤销，头部改为三个互相独立的具名字段。
- **`packet_approval_status: PACKET_APPROVED`**——以 registry 字节为准：
  治理框架已获 Aaron 批准（事件 3，"Approved for runner implementation only"）。
- **`draft_status_historical`**——纯历史标记，**不**表示治理框架仍待批准。
- **`real_s0_authorization: REAL_S0_NOT_AUTHORIZED`**——不受上述任何一项影响：
  `PACKET_APPROVED` 与 `RUN_AUTHORIZED` 是不同状态（见 §0）。当前 HEAD 无
  对应 READY；生产解析器 `resolve_authorizations` 对当前 registry 字节返回
  **0 条存活授权**、链无 problem（S3 实测）。

本包只授权**首次真实 S0**。批准本包 ≠ 运行授权；运行只能由 §10 的精确
授权语句触发。

## 0. Trial 治理状态机（Aaron 2026-07-31 修订批复）

```
PACKET_DRAFTED → PACKET_APPROVED → RUNNER_IMPLEMENTED
→ READY_FOR_RUN_AUTHORIZATION → RUN_AUTHORIZED → RUNNING
→ COMPLETED / FAILED
```

- 当前位置（**2026-08-09 现值**；状态机词汇对当前 HEAD 无单一命名态，
  如实分述）：registry 最新 READY = **行 11 @ `6cb7eb7…`（历史
  commit）**，其对当前 HEAD 的失效/挂起语义**待 Aaron 裁决**（Option
  A/B/C，见 DECISION_REQUIRED_READY_SUPERSESSION.md）；当前 HEAD 无
  对应 READY；现势 = **Codex HOLD（M6.1.3 裁定，未撤销）＋ Fable 自判
  `M6_1_4_R2_STATUS=HOLD`（未经 Codex 复审；F-1／F-2 均写未闭合）**
  **【时态更正 —— M6.1.6 / S3，2026-08-09】** 此处原写「两名独立复核员
  尚未开跑」，已过时并予更正：
  **(i) M6.1.4-R2 的两名复核员已开跑并交出判定——`R1_VERDICT=PASS`
  （附三条其后被证伪的声明）／`R2_VERDICT=FAIL`**（见
  `CODEX_REVIEW_PACKET_M6_1_4.md` §10）；
  **(ii) M6.1.6 的独立复核员亦已开跑并交出 `M6_1_6_REVIEW=PASS`**
  （四轴、6 Low、0 High/0 Medium、轴 4 research boundary 零发现；
  见 `CODEX_REVIEW_PACKET_M6_1_6.md` §3——**其中在唯一允许的修复轮内
  落地的两条 Low 未经独立复核员重新复核**）。
  **结论不变**：F-1 整体与 F-2 整体仍为 `PARTIAL`；
  **`real_s0` 仍为 `REAL_S0_NOT_AUTHORIZED`。**
  （治理框架获批于 registry 事件 3。M6 起完整生产链进入
  代码库但 **fail-closed**：`ResolvedS0Methods` **八个结构化方法字段**（DR-M6-A..H，含 M6.1.1
  新增 stability_population 与 M6.1.3 新增 worst_day_estimator）任一
  未裁 → StudyConfig 无法派生 → Stage B 拒绝。Codex 对 M6.1.3 候选
  `1e188b5…` 判 `M6_1_3_VERDICT=HOLD / REAL_RUN_READY=NO`（RC-1/RC-2
  列 ENGINEERING_REQUIRED，M6.1.4 工程修复进行中）；registry 最新
  READY（行 11）属历史 commit `6cb7eb7…`，当前 HEAD 无对应 READY——
  旧 READY 的 append-only 失效/挂起语义待 Aaron 裁决（见
  DECISION_REQUIRED_READY_SUPERSESSION.md）。DECISION_REQUIRED_M6_1
  全部裁决落地并经审计前，不追加 READY、不受理授权；真实运行仍需
  §10 语句）。

  **【HEAD／commit 距离／工作树事实 —— M6.1.7 / S3，2026-08-09 实测更新】**
  上文写于 M6.1.6 尚未入库时，其「当前 HEAD」指向 `1e188b5…`；
  **该指代现已过时**，在此更新（原文保留，不改写）：

  | 事实 | 现值（S3 对仓库实测） |
  |---|---|
  | 当前 `git HEAD` | **`185e47f7e95c5d0cca4b44257c5b32c99790ef83`**（M6.1.6 入库） |
  | 分支 | `master` |
  | `git rev-list --count 6cb7eb71..HEAD`（自 registry 行 11 READY 起的 commit 距离） | **8**（M6.1.6 期间为 7） |
  | 其中带码候选里程碑 | **6**（M6 / M6.1 / M6.1.1 / M6.1.2 / M6.1.3 / **M6.1.6**）；另两个为 registry 行 11 追加 commit 与 HANDOFF_TO_CODEX 独立 handoff commit |
  | 工作树 | **未提交**的 M6.1.7 改动，**M6.1.7 无任何 commit**。`git status --porcelain` **在本次测量时为 10 行 ＝ 9 modified ＋ 1 untracked**：3 个生产源（`scripts/s0_real_run.py`、`src/itsf/s0/runner.py`、`src/itsf/s0/output_proof.py`）＋ 3 份测试（`tests/test_s0_runner.py`、`tests/test_s0_output_proof.py`、`tests/test_m6_chain.py`）＋ 3 份治理文档（本文件、`CODEX_REVIEW_PACKET_M6_1_6.md`、`DECISION_REQUIRED_READY_SUPERSESSION.md`）＋ untracked 的 `CODEX_REVIEW_PACKET_M6_1_7.md`。**⚠ 该计数把本文件自己算在内**——本文件每被编辑一次它就已经是旧值；这是一个**带时刻限定的观测值，不是稳定事实**（复核员 L-8 指出前值 6 为自相矛盾） |
  | `git diff --check` | 净（exit 0） |
  | `ops/TRIAL_REGISTRY.md` sha256 | `de63b3d690c5c4be…b440`（＝基线，未修改；解析出 **13** 条事件） |
  | `EXPOSURE_LEDGER.md` sha256 | `394813431d879555…bc9e6`（＝基线，未修改） |
  | `runs/` | 不存在；S0-T001 未消耗 |

  **不变的结论**：**当前 HEAD 仍无对应 READY**（行 11 绑定
  `6cb7eb7…`，其间已前进 8 个 commit）；`resolve_authorizations` 对当前
  registry 字节仍返回 **0 条存活授权**；
  **`real_s0_authorization` 保持 `REAL_S0_NOT_AUTHORIZED`。**
  Codex 对 M6.1.3 的 `HOLD / REAL_RUN_READY=NO` 裁定**未被撤销**。
  M6.1.6 与 M6.1.7 均**未**追加任何 registry 事件。
  M6.1.7 闭合的四个对象及其复算数字见 `CODEX_REVIEW_PACKET_M6_1_7.md`；
  **其中 M6.1.6 宣布的两条 CLOSED 已被 M6.1.7 判为历史性临时并重新打开**
  （见该 packet §3 与 `CODEX_REVIEW_PACKET_M6_1_6.md` 顶部批注）——
  故上文 (ii) 所引的 `M6_1_6_REVIEW=PASS` **不得**被读作那两条接缝已终局闭合。

- `PACKET_APPROVED` 与 `RUN_AUTHORIZED` 是**不同状态**，前者绝不自动
  推进为后者；每次状态变化以事件追加进 ops/TRIAL_REGISTRY.md
  （UTC 时间＋commit＋actor＋原因），既有记录永不修改。
- **环境锁（M5-T5 首渲染；M6.1.4 起对部分行陆续重渲染——**逐行时效见下表**；
  authorized_commit 除外，见 §1 防自引用定案）**：

  **时效标注（S3 于 2026-08-09 对当前工作树字节逐行复算）**：

  **本表已按 M6.1.6 工作树重算（S3，2026-08-09）。M6.1.6 又改动了
  `scripts/s0_real_run.py` 与 `src/itsf/s0/runner.py`，并新增了一个
  生产源文件；下表的 `runner.py` 行与 `s0_real_run.py` 的现值随之更新。**

  | 行 | 状态 |
  |---|---|
  | `scripts/s0_real_run.py` | **`STALE_SNAPSHOT_NOT_VALID_FOR_CURRENT_WORKTREE`**（现值 `937c96bf6b15d26b…`；**M6.1.6 更新**，此前记为 `5ea7b7f11e84577c…`） |
  | `src/itsf/s0/runner.py` | **`STALE_SNAPSHOT_NOT_VALID_FOR_CURRENT_WORKTREE`（M6.1.6 新增失效行）**——锁内 `772790cd9572446a…`，现值 `0c1e5cbb9861f8da…`（M6.1.6 prepare 接缝）。**此行此前列在"其余 10 行一致"内，该归类现已为假** |
  | `src/itsf/contracts.py` | **`STALE_SNAPSHOT_NOT_VALID_FOR_CURRENT_WORKTREE`**（现值 `d72a9b05dbf481a4…`，M6.1.6 未再改动） |
  | `src/itsf/s0/evidence.py` | **`STALE_SNAPSHOT_NOT_VALID_FOR_CURRENT_WORKTREE`**（现值 `676fbcd1ae0ac2a9…`，M6.1.6 未再改动） |
  | 其余 **9** 行（runinfra / context / dataset / labels / features / report / stability / handoff / guards） | 与当前工作树字节**逐项一致**（S3 复算） |
  | `requirements_lock` | 与当前字节**一致**（`f87799f6d24d3788…`） |
  | **`src/itsf/s0/output_proof.py`** | **不在本环境锁内 —— 覆盖缺口。** M6.1.6 新增的**生产源**（治理输出证明，`scripts/s0_real_run.py:1091` 与 `:2328` 导入），现值 `1f045ed5fb75480a…`。本轮**不修改本锁的字段集**（属重渲染范围），仅在此如实登记 |

  ---

  **【M6.1.7 重渲染，S3，2026-08-09】上表整体已被 M6.1.7 工作树追过。**
  M6.1.6 已作为 commit `185e47f7e95c5d0cca4b44257c5b32c99790ef83` 入库，
  上表所述「工作树」即该 commit；M6.1.7 在其之上产生了**未提交**的改动。
  **下表是对当前工作树字节的逐行复算（S3 实测，非转录）**：

  | 行 | 锁内旧值（M6.1.6 重渲染值） | 当前工作树现值 | 状态 |
  |---|---|---|---|
  | `scripts/s0_real_run.py` | `937c96bf6b15d26b…` | **`131b0dd11422ca3d…`** | **已更新** |
  | `src/itsf/s0/runner.py` | `0c1e5cbb9861f8da…` | **`b44306f8f1202e80…`** | **已更新** |
  | `src/itsf/s0/output_proof.py` | `1f045ed5fb75480a…` | **`b43c05243bd9b886…`** | **已更新** |
  | 其余 **11** 行（runinfra / context / dataset / labels / features / contracts / report / stability / handoff / evidence / guards） | — | 与锁内值**逐位一致** | 未变 |
  | `requirements_lock` | `f87799f6d24d3788…` | 一致（全 hash 复算相同） | 未变 |
  | 两个 preflight 工件 | `9d6dd1c1…` / `ea287f85…` | 一致 | 未变 |

  **变的是哪三个字段、为什么变（逐条给出，不笼统）**：

  1. **`src/itsf/s0/runner.py`** —— Stage E 的写路径由
     `write_text(content, encoding="utf-8")`（Windows 文本模式，`\n`→`\r\n`）
     改为「**编码恰好一次**、以 `write_bytes` 原样落盘、同一 `bytes` 值入哈希链」；
     新增**必需**的写后验证接缝（未接线在曝光前即拒绝）；
     `if not prepared` 回退为 `if prepared is None`；
     `render_report` 改为两参 `(result, prepared)`；
     `INCIDENT_*.md` / `HALF_TRANSITION.md` 两处写入补 `newline="\n"`。
  2. **`src/itsf/s0/output_proof.py`** —— 发布判定改从**磁盘**取得：
     `sealed_artifacts=` 变为永远抛 `ProofRefused` 的毒丸，
     生产改传 `report_path=<run_dir>/S0_REPORT.json`，
     `GovernanceProof.actual_source` 被强制为 `"file"`；
     内存检查降级为 `screen_governance_draft`（返回不可当作验收的 `DraftScreen`）；
     新增封存集轴（逐条 `sha256`／`bytes` 对 `Path.read_bytes()` 比对，
     并要求声明集合恰等于运行目录实际内容）。
  3. **`scripts/s0_real_run.py`** —— 治理数据改从**曝光前授权快照**取得
     （prepared 对象携带该快照；`compute` 不再重读 registry；
     `_expected_governance(snapshot)` 从快照取 SEQUENCE、仍从实时 registry
     字节重读 authorized COMMIT 并要求两者一致），
     以及渲染屏／磁盘判定的接线分离。

  **未变的原因同样具名**：M6.1.7 **未触碰**研究语义面
  （`dataset.py` / `context.py` / `contracts.py` / `evidence.py` /
  `report.py` / `handoff.py` 字节逐位不变），故 F-2 与 EV-11 侧的
  锁值一并不动。

  **本次重渲染不改变本锁的字段集**（M6.1.6 已把 `output_proof.py` 补入锁内），
  仅更新三个取值。`ops/requirements.lock.txt`、Python／依赖版本行、
  两个 preflight 工件哈希**均未改动**。

  **上述失效行仅在形成候选 commit 时重渲染**；HOLD 期间不重渲染，以免声称一个
  不存在的候选。**不得**对本块整体加"全部陈旧"的笼统标注——那对其余 9 行
  ＋ `requirements_lock` 为假。

  ```
  runner_entrypoint: scripts/s0_real_run.py  (zero CLI args; env-clean gate)
  runner_source_sha256:
    scripts/s0_real_run.py:  131b0dd11422ca3d...   # M6.1.7 重渲染（M6.1.6 值 937c96bf6b15d26b）
    src/itsf/s0/runner.py:   b44306f8f1202e80...   # M6.1.7 重渲染（M6.1.6 值 0c1e5cbb9861f8da）
    src/itsf/s0/runinfra.py: b6cd12d3158ba2a7...
    src/itsf/s0/context.py:  e022cd1a012a0dd8...
    src/itsf/s0/dataset.py:  8e12d35043c0110d...
    src/itsf/s0/labels.py:   964af7725061ad5d...
    src/itsf/s0/features.py: a5e222f679731640...
    src/itsf/contracts.py:   d72a9b05dbf481a4...   # M6.1.6 候选重渲染；M6.1.7 未再改动
    src/itsf/s0/report.py:   52d050bb6f1095e9...
    src/itsf/s0/stability.py: 7eebd7e057412cc7...
    src/itsf/s0/handoff.py:  a1f2c0a1ac77f96d...
    src/itsf/s0/evidence.py: 676fbcd1ae0ac2a9...   # M6.1.6 候选重渲染；M6.1.7 未再改动
    src/itsf/s0/output_proof.py: b43c05243bd9b886...   # M6.1.7 重渲染（M6.1.6 值 1f045ed5fb75480a）
    src/itsf/guards.py:      6ec6345734e97f2f...
  requirements_lock: ops/requirements.lock.txt
    sha256 f87799f6d24d3788b8b7b41b7f81d3b01cb2da8070294eba56bada69bbcc16a0
  python: 3.13.14 | pandas 2.3.3 | numpy 2.5.0 | databento 0.81.0
  pandas-market-calendars 5.4.0 | tzdata 2026.3
  os: Windows-11-10.0.26200-SP0 | machine tz irrelevant (all logic ET via
  zoneinfo; context enforces tz-aware ET at the choke point)
  preflight (M5-T5 rerun, IR-22/23/24, IR-24 divergence==0 evidenced):
    S0_INPUT_PREFLIGHT.json  9d6dd1c15602f6188e0b85754118dd51eb81b65c...
    S0_INPUT_PREFLIGHT_REPORT.md  ea287f85638c0afdac6d5d0dd9bbfbc85f1c...
  zero-override proof: 13-gate roster incl. parent_env_clean +
    frozen_constants_in_process; hermetic child env; no CLI args
    (pinned by tests/test_s0_runner.py)
  ```

  **【M6.1.6 候选重渲染，2026-08-09】** 上表标为
  `STALE_SNAPSHOT_NOT_VALID_FOR_CURRENT_WORKTREE` 的四行已按本候选字节
  重渲染，故上表的 STALE 标注对本候选**已不再适用**（保留为沿革）。
  **另一处变更须显式声明**：`src/itsf/s0/output_proof.py` 是 M6.1.6 新增的
  **生产源**（被 `scripts/s0_real_run.py` 导入），此前**不在**本锁内——
  本次**向锁内新增该行**，即改变了本锁的字段集。理由：本锁的用途是钉住
  "将要运行的源字节"，遗漏一个生产源会使锁**静默不完整**。此为工程性
  补全，不涉任何研究定义。
  重渲染后的状态上限为 `READY_FOR_RUN_AUTHORIZATION`（须 final-readiness
  审计全 CLOSED），仍须 Aaron 发 §10 精确语句才进入 `RUN_AUTHORIZED`。

  **【M6.1.7，S3，2026-08-09 —— 本次重渲染的性质，务必与上段区分】**
  上段（M6.1.6）是对一个**已形成的候选**的重渲染。
  **本次不同：M6.1.7 至今没有 commit**，上面三行的现值取自
  **未提交的工作树字节**。故本次重渲染**不宣称任何候选**，
  也**不**把状态推进到 `READY_FOR_RUN_AUTHORIZATION`。
  其唯一用途是：让本锁不要在字节层面静默陈旧。
  一旦 M6.1.7 形成 commit，这三行须**再次**按该 commit 的字节复算确认。
  **`real_s0_authorization` 保持 `REAL_S0_NOT_AUTHORIZED`，不变。**

  **新鲜度警告（如实记录，不隐去）**：S3 在同一次会话内实测到
  `scripts/s0_real_run.py` **四个**取值——`9565c930…` → `a86515c0…` →
  `ef03cc3a…` → **`131b0dd1…`**（工程车道、主代理、复核修复轮先后编辑）。
  上表与锁内记的是**修复轮后的最终重读值**，由 S3 在全部编辑完成后亲自复算，
  **不是转录自任何人交回的清单**——本轮凡他人交回的数值一律重测，
  该纪律对主代理与独立复核员同样适用。
  **该重读不构成「此后不再变」的保证**，故在本锁被用于任何 readiness
  判断之前，**必须**对候选 commit 的字节重新复算。
  未移动并经 S3 复算确认的：`runner.py` `b44306f8…`、
  `output_proof.py` `b43c0524…`、`runinfra.py` `b6cd12d3…`（锁内值，逐位相同；
  最后一项同时是「§4.4 延期项确未被动」的字节证据）。

  **⚠ 本锁的字节一致 ≠ 可以起跑。** 见
  `CODEX_REVIEW_PACKET_M6_1_7.md` 顶部的 **H-1**（guarded logger 会在
  Stage F、一次已通过验证的封存之后烧掉 trial；基线即存在，M6.1.7 范围外）
  与 **L-5**（`runs/` 位于同步中的 OneDrive 树内，任一未声明条目即
  `disk_extra_file` → 烧掉 trial）。**两者都必须在第一次真实 S0 之前
  由 Aaron／Codex 处置**，且都不在本车道的修改权限内。

## 1. 运行代码版本

- 起草时 Git HEAD（全 hash）：`541571f4c0f55eadf19f9edfda1688e98f5deffd`
- 起草时工作区：CLEAN（git status --porcelain 空）
- **本次运行允许使用的唯一 commit**（Aaron 2026-08-02 §四防自引用定案）：
  ```
  authorized_commit_source: exact_section_10_runtime_authorization_event
  authorized_commit: TO_BE_SUPPLIED_BY_AARON
  runtime_requirement: authorized_commit == git_HEAD
  ```
  tracked 授权包**永不**嵌入自身最终 commit hash（含自身 hash 的文件无法
  稳定得到自己的 commit hash）；真正的 commit 只由 Aaron 的 §10 精确语句
  提供，并由 registry 事件解析器结构化验证（event 单元格恰为
  RUN_AUTHORIZED＋逐字语句＋40 位 hash == HEAD）。
  历史注记：runner 已实现（M5-T1..T4），Stage C 为真实链，占位符全除。
- 运行前 HEAD 若与授权语句中的 hash 不一致，**授权自动失效**，必须重新
  申请；工作区必须 CLEAN。

## 2. 冻结与治理状态

| 项 | 引用 |
|---|---|
| s0-freeze-v1 | tag → commit `89e2505928342d131c8f6eff93369bcc46f909b4`（Charter v1.2-r2、S0 预注册 v0.6、purchase_plan rev4） |
| mc-freeze-v1 | tag → commit `5d1ec10ee3ff66cf9bd9c432458d3367dea42da6`（MC_METHOD_SPEC v0.6、platform_params v0.6、registry、manifest_v5） |
| G9 resolution | commit `f932714725dbbc769f9c33deaccd468d1b6d6985`（CME 费表官方证据，Case A，$1.74 不变） |
| M4 最终收口 | commit `d036837ccdb5b0c29b4cff740eb528b6129f02a3`；key attestation commit `541571f4c0f55eadf19f9edfda1688e98f5deffd` |
| IR-1..IR-20 | 全部 APPROVED_BY_AARON（IMPLEMENTATION_RESOLUTIONS.md）；对 S0 直接适用：IR-2/11（描述性口径）、IR-4（sizing 含 $1.74）、IR-7（场景 slip）、IR-12..14（F10）、IR-15（路径）、IR-16（symbology 仅验证披露）、IR-17（发布时刻 NA）、IR-18..20（F10 冲突/前收盘/F4 参照集） |
| 运行前重验 | seal_check、structure assertions、guards 七项冻结哈希必须在运行当刻重新通过（§9 硬门），本包记录不替代运行时检查 |

## 3. 正式 trial 登记（ops/TRIAL_REGISTRY.md 同步建立）

```
trial_id: S0-T001
trial_type: FIRST_REAL_S0_FULL_DEVELOPMENT_RUN
researcher_exposure_ledger_seq: 1        # 首笔真实结果暴露
is_first_real_s0: true
```

**本 trial 将暴露的结果**（一次性、不可逆的 researcher exposure）：
双 Oracle（theoretical/executable）天花板统计；Y_cont 分布与延续基础率
p（θ 主 0.5/副 0.3）；E1/E2 引擎产出（含强制最差日 P1/P5）；按年表与
leave-one-year-out 分组；proxy/actual-micro 两时代轴分列；频率输出
（年可交易日数、Oracle 月均频率）；全部 NA 与剔除计数表。
**不暴露**：MC、EV、GO/STOP、Checkpoint 0（另行授权）。
trial 开始后不得重置、删除或重新编号；失败运行同样入册永久保留。

**trial 正式开始与 exposure 边界（Aaron 2026-07-31 修订批复）**：
- Stage A 或 Stage B 失败：记录 `PRE_RUN_ATTEMPT_FAILURE` 事件，保留
  失败日志与 artifact；**不消耗** researcher exposure ledger；**不**强制
  改用 S0-T002；再次尝试前须 Aaron 重新确认机械问题已关闭。
  （理由：A/B 阶段未计算、未暴露任何 Oracle 结果。）
- Stage A/B 全部通过、即将进入 Stage C 的瞬间：原子追加 `RUN_STARTED`
  事件，S0-T001 进入 RUNNING，exposure ledger 序号 1 **正式消耗**。
- Stage C 及以后失败：S0-T001 永久占用，记录 RUN_FAILURE_REPORT，
  修复后必须申请 S0-T002。
- **任何中间结果一旦被读取或展示，一律视为 Stage C exposure 已发生**，
  无论程序处于哪个阶段。
- **措辞修正（SA-10 N1，Aaron 2026-08-02 批准）**：Stage B 会在内存中
  完整构建数据集（IR-22 的 Stage-B STOP 语义要求如此），但**只释放结构
  计数，绝不释放任何研究数值**；A/B 失败不消耗 exposure 的依据是
  "未释放"，而非"未计算"。
- **Registry 授权快照控制（SA-10 N5 补偿控制，Aaron 2026-08-02 §三）**：
  Stage A 在授权门通过后结构化解析最后一个合法 RUN_AUTHORIZED 事件并
  写入 attempt 目录 `AUTHORIZATION_SNAPSHOT.json`（registry_sha256／
  event_sequence／trial_id／authorized_commit／精确语句 sha256）；
  进入原子 RUN_STARTED 转换前**再次核验 registry 未变**（防事件插入）；
  追加后把新 registry hash 记入 runs 目录。

## 4. 输入数据锁定（运行时逐项重验，不符即 STOP）

| 输入 | 锁定值 |
|---|---|
| A1 job | `GLBX-20260727-DL3BEBCHJA`，root `C:\Users\Aaron\quant-data\databento-archive\intraday-trend\development_signal\`，139 个 dbn.zst |
| A1 官方 manifest.json SHA-256 | `d8d1edc7b549b441d691dda74331806c957a19946e746bd795978e01d73c3ae8` |
| A1 raw 文件哈希 | 全部 139 文件经 loader 逐文件对 manifest 验证（fail-closed，attestation 三方核对 all_raw_sha256_match=true） |
| F10 事件表 SHA-256 | `5e92ad00737339c392ed2c0927736e196e076e185897c146c884d5f515bb5e8c`（IR-17 版，468 行 9 列） |
| symbology mapping SHA-256 | `85a32d44994b51e004e0c322510527aae18b70e1fadc70437e754253a2ac1850`（48 区间，47/47 验证） |
| spread_cost_table.csv SHA-256 | `b6d6984ff7c364f9a57514d7583685956f6b080ec02027ee8401f38f6d9509bf`（唯一允许的成本侧输入） |
| physical-copy attestation SHA-256 | `51ce415c6e2c06eb363d8061b9543c13d1b9ff11dfecbd9ec2312e3c66212813` |
| **raw_file_set_sha256**（集合摘要） | `08fca11b7a9aea1f96f740409c099696e48907a408f409dfbadd82c5ac584298` = SHA256(sorted(relative_path\|size\|file_sha256))，覆盖全部 139 个 A1 dbn.zst；总文件数 139，总字节 58,711,328。一次性验证集合无缺失/新增/改名/替换（成员 hash 取自三方核对过的官方 manifest） |
| Data QA / Preflight 对应 commit | QA `4ab40c5`＋Addendum `ac2979f`；Preflight 重跑 `d036837`（json SHA-256 `5c0ae2d7bc007cd8196d2bca796c1bf2f36e0d2c35ef4ac354d0f1d187614bbf`） |

**硬禁止**：访问 IV（2022-01-01 起任何 NQ 数据，roles.py 机器强制）；
读取 raw A2 BBO（只许上表 derived spread table）；触碰 Physical Lockbox。

## 5. 运行配置锁定

- 全部 Primary 参数唯一来源：STUDY_0_PREREGISTRATION.md（s0-freeze-v1）
  ＋ gate1/platform_params.yaml（mc-freeze-v1）＋已批 IR；代码不得内嵌
  与冻结文本不同的常数。
- 成本口径：S0 统一平台费 $1.74 RT（G9 Case A）＋ 2025Q1 spread 表四档
  场景（proxy 假设按预注册 §7 分时代披露）；场景 adverse slip 按 IR-7。
- Oracle：双路径定义（theoretical / executable）照预注册 §5-6；方向恒
  = d_open；E1（OR 对侧止损/15:45 退出）、E2（无止损 15:45 定时退出）。
- 日期资格：按冻结规则（三类剔除＋批准漏斗顺序）由 runner **独立重新
  计算**；NA 政策 = 行 45。F10：IR-12/13/14/17/18；F4：IR-20；F5：IR-19；
  F11：IR-16 映射仅验证披露。
- **expected_preflight_assertions（只作运行断言，禁作算法配置——Aaron
  2026-07-31 修订批复）**：漏斗 2989→2969→2884→2882→2868；F10 最终互斥
  128/134/83/2528/9；其余 Preflight 结构计数。runner 必须按冻结原始规则
  独立计算后与这些观测值**比对**（不符即 STOP）；禁止把这些数字用作
  样本选择、事件归类或特征取值的输入常数。

  > **【M6.1.6 / S3 补，2026-08-09】治理链与一处文档层冲突（如实并列，不自行裁决）**
  >
  > **治理链存在**：把 preflight 的结构性计数用作 expected 断言，是获授权的——
  > IR-22（`IMPLEMENTATION_RESOLUTIONS.md:70`，已批准）明令 `context.py` 与
  > `scripts/s0_input_preflight.py` **同步修复同测试**；IR-26（同上 :123-，
  > 已批准，Aaron E5）收口于 66 断言 all_pass；`ops/TRIAL_REGISTRY.md:33`
  > （行 11）记录「Stage B 5/5 全过（含 `preflight_assertions_match` 66/66）」。
  >
  > **DOCUMENTATION-LAYER CONFLICT**：工件自带的
  > `S0_INPUT_PREFLIGHT.json` `"approval"` 字段仍为 `"AWAITING_AARON_APPROVAL"`
  > （`S0_INPUT_PREFLIGHT_REPORT.md:5` 同），而 `src/itsf/s0/dataset.py:667-668`
  > 与 `src/itsf/s0/context.py:73` 两处 docstring 称其 "approved"／"APPROVED"。
  >
  > **ENGINEERING CONFORMANCE RISK**：expected 与 actual 由**两份形态不同的
  > 实现**产生（谓词级差异见 `CODEX_REVIEW_PACKET_M6_1_6.md` §6.3），其一致性
  > 今日**只有经验证据**（A1 数据上 66/66 的一次观测），**不是结构等价证明**。
  > 一次真实 STOP 的先例已在 registry 内：2026-08-01 的 `INC-fa9234e0e541`。
  > IR-22 的「同步修复同测试」命令必须持续遵守。
  >
  > 本条**不是**新裁决请求，**不改动 registry、不改动源码**。
- seeds（DR-02 重渲染，Codex baseline audit 批复 Option A）：
  **研究路径随机源唯一 = 冻结 seeds {7, 13, 31}**（S0 §9 Primary
  bootstrap＋附录 A 网格分层抽样＋MC 三 seed 收敛；contracts.
  RESEARCH_BOOTSTRAP_SEEDS 单一真源，进程内冻结常量门核验）。
  `20260731` 改名 `engineering_seed`：仅作 run-infra 出处戳记入运行
  元数据，**禁止进入任何研究计算**（隔离由源码级测试强制）。
  S0 主计算（Oracle/路径/成本）确定性，无其他随机源。
- **runner 必须零命令行参数**：不接受任何可覆盖冻结 Primary 配置的
  运行时输入（inspect 级测试固化）。

## 6. 输出目录

- **双目录语义（Aaron 2026-07-31 修订批复）**：
  - Stage A/B 使用独立 pre-run attempt 目录
    `attempts/S0-T001-A<sequence>_<UTC>/`——只含机械日志与
    PRE_RUN_ATTEMPT_FAILURE 报告，**不含任何研究结果**；机械失败保留
    该目录，不消耗 exposure，不换 trial 编号；
  - Stage A/B 全部通过后才**原子创建**正式目录
    `runs/S0-T001_<UTCyyyymmddTHHMMSSZ>/`——创建正式目录与追加
    `RUN_STARTED` 事件必须属于同一受控转换，随后进入 Stage C 并消耗
    exposure ledger 序号 1；
  - 正式目录运行前**必须不存在**（存在即 STOP）；本包不创建任何目录。
- 禁止覆盖任何既有输出；临时文件、日志、结构结果、最终报告全部归入
  该目录；失败或中止时目录整体保留，禁止删除。
- **hash manifest 非自引用设计（Aaron 2026-07-31 修订批复）**：
  ```
  manifest_format: jsonl_hash_chain（append-only）
  manifest_self_excluded: true          # manifest 不对自身求 hash
  each_record: {stage, relative_path, file_sha256, previous_record_hash}
  ```
  临时未关闭文件不得进入 final manifest；每阶段结束写入 stage seal
  记录；失败目录同样保留完整 hash chain。

## 7. 运行阶段与信息释放顺序

| Stage | 内容 | 信息释放 |
|---|---|---|
| A | 运行前机械检查（§9 全部硬门） | 仅 pass/fail |
| B | 数据加载与结构验证（对 Preflight 计数逐项一致） | 仅结构计数 |
| C | S0 计算（Oracle/标签/引擎） | **零释放**（含日志，见下） |
| D | 结果完整性验证（行数＋**NA 守恒**） | 仅 pass/fail |

- **Stage C 日志防泄漏（机器强制）**：控制台与日志只允许阶段状态、
  心跳、文件 hash、非研究性的完成/失败状态；机器禁止输出 Oracle、
  标签、E1/E2、年度结果、频率、分布或任何局部研究数字——以日志词汇
  与 schema 守卫测试固化。
- **NA 完整性（取代"无 NaN"粗判——Aaron 2026-07-31 修订批复）**：
  预期 NA 必须与批准的 feature/label/anchor NA 原因表**逐项守恒**
  （允许原因显式枚举：F5 roll 日/IR-19 锚点缺失、F10 多事件、ADR14 与
  F4 warm-up、L82 零方向、锚点缺失等）；任何未登记原因产生的 NA/NaN
  立即 STOP；不得以 dropna、填充或隐式类型转换消除异常。
| E | 生成正式 S0 报告（封存入 trial 目录，含哈希） | 报告整体交付 |
| F | S0 报告封存后，MC 才可另行申请授权 | — |

中途不得向 Aaron 展示零散结果、日志数字或局部指标；不得因看到任何
中间结果而修改代码、配置或样本（预注册反窥视条款）。

## 8. 失败处理

hash 不符 / schema 不符 / 日期计数与 Preflight 不符 / 配置漂移 /
异常退出 / 任一测试失败 → **立即停止**。不得自动修复；不得静默重跑；
不得更换 seed；不得删除失败输出。生成 RUN_FAILURE_REPORT（含失败点、
已释放信息清单、目录 hash 状态）入 trial 目录并登记 TRIAL_REGISTRY。
修复后是否允许新开 trial（S0-T002）由 Aaron 再次批准；S0-T001 编号
永久占用。

## 9. 运行前硬门（全部满足才可进入 Stage B，缺一即 STOP）

1. git status clean；2. HEAD == 授权语句中的 commit；3. 全量 pytest 通过；
4. seal_check 通过；5. structure assertions 通过；6. guards 七项冻结哈希
通过；7. M4_KEY_CLOSURE_ATTESTATION.md 存在；8. gate1/G9_RESOLVED.flag
存在；9. ops/SECOND_COPY_ATTESTED.flag 存在；10. §4 全部输入 hash 逐项
一致；11. 输出目录此前不存在；12. TRIAL_REGISTRY 事件链
显示 S0-T001 处于 **RUN_AUTHORIZED** 状态（§0 状态机；由 Aaron 的 §10
精确语句触发追加，PACKET_APPROVED 不构成此门）；13. Aaron 已给出 §10
精确授权语句。全链以机器退出码为闸。

## 10. 唯一有效授权语句

只有 Aaron 回复以下**精确文本**（替换尖括号内容）后才允许运行：

```
启动第一次真实S0，授权trial_id: S0-T001，使用commit: <完整commit hash>
```

"开始"、"可以跑"、"继续"或任何其他表述**均不构成授权**。

## 11. 明确排除

本授权包只覆盖首次真实 S0（S0-T001）。**不**自动授权：MC、Checkpoint 0、
IV 访问或采购、Physical Lockbox、任何参数修改、第二次及以后 trial、
对本包所锁 hash 的任何替换。上述每一项都需要独立申请与 Aaron 独立批准。
