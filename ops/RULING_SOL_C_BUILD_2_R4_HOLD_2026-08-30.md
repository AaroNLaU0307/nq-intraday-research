＃ 第 4 轮 C_BUILD_2 措辞复审 —— fresh Sol，VERDICT=HOLD

```ini
RECORD_TYPE=REVIEW_OUTCOME ＋ 复现证据
REVIEW_ID=c-build-2-wording-r4
RETURNED=2026-08-30
VERDICT=HOLD          WORDING_MAY_GO_TO_AARON=NO
CONTRACT_CLOSURE_ASSESSMENT=NO
SEAT_STATUS=BLIND     PERSISTED_SEARCH_OUTPUT=NONE     SOURCE_WRITES=NONE
```

**四条发现全部成立，全部复现在先。builder 无一条辩解。**

## 0. 它一句话说中了根因

> 合同推导是**路径不敏感的集合**，并且**只识别有限的调用语法**；
> 它仍会把「同形但语义不同的路径」折叠掉。

我上一轮在 §4 自陈了五个「最可能仍然错的地方」，**第 1 条和第 2 条正是这两个根因**。
我看见了它们，写下了它们，**然后没有去修**。这一点比被打穿本身更值得记：
**列出弱点不等于处理弱点。**

## 1. HIGH ①：义务 (a) 可在合同 12/12 全绿时失效

注入（与既有路径**守卫串完全同形**）：

```python
if final.exists():
    existing = intended            # 不是读，是赋值
    if existing == intended:
        return PartialAction("already_sealed", detail="mutant-no-read")
```

**复现：12 passed。** 两个原因叠加：

```
出口存进 set     -> (kind, action, guard) 相同的新路径被去重掉，看不见
溯源是函数级     -> 只证明"函数里某处有 existing = final.read_bytes()"，
                    不证明"这条路径上的 existing 来自那次读"
```

## 2. HIGH ②：义务 (b)/(c) 经可调用对象绕过

注入（`_preserve` 之后）：

```python
next(iter((Path.unlink,)))(out / preserved)
```

**复现：12 passed。** `preserved_as=` 照常返回，**而文件已被删除**。
我上一轮拒绝了函数内所有 `getattr`，但那只挡住一种形状 ——
**黑名单是开放世界**，删除动作作为**值**被调用，任何名字检查都看不见。

## 3. MEDIUM ①：64-hex 正则只认小写

```
UPPERCASE_64HEX  TESTS=2 FAILURES=0    <- 绕过
LOWERCASE_64HEX  TESTS=2 FAILURES=1    <- 才拦住
```

上一轮我把 base64／分段书写称为「越过了合理伪装的界」，**并标明那是判断不是证明**。
**大写 SHA-256 根本不在那一类** —— 它是无数工具的常规输出，而我的判断没有覆盖它。

## 4. MEDIUM ②：`REVIEWED_SET_UNCHANGED_SINCE=dba55d9` 是错误自报

```
dba55d9..HEAD 触碰了 tests/test_resolve_partial_path_contract.py
触碰它的提交： eab7992 "attack my own fix with Sol's objection..."
```

**八个哈希前缀全对，工作树也干净 —— 错的是 range 声称本身。**
而那个提交正是我自己「加固合同」的那一次。

这是这一晚同一形态最直白的一次：**声称比事实宽**。而复审席被告知要**信任那一行**。

## 5. 修法 —— 打根因，不打那四个例子

| 根因 | 修法 |
|---|---|
| 路径不敏感 ＋ set 去重 | 出口改为**有序列表**，逐位比对；每个出口携带**它自己路径上可见的绑定**；义务 (a) 用该路径的绑定回答 |
| 开放世界的调用识别 | **封闭调用世界**：`resolve_partial` 与两个助手内，每个调用必须匹配少数几种**形状**（`Name(...)` / `x.attr(...)`）且 callee 在白名单内。callee 是 Call／Subscript／Lambda 一律拒绝，**不需要知道它解析成什么** |
| 小写正则 | 改为大小写不敏感并归一化比较 |
| 手写 range 声称 | `tests/test_a_prompts_range_claim_actually_holds.py`：任何 **LIVE** 提示词的 range 声称由 git 机械核实；pin 改为**发行时才填** |

路径敏感的前提（目标函数无循环）由 `test_the_target_is_still_loop_free` 守着 ——
有循环时线性遍历只是近似，那时义务就在声称它没检查的东西。

## 6. 修后验证 —— 两个 HIGH 各被两条独立机制抓到

```
HIGH ①  出口列表多出一条  ＋  路径局部溯源：
        "on THIS path 'existing' is bound to 'intended', which is not a read"
HIGH ②  封闭世界形状规则：
        "callee is a Call -- not a plain name or attribute"
        ＋ next 不在允许的名字里
```

## 7. 席位

第 6 行，`NOT_EXPOSED`，且 `PERSISTED_SEARCH_OUTPUT=NONE`。
**第 5 行那次事故的成因（禁区只写成散文）在本轮 §0 改成了可执行的检索边界，
本行就是该修复生效的量度。**

## 8. 下一步

`ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND5.md`。
**第 4 轮的提示词字节一字未改地封存** —— 它是被据以裁决的材料。
