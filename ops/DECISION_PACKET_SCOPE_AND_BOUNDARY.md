# 两个边界问题 —— 决裁包

```ini
DELIVERY_STATUS=RETURNED
REVIEW_ID=dec-scope-boundary-2026-08-27
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=决裁席（adversarial decision seat）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被裁字节的作者；dec-four-owner-2026-08-27 的那个会话
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
DELEGATED=YES —— Aaron 2026-08-27「给我决策的部分一律让 fable 替我选择，我同意」
SUBAGENT_OR_WORKFLOW_BUDGET=0
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_SCOPE_AND_BOUNDARY.md`

**两个问题分属两个仓**：第 1 件在 ITSF，第 2 件在 `qros-runtime`。
两处仓根都在 §1 给出。

---

## 0. 为什么这两件必须裁，而不是 builder 自己选

**第 1 件**：一份已生效裁定的收尾句与它所依据的设计文档，对「可建范围」给出了
两个不同的边界。**两种读法都说得通**，而 builder 自行选一种然后建到一半，正是
第六轮 HOLD 的 Finding 1 形态（同一文档两条互斥规则，实现者得不到唯一答案）。

**第 2 件**：`qros-runtime` 第二维护窗连续三轮 HOLD，同一缺陷类。第 3 轮的复审席
自己把边界交给了 Aaron，逐字：

> 下一轮修复还需明确如何处理实际项目文件系统上的既存大小写别名，以及该合同是否
> 也覆盖 junction／symlink、8.3 和跨平台 Unicode 归一化；**审查席不替 Aaron
> 决定该边界。**

**且三轮的修法全部出自 builder**——由 builder 再自选第四种规则，是同一个错的第四次。

---

## 1. 传输核对（先做，不通过就 STOP）

ITSF 仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
运行时仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\qros-runtime`

| SHA-256 | 字节 | 路径（相对各自仓根） |
|---|---|---|
| `4539484721aa308410ba03b096d4b9f2822b78a806248fba035206836fbc5e52` | `9237` | ITSF `ops/RULING_FABLE_FOUR_OWNER_2026-08-27.md` |
| `de453448a8c007065850af2282f772edaa68c6a21e572f9bc767448f7c931fb7` | `15082` | ITSF `ops/N09_EXECUTION_PATH_DESIGN_R3.md` |
| `9890ae7fd050bd064eaefab2c5e285244e6fd640f67332ab787e1a555b3ad552` | `15872` | runtime `build-evidence/MAINTENANCE_WINDOW_2_SAVE_DIR_2026-08-27.md` |
| `c63b32a75961c32f76c600c41e95d42aeb40b219bdb0552a86a4ead5106a6f66` | `15804` | runtime `qros_runtime/projects.py` |

任一条不匹配 ⇒ STOP。

---

## 2. 禁区 —— 本节必须随包

**Review Packet 没有承载禁区清单的字段。2026-08-26 就因为清单只写在提示词里、
而交付的是 packet，烧掉了第二个复审席位。**

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不 grep、不 rglob、不广域符号搜索、不「顺手看一眼」。** 需要哪个路径就列出来，
由工作会话提供逐字节内容。

**为什么是禁令而不是提醒**：已烧掉的三个席位里，**第二个从未打开过那份隔离文件**
——一次广域符号搜索把片段带了出来；第三个只做了**一次单模式定向 grep**，同样触到了。

权威清单：ITSF 的 `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
**读那个 json，把里面每一条路径当作关闭。** 尤其点名（以下全部为禁区）：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

**许可起点**：ITSF 的 `ops/RECOVERY_ANCHOR.md`（outcome-clean，永不隔离）。
**运行时仓不含任何隔离件。**

**两条暴露轴不得合并**：研究轴那份本身就在禁区名单上；席位轴
`ops/REVIEWER_EXPOSURE_LOG.md` outcome-clean，可读。

---

## 3. 第 1 件 · R3 骨架能扩到哪

`dec-four-owner-2026-08-27` 的收尾句（已由 Aaron 追认）：

> builder 按第 1 件把 R3 骨架从 `DEFAULT_REFUSE_SCAFFOLD_ONLY` 扩到
> **「除 registry 写出口外全部可建」**

而它所依据的 `ops/N09_EXECUTION_PATH_DESIGN_R3.md` §6：

> **不可建**：任何能让上述结构**真的产出行、真的封存、真的归档、真的追加 P3**
> 的能力。

**差额恰好是三样**：行生产、封存、归档。

```
选项 NARROW —— 只建 R3 §1–§5 的结构层
  checkpoint 分派 · ROUTER_OF · 两个路由器矩阵 ·
  structural-only 调用图的 AST 守卫 · precheck 证据规则
  理由：与八个仍为 NO 的授权字段一致；代码不获得任何它今天不被授权使用的能力。
  代价：执行路径仍不能端到端演练，缺陷只能靠设计审发现。

选项 WIDE —— 另加行生产、封存、归档，只把 registry 写出口留空
  理由：这三样都不写 registry、不建目录、不读真实数据（可用 synthetic 演练），
  端到端演练能暴露设计审发现不了的缺陷。
  代价：生产包获得「产出行／封存／归档」的能力，而
  SUPPLEMENT_EXECUTION_AUTHORIZED / REAL_DATA_READ_AUTHORIZED /
  DIRECTORY_CREATION_AUTHORIZED 三者仍为 NO。
```

