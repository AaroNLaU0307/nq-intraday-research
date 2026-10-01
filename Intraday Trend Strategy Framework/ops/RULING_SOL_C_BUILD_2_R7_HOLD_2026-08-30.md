＃ 第 7 轮 fresh Sol：HOLD —— 复现与处置

```ini
REVIEW_ID=c-build-2-wording-r7
RETURNED=2026-08-30
VERDICT=HOLD
FINDINGS=3 HIGH
REPRODUCED_BY_BUILDER=3/3，进程内，未改任何被审字节
BUILDER_AGREES=3/3
CLAIM_COMMAND_MISMATCHES=5（席位列出），builder 认 5/5
SEARCH_BOUNDARY_COMPLIANCE=NO（席位主动申报，见席位轴台账第 12 行）
```

Sol 的核验项全部独立成立：提示词第 155 行匹配、13/13 受审件 SHA-256 与字节数匹配、
`18d59b…→909dc61` 对受审集触碰数 0、工作树为空。

---

## 0. 最难看的一条：**第 4 轮教过的东西，我在第 7 轮亲手犯回去**

`DECLARED_EXITS` 的注释逐字写着：

> **A list, never a set: two paths that look identical are two exits,
> and collapsing them is what round 4 walked through.**

**而我在导出覆盖时写的是** `declared = {name for _kind, name, _guard in DECLARED_EXITS}`。

那条注释就在列表正上方。**我读过它、在它下面写了文件、然后照样折叠。**

第 6 轮的错是「手写集合冒充导出」；第 7 轮的错是「导出了，但导出到了错误的粒度」。
**后者更糟**：它看起来像修好了。

---

## 1. HIGH-1 出口覆盖仍是名字级，不是路径级

### 复现（行号即路径身份）

```
branch C  divergent_partial_exists   runner 行 959
branch C  incident_id_malformed      runner 行 959
branch E  divergent_partial_exists   runner 行 968     <- 从未执行过
branch E  incident_id_malformed      runner 行 968     <- 从未执行过
DECLARED_EXITS 条目 10，去重后名字 8   =>  丢掉 2 条声明路径
```

Sol 的 `BRANCH_E_*_REACHED=False` 与 `DUPLICATE_UNREACHABLE_SUCCESS=True` 全部成立。

### 闭合：**路径身份 = (名字, 出口行, helper 内 raise 行)**，两侧全部导出

```
声明侧   walker 现在把 Call 节点与 helper 的 raise 行一起带出
         (_helper_exits 传 node；_raises_of 返回 node.lineno)
运行侧   sys.settrace 记录 resolve_partial 自身帧执行过的行，末行即出口行；
         traceback 里 runner 内非 resolve_partial 的帧给出 helper raise 行
```

`12 条声明 → 12 个唯一三元组`，运行侧实测**全部命中**。

### 变异证红（比 Sol 的更强的形式）

往 runner 里加一条**真实存在但不可达**的第二个 `divergent_partial_exists`：

```
AssertionError: [] != [('divergent_partial_exists', 1012, None)]
```

被逐条点名。R7 发出的那一版对同一变异是 `DUPLICATE_UNREACHABLE_SUCCESS=True`。

**非空过守卫也补了**：`sys.settrace` 在某些 runner 下静默失效，
届时每个路径身份都会退化成 `(name, None, ...)` 而看起来仍然健康 ——
所以先断言 tracer 真的记到了行，并断言声明侧确实存在重名
（否则这个文件的前提本身是空的，那就该删前提而不是让它绿着）。

---

## 2. HIGH-2 NTFS 备用数据流

### 复现

```
snapshot entries : ['residue.partial']      而 x:evidence 里有真实字节
```

Sol 的 `MAIN_BYTES_SURVIVE=True / ADS_SURVIVES=False` 成立。

### 闭合：**枚举，而不是收窄声称**

收窄成「仅默认数据流」是诚实的，也更便宜 —— 但那会**把真实字节留在治理目录里无人看管**。
所以走 `FindFirstStreamW`（OS 自己对「这个文件有哪些流」的回答），
全集仍然是**文件**，而不是我记得写下来的流名清单。

```
snapshot 现在把命名流按 file:stream 作为独立 key 记入
非 Windows 返回空 —— 那里本来就没有备用流可漏
```

### 变异证红

```
关掉枚举 =>  3 条变红，含 Sol 的原案
            （删 .partial、以相同主字节重写 final，ADS 消失）
```

并加 `TestTheStreamWalkIsREAL`：**ctypes 绑定坏掉与「没有流」不可区分**，
所以要求它在本平台上真的找到一条真的写进去的流。

