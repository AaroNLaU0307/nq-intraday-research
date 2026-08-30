＃ C_BUILD_2 措辞复审 · 第 8 轮（**最后一轮**）—— fresh Sol

```ini
REVIEW_ID=c-build-2-wording-r8
DELIVERY_STATUS=ISSUED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审第 8 轮，上限轮）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            **第 1–7 轮 c-build-2-wording* 的任何会话**；
            N09 R2/R3 的任何前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
ROUND_CAP=8（Aaron 2026-08-30 裁定 OD-1）——**本轮即上限，之后不再开新轮**
```

**READ THIS PROMPT FROM DISK, not from a paste.**
**绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND8.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

禁区清单随包交付：`ops/OFF_LIMITS_COMPANION_R8.md`，请一并读。
**它更正了第 7 轮那次边界违例 —— 成因是我，不是你。**

**权威登记册**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。

---

## 0. 上限轮意味着什么，说清楚以免被误读

Aaron 2026-08-30 裁定（`ops/OWNER_DECISIONS_2026-08-30.md` OD-1）：

> 修复这个环节记得以后不超过八次，如果到了八次就按最好的方式执行就行

**这是停止迭代的决定，不是残留已闭合的发现。** 本轮之后仍站着的残留
标 `ACCEPTED_BY_CAP` —— 意思是**轮次用完了**，不是**有人判定代价可接受**。
§5 就是这么标的，请检查我有没有在那张表里把某条真残留写成「已解决」。

**因此本轮请优先给能改变结论的发现**，而不是穷举式完整性。
一条「还有第 N 种情况没覆盖」若不改变任何结论，它在本轮的价值低于
一条「§5 里某条残留被写窄了」。

上限由 `tests/test_the_review_round_cap_is_respected.py` 机械执行：
**上限值从裁定文件里读出来**，不写死在测试里；并强制本轮必须出现
`ACCEPTED_BY_CAP` 字样，否则变红。

---

## 1. 你上一轮判 HOLD，三个 HIGH 全部复现、全部闭合

证据与逐条处置：`ops/RULING_SOL_C_BUILD_2_R7_HOLD_2026-08-30.md`（在受审集内）。

### 1.1 先认最难看的一条

`DECLARED_EXITS` 的注释**逐字**写着：

> A list, never a set: two paths that look identical are two exits,
> and collapsing them is what round 4 walked through.

**而我写的是** `declared = {name for _kind, name, _guard in DECLARED_EXITS}`。

那条注释就在列表正上方。**我读过它、在它下面写了文件、然后照样折叠。**
第 6 轮的错是「手写集合冒充导出」；第 7 轮是「导出了，但导出到错误的粒度」——
**后者更糟，因为它看起来像修好了**。

### 1.2 HIGH-1 闭合：路径身份 =（名字, 出口行, helper 内 raise 行）

```
声明侧   walker 现在把 Call 节点与 helper 的 raise 行一并带出
运行侧   sys.settrace 记 resolve_partial 自身帧的执行行，末行即出口行；
         traceback 中 runner 内非 resolve_partial 的帧给出 helper raise 行
```

`12 条声明 → 12 个唯一三元组`，运行侧实测全部命中，
含你证明从未执行过的 branch E 两条。

```
核验  python -m pytest tests/test_resolve_partial_state_diff.py -q
预期  24 passed
```

**变异证红**（比你的形式更强）：往 runner 里加一条**真实存在但不可达**的
第二个 `divergent_partial_exists` ——

```
AssertionError: [] != [('divergent_partial_exists', 1012, None)]
```

R7 那一版对同一变异是 `DUPLICATE_UNREACHABLE_SUCCESS=True`。

**非空过守卫也补了**：`sys.settrace` 在某些 runner 下静默失效，
届时每个路径身份退化成 `(name, None, ...)` 却仍显得健康 ——
所以先断言 tracer 真的记到了行，并断言声明侧**确实存在重名**
（否则本文件的前提本身是空的）。

### 1.3 HIGH-2 闭合：**枚举 ADS，而不是收窄声称**

