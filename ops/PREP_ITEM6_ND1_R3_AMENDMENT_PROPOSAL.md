# ND1 profile R3 修订提案 —— 悬空 P3 的闭合，与租约纪律

```
RECORD_TYPE=PROPOSAL_FOR_RATIFICATION
ITEM=6 ＋ 8（dec-eight-open-2026-08-26），按 Fable 指示捆绑
STATUS=提案，**第一步／共三步**。不释放任何门，不授权任何写入，不修改任何已批准工件。
PROPOSED_BY=Opus 5 main agent（builder seat）
AMENDS=ND1_RECOMMENDED_PROFILE_R2
       sha256 a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d
       （2026-08-23 已批准；记录 ops/DECISION_PACKET_N00_AND_ND1.md:1672）
NEXT=fresh Sol 复核 → Aaron ratify
OUTCOME_CLEAN=是
```

> **本提案不是修订本身。** 它是三步流程的第一步。在 Aaron ratify 之前，
> `src/itsf/mc/supplement_contract.py` 的 `EVENTS` 表**一字不改**。

---

## 一、缺口是两个，不是一个

### 1.1 词表缺口（Fable 发现，builder 复现）

运行器在 P3 之后硬崩溃，链尾悬在 P3。而：

```
P3 的合法后继 = ("P4", "A1", "F2")   ——三者 actor 全是 main agent (mc_ds_runner)
F3 的前驱     = ("P1","P2","F1","F2","F2v","AX")   ——不含 P3
```

运行器已死，那三条后继按第 4／5 项的 actor 绑定**没有人能合法写**；而唯一的
治理性终点 F3 **接不到 P3 上**。**所以悬空 P3 在现行图上无合法闭合路径。**

### 1.2 接线缺口（builder 实测，两位复审席都没点名）

**检测逻辑存在且正确，但生产代码从不调用它。** 实测：

```
链 = (P1, P2, P3, P4, P5)   refusal=None  problem=''  terminal='P5'  closed=True
链 = (P1, P2, P3)           refusal=None  problem=''  terminal=''    closed=False
                            assert_chain_closed -> SupplementRunnerError:
                                                   chain_not_closed: P3
```

- `assert_chain_closed`（`supplement_runner.py:739`）**判得对**，但全仓检索：
  **生产代码零调用**，只有测试（7 处）与 `supplement_registry.py:241` 的一句
  docstring。
- `ChainResolution.closed`（`supplement_registry.py:245`）**生产代码零读取**。
- A_PRECHECK 的 `registry_chain_resolvable` 门
  （`supplement_runner.py:279`）**只查 `chain.problem`**，而悬空链的
  `problem` 是空串。

**结论：悬空 P3 今天会通过 A_PRECHECK。** 不是因为没人写过检查，是因为写好的
检查没接到门上。

**这一半原以为可以独立于修订先落地——实测推翻了，见 §四.A。** 闭合检查不能直接
接上去：它会拒掉 `('P1','P2')`，而那是开跑前的正常态。真正要定的是「遗弃」谓词，
那是设计问题，归复核。

## 二、Part A —— 提议的 profile 修订（需 ratify）

### A.1 新增事件 CR1

```python
EventSpec("CR1", "SUPPLEMENT_RUN_CRASH_RESOLVED", NUMBERED, ACTOR_MAIN_AGENT,
          ("supplement_id", "dangling_event", "incident_id",
           "crash_evidence_summary", "recovery_authorization_doc",
           "registry_intact_verification"),
          ("P3",), ("F3",), False, incident_required=True)
```

逐字段理由：

| 字段／位 | 取值 | 为什么 |
|---|---|---|
| `row_class` | `NUMBERED` | 治理动作，与 A2／AX／F3 同类，不是运行器的即时事件 |
| `actor` | `ACTOR_MAIN_AGENT` | 按第 4 项：actor 是复合「权限 (工具)」token 且**双向绑定**——执行追加的确实是主代理，不带工具括号 |
| `predecessors` | `("P3",)` | 唯一的悬空点。**不要**扩到 P4／A1：那些有各自的闭合路径 |
| `successors` | `("F3",)` | 崩溃后的补给必须走取代流程（F3 → T1 起新 supplement_id） |
| `terminal` | `False` | CR1 是裁定，不是终点 |
| `incident_required` | `True` | 崩溃必然有事故号 |
| `recovery_authorization_doc` | 必填 | **复用 A2 的字段模式**（已实测 A2 required_fields 含此字段） |

