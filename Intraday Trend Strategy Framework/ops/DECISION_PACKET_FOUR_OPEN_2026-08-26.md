# 四项待裁决策包 —— 交 Fable

```
RECORD_TYPE=DECISION_PACKET
DATE=2026-08-26
ITEMS=4
DECIDER=Fable 5（Aaron 常设指示：需他决策的直接交 Fable）
BUILDER=Opus 5 —— 呈交，不投票；每项均给出可裁选项与依据，不预填结论
```

> **裁定 ≠ 解锁。** 其中两项即使裁了，也不能由 builder 直接执行——原因逐项写在
> 「裁定之后还缺什么」里。Aaron 若要一次到位，需在该项上额外一句授权。

---

## D-1 —— exposure 台账是否补一条只含指针的行

### 事实

2026-08-25 一个 fresh Sol 复审席位读到 `ops/MC_TO_STRATEGY_MASTER_PLAN.md`
（outcome-carrying），自陈 `OUTCOME_EXPOSED=TARGET_METRIC`，从此不能再担任
outcome-blind 的 Stage I。事件**已经**记在
`ops/REVIEWER_EXPOSURE_LOG.md`（append-only，保留席位自评）。

**没有**记进 `ops/EXPOSURE_LEDGER.md`，理由三条（实测）：

1. 该件是**合规承载件**，逐行转录仓根的权威历史台账，
   `test_exposure_ledger_migration` 守着两者**逐行恒等**；只追加承载件立刻破坏。
2. `test_exactly_one_row_carries_the_target_metric_exposure` 要求
   `REVEALED_TARGET_METRIC` **恰有一行**。
3. **最要紧**：该台账记的是**研究者对 S0 outcome 的暴露**，消耗研究自由度，
   量纲是累计 1575。本次是**复审席位读到治理文档里的 verdict token**。
   **烧掉一个席位不消耗研究自由度。** 同轴记录 = 凭空多出一次「研究者暴露于
   目标统计量」。

### 可裁选项

- **A：不补。** 席位暴露与研究暴露是两条轴，各自有台账，互相指针即可
  （现状）。代价：读 exposure 台账的人看不到这件事，除非他也读席位台账。
- **B：补一条只含指针的行**，classification 用不与研究暴露冲突的值。代价：要动
  一份 append-only 的权威台账，并修改一条已批准的「恰一行」不变量。
- **C：补，但补在仓根的权威历史台账**，承载件按转录规则同步。代价同 B，且触及
  五列历史格式。

### 裁定之后还缺什么

**若裁 B 或 C：builder 仍不能执行。** Aaron 的常设禁令写明「未经**单独授权**
不得追加 registry／exposure 事件」。那是对**动作**的禁令，Fable 的裁定是对
**问题**的回答——两者不互相取代。执行需要 Aaron 另加一句，或由他本人追加。

---

## D-2 —— 恢复锚是 outcome-carrying，拆还是不拆

### 事实

`ops/MC_TO_STRATEGY_MASTER_PLAN.md` 同时是：

- `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome` 成员（已核）；
- 本项目**唯一的恢复锚**，其 §1「恢复序」是任何会话定位状态的标准第一站。

**所以任何 outcome-blind 复审者，做一次完全正常的状态定位就会踩中。** 这不是
一次偶然——它一直成立，只是过去的提示词够窄，没人走到那里。D-1 那次暴露就是它
的第一次兑现。

### 可裁选项

- **A：拆锚。** 主计划分成「outcome-clean 恢复锚」＋「outcome-carrying 附录」，
  恢复序指向前者。**结构性根治**，但改动大，触及一份 append-only 的锚文件，且
  §1 恢复序本身要改。
- **B：不拆，靠禁区清单。** 已落地机械化版本：
  `test_a_live_prompt_names_the_outcome_carrying_artifacts_as_off_limits`
  强制活跃 review 的提示词点名登记表与恢复锚。**便宜**，但本质是把安全押在
  「每次都写对提示词」上。
- **C：A＋B。** 拆锚，同时保留禁区清单作纵深。

### builder 的一条相关事实，供裁定参考，不构成投票

Review Packet v1 的 `PULL_PROTOCOL` 让复审者**列出所需路径、由工作会话提供
字节**——它根本不导航。这是比 B 更强的结构性缓解，**但只覆盖走 packet 的复审**，
不覆盖任何按恢复序自行定位的会话（包括未来的 builder 会话本身）。

---

## D-3 —— P3 与失败事件由谁追加

### 事实（两份已批准文本相抵）

