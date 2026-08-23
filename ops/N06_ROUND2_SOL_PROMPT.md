# N06 第二轮 — 给 fresh Sol 的提示词（逐字发送）

```
PROMPT_FOR=Codex GPT-5.6 Sol
WINDOW=NEW_TOP_LEVEL_SESSION（必须是全新会话）
MUST_NOT_BE=第一轮 N06 的那个 Sol 会话
CANDIDATE_HEAD=17904bf6aef2b11f898e05a7351123af614e6cfd
PRIOR_REVIEWED_HEAD=291786aec0a33826516b7b435446780530e46444（那轮判 HOLD）
```

> **为什么必须换会话**：第一轮 Sol 提了四条 finding，这四条是 Opus 修的。
> 提出者不宜验收自己所提缺陷的闭合（`session-conventions` §1：写 issue 的人
> 不该给"执行得好不好"打分）。且 fresh context independence 只在新的顶层
> 会话里成立。

---

## 逐字发送的部分（从下一行开始复制）

```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
ROLE=verifier
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=BUILDER_OF_THIS_WORK,REPAIRER_OF_THESE_FINDINGS,FIRST_N06_REVIEW_SESSION
LANE=MEASUREMENT
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
WHY_THIS_MODEL=N06 第二轮 exact-tree 验收；第一轮判 HOLD 的四条已修，提出者不得验收自己所提缺陷的闭合
```

N06 第二轮 exact-tree 验收。

仓库：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
候选 HEAD：`17904bf6aef2b11f898e05a7351123af614e6cfd`
上一轮被验、判 HOLD 的 HEAD：`291786aec0a33826516b7b435446780530e46444`

**动手前先逐个重算 SHA-256，任一不匹配即停止并报告**（artifact transport
rule；chat 里的字节不是真相源）：

```
ops\N06_REVIEW_HANDOFF.md          271c6036bb2d2c3470b3e39594a3b89151177dffa19afbe40c7a32299a7d8c8c
ops\ND1_PROFILE_RATIFICATION.md    cf2c3cb2bdb79b34498c2a7ebc53344c70ef89f0686466a010ce62431541d05e
ops\N06_HOLD_REPAIR_EVIDENCE.md    54ea4be3460d2f6cb4a2bc0e6a820c9d07c90a740c583c6e47c308a97739b375
ops\N06_HOLD_RED_PROOF.md          22ad0408bec397d6b185a7b3f8fed189844bfb05f8b9c2d923727cd785e1e55f
ops\DECISION_PACKET_N00_AND_ND1.md da64a3d68454e6f129287412f200ea51309ee85daad9d9bdb7465d9765e47991
```

先读 `ops\N06_REVIEW_HANDOFF.md`（它的 §0 列出上一轮四条 finding 及其处置，
§2 说明 gate 归属未定，§7 列出仍缺什么）。

### 一、上一轮四条 finding 的闭合，逐条独立复核

不要采信 builder 的自述；每条自己重算或重跑。

1. **High — 实现先于治理批准。** Aaron 于 2026-08-23 批准
   `ND1_RECOMMENDED_PROFILE_R2`。请核：R2 canonical bytes 重算是否
   `a3d40b7ce218294b75265622306bb91fc01081f98a0bacce8f8e86a3d3d8741d`；
   R2 是否 correction-only（对 R1 逐行 diff，差异应恰为 4 行，全在
   `PROFILE_ID` 与 P3）；代码 `supplement_contract.EVENTS["P3"]` 的前置/后继
   是否与 R2 的 `P3_PERMITTED_PREDECESSOR` / `P3_PERMITTED_SUCCESSOR` 一致。
2. **Medium — scope digest 编码。** `ops\N06_REVIEW_HANDOFF.md` 现记
   `e833ef7bb95bc03674516215d7d149f5815b9cf1d4b0ea333413689bff90efad`。
   请用 `qros-runtime\qros_runtime\serialize.py` 的 `scope_content_digest`
   对该件 §4.1 的 24 条 `(path, sha256)` 有序对独立复算并比对。
3. **Low — `$` 锚点。** 请自行遍历 `src\itsf\mc\` 下全部 supplement 相关模块
   （含 `day_strata_supplement.py`），确认不存在 `re.compile(r"^...$")` 形态的
   **校验用**锚点，并对已编译 pattern 做尾随 `\n` / `\r\n` 行为探测。
   注意：`supplement_registry.py` 里 `(.*)$` 那两处是**提取器**不是校验器，
   上一轮已判定不属此缺陷类——请自行确认该判定是否成立。
4. **Low — Python 版本契约。** `.python-version` 与 battery 断言是否一致，
   以及该契约是否真的是这些测试所需要的。

### 二、独立验收（不限于上一条）

- 生产封印边界：手工 payload 能否进入 `seal_supplement_production`；
  盲式保证（四字段行）是否在生产 seal 边界被重新校验。
- `B_DERIVE` 五个 gate 是否各自独立地拒绝 duck type / 子类 / 完美镜像。
- output-root 绑定与 `plan_supplement_paths` 的 containment / reparse /
  `<id>_<UTC>` 命名。
- registry fail-closed：next-value 序列、六个整数下界、`output_root` 绝对性。
- 全套件、collect count 与双 floor pin 是否自洽（应为 3966）。
- `git diff --check`、frozen hashes、protected state（registry `ee9da33f…`、
  exposure `382182bf…`、attestation `d839b965…`、S0-T001 封存 14 文件
  run==archive）、两个 `supplements\` 子树仍不存在、registry 中零
  `SUPPLEMENT_` 事件行。

### 三、明确不在你职责内、也不要替 Aaron 决定的

- 本次 review 属 **Stage I** 还是 **discretionary Tier-1**（决定 packet 能否
  生成；Stage I 最小基底要求 A2 记录，而本仓库无 `runs\`、无 A2 记录）。
- ITSF 是否纳入 L6 runtime，以及 `LANE` / `STAGE` 取值——spec §2.4 明写
  "never inferred"，属 Aaron。
- 任何执行授权。

### 四、你的产出

- `VERDICT: PASS | HOLD`，以及它**不是** `PACKET_OUTCOME`、不释放任何 gate
  transition 的明示（当前无 `qros-state.yaml`、无 issuance 可绑）。
- Critical/High 优先，逐条给具体证据（路径、行号、可复现命令）。
- 区分"你自己复现的事实"与"builder 自报的证据"。
- 独立性按维度分别陈述（context / authorship / model-diversity / empirical），
  不要给一个笼统的"独立"。
- 不要修仓库。发现缺陷只报告。

### 五、你应当知道的既有残留（不必重新发现，但可挑战其定性）

见 `ops\N06_HOLD_REPAIR_EVIDENCE.md` §3 的八条，其中最重要一条：
`__new__` + `object.__setattr__` 可绕过两处 capability 检查且无需读取任何
私有；builder 的立场是"真正成立的边界是**重新推导**而非 capability，因为每个
被篡改的事实都在各自专属码上被拒"。这一立场是否站得住，属你的判断范围。
```

---

## 附：本件自身的哈希

生成后请以 `sha256sum ops/N06_ROUND2_SOL_PROMPT.md` 自查；本件仅为提示词
载体，不是 Review Packet v1，也不授权任何执行。