**builder 已实测（省 Sol 一步）**：按真实 `EventSpec` 签名构造上面这条规格
**能通过**——8 个位置参数 ＋ `incident_required=True` 与
`__init__(short_id, token, row_class, actor, required_fields, predecessors,
successors, terminal, incident_required=False)` 吻合；`short_id="CR1"`
**未被占用**；`token="SUPPLEMENT_RUN_CRASH_RESOLVED"` **与既有 token 不冲突**
（全表唯一的重复是 `SUPPLEMENT_PROPOSED`，T1 复用 P1 的词，那是 §D.3.2 的刻意设计）。
**这只证明它构造得出来，不证明它是对的设计。**

### A.2 `NON_TERMINAL_TRAPS` 增加 `"CR1"`

```python
NON_TERMINAL_TRAPS = ("A1", "AX", "CR1")     # 现为 ("A1", "AX")
```

**理由（builder 提议，Fable 未指定，请 Sol 重点看这条）**：CR1 与 AX 形状同构
——非终态、由失败点接入、后继唯一指向 F3。`assert_chain_closed` 对 trap 报
`chain_stops_at_non_terminal`（一条**说得清**的消息），对非 trap 只报
`chain_not_closed`。停在 CR1 应当得到前者。

**同时须改**：`assert_chain_closed` 里那句写死的三元表达式
（`supplement_runner.py:748-749`）现在只认 A1／AX，加 CR1 会让它给出错误提示。
**这是修订的建造义务，不是可选项。**

### A.3 `FORBIDDEN_EDGES` 增加两条

```python
("CR1", "P4"),    # 崩溃裁定永不复活运行
("CR1", "P5"),    # 更不能直接跳到独立验证
```

两者都不在 CR1 的 `successors` 里，所以已经非法；**但 `FORBIDDEN_EDGES` 是
「数据化的显式拒绝清单」，有测试逐条断言解析器拒绝它们**。写进去让「永不复活」
成为被测断言，而不是靠 successors 恰好没写。

### A.4 明确**不动**的

- P3／P4／A1／F1／F2／A2／AX／F3／P5／T1 的任何字段，含 actor（第 5 项裁定：保留）。
- `TERMINAL_SHORT_IDS = ("P5", "F3")`。
- `plan_failure_event` 的 `ACTOR_RUNNER` 硬编码。
- `scripts/s0_real_run.py` 的 S0 先例代码。
- `ROW_CELLS` 六格契约（第 4 项裁定：不加 executor 字段）。

## 三、Part B —— 租约纪律（第 8 项，**不改 profile**）

租约今天不存在（全仓检索零命中）。本部分是**对未来租约设计的约束**，随修订
一并入记录，**不构成任何 profile 变更**：

1. **回收 = 一次恢复写入 = 逐 incident 经 Aaron 明示授权。** 永不自动。
2. **fail-closed 不得沦为 fail-silent**：楔死的租约必须在每次 bootstrap
   大声可见——点名持有者、楔死时长、裁定程序。
3. **裁定程序须文档化到「一行决策即可解除」**。否则楔死催生绕行文化，而绕行
   文化才是不变量真正的死法。
4. FALSIFIER（继承 Fable）：一个季度 ≥3 次陈旧租约裁定且每次同形零信息 ⇒
   可重开一条**窄**自动路径（仅当第 6 项的持久崩溃标记证明持有者已死），
   **该重开归 Aaron**。

## 四、建造义务（ratify 之后才做）

### A. 接线缺口 —— **不是接线，是要先定谓词（builder 自证前一版写错了）**

> **本节第一版写的是「把 `assert_chain_closed` 接到门上，最小改动」。那是错的，
> 我在动手实施前实测推翻了它。逐字保留这次更正，因为错的那版差一点就作为
> 「低风险接线」发出去了。**

实测 `assert_chain_closed` 对各前缀的判定：

```
('P1',)                     -> 拒绝: chain_not_closed: P1
('P1','P2')                 -> 拒绝: chain_not_closed: P2
('P1','P2','P3')            -> 拒绝: chain_not_closed: P3
('P1','P2','P3','P4')       -> 拒绝: chain_not_closed: P4
('P1','P2','P3','P4','P5')  -> 通过
```

**`('P1','P2')` 正是任何合法运行开跑之前的状态。** 把闭合检查接到 A_PRECHECK
会拒掉**每一次正当运行**。`ChainResolution.closed` 同理——它对 P2 链与悬空 P3
链**都**是 `False`，**分辨不了这两者**。

**所以判据不能是「是否闭合」，必须是「是否被遗弃」。** 提议谓词：

```
ABANDONED(chain) ==  last ∈ {"P3"} ∪ NON_TERMINAL_TRAPS
```

理由（每个事件的后继实测如下，谓词从中推出）：

