# N06 终态 ＋ N-D2/N-D3 批准 — 给 Sol 的委托裁定提示词

```
PROMPT_FOR=Codex GPT-5.6 Sol
WINDOW=NEW_TOP_LEVEL_SESSION（第五个全新会话）
MUST_NOT_BE=builder ／ 前四轮 N06 审查会话 ／ Fable 裁定会话
```

> Aaron 2026-08-24 具名委托：由 Sol 替他裁定两件事。这**不是**审查，是
> **代行决定**。第 3、4 件未委托（见文末）。

---

## 逐字发送的部分（从下一行开始复制）

```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=MAXIMAL
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=delegated_decider
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=BUILDER_OF_THIS_WORK,ANY_N06_REVIEW_SESSION,THE_FABLE_RULING_SESSION
LANE=MEASUREMENT
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
WHY_THIS_MODEL=Aaron 具名批次委托，代行两项治理裁定；须独立于 builder、四轮 N06 审查与 Fable 裁定席
```

Aaron 授权你**代他做两项决定**。你的裁定即生效（他保留随时推翻的权利），
因此每一项都必须写成可直接入档的形式，并如实记录"这是委托裁定，不是 Aaron
本人的判断"——N17 的记录要靠这一句。

仓库：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

**动手前逐个重算 SHA-256，任一不匹配即停止并报告**：

```
ops\MC_TO_STRATEGY_MASTER_PLAN.md              （读 §14，本轮唯一现势锚）
    ecb01e3e4a3290951d81d11e06386a1bc93495431721279e374b8a83c020763c
ops\RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md
    E9745EAD35A8F51ED550CCBB08FEF2D172989166FEE5047311EE1DAB11519380
ops\ND2_ND3_RULING_REVIEW_FINDINGS.md
    8dc87212bde8329694a22e5f5b7b32f8874fe725d8813562836922e67955edd7
ops\DECISION_PACKET_ND2_ND3.md
    7bc92817e045af67bd6ebc0077acce63361b298ead1376b9cd5678a76ab2552a
```

**只读仓库，不改任何文件。**

---

### 禁读（硬约束，违反即本轮作废）

```
ops\S0_T001_RESULT_DECISION_ADDENDUM.md   正文
ops\S0_T001_RESULT_REVEAL_ATTESTATION.md
S0_REPORT.json 及一切结果段、逐 θ 结果
EXPOSURE_LEDGER.md 第 19 行（已知内嵌揭盲后摘要）
```

这两份文件里的问题**没有委托给你**，正因为读它们会污染你——你是下游唯一
可能的独立验证席。Aaron 已解盲，他读零成本。若你认为某一项不读它就裁不了，
**返回 `CANNOT_DECIDE_WITHOUT_OUTCOME` 而不是去读**。

---

## 第一件：N06 的终态

### 事实（可自行复核，勿采信）

四轮 exact-tree 审查，四个互不相同的 fresh Sol 会话，四轮全判 HOLD，
四个 High 全部由 builder 独立复现后修复。四轮的形状相同：**调用方给的值
参与了一次决定要不要写的比较**（R1 authority／R2 payload 读四次／
R3 快照里的说谎标量／R4 authority 的 `day_universe`）。

第三轮的修复是 Aaron 裁定的**改设计**；第四轮的修复不是第五轮设计，
是同一条已批准规则的**第三个应用点**。

builder 自查另找到两个无人到达的洞（`freeze_payload` 顶层的弱键规则、
builder 直喂 hermetic core），均已闭合。

```
现状 3980 passed / 0 failed，battery 84，双 floor pin 3980
残留 F1/F2 exact-type capability bypass —— `__new__` + `object.__setattr__`
     在 Python 层面不可根治
Aaron 2026-08-24：不再审 N06
```

### 问题

§4 DAG 写 **N-D2 依赖 N06**，§13.5 写「只有 N06 PASS 之后才进入 N-D2」。
不再审查 ⇒ N06 **永远不会以 PASS 结束**。终态未裁之前，进入 N-D2 是未记录的
绕过。

### 你要裁的

从下列三条中选一条，或提出第四条并给理由：

- **(a)** 宣布 N06 以「**接受＋披露残留**」终结——四轮 High 全闭合，
  F1/F2 载入 N17 披露；
- **(b)** 修改 DAG 依赖，把 N-D2 从 N06 解绑，理由入档；
- **(c)** 维持 HOLD 且**不**进入 N-D2。

