# N09 A2 —— 复审席位 outcome 暴露 ＋ 非正式 REDESIGN 裁定

```
RECORD_TYPE=REVIEW_OUTCOME_AND_EXPOSURE_EVENT
ITEM_ID=N09-EXECUTION-PATH-A2
DATE=2026-08-25
REVIEWER=Codex GPT-5.6 Sol，fresh top-level session
TRANSCRIBED_BY=Opus 5 main agent（builder seat）—— 转录，非背书

L6_VERDICT=REJECTED_INCOMPLETE
L6_GATE_EFFECT=NONE —— **不释放 A2→B，不授权构建，不授权运行**
ENGINEERING_VERDICT=REDESIGN（**非正式**，见 §2）
EXPOSURE_EVENT=YES —— 见 §1，**待 Aaron 授权后方可入账**
```

---

## 1. 先说最重要的：一个复审席位被烧掉了

Sol 自陈：

> 「读取治理状态时，我误入已隔离的 outcome-carrying master plan，看到了 verdict
> token 和 exposure count；未读取真实 Development 数据或目标绩效数值。」
> 「本会话已 outcome-exposed，不能再承担未来的 outcome-blind Stage I。」

其 header 自报 `OUTCOME_EXPOSED=TARGET_METRIC`。**本记录不下调它的自评。**

### 1.1 这是我的错，不是它的操作失误

`ops/MC_TO_STRATEGY_MASTER_PLAN.md` **确实登记在
`ops/OUTCOME_CARRYING_ARTIFACTS.json` 的 `carries_outcome` 里**（已核，11 项之一）。

而它同时是本项目**唯一的恢复锚**：主计划 §1「恢复序」就是任何会话定位状态的
标准入口。**于是任何 outcome-blind 复审者，只要按恢复序做一次正常的状态定位，
第一步就会打开一份 outcome-carrying 文件。**

我发出的 A2 提示词**没有给禁区清单**。送审的六份工件是 outcome-clean 的
（`test_review_artifacts_are_outcome_clean` 通过），但**没有任何东西阻止复审者
导航到送审集之外**。守卫查的是「送来的东西干净」，不是「他会走到哪里」。

### 1.2 待 Aaron 授权入账的 exposure 事件

**本记录未向 `ops/EXPOSURE_LEDGER.md` 追加任何行。** 常设禁令写明「未经单独
授权不得追加 registry／exposure 事件」，故按限制性读法停在这里。

同时如实说明代价：L6 §10.1 是「无账即 `UNKNOWN`，绝不为 `NONE`」。**不入账
不等于没发生，只等于状态未知**——那比记下来更糟。

拟入账字段（Aaron 裁定后由他或经他授权追加）：

```
EVENT              = REVIEWER_OUTCOME_EXPOSURE
DATE               = 2026-08-25
SEAT               = Codex GPT-5.6 Sol，fresh session（N09-EXECUTION-PATH-A2）
ARTIFACT_READ      = ops/MC_TO_STRATEGY_MASTER_PLAN.md（carries_outcome）
WHAT_WAS_SEEN      = verdict token ＋ exposure count（复审者自陈）
WHAT_WAS_NOT_READ  = 真实 Development 数据；目标绩效数值（复审者自陈）
CLASSIFICATION     = TARGET_METRIC（复审者自评，未由 builder 下调）
N_TRIALS_MOVED     = NO
CONSEQUENCE        = 该会话不得再承担 outcome-blind Stage I
CAUSE              = builder 未在提示词中给出 outcome-carrying 禁区清单
```

### 1.3 一个比本次事件更大的结构问题，交 Aaron

**恢复锚本身是 outcome-carrying 的。** 这不是这一次的偶然，它对**每一个**未来的
outcome-blind 复审者都成立，而且此前一直成立——只是过去的提示词都足够窄，没人
走到那里。

两条可能的处置，**都不是我能定的**：

- **A** —— 把主计划拆成「outcome-clean 恢复锚」＋「outcome-carrying 附录」，
  恢复序指向前者。改动大，触及 append-only 的锚文件。
- **B** —— 不拆，改为要求**每一份复审提示词携带显式禁区清单**。便宜，但把安全性
  押在「每次都记得写」上——而本项目今天已经证明过三次，「记得」不是控制。

builder 已落地 B 的机械化版本（见 §4），但**A 与 B 之间的取舍归 Aaron**。

---

## 2. 为什么这份裁定是「非正式」的

Sol 的正式状态是 `REJECTED_INCOMPLETE`，原因两条：

1. **Review Packet v1 absent** —— L6 要求复审以 Review Packet v1（36 个
   origin-tagged 字段）travel；我发的是散文提示词。**不是 Review Packet 的复审
   不释放任何 gate。**
2. 复审者 outcome-blindness 已失。

还有一条我自己的命名错误：**项目现处 `STAGE=C`，早已越过 A2**。L6 的 A2 是
`A→A2→B` 链上的门。我需要的其实是「动手前的 fresh-seat 设计挑战」，却把它命名为
A2，等于邀请对方按 L6 门来评——而那必然评不过。

**所以：§3 的六条只能作为工程意见采纳，不得记为委托裁定，也不释放任何门。**

## 3. 六条修改（工程内容；builder 已独立复核其中两条）

