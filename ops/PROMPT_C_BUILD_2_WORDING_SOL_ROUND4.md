＃ C_BUILD_2 措辞复审 · 第 4 轮 —— fresh Sol（**已返回：VERDICT=HOLD**）

> 2026-08-30 返回，四条发现全部成立、全部复现。裁定与处置见
> `ops/RULING_SOL_C_BUILD_2_R4_HOLD_2026-08-30.md`。
> **本文以下内容是发出时的原字节，一字未改** —— §1.2 与 §4 描述的是当时那版合同，
> 它已被第 4 轮打穿并重写。改它就是改一份已被据以裁决的材料。

```ini
REVIEW_ID=c-build-2-wording-r4
DELIVERY_STATUS=RETURNED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审第 4 轮）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            **第 1、2、3 轮 c-build-2-wording* 的任何会话**；
            N09 R2/R3 的任何前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND4.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 0. 检索边界 —— **可执行的，不是散文**

第 3 轮之后有一个决裁席位在本仓做了两次**仓根范围**检索，作用域含两份禁区台账。
**成因是 builder 的**：禁区清单只写成文字，没有随包给出可执行的约束。
**这是同一形态第三次**，所以本轮把它写成规则：

```
允许检索的根        src/  ·  tests/  ·  §2 表中逐条列名的 ops 文件
禁止               仓根范围的 grep / rglob / find；ops/ 全目录枚举
永不打开           ops/outcome_quarantine/**
                   ops/EXPOSURE_LEDGER.md
                   EXPOSURE_LEDGER.md（仓根那份）
                   ops/OUTCOME_CARRYING_ARTIFACTS.json 的 carries_outcome 全部路径
```

需要禁区之外、上表之外的字节：**列出路径向工作会话索取**，不要自己去开。
若你的工具会把大块检索结果持久化到磁盘，请在回答里报告该文件路径。

## 1. 第 3 轮判 HOLD，两条发现，builder 全部接受

**没有辩解，两条都先复现后修。** 证据：`ops/FINDINGS_SOL_R3_REPRODUCED_2026-08-30.md`。

### 1.1 第一次复现是错的 —— 请把这件事也算进你的判断

我照第 3 轮的描述注入变异，**全红**。红了不等于第 3 轮错了，
**等于我复现的不是它的变异**：我的注入对测试实际使用的文件名生效，
所以行为测试立刻抓住；第 3 轮的新路径守在一个**测试从不满足**的条件上。

照这个理解重做，**59/59 全绿，与它一字不差**。

**如果我停在第一次，我会写下「无法复现」，而缺陷仍在。**

### 1.2 HIGH 的修法 —— 封闭出口合同，不是把两个反例追加成用例

`tests/test_resolve_partial_path_contract.py`。

每个出口由 AST 导出为 `(kind, action-or-code, guard source)`，
导出集合必须**等于**声明集合 `DECLARED_EXITS`。**新增出口即变红**，
直到作者写下它并回答三条义务：

```
(a) already_sealed 的路径必须读过 FINAL 并与 intended 比较过，
    且被比较的名字必须是从磁盘读来的（不是有人赋的值）
(b) 任何路径不得摧毁 .partial —— 含 getattr 动态到达。
    本文件干脆拒绝该函数内的**任何** getattr：合同看不出计算出的名字解析成什么
(c) retry_permitted 必须 preserved_as= 一个由 _preserve 绑定的名字
```

**合同跟着调用走**（`_preserve` → `_divergent_name`），因为停在函数边界
只会把违规赶到低一层。

### 1.3 MEDIUM 的修法 —— 加宽探测域，同时缩窄声称

字段形状的模式总能靠不用那个字段绕开。探测域改为**哈希本身**：
记录里任何 64-hex 都必须是本文件审查过的批准。实测 4/4/4，零误报。

**修不掉的那一半写在文件里**：这个扫描只读一个文件；
批准若记在别处它管不着。闭合它需要 `SIGNABLE_RATIFICATION_ROUTES=1`
成为权威冻结不变量 —— **那正是你上一轮列的 `UNRESOLVED_FOR_AARON`，尚未裁定。**
在裁定前，该文件的声称是「**记在这里的**每份批准」。

## 2. 受审集

```
REVIEWED_SET_UNCHANGED_SINCE=<发行时填入>
```

**语义**：该 commit 之后没有任何 commit 触碰过下表的参考件。

> **第 4 轮 MEDIUM 订正。** 上一版这里写死 `dba55d9`，而我自己的下一个提交
> `eab7992` 又改了 `tests/test_resolve_partial_path_contract.py` —— 它就在受审集里。
> 表里八个哈希全对，**错的是 range 声称**。这是一次自报，也是我这一晚反复抓的
> 同一形态：**声称比事实宽**。
>
> 现在它**发行时才填**，并由 `tests/test_a_prompts_range_claim_actually_holds.py`
> 从 git 机械核实 —— 任何 LIVE 提示词的 range 声称若不成立，套件变红。
本提示自身不在该 range 内（发出 delivery 就是对它的一次提交，无不动点）。

| 角色 | 路径 | sha256（前 16） |
|---|---|---|
| delivery | `ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND4.md` | 发行时填入 |
| reference | `src/itsf/mc/supplement_runner.py` | `981d098819f340b4` |
| reference | `src/itsf/mc/supplement_contract.py` | `34b2a17ed2e1617e` |
| reference | `tests/test_resolve_partial_path_contract.py` | `37c272c04fa0f4dd` |
| reference | `tests/test_every_sealed_final_was_read_back.py` | `c2987bafbe62e3a1` |
| reference | `tests/test_c_build_2_wording_coverage.py` | `4d4874c5e22b5adf` |
| reference | `tests/test_n09_checkpoint_assertions.py` | `40f9ecce8b9ecf58` |
| reference | `tests/test_every_approval_is_accounted_for.py` | `683cd0c456d946ca` |
| reference | `tests/test_the_ratified_preimage_is_reconstructible.py` | `3b8fd362614ee7e7` |
| reference | `ops/FINDINGS_SOL_R3_REPRODUCED_2026-08-30.md` | 发行时填入 |
| reference | `ops/RULING_SOL_C_BUILD_2_R3_HOLD_2026-08-30.md` | 发行时填入 |

## 3. 我用你自己的反对意见攻击了我的修复，结果它两次抓到我

你两轮的核心反对都是同一句：**「把我列出的现有路径当成所有可能路径」**。
新合同的 `DECLARED_EXITS` **也是手写的**，所以我先自己攻它。

**第一击**：合同只枚举 `resolve_partial` 自己的体，
于是 `_preserve` 里 `raise` 出来的 `divergent_partial_exists`
和 `_divergent_name` 里的 `incident_id_malformed` ——
**两个真实的异常出口** —— 它看不见。
**这是同一晚第四次「推导停在函数边界」，而且发生在给这条 HOLD 写的修复里。**

**第二击**：改成跟调用走之后，它立刻告诉我 `_preserve` 有**两个**调用点
（branch C `:959` 与 branch E `:968`），我只声明了一个。

两处都在本包发出**之前**由机制抓到，不是由你抓到。
这是我能给出的、关于该合同是否真闭合的最强证据 —— 也请你把它当作靶子。

## 4. 请攻击这些（builder 认为最可能仍然错的地方）

1. **`DECLARED_EXITS` 仍是手写的。** 机制保证「导出集 == 声明集」，
   但**导出本身**只跟模块级 `ast.Name` 调用。经属性调用
   （`self.foo()`、`mod.bar()`）、经 `getattr`、经参数传入的可调用对象，
   都不在导出里。我拒绝了函数内的所有 `getattr`，但那只挡住一种形状。
2. **义务 (a) 的检查是「守卫串里含 `== intended` 且左侧名字来自 `read_bytes`」。**
   一条构造得当的新路径可能满足这个形状而语义上并未回读 FINAL。
3. **`_MODULE_FUNCTIONS` 在 import 时求值一次。** 若有测试在运行期改写运行器，
   合同看到的是旧快照。我没有测这一条。
4. **MEDIUM 的修法把探测域绑到「64-hex」。** 一份用 base64 或分段书写哈希的
   散文批准，仍然能绕过去。我认为这已经越过了「合理伪装」的界，但那是判断不是证明。
5. **本轮新增的三道 C_BUILD_1 门接线已落地**（`_classify_c_build_1`）。
   它不在你上一轮的受审集里，但它现在与 C_BUILD_2 同处一个文件。
   **`_g_seal_staging_partial` 仍无条件拒绝**，理由记在
   `ops/PREPARED_C_BUILD_1_GATE_WIRING.md`。请确认接线没有污染你在审的措辞。

## 5. 交付要求

沿用第 3 轮的字段（`VERDICT` / `CONDITIONS_MET` / `FINDINGS` /
`UNVERIFIABLE_SELF_REPORTS` / `SEAT_STATUS` / `INDEPENDENCE_STATEMENT`），
另加一条：

```
CONTRACT_CLOSURE_ASSESSMENT=  封闭出口合同是否真的闭合了你第 3 轮的反对？
                             若否，给出一个绕过它的新路径形状（像前两轮那样，
                             直接在 AST 里注入并跑）。
```

**「HOLD」是合法且受欢迎的结论。** 前三轮都是 HOLD，每一轮的发现都成立，
其中两轮各带出了一个更大的洞。**猜一个 PASS 比 HOLD 糟得多。**
