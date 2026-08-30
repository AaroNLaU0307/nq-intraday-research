＃ C_BUILD_2 措辞复审 · 第 5 轮 —— fresh Sol

> **发行流程（builder 用，2026-08-30 学到的）**：哈希与 pin **和 `ISSUED` 是同一个动作**。
> 备而未发时表里是占位符 —— 一份钉了字节却说自己「未发」的文件，守卫会拒绝，而它是对的：
> 我先武装了登记册、又继续改受审文件，冻结守卫当场抓住。**改完再武装，不是反过来。**

```ini
REVIEW_ID=c-build-2-wording-r5
DELIVERY_STATUS=RETURNED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审第 5 轮）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            **第 1、2、3、4 轮 c-build-2-wording* 的任何会话**；
            N09 R2/R3 的任何前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
```

**READ THIS PROMPT FROM DISK, not from a paste.** 本文件从磁盘读取，不从粘贴读。
**绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND5.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

## 0. 检索边界 —— 可执行的

下栏中 `永不打开` 之下的每一条路径都是 **OFF-LIMITS**（outcome-carrying），逐条点名只为**标记禁区**，不是引导你去读：

```
允许检索的根        src/  ·  tests/  ·  §2 表中逐条列名的 ops 文件
禁止               仓根范围的 grep / rglob / find；ops/ 全目录枚举
永不打开           ops/outcome_quarantine/**
                   ops/EXPOSURE_LEDGER.md
                   EXPOSURE_LEDGER.md（仓根那份）
                   ops/OUTCOME_CARRYING_ARTIFACTS.json 的 carries_outcome 全部路径
```

需要上表之外的字节：**列出路径向工作会话索取**。
第 4 轮席位报了 `PERSISTED_SEARCH_OUTPUT=NONE` —— 本节就是为此存在的，请照做并同样报告。

## 1. 第 4 轮判 HOLD，四条全中，**其中最该记的一条是我自己造的**

四条全部复现在先。证据与逐条处置：`ops/RULING_SOL_C_BUILD_2_R4_HOLD_2026-08-30.md`。

### 1.1 我在第 4 轮的 §4 里列出了这两个根因，然后没有去修

第 4 轮提示词 §4 的第 1、2 条，逐字：

> 1. **导出本身只跟模块级 `ast.Name` 调用**……
> 2. **义务 (a) 的检查是「守卫串里含 `== intended` 且左侧名字来自 `read_bytes`」。**
>    一条构造得当的新路径可能满足这个形状而语义上并未回读 FINAL。

**第 4 轮用的正是这两条。**
**列出弱点不等于处理弱点** —— 这是本轮我从自己身上学到的东西，
也是我把 §4 的形制改掉的原因（见下）。

### 1.2 四条各自的根因与修法

| 发现 | 根因 | 修法 |
|---|---|---|
| HIGH ① 同形路径被吞 | 出口存进 **set**；溯源是**函数级**不是路径级 | 出口改**有序列表**逐位比对；每个出口携带**它自己路径上的绑定**；义务 (a) 用该路径的绑定回答 |
| HIGH ② 删除经可调用对象 | 名字黑名单是**开放世界** | **封闭调用世界**：只允许 `Name(...)` 与 `x.attr(...)` 两种形状且 callee 在白名单内；callee 是 Call／Subscript／Lambda 一律拒绝，**无需知道它解析成什么** |
| MEDIUM ① 大写哈希 | 正则只认小写 | 大小写不敏感并归一化。我上一轮把 base64／分段称为「越过合理伪装」**并标明那是判断**；大写根本不在那一类 |
| MEDIUM ② range 自报 | 手写并寄希望 | `tests/test_a_prompts_range_claim_actually_holds.py` 从 git 机械核实**每一份 LIVE 提示词**；pin 改为**发行时才填** |

### 1.3 我另外自己往下推了两层（第 4 轮没点名，但同一根因）

- **语句世界也封闭了。** 遍历原本只递归 `ast.If` —— 一个 `try:` 或 `with:` 里的
  `return` 对它**不可见**。现在遇到不认识的语句类型**直接失败并说明原因**。
  已证：往函数里塞一个 `try:` 早退 → 合同变红。
- **`_FNS` 不再在 import 时缓存。** 这是第 4 轮 §4 我列出却没修的第 3 条。
  这次修了 —— 因为上面 §1.1。

## 2. 受审集

```
REVIEWED_SET_UNCHANGED_SINCE=91ff15d830621f18730d82d6d8bc69b5322b646c
```