| last | 含义 | 可否在此状态下开新工作 |
|---|---|---|
| `P1` / `P2` | 已提议／已授权，**尚未开跑** | **可以**——这就是开跑前的正常态 |
| `F1` | 开跑前尝试失败，`successors=('P3','P2S','F3')` | **可以**——重试是设计内的 |
| **`P3`** | **已开跑、已消耗暴露，无任何终止事件** | **不可以 ⇒ 遗弃** |
| **`A1` / `AX`** | 非终态陷阱（现行 `NON_TERMINAL_TRAPS`） | **不可以 ⇒ 须先裁定** |
| `P4` | 已封存，待独立验证 | **存疑，见下** |
| `F2` | 开跑后失败，`successors=('F3',)` | 存疑，见下 |
| `P5` / `F3` | 已闭合 | 不适用（该 id 已终结） |

**两处 builder 定不了、请 Sol 裁的**：

1. **`P4`**：链已封存待 P5 验证。它不是「遗弃」，但也不该允许同一 supplement_id
   开新运行。这是「遗弃」之外的**第二种拒绝理由**，还是根本不该由这个门管？
2. **`F2`**：开跑后失败且只能走向 F3。同一 id 还能再跑吗？（我的判断：不能，
   但 `F2` 不在 `NON_TERMINAL_TRAPS` 里，所以现行词表没这么说。）

**为什么仍值得先落地**：谓词一旦定下，实现是加性 fail-closed，且**今天落地
可观测行为零变化**——`run_supplement_production` 本就 gate-first 拒绝，没有 MC
生产路径能走到这个门。但**在谓词被复核之前，builder 不实施**：一个把每次正当
运行都拒掉的门，比没有门更糟。

### B. 修订本体（须 ratify）

1. `EVENTS` 加 CR1；`NON_TERMINAL_TRAPS` 加 CR1；`FORBIDDEN_EDGES` 加两条。
2. 修 `assert_chain_closed:748-749` 的写死提示语，使其覆盖 CR1。
3. bootstrap 悬链拒绝：链尾为 P3 且无后继 ⇒ 拒绝**该 supplement_id 的一切新
   工作**，并拒绝 **MC 生产入口整体**，直至裁定。
4. **每一条都要变异证红**（Fable 条件 1）。
5. 悬空 A1 **不需要新机制**——A1 的后继 A2／AX 本就是 main agent 事件，
   现行词表已可闭合。

## 五、FALSIFIER

- **（继承 Fable）** 真实事故显示悬空 P3 的拒绝以裁定无法快速解除的方式楔死了
  **无关的** supplement_id ⇒ 拒绝范围（per-id vs 全局）须重设计。本提案有意
  取偏楔死的一侧（per-id ＋ MC 入口整体 fail-closed），**此偏向可由 Aaron 回调**。
- **（builder 追加）** 若 §四.A 的谓词落地后，任何**既有**测试变红，说明现行
  套件里存在依赖「被遗弃的链能通过门」的用例 —— 那本身是要报告的发现，
  **不得靠放宽新检查来消音**。
- **（builder 追加，来自本节的自我更正）** 若复核认为 `ABANDONED` 谓词仍然过宽
  或过窄，**以拒得多为安全侧**：多拒一次要 Aaron 裁一句，少拒一次可能放行第二次
  消耗暴露的运行。

## 六、请 fresh Sol 重点看的

1. **§二.A.2 是 builder 的提议，不是 Fable 裁定的一部分**：CR1 该不该进
   `NON_TERMINAL_TRAPS`？我按与 AX 的形状同构推的。
2. **§一.2 的接线缺口**请独立复核——我的证据是实测输出，但「生产零调用」是
   一次全仓检索的结论，请自行确认口径。
2b. **§四.A 的 `ABANDONED` 谓词**——尤其 `P4` 与 `F2` 两栏我明说定不了。
   这一节的第一版是错的（写成「把闭合检查接上去」，而闭合检查会拒掉 `('P1','P2')`
   即开跑前的正常态），更正逐字保留在原处。**请当作最可能还藏着错的一节看。**
3. `predecessors=("P3",)` 是否过窄：P4 之后、A1 之后的崩溃走什么路？
   （我的判断：P4 之后链已封存，A1 有 A2／AX，都不悬空——请证伪。）
4. CR1 → F3 强制走取代流程，是否对「崩溃后只想重跑一次」的场景过重。

## 七、常设禁令（对复审席位同样在 force）

- **只读。** 不改文件、不打补丁。
- **不得在本仓做任何检索**（S1(b)）；需要路径就列出来，由工作会话经
  `PULL_PROTOCOL` 提供字节。
- 禁区权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`，
  **每一条路径都当作关闭**。
- 零真实数据读取；零执行；不在 `C:\Users\Aaron\quant-data\` 下创建目录；
  不追加 registry／台账事件；不签发授权；不填 P2 占位符。
- **PASS 不授权任何写入**：修订本体须 Aaron ratify 之后才动 `EVENTS` 表。