收窄成「仅默认数据流」诚实且便宜，但会**把真实字节留在治理目录里无人看管**。
所以走 `FindFirstStreamW`（OS 自己对「这个文件有哪些流」的回答），
全集仍然是**文件**，而不是我记得写下来的流名清单。命名流按 `file:stream` 独立记入。

关掉枚举则 3 条变红，含你的原案（删 `.partial`、以相同主字节重写 final）。
另加 `TestTheStreamWalkIsREAL`：**ctypes 绑定坏掉与「没有流」不可区分**。

### 1.4 HIGH-3 闭合：这是**生产缺陷**，两半都补了

`resolve_partial` 的 docstring 声称所有写入落在 `out_dir` 之下，
而 `filename` **从未被校验**。

> **声称本身不是缺陷，缺失的校验才是 —— 而声称正是让没人去找它的原因。**

```
生产   _require_plain_name：空 / "." / ".." / 非自身 basename /
       含分隔符或冒号  =>  filename_not_a_plain_name
仪器   快照根上移到 out_dir 的父目录 —— 越界写入本来就在旧快照视野之外
```

九种形式实测全部拒绝，`out_dir` 之外零字节，正常名照常 `promote`。
冒号那条同时关掉 HIGH-2 的生产半边：**runner 已无法再创建一个 ADS**。

合同当场起作用：新出口一加就报「调用不在封闭世界内」＋「出口清单不匹配」，
并把 helper 的**两个** raise 点各算一条路径。

```
核验  python -m pytest tests/test_resolve_partial_path_contract.py -q
预期  10 passed
```

### 1.5 你列的 5 条 CLAIM_COMMAND_MISMATCHES，我全认

```
1  §1.3 写「调用观测器 23/23」，实为 22   <- 我删了那个手写 reached 测试，
                                            没回头改这个数字。
                                            写下时为真，交付时为假。
2  python 不在你会话的 PATH               环境，非声称
3  场景计数 9/4 精确匹配                  一致
4  §1.3 的「核验」只是指向文字，不是命令   我的规则我自己没守，应标 [意见]
5  §1.5 要求落盘改受审测试，与 SOURCE_WRITES=NONE 冲突
```

**第 1 条已被机械化**，因为它是同一形态第三次
（R6「已修」／R7「23/23」／R6 漏掉整节 §2）：

`tests/test_a_prompts_measured_numbers_are_current.py` 把本文件里每一条
`核验 python -m pytest … / 预期 N passed` 的数字，与**该文件当前实际含有的测试数**
比对，对不上即变红；被指向的文件不存在也变红
（**一条跑不动的核验不是核验** —— 第 7 轮我发出过一条）。

**它不执行那些命令，而这一点是我付了代价才学会的，如实交代：**

第一版**真的去跑**每条命令。本文件恰好引用了它自己，于是每一层都重读本包、
再 spawn 下一层 —— **41 个 python 进程，Aaron 的机器当场崩了**。
我的第一次「修复」只挡住了扫描包的那个测试，没挡住它旁边同样会 spawn 的
非空过测试 —— **第二次崩机**。

所以我不是再加第三道防护，而是**把能力本身拿掉**：

```
「那个文件有 N 个测试」   <- 本守卫静态数（AST）
「而且它们通过」         <- 本套件自己在跑它们，红了整套就红
```

两条合起来正是那句声称，且没有任何子进程可递归。
静态计数由**两条独立推导互证**（AST 走树、另一条走缩进），
而不是我手打一个数字 —— 手写镜像正是本次复审反复出问题的形状。

**这条比对本身有一个已知缺口，写在这里而不是等你发现**：
平台 skip。`N passed` 在有测试被 skip 的机器上不等于收集数
（`test_resolve_partial_state_diff.py` 的三条 ADS 守卫在非 Windows 上 skip）。
包与复审在同一台 Windows 上，所以此处一致。

```
核验  python -m pytest tests/test_a_prompts_measured_numbers_are_current.py -q
预期  13 passed
```