| sha256 | bytes | 路径 |
|---|---|---|
| `981d098819f340b460b094bbcc284039973417f43e4ba65b252967d4d5c352b2` | 50099 | `src/itsf/mc/supplement_runner.py` |
| `34b2a17ed2e1617e34457882d7df7b4bcc0cc8d658003f8ea5a07a607bdfe0cf` | 32616 | `src/itsf/mc/supplement_contract.py` |
| `d3cb7a145ea0778fe9812d3ee4252ebc0bbcf34e59d5497e6014dbe1bb2a1ccd` | 17264 | `tests/test_resolve_partial_path_contract.py` |
| `b329b372eeab1069675267c8e50f71bb903d5117257106e5edbfdfb4b4920fd0` | 6722 | `tests/test_a_prompts_range_claim_actually_holds.py` |
| `c2987bafbe62e3a16dcc3249016985c91cac8259b04bec4ec959423300d1be95` | 6100 | `tests/test_every_sealed_final_was_read_back.py` |
| `4d4874c5e22b5adff47312bb03c0e405418fb894446b9ecd87a46e7ecef42613` | 11556 | `tests/test_c_build_2_wording_coverage.py` |
| `40f9ecce8b9ecf5835073291a200920316f65478e4188a633d44ed0680a311c0` | 26667 | `tests/test_n09_checkpoint_assertions.py` |
| `4ae94ad34a5c2d4c06a8dd7a99aeef546356fb2ba8b384faf6cd8082f4ea1097` | 13730 | `tests/test_every_approval_is_accounted_for.py` |
| `3b8fd362614ee7e7c689bde19d9797b501464de5bc2caa57cb8271963effae50` | 6869 | `tests/test_the_ratified_preimage_is_reconstructible.py` |
| `90d0f93f1b17b2793277aed7f313691305f5178ae5d6bfcbd794b141f7209799` | 4562 | `ops/RULING_SOL_C_BUILD_2_R4_HOLD_2026-08-30.md` |
| `eee5ddbfafa45b0a373d96c5ff0a2de8aeee9b51a3db3a42d96c85b6d84e96fa` | 2644 | `ops/OFF_LIMITS_COMPANION_R5.md` |

**delivery**：`ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND5.md`，其字节见 `ops/ARTIFACTS_UNDER_REVIEW.json`。

**禁区清单不在本包内** —— 评审包不得携带它（D-2 裁定，第二个席位被烧之后）。
它随包交付：`ops/OFF_LIMITS_COMPANION_R5.md`，请一并读。

**核对你读的是当前文件**：line 82 of it must read 那一行 —— `REVIEWED_SET_UNCHANGED_SINCE` 必须是 `91ff15d830621f18730d82d6d8bc69b5322b646c`。
对不上 ⇒ 你手上是陈旧粘贴 ⇒ **STOP**，回磁盘重读。

## 3. 修后我自己跑的反例

```
HIGH ① 的注入  -> 出口列表多出一条  ＋  路径局部溯源报出
                  "on THIS path 'existing' is bound to 'intended', which is not a read"
HIGH ② 的注入  -> "callee is a Call -- not a plain name or attribute"
                  ＋ next 不在允许名字里
try/except 早退 -> "a `return` inside it would be INVISIBLE"
大写 64-hex    -> 变红
```

## 4. 本轮我**接受并声明**的残留 —— 不是「可能错的地方」清单

第 4 轮我把这一节写成「我觉得还可能错的五处」，然后没修，于是被用来打我。
所以本轮改成：**要么已修，要么在此明确接受，并写明代价。**

| 残留 | 为什么接受 | 代价 |
|---|---|---|
| `DECLARED_EXITS` 对**顺序**敏感 | 语义等价的重排会变红。这是**故意的**：重排也值得看一眼 | 噪声；重排时要改声明 |
| 白名单可以被加条目消音 | 无法机械区分「合法新增」与「为了变绿而加」 | 文件里写明「加条目是有意的动作」，但这是社会约束不是机械约束 |
| 合同只覆盖 `resolve_partial` ＋ 两个助手 | C_BUILD_2 的措辞就锚在这里 | 若措辞将来指向别处，合同要跟着扩 |
| 义务 (a) 匹配守卫串含 `== intended` | 若改成 `_same(existing, intended)` 之类，`assertIn` **失败闭合**（变红）——已核 | 变红时需要人来判断是不是合法写法 |

**若你认为其中任何一条不该被接受，请直说** —— 我把它们列在这里就是为了让你能反对，
而不是为了显得坦诚。

## 5. 交付要求

沿用第 4 轮字段，另加：

```
CONTRACT_CLOSURE_ASSESSMENT=  路径敏感 ＋ 封闭调用世界 ＋ 封闭语句世界，
                             是否闭合了你第 3、4 轮的反对？
                             若否，注入一条绕过它的路径并跑出来。
ACCEPTED_RESIDUALS_ASSESSMENT= §4 那四条「接受」里，有哪几条你认为不该接受？
```

**HOLD 受欢迎。前四轮都是 HOLD，每一轮的发现都成立。猜一个 PASS 比 HOLD 糟得多。**
