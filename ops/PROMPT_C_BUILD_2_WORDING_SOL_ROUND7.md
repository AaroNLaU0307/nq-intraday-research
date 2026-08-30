＃ C_BUILD_2 措辞复审 · 第 7 轮 —— fresh Sol

```ini
REVIEW_ID=c-build-2-wording-r7
DELIVERY_STATUS=PREPARED_NOT_ISSUED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审第 7 轮）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            **第 1–6 轮 c-build-2-wording* 的任何会话**；
            N09 R2/R3 的任何前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
ROUND_CAP=8（Aaron 2026-08-30 裁定 OD-1）——本轮之后只剩一轮
```

**READ THIS PROMPT FROM DISK, not from a paste.**
**绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND7.md`

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

禁区清单随包交付：`ops/OFF_LIMITS_COMPANION_R7.md`，请一并读。
检索边界与逐条禁区见该件，本文件不复述。

**权威登记册**：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
点名它是为了让你**有东西可以对照**——只读交付件却无从核对任何路径，
本身就是 D-2 那次烧掉席位的形状。

---

## 0. 本轮的新纪律，因为上一轮我骗了你

**第 6 轮 §4 第 1 条我写的是**：

> 写完这一节之后我把它修了：现在还包 `builtins.open`、`os.open`、
> `shutil.copy/copy2/move/rmtree`。

**这句话在字节里是假的。** `self._saved = {}` 从未被填充，
`__exit__` 的恢复循环读到空字典，四个名字之外什么也没包。
你实测出来了，你是对的。

这不是缺陷，是**声称**。缺陷是代码错了；这一条是我把没做的事写成做了，
而且写在「上一轮的教训就是列出弱点不等于处理弱点」的正下方。
成因是顺序：我把**计划**写进提示词，转去修 §4 第 3、4 条（那两条是真做了的），
再没回来。**同一族顺序错误的第三次**。

**所以本轮起，每一条声称旁边挂一条你可以直接跑的命令。**
没有命令的段落标 `[意见]`，不算声称，你可以不当证据看。
如果某条命令的输出和它旁边的话不一致，**那一条按假处理，并请点名**。

---

## 1. 你上一轮判 HOLD，两个 HIGH 全部复现

证据与逐条处置：`ops/RULING_SOL_C_BUILD_2_R6_HOLD_2026-08-30.md`（在受审集内）。

### 1.1 六轮六个 HOLD，而形状是同一个，只是下沉了一层

```
R3–R5   我枚举语法形状        满足形状而违反语义的表达式集合是无穷的
R6      我枚举拦截点          能改字节的机制集合同样是无穷的
```

`builtins.open` · `os.open` · `shutil.*` · `mmap` · `os.truncate` · `ctypes` ·
子进程 · `Path` 子类 · 提前绑定的局部名。

**把那三个补进包装器就是第 7 轮的同一个错**，而你下一轮会用 `mmap` 回来。
所以本轮换的不是紧度，是**仪器的种类**。

### 1.2 换成：不观测操作，观测状态

`tests/test_resolve_partial_state_diff.py`。整个目录逐字节快照，
跑真实的 `resolve_partial`，再快照，**对 diff 断言**：

```
跑之前存在的每一团字节，跑之后必须还在某处
```

digest 的**多重集包含**。改名保住它（branch C 正该改名），
删除丢掉它，截断成空丢掉它，同长覆写也丢掉它。
**它从不询问是哪个 API 干的**，所以没有可绕的名字表。

这不是新发明：`day_strata_pipeline.supplement_bytes_snapshot` 是同一个仪器，
为同一个理由造的，C_BUILD_1 一直这么断言。resolve_partial 本来就该这么做。

```
核验  python -m pytest tests/test_resolve_partial_state_diff.py -q
预期  16 passed, 13 subtests passed
```

### 1.3 用你的原版变异打三个仪器

模块级 `Path` 子类覆写 `write_bytes` 走未包裹的 `builtins.open`；
函数体内新增的唯一调用是 `partial.write_bytes(b"")`，白名单内的形状。

```
AST 合同        10/10 全绿      与你报告一致
调用观测器      23/23 全绿      与你报告一致
状态 diff       4 failed        点名 (final=different, partial=intended)
                                    (final=different, partial=residue)
