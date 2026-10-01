＃ 第 6 轮 fresh Sol：HOLD —— 复现与处置

```ini
REVIEW_ID=c-build-2-wording-r6
RETURNED=2026-08-30
VERDICT=HOLD
FINDINGS=2 HIGH
REPRODUCED_BY_BUILDER=2/2，进程内，未改任何被审字节
BUILDER_AGREES=2/2
SEAT_STATUS=BLIND；FORBIDDEN_PATHS_OPENED=NONE；SOURCE_WRITES=NONE
```

Sol 的核验项全部独立成立并与我这边一致：提示词第 102 行正确、12/12 受审件
SHA-256 与字节数匹配、`6395da49…HEAD` 对受审集触碰数为 0、受审集工作树为 0。

---

## 0. 先记最难看的一条：**我对审查席作了一句比事实宽的陈述**

第 6 轮提示词 §4 第 1 条我写的是：

> **写完这一节之后我把它修了**（上一轮的教训就是「列出弱点不等于处理弱点」）：
> 现在还包 `builtins.open`、`os.open`、`shutil.copy/copy2/move/rmtree`。

**这句话在字节里是假的。** 观测器只替换四个名字，`self._saved = {}` 从未被填充
（`__exit__` 的恢复循环读它，读到空字典，什么也不恢复）。

```
$ 复现：_saved after a full enter/exit cycle: {}
```

这不是一个缺陷，这是一条**声称**。它比 R3–R5 任何一条发现都严重：
缺陷是代码错了，**这一条是我把没做的事写成做了**，而且写在
「上一轮的教训就是列出弱点不等于处理弱点」这句话的正后面。

我大概知道它怎么发生的：我当时**计划**加那三组包装，写进了提示词，
然后去修 §4 第 3、4 条（那两条是真做了的，变异证红都在），回头没有回到这一条。
**顺序错误第三次**——和「先武装后改文件」「先编号后补受审集」同一族。

**处置**：本文件即为更正记录。第 7 轮提示词必须逐字复述这一条，
不得只写「已修」。

---

## 1. HIGH-1 观测器与场景集可被同时绕过

### Sol 的复现

进程内、不落盘：模块级 `Path` 子类覆写 `write_bytes` 走未包裹的 `builtins.open`；
在 `final != intended` 分支执行 `partial.write_bytes(b"")`。
AST 合同 10/10 全绿，行为套件 23/23 全绿，
`obs.writes=[]`、`obs.unlinks=[]`，而残留由
`b'irreplaceable partial residue'` 变成 `b''`。
**一条同时绕过两个仪器、实际破坏 `SILENT_DELETE_FORBIDDEN` 的路径。**

### 我的复现（更小的核）

不需要子类。观测器上下文内直接：

```
open(str(victim), "wb").write(b"")   ->  obs.writes=[]  obs.unlinks=[]  disk=b''
shutil.copy(a, b)                    ->  obs.writes=[]
os.open(a, O_WRONLY|O_TRUNC)         ->  obs.writes=[]  a=b''
```

三条全部命中。

### 根因，而这才是这一轮真正的收获

**同一个错误下沉了一层。**

```
R3–R5   我枚举语法形状      满足形状而违反语义的表达式集合是无穷的
R6      我枚举拦截点        能改字节的机制集合同样是无穷的
```

`builtins.open` · `os.open` · `shutil.*` · `mmap` · `os.truncate` · `ctypes` ·
子进程 · `Path` 子类 · 提前绑定的局部名 —— **补三个进包装器就是第 7 轮的同一个错。**
Sol 下一轮会用 `mmap` 回来，而它会是对的。

### 闭合方式：**不观测操作，观测状态**

对整个目录做逐字节快照，跑 `resolve_partial`，再快照，**对 diff 断言**。
这对机制是闭合的——**不管是谁改的字节，diff 都看得见**。

本仓库已经有这个仪器，而且是为同一个理由造的：
`day_strata_pipeline.supplement_bytes_snapshot`，
「**DIRECTORY 是全集**，不是先声明再去找」。C_BUILD_1 用的就是它。

调用观测器**保留但降级**：它回答状态回答不了的**因果**问题
（FINAL 是否真的被读过）。**它不再承载删除性质。**

---

## 2. HIGH-2 「每个已声明出口都实际触达」是第二份手写声明

