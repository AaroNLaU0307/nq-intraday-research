# 下一份要交出去的东西 —— 固定入口

> **这个文件名永远不变。** 我说「贴这个给 Sol／Fable」时，指的就是它。

```
UPDATED = 2026-08-29 深夜
```

---

## 先读这条：你批准的「重开 B」我没有执行，因为依据是我造的

你说「按你推荐的继续工程」。**动手之前我回去核了推荐的依据，它是假的。**

我在 §12.5 写「`already_sealed` 分支不问出处、**从未复读校验**」。
前半句真，后半句假 —— 那个分支 `final.read_bytes()` 之后就跟 `intended` 比了，
**与 promote 后那次复读是同一个检查**。实测计数五条路径：每一条「把 FINAL 当作
已封存」的路径都读回并比对过；唯一读 0 次的路径根本不封存 FINAL。

所以 (a) 声称防的类**没有实例**，原措辞是对的，判据 (1) 在 (a) 上本来就成立。

**我做错的是把类偷换了**：换成「出处未知的 FINAL 被接受」——我自己引进的更宽的类
——再宣布 (a) 覆盖不了它。量对的一半是真的，推出来的一半是假的。

```
§12.5      文本保留，结论撤回（§14）
§13.5      撤回
决裁包      WITHDRAWN，全文保留为误判记录
重开 B     不执行
```

**第 1 轮复审席的 HIGH ② 在我供的前提下推理完全正确，不该记它一笔。**

---

## 现在备妥待发一份

```
ITSF   ops/PROMPT_C_BUILD_2_WORDING_SOL_ROUND2.md
       措辞复审第 2 轮。pin=427224f，1 delivery + 9 reference 已武装。
       **主攻击面是 builder 自陈的可复核性** —— 上一轮席位在我供的假前提上
       做了正确推理，所以这一轮请它把 §12–§14 里每句「实测……」当作待证，
       并明说哪些它根本无法独立复核。
       **我不知道还有几句是那样的。这是我请它找的东西。**
```

**随它一起交出去**：`ops/SELF_REPORT_AUDIT_2026-08-29.md`（伴随件，不在受审集内）。
prompt §0 写「我不知道还有几句是这样的」；写完我自己把更早会话的九条重量了 ——
八条逐字符合，一条是陈旧时态非假。**伴随件让席位不必重做我已做过的功**，
并明写这个方法抓不到 §12.5 那种散文里的偷换，那才是该看的地方。

qros-runtime 这边没有 prompt 在飞；挡路的是「倒转默认作为设计的正式采纳」，归你。

---

## 策略 build：推不到，卡点不是工程

恢复锚 §4 的原话，我复核过：

```
N09（MC-DS-S001 执行封存）需要 Aaron 的 P2 精确授权
N10 依赖 N09 的真实执行
N11 从未实现；N13 依赖 N11
故 N12 之后不存在 builder 可独立推进的 DAG 节点
```

**再加多少测试都不会让这条链通。** N11 的身份只在隔离件里（我没开），
非隔离文件全都只写「未实现」—— 要知道它是什么，得你说或解隔离。

**通往策略 build 的第一块砖是你的 P2 授权，不是我的下一次提交。**

---

## 2026-08-29 落地的

```
qros 第 8 轮 HOLD —— 第六实例（普通文件被当作目录放行，四种形状全复现）
     骨架按裁定倒转；我自己的三条测试把缺陷断言成了正确行为，已就地更正。
     设计出自第 8 轮复审席，后续认证不得声称对该元素独立。

ITSF 第 1 轮 HOLD 五条：四条真、已闭合；第五条是我造的、已撤回
     ① 传输锚点不存在（我声称自身哈希在 §1，表里没那行）→ 改指登记册
     ③ falsifier 现已在批准原文字节上闭合；原像唯一性全文扫描命中恰好 1 处
       （跨度是靠哈希选中的，ratification 记录的行数只是搜索线索）
     ④ AnnAssign 别名 + write_bytes(b"") 两条绕法
     ⑤ 「跨四结局」实际只跑三条
     ② → §14 撤回
     顺带量到 SILENT_DELETE_FORBIDDEN 是导出值不是批准值，(b) 依据行已更正
```

**ITSF 4465/0 · qros-runtime 1057/22/25。机制仍零改动。**

---

## 还压在你手上、我不动的

