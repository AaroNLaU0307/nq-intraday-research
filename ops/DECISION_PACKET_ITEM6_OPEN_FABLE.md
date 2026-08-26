# 第 6 项的三个开放项 —— 决裁包

```ini
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
EXECUTION_MODE=STANDARD
ROLE=决裁席（adversarial decision seat）
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=builder；被裁字节的作者；ratification authority
LANE=FULL
OUTCOME_EXPOSED=NONE（本包不含任何目标绩效数值）
PREREG_SEALED=YES
DELEGATED=YES —— Aaron 2026-08-27 原话「其余的就按fable推荐的方式做，我同意」
SUBAGENT_OR_WORKFLOW_BUDGET=0
```

**本文件从磁盘读取。绝对路径**：
`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\DECISION_PACKET_ITEM6_OPEN_FABLE.md`

---

## 0. 你在裁什么，以及边界

第 6 项（ND1 profile R3 修订提案）经**六轮 fresh Sol HOLD** 后，工程内容已全部
闭合。剩下三个开放项**不是工程问题，是政策取舍**——每一个都有两个都说得通的完整
形，builder 不得替任何人选。

**三项 `DELEGABLE=YES`，你的裁定即生效决定**（Aaron 保有 append 推翻的常设否决权）。

### 明确不在本包内的第四项

```
是否 ratify R3（即改动 R2 已批准的 P3／F3 两行）—— STILL_AARON_ONLY
```

**理由（三条，均可核）**：R1 与 R2 在 `ops/ND1_PROFILE_RATIFICATION.md` 里都是
Aaron 的逐字原文；该文件 §7 的修订路线终点写死是「Aaron 批准 R3 的 id ＋ hash ＋
精确 doc HEAD。不得从参照清单里挑值直接生效」；且**上一轮 Fable 自己就把这条列进
了 `STILL_AARON_ONLY`**。

**你不得裁它，也不得在裁另外三项时以「假定 R3 会被批准」为前提反推。** 三项各自
独立成立或不成立。

---

## 1. 传输核对（先做，不通过就 STOP）

本包引用的字节，逐条哈希：

| SHA-256 | 字节 | 路径（相对仓根） |
|---|---|---|
| `12827d36b1324f46073aa6f56ef9ae2d5da55ab785beaf066535a7425903af28` | 34525 | `ops/PREP_ITEM6_ND1_R3_AMENDMENT_PROPOSAL.md` |
| `c02baaecfb1d3d1b5c3817e27474406418e6200e9e62024d26758a62f07245f4` | 11817 | `tests/test_nd1_profile_revision_chain.py` |
| `cf2c3cb2bdb79b34498c2a7ebc53344c70ef89f0686466a010ce62431541d05e` | 8277 | `ops/ND1_PROFILE_RATIFICATION.md` |

> 上表哈希在本包定稿后重新取过，**已含 §4 自纠的三处改动**。逐条重算必须匹配；
> 任一条不匹配 ⇒ STOP，不要自行判断差异是否无害。

仓根：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`

---

## 2. 禁区 —— 本节必须随包，不是背景说明

**Review Packet 没有承载禁区清单的字段。2026-08-26 就因为清单只写在提示词里、
而交付的是 packet，烧掉了第二个复审席位。**

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**不 grep、不 rglob、不广域符号搜索、不「顺手看一眼」。** 需要哪个路径就列出来，
由工作会话提供逐字节内容。

**为什么是禁令而不是提醒**：已烧掉的三个席位里，**第二个从未打开过那份隔离文件**
——一次广域符号搜索把片段带了出来；第三个（决裁席）只做了**一次单模式定向 grep**，
同样触到了。只要隔离内容还在可检索的树里，任何检索都可能带出它。

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。尤其点名：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

它**既是 outcome-carrying，又是本项目的恢复锚**——按常规做一次状态定位就会踩中。

**许可起点**：`ops/RECOVERY_ANCHOR.md`（outcome-clean，永不隔离，专为 blind 席位
可读而写）。

**两条暴露轴，不得合并**：研究轴 `ops/EXPOSURE_LEDGER.md`／席位轴
`ops/REVIEWER_EXPOSURE_LOG.md`。烧掉一个席位**不消耗研究自由度**。

---

## 3. 三个待裁项

### R-A · `FORBIDDEN_EDGES` —— ZERO 还是 FULL

**背景（Sol 连续两轮指出）**：两条禁边对强制正确性**都非必要**——CR1 的 closed
successor list 只有 `F3`，普通 transition 检查已会拒 `CR1→P4/P5`。若要作为具名
政策保留，**当前又缺一条：真正的重启边 `CR1→P3`**。Sol 明确说：**不能保留这个
缺一条的中间态。**

```
选项 ZERO —— 一条不加，完全依赖 closed successor list。
  理由：不制造与 successors 重复的第二真相源（本栈反复付过代价的形态）。
  代价：「崩溃裁定永不复活运行」不是被测断言，只是 successors 恰好没写。