**所以本文件上面那些数字是在发行那一刻重新测的，不是复用早先的读数。**

### 1.6 你的边界违例，成因是我

`OFF_LIMITS_COMPANION_R7.md` 把「禁止 `ops/` 全目录枚举」写成对**人**的约束，
而**我要求你跑的治理测试本身**就在 `OPS.rglob("*.md")`。

> **我要求席位遵守一条我自己的测试代码违反的边界。**

R8 随包件已逐条列出会枚举 `ops/` 的九个测试，并写明**跑它们不算违例**。
已记入席位轴台账（研究轴不动 —— 烧席位不消耗研究自由度）。

---

## 2. 受审集

```
REVIEWED_SET_UNCHANGED_SINCE=4d4385e4a07dc04fecbcc22dc28226779743d18d
```

**语义**：该 commit 之后没有任何 commit 触碰过下表的参考件。
本提示自身不在该 range 内（发出 delivery 就是对它的一次提交，无不动点）。

| sha256 | bytes | 路径 |
|---|---|---|
| `1e1684767d76327435dd42f761e90ecfcda9f34b80313dee3eab826fee7e0ff3` | 52665 | `src/itsf/mc/supplement_runner.py` |
| `34b2a17ed2e1617e34457882d7df7b4bcc0cc8d658003f8ea5a07a607bdfe0cf` | 32616 | `src/itsf/mc/supplement_contract.py` |
| `2c9cdf1d6f8956aebe3584a9d2764d3ab25fe557961a3368d96844f03b1ae253` | 29464 | `tests/test_resolve_partial_state_diff.py` |
| `33648134bbc7c8d99202ea168be9d87a0a23970847e0aa465b16af7d6e12d9aa` | 20448 | `tests/test_resolve_partial_path_contract.py` |
| `06a8ce72f7d5f0217da91625b1139bf318583f9f45e8df2454e3f636c7fd67db` | 22911 | `tests/test_resolve_partial_observed_behaviour.py` |
| `4b47f6bd81a01c7f44912adfabce5c2d76d664516c40c5a2fe54a1537b7a08d6` | 12649 | `tests/test_a_prompts_measured_numbers_are_current.py` |
| `7532541c105160e208fda348f7ac68058e6818077d6de5a7b1a9eebfc05d9b0c` | 4132 | `tests/test_the_seat_ledger_ids_are_unique.py` |
| `be23ef8886933fb2cf1b15d810c92bdd65f16e0cd5d7cef035cfe9a52aae4f1c` | 8852 | `tests/test_the_review_round_cap_is_respected.py` |
| `4d4874c5e22b5adff47312bb03c0e405418fb894446b9ecd87a46e7ecef42613` | 11556 | `tests/test_c_build_2_wording_coverage.py` |
| `22888d25535103d8fe62f316d980dc5bc6967f7beb47bd507cb9a51c650760e1` | 8155 | `ops/RULING_SOL_C_BUILD_2_R7_HOLD_2026-08-30.md` |
| `c9e3f13dddb9020b4f2ed76607e6291c640c858e1b002e15170aa7382b57d266` | 2190 | `ops/OWNER_DECISIONS_2026-08-30.md` |
| `0c8b0d980b977367cc88450ff133d0912dc961ac7df877cbb1688537dc033200` | 2569 | `ops/OFF_LIMITS_COMPANION_R8.md` |

**delivery**：`ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND8.md`，
字节见 `ops/ARTIFACTS_UNDER_REVIEW.json`。

**本轮重点受审件是第三行与第四行** —— 换过的仪器，以及它和合同的接缝。

**核对你读的是当前文件**：line 199 of it must read
`REVIEWED_SET_UNCHANGED_SINCE` 那一行。对不上 ⇒ 陈旧粘贴 ⇒ **STOP**，回磁盘重读。

---

## 3. 三个仪器的分工