```
1. C_BUILD 拆成显式 checkpoint：首次写入前的 row/product 校验；staging 中的
   partial/seal 校验；archive report 存在之后才跑 archive_policy_a。
   生产侧校验仍是唯一真相源，runner 的门只对其结果/异常做分类，不重复实现不变量。
2. 扩展或拆分 GateContext，使一个门不可能在其所需证据存在之前运行。
   每个 C_BUILD 门配一条红证/变异证明，并证明该门通过之前不产生任何效果。
3. snapshot₂ 要定义在精确的比较域上：必须等于 snapshot₁ 加**恰好一条 canonical
   P3 行**，而不是「解析后事件序列等价」。P3 追加失败／半追加／回读不符是
   **不确定的半转移，走 Aaron**，不自动归入普通 F2。
4. 三个快照用不同名字与类型：supplement_registry_snapshot_before_p3 /
   _after_p3 / s0_custody_authorization_snapshot。
   consumer.prepare_mc_input 只接 S0 custody 快照；不得调用
   real_input.prepare_real_mc_input。
5. day_rows 生产者必须复用生产侧 S0 universe/data assembly 路径。
   **vol 与 event 两个分层都来自 s0.dataset 的映射**；s0.context 提供的是上游
   事件事实，**不是最终 event-stratum 映射**。要求对
   authority.expected_day_set 做逐日精确对拍。
6. bundle_precheck 的字节/哈希表必须持久化，并在 P3 之前精确绑定到
   prepared.file_sha256，进入运行证据。
```

### 3.1 builder 独立复核了其中两条

**第 1 条（最强反对）—— 成立。** `GateContext` 的字段是
`supplement_id / head_commit / registry_text / runs_root / archive_root /
repo_dirty_paths / g9_flag / second_copy_flag / frozen_hashes_ok / chain /
authority / prepared / utc_stamp`：**没有 `product`，没有 seal 证据，没有
archive report**（`archive_root` 只是根路径）。而五个门分属首次写入前／staging 中／
archive 后三个时刻，却被 `run_stage_gates("C_BUILD", ctx)` 一次性跑在同一个上下文
上。**我设计里那句「跑 A→B→C」不成立。**

**第 5 条 —— 我的设计写错了事实。** 最终 event-stratum 映射归 `s0/dataset.py`
（`event_stratum_of` / `build_event_stratum_map` / `RULED_EVENT_NA_MAPPING` /
`EVENT_STRATA`），`s0/context.py` 只提供上游 flag。我的设计 §4 把它归给了
context。**Sol 是对的。**

### 3.2 复审者自陈的验证局限（如实转录）

> 「冻结守卫 7 项、outcome-clean 守卫 4 项均通过手工函数执行。**完整 pytest 未
> 运行**——PATH 中没有 Python，随附 Python 3.12 环境又未安装 pytest；未擅自安装
> 依赖。没有修改任何文件。」

### 3.3 设计贡献登记（复审者要求，予以照办）

> 「若上述精确 checkpoint 或 snapshot 规则被逐字采纳，应在 N09 lineage 中记录为
> 设计贡献。」

**照办**：若第 1–6 条被逐字采纳，其设计贡献归该 Sol 会话，须在 N09 lineage 中
具名记录，且带 `DELEGATED=YES`。

### 3.4 独立性范围（复审者自陈）

新会话、未参与实现、保持只读；**但在 C2 派生部分没有模型家族多样性**
（C2 由另一个 Sol 会话撰写）。

---

## 4. builder 已做与未做

**已做**：核实主计划确在 outcome-carrying 登记表内；核实第 1 与第 5 条；把禁区
清单机械化进复审提示词守卫（§1.3 的 B 方案）；本记录落盘。

**未做**：未追加任何 exposure 行；未改任何送审工件；未按六条改设计（下一步，
且第 3 与第 4 条含「走 Aaron」的分支）；未读真实 Development 数据；未创建目录。

## 5. 欠 Aaron 的两件

1. **授权把 §1.2 的 exposure 事件入账**（不入账 = 状态 `UNKNOWN`，不是 `NONE`）。
2. **恢复锚 outcome-carrying 的结构处置**：拆锚（A）还是只靠提示词禁区清单（B）。

---

## 6. 一条 builder 的自纠，写在这里因为它是同一个毛病

为堵 §1.3 的 B 方案，我加了守卫
`test_a_live_prompt_names_the_outcome_carrying_artifacts_as_off_limits`。
它有两半：一半查提示词是否点名登记表，一半查是否点名恢复锚。

**第二半一开始是坏的。** `carries_outcome` 的条目是对象不是字符串，我写的
`"MASTER_PLAN" in entry` 查的是**字典的键**，恒为 False——**锚检查静默地什么都
没做**。我是在核对「为什么只报了一条而不是两条」时发现的；如果当时没多问那一句，
它会作为一条永远通过的绿灯留在套件里。

一个通过了却什么都没保护的守卫，正是我今天已经写过三份事故记录去警惕的东西，
而我又写了一个。已修：条目先归一化为路径，并对「归一化后为空」和「找不到锚」
各加一条断言——**查找目标不存在时必须失败，而不是安静地返回空**。
修好后变异验证：两半同时报错。