选项 FULL —— 三条全加，各配专用拒绝码：
  ("CR1","P4") ("CR1","P5") ("CR1","P3")
  其中 ("CR1","P3") 才是真正的重启边——「永不复活」这句话的正面对象。
  代价：三条与 successors 重复，须同步维护。
```

**builder 的观察（非裁定，已实测）**：`supplement_contract.FORBIDDEN_EDGES`
（`src/itsf/mc/supplement_contract.py:348`）现有 **8 条**，逐条为：

```
("F1","P2") ("A1","P5") ("A1","P4") ("AX","A2")
("AX","P5") ("P2S","P3") ("P3","P2S") ("F2","P3")
```

其中 `("F2","P3")` 与 `("P2S","P3")` **都是重启边**，拒绝码分别是
`f2_to_p3_in_place_retry` 与 `p2s_to_p3_without_new_p2`（在
`supplement_registry.FORBIDDEN_EDGE_CODES`，`src/itsf/mc/supplement_registry.py:420`）
——「禁止就地重启」在这张表里已有先例，且正是它的主要用途。若取 FULL，
`("CR1","P3")` 与那两条同形。

**没有第三种。** 中间态（只加两条）是第六轮 HOLD 的 Finding 1，已被消除；你的裁定
必须落在 ZERO 或 FULL 其一。

**若取 FULL，附带义务**：每条新边须在
`supplement_registry.FORBIDDEN_EDGE_CODES` 有专用拒绝码，且每条变异证红。

---

### R-B · profile 行绑定独立语法块，这个构造接不接受

**问题来源（Sol Finding 3）**：R3 的哈希只覆盖 profile 块，而 CR1 的
`row_class`／`actor`／字段表／`terminal`／`incident_required` **全在块外**，
`ADOPT_AS_INTRODUCED_BY_R3` 没有唯一 section marker，也没有子块哈希。**等于批准
了一个指向未固定字节的引用。**

**builder 提出的构造**：CR1 语法自成一个 canonical 块
（`BEGIN_ND1_CR1_GRAMMAR_R3` … `END_ND1_CR1_GRAMMAR_R3`），profile 里加一行

```
RECOMMENDED_CR1_GRAMMAR_SHA256=c251335f8d8c4dc89bce4ff7fb445f862d29a04b676bb3a90f6ef5ce5d5e3483
```

把它绑住。**绑定因此落进 R3 哈希的覆盖范围，而语法块本身不含自己的哈希，无自引用。**

**请裁**：

1. 这个构造是否**真的**闭合了 Finding 3——批准 R3 是否就等于批准了那段语法的
   精确字节。
2. 有没有**第二条**路径能让语法块变化而 R3 哈希不变（若有，构造未闭合）。
3. 两级哈希是否引入了新的维护危害（两个块必须同步改，改一个忘一个会怎样）。

**已机械化的部分（`tests/test_nd1_profile_revision_chain.py`，11 项全绿）**：
R3 块的字节确实算出所声明的哈希；对 R2 恰为 **13 处编辑**（4 改 ＋ 9 加 ＋ 0 删，
逐行口径 60 − 47 = 13 与按键口径一致）；CR1 的边双向声明；各条边界行仍为 `NO`。
**八条变异全红。**

---

### R-C · 悬空 P3 的拒绝范围 —— per-id 还是全局阻断 MC 入口

**已裁的部分**：per-id 拒绝（同一 `supplement_id` 上有悬空 P3 时拒绝开新运行）。

**未裁的部分，即本项**：是否**同时阻断整个 MC 生产入口**——即任一 id 上存在悬空
P3 时，所有 id 都不得开新运行。

```
选项 PER_ID_ONLY —— 只拒该 id。
  理由：一次事故不楔死无关的 supplement_id。
  代价：MC 入口在存在未闭合崩溃链时仍可用于其他 id。

选项 GLOBAL —— 任一悬空 P3 阻断整个 MC 入口。
  理由：未闭合的崩溃链意味着 registry 状态未知；在未知状态上开任何新运行都可疑。
  代价：单个 id 的事故楔死全部工作，且解除依赖裁定速度。