裁 (a) 必须同时给出：**F1/F2 残留在 N17 的披露措辞**，以及它在 N09 真实执行
之前是否需要任何额外缓解。

### 你应当先自己判断的

四轮 High 是否**真的**全部闭合——你有权重跑攻击、重读修复。builder 的自陈
不构成闭合证明。若你复现出任何一个仍然可用，那答案就不是 (a)。

---

## 第二件：Fable 的 32 项裁定是否批准

`ops\RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md` 是 Fable 5 按 Aaron 委托
出的完整裁定提案（32 项：M15/D2/O4/E3/G8，零 `CANNOT_DECIDE`）。
`ops\ND2_ND3_RULING_REVIEW_FINDINGS.md` 是 builder 的验收：八条承重事实断言
逐条核过全对，另提**两处须改（数值均不动）**：

1. **M2** 的 5.0 日/月自称"从平台算术导出、零自由参数"，但
   `gate1/platform_params.yaml:80-81` 显示平台**没有日历月窗口**
   （`qualifying_days_required: 5`，每次批准 payout 后重置重计），达标日跨月
   累积合法。故 5.0 是**设定**不是导出，须与 M1/M3 同列为从零设定。
2. **D1** 的理由「E2 组合本就不可 GO」与 Fable 自己的 **M13** 冲突——M13 裁定
   β 的替代集合就是那两个 E2 组合，而 §10.4 边界区处理明写 β 适用主门槛并可
   判 GO。结论仍成立（`over_budget` 仅见 `consumer.py:1471`，不进任何门），
   但该句须删。

### 你要裁的

- 整体批准 / 整体批准并采纳上述两处修正 / 逐项修改（逐项改须显式处理
  Fable 附录一的 17 条依赖，尤其 **M14=NO ⇒ M15 与 G7 连动失效**）；
- 是否采纳 builder 的建议：给 **E2 补一条聚合绊线**（现绊线是单次运行
  >280 min，而 M10 的倍数是 ×18，聚合 custody 15–42 小时不在任何绊线视野内）；
- **M2 的定性**：同意改称"设定"，还是你认为 builder 的反驳不成立（若后者，
  请给出平台层面的窗口依据）。

### 你应当自己复核的（不要采信 builder）

- 那八条承重断言（FREEZE_LOG 冻结时点、S0 §9 块长 5/21、`consumer.py:1441`
  的 offered 语义、`gate2_cost_guard`、`GridRepeatPolicy.max_doublings`、
  `k_per_seed=200`、附录 A 两张区域图、θ 0.5/0.3）；
- 包 §2.1 的复核结论（三个候选阈值在仓库内无出处）；
- **M12 把 α 的检查对象定为块长-21 重算，代价是 ≈2× 主通道认知层算力**——
  这是全部 32 项里最贵的一条，请单独判断它值不值。

---

## 三、你不得做的

- 不读上面禁读清单里的任何内容
- 不授权任何真实运行、不追加 registry／exposure 事件、不创建任何目录
- 不执行 supplement／MC、不读真实 Development 数据
- 不改冻结文本的**数字**
- 不碰 N00 缺失的五份 Round-4 文档（不属你）
- 不决定 Stage I vs discretionary Tier-1、不推断 LANE／STAGE
- 不修仓库任何文件（read-only）

## 四、产出

每件一块，可直接入档：

```
ITEM=N06_DISPOSITION | ND2_ND3_RATIFICATION
DECISION=<可执行，不留占位符>
理由=<机制上的>
备选及为何不选=
我自己复现的=  ／  builder 自报未复核的=
DELEGATED=YES（Aaron 2026-08-24 具名委托；这不是 Aaron 本人的判断）
```

末尾附**独立性声明**，按 context／authorship／model-diversity／empirical 四维
分述，并明确一点：**前四轮 N06 审查都是 Sol**，因此你对 N06 的裁定
**不具备模型族多样性**——只有会话独立性。请如实写出来，不要淡化。

---

## 未委托给你的两件（不要碰，也不要建议如何碰）

```
3. 读 ops\S0_T001_RESULT_DECISION_ADDENDUM.md:26 与 EXPOSURE_LEDGER:19 并裁定
   —— 含揭盲 outcome，读即污染；归 Aaron
4. 找回或宣告丢失 N00 的五份 Round-4 文档 —— 恢复须 Aaron
```
