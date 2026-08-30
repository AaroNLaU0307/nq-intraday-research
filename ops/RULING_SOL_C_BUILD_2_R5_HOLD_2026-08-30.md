＃ 第 5 轮 C_BUILD_2 措辞复审 —— fresh Sol，VERDICT=HOLD

```ini
RECORD_TYPE=REVIEW_OUTCOME ＋ 复现证据
REVIEW_ID=c-build-2-wording-r5      RETURNED=2026-08-30
VERDICT=HOLD                        WORDING_MAY_GO_TO_AARON=NO
SPECIFICATION_VERDICT=FAIL          ENGINEERING_QUALITY_VERDICT=FAIL
CONTRACT_CLOSURE_ASSESSMENT=NO
SEAT_STATUS=BLIND  OUTCOME_EXPOSED=NONE  PERSISTED_SEARCH_OUTPUT=NONE
SOURCE_WRITES=NONE  FORBIDDEN_PATHS_OPENED=NONE
```

**四条全部成立、全部复现。三个 HIGH 各自 10/10 全绿。**

## 0. 这一轮让我看见的不是四个缺陷，是五轮共同的错

```
R3  路径是被枚举的，不是被闭合的
R4  集合去重 ＋ 开放世界的调用识别
R5  词法匹配不是数据流；封了 callee 名字没封接收者/参数/效果；
    helper 控制流没有可达性概念
```

每轮我把**语法**收紧一格，每轮它写出**满足更紧语法、违反语义**的代码。

**根因是我的**：「这条路径回答 `already_sealed` 之前读过 FINAL」是**运行期属性**。
对任何我要求的形状，满足形状而违反语义的表达式集合都是**无穷**的。
**五轮收紧语法，是五轮在解错的问题。**

而它的验证方法一直在说这件事 —— 每个反例都是**直接执行并计数**。

## 1. 三个 HIGH（复现结果均为 10/10 GREEN）

| # | 注入 | 真实后果 |
|---|---|---|
| ① | `existing = ((final.read_bytes, intended)[1] if incident_id == "…" else final.read_bytes())` | 文本含 `read_bytes` 与 `final`，**该路径读盘 0 次** |
| ② | `(out / preserved).write_bytes(intended[:0])` | `write_bytes` **在白名单里**；行里仍写 `preserved_as`，文件已被清空 |
| ③ | `_preserve` 前置 `return path.name` | 改名从未发生，`.partial` 原地未动，`BRANCH_C_RENAME_THEN_ALLOW_RETRY` 不成立 |

## 2. MEDIUM：range 守卫的两个 false green

```
ISSUED 但无 pin      -> 旧版 `if not pin: continue`，零 git 调用
表中有已删除路径      -> 旧版 `.exists()` 过滤，该行从不被查询
```
读代码即确认，两条均已修并变异证红。

## 3. 修法 —— 换仪器，不是再补一层语法

`tests/test_resolve_partial_observed_behaviour.py`：包住真实
`Path.read_bytes` / `write_bytes` / `unlink` / `os.replace`，驱动真实函数跑真实场景，
对**观测到的动作**断言。三个 HIGH 各被点名抓住：

```
① answered `already_sealed` having read FINAL 0 times
② the named file holds b'' instead
③ the `.partial` is still in place, BRANCH_C_RENAME_THEN_ALLOW_RETRY did not happen
```

**AST 合同的声称已缩窄**为它真正语法性的那一半：一条新出口不能不经声明就存在。
它不再声称能确立三条义务。

## 4. 它对 §4「接受」的裁定，我全部照办

```
接受①；②、④不应接受；③范围原则可接受但两个 helper 内部未闭合
```

- ④ 已不再是「接受」—— 义务整体移到行为观测
- ② 不再承重 —— 即便有人把 `write_bytes` 加进白名单（它正是这么绕的），
  行为观测仍会因「被点名的文件是空的」而红。**纵深防御，不是同层补丁**
- ③ 行为观测**按效果断言，不按函数边界** —— 字节被谁清空的都一样会被看见

## 5. 席位

`NOT_EXPOSED`，且 `PERSISTED_SEARCH_OUTPUT=NONE`、`SOURCE_WRITES=NONE`、
`FORBIDDEN_PATHS_OPENED=NONE`。可执行的检索边界连续第二轮生效。

## 6. 下一步

`ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND6.md`，其 §3 请它攻击**观测器本身**
（`os.open`／`shutil`／子进程绕过、场景集是否完整、计数不等于因果）。
