# ND1 profile R3 修订提案 —— 悬空 P3 的闭合，与租约纪律

```
RECORD_TYPE=PROPOSAL_FOR_RATIFICATION
ITEM=6 ＋ 8（dec-eight-open-2026-08-26），按 Fable 指示捆绑
STATUS=提案，**第一步／共三步**。不释放任何门，不授权任何写入，不修改任何已批准工件。
PROPOSED_BY=Opus 5 main agent（builder seat）
AMENDS=ND1_RECOMMENDED_PROFILE_R2
       sha256 a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d
       批准记录=ops/ND1_PROFILE_RATIFICATION.md §8（Aaron 2026-08-23 逐字「批准 R2」）
       **引用更正**：前一版把批准记录写成 ops/DECISION_PACKET_N00_AND_ND1.md:1672，
       那是错的——该文件第 1 行自陈 NOTHING_HEREIN_IS_APPROVED=YES，它装的是
       profile 正文，不是批准。fresh Sol 判 REJECTED_INCOMPLETE 时点破了这一条。
ROUTE=ops/ND1_PROFILE_RATIFICATION.md §7 的既定修订路径（见 §二.0）
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

> **更正（fresh Sol，2026-08-27，第四次交付的 HOLD）。** 本节前一版的结论写的是
> 「悬空 P3 今天会通过 A_PRECHECK」。**那句是假的**，Sol 指出并经 builder 实测推翻：
>
> ```
> 链 (P1,P2)        live_authorizations = 1
> 链 (P1,P2,P3)     live_authorizations = 0      <- P3 消费掉了那条 live P2
> ```
>
> `_g_live_authorization_unique`（`supplement_runner.py:299`）在零条 live 授权时
> 以 `SupplementRunNotAuthorized` 拒绝。**所以完整的 A_PRECHECK 确实会拒**，
> 只是不经 `registry_chain_resolvable` 那道门。

**修正后的结论，弱得多但为真**：

- **成立**：`assert_chain_closed` 生产零调用、`ChainResolution.closed` 生产零读取、
  `registry_chain_resolvable` 只查 `problem`（悬空链为空串）。
- **不成立**：「悬空 P3 会通过 A_PRECHECK」。
- **真正的残留价值**：拒绝**存在但诊断错误**——操作者被告知的是「没有 live 授权」，
  而真相是「有一次运行被遗弃了」。**一条把崩溃说成未授权的拒绝信息，会把人引向
  重发授权，而不是引向事故裁定。**

**这一半原以为可以独立于修订先落地——实测推翻了，见 §四.A。** 闭合检查不能直接
接上去：它会拒掉 `('P1','P2')`，而那是开跑前的正常态。真正要定的是「遗弃」谓词，
那是设计问题，归复核。

## 二.0 **修订必须走 §7 的既定路径 —— 前一版没走**

`ops/ND1_PROFILE_RATIFICATION.md` §7 逐字：

```
只能走决策包 §D.10.3：Aaron 指出要改什么 → builder 产出
ND1_RECOMMENDED_PROFILE_R2 → 跨字段检查重跑 → 新 canonical SHA-256 →
新的 doc-only commit → Aaron 批准 R2 的 id + hash + 精确 doc HEAD。
不得从参照清单里挑值直接生效，也不得就地改写本记录。
```

**前一版提案的结构性错误**：它提的是「ratify 之后改
`src/itsf/mc/supplement_contract.py` 的 `EVENTS` 表」。**代码是批准之后的转录，
不是批准的对象。** 要批的是一份 **R3 canonical profile 字节块**及其 SHA-256。
本节即改正。

**builder 已复算并证明拿到的是对的字节**：决策包第 1613/1665 行之间的 51 行，
按块内自述口径规范化（`BEGIN` 与 `END` 之间的行，不含这两行，LF，UTF-8，逐行原样），
重算得 `a3d40b7ce218…8741d`，**与已批准值逐字节相等**。

## 二.1 R3 候选正文（correction-only，由 R2 字节构造）

> **本节为第二版。** 第一版被 fresh Sol 判 HOLD，`STRONGEST_OBJECTION` 是
> **CR1→F3 单向声明**——见 §二.2(a)。第一版的 `d26cbc3e…` 作废。

```
BEGIN_ND1_RECOMMENDED_PROFILE_R3
PROFILE_ID=ND1_RECOMMENDED_PROFILE_R3
PROFILE_FIELD_PREFIX=RECOMMENDED_（本块内每一行都是提案值；块内不存在任何已批准值）
PROFILE_STATUS=PROPOSED_NOT_EFFECTIVE
RECOMMENDED_GRAMMAR_FORMAT_RULES=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P2=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P2S=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P3=ADOPT_AS_CORRECTED_BY_R2_THEN_R3
RECOMMENDED_P3_PERMITTED_PREDECESSOR=P2|F1
RECOMMENDED_P3_PERMITTED_SUCCESSOR=P4|A1|F2|CR1
RECOMMENDED_GRAMMAR_P4=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_P5=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_A1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_A2=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_AX=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F2=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F2V=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_F3=ADOPT_AS_CORRECTED_BY_R3
RECOMMENDED_F3_PERMITTED_PREDECESSOR=P1|P2|F1|F2|F2v|AX|CR1
RECOMMENDED_F3_PERMITTED_SUCCESSOR=T1
RECOMMENDED_GRAMMAR_T1=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_CR1=ADOPT_AS_INTRODUCED_BY_R3
RECOMMENDED_CR1_PERMITTED_PREDECESSOR=P3
RECOMMENDED_CR1_PERMITTED_SUCCESSOR=F3
RECOMMENDED_CR1_DANGLING_EVENT_DOMAIN=P3
RECOMMENDED_CR1_REGISTRY_INTACT_VERIFICATION_DOMAIN=64HEX_SHA256_OF_REGISTRY_AT_RESOLUTION
RECOMMENDED_GRAMMAR_STATE_MACHINE=ADOPT_AS_WRITTEN
RECOMMENDED_GRAMMAR_PARSER_FAIL_CLOSED_RULES=ADOPT_AS_WRITTEN
RECOMMENDED_F1_GATE_NAME_ENUM=DEFER_TO_N04
RECOMMENDED_ND1_PARSER_MALFORMED_ROW_POLICY=B_REFUSE
RECOMMENDED_ND1_SUPPLEMENT_SEQUENCE_NAMESPACE=GLOBAL
RECOMMENDED_ND1_PRESTART_COMMIT_CHANGE_REAUTH=YES
RECOMMENDED_ND1_POSTSTART_FAILURE_NEW_ID=YES
RECOMMENDED_ND1_SUPERSEDE_TARGET=2_SUPERSEDES_SUPPLEMENT_ID_ITSELF
RECOMMENDED_ND1_ARCHIVE_FAILURE_POLICY=A
RECOMMENDED_ND1_FORMAL_TRIAL=NO
RECOMMENDED_ND1_STARTED_CONSUMES_GLOBAL_RUN_SEQUENCE=NO
RECOMMENDED_ND1_STARTED_CONSUMES_EXPOSURE_SLOT=NO
RECOMMENDED_ND1_SUPPLEMENT_LEDGER_CREATE=YES
RECOMMENDED_ND1_EXPOSURE_ROW_QUANTITY_ZERO=YES
RECOMMENDED_ND1_STRUCTURAL_ACCESS_CHARACTERISATION=STRUCTURAL_LABEL_NOT_OUTCOME
RECOMMENDED_ND1_PARTIAL_RECOVERY_RULE=MODIFY
RECOMMENDED_ND1_PARTIAL_MODIFY_TEXT=BRANCH_E_RENAME_TO_.partial.divergent.<incident_id>;BRANCH_C_RENAME_THEN_ALLOW_RETRY
RECOMMENDED_ND1_OUTPUT_ROOT_OPTION=A
RECOMMENDED_ND1_SUPPLEMENT_DIRECTORY_NAME=2_ID_UNDERSCORE_UTC
RECOMMENDED_ND1_FUTURE_DIRECTORY_POLICY=REUSE_EXISTING_ROOTS_WITH_supplements_SUBTREE
RECOMMENDED_ND1_WRITE_PROBE_AUTHORIZED=NO
RECOMMENDED_ND1_SUPPLEMENT_EXECUTION_AUTHORIZED=NO
RECOMMENDED_ND1_DISCLOSURE_CONTENT=ADOPT_SEVEN_POINTS_AS_WRITTEN
RECOMMENDED_ND1_DISCLOSURE_PLACEMENTS=ADOPT_FOUR_PLACEMENTS_AS_WRITTEN
RECOMMENDED_ND1_DISCLOSURE_WORDING_BY_AARON=YES
RECOMMENDED_ND1_EXECUTION_SENTENCE_BINDS=supplement_id+40hex_commit+output_root
RECOMMENDED_ND1_EXECUTION_SENTENCE_ONE_RUN_ONLY=YES
RECOMMENDED_ND1_EXECUTION_SENTENCE_EXPIRES_ON_COMMIT_CHANGE=YES
PROFILE_CONTAINS_NO_EXECUTION_AUTHORIZATION=YES
PROFILE_CREATES_NO_DIRECTORY=YES
PROFILE_APPENDS_NO_REGISTRY_OR_EXPOSURE_EVENT=YES
END_ND1_RECOMMENDED_PROFILE_R3
```

```
CANONICAL_BYTES=BEGIN 与 END 两行之间的行（不含这两行），LF 结尾，UTF-8，逐行原样
R3_CANONICAL_SHA256=12105e98438c6a547d2264f195b59f0bb5e2831342c536a7aa87e0cfc9a8873c
```

**correction-only 的机械证明（沿 §D.11.3 的形式）**：

```
R2_LINES=51
R3_LINES=58
INHERITED_VERBATIM=47 / 58
EDITS=11
  changed  PROFILE_ID=..._R2 -> ..._R3
  changed  RECOMMENDED_GRAMMAR_P3=ADOPT_AS_CORRECTED_BY_R2
        -> RECOMMENDED_GRAMMAR_P3=ADOPT_AS_CORRECTED_BY_R2_THEN_R3
  changed  RECOMMENDED_P3_PERMITTED_SUCCESSOR=P4|A1|F2 -> P4|A1|F2|CR1
  changed  RECOMMENDED_GRAMMAR_F3=ADOPT_AS_WRITTEN -> ADOPT_AS_CORRECTED_BY_R3
  added    RECOMMENDED_F3_PERMITTED_PREDECESSOR=P1|P2|F1|F2|F2v|AX|CR1
  added    RECOMMENDED_F3_PERMITTED_SUCCESSOR=T1
  added    RECOMMENDED_GRAMMAR_CR1=ADOPT_AS_INTRODUCED_BY_R3
  added    RECOMMENDED_CR1_PERMITTED_PREDECESSOR=P3
  added    RECOMMENDED_CR1_PERMITTED_SUCCESSOR=F3
  added    RECOMMENDED_CR1_DANGLING_EVENT_DOMAIN=P3
  added    RECOMMENDED_CR1_REGISTRY_INTACT_VERIFICATION_DOMAIN=64HEX_SHA256_OF_REGISTRY_AT_RESOLUTION