```
八项授权            全 NO；迁移 ①②③ 全 NO（③ 另有硬件阻断）
R4                  迁移执行完成之后才起草
qros 倒转默认        作为设计的正式采纳
qros HEADER_SCOPE    独立窗口复核；ORIGINAL_PACKET_WORK 仍 UNRESOLVED
32,767 等号处         保守拒绝，还是另定可移植性政策
「出处未知」          真的，但不是 (a) 的缺陷；是否处置与判据(1)无关
三条裁定的独立性      dec-four-owner · dec-scope-boundary · dec-registry-migration
四个决策席无席位轴行   那四席状态 UNKNOWN，不是 NONE。我没有编造行。
qros 席位台账        仍不存在，八个席位无一行记录
```

---

## 以下为更早的记录，保留不改

---

## 先读这一段 —— 2026-08-27 之后的状态

**R3 已由 Aaron 批准**（`ops/ND1_PROFILE_RATIFICATION.md` §9，绑 doc HEAD
`2728e43`），**CR1 已转录进生产代码**，Fable 的三项裁定（R-A=FULL、R-B=接受构造、
R-C=PER_ID_ONLY）**能执行的部分全部执行完毕**。ITSF 全量 4290/0。

**builder 这边已经没有可独立推进的 DAG 节点了。** 恢复锚 §4 明写：N09 需 Aaron 的
P2；N10 依赖 N09 的真实执行；N11 从未实现；N13 依赖 N11。

### 只剩四件，全在 Aaron 手上

```
1. P3 与失败事件的写者是谁 —— D-3 的核心矛盾：已批准 actor 表派给 runner，
   而全局边界 4 写「只有主代理写 registry」。两条已批准规则相抵。
   建议交决裁席（提案是 builder 写的，不宜自裁）。
2. 目录创建授权的四要素 —— 来源／actor／精确文本／commit 绑定／有效期。
   builder 可备模板；填写与生效是 Aaron 的。
3. D-3 的五项 UNRESOLVED_FOR_AARON —— 见 ops/RULING_SOL_D3_HOLD_2026-08-26.md。
4. N09 的 P2 —— §D.10.4 要求 Aaron 单独的、绑定完整 40 位 commit 的精确语句。
   builder 不得代填（常设禁令「不填 P2 占位符」未撤销）。
```

**三条独立授权仍不得合并**（ND1）：目录创建 / 写探针 / 执行。
`DIRECTORY_CREATION_AUTHORIZED=NO` 时，签了 P2 也不能建 `supplements\` 子树。

### qros-runtime 第二维护窗：开着，第 3 轮在飞

```
提示词  build-evidence/PROMPT_WINDOW2_SOL_ROUND3.md
钉子    REVIEWED_SET_UNCHANGED_SINCE=7ca707e
状态    第 1、2 轮均 HOLD 并已 reproduce-first 修复；956/22/25 全 PASS
闭窗    未做 —— ITSF 注册表未切、偏离记录未闭合、过渡形 B 继续有效、
        GRAD 试点被互斥挡着。这几项两轮都列为 UNRESOLVED_FOR_AARON
```

---

## 以下为 2026-08-26 的记录，保留不改

---

## 现在挂着的交付

### ①（已完成）八项待裁 —— Fable 已裁，Aaron 已采纳

```
DECISION_ID  dec-eight-open-2026-08-26        DELEGATED=YES
裁定全文     ops/RULING_FABLE_EIGHT_OPEN_2026-08-26.md
             sha256 5116f7b03dabe6cc4a8a2357b02b4b30e3a9227d050e41d9c1f0943262ed7dd3
