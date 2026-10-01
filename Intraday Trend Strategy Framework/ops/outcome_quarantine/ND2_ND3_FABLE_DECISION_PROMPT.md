# N-D2＋N-D3 合并裁定 — 给 Fable 的提示词

```
PROMPT_FOR=Fable 5
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=本包作者（Opus builder 会话）／任何 N06 审查会话
STATUS=READY（包已落盘，哈希已填）
```

> 包已落盘于 commit `cb8bef39f358fbeaeef982c3be32d0bc8f5f3e8e`，32 项。
> 包由**内容哈希**钉定，不由 HEAD 钉定——后续 commit 不影响它，只要重算的
> SHA256 匹配即可开工。

---

## 逐字发送的部分（从下一行开始复制）

```ini
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=MAXIMAL
RECOMMENDED_EFFORT=max
EXECUTION_MODE=STANDARD
ROLE=delegated_decider
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=BUILDER_OF_THIS_WORK,AUTHOR_OF_THIS_PACKET,ANY_N06_REVIEW_SESSION
LANE=MEASUREMENT
OUTCOME_EXPOSED=AGGREGATE
PREREG_SEALED=YES
SUBAGENT_OR_WORKFLOW_BUDGET=3 workflows，单波最多 3，read-only 起步，不递归
WHY_THIS_MODEL=对抗审计席定门槛：最不倾向放水的席位来设及格线；且必须独立于 builder
```

你被 Aaron 授权，对 N-D2＋N-D3 合并决策包中的全部条目**给出完整裁定方案**。

**先读包的 §2。** 那里有三个发现会改变你对本任务的理解：三个候选阈值在仓库
里没有出处（你是从零设定，不是追认）；有一份揭盲后文档已就 feasibility 作出
断言而**你我都不得读**（归 Aaron）；frequency 门在定义上无法对 S0 无知。

**你的裁定是给 Aaron 的一次性批准对象，不自动生效。** 他会整体批准或逐项改。
因此每一项都必须可独立判读：他不应该需要回头读上下文才能理解某一项在裁什么。

仓库：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
包：`ops\DECISION_PACKET_ND2_ND3.md`
SHA256 `7bc92817e045af67bd6ebc0077acce63361b298ead1376b9cd5678a76ab2552a`
落盘 commit `cb8bef39f358fbeaeef982c3be32d0bc8f5f3e8e`（32 项：M15/D2/O4/E3/G8）

动手前重算包的 SHA256，不匹配即停止并报告。**只读仓库，不改任何文件。**

---

### 一、污染防火墙（本提示词最重要的一条）

S0-T001 **已经揭盲**（`verdict=INCONCLUSIVE_PENDING_MC`，researcher exposure=1575）。
你现在定的每一个门槛，都是在 S0 结果已经存在的世界里定的。这一点无法消除，
只能**切开输入并如实申报**。

**允许读**：冻结设计文本（MC §3／§4.4／§6、S0 §10.5 的频率输出定义）、
本包正文、生产代码、测试。

**禁止读**：S0 已揭盲的 outcome 值——Checkpoint-0 判定统计量的实际数值、
逐 θ 结果、`S0_REPORT.json` 的结果段、任何能让你反推"某个门槛会不会被通过"
的封存数字。

**每一项裁定必须申报** `CONSULTED_S0=[...]`：你为这一项实际查阅了哪些 S0 量。
空集就写 `NONE`。

如果某一项**不看禁止内容就无法裁定**，不要去看——返回
`RULING=CANNOT_DECIDE_WITHOUT_OUTCOME` 并说明缺什么。那一项归 Aaron。
**这不是失败，这是本轮最有价值的输出之一。**

### 二、偏向方向（明确要求，不是风格建议）

不确定时，选**让 GO 更难**的那个裁法，并在该项写明 `MAKES_GO_HARDER=YES`。

理由：门槛定严导致 STOP，事后可以论证、可以重设计；门槛定松导致 GO，
事后不可挽回——钱已经进去了。两种错误的代价不对称。

