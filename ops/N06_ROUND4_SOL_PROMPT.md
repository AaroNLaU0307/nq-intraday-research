# N06 第四轮 — 给 fresh Sol 的提示词（逐字发送）

```
PROMPT_FOR=Codex GPT-5.6 Sol
WINDOW=NEW_TOP_LEVEL_SESSION（第四个全新会话）
MUST_NOT_BE=builder ／ 第一、二、三轮 N06 会话
```

> 第三轮提出标量子类 High，由 builder 修复。提出者不宜验收自己所提缺陷的
> 闭合（`session-conventions` §1）。前三轮同理。

---

## 逐字发送的部分（从下一行开始复制）

```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=BUILDER_OF_THIS_WORK,REPAIRER_OF_THIS_FINDING,FIRST_N06_REVIEW_SESSION,SECOND_N06_REVIEW_SESSION,THIRD_N06_REVIEW_SESSION
LANE=MEASUREMENT
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
WHY_THIS_MODEL=N06 第四轮 exact-tree 验收；第三轮的 High 已由改设计闭合，提出者不得验收自己所提缺陷的闭合
```

N06 第四轮 exact-tree 验收。

仓库：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
代码候选 HEAD：`ea610e728386705fa1793051f29e5aaf7d0e2e5a`（handoff 生成于此）
其后仅有 doc-only commit；工件由**内容哈希**钉定，重算匹配即可开工
第三轮被验、判 HOLD：`2a7374fc069274eeab2b090f5be84520efda5868`
第二轮：`17904bf6aef2b11f898e05a7351123af614e6cfd`
第一轮：`291786aec0a33826516b7b435446780530e46444`

**动手前逐个重算 SHA-256，任一不匹配即停止并报告**：

```
ops\N06_REVIEW_HANDOFF.md                72970e94f2a5d2bbc9ec1102c335f3bd9a5d2a9afd7f6edccee736851c7491d3
ops\N06_ROUND3_HOLD_REPAIR_EVIDENCE.md   aa07383c4cf19d7a9c28aa072ed722ee16c8807ed50b4c17ad772f67d9db5aec
ops\N06_ROUND2_HOLD_REPAIR_EVIDENCE.md   28ab25041bf0b20cae1db1c20d0feb8f37a689138655e9aced86bd6faa32e441
ops\N06_HOLD_REPAIR_EVIDENCE.md          6b12ca2a1868f2a634522cfdfd792fdc777bbbc0b2b0fa8ccd0c3ecabe6690ce
ops\ND1_PROFILE_RATIFICATION.md          cf2c3cb2bdb79b34498c2a7ebc53344c70ef89f0686466a010ce62431541d05e
ops\N06_HOLD_RED_PROOF.md                22ad0408bec397d6b185a7b3f8fed189844bfb05f8b9c2d923727cd785e1e55f
ops\DECISION_PACKET_N00_AND_ND1.md       da64a3d68454e6f129287412f200ea51309ee85daad9d9bdb7465d9765e47991
```

先读 `ops\N06_ROUND3_HOLD_REPAIR_EVIDENCE.md`，再读 `ops\N06_REVIEW_HANDOFF.md`。

### 一、这一轮不是补丁，是改设计——请攻它的新结构

前三轮的 High 是同一个形状：**调用方给的值参与了一次决定要不要写的比较**
（R1 authority／R2 payload 读四次／R3 快照里的说谎标量）。本轮按 Aaron 裁定
改了设计：

- `seal_supplement_production` 从 authority 派生 day universe 与 binding，
  **用 rows 重建 payload**，序列化**重建结果**；
- receipt 对着**重建结果**再验一次；
- 冻结只收**精确内建标量**，子类拒绝而非强转。

请自行构造攻击，至少覆盖：

1. **`rebuilt` 与 `declared` 之间还有没有缝**——有没有任何一条路径让写出的
   字节不是 `_rebuild_from_rows` 的产物。