采纳记录     ops/OWNER_DECISIONS_2026-08-26.md（逐项结算表在 OD-2026-08-26-3）
登记表       已清空（十路径解冻）
```

**第 4、5 项已完成**（所欠仅决策记录，且本就零改动）。**其余六项的实质选择已定，
但执行仍欠 Aaron 的具体动作** —— 逐项见 OD-2026-08-26-3 的「还欠」栏。
**八项不解锁 D-3**：其 HOLD 条件 3 继续在 force。

### ② 等 Aaron —— 六个具体动作

1. **全局 `~/.claude/CLAUDE.md` L6 exposure 句的修订授权**（第 1 项）
2. **carve-out 行使 ＋ 迁移执行授权**，并确认 08-25 hold 不覆盖本项（第 2 项）
3. **开启 qros-runtime 维护窗**（第 3 项）
4. **ND1 profile R3 修订的 ratify**，走提案→fresh Sol→Aaron 三步（第 6 项）
5. **见证目录的单独目录创建授权**，若落在 `C:\Users\Aaron\quant-data\` 下（第 7 项）
6. **席位台账分类**：第 3 行终分类、第 4 行 `NOT_EXPOSED` 值的存废、第 5 行终分类

**Aaron 2026-08-26 已把上述 1–6 之外的决定再次委托 Fable**（第 6 项走 Sol 复核，不在委托范围内）。决策包见 `ops/DECISION_PACKET_REMAINING_FABLE.md`。

### 准备进度（Aaron 2026-08-26：「全部都可以开始准备做了」）

| 项 | 备妥了什么 | 落地还欠 |
|---|---|---|
| **1** | `ops/PREP_ITEM1_L6_EXPOSURE_TEXT.md` —— 逐字终稿可整段替换；条件 2 已核验 | 你对全局 `CLAUDE.md` 的修订授权 |
| **7** | `ops/REGISTRY_SYNC_FAILURE_MODEL.md`（边界 3+4）＋ `src/itsf/s0/registry_witness.py`（边界 1+2，13 测试、6 变异全红） | 见证根的目录创建授权；之后才接入生产门 |
| **2** | `ops/PREP_ITEM2_QUARANTINE_MIGRATION.md` —— 可行性已测（生产代码零路径引用，32 条待改全在测试／配置／文档）＋迁移计划 | carve-out 文本、hold 范围确认、**外加仓根台账三选一**（裁定没区分它） |
| **3** | `ops/PREP_ITEM3_SAVE_DIR_CONFIGURABLE.md` —— 补丁设计已出；接缝已在（`required_save_path` 早就收 `repo` 却没用） | 开维护窗，**外加范围三选一**（`header.py:201` 是同一缺陷的第二处，D-4 未点名） |
| **6＋8** | **`ops/PROMPT_ITEM6_SOL_REVIEW.md`** —— 完整 packet＋十条冻结送审集。第一次交付裸文件被判 `REJECTED_INCOMPLETE`（origin=BUILDER），**那是我的错**，本次是补正 | 把提示整份发给新 Sol；Sol 过后你 ratify |

**第 7 项的代码刻意未接入任何门**：`witness_path` 是必填参数、无默认值，模块
永不建目录（变异证红）。接入会改变运行期行为，而运行期行为依赖那个尚未授权的
见证根。

### ③ N09 的 R3 设计 —— **已完成**（2026-08-27）

**这一段此前是错的，2026-08-27 改正。** 原文写「R3 在 ① 返回之前写不了」——
那是对 High #2 的转述，而 Sol 原文说的是 the claimed execution path 建不了，
并明确给出第二分支：`or limit the authorized build explicitly to an
always-refusing scaffold`。五条最小解阻条件里 **1／2／4／5 全是 builder 的活**，
第 3 条自带 builder 可走的分支。裁定全文与逐条复现见
`ops/RULING_SOL_N09_R2_HOLD_2026-08-26.md`。

**R3 已写完**：`ops/N09_EXECUTION_PATH_DESIGN_R3.md`，范围取条件 3 的第二分支
（`BUILD_SCOPE=DEFAULT_REFUSE_SCAFFOLD_ONLY`），五条最小解阻条件逐条应答：

```
条件 1  三个 checkpoint 各自的副作用断言（R2 那条统一断言对 C_BUILD_2/3 不成立）
条件 2  冻结 A1/F2/indeterminate 矩阵 —— 并暴露一个真实缺陷：archive_policy_a
        是一道门，其拒绝经路由器 A 发 F2，而已批准政策要求这一格发 A1
条件 3  取第二分支：默认拒绝骨架
条件 4  钉死 structural-only 调用图（loader → build_universe →
        build_vol20_regime_mapping_from_universe → build_event_stratum_map），
        AST 层面禁止 build_s0_dataset / compute_day / labels / Oracle / study
条件 5  点名 atoms.canonical_json；落点进封存清单；P3 之前绑定；
        P3 之后落盘失败 = INDETERMINATE 走 Aaron
```

R3 对现有代码的每条断言由 `tests/test_n09_r3_design_facts.py` 机械钉住
（21 项，4 条变异证红）。

**2026-08-27／28 更新 —— §1–§6 现在全部有机制了。** 措辞要准：
**加的是守卫，不是骨架本身**；骨架在各出口处的其余结构仍未建。

```
§1  三个 checkpoint 各自的断言     tests/test_n09_checkpoint_assertions.py（19）
§2  两个路由器 ＋ 转移矩阵         supplement_contract（当日早些时候）
§4  structural-only 调用图         tests/test_n09_scaffold_criteria.py（17）
§5  precheck 证据四规则            tests/test_n09_precheck_evidence_rules.py（22）
§6  骨架的四条判据                 同上 scaffold_criteria
```

**过程中测出四处 R3 自己的事实陈述不成立**，逐条记在 R3 §9–§11：

```
§5 说三份 canonical_json 同体      不同体 —— 一份缺 allow_nan，对 NaN 产出非法 JSON
                                   Aaron 2026-08-28 作废该范围声明，已修
