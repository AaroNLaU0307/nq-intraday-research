# N06 第三轮 — 给 fresh Sol 的提示词（逐字发送）

```
PROMPT_FOR=Codex GPT-5.6 Sol
WINDOW=NEW_TOP_LEVEL_SESSION（第三个全新会话）
MUST_NOT_BE=builder ／ 第一轮 N06 会话 ／ 第二轮 N06 会话
```

> 第二轮提出 TOCTOU High，由 builder 修复。提出者不宜验收自己所提缺陷的
> 闭合（`session-conventions` §1）。第一轮同理。故本轮必须是第三个会话。

---

## 逐字发送的部分（从下一行开始复制）

```ini
RECOMMENDED_MODEL=Codex GPT-5.6 Sol
EFFORT_INTENT=VERY_HIGH
RECOMMENDED_EFFORT=Extra High
EXECUTION_MODE=STANDARD
ROLE=verifier
WINDOW=NEW_TOP_LEVEL_SESSION
MUST_NOT_BE=BUILDER_OF_THIS_WORK,REPAIRER_OF_THIS_FINDING,FIRST_N06_REVIEW_SESSION,SECOND_N06_REVIEW_SESSION
LANE=MEASUREMENT
OUTCOME_EXPOSED=NONE
PREREG_SEALED=YES
WHY_THIS_MODEL=N06 第三轮 exact-tree 验收；第二轮的 TOCTOU High 已修，提出者不得验收自己所提缺陷的闭合
```

N06 第三轮 exact-tree 验收。

仓库：`C:\Users\Aaron\OneDrive\Desktop\Quant trade\Intraday Trend Strategy Framework`
候选 HEAD：`<本文件所在 commit，见终报>`
第二轮被验、判 HOLD 的 HEAD：`17904bf6aef2b11f898e05a7351123af614e6cfd`
第一轮被验、判 HOLD 的 HEAD：`291786aec0a33826516b7b435446780530e46444`

**动手前逐个重算 SHA-256，任一不匹配即停止并报告**：

```
ops\N06_REVIEW_HANDOFF.md               3398e05118c98127d38848f2a696493976c39654529a72e4e72664254f73da9a
ops\N06_ROUND2_HOLD_REPAIR_EVIDENCE.md  28ab25041bf0b20cae1db1c20d0feb8f37a689138655e9aced86bd6faa32e441
ops\N06_HOLD_REPAIR_EVIDENCE.md         6b12ca2a1868f2a634522cfdfd792fdc777bbbc0b2b0fa8ccd0c3ecabe6690ce
ops\ND1_PROFILE_RATIFICATION.md         cf2c3cb2bdb79b34498c2a7ebc53344c70ef89f0686466a010ce62431541d05e
ops\N06_HOLD_RED_PROOF.md               22ad0408bec397d6b185a7b3f8fed189844bfb05f8b9c2d923727cd785e1e55f
ops\DECISION_PACKET_N00_AND_ND1.md      da64a3d68454e6f129287412f200ea51309ee85daad9d9bdb7465d9765e47991
```

先读 `ops\N06_ROUND2_HOLD_REPAIR_EVIDENCE.md`，再读 `ops\N06_REVIEW_HANDOFF.md`。

### 一、第二轮 High 的闭合，自己攻，不要采信

缺陷：`seal_supplement_production` 多次读取 caller 控制的 `product.payload`，
状态型 Mapping 可让检查看到合规 rows、序列化看到带 `pnl` 的 rows。

修复：`freeze_payload()` 在 seal 入口一次性深度冻结，其后所有检查与最终
`canonical_supplement_bytes` 只消费该快照。

请自行构造攻击，至少覆盖：

1. 状态型 **outer** Mapping（覆写 `items()` **与** `__getitem__` — builder 的
   第一版攻击只覆写了后者，而冻结走 `items()`，测试因此通过却什么也没测；
   这条教训已记录，请勿重蹈）。
2. 状态型 **row** Mapping（内层，而非外层）。
3. 状态型 **binding**、`rows_digest`、`supplement_id` 等其余键。
4. 在 `freeze_payload` **之后**才变异的对象（证明快照确实与来源解耦）。
5. `__new__` ＋ `object.__setattr__` 构造的 exact-type product/receipt。
6. 冻结拒绝的值类型（`production_payload_unsupported_type`）是否可绕过，
   例如伪装成 `Mapping` 或 `Sequence` 的自定义类型。

判据是**析取**，不是"一律拒绝"：写入前拒绝，或封存一份无禁止字段、
`rows_digest` 与其自身 rows 一致的稳定快照。任何"封印返回且字节含禁止字段"
或"声明摘要 ≠ 实际 rows"都是 High。

**内存捕获，不要写 governed roots**（替换 `resolve_partial` 即可）。

### 二、独立复核第二轮已确认的其余项

不必重做全部一轮/二轮工作，但请抽查你认为最可能退化的：R2 摘要
`a3d40b7c…` 与 correction-only 性质、scope digest 经 runtime serializer 复算、
十个校验 pattern 拒绝 `\n`/`\r\n`、`.python-version` 与 battery 断言一致。

### 三、其余生产边界

`B_DERIVE` 五个 gate、output-root 绑定与 `plan_supplement_paths`、
registry fail-closed（next-value 序列、六个整数下界、`output_root` 绝对性）、
`.partial` 分支 C/E、default-refuse 生产入口。

### 四、机械项

全套件与 collect count 应为 **3970** 且与双 floor pin 一致；
`git diff --check`；frozen hashes 7/7；registry `ee9da33f…`、
exposure `382182bf…`、attestation `d839b965…`；S0-T001 run/archive 14 文件
逐文件相等；两个 `supplements\` 子树不存在；registry 零 `SUPPLEMENT_` 行；
`final_candidate_scans.py` 三个既有 false positive（**不得**被伪称 CLEAN）。

### 五、明确不在你职责内

- 本次 review 属 **Stage I** 还是 **discretionary Tier-1**；
- ITSF 是否纳入 L6 runtime，`LANE` / `STAGE` 取值（spec §2.4：never inferred）；
- 任何执行授权。

以上三项属 Aaron。

### 六、产出

- `VERDICT: PASS | HOLD`，并明示**这不是 `PACKET_OUTCOME`、不释放任何 gate
  transition**（无 `qros-state.yaml`、无 issuance 可绑）。
- Critical/High 优先，逐条给路径、行号、可复现命令。
- 区分"你自己复现的事实"与"builder 自报的证据"。
- 独立性按 context / authorship / model-diversity / empirical 四维分别陈述。
- 不要修仓库。

### 七、你应当知道的残留（可挑战其定性）

见 `ops\N06_HOLD_REPAIR_EVIDENCE.md` §3。注意其中第 1 条的定性**已被第二轮
证伪并就地更正**：`__new__` 可绕过 capability 这一残留仍然成立，但**不得**
再以"重新推导足以兜底"为其背书——那正是第二轮攻破的地方。若你认为现在的
定性仍然过宽，请直说。
```

---

*本件仅为提示词载体，不是 Review Packet v1，不授权任何执行。*