```

失败恰好落在你指出的遗漏区域。
`supplement_runner.py` 用备份还原，sha256 `981d0988…`，逐字节相同。

**如实交代**：我先试过一条更弱的注入（裸 `open()`），它被 AST 的封闭调用世界
抓到了 —— 那一条**不构成**对你发现的复现，**你的版本才是**。

```
核验  复现步骤逐字写在 ops/RULING_SOL_C_BUILD_2_R6_HOLD_2026-08-30.md §5.1
```

### 1.4 场景集不再由我列

```
FINAL   ∈ {absent, ==intended, !=intended}
PARTIAL ∈ {absent, ==intended, !=intended}
```

机械取叉积 = 9 种，其中就包含你点名的**两者同时存在的四种**。

```
核验  python -c "import sys;sys.path[:0]=['tests','src'];import test_resolve_partial_state_diff as t;both=[x for x in t.SCENARIOS if 'absent' not in x];print(len(t.SCENARIOS), len(both), both)"
预期  9 4 [('intended','intended'), ('intended','residue'), ('different','intended'), ('different','residue')]

      **这条命令的第一版我写错了**（漏了 `src`，直接 ModuleNotFoundError）。
      是 §0 的纪律在发行前抓到的 —— 一条跑不通的核验命令，
      和一句没做的事写成做了，是同一种东西。
```

### 1.5 HIGH-2：手写的 `reached` 已删除，声称改为从执行导出

旧的 `test_every_declared_exit_NAME_is_reached_by_some_test` 已删除，
原位留下删除理由与去向。新的判据里 `reached` 由每次**真实运行**返回或抛出的
出口名累积而成，`declared` 仍从 `DECLARED_EXITS` 导出。

```
核验  把 ("raise", "unseen_exit", "") 加进 tests/test_resolve_partial_path_contract.py
      的 DECLARED_EXITS，然后
      python -m pytest tests/test_resolve_partial_state_diff.py::TestEveryDeclaredExitIsReachedBYEXECUTION -q
预期  AssertionError: Lists differ: [] != ['unseen_exit']
      （我这边实测即此。记得改回去，或用进程内变异）
```

---

## 2. 受审集

```
REVIEWED_SET_UNCHANGED_SINCE=<发行时填入>
```

**语义**：该 commit 之后没有任何 commit 触碰过下表的参考件。
本提示自身不在该 range 内（发出 delivery 就是对它的一次提交，无不动点）。

| sha256 | bytes | 路径 |
|---|---|---|
| <发行时填入> | <发行时填入> | `src/itsf/mc/supplement_runner.py` |
| <发行时填入> | <发行时填入> | `src/itsf/mc/supplement_contract.py` |
| <发行时填入> | <发行时填入> | `tests/test_resolve_partial_state_diff.py` |
| <发行时填入> | <发行时填入> | `tests/test_resolve_partial_observed_behaviour.py` |
| <发行时填入> | <发行时填入> | `tests/test_resolve_partial_path_contract.py` |
| <发行时填入> | <发行时填入> | `tests/test_a_prompts_range_claim_actually_holds.py` |
| <发行时填入> | <发行时填入> | `tests/test_the_register_speaks_one_vocabulary.py` |
| <发行时填入> | <发行时填入> | `tests/test_the_review_round_cap_is_respected.py` |
| <发行时填入> | <发行时填入> | `tests/test_every_sealed_final_was_read_back.py` |
| <发行时填入> | <发行时填入> | `tests/test_c_build_2_wording_coverage.py` |
| <发行时填入> | <发行时填入> | `ops/RULING_SOL_C_BUILD_2_R6_HOLD_2026-08-30.md` |
| <发行时填入> | <发行时填入> | `ops/OWNER_DECISIONS_2026-08-30.md` |
| <发行时填入> | <发行时填入> | `ops/OFF_LIMITS_COMPANION_R7.md` |

**delivery**：`ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND7.md`，
字节见 `ops/ARTIFACTS_UNDER_REVIEW.json`。

**本轮重点受审件是第三行** `test_resolve_partial_state_diff.py` —— 换掉的那个仪器。

**核对你读的是当前文件**：line <发行时填入> of it must read
`REVIEWED_SET_UNCHANGED_SINCE` 那一行。对不上 ⇒ 陈旧粘贴 ⇒ **STOP**，回磁盘重读。

---

## 3. 现在三个仪器的分工，写明以免被误读为冗余

```
状态 diff     SILENT_DELETE_FORBIDDEN、branch C 真的改名、出口覆盖
              —— 对机制闭合，不问是谁改的字节
