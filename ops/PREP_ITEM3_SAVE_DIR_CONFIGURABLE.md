# 第 3 项交付物 —— `_SAVE_DIR` 配置化的准备与一处范围发现

```
RECORD_TYPE=PREPARED_ARTIFACT
ITEM=3（dec-eight-open-2026-08-26）：D-4 的运行时工作项
STATUS=已核准事实、已出补丁设计，**未实施**
RULED=D-4 裁 A（改运行时，`_SAVE_DIR` 可配置）；Fable 2026-08-26 定时点／认证深度／
      B 的失效条件；Aaron 已采纳（OD-2026-08-26-2）
NEEDS=Aaron **开启维护窗**（D-4 条件 5 的定义性要求）
      ＋ §2 的范围问题需你（或 Fable 补裁）先答
SCOPE_NOTE=改动落在 `Quant trade\qros-runtime\`（**已认证仓**），不在本仓。
           本件只是设计，未向那个仓写入任何字节。
OUTCOME_CLEAN=是
```

---

## 1. 现状（实测，非转述）

```
packet.py:64    _SAVE_DIR = "runs/packets"
packet.py:146   def required_save_path(repo, review_id):
                    return "%s/%s.packet" % (_SAVE_DIR, review_id)
packet.py:290   "REQUIRED SAVE PATH: %s" % packet_obj.save_path      ← 渲染处一
packet.py:973   save_path=required_save_path(repo, review_id)

header.py:200   def required_save_path(role):
header.py:201       return "runs/prompts/%s.header" % role.replace(" ", "-").lower()
cli.py:771      "REQUIRED SAVE PATH: %s" % headermod.required_save_path(args.role)  ← 渲染处二
```

**一个有利事实**：`packet.py:146` **已经接收 `repo` 却完全没用它**。配置化的接缝
早就在签名里了，加配置是填空，不是改形状。

## 2. **范围发现：同一个缺陷有两处，D-4 只点名了一处**

| 位置 | D-4 的 `COLLATERAL` 覆盖了吗 |
|---|---|
| `packet.py:64` 的 `_SAVE_DIR` | **点名了** |
| `header.py:201` 的内联 `"runs/prompts/..."` | **没点名** |

D-4 原文写的是「`qros_runtime/packet.py:64 _SAVE_DIR` 及 **REQUIRED SAVE PATH
渲染处**、运行时测试与 conformance、注册流程说明」。

**渲染处确实是两个**（`packet.py:290` 与 `cli.py:771`），所以从「渲染处」这三个字
看，第二处被扫进来了。**但那个常量本身没被点名**——照字面实施的人会改 `_SAVE_DIR`
与两处渲染，然后合理地不去动 `header.py:201`，因为**它不叫 `_SAVE_DIR`**。

**后果**：`qros prompt` 仍会让项目把 header 存进 `<repo>/runs/prompts/`，
**与 packet 完全相同的 L-5／R5 禁令**。

**目前是潜伏的，没踩到过**：ITSF 全仓检索 `runs/prompts` **零命中**——本项目的
提示词一直是手写的，从未用过 `qros prompt`。

**难度不对称，要说清楚**：`packet.py:146` 已收 `repo`，加配置是加性的；
`header.py:200` **连 `repo` 都不收**，配置化要改签名——这比 D-4 条件 1 的
「加性且向后兼容」要重一档。

### 请你（或 Fable 补裁）先答

```
SCOPE = A：只按 D-4 字面修 packet 侧，header 侧另立工作项
      | B：一并修，视为「REQUIRED SAVE PATH 渲染处」的完整闭包
      | C：一并修但先由 Fable 补一句，因为它严格说是新范围
```

**builder 不替任何人选。** 我的观察仅止于：留着它，等于明知同一个坑还留着第二个。

## 3. 补丁设计（开窗后实施，严格按 D-4 条件 1–4）

### 3.1 配置面（条件 2：项目级持久配置，**禁用环境变量**）