2. **`_rebuild_from_rows` 自己可否被污染**：`supplement_build_inputs`
   返回的 binding／day set、`build_day_strata_supplement_test_only` 内部的
   `_validate_row`（它按引用返回 `trade_date`、对两个 strata 调 `str()`）。
3. **冻结的完备性**：`bool`/`int` 子类、`float` 子类、嵌套三层以上、
   Mapping 子类伪装、`__class__` 属性欺骗、`__subclasshook__`／
   `__instancecheck__` 干预 `isinstance(value, Mapping)` 的两个分支。
4. **顶层 vs 嵌套是否真的同一条规则**（第三轮修复正是因为它们曾经不同；
   builder 自己写测试时才发现顶层内联了更弱的版本）。
5. 拒绝顺序是否仍如宣称：手工装配产物先以自己的名字失败；
   `production_day_set_drift` / `production_rows_digest_drift` /
   `production_forbidden_row_field` 是否都仍可达且未被遮蔽。
6. `production_payload_drift`、`production_rebuild_refused`、
   `production_supplement_id_divergence` 三个新码是否可达、是否有死码。

判据不变：**任何"封印返回且字节含禁止字段"或"声明摘要 ≠ 实际 rows"都是
High**。另加一条：**任何"写出的字节不是 seal 自己重建的那份"也是 High**。

**内存捕获，不要写 governed roots**（替换 `resolve_partial` 即可）。

### 二、三个你应当知道的历史，可挑战其定性

1. **F1/F2 已被重新定性**：不再是良性残留，而是第三轮封存违规的组成部分。
   若你认为现在的定性仍然过宽或过窄，直说。
2. **"重新推导才是边界"这句话已被两次收回**，第三轮发现它还立在两份文档里，
   现已全部更正。请核对是否还有第四处。
3. **builder 自己发现的洞**：`freeze_payload` 顶层曾内联更弱的键规则。这类
   "同一规则的两份实现"是本模块反复出问题的位置，值得优先找。

### 三、其余生产边界（同前三轮）

`B_DERIVE` 五个 gate、output-root 绑定与 `plan_supplement_paths`、
registry fail-closed（next-value 序列、六个整数下界、`output_root` 绝对性）、
`.partial` 分支 C/E、default-refuse 生产入口。

### 四、机械项

全套件与 collect 应为 **3977** 且与双 floor pin 一致；`git diff --check`；
frozen hashes 7/7；registry `ee9da33f…`、exposure `382182bf…`、
attestation `d839b965…`；S0-T001 run/archive 14 文件逐文件相等；
两个 `supplements\` 子树不存在；registry 零 `SUPPLEMENT_` 行；
`final_candidate_scans.py` 三个既有 false positive（**不得**被伪称 CLEAN）。

### 五、明确不在你职责内

本次 review 属 Stage I 还是 discretionary Tier-1；ITSF 是否纳入 L6 runtime，
`LANE`／`STAGE` 取值（spec §2.4：never inferred）；任何执行授权。以上归 Aaron。

### 六、产出

- `VERDICT: PASS | HOLD`，并明示**这不是 `PACKET_OUTCOME`、不释放任何 gate
  transition**（无 `qros-state.yaml`、无 issuance 可绑）。
- Critical/High 优先，逐条给路径、行号、可复现命令。
- 区分"你自己复现的事实"与"builder 自报的证据"。
- 独立性按 context／authorship／model-diversity／empirical 四维分别陈述。
- 不要修仓库。

### 七、若你再判 HOLD

主计划 §3 边界 10 规定同类反复即停。这已是第四轮。**若你的 High 与前三轮
属同一形状**（调用方的值参与决定写不写的比较），请明说，因为那意味着这套
生产路径需要整体重新设计而不是再修一轮——那是 Aaron 的决定，不是我们的。
```

---

*本件仅为提示词载体，不是 Review Packet v1，不授权任何执行。*