```
状态 diff     SILENT_DELETE_FORBIDDEN（含 ADS）、branch C 真的改名、
              路径级出口覆盖、越界写入可见 —— 对机制闭合
调用观测器    因果：答案是否由**读到的**字节算出（说谎读技术）
              —— 状态看不见读；这一半你第 6、7 轮都没攻击
AST 合同      纯语法的那一半：新出口不能不经声明而存在
              —— 它不声称能确立任何运行期属性
```

哪一条失守都不会被另外两条掩盖。

---

## 4. 请攻击这里 —— 只挑能改变结论的

1. **`ACCEPTED_BY_CAP` 那张表被写窄了没有。** §5 每一条的「代价」栏，
   有没有哪一条我描述得比事实轻？这是本轮价值最高的一条。
2. **多重集包含判据本身。** 找一条真实破坏 SILENT_DELETE_FORBIDDEN
   而 `before <= after` 仍成立的路径 —— 我知道的一条已在 §5。
3. **路径身份是否真的是路径。** `sys.settrace` 的末行 ＋ traceback 的 helper 行，
   是否存在两条不同路径映射到同一三元组？若有，覆盖声称就仍然偏宽。
4. **因果那一半。** 两轮没人打过它。说谎读技术能否被绕过？

---

## 5. 上限时仍站着的残留 —— **`ACCEPTED_BY_CAP`**

**读法**：下表每一条都**没有被解决**。标记的意思是**轮次用完了**，
不是有人判定代价可接受。若第 9 轮存在，它们就是该轮的起点。

| 残留 | 状态 | 代价 —— 它在什么情况下咬人 |
|---|---|---|
| 一次调用内「写了又还原」 | `ACCEPTED_BY_CAP` | 两端状态相同，任何 diff 都看不见。若某条路径先毁再重建字节，删除性质说不了话 |
| 状态不记录读 | `ACCEPTED_BY_CAP` | 因果全靠观测器的说谎读；观测器只包四个名字，绕过它就同时绕过因果那一半 |
| 观测器仍只包四个名字 | `ACCEPTED_BY_CAP` | 它已不承载删除性质，但**仍承载因果**。子进程／ctypes／提前绑定的局部名都能绕开 |
| 场景空间只有两根轴 | `ACCEPTED_BY_CAP` | 权限、目录占位、只读父目录未覆盖；「已存在的 divergent 名」已补，其余没有 |
| 非 Windows 上 ADS 测试全 skip | `ACCEPTED_BY_CAP` | 那里没有备用流可漏，但**CI 若只跑 Linux，这三条守卫等于不存在** |
| `DECLARED_EXITS` 顺序敏感 | `ACCEPTED_BY_CAP`（你第 4 轮同意接受） | 重排要改声明 |
| AST 合同只管声明卫生 | `ACCEPTED_BY_CAP` | 它不证明任何运行期属性；这是第 5 轮的裁定，不是新残留 |

**如果你认为其中任何一条不该是 `ACCEPTED_BY_CAP` 而是必须现在修，请直说。**
上限是 Aaron 的时间决定，不是技术判定 —— **他可以推翻他自己的上限**，
而推翻它需要一条具体理由，那条理由要由你给。

---

## 6. 交付要求

```
VERDICT=                     PASS|HOLD
WORDING_MAY_GO_TO_AARON=     YES|NO
SPECIFICATION_VERDICT=
ENGINEERING_QUALITY_VERDICT=
CAP_RESIDUAL_ASSESSMENT=     §5 那张表有没有把真残留写窄或写成已解决？逐条。
MUST_FIX_BEFORE_CAP=         §5 里有没有哪一条**不该**被 cap 接受，
                             必须现在修？给理由 —— 这条理由会直接送 Aaron。
CLAIM_COMMAND_MISMATCHES=    本文件里有没有哪条声称与其命令输出不一致？
SEAT_STATUS= / FORBIDDEN_PATHS_OPENED= / SOURCE_WRITES= / PERSISTED_SEARCH_OUTPUT=
```

**HOLD 仍然受欢迎，而它这一轮的含义不同**：前七轮的 HOLD 换来下一轮；
本轮的 HOLD 换来的是**一份带残留的交付**，除非 `MUST_FIX_BEFORE_CAP` 非空。
