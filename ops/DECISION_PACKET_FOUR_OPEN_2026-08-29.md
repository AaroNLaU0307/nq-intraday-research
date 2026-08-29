# 四件待裁 —— 决裁包（2026-08-29）

```ini
RECORD_TYPE=DECISION_PACKET
REVIEW_ID=dec-four-open-2026-08-29
RECOMMENDED_MODEL=Fable 5
EFFORT_INTENT=HIGH
RECOMMENDED_EFFORT=high
ROLE=决裁席（adjudication seat）
DELEGATED=YES —— Aaron 2026-08-29「其余的问题如果你拿不定决定或者裁决，
                 交给 fable 也行，让它替我做裁决」
MUST_NOT_BE=builder；本包的作者
LANE=FULL
OUTCOME_EXPOSED=NONE
PREREG_SEALED=N/A
```

## 0. 关于本包席位独立性的如实交代 —— 请先读

**如果本包是由 builder spawn 的 Fable 子代理读到的，那个席位对 builder 不独立**
（QROS：独立性活在会话里不在模型里；subagent 对其 spawner 不独立）。
那种情况下它的结论是**顾问级**，不是独立裁决，记录时必须如此标注。

**完全独立的形式**是 Aaron 开一个全新的 Fable 会话把本包贴进去。

**为什么这四条即便如此也可以交出去**：保留给 Aaron 的六条
（成本／主指标／样本切分与 NA／何时动真实数据／promotion-falsified／
在 `quant-data` 下建目录）之所以保留，是因为**由造东西的人定评判标准，
会让好结果失去信息量**。下面四条没有任何"结果"可以被粉饰 ——
它们问的是"这个失败记到哪一栏""这份授权取什么形制"。

**builder 在每一条都给出了倾向，并且都写了自己可能错在哪。** 请优先攻击那部分。

## 0.1 禁区

本包 outcome-clean。**不得打开** `ops/OUTCOME_CARRYING_ARTIFACTS.json` 的
`carries_outcome` 名单上的任何路径，尤其
`ops/outcome_quarantine/**` 与两份 `EXPOSURE_LEDGER.md`。
需要其中事实请列出路径向工作会话索取，**不要自己去开**。

---

## 第 1 件 —— `production_payload_unsupported_type` 该归哪个门

### 事实

`supplement_production._freeze_value` 在载荷里发现一个键或值**不是恰好内建类型**
（一个敌意子类活过冻结）时抛出此码。它可以从
`build_supplement_from_authority` **传递地**逃到调用方。

C_BUILD 的五道门（已批准封闭枚举，不可增删）：

```
row_schema_blind · day_set_exact · rows_digest_recompute ·
seal_staging_partial · archive_policy_a
```

门名与阶段会被写进 F1/F2 登记簿行。

### builder 的处置与倾向

**现状：`classify_builder_failure` 对它大声拒绝，附上这个问题。**
倾向：**维持拒绝**，直到有人裁定。

### builder 可能错在哪（请攻击这里）

1. **「拒绝」在真跑时意味着停机，而不是记一条 F1。** 一次完整性缺陷因此
   **不会在登记簿里留下痕迹**，只留下一个 traceback。有人可以合理主张：
   宁可归到 `row_schema_blind` 也要有记录 —— 一条名字不完美的记录，
   仍然强过没有记录。**这一条我没有反驳，只是选了从严的一边。**
2. `row_schema_blind` 的既有注释说它存在的意义是「让失败在 F1/F2 词表里有一个
   NAMED stage/gate」—— 那句话可以读成「它就是 C_BUILD 的兜底门」，
   而我读成了「它管行」。**两种读法我没有证据裁断。**
3. 载荷里的键值**可能来自 authority 的 binding 而不是行**，那样它更像
   B_DERIVE 的 `custody_authority_binding`。我没有做数据流分析去确定。

### 三个可选结论

```
甲  维持拒绝（builder 倾向）        代价：真跑时停机，登记簿无记录
乙  归 C_BUILD / row_schema_blind   代价：门名不精确，但有记录
丙  归 B_DERIVE / custody_authority_binding  代价：需要先证明来源确实是 binding
```

