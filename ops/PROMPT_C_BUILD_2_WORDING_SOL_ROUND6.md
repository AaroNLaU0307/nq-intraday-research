＃ C_BUILD_2 措辞复审 · 第 6 轮 —— fresh Sol

```ini
REVIEW_ID=c-build-2-wording-r6
DELIVERY_STATUS=PREPARED_NOT_ISSUED
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier（措辞复审第 6 轮）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被审字节的作者；dec-c-build-2-hook-2026-08-28 的决裁席（Fable 5）；
            **第 1–5 轮 c-build-2-wording* 的任何会话**；
            N09 R2/R3 的任何前序复审会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
```

**READ THIS PROMPT FROM DISK, not from a paste.** 本文件从磁盘读取，不从粘贴读。
**绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\PROMPT_C_BUILD_2_WORDING_SOL_ROUND6.md`

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

禁区清单随包交付：`ops/OFF_LIMITS_COMPANION_R6.md`，请一并读。

## 1. 第 5 轮判 HOLD，四条全中，而它让我看见了**前五轮共同的错**

四条全部复现在先（三个 HIGH 各自 10/10 全绿，MEDIUM 读代码即确认）。
证据与逐条处置：`ops/RULING_SOL_C_BUILD_2_R5_HOLD_2026-08-30.md`。

### 1.1 五轮五个 HOLD，形状是同一个

```
R3  路径是被枚举的，不是被闭合的
R4  集合去重  ＋  开放世界的调用识别
R5  词法匹配不是数据流；封了 callee 名字没封接收者/参数/效果；
    helper 控制流没有可达性概念
```

每一轮我都把**语法**收紧一格，每一轮你都写出**满足更紧的语法、违反语义**的代码。

**根因是我的，不是检查器的**：
「这条路径在回答 `already_sealed` 之前读过 FINAL」是一个**运行期属性**。
对任何一种我要求的形状，**满足该形状而违反语义的表达式集合都是无穷的**。
**五轮收紧语法，是五轮在解错的问题。**

而你自己的验证方法一直在说这件事 —— 你每个反例都是**直接执行并计数**
（`FINAL_READ_COUNT=0`、`PRESERVED_EXISTS=False`）。

### 1.2 所以本轮换了仪器：**行为观测**

`tests/test_resolve_partial_observed_behaviour.py`：包住真实的
`Path.read_bytes` / `write_bytes` / `unlink` / `os.replace`，
驱动**真实的** `resolve_partial` 跑过全部真实场景，对**观测到的动作**断言：

```
答 already_sealed   =>  FINAL 真的被读过（计数 >= 1）
答 retry_permitted  =>  被点名的文件真的存在，且真的持有原残留字节
                        且原 .partial 真的不在了（改名真的发生过）
任何场景            =>  .partial 从未被删除
```

**你三个 HIGH 现在各被点名抓住**：

```
HIGH ① -> answered `already_sealed` having read FINAL 0 times
HIGH ② -> the named file holds b'' instead
HIGH ③ -> the `.partial` is still in place, BRANCH_C_RENAME_THEN_ALLOW_RETRY did not happen
```

### 1.3 AST 合同的**声称已缩窄**

它不再声称能确立那三条义务。它保留的是**真正语法性的那一半**：
**一条新出口不能不经声明就存在**。文件名与类名都改了以反映这一点。

### 1.4 MEDIUM 的两个 false green

```
ISSUED 但无 pin        -> 旧版 continue，零 git 调用  =>  现在直接判失败
表中列了已删除路径      -> 旧版被 .exists() 过滤掉    =>  现在直接判失败
```
两条均已变异证红。

## 2. 你上一轮对 §4「接受」的裁定，我的应答

```
你说：接受①；②、④不应接受；③范围原则可接受但两个 helper 内部未闭合
```

- **④（义务 (a) 词法匹配）** —— 你是对的，**已不再是"接受"**：义务整体移到行为观测。
- **②（白名单可被加条目消音）** —— 你是对的。**现在它不再承重**：
  即使有人把 `write_bytes` 加进白名单（你正是这么绕过去的），
  行为观测仍会因「被点名的文件是空的」而变红。**纵深防御，不是同一层的补丁。**
- **③（范围只覆盖 helper 外壳）** —— 你是对的。**行为观测按效果断言，不按函数边界**：
  无论字节是被哪个函数删的、清空的、没改名的，观测到的就是观测到的。

## 3. 请攻击这里

1. **观测器本身。** 它替换 `Path.read_bytes` 等四个方法。绕过它的路子：
   `os.open`／`open()`／`io.open`／`os.replace` 之外的重命名系统调用／
   `shutil`／子进程。**我没有封闭这些** —— 请试。
2. **场景集是我列的。** 五个场景（无文件／final 相同／final 不同／
   partial 不同／partial 相同）。**若存在第六种真实状态而我没列，观测就没跑到它。**
3. **计数 ≠ 因果。** 「读过 FINAL 至少一次」不等于「用读到的字节做了比较」。
   一条先读一次再拿别的值比较的路径，会通过。
4. **AST 合同与行为观测之间有缝。** 合同保证新出口被声明，观测保证效果正确，
   但没有机制保证**每一条被声明的出口都被某个场景执行到**。

## 4. 本轮接受的残留

| 残留 | 为什么接受 | 代价 |
|---|---|---|
| `DECLARED_EXITS` 顺序敏感 | 你上一轮同意接受 | 重排要改声明 |
| 观测器只包 `pathlib`／`os.replace` | 覆盖生产代码实际使用的全部路径；扩到任意 IO 需要 import 钩子 | §3 第 1 条正是它的边界 |
| 场景集手写 | 无法机械枚举「真实文件系统状态」 | §3 第 2 条 |

## 5. 交付要求

沿用第 5 轮字段，另加：

```
INSTRUMENT_ASSESSMENT=  从 AST 检查改为行为观测，是否闭合了你 R3–R5 的反对？
                        若否，给出一条既绕过观测器又绕过合同的路径并跑出来。
SCENARIO_COMPLETENESS=  §3 第 2 条：有没有第六种真实状态是场景集没覆盖的？
```

**HOLD 受欢迎。前五轮都是 HOLD，每一轮的发现都成立，而第 5 轮让我换掉了整个仪器。**