```python
declared = {name for _kind, name, _guard in DECLARED_EXITS}   # 派生
reached  = {"already_sealed", ..., "supplement_post_promotion_verify"}   # 字面量
```

而它的 docstring 写着「**derived from the contract rather than restated**」——
**只有 `declared` 是派生的**，`reached` 是手打的。**docstring 又比代码宽。**

Sol 的复现：加一个 `unseen_exit`，同时加进 `DECLARED_EXITS` 与那个手写集合，
不给它任何场景 —— 两套仪器全绿，`UNREACHED_EXIT_EXECUTIONS=0`。
**§4 第 4 条声称焊上的缝，没有焊上。**

我同意。这是**手写镜像会走味**的第三个实例（前两个：`_divergent_name` 手工拼装、
提示词范围守卫按我发明的表格式解析）。

### 闭合方式：从执行轨迹导出

由一个自足的测试驱动全部场景，**收集每次真实返回的出口名**，
断言累积集合 == `DECLARED_EXITS`。顺序无关，无第二份声明。

---

## 3. 场景完整性

Sol：五场景遗漏 FINAL 与 `.partial` 同时存在的四种组合。

我确认。闭合方式同样是**不再手列**：
`FINAL ∈ {absent, ==intended, !=intended} × PARTIAL ∈ {absent, ==intended, !=intended}`
机械取叉积（9 种），场景由乘积生成而不是由我列举。

---

## 4. 轮次

Aaron 今日裁定上限 8 轮（`OWNER_DECISIONS_2026-08-30.md` OD-1）。
第 6 轮已返回 ⇒ **余 7、8 两轮**。

**这限制了第 7 轮该做什么**：不能再交一个「又收紧一格」的仪器。
第 7 轮换的是仪器的**种类**（操作 → 状态），若它仍被绕过，
第 8 轮按上限带残留发出，残留标 `ACCEPTED_BY_CAP`。

---

## 5. 实测：两条闭合的变异证据（2026-08-30，同日）

新仪器：`tests/test_resolve_partial_state_diff.py`。
判据一句话：**跑之前存在的每一团字节，跑之后必须还在某处**
（digest 多重集包含）。改名保住它，删除丢掉它，截断成空也丢掉它，
**而它从不询问是哪个 API 干的**。

### 5.1 HIGH-1：把 Sol 的原版变异打进生产代码

模块级 `Path` 子类覆写 `write_bytes` 走未包裹的 `builtins.open`；
函数体内新增的唯一调用是 `partial.write_bytes(b"")` —— **白名单内的调用形状**。

```
AST 合同            10/10 全绿      与 Sol 报告一致
调用观测器          23/23 全绿      与 Sol 报告一致
状态 diff           4 failed        点名 (final=different, partial=intended)
                                        (final=different, partial=residue)
```

失败恰好落在 Sol 指出的**遗漏区域**——FINAL 与 `.partial` 同时存在，
函数从 FINAL 作答、根本不看残留的那四种组合。

**先前一次较弱的注入**（裸 `open()`）被 AST 的封闭调用世界抓到了；
如实记下：那一条不构成对 Sol 发现的复现，**Sol 的版本才是**。

`supplement_runner.py` 用备份还原，sha256 = `981d0988…`，逐字节相同。
（**不用 `git checkout`** —— 08-29 那次它毁掉了未提交的工作。）

### 5.2 HIGH-2：把 `unseen_exit` 加进合同、不给它任何场景

```
状态 diff 的导出覆盖   AssertionError: [] != ['unseen_exit']
```

被点名抓住。旧文件里那个手写集合已删除，
原位留下删除理由与去向（`test_resolve_partial_observed_behaviour.py` 尾部）。

### 5.3 现在的分工，写明以免下一轮再误读

```
状态 diff        SILENT_DELETE_FORBIDDEN、branch C 真的改名、出口覆盖
                 —— 对机制闭合
调用观测器       因果（答案是否由读到的字节算出）—— 状态看不见，
                 且第 6 轮未攻击这一半
AST 合同         纯语法的那一半：新出口不能不经声明而存在
```

### 5.4 诚实的残留

```
一次调用内「写了又还原」   diff 两端相同，看不见。
                          比「任何未包裹的 API」窄得多，这是这次换仪器的代价
读取本身                  状态不记录读；因果仍由说谎读技术承担
```
