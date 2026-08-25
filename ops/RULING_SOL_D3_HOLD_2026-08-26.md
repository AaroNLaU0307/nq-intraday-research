# D-3 复审结果 —— fresh Sol：**VERDICT=HOLD**

```
RECORD_TYPE=REVIEW_OUTCOME
ITEM_ID=D-3
REVIEW_ID=rv-0a3a74abcff1-549123517d20 的后继：rv-f4207865a116-c004854e6828
GATE=TIER1_DISCRETIONARY（自主复审：不释放任何门，不是任何要求的 gate）
VERDICT=HOLD
SEAT_STATUS=BLIND —— **席位未被烧**
TRANSPORT_PRECHECK=PASS
DELEGATED=NO —— Sol 只复核，终裁仍归 Aaron
OUTCOME_CLEAN=是（机械扫描；本件永不进入 carries_outcome）
```

> **来源与哈希的诚实说明。** 本裁定**经聊天送达**，不是以磁盘文件交付的。
> 按常设传输规则「聊天携带的字节永远不是真相源」，本件记录的 SHA256 证明的是
> **本次转录的字节**，不是某个原始文件。转录忠实性由 Aaron 的原始粘贴为准；
> 若两者不符，以 Aaron 手上的原文为准并在本件下方追加更正，**不改上方**。

---

## 一、Sol 返回原文（逐字）

```
ITEM_ID=D-3
REVIEW_ID=rv-f4207865a116-c004854e6828
TRANSPORT_PRECHECK=PASS
VERDICT=HOLD
SEAT_STATUS=BLIND
STRONGEST_OBJECTION=提案把安全性建立在尚未定义的"写者租约"上，但现有读—校验—追加
之间没有同一临界区。另一写者可以在最终快照核对后、P3 追加前改变 registry，使 P3
基于陈旧授权快照落盘。当前简单文本追加也不能提供跨进程或 OneDrive 级原子性。
```

**FINDINGS（五条，Sol 自评置信度照录）**

1. **HIGH／高置信度** —— 缺少覆盖「最终快照核对 → P3 追加」的互斥或
   compare-and-append 协议。`registry_boundary.py:123` 只产生不可变读快照；
   `runner.py:762` 的最终重核、目录创建与 `runner.py:772` 的 `RUN_STARTED`
   追加是分离操作；`append_registry_event_line`（`runner.py:1388`）只是无锁
   `open("a")`＋`write`，无 CAS、无 flush/fsync 协议、无冲突复核。
   **所以「受托单写」目前是角色约定，不是可验证的单写不变量。**
2. **HIGH／高置信度** —— 失败事件条款与已批准 actor 合同及现有先例直接冲突。
   `supplement_contract.py:238` 把 P3 指定给 runner；`:246` 起 A1／F1／F2 同样
   指定 `main agent (mc_ds_runner)`；`supplement_runner.py:648` 的
   `plan_failure_event` 又把 F1／F2 actor 硬编码为 runner；S0 的
   `runner.py:698` `_fail_run` 在捕获异常、进程仍存活时自行追加 `FAILED`。
   **「运行器永不写自己的讣告」不适用于被运行器捕获的失败；只有硬崩溃才没有
   存活 runner。**
3. **HIGH／高置信度** —— 硬崩溃与陈旧租约恢复没有完整状态机：租约取得、持有
   范围、所有合法写者、崩溃释放、恢复授权、PID／时钟失效、恢复事件词表，以及
   P3 后无终止行时下一次 bootstrap 的精确拒绝条件，全未定义。且当前没有可供
   复核的 MC 生产执行路径 —— `supplement_runner.py:935`
   `run_supplement_production` 仍默认拒绝。
4. **MEDIUM／高置信度** —— never-re-read 只在 S0 先例中通过对象传递和结构维持，
   尚未成为 MC runner 的强制接口。S0 把预暴露快照放入 prepared object 并在 P3
   后继续传递，但 D-3 没有规定 MC 的等价接口，也没有禁止下游重新调用 registry
   boundary。**仅靠注释无法关闭分快照回归。**