§5 把第三份写成 canonical_json      实为 _canonical（行号对，名字不对）
§5 说是三份                        按签名找是五份，但另两份是 manifest 的另一套合同
§1 说 C_BUILD_2 三条都是文件系统事实 其中的状态只存在于 resolve_partial 调用内部，
                                   而它不提供让门在那一刻运行的钩子 ——
                                   已出决裁包 dec-c-build-2-hook-2026-08-28
```

**`STATUS=NOTHING_IMPLEMENTED` 对「骨架的出口结构」仍然逐字为真**，
对「§1–§6 的机制」已不再为真。

**越过骨架仍需 Aaron 的四项**（R3 §7，builder 不代填）：P3／失败事件的写者、
目录创建授权的四要素、D-3 的五项 `UNRESOLVED_FOR_AARON`、N09 的 P2。

---

## 禁区 —— 任何复审席位交付时必须随附本节

**这一节是本文件存在的第二个理由。** Review Packet 由 `qros packet` 机械生成，
**没有承载禁区清单的字段**；2026-08-26 就因为清单只写在提示词里、而交付的是
packet，烧掉了第二个复审席位。本文件是那份清单的常驻载体。

**交给任何复审席位时，把本节一起给他。**

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`。
**读那个 json，把里面每一条路径当作关闭。** 尤其点名：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

它**既是 outcome-carrying，又是本项目的恢复锚**（§1「恢复序」是任何会话定位
状态的标准第一站）。按常规做一次状态定位就会踩中。

**而且「别打开它」还不够。** 第二次暴露的席位**没有打开它**——一次广域符号搜索
把片段带了出来。所以：**不要在本仓做广域检索**。需要什么路径就列出来，由工作
会话提供逐字节内容（Review Packet 的 `PULL_PROTOCOL` 正是这个约定）。

---

## outcome-blind 席位的操作规则（D-2 / S1(b)，2026-08-26 生效）

**这一节必须随每一次复审交付一起给出。** 它不是建议。

### 你可以从哪里开始（许可起点，D-2 条件 4）

```
ops/RECOVERY_ANCHOR.md
```

**outcome-clean，永不隔离，专为 blind 席位可读而写。** 它给出恢复序、两条暴露轴、
禁区清单与本节的检索禁令。只告诉一个席位「不许读什么」而不告诉它「可以从哪开始」，
正是第一个席位自己找路、并因此被烧的原因。

### 规则

```
BLIND_SEAT_MAY_NOT_SEARCH_THE_REPOSITORY = 是
```

**outcome-blind 席位不得在本仓做任何自主检索**——不 grep、不 rglob、不广域符号
搜索、不「顺手看一眼」。**需要什么路径就列出来，由工作会话提供逐字节内容**
（Review Packet v1 的 `PULL_PROTOCOL` 就是这个约定）。

### 为什么是禁令而不是提醒

两个席位已经烧掉，**第二个从未打开过那份文件**——一次广域符号搜索把隔离锚的
片段带了出来。第三个席位（决裁席）做了**一次单模式定向 grep**，同样触到了。

所以「别打开文件 X」这类围栏**在原理上不够**：只要隔离内容还在席位能检索到的
树里，任何检索都可能带出它。在拆锚（D-2 的 A 半）落地之前，**禁止检索是唯一
真正起作用的那一半**。

### 两条暴露轴，一并告知（D-1 条件 1）

```
研究轴  ops/EXPOSURE_LEDGER.md        —— 研究自由度消耗   【OFF-LIMITS，blind 席位不得读】
席位轴  ops/REVIEWER_EXPOSURE_LOG.md  —— 复审席位被烧；不消耗研究自由度   【可读】
```

**烧掉一个席位不消耗研究自由度**，所以两者分账。要报告自身暴露状态，看席位轴；
要报告研究暴露状态，看研究轴。**两者永不混记。**

### 禁区（S2：本节机械附着于每一种交付载体）

权威清单：`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome`，**每一条
路径都当作关闭**。尤其：

```
ops/outcome_quarantine/MC_TO_STRATEGY_MASTER_PLAN.md
```

它既是 outcome-carrying，又是本项目的恢复锚——按常规做一次状态定位就会踩中。