**builder 的观察（非裁定，已实测）**：`day_strata_supplement.py` 里
`build_day_strata_supplement_test_only` 与 `seal_supplement_test_only`
**已经存在**——纯 hermetic 核心，无 I/O，且名字里的 `_test_only` 是既有的隔离手段。
所以 WIDE 的一部分能力**本就在树里**，差别在于是否把它们接进 C_BUILD 的五道门。

**请裁**：NARROW 还是 WIDE。若 WIDE，**「不建 registry 写出口」的机械判据是什么**
（R3 §6 给的是 AST 可达性，不是 grep——请判它够不够，以及封存／归档的落盘是否
需要与之同等的判据）。

**builder 已按限制性读法只建 NARROW 那部分**，等本裁定再决定要不要扩。

---

## 4. 第 2 件 · `save_dir` 合同的边界在哪

**三轮 HOLD，同一缺陷类**：

```
第 1 轮  ops//packets、ops/./prompts     修：逐段规则 ＋ posixpath 规范形
第 2 轮  dots/packets.（Windows 尾点）    修：跨平台安全段规则
第 3 轮  OPS/packets（大小写，且状态相关） 修：把等价类塌缩（只允许小写 ＋ ASCII）
```

第 3 轮复审席的 `STRONGEST_OBJECTION`（逐字）：

> 当前修法再次以有限规则集代替了文件系统身份性质。

**builder 的一个测量，可能改变问题的形状**：三轮找到的**四个分叉形状，按渲染路径
全都取得回文件**：

```
dots/packets./rv-x.packet   枚举相等=否   按渲染路径可取回=是
OPS/packets/rv-x.packet     枚举相等=否   按渲染路径可取回=是
ops//packets/rv-x.packet    枚举相等=否   按渲染路径可取回=是
ops/./prompts/a2.header     枚举相等=否   按渲染路径可取回=是
```

`rglob` 报的是文件系统的**规范拼写**——显示归一化，不是位置。

**但 finding 仍成立，理由是另外两条**：

1. **跨平台**：大小写敏感的文件系统上 `OPS/packets` 与 `ops/packets` 是**两个目录**。
2. **本项目自己的 exact-set 磁盘不变量**——正是开这个窗的 L-5 缺陷；记录
   `OPS/packets/x` 而枚举给 `ops/packets/x`，精确集合比对失败。

**核心困难（builder 已实测，非推测）**：「配置的目录会不会与既存的不同大小写目录
冲突」**依赖文件系统状态，配置解析时不可判定。不是难，是原理上不可能。**

```
选项 LEXICAL_ONLY —— 合同只承诺词法性质，止步于此
  即：save_dir 是一个规范的、小写的、ASCII 的相对 POSIX 路径。
  渲染行是「应当保存到哪」的**规范**，不是「文件系统会怎么报告」的**预测**。
  junction/symlink/8.3/既存别名明确划出合同之外。
  理由：这是一个词法校验器能诚实承诺的全部。
  代价：exact-set 不变量若比对枚举输出，仍可能失配——须由别处保证。

选项 RENDER_TIME —— 把检查移到渲染时（那里看得见状态）
  qros packet/prompt 渲染路径时，实地核对父目录不存在不同拼写的别名，否则拒绝。
  理由：让性质由构造成立，而不是由规则逼近。
  代价：渲染不再是纯函数，要碰文件系统；且 header.required_save_path 今天不收
  repo 参数（packet 侧收），两侧形制会不对称。

选项 BOTH —— 词法合同 ＋ 渲染时核对，各管一段
  代价：两处都要维护；但两处各自诚实。
```

**请裁**：三选一，并明确 junction／symlink／8.3／Unicode 归一化**在不在合同内**。

**若选 RENDER_TIME 或 BOTH**：这会改动已认证接口的形状（渲染需要 repo 上下文），
请一并判**它是否仍属 D-4 条件 1 的「加性」**，还是触发 R2 补裁写死的硬回退
（「若被迫出现对已认证接口的非加性破坏 ⇒ STOP，header 另立工作项」）。

---

## 5. 常设禁令（对你同样在 force）

不读真实 Development 数据；不执行 supplement／MC／S0／strategy；不在
`C:\Users\Aaron\quant-data\` 下创建任何目录；不做写探针；不追加任何 registry／
exposure 事件；不写 `APPROVED`／`EFFECTIVE`／`RATIFIED` 值；**不代签 P2、不代拟
执行语句**；不改样本／标签／NA 政策／成本／Primary／Oracle／feasibility／运行定义；
不推送、不打标签、不 amend；不闭维护窗；不推断 LANE／STAGE。

**READ_ONLY**：只裁不做，零文件修改。

---

## 6. 返回格式

```
ITEM=SCOPE-BOUNDARY
DELEGATED=YES
TRANSPORT_PRECHECK=PASS|STOP

ITEM=第 1 件 R3 骨架的可建范围
  RULING=NARROW|WIDE
  若 WIDE：不建 registry 写出口的机械判据是什么；封存／归档落盘要不要同等判据
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE
ITEM=第 2 件 save_dir 合同的边界
  RULING=LEXICAL_ONLY|RENDER_TIME|BOTH
  合同内／外：junction · symlink · 8.3 · Unicode 归一化 · 既存别名
  若 RENDER_TIME 或 BOTH：是否仍属 D-4 条件 1 的加性，还是触发 R2 硬回退
  REASONS / CONDITIONS / FALSIFIER / CONFIDENCE

STRONGEST_OBJECTION=<对你自己两条裁定中最弱的那条>
STILL_AARON_ONLY=<你认定不可代裁的>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本裁定不释放任何 gate，不闭任何维护窗，不是研究授权，不是运行授权。**
