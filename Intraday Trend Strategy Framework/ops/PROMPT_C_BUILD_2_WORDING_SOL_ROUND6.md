＃ C_BUILD_2 措辞复审 · 第 6 轮 —— fresh Sol

```ini
REVIEW_ID=c-build-2-wording-r6
DELIVERY_STATUS=RETURNED
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

## 2. 受审集

```
REVIEWED_SET_UNCHANGED_SINCE=6395da49dc2cdaee9f9e84eb057b25dda869f8af
```

**语义**：该 commit 之后没有任何 commit 触碰过下表的参考件。
本提示自身不在该 range 内（发出 delivery 就是对它的一次提交，无不动点）。

| sha256 | bytes | 路径 |
|---|---|---|
| `981d098819f340b460b094bbcc284039973417f43e4ba65b252967d4d5c352b2` | 50099 | `src/itsf/mc/supplement_runner.py` |
| `34b2a17ed2e1617e34457882d7df7b4bcc0cc8d658003f8ea5a07a607bdfe0cf` | 32616 | `src/itsf/mc/supplement_contract.py` |
| `02c411389a30bfef1e84794f99b752cd98abcbb387a837effb713ca99d221caa` | 23052 | `tests/test_resolve_partial_observed_behaviour.py` |
| `054d0d6309ef464f80ad8c8aa6f0f5fff7e41605e1a13bd85e574e2efdbc8ce6` | 18211 | `tests/test_resolve_partial_path_contract.py` |
| `d8c207f8637e4bada2feb359fb0c35b9ade02eba851157129470d51f43231397` | 7846 | `tests/test_a_prompts_range_claim_actually_holds.py` |
| `c2987bafbe62e3a16dcc3249016985c91cac8259b04bec4ec959423300d1be95` | 6100 | `tests/test_every_sealed_final_was_read_back.py` |
| `4d4874c5e22b5adff47312bb03c0e405418fb894446b9ecd87a46e7ecef42613` | 11556 | `tests/test_c_build_2_wording_coverage.py` |
| `267863b964eccbbe59a4c8b6069f5cf63b36138a2b8f7c7eae857f7f020af811` | 27138 | `tests/test_n09_checkpoint_assertions.py` |
| `4ae94ad34a5c2d4c06a8dd7a99aeef546356fb2ba8b384faf6cd8082f4ea1097` | 13730 | `tests/test_every_approval_is_accounted_for.py` |
| `3b8fd362614ee7e7c689bde19d9797b501464de5bc2caa57cb8271963effae50` | 6869 | `tests/test_the_ratified_preimage_is_reconstructible.py` |
| `1e28255b695f1aa5590067631f9798bcdc0af81421eb2e1ffdfa2905599b251b` | 3686 | `ops/RULING_SOL_C_BUILD_2_R5_HOLD_2026-08-30.md` |
| `bafdc75a150011e4fc9f0cafad72de5fc0c06696eb9a01b446516d57defc72fa` | 2644 | `ops/OFF_LIMITS_COMPANION_R6.md` |

**delivery**：`ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND6.md`，字节见 `ops/ARTIFACTS_UNDER_REVIEW.json`。

**本轮的重点受审件是第三行** `test_resolve_partial_observed_behaviour.py` ——
换掉的那个仪器本身。

**核对你读的是当前文件**：line 102 of it must read 那一行 ——
`REVIEWED_SET_UNCHANGED_SINCE` 必须是 `6395da49dc2cdaee9f9e84eb057b25dda869f8af`。
对不上 ⇒ 陈旧粘贴 ⇒ **STOP**，回磁盘重读。

**一处如实交代**：本节是**补写的**。第一版的第 6 轮包**根本没有受审集**——
我把 §2 编号给了别的内容，传输表和 pin 一起漏了。发行守卫会在武装时拦下，
但那是兜底不是流程；和第 5 轮「先武装后改文件」是同一类顺序错误。

## 3. 你上一轮对 §5「接受」的裁定，我的应答

```
你说：接受①；②、④不应接受；③范围原则可接受但两个 helper 内部未闭合
```

- **④（义务 (a) 词法匹配）** —— 你是对的，**已不再是"接受"**：义务整体移到行为观测。
- **②（白名单可被加条目消音）** —— 你是对的。**现在它不再承重**：
  即使有人把 `write_bytes` 加进白名单（你正是这么绕过去的），
  行为观测仍会因「被点名的文件是空的」而变红。**纵深防御，不是同一层的补丁。**
- **③（范围只覆盖 helper 外壳）** —— 你是对的。**行为观测按效果断言，不按函数边界**：
  无论字节是被哪个函数删的、清空的、没改名的，观测到的就是观测到的。

## 4. 请攻击这里

1. **观测器本身。** 写这一节时它只包 `pathlib` 四个方法；
   **写完这一节之后我把它修了**（上一轮的教训就是「列出弱点不等于处理弱点」）：
   现在还包 `builtins.open`、`os.open`、`shutil.copy/copy2/move/rmtree`。
   **仍然开着的**：子进程、`ctypes`／直接系统调用、被提前绑定到局部名的原方法。
   请试这些。
2. **场景集是我列的。** 五个场景（无文件／final 相同／final 不同／
   partial 不同／partial 相同）。**若存在第六种真实状态而我没列，观测就没跑到它。**
3. **计数 ≠ 因果 —— 这一条也已修。** 新增 `TestTheReadIsCAUSAL_notMerelyCounted`：
   FINAL 在盘上确实等于 intended，但 `read_bytes` **被令返回不同字节**。
   若答案仍是 `already_sealed`，说明比较没用读到的东西。
   变异证红：`_ignored = final.read_bytes(); existing = intended` → 被点名抓住。
   **`partial` 的两次重读也已照做**（`TestBothPartialReadsAreCausalToo`）：
   第一次读决定 branch C，第二次读是落盘后的校验；各自令其说谎，答案必须改变。
   两条变异证红（读了但丢弃 / 读了但比较用别的值）。
4. **AST 合同与行为观测之间的缝 —— 也已焊上。** 写这一节时我量了一下：
   合同声明 8 个出口名，场景只跑到 5 个 —— `divergent_partial_exists`、
   `incident_id_malformed`、`supplement_post_promotion_verify` **从未被执行过**。
   一条「已声明但从未执行」的出口是两头落空：合同当它已交代，而没有任何观测见过它做什么。
   三条现已各有场景驱动，并加一条断言：**声明集里的每个出口名都必须被本文件跑到**，
   反向也查（不得声称跑到合同没声明的出口）。

## 5. 本轮接受的残留

| 残留 | 为什么接受 | 代价 |
|---|---|---|
| `DECLARED_EXITS` 顺序敏感 | 你上一轮同意接受 | 重排要改声明 |
| 观测器不包子进程／ctypes／提前绑定的局部名 | 挡住它们需要 import 钩子或 seccomp 级手段，代价与本项目不相称 | §4 第 1 条 |
| —— | 该条已做完，不再是残留 | 见 §4 第 3 条 |
| 场景集手写 | 无法机械枚举「真实文件系统状态」 | §4 第 2 条 |

## 6. 交付要求

沿用第 5 轮字段，另加：

```
INSTRUMENT_ASSESSMENT=  从 AST 检查改为行为观测，是否闭合了你 R3–R5 的反对？
                        若否，给出一条既绕过观测器又绕过合同的路径并跑出来。
SCENARIO_COMPLETENESS=  §4 第 2 条：有没有第六种真实状态是场景集没覆盖的？
```

**HOLD 受欢迎。前五轮都是 HOLD，每一轮的发现都成立，而第 5 轮让我换掉了整个仪器。**