---

### 交付前必须逐条核对的一件（2026-08-26 加入）

**本次交付点名的每一个路径，都不得出现在 `carries_outcome` 里。**

`ops/DECISION_PACKET_FOUR_OPEN_2026-08-26.md` 就栽在这上面：它一边写着禁区
清单，一边在呈交格式一节让复审者「形式沿用
`ops/outcome_quarantine/RULING_PROPOSAL_ND2_ND3_FABLE_2026-08-24.md`」——**而那份文件在隔离名单
上**。同一份文件里，禁止与指令自相矛盾。Fable 是先查注册表才没被烧，**那是它
谨慎，不是我做对了**。

机械做法：交付前把文件里出现的每个 `ops/...md` 路径与
`OUTCOME_CARRYING_ARTIFACTS.json` 求交集，非空即停。

---

## 已完成（保留最近三次，便于回溯）

| 何时 | 交给谁 | 什么 | 结果 |
|---|---|---|---|
| 2026-08-26 | Fable | 四项待裁决策包 | **全部返回** —— D-1=A、D-2=C、D-3=C（三步之第一步，故成为上面 ①）、D-4=改；裁决全文是隔离件，D-3 一节的干净副本见 `ops/D3_REGISTRY_WRITER_PROPOSAL.md` |
| 2026-08-26 | fresh Sol | R2 设计审（Review Packet v1，`rv-3651f9fe0b68-da56aecb6991`） | **HOLD** —— 三条 High 全部经 builder 独立复核成立；**四条 finding（3 High＋1 Medium）全部经 builder 独立复现成立**；裁定全文记录 `ops/RULING_SOL_N09_R2_HOLD_2026-08-26.md`（此前本格误指 `A2_N09_SOL_EXPOSURE_AND_REDESIGN_2026-08-25.md`，那份装的是 08-25 那轮的六条 REDESIGN）；席位暴露记 `ops/REVIEWER_EXPOSURE_LOG.md` 第 2 行 |
| 2026-08-25 | fresh Sol | MC-REG-COLLISION-001 批准 | **RATIFIED_AS_MODIFIED**（C2 被整条替换）→ 已实现，记录 `ops/RULING_MC_REG_COLLISION_SOL_RATIFICATION_2026-08-25.md` |
| 2026-08-25 | Fable | MC-REG-COLLISION-001 提案 | R2 提案 → 记录 `ops/RULING_PROPOSAL_MC_REG_COLLISION_FABLE_2026-08-25.md` |

---

## 交付前 builder 必须做的（清单，不是提醒）

1. 把送审工件**先 commit**，再 `derive_pin()` 派生钉子——钉子不手打。
2. 登记进 `ops/ARTIFACTS_UNDER_REVIEW.json`（含 `unchanged_since`）。
3. **提交之后**再跑一次
   `tests/test_artifacts_under_review_are_frozen.py`——不是提交之前。
4. 把上面「禁区」一节随交付一起给出。
5. **复审一返回，第一件事就是清空登记表** —— 在动任何被冻结的工件之前，不是之后。

   > **两次实测的教训（2026-08-26 迁移、2026-08-27 第六次 HOLD）。** 两次都是
   > 复审已经返回、我直接去改 findings 指出的文件，而那些文件还在冻结集里。
   > 冻结守卫两次都抓到了，但**它只在全套件里跑**——代价是一次 6 分钟的空跑。
   > 顺序对了就零成本：**清表 → 再改**。
   >
   > 改完之后跑的快速子集里**必须包含
   > `tests/test_artifacts_under_review_are_frozen.py`**（0.1 秒），
   > 否则这个错要等到全套件才暴露。
6. **交付说明里的路径一律写绝对路径。** 2026-08-26 实测：决裁席的工作目录在
   `Desktop`、不在仓内，而我给的是仓相对路径 `ops/PROMPT_...md`，它只能**先检索
   才能找到那份写着「不许检索」的文件**——三次文件名操作发生在读到禁令之前
   （席位台账第 5 行）。这次只命中文件名，纯属运气：`ops\PROMPT*` 那一次若有隔离件
   恰好叫 `*PROMPT*`，返回的就是禁区路径。**一个必须先被找到才能读到禁令的文件，
   本身就是缺陷。** 绝对路径形如
   `C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework\ops\<名>`。

前三条各自对应今天一次真实的失败，逐条写在
`ops/INCIDENT_TRANSPORT_HEAD_PIN_20260825.md` 与
`ops/INCIDENT_TRANSPORT_PIN_DERIVATION_20260825.md`。