调用观测器    因果：答案是否由**读到的**字节算出（说谎读技术）
              —— 状态 diff 看不见读，这一半你第 6 轮也没攻击
AST 合同      纯语法的那一半：新出口不能不经声明而存在
              —— 它已不再声称能确立任何运行期属性
```

**三者不是同一层的三道补丁**：删除性质只由状态承担，
因果只由观测器承担，声明卫生只由合同承担。哪一条失守都不会被另外两条掩盖。

---

## 4. 请攻击这里

1. **状态 diff 的判据本身。** 我用的是 digest 多重集包含。
   请找一条**真实破坏了 SILENT_DELETE_FORBIDDEN、而多重集包含仍然成立**的路径。
   我知道的一条已写在 §5（一次调用内写了又还原）——请找我不知道的。
2. **快照的全集。** `snapshot()` 走 `root.rglob("*")` 只收 `is_file()`。
   符号链接、硬链接、目录本身、`out_dir` **之外**的写入 —— 我没有覆盖。
   `resolve_partial` 的 docstring 声称「Every write this function performs lands
   under `out_dir`」，**而我的仪器只看 `out_dir` 之内**：这句声称本身没有被任何东西证过。
   这可能是本轮最真的缝。
3. **导出的出口覆盖。** `_reached()` 里有两条出口靠说谎读驱动
   （branch E 与 post-promotion verify）。那是**干预**，不是自然状态。
   请检查该干预是否让覆盖声称变得循环。
4. **叉积是否是正确的状态空间。** 我用 `{absent, ==intended, !=intended}` 两轴。
   若真实状态空间还有第三根轴（权限、目录占位、已存在的 divergent 名、
   零字节 vs 不存在），叉积就仍然是我列的，只是列得体面一点。

---

## 5. 本轮接受的残留

| 残留 | 为什么接受 | 代价 |
|---|---|---|
| 一次调用内「写了又还原」 | 两端状态相同，任何 diff 都看不见；挡它要回到调用拦截，而那正是本轮否定的路线 | §4 第 1 条 |
| 状态不记录读 | 读不改变状态；因果由观测器的说谎读承担 | 分工见 §3 |
| 观测器仍只包四个名字 | **本轮没有扩它**，因为扩它就是重犯 R6 的错；它已不承载删除性质 | 若你能证明因果那一半也可被绕过，那是真发现 |
| `DECLARED_EXITS` 顺序敏感 | 你第 4 轮同意接受 | 重排要改声明 |

---

## 6. 交付要求

沿用第 6 轮字段，另加：

```
INSTRUMENT_KIND_ASSESSMENT=  从「观测操作」改为「观测状态」，是否闭合了 R6 的绕过类？
                             若否，给出一条真实破坏 SILENT_DELETE_FORBIDDEN
                             而多重集包含仍成立的路径，并跑出来。
OUT_DIR_CLAIM=               §4 第 2 条：runner 声称所有写入都落在 out_dir 之内。
                             这句话有被任何东西证过吗？
CLAIM_COMMAND_MISMATCHES=    §0 的新纪律：本文件里有没有哪一条声称，
                             其旁边的命令跑出来和它说的不一致？逐条列。
```

**HOLD 受欢迎。** 前六轮都是 HOLD，每一轮的发现都成立。

**但请知道轮次是有限的**：Aaron 2026-08-30 裁定上限 8 轮，本轮之后只剩一轮。
到第 8 轮措辞按当时最好的状态发出，仍站着的残留标 `ACCEPTED_BY_CAP`
（意思是**轮次用完了**，不是**有人判定代价可接受**）。
所以本轮请优先给**能改变结论的**发现，而不是穷举式的完整性。