5. **HIGH／中置信度** —— OneDrive 环境下的追加原子性未建立。工作树确实位于
   OneDrive 路径；当前 writer 是普通文本追加。审阅范围内没有证据证明半写、
   重复写、冲突副本或同步代理竞争可被预防或可靠检出。
   **「qros-runtime 所有 writer 均无锁」仍是 BUILDER 报告** —— 该席位没有越界
   检查 qros-runtime 源码。

**五点逐一作答**

| 点 | 结论 | 要点 |
|---|---|---|
| ① 分快照读 | **HOLD** | 须让同一不可变预-P3 快照贯穿运行，并使最终快照比较与 P3 追加处于一个所有 registry writer 都遵守的临界区；还须用接口和测试阻止 P3 后重新读取 |
| ② 陈旧租约 | **HOLD** | 租约语义尚未定义。自动超时回收、谁可回收、回收是否属受权写入，**不能由 reviewer 代 Aaron 决定** |
| ③ 并发竞争 | **HOLD** | 现有读取与追加没有跨进程互斥；两个 writer 可在相同旧快照上分别通过检查。**P3 安全条件目前不可满足** |
| ④ OneDrive 原子性 | **HOLD** | 代码阅读不能证明同步环境属性；须由 Aaron 决定是否禁止在主动同步树上做 canonical 写入，或批准一套有明确故障模型、冲突检测与恢复程序的操作边界 |
| ⑤ actor 表冲突 | 见下 | —— |

**⑤ 的完整答复（逐字，这是本次复审最有价值的一段）**

> 「记录 actor」与「执行追加的进程」在抽象上是两个问题，但当前 schema 没有独立
> executor 字段，且 actor 文本明确包含 `mc_ds_runner`，planner 也硬编码该值。
> 因此现有已批准工件实际上把二者绑定了。不能在不修订合同的情况下让主代理写行
> 却仍标称 runner。**较窄且与现有合同一致的解释是：运行器存活并捕获到的
> A1/F1/F2 仍由运行器追加；硬崩溃后的检测／恢复由主代理负责，并使用 Aaron
> 批准的独立恢复语义。** 是否采用该解释仍属 Aaron 终裁。

**UNRESOLVED_FOR_AARON（五项，原文）**

1. actor 是否同时表达实际执行者；若否，是否增加独立 executor provenance。
2. 保留 A1／F1／F2 的 runner actor，还是修订已批准 profile、planner 与生产先例。
3. P3 后硬崩溃应产生什么事件、由谁追加，以及恢复写入的授权条件。
4. registry 是否允许继续在主动同步的 OneDrive 树中作为 canonical 写入面。
5. 租约回收能否自动执行，还是必须 fail-closed 等待人工裁定。

**INDEPENDENCE_STATEMENT（摘要，原文按维度分述）**：新顶层会话，非 builder 会话
延续；未参与提案或送审代码创作，只读未改；提案来自 Fable、复核为 Codex/Sol，
`MATERIAL_DESIGN_CONTRIBUTOR=UNKNOWN` 仍成立，**本结论不认证 sealed
preregistration 的未知设计来源**；未读真实数据、未运行研究、未暴露 target
metric，**不主张经验复制**；未打开隔离件、未做任何 grep／rg／rglob／符号检索。

**Sol 自报的传输证据**：line 60 freshness marker 匹配；六工件＋packet 的
SHA-256／字节数全部匹配；`git log 7b582b1..HEAD -- <六路径>` 为空；
`GENERATED_BLOCK_SHA256` 重算 `4bf1b6dd…942e` 匹配；未运行测试或真实 run。

---

## 二、builder 的独立复核 —— **逐条复现，不采信**