在 `qros-state.yaml` 增加一个可选字段（DECLARED 分区）：

```yaml
packet_save_dir: "ops/packets"      # 省略时 == "runs/packets"
```

**为什么放 `qros-state.yaml` 而不是注册表**：注册表在认证仓之外、无需认证轮，
但它是**跨项目**的；save dir 是**每项目**属性。状态文件已经是项目级自陈的正典位置。
（注册表也可以，两者都满足条件 2；此处是 builder 的取舍，可推翻。）

### 3.2 代码（条件 1：加性、默认值恒为 `"runs/packets"`）

```python
_SAVE_DIR_DEFAULT = "runs/packets"          # 名字改了，值一字未变

def required_save_path(repo, review_id, save_dir=None):
    return "%s/%s.packet" % (save_dir or _SAVE_DIR_DEFAULT, review_id)
```

调用点 `packet.py:973` 传入从 state 读到的值。**无显式配置时认证行为零变化**——
这是条件 1 的字面要求，也是「不需要重跑全部既有认证」的依据。

### 3.3 渲染（条件 3：必须渲染**生效**路径）

`packet.py:290` 渲染的是 `packet_obj.save_path`，而 `save_path` 由 `:973` 计算，
所以**它自动渲染生效路径**，无需改动。这一条已经满足——
**前提是 `:973` 传了配置值**。偏离记录 §5 那条陈旧行的危害不得复制过来。

### 3.4 测试与 conformance（条件 4）

运行时自己有 **6+ 处硬编码** `"runs/packets/%s.packet"`：
`tests/fakes.py:275`、`test_integration_cli.py:299`、`test_satisfaction.py:174`、
`test_sol_hold_repairs.py:209/892/2509`。

这些**不改**（它们钉的是默认行为，必须继续绿）。**新增**配置路径的覆盖用例：
默认、显式同值、显式异值、非法值拒绝。

## 4. 认证深度与时点（Fable 裁定，逐字要点）

- **时点**：下一个 Aaron 开启的维护窗，并以「**先于第一个 GRAD pilot 完成**」
  为目标排序——pilot 恰恰要签发 packet，带伤 pilot 的风险大于窗的风险。
- **认证**：机器检查先行（923+ 测试、22 conformance、25 render-checks ＋ 3.4 新用例），
  **然后一轮 fresh Sol（High）**。不取零轮（M15-1 的零轮先例是零生产实例缺陷；
  本项动的是每次复审都过手的 packet 渲染语义），不取多轮（改动加性、默认不变、
  falsifier 明确）。Sol HOLD 走既有 reproduce-first 修复环。
- **B 的失效**：**按事件，不按日历**——A 落地且 conformance 通过之日为止。
  当日 ITSF 切换配置、实跑一次 `qros packet` 验证渲染路径、向
  `ops/RUNTIME_DEVIATION_PACKET_SAVE_DIR.md` **append** 一行闭合。
- **排序保护（条件 4）**：pilot 不得在窗中途开始。若你先开 pilot，则 A 顺延至
  下一窗、pilot 照常在 B 下进行——**pilot 不被本项阻塞**。

## 5. 不得动

`tests/conftest.py` 的 R5 守卫、`test_s0_runner` 两条 `runs` 断言、
`<repo>/runs` 禁令本身、既有 `PACKET_ISSUANCE` 记录、运行时那 6+ 处默认路径断言。

## 6. FALSIFIER

- **（继承 D-4）** 配置化后任一项目出现 `PACKET_ISSUANCE` 的生效 `saved_path`
  与实际存放位置分叉（双真相源）⇒ 设计错误，回撤配置项重设计。
  **`saved_path` 保持唯一权威，配置只导向写入器。**
- **（继承 Fable）** 窗内改动若需要**削弱**（而非扩展）任何既有测试或守卫 ⇒
  STOP，按 D-4 反向条款处理。