```

**已在提案里的 FALSIFIER（继承自上一轮 Fable，本版收窄）**：真实事故显示 per-id
拒绝以裁定无法快速解除的方式**楔死了无关的** supplement_id ⇒ 拒绝范围须重设计。

**两条 builder 必须如实说明的**：

1. **`NON_TERMINAL_TRAPS` 是闭链诊断集合，不得直接充当启动授权政策集合。** 前者
   回答「这条链闭上了吗」，后者回答「能不能在这个 id 上开新运行」。提案已把两者
   彻底分开：白名单是政策，traps 仍只供 `assert_chain_closed` 诊断。
2. **今天落地可观测行为零变化**——`run_supplement_production` 本就 gate-first
   拒绝。**注意有两个同名生产入口**，builder 已逐个打开确认，两者都是 `NoReturn`：
   `day_strata_supplement.run_supplement_production`（`:130`）与
   `supplement_runner.run_supplement_production`（`:935`）。两者的 docstring 都
   写明：唯一读的仓内文件是 `ops/TRIAL_REGISTRY.md`，紧接着就是拒绝，不开
   Development 数据、不碰输出根、不建目录、不写探针、不追加任何行。
   所以本项**不是紧急的**，但它是实现者从文档里得不到唯一答案的那类缺口
   （Finding 2 的成因）。

---

## 4. builder 起草本包时自己发现并已改的三处 —— 如实报告

本包起草过程中，builder 在提案文件里发现三处缺陷，**已改，且改动本身要接受你的
审视**：

1. **§二.1b 机械证明块的枚举漏了一行**：`added` 列写「6 处」，实际是 7 处——漏了
   `RECOMMENDED_CR1_REGISTRY_INTACT_CRITERION`。已补，并加上 `removed（无）` 与
   合计行。
2. **正文写「对 R2 恰为 12 处编辑」，而实测与测试常量都是 13。** 已改为 13。
   （12 与 13 的差正是第 1 条漏掉的那一行。）
3. **§七 的标题被叠加编辑串成了三遍。** 已去重。

**为什么报告**：第 1、2 条是**同一份文档内部的算术不自洽**，正是第六轮 HOLD
（§A.3 声明 ZERO-or-FULL 而建造义务仍写「加两条」）的同类。它在被送去决裁**之前**
被抓到，但抓到它的是 builder 自己，不是守卫——**这一点值得你在裁 R-B 时考虑：
一个靠人工核对才能发现算术错误的构造，是否够格承载批准语义。**

---

## 5. 常设禁令（对你同样在 force）

不读真实 Development 数据；不执行 supplement／MC／S0／strategy；不在
`C:\Users\Aaron\quant-data\` 下创建任何目录；不做写探针；不追加任何 registry／
exposure 事件；不写 `APPROVED`／`EFFECTIVE`／`RATIFIED` 值；不改样本／标签／
NA 政策／成本／Primary／Oracle／feasibility／运行定义；不推送、不打标签、不 amend；
不裁 Stage I 与 discretionary Tier-1 之别；不推断 LANE／STAGE；不填 P2 占位符。

**READ_ONLY**：本轮只裁不做，零文件修改。若你认为某处必须改，写进裁定由 builder 执行。

---

## 6. 返回格式

```
ITEM=6-OPEN
DELEGATED=YES
TRANSPORT_PRECHECK=PASS|STOP

逐项：
ITEM=R-A  RULING=ZERO|FULL
          REASONS=<可核，指向本包内的字节>
          CONDITIONS=<实施条件，含变异证红要求>
          FALSIFIER=<什么事实会推翻这个选择>
          CONFIDENCE=HIGH|MEDIUM|LOW
ITEM=R-B  RULING=接受该构造|不接受（并说明替代）
          三问逐条作答：闭合了吗 · 有无第二条路径 · 维护危害
          ...同上四栏
ITEM=R-C  RULING=PER_ID_ONLY|GLOBAL
          ...同上四栏

STRONGEST_OBJECTION=<对你自己三条裁定中最弱的那条>
STILL_AARON_ONLY=<你认定不可代裁的，含 R3 的 ratify>
SEAT_STATUS=BLIND|EXPOSED（并说明触发方式）
INDEPENDENCE_STATEMENT=<按维度：会话、作者身份、模型多样性、经验独立性、设计贡献>
```

**本裁定不释放任何 gate，不是研究授权，不是运行授权。**