但**不要为了保守而保守**：如果某项严格化没有机制上的理由，说清楚它中性，
写 `MAKES_GO_HARDER=NO` 并给理由。虚假的严格和虚假的宽松一样坏。

### 三、四个层级（包正文已按此分组，裁定强度按级递减）

| 层 | 内容 | 你的裁定强度 |
|---|---|---|
| **M — 方法，直接决定 GO/STOP** | feasibility 三门、K 收敛、fixed-world、α／β 的检查对象与门槛 | 最高严格度；防火墙全额适用；逐项申报 |
| **D — 冻结文本里的洞** | E2 `over_budget` 谓词、冻结层-1 会计、feasibility 三门的量词 | 每一项必须标 `POST_FREEZE_DEFINITION=YES` |
| **E — 工程事实追认** | mean/SD/SE 的 ULP 级迁移、custody 链 100–140 分钟预算、是否要求生产规模冒烟 | 常规判断即可 |
| **G — 治理词汇** | registry 事件词表、字段、状态转移、失败族、id 不复用、READY 模式复用 | 机械性为主；只需自洽与 fail-closed |

**层 D 是关键**：这三项不是"还没决定"，是**冻结文本本身有洞**——它要求披露
`P(realised_loss > 预算)` 却从未定义 per-day 布尔指哪一个、损失按每合约还是
按仓位、预算按 policy budget 还是 n×anchor。你是在**冻结之后补定义**。
每一条这样的补丁都必须可被 N17 如实披露，所以标记不可省。

### 四、你不得做的

- 不改冻结文本的**数字**（补定义 ≠ 改数值；两者混淆即为重大缺陷）
- 不发明新的策略候选，不碰 N00 缺失的五份 Round-4 文档（不属你）
- 不授权任何运行、不追加 registry／exposure 事件、不创建任何目录
- 不读真实 Development 数据、不执行 supplement／MC
- 不判定 N06、不决定 Stage I vs discretionary Tier-1、不推断 LANE／STAGE
- 不写 `APPROVED` / `EFFECTIVE` / `RATIFIED` —— 你产出的是**提案**
- 不修仓库任何文件（read-only）

### 五、workflow 预算

默认 3 个，单波最多 3 且互不重叠，等一波齐了再合并去重，不递归。
仅在 Critical/High 未决、证据冲突或明显未覆盖的高风险面才开第二波。
上限 6，超过需 Aaron 明确批准。read-only 起步，不做修复。

### 六、输出格式（每项一块，不合并不省略）

```
ITEM_ID=
TIER=M|D|E|G
RULING=<裁定，一句话可执行，不留占位符>
理由=<为什么是这个，机制上的>
备选=<考虑过但不选的，及为何不选>
CONSULTED_S0=[...] | NONE
MAKES_GO_HARDER=YES|NO
POST_FREEZE_DEFINITION=YES|NO
若被裁反=<Aaron 若选另一个，工程与结论上的后果>
```

末尾另附三段：

1. **相互依赖**——哪些项一旦单独改会与其他项矛盾（Aaron 逐项改时最容易踩的坑）
2. **`CANNOT_DECIDE_WITHOUT_OUTCOME` 清单**——连同各自缺什么
3. **独立性声明**——按 context／authorship／model-diversity／empirical 四维分述；
   并明说：本件是**提案**，不是 `PACKET_OUTCOME`，不释放任何 gate transition

### 七、你应当知道的两件事

- **生产规模从未执行过。** 全部逻辑测试在 B=2／M=2。只在 B=1000 或 M=21 才
  显形的问题（浮点累加序、type-7 分位边界、内存耗时）在这个仓库里从未被跑过。
  层 E 里"是否要求一次生产规模冒烟"这一项，请认真裁——它决定 N16 那次真实
  运行是不是同时也是这套代码的首次生产规模执行。
- **冻结发生在设计完成之前。** 层 D 三项就是证据。这不影响你的工作，但影响
  你对"冻结文本说了算"这句话的信任度——遇到冻结文本与生产代码不符，
  报告冲突，不要默认哪一边对。
```

---

*本件为提示词载体，不是 Review Packet v1，不授权任何执行。*