- **全局边界第 4 条**：「registry／exposure／supplement ledger 均 append-only，
  **只允许主代理单写**」。若编排器自己追加 P3，那就是**生产代码在写 registry**。
- **`scripts/s0_real_run.py` 的先例**：真实 S0 运行**由运行器自己**追加了
  `RUN_STARTED`。这是已发生的历史，不是提案。

两种读法都讲得通。这与 `MC-REG-COLLISION-001` **是同一个形状**：两份已批准
工件相抵，需要一次调和。

### 可裁选项

- **A：编排器自己追加**（沿用 S0 先例）。需说明边界第 4 条的「主代理」在运行器
  语境下如何读。
- **B：编排器只**规划**事件，由主代理追加**（`plan_failure_event` 今天正是只
  规划不写）。代价：运行中途需要人工介入，而 P3 是 pre-start/post-start 的唯一
  分界——介入窗口本身带风险。
- **C：分开裁**：P3（在 exposure 消耗点上）与失败事件（事后）适用不同规则。

### 裁定之后还缺什么

**builder 建议走完整三步**：Fable 提案 → **fresh Sol 批准** → Aaron 裁决。
理由：这一项决定的是**生产代码能否写权威 trial registry**，而
`MC-REG-COLLISION-001` 走完三步时，Sol 在 Fable 的提案里找出了一个真实漏洞
（可变文件的分快照读取）。同一形状的问题，同一道工序。

---

## D-4 —— qros-runtime 的 `_SAVE_DIR` 改不改

### 事实

`qros_runtime/packet.py:64` 硬编码 `_SAVE_DIR = "runs/packets"`，无配置项。
本仓**禁止 `<repo>/runs` 存在**（L-5 缺陷的回归守卫，约十处断言含 conftest 的
suite-wide fixture，且在 R5 事故后才加进监视表）。实测：建了它，
`test_s0_runner` 从 213/213 掉到 211/213。

现状：本项目按偏离运行，packet 存 `ops/packets/`，偏离记在
`ops/RUNTIME_DEVIATION_PACKET_SAVE_DIR.md`，PACKET_ISSUANCE 已按同 review_id
追加 correction 记录新 `saved_path`，验证器判 `no rejection`。

### 可裁选项

- **A：改 runtime**，把 `_SAVE_DIR` 变成可配置项。**根治**，且惠及每个未来项目。
- **B：维持按项目偏离**（现状）。便宜，但每个新项目都要各自踩一次、各自发现一次。
- **C：改本仓**，让 `<repo>/runs` 可以存在。**builder 明确反对**：那是为一个真实
  缺陷建立、并在一次真实事故后加固的回归守卫，为迁就一个硬编码常量削弱它，方向
  是反的。

### 裁定之后还缺什么

**若裁 A：builder 不会直接动手。** `qros-runtime` 是**已认证的、operational 的**
运行时（902 测试 ＋ 22 conformance ＋ 25 render-checks，15 轮 Sol 认证弧），且
**在本项目仓库之外**。改它需要它自己的认证轮次，并影响所有已注册项目。这超出
「本项目 builder」的席位范围，需 Aaron 另开一件事。

---

## 呈交给 Fable 的形状

```
ITEM_ID=D-1 | D-2 | D-3 | D-4
RULING=<所选项，或你构造并论证的新选项>
CONDITIONS=<裁定安全成立所需的条件>
FALSIFIER=<什么观察会显示这条裁定错了>
COLLATERAL=<需修订哪些已批准工件，逐文件逐符号；以及哪些不得触碰>
```

**四项一次裁完**，形式沿用 `ops/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`。

## 常设禁令（对 Fable 同样在force）

- **只读。** 不修改任何文件，不打补丁；裁定是散文加精确的文件/符号引用。
- 不读真实 Development 数据；不执行 supplement／MC／S0／策略；
  不在 `C:\Users\Aaron\quant-data\` 下创建目录（两个 `supplements\` 子树
  必须保持不存在）。
- 不追加 registry／exposure 事件；不签发任何授权；不填 P2 占位符。
- 不改样本／标签／NA 政策／成本／Primary／Oracle／feasibility／运行定义。
- **禁区**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome` 全部
  路径，**尤其是 `ops/MC_TO_STRATEGY_MASTER_PLAN.md`**——它既是 outcome-carrying
  又是恢复锚，D-2 正是关于它。**读它就会重演 D-1 的暴露。** 本包已把 D-2 所需
  的全部事实写在上面，不需要打开它。
