# MC-REG-COLLISION-001 —— fresh Sol 批准（附修改）

```
RECORD_TYPE=DELEGATED_RATIFICATION
ITEM_ID=MC-REG-COLLISION-001
VERDICT=PASS        RULING=RATIFIED_AS_MODIFIED
DECIDED_BY=Codex GPT-5.6 Sol，fresh top-level session
DELEGATED=YES —— 委托裁定，不是 Aaron 本人的判断。凡引用必须带此标记。
BASIS=ops/RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md
      （Fable 5 提案，SHA256 03C42848…，16230 bytes）
TRANSCRIBED_BY=Opus 5 main agent（builder seat）—— 转录，非背书
AARON_ADJUDICATION=PENDING —— **本记录不解锁任何实现**
```

> Sol 原话：「`PASS` applies only to the ruling as modified below. It releases
> no gate, authorizes no run, and is not Aaron's judgment.」

---

## 1. 批准的条件全文（C1–C5）

- **C1** —— 原样批准。MC 前缀所有权：每一行大写 `MC_*` 由 `mc_registry` 拥有；
  未知令牌与畸形行式行 fail closed。
- **C2** —— **整条替换**（下节全文）。
- **C3** —— 恰好解除 `MC_RUN_AUTHORIZED` 与 `MC_RUN_STARTED` 两个。另外三个名字
  继续按名拒绝，且原五名转录须保持可核，以**显式排除项并引用本裁定**的方式记录，
  不得静默删除。
- **C4** —— `consumer.authorize_real_mc` 的无条件 raise 只能换成基于解析的
  live-authorization 判定，**永不**用子串匹配，**且不得早于 C2**。
  `day_strata_supplement` 的 MC 侧后继同理。
- **C5** —— 解除动作不得搭载任何 registry 追加、exposure 移动、授权、已批准记录
  编辑，或 Stage-I／Tier-1 裁定。

## 2. C2 的替换全文（Sol 撰写）

> **C2（单快照中介不变量）**：`MC_RUN_AUTHORIZED` 与 `MC_RUN_STARTED` 离开按名
> 拒绝，只能发生在**同一次**引入 `ops/TRIAL_REGISTRY.md` 单一共享生产校验边界的
> 改动里。任何把该路径当作授权来源或链解析来源的生产代码，其结果必须经由该边界
> 取得；边界之外的生产直读或直接调用 resolver 一律禁止，**例外**仅限无条件拒绝
> 的桩——即不可能返回授权、就绪状态或可用链的桩。对每一个依赖 supplement 解析的
> 结果，边界必须**读一次** registry，并让 supplement 解析与 MC 解析
> （`resolve_mc_chains`，直接或经 `find_live_mc_authorization`）跑在**同一份不可变
> 快照**上。任一生命周期给出拒绝，即无可用结果、无下游动作。须有一条
> 架构/不可绕过测试与一条行为测试同时钉住这两条性质。今日
> `supplement_runner` 的 resolver seam 与 A_PRECHECK 门必须使用该边界；
> `day_strata_supplement`、`real_input`、`consumer` 在其替代物改用该边界之前，
> 保持无条件拒绝。在同一次改动落地之前，按名拒绝保持与今日逐字节相同。

## 3. Sol 的最强反对，以及 builder 的独立复核

> Sol：「C2 原文要求覆盖每一个生产读取方，却允许对同一份**可变**共享文件分别
> 读取。于是 MC 校验可能在一个版本上成功，而 supplement 解析作用在另一个版本
> 上。」

**builder 已机械复核，反对成立。** 生产代码里对 `ops/TRIAL_REGISTRY.md` 存在
**四处彼此独立的 `read_text`**：

```
src/itsf/mc/consumer.py:3206
src/itsf/mc/day_strata_supplement.py:140
src/itsf/mc/real_input.py:32
src/itsf/mc/supplement_runner.py:947
```

按 Fable 原 C2 的措辞，各路径各自接线、各自读取，两套解析拿到不同快照是可达的。
**这是一次实质改进，不是措辞润色。**

## 4. 未采纳与不阻断项

- **C6 未采纳**（builder 提的大小写/前缀变体加固）。Sol：真实但**先于 R2 存在**、
  机器不可达的加固缺口，R2 既未制造也未扩大；**另案跟踪**。
- **`_TOKEN_SCAN_RE` 归属问题不阻断**。畸形的大写 `MC_RUN_*` 行会被归到
  `supplement_row_malformed`。Sol：这是诊断归属问题，仍然 fail-closed，**不构成
  supplement 拥有该行**。
- **F3 未触发，根活着**。§D.3.4（`ops/DECISION_PACKET_N00_AND_ND1.md:811`）的
  `REASON` 是「生命周期定义……尚不完整」，`CONSEQUENCE` 是「在 N-D3 裁定前」；
  对这两个 MC 事件不附带任何额外的接线或 GRID-replay 前置。builder 已独立核对该
  行，读法一致。
- **R1 的成本核算不反转**：仍需修订 G8，且把单快照问题换成跨文件一致性与排序
  问题。

## 5. 传输（本次两端都干净）

Sol 收尾复核：六份哈希与字节数全中；`git log ba97453..HEAD -- <六份>` 为空；
工作树 clean；实测 HEAD `2bea4a4b01f75d14bf9cd36de6e97d75bcb8039b`。未跑任何
测试，未执行任何研究。

**上一轮 STOP 的修复在本轮生效**：`REVIEWED_SET_UNCHANGED_SINCE` 这个不会过期的
钉子被 Sol 用上了，且在 HEAD 已经又前进两个 commit 的情况下依然成立。

## 6. 一条必须随裁定传播的独立性限制

Sol 自陈：

> 「This reviewer authored the C2 modification and therefore is not independent
> of that modified condition's design.」

**照直说：C2 的现行文本从未被任何独立席位复核过。** Sol 独立于 Fable 的提案与
builder 的记录/代码，但对 C2-as-modified 它是作者。

builder 的意见（供 Aaron 裁）：**不必现在再开一轮。** C2 约束的是一次未来改动，
而那次改动落地时会走 N14（Codex exact-tree MC 审查）。在实现存在时复核一条条件，
比在抽象层面复核它更有力。但这条限制必须随裁定一起传播，不得在日后被读成
「C2 已经过独立复核」。

## 7. 本记录不做什么

Fable 的 COLLATERAL 写明修订「**only after Sol ratification + Aaron**」。Sol 已
批准，**Aaron 尚未裁决**。故本轮：

- 未改 `supplement_registry.py`、`supplement_contract.py`、`mc_registry.py`；
- 未向 `ops/DECISION_MC_REGISTRY_COLLISION.md` 追加收口段（该追加在 COLLATERAL
  清单内，同样受 Aaron 门限）；
- 未建任何校验边界，未接任何线；
- 未追加 registry 行，未动 exposure，未授权任何运行。