```

### 二.2 三处升级 —— **(a) 是 Sol 判 HOLD 的直接原因**

**(a) CR1→F3 必须双向声明，第一版漏了，而且我还明写「F3 不动」。**

`tests/test_mc_supplement_integration.py:208`
`test_predecessor_and_successor_declarations_agree_with_each_other` **强制每条边
双向声明**。第一版 R3 给了 CR1 `successors=("F3",)` 却没把 CR1 加进 F3 的
predecessors，而 §二.A.4 还把 F3 列进「明确不动的」——**提案自相矛盾，ratify 后
必然打红那条不变量**。

**本版已修**：`RECOMMENDED_GRAMMAR_F3` 转 `ADOPT_AS_CORRECTED_BY_R3`，并显式声明
F3 的 predecessor／successor 两行（沿 R2 为 P3 做的先例）。**F3 因此不再是「不动」
的**，§二.A.4 已相应更正。

**(b) 这不是纯增补——它改了两行已批准字段。**
`RECOMMENDED_P3_PERMITTED_SUCCESSOR`（R2 刚钉死的那一行）与
`RECOMMENDED_GRAMMAR_F3`。**请复审席正面裁：改一行 R2 刚批准的字段，是否仍在
「修订」的范围之内。** Sol 第四次复核的意见是「没有超出 amendment 路径，但只能由
Aaron 明示 ratify」。

**(c) `ADOPT_AS_INTRODUCED_BY_R3` 是词表新值，且 canonical 绑定尚未定义。**
既有取值都预设「§D 里已经写好了语法」，而 CR1 没有。**Sol 另指出**：
`R3_CANONICAL_SHA256` 只覆盖 58 行 profile 块，**不覆盖 §二.A.1 的 `EventSpec`**；
提案原先所称「同 SHA 绑定」并未被精确定义。doc HEAD 可间接绑定全文，
**但那是绑定方式的选择，builder 定不了。**

**(d) 两个字段的值域，本版已按 Sol 要求封闭（取值是 builder 的提议）**：

- `RECOMMENDED_CR1_DANGLING_EVENT_DOMAIN=P3` —— 否则可在 P3 之后声称任意 dangling
  event。
- `RECOMMENDED_CR1_REGISTRY_INTACT_VERIFICATION_DOMAIN=64HEX_SHA256_OF_REGISTRY_AT_RESOLUTION`
  —— 一个可复算的证明，而不是一个 `YES`。**这个取值是我提的，请裁。**

## 二、Part A —— CR1 的语法正文（随 R3 profile 一并批准）

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

- P3／P4／A1／F1／F2／A2／AX／P5／T1 的任何字段，含 actor（第 5 项裁定：保留）。
  **F3 已从本清单移出** —— §二.2(a)：CR1→F3 必须双向声明，F3 的 predecessor
  因此必须改。前一版把 F3 列在这里，与它自己新增的边直接矛盾。
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

**第一版提议的是一个「遗弃」黑名单。fresh Sol 判 HOLD 并指出它至少漏了 A2 与
F2v。追下去发现问题比漏项更深：黑名单形式本身是错的** —— 日后新增任何事件都会
**默认可放行**，这与整栈的 fail-closed 方向相反。

**改为白名单**（实测各事件的 terminal 位与后继得出）：

```
START_ADMISSIBLE(chain) == last ∈ {"P1", "P2", "F1"}
```

即：**只有尚未开跑的三种状态允许开新运行**，其余一律拒绝。**新增事件默认落在
拒绝侧**，这正是白名单相对黑名单的全部价值。

| last | 状态 | 可否开新运行 | 拒绝时该说什么（Sol 要求各状态命名不同） |
|---|---|---|---|
| `P1` / `P2` | 已提议／已授权，**未开跑** | **可以** | —— |
| `F1` | 开跑前尝试失败 | **可以**（重试是设计内的） | —— |
| **`P3`** | 已开跑、无任何终止事件 | 否 | **`ABANDONED_RUN`** —— 需 CR1 裁定 |
| `P4` | 已封存 | 否 | `AWAITING_INDEPENDENT_VERIFICATION`（待 P5／F2v） |
| `F2` | 开跑后失败 | 否 | `AWAITING_RETIREMENT`（待 F3） |
| `A1` | 归档失败 | 否 | `AWAITING_ARCHIVE_RESOLUTION`（待 A2／AX） |
| `AX` | 归档永久失败 | 否 | `AWAITING_RETIREMENT`（待 F3） |
| **`A2`** | 归档已恢复 | 否 | `AWAITING_INDEPENDENT_VERIFICATION`（待 P5）**（第一版漏列）** |
| **`F2v`** | 验证失败 | 否 | `AWAITING_RETIREMENT`（待 F3）**（第一版漏列）** |
| `CR1` | 崩溃已裁定 | 否 | `AWAITING_RETIREMENT`（待 F3） |
| `P5` / `F3` | 已闭合 | 否 | 该 id 已终结，新运行须用新 id |

**两条 Sol 强调、本版采纳的分界**：

1. **`NON_TERMINAL_TRAPS` 是闭链诊断集合，不得直接充当启动授权政策集合。** 前者
   回答「这条链闭上了吗」，后者回答「能不能在这个 id 上开新运行」。本版把两者
   彻底分开：白名单是政策，traps 仍只供 `assert_chain_closed` 诊断。
2. **per-id 拒绝与「是否阻断整个 MC 入口」是两个政策决定，不得藏在一个布尔谓词里。**
   本版只裁 per-id；**全局阻断范围留给 Aaron**（见 §六）。

**为什么仍值得先落地**：谓词一旦定下，实现是加性 fail-closed，且**今天落地
可观测行为零变化**——`run_supplement_production` 本就 gate-first 拒绝，没有 MC
生产路径能走到这个门。但**在谓词被复核之前，builder 不实施**：一个把每次正当
运行都拒掉的门，比没有门更糟。

### B. 修订本体（须 ratify）—— **代码是转录，不是批准对象**

**顺序按 §二.0 的既定路径，不得倒**：
Sol 复核本提案 → builder 把 R3 正文与 CR1 语法做 **doc-only commit**（该 commit
即 `APPROVAL_BINDS_DOC_HEAD`）→ Aaron 批准 `id + sha256 + 精确 doc HEAD` →
**然后**才轮到下列代码转录：

1. `EVENTS` 加 CR1 **并把 CR1 加进 `EVENTS["F3"].predecessors`**；
   `NON_TERMINAL_TRAPS` 加 CR1；`FORBIDDEN_EDGES` 加两条
   ——**逐字转录已批准的 R3 正文，不得反过来由代码定义 profile**。
1b. **（Sol 第四次复核补出，第一版漏列）**
   · 每条新 `FORBIDDEN_EDGES` 必须在 `supplement_registry.FORBIDDEN_EDGE_CODES`
     配专用拒绝码，并进 `REFUSAL_CODES`（实测该映射在 `:420`，码集在 `:505`）。
   · `supplement_runner.plan_next_short_id`（`:679`）必须支持 `CR1→F3`。
   · CR1 的两个字段值域必须由 `supplement_registry._check_field_values`（`:848`）
     实际强制，不能只写在 profile 里。
2. 修 `assert_chain_closed:748-749` 的写死提示语 —— **Sol 要求提示语由 successor
   数据生成，不再扩展那个硬编码三元表达式**。加一个事件就要改一次字符串，是同一
   缺陷的第三次重演。
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

## 六、请 fresh Sol 重点看的（第五次交付，已按第四次 HOLD 改过）

**第四次 HOLD 的四条，本版逐条处理如下**：

| Sol 的发现 | 本版做法 |
|---|---|
| HIGH 1 CR1/F3 边不对称 | **已修**：F3 转 `ADOPT_AS_CORRECTED_BY_R3`＋显式两行；R3 哈希因此变为 `12105e98…`，`d26cbc3e…` 作废 |
| HIGH 2 谓词不全＋我的前提陈述不准 | **已修**：我的「悬空 P3 会过 A_PRECHECK」经实测推翻并公开更正（§一.2）；黑名单改白名单，A2／F2v 补入，per-id 与全局阻断拆开 |
| HIGH 3 CR1 字段域与 canonical 绑定未闭合 | **值域已封闭**（§二.2(d)，取值是我提的）；**canonical 绑定方式仍未定**，明确留给你与 Aaron |
| MEDIUM 4 禁边非必要＋建造义务不全 | **建造义务已补**（`FORBIDDEN_EDGE_CODES`／`plan_next_short_id`／`_check_field_values`）；**禁边是否保留、以及是否该正面处理真正的重启边 `CR1→P3`，请裁** |

**请重点打的**：

1. **§二.2(b)**：R3 改了**两行**已批准字段（P3 后继、F3 语法）。第四次你的意见是
   「没有超出 amendment 路径，但只能由 Aaron 明示 ratify」——本版把 F3 也拉进来了，
   **范围更大，请重新判**。
2. **§四.A 的白名单**：`START_ADMISSIBLE = {P1, P2, F1}`。它是我按你的批评从黑名单
   改过来的——**改动方向对不对、集合本身有没有漏，请证伪**。
3. **§二.2(c) 的 canonical 绑定**：`R3_CANONICAL_SHA256` 只覆盖 58 行 profile 块，
   不覆盖 CR1 的 `EventSpec`。**绑定方式我定不了**，请给出可行形。
4. **`CR1→P3`**：你指出「永不复活运行」应正面处理真正的重启边。本版**没有**把它
   加进 `FORBIDDEN_EDGES`——因为它同样不在 CR1 的 successors 里，与 P4／P5 同理。
   **要么三条都列、要么一条都不列，请裁哪一种。**
5. **`registry_intact_verification` 取 64-hex SHA-256** 是我的提议，不是任何裁定。

## 七、常设禁令（对复审席位同样在 force）## 七、常设禁令（对复审席位同样在 force）

- **只读。** 不改文件、不打补丁。
- **不得在本仓做任何检索**（S1(b)）；需要路径就列出来，由工作会话经
  `PULL_PROTOCOL` 提供字节。
- 禁区权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`，
  **每一条路径都当作关闭**。
- 零真实数据读取；零执行；不在 `C:\Users\Aaron\quant-data\` 下创建目录；
  不追加 registry／台账事件；不签发授权；不填 P2 占位符。
- **PASS 不授权任何写入**：修订本体须 Aaron ratify 之后才动 `EVENTS` 表。