---

## 第 2 件 —— 运行时目录创建授权的形制（甲乙丙）—— **撤回：已裁**

> **2026-08-30 追加订正。** 本件不该被送出：`OWNER_DECISIONS_2026-08-29.md` §5
> 已由 Aaron 逐字裁定**乙**，§6 写着「形制已定（乙）」。决裁席认出并拒绝重裁 ——
> 正确。builder 的 `DIRECTORY_CREATION_GRANTS.md` 里那句「Aaron 尚未裁」是假的，
> 订正见该文件末尾 `订正-ALREADY-RULED-2026-08-30`。**原文保留于下，不修改。**


### 事实

父层两条路径的授权 Aaron 已于 2026-08-29 给出并执行完毕（已用掉）。
但真实运行目标是**第二层**：

```
<runs_root>\supplements\<supplement_id>_<UTC>
<archive_root>\supplements\<supplement_id>_<UTC>
```

`<UTC>` 是**运行时刻**的 `YYYYMMDDTHHMMSSZ`，签授权时不可能知道。
而 `DIRECTORY_CREATION_GRANTS.md` §1 要求授权文本含**封闭枚举的绝对路径清单，
不得含通配符**。**两者不可兼得。**

### 三条出路（原文见 `ops/SUPPLEMENTS_SUBTREE_GRANT_PREPARATION.md` §2）

```
甲  由 P2 蕴含运行时目录创建
乙  运行时刻查实 UTC 后再签一份封闭清单
丙  修订 ND1_SUPPLEMENT_DIRECTORY_NAME，把 <UTC> 拿掉
```

### builder 倾向：**乙**

理由：甲**正面抵触** ND1「目录创建与执行是两条不得合并的授权」的明令；
丙要动已批准值，而 A2 永久 HOLD 使修正案没有可满足的前置门。

### builder 可能错在哪

- **乙要求 Aaron 在运行那一刻在场。** 如果他不在，运行就停在那里。
  一个"完全符合形制但实际执行不了"的方案，和甲的"违反明令但能跑"，
  哪个更糟，**我没有立场裁**。
- 我把"不得合并"读作绝对禁令。它也可能只是禁止**同一句话**同时授权两者，
  而不禁止一份 P2 在**另一条明确条款**下蕴含目录创建。**文本我没有逐字复核到这一层。**

---

## 第 3 件 —— 席位跨两仓被消耗时记在哪一边

### 事实

同一个 fresh Sol 席位可能在 `qros-runtime` 与 ITSF 两仓都被消耗。
两仓各有自己的 `ops/REVIEWER_EXPOSURE_LOG.md`（席位轴，append-only）。

### builder 倾向

**两边都记，各记各自仓内消耗的那次**，并在 `cause` 里互相指名。
理由：席位是**会话**属性不是仓属性，只记一边会让另一仓读到假的 `NONE`。

### builder 可能错在哪

同一事件出现在两份 append-only 台账里，**去重责任就落到了读者身上**。
一个只读一边的人会低估消耗，读两边的人会高估。
单一权威台账＋另一边放指针，可能更好。

---

## 第 4 件 —— `ops/EXPOSURE_LEDGER.md` 要不要留一条只含指针的行

### 事实

席位曝光事件目前只进席位轴。研究轴台账（`ops/EXPOSURE_LEDGER.md`）
是 append-only 权威件，且有一条**已批准的「恰有一行携带 TARGET_METRIC」不变量**
被机械守卫钉着。

### builder 未处置

**这一条最接近 Aaron 的保留区**（它动一份 append-only 的研究轴权威台账）。
builder 在 ITSF 那份席位台账里就把它留给了 Aaron，本包沿用。

**请决裁席明确说明：这一条你是否认为该由 Aaron 本人裁，而不是你。**
如果你认为该由你裁，请一并说明为什么它不落入"研究轴记账"这一类。

---

## 交付要求

每一件给出 **裁定 ＋ 理由 ＋ 你认为 builder 的倾向错在哪**。
若某一件你认为证据不足以裁定，**明说不裁**，并列出缺哪一份具体证据 ——
「不裁」是合法结论，猜一个不是。
