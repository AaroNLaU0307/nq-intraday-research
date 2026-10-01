＃ 第 3 轮 HOLD 的两条发现 —— 复现在先，采信在后

```ini
RECORD_TYPE=REPRODUCTION_EVIDENCE
REVIEW_ID=c-build-2-wording-r3
VERDICT=HOLD（两条发现，builder 全部接受）
METHOD=不采信席位自陈。每一条先自己跑出来，再动手修。
```

## 0. 第一次复现是**错的**，这件事比结论更值得记

我第一次照 Sol 的描述注入变异 —— 「在 docstring 后新增一条写 FINAL 却不回读的
`already_sealed` 早退」—— 结果 **12 failed / 24 failed，全红**。

红了不等于 Sol 错了，**等于我复现的不是它的变异**。

差别在守卫条件：我的注入对测试实际使用的文件名生效，于是行为测试立刻抓住。
Sol 的新路径守在一个**现有测试从不满足**的条件上 —— 所有既有场景仍走原路径，
行为测试全绿，而声称「枚举了所有路径」的结构守卫看不见新路径的存在。

照这个理解重做，**59/59 全绿，与 Sol 一字不差**。

**如果我停在第一次，我会写下「无法复现」，而缺陷仍在。**

## 1. HIGH —— C_BUILD_2 的路径覆盖不是失败闭合

### 复现（五文件套件，基线 59 passed）

```
MUT-a  新增分支：写 FINAL，从不回读，返回 already_sealed        -> 59/59 GREEN
MUT-b  新增分支：getattr(p,'unlink')() 删除 .partial，
       返回 retry_permitted                                     -> 59/59 GREEN
```

两条均以 `if incident_id == 'INC-ffffffffffff':` 守卫 —— 一个没有测试会传的值。

### 为什么两边都看不见

```
行为测试     只驱动既有场景 -> 新分支从不执行
结构守卫     枚举既有路径   -> 新分支不在枚举里，而枚举就是它的全集定义
```

Sol 的原话：「这些测试再次把**我列出的现有路径**当成**所有可能路径**。」

### 修法 —— 按 Sol 的要求，不是把两个反例追加成用例

`tests/test_resolve_partial_path_contract.py`：一份**封闭的出口合同**。

每个 `return`／`raise` 由 AST 导出为 `(kind, action-or-code, guard source)`，
导出集合必须**等于**声明集合 `DECLARED_EXITS`。**新增一条出口即变红**，
直到作者把它写下来并回答三条义务：

```
(a) 回答 already_sealed 的路径，必须读过 FINAL 并与 intended 比较过
    —— 且比较的那个名字必须是从磁盘读来的，不是有人赋的值
(b) 任何路径都不得摧毁 .partial（SILENT_DELETE_FORBIDDEN=YES）
    —— 含 getattr 动态到达；本文件干脆拒绝该函数内的**任何** getattr，
       因为合同看不出计算出来的名字会解析成什么
(c) 回答 retry_permitted 的路径，必须 preserved_as= 一个由 _preserve 绑定的名字
    —— 空字符串会通过「有这个关键字」但什么都没保全
```

合同**跟着调用走**，覆盖 `_preserve` 与 `_divergent_name`：
停在函数边界的合同只会把删除赶到低一层。

### 修后验证 —— 四个变异，各被正确的那条抓到

```
Sol (a) 新路径不回读 FINAL            -> 封闭出口集（出现了未声明的出口）
Sol (b) getattr unlink                -> 动态属性拒绝 ＋ 封闭出口集
Sol (c) retry_permitted 空 preserved  -> 封闭出口集 ＋ preserved_as 检查
额外    朴素 .unlink()                -> 直接破坏性调用检查
```

## 2. MEDIUM —— 批准守卫的探测域与它的声称不符

### 复现（`test_every_approval_is_accounted_for.py`，基线 8 passed）

```
规范字段批准  APPROVED_FAKE_PROFILE_SHA256=<64hex>   -> 1 failed（Sol 说会红，确实红）
散文式批准    「其 SHA-256 为 <64hex>，绑定到文档 HEAD <40hex>」 -> 8/8 GREEN
```

### 修法：加宽**探测域**，同时把**声称**缩窄

字段形状的模式，总能靠不用那个字段绕过去。所以探测域改为**哈希本身**：
记录里任何一个 64 位十六进制，都必须是本文件审查过的批准。

实测：记录里 4 个 64-hex，字段声明 4 个，已审 4 个 —— **零误报**，
免了一份会腐烂的豁免清单。

两个反例现在都变红，包括「一个裸哈希、连散文都没有」。

### 剩下的、修不掉的那一半，写下来而不是留给下一个复审再发现一次

这个扫描**只读一个文件**。批准若记在**别处**，它管不着，而且一直如此。

要闭合它需要 `SIGNABLE_RATIFICATION_ROUTES=1`（「批准只在追加进本记录后生效」）
成为**权威、冻结、机械强制**的治理不变量，而今天它是 builder 自陈。
**Sol 把这一条列为 `UNRESOLVED_FOR_AARON`。** 在它被裁定前，
本文件的诚实声称是「**记在这里的**每份批准」，不是「每份批准」。

## 3. 一条对 builder 有利的事实，如实记下而不当作抵消

`CONDITIONS_MET` 第 4 条 **MET**：裁定记录 commit 之后
`supplement_runner.py` 与 `supplement_contract.py` **零提交、零 diff**。

08-29 通宵里我确实动了 `supplement_runner.py` 一次（C_BUILD_1 接线），
**冻结登记册在提交前抓住并挡了回去**，补丁停放到本轮返回。
见 `ops/PREPARED_C_BUILD_1_GATE_WIRING.md`。
