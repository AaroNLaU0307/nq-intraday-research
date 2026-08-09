# DECISION_REQUIRED_READY_SUPERSESSION（治理决策包；Fable 起草，Aaron 裁决）

M6.1.4 主代理按 Codex 指令新建。本文件**只陈述事实与选项，不做裁决、
不追加任何 registry 事件**。

> **独立复算证明（2026-08-09，只读代理 S3）**：本文件 §1 的**全部**事实已对
> 仓库实际字节逐条复算，**无一需要更正**。复算项：registry sha256
> `de63b3d6…b440`（一致）；`resolve_authorizations` 对该字节返回
> **0 条存活授权**且链无 problem；`git rev-list --count 6cb7eb71..HEAD` == **7**；
> 5 个带码里程碑的 **40 位全 hash 逐一比对一致**；当前 HEAD 仍为
> `1e188b5…`（本轮无新 commit）。本文件是这五份治理文档中**唯一**未发现
> 事实错误的一份。

## 1. 事实（2026-08-08 起草，2026-08-09 经 S3 复算仍全部成立；按来源分三类——registry 字节 / git 历史 / 外部裁定）

**1a. registry 字节事实**（对 `ops/TRIAL_REGISTRY.md` 实际字节核对，
sha256 `de63b3d690c5c4be…b440`）：

- 最新 READY 事件 = **行 11 READY_FOR_RUN_AUTHORIZATION @
  `6cb7eb718c903d119b7e51c7171e6db6f43aca67`**（2026-08-01，IR-26 收口，
  SA-16 审计 ALL_CLOSED）。
- 两个历史 RUN_AUTHORIZED（行 6 @`524c9ab`、行 9 @`08e74235`）均已被
  行 7/10 精确 supersede；生产解析器 `resolve_authorizations` 返回
  **0 条存活授权**。S0-T001 未消耗。

**1b. git 历史事实**（对 `git log 6cb7eb71..HEAD` 核对）：

- 行 11 之后代码前进了 **7 个 commit，其中 5 个为带码候选里程碑**，
  每个均有自己的评审包、均无对应 READY 事件（M6.x 系列在 Codex HOLD
  下明令不追加 READY）：
  - M6 `08fca9bd47837489e7a84fcc4107f2fc7ce807b4`
  - M6.1 `4dcff1697fd87c6c48b4d30fac9f3dedd446087c`
  - M6.1.1 `ffb1647615dbc9259ab749ea6e4a223432c455ae`
  - M6.1.2 `712532ddd6d2276ec665eaed6db7ce270df9c544`
  - M6.1.3 `1e188b54ace011bb4c2ab7356f775af6d32aab37`（当前 HEAD）
  （另两个为 registry 行 11 追加 commit 与 HANDOFF_TO_CODEX 独立
  handoff commit。）

**1c. 外部裁定（无库内一手来源；来源=Aaron 转达的 Codex 复审结论，
以本文件与 M6.1.4 执行提示词为其库内记录）**：

- Codex 对 M6.1.3 裁定 `M6_1_3_VERDICT=HOLD / REAL_RUN_READY=NO`；
  RC-1/RC-2 列 ENGINEERING_REQUIRED，M6.1.4 工程修复进行中。

## 2. 问题

registry 为 append-only。行 11 的 READY 绑定的是历史 commit
`6cb7eb7…`；新 HEAD 出现后，旧 READY 事件的账面语义未定义——packet §0
状态机词汇只定义了 `RUN_AUTHORIZATION_SUPERSEDED`（针对 RUN_AUTHORIZED
行），**没有 READY 行的失效/挂起事件类型**。当前风险仅为可读性
（阅读者可能把行 11 误读为"最新代码 READY"）；无暴露风险——解析器
0 存活授权，真实链 fail-closed。

## 3. 选项（列举，不裁决）

- **Option A — 无操作惯例**：READY 语义上绑定其 40 位 commit；新 HEAD
  天然无 READY，无需新增事件类型。成本最低；缺点是账面需要读者理解
  该惯例（可在 packet §0 增一句惯例说明，属文档而非事件）。
- **Option B — 显式失效事件**：在 §0 词汇表新增
  `READY_SUPERSEDED`（或 `READY_EXPIRED`）事件类型，凡候选 commit
  前进且旧 READY 未消耗时追加一行指向被取代行。账面最清晰；成本是
  每个里程碑一行、且词汇表修订本身需 Aaron 批准后才能首次使用。