`REPRODUCED` ＝ 我自己打开代码看到了同一事实；`CONFIRMED_BY_RECOMPUTE` ＝ 我用
运行时自己的规则重算得到同一数值。

| Sol 的断言 | 我的复核 | 结果 |
|---|---|---|
| `GENERATED_BLOCK_SHA256=4bf1b6dd…942e` | 用 `serialize.generated_block_preimage` 对 101 条字段行重算 | **CONFIRMED_BY_RECOMPUTE** |
| F1：writer 无锁 | `runner.py:1388` 全文即 `open("a")`＋`write` 两行，无 lock／CAS／fsync | **REPRODUCED** |
| F1：核对与追加分离 | `runner.py:772` 一带确为 `pre_exposure_recheck()` → `rdir.mkdir()` → `append_registry_event("RUN_STARTED")` 三个独立步骤 | **REPRODUCED** |
| F2：actor 表与 planner 冲突 | 与我出包前实测一致（提案 §2.5–2.7） | **REPRODUCED** |
| F3：无 MC 生产执行路径 | `supplement_runner.py:935` gate-first，`assert_real_run_allowed` 紧随其后 | **REPRODUCED** |
| F4：never-re-read 靠结构 | `s0_real_run.py:2602` 把 assertions bytes 收进 prepared object；`:2999` 注释明写 `REGISTRY` 在该行以下不再被读 —— 确为结构＋注释，非机制 | **REPRODUCED** |
| F5：OneDrive 属环境属性 | 同意；仓确在 OneDrive 树下 | **REPRODUCED** |

### 2.1 我第一次重算 `GENERATED_BLOCK_SHA256` 得到的是别的值 —— 是我错

首次我把「章节标题行 ＋ 空行」也算进了 preimage，得 `0a0f0128…`。运行时的
`_render`（`packet.py:1154`）只对**字段行**取前像。改正后与 Sol 一致。
**记在这里，是因为一个错误的独立重算若不追究，会被误当成 Sol 的错。**

### 2.2 Sol 没提的第四个 ⑤ 数据点：写入器的 docstring 自称主代理

`append_registry_event_line` 的 docstring 第一句是：

```
"""MAIN-AGENT owned append-only registry writer: ...
```

而 `scripts/s0_real_run.py:3139` 把它接成 actor 恒为 `"main agent (s0_real_run)"`。
**「谁拥有这个写入器」与「行里写谁是 actor」的混淆，就活在同一个函数里** ——
docstring 说主代理拥有，调用点写运行器执行。这与 Sol 的 ⑤ 同向，且是第四个
独立证据点（前三个：actor 表、planner 硬编码、S0 先例）。

### 2.3 一处范围澄清

Sol 正确地把「qros-runtime 所有 writer 无锁」标为 **builder 报告、未经其复核**。
属实：那是我在出包前检索 `fcntl`／`msvcrt`／`filelock`／`.lock` 得零命中，
**是我的报告，不是独立确认**。Sol 遵守了不越界的约束，这是对的。

---

## 三、这份 HOLD 意味着什么、不意味着什么

**意味着**：D-3 提案**不进入实施**。条件 3 继续生效 —— 生产代码不得获得任何
registry 写能力。上面五项 `UNRESOLVED_FOR_AARON` 需要 Aaron 本人裁。

**不意味着**：

- **不意味着 Fable 的提案被否**。P3 那一半与已批准 actor 表一致；Sol 质疑的是
  **它的安全前提**（租约、临界区、原子性）尚不存在，以及**失败事件那一半**与
  已批准合同相抵。
- **不释放也不阻塞任何门**。Tier-1 自主复审「不释放任何 transition，也永远不是
  任何要求的 gate」。ITSF 的 `A2→B` 与 `I→J` 状态不因本件改变。
- **不是研究授权，不是运行授权。**

**builder 在此停手。** 修 HOLD 需要先定 ⑤ 与那五项，而它们全在 Aaron 的权限内；
在他裁定之前动手，等于替他选一种读法。