---

## 3. HIGH-3 `out_dir` 声称被证伪 —— 这是**生产缺陷**，不是仪器问题

### 复现

```
resolve_partial(out, "../escaped.json", ...)  ->  promote
OUT_SNAPSHOT_BEFORE/AFTER = {} / {}    BLOBS_LOST = []
ESCAPED_EXISTS = True                  ESCAPED_UNDER_OUT = False
```

docstring 声称「Every write this function performs lands under `out_dir`」，
`filename` 却**从未被校验**。

**这句声称本身不是缺陷，缺失的校验才是 —— 而声称正是让没人去找它的原因。**

### 闭合：两半都补

```
生产   _require_plain_name(filename)：空 / "." / ".." / 非自身 basename /
       含分隔符或冒号  =>  filename_not_a_plain_name
仪器   快照根改为 out_dir 的父目录 —— 越界写入本来就在快照视野之外
```

九种形式实测全部拒绝（`../x`、`a/b`、`C:/abs`、UNC、`sub\x`、`""`、`.`、`..`、
`x.json:evidence`），`out_dir` 之外零字节，正常文件名照常 `promote`。

冒号那一条同时关掉 HIGH-2 的生产半边：**runner 已无法再创建一个 ADS**。

### 合同当场起作用

新出口一加，AST 合同立刻报「调用不在封闭世界内」与「出口清单不匹配」，
并把 helper 的**两个** raise 点各算一条路径。两条都按声明补进 `DECLARED_EXITS`，
`_require_plain_name` 作为**有意行为**加入允许调用名单（只读、只抛）。

---

## 4. CLAIM_COMMAND_MISMATCHES —— 5 条，我全认

```
1  §1.3 写「调用观测器 23/23」，实为 22        <- 我删掉了那个手写 reached 测试，
                                                 却没有回头改这个数字。
                                                 写的时候是真的，发的时候是假的。
2  python 不在该会话 PATH                       环境，非声称
3  场景计数 9/4 精确匹配                        一致
4  §1.3 的「核验」只是指向文字，不是可跑命令     应标 [意见]，是我的规则我自己没守
5  §1.5 要求落盘改受审测试，与 SOURCE_WRITES=NONE 冲突
```

**第 1 条和第 4 条是 §0 那条新纪律要抓的东西，而它们出现在同一份宣布该纪律的文件里。**
第 1 条尤其：**一个数字在写下时为真、在交付时为假**，
和第 6 轮那句「已修」是同一个成因 —— 改了别处，没有回到已经写好的段落。

**处置**：第 8 轮的数字全部在**发行那一刻**重新测量后填入，不复用任何早先测得的值。

---

## 5. 检索边界违例 —— **是我的缺陷，同一形态第四次**

席位主动申报：其额外执行的五个治理测试内部使用 `ops/` glob，
间接打开了 §2 之外的 `ops/N09_EXECUTION_PATH_DESIGN_R3.md`。
按权威登记册，未打开任何 outcome-carrying 路径，故仍为 `BLIND`；
但本轮**不得被表述为完全合规的认证席** —— 席位自己就是这么说的。

**成因不是席位不小心。** `OFF_LIMITS_COMPANION_R7.md` 把「禁止 ops/ 全目录枚举」
写成了对**人**的约束，而**我要求他跑的治理测试本身**就在做这件事
（`test_ops_index_is_complete` 走 `OPS.rglob("*.md")`）。

> **我要求席位遵守一条我自己的测试代码违反的边界。**

已记入席位轴台账第 12 行（研究轴不动 —— 烧席位不消耗研究自由度）。
第 8 轮随包件必须写明：**哪些治理测试会枚举 `ops/`，跑它们不算违例**。

---

## 6. 顺带修掉的两件

```
席位轴台账 id 4–6 各出现两次（早前会话在 4 号重启编号），我这次又撞了 7/8/9
=>  我的三行改为 10/11/12；旧行不改（追加式）；
    新增 tests/test_the_seat_ledger_ids_are_unique.py，冻结已有碰撞、拒绝新的
```

行号被按编号引用（「成因同第 6 行」），**重复编号会让引用同时指向一次干净席位和一次事故**。

---

## 7. 轮次

```
已用 7   剩 1
```

第 8 轮是最后一轮（Aaron OD-1）。**这限制了它该问什么**：
不是穷举完整性，而是**还有没有能改变结论的东西**。
仍站着的残留届时标 `ACCEPTED_BY_CAP` —— 意思是轮次用完了，不是有人判定代价可接受。