- **Option C — 挂起语义**：行 11 保持「最近一次通过 final-readiness
  审计的基线」含义，待下一次 final-readiness 审计产生新 READY 行时
  自然覆盖；期间 packet §0 以 HOLD/NOT READY 状态行作为现势声明
  （本次已按 Codex 指令写入）。缺点是长窗口内账面与代码状态脱钩，
  依赖 packet 而非 registry 表达现势。

## 4. 请求

请 Aaron 在 Option A/B/C（或另行指定）中裁决。未裁期间维持现状：
0 存活授权、不追加任何 registry 事件、不受理授权、真实 S0 禁止。

## 5. 本裁决在 Aaron 队列中的位置（防止队列被观察项灌水）

**待 Aaron 裁决的完整集合恰为两组**：

1. **DR-1 … DR-8**（八个方法家族，见 `DECISION_REQUIRED_M6_1.md`；
   DR-8 = DR-M6-H）；
2. **本文件的 READY supersession**（Option A/B/C）。

**没有第三组。** 特别地，以下**不是**新增裁决项，不得计入队列：

- **DR-7「没有专门的 report/seal gate」**——那是对 DR-7 的**观察**，
  DR-7 本身已在第 1 组内。该条已从 M6.1.4 packet 的 DECISION_REQUIRED 栏
  移出，并入其 P-7。
- **M6.1.4 packet 的 D-4／D-5／D-6**（EV-11 五布尔 reducer 冻结、逐叶披露的
  冻结 schema 扩展、单调 `y_cont` 轨）——它们是**挂在既有 DR 伞下、被一条
  已在队列中的裁决卡住的工程项**，说明"哪条裁决落地后哪块工程才能动"，
  **不增加**需要做的裁决数量。

工程侧的未闭合项（F-1／F-2 等）属 `ENGINEERING_REQUIRED`，在 Fable 权限内
执行，**同样不进入本队列**。

### 5.1 M6.1.6 / S3 队列复核（2026-08-09）——**长度不变，且撤回一条候选**

**队列仍恰为两组。M6.1.6 未新铸任何研究 DR 编号，未追加任何 registry 事件。**

- **撤回（WITHDRAWN）**：拟建的候选台账行 **`NEW-LABELDEPS-CONFLICT`**
  （称 `dataset._LABEL_DEPS` 与 `_label_anchor_availability` 内的 `ok`
  「互斥／内容不同」）**经逐格复算为假**，予以撤回，**不进入本队列**。
  在 `_LABEL_DEPS` 所载的四条轴（O1000, C1544, ADR14, d_open）上，
  两者对**全部六个标签**取值一致；唯一差别是 `ok` 另需 `pm_ok`，
  而 `_LABEL_DEPS` 没有 PM 列——正确表述是 **PROJECTION**，不是矛盾。
  （该字面量全库零命中，故撤回为纯文档性，无行需删除。）
- **不变**：M6.1.4 packet 的 **D-4**（EV-11 reducer 冻结）仍挂在既有 DR 伞下。
  M6.1.6 **未触碰 EV-11 语义**，**故本轮不产生任何新的 Aaron 裁决请求。**
- **补正（不改变队列）**：不得把 D-4 的背景读作「preflight 全然未获批准」——
  IR-22／IR-26／registry 行 11 构成的外部治理链**授权了把 preflight 的
  结构性计数用作 expected 断言**；但该链**不冻结 reducer**，故 D-4 存续。
  同时存在一处 **DOCUMENTATION-LAYER CONFLICT**（工件 `approval` 字段
  说「待批」，`dataset.py:667-668` 与 `context.py:73` 两处 docstring
  说「已批」），**本轮不解决、不裁决**。
  详见 `CODEX_REVIEW_PACKET_M6_1_6.md` §6.1。
- **§1c 的前向状态更新**：其「M6.1.4 工程修复进行中」现应读作——M6.1.4-R2
  收口于 `HOLD`（R1 PASS 附条件／R2 FAIL），其后 M6.1.6 轮闭合了两个
  具名接缝并获独立复核 `M6_1_6_REVIEW=PASS`（其中两条 Low 的修复
  **未经重新复核**）。**Codex 对 M6.1.3 的 `HOLD / REAL_RUN_READY=NO`
  裁定未被撤销**，`REAL_S0_NOT_AUTHORIZED` 维持，
  §4 的「未裁期间维持现状」原封不动。
- **§1a／§1b 的事实**（registry sha256 `de63b3d6…b440`、0 条存活授权、
  `6cb7eb71..HEAD` == 7 个 commit、当前 HEAD 仍为 `1e188b5…`）
  **经 M6.1.6 / S3 再次复算，仍全部成立**（registry 与 EXPOSURE_LEDGER
  字节本轮未改动）。
